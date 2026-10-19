# -*- coding: utf-8 -*-
"""在母稿 §9.7 新增第 45 条：k* 的份额比依赖是一项新的、独立的限制。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"

OLD = ("44. **`r*` 本身的参数不确定性会改变判定。** `L` 与 `CoC_design` 各 ±10% 使 `r*` 移动约 0.05–0.09。"
       "若 `r*` 实际约为 0.51，则 Santa Clara 的 r=0.499 已接近甚至越过。"
       "**\"未越过\"不是一个稳健的结论，而是一个在标称参数下的结论。**")

NEW = OLD + """

45. **`k* = 3.50` 强烈依赖份额比 `ρ = α/β`，不可作为普适常数引用。** `k* = (1/r* − 1)/ρ`；本文的 3.50 条件于 Santa Clara 的 `ρ = 6%/26% = 0.2308`。`ρ` 从 0.10 变到 1.0，`k*` 由 8.08 降到 0.81，加州 169 系统中符合边界的从 57 个降到 3 个（详见 §5.9.9）。**只报 `k* = 3.50` 而不报 `ρ`，会把一个"需代入两城市自身份额的问题"误读成"一个固定阈值"。** 本文同时报出保守边界（`ρ = 1` 时 `k* = 0.81`，仍有 3 个系统低于它），以免读者把 Santa Clara 口径当作通用口径。
    **同一条也适用于 `r*`**：`k*` 对 `r*` 的敏感性同样显著（`ρ = 0.2308` 时，`r*` 由 0.50 到 0.61 使 `k*` 由 4.33 降到 2.77），故第 44 条的参数不确定性会经由 `r*` 传递到 `k*`。

46. **份额本身只有一城数据。** `ρ = 6%/26%` 来自 Santa Clara 市府 2026-10-06 陈述材料（RTC #26-1037）第 27 页的两张饼图，**本文没有任何第二座城市的同类份额数据**。因此 §5.9.8 的 169 系统分布只能回答"若某城市出现同等份额的数据中心会怎样"，不能回答"这些城市实际会不会出现"。这一条比第 43 条的样本选择偏差更根本：缺的不是样本量，而是**被代入的那个量本身**。"""

t = MS.read_text(encoding="utf-8")
if OLD not in t:
    print("未匹配")
else:
    t = t.replace(OLD, NEW, 1)
    MS.write_text(t, encoding="utf-8")
    print(f"OK 已新增第 45、46 条；母稿 {len(t)} 字符")

import re
m = re.search(r"## 9 局限(.*?)(?=## 10)", t, flags=re.S)
nums = [int(x) for x in re.findall(r"^(\d+)\. \*\*", m.group(1), flags=re.M)]
print("编号连续:", nums == list(range(1, len(nums) + 1)), f"共 {len(nums)} 条")
