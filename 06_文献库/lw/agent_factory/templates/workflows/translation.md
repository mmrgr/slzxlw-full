# 翻译型工作流模板

> 本模板适用于文档翻译、论文翻译、批量翻译等场景。
> 生成系统时，将本模板适配到具体任务后写入 `workflow.json`。

---

## 一、工作流概述

翻译型工作流遵循"术语提取 → 并行翻译 → 一致性检查 → 审校"的架构。翻译型工作流的核心特点是**术语先行**和**分块并行翻译**——先提取全文术语建立统一术语表，再将文档分块后并行翻译，最后做全文一致性检查。

**适用场景：**
- 学术论文批量翻译
- 技术文档翻译
- 书籍翻译
- 多语言文档生成
- 合同/法律文档翻译

---

## 二、DAG 结构图

```
                    ┌──────────────┐
                    │   T0: 规划    │  agent: planner
                    │  (需求分解)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  T1: 术语提取  │  agent: researcher
                    │  (建立术语表)  │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │ T2a: 翻译-1  │  │ T2b: 翻译-2  │  │ T2c: 翻译-N  │  agent: writer
   │ (第1块)      │  │ (第2块)      │  │ (第N块)      │  parallel_group: 2
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼───────┐
                    │  T3: 拼接合并  │  agent: orchestrator
                    │  (分块拼接)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ T4: 一致性检查 │  agent: reviewer
                    │ (全文术语一致) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  T5: 事实核查  │  agent: fact_checker
                    │  (数据引用)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   T6: 审校    │  agent: reviewer
                    │  (语言质量)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   T7: 交付    │  agent: orchestrator
                    │  (格式输出)    │
                    └──────────────┘
```

---

## 三、核心策略：分块翻译

### 分块策略

| 参数 | 值 | 说明 |
|------|-----|------|
| 块大小 | 800-1000 词 | 每块约 800-1000 个英文单词 |
| 分块单位 | 自然段落 | 以段落为最小单位，不在段落中间切分 |
| 块间上下文 | 前 2-3 句 | 每块携带前一块的最后 2-3 句作为衔接上下文 |
| 术语表 | 全局共享 | 所有分块共享同一份术语表 |
| 最大并行 | max_parallel | 同时翻译的分块数受并行度限制 |

### 为什么是 800-1000 词？

1. **上下文完整性**：800-1000 词通常包含 3-5 个完整段落，上下文信息足够。
2. **Token 效率**：加上术语表和衔接上下文，单块总输入约 12000-15000 字符，在 max_context_chars_per_task 范围内。
3. **质量平衡**：块太大则并行度低、重试成本高；块太小则上下文不足、拼接处易出问题。
4. **段落边界**：按段落分块避免在句子中间切分，保证语义完整。

### 分块示例

```
原文：12000 词的论文

分块方案：
  块1: 第1-3节（950词）  → T2a
  块2: 第4-5节（880词）  → T2b
  块3: 第6-7节（1020词） → T2c
  块4: 第8节+参考文献（850词） → T2d

每块输入：
  - 本块源文本
  - 前2-3句衔接上下文（第1块无）
  - 完整术语表
  - 翻译风格指南
```

---

## 四、任务节点定义

### T0：规划（planner）

| 属性 | 值 |
|------|-----|
| 输入 | 翻译需求（源语言、目标语言、文档列表、质量要求） |
| 输出 | DAG、分块方案、每块的字数估算 |
| 特别职责 | 确定分块策略、计算所需并行翻译实例数 |

### T1：术语提取（researcher）

| 属性 | 值 |
|------|-----|
| 依赖 | T0 |
| 输入 | 全部源文档 |
| 输出 | 术语表 (terminology.json)、术语冲突标记 |
| 特别职责 | 提取所有专业术语，建立源→目标语言映射，标注冲突术语 |
| 完成条件 | 术语覆盖所有出现 >= 3 次的专业词汇 |

### T2a/T2b/.../T2n：并行翻译（writer，并行）

| 属性 | 值 |
|------|-----|
| 依赖 | T1（术语表必须先就绪） |
| 并行组 | 2 |
| 输入 | 本块源文本 + 衔接上下文 + 术语表 + 风格指南 |
| 输出 | 本块译文 |
| 完成条件 | 本块全部段落已翻译、术语一致、引用保留 |
| 约束 | 严格使用术语表中的翻译，不得自行变更术语 |

