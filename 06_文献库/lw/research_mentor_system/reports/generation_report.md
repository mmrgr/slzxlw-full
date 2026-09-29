# 生成报告 — Nature子刊研究导师系统

> 本报告记录本系统如何通过 Agent Factory 流程生成，涵盖需求分析、架构决策、Agent设计、工作流设计、记忆系统、深度思考集成、质量保障、已知限制与后续优化方向。

生成系统：Nature子刊研究导师系统（research_mentor_system）
生成框架：Agent Factory（位于 `../agent_factory/`）
生成日期：2026-07-31
版本：1.0

---

## 1. 需求分析摘要

**用户原始需求**：构建一个"Nature子刊研究导师系统"，由 AI Coding Agent 扮演6种角色，指导零基础用户完成环境科学研究并写出 Nature 子刊水平论文，跨越8个阶段（Phase 0-7）。

**Requirement Analyst 分析结论**：
- 任务类型：长期运行（long_running=true）、交互式教学-研究-写作陪伴系统，跨度20-40周。
- 交付物：Nature 子刊水平研究论文 + 完整投稿材料（deliverable_type=research_paper）。
- 关键属性：需联网检索文献（needs_internet=true）、需文件处理（needs_file_processing=true）、质量优先（user_priority=quality）、高风险（risk_level=high）、严格模式（mode=strict）。
- 准确性关键步骤：研究设计、假说可证伪性、数据收集质控、统计分析、结果解读、引用核对。
- 待确认问题：7项（用户背景/方向/时间/资源/英文/期刊/工具基础），详见 `requirements/open_questions.json`。
- 合理假设：8项，详见 `requirements/assumptions.json`。

需求文档产出：`requirements/requirements.json`，并通过 `assumptions.json`、`open_questions.json`、`acceptance_criteria.json` 配套约束。

---

## 2. 架构决策

**决策：分层多Agent + 交互式教学模式**

理由：
1. **任务跨度长、环节异质**：从方向探索到投稿，涉及文献检索、研究设计、数据分析、学术写作、同行评审等多类专长，单一Agent难以兼顾深度与质量，故采用多Agent分工。
2. **零基础用户需教学陪伴**：不是一次性流水线，而是数月的师生关系，需交互式教学（讲授→提问→任务→审阅→迭代），故采用"导师-学生"角色隐喻而非纯流水线。
3. **分层编排**：设主导师为 Orchestrator 全程统筹，5个专家Agent按阶段出场，1个记忆管家后台支撑，形成"统筹层-专家层-支撑层"三层结构。
4. **受并发约束**：max_parallel=2，因为交互式系统本质是单用户串行对话，并行仅用于撰写-审稿流水线等局部环节，避免Token浪费与上下文污染。
5. **严格模式**：高风险正式交付，启用全量审核、转换检查点、冲突裁决与完整追踪。

**与 Agent Factory 架构原则的对齐**：遵循最小权限（read_scope/write_scope）、单写者（并行Agent写权限不重叠）、确定性优先（检查点可机器核验）、引用路径而非复制内容（记忆按路径加载）。

---

## 3. Agent设计（6个角色的设计理由）

| Agent | 设计理由 |
|-------|----------|
| **主导师 principal_mentor** | 研究全流程需统一规划与质量把关者。零基础用户易迷失方向，需一位"总导师"统筹阶段转换、裁决分歧、执行终审。设为 Orchestrator 全程在场，避免各专家Agent各自为政。 |
| **文献研究员 literature_researcher** | 文献检索、空白识别、引用核对是研究起点与投稿前必做项，需专门专长。活跃于 Phase 0（可行性验证）、Phase 2（综述主导）、Phase 6（引用补充），职责聚焦且禁止撰写正文以与写作教练互斥。 |
| **方法论导师 methodology_mentor** | 研究设计、数据收集、分析解读决定科学性，是"不可降级"核心。活跃于 Phase 1/3/4，承担知识图谱构建与失败模式预判，是深度思考的主要承载者。 |
| **写作教练 writing_coach** | Nature 子刊写作有高度专业化要求（漏斗式引言、讨论推理脚手架、图表设计），需独立专长。活跃于 Phase 2（综述写作支持）、Phase 5（正文主导）、Phase 7（投稿材料），与审稿模拟员形成"写-审"分离。 |
| **审稿模拟员 peer_reviewer** | Nature 子刊标准需独立审稿视角，写作者不可自审。设独立Agent在 Phase 5（分节即时审）、Phase 6（全文审+二审）出场，五维度审稿且禁止直接改稿，确保审稿独立性与标准不降。 |
| **记忆管家 memory_curator** | 跨数月、跨会话系统必须持久化用户画像、进度、决策、知识盲区。设后台Agent全程维护记忆、压缩上下文、管理Token，使主导师与专家层无需各自处理记忆，职责单一化。 |

