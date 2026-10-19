# -*- coding: utf-8 -*-
"""修正三处 6%/26% 的出处表述（母稿 §5.9.2、英文 §3.4、SI S7.2）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 英文 & SI 共用的旧段 ----------
EN_OLD = """The 6% and 26% shares come from page 27 of the council staff presentation of 2026-10-06 (RTC #26-1037), which contains two pie charts: recycled water at 26% for data centres and 74% for the rest of the city, potable water at 6% for data centres and 94% for the rest. **These percentages exist only inside the graphics and are absent from the PDF text layer**; they were obtained by rendering page 27 at 200 dpi and reading the image. Any text-only extraction misses them. The two denominators differ and are not additive."""

EN_NEW = """The 6% and 26% shares carry a provenance chain that must be stated exactly. The originating
document is the City's report to council, File 26-1037 of 2026-10-06, in its "Water Usage"
section; that original is not in our possession and we could not verify it independently. What
we can verify is the document through which the figures reached us, an independent community
report of October 2026, whose page 53 reproduces them in text: "October staff water figures [1]
Data centers: about 6% of potable use and 26% of recycled use. Separate water-system
denominators; not 32% of combined use. Supporting period and volumes need disclosure." The
shares are therefore a transcribed government statement, not a first-hand measurement, and the
two denominators differ and are not additive."""

SI_OLD = EN_OLD  # SI 同段
SI_NEW = """The 6% and 26% shares carry a provenance chain that must be stated exactly, and it is weaker
than a first-hand reading.

| Link | Content | Verifiable here |
|---|---|---|
| Origin | City of Santa Clara, File 26-1037, 2026-10-06, "Water Usage" section | **no** — original not held |
| Transcription | *Santa Clara data centers — Independent community report*, October 2026, **p.53** table, citing the above as `[1]` | yes — present in the text layer |
| Use here | share ratio $\\rho=6/26$ for the $k^{*}$ screen | — |

The verifiable line (p.53, text layer, not read from a graphic) is:

> "October staff water figures [1] Data centers: about 6% of potable use and 26% of recycled use.
> Separate water-system denominators; not 32% of combined use. Supporting period and volumes need
> disclosure."

Three qualifications follow. First, the shares are a **transcribed government statement rather
than a first-hand measurement**: we hold the community report, not the City's original, so we
cannot independently confirm its "Water Usage" section or any graphic in it. An earlier version
of this manuscript described the figures as existing only inside two pie charts on page 27 and as
recoverable only by rendering that page at 200 dpi; the evidence available to us does not support
that description, and it has been corrected. Second, the two denominators differ and are not
additive, as the source itself warns ("not 32% of combined use"). Third, the reporting period is
undisclosed, again as the source itself states.

$\\rho=6/26$ should therefore be read as a **government-stated but independently unverified
scenario anchor**, not as reproducible measurement. That evidential grade is carried into the
sensitivity analysis of S7.7 and the limitation at item 40."""

# ---------- 母稿 ----------
MS_OLD = """### 5.9.2 一手数据：6% 与 26%"""

MS_NEW = """### 5.9.2 6%/26% 的来源链与证据等级

数据中心占全市自来水 **6%**、占全市再生水 **26%** 这两个份额，其来源链须完整交代：

| 环节 | 内容 | 本文能否核验 |
|---|---|---|
| 原始出处 | City of Santa Clara，File 26-1037，2026-10-06 市议会 staff report 的 "Water Usage" 段落 | ❌ **原件不在手上** |
| 转录来源 | *Santa Clara data centers — Independent community report*（2026-10）**p.53** 表格，以 `[1]` 引用上述市府报告 | ✅ 文本层可核（见下） |
| 本文用法 | `k*` 判据的份额比 `ρ = 6/26` | — |

**可核验的那一行原文**（社区报告 p.53，**文本层**，非读图所得）：

> "October staff water figures [1] Data centers: about 6% of potable use and 26% of recycled use. Separate water-system denominators; not 32% of combined use. Supporting period and volumes need disclosure."

**三点必须随数据出现**：

1. **6%/26% 是转录值，不是本文从市府原件读出的一手值。** 本文能直接核验的是上述社区报告的一行表格文字；市府 26-1037 原件不在手上，故**无法独立核实**其 "Water Usage" 段落或任何图形中的原始表述。此前版本称"该值只存在于 p.27 饼图中、须渲染 200 dpi 读图"，**与现有证据不符，已更正**。
2. **两个分母不同，不可加总。** 原文本身即警告 "**not 32% of combined use**"。
3. **观测时段未披露。** 原文明确写 "Supporting period and volumes need disclosure"。

> **因此 `ρ = 6/26` 应视为一个政府陈述的、但未经独立复核的情景锚定值，而非可复算的实测数据。** 该证据等级已并入 §5.9.9 的敏感性与 §9.7 的局限。

#### 5.9.2b 份额的原始呈现（转录）"""

n = 0
for path, old, new, tag in ((MS, MS_OLD, MS_NEW, "母稿 §5.9.2"),
                            (EN, EN_OLD, EN_NEW, "英文 §3.4"),
                            (SI, SI_OLD, SI_NEW, "SI S7.2")):
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"OK {tag}")
        n += 1
    else:
        print(f"未匹配 {tag}")
print(f"完成 {n}/3")
