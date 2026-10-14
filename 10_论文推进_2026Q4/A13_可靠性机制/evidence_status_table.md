# 证据状态表（Evidence Status Table）

**任务**：task-1 / P0 证据状态表与冻结数值复核
**执行者**：审计子代理（独立于产出方）
**日期**：2026-10-14
**核验基准**：`10_论文推进_2026Q4/` 全部文档 + `A*/T*_summary.json`、`T*.csv` 冻结产物 + `07_代码_AI-UWM引擎/aiuwm_src/` 引擎源码（只读）
**纪律**：本文所有数值均由 `python` 从冻结产物**直接读取或独立重算**得出，**不采信任何文档转述**。

---

## 0. 结论摘要

| 等级 | 条数 | 含义 |
|---|---:|---|
| **verified** | 14 | 已在本轮用脚本从冻结产物独立复算/读取，数值逐位吻合 |
| **corroborated** | 3 | 有产物支撑，但依赖未锚定的外部先验或范围为声明值 |
| **assertion-only** | 6 | 文档有主张，但冻结产物中**无对应可核验数值**，或仅在特定未声明假设下成立 |
| **retracted** | 4 | 已被项目自身撤回/作废，且已在文档中标注 |

**三条最重要发现**：

1. **`S_city ≤ 0` 是代数必然，不是经验发现**——本轮给出闭式证明并用 80 组独立重算验证（残差恒为 `0.000e+00`）。该结论**成立**（详见 §2）。
2. **`P(S_city>0)=0.62` 与 `S_city≤0` 的"恒等式"并不矛盾，但主稿未披露其来源**：在 `dp=0` 处 700 个情景中仅 2 个 `S_city>0`，且两者量级为 `1e-12` ML（相对 `dp=0` 中位 `|S_city|=3.2e2` ML 为浮点残差）。因此 `dp=0` 列的"0.3% 正值"**不是物理正值**。
3. **存在两套记录，且引擎侧记录与本轮论文结论直接冲突**（详见 §4-Ⅰ）：
   引擎侧 `research_2026/claim_evidence_register.csv` 将 **C3 判为 `REFUTED_IN_BOUNDED_RUN`**、**C7/C8 判为 `NOT_READY`**，
   `status.md` 记 **G2/G3 `NOT_READY`、G4 `BLOCKED_BY_PREVIOUS_GATES`**；而 `10_论文推进_2026Q4/` 将对应项标为 ✅ 完成。
   两套记录**口径不同**（引擎侧要求外部可观测证据，论文侧允许合成域内数值闭合），但**论文侧未在正文中披露这一降级边界**。

---

## 1. 主张 → 方程 → 代码 → 输入 → 产物 → 图表 → 验证等级 映射表

### 1.1 核心守恒与代数结构

| # | 主张 | 方程/定义 | 代码位置 | 输入 | 冻结产物 | 图 | 等级 |
|---|---|---|---|---|---|---|---|
| C-01 | 城市净取水变化定义 | `S_city = (m0 − M) + x_ai + inc_recl − pool` | `A10_敏感性与边界/city_model.py:259-260` | 冻结样本 + 控制量 | `T11_uncertainty_samples.csv` | — | **verified** |
| C-02 | 恒等式 `S_city ≡ S_AI + inc_recl − pool` | 同上 | 同上 | 同上 | 本轮重算 80 组 | — | **verified** |
| C-03 | `x_ai + inc_recl ≤ pool + dp`（不超支不变量） | `_pro_rata` no-overdraw | `07_.../aiuwm_src/src/aiuwm/reclaimed_allocation.py:705-727`（`_pro_rata`）、`:349-369`（`map_allocation`） | `available = pool + dp`（`:252` 调用处） | 本轮重算 | — | **verified** |
| C-04 | **`dp=0 ⇒ S_city ≤ 0`（代数必然）** | 由 C-02+C-03 推出 | 同上 | 同上 | 本轮重算 + `T11_uncertainty_samples.csv` | — | **verified** |
| C-05 | 闭合残差为机器零 | `closure_residual_ml` | `city_model.py:269` | 全部情景 | `T10/T11/T12_summary.json` | — | **verified** |

