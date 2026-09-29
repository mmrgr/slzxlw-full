# Agent Factory — 声明式多Agent体系生成器

> **核心定位**：用户描述需求 → 系统自动分析、设计、生成一套完整的多Agent协作工程 → 生成的工程可被任意 AI Coding Agent（TRAE / Cursor / Claude Code / Codex 等）直接读取并执行。无需本地部署 LLM，无需调用大模型 API。

---

## 一、它是什么

Agent Factory **不是一个需要独立运行的程序**，而是一套**声明式指令文件 + 结构化协议 + 记忆体系**。

AI Coding Agent 读取本目录下的 `AGENTS.md` 后，会理解整个体系的工作方式，并按照其中的指令"扮演"各个 Agent 角色，完成从"需求理解"到"生成可执行多Agent工程"的全流程。

```
用户需求（自然语言）
    │
    ▼
AI Coding Agent 读取 AGENTS.md
    │
    ▼
按指令依次/并行扮演 Agent Factory 的 12 个角色
    │
    ▼
输出一个完整的多Agent系统工程目录
    │
    ▼
该工程同样是一组指令文件，可被 AI Coding Agent 直接读取执行
```

## 二、核心特性

| 特性 | 实现方式 | 对应目录 |
|------|----------|----------|
| **无需部署 LLM** | 全部为声明式指令文件，AI Coding Agent 自身作为执行引擎 | 全局 |
| **最大化并行** | 基于 DAG 任务依赖图调度，自动识别可并行节点 | `core/parallel_rules.md` `schemas/workflow_dag.schema.json` |
| **最小化 Token** | 上下文最小化 + 引用路径而非复制内容 + 确定性程序优先 + 缓存增量 | `core/token_optimization.md` `protocols/data_passing.md` |
| **记忆进化** | 五层记忆体系 + 受控进化流程 + A/B 测试 + 回滚 | `memory/` `agents/memory_curator.md` |
| **深度思考补偿** | 结构化推理脚手架 + 慢思考触发 + 自我验证 + 迭代深化 | `thinking/` |

## 三、目录结构

```
agent_factory/
├── README.md                    ← 你正在看的文件（总入口）
├── AGENTS.md                    ← AI Coding Agent 的执行手册
├── config/                      ← 配置文件
│   ├── factory_config.yaml      ← Agent Factory 默认配置
│   └── budget_template.yaml     ← Token / Agent 预算模板
├── core/                        ← 核心原则与规则
│   ├── principles.md            ← 10 条核心原则（含反过度设计）
│   ├── task_classification.md   ← 何时需要多Agent的分类决策树
│   ├── parallel_rules.md        ← 并行调度规则与冲突检测
│   ├── token_optimization.md    ← Token 优化的 6 种策略
│   ├── quality_assurance.md     ← 四层质量检查体系
│   └── safety_rules.md          ← 安全与权限规则
├── agents/                      ← Agent Factory 自身的 12 个角色定义
│   ├── requirement_analyst.md
│   ├── system_architect.md
│   ├── workflow_planner.md
│   ├── agent_designer.md
│   ├── contract_designer.md
│   ├── tool_architect.md
│   ├── security_auditor.md
│   ├── test_engineer.md
│   ├── efficiency_optimizer.md
│   ├── memory_curator.md
│   ├── integration_reviewer.md
│   └── scaffold_builder.md
├── templates/                   ← 可复用模板库
│   ├── agent_roles/             ← 生成系统可用的角色模板
│   ├── workflows/               ← 工作流模板（文档处理/研究/开发/翻译等）
│   └── project_scaffold.md      ← 生成系统的标准目录结构
├── schemas/                     ← JSON Schema 协议定义
│   ├── requirements.schema.json
│   ├── agent_manifest.schema.json
│   ├── workflow_dag.schema.json
│   ├── memory_entry.schema.json
│   └── run_report.schema.json
├── memory/                      ← 五层记忆体系
│   ├── README.md                ← 记忆系统使用说明
│   ├── user_preferences.json    ← 用户偏好记忆
│   ├── episodic/                ← 情景记忆（具体任务记录）
│   ├── semantic/                ← 语义记忆（可复用知识）
│   ├── procedural/              ← 程序性记忆（已验证的执行方式）
│   ├── evaluation/              ← 评估记忆（方案效果对比）
│   └── candidates/              ← 记忆候选区（待审批）
├── protocols/                   ← 协议定义
│   ├── agent_contract.md        ← Agent 契约协议
│   ├── data_passing.md          ← 数据传递协议（引用路径）
│   ├── conflict_resolution.md   ← 冲突解决协议
│   └── error_handling.md        ← 错误处理与重试协议
├── thinking/                    ← 深度思考补偿机制
│   ├── deep_thinking_protocol.md ← 深度思考协议（核心）
│   ├── reasoning_scaffolds.md   ← 推理脚手架模板
│   └── verification_checklist.md ← 自我验证清单
├── evaluation/                  ← 评估框架
│   ├── acceptance_criteria.md   ← 验收标准框架
│   └── test_templates/          ← 测试模板
└── examples/                    ← 示例
    └── example_usage.md         ← 完整使用示例
```

## 四、如何使用

### 对 AI Coding Agent 说

```
请阅读 agent_factory/AGENTS.md，然后按照其中的流程，
为以下需求生成一个多Agent系统：

[在此描述你的需求]
```

AI Coding Agent 读取 `AGENTS.md` 后会自动执行全流程。

### 三种运行模式

| 模式 | 适用场景 | 特点 |
|------|----------|------|
| **快速模式** | 低风险、简单任务 | 少量Agent、最少审核、优先速度 |
| **标准模式** | 日常任务 | 合理并发、全部结构校验、一次语义审核 |
| **严格模式** | 高风险、正式交付 | 全量审核、冲突裁决、完整追踪、回归评估 |

用户可在需求中指定模式，或在 `config/factory_config.yaml` 中设置默认值。

## 五、设计哲学

> **最关键的补充不是"创建更多 Agent"，而是让系统具备四种能力：**
> 1. 知道何时**不需要** Agent
> 2. 知道如何**证明结果正确**
> 3. 知道如何从**失败中学习**
> 4. 知道如何**安全地改进自己**

这四句话是整个 Agent Factory 的设计基石。所有机制都服务于这四个目标。
