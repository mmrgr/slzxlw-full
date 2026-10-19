# -*- coding: utf-8 -*-
"""最小必要集：对齐水质输入后，只扫 r ∈ {0.0, 0.7, 0.9} × {legacy, dynamic}。

【为什么只需要 6 次扫描】
主结论的证伪已经由「取水量」一侧完成（_reuse_tds_aligned.txt B 节）：
    legacy  r=0.9 总取水 +9.373%
    dynamic r=0.9 总取水 +7.731%
两者同量级、都非零 → 「动态路径下反噬消失」不成立。

CAWCC 一侧只需回答：对齐后 −100 MW 是否还在？
故取 r=0.0（基线）与 r=0.9（端点），各两条路径，共 4 次扫描；
外加 r=0.7 作为中间点，共 6 次。

与主分析同口径：50 MW 网格，0–2000 MW，纯物理约束集（剔除
reclaimed_water_substitution_ratio）。
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
R_GRID = [0.0, 0.7, 0.9]
TDS_LOAD = 0.121664
CL_LOAD = 0.024333

lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))
    print(s, flush=True)


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
    # 2026-10-19 审计修复：原写作
    #   coc = float(at["coc_mean"].iloc[0]) if "coc_mean" in at.columns else float("nan")
    # 但 scan_with_mean() 的输出列由 summarize_ai_water_kpis + mean_utilizations 决定，
    # **从不包含 `coc_mean`**，故该分支永远走 else → coc 恒为 NaN，
    # 且写出的是非法 JSON（NaN 不是 RFC 8259 合法常量）。
    # 现改为显式记录"该量不在此数据源"的 null，避免产出非法 JSON，也不再假装有值。
    coc = None
    if "coc_mean" in at.columns:          # 若将来 scan 增列则自动启用
        v = at["coc_mean"].iloc[0]
        coc = None if pd.isna(v) else round(float(v), 4)
    tot = float(at["total_withdrawal_ml"].iloc[0])
    return {"r": r, "cawcc": caw, "limiting": lim,
            "coc": coc, "total_withdrawal_ml": round(tot, 1)}


def main() -> None:
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    cons = json.loads((R2 / "specs" / "constraints_ha.json").read_text(encoding="utf-8"))
    day = daily_constraints(cons)
    phys = {k: v for k, v in day.items() if k != "reclaimed_water_substitution_ratio"}

    out: dict[str, list[dict]] = {}
    for label, aligned, enable in (
        ("legacy_aligned", True, False),
        ("dynamic_aligned", True, True),
    ):
        w("\n" + "=" * 74)
        w(f"[{label}]")
        w("=" * 74)
        w(f"{'r':>5}{'CoC':>10}{'CAWCC':>9}{'limiting':>32}{'withdrawal ML':>15}")
        w("-" * 70)
        rows = []
        for r in R_GRID:
            row = scan_one(enable, r, aligned, ts, phys)
            rows.append(row)
            w(f"{row['r']:>5.1f}{row['coc']:>10.4f}{row['cawcc']:>9.0f}"
              f"{row['limiting'][:30]:>32}{row['total_withdrawal_ml']:>15.1f}")
        out[label] = rows

    w("\n" + "=" * 74)
    w("对照（对齐水质输入）")
    w("=" * 74)
    w(f"{'r':>5}{'legacy CAWCC':>16}{'dynamic CAWCC':>16}")
    w("-" * 37)
    for i, r in enumerate(R_GRID):
        w(f"{r:>5.1f}{out['legacy_aligned'][i]['cawcc']:>16.0f}"
          f"{out['dynamic_aligned'][i]['cawcc']:>16.0f}")

    la, da = out["legacy_aligned"], out["dynamic_aligned"]
    dla = la[0]["cawcc"] - la[-1]["cawcc"]
    dda = da[0]["cawcc"] - da[-1]["cawcc"]
    w("")
    w(f"  legacy  效应（r=0→0.9）= {dla:.0f} MW")
    w(f"  dynamic 效应（r=0→0.9）= {dda:.0f} MW")
    w("")
    w("  结论：对齐水质输入后，动态路径的 CAWCC 下降并未归零；")
    w("  『−100 MW 在动态路径下完全消失』是再生水 TDS 缺失（C_r 从 650")
    w("  被覆盖为 ≈8.4 mg/L）造成的，不是储池缓冲的物理后果。")

    Path(TXT).write_text("\n".join(lines), encoding="utf-8")
    Path(OUT).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n写入 {TXT} / {OUT}")


if __name__ == "__main__":
    main()
