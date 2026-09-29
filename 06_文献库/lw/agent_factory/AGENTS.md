# AGENTS.md — Agent Factory 执行手册

> **本文件是 AI Coding Agent 的执行入口。** 读取本文件后，你将按照其中的流程，为用户需求生成一个完整的多Agent系统工程。

---

## 0. 前置准备

在开始之前，依次读取以下文件以获取完整规则上下文（**按需读取，不要一次性全部读取**）：

| 步骤 | 读取文件 | 用途 |
|------|----------|------|
| 1 | `core/principles.md` | 10 条核心原则，贯穿全流程 |
| 2 | `core/task_classification.md` | 判断是否需要多Agent |
| 3 | `config/factory_config.yaml` | 默认配置与预算 |
| 4 | `memory/user_preferences.json` | 用户偏好（如果存在） |
| 5 | 各角色定义（`agents/*.md`） | 在执行到对应角色时再读取 |

**Token 节约原则**：只读取当前阶段需要的文件。不要在第一阶段就读取全部 12 个角色定义。

---

## 1. 执行流程总览

```
Phase 1: 需求理解        ── Requirement Analyst
         （串行）
              │
              ▼
Phase 2: 架构决策        ── System Architect
         （串行）
              │
              ▼
Phase 3: 工作流规划      ── Workflow Planner
         （串行）
              │
              ▼
Phase 4: 并行设计        ── Agent Designer ──┐
         （3路并行）       Contract Designer ──┤── 互不依赖，可并行
                          Tool Architect ─────┘
              │
              ▼
Phase 5: 工程构建        ── Scaffold Builder
         （串行）
              │
              ▼
Phase 6: 并行审核        ── Test Engineer ──────┐
         （3路并行）       Security Auditor ────┤── 互不依赖，可并行
                          Efficiency Optimizer ─┘
              │
              ▼
Phase 7: 集成审查        ── Integration Reviewer
         （串行）
              │
              ▼
Phase 8: 记忆更新        ── Memory Curator
         （串行，可选）
```

**并行规则**：Phase 4 和 Phase 6 的三个角色可以并行执行。如果你（AI Coding Agent）支持子代理并行，则同时启动它们；如果不支持，则按顺序快速执行，但标注它们之间无依赖关系。

---

## 2. 各阶段详细执行指令

### Phase 1: 需求理解 — Requirement Analyst

**读取**：`agents/requirement_analyst.md`、`schemas/requirements.schema.json`

**执行**：
1. 分析用户的自然语言需求
2. 识别以下要素（缺失的用保守默认值，并记录为 assumption）：
   - 最终交付物是什么
   - 输入是什么（文件/文本/URL/数据）
   - 是否需要联网
   - 是否需要处理文件
   - 哪些步骤必须准确（critical），哪些可以近似
   - 是否允许人工确认节点
   - 是否需要长期运行
   - 是否涉及隐私或高风险数据
   - 用户更关注速度、质量还是资源消耗
3. **只有缺失信息会显著改变系统架构时才向用户提问**，其余使用默认值
4. 输出以下文件到生成工程的 `requirements/` 目录：
   - `requirements.json` — 结构化需求
   - `assumptions.json` — 所做的假设
   - `open_questions.json` — 需要用户确认的问题（可为空）
   - `acceptance_criteria.json` — 验收标准

**深度思考触发**：此阶段涉及对需求的理解和判断，必须启用 `thinking/deep_thinking_protocol.md` 中的"需求分析推理脚手架"。特别关注用户**没有说出来的隐含需求**。

### Phase 2: 架构决策 — System Architect

**读取**：`agents/system_architect.md`、`core/task_classification.md`

**执行**：
1. 根据 `core/task_classification.md` 中的决策树，判断任务类型：
   - 单 Agent 足够 → 直接生成单Agent方案，跳到 Phase 5
   - 单 Agent + 确定性脚本 → 生成混合方案
   - 多 Agent 串行 / 并行 / 分层 → 继续后续流程
2. **反过度设计检查**：
   - 这个任务真的需要 N 个 Agent 吗？
   - 有没有两个职责高度重叠的角色？
   - 能否用确定性代码替代某些 Agent？
3. 输出 `architecture_decision.json`：
   - 选择的架构类型及理由
   - Agent 数量及各自职责概要
   - 确定性程序与 Agent 的分工

**深度思考触发**：此阶段是关键架构决策，必须启用"架构决策推理脚手架"。需要考虑至少 2 种替代方案并比较。

