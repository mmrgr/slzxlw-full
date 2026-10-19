# -*- coding: utf-8 -*-
"""把"高 r 段 CoC 按目标 r 计算、而实际交付不足"这一发现写入论文。

【完整证据】
D-HA，1100 MW，730 天：
  r=0.70: r_eff = 0.700000（0/730 天短缺），CoC_model = 4.3222 = CoC(目标)
  r=0.75: r_eff = 0.740217（262/730 短缺），CoC_model = 4.1315 = CoC(目标)，CoC(r_eff)=4.1674
  r=0.80: r_eff = 0.755645（620/730 短缺），3.9568 vs 4.1110（差 -0.154）
  r=0.85: r_eff = 0.751428（724/730 短缺），3.7964 vs 4.1263（差 -0.330）
  r=0.90: r_eff = 0.743997（724/730 短缺），3.6484 vs 4.1535（差 -0.505）

模型 CoC 与"按目标 r 解析"一致到 1e-15，说明：
  **模型按目标配比计算混合水质，而非按实际交付比例。**

【成因】
再生水产能限制（40 ML/d + 300 ML 储池）使高 r 时无法交付目标量，
但冷却塔的 CoC 计算只看设定的配比参数，不看当日实际交付。

【后果与限定】
1. r > 0.70 区段，模型**低估 CoC、高估水质反噬** → 该区段的效应量是**上界**；
2. 这解释了上一轮 CAWCC 解析式 22.86 MW 残差的来源：
   不是解析式错，而是模型 CoC 与有效配比不一致；
3. **r* = 0.5532 不受影响**：它位于 r_eff 完全达标（≤0.70）的区间内。

【与已有表述的关系】
论文 §3.3(b) 剔除 max_reuse_utilization 的理由是"300 ML 储池使日尺度处理速率达铭牌属正常调蓄"。
本发现表明：**产能限制的效应并未消失，而是以"r_eff 自回落 + CoC 仍按目标算"的方式进入了模型**。
这一点此前未被说明。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 母稿：§5.7.7 之后追加 5.7.8 ----------
MS_ANCHOR = "## 5.8 结果 5：瓶颈位置是政策的内生函数（纯物理口径）"
MS_NEW = """### 5.7.8 一处必须披露的模型内部张力：CoC 按目标配比计算，而非按实际交付

上一节把 CAWCC 解析式的 22.9 MW 残差归因于"缺一个随 r 增长的项"，当时未分解。本节给出分解结果。

在 D-HA、1100 MW、730 天驱动下，逐步提高目标替代率 r，并同时记录三个量：目标 r、实际交付比例 `r_eff`（`actual_reclaimed_fraction` 的日均）、以及模型输出的 CoC：

| r（目标） | `r_eff`（实际交付） | 未达标天数 | 模型 CoC | 按目标 r 解析 | 按 `r_eff` 解析 |
|---:|---:|---:|---:|---:|---:|
| 0.70 | 0.700000 | **0/730** | 4.3222 | 4.3222 | 4.3222 |
| 0.75 | 0.740217 | 262/730 | 4.1315 | 4.1315 | 4.1674 |
| 0.80 | 0.755645 | 620/730 | 3.9568 | 3.9568 | 4.1110 |
| 0.85 | 0.751428 | 724/730 | 3.7964 | 3.7964 | 4.1263 |
| 0.90 | 0.743997 | 724/730 | 3.6484 | 3.6484 | 4.1535 |

**两条事实**：

1. **`r_eff` 从 r = 0.75 起就达不到目标**，并稳定在 **0.74–0.76 的平台**上（受再生水产能 40 ML/d 与 300 ML 储池限制）。到 r = 0.9 时，730 天中有 **724 天**交付不足。
2. **模型的 CoC 始终等于"按目标 r 的解析值"，而不是"按 `r_eff` 的解析值"**——两者到 r = 0.9 时相差 **0.505**（3.6484 vs 4.1535），而模型输出与前者一致到 1e-15。

**这意味着什么**：当再生水交付不足时，实际的混合补水比设定配比更"淡"（自来水占比更高），真实 CoC 应更高、反噬应更小。**但模型仍按目标配比计算 CoC，因此在 r > 0.70 的区段低估了 CoC、高估了水质反噬。**

**三项后果，必须连同本节结论一并报告**：

1. **r > 0.70 区段的效应量是上界**，不是点估计。本文 §5.8.2 主表在 r = 0.8/0.9 报告的 CAWCC 下降（1100 MW）应读作"**在此建模约定下的上界**"。
2. **这解释了上一节 22.86 MW 残差的来源**：不是解析式算错，而是模型的实际 CoC 与"按有效配比应有"的 CoC 不一致。解析式用目标 r 是对的（与模型同约定），其残差来自模型本身的这一简化，而非代数错误。
3. **`r* = 0.5532` 不受影响**。它位于 `r_eff` 完全达标（r ≤ 0.70，0/730 天短缺）的区间内，故 §5.7 的阈值结论不依赖这一简化。

