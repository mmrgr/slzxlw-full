# -*- coding: utf-8 -*-
"""把"D-CO 端联合口径降幅远大于 D-HA"这一遗漏写入论文。

【事实（rstar_physical_cawcc_by_r.csv，20 行）】
                r=0.6   r=0.7   r=0.8   r=0.9
HA 联合          1150    1100     900     800
HA 纯物理        1150    1150    1100    1100
HA 差距            0      -50    -200    -300
CO 联合          1200    1000     850     700
CO 纯物理        1450    1450    1450    1400
CO 差距          -250    -450    -600    -700

【机制】
两端政策约束的首失效容量相近（HA: 1350/1150/950/850；CO: 1250/1050/…），
但**纯物理瓶颈位置不同**：
  HA 纯物理瓶颈 = 水源取水（1200），比政策约束失效点更早/接近 → 政策约束难以主导
  CO 纯物理瓶颈 = 电网（1500），远晚于政策约束失效点 → 政策约束轻易主导
故 CO 端"政策口径 vs 纯物理"差距在 r=0.9 达 700 MW，远超 HA 端的 300 MW。

【为什么这是重要遗漏】
主稿此前只说"HA 端差 300 MW"，读者会认为"CO 端政策口径影响小"。
实际相反：**CO 端才是政策口径影响最大的端点**。
这同时强化了本文的口径分离主张——若不分离，CO 端会被误报为"r 提高使承载容量从 1450 降到 700"，
而纯物理值仅有 50 MW 的下降。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 母稿：替换读数 3，并给主表加网格标注 ----------
MS_OLD_TABLE_HEAD = """| r | D-HA 物理 CAWCC | D-HA 首失效约束 | D-CO 物理 CAWCC | D-CO 首失效约束 |
|---:|---:|---|---:|---|"""
MS_NEW_TABLE_HEAD = """> 下表为 **50 MW 网格**上的绝对容量值。按 §5.8.2 网格框的规则，**绝对值的引用须注明"50 MW 网格系统性低估 0–25 MW"**；中间 r 值的**降幅**不得引用。

| r | D-HA 物理 CAWCC | D-HA 首失效约束 | D-CO 物理 CAWCC | D-CO 首失效约束 |
|---:|---:|---|---:|---|"""

MS_OLD_3 = """3. **联合口径会高估效应**：D-HA 在 r=0.9 时联合口径 800 MW、纯物理 1100 MW，差 **300 MW**。该差距主要来自"政策目标达不到"，不是物理能力下降。**本文只主张 100 MW 的物理效应。**"""
MS_NEW_3 = """3. **联合口径会高估效应——且在 D-CO 端高估得更多。** r=0.9 时：

   | 域 | 联合口径 | 纯物理 | 差距 |
   |---|---:|---:|---:|
   | D-HA | 800 | 1100 | **−300 MW** |
   | D-CO | 700 | 1400 | **−700 MW** |

   **D-CO 端的口口径差距（700 MW）是 D-HA 端（300 MW）的两倍以上。** 机制是两端的**纯物理瓶颈位置不同**：D-HA 的物理瓶颈在水源取水（1200 MW），与政策约束的失效点（r=0.9 时 850 MW）接近，故政策约束难以成为额外的主导约束；D-CO 的物理瓶颈在电网（1500 MW），**远晚于**政策约束的失效点（r=0.9 时约 650 MW），故政策约束轻易接管主导地位。

   **这恰好强化了本文的口径分离主张**：若不分口径，D-CO 端会被误报为"提高 r 使承载容量由 1450 降至 700 MW"，而纯物理口径下实际只有 **50 MW** 的下降。**本文只主张纯物理口径的 50–100 MW 效应，拒绝联合口径的 300–750 MW。**"""

# ---------- 英文 ----------
EN_OLD = ("They give $k=5.43$ and $r=0.444$, 10.9 points below $r^{*}$.")
# 不放这里，改为在 §3.3 的口径段落后追加
EN_ANCHOR = ("All conclusions about whether $r$ changes carrying capacity therefore rest on the "
             "purely physical set; the joint set appears only as a contrast, and the gap reaches "
             "300 MW at $r=0.9$.")
EN_NEW = ("All conclusions about whether $r$ changes carrying capacity therefore rest on the "
          "purely physical set; the joint set appears only as a contrast, and the gap at $r=0.9$ "
          "reaches 300 MW at the water-scarce endpoint and 700 MW at the cool endpoint. The ordering "
          "is the opposite of what one might expect from the endpoints' policy targets alone, and "
          "the reason is where each endpoint's physical bottleneck sits: at the water-scarce "
          "endpoint it is source abstraction at 1200 MW, close to where the policy constraint fails "
          "(850 MW at $r=0.9$), so the policy constraint can hardly take over; at the cool endpoint "
          "the physical bottleneck is grid connection at 1500 MW, far later than the policy "
          "constraint's failure point, so the policy constraint readily does. Without the "
          "separation the cool endpoint would be misreported as losing 750 MW of capacity when the "
          "physical loss is 50 MW.")

# ---------- SI ----------
SI_ANCHOR = "### S5.5 Limitations specific to the threshold chapter"
SI_NEW = """### S5.4b Joint-versus-physical gap is larger at the cool endpoint

