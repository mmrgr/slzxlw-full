# A37 六主图 v4 — 图件索引 (figure index)

> 生成时间: 2026-10-17 19:27:08  |  生成脚本: `make_figure_index.py`  |  复现: `make_all_figures.py`

本轮重绘动因 (2026-10-16, 第二轮): 六主图 v4 初版建于 2026-10-16 03:14, **早于**随后完成的三组新证据 —— A38 模拟审稿的 NE-1/NE-2/NE-4 与 A39 的 WP8/WP9/WP10。主稿与 SI 已按新证据改写, 图注的 n、数值与限制声明必须同步, 故对**受影响的图**作增量更新 (Fig.2/4/5/6 重绘, Fig.1/3 图件不变仅图注复核)。

首轮动因 (v4 初版): A27 把限值从**占位档**换成**引用档** (GB/T 50050-2017), 使有害情景由 285 降至 102、可靠情景由 1094 变为 813, 并暴露出 CoC 触下限的退化情景门禁。
按项目纪律「**改了限值/门禁 ⇒ 必须重跑所有下游产物**」, 旧图 (`_archive_2026-10-17/过时图定稿_09/`, `A16_英文稿/figures/`) 建于此前的旧口径, **已过时**, 已归档仅作审计留痕。
本轮改动前的 v4 初版亦已整体复制到 `_prev_2026-10-16/` (图件 + 脚本 + 图注 + 索引 + 门禁), 便于逐项比对与回退。

---

## 1. 图件总表

| 图号 | 科学问题 | 数据源 | 生成脚本 | 输出文件 | SHA256 (16) |
|---|---|---|---|---|---|
| **Fig. 1** | 研究边界如何划定? 三种反事实 (B0/B1/B2) 与三分账是什么? | `A13_可靠性机制/supply_state_regimes.csv`<br>`A26_语义统一/CHI_SEMANTICS.md` | `make_fig1.py` | `Fig1_boundary_counterfactuals.pdf`<br>`Fig1_boundary_counterfactuals.png` | pdf: `9cb30218a66a8cc7`<br>png: `8801082eed3c98c0` |
| **Fig. 2** | 掺混如何改变 CoC? 哪个物种绑定 CoC? 该结论跨限值档稳健吗? | `A33_WP4_组成重构/wp4_results.csv`<br>`A4_水化学参数域/T6_coc_limits.csv`<br>`A4_水化学参数域/T6_water_chemistry_samples.csv`<br>`A27_引用限值/A27_引用限值报告.md`<br>`A38_模拟审稿/ne2_panel_robustness_summary.json` | `make_fig2.py` | `Fig2_water_quality_coc.pdf`<br>`Fig2_water_quality_coc.png` | pdf: `ca33d8b17ebabb5b`<br>png: `d0eaf02c063b689c` |
| **Fig. 3** | dS_pot 的符号结构是什么? q>0 组是否有害? | `A13_可靠性机制/supply_state_regimes.csv`<br>`A33_WP4_组成重构/wp4_results.csv`<br>`A13_可靠性机制/COLUMN_NAMES_CORRECTED.md` | `make_fig3.py` | `Fig3_city_results_signs.pdf`<br>`Fig3_city_results_signs.png` | pdf: `af4d1c2df0565cad`<br>png: `48aa17a6efd907d1` |
| **Fig. 4** | 仅用干预前可观测量能否预测 dS_pot 符号? 折外增益是否成立? | `A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json`<br>`A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json`<br>`A31_WP2_假设冻结/wp2_e3_predictions.csv`<br>`A31_WP2_假设冻结/wp2_e3b_features.csv`<br>`A38_模拟审稿/red_team_findings.md` | `make_fig4.py` | `Fig4_independent_prediction.pdf`<br>`Fig4_independent_prediction.png` | pdf: `ce6ece350c81cbeb`<br>png: `c91d18ff2449ef77` |
| **Fig. 5** | 哪个参数主导 dS_pot? 主效应解释多少? 结论跨限值档稳健吗? 极端事件会翻转吗? | `A34_WP5_敏感性与极端事件/wp5_morris.csv`<br>`A34_WP5_敏感性与极端事件/wp5_sobol.csv`<br>`A34_WP5_敏感性与极端事件/wp5_extreme_cases.csv`<br>`A34_WP5_敏感性与极端事件/wp5_extreme_summary.json`<br>`A38_模拟审稿/ne4_sobol_bootstrap_summary.json`<br>`A38_模拟审稿/ne2_panel_robustness_summary.json` | `make_fig5.py` | `Fig5_sensitivity_extremes.pdf`<br>`Fig5_sensitivity_extremes.png` | pdf: `863ab313b1940a1e`<br>png: `31aaa983c525ff46` |
| **Fig. 6** | 真实设施中 committed 分支占比是多少? 该用途/规模/成本有真实外部锚点吗? | `A30_WP0取证/a24b_partial_id_summary.json`<br>`A30_WP0取证/a24b_capacity_table.csv`<br>`A39_WP8_外部效度/wp8_real_reuse_cases_summary.json`<br>`A39_WP8_外部效度/wp9_cooling_share_summary.json`<br>`A39_WP8_外部效度/wp10_water_price_summary.json`<br>`A39_WP8_外部效度/wp11_reuse_deployment_summary.json` | `make_fig6.py` | `Fig6_external_anchor_partial_id.pdf`<br>`Fig6_external_anchor_partial_id.png` | pdf: `b2bdb25241a59115`<br>png: `f3e64f8fffb1bcb6` |

