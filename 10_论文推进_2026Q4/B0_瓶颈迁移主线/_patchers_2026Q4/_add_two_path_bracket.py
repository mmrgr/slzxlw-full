# -*- coding: utf-8 -*-
"""判断"动态路径下 r* 机制消失"是否物理合理，以及论文应如何表述。

【确凿数据（D-HA，固定 1100 MW，730 天）】
               总取水 ML    取水比
legacy  r=0.0  30782.8     0.936303
        r=0.9  33667.1     0.948293   （+9.37%）
dynamic r=0.0  30782.8     0.936303
        r=0.9  30786.3     0.936303   （+0.011%，取水比一字不动）

【物理判断】
动态路径下，储池（24 ML，满库）吸收了盐分，环路排污 TDS 降到约 194 mg/L
（接近补水浓度）。这意味着：
  - 环路本身不积盐 → CoC 由设计值 5.0 主导，L 限值不起作用
  - 因此提高 r 不改变 CoC → 不改变补水需求 → 不改变取水
  
这在物理上**是自洽的**：一个带足够大的缓冲池、且排污量足够维持低环内浓度的
冷却系统，确实不会因为补水略微变咸而被迫降低浓缩倍数。

【但这也暴露了 legacy 路径的一个隐含假设】
legacy 路径等价于假设：
  **混合补水的全部盐负荷立即、完全作用于环路，无任何缓冲或时滞。**

这个假设在什么情况下成立？
  - 储池容量相对日补水很小（缓冲可忽略）
  - 或系统总是处于"盐分已充分混合"的稳态
反之，当储池容量约等于数日补水量（本模型：24 ML vs 约 38 ML/d ≈ 0.6 天）
时，缓冲显著。

【论文应如何表述（三层）】
1. **判据 r* 本身仍成立**：它是"水质上限开始约束 CoC"的门槛，纯代数，与路径无关。
2. **阈值型响应（取水随 r 上升）是 legacy 路径的性质**：动态路径下该响应消失。
3. **两个路径给出该机制的上下界**：
   - legacy = 无缓冲极限 = 反噬**上界**
   - dynamic = 满库缓冲 = 反噬**下界**（≈0）
   真实系统介于两者，取决于储池容量与运行策略。

这是最诚实、也最有信息量的表述方式。它把"路径依赖"从缺陷转化为
"机制强度的界定范围"。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 母稿：§5.7.9 之后追加 5.7.10 ----------
MS_ANCHOR = "## 5.8 结果 5：瓶颈位置是政策的内生函数（纯物理口径）"
MS_NEW = """### 5.7.10 两条路径给出该机制的上下界

§5.7.9 披露了本文结果建立在 legacy volume-only 路径之上。一个必然的追问是：**若改用动态盐分路径，主结论是否还成立？** 本节给出答案。

**在 D-HA 端点、固定 1100 MW、730 日驱动下**，逐步提高目标替代率 r：

| r | legacy 总取水 ML | legacy 取水比 | 动态 总取水 ML | 动态 取水比 |
|---:|---:|---:|---:|---:|
| 0.0 | 30,782.8 | 0.936303 | 30,782.8 | 0.936303 |
| 0.5 | 30,782.8 | 0.936303 | 30,782.8 | 0.936303 |
| 0.6 | 31,140.5 | 0.937790 | 30,783.3 | **0.936303** |
| 0.7 | 31,935.9 | 0.941097 | 30,784.2 | **0.936303** |
| 0.8 | 32,776.8 | 0.944592 | 30,785.3 | **0.936303** |
| 0.9 | 33,667.1 | 0.948293 | 30,786.3 | **0.936303** |

**legacy 路径下总取水上升 9.37%、取水比上升 0.0120；动态路径下总取水仅升 0.011%、取水比一位不动。**

纯物理 CAWCC 随之：

| r | legacy CAWCC | 动态 CAWCC |
|---:|---:|---:|
| 0.0 – 0.5 | 1200 | 1200 |
| 0.6 | 1150 | **1200** |
| 0.7 | 1150 | **1200** |
| 0.8 | 1100 | **1200** |
| 0.9 | 1100 | **1200** |

**即：动态路径下 CAWCC 恒为 1200 MW，−100 MW 的效应完全消失。**

**这意味着什么，必须分三层说清，不可混谈**：

1. **判据 `r*` 本身不受影响。** `r*` 是"水质上限开始约束 CoC"的代数门槛，由四个水质参数决定，与模型走哪条路径无关。§5.7.2 的推导、§5.7.3b 的四情形分类学、§5.7.3c 的弹性全部继续成立。
2. **阈值型的取水响应是 legacy 路径的性质，不是判据的推论。** 动态路径下储池（24 ML，约 0.6 日补水量）吸收盐分、排污 TDS 降至约 194 mg/L（接近补水浓度），环路不积盐，故 CoC 恒被设计值主导，提高 r 不改变补水需求。**这是一个物理上自洽的结果**，而非数值伪影。
3. **因此两条路径给出该机制的上下界。** legacy 路径等价于"混合补水的全部盐负荷立即完全作用于环路、无缓冲无时滞"，是反噬的**上界**；动态路径是满库缓冲稳态，给出**下界**（≈0）。真实系统介于两者，取决于储池容量相对日补水量的比例与运行策略。

> **对本文结论的影响（诚实表述）**：本文报告的 **−100 MW 与 +6.48% 是上界**，不是点估计。在储池容量显著且处于满库稳态的系统中，同一机制的效应可以趋近于零。
>
> **但这不使判据失效。** 判据回答的是"**是否存在一个 r 之上水质约束开始起作用**"，答案是肯定且可闭式计算的；两条路径的差别在于"越过该门槛后实际损失多少"。前者是本文的主张，后者是模型输出且受路径约定影响。

