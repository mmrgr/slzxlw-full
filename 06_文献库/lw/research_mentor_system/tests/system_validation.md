# 系统验证文件 — Nature子刊研究导师系统

> 本文件用于在系统交付与每次重大变更后，对系统结构、Agent定义、工作流、记忆系统、深度思考集成、首次对话流程与阶段转换检查点进行完整性验证。每项检查给出"检查方法""期望结果""通过判据"，逐项执行并记录结果。

验证执行人：主导师（principal_mentor）或独立校验者
验证日期：__________

---

## 1. 结构完整性检查

**目的**：确认系统所有必要文件已就位。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 1.1 | 核心配置文件 | 检查 `agent_manifest.json`、`workflow.json`、`AGENTS.md`、`README.md` 是否存在 | 4个文件均存在且非空 | 全部存在 | ☐通过 ☐未通过 |
| 1.2 | 需求文件目录 | 检查 `requirements/` 下 4 个文件 | requirements.json / assumptions.json / open_questions.json / acceptance_criteria.json 均存在 | 4个齐全 | ☐通过 ☐未通过 |
| 1.3 | Agent定义目录 | 检查 `agents/` 目录 | 含 6 个 `{agent_name}.md` 文件 | 6个齐全 | ☐通过 ☐未通过 |
| 1.4 | 记忆系统目录 | 检查 `memory/` 目录结构 | 含 user_profile / learning_progress / decisions / knowledge_gaps 及 episodic/semantic/procedural/evaluation 子目录 | 结构完整 | ☐通过 ☐未通过 |
| 1.5 | 报告与测试 | 检查 `reports/generation_report.md`、`tests/system_validation.md` | 两文件存在 | 存在 | ☐通过 ☐未通过 |
| 1.6 | JSON语法合法性 | 对所有 `.json` 文件执行 JSON 解析 | 全部为合法JSON，无语法错误 | 0 错误 | ☐通过 ☐未通过 |

---

## 2. Agent定义完整性检查