> **与 §3.3(b) 的关系**：本文剔除 `max_reuse_utilization` 的理由是"300 ML 储池使日尺度处理速率达铭牌属正常调蓄"。本节表明，**产能限制的效应并未消失——它以"`r_eff` 自回落 + CoC 仍按目标计算"的方式进入了模型**，且方向是保守的（高估水侧压力）。此前这一传导路径未被说明，现补记于此。

""" + MS_ANCHOR

# ---------- 英文 ----------
EN_ANCHOR = ("The consequence for how this paper should be read is direct: the −100 MW figure is a "
             "model output, never an analytic prediction.")
EN_NEW = ("The consequence for how this paper should be read is direct: the −100 MW figure is a "
          "model output, never an analytic prediction. The residual has a specific cause, which we "
          "report because it constrains the high-$r$ results. Raising the target ratio beyond about "
          "0.70 exhausts the reclaimed supply: at 1100 MW the delivered fraction stays at "
          "0.700000 with no shortfall days up to $r=0.70$, but falls to 0.740 and 0.744 with 620 "
          "and 724 of 730 days short at $r=0.80$ and $0.90$. The model nevertheless computes the "
          "cycles of concentration from the *target* mix rather than the delivered one — its output "
          "matches the target-based closed form to 1e-15 while differing from the delivered-based "
          "value by 0.505 at $r=0.9$ (3.6484 against 4.1535). Because a shortfall makes the real "
          "blend fresher than the target, the true cycles would be higher and the penalty smaller, "
          "so the model understates CoC and overstates the water-quality penalty above $r\\approx0.70$. "
          "The declines reported at $r=0.8$ and $0.9$ are therefore upper bounds under this modelling "
          "convention, not point estimates. The threshold itself is unaffected: $r^{*}=0.5532$ lies "
          "where delivery is complete.")

# ---------- SI ----------
SI_ANCHOR = "## S6 Methodological detail compressed from the main text"
SI_NEW = """### S5.9 CoC is computed from the target mix, not the delivered one

Section S5.8 attributes the analytic residual to a term rising with $r$ without decomposing it. The
decomposition follows.

At the water-scarce endpoint, 1100 MW and the full 730-day driver, raising the target substitution
ratio yields:

| $r$ target | $r_{\\mathrm{eff}}$ delivered | days short | CoC model | CoC at target $r$ | CoC at $r_{\\mathrm{eff}}$ |
|---:|---:|---:|---:|---:|---:|
| 0.70 | 0.700000 | **0 / 730** | 4.3222 | 4.3222 | 4.3222 |
| 0.75 | 0.740217 | 262 / 730 | 4.1315 | 4.1315 | 4.1674 |
| 0.80 | 0.755645 | 620 / 730 | 3.9568 | 3.9568 | 4.1110 |
| 0.85 | 0.751428 | 724 / 730 | 3.7964 | 3.7964 | 4.1263 |
| 0.90 | 0.743997 | 724 / 730 | 3.6484 | 3.6484 | 4.1535 |

Two facts stand out. First, delivery falls short from $r=0.75$ onward and settles on a plateau near
0.74–0.76, set by the 40 ML d⁻¹ reclaimed capacity and the 300 ML pond; by $r=0.9$ only 6 of 730
days meet the target. Second, the model's CoC always equals the value computed from the **target**
mix, agreeing with it to 1e-15, while differing from the delivered-mix value by up to 0.505
(3.6484 against 4.1535).

When delivery falls short the real blend is fresher than the target, so the true cycles would be
higher and the penalty smaller. The model therefore understates CoC and overstates the
water-quality penalty above $r\\approx0.70$. Three consequences follow. The declines reported at
$r=0.8$ and $0.9$ in the main results table are upper bounds under this modelling convention rather
than point estimates. The analytic residual of S5.8 is explained: the closed form uses the target
ratio, consistently with the model, and the discrepancy originates in the model's simplification,
not in the algebra. And the threshold is untouched, because $r^{*}=0.5532$ lies in the region where
delivery is complete.

This also clarifies how capacity limitation enters the model despite `max_reuse_utilization` being
excluded (item (b) of the constraint discussion, S4.2). That indicator was excluded because a
300 ML pond makes nameplate daily throughput normal buffering rather than failure. The capacity
limit has not vanished on that account: it propagates through the delivered-fraction shortfall while
CoC remains target-based, and the direction of that propagation is conservative, overstating
water-side pressure.

**Evidence:** `_reff_shortfall.json`, `_reff_shortfall.txt`, `_coc_reff_tension.json`,
`_quantify_reff_shortfall.py`, `_verify_coc_reff.py`.

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
if MS_ANCHOR in t and "5.7.8" not in t:
    MS.write_text(t.replace(MS_ANCHOR, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿 §5.7.8")
    n += 1
else:
    print("母稿未匹配")

t = EN.read_text(encoding="utf-8")
if EN_ANCHOR in t and "delivered fraction stays" not in t:
    EN.write_text(t.replace(EN_ANCHOR, EN_NEW, 1), encoding="utf-8")
    print("OK 英文")
    n += 1
else:
    print("英文未匹配")

t = SI.read_text(encoding="utf-8")
if SI_ANCHOR in t and "S5.9" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S5.9")
    n += 1
else:
    print("SI 未匹配或已存在")
print(f"完成 {n}/3")
