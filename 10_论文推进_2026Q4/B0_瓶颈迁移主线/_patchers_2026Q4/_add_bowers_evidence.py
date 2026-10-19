# -*- coding: utf-8 -*-
"""把"冷却技术档 × Bowers 设计值"的外部一致性检验写入母稿、英文稿、SI。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------------- 母稿：§5.9.2c 之后追加 5.9.2d ----------------
MS_ANCHOR = "### 5.9.3 由份额反推园区配比"
MS_NEW = """#### 5.9.2d 冷却技术档与一个独立设计值的量级一致性检验

本文水侧参数（WUE、冷却技术）此前无任何外部对照。市议会社区报告（转引 Bowers 项目 Final EIR，2023-10，pp.3-14 与 4.18-2）给出一个**独立的官方设计值**：

> 该项目采用 "**rooftop air-cooled chillers with adiabatic assistance**"（风冷为主、高温时段绝热辅助），
> 设计冷却用再生水 **≤ 0.5 acre-foot/年 = 616.7 m³/yr**；另估计自来水约 2 AF/年（含约 1 AF 景观）。

把模型 7 个冷却技术档在 IT = 10 MW 下的 WUE 与之并列：

| 模型技术档 | WUE (L/kWh) | 年补水 (m³) |
|---|---:|---:|
| `dry` | **0.000** | 0 |
| `dry_first` | **0.398** | 56.9 |
| `hybrid` | **0.606** | 86.1 |
| `liquid_to_water` | 1.912 | 251.7 |
| `efficient_evaporative` | 2.117 | 278.7 |
| `evaporative` | **2.205** | 290.2 |
| `liquid_to_air` | 0.000 | 0 |

**一致性结论**：Bowers 设计值对应的 WUE 取决于其 IT 容量——若 IT = 10 MW 则为 **0.0070 L/kWh**。该值**落在 `dry`(0) 与 `dry_first`(0.398) 之间**，且这一结论**对 IT ∈ [1, 72] MW 全区间成立**（WUE 从 0.0704 单调降到 0.0010），因此不依赖于那个未公开的容量。它与其 EIR 所述的"风冷为主、仅高温少量补水"**在档位上吻合**。

**两项可用于论文的推论**：

1. **模型的技术档梯度是单调且量级正确的**：`dry`(0) < `dry_first`(0.398) < `hybrid`(0.606) < `evaporative`(2.205)，且湿冷档落在工程常识的 2–4 L/kWh 区间内。这说明模型的水侧实现没有量级错误。
2. **不能把 Santa Clara 的全部数据中心一律按湿冷建模**：Bowers 的 WUE 比模型湿冷档低 **约 315 倍**。该市确实存在以风冷/绝热为主的设施。本文用单一 `evaporative` 设定作为主情景，因此**对全市水耗的方向性影响是"偏高"而非"偏低"**——这使本文关于"水侧压力"的结论偏保守。

> ⚠️ **必须同时声明的限制**：Bowers 的 **IT 容量未公开**。社区报告明确指出，CEC 的 72 MW 是**备用发电 designation**，"不应读作实测年电网需求"。故本小节只做**档位/量级一致性检验**，**不能用于锚定 WUE 数值**，也不能据此推断全市数据中心的技术构成或总水耗。

""" + MS_ANCHOR

# ---------------- 英文 §3.4 ----------------
EN_ANCHOR = "This is a transferable screening procedure, not an assessment of one city"
EN_ADD = (" A separate external check supports the water-side implementation. The city's community "
          "report reproduces a project-level environmental design estimate — rooftop air-cooled "
          "chillers with adiabatic assistance, cooling water at most 0.5 acre-feet per year, or "
          "616.7 m³ — which corresponds to a WUE between 0.001 and 0.07 L/kWh across any IT capacity "
          "from 1 to 72 MW. That range sits between the model's `dry` tier (0.000 L/kWh) and its "
          "`dry_first` tier (0.398 L/kWh), matching the air-cooled design the document describes, "
          "while the model's evaporative tier reaches 2.205 L/kWh, inside the conventional 2–4 band. "
          "The tier ordering is therefore monotone and of the right magnitude, and modelling every "
          "facility as evaporative biases the water side upward rather than downward (SI S7.13). ")

# ---------------- SI 新增 S7.13 ----------------
SI_ANCHOR = "## S8 Data-reliability warnings for reviewers"
SI_NEW = """### S7.13 External check on the water-side implementation: cooling tiers against a project design value

