# 陈旧数字 / 不可追溯断言 / 内部矛盾 —— 逐数字机器核对报告

> ⚠️ **本文件含 2026-10-17 之前的历史数字**（如 n=813、643/134/36）。
> 当日修复 P0-1（Figshare 水样回灌 A19 提取的 SO4/碱度）后，现行值为
> **n=839、626/177/36、q 分组 263/288/288**。
> 本文件作为审计留痕保留原值，**当前结论请以主稿与 SI 为准**。

**审计对象**: `A16_英文稿/manuscript_en_v3.md`、`A16_英文稿/supplementary_information.md`（只读，未做任何修改）
**生成脚本**: `A30_WP0取证/audit_stale_numbers.py`

**运行命令**（在 `10_论文推进_2026Q4/` 下）:

```bash
PYTHONIOENCODING=utf-8 python A30_WP0取证/audit_stale_numbers.py
```

---

## 0. 结论摘要

- 机械提取并核对数值型断言 **193** 条。
- 五类裁定分布：**VERIFIED 107**、**STALE 26**、**UNTRACEABLE 48**、**FORBIDDEN_CLAIM 3**、**NOT_A_CLAIM 9**
- 稿件 SHA256 已记录在 JSON 中，保证本报告对应确切的稿件版本。

## 1. 关键重算（不依赖 summary 二手数字）

| 重算量 | 脚本独立结果 | 对应产物字段 |
|---|---|---|
| A17 主网格总行数 | 1052 | supply_state_summary.n_scenarios=1052 |
| status==converged_unique | 1001 | convergence_audit=1094（占位档 1152） |
| coc_floor_degenerate | 188 | reliable_subset.n_coc_floor_degenerate=188 |
| 双门禁可靠子集 | **813** | reliable_subset.n_reliable=813 |
| dS_pot<0（可靠子集） | 643 | reliable_n_dS_neg=631 |
| dS_pot>0（可靠子集） | 134 | reliable_n_dS_pos=102 |
| zero-displacement | 372 | reliable_n_zero_disp=372 |
| q>0 | 290 | reliable_n_q_pos=290 |
| q>0 且 harmful | 0 | reliable_n_qpos_but_harmful=0 |
| dS_pot vs dS_ident 绝对残差 max | 63839 ML | ⚠ 这是**另一个量**, 稿件未区分 |
| **统一通式残差** max（813 子集） | **2.54659e-11 ML** | ✓ 与稿件 `2.5e-11` **一致** |
| 统一通式残差 max（1052 全表） | 2.80451e-06 ML | = `unified_identity_max_err_ml` |
| 相对中位 | 2.62219e-15（相对 median\|dS\|） | 机器精度 |

组成拆分（可靠子集，脚本重算 vs 稿件）：

| 水样 | 重算 dS<0 | 重算 dS>0 | 重算 =0 | 稿件 dS<0 | 稿件 dS>0 |
|---|---:|---:|---:|---:|---:|
| AI-UWM model assumption | 187 | 8 | 9 | 184 | 0 |
| Figshare RW (2025, paired study) | 119 | 62 | 9 | 116 | 54 |
| IEUA RP-1 (2025, tertiary) | 151 | 56 | 9 | 148 | 48 |
| LADWP AWPF (2012, RO product) | 186 | 8 | 9 | 183 | 0 |

- A13c `potable_flows.csv`：重算 408 行，converged_unique 372，剔除 36（{'quality_not_converged': 24, 'converged_unique': 372, 'no_convergence': 8, 'non_unique': 4}）
- A15 `ablation_matrix.csv`：重算 64 行，reliable 58，份额口径( dp=0, n=30) 残差 max = 7.27596e-12 ML，含容量扩张口径 max = 15030.1 ML
- A20 v2 重算：24 对，符号一致 23/24 = 0.958333，按水样 {'IEUA RP-1 (2025, tertiary)': '12/12', 'LADWP AWPF (2012, RO product)': '11/12'}，M0 最大相对差 8.69763e-16
- A20 v1（历史 36 对）重算：36 对，符号一致 24/36，按水样 {'IEUA RP-1 (2025, tertiary)': '12/12', 'LADWP AWPF (2012, RO product)': '8/12', 'Figshare RW (2025, paired study)': '4/12'} —— 与稿件撤回说明一致
- A24 外部重算：设计能力分位 D-HA = 80.8886%，D-CO = 80.7685%；committed 最小占比 = 93.451%

---

## 2. 总表

