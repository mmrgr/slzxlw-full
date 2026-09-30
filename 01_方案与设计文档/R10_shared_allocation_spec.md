# R10 shared/dedicated 回用分配规格

## 目的

把“再生水可用量”与“AI 实际拿到的水量”分开，显式计算 incumbent 用户被置换的 potable 用水。该模块既作为可审计纯函数存在，也已接入 Q1/shared 的期初 central supply 双 DC daily slice；该 slice 仍不是正式 E3 结果。

## 输入

- `incumbent_demands_ml`: 既有用户当日再生水需求。
- `ai_demand_ml`: AI 冷却当日再生水目标需求。
- `reclaimed_supply_ml`: 当日实际可交付再生水总量（shared 模式在扣除 incumbent reservation 之前）；不得使用名义总处理能力替代。代码 API 对应 `available_supply_ml`。
- `allocation_policy`: `incumbent_first`、`pro_rata` 或 `dedicated_incremental`。
- `dedicated_supply_ml`: 仅 `dedicated_incremental` 使用，且必须标记为新增产水，不得从 shared pool 扣除。

## 输出

- incumbent delivered reclaimed volume；
- AI delivered reclaimed volume；
- incumbent displaced potable volume；
- AI potable displacement (`S_AI` 的直接供水项)；
- shared-pool withdrawal、dedicated supply、unmet reclaimed demand；
- water closure residual；
- policy/scenario identifier 和输入 seed。

## 不变量

1. shared delivery 不超过 `reclaimed_supply_ml`；allocator 内部先保护/分配 incumbent，再计算 incremental surplus；
2. dedicated supply 不挤占 incumbent shared allocation；结果必须另外报告 `preserved_incumbent_reclaimed_ml`，不能把 incumbent 从结果中隐去；
3. 所有 delivered、unmet 和 displacement 均非负；
4. `supply = shared_withdrawal + dedicated_withdrawal + residual`；
5. 对 `pro_rata`，交换用户输入顺序不改变结果；
6. 对同一输入和 policy，结果完全确定；
7. incumbent displacement 不能被误写成城市 source-water saving，后者必须在城市反事实层另算。

## E3 接口约定

四个完全配对状态为 `Q0A0`、`Q1A0`、`Q0A1`、`Q1A1`。其中 A0 使用 shared policy，A1 使用 dedicated incremental policy。主结果至少保存：

\[
\Delta_Q=Y(Q1,A0)-Y(Q0,A0),\quad
\Delta_A=Y(Q0,A1)-Y(Q0,A0),\quad
\Delta_{QA}=Y(Q1,A1)-Y(Q1,A0)-\Delta_A.
\]

首选 `Y = city source withdrawal`，并同时输出 AI potable demand、incumbent potable displacement、WWTW inflow 和 GHG。

## 接入门禁

standalone module 通过单元测试后，主模型 daily slice 还必须满足：

- 两个数据中心共享一个池的顺序交换测试；
- shared 与 dedicated 的 paired counterfactual；
- 质量状态的 source concentration 传递；
- 供给不足时的 unmet/priority 诊断；
- full-engine 水量和逐溶质闭合。

任何一项未通过，状态保持 `NOT_READY_SHARED_POOL_ALLOCATION` 或
`NOT_READY_JOINT_QUALITY_ALLOCATION`，不运行正式 E3。当前已通过双 DC 顺序交换、source-quality 传递、joint root/质量 residual、跨日 recovered-return 以及水/逐溶质闭合；same-day WWTW production、dedicated 主模型接入和 G2/G3 仍未完成。

当前 `full_engine` 仅允许显式 `reuse_allocation_mode="shared_incumbent_first"`；`dedicated_incremental` 仍停留在独立纯函数层，因为它需要独立的增量供水源，不能错误地从 shared pool 余额中扣除。
