"""T2 探针: 真实再生水化学驱动 calculate_data_center_plan 的 quality_limited 固定点.
目的:
  1) 确认 quality_limited 求解在真实水样下收敛;
  2) 确认固定点与日期无关 (CoC 只依赖掺混比, 不依赖蒸发量);
  3) 量出"限值面板"对可用 CoC 的影响.

⚠ 清理轮 2026-10-14 标注: 这是一次性探针 (不写任何文件), **保留**是因为
  `03_阶段结果_T2-T8.md` 把它当作证据引用 ("固定点探针, 证日期无关性")。
  删除它须同步修改 03 的引用。
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(REPO / "src"))
from aiuwm.data_center import calculate_data_center_plan  # noqa: E402

R2 = REPO / "examples" / "cawcc_r2"

PANEL_ENGINE = {"TDS": 2200.0, "chloride": 500.0}
PANEL_FULL = {"TDS": 2200.0, "chloride": 500.0, "hardness": 700.0,
              "alkalinity": 500.0, "silica": 150.0}
QUAL_IEUA = {"TDS": 443.0, "chloride": 100.0, "hardness": 149.427,
             "alkalinity": 140.0, "silica": 24.0}
QUAL_MODEL = {"TDS": 650.0, "chloride": 130.0}


def build(dom: str):
    proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
    comp = copy.deepcopy(proj["components"]["AI_DC1"])
    comp["installed_it_capacity_mw"] = 1000.0
    ts = pd.read_csv(R2 / dom / "timeseries.csv")
    return comp, ts


def drivers_from(row) -> dict:
    return {
        "temperature_c": float(row.temperature_c),
        "relative_humidity": float(row.relative_humidity_pct),
        "load_factor": float(row.ai_load_factor_a30),
    }


def main() -> int:
    comp, ts = build("ha")
    comp["cooling"]["coc_mode"] = "quality_limited"
    comp["water_sources"]["reclaimed"]["target_fraction"] = 0.9
    comp["water_sources"]["potable"]["target_fraction"] = 0.1

    for panel_name, panel in (("engine", PANEL_ENGINE), ("full", PANEL_FULL)):
        comp["cooling"]["water_quality_limits"] = dict(panel)
        print(f"\n########## 限值面板 = {panel_name} {panel}")
        for qname, q in (("IEUA", QUAL_IEUA), ("model", QUAL_MODEL)):
            print(f"\n--- 水质 {qname} (TDS={q['TDS']:.0f}, Cl={q['chloride']:.0f})")
            print(f"{'day':>4} {'avail':>6} {'CoC':>7} {'frac':>7} {'ext_mk':>9} "
                  f"{'evap':>8} {'status':>14} {'resid':>10} {'roots':>5}")
            for i in (0, 182, 364, 546):
                row = ts.iloc[i]
                for avail in (0.0, 10.0, 25.0, 40.0):
                    p = calculate_data_center_plan(
                        comp, pd.Timestamp(row.date), drivers_from(row),
                        reclaimed_available_ml=avail, reclaimed_quality_mg_l=q,
                    )
                    print(f"{i:>4} {avail:>6.1f} {p.cycles_of_concentration:>7.3f} "
                          f"{p.quality_solver_reclaimed_fraction:>7.4f} "
                          f"{p.external_makeup_ml:>9.4f} {p.evaporation_ml:>8.4f} "
                          f"{p.quality_solver_status:>14} "
                          f"{p.quality_solver_residual:>10.2e} "
                          f"{p.quality_solver_root_count:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
