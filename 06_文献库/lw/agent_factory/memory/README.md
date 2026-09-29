# 记忆系统使用说明

> 本文件说明 Agent Factory 记忆系统的五层体系、状态流转、条目结构、受控进化流程，以及如何读取和写入记忆。
>
> **核心原则：新记忆不自动启用，必须经过审批流程。**

---

## 一、五层记忆体系

Agent Factory 的记忆系统分为五层，每层存储不同类型的知识：

| 层级 | 名称 | 目录 | 存储内容 | 生命周期 |
|------|------|------|----------|----------|
| 第一层 | 用户偏好 | `user_preferences.json` | 用户的语言风格、格式偏好、质量要求 | 永久（用户可修改） |
| 第二层 | 情景记忆 | `episodic/` | 具体任务执行的上下文记录（何时、做了什么、结果如何） | 中期（可淘汰） |
| 第三层 | 语义记忆 | `semantic/` | 领域概念、事实知识、术语表、实体关系 | 长期（可进化） |
| 第四层 | 程序性记忆 | `procedural/` | 操作流程、最佳实践、有效策略模式 | 长期（可进化） |
| 第五层 | 评估记忆 | `evaluation/` | 质量评估结果、常见错误模式、审核规则 | 长期（可进化） |

### 第一层：用户偏好（user_preferences.json）

存储用户个人化的偏好设置，影响所有 Agent 的行为风格。

**典型内容：**
- 语言风格偏好（学术/通俗/正式/口语）
- 输出格式偏好（Markdown/DOCX/JSON）
- 质量严格度偏好（fast/standard/strict）
- 术语翻译偏好（保留原文/翻译/双语标注）
- 特定领域的个人术语习惯

### 第二层：情景记忆（episodic/）

存储具体任务执行的"经历"，类似人类的" episodic memory"。

**典型内容：**
- 任务ID、执行时间、执行Agent
- 任务输入输出的摘要
- 执行过程中遇到的问题与解决方案
- 任务结果（pass/fail/partial）

### 第三层：语义记忆（semantic/）

存储领域知识和事实，类似人类的" semantic memory"。

**典型内容：**
- 领域术语表（源语言→目标语言映射）
- 概念定义与关系
- 已验证的事实知识
- 实体信息（人名、机构名、项目名）

### 第四层：程序性记忆（procedural/）

存储"怎么做"的知识，类似人类的" procedural memory"。

**典型内容：**
- 有效的任务分解模式
- 高效的检索策略
- 已验证的审核规则
- 分块处理最佳实践
- 降级策略选择经验

### 第五层：评估记忆（evaluation/）

存储质量评估的反馈与模式。

**典型内容：**
- 常见错误模式（哪些错误反复出现）
- 有效审核规则（哪些检查最有价值）
- 质量趋势（某类任务的质量是否在改善）
- 用户满意度反馈

---

## 二、记忆状态流转

每条记忆条目都有明确的生命周期状态：

```
┌───────────┐     审批通过      ┌───────────┐     使用验证     ┌───────────┐
│ candidate │ ───────────────→ │ validated │ ───────────────→ │ approved  │
│  (候选)    │                  │ (已验证)   │                  │ (已批准)   │
└─────┬─────┘                  └─────┬─────┘                  └─────┬─────┘
      │                              │                              │
      │ 审批拒绝                      │ 验证失败                      │ 过时/被替代
      ▼                              ▼                              ▼
┌───────────┐                  ┌───────────┐                  ┌───────────┐
│ rejected  │                  │ rejected  │                  │ deprecated│
│ (已拒绝)   │                  │ (已拒绝)   │                  │ (已废弃)   │
└───────────┘                  └───────────┘                  └───────────┘
```

### 状态说明

| 状态 | 说明 | 可被Agent读取？ | 可被Agent写入？ |
|------|------|----------------|----------------|
| **candidate** | 新产生的记忆，等待审批 | 否（仅在候选区） | 是（写入候选区） |
| **validated** | 通过初步验证，确认格式与内容合规 | 是（只读） | 否 |
| **approved** | 正式批准，可被所有Agent使用 | 是（只读） | 否 |
| **deprecated** | 已过时或被更好的记忆替代 | 是（只读，低优先级） | 否 |
| **rejected** | 审批未通过，不可使用 | 否 | 否 |

### 状态流转规则

1. **candidate → validated**：候选记忆通过格式校验和内容初步审查。
2. **candidate → rejected**：候选记忆格式错误、内容不准确或重复。
3. **validated → approved**：经过实际使用验证，确认有效后正式批准。
4. **validated → rejected**：使用中发现问题，回退为拒绝。
5. **approved → deprecated**：被更新的记忆替代或已过时。
6. **deprecated → approved**：如果旧记忆重新变得有效（罕见），可恢复。

