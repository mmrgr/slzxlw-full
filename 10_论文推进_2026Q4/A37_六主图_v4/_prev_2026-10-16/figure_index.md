# A37 六主图 v4 — 图件索引 (figure index)

> 生成时间: 2026-10-16 03:16:10  |  生成脚本: `make_figure_index.py`  |  复现: `make_all_figures.py`

本轮重绘动因: A27 把限值从**占位档**换成**引用档** (GB/T 50050-2017), 使有害情景由 285 降至 102、可靠情景由 1094 变为 813, 并暴露出 CoC 触下限的退化情景门禁。
按项目纪律「**改了限值/门禁 ⇒ 必须重跑所有下游产物**」, 旧图 (`09_图定稿/`, `A16_英文稿/figures/`) 建于此前的旧口径, **已过时**, 全部保留仅作审计留痕。

---

## 1. 图件总表

| 图号 | 科学问题 | 数据源 | 生成脚本 | 输出文件 | SHA256 (16) |
|---|---|---|---|---|---|
| **Fig. 1** | 研究边界如何划定? 三种反事实 (B0/B1/B2) 与三分账是什么? | `A13_可靠性机制/supply_state_regimes.csv`<br>`A26_语义统一/CHI_SEMANTICS.md` | `make_fig1.py` | `Fig1_boundary_counterfactuals.pdf`<br>`Fig1_boundary_counterfactuals.png` | pdf: `fae95a5eef80421d`<br>png: `8801082eed3c98c0` |
| **Fig. 2** | 掺混如何改变 CoC? 哪个物种绑定 CoC? | `A33_WP4_组成重构/wp4_results.csv`<br>`A4_水化学参数域/T6_coc_limits.csv`<br>`A4_水化学参数域/T6_water_chemistry_samples.csv`<br>`A27_引用限值/A27_引用限值报告.md` | `make_fig2.py` | `Fig2_water_quality_coc.pdf`<br>`Fig2_water_quality_coc.png` | pdf: `0dc59c12e7c62b21`<br>png: `34a7f338927d79b0` |
| **Fig. 3** | dS_pot 的符号结构是什么? q>0 组是否有害? | `A13_可靠性机制/supply_state_regimes.csv`<br>`A33_WP4_组成重构/wp4_results.csv`<br>`A13_可靠性机制/COLUMN_NAMES_CORRECTED.md` | `make_fig3.py` | `Fig3_city_results_signs.pdf`<br>`Fig3_city_results_signs.png` | pdf: `aff1cfb1ee726293`<br>png: `5b1b7b280b927870` |
| **Fig. 4** | 仅用干预前可观测量能否预测 dS_pot 符号? | `A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json`<br>`A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json`<br>`A31_WP2_假设冻结/wp2_e3_predictions.csv`<br>`A31_WP2_假设冻结/wp2_e3b_features.csv` | `make_fig4.py` | `Fig4_independent_prediction.pdf`<br>`Fig4_independent_prediction.png` | pdf: `30d8a7446f2c7d0a`<br>png: `e6126f94b2b5a537` |
| **Fig. 5** | 哪个参数主导 dS_pot? 交互多强? 极端事件会翻转吗? | `A34_WP5_敏感性与极端事件/wp5_morris.csv`<br>`A34_WP5_敏感性与极端事件/wp5_sobol.csv`<br>`A34_WP5_敏感性与极端事件/wp5_extreme_cases.csv`<br>`A34_WP5_敏感性与极端事件/wp5_extreme_summary.json` | `make_fig5.py` | `Fig5_sensitivity_extremes.pdf`<br>`Fig5_sensitivity_extremes.png` | pdf: `28e91a12d3aa399d`<br>png: `e35e2aeb815039a1` |
| **Fig. 6** | 真实设施中 committed 分支占比是多少? | `A30_WP0取证/a24b_partial_id_summary.json`<br>`A30_WP0取证/a24b_capacity_table.csv` | `make_fig6.py` | `Fig6_external_anchor_partial_id.pdf`<br>`Fig6_external_anchor_partial_id.png` | pdf: `4940a2e6f840ee00`<br>png: `85b1b95140345da9` |

> 图注文件: 每张图配 `figN_caption.md` (英文, 含标题句 + 数据/方法 + n + 限制)。

---

## 2. 数据源 SHA256 (可追溯)

数值来自哪一版文件, 由下表锁定。若上游文件变更, 哈希不匹配即说明图需重跑。

| 数据源 | 行数 | SHA256 (16) |
|---|---:|---|
| `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md` | 68 | `ce34a93e5e035cf2` |
| `A13_可靠性机制/supply_state_regimes.csv` | 1053 | `0a9401500b14adb8` |
| `A26_语义统一/CHI_SEMANTICS.md` | 114 | `28f56962f1cccb27` |
| `A27_引用限值/A27_引用限值报告.md` | 133 | `cd31f8408addc23d` |
| `A30_WP0取证/a24b_capacity_table.csv` | 6 | `4a2e78c1b65ce2d0` |
| `A30_WP0取证/a24b_partial_id_summary.json` | 97 | `d719fe049214cca9` |
| `A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json` | 104 | `fd6f8e0ab54cfda2` |
| `A31_WP2_假设冻结/wp2_e3_predictions.csv` | 814 | `83a174e88aa3a2f6` |
| `A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json` | 103 | `66af9ef11309e5a8` |
| `A31_WP2_假设冻结/wp2_e3b_features.csv` | 814 | `f4937ae54b12e9e5` |
| `A33_WP4_组成重构/wp4_results.csv` | 61 | `c88f6ecdf02fda2a` |
| `A34_WP5_敏感性与极端事件/wp5_extreme_cases.csv` | 65 | `77b5575081622682` |
| `A34_WP5_敏感性与极端事件/wp5_extreme_summary.json` | 956 | `a0da82fcabe86d34` |
| `A34_WP5_敏感性与极端事件/wp5_morris.csv` | 49 | `28d853c9e593d2bd` |
| `A34_WP5_敏感性与极端事件/wp5_sobol.csv` | 29 | `10de968169a2ae66` |
| `A4_水化学参数域/T6_coc_limits.csv` | 6 | `dd5473921793759a` |
| `A4_水化学参数域/T6_water_chemistry_samples.csv` | 6 | `cb646b4922c1ac5b` |

