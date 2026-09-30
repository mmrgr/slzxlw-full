# R10 门禁状态（2026-09-29）

| Gate | 状态 | 证据 | 当前解释 |
|---|---|---|---|
| G0 reproducibility | IN_PROGRESS | `07_代码_AI-UWM引擎/aiuwm_src/REPRODUCTION_MANIFEST.md` | 环境、HEAD、脏工作树与重算命令已登记；本轮新改动尚未提交 |
| G1c isolated quality solver | PASS | `src/aiuwm/quality_state.py`, `tests/test_quality_state.py`, `tests/test_data_center.py` | 隔离质量状态与固定点 fixtures 已存在；`quality_mg_l` canonical alias 已加入 CoC 计算；`compileall` 与 `git diff --check` 通过 |
| G1c main-model integration | DAILY_SLICE_PASS / CO_CURRENT_DIAGNOSTIC_PASS / NOT_READY_FOR_E3 | `src/aiuwm/full_engine.py`; `tests/test_ai_water_balance.py`, `tests/test_same_day_wwtw_phase.py` | 期初 central supply 的双 DC Q1/shared slice 已完成 treated quality → CoC → joint allocation → final plan 回写，并通过跨日 recovered-return 与水/溶质闭合；新增 opt-in bounded same-day WWTW→reuse→DC fixed-point diagnostic，AI DC fixture 已通过收敛、反馈归因和水量闭合测试；该模式仍是诊断接口，不解除 G2/G3 或正式 E3 门禁 |
| G2 chemistry cross-validation | NOT_READY | [R10 G2/G3 审计](R10_G2_G3_审计与解除条件_2026-09-30.md); `scripts/audit_g2_g3_evidence.py`; WQP ambient pilot | 129 个环境水样本已有直接 TDS/氯化物 reduced-order 对照与 IPhreeqc 逐样本诊断；条件 false-safe 为 125/129（96.9%），Spearman 排序相关约 0.250。该结果仍是环境水 `PILOT_ONLY`，缺再生水来源与人工复核，不能解除 G2 |
| G3 facility hold-out | NOT_READY | [R10 G2/G3 审计](R10_G2_G3_审计与解除条件_2026-09-30.md); `scripts/audit_g2_g3_evidence.py`; Meta 2025 annual disclosure | 已登记 18 个命名设施的 2020–2024 年度电量/取水公开披露，但没有可运行 G3 的日级表计、补水/排污/CoC 和留出 provenance |
| G4 mechanism | BLOCKED_BY_PREVIOUS_GATES | — | 先完成 G1–G3，才运行 E3 |
| G5 adaptation | ISOLATED_LEDGER_PASS / READ_ONLY_PILOT / MAIN_MODEL_NOT_READY | `src/aiuwm/adaptation.py`; `scripts/run_e4_adaptation_pilot.py`; `src/aiuwm/full_engine.py`; `tests/test_adaptation.py`, `tests/test_e4_adaptation_pilot.py` | A0–A3 的水量、溶质去向、reject/unreturned、能源、碳、成本、SLA 与 infeasible/NA 规则已在独立 ledger 通过；新增 gate-safe E4 runner 可对导出的主模型日表做 A0–A3 只读诊断并保存哈希（manifest 永远保持 `NOT_READY`，另报 `diagnostic_status=READ_ONLY`），但没有 paired B2 基线、正式适应反馈或 G2/G3 通过，因此正式 E4 仍被前置门禁阻止 |
| G6–G8 | BLOCKED_BY_PREVIOUS_GATES | — | 不运行边界、全球筛选或大规模扩展 |

## 本轮停止条件

在 G2/G3、完整生产时序和 E3/E4 全链闭合通过前，不运行正式 E3/E4，不扩展城市数量，不细化 CAWCC，也不制作全球地图。

## 已完成的最小动作

