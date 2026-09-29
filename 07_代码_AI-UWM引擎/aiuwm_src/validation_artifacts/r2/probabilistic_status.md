# 概率结果状态

2026-09-27 已按修订后的 KPI、年度口径和 50 MW 转折网格完成最终概率批次：每域 1024 样本、24 workers、bootstrap 2000。`probabilistic_corrected.csv`、`probabilistic_corrected_summary.json` 与检查点文件均来自该批次；早期 40/64 样本文件只保留作样本量敏感性审计。

最终结果：

- HA 物理 CAWCC P05/P50/P95 = 950/1050/1200 MW；1,000 MW 超限计数 **64/1024**（点估计 0.0625，bootstrap 95% CI [0.0488, 0.0781]，精确二项单侧 95% 上界 0.0764）。政策阈值 P05/P50/P95 = 1150/1250/1350 MW，右删失率 0。
- CO 物理 CAWCC P05/P50/P95 = 1250/1350/1500 MW；1,000 MW 超限计数 **0/1024**。政策阈值 P05/P50/P95 = 1800/2000/2000 MW，右删失率 0.58496。

> **统计表述约束（2026-09-27 修正）**：CO 的 0/1024 在 bootstrap 下区间退化为 `[0, 0]`，**不得**据此写成"风险为零"。正确写法是"**观察到 0 次超限**"，并给出**精确二项（Clopper-Pearson）单侧 95% 上界 = 0.29%**（即检出限约为 0.3%）。该字段已由 `scripts/add_exact_binomial_bound.py` 写入 `probabilistic_corrected_summary.json` 的 `exceedance_probability_exact_upper95` 与 `exceedance_interpretation`；CO 政策阈值同样为 0/1024，单侧上界 0.29%。HA 的非零计数（64/1024）仍用 bootstrap 区间，并附精确区间 [0.0488, 0.0781] 作交叉核对。

重算命令：

```powershell
$env:PYTHONPATH='src;scripts'
python scripts/run_r2_probabilistic.py --domains ha,co --samples 1024 --workers 24 --bootstrap 2000
```

结果同时报告物理 CAWCC、政策目标阈值、右删失比例、P05/P50/P95、1,000 MW 超限计数/概率、bootstrap 置信区间与精确二项上界。末库容可持续性是独立 estimand，已由 `reservoir_sustainability_corrected.json` 和 10 年合成诊断单独报告。

**跨样本量收敛判定状态（R5/T0.3，`probabilistic_convergence.json`）**：

- HA = `CONVERGED_PARTIAL`：P05/P95 在 256/1024/1699 三个样本量下完全一致；**P50 在 1050–1100 MW 之间移动一个网格步，不得锁定为单一数字**；最大批次为部分完成批次（1699），只能表述为"在已完成样本量范围内稳定"。
- CO = `INSUFFICIENT_BATCHES`：仅有 256/1024 两个样本量点，**不得写"已通过收敛判定"**，只能写"两个独立样本量下分位点一致，方向上支持稳定；条件于现有批次"。

自适应网格与完整 50 MW 网格已对两域各 8 个参数抽样点复核，16/16 个物理阈值和政策阈值均一致；记录见 `probabilistic_grid_audit_8.json`。