**目的**：确认 `agent_manifest.json` 中 6 个 Agent 定义完整且互斥。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 2.1 | Agent数量 | 读取 `agent_manifest.json` 的 `total_agents` 与 `agents` 数组长度 | 均为 6 | 数值一致=6 | ☐通过 ☐未通过 |
| 2.2 | 必填字段齐全 | 逐个 Agent 检查 agent_name / role / responsibilities / phases_active / read_scope / write_scope / max_retries / completion_condition / forbidden_actions | 9 个字段全部存在 | 无缺失 | ☐通过 ☐未通过 |
| 2.3 | 角色集合 | 核对 6 个 agent_name | principal_mentor / literature_researcher / methodology_mentor / writing_coach / peer_reviewer / memory_curator | 完全匹配 | ☐通过 ☐未通过 |
| 2.4 | 职责互斥 | 检查 responsibilities 是否存在明显重叠 | 各Agent职责边界清晰，无核心职责重叠 | 无冲突 | ☐通过 ☐未通过 |
| 2.5 | 编排者 | 检查 `orchestrator` 字段 | 值为 `principal_mentor` | 一致 | ☐通过 ☐未通过 |
| 2.6 | 最大并行 | 检查 `max_parallel` | 值为 2 | 一致 | ☐通过 ☐未通过 |
| 2.7 | 写权限无冲突 | 检查并行Agent（Phase 5 的 writing_coach 与 peer_reviewer）write_scope 是否重叠 | writing_drafts/* 与 review_reports/* 不重叠 | 无重叠 | ☐通过 ☐未通过 |
| 2.8 | max_retries | 检查所有 Agent | 均为 3 | 全部=3 | ☐通过 ☐未通过 |
| 2.9 | 对应md文件 | 检查 `agents/{agent_name}.md` 是否存在 | 6个md文件齐全 | 齐全 | ☐通过 ☐未通过 |

---

## 3. 工作流一致性检查

**目的**：确认 `workflow.json` 的 8 个阶段连贯、依赖无环、关键路径完整。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 3.1 | 阶段数量 | 读取 `phases` 与 `tasks` 数组长度 | 均为 8 | 一致=8 | ☐通过 ☐未通过 |
| 3.2 | task_id 连续 | 核对 task_id | phase_0 至 phase_7 连续无缺 | 无缺漏 | ☐通过 ☐未通过 |
| 3.3 | 依赖无环 | 检查 depends_on 形成的图 | phase_n 依赖 phase_(n-1)，形成线性链，无环 | 无环 | ☐通过 ☐未通过 |
| 3.4 | 关键路径 | 核对 `critical_path` | 为 phase_0→…→phase_7 的完整序列 | 完整匹配 | ☐通过 ☐未通过 |
| 3.5 | 主导Agent一致 | 核对各 task 的 `agent` 与 AGENTS.md 主导Agent | phase_0=principal_mentor; 1/3/4=methodology_mentor; 2=literature_researcher; 5/7=writing_coach; 6=peer_reviewer | 一致 | ☐通过 ☐未通过 |
| 3.6 | phases_active 覆盖 | 核对 manifest 中各 Agent phases_active 与其主导/支持阶段吻合 | 文献研究员[0,2,6]; 方法论[1,3,4]; 写作[2,5,7]; 审稿[5,6]; 主导师/记忆管家全程 | 一致 | ☐通过 ☐未通过 |
| 3.7 | 并行机会 | 核对 `parallel_opportunities` | 含 Phase 2 与 Phase 5 两条 | 齐全 | ☐通过 ☐未通过 |
| 3.8 | 总周期 | 核对 `total_estimated_weeks` | 为 "20-40" | 一致 | ☐通过 ☐未通过 |
| 3.9 | 每阶段检查点 | 各 task 含 `checkpoints` 数组且非空 | 8 个 task 均有 ≥3 条检查点 | 全部非空 | ☐通过 ☐未通过 |

---

## 4. 记忆系统检查

**目的**：确认记忆文件可读写、跨阶段可传递。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 4.1 | 目录可写 | 尝试向 `memory/` 各子目录写入测试文件并删除 | 写入/读取/删除均成功 | 全部成功 | ☐通过 ☐未通过 |
| 4.2 | 关键记忆文件 | 检查 user_profile / learning_progress / decisions / knowledge_gaps 文件（首次对话前可空但须可创建） | 文件可创建且为合法JSON结构 | 可创建 | ☐通过 ☐未通过 |
| 4.3 | 读写权限映射 | 核对 manifest 中各Agent read_scope/write_scope 引用的 memory 路径是否存在对应目录 | notes/literature_notes / methodology_notes / writing_drafts / review_reports / episodic / semantic / procedural / evaluation 目录齐备 | 齐备 | ☐通过 ☐未通过 |
| 4.4 | 单写者原则 | 检查同一 memory 文件是否被多个Agent写入 | decisions.json 仅 principal_mentor 可写；research_context.json 仅 literature_researcher 与 methodology_mentor 写（不同阶段，非并行） | 无并行写冲突 | ☐通过 ☐未通过 |
| 4.5 | 版本管理 | 模拟一次决策变更，检查 memory_curator 是否保留旧版本 | 旧版本保留而非覆盖 | 保留 | ☐通过 ☐未通过 |
| 4.6 | 跨阶段传递 | 模拟 Phase 0→1 转换，检查 decisions.json 中选定方向是否可被 Phase 1 读取 | 上下文成功传递 | 成功 | ☐通过 ☐未通过 |

---

## 5. 深度思考集成检查

**目的**：确认 Phase 3 与 Phase 5 存在深度思考强制触发点，且推理脚手架可用。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 5.1 | 触发点存在 | 在 AGENTS.md 中检索"深度思考强制触发" | Phase 3 与 Phase 5 均标注强制触发 | 两处齐备 | ☐通过 ☐未通过 |
| 5.2 | Phase 3 脚手架 | 核对 Phase 3 Step 3 的 7 步推理脚手架（数据类型→方法列举→优缺点→可行性→选定→失败模式→应对） | 7 步完整 | 完整 | ☐通过 ☐未通过 |
| 5.3 | Phase 5 脚手架 | 核对 Phase 5 Step 5 讨论撰写的 7 步推理脚手架（最重要发现→意义→新在哪→机制→局限→未来→take-home） | 7 步完整 | 完整 | ☐通过 ☐未通过 |
| 5.4 | 协议文件可达 | 检查 `../agent_factory/thinking/deep_thinking_protocol.md` 引用路径可达 | 文件存在可读 | 可达 | ☐通过 ☐未通过 |
| 5.5 | 按需触发条件 | 核对 AGENTS.md 第7节按需触发条件（理解困难/结果矛盾/审稿重大问题/方向选择困难） | 4 条齐备 | 齐备 | ☐通过 ☐未通过 |
| 5.6 | 多方案比较 | 核对 Phase 3 研究问题≥2版本比较、Phase 5 标题≥3版本比较 | 均有强制多方案比较 | 齐备 | ☐通过 ☐未通过 |
| 5.7 | 反事实思考 | 核对 Phase 3 主导师反事实审核、Phase 4 结果反事实解读 | 两处齐备 | 齐备 | ☐通过 ☐未通过 |

---

## 6. 首次对话流程检查

**目的**：确认首次对话引导逻辑正确，能建立用户画像并进入 Phase 0。

| 编号 | 检查项 | 检查方法 | 期望结果 | 通过判据 | 结果 |
|------|--------|----------|----------|----------|------|
| 6.1 | 启动流程定义 | 核对 AGENTS.md 第1节"每次对话启动流程"5 个 Step | 加载记忆→首次判断→阶段判断→加载上下文→交互 | 5步齐备 | ☐通过 ☐未通过 |
| 6.2 | 首次判定 | 检查"记忆文件为空或不存在"判定逻辑 | 逻辑存在且正确 | 存在 | ☐通过 ☐未通过 |
| 6.3 | 引导话术 | 核对首次对话6个问题（背景/方向/时间/资源/英文/期刊） | 6个问题齐备 | 齐备 | ☐通过 ☐未通过 |
| 6.4 | 画像写入 | 模拟首次对话，检查回答是否写入 `memory/user_profile.json` | 写入成功且为合法JSON | 成功 | ☐通过 ☐未通过 |
| 6.5 | 开放问题对齐 | 核对 `requirements/open_questions.json` 的7个问题与首次对话话术覆盖一致 | 一一对应 | 一致 | ☐通过 ☐未通过 |
| 6.6 | 假设确认 | 核对 `requirements/assumptions.json` 的假设在首次对话中得到确认 | 8条假设均有验证途径 | 齐备 | ☐通过 ☐未通过 |
| 6.7 | 进入Phase 0 | 检查画像写入后是否进入 Phase 0 | 流程衔接正确 | 正确 | ☐通过 ☐未通过 |

---

## 7. 阶段转换检查点验证

**目的**：确认 8 个阶段的转换检查点充分、可验证、不可绕过。

| 编号 | 阶段 | 关键检查点 | 检查方法 | 通过判据 | 结果 |
|------|------|-----------|----------|----------|------|
| 7.0 | Phase 0→1 | 方向已选定/理由书通过审阅/可行性有文献支撑 | 核对 workflow phase_0.checkpoints 与 AGENTS.md Phase 0 转换检查点 | 3条齐备且一致 | ☐通过 ☐未通过 |
| 7.1 | Phase 1→2 | 核心概念掌握/≥3篇seminal论文笔记/知识图谱覆盖 | 核对 phase_1.checkpoints | 3条齐备 | ☐通过 ☐未通过 |
| 7.2 | Phase 2→3 | 综述初稿通过审阅/≥1个研究空白/研究问题初成 | 核对 phase_2.checkpoints | 3条齐备 | ☐通过 ☐未通过 |
| 7.3 | Phase 3→4 | 研究问题通过审核/假说可证伪/方法可行且失败模式有应对/计划书通过 | 核对 phase_3.checkpoints | 4条齐备 | ☐通过 ☐未通过 |
| 7.4 | Phase 4→5 | 数据收集完成/分析可复现/图表达Nature标准/结果解读正确 | 核对 phase_4.checkpoints | 4条齐备 | ☐通过 ☐未通过 |
| 7.5 | Phase 5→6 | 章节齐全且审稿意见已回应/逻辑连贯/图表达标/无重大问题 | 核对 phase_5.checkpoints | 4条齐备 | ☐通过 ☐未通过 |
| 7.6 | Phase 6→7 | 审稿意见处理完毕/二审通过或仅minor/修改对照表完整/主导师终审 | 核对 phase_6.checkpoints | 4条齐备 | ☐通过 ☐未通过 |
| 7.7 | Phase 7→交付 | 投稿材料完成/格式合规/最终清单通过/主导师终审 | 核对 phase_7.checkpoints + acceptance_criteria | 4条齐备 | ☐通过 ☐未通过 |
| 7.8 | 不可绕过 | 核对 principal_mentor forbidden_actions 含"跳过阶段或绕过检查点" | 禁止项存在 | 存在 | ☐通过 ☐未通过 |
| 7.9 | 回退机制 | 核对 AGENTS.md"不满足时继续当前阶段或回退" | 回退逻辑存在 | 存在 | ☐通过 ☐未通过 |

---

## 验证结论

- 总检查项数：____
- 通过项数：____
- 未通过项数：____
- 未通过项编号及处置：________________

**交付判定**：全部检查项通过 ☐ 是 ☐ 否。仅当全部通过时，系统可投入正式运行；存在未通过项须修复后复验。

**验收标准对齐**：本验证与 `requirements/acceptance_criteria.json` 的 5 组标准（研究设计/数据分析/论文完成度/模拟审稿/投稿材料）一一对应，确保交付物满足既定验收门槛。
