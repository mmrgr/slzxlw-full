# -*- coding: utf-8 -*-
"""把"CAWCC(r) 的解析形式仅在近似意义上成立"这一结果写入论文。

【完整证据链】
1. 假设：CAWCC(r) = A / f(r)，f = CoC/(CoC−1)，A 为常数（由 r≤r* 区定标）。
2. 50 MW 网格：所有预测误差 ≤ 0.70 个网格步 → 看似成立。
3. 25 MW 网格：最大 0.45 步 → 仍看似成立。
4. **10 MW 网格：r=0.9 处误差 2.11 步（21 MW）→ 超出容差，不成立。**
5. **1 MW 网格精确定位**：r=0.9 的真 CAWCC = 1111.76 MW，
   解析预测 1088.9 MW，**差 +22.86 MW**。1 MW 网格的量化容差仅 ±1 MW，
   故这 22.9 MW **不是量化误差**。
6. 偏差随 r 单调增大（r=0.6 约 +5、r=0.8 约 +9、r=0.9 约 +23），
   说明解析式缺一个随 r 增长的项。

【因此可写入论文的结论】
- **阈值位置 r\* 是精确解析的**（8.9e-16，已确立）；
- **效应量 CAWCC(r) 不是精确解析的**：`A/f(r)` 只能给出约 1–2% 的近似，
  在高 r 端偏差可达 23 MW（约 2% of 1200）。
- 这是一个**诚实的边界**：本文的解析能力覆盖"阈值在哪里"，不覆盖"越过阈值后损失多少"。

【意义】
这实际上**强化**了论文已声明的定位：r* 是判据（criterion），效应量是模型输出。
此前只是陈述，现在有了定量边界：解析近似在 r ≤ 0.8 内可靠（≤1 步），
在 r=0.9 处失效。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 母稿：§5.7.6 之后追加 5.7.7 ----------
MS_ANCHOR = "## 5.8 结果 5：瓶颈位置是政策的内生函数（纯物理口径）"
MS_NEW = """### 5.7.7 一个诚实的边界：阈值可解析，效应量不可

§5.7 已证明**阈值位置** `r*` 是精确解析的（与模型输出一致到 8.9×10⁻¹⁶）。一个自然的问题是：**越过阈值后的效应量能否同样解析预测？**

考虑 D-HA 的首失效约束 `max_source_abstraction_ratio ≤ 0.95`。若城市源取水可写成
`base + MW·k·f(r)`，其中 `f(r) = CoC(r)/(CoC(r)−1)`，则令其等于 `0.95·CAP` 解出

```
CAWCC(r) = A / f(r)          （A 为常数，由 r ≤ r* 区间定标）
```

**检验结果分三层**：

| 网格 | 最大相对误差 | 判定 |
|---|---:|---|
| 50 MW | 0.70 个网格步 | 看似成立 |
| 25 MW | 0.45 步 | 看似成立 |
| **10 MW** | **2.11 步（21 MW）** | **超出容差** |

**再用 1 MW 网格精确定位 r = 0.9**：真 CAWCC = **1111.76 MW**，解析预测 **1088.9 MW**，**差 +22.86 MW**。1 MW 网格的量化容差仅 ±1 MW，故这 **22.9 MW 不是量化误差**。

且偏差随 r **单调增大**（r=0.6 约 +5 MW、r=0.8 约 +9 MW、r=0.9 约 +23 MW），说明解析式**缺一个随 r 增长的项**（可能来自再生水交付比例、园区储水调蓄或多物种取紧的耦合，本文未逐一分解）。

**因此本文必须区分两种解析能力**：

- **阈值位置**：✅ **精确解析**。`r* = (L/CoC_d − C_p)/(C_r − C_p)` 与模型一致到机器精度。这支撑 §5.7 的全部结论。
- **效应量**：❌ **仅近似**。`A/f(r)` 在 r ≤ 0.8 内可靠（≤1 个网格步），在 r = 0.9 处偏差达 **2%**。因此本文的 **−100 MW 始终是模型输出，不是解析预测**。

> **这个边界不是缺陷，而是本文定位的定量表述**：本文主张的是**判据**（阈值在哪里），不是**预测**（越过之后损失多少）。此前这只是定位陈述；现在它有了具体数字——解析近似在 80% 的参数区间内可用，在端点失效。