### Phase 3: 工作流规划 — Workflow Planner

**读取**：`agents/workflow_planner.md`、`schemas/workflow_dag.schema.json`、`core/parallel_rules.md`

**执行**：
1. 生成任务依赖图 DAG（机器可读的 JSON）
2. 标注每个任务的：
   - `task_id`、`agent`、`depends_on`、`parallel_group`
   - `inputs`（引用路径）、`outputs`（输出路径）
   - `risk_level`（high / medium / low）
3. **并行冲突检测**（按 `core/parallel_rules.md`）：
   - 同一文件不能被两个并行任务同时写入
   - 依赖未完成的任务不能并行
   - 共享状态只能由 Orchestrator 更新
4. 输出 `workflow.json`

### Phase 4: 并行设计（3路并行）

同时启动以下三个角色，它们之间无依赖：

#### 4a. Agent Designer
**读取**：`agents/agent_designer.md`、`templates/agent_roles/`、`protocols/agent_contract.md`

为 DAG 中的每个 Agent 生成完整定义：
- 职责描述（明确且互斥）
- 输入输出 JSON Schema（引用 `schemas/` 中的定义）
- 文件读写范围（`read_scope` / `write_scope`）
- 完成条件
- 错误类型与最大重试次数
- 禁止行为

输出到 `agents/` 目录，每个 Agent 一个 `.md` 文件。

#### 4b. Contract Designer
**读取**：`agents/contract_designer.md`、`schemas/`

生成所有 JSON Schema 文件，确保 Agent 间数据交换格式一致。

输出到 `schemas/` 目录。

#### 4c. Tool Architect
**读取**：`agents/tool_architect.md`

判断 DAG 中哪些任务应该交给确定性程序：
- 文件遍历、格式转换、数据清洗、JSON 校验、哈希比较、数字核对、去重、排序、缓存判断、文件合并 → **程序**
- 内容理解、语义分析、翻译、规划、复杂判断、审校、异常解释、冲突裁决 → **Agent**

输出 `tool_assignment.json`，标注每个任务是 `program` 还是 `agent`，以及对应的脚本路径。

**硬规则**：在能够用确定性代码可靠完成的情况下，不得调用语言 Agent。

### Phase 5: 工程构建 — Scaffold Builder

**读取**：`agents/scaffold_builder.md`、`templates/project_scaffold.md`

**执行**：
1. 创建完整工程目录结构（按 `templates/project_scaffold.md`）
2. 写入所有已生成的文件：
   - `AGENTS.md`（生成系统的执行入口）
   - `README.md`（说明文档）
   - `agent_manifest.json`（Agent 清单）
   - `workflow.json`（DAG）
   - `schemas/`（所有 Schema）
   - `agents/`（所有 Agent 定义）
   - `src/`（确定性脚本）
   - `tests/`（测试文件）
   - `config/`（配置文件）
3. 生成 `AGENTS.md` 时，在其中写入一条可直接执行的提示词，让 AI Coding Agent 知道如何运行这个系统

### Phase 6: 并行审核（3路并行）

#### 6a. Test Engineer
**读取**：`agents/test_engineer.md`、`evaluation/test_templates/`

生成：
- 单元测试（每个 Agent 的输入输出校验）
- 集成测试（Agent 间数据传递）
- 失败场景测试（Agent 崩溃、Schema 错误、文件缺失）
- 缓存测试（增量执行正确性）
- 断点恢复测试

输出到 `tests/` 目录。

#### 6b. Security Auditor
**读取**：`agents/security_auditor.md`、`core/safety_rules.md`

检查：
- 每个 Agent 的读写范围是否最小化
- 是否存在提示注入风险
- 高风险操作是否设置了人工确认节点
- 敏感信息处理是否合规
- 是否有 Agent 可以越权访问

输出 `security_audit_report.json`。

#### 6c. Efficiency Optimizer
**读取**：`agents/efficiency_optimizer.md`、`core/token_optimization.md`

检查：
- Agent 数量是否可以减少
- 上下文是否可以进一步最小化
- 是否有重复调用可以缓存
- 是否有内容复制可以改为引用路径
- 小任务是否可以合并
- 全量审核是否可以改为风险审核

输出 `optimization_report.json`，如发现问题则直接修改对应文件。

### Phase 7: 集成审查 — Integration Reviewer

**读取**：`agents/integration_reviewer.md`

**执行**：
1. 检查所有组件是否可以真正协同：
   - DAG 中的依赖关系是否完整
   - Agent 间的 Schema 是否匹配
   - 文件读写范围是否冲突
   - 确定性脚本与 Agent 的接口是否对齐