---

## 3. 独立核验过的关键数值

以下数值由 figure-builder 从**权威产物独立复算** (探针脚本 `_probe_verify.py` / `_probe_signs.py` / `_probe_q.py`), 非从文档转抄。

| 量 | 值 | 口径 | 核验说明 |
|---|---|---|---|
| 严格符号 dS_pot 计数 | **643 负 / 134 正 / 36 零** | n_eff=813 | 复现; 必须用 dS==0.0 精确判零。容差 1e-9 得 631/102 (旧口径, n=733) |
| q 分组 | **290 / 288 / 235** | n_eff=813 | 复现; q=(M0-M1)/M1, 该列需自行计算, 源文件无 q 列 |
| q>0 组有害计数 | **0 / 290** | n_eff=813 | 复现; 无正例 ⇒ 不具鉴别力 |
| 恒等式残差 | **2.546585164964e-11** | n_eff=813 | 复现 (相对 2.93e-16); 须用 max(0,inc_B2-inc_B1)-(M0-M1)-x_ai_B1 重建 |
| WP4 城市级 | **47/47 全部有益; q 分组 23/24** | n_eff=47 | 复现; 双门禁后 60 → 47, 剔除 13 |
| E3 仅化学 | **0.6712 vs 基线 0.8608** | n_eff=733 | 来自 summary.json |
| E3b 联合 C4 | **0.9059 全样本; 折外 0.9009 vs 0.8594** | n_eff=733 | 复现 tp/fp/tn/fn = 602/40/62/29 (须在剔除 80 近零行的子集上) |
| Sobol ΣS1 | **0.223 (ha) / 0.218 (co)** | Saltelli ha|IEUA | 复现 ≈0.22 |
| 极端事件翻转 | **0 / 8** | n_eff=64 | 复现 (4 热浪 + 4 干旱, 0 翻转) |
| 碱度保守界比 | **2.500 (IEUA); 49.3 (LADWP)** | baseline 限值档 | 复现; 静态余量比, 非动态临界值 |
| 碱度动态翻转临界 | **≈ 2.615×** | 41 点 × 2 域 × 2 水样 | 来自 WP5 报告表; 无观测支撑 |
| committed 占比界 | **[0%, 100%] 不可识别** | n=10826 (仅产能) | 来自 a24b_partial_id_summary.json (WITHDRAWN_AS_UNIDENTIFIED) |

---

## 4. 统一口径 (全册一致)

| 项 | 约定 |
|---|---|
| 主估计量 | `dS_pot = C - F = max(0, inc_B2 - inc_B1) - [(M0 - M1) + x_ai]` |
| 符号语义 | `dS_pot > 0` = 城市净取水**上升 (有害)**; `< 0` = **下降 (有益)** |
| 双门禁 | `status == "converged_unique"` **且** `~coc_floor_degenerate` |
| 零值约定 | **严格符号**: `dS_pot == 0.0` 单列, **不设容差带**。若用 `|dS|<1e-9` 会得到旧的 631/102 且实际 n=733 |
| 样本量 | 每图必标 `n_eff`; 每图必标数据源文件 |
| 列名注意 | `x_ai_B1_ml` / `x_ai_B2_ml` **列名互换**, 见 `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md` |
| 残差口径 | 用**相对**容差; 2.55e−11 (绝对) / 2.93e−16 (相对) |

---

## 5. 已撤回主张的隔离 (图中不得出现)

| 原主张 | 处置 | 图中处理 |
|---|---|---|
| "95–93% 真实设施已处于已承诺状态, empirically dominant" | **撤回** (不可识别, 界 = [0%,100%]) | Fig.6 以部分识别呈现, 不出现任何点估计 |
| "更干净 ⇒ CoC 更高 ⇒ 更省补水 ⇒ 更有利" | **撤回** (x_ai 主导, corr = −0.93) | 全册不出现; Fig.2 用限值/浓度比讲机理 |
| 判据吻合率 1.0000 作为预测/发现 | **降级**为记账一致性检验 | Fig.3 限制句显式声明 q>0 不具鉴别力 |
| H3 "有力证实" | **降级**为鉴别力不足 | Fig.3 用 "sufficient condition" |
| R² = 0.557 / 基线 −0.050 | **更正**为 0.806 / −0.073 | 不在六图中引用旧值 |
| 头条计数 631/102 标 n=813 | **改用** 643/134/36 并披露容差口径 | Fig.3 直接标注 |

---

## 6. 复现与校验

```bash
cd "10_论文推进_2026Q4/A37_六主图_v4"
PYTHONIOENCODING=utf-8 python make_all_figures.py   # 重跑全部六图
PYTHONIOENCODING=utf-8 python make_figure_index.py  # 重算本索引与哈希
```

规格: PDF + PNG 双份, 400 dpi, `pdf.fonttype=42` (TrueType 嵌入)。配色与 rcParams 复用上级 `figstyle.py` (只读), 在其上叠加 Nature Water 风格。

### 与上一版图件的关系

`09_图定稿/` 与 `A16_英文稿/figures/` **未被改动**, 保留作审计留痕。本目录 `A37_六主图_v4/` 是唯一有效的六张主图。
