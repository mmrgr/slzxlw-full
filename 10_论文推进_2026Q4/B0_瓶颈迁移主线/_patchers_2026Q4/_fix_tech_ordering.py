# -*- coding: utf-8 -*-
"""修正：10 MW 网格下 dry_first 降幅(90) > evaporative(70)，故"排序稳健"不成立。

【事实（三网格）】
            50mw  25mw  10mw
evaporative  100    75    70
hybrid        50    50    60
dry_first     50    75    90
dry            0     0     0

50 MW：evaporative(100) > hybrid(50) = dry_first(50)
25 MW：evaporative(75) = dry_first(75) > hybrid(50)
10 MW：**dry_first(90) > evaporative(70) > hybrid(60)**

→ **只有"dry 恒为 0"这一条在三网格下都成立。**
→ 排序在细网格下反转，原因是本轮的分解已说明：
     evaporative 的降幅随网格**收敛下降**（100→75→70）
     dry_first  的降幅随网格**发散上升**（50→75→90）
   两者机制不同，交叉不可避免。

【正确表述】
不可说"效应量随冷却技术单调下降"——那只在 50 MW 网格成立。
可以说的是：
  (1) 三个有冷却用水的档位降幅都在 50–90 MW 量级（与主结论 −100 MW 同量级）；
  (2) dry 档恒为 0（机制不适用）；
  (3) 各档的精确降幅及其排序**均受网格量化支配**，不可引用；
  (4) 因此"统一湿冷给出效应上限"这一说法**不能由本检验支持** —— 需要更强表述上的克制。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 母稿 ----------
MS_OLD = """2. **效应量随冷却水强度下降，但精确值受网格量化限制。** 三网格复核后，各档降幅极差 **10–40 MW**，故**不引用任何单档的精确降幅**。可引用的是：①**排序**为 `evaporative` > `hybrid` ≈ `dry_first` > `dry`(0)，与 WUE 排序一致；②**量级**均落在 50–90 MW，与主结论的 −100 MW 同量级；③`dry` 档在三网格下恒为 0。
   **分解显示两种不同机制**：`evaporative` 的降幅变化来自**端点**随网格上升（1100→1125→1130，基线恒 1200），连续细化后收敛到约 **70 MW**；`dry_first` 的降幅变化来自**基线**随网格上升（1100→1125→1140，端点恒 1050），呈**发散**。因此"`hybrid` 与 `dry_first` 降幅相同"这一观察**不可作为证据**——后者极差达 40 MW。"""

MS_NEW = """2. **精确降幅与档间排序均由网格量化支配，不可引用。** 三网格结果：

   | 技术档 | 50 MW | 25 MW | 10 MW |
   |---|---:|---:|---:|
   | `evaporative` | 100 | 75 | **70** |
   | `hybrid` | 50 | 50 | **60** |
   | `dry_first` | 50 | 75 | **90** |
   | `dry` | 0 | 0 | **0** |

   **排序在细网格上发生反转**：50 MW 下 `evaporative` 最高，而 10 MW 下 `dry_first`(90) 反超 `evaporative`(70)。原因是两者的网格依赖机制不同——`evaporative` 的基线三网格恒定 1200、端点随网格上升（1100→1125→1130），故降幅**收敛下降**（100→75→70）；`dry_first` 的端点三网格恒定 1050、基线随网格上升（1100→1125→1140），故降幅**发散上升**（50→75→90）。

   **因此本检验可支持的最强结论只有三条**：①三个有冷却用水的档位，其降幅均落在 **50–90 MW** 量级，与主结论的 −100 MW **同量级**（即差异不超过一倍）；②`dry` 档在三网格下**恒为 0**，因外部取水恒为零，机制**不适用**而非稳健；③**不得声称"效应量随冷却技术单调下降"，也不得声称"统一湿冷给出效应上限"**——这两点只在 50 MW 网格上成立，细网格下被推翻。"""

MS_OLD_LIM = "> **对外部有效性的含义**：本文的机制结论对冷却技术**稳健**，但**效应量是条件于技术构成的**。由于真实城市的技术构成未知（本城仅有一个项目的公开设计值），本文报告 −100 MW 时应理解为**湿冷上限情形**，真实值可能更小。这一点已并入 §9.6 的局限。"
MS_NEW_LIM = "> **对外部有效性的含义（比上一版本更克制）**：本文的**机制结论**（阈值型响应存在）对冷却技术**稳健**——三个用水档位全部保留该响应。但**效应量的精确值及其档间排序均受 50 MW 网格量化支配**，三网格复核后既不单调也不稳定。故本节**不主张** 「−100 MW 是湿冷上限」；可主张的是三档效应量同处数十 MW 量级。真实城市的 −100 MW 应理解为**该参数集与该网格下的值**，其随技术构成的变化方向**未被本检验确定**。这一点已并入 §9.6 的局限。"

# ---------- 英文 ----------
EN_OLD = ("The capacity response does scale with the technology, though its precise magnitude is "
          "grid-limited: across 50, 25 and 10 MW grids the drop is 100/75/70 MW for `evaporative`, "
          "50/50/60 for `hybrid`, 50/75/90 for `dry_first` and 0/0/0 for `dry`, so ranges of 10 to "
          "40 MW forbid quoting any single tier's exact value. What is citable is the ordering "
          "(`evaporative` > `hybrid` ≈ `dry_first` > `dry`), matching the WUE ordering, and the "
          "magnitude, which stays within 50–90 MW and so shares the order of the −100 MW main "
          "result. Uniform evaporative modelling therefore yields the upper end of the effect.")
EN_NEW = ("The capacity response varies with technology, but neither its exact magnitude nor the "
          "ordering of the tiers survives grid refinement: across 50, 25 and 10 MW grids the drop is "
          "100/75/70 MW for `evaporative`, 50/50/60 for `hybrid`, 50/75/90 for `dry_first` and 0/0/0 "
          "for `dry`. At 50 MW `evaporative` leads, whereas at 10 MW `dry_first` overtakes it, "
          "because the two depend on the grid in opposite ways — `evaporative` has a grid-invariant "
          "baseline with a rising endpoint, so its drop converges downward, while `dry_first` has a "
          "grid-invariant endpoint with a rising baseline, so its drop diverges upward. What can be "
          "claimed is only that the three tiers that use cooling water all fall in the 50–90 MW "
          "range, the same order as the −100 MW main result, and that `dry` is identically zero on "
          "all grids because it draws no external water — the criterion is inapplicable there rather "
          "than robust. We therefore do not claim that evaporative modelling bounds the effect from "
          "above (SI S7.14).")

# ---------- SI ----------
SI_OLD = """The capacity drop is grid-limited, with ranges of 10 to 40 MW across the three resolutions, so no
single tier's exact value is quotable. Decomposing the variation shows two distinct mechanisms.
For `evaporative` the baseline is stable at 1200 MW on all three grids while the $r=0.8$ endpoint
rises from 1100 to 1125 to 1130, so the drop falls 100 → 75 → 70 and converges near 70 MW. For
`dry_first` the endpoint is stable at 1050 MW while the baseline rises from 1100 to 1125 to 1140,
so the drop rises 50 → 75 → 90 and diverges. The observation that `hybrid` and `dry_first` share a
50 MW drop on the coarse grid is therefore an artefact of that grid and must not be cited as
evidence that the two technologies produce equal effects. `dry` is zero on all three grids because
its external withdrawal is identically zero."""

SI_NEW = """The capacity drop is grid-limited, with ranges of 10 to 40 MW across the three resolutions, and —
more importantly — the **ordering of the tiers does not survive refinement**. At 50 MW the ordering
is `evaporative` (100) > `hybrid` (50) = `dry_first` (50); at 25 MW it is `evaporative` (75) =
`dry_first` (75) > `hybrid` (50); at 10 MW it reverses to `dry_first` (90) > `evaporative` (70) >
`hybrid` (60). Decomposing the variation explains why. For `evaporative` the baseline is stable at
1200 MW on all three grids while the $r=0.8$ endpoint rises from 1100 to 1125 to 1130, so the drop
converges downward, 100 → 75 → 70. For `dry_first` the endpoint is stable at 1050 MW while the
baseline rises from 1100 to 1125 to 1140, so the drop diverges upward, 50 → 75 → 90. The two
depend on the grid in opposite directions, so a crossing is unavoidable and neither the individual
values nor their ranking is citable.

Three claims survive. First, all three tiers that use cooling water produce drops in the 50–90 MW
range, the same order of magnitude as the −100 MW main result. Second, `dry` is zero on all three
grids because its external withdrawal is identically zero — the criterion is inapplicable there,
not robust. Third, statements of the form "the effect decreases monotonically with cooling-water
intensity" or "uniform evaporative modelling bounds the effect from above" hold only on the 50 MW
grid and are refuted by the finer ones; we therefore do not make them."""

n = 0
for path, pairs, tag in (
        (MS, [(MS_OLD, MS_NEW), (MS_OLD_LIM, MS_NEW_LIM)], "母稿"),
        (EN, [(EN_OLD, EN_NEW)], "英文"),
        (SI, [(SI_OLD, SI_NEW)], "SI")):
    t = path.read_text(encoding="utf-8")
    ok = 0
    for old, new in pairs:
        if old in t:
            t = t.replace(old, new, 1)
            ok += 1
        else:
            print(f"  {tag} 未匹配: {old[:60]}")
    if ok:
        path.write_text(t, encoding="utf-8")
        print(f"OK {tag}（{ok}/{len(pairs)}）")
        n += 1
print(f"完成 {n}/3")