### T3：拼接合并（orchestrator）

| 属性 | 值 |
|------|-----|
| 依赖 | 所有 T2x 完成 |
| 输入 | 所有分块译文 |
| 输出 | 完整译文 |
| 特别职责 | 按原始顺序拼接、检查拼接处连贯性 |

### T4：一致性检查（reviewer）

| 属性 | 值 |
|------|-----|
| 依赖 | T3 |
| 输入 | 完整译文、术语表 |
| 输出 | 一致性检查报告 |
| 特别职责 | 全文术语一致性扫描、风格统一性检查 |

### T5：事实核查（fact_checker）

| 属性 | 值 |
|------|-----|
| 依赖 | T4 |
| 输入 | 完整译文、源文本 |
| 输出 | 事实核查报告 |
| 特别职责 | 核对数字、日期、引用、人名是否准确翻译 |

### T6：审校（reviewer）

| 属性 | 值 |
|------|-----|
| 依赖 | T5 |
| 输入 | 完整译文、源文本、一致性报告、事实核查报告 |
| 输出 | 审校报告、通过/驳回决策 |
| 特别职责 | 语言流畅性、翻译准确性、格式完整性全面审核 |

### T7：交付（orchestrator）

| 属性 | 值 |
|------|-----|
| 依赖 | T6 (verdict = pass) |
| 输入 | 通过审校的译文 |
| 输出 | 最终翻译文档（DOCX/Markdown等） |

---

## 五、workflow.json 完整示例

```json
{
  "workflow_id": "translation_001",
  "workflow_type": "translation",
  "mode": "standard",
  "tasks": [
    {
      "id": "T0",
      "name": "翻译规划",
      "agent": "planner",
      "depends_on": [],
      "parallel_group": 0,
      "context_estimate": 5000,
      "risk": "low",
      "max_retries": 1,
      "output": {
        "chunking_plan": "按段落分块，每块800-1000词",
        "total_chunks": 4,
        "parallel_strategy": "max_concurrency=4"
      }
    },
    {
      "id": "T1",
      "name": "术语提取",
      "agent": "researcher",
      "depends_on": ["T0"],
      "parallel_group": 1,
      "context_estimate": 20000,
      "risk": "medium",
      "max_retries": 2,
      "output_target": "research_output/terminology.json"
    },
    {
      "id": "T2a",
      "name": "翻译-第1块",
      "agent": "writer",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 15000,
      "risk": "medium",
      "max_retries": 2,
      "input_refs": {
        "source_text": "input/paper_01_chunk_1.txt",
        "terminology": "research_output/terminology.json",
        "context_prefix": null
      },
      "output_target": "output/paper_01_chunk_1_zh.md"
    },
    {
      "id": "T2b",
      "name": "翻译-第2块",
      "agent": "writer",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 15000,
      "risk": "medium",
      "max_retries": 2,
      "input_refs": {
        "source_text": "input/paper_01_chunk_2.txt",
        "terminology": "research_output/terminology.json",
        "context_prefix": "output/paper_01_chunk_1_zh.md:last_3_sentences"
      },
      "output_target": "output/paper_01_chunk_2_zh.md"
    },
    {
      "id": "T2c",
      "name": "翻译-第3块",
      "agent": "writer",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 15000,
      "risk": "medium",
      "max_retries": 2,
      "input_refs": {
        "source_text": "input/paper_01_chunk_3.txt",
        "terminology": "research_output/terminology.json",
        "context_prefix": "output/paper_01_chunk_2_zh.md:last_3_sentences"
      },
      "output_target": "output/paper_01_chunk_3_zh.md"
    },
    {
      "id": "T2d",
      "name": "翻译-第4块",
      "agent": "writer",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "context_estimate": 15000,
      "risk": "medium",
      "max_retries": 2,
      "input_refs": {
        "source_text": "input/paper_01_chunk_4.txt",
        "terminology": "research_output/terminology.json",
        "context_prefix": "output/paper_01_chunk_3_zh.md:last_3_sentences"
      },
      "output_target": "output/paper_01_chunk_4_zh.md"
    },
    {
      "id": "T3",
      "name": "分块拼接",
      "agent": "orchestrator",
      "depends_on": ["T2a", "T2b", "T2c", "T2d"],
      "parallel_group": 3,
      "context_estimate": 30000,
      "risk": "low",
      "max_retries": 1,
      "output_target": "output/paper_01_zh_full.md"
    },
    {
      "id": "T4",
      "name": "一致性检查",
      "agent": "reviewer",
      "depends_on": ["T3"],
      "parallel_group": 4,
      "context_estimate": 20000,
      "risk": "medium",
      "max_retries": 1,
      "review_type": "terminology_consistency"
    },
    {
      "id": "T5",
      "name": "事实核查",
      "agent": "fact_checker",
      "depends_on": ["T4"],
      "parallel_group": 5,
      "context_estimate": 15000,
      "risk": "medium",
      "max_retries": 1,
      "fact_check_scope": "data_and_citations"
    },
    {
      "id": "T6",
      "name": "语言审校",
      "agent": "reviewer",
      "depends_on": ["T5"],
      "parallel_group": 6,
      "context_estimate": 25000,
      "risk": "medium",
      "max_retries": 1,
      "review_type": "accuracy_and_fluency"
    },
    {
      "id": "T7",
      "name": "格式输出",
      "agent": "orchestrator",
      "depends_on": ["T6"],
      "parallel_group": 7,
      "context_estimate": 5000,
      "risk": "low",
      "max_retries": 0,
      "condition": "T6.verdict == 'pass'",
      "output_target": "output/paper_01_zh.docx"
    }
  ],
  "parallel_groups": {
    "2": {
      "tasks": ["T2a", "T2b", "T2c", "T2d"],
      "max_concurrency": 4
    }
  },
  "retry_edges": [
    {
      "from": "T6",
      "to": "T3",
      "condition": "T6.verdict == 'retry'",
      "max_retries": 2,
      "retry_scope": "affected_chunks_only"
    },
    {
      "from": "T4",
      "to": "T2a",
      "condition": "T4.issues contain chunk_1 terminology errors",
      "max_retries": 1,
      "note": "仅重试有问题的分块，不全部重翻"
    }
  ]
}
```

