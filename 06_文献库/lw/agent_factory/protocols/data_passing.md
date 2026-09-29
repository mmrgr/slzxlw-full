# 数据传递协议

> **本文件定义了 Agent Factory 生成的多Agent系统中 Agent 间数据传递的规范。** 核心原则（P4）：Agent 间传递文件路径而非文件内容。本协议贯穿 Workflow Planner（Phase 3）、Agent Designer（Phase 4a）、Scaffold Builder（Phase 5）和 Integration Reviewer（Phase 7），是上下文最小化（P3）和断点恢复的基础。

---

## 一、核心原则：引用路径而非复制内容

### 1.1 原则声明

> **Agent 之间永远传递文件路径，绝不传递文件内容。**

所有 Agent 的输入和输出都是**路径引用**，而非内联内容。Agent 在执行时按需读取路径指向的文件，读取后也不将全文保留在上下文中传递给下游。

### 1.2 为什么引用路径

| 收益 | 说明 |
|------|------|
| 上下文最小化 | workflow.json 始终保持轻量（< 2,000 Token），而非膨胀到数万 Token |
| 断点恢复 | 文件已落盘，中断后直接从路径恢复，无需重新计算 |
| 缓存复用 | 输入哈希不变时直接复用输出文件，跳过执行 |
| 并行安全 | 多个 Agent 读取同一文件不会产生写冲突 |
| 审计追溯 | 每个中间产物都可独立检查，支持 run_report.json 的 traceability |

### 1.3 反面案例 vs 正面案例

```
反面案例（复制内容）：
  Agent A 把提取的全部事实直接写入 workflow.json

  {
    "task_id": "T2",
    "agent": "drafter",
    "input": {
      "facts": [
        {"claim": "2024年全国数字经济规模达53.9万亿元", "source": "..."},
        {"claim": "数字经济占GDP比重达41.5%", "source": "..."},
        ... // 200条事实，workflow.json 膨胀到 30,000 Token
      ]
    }
  }

  问题：workflow.json 膨胀、上下文被稀释、无法断点恢复、无法缓存


正面案例（引用路径）：
  Agent A 把事实写入独立文件，workflow.json 只引用路径

  {
    "task_id": "T2",
    "agent": "drafter",
    "inputs": ["output/T1/facts.json"],
    "outputs": ["output/T2/draft.md"]
  }

  # workflow.json 始终保持轻量（< 2,000 Token）
  # Agent B 执行时按需读取 facts.json 的内容
```

---

## 二、任务包结构

每个 Agent 执行时接收一个**任务包**（Task Package），包含完成该任务所需的全部信息。任务包遵循引用路径原则——大块数据用路径引用，只有轻量元数据内联。

### 2.1 任务包字段定义

```json
{
  "task_id": "T2",
  "objective": "基于提取的事实和提纲，撰写综述报告正文",
  "input_paths": [
    "output/T1/facts.json",
    "output/T1/outline.json"
  ],
  "output_path": "output/T2/draft.md",
  "constraints": {
    "word_count_min": 2000,
    "word_count_max": 3000,
    "language": "zh-CN",
    "must_cite_all_facts": true
  },
  "local_context": {
    "paper_count": 10,
    "topic": "数字经济高质量发展",
    "style_guide_ref": "config/style_guide.json"
  },
  "relevant_terms": [
    "数字经济", "GDP", "产业升级", "新质生产力"
  ],
  "output_schema": "schemas/draft.schema.json",
  "completion_criteria": [
    "输出文件 output/T2/draft.md 已生成",
    "输出文件通过 schemas/draft.schema.json 校验",
    "正文字数在 2000-3000 之间",
    "所有事实均被引用"
  ]
}
```

### 2.2 字段说明

