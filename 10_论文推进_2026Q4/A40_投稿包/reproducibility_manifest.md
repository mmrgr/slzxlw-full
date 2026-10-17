# 复现清单（Reproducibility Manifest）

> 自动生成：`python A40_投稿包/make_reproducibility_manifest.py`

**总体状态：ALL_CHECKS_PASS**（产物缺失 0；数字复算 17/17 PASS）

---

## 1. 权威产物与哈希（SHA256 前 16 位）

| 名称 | 哈希 | 存在 | 路径 | 生成脚本 | 说明 |
|---|---|:---:|---|---|---|
| 主稿 | `a37e4819ed453075` | ✅ | `A16_英文稿/manuscript_en_v3.md` | （手写稿，非生成） | Manuscript (v4 content) |
| SI | `7c8799ccc9d3d0d4` | ✅ | `A16_英文稿/supplementary_information.md` | （手写稿，非生成） | Supplementary Information S1–S21 |
| 六主图索引 | `3fbdbd48c9c7f3aa` | ✅ | `A37_六主图_v4/figure_index.md` | `A37_六主图_v4/make_figure_index.py` | Figures 1–6 + captions + hashes |
| 主网格 | `f92443fdcc383b4a` | ✅ | `A13_可靠性机制/supply_state_regimes.csv` | `A13_可靠性机制/supply_state_regimes.py` | A17 main grid (1052 rows) |
| 留出检验 | `4b7827c7b08066ea` | ✅ | `A15_稳健性/holdout_summary.json` | `A15_稳健性/holdout_validation.py` | Cross-domain holdout R²=0.766 |
| 模型桥接 | `54f7a1ccc3d6ebd7` | ✅ | `A20_模型桥接/bridging_summary_v2.json` | `A20_模型桥接/bridging_v2.py` | 24 paired runs |
| A24b 部分识别 | `d719fe049214cca9` | ✅ | `A30_WP0取证/a24b_partial_id_summary.json` | `A30_WP0取证/a24b_partial_identification.py` | regime share NOT identified |
| A24b 产能表 | `4a2e78c1b65ce2d0` | ✅ | `A30_WP0取证/a24b_capacity_table.csv` | `A30_WP0取证/a24b_partial_identification.py` | capacity feasibility 2.1–6.6% |
| 溶质闭合(R10a) | `062da967303c50e3` | ✅ | `A30_WP0取证/a21_solute_closure_summary.json` | `A30_WP0取证/a21_solute_closure.py` | relative residual 5.7e-19 |
| 通量平衡(vol-only) | `4c8471a6555c9021` | ✅ | `A30_WP0取证/volonly_flux_balance_summary.json` | `A30_WP0取证/volonly_flux_balance.py` | 1.9e-16 / 2.5e-16 |
| 主稿数字审计 | `8eefafaf5eaabf74` | ✅ | `A30_WP0取证/stale_number_audit.json` | `A30_WP0取证/audit_stale_numbers.py` | 193 values audited |
| 数字追溯 | `6df61bc028df424c` | ✅ | `A30_WP0取证/untraceable_traceability_summary.json` | `A30_WP0取证/trace_untraceable.py` | 48 UNTRACEABLE resolved |
| 证据台账 | `4b9b69d31f4f78be` | ✅ | `A30_WP0取证/证据台账_EVIDENCE_LEDGER.md` | `A40_投稿包/make_reproducibility_manifest.py` | claim → artifact ledger |
| E3 独立预测 | `6932c18cd11b9882` | ✅ | `A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json` | `A31_WP2_假设冻结/wp2_e3_independent_prediction.py` | chemistry-only fails (0.671 < 0.861) |
| E3b 联合预测 | `ebd1ba69d685201f` | ✅ | `A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json` | `A31_WP2_假设冻结/wp2_e3b_combined_prediction.py` | single-fold driven (median gain 0.000) |
| H4 稳健性 | `15a5fd5ee54c23ed` | ✅ | `A32_WP3_水化学/wp3_h4_robustness_summary.json` | `A32_WP3_水化学/wp3_h4_robustness.py` | q sign on complete samples |
| WP4 组成重算 | `c88f6ecdf02fda2a` | ✅ | `A33_WP4_组成重构/wp4_results.csv` | `A33_WP4_组成重构/wp4_complete_samples.py` | complete-species city-level dS |
| WP5 Morris | `28d853c9e593d2bd` | ✅ | `A34_WP5_敏感性与极端事件/wp5_morris.csv` | `A34_WP5_敏感性与极端事件/wp5_morris_sobol.py` | screening |
| WP5 Sobol | `10de968169a2ae66` | ✅ | `A34_WP5_敏感性与极端事件/wp5_sobol.csv` | `A34_WP5_敏感性与极端事件/wp5_morris_sobol.py` | variance decomposition |
| WP5 极端事件 | `a0da82fcabe86d34` | ✅ | `A34_WP5_敏感性与极端事件/wp5_extreme_summary.json` | `A34_WP5_敏感性与极端事件/wp5_extreme_events.py` | 0/8 sign flips |
| NE-1 双路径 | `786b19e987102e75` | ✅ | `A38_模拟审稿/ne1_r10a_signflip_summary.json` | `A38_模拟审稿/ne1_r10a_signflip.py` | direction robust, mechanism path-dependent |
| NE-2 限值档 | `8ca7d4190e23e84a` | ✅ | `A38_模拟审稿/ne2_panel_robustness_summary.json` | `A38_模拟审稿/ne2_panel_robustness.py` | binding species NOT panel-invariant |
| NE-4 Sobol区间 | `1a2fe74c67190e52` | ✅ | `A38_模拟审稿/ne4_sobol_bootstrap_summary.json` | `A38_模拟审稿/ne4_sobol_bootstrap.py` | bootstrap 95% CI |
| WP8 用途分布 | `12a6450979f62a84` | ✅ | `A39_WP8_外部效度/wp8_real_reuse_cases_summary.json` | `A39_WP8_外部效度/wp8_real_reuse_cases.py` | B3 = 40/141 = 28.4% |
| WP9 冷却水占比 | `1c17232fcb7cfea9` | ✅ | `A39_WP8_外部效度/wp9_cooling_share_summary.json` | `A39_WP8_外部效度/wp9_cooling_share.py` | 0.258 traced to source |
| WP10 水价对照 | `297513f53a329292` | ✅ | `A39_WP8_外部效度/wp10_water_price_summary.json` | `A39_WP8_外部效度/wp10_water_price.py` | reuse/tap = 1.56 |
| WP11 产能部署 | `20252ecb36c423fa` | ✅ | `A39_WP8_外部效度/wp11_reuse_deployment_summary.json` | `A39_WP8_外部效度/wp11_reuse_deployment.py` | 11 positive-capacity projects, 100% in modelled range |
| 终审门禁 | `9636cc61f6f11d72` | ✅ | `A36_终审/final_gate.py` | （手写脚本） | all checks PASS |

