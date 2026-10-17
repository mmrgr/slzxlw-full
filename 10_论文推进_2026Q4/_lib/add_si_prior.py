"""在 SI 中补入先验敏感性分析披露 (2026-10-17).

【为什么】
`A15_稳健性/prior_sensitivity.csv` 有一个 27 配置 × 600 LHS 的先验敏感性分析，
其结论是：dpA 口径(dp_scale=0)下 S_city 中位数**全为负**(−10,409 ~ −0)，
dpB 口径(dp_scale=1.0)下**有正有负**(−9,125 ~ +22,414)。
但论文与 SI 完全没有提到它。

【为何值得披露】
作者自己在脚本 docstring 里把它称为"**关键设计决定**"：
dp_scale 与引擎"池预算 = pool*(1+dp)"的实现耦合，会把可用池推到超过既有用户缺口，
于是 S_city>0 由位移记账驱动。这正是"两种口径必须分开报告"的具体体现。

【为何不影响主结论】
主网格(supply_state_regimes.csv)不含 dp_scale，主结论不依赖它。
本小节定位为：把"我们在敏感性里试过、并发现口径依赖"如实写出。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SI = Path(__file__).resolve().parent.parent / "A16_英文稿/supplementary_information.md"
t = SI.read_text(encoding="utf-8")

ANCHOR = "## S13. Conservation checks on both quality solver paths (added 2026-10-16)"
BLOCK = """## S12b. Prior sensitivity, and one caliber choice that must be stated

Because several inputs (pool scale, gap scale, incremental capacity) are set by assumption
rather than observation, we swept **27 prior configurations (3 × 3 × 3 over uniform,
log-uniform and triangular priors; 600 Latin-hypercube draws each, fixed seed)** through the
same evaluator (`A15_稳健性/prior_sensitivity.py`; `prior_sensitivity.csv`, `prior_bounds.json`).

The result is a **caliber-dependent sign**, and we state it rather than choose silently:

| caliber | what is held | median city outcome across the 27 priors |
|---|---|---|
| **A** (dp_scale = 0) | no incremental capacity; pure share question | **negative in 27/27** (range −10,409 to −0 ML) |
| **B** (dp_scale = 1.0) | pool budget inflated by `(1+dp_scale)` | **sign not stable** (range −9,125 to +22,414 ML) |

The mechanism is mechanical, not empirical: the engine implements incremental capacity as
`available = pool × (1 + dp_scale)`. At `dp_scale ≥ 1` the available pool is pushed past
existing-user demand, so a positive `S_city` is then produced by **displacement accounting** —
the same quantity counted on the other side of the ledger — rather than by a different physical
outcome.

**Consequence for this paper.** The main grid does not carry `dp_scale`; every headline number
in the main text is caliber A, where the sign of the city outcome is prior-invariant. Caliber B
is reported here because a reader who inflates the pool budget will land on the second row, and
should know that we know it. We do not claim the sign is prior-invariant under every
parameterisation — only under the one the paper uses, which is stated in the Methods.

"""
if "S12b" in t:
    print("已存在，跳过")
else:
    assert ANCHOR in t, "锚点缺失"
    t = t.replace(ANCHOR, BLOCK + ANCHOR, 1)
    SI.write_text(t, encoding="utf-8")
    print("已插入 S12b（先验敏感性与口径披露）")