**职责互斥设计**：文献研究员不写正文、审稿模拟员不改稿、写作教练不做统计分析、方法论导师不做文献综述撰写，从 forbidden_actions 强制隔离。

---

## 4. 工作流设计（8阶段路线图的设计理由）

**决策：线性关键路径 + 局部并行**

8 阶段构成线性关键路径（phase_0→…→phase_7），因为研究本身具有强时序依赖（无方向则无设计，无设计则无数据，无数据则无论文）。每个阶段设 3-4 个可验证转换检查点，未通过不得推进，可回退补强。

| 阶段 | 时长 | 主导Agent | 设计理由 |
|------|------|-----------|----------|
| Phase 0 方向探索 | 1-2周 | 主导师 | 零基础用户需先建立全景认知再选向，主导师统筹+文献研究员验证可行性 |
| Phase 1 基础建立 | 2-4周 | 方法论导师 | 选定方向后需知识图谱与概念内化，方法论导师教授+文献研究员配 seminal 论文 |
| Phase 2 文献综述 | 3-6周 | 文献研究员 | 综述是研究空白识别与论文引言的基础，文献研究员主导+写作教练并行教写作 |
| Phase 3 研究设计 | 2-4周 | 方法论导师 | 决定研究成败，强制深度思考（多方案比较+失败模式预判+反事实审核） |
| Phase 4 数据收集与分析 | 4-12周 | 方法论导师 | 实证核心，时长弹性最大，需质控与可复现分析 |
| Phase 5 论文撰写 | 4-8周 | 写作教练 | 写作需深度（讨论推理脚手架），审稿模拟员并行即时审形成流水线 |
| Phase 6 审稿与修改 | 2-4周 | 审稿模拟员 | 独立审稿视角主导，写作教练执行修改，二审闭环 |
| Phase 7 投稿准备 | 1-2周 | 写作教练 | 格式合规与投稿材料，主导师终审 |

**并行机会**：Phase 2（文献检索与综述写作教学并行）、Phase 5（撰写与即时审稿流水线），均受 max_parallel=2 约束且写权限不冲突。

**风险分布**：Phase 3/4/5 为 high risk（决定科学性与论文质量），Phase 0/1/2/6 为 medium，Phase 7 为 low，与 max_retries=3、strict 模式审核力度匹配。

---

## 5. 记忆系统设计

**结构**（见 AGENTS.md 第6节）：
```
memory/
├── user_profile.json        用户背景与偏好（主导师写）
├── learning_progress.json   当前进度与阶段（主导师/记忆管家写）
├── decisions.json           关键决策（主导师写，记忆管家版本管理）
├── knowledge_gaps.json      知识盲区（方法论导师写）
├── research_context.json    研究上下文（文献研究员/方法论导师写）
├── notes/                   分领域笔记（literature/methodology/writing_drafts/review_reports）
├── episodic/                重要对话摘要
├── semantic/                已掌握概念
├── procedural/              验证有效的教学方式
└── evaluation/              教学有效性评估
```

**设计要点**：
1. **分层记忆**：用户画像/进度/决策为高频核心记忆，每次对话必加载；notes/episodic/semantic 等按需检索，节约Token。
2. **单写者原则**：核心文件指定唯一写者（decisions.json 仅主导师），并行Agent写不同子目录，避免冲突。
3. **版本管理**：关键决策变更保留旧版本而非覆盖，保证可追溯。
4. **Token管理**：记忆管家每次只加载当前阶段所需上下文，对应"Token高效"特性。
5. **隐私保护**：不记录敏感个人信息（forbidden_actions 强制）。

---

## 6. 深度思考集成

**强制触发**（见 AGENTS.md 第7节）：
- **Phase 3 研究设计**：研究设计决定整个研究成败。强制多方案比较（≥2版本研究问题）+ 7步推理脚手架（数据类型→方法列举→优缺点→可行性→选定→失败模式→应对）+ 主导师反事实思考审核。
- **Phase 5 讨论撰写**：讨论是论文最需深度的部分。强制7步推理脚手架（最重要发现→意义→新在哪→机制→局限→未来→take-home message）。

