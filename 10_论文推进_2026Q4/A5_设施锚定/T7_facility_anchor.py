"""T7 v2 — 设施锚定（审计修复版, 2026-10-14）

修复 05_方法审计_v1 中的:
  C3  Meta WUE 含 14/90 缺失与 2 个 0 值 -> 剔除后按 IQR 报告, 删除"落包络内"的平凡判定
  C4  WUE 两端口径不对齐 -> 显式给出模型/披露两套口径并做 PUE 折算
  C5  GSA"独立实测确认"被高估 -> 降级为"原报告水量账算术自洽"(给定 CoC 时近乎恒等)
  C6  CoC 设计值 vs 有效值 -> 同时报告, 并引用 T8 的口径差
  C7  基线多口径 -> 明确声明唯一 M0/E 来源与量级差

本脚本不做设施级点预测精度声明。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EV = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src" / "research_2026" / "external_evidence"
EXT = HERE.parents[1] / "08_实验数据" / "external"

PUE_REF = 1.30          # 数据中心典型 PUE, 用于把 IT 口径折算到园区口径
IT_CAPACITY_MW = 1000.0
DAYS = 730.0
CAP_FACTOR = 0.8766


def gsa() -> pd.DataFrame:
    p = EV / "gsa_blowdown_recovery_2023" / "cooling_tower_periods_normalized.csv"
    d = pd.read_csv(p)
    num = ["period_days", "makeup_gal", "blowdown_gal", "drift_gal",
           "evaporation_gal", "heat_rejected_mmbtu", "water_per_heat_gal_per_mmbtu",
           "coc_water_balance"]
    for c in num:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["M_over_E"] = d.makeup_gal / d.evaporation_gal
    d["coc_from_form"] = 1.0 / (1.0 - 1.0 / d.M_over_E)     # 由 M/E 反解 (与 coc 同义)
    d["coc_formula"] = d.coc_water_balance / (d.coc_water_balance - 1.0)
    d["resid_pct"] = 100.0 * (d.M_over_E - d.coc_formula) / d.coc_formula
    return d


def meta() -> pd.DataFrame:
    cand = list(EXT.glob("g3_public_disclosures/**/*.csv"))
    if not cand:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in cand], ignore_index=True)


def baseline_source() -> dict:
    """C7: 唯一基线来源 —— A2 冻结冷却曲线 (φ=0) 的 M0 与 E。"""
    c = pd.read_csv(ROOT / "A2_规则实验" / "stage1_cooling_curve.csv")
    r = c[(c.domain == "ha") & (c.phi_actual == 0.0)].iloc[0]
    e, m = float(r.evap_ml), float(r.M_ml)
    return {"coC_design": float(r.CoC_mean), "E_ml": e, "M_ml": m,
            "M_over_E": m / e,
            "CoC_effective_by_water_balance": m / (m - e),
            "source": "A2_规则实验/stage1_cooling_curve.csv (domain=ha, phi=0)"}


def main() -> int:
    g = gsa()
    g.to_csv(HERE / "T7_gsa_anchoring.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 210)
    print("===== GSA 冷却塔: 报告水量账的算术自洽性 (C5 降级)")
    print(g[["period_label", "period_days", "coc_water_balance", "M_over_E",
             "coc_formula", "resid_pct"]].round(3).to_string(index=False))
    ok = g.dropna(subset=["M_over_E", "coc_formula"])
    mae = float(np.mean(np.abs(ok.M_over_E - ok.coc_formula)))
    print(f"\nM/E 与 CoC/(CoC-1) 平均绝对偏差 = {mae:.4f} (n={len(ok)})")
    print("注意(C5): 给定 CoC 时 CoC=M/(M-E) 是代数恒等式, 因此该检验只能说明"
          "'原报告的水量账算术自洽', 不能作为数据中心冷却物理律的独立验证。")
    print(f"实测 CoC 包络 (法院冷却塔, 非数据中心): "
          f"{g.coc_water_balance.min():.2f} – {g.coc_water_balance.max():.2f}")

    ref = baseline_source()
    print("\n===== 主模型参照 (C6/C7)")
    print(f"  来源: {ref['source']}")
    print(f"  CoC_design = {ref['coC_design']:.2f}; 由水量账反解的有效 CoC = "
          f"{ref['CoC_effective_by_water_balance']:.3f}")
    print(f"  → 口径差 {abs(ref['CoC_effective_by_water_balance']-ref['coC_design'])/ref['CoC_effective_by_water_balance']:.2%}"
          f" (C6: 内部回收抬高有效浓缩倍数; 与 T8 结论一致)")

    m = meta()
    wue_note = None
    if not m.empty:
        raw_n = len(m)
        m["wue_park_l_per_kwh"] = 1e6 * m["water_withdrawal_ml"] / (m["electricity_mwh"] * 1000.0)
        # C3: 剔除缺失与 0 值(明显不完整记录)
        bad = m["wue_park_l_per_kwh"].isna() | (m["wue_park_l_per_kwh"] <= 0.0) \
            | (m["electricity_mwh"] < 100e3)
        m["excluded"] = bad
        m.to_csv(HERE / "T7_meta_wue.csv", index=False, encoding="utf-8-sig")
        v = m.loc[~bad, "wue_park_l_per_kwh"]
        q1, q3 = float(v.quantile(.25)), float(v.quantile(.75))
        # 模型口径
        it_kwh = IT_CAPACITY_MW * DAYS * 24 * CAP_FACTOR * 1000.0
        model_wue_it = 1e6 * ref["M_ml"] / it_kwh                 # 冷却补水 / IT 电量
        model_wue_park = 1e6 * ref["M_ml"] / (it_kwh * PUE_REF)   # 园区口径
        print(f"\n===== Meta 2025 年度披露 → 园区 WUE (L/kWh, 剔除 {int(bad.sum())} 条)"
              f"  原始 {raw_n} → 有效 {int((~bad).sum())}")
        print(f"  披露口径(园区取水/园区电量): Q1={q1:.3f}  中位={v.median():.3f}  Q3={q3:.3f}"
              f"  IQR=[{q1:.3f}, {q3:.3f}]")
        print(f"  主模型(冷却补水/IT电量)  = {model_wue_it:.3f} L/kWh")
        print(f"  主模型折算到园区口径(PUE={PUE_REF}) = {model_wue_park:.3f} L/kWh")
        print(f"  → C4: 两端口径分子(冷却 vs 园区)与分母(IT vs 园区)均不同,"
              f" 比值仅在折算后有可比性; 中位比 = {model_wue_park/v.median():.1f}×")
        wue_note = {
            "n_disclosed_rows": raw_n, "n_used": int((~bad).sum()),
            "n_excluded": int(bad.sum()),
            "disclosure_park_wue_q1_median_q3": [q1, float(v.median()), q3],
            "model_cooling_over_it_wue_l_per_kwh": model_wue_it,
            "model_park_equivalent_wue_l_per_kwh": model_wue_park,
            "pue_assumed": PUE_REF,
            "ratio_of_park_equivalents": float(model_wue_park / v.median()),
            "interpretation": "Model is a WET evaporative design; the disclosed fleet mixes "
                              "closed-loop/dry designs. This is a scope statement, NOT a "
                              "validation of fleet-average WUE.",
        }
    else:
        print("\n[Meta] 未找到披露数据 (记录为未完成项)")

    summary = {
        "gsa_periods": int(len(g)),
        "gsa_accounting_selfconsistent_MAE": mae,
        "gsa_claim": "arithmetic consistency of the source report's own water balance; "
                     "NOT an independent validation of data-centre cooling physics (C5)",
        "gsa_coc_range": [float(g.coc_water_balance.min()), float(g.coc_water_balance.max())],
        "model_reference": ref,
        "baseline_source_note": "C7: single source = A2 frozen cooling curve at phi=0",
        "meta_disclosure": wue_note,
        "claim_boundary": "order-of-magnitude anchoring; NOT facility-level point prediction.",
    }
    (HERE / "T7_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n[write] {HERE/'T7_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
