# AI-UWM R2 实验数据集

导出时间：2026-09-24（R3 修正后重新导出）
来源：`aiuwm_src/validation_artifacts/`（`r2/` 聚合结果 + `timeseries/` 逐日过程）
对应方案：《AI-UWM 下一轮模拟：情景设置与实施方案》v4.3/R3；修正说明见同目录 `..\01_方案与设计文档\Nature级研究审查与修正计划_R3.md`

## 交付结构

```
AI-UWM_R2_实验数据集/
├── README_数据说明.md          本文件
├── AI-UWM_R2_册1_汇总.xlsx    索引 / 核心结果 / 各实验段聚合表 / 情景清单
├── AI-UWM_R2_册2_过程.xlsx    逐日抽样 + 全情景月聚合
├── AI-UWM_R2_册3_组分.xlsx    组件级逐日抽样（表最宽，单独成册）
└── csv/                      按实验段分目录的 CSV 源文件
```

分册原因：单个 Excel 工作簿有 1,048,576 行上限，逐日全量写 xlsx 会产生 GB 级文件。
逐日抽样步长：核心表（system/area/data_center）**每 3 日取一点**，组件表 **每 10 日取一点**（行数约为核心表的 13 倍）；月/年聚合为全量。

## 数据规模

- 逐日过程全量：45 个情景 / 1,563,174 行 / 293 MB
  （保留在仓库 `aiuwm_src/validation_artifacts/timeseries/`，未随本数据集复制）
- 抽样表 `system_daily_sampled`：10,980 行
- 抽样表 `area_daily_sampled`：10,980 行
- 抽样表 `data_center_daily_sampled`：10,980 行
- 抽样表 `system_monthly_all`：1,080 行
- 核心结果长表：116 条

## 口径说明

1. 模拟期 **730 天（2 年）**；未带 `annual_` 前缀的引擎 `*_ml` 字段为**全期累计**，`*_ml_d` 为**日均值**；带 `annual_` 前缀的字段按各表字段说明，统一按模拟年数年化。
   与文献年值比较时按年化值（÷2）换算。
2. 容量扫描网格 0–2000 MW 是**刻意设定的压力测试上界**。
   50–300 MW 表示中型园区情景；公开项目已出现约 1 GW 级 AI 园区，容量参照应随项目和电源条件注明。
3. 驱动为**合成序列**；结果代表模型情景，不是实测城市值。
4. 硬能力/利用率约束多数采用 **0.95**；峰值、局部接入和电力接网软指标按 **1.00** 判定。引擎对能力做硬截断，利用率恒 ≤1。
5. 绝对量报 3 位有效数字，无量纲比值保留 3 位小数（见方案 1.5 节）。
6. **城市梯度的中间城市是两端点的线性混合**，是合成谱而非真实城市，
   仅用于检验结论沿城市参数轴的连续性与单调性。
7. 造价与对标数据的**来源性质已分级标注**（见 `05_干预与边际/cost_parameters.csv` 与
   `11_文献对标/literature_benchmark_sources.csv`）：
   OFFICIAL（政府或电网正式文件）/ CASE（具体项目批复或中标）/
   DISCLOSURE（公司披露转述）/ INDUSTRY（行业基准）/ GREY（二手摘录或行业网页）。
   OFFICIAL 与 CASE 可直接作为工程参照；其余条目在论文中按原始年报、ESG 报告或造价定额复核。
8. **跨文献比较前先看口径**：`11_文献对标/literature_benchmark_caliber.csv` 记录了 4 例
   同一指标在不同来源/不同定义下不可直接比较的实例（WUE 同一公司同一年相差近 1 倍；
   城市漏损率同一年官方口径相差 >2.8 个百分点；再生水『利用率』与『替代率』分母不同；
   毛替代率 vs B0 城市源水增量代理）。引用时同时写出口径，避免跨口径混用；该代理不等同于同一 AI 负荷下 B2→B1 净淡水差分。
9. 城市侧对标使用 `cap_0000`（无 AI 负荷）作为城市基线，避免 AI 负荷污染城市指标。
   人均用水已区分**平均日/最高日**两个口径，只与 GB 50013-2018 同口径定额比对。
10. Pareto 候选集**包含 baseline（投资 0、增益 0）**。若不纳入，零增益但最便宜的选项
    会因无人能支配它而误入有效集——这是判定伪影，不是结果。
11. `probabilistic_large.csv/json` 是历史 **250 MW 粗网格**产物；当前 50 MW 结果使用 `probabilistic_corrected.csv/json`（物理 CAWCC）及其中的 `policy_*` 字段（目标阈值）。D-CO 政策阈值 P50/P95 在 2000 MW 网格上界右删失，写作 ≥2000 MW。
12. `morris.csv` 与 `city_morris.csv` 保留历史原生单位结果；跨参数排名应使用同目录的 `morris_normalized.csv` 与 `city_morris_normalized.csv`。

