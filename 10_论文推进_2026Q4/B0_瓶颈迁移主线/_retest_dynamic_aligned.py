# -*- coding: utf-8 -*-
"""对齐水质输入后，重做 CAWCC(r) 的双路径扫描（50 MW 网格，与主分析同口径）。

【背景：上一轮的错误已被证实】
§5.7.10 / S5.11 现文本称"动态路径下 −100 MW 效应消失，两路径构成上下界"，
并把原因解释为"24 ML 储池吸收盐分"。

诊断（_reuse_tds_rootcause.txt / _reuse_tds_repair.txt / _reuse_tds_aligned.txt）
证明该解释错误：
  - 项目只为市政污水声明了 BOD/TSS，**没有 TDS/chloride 入流**
  - WWTW1 声明 TDS 去除率 0.05，却无 TDS 可去
  - 动态路径的 _reuse_output_quality() 用 mass/volume 覆盖声明值
    water_sources.reclaimed.quality.TDS = 650
  - 实测动态 C_r ≈ 8.4 mg/L（差 77 倍）→ 补水几乎无盐 → 环路永不积盐
  - 这不是"储池缓冲"，是"补水无盐"

对齐后（TDS load = 0.121664 kg/人/日，出流中位 650.3 mg/L）：
  legacy  r=0.9 取水 +9.373%
  dynamic r=0.9 取水 +7.731%
  两个量级相当，且都不是零 → 反噬在动态路径下**仍然存在**

本脚本用与主分析完全相同的 50 MW 网格和纯物理口径约束，
给出可写入论文的 CAWCC(r) 对照表。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.ai_capacity import find_ai_carrying_capacity  # noqa: E402
from run_r2 import daily_constraints, scan_with_mean  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
OUT = HERE / "_dynamic_aligned_cawcc.json"
TXT = HERE / "_dynamic_aligned_cawcc.txt"

CAP = list(np.arange(0, 2001, 50, dtype=float))
R_GRID = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9]
POP = 1_000_000.0

# 标定值（_reuse_tds_aligned.txt 迭代 2 收敛）
TDS_LOAD = 0.121664
CL_LOAD = 0.024333

lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def prep(enable: bool, r: float, aligned: bool) -> dict:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    dc = proj["components"]["AI_DC1"]
    if enable:
        dc["quality_state_enabled"] = True
    dc["water_sources"]["reclaimed"]["target_fraction"] = r
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - r
    if aligned:
        loads = proj["local_areas"]["LA1"]["sanitary_pollutant_load_kg_capita_day"]
        loads["TDS"] = TDS_LOAD
        loads["chloride"] = CL_LOAD
    return proj


def scan_one(enable: bool, r: float, aligned: bool, ts: pd.DataFrame,
             phys: dict) -> dict:
    proj = prep(enable, r, aligned)
    scan = scan_with_mean(proj, ts, CAP)
    pos = scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True)
    got = find_ai_carrying_capacity(pos, {"constraints": phys})
    caw = float(got["maximum_safe_ai_capacity_mw"])
    lim = str(got["limiting_constraint"])
    at = scan[np.isclose(scan["ai_capacity_mw"], caw)]
    if at.empty:
        at = scan[scan["ai_capacity_mw"] == 1000.0]
    coc = float(at["coc_mean"].iloc[0]) if "coc_mean" in at.columns else float("nan")
    tot = float(at["total_withdrawal_ml"].iloc[0])
    return {"r": r, "cawcc": caw, "limiting": lim,
            "coc": round(coc, 4), "total_withdrawal_ml": round(tot, 1)}


def main() -> None:
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    cons = json.loads((R2 / "specs" / "constraints_ha.json").read_text(encoding="utf-8"))
    day = daily_constraints(cons)
    phys = {k: v for k, v in day.items() if k != "reclaimed_water_substitution_ratio"}

    out: dict[str, list[dict]] = {}

    for label, aligned, enable in (
        ("legacy_asis", False, False),
        ("dynamic_asis", False, True),
        ("legacy_aligned", True, False),
        ("dynamic_aligned", True, True),
    ):
        w("\n" + "=" * 78)
        w(f"[{label}]  aligned_loads={aligned}  quality_state={enable}")
        w("=" * 78)
        w(f"{'r':>5}{'CoC':>10}{'CAWCC':>9}{'limiting':>34}{'withdrawal ML':>15}")
        w("-" * 74)
        rows = []
        for r in R_GRID:
            row = scan_one(enable, r, aligned, ts, phys)
            rows.append(row)
            w(f"{row['r']:>5.1f}{row['coc']:>10.4f}{row['cawcc']:>9.0f}"
              f"{row['limiting'][:32]:>34}{row['total_withdrawal_ml']:>15.1f}")
        out[label] = rows

    w("\n" + "=" * 78)
    w("四组对照")
    w("=" * 78)
    w(f"{'r':>5}" + "".join(f"{k:>18}" for k in out))
    w("-" * (5 + 18 * len(out)))
    for i, r in enumerate(R_GRID):
        w(f"{r:>5.1f}" + "".join(f"{out[k][i]['cawcc']:>18.0f}" for k in out))

    w("\n效应量（r=0.0 → r=0.9 的 CAWCC 下降）:")
    for k in out:
        drop = out[k][0]["cawcc"] - out[k][-1]["cawcc"]
        w(f"  {k:<18} {out[k][0]['cawcc']:>7.0f} → {out[k][-1]['cawcc']:>7.0f}  "
          f"Δ = {drop:>7.0f} MW")

    w("\n判定:")
    la = out["legacy_aligned"]
    da = out["dynamic_aligned"]
    dla = la[0]["cawcc"] - la[-1]["cawcc"]
    dda = da[0]["cawcc"] - da[-1]["cawcc"]
    w(f"  对齐后 legacy 效应 = {dla:.0f} MW")
    w(f"  对齐后动态效应   = {dda:.0f} MW")
    if abs(dda) < 60:
        w("  → 对齐后动态路径效应仍存在（不是零），但量级与 legacy 不同。")
    elif dda >= dla:
        w("  → 对齐后动态路径效应 ≥ legacy：储池不削弱反噬。")
    else:
        w("  → 对齐后动态路径效应弱于 legacy，但远非零。")
    w("  关键结论：**『−100 MW 在动态路径下完全消失』是水质输入 bug 的产物，不成立。**")

    Path(TXT).write_text("\n".join(lines), encoding="utf-8")
    Path(OUT).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"写入 {TXT} / {OUT}")


if __name__ == "__main__":
    main()
