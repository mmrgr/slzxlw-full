# -*- coding: utf-8 -*-
"""在 50 MW 网格上重跑再生水三杠杆曲线，消除最后一处口径不一致。

【为什么必须重跑】
主结果的 physical_daily CAWCC（HA 1150 / CO 1450 MW）来自 **50 MW** 网格
（`CAPACITIES_SCAN = np.arange(0, 2001, 50)`），而两个杠杆曲线
（`reuse_marginal_curve.csv`、`reuse_production_marginal_curve.csv`）来自
`specs/interventions_{ha,co}.json` 的 **100 MW** 网格
（`capacities_mw = [0,100,...,2000]`，基点 HA 1100 / CO 1400）。

后果：`03_主稿_v2.md` §7.0 与 §7.5 的三杠杆表只能携带"不同网格、数值不可相减"的口径声明，
且 §9.2 第 8 条把"杠杆曲线未在 50 MW 网格上重跑"登记为已知缺口
（WR 英文稿 SI S4.1 / S4.6 沿用同一警告）。

本脚本把两个杠杆放到与主结果**同一网格（50 MW）**上重跑。

【口径声明（关键，2026-10-18 核对源码后确认）】
`run_r2.py` 的 C2/C3 段（第 412–586 行）调用
`find_ai_carrying_capacity(..., day_constraints)`，使用的是 **联合口径**
`day_constraints`（**含** `reclaimed_water_substitution_ratio` 政策约束），
**不是** `physical_day`。

因此本脚本**同时输出两种口径**，命名区分：
  *_50mw.csv          —— 联合口径（与既有 100 MW 产物同口径，可逐点对比验证）
  *_50mw_physical.csv —— 纯物理口径（与主结果 physical_daily 同口径）

【产物】（全部带 `_50mw` 后缀，不覆盖既有 100 MW 产物）
  reuse_marginal_curve_50mw.csv / reuse_marginal_curve_50mw_physical.csv
  reuse_production_marginal_curve_50mw.csv / ..._50mw_physical.csv
  reuse_levers_50mw_summary.json

【用法】PYTHONPATH="src;scripts" python scripts/run_reuse_levers_50mw.py
        PYTHONPATH="src;scripts" python scripts/run_reuse_levers_50mw.py --bases ha
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 直接复用 run_r2.py 的扫描与约束构造，保证与主结果逐位同源
from aiuwm.ai_capacity import find_ai_carrying_capacity, scan_ai_capacity  # noqa: E402
from run_r2 import daily_constraints, scan_with_mean  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

CAPACITIES_50MW = list(np.arange(0, 2001, 50, dtype=float))
YEARS = 2.0  # 730 日驱动


def parse_bases(argv: list[str]) -> list[str]:
    for i, a in enumerate(argv):
        if a == "--bases" and i + 1 < len(argv):
            return [b.strip().lower() for b in argv[i + 1].split(",") if b.strip()]
        if a.startswith("--bases="):
            return [b.strip().lower() for b in a.split("=", 1)[1].split(",") if b.strip()]
    return ["ha", "co"]


def split_constraints(constraints: dict) -> tuple[dict, dict]:
    """返回 (联合口径, 纯物理口径)，复刻 run_r2.py 第 311/313 行的规则。"""
    day = {"constraints": daily_constraints(constraints)}
    physical = {"constraints": {
        name: definition for name, definition in day["constraints"].items()
        if name != "reclaimed_water_substitution_ratio"
    }}
    return day, physical


def cawcc(scan: pd.DataFrame, cons: dict) -> dict:
    return find_ai_carrying_capacity(
        scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True), cons
    )


def run_base(base: str) -> dict:
    print(f"\n{'='*78}\n[{base.upper()}]\n{'='*78}")
    project0 = json.loads((R2 / base / "project.json").read_text(encoding="utf-8"))
    timeseries = pd.read_csv(R2 / base / "timeseries.csv")
    constraints = json.loads((R2 / "specs" / f"constraints_{base}.json").read_text(encoding="utf-8"))
    folder = OUT / base

    day_cons, phys_cons = split_constraints(constraints)

    base_scan = scan_with_mean(copy.deepcopy(project0), timeseries, CAPACITIES_50MW)
    b_joint = cawcc(base_scan, day_cons)
    b_phys = cawcc(base_scan, phys_cons)
    print(f"基线（50 MW 网格）：联合 {b_joint['maximum_safe_ai_capacity_mw']} MW "
          f"/ 纯物理 {b_phys['maximum_safe_ai_capacity_mw']} MW")

    def sweep_unused():  # 占位已删除，保留说明以免误读
        raise RuntimeError("unused")

    # ---------- 杠杆一：仅扩处理能力（产水量不变）----------
    base_reuse_capacity = float(project0["components"]["CENTRAL_REUSE"]["treatment_capacity_ml_day"])
    cap_grid = sorted({base_reuse_capacity, 45.0, 60.0, 75.0, 90.0, 120.0, 160.0})
    cap_joint, cap_phys = [], []
    for cap in cap_grid:
        trial = copy.deepcopy(project0)
        trial["components"]["CENTRAL_REUSE"]["treatment_capacity_ml_day"] = cap
        scan = scan_with_mean(trial, timeseries, CAPACITIES_50MW)
        fj, fp = cawcc(scan, day_cons), cawcc(scan, phys_cons)
        cap_joint.append({"reuse_treatment_capacity_ml_day": cap,
                          "cawcc_mw": fj["maximum_safe_ai_capacity_mw"],
                          "limiting_constraint": fj["limiting_constraint"]})
        cap_phys.append({"reuse_treatment_capacity_ml_day": cap,
                         "cawcc_mw": fp["maximum_safe_ai_capacity_mw"],
                         "limiting_constraint": fp["limiting_constraint"]})
        print(f"  [处理能力] {cap:6.1f} ML/d → 联合 {fj['maximum_safe_ai_capacity_mw']} / "
              f"物理 {fp['maximum_safe_ai_capacity_mw']} MW")

    # ---------- 杠杆二：提高产水量（WWTW 分流比）----------
    base_fraction = float(project0["components"]["WWTW1"]["central_reuse_fraction"])
    baseline_sewage_ml_d = float(
        base_scan.loc[base_scan["ai_capacity_mw"] == 0.0, "wastewater_ml"].iloc[0]
    ) / (365.0 * YEARS)
    prod_joint, prod_phys = [], []
    for fraction in (base_fraction, 0.25, 0.35, 0.45, 0.60):
        trial = copy.deepcopy(project0)
        trial["components"]["WWTW1"]["central_reuse_fraction"] = fraction
        trial["components"]["CENTRAL_REUSE"]["treatment_capacity_ml_day"] = round(
            fraction * baseline_sewage_ml_d * 1.25, 1
        )
        scan = scan_with_mean(trial, timeseries, CAPACITIES_50MW)
        fj, fp = cawcc(scan, day_cons), cawcc(scan, phys_cons)
        common = {"central_reuse_fraction": fraction,
                  "estimated_production_ml_day": fraction * baseline_sewage_ml_d,
                  "reuse_treatment_capacity_ml_day": round(fraction * baseline_sewage_ml_d * 1.25, 1)}
        prod_joint.append({**common, "cawcc_mw": fj["maximum_safe_ai_capacity_mw"],
                           "limiting_constraint": fj["limiting_constraint"]})
        prod_phys.append({**common, "cawcc_mw": fp["maximum_safe_ai_capacity_mw"],
                          "limiting_constraint": fp["limiting_constraint"]})
        print(f"  [产水量]   fraction={fraction:.2f} → 联合 {fj['maximum_safe_ai_capacity_mw']} / "
              f"物理 {fp['maximum_safe_ai_capacity_mw']} MW  ({fp['limiting_constraint']})")

    def finalize(rows: list[dict], xcol: str) -> pd.DataFrame:
        df = pd.DataFrame(rows)
        df["marginal_gain_mw_per_ml_day"] = (
            df["cawcc_mw"].astype(float).diff() / df[xcol].astype(float).diff()
        )
        return df

    cj = finalize(cap_joint, "reuse_treatment_capacity_ml_day")
    cp = finalize(cap_phys, "reuse_treatment_capacity_ml_day")
    pj = finalize(prod_joint, "estimated_production_ml_day")
    pp = finalize(prod_phys, "estimated_production_ml_day")

    cj.to_csv(folder / "reuse_marginal_curve_50mw.csv", index=False, encoding="utf-8-sig")
    cp.to_csv(folder / "reuse_marginal_curve_50mw_physical.csv", index=False, encoding="utf-8-sig")
    pj.to_csv(folder / "reuse_production_marginal_curve_50mw.csv", index=False, encoding="utf-8-sig")
    pp.to_csv(folder / "reuse_production_marginal_curve_50mw_physical.csv",
              index=False, encoding="utf-8-sig")

    print(f"\n  → 处理能力杠杆：联合增益 {cj['cawcc_mw'].iloc[-1]-cj['cawcc_mw'].iloc[0]:+.0f} MW "
          f"/ 物理增益 {cp['cawcc_mw'].iloc[-1]-cp['cawcc_mw'].iloc[0]:+.0f} MW")
    print(f"  → 产水量杠杆：  联合增益 {pj['cawcc_mw'].iloc[-1]-pj['cawcc_mw'].iloc[0]:+.0f} MW "
          f"/ 物理增益 {pp['cawcc_mw'].iloc[-1]-pp['cawcc_mw'].iloc[0]:+.0f} MW")

    return {
        "baseline_joint_mw": b_joint["maximum_safe_ai_capacity_mw"],
        "baseline_joint_limiting": b_joint["limiting_constraint"],
        "baseline_physical_mw": b_phys["maximum_safe_ai_capacity_mw"],
        "baseline_physical_limiting": b_phys["limiting_constraint"],
        "treatment_capacity_lever": {
            "joint": cj.to_dict("records"), "physical": cp.to_dict("records"),
            "joint_gain_mw": float(cj["cawcc_mw"].iloc[-1] - cj["cawcc_mw"].iloc[0]),
            "physical_gain_mw": float(cp["cawcc_mw"].iloc[-1] - cp["cawcc_mw"].iloc[0]),
        },
        "production_lever": {
            "joint": pj.to_dict("records"), "physical": pp.to_dict("records"),
            "joint_gain_mw": float(pj["cawcc_mw"].iloc[-1] - pj["cawcc_mw"].iloc[0]),
            "physical_gain_mw": float(pp["cawcc_mw"].iloc[-1] - pp["cawcc_mw"].iloc[0]),
        },
    }


def main() -> None:
    bases = parse_bases(sys.argv[1:])
    print(f"基底: {bases}\n网格: 50 MW, {len(CAPACITIES_50MW)} 点（与主结果同网格）")
    summary = {"grid_mw": 50.0, "capacities_mw": CAPACITIES_50MW, "bases": {}}
    for base in bases:
        summary["bases"][base] = run_base(base)
    out = OUT / "reuse_levers_50mw_summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物已写入 {out.name} 及 *_50mw*.csv")


if __name__ == "__main__":
    main()