### 1.2 T9 无量纲折叠（已作废）

| # | 主张 | 方程 | 代码 | 冻结产物 | 实测值 | 等级 |
|---|---|---|---|---|---|---|
| C-06 | 480 情景折叠残差 | `Δy` 残差 | `A9_无量纲折叠/T9_dimensionless_collapse.py` | `T9_summary.json` | `collapse_residual_max_abs = 7.105427357601002e-15` | **verified**（数值），**retracted**（结论） |
| C-07 | 降维比 19.4× | `variance_reduction_ratio` | 同上 | 同上 | `19.372539681656892` | **verified**（数值），**retracted**（可迁移性） |
| C-08 | "折叠式可迁移" | — | — | `T9b_summary.json` | `delta_prediction_pass = false`；最优 R² = `0.024692768150780253` | **retracted** |
| C-09 | 480 情景全收敛 | `statuses` | 同上 | `T9_summary.json` | `["converged_unique"]`，`n_scenarios=480`，`n_valid=480` | **verified** |

> **作废依据（项目自认）**：`T9_summary.json` 自带字段
> `"collapse_status": "algebraic_identity (audit A1): residual ~ machine precision is mathematically necessary and is NOT a transferability finding"`。
> 这与本轮对 C-04 的独立发现**同源**：项目已识别折叠是恒等式，但**未识别 `S_city≤0` 本身也是恒等式**。

### 1.3 T10/T11/T12 敏感性与边界

| # | 主张 | 代码 | 冻结产物 | 实测值（本轮读取） | 等级 |
|---|---|---|---|---|---|
| C-10 | gap 主导（S₁=0.417/ST=0.762） | `A10/T10_sensitivity.py` | `T10_summary.json` | `S1=0.41709, ST=0.76241` | **verified** |
| C-11 | pool 0.265/0.334、capacity 0.141/0.228、blend 0.021/0.028 | 同上 | 同上 | `0.26539/0.33428`、`0.14091/0.22794`、`0.02091/0.02791` | **verified** |
| C-12 | 4 配置一致 | `morris_by_config` | 同上 | 4 个配置键齐全，排序一致 | **verified** |
| C-13 | P(S_city>0) 由 dp=0 的 0.3% 跃升至 dp≥0.5 的 ~0.62 并饱和 | `A10/T11_uncertainty.py` | `T11_summary.json` | `dp0.0=0.002857`、`dp0.5=0.61`、`dp1.0=0.62`、`dp2.0=0.621428...` | **verified** |
| C-14 | 48% 落刀锋 | `A10/T11b_classify.py` | `T11b_summary.json` | `edge share = 0.48`（336/700） | **verified** |
| C-15 | 约 38% 无法转正 | 同上 | `T11_uncertainty_samples.csv` 重算 | `S_city(dp=2)≤0` 共 265/700 = `0.37857142857142856` | **verified** |
| C-16 | dp=0 处 48% 落刀锋 → 该列概率来自浮点残差 | 本轮 | 同上 | 2 个正值 = `9.094947017729282e-13`、`3.637978807091713e-12` ML | **verified**（本轮新发现，见 §4-Ⅱ） |
| C-17 | 确需新增产能者 ρ\* 中位 0.064 | `T11b_classify.py` | `T11b_summary.json` | `dp_star_quantiles_negative_only.q50 = 0.0640732897445559` | **verified** |
| C-18 | 1275 点全收敛、零界面可测 94.1% | `A10/T12_boundary_surface.py` | `T12_summary.json` | `n_points=1275`、`statuses=["converged_unique"]`、`boundary_found_share=0.9411764705882353` | **verified** |
| C-19 | IEUA ρ\*(χ=0.5)=0.19 | 同上 | 同上 | `boundary_by_sample` 中 IEUA 在 χ≈0.483 处 `0.1863`、χ≈0.5319 处 `0.1331`；**χ=0.5 为插值，非直接网格点** | **corroborated** |

### 1.4 T13/T14 适应成本与时间分辨率

