"""A22d: 缺失水质值对完整扫描的影响（1142 情景级）.

A22c 只在 4 个点上做了填补敏感性，样本太少。本脚本在**完整扫描**上量化：
  对每个 (域, pool_scale, φ, 水质档)，比较
     现状 q（缺失按 0）
     vs 填补后 q（缺失物种用同类中位数）
  并报告：
    · q 的中位数变化
    · q **符号翻转**的情景数（这才是关键的定性影响）
    · dS_pot 的符号是否随之改变

【为什么不直接改 A17 主结果】
填补会改变"水样"的定义；主口径应保持"只用有观测来源的水样"。
本脚本的作用是**量化该缺口的规模**，并据此决定主扫描是否应剔除该样本。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
if str(A10) not in sys.path:
    sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402
from aiuwm.data_center import calculate_data_center_plan as cdcp  # noqa: E402

SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
           "Figshare RW (2025, paired study)", "AI-UWM model assumption"]
DOMS = ("ha", "co")
POOL = (1.0, 2.0, 3.0)
PHIS = (0.2, 0.4, 0.6, 0.8)
CHIS = (1.0, 0.5)

_PANEL = cm.PANELS["B_full"]
_TBL = cm.load_samples()
# 填补值：只用有观测来源的水样（排除 AI-UWM 假设值）
_OBS = _TBL[_TBL["source"] != "AI-UWM model assumption"]
IMPUTE = {}
for sp in _PANEL:
    if sp in _OBS.columns:
        v = pd.to_numeric(_OBS[sp], errors="coerce").dropna()
        if len(v):
            IMPUTE[sp] = float(v.median())


def solve(dom: str, sample: str, ps: float, phi: float, chi: float,
          quality: dict) -> dict:
    """给定水质字典求解 B1/B2（直接用引擎，绕开 quality_dict 的裁剪）."""
    bl = cm.BASELINES[dom]
    pool_scale = float(ps)

    def one(target_phi: float) -> float:
        comp = cm.base_comp(bl, "B_full", target_phi, limit_scale=chi)
        # 显式覆盖限值（与 base_comp 的 PANEL×chi 一致）
        comp["cooling"]["water_quality_limits"] = {
            k: float(v) * chi for k, v in _PANEL.items()}
        p = cdcp(comp, bl["date_rep"], bl["drivers_rep"],
                 reclaimed_available_ml=(bl["P0"] * pool_scale) / cm.N_DAYS,
                 reclaimed_quality_mg_l=quality)
        return float(p.external_makeup_ml) * cm.N_DAYS

    M1 = one(phi)
    M0 = one(0.0)
    return {"M0": M0, "M1": M1, "q": (M0 - M1) / M1 if M1 > 0 else float("nan")}


def main() -> None:
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 80)
    rec("A22d  缺失水质值对完整扫描的影响")
    rec("=" * 80)
    rec(f"\n填补用中位数（仅用有观测来源的水样）: "
        f"{ {k: round(v, 1) for k, v in IMPUTE.items()} }")

    rows = []
    for dom in DOMS:
        for smp in SAMPLES:
            r0 = _TBL[_TBL["source"] == smp].iloc[0]
            present = cm.quality_dict(r0, _PANEL)
            missing = [k for k in _PANEL if k not in present]
            filled = dict(present)
            for k in missing:
                if k in IMPUTE:
                    filled[k] = IMPUTE[k]
            for ps in POOL:
                for phi in PHIS:
                    for chi in CHIS:
                        a = solve(dom, smp, ps, phi, chi, present)
                        c = solve(dom, smp, ps, phi, chi, filled)
                        rows.append({
                            "domain": dom, "sample": smp, "pool_scale": ps,
                            "phi": phi, "chi": chi, "n_missing": len(missing),
                            "q_current": a["q"], "q_imputed": c["q"],
                            "M1_current": a["M1"], "M1_imputed": c["M1"],
                        })
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "missing_quality_fullscan.csv", index=False, encoding="utf-8-sig")
    rec(f"\n完成 {len(d)} 情景")

    # ---------- 影响量化 ----------
    rec("\n[影响] 按水样")
    summary_impact = {}
    for smp in SAMPLES:
        g = d[d["sample"] == smp].copy()
        nm = int(g["n_missing"].iloc[0])
        flips = int(((g["q_current"] > 1e-9) != (g["q_imputed"] > 1e-9)).sum())
        # 只统计非零 q 的翻转（避免 0 边界噪声）
        both_nz = (g["q_current"].abs() > 1e-9) | (g["q_imputed"].abs() > 1e-9)
        flips_nz = int((((g["q_current"] > 0) != (g["q_imputed"] > 0)) & both_nz).sum())
        summary_impact[smp] = {
            "n_missing": nm,
            "q_current_median": float(g["q_current"].median()),
            "q_imputed_median": float(g["q_imputed"].median()),
            "q_sign_flips": flips,
            "q_sign_flips_nonzero": flips_nz,
            "share_q_pos_current": float((g["q_current"] > 1e-9).mean()),
            "share_q_pos_imputed": float((g["q_imputed"] > 1e-9).mean()),
            "M1_delta_median": float((g["M1_imputed"] - g["M1_current"]).median()),
            "M1_delta_max_abs": float((g["M1_imputed"] - g["M1_current"]).abs().max()),
        }
        s = summary_impact[smp]
        rec(f"  {smp[:34]:34} 缺失={nm}")
        rec(f"      q 中位: {s['q_current_median']:+.4f} → {s['q_imputed_median']:+.4f}")
        rec(f"      q>0 占比: {s['share_q_pos_current']:.3f} → {s['share_q_pos_imputed']:.3f}")
        rec(f"      q 符号翻转(非零): {s['q_sign_flips_nonzero']} / {len(g)}")
        rec(f"      M1 变化: 中位 {s['M1_delta_median']:+.1f} ML, 最大 {s['M1_delta_max_abs']:.1f} ML")

    # ---------- 结论 ----------
    tot_flips = sum(v["q_sign_flips_nonzero"] for v in summary_impact.values())
    rec(f"\n[结论] 全部情景中 q 符号翻转数 = {tot_flips} / {len(d)}")
    worst = max(summary_impact.items(), key=lambda kv: kv[1]["q_sign_flips_nonzero"])
    rec(f"  影响最大: {worst[0][:34]} ({worst[1]['q_sign_flips_nonzero']} 例翻转)")

    summary = {
        "n_scenarios": int(len(d)),
        "impute_values": IMPUTE,
        "by_sample": summary_impact,
        "total_sign_flips_nonzero": tot_flips,
        "worst_sample": worst[0],
        "recommendation": (
            "'AI-UWM model assumption' 只有 2 个物种(TDS/Cl)，其 hardness/alkalinity/silica "
            "被按 0 处理 → 对应限值永不触发 → 该水样显得比实际更干净，"
            "使其 q>0 的比例被**高估**。建议主扫描**剔除该样本**或明确标注其物种不全，"
            "与 A19 化学审计的结论一致。"),
        "discipline_note": "填补只用有观测来源的水样中位数；未据此更改主口径数字。",
    }
    (HERE / "missing_quality_fullscan_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rec("\n[write] missing_quality_fullscan.csv / _summary.json")
    (HERE / "a22d_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