> **关键约束：** 当 `auto_approve_candidates = false`（默认）时，candidate → validated 的转换需要人工审批或独立审批Agent确认。Agent 自身不能将自己的候选记忆直接提升为 validated。

---

## 三、记忆条目结构

所有记忆条目使用统一的 JSON 结构：

```json
{
  "id": "MEM-EPISODIC-2026-001",
  "layer": "episodic",
  "status": "approved",
  "created_at": "2026-07-27T10:00:00Z",
  "updated_at": "2026-07-27T10:00:00Z",
  "created_by": "planner",
  "approved_by": "human_review",
  "approved_at": "2026-07-27T14:00:00Z",

  "content": {
    "task_id": "translation_001",
    "task_type": "academic_paper_translation",
    "summary": "20篇论文批量翻译，18篇成功2篇失败",
    "key_findings": [
      "术语提取阶段应优先处理高频术语",
      "PDF解析失败是主要失败原因（2/20）"
    ],
    "outcome": "partial",
    "metrics": {
      "success_rate": 0.90,
      "avg_terminology_consistency": 0.96
    }
  },

  "tags": ["translation", "batch", "academic", "pdf"],
  "related_memories": ["MEM-PROCEDURAL-2026-003"],
  "expiry": null,
  "confidence": "high"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 唯一标识，格式 `MEM-{LAYER}-{YEAR}-{SEQ}` |
| `layer` | string | 是 | 记忆层级（user_preferences/episodic/semantic/procedural/evaluation） |
| `status` | string | 是 | 状态（candidate/validated/approved/deprecated/rejected） |
| `created_at` | string | 是 | 创建时间（ISO 8601） |
| `updated_at` | string | 是 | 最后更新时间 |
| `created_by` | string | 是 | 创建者（Agent名称或human） |
| `approved_by` | string | 否 | 审批者（当status为approved时必填） |
| `approved_at` | string | 否 | 审批时间 |
| `content` | object | 是 | 记忆内容（结构因层级而异） |
| `tags` | array | 否 | 标签，用于检索 |
| `related_memories` | array | 否 | 关联记忆ID列表 |
| `expiry` | string | 否 | 过期时间（null表示永不过期） |
| `confidence` | string | 否 | 置信度（high/medium/low） |

---

## 四、受控进化流程

记忆系统采用"受控进化"策略，防止低质量记忆污染知识库。

### 4.1 进化流程

```
Agent执行任务
    │
    ▼
产生新记忆（术语、经验、模式等）
    │
    ▼
写入 candidates/ 目录（status = candidate）
    │
    ▼
┌─────────────────────────────────┐
│ 审批流程                         │
│                                 │
│  auto_approve_candidates=false: │
│    → 人工审批或独立审批Agent确认  │
│                                 │
│  auto_approve_candidates=true:  │
│    → 自动格式校验 + 内容审查     │
│    → 通过则自动转为validated     │
└────────────────┬────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
     审批通过            审批拒绝
        │                 │
        ▼                 ▼
  status=validated   status=rejected
        │
        ▼
  在后续任务中使用验证
        │
   ┌────┴────┐
   │         │
 验证有效   验证无效
   │         │
   ▼         ▼
status=approved  status=rejected
   │
   ▼
迁移到正式记忆层目录
（episodic/semantic/procedural/evaluation）
```

### 4.2 审批标准

| 检查项 | 说明 | 不通过处理 |
|--------|------|-----------|
| 格式校验 | 条目结构符合JSON Schema | rejected |
| 内容准确 | 内容事实准确，无错误 | rejected |
| 非重复 | 与已有记忆不重复 | 合并到已有记忆 |
| 有价值 | 对未来任务有参考价值 | rejected |
| 来源可信 | 记忆来源可追溯 | rejected |

### 4.3 淘汰策略

当某层记忆条目数超过 `max_memory_items`（默认1000）时，触发淘汰：

1. **优先淘汰 deprecated 状态**的条目。
2. **其次淘汰低 confidence** 的条目（low > medium > high）。
3. **其次淘汰最久未使用**的条目（按 updated_at 排序）。
4. **最后淘汰 expiry 已过期**的条目。
5. **永不淘汰** approved 且 confidence=high 且无 expiry 的核心记忆。

---

## 五、如何读取记忆

### 5.1 读取规则

| 记忆层 | 谁可读 | 读取范围 |
|--------|--------|----------|
| 用户偏好 | 所有Agent | 全部（status = approved） |
| 情景记忆 | 所有Agent | 全部（status = approved/validated） |
| 语义记忆 | 所有Agent | 全部（status = approved） |
| 程序性记忆 | 所有Agent | 全部（status = approved） |
| 评估记忆 | 所有Agent | 全部（status = approved） |
| 候选区 | 仅审批Agent/人工 | 全部（所有status） |

### 5.2 读取示例

```python
from src.memory_manager import MemoryManager