---

## 2. 关键数字 → 权威来源

| 数字 | 值 | 权威产物 | 备注 |
|---|---|---|---|
| 可靠子集 n | **839** | `A13_可靠性机制/supply_state_regimes.csv` | dual gate subset |
| 恒等式残差(绝对) | **2.5466e-11 ML** | `同上 (Lead 复算)` | recomputed in final_gate.py |
| 恒等式残差(相对) | **2.93e-16** | `同上` | machine epsilon |
| 严格符号计数 | **626 / 177 / 36** | `同上` | $dS<0$ / $>0$ / $=0$, strict convention |
| q 分组 | **290 / 288 / 235** | `同上` | $q>0$ / $q=0$ / $q<0$ |
| q>0 且有害 | **0** | `同上` | no exception in 263 |
| 跨域留出 R² | **0.7661** | `A15_稳健性/holdout_summary.json` | H2_true_holdout.co_R2_phi_eff |
| 留出基线 R² | **−0.0733** | `同上` | trivial_baseline_R2 |
| 桥接配对 | **24** | `A20_模型桥接/bridging_summary_v2.json` | n_pairs |
| 桥接符号一致 | **23/24 = 0.958** | `同上` | sign_agreement |
| A24b committed 界 | **[0%, 100%]** | `A30_WP0取证/a24b_partial_id_summary.json` | not identified |
| 产能可行性 | **2.1–6.6%** | `A30_WP0取证/a24b_capacity_table.csv` | capacity only |
| R10a 溶质闭合 | **5.71e-19 (relative)** | `A30_WP0取证/a21_solute_closure_summary.json` | PASS |
| volume-only 通量平衡 | **1.93e-16 / 2.50e-16** | `A30_WP0取证/volonly_flux_balance_summary.json` | PASS |
| E3 仅化学准确率 | **0.6746** | `A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json` | < 0.8090 baseline |
| E3 多数类基线 | **0.8090** | `同上` | majority class |
| E3b 折外中位增益 | **+0.0918** | `A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json` | 2/4 folds informative; candidate |
| H4 IEUA q | **−0.096 → 24/24负** | `A32_WP3_水化学/wp3_h4_robustness_summary.json` | complete species |
| H4 LADWP q | **+0.223 → 23/23正** | `同上` | complete species |
| WP5 主导参数 | **limit_scale ST=0.944** | `A34_WP5_敏感性与极端事件/wp5_sobol.csv` | IEUA |
| WP5 碱度杠杆 | **临界≈2.62×** | `A34_WP5_敏感性与极端事件/wp5_morris.csv` | 唯一符号杠杆 (cited tier) |
| 极端事件翻转 | **0/8** | `A34_WP5_敏感性与极端事件/wp5_extreme_summary.json` | observation-driven |
| NE-1 双路径符号 | **4/4 (2 平凡, n_eff=2)** | `A38_模拟审稿/ne1_r10a_signflip_summary.json` | direction robust |
| NE-1 量级差 | **≈800×** | `同上` | +9.8% vs +0.012% |
| NE-2 strict 档绑定物种 | **silica / TDS** | `A38_模拟审稿/ne2_panel_robustness_summary.json` | alkalinity NOT binding |
| NE-4 x_alkalinity ST (IEUA) | **0.125 [0.015, 0.305]** | `A38_模拟审稿/ne4_sobol_bootstrap_summary.json` | significant |
| NE-4 x_alkalinity ST (LADWP) | **0.001 [0.000, 0.002]** | `同上` | effectively zero |
| WP8 B3 占比 | **40/141 = 28.4%** | `A39_WP8_外部效度/wp8_real_reuse_cases_summary.json` | largest category |
| WP8 规模落入模型域 | **26/38 = 68.4%** | `同上` | [1e3,1e5] m3/d |
| WP9 冷却水占比均值 | **0.25799037378455597** | `A39_WP8_外部效度/wp9_cooling_share_summary.json` | byte-identical to A24 |
| WP9 行业区间 | **0.000–0.990** | `同上` | median 0.184 |
| WP10 工业水价中位 | **1.550 CNY/m3** | `A39_WP8_外部效度/wp10_water_price_summary.json` | 61 cities |
| WP10 再生水/水价 | **1.56** | `同上` | reuse dearer by ~56% |
| WP11 有正产能项目 | **11 (中位 3.0e4 m3/d)** | `A39_WP8_外部效度/wp11_reuse_deployment_summary.json` | 100% 落在模型域; 两块不一致不可相加 |
| WP11 投资强度 | **1.14e4 CNY/(m3/d)** | `同上` | 量级参考, 非 NPV |

