# -*- coding: utf-8 -*-
"""把"C_p 需要多精确才能定论"写入 SI S7.10 末尾与母稿第 44 条。

核心结果（_cp_precision.py）：
  B 口径（r=0.499）判为未越过 ⟺ C_p < 230.8 mg/L
  A 口径（r=0.444）判为未越过 ⟺ C_p < 272.3 mg/L
  项目假设 180，距 B 口径临界值余 50.8 mg/L → 需精确到 ±25 mg/L
若 C_r 也未定，临界 C_p 随 C_r 强烈移动（C_r=500→380.2；C_r=800→81.4；C_r=1000→负）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"
MS = HERE / "03_主稿_v2.md"

SI_OLD = """**What would close the gap.** Facility-level finished-water TDS or electrical conductivity for
one city's potable supply and its recycled supply, from consumer confidence reports or plant
operating records. Such values are routinely published in the United States and would replace
both unanchored parameters at once; the loop salinity limit $L$ is the harder one, because it
depends on heat-exchanger metallurgy and operating practice rather than on water source alone."""

SI_NEW = """**How precisely must $C_p$ be measured before the verdict is settled?** Inverting the closed
form for $C_p$ answers this directly. Setting $r^{*}$ equal to the case city's observed ratio gives
$C_p=(L/\\mathrm{CoC}_d-r^{*}C_r)/(1-r^{*})$: the verdict is "not crossed" if and only if the true
$C_p$ lies below 230.8 mg L⁻¹ under the actual-use caliber ($r=0.499$), or below 272.3 mg L⁻¹ under
the supply-capacity caliber ($r=0.444$). The project assumes 180 mg L⁻¹, which leaves a margin of
50.8 mg L⁻¹ against the tighter of the two. A measurement precise to **±25 mg L⁻¹** would therefore
settle the question; typical laboratory TDS determinations are far more precise than that. The
obstacle is availability, not precision.

The requirement becomes much sharper if $C_r$ is also treated as unknown, because the two enter
the same expression. Holding $r=0.499$, the critical $C_p$ is 380.2 mg L⁻¹ at $C_r=500$, 230.8 at
$C_r=650$, 81.4 at $C_r=800$, and negative beyond about $C_r=1{,}000$ — at which point no positive
$C_p$ can keep the city below the threshold. Measuring the potable and reclaimed salinities
together therefore matters more than measuring either alone.

**What would close the gap.** Facility-level finished-water TDS or electrical conductivity for
one city's potable supply and its recycled supply, from consumer confidence reports or plant
operating records. Such values are routinely published in the United States and would replace
both unanchored parameters at once; the loop salinity limit $L$ is the harder one, because it
depends on heat-exchanger metallurgy and operating practice rather than on water source alone."""

MS_OLD = """    **如何真正闭合这个缺口**：需要某城市自来水与再生水的**出厂水 TDS 或电导率**实测值（美国通常可从 consumer confidence report 或水厂运行记录取得）——这一项可同时替换两个未锚定参数。`L`（循环水限值）最难，因为它取决于换热器材质与运行规范，而非水源本身。"""

MS_NEW = """    **需要多精确才能定论？** 把闭式解对 `C_p` 反解：`C_p = (L/CoC_d − r*·C_r)/(1 − r*)`。令 `r*` 等于该市实测配比，则**判定为"未越过"当且仅当真实 `C_p` 低于 230.8 mg/L**（实际用量口径 r=0.499），或低于 **272.3 mg/L**（供给能力口径 r=0.444）。项目假设 180 mg/L，距较紧的那个临界值尚有余量 **50.8 mg/L**。故**测到 ±25 mg/L 的精度即可定论**——常规实验室 TDS 测定的精度远高于此，**障碍是可得性，不是精度**。

    若 `C_r` 也当作未知，要求会急剧改变（两者进入同一表达式）：固定 `r=0.499`，`C_r=500` 时临界 `C_p` 为 380.2 mg/L，`C_r=650` 时为 230.8，`C_r=800` 时仅 81.4，`C_r` 超过约 1,000 后转为负值——即**不存在任何正 `C_p` 能使该城市低于阈值**。因此**同时测定自来水与再生水的含盐量，比只测其中之一更有价值**。

    **如何真正闭合这个缺口**：需要某城市自来水与再生水的**出厂水 TDS 或电导率**实测值（美国通常可从 consumer confidence report 或水厂运行记录取得）——这一项可同时替换两个未锚定参数。`L`（循环水限值）最难，因为它取决于换热器材质与运行规范，而非水源本身。"""

ok = 0
t = SI.read_text(encoding="utf-8")
if SI_OLD in t:
    SI.write_text(t.replace(SI_OLD, SI_NEW, 1), encoding="utf-8")
    print("OK SI S7.10")
    ok += 1
else:
    print("SI 未匹配")

u = MS.read_text(encoding="utf-8")
if MS_OLD in u:
    MS.write_text(u.replace(MS_OLD, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿第 44 条")
    ok += 1
else:
    print("母稿未匹配")
print(f"完成 {ok}/2")