mm = MemoryManager()

# 读取用户偏好
prefs = mm.read("user_preferences")
style = prefs.get("language_style", "academic")

# 读取语义记忆中的术语表
terminology = mm.read("semantic", tags=["terminology", "machine_learning"])

# 读取程序性记忆中的有效策略
strategies = mm.read("procedural", tags=["translation", "chunking"])

# 读取评估记忆中的常见错误模式
error_patterns = mm.read("evaluation", tags=["common_errors"])
```

### 5.3 上下文最小化原则

读取记忆时遵循**上下文最小化**原则：
- 只读取与当前任务相关的记忆条目（通过 tags 过滤）。
- 只读取 approved 状态的记忆。
- 记忆条目以引用路径传递，不全文复制到上下文。
- 每次读取的记忆条目数不超过 10 条（防止上下文膨胀）。

---

## 六、如何写入记忆

### 6.1 写入规则

| 记忆层 | 谁可写 | 写入位置 | 写入状态 |
|--------|--------|----------|----------|
| 用户偏好 | 仅人工 | user_preferences.json | approved（直接生效） |
| 情景记忆 | 所有Agent | candidates/ | candidate |
| 语义记忆 | researcher, fact_checker | candidates/ | candidate |
| 程序性记忆 | 所有Agent | candidates/ | candidate |
| 评估记忆 | reviewer, fact_checker | candidates/ | candidate |

> **关键约束：** Agent 写入的记忆**始终**先进入 `candidates/` 目录，状态为 `candidate`。只有经过审批流程后才能迁移到正式记忆层目录并转为 `approved`。

### 6.2 写入示例

```python
from src.memory_manager import MemoryManager

mm = MemoryManager()

# 写入情景记忆（候选）
mm.write_candidate(
    layer="episodic",
    created_by="planner",
    content={
        "task_id": "translation_001",
        "task_type": "academic_paper_translation",
        "summary": "术语提取应在翻译前完成，可显著提升一致性",
        "key_findings": ["术语先行策略有效"],
        "outcome": "pass"
    },
    tags=["translation", "terminology"]
)

# 写入语义记忆（候选 - 新术语）
mm.write_candidate(
    layer="semantic",
    created_by="researcher",
    content={
        "type": "terminology",
        "source_term": "transformer architecture",
        "target_term": "Transformer架构",
        "domain": "deep_learning",
        "sources": ["paper_01.pdf:p3"]
    },
    tags=["terminology", "deep_learning"],
    confidence="high"
)

# 写入程序性记忆（候选 - 有效策略）
mm.write_candidate(
    layer="procedural",
    created_by="writer",
    content={
        "strategy": "chunk_translation",
        "description": "按800-1000词分块翻译，每块携带前2-3句作为衔接上下文",
        "effectiveness": "high",
        "use_case": "长文档翻译"
    },
    tags=["translation", "chunking", "strategy"]
)
```

### 6.3 写入注意事项

1. **不自行审批**：Agent 写入候选记忆后，不得自行将状态改为 validated 或 approved。
2. **标注来源**：每条候选记忆必须标注 created_by 和内容来源。
3. **避免重复**：写入前检查是否已有相似记忆，如有则更新而非新增。
4. **标注置信度**：对不确定的记忆标注低 confidence，供审批时参考。
5. **不写入猜测**：未经源文本验证的"常识"或"推测"不应写入记忆。

---

## 七、目录结构

```
memory/
├── README.md                # 本文件
├── user_preferences.json    # 用户偏好（第一层，直接生效）
├── episodic/                # 情景记忆（第二层）
│   ├── MEM-EPISODIC-2026-001.json
│   └── MEM-EPISODIC-2026-002.json
├── semantic/                # 语义记忆（第三层）
│   ├── MEM-SEMANTIC-2026-001.json
│   └── terminology_ml.json
├── procedural/              # 程序性记忆（第四层）
│   └── MEM-PROCEDURAL-2026-001.json
├── evaluation/              # 评估记忆（第五层）
│   └── MEM-EVALUATION-2026-001.json
└── candidates/              # 候选区（所有新记忆先存放于此）
    ├── MEM-EPISODIC-2026-003.json
    ├── MEM-SEMANTIC-2026-005.json
    └── MEM-PROCEDURAL-2026-002.json
```

**说明：**
- `episodic/`、`semantic/`、`procedural/`、`evaluation/` 目录中存放已 approved 的正式记忆。
- `candidates/` 目录存放所有 status = candidate 的候选记忆，等待审批。
- 审批通过后，候选记忆从 `candidates/` 迁移到对应的正式记忆目录。
- 审批拒绝的记忆保留在 `candidates/` 中，状态改为 rejected，定期清理。
