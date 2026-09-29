# Agent Factory 完整使用示例

> 本文档以一个具体需求为例，展示从用户输入到生成完整多 Agent 系统的全过程。

---

## 需求场景

**用户需求：** 将20篇英文学术论文PDF批量翻译为中文Word文档。

**要求：**
- 源格式：PDF（英文学术论文）
- 目标格式：DOCX（中文Word文档）
- 术语翻译一致率 >= 95%
- 全文翻译，无遗漏段落
- 引用编号完整保留

---

## 阶段一：用户输入

用户向 Agent Factory 提交需求：

```
请帮我将 input/ 目录下的20篇英文学术论文PDF批量翻译为中文Word文档。
要求：
1. 术语翻译全文一致
2. 不遗漏任何段落
3. 保留引用编号和图表引用
4. 输出为 .docx 格式
```

Agent Factory 解析用户输入，生成结构化需求文件。

---

## 阶段二：需求解析（requirements.json）

Agent Factory 将用户需求解析为 `requirements/requirements.json`：

```json
{
  "requirement_id": "REQ-2026-001",
  "goal": "将20篇英文学术论文PDF批量翻译为中文Word文档",
  "constraints": {
    "source_format": "PDF",
    "target_format": "DOCX",
    "source_language": "English",
    "target_language": "Chinese",
    "batch_size": 20,
    "input_directory": "input/",
    "output_directory": "output/"
  },
  "acceptance_criteria": {
    "metrics": [
      {
        "name": "terminology_consistency_rate",
        "target_threshold": 0.95,
        "minimum_threshold": 0.90,
        "fail_below_minimum": true
      },
      {
        "name": "paragraph_completeness_rate",
        "target_threshold": 1.00,
        "minimum_threshold": 0.98,
        "fail_below_minimum": true
      },
      {
        "name": "citation_preservation_rate",
        "target_threshold": 1.00,
        "minimum_threshold": 1.00,
        "fail_below_minimum": true
      }
    ],
    "partial_result_allowed": true,
    "partial_result_conditions": [
      "批量处理中部分文档失败时，成功文档可交付"
    ]
  },
  "mode": "standard",
  "created_at": "2026-07-27T09:00:00Z"
}
```

---

## 阶段三：架构决策（architecture_decision.json）

Agent Factory 的规划师分析需求，做出架构决策，写入 `requirements/architecture_decision.json`：

```json
{
  "decision_id": "ARCH-2026-001",
  "workflow_type": "translation",
  "rationale": {
    "why_translation_workflow": "任务是英中翻译，适用翻译型工作流模板",
    "why_batch": "20篇论文需批量处理，每篇独立翻译但共享术语表",
    "chunking_strategy": "每篇论文按800-1000词分块，并行翻译",
    "agent_selection": {
      "planner": "规划分块方案与调度策略",
      "researcher": "统一提取20篇论文的术语，建立全局术语表",
      "writer": "并行翻译各篇各分块",
      "reviewer": "全文一致性检查与语言审校",
      "fact_checker": "核对数字、引用、人名翻译准确性"
    }
  },
  "agent_count": 7,
  "parallel_strategy": {
    "terminology_extraction": "串行（全局术语表需一次性提取）",
    "translation": "并行（每篇独立，篇内分块并行）",
    "review": "每篇独立审核，可并行"
  },
  "resource_estimate": {
    "total_tasks": 85,
    "estimated_tokens": 280000,
    "estimated_time": "约45分钟"
  },
  "degradation_plan": "如Token不足，优先保证术语提取和翻译，跳过fact_checker",
  "key_risks": [
    "PDF解析可能失败（学术PDF格式复杂）",
    "术语冲突需人工裁定",
    "分块拼接处可能不连贯"
  ]
}
```

---

## 阶段四：工作流定义（workflow.json）

基于翻译型工作流模板，生成 `workflow.json`。由于20篇论文需批量处理，采用"全局术语提取 + 逐篇并行翻译"策略：

