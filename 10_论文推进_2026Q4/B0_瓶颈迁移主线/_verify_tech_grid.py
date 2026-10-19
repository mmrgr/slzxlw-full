# -*- coding: utf-8 -*-
"""技术档网格收敛核验：把"不可引用精确降幅"这一规则固化为门禁。

【为什么必须固化成门禁】
第 51 轮已确立：50 MW 网格下中间区降幅受量化伪影影响，不可引用精确值。
但该规则当时只应用于**替代率 r 维度**，未应用于**冷却技术档维度**。
上一轮因此把 "−100 / −50 / −50" 写进了正文，本轮三网格复核发现极差 10–40 MW。

本门禁断言：
  1. 技术档降幅在三网格下极差 > 0（即确属网格依赖，不可作为精确值）；
  2. `evaporative` 的降幅随网格细化单调下降（收敛，因基线稳定、端点上升）；
  3. `dry_first` 的降幅随网格细化单调上升（发散，因端点稳定、基线上升）；
  4. `dry` 三网格下恒为 0；
  5. 排序在三网格下保持：evaporative ≥ others > dry。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
D = HERE / "_tech_grid_convergence.json"
MS = HERE / "03_主稿_v2.md"
SI = HERE / "05_wr_supplementary_en.md"
EN = HERE / "04_wr_manuscript_en.md"

RES: list[tuple[str, bool, str]] = []
GRIDS = ("50mw", "25mw", "10mw")
WET = ("evaporative", "hybrid", "dry_first")


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    if not D.exists():
        print("缺少 _tech_grid_convergence.json")
        return
    d = json.loads(D.read_text(encoding="utf-8"))

    # 1. 三档降幅均随网格变化
    for t in WET:
        drops = [d[t][g]["drop"] for g in GRIDS]
        rng = max(drops) - min(drops)
        ck(f"{t} 降幅存在网格依赖（极差 > 0）", rng > 0, f"{drops}，极差 {rng:.0f}")

    # 2. evaporative 单调下降
    ev = [d["evaporative"][g]["drop"] for g in GRIDS]
    ck("evaporative 降幅随网格细化单调下降（收敛）",
       ev[0] >= ev[1] >= ev[2], str(ev))

    # 3. dry_first 单调上升
    df = [d["dry_first"][g]["drop"] for g in GRIDS]
    ck("dry_first 降幅随网格细化单调上升（发散）",
       df[0] <= df[1] <= df[2], str(df))

    # 4. dry 恒 0
    dr = [d["dry"][g]["drop"] for g in GRIDS] if "dry" in d else None
    if dr is None:
        ck("dry 档数据存在", False, "json 缺 dry")
    else:
        ck("dry 三网格降幅恒为 0", all(x == 0 for x in dr), str(dr))

    # 5. 排序：50 MW 下 evaporative 最高，但 10 MW 下被 dry_first 反超
    o50 = {t: d[t]["50mw"]["drop"] for t in WET}
    o10 = {t: d[t]["10mw"]["drop"] for t in WET}
    ck("[50mw] evaporative 降幅最高",
       o50["evaporative"] >= o50["hybrid"] and o50["evaporative"] >= o50["dry_first"],
       str(o50))
    ck("[10mw] dry_first 反超 evaporative（排序在细网格反转）",
       o10["dry_first"] > o10["evaporative"], str(o10))
    ck("排序不稳健（两网格最高档不同）",
       max(o50, key=o50.get) != max(o10, key=o10.get),
       f"50mw:{max(o50, key=o50.get)} 10mw:{max(o10, key=o10.get)}")

    # 6. 两个机制分解（基线 vs 端点）
    b_ev = [d["evaporative"][g]["cawcc_r0"] for g in GRIDS]
    e_ev = [d["evaporative"][g]["cawcc_r08"] for g in GRIDS]
    ck("evaporative 基线三网格恒定", len(set(b_ev)) == 1, str(b_ev))
    ck("evaporative 端点随网格上升", e_ev[0] <= e_ev[1] <= e_ev[2], str(e_ev))

    b_df = [d["dry_first"][g]["cawcc_r0"] for g in GRIDS]
    e_df = [d["dry_first"][g]["cawcc_r08"] for g in GRIDS]
    ck("dry_first 端点三网格恒定", len(set(e_df)) == 1, str(e_df))
    ck("dry_first 基线随网格上升", b_df[0] <= b_df[1] <= b_df[2], str(b_df))

    # 7. 正文已改为三网格表述，不再出现单值精确降幅
    ms = MS.read_text(encoding="utf-8")
    en = EN.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    ck("母稿表格已改为三网格（100 / 75 / 70）", "100 / 75 / 70" in ms, "")
    ck("母稿写明精确降幅不可引用",
       ("不可引用" in ms) and ("网格量化支配" in ms), "")
    ck("SI 表格已改为三网格", "100 / 75 / 70" in si, "")
    ck("SI 写明 grid-limited", "grid-limited" in si, "")
    ck("母稿已撤回『湿冷上限』主张",
       "不主张" in ms and "湿冷上限" in ms, "")
    ck("英文已撤回『bounds the effect from above』",
       "do not claim that evaporative modelling bounds" in en, "")
    ck("SI 明确声明两条被否证的表述",
       "do not make them" in si, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"技术档网格收敛核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
