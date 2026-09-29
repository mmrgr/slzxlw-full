# 文档处理型工作流模板

> 本模板适用于文档转换、报告生成、文档摘要、格式迁移等场景。
> 生成系统时，将本模板适配到具体任务后写入 `workflow.json`。

---

## 一、工作流概述

文档处理型工作流遵循"提取 → 分析 → 生成 → 审核"的经典管线。每个阶段对应一个或多个 Agent，阶段间通过 DAG 定义依赖关系。

**适用场景：**
- PDF 转 Word/Markdown
- 文档摘要生成
- 报告自动生成
- 文档格式迁移
- 批量文档处理

---

## 二、DAG 结构图

```
                    ┌──────────────┐
                    │   T0: 规划    │  agent: planner
                    │  (需求分解)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   T1: 提取    │  agent: researcher
                    │  (信息提取)    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼─────┐ ┌───▼──────┐ ┌──▼─────────┐
       │ T2a: 分析-1 │ │T2b:分析-2│ │ T2c: 分析-3 │  agent: researcher
       │ (并行分块)  │ │(并行分块) │ │ (并行分块)  │  parallel_group: 2
       └──────┬─────┘ └───┬──────┘ └──┬─────────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼───────┐
                    │   T3: 生成    │  agent: writer
                    │  (内容生成)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   T4: 审核    │  agent: reviewer
                    │  (质量审核)    │
                    └──────┬───────┘
                           │
                      ┌────┴────┐
                      │         │
                 pass │         │ retry
                      │         │
              ┌───────▼──┐ ┌───▼──────────┐
              │ T5: 交付  │ │ T3': 修正重试  │  agent: writer
              │ (输出)    │ │ (回到生成)    │
              └──────────┘ └──────────────┘
```

---

## 三、任务节点定义

### T0：规划（planner）

| 属性 | 值 |
|------|-----|
| Agent | planner |
| 依赖 | 无 |
| 并行组 | 0（单独执行） |
| 输入 | 用户需求 (requirements.json) |
| 输出 | workflow.json（任务 DAG）、agent_manifest.json |
| 完成条件 | DAG 无循环、任务数 <= max_agents、每个任务有 Agent 分配 |

### T1：提取（researcher）

| 属性 | 值 |
|------|-----|
| Agent | researcher |
| 依赖 | T0 |
| 并行组 | 1 |
| 输入 | 源文档路径、任务 DAG |
| 输出 | 结构化素材 (research_output/extracted.json)、来源索引 |
| 完成条件 | 所有源文档均已提取、来源标注完整 |

### T2a/T2b/T2c：分析（researcher，并行）

| 属性 | 值 |
|------|-----|
| Agent | researcher（多个实例） |
| 依赖 | T1 |
| 并行组 | 2（max_concurrency 限制并行数） |
| 输入 | T1 的结构化素材（分块） |
| 输出 | 分块分析结果 |
| 完成条件 | 每块分析完成、结果通过 Schema 校验 |
| 分块策略 | 按文档章节或固定字数分块，每块 800-1000 词 |

### T3：生成（writer）

| 属性 | 值 |
|------|-----|
| Agent | writer |
| 依赖 | T2a, T2b, T2c（全部完成） |
| 并行组 | 3 |
| 输入 | 所有分块分析结果、术语表、用户偏好 |
| 输出 | 生成文档 |
| 完成条件 | 所有分析结果均已整合、格式符合规范、自检通过 |

### T4：审核（reviewer）

| 属性 | 值 |
|------|-----|
| Agent | reviewer |
| 依赖 | T3 |
| 并行组 | 4 |
| 输入 | 生成文档、源素材、术语表、验收标准 |
| 输出 | 审核报告、通过/驳回决策 |
| 完成条件 | 所有维度已审核、问题已分级、verdict 已明确 |

### T5：交付（orchestrator）

| 属性 | 值 |
|------|-----|
| Agent | orchestrator（仅汇总） |
| 依赖 | T4 (verdict = pass) |
| 并行组 | 5 |
| 输入 | 通过审核的文档 |
| 输出 | 最终交付文件、执行报告 |
| 完成条件 | 文件已写入输出路径、执行报告已生成 |