13. 能耗字段 `it_energy_mwh` 与 `facility_energy_mwh` 为 730 天累计 MWh；平均日功率（MW）= 字段 ÷ 730 ÷ 24，接网占用使用设施能耗（含 PUE）。
14. WUE 分为现场取水 WUE = `external_withdrawal_ml × 1000 / it_energy_mwh`，以及过程补水 WUE = `external_makeup_ml × 1000 / it_energy_mwh`，单位均为 L/kWh；两者不混用。

> **批次说明**：论文数值以 `07_代码_AI-UWM引擎/aiuwm_src/validation_artifacts/r2` 最新批次为准；本目录 CSV 是导出快照，重导前按文件时间核对。

## 文件索引

| 分类 | 文件 | 说明 |
|---|---|---|
| 01_现实性审计 | `realism_audit.csv` | 19 项现实性判据审计结果（两域） |
| 02_参数率定 | `dry_first_calibration.csv` | 干式优先冷却切换阈值率定扫描 |
| 03_基线对比/ha | `baseline_delta.csv` | [HA] 有/无 AI 数据中心的全期差值（剔除城市自然增长） |
| 03_基线对比/co | `baseline_delta.csv` | [CO] 有/无 AI 数据中心的全期差值（剔除城市自然增长） |
| 04_容量扫描/ha | `capacity_scan.csv` | [HA] 0–2000 MW 容量扫描原始逐点结果 |
| 04_容量扫描/co | `capacity_scan.csv` | [CO] 0–2000 MW 容量扫描原始逐点结果 |
| 04_容量扫描/ha | `capacity_threshold.csv` | [HA] 承载容量(CAWCC)判定结果与限制约束 |
| 04_容量扫描/co | `capacity_threshold.csv` | [CO] 承载容量(CAWCC)判定结果与限制约束 |
| 04_容量扫描/ha | `constraint_boundaries.csv` | [HA] 各约束的首次失效容量与裕度 |
| 04_容量扫描/co | `constraint_boundaries.csv` | [CO] 各约束的首次失效容量与裕度 |
| 04_容量扫描/ha | `constraint_informativeness.csv` | [HA] 约束可失效性诊断（恒真判据识别） |
| 04_容量扫描/co | `constraint_informativeness.csv` | [CO] 约束可失效性诊断（恒真判据识别） |
| 04_容量扫描/ha | `capacity_scan_corrected.csv` | [HA] 按顺序无关瓶颈逻辑重标注的容量扫描 |
| 04_容量扫描/co | `capacity_scan_corrected.csv` | [CO] 按顺序无关瓶颈逻辑重标注的容量扫描 |
| 04_容量扫描/ha | `constraint_boundaries_corrected.csv` | [HA] 修正后的逐约束首次失效表 |
| 04_容量扫描/co | `constraint_boundaries_corrected.csv` | [CO] 修正后的逐约束首次失效表 |
| 04_容量扫描/ha | `capacity_threshold_corrected.json` | [HA] 修正后的日/年物理承载摘要 |
| 04_容量扫描/co | `capacity_threshold_corrected.json` | [CO] 修正后的日/年物理承载摘要 |
| 05_干预与边际/ha | `intervention_marginal.csv` | [HA] 各类干预方案对 CAWCC 的增益 |
| 05_干预与边际/co | `intervention_marginal.csv` | [CO] 各类干预方案对 CAWCC 的增益 |
| 05_干预与边际/ha | `reuse_marginal_curve.csv` | [HA] 再生水「处理能力」杠杆边际曲线（无效杠杆） |
| 05_干预与边际/co | `reuse_marginal_curve.csv` | [CO] 再生水「处理能力」杠杆边际曲线（无效杠杆） |
| 05_干预与边际/ha | `reuse_production_marginal_curve.csv` | [HA] 再生水「产水量」杠杆边际曲线（真杠杆） |
| 05_干预与边际/co | `reuse_production_marginal_curve.csv` | [CO] 再生水「产水量」杠杆边际曲线（真杠杆） |
| 05_干预与边际 | `intervention_cost_benefit.csv` | 干预的投资区间与单位成本 万元/MW |
| 05_干预与边际 | `pareto_front.csv` | 投资-增益-居民缺水 三维 Pareto 判定 |
| 05_干预与边际 | `cost_parameters.csv` | 造价参数表（含来源与来源性质） |
| 06_机制实验/ha | `reclaimed_coc_feedback.csv` | [HA] 再生水比例→水质约束 CoC→补水/排污 反馈链 |
| 06_机制实验/co | `reclaimed_coc_feedback.csv` | [CO] 再生水比例→水质约束 CoC→补水/排污 反馈链 |
| 06_机制实验/ha | `reclaimed_net_substitution.csv` | [HA] 毛替代率 vs B0 城市源水增量代理（置换效应） |
| 06_机制实验/co | `reclaimed_net_substitution.csv` | [CO] 毛替代率 vs B0 城市源水增量代理（置换效应） |
| 06_机制实验/ha | `technology_comparison.csv` | [HA] 七种冷却技术对照（一技术一工程） |
| 06_机制实验/co | `technology_comparison.csv` | [CO] 七种冷却技术对照（一技术一工程） |
| 06_机制实验/ha | `policy_comparison.csv` | [HA] 三种分配政策对照（居民未满足量） |
| 06_机制实验/co | `policy_comparison.csv` | [CO] 三种分配政策对照（居民未满足量） |
| 07_情景矩阵/ha | `state_pressure_matrix.csv` | [HA] S×G 状态—压力 4×4 矩阵 |
| 07_情景矩阵/co | `state_pressure_matrix.csv` | [CO] S×G 状态—压力 4×4 矩阵 |
| 07_情景矩阵/ha | `heatwave_stress.csv` | [HA] 热浪极端情景（连续 15 天 +6 ℃） |
| 07_情景矩阵/co | `heatwave_stress.csv` | [CO] 热浪极端情景（连续 15 天 +6 ℃） |
| 08_不确定性/ha | `morris.csv` | [HA] Morris 筛选（AI 侧参数） |
| 08_不确定性/co | `morris.csv` | [CO] Morris 筛选（AI 侧参数） |
| 08_不确定性/ha | `sobol.csv` | [HA] Sobol 方差分解（AI 侧参数） |
| 08_不确定性/co | `sobol.csv` | [CO] Sobol 方差分解（AI 侧参数） |
| 08_不确定性/ha | `city_morris.csv` | [HA] Morris 筛选（城市侧参数） |
| 08_不确定性/co | `city_morris.csv` | [CO] Morris 筛选（城市侧参数） |
| 08_不确定性/ha | `city_sobol.csv` | [HA] Sobol 方差分解（城市侧参数，未收敛） |
| 08_不确定性/co | `city_sobol.csv` | [CO] Sobol 方差分解（城市侧参数，未收敛） |
| 08_不确定性/ha | `probabilistic_thresholds.csv` | [HA] 概率承载阈值原始样本（40 样本版） |
| 08_不确定性/co | `probabilistic_thresholds.csv` | [CO] 概率承载阈值原始样本（40 样本版） |
| 08_不确定性/ha | `probabilistic_summary.json` | [HA] 概率承载阈值 P05/P50/P95 汇总（40 样本版） |
| 08_不确定性/co | `probabilistic_summary.json` | [CO] 概率承载阈值 P05/P50/P95 汇总（40 样本版） |
| 08_不确定性/ha | `probabilistic_large.csv` | [HA] 概率承载阈值原始样本（1024 样本版） |
| 08_不确定性/co | `probabilistic_large.csv` | [CO] 概率承载阈值原始样本（1024 样本版） |
| 08_不确定性/ha | `probabilistic_large_summary.json` | [HA] 1024 样本分位数 + bootstrap 95% CI |
| 08_不确定性/co | `probabilistic_large_summary.json` | [CO] 1024 样本分位数 + bootstrap 95% CI |
| 08_不确定性/ha | `probabilistic_corrected.csv` | [HA] 1024 样本、50 MW 网格；物理 CAWCC 与政策阈值分开 |
| 08_不确定性/co | `probabilistic_corrected.csv` | [CO] 1024 样本、50 MW 网格；物理 CAWCC 与政策阈值分开 |
| 08_不确定性/ha | `probabilistic_corrected_summary.json` | [HA] 修正版物理 CAWCC 分布、CI 与政策阈值摘要 |
| 08_不确定性/co | `probabilistic_corrected_summary.json` | [CO] 修正版物理 CAWCC 分布、CI 与政策阈值摘要 |
| 08_不确定性/ha | `morris_normalized.csv` | [HA] AI 侧 Morris，输入按各自区间归一化 |
| 08_不确定性/co | `morris_normalized.csv` | [CO] AI 侧 Morris，输入按各自区间归一化 |
| 08_不确定性/ha | `city_morris_normalized.csv` | [HA] 城市侧 Morris，输入按各自区间归一化 |
| 08_不确定性/co | `city_morris_normalized.csv` | [CO] 城市侧 Morris，输入按各自区间归一化 |
| 08_不确定性 | `probabilistic_sample_size_comparison.csv` | 40 vs 1024 样本的分位数估计对照 |
| 09_能源富集/ha | `energy_rich_comparison.csv` | [HA] 能源富集补充情景与常规情景对比 |
| 09_能源富集/co | `energy_rich_comparison.csv` | [CO] 能源富集补充情景与常规情景对比 |
| 10_城市梯度 | `city_gradient_capacity_scan.csv` | 25 个合成城市 × 41 容量点全量扫描 |
| 10_城市梯度 | `city_gradient_cawcc.csv` | 每个合成城市的 CAWCC 与限制约束 |
| 10b_边界条件 | `advanced_city_cawcc.csv` | 「政策已达标」城市的 CAWCC 与限制约束（4 变体 × 2 域） |
| 10b_边界条件 | `advanced_city_interventions.csv` | 同一干预在达标城市上的增益（结论适用边界） |
| 10b_边界条件 | `advanced_city_indicators.csv` | 达标变体的城市侧指标复核（确认真的达标了） |
| 10c_现实尺度诊断 | `realistic_scale_scan.csv` | 城市规模 × AI 装机的二维重扫（现实区间约束不触发） |
| 10c_现实尺度诊断 | `realistic_scale_first_binding.csv` | 各人口规模下首个触及约束的 AI 装机 |
| 10c_现实尺度诊断 | `constraint_binding_diagnosis.csv` | 逐点约束越界诊断（50 MW 步长，全部约束值 + 阈值） |
| 10c_现实尺度诊断 | `experiment_design_audit.csv` | 实验设计自洽性与现实性硬检查（32 项判定） |
| 11_文献对标 | `literature_benchmark.csv` | 模型 WUE/PUE vs 披露值与行业基准 |
| 11_文献对标 | `literature_benchmark_sources.csv` | 对标值来源清单与来源性质 |
| 11_文献对标 | `literature_benchmark_model.csv` | 参与对标的模型侧取值 |
| 11_文献对标 | `literature_benchmark_city.csv` | 城市侧指标 vs 官方标准与政策锚点（含判定） |
| 11_文献对标 | `literature_benchmark_city_sources.csv` | 城市侧对标锚点（含比较方式与对标口径） |
| 11_文献对标 | `literature_benchmark_city_model.csv` | 模型城市侧取值（同一指标多口径并列） |
| 11_文献对标 | `literature_benchmark_caliber.csv` | 口径冲突警示 4 例（跨文献比较前必读） |
| 12_自检 | `r2_verification.json` | V1–V12 机器自检结果 |
| 13_逐日过程_抽样 | `system_daily_sampled.csv` | 10,980 行，逐日每 3 日取一点（全量见仓库） |
| 13_逐日过程_抽样 | `area_daily_sampled.csv` | 10,980 行，逐日每 3 日取一点（全量见仓库） |
| 13_逐日过程_抽样 | `data_center_daily_sampled.csv` | 10,980 行，逐日每 3 日取一点（全量见仓库） |
| 13_逐日过程_抽样 | `system_monthly_all.csv` | 1,080 行，全情景月聚合（全量） |
| 13_逐日过程_抽样 | `component_daily_sampled.csv` | 39,420 行，组件级逐日每 10 日取一点（单独成册） |
| 13_逐日过程_抽样 | `manifest.csv` | 45 个情景的元数据与关键 KPI（全量） |