""" + MS_ANCHOR

# ---------- 英文 ----------
EN_ANCHOR = ("The threshold's form is structural and its value conditional.")
EN_NEW = ("The threshold's form is structural and its value conditional. It is worth separating two "
          "kinds of analytic reach here. The threshold location is exactly analytic: "
          "$r^{*}$ matches the model to machine precision. The effect size is not. Writing the "
          "binding abstraction ratio as a constant plus a term proportional to "
          "$MW\\,f(r)$ with $f=\\mathrm{CoC}/(\\mathrm{CoC}-1)$ suggests "
          "$\\mathrm{CAWCC}(r)=A/f(r)$, but this only approximates the model: it agrees to within "
          "one grid step at 50 and 25 MW, fails at 10 MW (2.11 steps at $r=0.9$), and a 1 MW scan "
          "puts the true value at 1111.76 MW against a predicted 1088.9 MW, a 22.9 MW discrepancy "
          "that grid quantisation cannot explain since the tolerance there is ±1 MW. The bias grows "
          "monotonically with $r$ (about +5 MW at $r=0.6$ to +23 MW at $r=0.9$), so the closed form "
          "is missing a term that rises with $r$. The consequence for how this paper should be read "
          "is direct: the −100 MW figure is a model output, never an analytic prediction. The "
          "closed form tells us where the threshold is; it does not tell us how much is lost beyond it.")

# ---------- SI ----------
SI_ANCHOR = "## S6 Methodological detail compressed from the main text"
SI_NEW = """### S5.8 Analytic reach: the threshold is exact, the effect size is not

Section 5.7 establishes that the threshold location is exactly analytic. It is natural to ask
whether the effect size beyond the threshold is analytic too. Take the water-scarce endpoint's
binding constraint, an abstraction ratio of at most 0.95. If city source abstraction can be written
as a constant plus a term proportional to $MW\\,f(r)$ with $f(r)=\\mathrm{CoC}(r)/(\\mathrm{CoC}(r)-1)$,
then setting it equal to $0.95\\,CAP$ gives $\\mathrm{CAWCC}(r)=A/f(r)$ for a constant $A$ calibrated
in the region $r\\le r^{*}$ where CoC is pinned at its design value.

Tested across resolutions, the form appears to hold on coarse grids and fails on fine ones:

| Grid | Maximum deviation | Verdict |
|---|---:|---|
| 50 MW | 0.70 grid steps | appears to hold |
| 25 MW | 0.45 steps | appears to hold |
| 10 MW | **2.11 steps (21 MW)** | fails |

A 1 MW scan then fixes the true value at $r=0.9$: the last compliant capacity is 1111 MW (ratio
0.949889) and the first failing is 1112 MW (ratio 0.950034), giving an interpolated CAWCC of
1111.76 MW against the analytic 1088.9 MW. The discrepancy is **22.86 MW**, and at 1 MW resolution
the quantisation tolerance is ±1 MW, so this cannot be explained as rounding. The bias also grows
monotonically with $r$ — roughly +5 MW at $r=0.6$, +9 MW at $r=0.8$ and +23 MW at $r=0.9$ — which
means the closed form is missing a term that rises with $r$. We did not decompose that term; the
candidates include the delivered-versus-target reclaimed fraction, storage buffering in the reuse
pond, and coupling through the multi-species minimum.

This establishes a boundary that the paper should state explicitly rather than leave implicit.
Analytic reach covers the threshold, not the effect size: $r^{*}$ is exact to machine precision,
whereas the −100 MW figure is a model output that no closed form reproduces to better than about 2%
at the high end. The paper's self-description as a criterion rather than a prediction is therefore
not merely a framing choice; it is the honest description of what the analysis can and cannot
deliver.

**Evidence:** `_analytic_cawcc_test.json`, `_analytic_cawcc_multigrid.json`, `_fine_r09.json`,
`_test_analytic_cawcc.py`, `_test_analytic_multigrid.py`, `_fine_r09.py`.

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
if MS_ANCHOR in t and "5.7.7" not in t:
    MS.write_text(t.replace(MS_ANCHOR, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿 §5.7.7")
    n += 1
else:
    print("母稿未匹配")

t = EN.read_text(encoding="utf-8")
if EN_ANCHOR in t and "two kinds of analytic reach" not in t:
    EN.write_text(t.replace(EN_ANCHOR, EN_NEW, 1), encoding="utf-8")
    print("OK 英文")
    n += 1
else:
    print("英文未匹配")

t = SI.read_text(encoding="utf-8")
if SI_ANCHOR in t and "S5.8" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S5.8")
    n += 1
else:
    print("SI 未匹配或已存在")
print(f"完成 {n}/3")