```json
{
  "workflow_id": "batch_translation_001",
  "workflow_type": "translation",
  "mode": "standard",
  "description": "20篇英文学术论文PDF批量翻译为中文DOCX",

  "tasks": [
    {
      "id": "T0",
      "name": "批量翻译规划",
      "agent": "planner",
      "depends_on": [],
      "parallel_group": 0,
      "context_estimate": 5000,
      "risk": "low",
      "max_retries": 1
    },
    {
      "id": "T1",
      "name": "全局术语提取（20篇论文）",
      "agent": "researcher",
      "depends_on": ["T0"],
      "parallel_group": 1,
      "context_estimate": 30000,
      "risk": "medium",
      "max_retries": 2,
      "output_target": "research_output/terminology.json",
      "note": "统一提取20篇论文的术语，建立全局术语表"
    },
    {
      "id": "T2-P01",
      "name": "翻译-论文01",
      "agent": "writer",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 25000,
      "risk": "medium",
      "max_retries": 2,
      "sub_tasks": "论文01分4块并行翻译后拼接"
    },
    {
      "id": "T2-P02",
      "name": "翻译-论文02",
      "agent": "writer",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 25000,
      "risk": "medium",
      "max_retries": 2
    },
    {
      "id": "T2-P03",
      "name": "翻译-论文03",
      "agent": "writer",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 25000,
      "risk": "medium",
      "max_retries": 2
    },
    {
      "id": "...",
      "name": "翻译-论文04至论文19（结构同上）",
      "agent": "writer",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "note": "每篇论文一个翻译任务，受max_parallel限制分批执行"
    },
    {
      "id": "T2-P20",
      "name": "翻译-论文20",
      "agent": "writer",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 25000,
      "risk": "medium",
      "max_retries": 2
    },
    {
      "id": "T3-P01",
      "name": "一致性检查-论文01",
      "agent": "reviewer",
      "depends_on": ["T2-P01"],
      "parallel_group": 3,
      "context_estimate": 15000,
      "risk": "low",
      "max_retries": 1,
      "review_type": "terminology_consistency"
    },
    {
      "id": "...",
      "name": "一致性检查-论文02至论文20（结构同上）",
      "agent": "reviewer",
      "depends_on": ["T2-Pxx"],
      "parallel_group": 3,
      "note": "每篇论文独立审核，可并行"
    },
    {
      "id": "T4-P01",
      "name": "事实核查-论文01",
      "agent": "fact_checker",
      "depends_on": ["T3-P01"],
      "parallel_group": 4,
      "context_estimate": 12000,
      "risk": "medium",
      "max_retries": 1
    },
    {
      "id": "...",
      "name": "事实核查-论文02至论文20（结构同上）",
      "agent": "fact_checker",
      "depends_on": ["T3-Pxx"],
      "parallel_group": 4
    },
    {
      "id": "T5-P01",
      "name": "格式输出-论文01（DOCX）",
      "agent": "orchestrator",
      "depends_on": ["T4-P01"],
      "parallel_group": 5,
      "context_estimate": 3000,
      "risk": "low",
      "max_retries": 0,
      "condition": "T3-P01.verdict in ['pass','partial'] && T4-P01.verdict != 'fail'",
      "output_target": "output/paper_01_zh.docx"
    },
    {
      "id": "...",
      "name": "格式输出-论文02至论文20（结构同上）",
      "agent": "orchestrator",
      "depends_on": ["T4-Pxx"],
      "parallel_group": 5
    },
    {
      "id": "T6",
      "name": "批量交付汇总",
      "agent": "orchestrator",
      "depends_on": ["T5-P01", "T5-P02", "...", "T5-P20"],
      "parallel_group": 6,
      "context_estimate": 5000,
      "risk": "low",
      "max_retries": 0,
      "output_target": "reports/execution_report.md"
    }
  ],

  "parallel_groups": {
    "2": {
      "tasks": ["T2-P01", "T2-P02", "...", "T2-P20"],
      "max_concurrency": 5,
      "note": "同时最多翻译5篇论文"
    },
    "3": {
      "tasks": ["T3-P01", "...", "T3-P20"],
      "max_concurrency": 5
    },
    "4": {
      "tasks": ["T4-P01", "...", "T4-P20"],
      "max_concurrency": 5
    },
    "5": {
      "tasks": ["T5-P01", "...", "T5-P20"],
      "max_concurrency": 5
    }
  },

  "retry_edges": [
    {
      "from": "T3-Pxx",
      "to": "T2-Pxx",
      "condition": "T3-Pxx.verdict == 'retry'",
      "max_retries": 2,
      "retry_scope": "affected_chunks_only",
      "note": "仅重试有问题的分块，不全部重翻"
    }
  ]
}
```

