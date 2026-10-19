# -*- coding: utf-8 -*-
"""检验"技术构成"假设对本文结论的影响（修正 tech 文件加载方式）。

【修正】tech_*.json 是**完整 project 文件**（含全部 12 个组件），不是 patch。
直接 components.update() 会用 tech 文件的 WTW/WWTW 等参数覆盖基线，
污染非冷却参数。正确做法：**只取 AI_DC1.cooling 部分**替换。
"""
from __future__ import annotations

import copy
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
FIXED_MW = 1200.0


def load_cooling(tier: str) -> dict:
    """只读 tech 文件里的 AI_DC1.cooling。"""
    cfg = json.loads((R2 / "ha" / f"tech_{tier}.json").read_text(encoding="utf-8"))
    dc = cfg["components"]["AI_DC1"]
    return copy.deepcopy(dc["cooling"])


def set_r(cfg: dict, r: float) -> None:
    src = cfg["components"]["AI_DC1"]["water_sources"]
    src["reclaimed"]["target_fraction"] = float(r)
    src["potable"]["target_fraction"] = float(1.0 - r)


def main() -> None:
    base = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    cons_json = json.loads((R2 / "specs" / "constraints_ha.json").read_text(encoding="utf-8"))
    day = {"constraints": daily_constraints(cons_json)}
    phys = {"constraints": {k: v for k, v in day["constraints"].items()
                            if k != "reclaimed_water_substitution_ratio"}}

    print("=== 各技术档的 cooling 关键字段 ===")
    for tier in TIERS:
        c = load_cooling(tier)
        print(f"  {tier:<14} technology={c.get('technology')!s:<22} "
              f"CoC={c.get('cycles_of_concentration')} "
              f"limits={c.get('water_quality_limits')}")

    summary = {"fixed_capacity_mw": FIXED_MW, "tiers": {}}

    # ===== 1. 固定容量下的阈值型响应 =====
    print(f"\n=== 固定 {FIXED_MW:.0f} MW，冷却技术对阈值型响应的影响 ===")
    print(f"{'技术档':<14}{'r=0.5 ML':>12}{'r=0.8 ML':>12}{'增幅%':>9}{'WUE@r0':>10}")
    print("-" * 60)
    for tier in TIERS:
        cfg = copy.deepcopy(base)
        dc = cfg["components"]["AI_DC1"]
        dc["cooling"] = load_cooling(tier)
        dc["installed_it_capacity_mw"] = FIXED_MW
        dc.pop("capacity_schedule", None)

        vals, wue0 = {}, None
        for r in (0.0, 0.5, 0.8):
            t2 = copy.deepcopy(cfg)
            set_r(t2, r)
            res = FullAIUWMModel(t2, ts).run()
            d = res.data_center_daily
            vals[r] = float(pd.to_numeric(d["external_withdrawal_ml"], errors="coerce").sum())
            if r == 0.0:
                wue0 = float(pd.to_numeric(d["wue_l_kwh"], errors="coerce").mean())
        inc = 100.0 * (vals[0.8] / vals[0.5] - 1.0) if vals[0.5] else float("nan")
        print(f"{tier:<14}{vals[0.5]:>12.1f}{vals[0.8]:>12.1f}{inc:>9.3f}{wue0:>10.3f}")
        summary["tiers"][tier] = {
            "wue_l_per_kwh_at_r0": round(wue0, 3),
            "withdrawal_r05_ml": round(vals[0.5], 2),
            "withdrawal_r08_ml": round(vals[0.8], 2),
            "increase_pct": round(inc, 4) if inc == inc else None,
        }

    # ===== 2. 纯物理 CAWCC 随 r 的变化 =====
    print(f"\n=== 纯物理 CAWCC 随 r 的变化（技术档敏感性）===")
    print(f"{'技术档':<14}{'CAWCC r=0':>11}{'r=0.5':>9}{'r=0.8':>9}{'降幅 MW':>10}")
    print("-" * 56)
    for tier in TIERS:
        cfg = copy.deepcopy(base)
        dc = cfg["components"]["AI_DC1"]
        dc["cooling"] = load_cooling(tier)
        caw = {}
        for r in (0.0, 0.5, 0.8):
            t2 = copy.deepcopy(cfg)
            set_r(t2, r)
            scan = scan_with_mean(t2, ts, CAP)
            got = find_ai_carrying_capacity(
                scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True), phys)
            caw[r] = float(got["maximum_safe_ai_capacity_mw"])
        drop = caw[0.0] - caw[0.8]
        print(f"{tier:<14}{caw[0.0]:>11.0f}{caw[0.5]:>9.0f}{caw[0.8]:>9.0f}{drop:>10.0f}")
        summary["tiers"][tier].update({
            "physical_cawcc_r0": caw[0.0],
            "physical_cawcc_r05": caw[0.5],
            "physical_cawcc_r08": caw[0.8],
            "cawcc_drop_mw": drop,
        })

    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
