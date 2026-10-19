# -*- coding: utf-8 -*-
"""更新技术档网格门禁：删除已被推翻的"排序稳健"断言，改为断言"排序在细网格反转"。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
G = HERE / "_verify_tech_grid.py"

t = G.read_text(encoding="utf-8")

OLD = """    # 5. 排序保持
    for g in GRIDS:
        order = {t: d[t][g]["drop"] for t in WET}
        ck(f"[{g}] evaporative 降幅 ≥ hybrid 与 dry_first",
           order["evaporative"] >= order["hybrid"]
           and order["evaporative"] >= order["dry_first"], str(order))"""

NEW = """    # 5. 排序：50 MW 下 evaporative 最高，但 10 MW 下被 dry_first 反超
    o50 = {t: d[t]["50mw"]["drop"] for t in WET}
    o10 = {t: d[t]["10mw"]["drop"] for t in WET}
    ck("[50mw] evaporative 降幅最高",
       o50["evaporative"] >= o50["hybrid"] and o50["evaporative"] >= o50["dry_first"],
       str(o50))
    ck("[10mw] dry_first 反超 evaporative（排序在细网格反转）",
       o10["dry_first"] > o10["evaporative"], str(o10))
    ck("排序不稳健（两网格最高档不同）",
       max(o50, key=o50.get) != max(o10, key=o10.get),
       f"50mw:{max(o50, key=o50.get)} 10mw:{max(o10, key=o10.get)}")"""

if OLD in t:
    t = t.replace(OLD, NEW, 1)
    print("OK 已替换排序断言")
else:
    print("未匹配排序断言")

# 追加正文断言：不得再出现"效应上限"
OLD2 = '''    ck("SI 写明 grid-limited", "grid-limited" in si, "")'''
NEW2 = '''    ck("SI 写明 grid-limited", "grid-limited" in si, "")
    ck("母稿已撤回『湿冷上限』主张",
       "不主张" in ms and "湿冷上限" in ms, "")
    ck("英文已撤回『bounds the effect from above』",
       "do not claim that evaporative modelling bounds" in en, "")
    ck("SI 明确声明两条被否证的表述",
       "do not make them" in si, "")'''
if OLD2 in t:
    t = t.replace(OLD2, NEW2, 1)
    print("OK 已追加正文断言")
else:
    print("未匹配正文断言")

# 需要 en 变量
if "en = EN.read_text" not in t:
    t = t.replace('    ms = MS.read_text(encoding="utf-8")',
                  '    ms = MS.read_text(encoding="utf-8")\n    en = EN.read_text(encoding="utf-8")', 1)
    t = t.replace('SI = HERE / "05_wr_supplementary_en.md"',
                  'SI = HERE / "05_wr_supplementary_en.md"\nEN = HERE / "04_wr_manuscript_en.md"', 1)
    print("OK 已补 en/EN 变量")

G.write_text(t, encoding="utf-8")
print("门禁已更新")
