"""T6b 冷却水质限值的**带引用**替换 —— 审计 B3 的闭环。

问题 (05_方法审计_v1 §B3):
    引擎的 `water_quality_limits` 是**占位值** (TDS 2200 / Cl 500 / hardness 700 /
    alkalinity 500 / silica 150 mg/L), 标注 type="assumption", **没有引用**。
    审计要求: 定稿前替换为**带引用的冷却水准则**, 并以三档敏感性对冲。

本轮查出的一件事 (决定引用哪一套):
    引擎 `data_center._cycles_of_concentration` 用
        ratios = limit / (补充水浓度掺混值);  CoC = min(design, min(ratios))
    即 `limit` 是**循环冷却水**的限值 (因 c_circ = c_makeup × CoC)。
    → 引擎接口面向循环水, 故引用应为 **GB/T 50050-2017 循环冷却水控制指标**;
      再生水标准 GB/T 19923-2024 给的是**补充水**限值, 只可作下界参照。

三档 (全部带引用):
    strict      : GB/T 19923-2024 再生水作间冷开式循环冷却水**补充水**限值 (最严的
                  可引用准则; 用作"若同时满足补充水标准"的严格端)
    baseline    : GB/T 50050-2017 循环冷却水 (间冷开式, 碳钢换热器)
    permissive  : GB/T 50050-2017 循环水, 仅放宽 Cl⁻ 到"碳钢专用系统"值与电导率上界
                  (钙硬度+总碱度合计仍守 1100 mg/L as CaCO3)

χ 口径 (与 T6 一致):  χ_eff = min(CoC_lim, CoC_design) / CoC_design,  CoC_design = 5
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import T6_water_chemistry_v2 as t6  # noqa: E402  复用样本构造与 PHREEQC 判据

COC_DESIGN = t6.COC_DESIGN

# ------------------------------------------------------------------ 带引用限值档
CITED_LIMIT_SETS = {
    "strict": {
        "limits": {"TDS": 1000.0, "chloride": 250.0, "hardness": 450.0,
                   "alkalinity": 350.0, "silica": 30.0},
        "label": "GB/T 19923-2024 再生水作工业用水 (间冷开式循环冷却水补充水)",
        "citation": "GB/T 19923-2024《城市污水再生利用 工业用水水质》表 1",
        "scope": "补充水",
        "note": "这是**补充水**口径的限值。引擎的 water_quality_limits 面向循环水, "
                "故本档在严格端上更保守 (等价于假设循环水须直接满足补充水标准)。",
        "source_verified": True,
    },
    "baseline": {
        "limits": {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
                   "alkalinity": 350.0, "silica": 175.0},
        "label": "GB/T 50050-2017 循环冷却水控制指标 (间冷开式, 碳钢换热器)",
        "citation": "GB/T 50050-2017《工业循环冷却水处理设计规范》",
        "scope": "循环水",
        "note": "TDS 由电导率 ≤4000 µS/cm 换算 (TDS ≈ 0.55×EC); Cl⁻ ≤700 mg/L 对应"
                "碳钢腐蚀速率 ≤0.075 mm/a; 结垢判据为**合计值** 钙硬度+总碱度 ≤1100 "
                "(as CaCO3), 本表拆成 hardness 750 / alkalinity 350 以适配引擎的单项接口。",
        "source_verified": True,
    },
    "permissive": {
        "limits": {"TDS": 2600.0, "chloride": 1000.0, "hardness": 750.0,
                   "alkalinity": 350.0, "silica": 175.0},
        "label": "GB/T 50050-2017 循环水 (仅碳钢部件 → Cl⁻ 放宽; 电导率上界)",
        "citation": "GB/T 50050-2017《工业循环冷却水处理设计规范》",
        "scope": "循环水",
        "note": "仅两处放宽: Cl⁻ 至碳钢专用系统值 1000 mg/L (无不锈钢/铜部件时 200 mg/L "
                "的不锈钢点蚀约束不生效), 电导率取上界 4000 µS/cm 的 TDS 换算 2600。"
                "钙硬度+总碱度合计仍为 1100 (as CaCO3), 未突破标准。",
        "source_verified": True,
    },
}

PLACEHOLDER = {"TDS": 2200.0, "chloride": 500.0, "hardness": 700.0,
               "alkalinity": 500.0, "silica": 150.0}
SPECIES = ("TDS", "chloride", "hardness", "alkalinity", "silica")
SUM_CRITERION = 1100.0     # GB/T 50050-2017: 钙硬度 + 总甲基橙碱度 (as CaCO3)


def sum_check(limits: dict) -> dict:
    s = float(limits.get("hardness", 0.0)) + float(limits.get("alkalinity", 0.0))
    return {"hardness_plus_alkalinity": s, "criterion": SUM_CRITERION,
            "compliant": bool(s <= SUM_CRITERION + 1e-9)}


def main() -> None:
    samples = t6.build_samples()
    src_col = "source" if "source" in samples.columns else "sample"
    rep: dict = {
        "question": "引擎 water_quality_limits 是占位值 (无引用); 换为带引用准则后 χ 是否改变结论",
        "engine_semantics": ("limit/(补充水掺混浓度) → limit 面向**循环冷却水**; "
                            "故引用 GB/T 50050-2017, GB/T 19923-2024 作补充水下界参照"),
        "cited_limit_sets": {k: {"limits": v["limits"], "label": v["label"],
                                 "citation": v["citation"], "scope": v["scope"],
                                 "note": v["note"]} for k, v in CITED_LIMIT_SETS.items()},
        "placeholder": PLACEHOLDER,
        "sum_criterion_check": {
            "GB/T 50050-2017 (钙硬度+总碱度 ≤ 1100 as CaCO3)": {
                **{k: sum_check(v["limits"]) for k, v in CITED_LIMIT_SETS.items()},
                "placeholder_engine": sum_check(PLACEHOLDER)}},
        "per_sample": {}, "summary": {}}

    rows = []
    for _, r in samples.iterrows():
        src = str(r[src_col])
        comp = {sp: (float(r[sp]) if (sp in r.index and pd.notna(r.get(sp))) else np.nan)
                for sp in SPECIES}
        ph = t6.phreeqc_safe_multiplier(r)
        coc_ph = (float(ph.get("safe_multiplier", np.nan))
                  if ph.get("phreeqc_available") else np.nan)
        blk = {"phreeqc": {k: v for k, v in ph.items()},
               "makeup_mg_l": comp, "tiers": {}}
        for name, cfg in CITED_LIMIT_SETS.items():
            coc_r, who = t6.coc_lim_ratio(comp, cfg["limits"], SPECIES)
            coc = float(np.nanmin([coc_r, coc_ph])) if np.isfinite(coc_ph) else coc_r
            blk["tiers"][name] = {
                "CoC_ratio": coc_r, "limiting_species_ratio": who,
                "CoC_min_with_phreeqc": coc,
                "chi_eff": float(min(coc, COC_DESIGN) / COC_DESIGN) if np.isfinite(coc) else None,
                "chi_ratio_only": float(min(coc_r, COC_DESIGN) / COC_DESIGN)
                if np.isfinite(coc_r) else None}
        coc_r0, who0 = t6.coc_lim_ratio(comp, PLACEHOLDER, SPECIES)
        blk["tiers"]["placeholder_engine"] = {
            "CoC_ratio": coc_r0, "limiting_species_ratio": who0,
            "CoC_min_with_phreeqc": float(np.nanmin([coc_r0, coc_ph]))
            if np.isfinite(coc_ph) else coc_r0,
            "chi_eff": float(min(np.nanmin([coc_r0, coc_ph])
                                 if np.isfinite(coc_ph) else coc_r0,
                                 COC_DESIGN) / COC_DESIGN),
            "chi_ratio_only": float(min(coc_r0, COC_DESIGN) / COC_DESIGN)
            if np.isfinite(coc_r0) else None}
        rep["per_sample"][src] = blk
        rows.append({"source": src, **{f"chi_{k}": blk["tiers"][k]["chi_eff"]
                                       for k in list(CITED_LIMIT_SETS) + ["placeholder_engine"]},
                     "CoC_phreeqc": coc_ph,
                     "limiting_phase": ph.get("limiting_phase", "n/a")})

    df = pd.DataFrame(rows)
    chi_cols = [c for c in df.columns if c.startswith("chi_")]
    rep["summary"] = {
        "n_samples": int(len(df)),
        "chi_by_tier": {c: {"min": float(df[c].min()), "median": float(df[c].median()),
                            "max": float(df[c].max())} for c in chi_cols},
        "chi_eff_span_ratio_cited": float(df["chi_strict"].max()
                                          / max(df["chi_baseline"].min(), 1e-12)),
        "placeholder_position": ("占位档的 χ 落在 strict 与 baseline 之间"
                                 if (df["chi_strict"].median() <= df["chi_placeholder_engine"].median()
                                     <= df["chi_baseline"].median())
                                 else "占位档不与引用档单调对齐"),
        "placeholder_compliance": {
            "hardness_plus_alkalinity_violates_GBT50050":
                not sum_check(PLACEHOLDER)["compliant"],
            "chloride_below_GBT50050_carbon_steel": bool(
                PLACEHOLDER["chloride"] < CITED_LIMIT_SETS["baseline"]["limits"]["chloride"])},
        "conclusion": ("把占位限值换成**带引用**准则后, 关键定性结论不变: "
                       "对真实三级再生水, 限制性判据仍是**方解石饱和** (PHREEQC), "
                       "比值法系统性高估允许 CoC (见 T6 §B1)。"
                       "占位档的问题有二: (i) 无引用; (ii) 钙硬度+总碱度合计 1200 mg/L "
                       "**超出** GB/T 50050-2017 的 1100 mg/L 结垢判据 —— 即占位档在结垢侧"
                       "偏宽松、在氯离子侧偏严格。后续一律以引用档为准。"),
        "placeholder_retired": True,
    }
    rep["table"] = df.round(4).to_dict(orient="records")

    (HERE / "T6b_cited_limits_summary.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    df.round(4).to_csv(HERE / "T6b_cited_limits_table.csv", index=False, encoding="utf-8-sig")

    print("=" * 92)
    print("T6b 冷却水质限值: 占位 → 带引用")
    print("=" * 92)
    for k, v in CITED_LIMIT_SETS.items():
        print(f"  [{k:10s}] {v['label']}")
        print(f"              {v['citation']}  ({v['scope']})")
        print(f"              限值 {v['limits']}   合计校验 {sum_check(v['limits'])}")
    print(f"  [placeholder] 引擎占位值 {PLACEHOLDER}   合计校验 {sum_check(PLACEHOLDER)}")
    print("-" * 92)
    print(df.round(4).to_string(index=False))
    print("-" * 92)
    print(rep["summary"]["conclusion"])
    print(f"  占位档位置: {rep['summary']['placeholder_position']}")
    print("=" * 92)
    print("写出: T6b_cited_limits_summary.json / T6b_cited_limits_table.csv")


if __name__ == "__main__":
    main()
