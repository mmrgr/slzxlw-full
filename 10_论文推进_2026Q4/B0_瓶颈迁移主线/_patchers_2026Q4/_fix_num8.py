# -*- coding: utf-8 -*-
"""修正 §9.2 第 8 条的格式，使编号正则 ^(\\d+)\\. \\*\\* 仍可匹配。

问题：上一版写成 "8. ~~**干预从未...**~~"，删除线打断了 \\*\\* 前缀，
导致 _check_sync.py 的编号连续性检查读不到 8，报"缺号 8"。
修法：保持 "8. **" 前缀，把删除线放到标题内部或改为说明性措辞。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"

OLD = "8. ~~**干预从未在 50 MW 网格上重跑。**~~ **该缺口已于 2026-10-18 闭合。**"
NEW = ("8. **干预扫描已改在 50 MW 网格上重跑（原缺口已于 2026-10-18 闭合）。** "
       "~~旧版称\"干预从未在 50 MW 网格上重跑\"，该陈述已过时。~~ ")

t = MS.read_text(encoding="utf-8")
if OLD in t:
    t = t.replace(OLD, NEW, 1)
    MS.write_text(t, encoding="utf-8")
    print("OK 已修正第 8 条格式")
else:
    print("未匹配，打印当前第 8 条开头：")
    i = t.find("8. ")
    print(repr(t[i:i + 120]))

# 复检编号
import re
m = re.search(r"## 9 局限(.*?)(?=## 10)", t, flags=re.S)
nums = [int(x) for x in re.findall(r"^(\d+)\. \*\*", m.group(1), flags=re.M)]
print("编号连续:", nums == list(range(1, len(nums) + 1)), f"共 {len(nums)} 条")
