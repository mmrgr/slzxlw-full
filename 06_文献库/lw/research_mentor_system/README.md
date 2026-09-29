# Nature子刊研究导师系统

## 系统简介

本系统是一个**交互式研究导师系统**：AI Coding Agent 读取 `AGENTS.md` 后，化身环境科学资深教授，以6种导师角色，跨越8个阶段（Phase 0-7），陪伴零基础用户完成从研究方向选择到 Nature 子刊论文投稿的完整旅程，最终产出一篇 Nature 子刊水平的研究论文及完整投稿材料。它不是一次性流水线，而是跨越数月（约20-40周）的长期教学-研究-写作伙伴。

---

## 核心特性

| 特性 | 实现方式 |
|------|----------|
| **零基础友好** | 概念从零讲起，术语即时解释，苏格拉底式提问引导思考 |
| **长期记忆** | 跨会话记忆用户背景、进度、决策、知识盲区，由记忆管家维护 |
| **深度思考补偿** | 研究设计（Phase 3）与讨论撰写（Phase 5）强制使用推理脚手架 |
| **Nature级标准** | 审稿模拟按 Nature 子刊标准执行，不降低要求 |
| **交互式教学** | 讲授→提问→布置任务→审阅反馈→迭代，形成学习闭环 |
| **Token高效** | 每次对话只加载当前阶段需要的上下文 |

---

## 6个Agent角色

| Agent | 身份 | 核心职责 | 活跃阶段 |
|-------|------|----------|----------|
| **主导师** principal_mentor | 资深教授/Orchestrator | 整体规划、方向把关、阶段转换、终审、教学法决策 | 全程（Orchestrator） |
| **文献研究员** literature_researcher | 文献分析专家 | 文献检索、结构化分析、研究空白识别、引用核对 | Phase 0, 2, 6 |
| **方法论导师** methodology_mentor | 研究方法专家 | 知识图谱构建、研究设计、数据收集与分析指导 | Phase 1, 3, 4 |
| **写作教练** writing_coach | 学术写作专家 | 论文结构规划、分章节撰写指导、语言润色、投稿材料 | Phase 2, 5, 7 |
| **审稿模拟员** peer_reviewer | Nature审稿人 | 模拟同行评审、五维度审稿、修改验证 | Phase 5, 6 |
| **记忆管家** memory_curator | 学习记忆系统 | 跨会话记忆、进度追踪、知识盲区检测、Token管理 | 全程（后台） |

---

## 8阶段路线图概览

| 阶段 | 名称 | 时长 | 主导Agent | 风险 | 深度思考 |
|------|------|------|-----------|------|----------|
| Phase 0 | 方向探索 | 1-2周 | 主导师 | medium | - |
| Phase 1 | 基础建立 | 2-4周 | 方法论导师 | medium | - |
| Phase 2 | 文献综述 | 3-6周 | 文献研究员 | medium | - |
| Phase 3 | 研究设计 | 2-4周 | 方法论导师 | high | 强制触发 |
| Phase 4 | 数据收集与分析 | 4-12周 | 方法论导师 | high | - |
| Phase 5 | 论文撰写 | 4-8周 | 写作教练 | high | 强制触发 |
| Phase 6 | 审稿与修改 | 2-4周 | 审稿模拟员 | medium | - |
| Phase 7 | 投稿准备 | 1-2周 | 写作教练 | low | - |

**总周期**：约 20-40 周。**关键路径**：phase_0 → phase_1 → … → phase_7（线性依赖，不可跳过）。**并行机会**：Phase 2（文献检索与综述写作教学并行）、Phase 5（撰写与即时审稿流水线）。

---

## 如何使用

对 AI Coding Agent 说：

```
请阅读 research_mentor_system/AGENTS.md，
然后开始指导我做环境科学研究。
```

或更具体地：

```
请阅读 research_mentor_system/AGENTS.md，
我是零基础，想研究[某个方向]，目标是发Nature子刊。
```