---

## 3. 主张状态表（证据等级）

| 主张 | 证据强度 | 状态 | 说明 |
|---|---|---|---|
| 三分账（requested/delivered/abstracted 互不相等） | 强 | 已证 | 0/68 重合 |
| 统一恒等式 dS_pot = C − F | 强（但为恒等式） | E1 恒等式 | 不构成发现 |
| 符号判据 = 代数重排 | 强 | E1 恒等式 | 非发现 |
| q>0 ⇒ 城市受益 (263/263) | 中 | 样本内零例外 | **鉴别力不足**（无正例） |
| 净符号不能仅由化学判定 | 强（负结果） | 已证 | 0.671 < 0.861 |
| 加入分配量后折外预测更优 | **中等** | **候选判据** | 中位增益 +0.092; 仅 2/4 折有信息 |
| 碱度是唯一符号杠杆 | **弱** | **限定为 cited/permissive 档** | strict 档失效 (NE-2) |
| 中心结论方向对求解路径稳健 | 中 | 已证 | n_eff=2，机制仍路径依赖 (NE-1) |
| 极端事件不翻转符号 | 中 | 已证 | 观测驱动 0/8 |
| 工业冷却是真实主要用途 | 中 | 已证（案例集） | 28.4%，非随机样本 (WP8) |
| 冷却水占比 0.258 | 强 | 已追溯 | 与源数据逐位一致 (WP9) |
| 再生水成本高于工业水价 | 中 | 量级对照 | 比 1.56，**非因果** (WP10) |
| 真实产能项目规模与模型域吻合 | 中 | 已证（项目集） | 11/11 落在 1e3–1e5 (WP11) |
| committed 制度占比 | — | **不可识别** | 界 [0%,100%] (A24b) |
| 真实城市/设施标定 | — | **未做** | 根本瓶颈 |