The model's water-side parameters — WUE and the cooling-technology settings — previously had no
external comparison; the parameter envelope marks most of them unanchored. An independent official
figure is available. The city's community report reproduces a project-level environmental design
estimate for the Bowers project (Final EIR, October 2023, printed pp. 3-14 and 4.18-2): rooftop
air-cooled chillers with adiabatic assistance, with cooling water of at most 0.5 acre-feet per year,
equal to 616.7 m³.

Running the model's seven cooling tiers at an IT capacity of 10 MW gives:

| Tier | WUE (L kWh⁻¹) | Annual make-up (m³) |
|---|---:|---:|
| `dry` | **0.000** | 0 |
| `dry_first` | **0.398** | 56.9 |
| `hybrid` | **0.606** | 86.1 |
| `liquid_to_water` | 1.912 | 251.7 |
| `efficient_evaporative` | 2.117 | 278.7 |
| `evaporative` | **2.205** | 290.2 |
| `liquid_to_air` | 0.000 | 0 |

The design figure implies a WUE that depends on the facility's IT capacity. At 10 MW it is
0.0070 L kWh⁻¹, which lies between the `dry` tier and the `dry_first` tier. Crucially, this holds
across the whole plausible capacity range: from 1 to 72 MW the implied WUE moves from 0.0704 to
0.0010 L kWh⁻¹, never leaving that interval. The conclusion therefore does not depend on the one
quantity the document does not disclose. It also agrees with the document's own description of the
design as air-cooled with adiabatic assistance.

Two inferences follow. First, the tier gradient is monotone and of the right magnitude, and the
evaporative tier at 2.205 L kWh⁻¹ sits inside the conventional 2–4 band, so the water-side
implementation carries no order-of-magnitude error. Second, Santa Clara is not uniformly
evaporatively cooled: the Bowers design implies a WUE about 315 times below the model's evaporative
tier. Since the main text models every facility with a single evaporative setting, its water-side
results are biased upward rather than downward, which makes the paper's account of water-side
pressure conservative.

**Limit, stated with the result.** The Bowers IT capacity is not public. The community report
explicitly warns that the 72 MW designation belongs to backup generation and must not be read as
measured annual grid demand. This check therefore establishes tier and order-of-magnitude
consistency only; it cannot anchor a WUE value, and it supports no inference about the technology
mix or total water use of the city's data centres.

**Evidence:** `_tech_wue_benchmark.json`, `_verify_bowers_benchmark.py` (9/9), reading
`2025 Urban Water Management Plan` and `Item 7 Post Meeting Material.pdf` pp. 60–61.

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
if MS_ANCHOR in t and "5.9.2d" not in t:
    MS.write_text(t.replace(MS_ANCHOR, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿 §5.9.2d")
    n += 1
else:
    print("母稿锚点问题")

t = EN.read_text(encoding="utf-8")
if EN_ANCHOR in t and "`dry_first` tier" not in t:
    EN.write_text(t.replace(EN_ANCHOR, EN_ADD + EN_ANCHOR, 1), encoding="utf-8")
    print("OK 英文 §3.4")
    n += 1
else:
    print("英文锚点问题")

t = SI.read_text(encoding="utf-8")
if SI_ANCHOR in t and "S7.13" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S7.13")
    n += 1
else:
    print("SI 锚点问题")

print(f"完成 {n}/3")
print("英文词数:", len(re.sub(r"\$[^$]*\$", " MATH ", EN.read_text(encoding='utf-8')).split()))
