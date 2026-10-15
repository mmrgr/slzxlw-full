"""A27: 用带引用的准则值替换引擎占位限值 —— 影响评估.

【问题（审计 B3，A19 已登记，一直未执行）】
`city_model.PANELS["B_full"]` 用的是**无引用的引擎占位限值**：
    {TDS 2200, chloride 500, hardness 700, alkalinity 500, silica 150}
且在**结垢侧违反** GB/T 50050-2017：钙硬度+总碱度 = 700+500 = **1200 > 1100**。

【已有替代（A4_水化学参数域/T6b_limits_cited.py，已核验 source_verified=True）】
    baseline   = GB/T 50050-2017 循环水:  2200 / 700 / 750 / 350 / 175  （合计 1100 ✓）
    permissive = GB/T 50050-2017 放宽 Cl⁻: 2600 / 1000 / 750 / 350 / 175
    strict     = GB/T 19923-2024 补充水:   1000 / 250 / 450 / 350 / 30

【本脚本】
  1. 建立"占位 vs 引用"的限值对照；
  2. 在同一批情景上分别求解，量化对 CoC / dS_pot 的影响；
  3. 判定中心结论（符号结构、q>0 充分性）是否改变。

⚠ 本脚本**只做影响评估**，不直接改 city_model。替换决定见报告。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "A10_敏感性与边界"))
sys.path.insert(0, str(ROOT / "A4_水化学参数域"))
import city_model as cm  # noqa: E402
import T6b_limits_cited as cited  # noqa: E402
from aiuwm.data_center import calculate_data_center_plan as cdcp  # noqa: E402

PLACEHOLDER = dict(cited.PLACEHOLDER)
TIERS = {k: v["limits"] for k, v in cited.CITED_LIMIT_SETS.items()}

SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
           "Figshare RW (2025, paired study)", "AI-UWM model assumption"]
PHIS = (0.2, 0.4, 0.6)


def solve(dom: str, sample: str, phi: float, limits: dict) -> dict:
    """用指定限值集求解一对 (B2, B1)。"""
    bl = cm.BASELINES[dom]
    row = cm.load_samples()
    r0 = row[row["source"] == sample].iloc[0]
    q = cm.quality_dict(r0, cm.PANELS["B_full"])   # 物种取自水样

    def one(tgt: float) -> dict:
        comp = cm.base_comp(bl, "B_full", tgt)
        comp["cooling"]["water_quality_limits"] = {k: float(v) for k, v in limits.items()}
        p = cdcp(comp, bl["date_rep"], bl["drivers_rep"],
                 reclaimed_available_ml=1e9, reclaimed_quality_mg_l=q)
        return {"M": float(p.external_makeup_ml), "CoC": float(p.cycles_of_concentration),
                "status": str(getattr(p, "quality_solver_status", "?"))}

    b1, b2 = one(phi), one(0.0)
    return {"M0": b2["M"], "M1": b1["M"], "CoC1": b1["CoC"], "CoC0": b2["CoC"],
            "q": (b2["M"] - b1["M"]) / b1["M"] if b1["M"] > 0 else float("nan")}


def main() -> None:
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 80)
    rec("A27  占位限值 vs 带引用准则值：影响评估")
    rec("=" * 80)

    rec("\n[限值对照]")
    rec(f"  {'档位':34} {'TDS':>6} {'Cl':>6} {'hard':>6} {'alk':>6} {'silica':>7}  硬度+碱度")
    def row(lab: str, d: dict) -> None:
        s = d.get("hardness", 0) + d.get("alkalinity", 0)
        flag = "  ⚠>1100" if s > 1100 else ""
        rec(f"  {lab:34} {d.get('TDS',0):6.0f} {d.get('chloride',0):6.0f} "
            f"{d.get('hardness',0):6.0f} {d.get('alkalinity',0):6.0f} "
            f"{d.get('silica',0):7.0f}  {s:6.0f}{flag}")
    row("占位值 (无引用, 现用)", PLACEHOLDER)
    for k, v in TIERS.items():
        row(f"{k} (GB/T 引用)", v)

    # ---------- 影响评估 ----------
    rec("\n[影响] 同情景下 CoC 与 q 的变化")
    rows = []
    for dom in ("ha", "co"):
        for smp in SAMPLES:
            for phi in PHIS:
                try:
                    rp = solve(dom, smp, phi, PLACEHOLDER)
                except Exception as e:  # noqa: BLE001
                    rec(f"  ERROR placeholder {dom} {smp} phi={phi}: {e}")
                    continue
                for tier, lim in TIERS.items():
                    try:
                        rc = solve(dom, smp, phi, lim)
                    except Exception as e:  # noqa: BLE001
                        rec(f"  ERROR {tier} {dom} {smp} phi={phi}: {e}")
                        continue
                    rows.append({
                        "domain": dom, "sample": smp, "phi": phi, "tier": tier,
                        "CoC_placeholder": rp["CoC1"], "CoC_cited": rc["CoC1"],
                        "dCoC": rc["CoC1"] - rp["CoC1"],
                        "q_placeholder": rp["q"], "q_cited": rc["q"],
                        "q_sign_ph": "+" if rp["q"] > 1e-9 else "-" if rp["q"] < -1e-9 else "0",
                        "q_sign_ci": "+" if rc["q"] > 1e-9 else "-" if rc["q"] < -1e-9 else "0",
                    })
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "placeholder_vs_cited.csv", index=False, encoding="utf-8-sig")
    rec(f"  完成 {len(d)} 组对照")

    if len(d):
        rec("\n  按档位汇总 CoC 变化:")
        g = d.groupby("tier").agg(n=("dCoC", "size"), dCoC中位=("dCoC", "median"),
                                  dCoC最小=("dCoC", "min"), dCoC最大=("dCoC", "max"))
        rec(g.round(3).to_string())

        rec("\n  ★ q 符号是否改变（关键）:")
        for tier, gg in d.groupby("tier"):
            flips = int((gg.q_sign_ph != gg.q_sign_ci).sum())
            rec(f"    {tier:12}: 符号翻转 {flips}/{len(gg)}  "
                f"(占位 q>0 {int((gg.q_sign_ph=='+').sum())} -> 引用 q>0 {int((gg.q_sign_ci=='+').sum())})")

    summary = {
        "issue": ("city_model.PANELS 用无引用的引擎占位限值, 且在结垢侧违反 "
                  "GB/T 50050-2017 (钙硬度+总碱度 1200 > 1100)。"),
        "placeholder": PLACEHOLDER,
        "cited_tiers": {k: {"limits": v, "label": cited.CITED_LIMIT_SETS[k]["label"],
                            "citation": cited.CITED_LIMIT_SETS[k]["citation"]}
                        for k, v in TIERS.items()},
        "n_comparisons": int(len(d)),
        "coc_delta_by_tier": (d.groupby("tier").dCoC.median().round(3).to_dict()
                              if len(d) else {}),
        "q_sign_flips_by_tier": ({t: int((g.q_sign_ph != g.q_sign_ci).sum())
                                  for t, g in d.groupby("tier")} if len(d) else {}),
        "discipline_note": "只做影响评估; 未改 city_model; 引用的限值集来自 A4/T6b (已核验)。",
    }
    (HERE / "placeholder_vs_cited_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rec("\n[write] placeholder_vs_cited.csv / _summary.json")
    (HERE / "a27_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
