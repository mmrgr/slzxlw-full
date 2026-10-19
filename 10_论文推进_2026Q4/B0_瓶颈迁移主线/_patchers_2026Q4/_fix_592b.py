# -*- coding: utf-8 -*-
"""删除母稿 5.9.2b 中与新证据等级矛盾的旧解释，只保留转录取值表。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"

OLD = """#### 5.9.2b 份额的原始呈现（转录）

Santa Clara 市议会 2026-10-06 staff presentation（RTC #26-1037）第 27 页给出两张饼图：

| 图 | Data Centers | Santa Clara excl. Data Centers |
|---|---|---|
| **Recycled Water** | **26%** | 74% |
| **Potable Water** | **6%** | 94% |

> ⚠️ **两个技术限定必须随数据出现**：
> 1. **这两个百分比只存在于图形中，PDF 文本层没有**——我们是通过渲染该页为 200 dpi 图像后读图获得的。任何纯文本抓取都拿不到。
> 2. **两个分母不同，不可加总。** 随后的第三方证据台账明确警告："Separate water-system denominators; **not 32% of combined use**. Supporting period and volumes need disclosure."
"""

NEW = """#### 5.9.2b 转录所得的份额（供计算使用）

| 指标 | 数据中心 | 全市其余 | 分母 |
|---|---:|---:|---|
| 再生水 | **26%** | 74% | 全市再生水用量 |
| 自来水 | **6%** | 94% | 全市自来水用量 |

> 上表两个百分比的分母不同，**不可相加得到 32%**。其证据等级见 5.9.2 的来源链说明：转录自社区报告，未经市府原件独立复核。
"""

t = MS.read_text(encoding="utf-8")
if OLD in t:
    MS.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 已删除旧解释")
else:
    print("未匹配")
