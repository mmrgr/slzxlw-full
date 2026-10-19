# -*- coding: utf-8 -*-
"""修正：CO 端 r=0.9 时纯物理瓶颈是 local_connection，不是 grid_connection。

两者同属"电气侧"，但具体约束不同：
  max_daily_average_grid_connection_ratio（日平均电网接网比）—— r≤0.8 时
  max_local_connection_ratio（本地接水连接比）—— r=0.9 时

正文写"CO 的物理瓶颈在电网（1500 MW）"在 r=0.9 这一格上不准确，应改为"电气侧约束"，
并说明 r=0.9 时具体是本地接网。SI 表格已按 r=0.9 行标注 −50 MW（1450→1400），与 local_connection 一致。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
G = HERE / "_verify_co_gap.py"
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"

# 1) 门禁断言放宽为"电气侧"
t = G.read_text(encoding="utf-8")
OLD = '''    ck("CO 纯物理瓶颈 = 电网",
       "grid" in str(co9[bc]), str(co9[bc]))'''
NEW = '''    ck("CO 纯物理瓶颈 = 电气侧（grid 或 local_connection）",
       ("grid" in str(co9[bc])) or ("local_connection" in str(co9[bc])), str(co9[bc]))'''
if OLD in t:
    G.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 门禁断言已放宽为电气侧")
else:
    print("门禁未匹配")

# 2) 正文修正
t = MS.read_text(encoding="utf-8")
OLD2 = "D-CO 的物理瓶颈在电网（1500 MW），**远晚于**政策约束的失效点（r=0.9 时约 650 MW），故政策约束轻易接管主导地位。"
NEW2 = "D-CO 的物理瓶颈在**电气侧**（r ≤ 0.8 时为日平均电网接网比，1500 MW；r=0.9 时转为本地接水连接比，1400 MW），**远晚于**政策约束的失效点（r=0.9 时约 650 MW），故政策约束轻易接管主导地位。"
if OLD2 in t:
    MS.write_text(t.replace(OLD2, NEW2, 1), encoding="utf-8")
    print("OK 母稿已修正为电气侧")
else:
    print("母稿未匹配，尝试备选")
    for cand in ("物理瓶颈在电网（1500 MW）", "D-CO 的物理瓶颈在电网"):
        if cand in t:
            print("  存在候选:", cand)

# 3) 英文修正
t = EN.read_text(encoding="utf-8")
OLD3 = "at the cool endpoint the physical bottleneck is grid connection at 1500 MW, far later than the policy constraint's failure point"
NEW3 = "at the cool endpoint the physical bottleneck is electrical (grid connection at 1500 MW up to $r=0.8$, local connection at 1400 MW at $r=0.9$), far later than the policy constraint's failure point"
if OLD3 in t:
    EN.write_text(t.replace(OLD3, NEW3, 1), encoding="utf-8")
    print("OK 英文已修正为电气侧")
else:
    print("英文未匹配")
