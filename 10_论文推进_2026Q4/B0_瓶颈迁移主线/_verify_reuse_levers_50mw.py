# -*- coding: utf-8 -*-
"""三杠杆 50 MW 重跑结果的自动核验。

核心断言：
  1. 两基底基线 CAWCC 与主结果 physical_daily（HA 1150 / CO 1450）一致；
  2. 处理能力杠杆在两端都恒为 0 增益（无效杠杆）；
  3. 产水量杠杆在 HA 有效、在 CO 无效；
  4. HA 产水量杠杆的真实增益是 +250 MW，而旧 100 MW 网格给的 +300 是基线伪影；
  5. 产水量杠杆确实把瓶颈从水源取水迁移到电网；
  6. 联合口径与纯物理口径在本扫描下数值相同（须记录，不能假定）。

用法: python _verify_reuse_levers_50mw.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
R2 = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
SUM = R2 / "reuse_levers_50mw_summary.json"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    if not SUM.exists():
        print("缺少 reuse_levers_50mw_summary.json")
        return
    s = json.loads(SUM.read_text(encoding="utf-8"))
    ck("产物存在且含两基底", set(s["bases"]) == {"ha", "co"}, str(sorted(s["bases"])))
    ck("网格记录为 50 MW", s["grid_mw"] == 50.0, str(s["grid_mw"]))

    ha, co = s["bases"]["ha"], s["bases"]["co"]

    # ---- 基线必须与主结果一致 ----
    ck("HA 基线物理 CAWCC = 1150（与主结果一致）",
       ha["baseline_physical_mw"] == 1150.0, str(ha["baseline_physical_mw"]))
    ck("CO 基线物理 CAWCC = 1450（与主结果一致）",
       co["baseline_physical_mw"] == 1450.0, str(co["baseline_physical_mw"]))
    ck("HA 基线限制约束 = 水源取水比",
       "max_source_abstraction_ratio" in ha["baseline_physical_limiting"],
       ha["baseline_physical_limiting"])
    ck("CO 基线限制约束 = 电网",
       "grid" in co["baseline_physical_limiting"],
       co["baseline_physical_limiting"])

    # ---- 处理能力杠杆恒为 0 ----
    ck("HA 处理能力杠杆增益 = 0", ha["treatment_capacity_lever"]["physical_gain_mw"] == 0.0,
       str(ha["treatment_capacity_lever"]["physical_gain_mw"]))
    ck("CO 处理能力杠杆增益 = 0", co["treatment_capacity_lever"]["physical_gain_mw"] == 0.0,
       str(co["treatment_capacity_lever"]["physical_gain_mw"]))
    for base, d in (("HA", ha), ("CO", co)):
        recs = d["treatment_capacity_lever"]["physical"]
        vals = {r["cawcc_mw"] for r in recs}
        ck(f"{base} 处理能力杠杆逐点 CAWCC 恒定", len(vals) == 1, str(sorted(vals)))

    # ---- 产水量杠杆：HA 有效 / CO 无效 ----
    ck("HA 产水量杠杆增益 = +250 MW（非旧的 +300）",
       ha["production_lever"]["physical_gain_mw"] == 250.0,
       str(ha["production_lever"]["physical_gain_mw"]))
    ck("CO 产水量杠杆增益 = 0", co["production_lever"]["physical_gain_mw"] == 0.0,
       str(co["production_lever"]["physical_gain_mw"]))

    # ---- 瓶颈迁移 ----
    ha_prod = ha["production_lever"]["physical"]
    ck("HA 产水量杠杆：基线瓶颈为水源取水",
       "max_source_abstraction_ratio" in ha_prod[0]["limiting_constraint"],
       ha_prod[0]["limiting_constraint"])
    ck("HA 产水量杠杆：抬高后瓶颈迁移到电网",
       all("grid" in r["limiting_constraint"] for r in ha_prod[1:]),
       ha_prod[1]["limiting_constraint"])
    co_prod = co["production_lever"]["physical"]
    ck("CO 产水量杠杆：瓶颈自始至终为电网",
       all("grid" in r["limiting_constraint"] for r in co_prod),
       co_prod[0]["limiting_constraint"])

    # ---- 联合 vs 纯物理 ----
    same_ha = ha["baseline_joint_mw"] == ha["baseline_physical_mw"]
    same_co = co["baseline_joint_mw"] == co["baseline_physical_mw"]
    ck("HA 联合口径与纯物理口径数值相同（须如实记录）", same_ha,
       f"joint={ha['baseline_joint_mw']} phys={ha['baseline_physical_mw']}")
    ck("CO 联合口径与纯物理口径数值相同（须如实记录）", same_co,
       f"joint={co['baseline_joint_mw']} phys={co['baseline_physical_mw']}")

    # ---- 旧的 100 MW 产物仍在，作为历史对照 ----
    old_ha = R2 / "ha" / "reuse_production_marginal_curve.csv"
    ck("旧 100 MW 产物仍保留（历史对照）", old_ha.exists(),
       f"{old_ha.stat().st_size} B" if old_ha.exists() else "缺失")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\n三杠杆 50 MW 核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