- 新增显式 opt-in `quality_state_enabled`，默认保持旧的 volume-only 行为。
- 单 DC 质量状态支持初始质量、source mixing、storage carryover、treated reuse output quality、recovered-return volume/mass carryover、CoC-scaled blowdown solute partition 与逐日残差输出；质量来源 provenance 区分 `treated_output` 与 `scenario_prior`。
- 多 DC 主模型对满足 Q1/shared 质量条件的期初 central supply slice 已返回 `READY_JOINT_CO_CURRENT`；不满足条件或质量根失败时仍返回 `NOT_READY_JOINT_QUALITY_ALLOCATION`，不会静默重复分配 shared pool。
- 新增独立 [shared/dedicated 分配规格](R10_shared_allocation_spec.md) 与 `src/aiuwm/reclaimed_allocation.py`；API 已明确 `available_supply_ml` 的总供给语义，并报告 dedicated 下 preserved incumbent；该模块已通过顺序无关性、incumbent displacement、dedicated no-displacement 和 overdraw 测试。`full_engine` 当前只允许 shared opt-in；dedicated 仍未接入，避免把独立增量水源误扣 shared pool。
- `src/aiuwm/reclaimed_allocation.py` 的 joint quality/allocation fixed-point 已接入 `full_engine`：incumbent-first、动态 external makeup、阻尼迭代、多起点 root 审计、quality residual 门禁和水量闭合均保留；当前质量分配仍明确限定为期初 central supply。新增 `same_day_wwtw_production={enabled:true,mode:"co_current_diagnostic"}` 的 bounded fixed-point 诊断，可在显式 opt-in 下把当日 WWTW 产量迭代回 central reuse→DC，并报告 provisional seed 归因、收敛残差和存储闭合；它仍不改变默认行为，也不解除 G2/G3 或正式 E3 门禁。
- E3/E4 的 Q0/Q1、shared/dedicated estimands、全链闭合与 A0–A3 可行性规则已冻结在 [R10_E3_E4_pilot_spec.md](R10_E3_E4_pilot_spec.md)；新增 `scripts/run_e3_mechanism_pilot.py` 作为四状态 paired-table 只读诊断，正式运行仍被 G2/G3、独立审阅、same-day production 时序和全链闭合门禁阻止。
- 新增独立 E4 adaptation ledger：`src/aiuwm/adaptation.py` 覆盖 A0–A3、逐溶质闭合、年化膜成本、A3 PUE/能源代价、SLA 与可行性筛选；主模型 provenance 明确为 `NOT_READY`，质量证据默认标记为 `scenario_prior`。
- 新增 gate-safe E4 只读 runner：`scripts/run_e4_adaptation_pilot.py` 读取导出的 `data_center_daily`，可选配 paired freshwater baseline 和版本化 A0–A3 config，输出 summary/daily CSV 与输入/输出哈希；`--formal` 在 G2/G3 未 `READY` 时会在适应计算前拒绝，诊断结果不改变主模型门禁。
- 新增只读边界适配器 `cooling_ledger_from_data_center_daily(...)`，以及 `FullModelResult.to_e4_ledger()` / `e4_adaptation_diagnostic()`；主模型写出 `adaptation_diagnostic.json`，只记录 A0 账本与 paired baseline 缺口，不向主模型回灌策略，故不改变 `MAIN_MODEL_NOT_READY`。
- 新增 gate-safe `scripts/audit_g2_g3_evidence.py` 与 `scripts/run_r10_pilot.py`：没有完整 G2/G3 PASS manifest 时只允许输出 diagnostic/daily-slice preflight，不执行正式 E3/E4，也不会产生 estimand 数字；当前审计结果为 G2/G3 均 `NOT_READY`。
- 已登记 AquaSPICE 公开冷却塔处理试验数据（`data/external_evidence_registry.csv`、`validation_artifacts/external_evidence/aqua_spice_manifest.json`）作为 A1/A2 参数筛选证据；其适用范围不含数据中心设施留出或 PHREEQC 交叉验证，故不改变 G2/G3 门禁。
- 新增 `scripts/run_g2_phreeqc_crosscheck.py` 独立 IPhreeqc pilot，记录数据库/输入哈希、逐样本 saturation diagnostics，以及基于直接 WQP 70300 TDS/氯化物的条件 reduced-order 对照；环境 pilot 的 false-safe 为 125/129、排序 Spearman 约 0.250，当前仍输出 `PILOT_ONLY`，G2 保持 `NOT_READY`。
- 新增 WQP 环境水化学 pilot：`scripts/acquire_wqp_chemistry.py` 将 USGS-07241550 的 129 个完整活动样本、原始文件哈希和规范化表登记为 `E2_observed_ambient`；该证据不等同于再生水或 G3 设施留出。
- 新增 Meta 公开设施年度证据审计：`R10_G3公开设施证据审计_2026-09-30.md` 与 `E2-META-2025-DC` manifest 保存 18 个命名设施 × 5 年年度电量/取水、源文件哈希及口径边界；不将无法归属设施的 leased/other 类别分摊，也不从年度值反推日序列。
- 窄范围验证：质量、分配、joint solver、数据中心、same-day production phase、full-engine、adaptation、E3/E4 gate-safe runners、registry contract、外部证据登记、WQP acquisition、PHREEQC pilot、G3 runner 与 R10 preflight 测试完整套件 `137 passed`；`python -m compileall -q src tests`、R10 审计脚本编译与 `git diff --check` → PASS。
- `scripts/build_reproduction_manifest.py` 已修复 Windows 默认代码页导致的 Git 输出解码错误，并成功重生成清单。
- G0 的最小注册表契约已落地为 `data/parameter_registry_schema.json` 与 `data/scenario_registry_schema.json`；首批 `data/parameter_registry.csv` 和 `data/scenario_registry.csv` 已生成，全部 R10 Q/L/A 情景暂标记 `not_ready`，化学点值明确标记为 `scenario_prior`。




