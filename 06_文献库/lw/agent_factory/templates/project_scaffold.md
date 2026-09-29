# Agent Factory 项目脚手架模板

本模板定义 Agent Factory 生成的多 Agent 系统的标准目录结构。
AI Coding Agent 在生成系统时，按照此结构创建目录与文件。

---

## 一、完整系统目录结构

```
my_agent_system/
├── AGENTS.md                    # 系统入口：所有 Agent 的索引与说明
├── README.md                    # 项目说明：用途、用法、依赖
├── agent_manifest.json          # Agent 清单：所有 Agent 的元数据注册表
├── workflow.json                # 工作流定义：DAG 任务依赖图
├── requirements/
│   ├── requirements.json        # 需求规格：用户需求的结构化描述
│   └── architecture_decision.json  # 架构决策：Agent 划分与职责分配理由
├── schemas/
│   ├── input_schema.json        # 输入数据模式：系统接受的输入格式
│   ├── output_schema.json       # 输出数据模式：系统产出的输出格式
│   └── task_schema.json         # 任务模式：Agent 间传递数据的格式
├── agents/
│   ├── planner/
│   │   └── AGENTS.md            # 规划师 Agent 定义
│   ├── researcher/
│   │   └── AGENTS.md            # 研究员 Agent 定义
│   ├── writer/
│   │   └── AGENTS.md            # 写作者 Agent 定义
│   ├── reviewer/
│   │   └── AGENTS.md            # 审校员 Agent 定义
│   └── fact_checker/
│       └── AGENTS.md            # 事实核查员 Agent 定义
├── src/
│   ├── orchestrator.py          # 编排器：调度 Agent 执行 DAG
│   ├── context_manager.py       # 上下文管理器：管理 Agent 间数据传递
│   ├── memory_manager.py        # 记忆管理器：读写五层记忆
│   └── utils/
│       ├── file_io.py           # 文件读写工具
│       └── validators.py        # 数据校验工具
├── tests/
│   ├── test_planner.py          # 规划师单元测试
│   ├── test_researcher.py       # 研究员单元测试
│   ├── test_integration.py      # 集成测试
│   └── test_fixtures/           # 测试数据
│       └── sample_input.json
├── config/
│   └── system_config.yaml       # 系统级配置（覆盖 Factory 默认配置）
├── memory/
│   ├── README.md                # 记忆系统说明
│   ├── user_preferences.json    # 用户偏好记忆
│   ├── episodic/                # 情景记忆
│   ├── semantic/                # 语义记忆
│   ├── procedural/              # 程序性记忆
│   ├── evaluation/              # 评估记忆
│   └── candidates/              # 记忆候选区
├── reports/
│   └── execution_report.md      # 执行报告：运行日志与结果摘要
└── examples/
    └── sample_run.md            # 示例运行记录
```

---

## 二、目录与文件用途说明

### 顶层文件

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | 系统入口文件。列出所有 Agent 的角色、职责、输入输出，AI Coding Agent 首先读取此文件了解全局。 |
| `README.md` | 项目说明文档。面向人类用户，说明系统用途、使用方法、依赖项和注意事项。 |
| `agent_manifest.json` | Agent 清单注册表。每个 Agent 的 ID、角色、输入输出模式、依赖关系的结构化描述。 |
| `workflow.json` | 工作流 DAG 定义。描述任务节点、依赖边、并行分组、执行顺序。 |

### requirements/ — 需求与架构

| 文件 | 用途 |
|------|------|
| `requirements.json` | 用户需求的结构化描述：目标、约束、输入来源、输出格式、验收标准。 |
| `architecture_decision.json` | 架构决策记录：为何选择这些 Agent、为何这样划分职责、关键设计权衡。 |

### schemas/ — 数据模式

| 文件 | 用途 |
|------|------|
| `input_schema.json` | 系统输入的数据格式定义（JSON Schema）。 |
| `output_schema.json` | 系统输出的数据格式定义（JSON Schema）。 |
| `task_schema.json` | Agent 间任务传递数据的格式定义（JSON Schema）。 |

### agents/ — Agent 定义

每个 Agent 一个子目录，内含 `AGENTS.md` 定义文件。定义内容包括：
- 角色定位与职责
- 输入格式与来源
- 输出格式与目标
- 完成条件
- 深度思考脚手架（如适用）
- 记忆读写权限

### src/ — 源代码

