# AI-UWM 可复现清单（R5）

本清单随 `scripts/build_reproduction_manifest.py` 自动生成，请勿手改。

## 一、运行环境

| 项 | 值 |
|---|---|
| python | `3.12.14` |
| platform | `Windows-11-10.0.26200-SP0` |
| numpy | `2.3.5` |
| pandas | `3.0.1` |
| scipy | `未安装` |

## 二、代码版本

| 项 | 值 |
|---|---|
| git HEAD | `8ff14f5 T0.3 收敛诊断增强: 从部分批次 checkpoint 读样本 + 同尺寸优先完整批次` |
| 远端 | `https://github.com/mmrgr/AI-UWM.git` |
| 工作区脏 | 是（有未提交变更） |

未提交文件：
```
M .gitignore
 M AI_DATA_CENTER_RESEARCH_CN.md
 M README.md
 M examples/cawcc_r2/co/policy_a.json
 M examples/cawcc_r2/co/policy_b.json
 M examples/cawcc_r2/co/policy_c.json
 M examples/cawcc_r2/co/project.json
 M examples/cawcc_r2/co/tech_dry.json
 M examples/cawcc_r2/co/tech_dry_first.json
 M examples/cawcc_r2/co/tech_efficient_evaporative.json
 M examples/cawcc_r2/co/tech_evaporative.json
 M examples/cawcc_r2/co/tech_hybrid.json
 M examples/cawcc_r2/co/tech_liquid_to_air.json
 M examples/cawcc_r2/co/tech_liquid_to_water.json
 M examples/cawcc_r2/ha/energy_rich.json
 M examples/cawcc_r2/ha/policy_a.json
 M examples/cawcc_r2/ha/policy_b.json
 M examples/cawcc_r2/ha/policy_c.json
 M examples/cawcc_r2/ha/project.json
 M examples/cawcc_r2/ha/tech_dry.json
 M examples/cawcc_r2/ha/tech_dry_first.json
 M examples/cawcc_r2/ha/tech_efficient_evaporative.json
 M examples/cawcc_r2/ha/tech_evaporative.json
 M examples/cawcc_r2/ha/tech_hybrid.json
 M examples/cawcc_r2/ha/tech_liquid_to_air.json
 M examples/cawcc_r2/ha/tech_liquid_to_water.json
 M examples/cawcc_r2/parameter_sources.csv
 M pyproject.toml
 M scripts/audit_doc_consistency.py
 M scripts/audit_realism.py
 M scripts/build_literature_benchmark.py
 M scripts/build_r2_domains.py
 M scripts/export_r2_dataset.py
 M scripts/run_r2.py
 M src/aiuwm/data_center.py
 M src/aiuwm/full_engine.py
 M src/aiuwm/validation.py
 M tests/test_ai_water_balance.py
 M tests/test_data_center.py
?? REPRODUCTION_MANIFEST.md
?? data/R10_REGISTRY_README.md
?? data/external_evidence_registry.csv
?? data/parameter_registry.csv
?? data/parameter_registry_schema.json
?? data/scenario_registry.csv
?? data/scenario_registry_schema.json
?? scripts/acquire_wqp_chemistry.py
?? scripts/add_exact_binomial_bound.py
?? scripts/audit_g2_g3_evidence.py
?? scripts/audit_water_balance_closure.py
?? scripts/build_claim_register.py
?? scripts/build_cooling_partition_check_R7.py
?? scripts/build_cooling_technology_tradeoff_R7.py
?? scripts/build_intervention_wec.py
?? scripts/build_parameter_envelope_R7.py
?? scripts/build_reclaimed_compatibility_R9.py
?? scripts/build_reclaimed_fraction_sweep_R8.py
?? scripts/build_reproduction_manifest.py
?? scripts/build_technology_load_sensitivity_R7b.py
?? scripts/build_total_water_footprint_frontier_R7b.py
?? scripts/diagnose_wwtw_electricity_R8.py
?? scripts/diagnose_wwtw_process_emissions_R8.py
?? scripts/merge_reservoir_ensemble.py
?? scripts/register_external_evidence.py
?? scripts/repair_d1_d2_R8.py
?? scripts/run_g2_phreeqc_crosscheck.py
?? scripts/run_r10_pilot.py
?? scripts/verify_variant_consistency_R8.py
?? src/aiuwm/adaptation.py
?? src/aiuwm/quality_state.py
?? src/aiuwm/reclaimed_allocation.py
?? tests/test_adaptation.py
?? tests/test_external_evidence_registry.py
?? tests/test_g2_phreeqc_runner.py
?? tests/test_quality_state.py
?? tests/test_r10_pilot_runner.py
?? tests/test_reclaimed_allocation.py
?? tests/test_registry_contract.py
?? tests/test_same_day_wwtw_phase.py
?? tests/test_wqp_acquisition.py
```