> 图注文件: 每张图配 `figN_caption.md` (英文, 含标题句 + 数据/方法 + n + 限制)。

---

## 2. 数据源 SHA256 (可追溯)

数值来自哪一版文件, 由下表锁定。若上游文件变更, 哈希不匹配即说明图需重跑。

| 数据源 | 行数 | SHA256 (16) |
|---|---:|---|
| `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md` | 68 | `ce34a93e5e035cf2` |
| `A13_可靠性机制/supply_state_regimes.csv` | 1053 | `f92443fdcc383b4a` |
| `A26_语义统一/CHI_SEMANTICS.md` | 114 | `28f56962f1cccb27` |
| `A27_引用限值/A27_引用限值报告.md` | 133 | `cd31f8408addc23d` |
| `A30_WP0取证/a24b_capacity_table.csv` | 6 | `4a2e78c1b65ce2d0` |
| `A30_WP0取证/a24b_partial_id_summary.json` | 97 | `d719fe049214cca9` |
| `A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json` | 104 | `6932c18cd11b9882` |
| `A31_WP2_假设冻结/wp2_e3_predictions.csv` | 840 | `261b1eeede5206b3` |
| `A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json` | 103 | `ebd1ba69d685201f` |
| `A31_WP2_假设冻结/wp2_e3b_features.csv` | 840 | `9f7315e0f9c449c8` |
| `A33_WP4_组成重构/wp4_results.csv` | 61 | `c88f6ecdf02fda2a` |
| `A34_WP5_敏感性与极端事件/wp5_extreme_cases.csv` | 65 | `77b5575081622682` |
| `A34_WP5_敏感性与极端事件/wp5_extreme_summary.json` | 956 | `a0da82fcabe86d34` |
| `A34_WP5_敏感性与极端事件/wp5_morris.csv` | 49 | `28d853c9e593d2bd` |
| `A34_WP5_敏感性与极端事件/wp5_sobol.csv` | 29 | `10de968169a2ae66` |
| `A38_模拟审稿/ne2_panel_robustness_summary.json` | 663 | `8ca7d4190e23e84a` |
| `A38_模拟审稿/ne4_sobol_bootstrap_summary.json` | 241 | `1a2fe74c67190e52` |
| `A38_模拟审稿/red_team_findings.md` | 278 | `03ef712f8efd0716` |
| `A39_WP8_外部效度/wp10_water_price_summary.json` | 39 | `297513f53a329292` |
| `A39_WP8_外部效度/wp11_reuse_deployment_summary.json` | 98 | `20252ecb36c423fa` |
| `A39_WP8_外部效度/wp8_real_reuse_cases_summary.json` | 125 | `12a6450979f62a84` |
| `A39_WP8_外部效度/wp9_cooling_share_summary.json` | 66 | `1c17232fcb7cfea9` |
| `A4_水化学参数域/T6_coc_limits.csv` | 6 | `dd5473921793759a` |
| `A4_水化学参数域/T6_water_chemistry_samples.csv` | 6 | `cb0915739bae62b3` |

