# 冲突解决协议

> **本文件定义了 Agent Factory 生成的多Agent系统中，多个 Agent 给出不同结论时的解决规则。** 在并行审核（Phase 6）、多源数据整合、跨 Agent 推理等场景中，冲突不可避免。本协议确保冲突被系统性地识别、分类和解决，而非被忽略或随机选择。本协议主要在 strict 模式下启用；standard 模式下对高风险冲突启用；fast 模式下默认不启用。

---

## 一、核心原则

冲突解决遵循以下优先级原则，从高到低：

| 优先级 | 原则 | 说明 |
|--------|------|------|
| 1 | 确定性规则优先 | 能用确定性规则解决的，先用规则，不调用 Agent |
| 2 | 原始证据优先 | 涉及事实判断时，优先采信原始证据而非 Agent 的推断 |
| 3 | 用户指令优先 | 涉及用户偏好时，优先用户明确指令 |
| 4 | 裁决 Agent 介入 | 涉及专业判断时，提交裁决 Agent 做最终裁定 |
| 5 | 裁决最小上下文 | 裁决 Agent 只读取冲突内容，不重新读取整个任务 |

> **核心哲学**：冲突解决的目标不是"让所有 Agent 达成一致"，而是"找到最可能正确的结论"。一致性可以通过压制 dissent 达到，但正确性需要尊重证据。

---

## 二、冲突类型分类

### 2.1 四大冲突类型

| 冲突类型 | 标识 | 描述 | 典型场景 | 解决优先级 |
|----------|------|------|----------|------------|
| 事实冲突 | `fact_conflict` | 多个 Agent 对同一事实给出不同的陈述 | Agent A 说"规模达53.9万亿"，Agent B 说"规模达55.2万亿" | 原始证据优先 |
| 偏好冲突 | `preference_conflict` | 多个 Agent 对同一选择给出不同建议 | Agent A 建议"用正式语体"，Agent B 建议"用通俗语体" | 用户指令优先 |
| 判断冲突 | `judgment_conflict` | 多个 Agent 对同一问题给出不同专业判断 | Agent A 认为"论证充分"，Agent B 认为"论证薄弱" | 裁决 Agent 介入 |
| 格式冲突 | `format_conflict` | 多个 Agent 对同一输出的格式要求不一致 | Agent A 要求"标题用一、二、三"，Agent B 要求"标题用1. 2. 3." | 确定性规则优先 |

### 2.2 冲突识别

冲突在以下场景中被识别：

```
场景1：并行审核（Phase 6）
  多个 Reviewer Agent 对同一输出给出不同的审核结论
  → 比对审核结果，识别分歧点

场景2：多源数据整合
  多个数据源对同一指标给出不同数值
  → 数据对齐时发现数值不一致

场景3：跨 Agent 推理
  不同 Agent 基于各自上下文得出不同结论
  → 结论汇总时发现矛盾

场景4：记忆与当前结论
  记忆库中的既有结论与本次 Agent 输出不一致
  → 交叉验证时发现冲突
```

---

## 三、冲突解决流程

### 3.1 通用解决流程

```
检测到冲突
    │
    ▼
┌─────────────────┐
│ 冲突分类         │
│ (fact/preference │
│  /judgment/format)│
└────────┬────────┘
         │
    ┌────┴────┬─────────┬──────────┐
    ▼         ▼         ▼          ▼
 事实冲突  偏好冲突  判断冲突   格式冲突
    │         │         │          │
    ▼         ▼         ▼          ▼
 原始证据  用户指令  裁决Agent  确定性规则
 优先      优先      介入       优先
    │         │         │          │
    ▼         ▼         ▼          ▼
 查证原始  查询用户  裁决Agent   应用规则
 证据      偏好      做裁定      统一格式
    │         │         │          │
    ▼         ▼         ▼          ▼
 记录解决  记录解决  记录裁决    记录统一
 方案与    方案与    理由与      方案
 依据      依据      依据
    │         │         │          │
    └────┬────┴────┬────┴──────────┘
         │         │
         ▼         ▼
    ┌─────────────────┐
    │ 更新 run_report │
    │ open_issues     │
    └─────────────────┘
```

### 3.2 事实冲突解决流程（fact_conflict）

**原则**：原始证据优先。Agent 的推断不如原始数据可靠。