## 复现方式

```powershell
Set-Location 'C:\Users\mmrgr\Desktop\论文\算力中心\07_代码_AI-UWM引擎\aiuwm_src'
$env:PYTHONPATH='src;scripts'
python scripts/build_r2_domains.py --years 2 --seed 20260918   # 建域
python scripts/audit_realism.py --domains ha,co --ai-capacity 1000        # 审计(须 0 FAIL)
python scripts/calibrate_dry_first.py --domains ha,co --capacity 750
python scripts/run_r2.py --domains ha,co                      # 主矩阵
python scripts/run_r2_sensitivity.py --domains ha,co          # AI 侧敏感性
python scripts/run_r2_extra.py --domains ha,co                # 城市侧敏感性 + 能源富集
python scripts/run_r2_probabilistic.py --samples 1024 --workers 24   # 大样本概率阈值
python scripts/run_r2_city_gradient.py --grid 5 --workers 16  # 25 城梯度
python scripts/run_r2_cost_pareto.py                          # 成本效益与 Pareto
python scripts/build_literature_benchmark.py                  # 文献对标
python scripts/run_r2_timeseries.py --domains ha,co           # 逐日过程全量落盘
python scripts/export_r2_dataset.py --out 'C:\Users\mmrgr\Desktop\论文\算力中心\08_实验数据' # 本数据集
```

种子固定为 `20260918 + 101 × 域序号`，不使用 `hash(str)`（避免 PYTHONHASHSEED 不确定性）。