---

## 4. 本轮数字复算结果

| 检验 | 复算 | 期望 | 结果 |
|---|---:|---:|:---:|
| 可靠子集 n | 839.0 | 839.0 | ✅ |
| 恒等式绝对残差 | 4.3655745685100555e-11 | 4.365575e-11 | ✅ |
| dS<0 | 626.0 | 626.0 | ✅ |
| dS>0 | 177.0 | 177.0 | ✅ |
| dS=0 | 36.0 | 36.0 | ✅ |
| q>0 组 | 263.0 | 263.0 | ✅ |
| q>0 且有害 | 0.0 | 0.0 | ✅ |
| 留出 R² | 0.7660719253900063 | 0.7660719253900063 | ✅ |
| 桥接配对 | 24.0 | 24.0 | ✅ |
| A24b 界=[0,100] | {'lower': 0.0, 'upper': 100.0} | {'lower': 0, 'upper': 100} | ✅ |
| E3 verdict | NOT_PREDICTIVE | NOT_PREDICTIVE | ✅ |
| E3b 折外中位增益 | 0.0918367346938776 | 0.0918 | ✅ |
| NE-2 strict 档绑定物种 | ['TDS', 'silica'] | ['TDS', 'silica'] | ✅ |
| WP8 B3 为最大类别 | 40 | 40 | ✅ |
| WP9 与 A24 逐位一致 | 0.25799037378455597 | 0.25799037378455597 | ✅ |
| WP10 比价 | 1.5564516129032258 | 1.5564516129032258 | ✅ |
| WP11 两块不一致且 11 个正产能 | 11 | 11 | ✅ |

---

## 5. 运行全部门禁

```bash
cd 10_论文推进_2026Q4
PYTHONIOENCODING=utf-8 python A36_终审/final_gate.py          # 终审门禁 (应全部 PASS)
PYTHONIOENCODING=utf-8 python A40_投稿包/make_reproducibility_manifest.py  # 本清单
PYTHONIOENCODING=utf-8 python A37_六主图_v4/_gate_check.py    # 图件门禁
PYTHONIOENCODING=utf-8 python A37_六主图_v4/make_all_figures.py  # 重绘全部主图
```

## 6. 已撤回的主张（不得复活）

| 主张 | 撤回原因 |
|---|---|
| 95%/93% 真实设施已处于已承诺状态 | **不可识别**：只观测供方产能，未观测需方需求；界 [0%,100%] |
| 更干净 ⇒ 更省补水 ⇒ 更有利 | 实测 $x_{\rm AI}$ 主导（corr −0.93），$q$ 仅 −0.16 |
| 判据吻合率 1.0000 具有预测力 | E3 严格检验 0.671 < 基线 0.861 |
| 加入分配量后折外预测更优 | 单折驱动，中位增益 0.000 |
| 碱度是普适的唯一符号杠杆 | strict 限值档下绑定物种变为 silica/TDS 且无杠杆 |
| 高盐度再生水反转 committed 结果 | 依赖不完整样本 + 不可追溯均值 |
| 两条符号相反通道 / ψ / φ* / 供水下限 | 2026-10-14 已撤回（量纲/范畴错误） |

## 7. 明确未完成的项

- **真实城市/设施标定**：未做（无需求侧数据）—— 本文最大瓶颈；
- **NE-3 温度维**：需外部热力学数据库，本地不可得；
- **流域净耗水**：未建模（城市取水 ≠ 流域耗水）；
- **投资/成本结论**：无寿命与折现数据，未做。
