# 研究分析型工作流模板

> 本模板适用于多源信息检索、综合研究、竞品分析、行业调研等场景。
> 生成系统时，将本模板适配到具体任务后写入 `workflow.json`。

---

## 一、工作流概述

研究分析型工作流遵循"多源检索 → 并行分析 → 综合 → 审核"的架构。与文档处理型不同，研究分析型的核心特点是**多源并行检索**和**跨源综合**——从多个独立信息源并行采集，然后将各源的分析结果交叉综合为统一报告。

**适用场景：**
- 多源文献综述
- 竞品分析报告
- 行业趋势研究
- 技术方案对比评估
- 市场调研报告

---

## 二、DAG 结构图

```
                    ┌──────────────┐
                    │   T0: 规划    │  agent: planner
                    │  (需求分解)    │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │ T1a: 检索-A  │  │ T1b: 检索-B  │  │ T1c: 检索-C  │  agent: researcher
   │ (来源A)      │  │ (来源B)      │  │ (来源C)      │  parallel_group: 1
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │ T2a: 分析-A  │  │ T2b: 分析-B  │  │ T2c: 分析-C  │  agent: researcher
   │ (来源A分析)  │  │ (来源B分析)  │  │ (来源C分析)  │  parallel_group: 2
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼───────┐
                    │   T3: 综合    │  agent: writer
                    │  (跨源综合)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  T4: 事实核查  │  agent: fact_checker
                    │  (事实验证)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   T5: 审核    │  agent: reviewer
                    │  (质量审核)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   T6: 交付    │  agent: orchestrator
                    │  (报告输出)    │
                    └──────────────┘
```

---

## 三、核心特点：多源并行与交叉综合

### 多源并行检索（T1a / T1b / T1c）

多个来源**同时**检索，互不依赖。每个来源由独立的 researcher 实例处理。

**来源类型示例：**
- 来源 A：学术论文数据库
- 来源 B：行业报告 / 白皮书
- 来源 C：新闻 / 博客 / 社区讨论

### 并行分析（T2a / T2b / T2c）

每个来源的检索结果由对应的 researcher 实例独立分析，提取关键发现、数据、观点。

### 跨源综合（T3）

writer 将所有来源的分析结果交叉综合：
1. **信息聚合**：按主题汇总各源的发现。
2. **冲突识别**：标注不同来源间的矛盾信息。
3. **交叉验证**：多源相互佐证的信息标注为高可信。
4. **综合推理**：基于多源信息形成综合结论。

---

## 四、任务节点定义

### T0：规划（planner）

| 属性 | 值 |
|------|-----|
| 输入 | 研究主题、信息源列表、研究深度要求 |
| 输出 | DAG、Agent 分配、每个来源的检索策略 |
| 特别职责 | 确定信息源数量与并行度，评估来源可信度 |

### T1a/T1b/T1c：多源检索（researcher，并行）

| 属性 | 值 |
|------|-----|
| 依赖 | T0 |
| 并行组 | 1 |
| 输入 | 各自来源的检索策略 |
| 输出 | 各源的结构化素材 |
| 完成条件 | 每个来源检索完成，素材有来源标注 |

### T2a/T2b/T2c：并行分析（researcher，并行）

| 属性 | 值 |
|------|-----|
| 依赖 | 对应的 T1x |
| 并行组 | 2 |
| 输入 | 各源的检索素材 |
| 输出 | 各源的分析结果（关键发现、数据、观点） |
| 完成条件 | 每源分析完成，发现已结构化 |

### T3：综合（writer）

| 属性 | 值 |
|------|-----|
| 依赖 | T2a, T2b, T2c（全部完成） |
| 输入 | 所有源的分析结果 |
| 输出 | 综合研究报告 |
| 特别职责 | 跨源信息聚合、冲突识别、交叉验证、综合推理 |

### T4：事实核查（fact_checker）

| 属性 | 值 |
|------|-----|
| 依赖 | T3 |
| 输入 | 综合报告、各源原始素材 |
| 输出 | 事实核查报告 |
| 特别职责 | 验证跨源综合中的因果推理和数据引用 |

### T5：审核（reviewer）

| 属性 | 值 |
|------|-----|
| 依赖 | T4 |
| 输入 | 综合报告、事实核查报告 |
| 输出 | 审核报告、通过/驳回决策 |
| 特别职责 | 检查综合逻辑是否成立、冲突处理是否合理 |

### T6：交付（orchestrator）

| 属性 | 值 |
|------|-----|
| 依赖 | T5 (verdict = pass) |
| 输出 | 最终研究报告、执行报告 |

---

## 五、workflow.json 完整示例