```
步骤1：识别冲突事实
  Agent A: "2024年数字经济规模达53.9万亿元"
  Agent B: "2024年数字经济规模达55.2万亿元"
  → 冲突点：53.9万亿 vs 55.2万亿

步骤2：追溯原始证据
  查询 Agent A 的数据来源 → output/T1/facts.json 中 F012，来源论文A
  查询 Agent B 的数据来源 → output/T1/facts.json 中 F045，来源论文B

步骤3：核对原始出处
  读取论文A原文对应段落 → "53.9万亿元"
  读取论文B原文对应段落 → "55.2万亿元"
  → 两个来源确实不同

步骤4：判断数据时效性
  论文A发布于2024年12月（年度数据）
  论文B发布于2025年3月（修订数据）
  → 论文B数据更新，采信55.2万亿

步骤5：记录解决方案
  冲突记录：
  {
    "type": "fact_conflict",
    "fact": "2024年数字经济规模",
    "conflicting_values": ["53.9万亿", "55.2万亿"],
    "sources": ["论文A(2024.12)", "论文B(2025.03)"],
    "resolution": "采信55.2万亿",
    "reason": "论文B发布更晚，数据为修订值",
    "evidence_ref": "output/T1/facts.json#F012, output/T1/facts.json#F045"
  }
```

**若无法追溯原始证据**（如数据来源不可查）：

```
步骤4（替代）：降级为判断冲突
  → 交由裁决 Agent 判断哪个更可靠
  → 或标记为 open_issue，在报告中注明数据不一致
```

### 3.3 偏好冲突解决流程（preference_conflict）

**原则**：用户指令优先。Agent 的建议不如用户的明确指令。

```
步骤1：识别冲突偏好
  Agent A（语言审核）: "建议使用正式学术语体"
  Agent B（可读性审核）: "建议使用通俗易懂语体"
  → 冲突点：正式 vs 通俗

步骤2：查询用户偏好
  查询 memory/user_preferences.json → 用户偏好"面向大众的科普风格"
  查询 requirements.json → deliverable_detail: "面向公众的综述报告"

步骤3：应用用户指令
  用户偏好"面向大众" → 采信 Agent B 的建议"通俗易懂语体"
  但可保留部分正式表述（平衡专业性与可读性）

步骤4：记录解决方案
  冲突记录：
  {
    "type": "preference_conflict",
    "preference": "语体风格",
    "conflicting_suggestions": ["正式学术语体", "通俗易懂语体"],
    "resolution": "通俗易懂语体为主，专业术语保留并加注",
    "reason": "用户偏好面向大众的科普风格",
    "source": "memory/user_preferences.json"
  }
```

**若用户偏好未明确**：

```
步骤2（替代）：查询用户确认
  若 allow_human_confirmation = true → 生成确认请求，等待用户回复
  若 allow_human_confirmation = false → 采用保守默认值（正式语体），
                                        标记为 open_issue
```

### 3.4 判断冲突解决流程（judgment_conflict）

**原则**：裁决 Agent 介入。专业判断需要独立第三方裁决。

```
步骤1：识别冲突判断
  Agent A（逻辑审核）: "论证链条完整，逻辑严密"
  Agent B（内容审核）: "论证存在跳跃，第3段缺少过渡"
  → 冲突点：论证是否完整

步骤2：准备冲突材料
  提取冲突双方的核心论点与依据
  提取被审核内容的相关段落
  不包含全局上下文（遵循裁决最小上下文原则）

步骤3：提交裁决 Agent
  裁决 Agent 只接收：
  - 冲突描述（Agent A 和 Agent B 各自的结论与理由）
  - 被审核内容的相关段落（路径引用）
  - 裁决要求（"请判断论证是否完整，给出裁决理由"）

  裁决 Agent 不接收：
  - 整个任务的完整上下文
  - 其他 Agent 的输出
  - 全局历史记录

步骤4：裁决 Agent 做出裁定
  裁决 Agent 独立审视冲突材料，给出裁决：
  - 采信哪一方（或部分采信）
  - 裁决理由
  - 建议的修改方向

步骤5：记录解决方案
  冲突记录：
  {
    "type": "judgment_conflict",
    "issue": "论证完整性判断",
    "agent_a_view": "论证链条完整（逻辑审核Agent）",
    "agent_b_view": "第3段缺少过渡（内容审核Agent）",
    "arbiter": "arbiter_agent",
    "resolution": "部分采信Agent B，第3段确实缺少过渡",
    "reason": "经独立审视，第3段从'规模分析'直接跳到'区域差异'，缺少逻辑连接",
    "arbiter_context": "仅读取冲突描述和第3段内容"
  }
```

