# -*- coding: utf-8 -*-
"""补入 D-CO 端的三网格检验，使"负结果"享有与主结论同等的检验强度。

【现状】
主稿 §5.8.2 网格框只列 D-HA：
  零效应区 0/0/0；端点 −100/−100/−90；中间区 −50/−50/... 
**从未列出 D-CO 的三网格数字。**

而 D-CO 的"基本不动"是论文的**核心负结果**（双因素判据的第二条件靠它成立）。
一个负结果若未经同等网格检验，其可信度低于主结论。

【实测（rstar_grid_convergence_table.csv）】
D-CO 纯物理 CAWCC：
  r=0.0–0.8: 50mw=1450, 25mw=1450, 10mw=1460
  r=0.9    : 50mw=1400, 25mw=1425, 10mw=1440
降幅：50 / 25 / 20 MW，三网格下均 ≤ 50 MW，相对基线 ≤ 3.4%

【结论】
"基本不动"在三网格下**成立**，且降幅随网格细化单调减小（50→25→20），
说明 50 MW 网格对 CO 端略有高估，但方向不变。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 母稿：在网格框的表格中补 CO 行 ----------
MS_OLD = """> | 区间 | 50 MW | 25 MW | 10 MW | 判定 |
> |---|---|---|---|---|
> | **零效应区（r ≤ 0.5）** | 降幅 **0** | **0** | **0** | ✅ **三网格完全一致** |
> | **端点（D-HA, r=0.9）** | −100 | −100 | −90 | ✅ 稳健（极差 10 MW） |
> | **中间区（r=0.6 / 0.8）** | −50 / −100 | −25 / −75 | −10 / −70 | ❌ **极差 30–40 MW** |"""

MS_NEW = """> | 域 | 区间 | 50 MW | 25 MW | 10 MW | 判定 |
> |---|---|---|---|---|---|
> | D-HA | **零效应区（r ≤ 0.5）** | 降幅 **0** | **0** | **0** | ✅ 三网格完全一致 |
> | D-HA | **端点（r=0.9）** | −100 | −100 | −90 | ✅ 稳健（极差 10 MW） |
> | D-HA | **中间区（r=0.6 / 0.8）** | −50 / −100 | −25 / −75 | −10 / −70 | ❌ 极差 30–40 MW |
> | **D-CO** | **全区间** | 0（r≤0.8）/ −50（r=0.9） | 0 / −25 | 0 / −20 | ✅ **负结果成立**：三网格下降幅均 ≤ 50 MW，相对基线 ≤ 3.4% |
>
> **D-CO 端同样经过三网格检验**（此前版本只列 D-HA）。其"基本不动"的结论在三网格下成立，且降幅随网格细化单调减小（50 → 25 → 20 MW），说明 50 MW 网格对 CO 端略有高估，但方向不变。**负结果与主结论享有同等检验强度。**"""

# ---------- 英文 ----------
EN_OLD = ("Quantisation is why only the zero-effect region and the endpoint decline are cited as "
          "numbers.")
EN_NEW = ("Quantisation is why only the zero-effect region and the endpoint decline are cited as "
          "numbers. The cool endpoint's negative result was checked on the same three grids: its "
          "decline is 50, 25 and 20 MW at 50, 25 and 10 MW resolution, never exceeding 3.4% of its "
          "baseline, so the conclusion that it barely moves survives refinement, with the coarse "
          "grid slightly overstating it.")

# ---------- SI ----------
SI_ANCHOR = "### S5.4b Joint-versus-physical gap is larger at the cool endpoint"
SI_NEW = """### S5.4c Grid convergence at the cool endpoint

The main text's grid-convergence box reports the water-scarce endpoint's three-grid behaviour. The
cool endpoint carries the paper's central negative result — that its capacity barely responds
because its bottleneck is electrical — and a negative result deserves the same scrutiny as a
positive one. Checked on the same three grids:

| $r$ | 50 MW | 25 MW | 10 MW |
|---:|---:|---:|---:|
| 0.0 – 0.8 | 1450 | 1450 | 1460 |
| 0.9 | 1400 | 1425 | 1440 |
| **decline, $r$=0 → 0.9** | **50** | **25** | **20** |

The negative result holds: the decline never exceeds 50 MW, or 3.4% of the baseline, on any grid.
Two details are worth recording. First, the decline shrinks monotonically as the grid is refined
(50 → 25 → 20 MW), so the coarse grid slightly overstates the cool endpoint's response while
preserving its direction. Second, the 10 MW baseline is 1460 rather than 1450, a 10 MW difference
that the main text's single 1450 figure does not show; the absolute value carries the same
0–25 MW systematic underestimation documented for the water-scarce endpoint.

**Evidence:** `rstar_grid_convergence_table.csv`, `_check_co_grid.py`.

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
if MS_OLD in t:
    MS.write_text(t.replace(MS_OLD, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿网格框已补 CO 行")
    n += 1
else:
    print("母稿未匹配")

t = EN.read_text(encoding="utf-8")
if EN_OLD in t:
    EN.write_text(t.replace(EN_OLD, EN_NEW, 1), encoding="utf-8")
    print("OK 英文")
    n += 1
else:
    print("英文未匹配")

t = SI.read_text(encoding="utf-8")
if SI_ANCHOR in t and "S5.4c" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S5.4c")
    n += 1
else:
    print("SI 未匹配或已存在")
print(f"完成 {n}/3")
