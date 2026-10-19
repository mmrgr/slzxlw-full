# -*- coding: utf-8 -*-
"""用三网格数据修正 §5.8.7 的技术档降幅表述。

【关键修正】
上一轮写：evaporative −100 / hybrid −50 / dry_first −50 / dry 0。
三网格复核后：降幅受量化影响，**不可引用精确值**。

但分解后发现两种不同机制：
  evaporative：基线三网格恒 1200，端点 1100→1125→1130 → 降幅 100→75→70（**收敛到 ~70**）
  dry_first  ：端点三网格恒 1050，基线 1100→1125→1140 → 降幅 50→75→90（**发散**）
  hybrid     ：基线 1150→1150→1160，端点恒 1100 → 降幅 50→50→60（极差 10，最稳）

【可引用的与不可引用的】
可引用：
  - 排序：evaporative > dry_first ≈ hybrid > dry(0)，与 WUE 排序一致；
  - 量级：三档降幅都在 50–90 MW（"数十 MW"），与主结论 −100 MW 同量级；
  - dry 档恒为 0（三网格下取水恒 0，机制不适用）。
不可引用：
  - 任何一档的**精确降幅**（极差 10–40 MW）。
  - 特别是"dry_first 降幅与 hybrid 相同"这一观察 —— dry_first 的降幅随网格发散（50→90），
    不能作为"两者效应相同"的证据。

【对主结论的影响】
主文 §5.8.2 引用的 −100 MW 是 **evaporative 档在 50 MW 网格**上的值，
而其 10 MW 值为 −70 MW。这与第 51 轮已登记的"中间区降幅不可引用"规则一致，
但此前未把这规则应用到**技术档**维度。本次补上。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 母稿 §5.8.7 表格与结论替换 ----------
MS_OLD_TABLE = """| 技术档 | WUE (L/kWh) | `CoC_design` | 固定 1200 MW 下 r 0.5→0.8 取水增幅 | 纯物理 CAWCC r=0→0.8 |
|---|---:|---:|---:|---|
| `evaporative` | 2.125 | 5.0 | **+6.478%** | 1200 → 1100（**−100 MW**） |
| `hybrid` | 0.558 | 5.0 | **+6.472%** | 1150 → 1100（**−50 MW**） |
| `dry_first` | 0.327 | **6.0** | **+7.851%** | 1100 → 1050（**−50 MW**） |
| `dry` | 0.000 | 5.0 | **不适用**（外部取水恒 0） | 1300 → 1300（**0**） |"""

MS_NEW_TABLE = """| 技术档 | WUE (L/kWh) | `CoC_design` | 固定 1200 MW 下 r 0.5→0.8 取水增幅 | 纯物理 CAWCC 降幅（50/25/10 MW 三网格） |
|---|---:|---:|---:|---|
| `evaporative` | 2.125 | 5.0 | **+6.478%** | 100 / 75 / 70 |
| `hybrid` | 0.558 | 5.0 | **+6.472%** | 50 / 50 / 60 |
| `dry_first` | 0.327 | **6.0** | **+7.851%** | 50 / 75 / 90 |
| `dry` | 0.000 | 5.0 | **不适用**（外部取水恒 0） | 0 / 0 / 0 |"""

MS_OLD_CONC = """2. **效应量随冷却水强度单调下降。** 降幅 −100 → −50 → −50 → 0 MW。这给"偏保守"这一说法提供了**定量内容**：若全市有一半设施为 `hybrid`，本文的 −100 MW 实际应约为 **−50 MW**。"""

MS_NEW_CONC = """2. **效应量随冷却水强度下降，但精确值受网格量化限制。** 三网格复核后，各档降幅极差 **10–40 MW**，故**不引用任何单档的精确降幅**。可引用的是：①**排序**为 `evaporative` > `hybrid` ≈ `dry_first` > `dry`(0)，与 WUE 排序一致；②**量级**均落在 50–90 MW，与主结论的 −100 MW 同量级；③`dry` 档在三网格下恒为 0。
   **分解显示两种不同机制**：`evaporative` 的降幅变化来自**端点**随网格上升（1100→1125→1130，基线恒 1200），连续细化后收敛到约 **70 MW**；`dry_first` 的降幅变化来自**基线**随网格上升（1100→1125→1140，端点恒 1050），呈**发散**。因此"`hybrid` 与 `dry_first` 降幅相同"这一观察**不可作为证据**——后者极差达 40 MW。"""

# ---------- 英文 ----------
EN_OLD = ("The capacity response does scale with the technology: the physical CAWCC drop is −100, −50, −50 and 0 "
          "MW across those tiers, so modelling every facility as evaporatively cooled yields the "
          "upper bound of the effect, and a city with half its facilities on hybrid cooling would "
          "show roughly −50 MW rather than −100 MW.")
EN_NEW = ("The capacity response does scale with the technology, though its precise magnitude is "
          "grid-limited: across 50, 25 and 10 MW grids the drop is 100/75/70 MW for `evaporative`, "
          "50/50/60 for `hybrid`, 50/75/90 for `dry_first` and 0/0/0 for `dry`, so ranges of 10 to "
          "40 MW forbid quoting any single tier's exact value. What is citable is the ordering "
          "(`evaporative` > `hybrid` ≈ `dry_first` > `dry`), matching the WUE ordering, and the "
          "magnitude, which stays within 50–90 MW and so shares the order of the −100 MW main "
          "result. Uniform evaporative modelling therefore yields the upper end of the effect.")

# ---------- SI ----------
SI_OLD_TABLE = """| Tier | WUE (L kWh⁻¹) | $\\mathrm{CoC}_d$ | Make-up increase, $r$ 0.5→0.8 at 1200 MW | Physical CAWCC, $r$=0→0.8 |
|---|---:|---:|---:|---|
| `evaporative` | 2.125 | 5.0 | **+6.478%** | 1200 → 1100 (**−100 MW**) |
| `hybrid` | 0.558 | 5.0 | **+6.472%** | 1150 → 1100 (**−50 MW**) |
| `dry_first` | 0.327 | **6.0** | **+7.851%** | 1100 → 1050 (**−50 MW**) |
| `dry` | 0.000 | 5.0 | **not applicable** (external withdrawal identically zero) | 1300 → 1300 (**0**) |"""

SI_NEW_TABLE = """| Tier | WUE (L kWh⁻¹) | $\\mathrm{CoC}_d$ | Make-up increase, $r$ 0.5→0.8 at 1200 MW | Physical CAWCC drop, 50/25/10 MW grids |
|---|---:|---:|---:|---|
| `evaporative` | 2.125 | 5.0 | **+6.478%** | 100 / 75 / 70 |
| `hybrid` | 0.558 | 5.0 | **+6.472%** | 50 / 50 / 60 |
| `dry_first` | 0.327 | **6.0** | **+7.851%** | 50 / 75 / 90 |
| `dry` | 0.000 | 5.0 | **not applicable** (external withdrawal identically zero) | 0 / 0 / 0 |

The capacity drop is grid-limited, with ranges of 10 to 40 MW across the three resolutions, so no
single tier's exact value is quotable. Decomposing the variation shows two distinct mechanisms.
For `evaporative` the baseline is stable at 1200 MW on all three grids while the $r=0.8$ endpoint
rises from 1100 to 1125 to 1130, so the drop falls 100 → 75 → 70 and converges near 70 MW. For
`dry_first` the endpoint is stable at 1050 MW while the baseline rises from 1100 to 1125 to 1140,
so the drop rises 50 → 75 → 90 and diverges. The observation that `hybrid` and `dry_first` share a
50 MW drop on the coarse grid is therefore an artefact of that grid and must not be cited as
evidence that the two technologies produce equal effects. `dry` is zero on all three grids because
its external withdrawal is identically zero."""

n = 0
for path, pairs, tag in (
        (MS, [(MS_OLD_TABLE, MS_NEW_TABLE), (MS_OLD_CONC, MS_NEW_CONC)], "母稿"),
        (EN, [(EN_OLD, EN_NEW)], "英文"),
        (SI, [(SI_OLD_TABLE, SI_NEW_TABLE)], "SI")):
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