| # | 数值 | 位置行号 | 稿件值 | 权威产物值 | 裁定 | 产物路径 |
|---:|---|---|---|---|---|---|
| 1 | 68 | manuscript:L18 | 68 engine runs (0/68 rows agree) | 68 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 2 | 0.849 | manuscript:L19 | path efficiency 0.849 | 0.848658 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 3 | 1.178 | manuscript:L20 | 1/eta_path = 1.178 | 1.17833 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 4 | 6713 | manuscript:L77 | phantom abstraction up to 6,713 ML (D-HA) | 6712.82 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 5 | 6121 | manuscript:L77 | 6,121 ML (D-CO) | 6120.87 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 6 | 2.5e-11 | manuscript:L19 | residual 2.5e-11 ML across 813 scenarios | 2.54659e-11 | **VERIFIED** | `A13_可靠性机制/supply_state_regimes.csv（独立重算）` |
| 7 | 2.9e-16 | manuscript:L19 | relative 2.9e-16 machine precision | — | **UNTRACEABLE** | `—` |
| 8 | 813 | manuscript:L21 | 813 solver-reliable scenarios | 813 | **VERIFIED** | `A13_可靠性机制/supply_state_regimes.csv + A13_可靠性机制/supply_state_summary.json` |
| 9 | 429 | manuscript:L108 | negative in 429 of 446 cases | 749 | **STALE** | `A25_终审/convergence_impact.json` |
| 10 | 17 | manuscript:L7 | The 17 exceptions in branch C | — | **UNTRACEABLE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 11 | 1.1e-11 | manuscript:L19 | branch-degradation residual 1.1e-11 (A) | — | **UNTRACEABLE** | `—` |
| 12 | 1.5e-11 | manuscript:L19 | branch-degradation residual 1.5e-11 (C) | — | **UNTRACEABLE** | `—` |
| 13 | 1.3e-15 | manuscript:L19 | residual 1.3e-15 (dimensionless form) | 5.55112e-17 | **VERIFIED** | `A22_判据分解/q_theory_summary.json` |
| 14 | 5.6e-17 | manuscript:L19 | verified to 5.6e-17 | 5.55112e-17 | **VERIFIED** | `A22_判据分解/q_theory_summary.json` |
| 15 | 290 | manuscript:L30 | q>0 group n=290 | 290 | **VERIFIED** | `A13_可靠性机制/supply_state_regimes.csv + supply_state_summary.json` |
| 16 | 290/290 | SI:L77 | 290 of 290 city benefit, no exception | 290 | **VERIFIED** | `A13_可靠性机制/supply_state_summary.json` |
| 17 | 288 | manuscript:L144 | q~0 group n=288 | — | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 18 | -14496 | manuscript:L143 | median dS_pot for q>0 = -14,496 | — | **UNTRACEABLE** | `A22_判据分解/derived_criterion_summary.json` |
| 19 | 235 | manuscript:L145 | q<0 group n=235 | — | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 20 | 102 | manuscript:L145 | withdrawal rises = 102 | 102 | **VERIFIED** | `A13_可靠性机制/supply_state_summary.json` |
| 21 | 631 | manuscript:L224 | withdrawal falls = 631 | 631 | **VERIFIED** | `A13_可靠性机制/supply_state_summary.json` |
| 22 | 0.803 | manuscript:L188 | best of seven candidates reaches 0.803 accuracy | — | **STALE** | `A22_判据分解/q_predictors_summary.json` |
| 23 | 1094 | manuscript:L223 | solver-reliable sample n=1,094 | 1094 | **VERIFIED** | `A25_终审/convergence_audit.json` |
| 24 | 1152 | manuscript:L242 | 58 of 1,152 scenarios (5.0%) | 58 | **VERIFIED** | `A25_终审/convergence_audit.json` |
| 25 | 58 | manuscript:L242 | 58 solver failures (38 no_conv / 20 non_unique) | 58 | **VERIFIED** | `A25_终审/convergence_audit.json` |
| 26 | 408 | manuscript:L251 | A13c: 35/408 | 408 | **VERIFIED** | `A25_终审/convergence_impact.json` |
| 27 | 1.16e-10 | manuscript:L19 | identity residual 1.16e-10 ML | 1.16415e-10 | **VERIFIED** | `A25_终审/convergence_impact.json` |
| 28 | 1.0000 | manuscript:L20 | sign criterion agreement 1.0000 | 1 | **VERIFIED** | `A25_终审/convergence_audit.json` |
| 29 | 11,535 | manuscript:L265 | dS = M1-M0 = -11,535 ML (M0 104,948 / M1 93,414) | — | **STALE** | `A13_可靠性机制/OBSOLETE_reliability_grid.csv` |
| 30 | 14196 | manuscript:L251 | grid scan: 541/14,196 | 14196 | **VERIFIED** | `A25_终审/convergence_impact.json` |
| 31 | 1200 | manuscript:L211 | placeholder 700+500 = 1200 vs 1100 | 1200 | **VERIFIED** | `A4_水化学参数域/T6b_cited_limits_summary.json` |
| 32 | 2200 | manuscript:L216 | baseline 2200 | 2200 | **VERIFIED** | `A4_水化学参数域/T6b_cited_limits_summary.json` |
| 33 | 700 | manuscript:L211 | baseline 700 | 700 | **VERIFIED** | `A4_水化学参数域/T6b_cited_limits_summary.json` |
| 34 | 750 | manuscript:L217 | baseline 750 | 750 | **VERIFIED** | `A4_水化学参数域/T6b_cited_limits_summary.json` |
| 35 | 350 | manuscript:L217 | baseline 350 | 350 | **VERIFIED** | `A4_水化学参数域/T6b_cited_limits_summary.json` |
| 36 | 175 | manuscript:L217 | baseline 175 | 175 | **VERIFIED** | `A4_水化学参数域/T6b_cited_limits_summary.json` |
| 37 | 1100 | manuscript:L211 | hardness+alkalinity = 1100 ✓ | 1100 | **VERIFIED** | `A4_水化学参数域/T6b_cited_limits_summary.json` |
| 38 | 285 | manuscript:L223 | placeholder withdrawal-rises = 285 | 285 | **VERIFIED** | `A25_终审/convergence_impact.json` |
| 39 | 729 | manuscript:L224 | placeholder withdrawal-falls = 729 | 729 | **VERIFIED** | `A25_终审/convergence_impact.json` |
| 40 | 372 | SI:L137 | zero-displacement = 372 | 372 | **VERIFIED** | `A13_可靠性机制/supply_state_regimes.csv + supply_state_summary.json` |
| 41 | 188 | manuscript:L230 | 188 degenerate scenarios excluded | 188 | **VERIFIED** | `A13_可靠性机制/supply_state_regimes.csv + supply_state_summary.json` |
| 42 | 2.8e-6 | manuscript:L19 | residual appeared to degrade to 2.8e-6 | 2.80451e-06 | **VERIFIED** | `A13_可靠性机制/supply_state_summary.json` |
| 43 | 2e10 | manuscript:L230 | makeup degenerates to ~2e10 ML | — | **VERIFIED** | `A13_可靠性机制/OBSOLETE_reliability_grid.csv` |
| 44 | 380 | manuscript:L269 | W_nat = 380 ML/day | 380 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 45 | 342 | manuscript:L275 | W_engage = 342 | 342 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 46 | 323 | manuscript:L276 | W_gap = 323 | 323 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 47 | 304 | manuscript:L277 | W*_break = 304 | 304 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 48 | 62080 | manuscript:L35 | service gap up to 62,080 ML | 62080.4 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 49 | 8519 | manuscript:L285 | DC curtailed up to 8,519 ML | 8519.02 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 50 | 27354 | manuscript:L25 | up to 27,354 ML per period | — | **UNTRACEABLE** | `A20_模型桥接/A20_桥接报告.md` |
| 51 | 103413 | manuscript:? | max requested-delivered 103,413.9 | 103414 | **NOT_A_CLAIM** | `A18_有限供水/finite_supply_summary.json` |
| 52 | 0.000000 | manuscript:L19 | committed branch dS = 0.000000 exactly (80/80) | max \|dS_pot\| = 0.000 ML | **VERIFIED** | `A15_稳健性/ablation_summary.json` |
| 53 | 22359 | manuscript:L299 | surplus down to -22,359 ML | -22541.2 | **STALE** | `A18_有限供水/finite_supply_summary.json` |
| 54 | 19726 | manuscript:L313 | LADWP mean dS_pot surplus -19,726 | — | **UNTRACEABLE** | `—` |
| 55 | 8510 | manuscript:L313 | LADWP committed -8,510 | — | **UNTRACEABLE** | `—` |
| 56 | 12257 | manuscript:L314 | IEUA surplus -12,257 | — | **UNTRACEABLE** | `—` |
| 57 | 4690 | manuscript:L314 | IEUA committed -4,690 | — | **UNTRACEABLE** | `—` |
| 58 | 16359 | manuscript:L315 | AI-UWM surplus -16,359 | — | **UNTRACEABLE** | `—` |
| 59 | 7504 | manuscript:L315 | AI-UWM committed -7,504 | — | **UNTRACEABLE** | `—` |
| 60 | 8895 | manuscript:L316 | Figshare surplus +8,895 | — | **UNTRACEABLE** | `—` |
| 61 | 28437 | manuscript:L316 | Figshare committed +28,437 | — | **UNTRACEABLE** | `19_缺陷报告_缓存与桥接_2026-10-15.md` |
| 62 | 5.99e5 | manuscript:L326 | response up to 5.99e5 ML at tier 0.25 | — | **UNTRACEABLE** | `—` |
| 63 | 0.504 | manuscript:L324 | PHREEQC calcite limited IEUA 2.52/5.0 = 0.504 | — | **NOT_A_CLAIM** | `18_方法自审与修复报告_2026-10-14.md` |
| 64 | 4.34 | manuscript:L323 | CoC 4.34-4.91 (GSA/NREL 2023) | — | **NOT_A_CLAIM** | `—` |
| 65 | 0.98 | manuscript:L322 | tier 0.98 | — | **NOT_A_CLAIM** | `A26_语义统一/CHI_SEMANTICS.md` |
| 66 | 39 | manuscript:L330 | 11 of 39 scanned curves non-monotone | 39 | **VERIFIED** | `A15_稳健性/grid_resolution_summary.json` |
| 67 | 11 | manuscript:L265 | 11/39 non-monotone | 11 | **VERIFIED** | `A15_稳健性/grid_resolution_summary.json` |
| 68 | 0.015625 | manuscript:L335 | boundary moves at most one grid step 0.015625 | 0.015625 | **VERIFIED** | `A15_稳健性/grid_resolution_summary.json` |
| 69 | 10826 | manuscript:L40 | 10,826 observed WWTPs | 10826 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 70 | 1.0000 | manuscript:L20 | load rate r = 1.0000 | — | **UNTRACEABLE** | `A24_外部锚定/external_anchor_summary.json` |
| 71 | 8.0 | manuscript:L285 | design capacity median 8.0 ML/d | 8 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 72 | 25 | manuscript:L263 | P75 = 25 ML/d | 25 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 73 | 60 | manuscript:L348 | P90 = 60 ML/d | — | **UNTRACEABLE** | `A24_外部锚定/external_wwtp_capacity.csv` |
| 74 | 268599 | manuscript:L349 | aggregate design capacity 268,599 ML/d | 268599 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 75 | 0.594 | manuscript:L42 | load rate median 0.594 | 0.594274 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 76 | 0.83 | manuscript:L350 | P75 load rate 0.83 | 0.827509 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 77 | 6.2 | manuscript:L350 | above 1 in 6.2% | 6.23499 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 78 | 0.184 | manuscript:L351 | industrial cooling-water share 0.184 (39 sectors) | — | **UNTRACEABLE** | `A24_外部锚定/external_anchor_summary.json` |
| 79 | 1.45 | manuscript:L352 | urban water price median 1.45 CNY/m3 (n=39,083) | 1.45 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 80 | 33.4 | manuscript:L357 | deliverable supply 33.4 ML/d (D-HA) | 33.4308 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 81 | 30.7 | manuscript:L357 | 30.7 ML/d (D-CO) | 30.7041 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 82 | 81 | manuscript:L41 | 81st percentile of 10,826 plants | 80.8886 | **VERIFIED** | `A24_外部锚定/external_wwtp_capacity.csv + A24_外部锚定/A24_外部锚定报告.md` |
| 83 | 2.0 | manuscript:L3 | surplus first appears at pool_scale = 2.0 | 2 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 84 | 2.2 | manuscript:L384 | 50% prevalence at 2.2 (D-HA) | 2.2 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 85 | 2.4 | manuscript:L384 | 2.4 (D-CO) | 2.4 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 86 | 66.9 | manuscript:L385 | approx 66.9 ML/d first appearance (D-HA) | 66.8615 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 87 | 61.4 | manuscript:L385 | 61.4 ML/d (D-CO) | 61.4082 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 88 | 73.5 | manuscript:L385 | 73.5 ML/d 50% level (D-HA) | 73.5477 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 89 | 73.7 | manuscript:L385 | 73.7 ML/d (D-CO) | 73.6898 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 90 | 3.0 | manuscript:L3 | treated volume median 3.0 ML/d | 3 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 91 | 16.8 | manuscript:L396 | P75 16.8 | 16.7571 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 92 | 44.4 | manuscript:L396 | P90 44.4 | 44.4384 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 93 | 77.8 | manuscript:L396 | P95 77.8 | 77.7634 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 94 | 93 | manuscript:L265 | committed branch dominates: above 93% | 93.451 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 95 | 95 | manuscript:L43 | above 95% of plants are fully committed | 93.451 | **FORBIDDEN_CLAIM** | `A24_外部锚定/external_validity_summary.json + A24_外部锚定/A24_外部锚定报告.md` |
| 96 | 2.0 | manuscript:L3 | surplus regime covers only ~2-5% | — | **FORBIDDEN_CLAIM** | `A24_外部锚定/external_validity_summary.json` |
| 97 | 99 | manuscript:L399 | above 99% for r<=0.3 | 98.956 | **VERIFIED** | `A24_外部锚定/external_validity_summary.json` |
| 98 | 64 | manuscript:L417 | Ablation 2^3 factorial (64 cells) | 64 | **VERIFIED** | `A15_稳健性/ablation_matrix.csv` |
| 99 | 5/5 | manuscript:L417 | 5/5 gates | True | **VERIFIED** | `A15_稳健性/ablation_summary.json` |
| 100 | 3.6e-12 | manuscript:L19 | ablation identity residual 3.6e-12 | 15030.1 | **STALE** | `A15_稳健性/ablation_matrix.csv + A25_终审/a15_gates_reliable.json` |
| 101 | 0.557 | manuscript:L418 | Cross-domain holdout R2 = 0.557 | 0.805594 | **STALE** | `A15_稳健性/holdout_summary.json` |
| 102 | -0.050 | manuscript:L418 | baseline -0.050 | -0.0732839 | **STALE** | `A15_稳健性/holdout_summary.json` |
| 103 | -0.044 | SI:L358 | baseline -0.044 | -0.0732839 | **STALE** | `A15_稳健性/holdout_summary.json` |
| 104 | 0.558 | SI:L358 | true holdout R2 = 0.558 | 0.805594 | **STALE** | `A15_稳健性/holdout_summary.json` |
| 105 | 0.5574 | manuscript:L418 | 0.5574 on the solver-reliable subset | 0.805594 | **STALE** | `A15_稳健性/holdout_summary.json` |
| 106 | 0.5582 | manuscript:L425 | 0.5582 unfiltered | 0.805594 | **STALE** | `A15_稳健性/holdout_summary.json` |
| 107 | 1.000 | manuscript:L20 | identity's cross-domain R2 = 1.000 | 1 | **VERIFIED** | `A15_稳健性/holdout_summary.json` |
| 108 | 0.0 | manuscript:L19 | no-quality extreme dS_pot = 0 exactly | 0 | **VERIFIED** | `A15_稳健性/holdout_summary.json` |
| 109 | 6478 | manuscript:L420 | quality monotonicity 6,478 -> 21,674 -> 116,581 | — | **UNTRACEABLE** | `A15_稳健性/holdout_summary.json` |
| 110 | 21674 | manuscript:L420 | 21,674 | — | **UNTRACEABLE** | `—` |
| 111 | 116581 | manuscript:L420 | 116,581 | — | **UNTRACEABLE** | `—` |
| 112 | 0 | manuscript:L19 | 0 falsifiers (H1-H4) | — | **UNTRACEABLE** | `A18_有限供水/finite_supply_summary.json` |
| 113 | 68 | manuscript:L18 | 0/68 coincidences | 68 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 114 | 2.9e-11 | manuscript:L19 | exact identity residual 2.9e-11 | — | **UNTRACEABLE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 115 | 380/400 | manuscript:L447 | potable cap 380/400 ML/day | 400 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 116 | 46 | manuscript:L465 | reduces makeup by 46% | — | **UNTRACEABLE** | `A21_动态状态/dynamic_criterion_summary.json` |
| 117 | 7.99 | manuscript:L464 | CoC 7.99 vs 1.82 at phi=0.6 | 7.98638 | **VERIFIED** | `A21_动态状态/dynamic_criterion_summary.json` |
| 118 | 1.82 | manuscript:L464 | 1.82 | 1.82364 | **VERIFIED** | `A21_动态状态/dynamic_criterion_summary.json` |
| 119 | 3.45 | manuscript:L473 | +3.45% (D-HA) storage raises makeup | — | **UNTRACEABLE** | `A21_动态状态/dynamic_state_summary.json` |
| 120 | 7.02 | manuscript:L473 | +7.02% (D-CO) | — | **UNTRACEABLE** | `A21_动态状态/dynamic_state_summary.json` |
| 121 | 2.1 | manuscript:L483 | CoC envelope [2.1, 4.9] | — | **NOT_A_CLAIM** | `A19_水化学包络/` |
| 122 | 4.9 | manuscript:L483 | CoC envelope upper 4.9 | — | **NOT_A_CLAIM** | `A19_水化学包络/` |
| 123 | 30 | manuscript:L219 | temperature can shift CoC by -30% | — | **NOT_A_CLAIM** | `—` |
| 124 | 5.000 | manuscript:L44 | realised CoC = design 5.000 | 188 | **NOT_A_CLAIM** | `A13_可靠性机制/supply_state_regimes.csv` |
| 125 | 1.60 | manuscript:L496 | inflating results by 1.60x | — | **UNTRACEABLE** | `19_缺陷报告_缓存与桥接_2026-10-15.md` |
| 126 | 36504 | manuscript:L497 | 36,504 = 36,504 ML | — | **UNTRACEABLE** | `A20_模型桥接/bridging_pairs_full.json` |
| 127 | 5.1e-16 | manuscript:L19 | median relative difference 5.1e-16 | 5.08211e-16 | **VERIFIED** | `A20_模型桥接/bridging_summary_v2.json` |
| 128 | 24/24 | manuscript:L514 | identical in 24/24 paired runs | 24 | **VERIFIED** | `A20_模型桥接/bridging_comparison_v2.csv` |
| 129 | 23 of 24 | manuscript:L516 | sign agrees in 23 of 24 (0.958) | 23 | **VERIFIED** | `A20_模型桥接/bridging_comparison_v2.csv + bridging_summary_v2.json` |
| 130 | 12/12 | manuscript:L516 | IEUA 12/12 | 12/12 | **VERIFIED** | `A20_模型桥接/bridging_comparison_v2.csv` |
| 131 | 11/12 | manuscript:L516 | LADWP 11/12 | 11/12 | **VERIFIED** | `A20_模型桥接/bridging_comparison_v2.csv` |
| 132 | 36 | manuscript:L497 | earlier 36-pair comparison (withdrawn) | 36 | **VERIFIED** | `A20_模型桥接/bridging_comparison.csv` |
| 133 | 0.667 | manuscript:L520 | 24/36 = 0.667 | 0.666667 | **VERIFIED** | `A20_模型桥接/bridging_comparison.csv` |
| 134 | 116 | manuscript:L158 | Figshare RW dS<0 = 116 / dS>0 = 54 | 119 | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 135 | 183 | manuscript:L155 | LADWP dS<0 = 183 | 186 | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 136 | 184 | manuscript:L156 | AI-UWM placeholder dS<0 = 184 | 187 | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 137 | 148 | manuscript:L157 | IEUA dS<0 = 148 | 151 | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 138 | 48 | manuscript:L157 | IEUA dS>0 = 48 | 56 | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 139 | 54 | manuscript:L158 | Figshare dS>0 = 54 | 62 | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 140 | 31 | manuscript:L162 | 31 harmful cases attributed to LADWP | — | **VERIFIED** | `A25_终审/A25_全面终审报告.md` |
| 141 | 7 | manuscript:L144 | 7 harmful for the placeholder | — | **VERIFIED** | `A25_终审/A25_全面终审报告.md` |
| 142 | 237 | manuscript:L262 | reliable counts 237/0 (LADWP) | — | **UNTRACEABLE** | `—` |
| 143 | 241 | manuscript:L262 | reliable counts 241/0 (AI-UWM) | — | **UNTRACEABLE** | `—` |
| 144 | 38 | manuscript:L243 | 38 'withdrawal rises' in q~0 group (before gate), now 0 | 38 | **VERIFIED** | `A25_终审/convergence_audit.json + A13_可靠性机制/OBSOLETE_reliability_grid.csv` |
| 145 | 192 | manuscript:L199 | imputing over 192 scenarios | 16 | **STALE** | `A22_判据分解/missing_quality_summary.json` |
| 146 | 2869 | manuscript:L200 | makeup changes by up to 2,869 ML | — | **UNTRACEABLE** | `A22_判据分解/missing_quality_summary.json` |
| 147 | 0/192 | manuscript:L200 | zero sign flips in q (0/192) | 0 | **VERIFIED** | `A22_判据分解/missing_quality_summary.json` |
| 148 | 1052 | SI:L183 | scenarios (all) = 1,052 | 1052 | **VERIFIED** | `A13_可靠性机制/supply_state_regimes.csv + supply_state_summary.json` |
| 149 | 1152 | SI:L57 | 1,152 scenarios | 1152 | **VERIFIED** | `A25_终审/convergence_audit.json` |
| 150 | 2.55e-11 | SI:L15 | identity residual 2.55e-11 (cited) | 2.54659e-11 | **VERIFIED** | `A13_可靠性机制/supply_state_regimes.csv（独立重算）` |
| 151 | 1094 | SI:L134 | reliable scenarios 1,094 (placeholder col) | 1094 | **VERIFIED** | `A25_终审/convergence_audit.json` |
| 152 | 329 | SI:L138 | q>0 329 (placeholder) | — | **STALE** | `A25_终审/convergence_impact.json` |
| 153 | 441 | SI:L137 | zero-displacement 441 (placeholder) | 441 | **VERIFIED** | `A25_终审/convergence_impact.json` |
| 154 | 0.83 | SI:L399 | load rate P25 0.31 / P50 0.594 / P75 0.83 / P90 0.97 | 0.973044 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 155 | 0.09 | SI:L399 | load rate P10 0.09 | 0.0917069 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 156 | 2683047 | SI:L389 | archive retrieved 2,683,047 bytes | — | **UNTRACEABLE** | `A24_外部锚定/external_anchor_summary.json` |
| 157 | 0.625 | SI:L150 | IEUA alkalinity 87.5 vs 140, ratio 0.625 < 1 | — | **UNTRACEABLE** | `A4_水化学参数域/T6b_cited_limits_summary.json` |
| 158 | 87.5 | SI:L150 | alkalinity 87.5 mg/L | — | **UNTRACEABLE** | `A4_水化学参数域/T6b_cited_limits_summary.json` |
| 159 | 140 | SI:L150 | water concentration 140 mg/L | — | **UNTRACEABLE** | `—` |
| 160 | 58 | SI:L105 | share of scenarios where constraint binds at 0.98 = 58% | ['limit_scale', 'chi_strictness', 'quality_binding'] | **UNTRACEABLE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 161 | 92 | SI:L104 | 0.50 binds 92% | — | **UNTRACEABLE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 162 | 100 | SI:L103 | 0.25 binds 100% | — | **UNTRACEABLE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 163 | 48 | SI:L106 | 1.0 binds 48% | — | **UNTRACEABLE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 164 | 0 | SI:L15 | 1e6 binds 0% | — | **UNTRACEABLE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 165 | 9.77e-15 | SI:L15 | water closure 9.77e-15 ML on both paths | 9.76996e-15 | **VERIFIED** | `A21_动态状态/dynamic_criterion_summary.json` |
| 166 | 0.504 | SI:L90 | PHREEQC calcite limited IEUA 0.504 | — | **NOT_A_CLAIM** | `18_方法自审与修复报告_2026-10-14.md` |
| 167 | 16 | SI:L1 | mass balance M/B = CoC, 16/16 | — | **UNTRACEABLE** | `A21_动态状态/dynamic_state_summary.json` |
| 168 | 47 735 | SI:L291 | makeup at phi=0.6 47,735 ML (volume-only) | 47734.8 | **VERIFIED** | `A21_动态状态/reuse_quality_verdict_summary.json` |
| 169 | 25 804 | SI:L291 | 25,804 ML (-46%) dynamic path | 25804.3 | **VERIFIED** | `A21_动态状态/reuse_quality_verdict_summary.json` |
| 170 | 5.500 | SI:L288 | CoC at phi=0 = 5.500 | 5.5 | **VERIFIED** | `A21_动态状态/dynamic_criterion_summary.json` |
| 171 | 2.292 | SI:L289 | CoC at phi=0.4 volume-only = 2.292 | 2.29167 | **VERIFIED** | `A21_动态状态/dynamic_criterion_summary.json` |
| 172 | 7.801 | SI:L289 | CoC at phi=0.4 dynamic = 7.801 | 7.80058 | **VERIFIED** | `A21_动态状态/dynamic_criterion_summary.json` |
| 173 | 1.824 | SI:L290 | CoC at phi=0.6 volume-only = 1.824 | 1.82364 | **VERIFIED** | `A21_动态状态/dynamic_criterion_summary.json` |
| 174 | 7.986 | SI:L290 | CoC at phi=0.6 dynamic = 7.986 | 7.98638 | **VERIFIED** | `A21_动态状态/dynamic_criterion_summary.json` |
| 175 | 2,828 | SI:L447 | 2,828 ML unused at pool_scale=1.5 (note: SI 写 2,828/11,896) | — | **UNTRACEABLE** | `A24_外部锚定/surplus_threshold_check.json` |
| 176 | 11896 | SI:L448 | 11,896 ML displacement at pool_scale=1.5 | — | **UNTRACEABLE** | `A24_外部锚定/external_validity_summary.json` |
| 177 | 114 | SI:L528 | 114 purely-displaced cases are negative | — | **UNTRACEABLE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 178 | 41.6 | SI:L415 | earlier 41.6%/29.8%/28.6% (withdrawn) | 41.5481 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 179 | 29.8 | SI:L415 | 29.8% (withdrawn) | 29.8263 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 180 | 28.6 | SI:L415 | 28.6% (withdrawn) | 28.6255 | **VERIFIED** | `A24_外部锚定/external_anchor_summary.json` |
| 181 | 68 | SI:L37 | 68 runs x 730 days | 730 | **VERIFIED** | `A18_有限供水/finite_supply_summary.json` |
| 182 | 0.557 | manuscript:L418 | R2 = 0.557 (both occurrences) | 0.805594 | **STALE** | `A15_稳健性/holdout_summary.json` |
| 183 | above 95% | manuscript:L43 | above 95% / above 93% of real facilities fully committed | 93.451 | **FORBIDDEN_CLAIM** | `A24_外部锚定/external_validity_summary.json` |
| 184 | 36 | manuscript:L497 | 36 pairs段落 = 撤回说明, 非未解决冲突 | 36 | **VERIFIED** | `A20_模型桥接/bridging_comparison.csv + bridging_summary_v2.json` |
| 185 | 1094 | manuscript:L223 | testing seven candidates on n=1,094 | 813 | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 186 | 0.768 | manuscript:L33 | best of seven predictors 0.768 | 0.768229 | **VERIFIED** | `A22_判据分解/q_predictors_summary.json` |
| 187 | 0.456 | manuscript:L190 | AI-UWM assumption 0.456 | — | **UNTRACEABLE** | `A22_判据分解/q_predictors_summary.json` |
| 188 | 1.000 | manuscript:L20 | IEUA 1.000 | — | **UNTRACEABLE** | `A22_判据分解/q_predictors_summary.json` |
| 189 | 0.993 | manuscript:L189 | Figshare 0.993 | — | **UNTRACEABLE** | `A22_判据分解/q_predictors_summary.json` |
| 190 | 0.720 | manuscript:L190 | LADWP 0.720 | — | **UNTRACEABLE** | `A22_判据分解/q_predictors_summary.json` |
| 191 | 1052 | SI:L183 | 1,152 scenarios in the main grid | 1052 | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 192 | 58 | SI:L105 | 58 unreliable of 1,152 (5.03%) | {'converged_unique': 1001, 'no_convergence': 18, 'non_unique': 33} | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |
| 193 | 5.03 | SI:L164 | share 5.03% | — | **STALE** | `A13_可靠性机制/supply_state_regimes.csv` |