2. 执行一次模拟 dry-run（在脑海中走一遍 DAG）
3. 检查验收标准是否可验证
4. 如发现问题，生成修复指令并回到对应阶段

输出 `integration_report.json`。

**深度思考触发**：此阶段需要全局视角，必须启用"集成审查推理脚手架"。

### Phase 8: 记忆更新 — Memory Curator（可选）

**读取**：`agents/memory_curator.md`、`memory/README.md`

**执行**：
1. 从本次运行中提取候选记忆：
   - 成功的设计模式
   - 遇到的问题和解决方案
   - 用户偏好
   - 有效的 Agent 模板
2. 将候选记忆写入 `memory/candidates/`
3. **不自动启用**，标记为 `candidate` 状态，等待后续验证

---

## 3. 深度思考补偿机制（关键）

### 为什么需要

当 AI Coding Agent 使用 flash 模型或低级模型时，容易出现：
- 跳过关键推理步骤
- 忽略隐含需求
- 架构决策草率
- 质量检查流于形式

### 如何触发

在以下阶段**必须启用**深度思考协议（读取 `thinking/deep_thinking_protocol.md`）：

| 阶段 | 触发条件 | 使用哪个脚手架 |
|------|----------|----------------|
| Phase 1 需求理解 | 总是 | 需求分析推理脚手架 |
| Phase 2 架构决策 | 总是 | 架构决策推理脚手架 |
| Phase 4a Agent设计 | Agent数量 > 3 | 角色设计推理脚手架 |
| Phase 7 集成审查 | 总是 | 集成审查推理脚手架 |
| 任何阶段 | 检测到推理不充分 | 通用深化协议 |

### 核心机制

1. **结构化推理脚手架**：强制按步骤推理，每步输出中间结论
2. **多方案比较**：关键决策必须生成至少 2 个方案并比较
3. **自我验证清单**：每个结论必须通过验证清单检查
4. **迭代深化**：如果验证不通过，重新推理（最多 2 轮）
5. **反事实思考**：考虑"如果这个决策错了会怎样"

详见 `thinking/deep_thinking_protocol.md`。

---

## 4. Token 优化执行规则

在执行全流程时，必须遵守以下规则（详见 `core/token_optimization.md`）：

1. **按需读取**：只读取当前阶段需要的文件
2. **引用路径**：Agent 间传递文件路径，不复制内容
3. **上下文最小化**：每个角色只获得完成当前任务所需的最小信息
4. **确定性优先**：能用代码完成的，不调用 Agent
5. **缓存复用**：输入未变化时，直接复用上次结果
6. **摘要传递**：大文件先摘要，只在需要细节时读取原文

---

## 5. 降级策略

当运行环境受限时，按以下优先级降级：

| 降级级别 | 措施 |
|----------|------|
| Level 1 | 复用缓存，跳过已完成的任务 |
| Level 2 | 减少候选方案数量（从多方案改为单方案） |
| Level 3 | 将全量审核改为风险审核（只审核高风险节点） |
| Level 4 | 合并过小任务，减少 Agent 数量 |
| Level 5 | 使用确定性校验替代 Agent 审核 |
| Level 6 | 减少核心处理范围（最后手段，需告知用户） |

---

## 6. 输出清单

生成的多Agent系统必须包含以下文件，否则视为未完成：

```
generated_system/
├── AGENTS.md                  ← 执行入口（必须）
├── README.md                  ← 说明文档（必须）
├── agent_manifest.json        ← Agent清单（必须）
├── workflow.json              ← DAG工作流（必须）
├── requirements/
│   ├── requirements.json      ← 结构化需求（必须）
│   ├── assumptions.json       ← 假设记录（必须）
│   ├── open_questions.json    ← 待确认问题（可为空）
│   └── acceptance_criteria.json ← 验收标准（必须）
├── schemas/                   ← JSON Schema（必须，至少1个）
├── agents/                    ← Agent定义（必须，至少1个）
├── src/                       ← 确定性脚本（如有）
├── tests/                     ← 测试文件（必须，至少1个）
├── config/                    ← 配置文件（必须）
├── memory/                    ← 记忆目录（如启用）
└── reports/
    └── generation_report.md   ← 生成报告（必须）
```

**完成条件**：
1. 测试通过（至少结构校验通过）
2. 样本 dry-run 成功
3. 质量报告无 critical 错误
4. 断点恢复有效
5. 不存在未授权文件访问