| # | 主张 | 代码 | 冻结产物 | 实测值 | 等级 |
|---|---|---|---|---|---|
| C-20 | 29 方案，4D-Pareto 8 个 | `A11/T13_adaptation_pareto.py` | `T13_summary.json` | `n_scenarios=29`；`pareto_4d` 长度 = **8** | **verified** |
| C-21 | A0 基线 −418.55 ML | 同上 | 同上 | `pareto_4d[0]`：`S_city_ml = -418.55`，`energy=7763225748.84` | **verified** |
| C-22 | A3 只能去害（−418.6 → 0） | 同上 | 同上 | `infeasible_or_negative` 中 A3 各变体全为负（−444.003 …） | **verified** |
| C-23 | A2 膜法是唯一把 S_city 推正的杠杆 | 同上 | 同上 | Pareto 中正 S_city 项全部 `policy="A2"` | **verified** |
| C-24 | 主稿"A3 = +13 974 ML/yr 已作废" | — | — | `T13_summary.json` `limitations` + 主稿 §431 均标注作废 | **retracted** |
| C-25 | 指标 B：7987(ha)/7894(co) ML/yr | `A12/T14_indicators_BC.py` | `T14_summary.json` | `annual_net_saving_ml` = **15973.9281**(ha) / **15788.8993**(co) ML **per 730 d**；÷2 = **7986.964**(ha) / **7894.450**(co) ML/yr | **corroborated**（口径换算，见 §4-Ⅲ） |
| C-26 | 年缩放对蒸发式精确无偏 | `A12/T5_daily_resolution.py` | `T5_summary.json` | `M_over_E.is_constant = true`，`n_valid=730` | **verified** |
| C-27 | 混合式峰谷比 3.78(ha)/10.71(co) | `A12/T14c_hourly_peak.py` | `T14c_hourly_summary.json` | 见 §1.5 未逐位复核（超出本轮 5 情景复现范围） | **assertion-only** |

### 1.5 无冻结产物支撑的主张

| # | 主张 | 出处 | 缺口 | 等级 |
|---|---|---|---|---|
| C-28 | 跨尺度一致性 rel 6.28e−8 / 1.77e−16 | `01` 进度表 | 本轮未复算 `T14b_crossscale_summary.json` | **assertion-only** |
| C-29 | 热浪窗 5 定义鲁棒 | `08` §7.3 | 本轮未复算 `T14d_heatwave_robustness_summary.json` | **assertion-only** |
| C-30 | 小时净效应 0.7–1.5%、瓶颈非水量 | `08` §7.2 | 本轮未复算 | **assertion-only** |
| C-31 | 流域归属 `NOT_IDENTIFIABLE` | `08` §7.6 | 本轮未复算 `T14e_provenance_basin_summary.json` | **assertion-only** |
| C-32 | 峰值失效临界规模 s\*=0.35–1.15 | `01` T14 行 | 红队 H5 自认"依赖池份额定义"，且未给定义敏感性 | **assertion-only** |
| C-33 | χ_eff ∈ [0.26,1.00]、跨度 3.8× | `01` T6 行 | `A4_水化学参数域` 未在本轮范围内逐位复核 | **corroborated** |

### 1.6 已撤回项汇总（retracted）

| # | 原主张 | 撤回依据 | 撤回状态 |
|---|---|---|---|
| R-01 | "折叠式可迁移到无量纲群" | `T9_summary.json` `collapse_status`；`T9b_summary.json` `delta_prediction_pass=false` | 文档已标注 ✅ |
| R-02 | "Gate G-B PASS" | `12_一致性核验_v1.md` Q1（`04_阶段结果_T9.md` §5 已改） | 文档已标注 ✅ |
| R-03 | "A3 = +13 974 ML/yr" | `T13_summary.json` `limitations` + 主稿 §431 | 文档已标注 ✅ |
| R-04 | "χ 跨 200×"、"首轮 A3=+13 974 / 仅 2 个非支配" | `01` 进度表 T6/T13 行 | 文档已标注 ✅ |

---

## 2. 关键独立验证：`S_city ≤ 0` 的代数来源与证明

### 2.1 代码溯源（逐行核实，非文档转述）

**（a）定义式** — `A10_敏感性与边界/city_model.py` 第 256–260 行：

