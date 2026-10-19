# -*- coding: utf-8 -*-
"""把"非 informative 约束的扫描范围边界检验"写入母稿、英文、SI。

【结果（0–4000 MW，50 MW 步长，排除 0 MW 伪影）】
原结论：HA 3 条 / CO 6 条约束"从未失效"（扫描 0–2000 MW）。
扩展后：**两端各只剩 1 条**真正从不失效：
  max_wwtw_utilization（HA 最大观测 0.8992，CO 0.8755，阈值 0.95）

其余原"非 informative"约束的实际首失效容量：
              HA      CO
system_reliability_fraction   2050    2550
unmet_cooling_water_ml        2300    3000
domestic_unmet_ml             1850    2350
peak_capacity_ratio           1750    2300
reclaimed_water_substitution  1350    2100

【两点意义】
1. **加强**了"污水处理不是瓶颈"这一与直觉相反的主张：扩到两倍容量仍不失效
   （HA 0.8992 / CO 0.8755 vs 阈值 0.95），不是扫描范围不足造成的假象。
2. **削弱**了其他几条"非 informative"的表述：它们其实在 2000 MW 之外就失效了，
   论文此前说"3/6 条从未失效"是**范围依赖的**，必须改为"在 0–2000 MW 内未失效"，
   并给出扩展扫描下的真实首失效点。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 母稿：在 §5.3 末尾追加 ----------
MS_ANCHOR = "### 5.4 干预反事实：对症 vs 非对症"
MS_NEW = """**4. 扫描范围的边界检验（2026-10-19 新增）：把容量扫描从 2000 MW 扩到 4000 MW。**

上文"3 条 / 6 条约束从未失效"这一表述是**范围依赖的**。把扫描上限加倍后（0–4000 MW，仍 50 MW 步长，并排除 0 MW 处"无 AI 故替代率为 0"的定义域伪影），两端**各只剩 1 条约束真正从不失效**：

| 约束 | HA 首失效 | CO 首失效 |
|---|---:|---:|
| `max_wwtw_utilization` | **未失效**（最大 0.8992） | **未失效**（最大 0.8755） |
| `system_reliability_fraction` | 2050 | 2550 |
| `unmet_cooling_water_ml` | 2300 | 3000 |
| `domestic_unmet_ml` | 1850 | 2350 |
| `peak_capacity_ratio` | 1750 | 2300 |
| `reclaimed_water_substitution_ratio` | 1350 | 2100 |

**这个检验同时产生一个加强和一个削弱**：

- **加强**："污水处理能力不是瓶颈"这一与直觉相反的主张**成立且稳健**——容量扩到本文主结果的两倍以上，其利用率仅达 0.8992（HA）/ 0.8755（CO），距阈值 0.95 仍有明确余量。它**不是扫描范围不足造成的假象**。
- **削弱**：其余几条约束的"非 informative"**只是 2000 MW 以内的性质**。本文正文此前的"3 条 / 6 条从未失效"应读作"**在 0–2000 MW 扫描范围内未失效**"；超出该范围，它们会按上表的容量失效。

> **方法学含义**：负结果必须连同其成立范围一起陈述。"该约束从未失效"这句话在缺少范围限定时会被误读为系统属性，而实际它可能只是扫描边界的产物。本文选择在原文保留 2000 MW 内的陈述（因为主结论正是在该范围内做出的），同时给出加倍范围下的边界，使读者能判断哪些负结果稳健、哪些范围依赖。

**证据**：`r2/{ha,co}/capacity_scan_4000mw.csv`、`_noninformative_extended.json`、`_noninformative_recheck.json`。

""" + MS_ANCHOR

# ---------- 英文 ----------
EN_ANCHOR = ("Six constraints never carry information at the cool endpoint and three at the "
             "water-scarce one. A non-informative constraint is not evidence of safety: the scan "
             "never reached it. Two negative results matter.")
EN_NEW = ("Six constraints never carry information at the cool endpoint and three at the "
          "water-scarce one **within the 0–2000 MW scan**. A non-informative constraint is not "
          "evidence of safety: the scan never reached it. Doubling the scan ceiling to 4000 MW "
          "shows how range-dependent that statement is — only `max_wwtw_utilization` then remains "
          "non-informative at either endpoint, reaching just 0.8992 and 0.8755 against a 0.95 "
          "threshold, while the other five first fail between 1350 and 3000 MW. This both "
          "strengthens and weakens a negative result. It strengthens the counter-intuitive claim "
          "that wastewater capacity is not a bottleneck, since that survives a scan ceiling more "
          "than twice the main result. It weakens the remaining non-informative statements, which "
          "hold only inside the original range. Two of the negative results therefore matter.")

# ---------- SI ----------
SI_ANCHOR = "### S5.2 Method gaps, registered honestly"
SI_NEW = """### S5.1b Range-dependence of the non-informative constraints

The main text reports that three constraints at the water-scarce endpoint and six at the cool one
never fail within the 0–2000 MW scan, and states explicitly that this is not evidence of safety.
The obvious follow-up question, which had not been tested, is whether those constraints fail once
the scan is extended. Doubling the ceiling to 4000 MW gives:

| Constraint | D-HA first failure | D-CO first failure |
|---|---:|---:|
| `max_wwtw_utilization` | **never** (max 0.8992) | **never** (max 0.8755) |
| `system_reliability_fraction` | 2050 | 2550 |
| `unmet_cooling_water_ml` | 2300 | 3000 |
| `domestic_unmet_ml` | 1850 | 2350 |
| `peak_capacity_ratio` | 1750 | 2300 |
| `reclaimed_water_substitution_ratio` | 1350 | 2100 |

At 0 MW the reclaimed substitution ratio is zero because no data centre exists, so that point is
excluded as a domain artefact rather than a failure.

The result cuts both ways. It strengthens one claim and limits five others. The strengthened claim
is that wastewater treatment capacity is not a bottleneck: with the scan ceiling doubled to 4000 MW
its utilisation reaches only 0.8992 and 0.8755 against a 0.95 threshold, so the conclusion does not
depend on where the scan stopped. The five limited claims are the other non-informative statements,
which hold only inside 0–2000 MW and would fail between 1350 and 3000 MW if the scan were extended.
The main text keeps the 0–2000 MW wording, since the paper's conclusions are drawn in that range,
but reports the extended boundaries so that a reader can tell which negative results are robust and
which are range-dependent.

**Evidence:** `{ha,co}/capacity_scan_4000mw.csv`, `_noninformative_extended.json`,
`_noninformative_recheck.json`, `_test_noninformative_extended.py`.

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
if MS_ANCHOR in t and "扫描范围的边界检验" not in t:
    MS.write_text(t.replace(MS_ANCHOR, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿 §5.3 扩展")
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
if SI_ANCHOR in t and "S5.1b" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S5.1b")
    n += 1
else:
    print("SI 未匹配或已存在")
print(f"完成 {n}/3")