---

## 阶段五：Agent 清单（agent_manifest.json）

```json
{
  "manifest_id": "MANIFEST-2026-001",
  "agents": [
    {
      "id": "planner",
      "role": "规划师",
      "definition": "agents/planner/AGENTS.md",
      "input_schema": "schemas/input_schema.json",
      "output_schema": "schemas/workflow_schema.json",
      "memory_access": {
        "read": ["user_preferences", "episodic", "semantic", "procedural", "evaluation"],
        "write": ["candidates"]
      }
    },
    {
      "id": "researcher",
      "role": "研究员",
      "definition": "agents/researcher/AGENTS.md",
      "input_schema": "schemas/task_schema.json",
      "output_schema": "schemas/research_output_schema.json",
      "memory_access": {
        "read": ["user_preferences", "episodic", "semantic", "procedural", "evaluation"],
        "write": ["candidates"]
      },
      "instances": 1,
      "note": "全局术语提取仅需1个实例"
    },
    {
      "id": "writer",
      "role": "写作者",
      "definition": "agents/writer/AGENTS.md",
      "input_schema": "schemas/task_schema.json",
      "output_schema": "schemas/translation_output_schema.json",
      "memory_access": {
        "read": ["user_preferences", "episodic", "semantic", "procedural", "evaluation"],
        "write": ["candidates"]
      },
      "instances": 5,
      "note": "最多5个并行实例，每实例处理1篇论文"
    },
    {
      "id": "reviewer",
      "role": "审校员",
      "definition": "agents/reviewer/AGENTS.md",
      "input_schema": "schemas/task_schema.json",
      "output_schema": "schemas/review_output_schema.json",
      "memory_access": {
        "read": ["user_preferences", "episodic", "semantic", "procedural", "evaluation"],
        "write": ["candidates"]
      },
      "instances": 5
    },
    {
      "id": "fact_checker",
      "role": "事实核查员",
      "definition": "agents/fact_checker/AGENTS.md",
      "input_schema": "schemas/task_schema.json",
      "output_schema": "schemas/factcheck_output_schema.json",
      "memory_access": {
        "read": ["user_preferences", "episodic", "semantic", "procedural", "evaluation"],
        "write": ["candidates"]
      },
      "instances": 5
    },
    {
      "id": "orchestrator",
      "role": "编排器",
      "definition": "src/orchestrator.py",
      "note": "仅负责调度与汇总，不执行具体子任务",
      "memory_access": {
        "read": [],
        "write": []
      }
    }
  ]
}
```

---

## 阶段六：Agent 定义片段

以写作者 Agent 为例（`agents/writer/AGENTS.md` 核心片段）：

```markdown
# 写作者 Agent — 论文翻译

## 角色定位
将英文学术论文分块翻译为中文，严格使用全局术语表。

## 当前任务
- 输入：英文论文分块文本（800-1000词/块）+ 全局术语表 + 前2-3句衔接上下文
- 输出：中文翻译（Markdown格式，后续转换为DOCX）

## 翻译规范
1. 术语表中的术语必须使用指定翻译，不得自行变更
2. 引用编号 [1], [2] 等原样保留
3. 图表引用 "Figure 1", "Table 2" 译为"图1"、"表2"
4. 被动语态尽量转为主动语态
5. 长句可适当拆分以符合中文表达习惯
6. 学术风格，用词正式

## 分块处理
- 本篇论文分4块，每块约900词
- 每块翻译时携带前块最后2-3句作为衔接上下文
- 4块全部完成后拼接为完整译文

## 完成条件
- 所有段落已翻译（无遗漏）
- 术语使用与术语表一致
- 引用编号完整保留
- 自检报告 overall_status = pass
```

---

## 阶段七：执行过程

编排器读取 `workflow.json`，按 DAG 调度执行：