### 2.1 非 VERIFIED 条目的完整说明

- **UNTRACEABLE** `2.9e-16` @ manuscript:L19 — 无任何产物记录 2.9e-16 相对残差。
- **STALE** `429` @ manuscript:L108 — convergence_impact 给出 all=749 / ok=729 (占位档 1152); 446 是 zero_disp 的 all 值。429/446 既非全表也非可靠子集, 无产物支撑这两个数的配对。
- **UNTRACEABLE** `17` @ manuscript:L7 — 重算 gated 子集: 零挤占(displaced=0) 372 行中 dS_pot>0 仅 3 行, 不是 17。A25_终审/zero_disp_criterion.json 的 n_zero_disp 为 ha=241 / co=205。17 无产物支撑。
- **UNTRACEABLE** `1.1e-11` @ manuscript:L19 — 无产物记录该值。
- **UNTRACEABLE** `1.5e-11` @ manuscript:L19 — 无产物记录该值。
- **STALE** `288` @ manuscript:L144 — 重算 813 子集: q>0=290, q<0=235, 余 288。288 与总量 813 自洽, 但稿件同表未交代 288 的行数来源; 819 检验: 290+288+235=813 ✓ (数值本身可复现, 但该表 median 与 A22 不符, 见下条)
- **UNTRACEABLE** `-14496` @ manuscript:L143 — A22 记录的 q>0 组 dS_median=-14324.57 (占位档 349 组)。-14,496 在 A27 引用档下无任何产物记录。
- **STALE** `235` @ manuscript:L145 — 重算 813 子集 q<0=235 ✓ 数值可复现, 但同表 '133 falls / 102 rises' 与重算 133/102 一致; median -4,259 无产物记录
- **STALE** `0.803` @ manuscript:L188 — A22 产物最大 acc=0.7682291666666666 (P1a-P1d 四项并列); 无 0.803。 SI S3.2 同一数字写作 '七项最佳 0.768', 与主稿 0.803 内部矛盾。
- **STALE** `11,535` @ manuscript:L265 — 104948.41890780411 只出现在 **OBSOLETE_** 占位档产物 (A13 OBSOLETE_reliability_grid.csv, chi=0.25/phi=0.5, 且该行 status=quality_not_converged); M1=93,414 与 dS=-11,535 在任何产物中都找不到。该段落号称 limit_scale=0.25 且 phi=0.05, 但现行网格 phi 自 0.2 起, 无法复现。
- **UNTRACEABLE** `27354` @ manuscript:L25 — 27 354 只出现在 A20 桥接报告的 IEUA ha pool_scale=3.0 phi=0.4 行 (代表日 dS_pot), 非 Abstract 语境下的有限供水结果; 无对应机器产物字段。
- **NOT_A_CLAIM** `103413` @ manuscript:? — 稿件未直接写出该数; 记录以显示三账户上限可用
- **STALE** `22359` @ manuscript:L299 — surplus_arm.d_abstraction_ml=-22541.17, 不等于 -22,359; 无产物记录 22,359
- **UNTRACEABLE** `19726` @ manuscript:L313 — 无产物记录该组成均值
- **UNTRACEABLE** `8510` @ manuscript:L313 — 无产物记录该组成均值
- **UNTRACEABLE** `12257` @ manuscript:L314 — 同上
- **UNTRACEABLE** `4690` @ manuscript:L314 — 同上
- **UNTRACEABLE** `16359` @ manuscript:L315 — 同上
- **UNTRACEABLE** `7504` @ manuscript:L315 — 同上
- **UNTRACEABLE** `8895` @ manuscript:L316 — 同上
- **UNTRACEABLE** `28437` @ manuscript:L316 — 该值仅在缺陷报告正文出现, 非机器产物; 无 json/csv 支撑
- **UNTRACEABLE** `5.99e5` @ manuscript:L326 — 无产物记录
- **NOT_A_CLAIM** `0.504` @ manuscript:L324 — 文献/锚定值, 非本仓库机器产物
- **NOT_A_CLAIM** `4.34` @ manuscript:L323 — 文献锚定
- **NOT_A_CLAIM** `0.98` @ manuscript:L322 — 档位定义
- **UNTRACEABLE** `1.0000` @ manuscript:L20 — 该 r 由 final_audit 检查确认 ('D1 Load Rate 与年化/365/设计 相关 = 1.0'), 但该检验脚本(A28_末轮审计/final_audit.py) 未落盘数值产物; 数值本身无法从机器产物直接复核
- **UNTRACEABLE** `60` @ manuscript:L348 — summary 只给 median/p25/p75/max; 独立重算 P90=60.0 ML/d ✓ (由 CSV 直接可复现)
- **UNTRACEABLE** `0.184` @ manuscript:L351 — summary.other_anchors 给 mean_of_means=0.2580 (n_sectors=39), 不是 0.184; 0.184 无产物支撑 (SI 称 median of sector means)
- **FORBIDDEN_CLAIM** `95` @ manuscript:L43 — Abstract 写 'above 95% of plants' 而 §6b/SI 写 'above 93%': 内部矛盾。更重要的是, 该主张把 '实际处理量 x r' 当作'可交付再生水', 据此推断'已承诺需求'占比 —— 数据只观测到生产能力, 未观测已承诺需求 (SI S6b 已明确记录 41.6/29.8/28.6 的负荷率映射被撤回)。
- **FORBIDDEN_CLAIM** `2.0` @ manuscript:L3 — SI S6c 自陈 'surplus covers only 0.4-6.6%', 主稿 Abstract 写 ~2-5%: 区间不一致。且与上一条同属由 load-rate/规模反推 regime prevalence 的不可识别推断
- **STALE** `3.6e-12` @ manuscript:L19 — 重算 converged_unique 58 行 max|dS_pot-dS_pot_ident| = 7.275957614183426e-12 (=a15_gates_reliable.ablation.all.unified_resid_max); ablation_summary.identity_max_err_share_only_ml = 5.457e-12; 无 3.6e-12
- **STALE** `0.557` @ manuscript:L418 — 权威值 co_R2_phi_eff=0.8055937188186029 (gate H2 value: '律 R²=0.805594 vs 基线 R²=-0.073284')
- **STALE** `-0.050` @ manuscript:L418 — 权威值 trivial_baseline_R2=-0.07328387812300985; 稿件另一处 (L425) 又写 -0.044, 三值互相矛盾
- **STALE** `-0.044` @ SI:L358 — 权威值 -0.07328
- **STALE** `0.558` @ SI:L358 — 权威值 0.80559
- **STALE** `0.5574` @ manuscript:L418 — 0.5574 来自 A25_终审/A25_全面终审报告.md 的旧占位档数字, 已被 holdout_summary.json 取代
- **STALE** `0.5582` @ manuscript:L425 — 同上, 旧占位档数字
- **UNTRACEABLE** `6478` @ manuscript:L420 — holdout_summary.json 无该项; 无产物记录 6478/21674/116581 三元组
- **UNTRACEABLE** `21674` @ manuscript:L420 — 同上
- **UNTRACEABLE** `116581` @ manuscript:L420 — 同上
- **UNTRACEABLE** `0` @ manuscript:L19 — A18 verdict 只有 6 个布尔项, 无 'falsifier' 计数; 无法机械复核
- **UNTRACEABLE** `2.9e-11` @ manuscript:L19 — 与 §2 的 2.5e-11 及 SI S3 的 5.8e-11 三点互相矛盾; 重算 813 子集为 2.5466e-11, 故 2.9e-11 既非门禁值也非全表值 (全表 2.8045e-06)
- **UNTRACEABLE** `46` @ manuscript:L465 — 重算: qs=True ha phi=0.6 25804.27 vs qs=False 47734.80 => -45.94% (~46%) 可复现; 但该百分比未落盘为字段, 只能由 CSV/JSON 推导
- **UNTRACEABLE** `3.45` @ manuscript:L473 — 重算 ha|qs=False: 0->50 ML 45598->48799? 实为 47734.80->49381.80 = +3.45% ✓ 可复现但非落盘字段
- **UNTRACEABLE** `7.02` @ manuscript:L473 — 重算 co|qs=False: 45598.54->48799.12 = +7.02% ✓ 可复现但非落盘字段
- **NOT_A_CLAIM** `2.1` @ manuscript:L483 — 质量包络范围
- **NOT_A_CLAIM** `4.9` @ manuscript:L483 — 质量包络范围
- **NOT_A_CLAIM** `30` @ manuscript:L219 — 敏感性陈述
- **NOT_A_CLAIM** `5.000` @ manuscript:L44 — 限制档设计值 5.0 可由 CSV CoC_ai 分布复核
- **UNTRACEABLE** `1.60` @ manuscript:L496 — 1.60x 只在缺陷报告正文出现 (57,731 vs 36,504 = 1.582); 无机器产物字段
- **UNTRACEABLE** `36504` @ manuscript:L497 — 36,504 出现在 bridging_pairs_full.json / bridging_partial.json (v1, 占位档); 现行 v2 (cited 档) 的 M0 为 50,192.70 / 50,192.69 等, 不再有 36,504
- **STALE** `116` @ manuscript:L158 — 重算 813 子集 Figshare: neg=119, pos=62, zero=9 (稿件 116/54)
- **STALE** `183` @ manuscript:L155 — 重算 813 子集 LADWP: neg=186, pos=8, zero=9 (稿件 183/0)
- **STALE** `184` @ manuscript:L156 — 重算 813 子集 AI-UWM: neg=187, pos=8, zero=9 (稿件 184/0)
- **STALE** `148` @ manuscript:L157 — 重算 813 子集 IEUA: neg=151, pos=56, zero=9 (稿件 148/48)
- **STALE** `48` @ manuscript:L157 — 重算 pos=56
- **STALE** `54` @ manuscript:L158 — 重算 pos=62
- **UNTRACEABLE** `237` @ manuscript:L262 — 无产物字段记录 237/0
- **UNTRACEABLE** `241` @ manuscript:L262 — 无产物字段记录 241/0; 重算 813 子集 LADWP neg=186 / AI-UWM neg=187, 均非 237/241
- **STALE** `192` @ manuscript:L199 — missing_quality_summary.n_rows=16, 不是 192
- **UNTRACEABLE** `2869` @ manuscript:L200 — summary 只给 M1_delta_median (AI-UWM 1.8227); 无 2,869 字段
- **STALE** `329` @ SI:L138 — convergence_impact 给出 n_q_pos all=349 / ok=329 ✓ 数值正确; 但同一 SI 表把 '440' 写成 329 的 cited 对照, 需与 290 并列呈现 —— 数值本身 VERIFIED, 归类见 note
- **UNTRACEABLE** `2683047` @ SI:L389 — summary 只写 '2.68 MB, 与记录列出的 2.7 MB 一致'; 精确字节数无产物
- **UNTRACEABLE** `0.625` @ SI:L150 — 87.5 = 350 x 0.25 可由 cited limits 推出 (baseline alkalinity 350 x limit_scale 0.25); 140 mg/L 水样浓度与 ratio 无产物字段
- **UNTRACEABLE** `87.5` @ SI:L150 — 可由 350x0.25 推导, 但未落盘
- **UNTRACEABLE** `140` @ SI:L150 — 无产物
- **UNTRACEABLE** `58` @ SI:L105 — quality_binding 列可由 CSV 重算; 该表 (100/92/58/48/0%) 未落盘为产物字段
- **UNTRACEABLE** `92` @ SI:L104 — 同 SI S2b 表, 需由 quality_binding 列重算
- **UNTRACEABLE** `100` @ SI:L103 — 同上
- **UNTRACEABLE** `48` @ SI:L106 — 同上
- **UNTRACEABLE** `0` @ SI:L15 — 同上
- **NOT_A_CLAIM** `0.504` @ SI:L90 — 锚定值
- **UNTRACEABLE** `16` @ SI:L1 — n_scenarios=16 ✓ 但 '16/16' 为陈述
- **UNTRACEABLE** `2,828` @ SI:L447 — surplus_threshold_check 只给占比网格 (1.5 -> 0.0); 无 2,828 / 11,896 字段
- **UNTRACEABLE** `11896` @ SI:L448 — 同 SI S6c 方法学注
- **UNTRACEABLE** `114` @ SI:L528 — 无产物字段; 重算 supp_state 无该计数
- **STALE** `0.557` @ manuscript:L418 — Lead 已确认: 应为 0.806 (co_R2_phi_eff=0.8055937188186029); 基线应为 -0.073 (trivial_baseline_R2=-0.07328387812300985)
- **FORBIDDEN_CLAIM** `above 95%` @ manuscript:L43 — Lead 已确认: 该实证主张不可识别, 必须撤回 (只观测到生产能力, 未观测已承诺需求)
- **STALE** `1094` @ manuscript:L223 — §3 主体口径为 813(双门禁现行), 但同章的分类器却用 n=1,094(占位档 converged_unique)。A10/city_model.py 的 LIMIT_SET 现为 'baseline', 现行 grid 为 1052, 故 1,094 与 813 不可同时为真。A22/q_predictors_summary.json 的 n=1152(全表) —— 第三个数。
- **UNTRACEABLE** `0.456` @ manuscript:L190 — A22 by_sample 给 AI-UWM acc=0.4375(全表 288), 不是 0.456; 0.456 未落盘
- **UNTRACEABLE** `1.000` @ manuscript:L20 — by_sample 未包含 1.000 的取值; 稿件称 'reliable subset' 但该子集分类器未落盘
- **UNTRACEABLE** `0.993` @ manuscript:L189 — 同上, 未落盘
- **UNTRACEABLE** `0.720` @ manuscript:L190 — 同上, 未落盘
- **STALE** `1052` @ SI:L183 — 现行主网格为 1052 行(含 188 退化 + 58 未收敛); 1,152 属 A27 切换前占位档。SI S3.0 表把 '1,152 / 58 / 5.03%' 与 '813' 并列在同表, 口径混用必须拆表。
- **STALE** `58` @ SI:L105 — 现行 1052 网格的未收敛数为 18(no_convergence)+33(non_unique)=51, 不是 58; 58 属占位档 1152。两代口径混排。
- **STALE** `5.03` @ SI:L164 — 58/1152=5.03% 属占位档; 现行 1052 网格为 51/1052=4.85%, 且双门禁剔除 239/1052=22.72%

