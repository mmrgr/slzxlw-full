# 系统验证文件 — 去AI味系统

> 本文件用于在系统交付与每次重大变更后，对系统结构、Agent定义、知识库完整性、工作流一致性、记忆系统和质量保障机制进行完整性验证。每项检查给出"检查方法""期望结果""通过判据"，逐项执行并记录结果。

验证执行人：质量把控师（quality_controller）或独立校验者
验证日期：__________

---

## 1. 结构完整性检查

**目的**：确认系统所有必要文件已就位。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 1.1 | 核心配置文件 | 检查 `agent_manifest.json`、`workflow.json`、`AGENTS.md`、`README.md`、`config/system_config.yaml` 是否存在 | 5个文件均存在且非空 | 全部存在 | ☐通过 ☐未通过 |
| 1.2 | 知识库目录 | 检查 `knowledge/` 下 3 个文件 | ai_signatures.md / detection_rules.md / humanization_techniques.md 均存在 | 3个齐全 | ☐通过 ☐未通过 |
| 1.3 | Schema目录 | 检查 `schemas/` 下 3 个文件 | detection_report.schema.json / simulation_report.schema.json / modification_record.schema.json 均存在 | 3个齐全 | ☐通过 ☐未通过 |
| 1.4 | 记忆系统目录 | 检查 `memory/` 目录 | 含 effective_strategies / failed_strategies / text_patterns / user_preferences 4个JSON + README.md | 5个齐全 | ☐通过 ☐未通过 |
| 1.5 | 报告与测试 | 检查 `reports/generation_report.md`、`tests/system_validation.md` | 两文件存在 | 存在 | ☐通过 ☐未通过 |
| 1.6 | JSON语法合法性 | 对所有 `.json` 文件执行 JSON 解析 | 全部为合法JSON，无语法错误 | 0 错误 | ☐通过 ☐未通过 |
| 1.7 | YAML语法合法性 | 对 `config/system_config.yaml` 执行 YAML 解析 | 合法YAML，无语法错误 | 0 错误 | ☐通过 ☐未通过 |

---

## 2. Agent定义完整性检查

**目的**：确认 `agent_manifest.json` 中 6 个 Agent 定义完整且互斥。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 2.1 | Agent数量 | 读取 `agent_manifest.json` 的 `total_agents` 与 `agents` 数组长度 | 均为 6 | 数值一致=6 | ☐通过 ☐未通过 |
| 2.2 | 必填字段齐全 | 逐个 Agent 检查 agent_name / role / responsibilities / phases_active / read_scope / write_scope / max_retries / completion_condition / forbidden_actions | 9 个字段全部存在 | 无缺失 | ☐通过 ☐未通过 |
| 2.3 | 角色集合 | 核对 6 个 agent_name | ai_detector / structure_reorganizer / language_humanizer / logic_enhancer / detection_simulator / quality_controller | 完全匹配 | ☐通过 ☐未通过 |
| 2.4 | 职责互斥 | 检查 Phase 2 三个并行Agent的 responsibilities 是否重叠 | 结构重组师只处理structural，语言人性化师只处理lexical+statistical，逻辑深化师只处理logical+emotional，无核心职责重叠 | 无冲突 | ☐通过 ☐未通过 |
| 2.5 | 编排者 | 检查 `orchestrator` 字段 | 值为 `quality_controller` | 一致 | ☐通过 ☐未通过 |
| 2.6 | 最大并行 | 检查 `max_parallel` | 值为 3 | 一致 | ☐通过 ☐未通过 |
| 2.7 | 写权限无冲突 | 检查 Phase 2 并行Agent（structure_reorganizer / language_humanizer / logic_enhancer）的 write_scope | 三个Agent的 write_scope 均为空数组（不直接写文件，由quality_controller合并） | 无并行写冲突 | ☐通过 ☐未通过 |
| 2.8 | max_retries | 检查所有 Agent | 均为 3 | 全部=3 | ☐通过 ☐未通过 |
| 2.9 | forbidden_actions非空 | 检查所有 Agent 的 forbidden_actions | 均为非空数组，含至少3条禁止项 | 全部非空 | ☐通过 ☐未通过 |

---

## 3. 知识库完整性检查

