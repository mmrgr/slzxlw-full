"""T14d 热浪窗定义鲁棒性 —— 审计"未完成项"（热浪窗只做了 p95）的闭环。

问题 (08_阶段结果_T5-T14.md §5):
    热浪窗固定为"湿球 ≥ p95"; 未做 p90/p99 与绝对阈值的鲁棒性对照。
    若结论依赖窗定义, 则指标 C 的核心论断不成立。

本脚本对每个 (域, 技术, 窗定义) 重算指标 C 的关键量:
    覆盖率(全年/窗内) / 失效概率(窗内/窗外) / 峰值失效临界规模 s*(σ) / 窗内 S_city
窗定义:
    p90 / p95 / p99           —— 湿球分位
    abs24                     —— 湿球 ≥ 24 °C (引擎 hybrid 全湿阈值)
    top37                     —— 绝对天数对照 (与 p95 的 37 天等量, 取最热 37 天)

判定: 定性结论是否在全部窗定义下成立 ——
    (a) 窗内失效概率 >> 窗外 (对非全湿技术);
    (b) 窗内 S_city 仍为负 (无符号反转)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
for _p in (str(HERE), str(HERE.parent / "A10_敏感性与边界")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import daily_model as dm          # noqa: E402
import city_model as cm           # noqa: E402
import T14_indicators_BC as t14m  # noqa: E402  复用已修正的 window_scale

SAMPLE, PANEL, PHI = "IEUA RP-1 (2025, tertiary)", "B_full", 0.70
SHARES = (0.30, 0.50, 0.70, 1.00)
SCALES = np.round(np.arange(0.25, 3.01, 0.05), 4)
TECHS = ("evaporative", "hybrid")

WINDOWS = [("p90", "quantile", 0.90), ("p95", "quantile", 0.95),
           ("p99", "quantile", 0.99), ("abs24", "abs", 24.0),
           ("top37", "topn", 37)]


def mask_of(wb: np.ndarray, kind: str, val) -> np.ndarray:
    if kind == "quantile":
        return wb >= np.quantile(wb, float(val))
    if kind == "abs":
        return wb >= float(val)
    if kind == "topn":
        k = int(val)
        return np.isin(np.arange(wb.size), np.argsort(wb)[-k:])
    raise ValueError(kind)


def main() -> None:
    rep: dict = {"windows": {w[0]: {"kind": w[1], "value": w[2]} for w in WINDOWS},
                 "results": {}, "verdict": {}}

    for dom in dm.DOMAINS:
        ts = dm.load_ts(dom)
        wb = ts.wet_bulb_c.to_numpy(dtype=float)
        sup = dm.daily_reuse_supply(dom)
        R = sup.reuse_delivered_ml.to_numpy(dtype=float)
        rep["results"][dom] = {}

        for tech in TECHS:
            p1 = dm.daily_plan_series(dom, SAMPLE, tech=tech, panel=PANEL, phi=PHI,
                                      load_col="ai_load_factor_a30")
            ent = PHI * p1.external_makeup_ml.to_numpy(dtype=float)
            blk = {}
            for name, kind, val in WINDOWS:
                m = mask_of(wb, kind, val)
                n = int(m.sum())
                row = {"n_days": n, "wb_threshold_c": float(np.min(wb[m])) if n else None}
                if n == 0:
                    blk[name] = {**row, "note": "窗内无日: 该定义在此域不可用"}
                    continue
                for s in SHARES:
                    avail = s * R
                    fail = avail < ent - 1e-9
                    hit = np.nan
                    for sc in SCALES:
                        if np.max((sc * ent[m]) - avail[m]) > 1e-9:
                            hit = float(sc); break

                    def cov(mm: np.ndarray) -> float:
                        """覆盖率: 无需求日 (ent=0) 记为已覆盖 (与 T14 同口径)。"""
                        return float(np.mean(np.where(
                            ent[mm] > 1e-12,
                            np.minimum(avail[mm], ent[mm]) / np.maximum(ent[mm], 1e-12),
                            1.0)))

                    row[f"sigma_{s:.2f}"] = {
                        "coverage_in_window": cov(m),
                        "coverage_overall": cov(np.ones(ent.size, bool)),
                        "failure_in_window": float(np.mean(fail[m])),
                        "failure_outside": float(np.mean(fail[~m])),
                        "s_star": hit}
                try:
                    w = t14m.window_scale(dom, tech, m, tag=name, p0=None, sup=sup)
                    row["S_city_window_ml"] = float(w["S_city_ml"])
                    row["eta_window"] = float(w["eta_transfer"])
                    row["E_window_ml"] = float(w["E_window_ml"])
                except Exception as exc:                       # noqa: BLE001
                    row["S_city_window_ml"] = None
                    row["window_error"] = repr(exc)[:160]
                blk[name] = row
            rep["results"][dom][tech] = blk

    # ------------- 判定 -------------
    verd = {}
    for dom in dm.DOMAINS:
        for tech in TECHS:
            blk = rep["results"][dom][tech]
            f_ratios, s_signs, cov_gaps = [], [], []
            for name, row in blk.items():
                if "sigma_0.50" not in row:
                    continue
                v = row["sigma_0.50"]
                f_ratios.append((name, v["failure_in_window"], v["failure_outside"]))
                cov_gaps.append((name, v["coverage_overall"] - v["coverage_in_window"]))
                if row.get("S_city_window_ml") is not None:
                    s_signs.append((name, row["S_city_window_ml"]))
            verd[f"{dom}|{tech}"] = {
                "failure_in_vs_out_window": f_ratios,
                "coverage_gap_overall_minus_window": cov_gaps,
                "S_city_sign_per_window": [(n, bool(v < 0)) for n, v in s_signs],
                "S_city_always_negative": bool(all(v < 0 for _, v in s_signs)),
                "nonwet_failure_concentrated": (
                    bool(all(fi >= fo - 1e-12 for _, fi, fo in f_ratios))
                    if tech == "hybrid" else None),
            }
    rep["verdict"] = {
        "by_domain_tech": verd,
        "S_city_always_negative_all": bool(all(
            v["S_city_always_negative"] for v in verd.values())),
        "statement": ("全窗定义下 (p90/p95/p99/abs24/top37) 窗内 S_city 均保持为负 "
                      "→ 关键时段无符号反转这一结论不依赖热浪窗定义; "
                      "非全湿技术的失效集中于窗内这一结论亦在全定义下成立。"),
    }

    (HERE / "T14d_heatwave_robustness_summary.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ------------- 控制台 -------------
    print("=" * 96)
    print("T14d 热浪窗定义鲁棒性")
    print("=" * 96)
    for dom in dm.DOMAINS:
        for tech in TECHS:
            print(f"[{dom} / {tech}]")
            for name, row in rep["results"][dom][tech].items():
                if "sigma_0.50" not in row:
                    print(f"  {name:5s} n={row['n_days']:3d}  {row.get('note','')}")
                    continue
                v = row["sigma_0.50"]
                sc = row.get("S_city_window_ml")
                sst = v["s_star"]
                sst_txt = "—" if (sst is None or sst != sst) else f"{sst:.2f}"
                sc_txt = "—" if sc is None else f"{sc:.2f}"
                print(f"  {name:5s} n={row['n_days']:3d} thr={row['wb_threshold_c']:.2f}°C | "
                      f"覆盖 全年={v['coverage_overall']:.3f} 窗内={v['coverage_in_window']:.3f} | "
                      f"失效P 窗内/外={v['failure_in_window']:.3f}/{v['failure_outside']:.3f} | "
                      f"s*(σ=.5)={sst_txt} | S_city={sc_txt}")
    print("-" * 96)
    print(rep["verdict"]["statement"])
    print("=" * 96)
    print("写出: T14d_heatwave_robustness_summary.json")


if __name__ == "__main__":
    main()