```
[09:00] T0 规划开始
[09:02] T0 完成 → 生成85个任务的DAG
[09:02] T1 术语提取开始（串行，1个researcher实例）
[09:15] T1 完成 → 术语表含342个术语，7个冲突术语标注pending
[09:15] T2-P01~P05 开始并行翻译（第一批5篇）
[09:25] T2-P06~P10 开始并行翻译（第二批5篇）
[09:25] T3-P01~P05 开始并行审核（第一批）
[09:35] T2-P11~P15 开始并行翻译（第三批5篇）
...
[09:45] T2-P07 翻译完成，T3-P07 审核发现2个critical（术语不一致）
[09:46] T2-P07 触发重试，仅重译有问题的分块
[09:50] T2-P07 重试完成，T3-P07 重新审核 → pass
...
[09:55] T2-P15 PDF解析失败 → 标记为failed，继续处理其他论文
...
[10:30] 所有翻译+审核+事实核查完成
[10:32] T5-P01~P20 并行输出DOCX格式
[10:35] T6 批量交付汇总
[10:36] 执行完成
```

---

## 阶段八：执行报告（execution_report.md 片段）

```markdown
# 批量翻译执行报告

## 概要
- 任务ID: batch_translation_001
- 执行时间: 2026-07-27 09:00 - 10:36（约96分钟）
- 模式: standard
- 总论文数: 20
- 成功: 18
- 失败: 2
- 最终判定: PARTIAL

## 失败文档
| 文件 | 失败阶段 | 失败原因 |
|------|----------|----------|
| paper_07.pdf | T2-P07（翻译） | PDF解析失败，无法提取文本 |
| paper_15.pdf | T2-P15（翻译） | PDF加密，无法读取 |

## 成功文档质量指标
| 指标 | 目标值 | 实际值 | 状态 |
|------|--------|--------|------|
| 术语一致性率 | >= 95% | 96.3% | pass |
| 段落完整率 | = 100% | 100% | pass |
| 引用保留率 | = 100% | 100% | pass |
| 数据准确率 | = 100% | 99.8% | pass |
| 事实核查覆盖率 | >= 95% | 94.2% | warning |

## 重试记录
- T2-P07: 1次重试（术语不一致 → 修正后通过）
- T3-P12: 1次重试（段落遗漏 → 补充后通过）

## 术语冲突
7个术语存在多种译法，已标注[术语待定]：
1. attention mechanism → 注意力机制 / 注意机制
2. fine-tuning → 微调 / 精调
3. ...（详见 research_output/terminology.json 的 conflict_terms）

## Token消耗
- 预估: 280,000
- 实际: 265,000（低于预估5.4%）

## 降级记录
无降级触发。

## 候选记忆
本次执行产生以下候选记忆（已写入 candidates/）：
1. MEM-EPISODIC-2026-001: 批量翻译执行记录
2. MEM-PROCEDURAL-2026-001: 术语先行策略有效（程序性记忆）
3. MEM-EVALUATION-2026-001: PDF解析是主要失败原因（评估记忆）
```

---

## 阶段九：最终生成的工程目录结构

```
batch_translation_system/
├── AGENTS.md                        # 系统入口
├── README.md                        # 项目说明
├── agent_manifest.json              # Agent清单
├── workflow.json                    # 工作流DAG（85个任务）
├── requirements/
│   ├── requirements.json            # 需求规格
│   └── architecture_decision.json   # 架构决策
├── schemas/
│   ├── input_schema.json
│   ├── output_schema.json
│   └── task_schema.json
├── agents/
│   ├── planner/
│   │   └── AGENTS.md
│   ├── researcher/
│   │   └── AGENTS.md
│   ├── writer/
│   │   └── AGENTS.md
│   ├── reviewer/
│   │   └── AGENTS.md
│   └── fact_checker/
│       └── AGENTS.md
├── src/
│   ├── orchestrator.py
│   ├── context_manager.py
│   ├── memory_manager.py
│   └── utils/
│       ├── file_io.py
│       └── validators.py
├── tests/
│   ├── test_planner.py
│   ├── test_writer.py
│   ├── test_integration.py
│   └── test_fixtures/
├── config/
│   └── system_config.yaml
├── memory/
│   ├── README.md
│   ├── user_preferences.json
│   ├── episodic/
│   ├── semantic/
│   ├── procedural/
│   ├── evaluation/
│   └── candidates/
│       ├── MEM-EPISODIC-2026-001.json
│       ├── MEM-PROCEDURAL-2026-001.json
│       └── MEM-EVALUATION-2026-001.json
├── research_output/
│   ├── terminology.json             # 全局术语表（342个术语）
│   └── sources.json                 # 来源索引
├── output/
│   ├── paper_01_zh.docx
│   ├── paper_02_zh.docx
│   ├── ...
│   ├── paper_18_zh.docx
│   ├── paper_19_zh.docx
│   └── paper_20_zh.docx
├── reports/
│   ├── execution_report.md
│   ├── review_T3-P01.json
│   ├── ...
│   └── factcheck_T4-P01.json
└── examples/
    └── sample_run.md
```