**目的**：确认3个知识库文件内容完整，覆盖检测和修改所需的全部知识。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 3.1 | AI味特征知识库 | 检查 `knowledge/ai_signatures.md` | 包含六大类特征定义（结构/词汇/统计/逻辑/情感/文体）+ 检测清单 + 检测工具矩阵 | 六大类齐全 | ☐通过 ☐未通过 |
| 3.2 | 检测规则手册 | 检查 `knowledge/detection_rules.md` | 包含至少5种检测工具原理 + 7维度评分标准 + 各文体检测阈值 + 6条核心原则 | 齐全 | ☐通过 ☐未通过 |
| 3.3 | 人性化技术手册 | 检查 `knowledge/humanization_techniques.md` | 包含T1-T7七大技术 + 中英文替换表 + 操作示例 | 七大技术齐全 | ☐通过 ☐未通过 |
| 3.4 | 知识库引用一致 | 核对 `config/system_config.yaml` 中 knowledge_refs 引用的文件路径 | 3个路径均指向 knowledge/ 下实际存在的文件 | 一致 | ☐通过 ☐未通过 |
| 3.5 | Agent读取范围 | 核对 `agent_manifest.json` 中各Agent read_scope 引用的知识库路径 | ai_detector 和 detection_simulator 引用 ai_signatures+detection_rules；三个修改Agent引用 humanization_techniques | 一致 | ☐通过 ☐未通过 |

---

## 4. 工作流一致性检查

**目的**：确认 `workflow.json` 的7个task依赖关系正确、无环、关键路径完整、并行机会合理。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 4.1 | Task数量 | 读取 `tasks` 数组长度 | 为 7 | 一致=7 | ☐通过 ☐未通过 |
| 4.2 | Task ID完整 | 核对 task_id | phase1_detection / phase2a_structure / phase2b_language / phase2c_logic / phase2d_merge / phase3_simulation / phase3_final_review | 完整匹配 | ☐通过 ☐未通过 |
| 4.3 | 依赖无环 | 检查 depends_on 形成的图 | phase1→phase2a/b/c（并行）→phase2d→phase3→phase3_final_review，无环 | 无环 | ☐通过 ☐未通过 |
| 4.4 | Phase 2并行 | 核对 phase2a/b/c 的 parallel_group | 均为 2，depends_on 均为 ["phase1_detection"] | 三路同组 | ☐通过 ☐未通过 |
| 4.5 | 合并点依赖 | 核对 phase2d_merge 的 depends_on | 为 ["phase2a_structure", "phase2b_language", "phase2c_logic"]，等待三路完成 | 三路齐备 | ☐通过 ☐未通过 |
| 4.6 | 关键路径 | 核对 `critical_path` | 为 phase1_detection → phase2d_merge → phase3_simulation → phase3_final_review | 完整匹配 | ☐通过 ☐未通过 |
| 4.7 | 并行机会 | 核对 `parallel_opportunities` | 含 Phase 2 三路并行（phase2a/b/c），sync_point 为 phase2d_merge | 齐全 | ☐通过 ☐未通过 |
| 4.8 | 迭代配置 | 核对 `iteration_config` | max_iterations=3，含 iteration_loop、termination_condition、modification_density_by_round、not_passed_action | 齐全 | ☐通过 ☐未通过 |
| 4.9 | Agent一致 | 核对各 task 的 `agent` 与 `agent_manifest.json` 的 agent_name | phase1=ai_detector; 2a=structure_reorganizer; 2b=language_humanizer; 2c=logic_enhancer; 2d/3final=quality_controller; 3sim=detection_simulator | 一致 | ☐通过 ☐未通过 |
| 4.10 | 风险等级 | 核对各 task 的 risk_level | phase2d_merge 和 phase3_final_review 为 high，其余为 medium | 合理 | ☐通过 ☐未通过 |

---

## 5. 记忆系统检查

