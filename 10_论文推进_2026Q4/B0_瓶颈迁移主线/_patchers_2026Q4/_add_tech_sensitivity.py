# -*- coding: utf-8 -*-
"""把技术档敏感性检验写入母稿、英文稿、SI。

【结果】
固定 1200 MW 的阈值型响应（r 0.5→0.8 外部取水增幅）：
  evaporative +6.478% / hybrid +6.472% / dry_first +7.851% / dry 不适用（取水恒 0）
纯物理 CAWCC 降幅（r=0 → r=0.8）：
  evaporative 1200→1100（−100）/ hybrid 1150→1100（−50）
  dry_first 1100→1050（−50）/ dry 1300→1300（0）

【三点必须写清】
1. 三个有冷却用水的档位**全部保留**阈值型响应 → 机制不依赖具体冷却技术。
2. 效应量随冷却水强度下降而减小（−100 → −50 → 0）→ 本文用 evaporative 的"偏保守"从此**有定量内容**：
   若全市一半设施为 hybrid，则实际降幅约为 −50 MW 而非 −100 MW。
3. **dry 档必须单独说明**：其外部取水恒为 0，即机制"不适用"而非"稳健"。若不说明，
   "dry 档降幅 0"会被误读为机制在该档下消失。
4. dry_first 的 CoC=6（非 5），故 r*=0.3972（更低），跨阈值更早、增幅更大（7.851% > 6.478%）。
   这是 r* 对 CoC 敏感的又一个具体体现。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------------- 母稿：§5.8.6 之后追加 5.8.7 ----------------
MS_ANCHOR = "## 5.9 结果 6：判据在一个真实城市的应用"
MS_NEW = """### 5.8.7 冷却技术档的敏感性：机制不依赖技术，但效应量依赖

§5.9.2d 的外部对照显示，Santa Clara 并非所有数据中心都用湿冷（Bowers 项目为风冷+绝热，WUE 比湿冷低约 315 倍）。此前本文主情景在两个端点上**统一采用 `evaporative`**，并声称这使水侧结论"偏保守"。**该说法此前未经检验**，本轮补做。

在 D-HA 端点上切换 4 个冷却技术档（保持其余参数不变）：

| 技术档 | WUE (L/kWh) | `CoC_design` | 固定 1200 MW 下 r 0.5→0.8 取水增幅 | 纯物理 CAWCC r=0→0.8 |
|---|---:|---:|---:|---|
| `evaporative` | 2.125 | 5.0 | **+6.478%** | 1200 → 1100（**−100 MW**） |
| `hybrid` | 0.558 | 5.0 | **+6.472%** | 1150 → 1100（**−50 MW**） |
| `dry_first` | 0.327 | **6.0** | **+7.851%** | 1100 → 1050（**−50 MW**） |
| `dry` | 0.000 | 5.0 | **不适用**（外部取水恒 0） | 1300 → 1300（**0**） |

**四点必须写清**：

1. **阈值型响应不依赖冷却技术。** 三个有冷却用水的档位**全部保留**该响应（+6.47%～+7.85%），故 §5.7 的机制结论**不是湿冷假设的产物**。
2. **效应量随冷却水强度单调下降。** 降幅 −100 → −50 → −50 → 0 MW。这给"偏保守"这一说法提供了**定量内容**：若全市有一半设施为 `hybrid`，本文的 −100 MW 实际应约为 **−50 MW**。
3. **`dry` 档必须单独说明。** 其外部取水恒为 0，即 r* 机制**不适用**、而非"稳健"。若不点明，"dry 档降幅为 0"会被误读为机制在该档下失效。
4. **`dry_first` 的增幅更大（+7.851%）是因为它的 `CoC_design` = 6.0，故 `r*` = 0.3972 而非 0.5532。** 更低的 `r*` 意味着更早跨阈值、更大的越界幅度。这再次体现 `r*` 对 `CoC_design` 的高弹性（−1.69）。

> **对外部有效性的含义**：本文的机制结论对冷却技术**稳健**，但**效应量是条件于技术构成的**。由于真实城市的技术构成未知（本城仅有一个项目的公开设计值），本文报告 −100 MW 时应理解为**湿冷上限情形**，真实值可能更小。这一点已并入 §9.6 的局限。