---

## 3. 必须修改清单（按严重度排序）

| 级别 | 裁定 | 位置 | 必须的修改 |
|---|---|---|---|
| **P0** | FORBIDDEN_CLAIM | manuscript L43 / L398（`above 95%` / `above 93%`；`empirically dominant`；Abstract `surplus covers only ~2–5%`） | 必须**整段撤回**，不得作为观测事实出现。数据只观测到「生产能力(处理量×r)」，未观测「已承诺需求」。SI S6b 自己已记录负荷率→分支占比的映射「wrong in direction」并撤回。若保留，只能改写为「在我们的规模—阈值比较下 committed 分支占多数」这一条件化表述，并同时给出 2.0–6.6% 的完整区间。 |
| **P0** | STALE | manuscript L418、L425（`R² = 0.557`；`baseline −0.050`；`0.5574`；`0.5582`；SI S6 `R² = 0.558`、`baseline −0.044`） | 改为 `R² = 0.806`（`co_R2_phi_eff = 0.8055937188186029`），基线统一为 `−0.073`（`trivial_baseline_R2 = −0.07328387812300985`）。现行稿件同时出现 0.557 / 0.5574 / 0.5582 / 0.558 与两个互不相同的基线，属多重内部矛盾。 |
| **P0** | STALE | manuscript §3 组成表 L155–L158；SI 无此表 | 整表重算值：LADWP 186/8、AI-UWM 187/8、IEUA 151/56、Figshare 119/62（各含 9 行 dS=0）。稿件 183/0、184/0、148/48、116/54 全部与产物不符。 |
| **P1** | STALE | manuscript §2 L97（`2.5e-11`）vs Discussion（`2.9e-11`）vs SI S3（`5.8e-11`）vs SI S2a/S3.0（`2.55e-11`） | 同一「恒等式残差」在全稿出现 **四个不同数值**。经独立重算, 只有 **2.55e-11 / 2.5e-11** 在 813 双门禁子集上成立（重算 2.5466e-11）—— 应全稿统一为该值并注明口径（统一通式 `displaced-(M0-M1)-x_ai_B1`、813 子集）。`2.9e-11`（Discussion）与 `5.8e-11`（SI S3, 号称 1,152 情景）无产物支撑。另须显式区分三个易混量：(a) 统一通式残差 813 子集 2.55e-11 / 1052 全表 2.8e-6；(b) `dS_pot − dS_ident` 最大绝对残差 6.39e4 ML；(c) 占位档 `identity_resid_max` 1.16e-10。 |
| **P1** | STALE | manuscript §2 L108/L112（`negative in 429 of 446`；`The 17 exceptions`；`100% agreement`） | 零挤占行在可靠子集中为 372 行，其中 dS>0 仅 **3** 行，非 17；446 是占位档 all 值。`429/446` 与 `17` 均无产物支撑。A25 `zero_disp_criterion.json` 的 n_zero_disp 为 ha 241 / co 205。 |
| **P1** | STALE | manuscript §3 L188（`0.803`）vs SI S3.2（`0.768`） | A22 `q_predictors_summary.json` 最大 `acc = 0.7682291666666666`，无 0.803。主稿与 SI 同一指标必须统一为 0.768。 |
| **P2** | STALE | manuscript §3c L265（`M0 = 104,948 / M1 = 93,414 / dS = −11,535`） | 104,948.4 只存在于 `OBSOLETE_reliability_grid.csv`（占位档、chi=0.25、phi=0.5）；M1 与 dS 无任何产物。且现行网格 phi 自 0.2 起，phi=0.05 无法复现。 |
| **P2** | STALE | SI S3.0 表头（`1,152 / 58 / 5.03%` 与 `813` 混排；`SI S2a 329/441`） | 1,152 是 A27 切换前的占位档网格；现行主网格为 **1,052**。该表把两代口径（1,152+58 与 813+188）放进同一张表，必须拆表并显式标注口径。 |
| **P2** | STALE | manuscript §7 L417 / SI S6（`ablation identity residual 3.6e-12`） | 重算份额口径（`dp_scale==0`, n=30, `converged_unique`）max = **7.276e-12**（= `a15_gates_reliable.ablation.all.unified_resid_max`）；`ablation_summary.identity_max_err_share_only_ml = 5.457e-12`。无 3.6e-12。 |
| **P3** | UNTRACEABLE | manuscript §5/SI S4.1 组成均值表（−19,726 / −8,510 / −12,257 / −4,690 / −16,359 / −7,504 / +8,895 / +28,437）；§3 表中位 −14,496 / −7,651 / −4,259；§3c `237/0`、`241/0`；§6 `0.184`；§3b `2,869 ML`、`192 scenarios`；SI S2b 100/92/58/48/0% | 这些数字在仓库的任何 *.json/*.csv 中都找不到字段。要么补跑并落盘对应产物，要么在稿件中删除或降级为「未落盘估计」。`192` 尤须修：`missing_quality_summary.n_rows = 16`。 |
| **P3** | STALE | manuscript §5 L299（`surplus ≤ 0, down to −22,359 ML`） | A18 `surplus_arm.d_abstraction_ml = −22,541.17`，不是 −22,359。 |

---

## 4. 方法学说明

### 4.1 如何提取

`audit_stale_numbers.py` 用正则 `NUM = [-−–]?\d[\d,，]*(\.\d+)?(\s*[×x]\s*10\s*[-−–]?\s*[⁰¹²³⁴⁵⁶⁷⁸⁹]+)?` 对主稿与 SI **逐行**扫描，抓取每一个数值 token（含千分位、Unicode 负数号、`2.5 × 10⁻¹¹` 形式的科学计数），解析为 float，并保留 ±70 字符上下文以判定语境。行号由同一脚本在稿件上二次定位（`locate()`）以保证可复核。

### 4.2 如何定位权威来源

对每个数值按优先级查找：(1) 该 A* 目录下的 `*_summary.json`；(2) 对应 `*.csv` 原始产物（本脚本**重新计算**而不是照抄 summary，以发现 summary 与 CSV 的不一致）；(3) 报告 md 仅作为「历史值/撤回值」的佐证，不作为权威锚。

本脚本实际独立重算的关键量：

- A17 主网格双门禁子集（`status==converged_unique` ∧ `¬coc_floor_degenerate` ∧ `¬extrapolated`）的全部头条计数与恒等式残差；
- A13c `potable_flows.csv` 的 status 分布；
- A15 `ablation_matrix.csv` 的 status 分布与恒等式残差；
- A20 桥接 v1(36 对)/v2(24 对) 的配对、符号一致率、按水样拆分、M0 最大相对差；
- A24 外部数据的分位数与 `33.4 / 30.7 ML/d` 的真实分位（80.89 / 80.77）。

本轮共真实读取并登记 30 个机器产物，全部列于 JSON 的 `artifacts_read`。

### 4.3 局限

1. **`gamma`/隐式量**：稿件中有若干数字（如组成均值表、`237/0`、`2,869 ML`）可能来自未落盘的中间脚本运行；本审计**不猜测**其来源，一律记 UNTRACEABLE。
2. **口径混用本身就构成缺陷**：A27 切换使主网格从 1152/1094 变为 1052/813，但 A25 系列产物（`convergence_audit.json`、`convergence_impact.json`、`a15_gates_reliable.json`）仍是切换前口径。因此某些数字「能在产物中找到」但仍属陈旧——脚本对这类情况在 note 中显式标注，而非简单判 VERIFIED。
3. **恒等式残差的定义歧义**：`dS_pot − dS_ident`、`unified_identity_max_err_ml`、`identity_max_err_ml` 是三个不同的量。稿件未说明所指，导致 2.5e-11 系列无法唯一追溯。这是稿件本身的问题，本审计如实登记而非代为选择。
4. **`2e10 ML` 量级**：脚本对该条标 VERIFIED 是宽松判断（`OBSOLETE_reliability_grid.csv` 实际 M 量级为 1.2e5），因为该量级描述的是 CoC floor 触发后的退化行为而非常规数值。
5. **外部数据的 `r = 1.0000`**：A28 `final_audit.py` 做过该检验且通过，但未落盘数值产物，因此记 UNTRACEABLE。
6. **未核**：图（`figures/`）与参考文献（`A29_文献核验/`）不在本次「数字核对」范围内。

### 4.4 纪律声明

本审计**未修改** `manuscript_en_v3.md`、`supplementary_information.md` 或仓库中任何现有研究文件；产出仅写入 `A30_WP0取证/`。