| 字段 | 类型 | 说明 | 是否内联 |
|------|------|------|----------|
| `task_id` | string | 任务唯一标识 | 内联（轻量） |
| `objective` | string | 任务目标的一句话描述 | 内联（轻量） |
| `input_paths` | array | 输入文件的路径引用列表 | **路径引用**（不内联内容） |
| `output_path` | string | 输出文件的路径 | **路径引用** |
| `constraints` | object | 任务约束（字数、语言、格式等） | 内联（轻量） |
| `local_context` | object | 本地上下文（任务相关的少量元数据） | 内联（轻量） |
| `relevant_terms` | array | 相关术语列表（帮助 Agent 理解领域） | 内联（轻量） |
| `output_schema` | string | 输出 Schema 的路径引用 | **路径引用** |
| `completion_criteria` | array | 完成条件列表 | 内联（轻量） |

### 2.3 什么信息应该传入

| 信息类型 | 传入方式 | 理由 |
|----------|----------|------|
| 任务目标 | 内联（objective） | Agent 需要知道做什么 |
| 输入数据 | 路径引用（input_paths） | 数据可能很大，引用路径节省 Token |
| 输出位置 | 路径引用（output_path） | 明确写入位置，支持断点恢复 |
| 任务约束 | 内联（constraints） | 约束是轻量元数据，Agent 需要随时参照 |
| 输出格式 | 路径引用（output_schema） | Schema 可能较长，按需读取 |
| 完成条件 | 内联（completion_criteria） | Agent 需要随时检查是否完成 |
| 相关术语 | 内联（relevant_terms） | 帮助 Agent 理解领域，通常很短 |

### 2.4 什么信息不应传入

| 信息类型 | 不传入理由 |
|----------|------------|
| 其他 Agent 的完整输出内容 | 违反引用路径原则，膨胀上下文 |
| 全部 Schema 定义 | 只需传入当前 Agent 相关的 Schema 路径 |
| 全局历史记录 | 违反上下文最小化原则，稀释注意力 |
| 其他任务的任务包 | Agent 只需知道自己的任务 |
| 原始材料的完整内容 | 通过 input_paths 按需读取，不内联 |
| 记忆库的全部内容 | 只引用相关的 memory_id，不内联 |

---

## 三、引用路径 vs 复制内容 对比

### 3.1 场景对比

**场景**：Agent A 提取了 200 条事实，Agent B 需要基于这些事实撰写综述。

#### 错误方案（复制内容）

```json
// workflow.json — 膨胀到 30,000+ Token
{
  "task_id": "T2",
  "agent": "drafter",
  "input": {
    "facts": [
      {"id": "F001", "claim": "2024年全国数字经济规模达53.9万亿元", "source": "论文A"},
      {"id": "F002", "claim": "数字经济占GDP比重达41.5%", "source": "论文B"},
      {"id": "F003", "claim": "数字经济增速高于GDP增速3.2个百分点", "source": "论文C"},
      ...
      {"id": "F200", "claim": "...", "source": "论文J"}
    ],
    "outline": {
      "title": "数字经济高质量发展综述",
      "sections": [
        {"heading": "一、数字经济的规模与增长", "points": ["..."]},
        {"heading": "二、数字经济的结构特征", "points": ["..."]},
        ...
      ]
    }
  }
}
```

**问题**：
- workflow.json 膨胀到 30,000+ Token
- Agent B 的上下文被大量数据稀释，可能忽略 outline 中的关键结构要求
- 中断后无法恢复（数据在内存中，未落盘）
- 无法缓存复用（输入与配置混在一起，无法计算哈希）

#### 正确方案（引用路径）

```json
// output/T1/facts.json — 独立文件，200条事实
[
  {"id": "F001", "claim": "2024年全国数字经济规模达53.9万亿元", "source": "论文A"},
  {"id": "F002", "claim": "数字经济占GDP比重达41.5%", "source": "论文B"},
  ...
]

// output/T1/outline.json — 独立文件，提纲
{
  "title": "数字经济高质量发展综述",
  "sections": [...]
}

// workflow.json — 始终轻量（< 2,000 Token）
{
  "task_id": "T2",
  "agent": "drafter",
  "depends_on": ["T1"],
  "inputs": [
    "output/T1/facts.json",
    "output/T1/outline.json"
  ],
  "outputs": [
    "output/T2/draft.md"
  ]
}
```