---

## 3. 独立核验过的关键数值

以下数值由 figure-builder 从**权威产物独立复算** (探针脚本 `_probe_verify.py` / `_probe_signs.py` / `_probe_q.py`), 非从文档转抄。

| 量 | 值 | 口径 | 核验说明 |
|---|---|---|---|
| 严格符号 dS_pot 计数 | **626 负 / 177 正 / 36 零** | n_eff=839 | 复现; 必须用 dS==0.0 精确判零。容差 1e-9 得 614/145 (旧口径, n=759) |
| q 分组 | **263 / 288 / 288** | n_eff=839 | 复现; q=(M0-M1)/M1, 该列需自行计算, 源文件无 q 列 |
| q>0 组有害计数 | **0 / 263** | n_eff=839 | 复现; 无正例 ⇒ 不具鉴别力 |
| 恒等式残差 | **4.365575e-11** | n_eff=839 | 复现 (相对 3.55e-16); 须用 max(0,inc_B2-inc_B1)-(M0-M1)-x_ai_B1 重建 |
| WP4 城市级 | **47/47 全部有益; q 分组 23/24** | n_eff=47 | 复现; 双门禁后 60 → 47, 剔除 13 |
| E3 仅化学 | **0.6746 vs 基线 0.8090** | n_eff=733 | 来自 summary.json |
| E3b 联合 C4 | **0.9144 全样本; 折外 0.9171 vs 0.8151** | n_eff=733 | 复现 tp/fp/tn/fn = 602/40/62/29 (须在剔除 80 近零行的子集上) |
| E3b 折外增益已撤回 | **+0.184 (IEUA) / +0.000 ×2 / −0.018 (Figshare); median 0.000** | 4 折 (n=184/170/196/183) | 来自 e3b_summary.leave_one_sample_out 逐折复算; 仅 1/4 折为正 ⇒ 撤回折外预测主张 |
| Sobol ΣS1 (旧点估计) | **0.223 (ha) / 0.218 (co)** | Saltelli ha|IEUA | 复现 ≈0.22; Fig5 面板 b 仍绘制该点估计 |
| NE-4 ΣS1 (含区间) | **0.1877 (IEUA, n_eff=117) / 0.5809 (LADWP, n_eff=128)** | bootstrap 400, N_base=128 | 来自 ne4_sobol_bootstrap_summary.json; 均 ≪ 1 ⇒ 主效应只解释部分方差 |
| NE-4 ST 95% 区间 | **0.330 [0.075, 0.792] / 0.926 [0.051, 2.568] / 0.125 [0.015, 0.305]** | IEUA, 7 参数 | limit_scale / phi / alkalinity; phi 区间极宽 ⇒ 只引方向不引单点值 |
| NE-2 绑定物种不跨档 | **cited/permissive: alkalinity; strict: silica (IEUA) / TDS (LADWP)** | 3 档 × 2 水样 × 2 域 | 来自 ne2_panel_robustness_summary.json; strict 档无任何单物种符号杠杆 |
| 极端事件翻转 | **0 / 8** | n_eff=64 | 复现 (4 热浪 + 4 干旱, 0 翻转) |
| 碱度保守界比 | **2.500 (IEUA); 49.3 (LADWP)** | cited 限值档 | 复现; 静态余量比, 非动态临界值; 仅 cited/permissive 档成立 |
| 碱度动态翻转临界 | **≈ 2.615×** | 41 点 × 2 域 × 2 水样 | 来自 WP5 报告表; 无观测支撑 |
| committed 占比界 | **[0%, 100%] 不可识别** | n=10826 (仅产能) | 来自 a24b_partial_id_summary.json (WITHDRAWN_AS_UNIDENTIFIED); WP8-10 无需求字段 ⇒ 界不变 |
| WP8 B3 用途占比 | **40/141 = 28.4% (最大类别)** | n=141 案例集 | 来自 wp8 summary; 非随机样本 ⇒ 不代表全国占比 |
| WP8 B3 容量落域 | **26/38 = 68.4% 落在 [1e3, 1e5] m3/d; 中位 4000** | n=38 (报容量者) | 来自 wp8 summary.b3_industrial_cooling.capacity |
| WP9 冷却水占比 | **min 0.000 / median 0.184 / max 0.990; 7 行业 >0.5** | n=39/41 行业 | 来自 wp9 summary; 缺失 2 行业显式统计, 未按 0 填充 |
| WP9 0.258 追溯 | **0.25799037378455597 = 39 行业均值, ≈62 分位** | n=39 | 与 A24 mean_of_means 逐位一致 (相对差 0.0) |
| WP10 水价 vs 再生水成本 | **1.550 vs 2.413 ⇒ 比 1.556; 17/61 (27.9%) 城市高于成本** | 61 城市 / 7730 月观测 | 来自 wp10 summary; 仅量级对照, 非因果, 不可做 NPV |

