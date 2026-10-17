"""在主稿 Methods 中补充两种状态分类的说明 (2026-10-17).

【为什么需要】
数据里有两个状态列:
  state_by_pool : 三态 surplus / binding / shortage  (基于 pool vs elig 的**名义**比较)
  state_by_alloc: 二态 surplus / shortage            (基于**实际分配结果**)
二者**不一致**: binding 的 94 个可靠情景中, 74 个被 alloc 判为 surplus、20 个判为 shortage。
若读者把 binding 当作 shortage 的子类就会误读。

主稿此前从未解释这一点, 属于 GPT 第 06 条"统一供水状态、异常分类"的遗漏。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

ANCHOR = "**Design.** 839 solver-reliable paired scenarios"
BLOCK = """**Two supply-state classifications, and why both are reported.** Each scenario carries a
*nominal* state, obtained by comparing the available pool with incumbent eligibility
(`surplus` / `binding` / `shortage`, where `binding` means the pool is exactly exhausted), and a
*realised* state, obtained from the allocation actually returned by the joint solver
(`surplus` / `shortage` only). The two are **not** nested: of the 94 reliable scenarios labelled
`binding` nominally, 74 are realised as `surplus` and 20 as `shortage`, because whether a pool is
genuinely exhausted depends on the allocation that follows. We therefore treat `binding` as its
own category and never fold it into `shortage`; wherever a claim depends on the regime, we name
which of the two classifications it uses. (Reliable subset: nominal `shortage` 508 /
`binding` 94 / `surplus` 237; realised `shortage` 448 / `surplus` 391.)

"""
if ANCHOR in t:
    t = t.replace(ANCHOR, BLOCK + ANCHOR, 1)
    MS.write_text(t, encoding="utf-8")
    print("已在 Methods 插入状态分类说明")
else:
    print("MISS: 锚点未找到")