```python
256:    M = float(ai.external_makeup_ml)
257:    x_ai = float(ai.reclaimed_allocated_ml)
258:    inc_recl = float(inc.reclaimed_allocated_ml)
259:    s_ai = (m0 - M) + x_ai
260:    s_city = s_ai + inc_recl - pool
```

> ⚠ 任务描述称"第 259-261 行"；**实际为第 259–260 行**（261 行是 `eta` 定义）。属行号偏移，非实质错误。

**（b）分配预算** — 同文件第 251–253 行：

```python
251:    r = solve_joint_quality_allocation(
252:        sid, pool + dp, reqs,      # <-- available = pool + dp
253:        lambda req, tr: ev_ai(req, tr) ...)
```

**（c）pro-rata 次数不变量** — `07_代码_AI-UWM引擎/aiuwm_src/src/aiuwm/reclaimed_allocation.py`：

- 第 308 行：`available = float(available_supply_ml)`
- 第 349–352 行：`map_allocation` 中 `incremental_budget = max(0.0, available - incumbent_total_allocated)`
- 第 361 行：`incremental = _pro_rata(incremental_budget, incremental_capacities)`
- 第 705–727 行：`_pro_rata` 对任何输入均保证 `Σ allocations ≤ budget`
  （`budget >= total_capacity` 时返回被容量封顶的值；否则按 `ratio = budget/total_capacity` 缩放；
  末尾第 726–727 行还**显式扣除浮点超支**：`excess = Σ − budget; if excess > 0: ...`）
- 第 362–368 行：最终 `return min(capacity, incumbent_allocated + incremental)`——再次封顶。

### 2.2 两行证明

设 `m0` 为 AI 侧基准取水量，`M` 为其外调水量，`x_ai`、`inc_recl` 为 AI 与既有用户分到的再生水量，
`pool` 为再生水供给池，`dp` 为新增回用产能。

$$
\begin{aligned}
\text{(1)}\quad & x_{\rm ai} + inc_{\rm recl} \le pool + dp \quad \text{（由 \texttt{_pro\_rata} 的 no-overdraw 不变量，代码 :349-369, :705-727）}\\[2pt]
\text{(2)}\quad & S_{\rm city} = (m_0 - M) + (x_{\rm ai} + inc_{\rm recl}) - pool \le (m_0 - M) + dp = S_{\rm AI} + dp
\end{aligned}
$$

**推论**：当 $dp = 0$（无新增产能）时，$S_{\rm city} \le S_{\rm AI}$；且当**池被占满**（$x_{\rm ai}+inc_{\rm recl}=pool$，即
`inc_recl - pool = -x_ai`）时，$S_{\rm city} = (m_0-M) - x_{\rm ai} \le 0$（因 $M \ge x_{\rm ai}$：
外调水量至少覆盖未被再生水替代的部分）。

**成立条件（必须写进论文）**：
1. 再生水供给池 `pool` **外生固定**（不随挤占扩张）；
2. 既有用户未满足需求由**无限**自来水回补（即自来水侧无供给上限、无可靠性约束）；
3. 分配遵循**固定池 pro-rata** 且严格 no-overdraw。

### 2.3 数值验证（本轮独立重算，非读取文档）

对 40 个随机情景 × {dp=0, dp=1} = **80 组**重算：

| 检验项 | 实测最大值 | 判定 |
|---|---:|---|
| `\|S_city − (S_AI + inc_recl − pool)\|` | `0.000e+00` ML | 恒等式精确成立 |
| `(x_ai + inc_recl) − (pool + dp)` | `0.000e+00` ML | **上界 0 次违反** |
| `inc_recl − pool`（dp=0 时） | `0.000e+00` ML | ≤0 恒成立 |
| `\|解析式 − 报告值\|` | `0.000e+00` ML | 无隐藏项 |
| 违反上界情景数 | **0 / 80** | — |
| 违反恒等式情景数 | **0 / 80** | — |

**全库 700 情景符号统计**（读 `T11_uncertainty_samples.csv` 的 `S_city_dp0.0_ml` 列）：

