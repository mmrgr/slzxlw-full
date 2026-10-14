"""A22c: 缺失水质值按 0 计的影响（数据完整性缺陷定量）.

【问题】
`city_model.quality_dict` 只挑出水样里**存在**的物种。而限值集 `PANELS['B_full']`
含 5 个物种 (TDS/chloride/hardness/alkalinity/silica)。

于是缺失物种的浓度被当作 **0**，使**对应限值永不触发** —— 水样显得比实际更"干净"。

实测缺失情况：
  IEUA RP-1        : 完整 (0 缺失)
  LADWP AWPF       : 完整 (0 缺失)
  Figshare RW      : 缺 alkalinity, silica
  AI-UWM 假设值     : 缺 hardness, alkalinity, silica  ← 只有 2 个物种!

【本脚本】
在**同一水样**下, 对比三种处理：
  A 现状（缺失按 0 计）
  B 缺失物种**从限值集中剔除**（等价于不约束该物种 —— 与 A 应一致, 作为自检）
  C 缺失物种用**同类样本的中位数**填补（敏感性）
量化 q 的符号与 dS_pot 因此变化多少。
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

SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
           "Figshare RW (2025, paired study)", "AI-UWM model assumption"]
DOMS = ("ha", "co")
PHIS = (0.4, 0.7)
CHI = 0.5


def outcome(dom, sample, phi, *, panel: dict, quality: dict | None) -> dict:
    """用给定的限值集与（可能填补过的）水质求解一个情景."""
    bl = cm.BASELINES[dom]
    row = cm.load_samples()
    r0 = row[row["source"] == sample].iloc[0]
    q = quality if quality is not None else cm.quality_dict(r0, panel)
    # 直接用 base_comp + calculate_data_center_plan 以避免 quality_dict 再次裁剪
    from aiuwm.data_center import calculate_data_center_plan as cdcp
    comp = cm.base_comp(bl, "B_full", phi, limit_scale=CHI)
    comp["cooling"]["water_quality_limits"] = {k: float(v) * CHI for k, v in panel.items()}
    p = cdcp(comp, bl["date_rep"], bl["drivers_rep"],
             reclaimed_available_ml=1e9, reclaimed_quality_mg_l=q)
    M1 = float(p.external_makeup_ml)
    comp0 = cm.base_comp(bl, "B_full", 0.0, limit_scale=CHI)
    comp0["cooling"]["water_quality_limits"] = {k: float(v) * CHI for k, v in panel.items()}
    p0 = cdcp(comp0, bl["date_rep"], bl["drivers_rep"],
              reclaimed_available_ml=0.0, reclaimed_quality_mg_l=q)
    M0 = float(p0.external_makeup_ml)
    return {"M0": M0, "M1": M1, "CoC": float(p.cycles_of_concentration),
            "q": (M0 - M1) / M1 if M1 > 0 else float("nan")}


def main() -> None:
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 80)
    rec("A22c  缺失水质值按 0 计的影响")
    rec("=" * 80)

    panel_full = dict(cm.PANELS["B_full"])
    rec(f"\n限值集: {panel_full}")

    # 用同类已观测样本的中位数作填补值
    samples_tbl = cm.load_samples()
    med = {}
    for sp in panel_full:
        if sp in samples_tbl.columns:
            v = pd.to_numeric(samples_tbl[sp], errors="coerce").dropna()
            if len(v):
                med[sp] = float(v.median())
    rec(f"填补用中位数: { {k: round(v, 1) for k, v in med.items()} }")

    rows = []
    for dom in DOMS:
        for smp in SAMPLES:
            r0 = samples_tbl[samples_tbl["source"] == smp].iloc[0]
            present = cm.quality_dict(r0, panel_full)
            missing = [k for k in panel_full if k not in present]
            for phi in PHIS:
                # A 现状: quality_dict 只给存在物种 (缺失即 0)
                a = outcome(dom, smp, phi, panel=panel_full, quality=present)
                # B 自检: 把缺失物种从限值集剔除 (应等价于 A)
                panel_b = {k: v for k, v in panel_full.items() if k in present}
                b = outcome(dom, smp, phi, panel=panel_b, quality=present)
                # C 填补: 缺失物种用中位数
                filled = dict(present)
                for k in missing:
                    if k in med:
                        filled[k] = med[k]
                c = outcome(dom, smp, phi, panel=panel_full, quality=filled)
                rows.append({
                    "domain": dom, "sample": smp, "phi": phi,
                    "n_missing": len(missing), "missing": "|".join(missing),
                    "q_A_current": a["q"], "q_B_drop_limits": b["q"], "q_C_imputed": c["q"],
                    "M1_A": a["M1"], "M1_C": c["M1"],
                    "CoC_A": a["CoC"], "CoC_C": c["CoC"],
                    "dS_A": None, "dS_C": None,
                })
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "missing_quality_impact.csv", index=False, encoding="utf-8-sig")

    rec("\n[自检] A（缺失按0）与 B（剔除该限值）是否等价")
    eq = (d["q_A_current"] - d["q_B_drop_limits"]).abs().max()
    rec(f"  最大差异 = {eq:.3e}  → 等价={bool(eq < 1e-9)}")

    rec("\n[影响] 缺失值填补后 q 与补水的变化（按水样）")
    for smp in SAMPLES:
        g = d[d["sample"] == smp]
        nm = int(g["n_missing"].iloc[0])
        rec(f"  {smp[:34]:34} 缺失={nm}  "
            f"q_A 中位={g['q_A_current'].median():+.4f}  "
            f"q_C 中位={g['q_C_imputed'].median():+.4f}  "
            f"M1 变化中位={(g['M1_C'] - g['M1_A']).median():+9.0f} ML")
        # 符号是否翻转
        flips = int(((g["q_A_current"] > 0) != (g["q_C_imputed"] > 0)).sum())
        rec(f"      q 符号翻转的情景数 = {flips}/{len(g)}")

    summary = {
        "n_rows": int(len(d)),
        "A_equals_B": bool(eq < 1e-9),
        "missing_by_sample": {
            s: sorted(set(d[d["sample"] == s]["missing"].str.split("|").sum()))
            for s in SAMPLES},
        "impact": {
            s: {
                "n_missing": int(d[d["sample"] == s]["n_missing"].iloc[0]),
                "q_A_median": float(d[d["sample"] == s]["q_A_current"].median()),
                "q_C_median": float(d[d["sample"] == s]["q_C_imputed"].median()),
                "M1_delta_median": float((d[d["sample"] == s]["M1_C"]
                                          - d[d["sample"] == s]["M1_A"]).median()),
                "q_sign_flips": int(((d[d["sample"] == s]["q_A_current"] > 0)
                                     != (d[d["sample"] == s]["q_C_imputed"] > 0)).sum()),
            } for s in SAMPLES},
        "finding": (
            "缺失物种浓度被按 0 处理，使对应限值永不触发，水样显得更'干净'。"
            "影响集中在 AI-UWM 假设值(缺 3 项) 与 Figshare RW(缺 2 项)。"
            "'AI-UWM model assumption' 只有 2 个物种，本不应与 3 个公开实测样本并列"
            "作为'水质组成'参与主扫描 —— 这与 A19 化学审计的结论一致。"),
        "discipline_note": "A/B 等价性作为自检；C 为敏感性，不改变主结果口径。",
    }
    (HERE / "missing_quality_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rec("\n[write] missing_quality_impact.csv / _summary.json")
    (HERE / "a22c_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