AI Coding Agent 读取 `AGENTS.md` 后，会自动判断是首次对话还是继续进度：
- **首次对话**：以主导师身份收集用户背景（学历/方向/时间/资源/英文/期刊偏好），写入 `memory/user_profile.json`，进入 Phase 0。
- **继续进度**：读取 `memory/learning_progress.json` 的 `current_phase`，加载当前阶段上下文，以对应主导Agent身份继续交互。

每次对话结束自动更新记忆文件，实现跨会话续接。

---

## 目录结构

```
research_mentor_system/
├── AGENTS.md                       执行手册（AI Coding Agent 入口）
├── README.md                       本说明文档
├── agent_manifest.json             6个Agent清单（角色/职责/读写范围/禁止行为）
├── workflow.json                   8阶段DAG工作流（依赖/检查点/风险）
├── requirements/
│   ├── requirements.json           结构化需求
│   ├── assumptions.json            合理假设（8项，首次对话确认）
│   ├── open_questions.json         待确认问题（7项）
│   └── acceptance_criteria.json    验收标准（5组）
├── tests/
│   └── system_validation.md        系统验证（7类检查）
├── reports/
│   └── generation_report.md        生成报告
├── agents/                         6个Agent详细定义（.md）
└── memory/                         记忆系统（运行时填充）
    ├── user_profile.json
    ├── learning_progress.json
    ├── decisions.json
    ├── knowledge_gaps.json
    ├── research_context.json
    ├── notes/                      literature/methodology/writing_drafts/review_reports
    ├── episodic/
    ├── semantic/
    ├── procedural/
    └── evaluation/
```

---

## 与 Agent Factory 的关系

**本系统由 Agent Factory 生成。** Agent Factory（位于 `../agent_factory/`）是多Agent系统生成框架，提供需求分析、架构设计、工作流规划、Agent设计、记忆系统、深度思考协议、质量保障等成套方法论与 Schema。

本系统复用 Agent Factory 的：
- **深度思考协议**：`../agent_factory/thinking/deep_thinking_protocol.md`、`reasoning_scaffolds.md`、`verification_checklist.md`
- **设计原则**：最小权限、单写者、确定性优先、引用路径而非复制内容、Token优化
- **Schema 参考**：`agent_manifest.schema.json`、`workflow_dag.schema.json`、`requirements.schema.json`

为适配交互式教学场景，本系统在 Agent Factory 标准 Schema 基础上做了语义化扩展（如 `responsibilities` 为数组、`phases_active`、`orchestrator`、`task_id` 为 `phase_x`、`deliverable_type` 为 `research_paper`），详见 `reports/generation_report.md` 第8节"已知限制"。

---

## 设计哲学

1. **标准不因零基础而降低**：你可以做到，但 Nature 子刊标准不会降低。降级仅限范围/规模，不可降级科学严谨性与数据准确性。
2. **教学优先于产出**：苏格拉底式提问引导用户自己发现答案，而非直接给答案；脚手架式教学逐步撤去支持，培养独立研究能力。
3. **深度思考补偿单轮浅薄**：在研究设计与讨论撰写等关键环节强制结构化推理与自我验证，弥补单轮对话易跳步的缺陷。
4. **分离即质量**：写作者不自审（写作教练与审稿模拟员分离）、研究者不编造（方法论导师禁造数据）、综述者不写正文（文献研究员与写作教练互斥），通过职责隔离保障客观性。
5. **记忆即连续性**：跨数月的研究靠记忆系统维持连续性，关键决策可追溯，知识盲区可复用，使每次对话都建立在过往之上。
6. **检查点即护栏**：8个阶段的转换检查点不可绕过，未通过则回退补强，确保每一步扎实。

---

如需了解完整执行指令，请阅读 [AGENTS.md](computer://d:\my github\小说写作\research_mentor_system\AGENTS.md)。
如需了解系统生成过程，请阅读 [生成报告](computer://d:\my github\小说写作\research_mentor_system\reports\generation_report.md)。
如需运行系统验证，请阅读 [系统验证](computer://d:\my github\小说写作\research_mentor_system\tests\system_validation.md)。