### T3'：修正重试（writer）

| 属性 | 值 |
|------|-----|
| Agent | writer |
| 依赖 | T4 (verdict = retry) |
| 并行组 | 3（回到生成阶段） |
| 输入 | 审核报告中的修改建议、上一轮生成内容 |
| 输出 | 修正后的文档 |
| 完成条件 | 所有 critical 问题已修正 |
| 约束 | 重试次数 <= max_retries_per_task |

---

## 四、workflow.json 完整示例

```json
{
  "workflow_id": "doc_processing_001",
  "workflow_type": "document_processing",
  "mode": "standard",
  "tasks": [
    {
      "id": "T0",
      "name": "规划",
      "agent": "planner",
      "depends_on": [],
      "parallel_group": 0,
      "context_estimate": 3000,
      "risk": "low",
      "max_retries": 1
    },
    {
      "id": "T1",
      "name": "信息提取",
      "agent": "researcher",
      "depends_on": ["T0"],
      "parallel_group": 1,
      "context_estimate": 15000,
      "risk": "medium",
      "max_retries": 2
    },
    {
      "id": "T2a",
      "name": "分析-第1部分",
      "agent": "researcher",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 10000,
      "risk": "low",
      "max_retries": 1
    },
    {
      "id": "T2b",
      "name": "分析-第2部分",
      "agent": "researcher",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 10000,
      "risk": "low",
      "max_retries": 1
    },
    {
      "id": "T2c",
      "name": "分析-第3部分",
      "agent": "researcher",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 10000,
      "risk": "low",
      "max_retries": 1
    },
    {
      "id": "T3",
      "name": "内容生成",
      "agent": "writer",
      "depends_on": ["T2a", "T2b", "T2c"],
      "parallel_group": 3,
      "context_estimate": 25000,
      "risk": "high",
      "max_retries": 2
    },
    {
      "id": "T4",
      "name": "质量审核",
      "agent": "reviewer",
      "depends_on": ["T3"],
      "parallel_group": 4,
      "context_estimate": 12000,
      "risk": "medium",
      "max_retries": 1
    },
    {
      "id": "T5",
      "name": "交付",
      "agent": "orchestrator",
      "depends_on": ["T4"],
      "parallel_group": 5,
      "context_estimate": 2000,
      "risk": "low",
      "max_retries": 0,
      "condition": "T4.verdict == 'pass'"
    }
  ],
  "parallel_groups": {
    "2": {
      "tasks": ["T2a", "T2b", "T2c"],
      "max_concurrency": 3
    }
  },
  "retry_edges": [
    {
      "from": "T4",
      "to": "T3",
      "condition": "T4.verdict == 'retry'",
      "max_retries": 2
    }
  ]
}
```

---

## 五、降级策略

| 降级级别 | 触发条件 | 措施 |
|----------|----------|------|
| Level 1 | 并行接近上限 | T2a/T2b/T2c 改为串行执行 |
| Level 2 | Agent 总数超限 | 合并 T2a/T2b/T2c 为单个 T2 |
| Level 3 | Token 接近预算 | 跳过 T4 审核，T3 直接交付 |
| Level 4 | 上下文窗口不足 | T3 分块生成，逐块输出 |
| Level 5 | 单任务超限 | T1 和 T2 合并，提取即分析 |
| Level 6 | 系统资源严重不足 | 退化为单 Agent：planner 兼做提取+生成，跳过审核 |

---

## 六、使用方法

1. **确定需求**：明确输入文档类型、输出格式、质量要求。
2. **选择模式**：根据质量要求选择 fast/standard/strict。
3. **生成分块**：如果输入文档较大，预先确定分块策略。
4. **套用模板**：将上述 workflow.json 中的任务适配为具体任务名称。
5. **配置 Agent**：将 agents/ 下的角色模板适配为具体 Agent 定义。
6. **执行系统**：编排器读取 workflow.json，按 DAG 调度执行。