| 文件 | 用途 |
|------|------|
| `orchestrator.py` | 编排器：解析 workflow.json 的 DAG，调度 Agent 执行，管理并行与依赖。 |
| `context_manager.py` | 上下文管理器：管理 Agent 间的数据传递，确保上下文最小化（引用路径而非全文传递）。 |
| `memory_manager.py` | 记忆管理器：读写五层记忆，管理候选记忆的审批流程。 |
| `utils/file_io.py` | 文件读写工具函数。 |
| `utils/validators.py` | 数据校验工具函数（JSON Schema 校验等）。 |

### tests/ — 测试

| 文件 | 用途 |
|------|------|
| `test_*.py` | 每个 Agent 的单元测试，验证输入输出是否符合预期。 |
| `test_integration.py` | 集成测试，验证 Agent 间数据传递是否正确。 |
| `test_fixtures/` | 测试用例数据。 |

### config/ — 系统配置

| 文件 | 用途 |
|------|------|
| `system_config.yaml` | 系统级配置，可覆盖 Agent Factory 的默认配置（factory_config.yaml）。 |

### memory/ — 记忆系统

| 目录/文件 | 用途 |
|-----------|------|
| `README.md` | 记忆系统使用说明。 |
| `user_preferences.json` | 用户偏好记忆（第一层）。 |
| `episodic/` | 情景记忆（第二层）：具体任务执行记录。 |
| `semantic/` | 语义记忆（第三层）：概念、事实、关系知识。 |
| `procedural/` | 程序性记忆（第四层）：操作流程、最佳实践。 |
| `evaluation/` | 评估记忆（第五层）：质量评估与反馈。 |
| `candidates/` | 记忆候选区：新产生的记忆先存放于此，经审批后迁移到正式记忆层。 |

### reports/ — 执行报告

| 文件 | 用途 |
|------|------|
| `execution_report.md` | 每次系统运行的执行报告：各 Agent 执行状态、耗时、Token 消耗、错误日志、最终结果摘要。 |

### examples/ — 示例

| 文件 | 用途 |
|------|------|
| `sample_run.md` | 示例运行记录，展示一次完整的输入到输出过程。 |

---

## 三、最小可行系统（MVS）

当资源受限或任务简单时，仅生成以下必须文件：

```
my_agent_system/
├── AGENTS.md                    # 必须：Agent 索引
├── workflow.json                # 必须：工作流 DAG
├── agents/
│   ├── planner/
│   │   └── AGENTS.md            # 必须：规划师
│   ├── writer/
│   │   └── AGENTS.md            # 必须：写作者
│   └── reviewer/
│       └── AGENTS.md            # 必须：审校员
├── src/
│   └── orchestrator.py          # 必须：编排器
├── memory/
│   └── candidates/              # 必须：记忆候选区（即使为空也需存在）
└── reports/
    └── execution_report.md      # 必须：执行报告
```

**最小可行系统的约束：**
- 最多 3 个 Agent（planner → writer → reviewer）
- 无并行（串行执行）
- 无深度思考迭代
- 无 fact_checker 与 researcher
- 记忆系统仅保留候选区

**适用场景：** 原型验证、简单文档转换、快速草稿生成。

---

## 四、完整系统

当任务复杂、质量要求高时，生成完整目录结构（见第一节）。

**完整系统的增强：**
- 5+ 个 Agent（planner + researcher + writer + reviewer + fact_checker，可扩展）
- 基于 DAG 的并行执行
- 深度思考脚手架与自我验证
- 完整五层记忆系统
- 单元测试与集成测试
- 数据模式校验（JSON Schema）
- 架构决策记录
- 降级策略支持

**适用场景：** 学术翻译、多源研究报告、正式交付文档、大规模批处理。

---

## 五、从 MVS 到完整系统的扩展路径

```
MVS（3 Agent）
  ↓ 增加 researcher
MVS+（4 Agent）
  ↓ 增加 fact_checker
MVS++（5 Agent）
  ↓ 增加并行、深度思考、完整记忆
完整系统（5+ Agent，全功能）
  ↓ 增加自定义 Agent
扩展系统（6-12 Agent）
```

每一级扩展都保持向后兼容：新增 Agent 不破坏已有 Agent 的定义与接口。

---

## 六、文件命名规范

- Agent 定义文件统一命名为 `AGENTS.md`（放在各自子目录下）
- 配置文件使用 `.yaml` 扩展名
- 数据模式使用 `.json` 扩展名
- 源代码使用 `.py` 扩展名
- 测试文件以 `test_` 为前缀
- 文档文件使用 `.md` 扩展名
- 目录名使用小写蛇形命名（snake_case）
