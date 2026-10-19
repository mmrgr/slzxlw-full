# -*- coding: utf-8 -*-
"""核查 hybrid 与 dry_first 的 CAWCC 降幅同为 −50 MW 是真实还是量化伪影。

【疑点】
上一轮结果：
  evaporative  WUE=2.125  CAWCC 1200→1100  (−100)
  hybrid       WUE=0.558  CAWCC 1150→1100  (−50)
  dry_first    WUE=0.327  CAWCC 1100→1050  (−50)

hybrid 与 dry_first 的 WUE 相差 1.71 倍，降幅却完全相同。
而第 51 轮已经确立：50 MW 网格下的降幅受量化伪影影响，必须用更细网格复核。

【做法】
对 3 个湿档 × 3 个网格（50/25/10 MW）重算 CAWCC 降幅。
判定：
  - 若三网格下降幅一致 → 真结果
  - 若随网格变化 → 量化伪影，不可引用精确值
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
from run_r2 import daily_constraints, scan_with_mean  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
OUT = HERE / "_tech_grid_convergence.json"

GRIDS = {
    "50mw": list(np.arange(0, 2001, 50, dtype=float)),
    "25mw": list(np.arange(0, 2001, 25, dtype=float)),
    "10mw": list(np.arange(0, 2001, 10, dtype=float)),
}
TIERS = ["evaporative", "hybrid", "dry_first", "dry"]


def load_cooling(tier: str) -> dict:
    cfg = json.loads((R2 / "ha" / f"tech_{tier}.json").read_text(encoding="utf-8"))
    return copy.deepcopy(cfg["components"]["AI_DC1"]["cooling"])


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

    out = {}
    print(f"{'技术档':<14}{'网格':>7}{'CAWCC r=0':>12}{'CAWCC r=0.8':>13}{'降幅':>8}")
    print("-" * 56)
    for tier in TIERS:
        cfg0 = copy.deepcopy(base)
        cfg0["components"]["AI_DC1"]["cooling"] = load_cooling(tier)
        out[tier] = {}
        for gname, cap in GRIDS.items():
            caw = {}
            for r in (0.0, 0.8):
                t2 = copy.deepcopy(cfg0)
                set_r(t2, r)
                scan = scan_with_mean(t2, ts, cap)
                got = find_ai_carrying_capacity(
                    scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True), phys)
                caw[r] = float(got["maximum_safe_ai_capacity_mw"])
            drop = caw[0.0] - caw[0.8]
            print(f"{tier:<14}{gname:>7}{caw[0.0]:>12.0f}{caw[0.8]:>13.0f}{drop:>8.0f}")
            out[tier][gname] = {"cawcc_r0": caw[0.0], "cawcc_r08": caw[0.8], "drop": drop}
        dr = [out[tier][g]["drop"] for g in GRIDS]
        print(f"{'':14}{'极差':>7}{'':12}{'':13}{max(dr)-min(dr):>8.0f}")
        print()

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"产物：{OUT.name}")

    print("\n=== 判定 ===")
    for tier in TIERS:
        drops = [out[tier][g]["drop"] for g in GRIDS]
        rng = max(drops) - min(drops)
        verdict = "三网格一致（可引用）" if rng == 0 else f"极差 {rng:.0f} MW（不可引用精确值）"
        print(f"  {tier:<14} 降幅 {drops} → {verdict}")


if __name__ == "__main__":
    main()
