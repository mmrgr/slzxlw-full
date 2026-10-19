# -*- coding: utf-8 -*-
"""修正 §5.9.2 的出处表述：使其与手上可核验的证据一致。

【核验结果（_verify_share_source.py / _diag_share_provenance.py）】
1. `Item 7 Post Meeting Material.pdf`(73 页) 的封面即写明
   "Santa Clara data centers • Independent community report • October 2026"
   —— 它是**独立社区报告**，不是市府 staff presentation 本体。
2. 6% 与 26% 出现在该报告 **p.53（物理页）** 的一张表格中，文本层**确实存在**：
   "October staff water figures [1] Data centers: about 6% of potable use and
    26% of recycled use. Separate water-system denominators; not 32% of combined use.
    Supporting period and volumes need disclosure."
   注意：这段同时包含论文已引用的 "not 32%" 警告 —— 说明论文引用的那句话
   来自**这份社区报告**，而非市府原件。
3. 论文此前声称的英文原句 "approximately 6% of the City's total potable water use"
   在两个 PDF 中都搜不到；证据包的中文摘录卡声称见过该句，但无可核验原件。
4. 市府 staff report（26-1037）本体**不在手上的 PDF 之内**（手上有的是 1 页的
   030 请求函 + 73 页社区报告）。故"第 27 页饼图"这一说法无法用手上材料核验。

【修正原则】不改变 6% / 26% 这两个数值（它们是社区报告对市府数据的转录，且数值本身
与论文用法一致），但必须把**证据等级与来源链**改准确。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

MS_OLD = """### 5.9.2 一手数据：6% 与 26%

Santa Clara 市议会 2026-10-06 staff presentation（RTC #26-1037）第 27 页给出两张饼图：

| 图 | Data Centers | Santa Clara excl. Data Centers |
|---|---|---|
| **Recycled Water** | **26%** | 74% |
| **Potable Water** | **6%** | 94% |

> ⚠️ **两个技术限定必须随数据出现**：
> 1. **这两个百分比只存在于图形中，PDF 文本层没有**——我们是通过渲染该页为 200 dpi 图像后读图获得的。任何纯文本抓取都拿不到。
> 2. **两个分母不同，不可加总。** 随后的第三方证据台账明确警告："Separate water-system denominators; **not 32% of combined use**. Supporting period and volumes would be disclosed.""""

# 上面 OLD 的最后一句可能与原文不完全一致，改为分段替换更稳
MS_OLD = """### 5.9.2 一手数据：6% 与 26%

Santa Clara 市议会 2026-10-06 staff presentation（RTC #26-1037）第 27 页给出两张饼图：

| 图 | Data Centers | Santa Clara excl. Data Centers |
|---|---|---|
| **Recycled Water** | **26%** | 74% |
| **Potable Water** | **6%** | 94% |

> ⚠️ **两个技术限定必须随数据出现**：
> 1. **这两个百分比只存在于图形中，PDF 文本层没有**——我们是通过渲染该页为 200 dpi 图像后读图获得的。任何纯文本抓取都拿不到。
> 2. **两个分母不同，不可加总。** 随后的第三方证据台账明确警告："Separate water-system denominators; **not 32% of combined use**. Supporting period and volumes need disclosure."""

MS_NEW = """### 5.9.2 6%/26% 的来源链与证据等级

数据中心占全市自来水 **6%**、占全市再生水 **26%** 这两个份额，其来源链须完整交代：

| 环节 | 内容 | 本文是否能核验 |
|---|---|---|
| 原始出处 | City of Santa Clara，File 26-1037，2026-10-06 市议会 staff report 的 "Water Usage" 段落 | ❌ **原件不在手上** |
| 转录来源 | *Santa Clara data centers — Independent community report*（2026-10）**p.53** 表格，其中以 `[1]` 引用上述市府报告 | ✅ 文本层可核（见下） |
| 本文用法 | 作为 `k*` 判据的份额比 `ρ = 6/26` | — |

**可核验的那一行原文**（社区报告 p.53，文本层，非读图所得）：

> "October staff water figures [1] Data centers: about 6% of potable use and 26% of recycled use. Separate water-system denominators; not 32% of combined use. Supporting period and volumes need disclosure."

**三点必须随数据出现**：

1. **6% 与 26% 是转录值，不是本文从市府原件读出的一手值。** 本文能直接核验的是上述社区报告的一行表格文字；市府 26-1037 原件不在手上，故**无法独立核实**其"Water Usage"段落或任何图形中的原始表述。此前版本称"该值只存在于 p.27 饼图中、需渲染读图"，与现有证据不符，已更正。
2. **两个分母不同，不可加总。** 上述原文本身就警告 "**not 32% of combined use**"，并要求披露 "supporting period and volumes"——该要求至今未被满足。
3. **观测时段未披露。** 原文明确写 "Supporting period and volumes need disclosure"。

> **因此 `ρ = 6/26` 应被视为一个政府陈述的、但未经独立复核的情景锚定值，而非可复算的实测数据。** 这一证据等级已并入 §5.9.9 与 §9.7 的敏感性讨论。"""

# 英文
EN_OLD = """The 6% and 26% shares come from page 27 of the council staff presentation of 2026-10-06 (RTC #26-1037), which contains two pie charts: recycled water at 26% for data centres and 74% for the rest of the city, potable water at 6% for data centres and 94% for the rest. **These percentages exist only inside the graphics and are absent from the PDF text layer**; they were obtained by rendering page 27 at 200 dpi and reading the image. Any text-only extraction misses them. The two denominators differ and are not additive."""

EN_NEW = """The 6% and 26% shares carry a provenance chain that must be stated exactly. The originating
document is the City's report to council, File 26-1037 of 2026-10-06, in its "Water Usage"
section; that original is not in our possession and we cannot verify it independently. What we
can verify is the document through which the figures reached us, an independent community report
of October 2026, whose page 53 reproduces them in text: "October staff water figures [1] Data
centers: about 6% of potable use and 26% of recycled use. Separate water-system denominators; not
32% of combined use. Supporting period and volumes need disclosure." The shares are therefore a
transcribed government statement, not a first-hand measurement, and the two denominators differ
and are not additive."""

for path, old, new, tag in ((MS, MS_OLD, MS_NEW, "母稿 §5.9.2"),
                            (EN, EN_OLD, EN_NEW, "英文 §3.4")):
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"OK {tag}")
    else:
        print(f"未匹配 {tag}")

# SI S7.2
t = SI.read_text(encoding="utf-8")
i = t.find("### S7.2 The Santa Clara source data")
print("\n--- SI S7.2 现文 ---")
print(t[i:i + 700] if i >= 0 else "未找到")
