# 日志总索引 (LOG_INDEX)

> 自动生成: `python _logs/consolidate_logs.py`
> 生成时间: 2026-10-16 16:36:55

- 日志总数 **80**
- 仍未脚本写入(原地保留) **8**
- 已归档到 `_logs/` **72**
- 合计 262.2 KB / 2167 行

## 为何部分日志留在原地

机械核验: 只有仍被脚本以 `open(...,'w')` 写入的日志才原地保留 ——
若搬走, 脚本下次运行会在原处**重新生成**, 造成同一日志两处存在。
冻结的历史日志则复制到 `_logs/`, 并在原地留下 `<原名>.moved.md` 指针。

## 清单

| 来源目录 | 日志名 | 大小(B) | 行数 | 状态 | sha256(12) | 首行 |
|---|---|---:|---:|---|---|---|
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_1024.err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_1024.out.log` | 1114 | 34 | archived -> _logs/ | `65b24f0b05f0` | [ha] 1024 samples x 41 capacities, workers=24, restored=64 |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_adaptive_detached.err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_adaptive_detached.out.log` | 83 | 3 | archived -> _logs/ | `e231bf6b3de2` | [ha] 1024 samples x 41 capacities, workers=8, restored=588 |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_corrected_run.err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_corrected_run.log` | 464 | 18 | archived -> _logs/ | `634e25063564` | [ha] 1024 ���� x 41 ������, workers=24 |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_fast.err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_fast.out.log` | 79 | 3 | archived -> _logs/ | `54c16da955b5` | [ha] 256 samples x 41 capacities, workers=8, restored=0 |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_fast64.err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_fast64.out.log` | 625 | 14 | archived -> _logs/ | `5055da3f68d1` | [ha] 64 samples x 41 capacities, workers=8, restored=0 |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_rerun_20260926.err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_rerun_20260926.out.log` | 83 | 3 | archived -> _logs/ | `61b23a3b6394` | [ha] 1024 samples x 41 capacities, workers=8, restored=256 |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_rerun_20260927.err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_rerun_20260927.out.log` | 83 | 3 | archived -> _logs/ | `f203a2187447` | [ha] 1024 samples x 41 capacities, workers=4, restored=377 |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_rerun_detached.err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `probabilistic_rerun_detached.out.log` | 83 | 3 | archived -> _logs/ | `3dc9cd3bdc1a` | [ha] 1024 samples x 41 capacities, workers=8, restored=462 |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `reservoir_multiyear_10y.err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` | `reservoir_multiyear_10y.out.log` | 78 | 3 | archived -> _logs/ | `7b9c5164dfd2` | ha joint_gate 250.0 terminal100 200.0 |
| `09_工具与辅助脚本/脚本与日志` | `ab_install.log` | 1302 | 41 | archived -> _logs/ | `0dd0278bae3a` | ﻿=== npm install -g agent-browser === |
| `09_工具与辅助脚本/脚本与日志` | `ab_run.log` | 265 | 8 | archived -> _logs/ | `e88d3df783e7` | === START === |
| `09_工具与辅助脚本/脚本与日志` | `ab_run_wrapper.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `09_工具与辅助脚本/脚本与日志` | `batch2_out.log` | 1343 | 22 | archived -> _logs/ | `7d3a29adc691` | DONE 01 01_Xiao2025_NatSustain.pdf verified=True oa=hybrid dl=False |
| `09_工具与辅助脚本/脚本与日志` | `batch2b_out.log` | 2922 | 28 | archived -> _logs/ | `9f156ba69efc` | === CROSSREF TITLE SEARCH (correct DOIs) === |
| `09_工具与辅助脚本/脚本与日志` | `batch2c_out.log` | 4033 | 29 | archived -> _logs/ | `ebbd619a5044` | === TARGETED CROSSREF SEARCH === |
| `09_工具与辅助脚本/脚本与日志` | `batch2d_out.log` | 2127 | 19 | archived -> _logs/ | `9ce21029bf4c` | === Hsieh2010 === |
| `09_工具与辅助脚本/脚本与日志` | `dl_17.log` | 93 | 4 | archived -> _logs/ | `8963ab32317f` | ﻿START |
| `09_工具与辅助脚本/脚本与日志` | `dl_green.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `09_工具与辅助脚本/脚本与日志` | `dl_green2.log` | 116 | 4 | archived -> _logs/ | `419123398992` | ﻿START |
| `09_工具与辅助脚本/脚本与日志` | `download.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `09_工具与辅助脚本/脚本与日志` | `download_v2.log` | 2768 | 38 | archived -> _logs/ | `ce1aeea8f6a6` | ﻿01 Wang2026 [ESE] -> FAIL (SD-pdfft:<HTTPError 403: 'Forbidden'>) 0B |
| `09_工具与辅助脚本/脚本与日志` | `html2.log` | 92 | 2 | archived -> _logs/ | `2248a34ea668` | WROTE C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.html |
| `09_工具与辅助脚本/脚本与日志` | `identify.log` | 21650 | 276 | archived -> _logs/ | `e1dd88c8e514` | ﻿python.exe : fontTools is required to fully parse the encoding of a C |
| `09_工具与辅助脚本/脚本与日志` | `inventory.log` | 74223 | 269 | archived -> _logs/ | `38009de57a6a` | fontTools is required to fully parse the encoding of a CFF Type1 font  |
| `09_工具与辅助脚本/脚本与日志` | `oa_check.log` | 12 | 2 | archived -> _logs/ | `2f2852c8640b` | ﻿DONE 20 |
| `09_工具与辅助脚本/脚本与日志` | `param_run.log` | 46989 | 72 | archived -> _logs/ | `e2d8b0f7f5d2` | fontTools is required to fully parse the encoding of a CFF Type1 font  |
| `09_工具与辅助脚本/脚本与日志` | `pip_pypdf.log` | 616 | 12 | archived -> _logs/ | `346bc54de574` | ﻿Requirement already satisfied: pypdf in C:\Users\mmrgr\.workbuddy\bin |
| `09_工具与辅助脚本/脚本与日志` | `probe.log` | 263 | 8 | archived -> _logs/ | `15329008055b` | ﻿UNPAYWALL_ERR <HTTPError 422: 'Unprocessable Entity'> |
| `09_工具与辅助脚本/脚本与日志` | `probe2.log` | 141 | 4 | archived -> _logs/ | `fd84dca30b0b` | ﻿workbuddy@workbuddy.ai -> 200 oa= gold pdf= None |
| `09_工具与辅助脚本/脚本与日志` | `pw_cap3_0508_out.log` | 6 | 2 | archived -> _logs/ | `47acd618a9d4` | DONE |
| `09_工具与辅助脚本/脚本与日志` | `pw_cap3_05_08.log` | 4409 | 62 | archived -> _logs/ | `6968bb463866` | === 05 === start: Making AI Less 'Thirsty' \| Communications of the A |
| `09_工具与辅助脚本/脚本与日志` | `pw_cap5.log` | 296 | 8 | active (原地保留) | `65288974f76a` | === 01 === after wait title: Just a moment... |
| `09_工具与辅助脚本/脚本与日志` | `pw_cap5_out.log` | 6 | 2 | archived -> _logs/ | `47acd618a9d4` | DONE |
| `09_工具与辅助脚本/脚本与日志` | `pw_cap_05_01.log` | 1138 | 19 | archived -> _logs/ | `32087a023c02` | === 05 === start loaded: Making AI Less 'Thirsty' \| Communications of |
| `09_工具与辅助脚本/脚本与日志` | `pw_capture.log` | 184 | 8 | active (原地保留) | `8ddbdee6417c` | === 06 === |
| `09_工具与辅助脚本/脚本与日志` | `pw_capture2.log` | 2139 | 21 | archived -> _logs/ | `6267c71e3eb1` | === 06 === start loaded: Radware Bot Manager Captcha |
| `09_工具与辅助脚本/脚本与日志` | `pw_capture2_err.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `09_工具与辅助脚本/脚本与日志` | `pw_capture2_out.log` | 6 | 2 | archived -> _logs/ | `47acd618a9d4` | DONE |
| `09_工具与辅助脚本/脚本与日志` | `pw_capture2_out_0501.log` | 6 | 2 | archived -> _logs/ | `47acd618a9d4` | DONE |
| `09_工具与辅助脚本/脚本与日志` | `pw_capture2_wrapper.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `09_工具与辅助脚本/脚本与日志` | `pw_diag.log` | 9436 | 61 | active (原地保留) | `a72f94bd61fe` | === 06 === url=https://iopscience.iop.org/article/10.1088/1748-9326/ab |
| `09_工具与辅助脚本/脚本与日志` | `pw_diag_wrapper.log` | 9 | 2 | archived -> _logs/ | `46c428a7df80` | ﻿DONE |
| `09_工具与辅助脚本/脚本与日志` | `pw_install.log` | 1305 | 24 | archived -> _logs/ | `531ed12fdd0d` | ﻿Collecting playwright |
| `09_工具与辅助脚本/脚本与日志` | `pw_wrapper.log` | 9 | 2 | archived -> _logs/ | `46c428a7df80` | ﻿DONE |
| `09_工具与辅助脚本/脚本与日志` | `rename.log` | 3736 | 39 | active (原地保留) | `30b82bb7e579` | RENAMED: 02_Lei2025_RCR.pdf -> B1-02_Lei2025_Water_use_data_center_wor |
| `09_工具与辅助脚本/脚本与日志` | `syntax.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `09_工具与辅助脚本/脚本与日志` | `test_dl.log` | 365 | 5 | archived -> _logs/ | `7870a3ef6528` | ﻿10_Copernicus_test: status ok=True size=2272575 saved=C:\Users\mmrgr\ |
| `09_工具与辅助脚本/脚本与日志` | `v3_test.log` | 242 | 6 | archived -> _logs/ | `b18f15a07f55` | ﻿01_Wang2026_ESE: no PDF (urls found=1) |
| `09_工具与辅助脚本/脚本与日志` | `venv.log` | 0 | 1 | archived -> _logs/ | `e3b0c44298fc` |  |
| `10_论文推进_2026Q4/A10_敏感性与边界` | `t10.log` | 1635 | 34 | archived -> _logs/ | `1c28118212d7` | [Morris] ha\|B_full\|IEUA: n_eval=120 nan=0 |
| `10_论文推进_2026Q4/A10_敏感性与边界` | `t11.log` | 352 | 6 | archived -> _logs/ | `d645d0ec7baf` | [T11] n=700 \| 状态=['converged_unique', 'no_convergence'] |
| `10_论文推进_2026Q4/A10_敏感性与边界` | `t12.log` | 297 | 6 | archived -> _logs/ | `55aeb7a15e09` | [T12] 1275 点 \| 状态=['converged_unique'] |
| `10_论文推进_2026Q4/A11_适应成本` | `t13.log` | 1489 | 21 | archived -> _logs/ | `d412d49e7a83` | [T13] 29 方案 \| S_city ∈ [-444.0, 6,101.1] ML/yr |
| `10_论文推进_2026Q4/A12_时间分辨率` | `t14.log` | 4710 | 46 | archived -> _logs/ | `373db6bb4f65` | ====================================================================== |
| `10_论文推进_2026Q4/A12_时间分辨率` | `t14b.log` | 3395 | 41 | archived -> _logs/ | `f1a70feb7017` | ====================================================================== |
| `10_论文推进_2026Q4/A12_时间分辨率` | `t14c.log` | 3741 | 43 | archived -> _logs/ | `c19ad108a338` | ====================================================================== |
| `10_论文推进_2026Q4/A12_时间分辨率` | `t14d.log` | 3197 | 32 | archived -> _logs/ | `6f1c715c1004` | ====================================================================== |
| `10_论文推进_2026Q4/A12_时间分辨率` | `t14e.log` | 5223 | 44 | archived -> _logs/ | `40af8970fbab` | ====================================================================== |
| `10_论文推进_2026Q4/A15_稳健性` | `ablation.log` | 1411 | 27 | archived -> _logs/ | `4120ae3e8057` | ====================================================================== |
| `10_论文推进_2026Q4/A15_稳健性` | `boundary_stress.log` | 959 | 21 | archived -> _logs/ | `adba15a9f5a1` | ﻿===================================================================== |
| `10_论文推进_2026Q4/A15_稳健性` | `grid_resolution.log` | 1392 | 21 | archived -> _logs/ | `d578109ddfcf` | ﻿===================================================================== |
| `10_论文推进_2026Q4/A15_稳健性` | `holdout.log` | 2675 | 50 | archived -> _logs/ | `efce7c7a6659` | ====================================================================== |
| `10_论文推进_2026Q4/A15_稳健性` | `prior_sensitivity.log` | 3408 | 39 | archived -> _logs/ | `e72d55feb893` | ﻿===================================================================== |
| `10_论文推进_2026Q4/A19_水化学包络` | `t19.log` | 16172 | 224 | active (原地保留) | `b23ff1314831` | ====================================================================== |
| `10_论文推进_2026Q4/A19_水化学包络` | `t19b.log` | 4939 | 71 | active (原地保留) | `e0d15dbc8724` | ====================================================================== |
| `10_论文推进_2026Q4/A19_水化学包络` | `t19c.log` | 2795 | 35 | active (原地保留) | `30f4e1425280` | ====================================================================== |
| `10_论文推进_2026Q4/A19_水化学包络` | `t19d.log` | 4236 | 48 | active (原地保留) | `0a31129ed0a3` | ====================================================================== |
| `10_论文推进_2026Q4/A4_水化学参数域` | `t6b.log` | 3382 | 26 | archived -> _logs/ | `68a0a633fdb9` | ====================================================================== |
| `10_论文推进_2026Q4/A4_水化学参数域` | `t6v2.log` | 3579 | 33 | archived -> _logs/ | `523110e84dd0` | ===== B2 样本完整性矩阵 |
| `10_论文推进_2026Q4/A7_质量分配联合` | `t2.log` | 13037 | 68 | archived -> _logs/ | `94950c0027d9` | [baseline] ha: P0=24,404 ML \| 可回用需求=58,183 \| gap=33,779 \| E_total=2 |
| `10_论文推进_2026Q4/A9_无量纲折叠` | `t9.log` | 1518 | 28 | archived -> _logs/ | `858101e81193` | [city] ha: P0=24,404 ML \| gap=33,779 \| E_total=22,814 |

## 说明

- 原文**全部保留**, 无删除; 归档为**复制**操作, 可随时回滚。
- 原地 `<原名>.moved.md` 文件说明真实位置, 避免按旧路径找不到。
- 引擎目录 `07_代码_AI-UWM引擎/**/validation_artifacts/**` 下的日志属
  **引擎自带验证产物**, 一并纳入本索引但保留在其原位语义下(见上表来源列)。
