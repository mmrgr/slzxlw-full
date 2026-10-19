# -*- coding: utf-8 -*-
"""检验"技术构成"这一模型假设对本文结论的影响。

【动机】
上一轮的外部对照显示：Santa Clara 存在 WUE 比湿冷低约 315 倍的设施（Bowers，
air-cooled + adiabatic）。而本文主情景在**两个合成端点上都用单一 evaporative**。

论文因此写道："统一按湿冷建模使水耗偏高，故水侧压力结论偏保守。"
**但这句话此前从未被定量检验。** 本文的核心结论不是总水耗，而是：
  (1) r* 阈值位置与阈值型响应；
  (2) 瓶颈位置与迁移；
  (3) 纯物理承载容量的 −100 MW

若把冷却技术从 evaporative 换成 dry_first / hybrid，上述三条会怎样？
需要区分两种可能：
  A. 结论消失 —— 那"偏保守"就是错的，是"不成立"；
  B. 结论保留但效应量变小 —— 那"偏保守"成立，且可量化。

【做法】
在 D-HA 端点上，对 4 个技术档（evaporative / hybrid / dry_first / dry）各跑：
  - r* 的解析值（与冷却技术无关，应不变）
  - 阈值型响应是否存在（r=0.5→0.8 总取水增幅）
  - 纯物理 CAWCC 随 r 的变化
"""
from __future__ import annotations

import copy
import glob
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
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402
from run_r2 import daily_constraints, scan_with_mean  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
OUT = HERE / "_tech_sensitivity.json"
CAP = list(np.arange(0, 2001, 50, dtype=float))
TIERS = ["evaporative", "hybrid", "dry_first", "dry"]
R_POINTS = [0.0, 0.5, 0.8]
FIXED_MW = 1200.0


def load_tier(base_cfg: dict, tier: str) -> dict:
    f = R2 / "ha" / f"tech_{tier}.json"
    cfg = json.loads(f.read_text(encoding="utf-8"))
    trial = copy.deepcopy(base_cfg)
    if "components" in cfg:
        for cid, comp in cfg["components"].items():
            if cid in trial["components"]:
                trial["components"][cid].update(comp)
    else:
        trial["components"]["AI_DC1"].update(cfg)
    return trial


def main() -> None:
    base = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    cons_json = json.loads((R2 / "specs" / "constraints_ha.json").read_text(encoding="utf-8"))
    day = {"constraints": daily_constraints(cons_json)}
    phys = {"constraints": {k: v for k, v in day["constraints"].items()
                            if k != "reclaimed_water_substitution_ratio"}}

    summary = {"fixed_capacity_mw": FIXED_MW, "r_points": R_POINTS, "tiers": {}}

    # ===== 1. 固定容量下的阈值型响应 =====
    print(f"{'技术档':<16}{'r=0.5 取水 ML':>14}{'r=0.8 取水 ML':>14}{'增幅%':>9}{'r=0 WUE':>10}")
    print("-" * 66)
    for tier in TIERS:
        cfg = load_tier(base, tier)
        dc = next(v for v in cfg["components"].values() if v.get("kind") == "data_center")
        dc["installed_it_capacity_mw"] = FIXED_MW
        dc.pop("capacity_schedule", None)

        vals, wue0 = {}, None
        for r in R_POINTS:
            t2 = copy.deepcopy(cfg)
            d2 = next(v for v in t2["components"].values() if v.get("kind") == "data_center")
            t2["components"][d2["id"] if "id" in d2 else "AI_DC1"]["water_sources"]["reclaimed"]["target_fraction"] = r
            t2["components"][d2["id"] if "id" in d2 else "AI_DC1"]["water_sources"]["potable"]["target_fraction"] = 1 - r
            res = FullAIUWMModel(t2, ts).run()
            kpi_ext = float(pd.to_numeric(res.data_center_daily["external_withdrawal_ml"],
                                          errors="coerce").sum())
            vals[r] = kpi_ext
            if r == 0.0:
                wue0 = float(pd.to_numeric(res.data_center_daily["wue_l_kwh"],
                                           errors="coerce").mean())

        inc = 100.0 * (vals[0.8] / vals[0.5] - 1.0) if vals[0.5] else float("nan")
        print(f"{tier:<16}{vals[0.5]:>14.1f}{vals[0.8]:>14.1f}{inc:>9.3f}{wue0:>10.3f}")
        summary["tiers"][tier] = {
            "withdrawal_r0.5_ml": round(vals[0.5], 2),
            "withdrawal_r0.8_ml": round(vals[0.8], 2),
            "increase_pct_r05_to_r08": round(inc, 4) if inc == inc else None,
            "wue_l_per_kwh_at_r0": round(wue0, 3) if wue0 else None,
        }

    # ===== 2. 纯物理 CAWCC 随 r 的变化 =====
    print(f"\n{'技术档':<16}{'CAWCC r=0':>11}{'CAWCC r=0.5':>12}{'CAWCC r=0.8':>12}{'降幅 MW':>10}")
    print("-" * 62)
    for tier in TIERS:
        cfg = load_tier(base, tier)
        caw = {}
        for r in (0.0, 0.5, 0.8):
            t2 = copy.deepcopy(cfg)
            d2 = next(v for v in t2["components"].values() if v.get("kind") == "data_center")
            cid = d2["id"] if "id" in d2 else "AI_DC1"
            t2["components"][cid]["water_sources"]["reclaimed"]["target_fraction"] = r
            t2["components"][cid]["water_sources"]["potable"]["target_fraction"] = 1 - r
            scan = scan_with_mean(t2, ts, CAP)
            got = find_ai_carrying_capacity(
                scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True), phys)
            caw[r] = float(got["maximum_safe_ai_capacity_mw"])
        drop = caw[0.0] - caw[0.8]
        print(f"{tier:<16}{caw[0.0]:>11.0f}{caw[0.5]:>12.0f}{caw[0.8]:>12.0f}{drop:>10.0f}")
        summary["tiers"][tier].update({
            "physical_cawcc_r0": caw[0.0],
            "physical_cawcc_r05": caw[0.5],
            "physical_cawcc_r08": caw[0.8],
            "cawcc_drop_r0_to_r08_mw": drop,
        })

    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
