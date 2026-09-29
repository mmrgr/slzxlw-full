# AI-UWM 可复现清单（R5）

本清单随 `scripts/build_reproduction_manifest.py` 自动生成，请勿手改。

## 一、运行环境

| 项 | 值 |
|---|---|
| python | `3.14.0` |
| platform | `Windows-11-10.0.26200-SP0` |
| numpy | `2.3.5` |
| pandas | `2.3.3` |
| scipy | `1.17.1` |

## 二、代码版本

| 项 | 值 |
|---|---|
| git HEAD | `8ff14f5 T0.3 收敛诊断增强: 从部分批次 checkpoint 读样本 + 同尺寸优先完整批次` |
| 远端 | `https://github.com/mmrgr/AI-UWM.git` |
| 工作区脏 | 是（有未提交变更） |

未提交文件：
```
M AI_DATA_CENTER_RESEARCH_CN.md
 M examples/cawcc_r2/parameter_sources.csv
 M scripts/audit_doc_consistency.py
 M scripts/build_r2_domains.py
?? scripts/add_exact_binomial_bound.py
?? scripts/audit_water_balance_closure.py
?? scripts/build_claim_register.py
?? scripts/build_intervention_wec.py
?? scripts/build_reproduction_manifest.py
?? scripts/merge_reservoir_ensemble.py
```

> 注：`.gitignore` 第 10 行 `validation_artifacts/*` 使多数产物不入库——这是刻意设计（产物应由脚本重算），下方哈希用于校验重算结果是否一致。

## 三、关键产物校验（SHA256）

| 产物 | 字节数 | SHA256（前 16 位） |
|---|---|---|
| `validation_artifacts\r2\claim_register_R5.csv` | 5,395 | `9e4adc086fc36dbe` |
| `validation_artifacts\r2\water_balance_closure.csv` | 5,949 | `cf7459b8da8e3c18` |
| `validation_artifacts\r2\intervention_water_energy_carbon.csv` | 5,422 | `f72347adff14a9dc` |
| `validation_artifacts\r2\reservoir_multiyear_ensemble.json` | 11,338 | `60994aa9a229c292` |
| `validation_artifacts\r2\reservoir_multiyear_ensemble_12seq.json` | 6,760 | `ef6d1e59d34974d5` |
| `validation_artifacts\r2\literature_matrix_gap.csv` | 3,753 | `11c545e215a086a9` |
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