""" + MS_ANCHOR

# ---------- 英文 ----------
EN_ANCHOR = ("And the −100 MW and +6.48% figures are "
             "legacy-path values that should be read as the effect in the limit of no dynamic salt "
             "buffering, which is an upper bound, since buffering can only weaken the penalty.")
EN_NEW = ("And the −100 MW and +6.48% figures are legacy-path values that should be read as the "
          "effect in the limit of no dynamic salt buffering, which is an upper bound, since "
          "buffering can only weaken the penalty. Running the capacity scan under both paths makes "
          "the bracket explicit. At the water-scarce endpoint, raising $r$ from 0 to 0.9 moves total "
          "withdrawal by +9.37% and the abstraction ratio by +0.0120 under the legacy path, but by "
          "+0.011% with the abstraction ratio unchanged to six decimals under dynamic tracking. The "
          "purely physical CAWCC follows: it falls 1200 → 1100 MW under the legacy path and stays at "
          "1200 MW under the dynamic one, so the 100 MW effect disappears entirely there. These are "
          "not conflicting results but the two ends of a bracket. The legacy path assumes the whole "
          "salt load of the blended make-up acts on the loop immediately, with no storage buffering, "
          "which bounds the penalty from above. Dynamic tracking with a full 24 ML pond, roughly "
          "0.6 days of make-up, bounds it from below at essentially zero. A real system sits between "
          "them according to pond size relative to daily make-up and to operating policy. What "
          "survives both paths is the criterion: $r^{*}$ states that a quality ceiling begins to "
          "bind above a computable ratio, and that is a claim about where the constraint starts, not "
          "about how much is lost when it does.")

# ---------- SI ----------
SI_ANCHOR = "## S6 Methodological detail compressed from the main text"
SI_NEW = """### S5.11 Both paths, and the bracket they define

Section S5.10 shows that enabling dynamic salt tracking weakens the penalty substantially. The
obvious follow-up — whether the main result survives that change — is answered here.

At the water-scarce endpoint, fixed at 1100 MW over the 730-day driver:

| $r$ | legacy withdrawal ML | legacy ratio | dynamic withdrawal ML | dynamic ratio |
|---:|---:|---:|---:|---:|
| 0.0 | 30,782.8 | 0.936303 | 30,782.8 | 0.936303 |
| 0.5 | 30,782.8 | 0.936303 | 30,782.8 | 0.936303 |
| 0.6 | 31,140.5 | 0.937790 | 30,783.3 | **0.936303** |
| 0.7 | 31,935.9 | 0.941097 | 30,784.2 | **0.936303** |
| 0.8 | 32,776.8 | 0.944592 | 30,785.3 | **0.936303** |
| 0.9 | 33,667.1 | 0.948293 | 30,786.3 | **0.936303** |

Purely physical CAWCC:

| $r$ | legacy | dynamic |
|---:|---:|---:|
| 0.0 – 0.5 | 1200 | 1200 |
| 0.6 | 1150 | **1200** |
| 0.7 | 1150 | **1200** |
| 0.8 | 1100 | **1200** |
| 0.9 | 1100 | **1200** |

Under dynamic tracking CAWCC is invariant at 1200 MW, so the 100 MW effect vanishes entirely.

Three levels of interpretation must be kept apart. The criterion is untouched: $r^{*}$ is an
algebraic threshold for when the quality ceiling begins to bind, fixed by four water-quality
parameters and independent of the model path, so the derivation of S5.7.2, the four-regime taxonomy
of S5.7.3b and the elasticities of S5.7.3c all stand. The threshold-typed withdrawal response, by
contrast, is a property of the legacy path rather than a corollary of the criterion: with dynamic
tracking the 24 ML pond — about 0.6 days of make-up — absorbs the salt, blowdown TDS falls to
roughly 194 mg L⁻¹ near the make-up concentration, the loop does not accumulate salt, CoC stays at
its design value and raising $r$ does not change make-up demand. That is physically self-consistent,
not a numerical artefact. Consequently the two paths bracket the mechanism: the legacy path assumes
the entire salt load of the blend acts on the loop immediately with no buffering and bounds the
penalty from above, while dynamic tracking at full pond bounds it from below at essentially zero.

The consequence for the paper is that −100 MW and +6.48% are upper bounds, not point estimates; in a
system with substantial storage held full, the same mechanism can approach zero. The criterion
remains valid in either case, because it answers where a constraint begins to bind, not how much is
lost once it does.

**Evidence:** `_dynamic_path_cawcc.json`, `_dynamic_path_verify.txt`,
`_test_dynamic_path_main.py`, `_verify_dynamic_result.py`.

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
if MS_ANCHOR in t and "5.7.10" not in t:
    MS.write_text(t.replace(MS_ANCHOR, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿 §5.7.10")
    n += 1
else:
    print("母稿未匹配")

t = EN.read_text(encoding="utf-8")
if EN_ANCHOR in t:
    EN.write_text(t.replace(EN_ANCHOR, EN_NEW, 1), encoding="utf-8")
    print("OK 英文")
    n += 1
else:
    print("英文未匹配")

t = SI.read_text(encoding="utf-8")
if SI_ANCHOR in t and "S5.11" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S5.11")
    n += 1
else:
    print("SI 未匹配或已存在")
print(f"完成 {n}/3")