> 注：`.gitignore` 第 10 行 `validation_artifacts/*` 使多数产物不入库——这是刻意设计（产物应由脚本重算），下方哈希用于校验重算结果是否一致。

## 三、关键产物校验（SHA256）

| 产物 | 字节数 | SHA256（前 16 位） |
|---|---|---|
| `validation_artifacts\r2\claim_register_R5.csv` | 17,797 | `3556d2cc3890b68a` |
| `validation_artifacts\r2\water_balance_closure.csv` | 5,949 | `cf7459b8da8e3c18` |
| `validation_artifacts\r2\intervention_water_energy_carbon.csv` | 5,422 | `f72347adff14a9dc` |
| `validation_artifacts\r2\reservoir_multiyear_ensemble.json` | 11,338 | `60994aa9a229c292` |
| `validation_artifacts\r2\reservoir_multiyear_ensemble_12seq.json` | 6,760 | `ef6d1e59d34974d5` |
| `validation_artifacts\r2\literature_matrix_gap.csv` | 4,071 | `cc26da66d9e01e70` |
| `validation_artifacts\r2\probabilistic_status.md` | 2,623 | `1ae2795770b6c283` |
| `validation_artifacts\r2\ha\probabilistic_corrected_summary.json` | 2,565 | `ca5fdc7f691caa98` |
| `validation_artifacts\r2\co\probabilistic_corrected_summary.json` | 2,698 | `748caffb4dde24e8` |

## 四、重算命令（按依赖顺序）

```bash
cd "07_代码_AI-UWM引擎/aiuwm_src"
# 解释器：需 numpy/pandas/scipy（见环境一节）

# ① 单元测试
PYTHONPATH=src python -m pytest -q

# ② 主张登记表（依赖 reservoir_multiyear_ensemble.json）
PYTHONPATH=src python scripts/build_claim_register.py

# ③ 水量闭合（读已有逐日产物，不重跑引擎）
PYTHONPATH=src python scripts/audit_water_balance_closure.py

# ④ 水—能—碳—社会联合指标
PYTHONPATH=src python scripts/build_intervention_wec.py

# ⑤ 多序列集合（20 条 = 原 12 条 + 索引 12-19）
#   原 12 条：  --sequences 12 --base-seed 20260918 --stride 100003
#   新增 8 条： --sequences  8 --base-seed 1220954 --stride 100003
PYTHONPATH=src python scripts/audit_reservoir_ensemble.py \
    --domains ha,co --years 10 --max-mw 1200 --step-mw 100 \
    --sequences 12 --base-seed 20260918 --stride 100003 \
    --out validation_artifacts/r2/reservoir_multiyear_ensemble.json
PYTHONPATH=src python scripts/audit_reservoir_ensemble.py \
    --domains ha,co --years 10 --max-mw 1200 --step-mw 100 \
    --sequences 8 --base-seed 1220954 --stride 100003 \
    --out validation_artifacts/r2/reservoir_multiyear_ensemble_ext.json
PYTHONPATH=src python scripts/merge_reservoir_ensemble.py

# ⑥ 三道提交门禁
PYTHONPATH=src python scripts/audit_doc_consistency.py
PYTHONPATH=src python scripts/audit_experiment_design.py
PYTHONPATH=src python scripts/audit_realism.py

# ⑦ 本清单自身
PYTHONPATH=src python scripts/build_reproduction_manifest.py
```

## 五、尚未固化的可复现项

- ❌ **环境锁定文件**（`requirements.txt` / `environment.lock`）：当前依赖系统解释器，未锁定小版本
- ❌ **原始数据许可**：无真实数据源，故不适用；接入观测数据后须补充
- ❌ **7 张图的图表清单**：已登记为待办，尚未制作
- ❌ **独立审稿人式投稿前复核**：未执行
- ⚠️ 集合产物仅在种子层面可复现，因其依赖 `build_r2_domains` 的合成驱动规则版本