**按需触发**：用户反复理解困难、结果与预期矛盾、审稿发现重大问题、方向选择困难。

**协议依赖**：复用 `../agent_factory/thinking/deep_thinking_protocol.md` 与 `reasoning_scaffolds.md`、`verification_checklist.md`，不重复造轮子。

**设计理由**：零基础用户与AI在关键推理环节易出错或浅尝辄止，深度思考协议作为"补偿机制"强制结构化推理与自我验证，弥补单轮对话易跳步的缺陷。

---

## 7. 质量保障措施

1. **四层质量检查**：结构完整性（确定性检查）→ 科学严谨性（方法论导师）→ 写作质量（写作教练）→ Nature子刊标准（审稿模拟员）。
2. **转换检查点不可绕过**：每阶段 3-4 个可验证检查点，未通过不得推进，主导师 forbidden_actions 明确禁止绕过。
3. **审稿独立性**：审稿模拟员独立于写作教练，禁止改稿、禁止降标准、禁止跳维度。
4. **可复现性**：数据分析代码须可重跑得到相同结果（acceptance_criteria 强制）。
5. **引用核对**：文献研究员禁止虚构文献、禁止用掠夺性期刊、必须核对引用真实性。
6. **strict 模式**：全量审核、冲突裁决、完整追踪、回归评估。
7. **验收门槛**：`acceptance_criteria.json` 设5组标准，全部通过+主导师终审签字方可交付。

---

## 8. 已知限制

1. **真实投稿无法保证录用**：系统产出的是"Nature子刊水平"论文并通过模拟审稿，但真实期刊录用受编辑判断、竞争等不可控因素影响，系统不保证实际发表。
2. **依赖联网与文件处理能力**：若 AI Coding Agent 无联网能力，文献覆盖度受限（见假设A7）。
3. **数据来源依赖用户**：若无野外/实验条件且无合适公开数据集，研究可能无法推进（见假设A6）。
4. **Token成本**：20-40周长周期、深度思考强制触发会消耗较多Token，虽经记忆管家优化仍是高成本系统。
5. **教学效果依赖用户配合**：苏格拉底式教学需用户主动思考与完成任务，用户投入不足会影响质量。
6. **格式偏离 Agent Factory Schema**：为适配交互式教学场景，本系统的 agent_manifest.json 与 workflow.json 在字段上（如 responsibilities 为数组、phases_active、orchestrator、task_id 为 phase_x、deliverable_type 为 research_paper）做了语义化扩展，未严格符合 agent_factory 原始 JSON Schema 的 additionalProperties 约束，但均为合法JSON。
7. **降级边界**：降级仅限范围/规模，不可降级科学严谨性与数据准确性，但"Nature子刊标准"与"专业顶刊标准"的界限在边缘案例中需主导师人工裁量。

---

## 9. 后续优化方向

1. **Agent定义文件补全**：补齐 `agents/` 下 6 个 `{agent_name}.md` 详细教学指导文件，目前 manifest 已引用但部分待细化。
2. **记忆Schema化**：为 memory 各文件定义 JSON Schema，支持机器校验记忆完整性。
3. **进度可视化**：增加 `research_roadmap/` 可视化路线图，让用户直观看到所处阶段与剩余路径。
4. **断点续跑强化**：基于 learning_progress.json 实现更健壮的跨会话状态恢复与回退。
5. **领域扩展**：当前聚焦环境科学，后续可抽象为领域无关的研究导师框架，按方向注入领域知识包。
6. **真实审稿数据校准**：引入更多 Nature 子刊真实审稿意见案例，校准审稿模拟员的标准刻度。
7. **Token预算监控**：在记忆管家增加 Token 预算监控与预警，避免长周期成本失控。
8. **Schema对齐**：后续版本可向 agent_factory 标准 Schema 对齐（或扩展 Schema），以获得 Factory 工具链的自动校验支持。

---

## 附：产出文件清单

```
research_mentor_system/
├── AGENTS.md                       执行手册（已有）
├── README.md                       系统说明
├── agent_manifest.json             Agent清单
├── workflow.json                   DAG工作流
├── requirements/
│   ├── requirements.json           结构化需求
│   ├── assumptions.json            假设记录
│   ├── open_questions.json         待确认问题
│   └── acceptance_criteria.json    验收标准
├── tests/
│   └── system_validation.md        系统验证
├── reports/
│   └── generation_report.md        本报告
├── agents/                         6个Agent定义（待补全md）
└── memory/                         记忆系统（运行时填充）
```