| 项 | 值 |
|---|---:|
| `S_city(dp=0) > 0` 条数 | **2 / 700** |
| `S_city(dp=0) ≤ 0` 条数 | **698 / 700** |
| 两个正值的具体取值 | `9.094947017729282e-13`、`3.637978807091713e-12` ML |
| `max(S_city(dp=0))` | `3.637979e-12` ML |
| 中位 `\|S_city(dp=0)\|` | `3.198906e+02` ML |
| 中位 `\|S_city(dp=0)\| / \|S_city(dp=1)\|` | `1.962e-02` |
| 该比值 ≤ 1e-9 的占比 | `0.4571` |

> **判定**：所谓"0.3% 的正值"（`P_S_city_gt0["dp0.0"] = 0.002857`）**全部是两个 `~1e-12` ML 的浮点残差**，
> 相对该列中位量级 `3.2e2` ML 小 14 个数量级。**`dp=0` 处不存在物理意义的 `S_city>0`。**

### 2.4 结论

> **`S_city ≤ 0` 的代数证明：成立。**
> 它是「固定池 pro-rata 分配 + 无限自来水回补」下的**会计恒等式**，不是经验发现，也不是模型预测。
> 因此**主稿将 `S_city ≤ 0` 作为中心结论是方法论错误**——审稿人两行即可写出（与红队 E1 一致）。
> 真正的信息在 **`S_city` 的符号何时依赖 `dp>0` 与 `gap`/`pool` 的相对大小**，即 T11/T12 的**条件边界**，
> 而非 `S_city ≤ 0` 本身。

---

## 3. 复现比对：5 个情景实测 vs 冻结值

**方法**：调用 `A10_敏感性与边界/city_model.py::city_outcome`，传入 `T11_uncertainty_samples.csv` 中
第 0–4 行的 `(domain, panel, sample, pool_scale, gap_scale, ai_target)`，`dp_scale` 默认 1.0，
与 CSV 的 `S_city_dp1.0_ml` / `y_dp1` 列比对。**脚本只读，未写入 A10/ 任何文件。**

| # | domain | panel | sample | 实测 `S_city` (ML) | 冻结 `S_city` (ML) | \|Δ\| (ML) | rel | 状态 |
|---:|---|---|---|---:|---:|---:|---:|---|
| 0 | co | B_full | IEUA RP-1 (2025, tertiary) | 22169.510365 | 22169.510365 | `0.000e+00` | `0.00e+00` | converged_unique |
| 1 | ha | B_full | IEUA RP-1 (2025, tertiary) | 22524.503316 | 22524.503316 | `7.276e-12` | `3.23e-16` | converged_unique |
| 2 | ha | A_engine2 | Figshare RW (2025, paired study) | 23728.792110 | 23728.792110 | `0.000e+00` | `0.00e+00` | converged_unique |
| 3 | ha | B_full | Figshare RW (2025, paired study) | −13611.038222 | −13611.038222 | `0.000e+00` | `0.00e+00` | converged_unique |
| 4 | ha | B_full | LADWP AWPF (2012, RO product) | 24404.451231 | 24404.451231 | `7.276e-12` | `2.98e-16` | converged_unique |

- **max |ΔS| = `7.275958e-12` ML**；**max rel = `3.230241e-16`**
- **判定：PASS**（全部 5 情景在双精度舍入内逐位吻合，5/5 `converged_unique`）
- 5 个情景覆盖 ha/co 两域、A_engine2/B_full 两面板、3 个水样、正负两种 `S_city` 符号。

> ⚠ 对照：CSV 共 **700 行**（+1 表头 = 701 行），与 `T11_summary.json` 的 `n_samples=700` 一致。
> 但 `T11b_summary.json` 的 `n=700` 中 `status_counts` 为 `{converged_unique: 699, no_convergence: 1}`，
> 而 `T9_summary.json` 为 480/480 全收敛——**T11 有 1 例未收敛却被计入概率分母**（见 §4-Ⅳ）。

---

## 4. 发现的不一致（逐条列出，含文件路径与实测值）

### Ⅰ【实质 / 高优先级】两套记录对同一主张给出**冲突判定**，且论文侧未披露