**优势**：
- workflow.json 始终轻量
- Agent B 按需读取 facts.json 和 outline.json
- 中断后直接从路径恢复
- 输入哈希不变时复用输出

### 3.2 路径引用的额外收益

| 收益 | 说明 | 实现方式 |
|------|------|----------|
| 断点恢复 | 文件已落盘，中断后直接从路径恢复 | 状态文件记录每个任务的完成状态 |
| 缓存复用 | 输入哈希不变时直接复用输出文件 | cache_key 基于输入内容哈希 |
| 并行安全 | 多个 Agent 读取同一文件不产生写冲突 | 路径隔离 + 单写者原则 |
| 审计追溯 | 每个中间产物可独立检查 | run_report.json 的 traceability |
| 增量执行 | 只重新执行输入变化的任务 | 比对 cache_key |

---

## 四、分层摘要机制

当文件内容确实较大时，采用**分层摘要**策略：先传递摘要，只在需要细节时按需读取原文。分三个层级：

### 4.1 三层摘要体系

```
┌─────────────────────────────────────────────────────┐
│  领域摘要（Domain Summary）                          │
│  跨项目可复用的领域知识，存储于 memory/semantic/     │
│  例："数字经济领域常用指标与术语对照表"               │
│  体积：极小（< 500 Token）                           │
├─────────────────────────────────────────────────────┤
│  项目摘要（Project Summary）                         │
│  当前项目的全局概要，存储于 output/project_summary/  │
│  例："本项目分析10篇数字经济论文，提取核心论点"       │
│  体积：小（< 1,000 Token）                           │
├─────────────────────────────────────────────────────┤
│  运行摘要（Run Summary）                             │
│  本次运行的阶段性摘要，存储于 output/T{n}/summary    │
│  例："T1提取了200条事实，涉及5个主题"                │
│  体积：中等（< 2,000 Token）                         │
├─────────────────────────────────────────────────────┤
│  原始数据（Raw Data）                                │
│  完整的中间产物，存储于 output/T{n}/                 │
│  例：facts.json（200条事实的完整内容）               │
│  体积：大（可能 > 10,000 Token）                     │
└─────────────────────────────────────────────────────┘
```

### 4.2 分层摘要使用方式

下游 Agent 根据需要选择读取哪个层级：

```
场景：Agent C（核查Agent）需要核查 Agent B（撰写Agent）的草稿中的事实

层次1：Agent C 先读取 run_summary（"T2撰写了综述，引用了T1的200条事实"）
       → 了解全局，决定核查策略

层次2：Agent C 读取项目摘要（"本项目涉及数字经济5个主题"）
       → 理解领域背景

层次3：Agent C 按需读取 facts.json 的特定条目
       → 只读取需要核查的事实，不读取全部200条

层次4（如需要）：Agent C 读取原始论文的对应段落
       → 仅在事实核查发现疑点时
```

### 4.3 摘要生成规则

| 摘要层级 | 生成者 | 生成时机 | 存储位置 |
|----------|--------|----------|----------|
| 领域摘要 | Memory Curator（Phase 8） | 多次验证后 | `memory/semantic/` |
| 项目摘要 | Orchestrator | 项目启动时/结束时 | `output/project_summary/` |
| 运行摘要 | 各 Agent 输出时附带 | 每个 Agent 完成时 | `output/T{n}/summary.json` |

### 4.4 摘要内容规范

运行摘要（Run Summary）应包含：

```json
{
  "task_id": "T1",
  "summary": "从10篇论文中提取了200条事实",
  "key_topics": ["规模与增长", "结构特征", "区域差异", "政策影响", "国际比较"],
  "fact_count": 200,
  "source_count": 10,
  "quality_notes": "3篇论文的图表数据未能提取，已标记",
  "output_ref": "output/T1/facts.json"
}
```

