# -*- coding: utf-8 -*-
"""把 C_p 的外部锚定尝试结果写入 SI（新增 S7.10）。

【立场】
GAMA 是**地下水监测**数据，不是供水系统出厂水；且该文件只覆盖加州 19 个县（不含
Santa Clara）。因此**不能**用它替换项目的 C_p = 180 mg/L。

但它是目前唯一可获得的、覆盖加州多县、含 Total Dissolved Solids 实测值的公开数据，
足以回答一个更有限的问题：**C_p = 180 mg/L 在加州地下水分布中处于什么位置？**
答案：第 14.1 百分位（p5=120, p25=239, p50=420, p75=650, p95=2100）。

这本身是有价值的信息：它说明项目假设的 180 偏"淡"，而 C_p 一旦上移到全州中位 420，
r* 会从 0.5532 降到 0.0870 —— 足以翻转 Santa Clara 的判定。故这条必须写入，
作为"为什么 C_p 的锚定是本文最关键缺口"的直接证据。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"

NEW = """### S7.10 An attempted external anchor for $C_p$, and why it matters

Item 25 established that none of the four threshold parameters carries a measured anchor. We
attempted to close part of that gap for $C_p$, the potable-water TDS, using the only multi-county
public dataset we could reach that reports measured total dissolved solids: the California GAMA
Division of Drinking Water compilation (2020–present), obtained from the state open-data portal.

**What the dataset is and is not.** It reports groundwater monitoring results, not finished
drinking water at a treatment plant outlet, and the release we obtained covers 19 counties and
does **not** include Santa Clara. It therefore cannot replace the project value of 180 mg L⁻¹, and
we do not use it that way.

**What it can establish.** It locates the assumed value within the state's measured distribution.
Across 10,090 TDS determinations the percentiles are 120 (p5), 239 (p25), 420 (p50), 650 (p75)
and 2,100 mg L⁻¹ (p95); the assumed 180 mg L⁻¹ sits at the **14th percentile**, i.e. the project
assumes markedly fresher potable water than the Californian groundwater median. County medians
range from 210 mg L⁻¹ (Fresno) to 1,200 mg L⁻¹ (Imperial), and the neighbouring Alameda county
median is 546 mg L⁻¹.

**Why this is the most consequential of the four gaps.** $C_p$ enters the threshold twice, in the
numerator with a negative sign and in the denominator with a negative sign, and the numerator is
$L/\\mathrm{CoC}_d-C_p$. When $C_p$ approaches $L/\\mathrm{CoC}_d=440$ mg L⁻¹ the numerator
collapses and $r^{*}\\to0$; beyond it $r^{*}<0$ and the system enters Regime I, where any
substitution carries a cost. Evaluating the closed form at the observed values:

| $C_p$ source | $C_p$ (mg L⁻¹) | $r^{*}$ | Verdict for the case city ($r=0.444$ / $0.499$) |
|---|---:|---:|---|
| Project assumption (unanchored) | 180 | 0.5532 | not crossed / not crossed |
| Fresno county median | 210 | 0.5227 | not crossed / not crossed |
| GAMA statewide median | 420 | 0.0870 | **crossed / crossed** |
| Alameda county median | 546 | −1.0096 | **crossed / crossed** (Regime I) |
| Los Angeles county median | 550 | −1.1000 | **crossed / crossed** (Regime I) |

A shift of $C_p$ from 180 to the statewide median is enough to move the case city from clearly
below the threshold to clearly above it, and a further shift drives $r^{*}$ negative, which is a
categorical change rather than a numerical one. This is why we describe the case-city verdict as
nominal rather than robust: the verdict is decided by a parameter that has never been measured,
and the plausible range of that parameter straddles the decision boundary.

The same sensitivity applies to $C_r$: holding $C_p$ at 180, $C_r$ of 500, 650, 800 and
1,000 mg L⁻¹ give $r^{*}$ of 0.8125, 0.5532, 0.4194 and 0.3171 respectively. Reclaimed-water TDS
in practice varies by an order of magnitude with source and treatment, so this range is not
exotic.

**What would close the gap.** Facility-level finished-water TDS or electrical conductivity for
one city's potable supply and its recycled supply, from consumer confidence reports or plant
operating records. Such values are routinely published in the United States and would replace
both unanchored parameters at once; the loop salinity limit $L$ is the harder one, because it
depends on heat-exchanger metallurgy and operating practice rather than on water source alone.

**Evidence:** `_gama_tds_statewide.json`, `_c_p_anchor_impact.json`, `_gama_tds.py`,
`_cp_anchor_impact.py`.

---

### S7.11 Sensitivity of the critical ratio $k^{*}$"""


def main() -> None:
    t = SI.read_text(encoding="utf-8")
    anchor = "### S7.7 Sensitivity of the critical ratio $k^{*}$"
    if anchor not in t:
        print("找不到 S7.7 锚点")
        return
    # 在 S7.7 之前插入 S7.10/S7.11？不：S7.10 应放在 S7 末尾。
    # 实际做法：追加到 S7.9 之后、S8 之前
    anchor2 = "## S8 Data-reliability warnings for reviewers"
    if anchor2 not in t:
        print("找不到 S8 锚点")
        return
    t = t.replace(anchor2, NEW.replace("### S7.11 Sensitivity of the critical ratio $k^{*}$", "---") + "\n" + anchor2, 1)
    SI.write_text(t, encoding="utf-8")
    print("OK 已新增 S7.10")
    print("长度:", len(t))


if __name__ == "__main__":
    main()