---

## 4. 统一口径 (全册一致)

| 项 | 约定 |
|---|---|
| 主估计量 | `dS_pot = C - F = max(0, inc_B2 - inc_B1) - [(M0 - M1) + x_ai]` |
| 符号语义 | `dS_pot > 0` = 城市净取水**上升 (有害)**; `< 0` = **下降 (有益)** |
| 双门禁 | `status == "converged_unique"` **且** `~coc_floor_degenerate` |
| 零值约定 | **严格符号**: `dS_pot == 0.0` 单列, **不设容差带**。若用 `|dS|<1e-9` 会得到旧的 631/102 且实际 n=733 |
| 样本量 | 每图必标 `n_eff`; 每图必标数据源文件 |
| 外部效度数据 | WP8/WP9/WP10 同源于 Shen et al. 2026 *Nature Water* 复现包 (CC-BY); **均为案例集/结构表, 非随机抽样, 且无需求字段** |
| 折外验证 | 留一**组成** (leave-one-composition-out); 参数网格跨折共享 ⇒ 仅化学轴被留出 |
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
| 折外 0.901 vs 0.859 作为预测能力证据 | **撤回** (单折驱动: 4 折中仅 IEUA +0.184, 中位增益 0.000, 两折基线饱和, Figshare −0.018) | Fig.4 面板 b 直接印出逐折增益并标注 WITHDRAWN |
| "碱度是**唯一**符号杠杆" 作为普适机制 | **限定**为 cited/permissive 两档; strict 档绑定物种变为 silica/TDS 且**无**单物种杠杆 | Fig.5 面板 c 三档并列; Fig.2 面板 b 加边界注 |
| Sobol 指数单点值 (S_T = 0.944 / 0.682 等) | **补 95% bootstrap 区间**并披露 ΣS1 ≪ 1 | Fig.5 面板 b 叠加区间条; φ 只引方向 |
| "95–93% 真实设施已承诺" 若被 WP8/WP9/WP10 间接"坐实" | **不成立**: 三个新数据源**均无需求字段** | Fig.6 面板 a 界 **[0%, 100%] 保持不变**, 面板 g 显式写 NOT CHANGED |

---

## 6. 复现与校验

```bash
cd "10_论文推进_2026Q4/A37_六主图_v4"
PYTHONIOENCODING=utf-8 python make_all_figures.py   # 重跑全部六图
PYTHONIOENCODING=utf-8 python make_figure_index.py  # 重算本索引与哈希
```

规格: PDF + PNG 双份, 400 dpi, `pdf.fonttype=42` (TrueType 嵌入)。配色与 rcParams 复用上级 `figstyle.py` (只读), 在其上叠加 Nature Water 风格。

### 与上一版图件的关系

`_archive_2026-10-17/过时图定稿_09/` 与 `A16_英文稿/figures/` **未被改动**, 保留作审计留痕。本目录 `A37_六主图_v4/` 是唯一有效的六张主图。
