# -*- coding: utf-8 -*-
"""修正 §9.6 第 29、34 条中残留的"5 物种"描述，与 §3.1（实际 2 物种）一致。

历史：第九轮只改了 §5.7.2 的注，未改 §9.6 第 29/34 条，导致同一文档内
"模型追踪 2 个物种"（§3.1）与"模型追踪 5 个物种"（§9.6）并存。

事实（已在 src/ 与 project.json 核实）：
  water_quality_limits = {TDS: 2200, chloride: 500}
  potable   quality = {TDS: 180, chloride: 35}
  reclaimed quality = {TDS: 650, chloride: 130}
  → 仅 2 个物种，且两者都有完整源水质与限值 ⇒ 多物种取紧在本配置下是完整的。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"

OLD_29 = """    - 模型追踪 5 个物种（TDS、氯化物、硬度、碱度、硅），**其余 3 个物种在当前项目文件中只有限值或只有部分源水质，无法计算其 `r*`**。若它们的临界值更低，真实 `r*` 会更低、反噬更早开始。**这是本文数值的一个未闭合边界。**
    - 通用判据形式应为 `r* = min over s of [(L_s/CoC_design − C_p,s)/(C_r,s − C_p,s)]`。本文给出了两物种的完整计算，其余 3 个物种留待水质参数补齐后完成。"""

NEW_29 = """    - **本参数集只配置了这 2 个物种**（`water_quality_limits = {TDS: 2200, chloride: 500}`，两类源水亦只给 TDS 与氯化物），且两者都有完整的限值与源水质。因此**在本配置下多物种取紧是完整的，不存在"未计算的第 3 个物种"**（与 §3.1 的事实核对一致）。
    - 通用判据形式为 `r* = min over s of [(L_s/CoC_design − C_p,s)/(C_r,s − C_p,s)]`。**若将来扩展物种集合**（如硬度、碱度、硅），可能得到更低的 `r*`，届时须重新计算；但在现有配置下 `r* = min(0.5532, 0.6842) = 0.5532` 已是完备结果。"""

OLD_34 = """34. **多物种取紧后分类边界可能移动。** 本文只用 TDS 做判据（见第 29 条）。若引入氯化物（其 `r*` 更高，0.6842），TDS 仍是最紧者，故当前分类不变；但硬度、碱度、硅的源水质参数缺失，无法排除更紧的约束存在。"""

NEW_34 = """34. **分类边界随物种集合而定，但在当前配置下已取紧。** 本文对两个已配置物种（TDS 与氯化物）都计算了 `r*`：TDS 为 0.5532、氯化物为 0.6842，取紧者为 TDS，故当前分类以 0.5532 为准。**本配置中不存在第三个物种**（见第 29 条与 §3.1），故"无法排除更紧约束"这一表述在此处不适用；若将来补入硬度、碱度、硅，须重算并可能下移边界。"""

t = MS.read_text(encoding="utf-8")
n = 0
for old, new, tag in ((OLD_29, NEW_29, "第 29 条"), (OLD_34, NEW_34, "第 34 条")):
    if old in t:
        t = t.replace(old, new, 1)
        n += 1
        print(f"OK {tag}")
    else:
        print(f"未匹配 {tag}")
MS.write_text(t, encoding="utf-8")
print(f"完成 {n}/2")

# 复检
import re
left = [ln for ln in t.split("\n") if "5 个物种" in ln and "早期项目文档曾描述" not in ln]
print(f"\n剩余未加更正的『5 个物种』行数: {len(left)}")
for ln in left:
    print("  ", ln[:120])