---

## 阶段十：用户如何使用生成的系统

### 步骤 1：准备输入

将20篇英文论文PDF放入 `input/` 目录：

```
input/
├── paper_01.pdf
├── paper_02.pdf
├── ...
└── paper_20.pdf
```

### 步骤 2：启动系统

AI Coding Agent 读取 `AGENTS.md` 获取系统入口，读取 `workflow.json` 获取执行计划，然后按 DAG 调度执行：

```
请读取 batch_translation_system/AGENTS.md 和 workflow.json，
按照工作流定义执行批量翻译任务。
输入目录：input/
输出目录：output/
```

### 步骤 3：查看结果

执行完成后，在 `output/` 目录查看翻译结果：

```
output/
├── paper_01_zh.docx    ← 翻译完成的中文Word文档
├── paper_02_zh.docx
├── ...
└── paper_20_zh.docx
```

### 步骤 4：查看执行报告

在 `reports/execution_report.md` 查看执行详情，包括：
- 成功/失败文档列表
- 质量指标
- 重试记录
- 术语冲突（需人工裁定）
- 候选记忆（需人工审批）

### 步骤 5：处理待办事项

根据执行报告处理以下事项：

1. **失败文档**：检查 `paper_07.pdf` 和 `paper_15.pdf` 的失败原因，修复后重新翻译。
2. **术语冲突**：查看 `research_output/terminology.json` 中的 `conflict_terms`，人工裁定译法，更新术语表后可重新翻译相关段落。
3. **候选记忆审批**：查看 `memory/candidates/` 中的候选记忆，审批后迁移到正式记忆层，供未来任务复用。

### 步骤 6（可选）：复用记忆

下次执行类似翻译任务时，系统会自动读取已审批的记忆：
- 语义记忆中的术语表可直接复用
- 程序性记忆中的"术语先行策略"可指导规划
- 评估记忆中的"PDF解析是主要失败原因"可提前预警

---

## 总结

本示例展示了 Agent Factory 的完整工作流程：

1. **用户输入** → 自然语言需求
2. **需求解析** → requirements.json（结构化）
3. **架构决策** → architecture_decision.json（选择翻译型工作流）
4. **工作流定义** → workflow.json（85个任务的DAG）
5. **Agent 清单** → agent_manifest.json（6种Agent角色）
6. **Agent 定义** → agents/*/AGENTS.md（具体职责）
7. **执行** → 编排器按DAG调度，最大化并行
8. **执行报告** → 18/20成功，2篇失败，PARTIAL
9. **工程目录** → 完整的可复用系统
10. **用户使用** → 放入PDF、启动、查看结果、处理待办

**关键设计体现：**
- **无需部署LLM**：AI Coding Agent 自身作为执行引擎，读取指令文件后执行
- **最大化并行**：20篇论文分批并行翻译，每批5篇，受 max_parallel 限制
- **最小化Token**：术语表全局共享（引用路径而非全文复制）、分块处理控制上下文
- **记忆进化**：执行经验写入候选区，经审批后供未来复用
- **深度思考补偿**：翻译时启用术语一致性自检脚手架
- **允许部分结果**：2篇失败不影响18篇成功交付，标注为 PARTIAL