### 3.5 格式冲突解决流程（format_conflict）

**原则**：确定性规则优先。格式问题可以用规则解决，不需要 Agent。

```
步骤1：识别冲突格式
  Agent A: "标题编号用 一、二、三"
  Agent B: "标题编号用 1. 2. 3."
  → 冲突点：标题编号格式

步骤2：查询格式规则
  查询 config/style_guide.json → "title_numbering: chinese_ordinal"
  → 规则要求使用中文序数（一、二、三）

步骤3：应用确定性规则
  采信 Agent A 的格式（与规则一致）
  使用脚本统一所有标题编号格式

步骤4：记录解决方案
  冲突记录：
  {
    "type": "format_conflict",
    "format": "标题编号格式",
    "conflicting_formats": ["一、二、三", "1. 2. 3."],
    "resolution": "一、二、三",
    "reason": "config/style_guide.json 规定 title_numbering: chinese_ordinal",
    "method": "确定性规则，脚本统一处理"
  }
```

**若无明确格式规则**：

```
步骤2（替代）：采用约定默认值
  中文文档默认：一、二、三
  英文文档默认：1. 2. 3.
  标记为 open_issue，建议在 config/ 中补充格式规则
```

---

## 四、裁决 Agent 规范

### 4.1 裁决 Agent 的职责

裁决 Agent（Arbiter）是专门用于解决判断冲突的角色。其核心特征：

| 维度 | 规范 |
|------|------|
| 职责 | 仅负责在判断冲突中做出裁决，不负责执行裁决结果 |
| 输入 | 仅冲突内容（双方论点、相关材料路径），不含全局上下文 |
| 输出 | 裁决结论 + 裁决理由 + 建议修改方向 |
| 禁止 | 不得重新读取整个任务上下文；不得修改被裁决的内容；不得偏向任一方 |

### 4.2 裁决最小上下文原则

> **裁决 Agent 只读取冲突内容，不重新读取整个任务。**

这一原则的理由：

1. **效率**：重新读取整个任务上下文消耗大量 Token，且大部分信息与冲突无关
2. **公正**：裁决 Agent 不应受到全局上下文的影响，只基于冲突本身做判断
3. **聚焦**：裁决 Agent 的注意力应集中在冲突点上，而非分散到全局

```
裁决 Agent 接收的输入（最小上下文）：
{
  "conflict_type": "judgment_conflict",
  "issue": "论证完整性判断",
  "agent_a": {
    "name": "logic_reviewer",
    "conclusion": "论证链条完整",
    "reasoning": "各段落之间有逻辑连接词，因果关系清晰"
  },
  "agent_b": {
    "name": "content_reviewer",
    "conclusion": "第3段缺少过渡",
    "reasoning": "第3段从规模分析直接跳到区域差异，缺少逻辑连接"
  },
  "evidence_ref": "output/T2/draft.md#paragraph_3",
  "task": "请判断第3段的论证是否完整，给出裁决理由"
}

裁决 Agent 不接收：
  - 完整的 draft.md（只读取第3段）
  - 其他 Agent 的审核结果
  - 任务的完整上下文
  - 全部 Schema 和配置
```

### 4.3 裁决 Agent 的输出

```json
{
  "conflict_id": "conflict_001",
  "verdict": "partial_b",
  "conclusion": "部分采信 Agent B 的判断",
  "reasoning": "经独立审视第3段内容，从'2024年规模达55.2万亿'直接跳到'东部地区占比62%'，确实缺少从全国规模到区域差异的逻辑过渡。建议在第3段末尾增加一句过渡，如'总体规模的增长在区域间分布并不均衡'。",
  "suggested_fix": "在第3段末尾增加过渡句",
  "confidence": 0.85
}
```

---

## 五、冲突解决决策树

