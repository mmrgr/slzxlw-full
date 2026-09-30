# R10 E3/E4 小试验规格（冻结前审查版）

## Q 因子

- **Q0**：质量中性对照。保持源水、库存和分配相同，但 CoC 固定为设计值；质量只记账。
- **Q1**：质量反馈。至少使用 TDS 与 chloride，按混合浓度限制 CoC。
- 每个 Q 都有独立 B2：相同 AI 负荷、reclaimed target=0、相同 Q 设定。不得把 B0 无 AI 基线混入 Q 差分。
- Q1 水质记录 `source_id, indicator, value, unit, evidence_type, source/reference, date/period, uncertainty`。缺少来源时只能标记为 scenario prior。

## 分配

- `shared`：期初池加同日可用产水，先扣除 incumbent reservation，再对剩余 surplus 做 pro-rata；priority 仅作为敏感性分析。
- `dedicated`：AI 专用增量产水/处理/库存；incumbent 交付必须保持不变。
- 为避免与 E4 adaptation 混淆，shared/dedicated 记为 `Ls/Ld`；`A0–A3` 只保留给工程适应。
- 任何 `NOT_READY_SHARED_POOL_ALLOCATION` 或 `NOT_READY_JOINT_QUALITY_ALLOCATION` 必须使门禁失败，不能生成正式 E3 数字。

## 统一 estimands

\[
S_{AI}=W_{AI,potable}^{B2_Q,m}-W_{AI,potable}^{Q,m}
\]

\[
S_{city}=W_{source}^{B2_Q,m}-W_{source}^{Q,m},\qquad
\eta_{transfer}=S_{city}/S_{AI}
\]

当 `S_AI <= 0` 时，`eta_transfer` 记为 NA 或保留带符号值并明确说明。所有状态同时输出 incumbent potable delta、AI reclaimed/potable、WWTW inflow/treated/peak utilization、energy、GHG、cost、unmet/SLA、CoC 和水质。

四个 E3 状态为 `Q0/Ls`、`Q1/Ls`、`Q0/Ld`、`Q1/Ld`。建议定义：

\[
\Delta_Q^{Ls}=Y(Q1,Ls)-Y(Q0,Ls),\quad
\Delta_Q^{Ld}=Y(Q1,Ld)-Y(Q0,Ld),
\]

\[
\Delta_L^{Q}=Y(Q,Ld)-Y(Q,Ls),\quad
\Delta_{QL}=\Delta_Q^{Ld}-\Delta_Q^{Ls}.
\]

## E3 输出与门禁

每日保存 pool start、production、incumbent reservation、每个 DC 的 request/delivery、unmet、pool end、source fractions、CoC、浓度和 storage start/end。逐溶质保存 blowdown、internal return、removed、sewer、unreturned/reject、next-state。

必须通过：

1. 水量和逐溶质全链闭合 `<=1e-6`（按尺度归一化）；
2. 非负性、容量和唯一 fixed-point residual `<=1e-10`；
3. shared delivery 不超过 surplus、无重复扣池、DC permutation invariance、pro-rata 精确性；
4. dedicated 不改变 incumbent delivery；
5. Q0 回归旧模型；
6. Q1 的水质沿 reuse treatment→DC 传递，并完成 PHREEQC 代表状态排序/限制物种/CoC cross-check 和 false-safe 统计。

## E4 A0–A3

- A0：无适应，质量受限湿式基线。
- A1：化学/旁流处理，显式物种去除、剂量、reject mass、energy、cost。
- A2：膜处理，显式 recovery、permeate/reject、溶质去向、energy、replacement/capex。
- A3：混合/干式排热，显式 wet fraction、节水、额外 PUE/energy/GHG。

固定 IT load、天气和城市需求。每个适应方案输出全部 E3 estimands，以及 SLA、WWTW 负荷、能源、碳、年化 CAPEX/OPEX、reject 和 provenance。
当前单 DC 与双 DC opt-in Q1/shared 的期初 central supply slice 已将 treated output quality 传入 CoC fixed-point，joint allocation 回写最终计划，并记录 CoC-scaled blowdown 的逐溶质分配；新增显式 opt-in bounded same-day WWTW→reuse→DC fixed-point diagnostic，已通过 AI DC feedback、体积/质量残差和存储闭合测试，但完整 E3 仍保持未就绪。`scripts/run_e3_mechanism_pilot.py` 已提供四状态 paired-table 的只读差分诊断，会校验 common seed/provenance、逐日/DC 键完全配对、B2 基线和 `S_AI/S_city/eta_transfer`；它不调用主模型，也不会把 pilot 结果升级为正式 E3。单 DC recovered-return volume/mass 已可带入下一日质量求解。`quality_provenance=treated_output` 仅在 reuse pollutant ledger 有质量或显式声明时使用，否则保持 `scenario_prior`。

当前 `src/aiuwm/adaptation.py` 和 `scripts/run_e4_adaptation_pilot.py` 仍是只读 E4 ledger/diagnostic：它们验证 A0–A3 的水量/逐溶质闭合、reject/unreturned、能源、碳、成本、SLA 及 infeasible/NA 处理，并可读取主模型 daily rows；不会回灌适应策略。其 `provenance.main_model_integration=READ_ONLY_BOUNDARY`，在 paired B2、正式耦合反馈和独立审阅完成前，不得将诊断结果写入正式 E4 主结果。

`E*_adapt` 与 `C*_adapt` 只在满足 `S_city >= 0`、SLA/reliability、WTW/WWTW/reuse/source margin、grid/energy/carbon/cost caps 的方案中取最小值；无可行方案时写 `infeasible/NA`，不得写 0 或无穷。Pareto 集只包含可行点。