---

## 六、术语表管理

术语表是翻译型工作流的核心共享资源，所有并行翻译实例必须引用同一份术语表。

**术语表结构示例（terminology.json）：**
```json
{
  "version": "1.0",
  "source_language": "English",
  "target_language": "Chinese",
  "terminology": [
    {
      "id": "TERM-001",
      "source": "reinforcement learning",
      "target": "强化学习",
      "confidence": "high",
      "frequency": 15,
      "sources": ["paper_01.pdf:p3", "paper_01.pdf:p12"],
      "alternatives": ["增强学习"],
      "domain": "machine_learning"
    }
  ],
  "conflict_terms": [
    {
      "source": "attention mechanism",
      "candidates": [
        {"target": "注意力机制", "sources": ["paper_01.pdf:p5"]},
        {"target": "注意机制", "sources": ["paper_03.pdf:p8"]}
      ],
      "resolution": "pending",
      "note": "两种译法均常见，需人工裁定"
    }
  ]
}
```

**术语使用规则：**
1. 翻译时**必须**使用术语表中的 target 翻译，不得自行变更。
2. 遇到 conflict_terms 中未解决的术语，使用第一个候选译法，并在译文中标注 `[术语待定]`。
3. 发现术语表中未收录的新术语，写入候选区，不自行翻译。

---

## 七、降级策略

| 降级级别 | 措施 |
|----------|------|
| Level 1 | 并行翻译改为串行（max_concurrency=1） |
| Level 2 | 跳过 T5 事实核查，T4 一致性检查后直接审校 |
| Level 3 | 增大分块大小（800-1000词 → 1500-2000词），减少分块数 |
| Level 4 | 跳过 T4 和 T5，T3 拼接后直接 T6 审校 |
| Level 5 | 合并 T4/T5/T6 为单次审核 |
| Level 6 | 单 Agent 串行翻译：不分块、不并行、单次审核 |

---

## 八、批量翻译扩展

当需要翻译多篇文档时，在 T0 之上增加一层循环：

```
T0: 总规划（确定文档列表与优先级）
  ↓
对每篇文档独立执行 T1→T7 管线
（多篇文档间可并行，受 max_parallel_agents 限制）
  ↓
T_final: 批量交付（汇总所有文档的翻译结果）
```

**批量翻译注意事项：**
1. 多篇文档共享一份术语表（T1 对所有文档统一提取术语）。
2. 同一文档内的分块可并行，不同文档间也可并行。
3. 优先翻译术语出现频率高的文档，确保术语表尽早完善。