The main text states the joint-versus-physical gap at the water-scarce endpoint (300 MW at
$r=0.9$). The cool endpoint's gap is larger still, and the reason is instructive.

| $r$ | D-HA joint | D-HA physical | gap | D-CO joint | D-CO physical | gap |
|---:|---:|---:|---:|---:|---:|---:|
| 0.6 | 1150 | 1150 | 0 | 1200 | 1450 | −250 |
| 0.7 | 1100 | 1150 | −50 | 1000 | 1450 | −450 |
| 0.8 | 900 | 1100 | −200 | 850 | 1450 | −600 |
| 0.9 | 800 | 1100 | −300 | 700 | 1400 | −700 |

The two endpoints have similar policy-constraint failure capacities, so the difference is not in
the policy constraint but in **where the physical bottleneck sits**. At the water-scarce endpoint
the physical bottleneck is source abstraction at 1200 MW, close to the policy constraint's failure
point (850 MW at $r=0.9$); the two are comparable, so the policy constraint can hardly displace the
physical one. At the cool endpoint the physical bottleneck is grid connection at 1500 MW, far later
than the policy constraint's failure point, so the policy constraint takes over readily and the
joint estimate collapses.

This matters for how the paper's numbers should be read. Reported jointly, the cool endpoint would
appear to lose 750 MW of carrying capacity as $r$ rises to 0.9; under the purely physical set it
loses 50 MW. The 15-fold discrepancy is entirely an artefact of leaving the policy constraint in the
criterion set, which is the self-reference the main text warns against. It also shows that the
caliber separation is not a technicality that happens to matter at one endpoint — it matters most
where the physical bottleneck is electrical, which is precisely where a naive joint estimate looks
most alarming.

**Evidence:** `rstar_physical_cawcc_by_r.csv` (20 rows), `_audit_co_joint.py`.

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
ok = 0
for old, new in ((MS_OLD_TABLE_HEAD, MS_NEW_TABLE_HEAD), (MS_OLD_3, MS_NEW_3)):
    if old in t:
        t = t.replace(old, new, 1)
        ok += 1
    else:
        print("母稿未匹配:", old[:50])
if ok:
    MS.write_text(t, encoding="utf-8")
    print(f"OK 母稿（{ok}/2）")
    n += 1

t = EN.read_text(encoding="utf-8")
if EN_ANCHOR in t:
    EN.write_text(t.replace(EN_ANCHOR, EN_NEW, 1), encoding="utf-8")
    print("OK 英文")
    n += 1
else:
    print("英文未匹配")

t = SI.read_text(encoding="utf-8")
if SI_ANCHOR in t and "S5.4b" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S5.4b")
    n += 1
else:
    print("SI 未匹配或已存在")
print(f"完成 {n}/3")