""" + MS_ANCHOR

# ---------------- 英文 §3.3 末 ----------------
EN_ANCHOR = "The mechanism is thus stated completely as two conditions, $r>r^{*}$ and a water-side bottleneck."
EN_ADD = (" Cooling-technology sensitivity tests this. Switching the water-scarce endpoint among four "
          "tiers while holding everything else fixed gives make-up increases of +6.478% "
          "(`evaporative`), +6.472% (`hybrid`) and +7.851% (`dry_first`) for $r$ rising from 0.5 to "
          "0.8, so the threshold-typed response survives every tier that has cooling water at all; "
          "the `dry` tier draws none and the mechanism simply does not apply there. The capacity "
          "response does scale with the technology: the physical CAWCC drop is −100, −50, −50 and 0 "
          "MW across those tiers, so modelling every facility as evaporatively cooled yields the "
          "upper bound of the effect, and a city with half its facilities on hybrid cooling would "
          "show roughly −50 MW rather than −100 MW. The `dry_first` tier's larger increase is "
          "explained by its design cycles of concentration of 6.0, which lowers $r^{*}$ to 0.3972 "
          "and so crosses the threshold earlier (SI S7.14).")

# ---------------- SI 新增 S7.14 ----------------
SI_ANCHOR = "## S8 Data-reliability warnings for reviewers"
SI_NEW = """### S7.14 Cooling-technology sensitivity

The main text models both endpoints with a single evaporative cooling tier. Section S7.13 shows
that Santa Clara is not uniformly evaporatively cooled: one documented project uses air-cooled
chillers with adiabatic assistance at a WUE some 315 times below the evaporative tier. The claim
that a uniform evaporative assumption is conservative had not been tested. This section tests it.

Switching the water-scarce endpoint among four tiers while holding all other parameters fixed:

| Tier | WUE (L kWh⁻¹) | $\\mathrm{CoC}_d$ | Make-up increase, $r$ 0.5→0.8 at 1200 MW | Physical CAWCC, $r$=0→0.8 |
|---|---:|---:|---:|---|
| `evaporative` | 2.125 | 5.0 | **+6.478%** | 1200 → 1100 (**−100 MW**) |
| `hybrid` | 0.558 | 5.0 | **+6.472%** | 1150 → 1100 (**−50 MW**) |
| `dry_first` | 0.327 | **6.0** | **+7.851%** | 1100 → 1050 (**−50 MW**) |
| `dry` | 0.000 | 5.0 | **not applicable** (external withdrawal identically zero) | 1300 → 1300 (**0**) |

Four readings. First, the threshold-typed response does not depend on the cooling technology: all
three tiers that use any cooling water retain it, between +6.47% and +7.85%. The mechanism result
of the main text is therefore not an artefact of the evaporative assumption. Second, the effect
size does scale with water intensity, falling −100 → −50 → −50 → 0 MW. This gives quantitative
content to the conservatism claim: a city with half its facilities on hybrid cooling would show
roughly −50 MW rather than −100 MW. Third, the `dry` tier must be described separately, because its
external withdrawal is identically zero and the criterion is inapplicable rather than robust — left
unsaid, the zero capacity drop would read as the mechanism failing there. Fourth, `dry_first`
produces a larger make-up increase because its design cycles of concentration are 6.0 rather than
5.0, which lowers $r^{*}$ to 0.3972 and so crosses the threshold earlier; this is another concrete
instance of the high elasticity of $r^{*}$ with respect to $\\mathrm{CoC}_d$ (−1.69).

The implication for external validity is that the mechanism conclusion is robust to cooling
technology while the effect size is conditional on it. Because the technology mix of a real city is
unknown — only one project's design value is public here — the −100 MW figure should be read as the
evaporatively-cooled upper bound.

**Evidence:** `_tech_sensitivity.json`, `_verify_tech_sensitivity.py` (11/11).

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
if MS_ANCHOR in t and "5.8.7" not in t:
    MS.write_text(t.replace(MS_ANCHOR, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿 §5.8.7")
    n += 1
else:
    print("母稿锚点问题")

t = EN.read_text(encoding="utf-8")
if EN_ANCHOR in t and "Cooling-technology sensitivity tests this" not in t:
    EN.write_text(t.replace(EN_ANCHOR, EN_ANCHOR + EN_ADD, 1), encoding="utf-8")
    print("OK 英文 §3.3")
    n += 1
else:
    print("英文锚点问题")

t = SI.read_text(encoding="utf-8")
if SI_ANCHOR in t and "S7.14" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S7.14")
    n += 1
else:
    print("SI 锚点问题")

print(f"完成 {n}/3")