```json
{
  "workflow_id": "research_analysis_001",
  "workflow_type": "research_analysis",
  "mode": "standard",
  "tasks": [
    {
      "id": "T0",
      "name": "研究规划",
      "agent": "planner",
      "depends_on": [],
      "parallel_group": 0,
      "context_estimate": 5000,
      "risk": "medium",
      "max_retries": 1
    },
    {
      "id": "T1a",
      "name": "检索-学术论文",
      "agent": "researcher",
      "depends_on": ["T0"],
      "parallel_group": 1,
      "context_estimate": 15000,
      "risk": "medium",
      "max_retries": 2
    },
    {
      "id": "T1b",
      "name": "检索-行业报告",
      "agent": "researcher",
      "depends_on": ["T0"],
      "parallel_group": 1,
      "context_estimate": 12000,
      "risk": "medium",
      "max_retries": 2
    },
    {
      "id": "T1c",
      "name": "检索-新闻社区",
      "agent": "researcher",
      "depends_on": ["T0"],
      "parallel_group": 1,
      "context_estimate": 10000,
      "risk": "high",
      "max_retries": 2
    },
    {
      "id": "T2a",
      "name": "分析-学术论文",
      "agent": "researcher",
      "depends_on": ["T1a"],
      "parallel_group": 2,
      "context_estimate": 12000,
      "risk": "low",
      "max_retries": 1
    },
    {
      "id": "T2b",
      "name": "分析-行业报告",
      "agent": "researcher",
      "depends_on": ["T1b"],
      "parallel_group": 2,
      "context_estimate": 10000,
      "risk": "low",
      "max_retries": 1
    },
    {
      "id": "T2c",
      "name": "分析-新闻社区",
      "agent": "researcher",
      "depends_on": ["T1c"],
      "parallel_group": 2,
      "context_estimate": 8000,
      "risk": "medium",
      "max_retries": 1
    },
    {
      "id": "T3",
      "name": "跨源综合",
      "agent": "writer",
      "depends_on": ["T2a", "T2b", "T2c"],
      "parallel_group": 3,
      "context_estimate": 30000,
      "risk": "high",
      "max_retries": 2
    },
    {
      "id": "T4",
      "name": "事实核查",
      "agent": "fact_checker",
      "depends_on": ["T3"],
      "parallel_group": 4,
      "context_estimate": 15000,
      "risk": "medium",
      "max_retries": 1
    },
    {
      "id": "T5",
      "name": "质量审核",
      "agent": "reviewer",
      "depends_on": ["T4"],
      "parallel_group": 5,
      "context_estimate": 12000,
      "risk": "medium",
      "max_retries": 1
    },
    {
      "id": "T6",
      "name": "报告交付",
      "agent": "orchestrator",
      "depends_on": ["T5"],
      "parallel_group": 6,
      "context_estimate": 3000,
      "risk": "low",
      "max_retries": 0,
      "condition": "T5.verdict == 'pass'"
    }
  ],
  "parallel_groups": {
    "1": {
      "tasks": ["T1a", "T1b", "T1c"],
      "max_concurrency": 3
    },
    "2": {
      "tasks": ["T2a", "T2b", "T2c"],
      "max_concurrency": 3
    }
  },
  "retry_edges": [
    {
      "from": "T5",
      "to": "T3",
      "condition": "T5.verdict == 'retry' && T4.verdict == 'pass'",
      "max_retries": 2
    },
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

## 六、冲突处理策略

跨源综合中最常见的挑战是**来源间信息冲突**。T3（综合）阶段采用以下策略：

| 冲突类型 | 处理策略 | 示例 |
|----------|----------|------|
| 数据冲突 | 保留所有版本，标注各来源，标注可信度差异 | A源说市场规模100亿，B源说80亿 |
| 观点冲突 | 客观呈现各方观点，不强行裁决 | A源看好技术前景，B源持悲观态度 |
| 定义冲突 | 采用权威来源定义，标注替代定义 | A源定义X为...，B源定义X为... |
| 时间冲突 | 以最新来源为准，标注历史变化 | A源(2023)数据与B源(2025)数据不同 |

**原则：** 综合报告**不消除冲突**，而是**透明呈现冲突**，让读者自行判断。

---

## 七、降级策略

| 降级级别 | 措施 |
|----------|------|
| Level 1 | T1 和 T2 合并：检索即分析，减少阶段数 |
| Level 2 | 减少信息源数量（3源 → 2源 → 1源） |
| Level 3 | 跳过 T4 事实核查，T3 直接进入 T5 审核 |
| Level 4 | T3 分块综合：先两两综合，再最终综合 |
| Level 5 | 单源模式：仅保留最高可信度来源，跳过跨源综合 |
| Level 6 | 单 Agent 模式：planner 兼做检索+分析+综合 |