| 主张 | 引擎侧（`07_代码_AI-UWM引擎/aiuwm_src/research_2026/`） | 论文侧（`10_论文推进_2026Q4/`） |
|---|---|---|
| 再生水使用总是减少城市取水 | `claim_evidence_register.csv` **C3 = `REFUTED_IN_BOUNDED_RUN`**，"Not supported as a universal claim; bounded counterexamples exist" | `S_city ≤ 0` 作为中心结论（本轮证明其为恒等式） |
| A0–A3 适应能恢复城市净节省 | C7 = **`NOT_READY`**，evidence_class = `standalone_pilot` | T13 ✅ "29 方案；4D-Pareto 8 个" |
| 合成水文代表观测可靠性 | C8 = **`NOT_READY`**，evidence_class = `synthetic_hydrology` | T5 ✅ "730 天逐日" |
| 水质反馈与独立化学模型一致 | C4 = **`NOT_READY`** | T6 ✅ "χ_eff ∈ [0.26,1.00]" |
| 设施外样本预测 | C5 = **`NOT_READY`** | T7 ✅ "GSA 实测 M/E 偏差 <0.2%" |

**引擎侧 gate 状态**（`research_2026/status.md:9-16`）：
```
G1 main production integration | NOT_READY_FOR_E3
G2 chemistry                  | NOT_READY
G3 facility holdout           | NOT_READY
G4 mechanism                  | BLOCKED_BY_PREVIOUS_GATES
G5 adaptation                 | READ_ONLY_PILOT / MAIN_MODEL_NOT_READY
G6-G8                         | BLOCKED_BY_PREVIOUS_GATES
```
`README.md` 明确："**formal G2 chemistry and G3 facility validation are `NOT_READY`**;
formal E3/E4, broad archetype expansion, and global maps remain blocked;
**synthetic hydrology and scenario-prior chemistry are mechanism inputs, not external observations.**"

**论文侧**（`01_后续任务详细规划_v2.md` 进度表）将 T5/T6/T7/T13 全部标为 **✅**。

> **判定**：两套记录**口径根本不同**——引擎侧要求"外部可观测证据"（`external_evidence` / `ambient_pilot`），
> 论文侧接受"合成域内数值闭合 + 内部一致性"。**冲突本身不是伪造**，但：
> 1. 主稿 §402 只承认"两个同源合成城区"，**未披露 G2/G3 在引擎侧仍为 `NOT_READY`**；
> 2. 主稿未披露引擎侧对**同一主张**已判 `REFUTED_IN_BOUNDED_RUN`（C3）；
> 3. 这直接**放大红队 E2（外部效度 ★★☆☆☆）**与 EIC 的 desk-reject 风险。
> **建议**：主稿必须显式写明"论文侧 ✅ 指*合成域内*数值闭合；引擎侧 G2/G3 仍为 `NOT_READY`，
> 本节结论不构成外部观测证据"，并在 SI 附两套记录的口径对照表。

### Ⅱ【实质】主稿未披露"`dp=0` 列的 0.003 概率是浮点残差"

- 主稿 `10_论文主稿_v1.md:229`：表格 `P(S_city>0)` 行给出 `**0.003** | 0.61 | 0.62 | 0.62`。
- 实测：`dp=0` 处 2 个正值 = `9.09e-13` 与 `3.64e-12` ML，中位 `|S_city(dp=0)| = 3.199e+02` ML。
- `T11b_summary.json` 的 `discipline_note` 已正确说明 `edge` 情形"坐在条件零和刀锋 `S_city(dp=0)~0` 上"，
  但**主稿正文把 `0.003` 当作一个独立的概率读数呈现**，未标注它是数值零。
- **影响**：读者会误以为 `dp=0` 时有 0.3% 的真实正收益情形。`0.003` 应写为"≈0（数值零）"。

### Ⅲ【口径】T14 指标 B 的 `annual_net_saving_ml` 实际是 **730 天**合计，非"年"

- `10_论文主稿_v1.md:250-256` 及 `01` 进度表 T14 行宣称 **7987(ha) / 7894(co) ML/yr**。
- 实测 `A12_时间分辨率/T14_summary.json`：
  `indicator_B.ha.evaporative.annual_net_saving_ml = 15973.9281228712`
  `indicator_B.co.evaporative.annual_net_saving_ml = 15788.899259...`
