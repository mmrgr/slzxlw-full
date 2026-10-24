# -*- coding: utf-8 -*-
"""探针 2：水质兼容阈值 r* 是否真实控制承载瓶颈？

【为什么需要这个探针】
上一轮（2026-10-18）的结论是"CoC 是输入参数、全容量区间恒定（HA 4.322/CO 5.000），
故水质不可能成为承载判据"。该结论基于一个**未经检验的假设**：
它只在默认 target_fraction（HA 0.70 / CO 0.45）下采样容量，从未遍历再生水比例 r 这一维。
而 CoC 的代码路径（data_center.py::_cycles_of_concentration）实际是：

    CoC(r) = min( CoC_design, min_species( limit_s / C_mix_s(r) ) )
    C_mix_s(r) = r * C_reclaimed_s + (1-r) * C_potable_s

即 CoC 是 r 的**响应函数**，不是常量。由 CoC_design = L/C_mix 可解出解析阈值：

    r* = (L/CoC_design - C_potable) / (C_reclaimed - C_potable)

r > r* 时 CoC 开始跌破设计值 → 补水需求 M = E*CoC/(CoC-1) 上升 → "节水反噬"。

【本探针要回答的三个问题】
Q1  CoC(r) 是否真的按上式变化？（模型输出 vs 解析式，逐点比对）
Q2  r > r* 时，单位散热的取水量是否上升？（反噬是否可测）
Q3  把 r 政策阈值改动，首失效约束是否随之迁移？（r 是否成为承载判据的驱动变量）

【尺度】小规模：2 域 x 5 个 r 值 x 4 个容量点 = 40 次单次运行。
【用法】PYTHONPATH="src;scripts" python scripts/probe_rstar_mechanism.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.ai_metrics import summarize_ai_water_kpis  # noqa: E402
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

# 小规模验证点
CAPACITIES = [200.0, 800.0, 1200.0, 1600.0]
R_GRID = [0.0, 0.3, 0.5, 0.6, 0.8]


def analytic_rstar(limit_tds: float, coc_design: float, c_pot: float, c_rec: float) -> float:
    """解析阈值：r 超过此值，CoC 跌破设计值。"""
    c_mix_at_design = limit_tds / coc_design
    return (c_mix_at_design - c_pot) / (c_rec - c_pot)


def analytic_coc(r: float, limit_tds: float, coc_design: float, c_pot: float, c_rec: float) -> float:
    c_mix = r * c_rec + (1.0 - r) * c_pot
    return min(coc_design, limit_tds / c_mix)


def run_point(project: dict, timeseries: pd.DataFrame, capacity: float, r: float) -> dict:
    cfg = json.loads(json.dumps(project))
    for comp in cfg["components"].values():
        if comp.get("kind") != "data_center":
            continue
        comp["installed_it_capacity_mw"] = float(capacity)
        comp.pop("capacity_schedule", None)
        # 同时改 target_fraction 与约束阈值保持一致
        sources = comp.get("water_sources", {})
        if "reclaimed" in sources:
            sources["reclaimed"]["target_fraction"] = float(r)
        if "potable" in sources:
            sources["potable"]["target_fraction"] = float(1.0 - r)

    result = FullAIUWMModel(cfg, timeseries).run()
    daily = result.data_center_daily
    kpi = summarize_ai_water_kpis(result, cfg)

    coc_col = next((c for c in daily.columns if "cycles_of_concentration" in c.lower()), None)
    coc_mean = (
        float(pd.to_numeric(daily[coc_col], errors="coerce").mean()) if coc_col else float("nan")
    )
    fb_col = next((c for c in daily.columns if "quality_coc_fallback" in c.lower()), None)
    fallback_days = (
        int(pd.to_numeric(daily[fb_col], errors="coerce").fillna(0).sum()) if fb_col else -1
    )

    evaporation = float(pd.to_numeric(daily.get("evaporation_ml"), errors="coerce").sum()) \
        if "evaporation_ml" in daily.columns else float("nan")

    return {
        "capacity_mw": capacity,
        "target_r": r,
        "actual_reclaimed_fraction": kpi.get("reclaimed_water_substitution_ratio"),
        "coc_mean": coc_mean,
        "coc_fallback_days": fallback_days,
        "freshwater_withdrawal_ml": kpi.get("freshwater_withdrawal_ml"),
        "total_withdrawal_ml": kpi.get("total_withdrawal_ml"),
        "reclaimed_use_ml": kpi.get("reclaimed_water_use_ml"),
        "unmet_cooling_ml": kpi.get("unmet_cooling_water_ml"),
        "evaporation_ml": evaporation,
    }


def main() -> None:
    rows = []
    meta = {}
    for domain in ("ha", "co"):
        proj_path = R2 / domain / "project.json"
        project = json.loads(proj_path.read_text(encoding="utf-8"))
        timeseries = pd.read_csv(R2 / domain / "timeseries.csv")

        dc = next(v for v in project["components"].values() if v.get("kind") == "data_center")
        cooling = dc["cooling"]
        limits = cooling["water_quality_limits"]
        design = float(cooling["cycles_of_concentration"])
        q_rec = dc["water_sources"]["reclaimed"]["quality"]
        q_pot = dc["water_sources"]["potable"]["quality"]
        c_rec, c_pot = float(q_rec["TDS"]), float(q_pot["TDS"])
        r_star = analytic_rstar(float(limits["TDS"]), design, c_pot, c_rec)
        meta[domain] = {
            "coc_design": design,
            "limit_tds": float(limits["TDS"]),
            "c_potable_tds": c_pot,
            "c_reclaimed_tds": c_rec,
            "r_star": r_star,
        }
        print(f"\n=== {domain.upper()} ===  r* = {r_star:.4f}  "
              f"(C_pot={c_pot}, C_rec={c_rec}, L={limits['TDS']}, CoC_d={design})", flush=True)

        for r in R_GRID:
            for cap in CAPACITIES:
                rec = run_point(project, timeseries, cap, r)
                rec["domain"] = domain
                rec["r_star"] = r_star
                rec["coc_analytic"] = analytic_coc(r, float(limits["TDS"]), design, c_pot, c_rec)
                rec["r_above_rstar"] = bool(r > r_star)
                rows.append(rec)
                print(
                    f"  r={r:.2f} cap={cap:6.0f}  CoC_model={rec['coc_mean']:.4f} "
                    f"CoC_analytic={rec['coc_analytic']:.4f}  "
                    f"withdrawal={rec['reclaimed_use_ml']:.0f}  "
                    f"fw={rec['freshwater_withdrawal_ml']:.0f}",
                    flush=True,
                )

    frame = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT / "probe_rstar_mechanism.csv", index=False, encoding="utf-8-sig")
    (OUT / "probe_rstar_mechanism_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ---- 判定 ----
    print("\n" + "=" * 78)
    print("Q1  CoC(r) 与解析式是否一致？")
    print("=" * 78)
    for domain in ("ha", "co"):
        sub = frame[frame["domain"] == domain].dropna(subset=["coc_mean"])
        if sub.empty:
            continue
        err = (sub["coc_mean"] - sub["coc_analytic"]).abs().max()
        print(f"  {domain.upper()}: max|CoC_model - CoC_analytic| = {err:.3e}  "
              f"{'PASS' if err < 1e-3 else 'FAIL'}")

    print("\n" + "=" * 78)
    print("Q2  r > r* 时，单位容量取水是否上升？（反噬）")
    print("=" * 78)
    for domain in ("ha", "co"):
        sub = frame[frame["domain"] == domain]
        for cap in CAPACITIES:
            s = sub[sub["capacity_mw"] == cap].sort_values("target_r")
            if s.empty:
                continue
            below = s[s["target_r"] <= s["r_star"].iloc[0]]
            above = s[s["target_r"] > s["r_star"].iloc[0]]
            if below.empty or above.empty:
                print(f"  {domain.upper()} {cap:.0f}MW: 样本不足（无跨越 r* 的点）")
                continue
            w_below = below["total_withdrawal_ml"].max()
            w_above = above["total_withdrawal_ml"].max()
            delta = w_above - w_below
            pct = 100.0 * delta / w_below if w_below else float("nan")
            print(f"  {domain.upper()} {cap:6.0f}MW: 取水 {w_below:9.1f} -> {w_above:9.1f}  "
                  f"Δ={delta:+9.1f} ({pct:+.2f}%)  {'反噬成立' if delta > 0 else '无反噬'}")

    print("\n" + "=" * 78)
    print("Q3  跨 r* 的 CoC 落差（机制强度）")
    print("=" * 78)
    for domain in ("ha", "co"):
        sub = frame[frame["domain"] == domain]
        s = sub[sub["capacity_mw"] == CAPACITIES[0]].sort_values("target_r")
        if s.empty:
            continue
        print(f"  {domain.upper()}: CoC {s['coc_mean'].iloc[0]:.4f} -> {s['coc_mean'].iloc[-1]:.4f} "
              f"({100*(s['coc_mean'].iloc[-1]/s['coc_mean'].iloc[0]-1):+.2f}%)")

    print(f"\n产物: {OUT / 'probe_rstar_mechanism.csv'}")


if __name__ == "__main__":
    main()