下游 Agent 可以先读取 summary.json 决定是否需要读取完整的 facts.json。

---

## 五、路径引用的实现规范

### 5.1 路径格式

- 使用**相对路径**，相对于生成工程根目录
- 使用正斜杠 `/` 作为路径分隔符（跨平台兼容）
- 支持 glob 模式：`output/T1/*.json`
- 不使用绝对路径（不可移植）

### 5.2 路径命名规范

```
output/
├── T1/                         ← 任务T1的输出目录
│   ├── facts.json              ← 主输出
│   ├── summary.json            ← 运行摘要
│   └── status.json             ← 任务状态
├── T2/
│   ├── draft.md
│   ├── summary.json
│   └── status.json
├── T3/
│   └── ...
├── T4/
│   └── ...
├── final/                      ← 最终交付物
│   └── summary.docx
└── workflow_state.json         ← 全局状态（仅Orchestrator可写）
```

### 5.3 输入引用的来源标注

在 workflow.json 中，`inputs` 路径应能看出数据来源：

```
来源类型1：上游任务输出
  "inputs": ["output/T1/facts.json"]
  → 从T1的输出读取

来源类型2：原始输入文件
  "inputs": ["input/papers/*.pdf"]
  → 从原始输入读取

来源类型3：配置文件
  "inputs": ["config/style_guide.json"]
  → 从配置读取

来源类型4：记忆文件
  "inputs": ["memory/semantic/domain_knowledge.json"]
  → 从记忆层读取（只读）
```

### 5.4 数据传递完整性校验

Integration Reviewer（Phase 7）必须校验：

```
检查项：
  1. DAG 中每个任务的 inputs 路径都存在（上游已产出或原始输入存在）
  2. 上游任务的 outputs 路径与下游任务的 inputs 路径匹配
  3. 没有任务直接内联大块数据（应使用路径引用）
  4. workflow.json 文件大小 < 5,000 Token（保持轻量）
  5. 每个中间产物文件都有对应的 summary.json（分层摘要）
```

---

## 六、特殊情况处理

### 6.1 小数据可以直接内联

当数据足够小（< 200 Token）且只被使用一次时，可以直接内联在任务包中，无需独立文件：

```json
{
  "task_id": "T2",
  "constraints": {
    "word_count_min": 2000,
    "word_count_max": 3000
  }
}
```

约束条件、完成条件、术语列表等轻量元数据应内联，而非独立文件。

### 6.2 大文件必须分片引用

当单个文件非常大（> 50,000 Token）时，应分片存储并按需读取：

```
output/T1/
├── facts_part_001.json    ← 第1-50条事实
├── facts_part_002.json    ← 第51-100条事实
├── facts_part_003.json    ← 第101-150条事实
├── facts_part_004.json    ← 第151-200条事实
└── facts_index.json       ← 索引（含所有事实的摘要）
```

下游 Agent 先读取索引，再按需读取特定分片。

### 6.3 敏感数据的引用

涉及敏感数据的文件，路径引用时不暴露内容，但需标记：

```json
{
  "inputs": [
    {
      "path": "input/sensitive/user_data.json",
      "sensitive": true,
      "access_note": "包含个人隐私数据，仅限授权Agent读取，不写入记忆层"
    }
  ]
}
```

Security Auditor（Phase 6b）会检查敏感数据的引用是否合规。

---

## 七、数据传递检查清单

Workflow Planner 和 Integration Reviewer 必须确认：

- [ ] 所有 Agent 间数据传递使用路径引用，不内联大块内容
- [ ] 每个任务的 `inputs` 路径指向的文件存在或由上游任务产出
- [ ] 每个任务的 `outputs` 路径在其 `write_scope` 内
- [ ] workflow.json 保持轻量（< 5,000 Token）
- [ ] 大文件有对应的 summary.json 分层摘要
- [ ] 路径使用相对路径和正斜杠
- [ ] 敏感数据文件有 `sensitive` 标记
- [ ] 输出目录结构遵循 `output/T{n}/` 规范