**目的**：确认记忆文件可读写、格式合法、更新规则明确。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 5.1 | 文件存在 | 检查 `memory/` 下 4 个JSON文件 | effective_strategies / failed_strategies / text_patterns / user_preferences 均存在 | 4个齐全 | ☐通过 ☐未通过 |
| 5.2 | 初始状态 | 检查 4 个JSON文件内容 | effective_strategies/failed_strategies/text_patterns 为空数组 `[]`；user_preferences 含 version 和 last_updated 字段 | 符合初始状态 | ☐通过 ☐未通过 |
| 5.3 | JSON合法性 | 对 4 个JSON文件执行 JSON 解析 | 全部为合法JSON | 0 错误 | ☐通过 ☐未通过 |
| 5.4 | README说明 | 检查 `memory/README.md` | 包含4个文件用途说明、更新规则、记录格式示例、记忆使用方式表 | 齐全 | ☐通过 ☐未通过 |
| 5.5 | 配置引用 | 核对 `config/system_config.yaml` 中 memory.files 引用的路径 | 4个路径均指向 memory/ 下实际存在的文件 | 一致 | ☐通过 ☐未通过 |
| 5.6 | 读写权限映射 | 核对 `agent_manifest.json` 中各Agent read_scope/write_scope 引用的 memory 路径 | ai_detector 和 detection_simulator 可写 text_patterns.json；quality_controller 可写全部4个记忆文件；三个修改Agent只读 effective/failed_strategies | 一致 | ☐通过 ☐未通过 |
| 5.7 | 单写者原则 | 检查同一 memory 文件是否被多个并行Agent写入 | text_patterns.json 被 ai_detector（Phase 1）和 detection_simulator（Phase 3）写入，但两者不同时执行，无并行冲突；quality_controller 独占 effective/failed/user_preferences 写权限 | 无并行写冲突 | ☐通过 ☐未通过 |
| 5.8 | 容量限制 | 核对 `config/system_config.yaml` 中 memory.max_strategy_records | 值为 200 | 一致 | ☐通过 ☐未通过 |

---

## 6. 质量保障检查

**目的**：确认不可修改内容清单、质量检查清单、过度修改防护和降级策略配置完整。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 6.1 | 不可修改内容清单 | 核对 `config/system_config.yaml` 中 quality.unmodifiable_content | 含4类：数据/引用/术语/核心论点，每类含 type/reason/rule | 4类齐全 | ☐通过 ☐未通过 |
| 6.2 | 质量检查清单 | 核对 `config/system_config.yaml` 中 quality.checklist | 含10项检查项 | 10项齐全 | ☐通过 ☐未通过 |
| 6.3 | 过度修改防护 | 核对 `config/system_config.yaml` 中 quality.over_modification_guard | max_modification_ratio 为 0.70，含 description | 存在 | ☐通过 ☐未通过 |
| 6.4 | 文体阈值 | 核对 `config/system_config.yaml` 中 text_type_thresholds | 含5种文体（academic_paper/novel/news/blog/other），每种含 target/hard_limit/key_dimensions/allowed_features/notes | 5种齐全 | ☐通过 ☐未通过 |
| 6.5 | 降级策略 | 核对 `config/system_config.yaml` 中 degradation | 含5级降级 + non_degradable 列表 | 齐全 | ☐通过 ☐未通过 |
| 6.6 | 不可降级项 | 核对 degradation.non_degradable | 含原意保留/数据准确性/引用完整性/语言基本通顺 | 4项齐全 | ☐通过 ☐未通过 |
| 6.7 | 质量把控师禁止项 | 核对 `agent_manifest.json` 中 quality_controller 的 forbidden_actions | 含"放行未通过质量检查的文本""修改不可修改内容""终审时降低质量标准"等 | 齐全 | ☐通过 ☐未通过 |
| 6.8 | Schema校验可用 | 检查 3 个 Schema 文件是否可被引用 | detection_report / simulation_report / modification_record 三个 Schema 均定义了 required 字段和 additionalProperties: false | 可校验 | ☐通过 ☐未通过 |
| 6.9 | 深度思考配置 | 核对 `config/system_config.yaml` 中 phases 的 deep_thinking 标记 | Phase 1/2/3 均标记 deep_thinking: true | 3个阶段均启用 | ☐通过 ☐未通过 |
| 6.10 | AGENTS.md一致性 | 核对 AGENTS.md 中描述的流程、角色、质量保障与配置文件一致 | Agent名称/阶段划分/不可修改内容/检查清单与配置文件匹配 | 一致 | ☐通过 ☐未通过 |

---

## 验证结论

- 总检查项数：____
- 通过项数：____
- 未通过项数：____
- 未通过项编号及处置：________________

**交付判定**：全部检查项通过 ☐ 是 ☐ 否。仅当全部通过时，系统可投入正式运行；存在未通过项须修复后复验。