```
检测到冲突
    │
    ▼
是格式问题吗？────────── YES ──→ 查询格式规则 ──→ 有规则？── YES ──→ 应用规则
    │ NO                                                    │ NO
    │                                                       ▼
    │                                                  采用默认值
    │                                                  标记 open_issue
    ▼
是事实问题吗？────────── YES ──→ 能追溯原始证据？── YES ──→ 核对原始出处
    │ NO                          │ NO                    │
    │                             ▼                       ▼
    │                        降级为判断冲突          采信更可靠来源
    │                                                  （时效性/权威性）
    ▼
是偏好吗？────────────── YES ──→ 用户有明确指令？── YES ──→ 遵循用户指令
    │ NO                          │ NO
    │                             ▼
    │                        允许人工确认？── YES ──→ 请求用户确认
    │                             │ NO
    │                             ▼
    │                        采用保守默认值
    │                        标记 open_issue
    ▼
是专业判断吗？────────── YES ──→ 提交裁决 Agent ──→ 裁决最小上下文
    │                                          │
    │                                          ▼
    │                                     裁决结论 + 理由
    ▼
记录所有解决方案到 run_report.json
标记无法解决的为 open_issues
```

---

## 六、冲突记录格式

所有冲突及其解决方案必须记录在 `run_report.json` 的 `open_issues` 中（未解决的）或单独的冲突日志中（已解决的）：

```json
{
  "conflict_log": [
    {
      "conflict_id": "conflict_001",
      "type": "fact_conflict",
      "description": "2024年数字经济规模数据不一致",
      "conflicting_parties": [
        {"agent": "fact_extractor", "value": "53.9万亿", "source": "论文A"},
        {"agent": "fact_extractor", "value": "55.2万亿", "source": "论文B"}
      ],
      "resolution_method": "原始证据优先",
      "resolution": "采信55.2万亿",
      "reason": "论文B发布更晚，数据为修订值",
      "resolved": true,
      "resolved_by": "system_rule",
      "evidence_ref": ["output/T1/facts.json#F012", "output/T1/facts.json#F045"]
    },
    {
      "conflict_id": "conflict_002",
      "type": "judgment_conflict",
      "description": "论证完整性判断不一致",
      "conflicting_parties": [
        {"agent": "logic_reviewer", "conclusion": "论证完整"},
        {"agent": "content_reviewer", "conclusion": "第3段缺少过渡"}
      ],
      "resolution_method": "裁决Agent介入",
      "resolution": "部分采信content_reviewer",
      "reason": "第3段确实缺少逻辑过渡",
      "resolved": true,
      "resolved_by": "arbiter_agent",
      "arbiter_context": "仅读取冲突描述和第3段内容"
    }
  ]
}
```

---

## 七、冲突预防

### 7.1 预防优于解决

虽然冲突解决协议能处理已发生的冲突，但预防冲突更高效：

| 预防措施 | 说明 |
|----------|------|
| 统一术语表 | 所有 Agent 共享同一术语表，减少因术语理解不同导致的冲突 |
| 统一格式规则 | 在 config/style_guide.json 中明确所有格式规则 |
| 明确职责边界 | 通过 Agent 契约确保职责互斥，减少审核维度的重叠 |
| 用户偏好前置 | 在需求分析阶段明确用户偏好，减少偏好冲突 |
| 数据源标注 | 每个 Agent 的输出标注数据来源，便于冲突时追溯 |

### 7.2 冲突模式记忆

反复出现的同类冲突应被提取为记忆（通过 Memory Curator）：

```
观察：事实冲突中，"不同发布时间的同一指标"经常因数据修订而不一致
记忆候选：
{
  "type": "procedural",
  "content": "事实冲突解决时，若两个来源数据不一致，优先采信发布时间更晚的来源（可能是修订数据）",
  "scope": "fact_conflict_resolution",
  "status": "candidate"
}
```

经过多次验证后，该记忆可升级为 `approved`，被后续冲突解决流程自动引用。

---

## 八、冲突解决检查清单

- [ ] 所有冲突被正确分类（fact/preference/judgment/format）
- [ ] 事实冲突优先追溯原始证据
- [ ] 偏好冲突优先查询用户指令
- [ ] 判断冲突由裁决 Agent 介入
- [ ] 格式冲突优先应用确定性规则
- [ ] 裁决 Agent 只接收最小上下文（不读取整个任务）
- [ ] 所有冲突解决方案记录在冲突日志中
- [ ] 未解决的冲突标记为 open_issues
- [ ] 反复出现的冲突模式提取为记忆候选