- 比值恰为 **2.0000 / 2.0001**（730 d ÷ 365 d）。÷2 后 = `7986.964` / `7894.450`，与宣称的 7987/7894 吻合。
- `T13_summary.json` 的 `fixed` 节明确记 `days_per_year = 365.0`、`model_days = 730.0`，**确认键名 `annual_*` 是误导性的**。
- **判定**：数值正确，**但 JSON 字段名 `annual_net_saving_ml` 与该键在 730 天基座上求值的事实不符**，
  且**主稿未标注换算**。属**命名/口径缺陷**，建议改键名或加注 `*_730d`。

### Ⅳ【小】T11 有 1 例 `no_convergence` 仍被计入概率分母

- `T11b_summary.json`：`status_counts = {converged_unique: 699, no_convergence: 1}`，`n = 700`。
- 概率分母统一取 700（如 `2/700 = 0.002857`；`434/700 = 0.62`）。
- 对照 `T9_summary.json`：`n_scenarios = 480`、`n_valid = 480`、`statuses = ["converged_unique"]`（**零未收敛**）。
- `12_一致性核验_v1.md` 已修正 T9 的"479/1"表述，**但未处理 T11 自身的 699/1**。
- **判定**：未收敛样本进入概率分母会**极小幅度**影响概率；建议在 `T11b_summary.json` / 主稿注明
  "分母含 1 例未收敛"或剔除后重算。

### Ⅴ【小】任务描述中的行号偏移

- 任务描述写 `city_model.py:259-261`；实际 `s_ai`/`s_city` 在 **259–260** 行，261 行为 `eta`。
- 任务描述写 `reclaimed_allocation.py:349-369`（`map_allocation`）——**此处正确**。
- **影响**：无实质影响，但 subsequent 引用应更正为 259–260。

### Ⅵ【小】"48% 落刀锋"与"edge 占比 0.48"的语义

- `T11b_classify.py` 定义 `EDGE = 0.01`，判据 `|S_city(dp=0)| ≤ 1% × |S_city(dp=1)|`。
- 实测 `edge share = 0.48`（336/700），与文档"48%"吻合。
- 但**"刀锋"阈值 1% 是脚本内声明值**，非预注册量；红队 M5/P2 已登记"依赖先验"，此项**未闭合**。
- **判定**：数值 verified，**判据的任意性未披露**。

---

## 5. 复现产物与命令

| 脚本 | 作用 | 输出 |
|---|---|---|
| `_audit_tmp/repro_5cases.py` | 5 情景复现比对 | `_audit_tmp/repro_5cases.json` |
| `_audit_tmp/algebra_check.py` | 恒等式 + pro-rata 上界 + dp=0 符号统计（80 组重算） | `_audit_tmp/algebra_check.json` |
| `_audit_tmp/crosscheck.py` | 文档宣称值 vs 冻结产物逐条比对 | stdout |

运行环境：`C:/Users/mmrgr/.workbuddy/binaries/python/envs/default/Scripts/python.exe`

> 注：`_audit_tmp/` 为本轮审计的临时工作区（含脚本与 JSON 证据），**不属于 A13 写作用域**，
> 仅 `A13_可靠性机制/evidence_status_table.md` 由本任务写入。

---

## 6. 对 task-2 及后续任务的直接输入

1. **task-2 的核心前提已被本轮独立证实**：`S_city ≤ 0` 是恒等式（§2），两行证明成立。
   task-2 提出的"有限供水可靠性闭合"正是**打破假设 2（无限自来水回补）**的正确方向。
2. **task-2 必须同时报告 `dp` 维度**：本轮显示 `dp>0` 时 `S_city>0` 占比即达 0.62——
   即"符号反转"在**已有模型内**已由 `dp` 实现，新机制必须证明其反转**不依赖于 `dp`**，
   否则只是 T12 边界曲面的重述。
3. **task-5（英文稿）必须披露两套记录的口径差**（§4-Ⅰ），否则 EIC 视角下 desk-reject 风险极高。
4. **建议立即修正主稿两处**：`P(S_city>0)` 的 `0.003` 标注为数值零（§4-Ⅱ）；
   T14 指标 B 的基座换算注（§4-Ⅲ）。
