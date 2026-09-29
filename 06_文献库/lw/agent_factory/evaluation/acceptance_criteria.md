# 验收标准框架

> 本文件定义 Agent Factory 生成的多 Agent 系统的验收标准。
> 用于判定系统执行结果是否"完成"、"部分完成"或"失败"。

---

## 一、完成与失败的定义

### 完成（PASS）

系统执行结果满足以下**全部**条件时，判定为"完成"：

1. 所有输出文件已生成并写入指定路径。
2. 输出文件通过对应的 JSON Schema / 格式校验。
3. 无 critical 级别的未解决问题。
4. 核心验收指标达到阈值（见第四节）。
5. 执行报告已生成。

### 部分完成（PARTIAL）

系统执行结果满足以下条件时，判定为"部分完成"：

1. 核心输出已生成，但存在 warning 级别问题。
2. 部分非关键任务被降级跳过（如 fact_checker 被跳过）。
3. 核心验收指标达到最低阈值但未达到目标阈值。
4. 输出文件完整但质量略低于预期。

**部分完成允许交付**，但需在执行报告中明确标注降级情况和 warning 问题。

### 失败（FAIL）

系统执行结果出现以下**任一**情况时，判定为"失败"：

1. 核心输出文件未生成或为空。
2. 存在 critical 级别的未解决问题且重试次数已耗尽。
3. 核心验收指标低于最低阈值。
4. 系统执行过程中发生不可恢复的错误。
5. 输出文件未通过格式校验且无法自动修复。

---

## 二、错误分级

### Critical（严重 — 必须解决）

| 错误类型 | 说明 | 影响 |
|----------|------|------|
| 内容缺失 | 源文本中的段落/章节在输出中缺失 | 信息不完整，不可交付 |
| 数据错误 | 数字、日期、统计值与源文本不符 | 事实性错误，误导读者 |
| 术语严重不一致 | 同一术语在全文有两种以上翻译 | 专业性受损 |
| 引用丢失 | 引用编号、图表引用在输出中缺失 | 学术规范违规 |
| 格式损坏 | 输出文件无法打开或格式严重错误 | 不可用 |
| 系统崩溃 | Agent 执行过程中不可恢复的异常 | 系统不可用 |

### Warning（警告 — 建议解决）

| 错误类型 | 说明 | 影响 |
|----------|------|------|
| 轻微术语不一致 | 个别术语有1-2处不一致 | 可读性降低 |
| 格式不规范 | 标题层级、列表格式有轻微问题 | 可读性降低 |
| 表达生硬 | 个别句子翻译不够通顺 | 可读性降低 |
| 术语待定 | 冲突术语未裁定，标注了[术语待定] | 需人工后续处理 |
| 非关键Agent跳过 | fact_checker 等非关键Agent被降级跳过 | 质量保障降低 |

### Info（提示 — 仅记录）

| 错误类型 | 说明 | 影响 |
|----------|------|------|
| 风格建议 | 语言风格可优化的建议 | 无实质影响 |
| 格式优化 | 格式可进一步美化的建议 | 无实质影响 |
| 冗余信息 | 存在可精简的冗余表达 | 无实质影响 |

---

## 三、输出文件必须满足的条件

### 通用条件（所有输出文件）

1. **存在性**：文件已创建且非空。
2. **可读性**：文件可被对应工具正常读取（JSON 可解析、Markdown 可渲染、DOCX 可打开）。
3. **编码**：文件使用 UTF-8 编码。
4. **命名**：文件名符合命名规范（无空格、无特殊字符）。
5. **路径**：文件位于指定的输出目录中。

### 翻译类输出额外条件

1. **完整性**：源文本的所有段落均在译文中有对应翻译。
2. **术语一致**：术语表中的术语在全文翻译一致率 >= 95%。
3. **引用保留**：引用编号保留率 = 100%。
4. **字数比例**：译文字数 / 源文字数在 0.8-1.5 倍范围内。
5. **无占位符**：译文中无未处理的 [TODO]、[MISSING] 等占位符。

### 研究报告类输出额外条件

1. **来源标注**：每条关键论断有来源标注。
2. **冲突透明**：来源间的信息冲突已明确标注。
3. **结构完整**：报告包含引言、方法、发现、结论等必要章节。
4. **数据准确**：报告中引用的数据与原始来源一致。

---

## 四、准确率评估方式

### 术语一致性率

```
术语一致性率 = (术语表中术语在全文使用正确翻译的次数) / (术语在全文出现的总次数)
```

- **目标阈值**：>= 95%
- **最低阈值**：>= 90%（低于此值为 FAIL）

### 段落完整率

```
段落完整率 = (译文中存在的源文本段落数) / (源文本总段落数)
```

- **目标阈值**：= 100%
- **最低阈值**：>= 98%（低于此值为 FAIL）

### 引用保留率

```
引用保留率 = (译文中保留的引用数) / (源文本中的引用总数)
```

- **目标阈值**：= 100%
- **最低阈值**：= 100%（任何引用丢失均为 FAIL）

### 数据准确率

```
数据准确率 = (翻译正确的数据项数) / (源文本中的数据项总数)
```

- **目标阈值**：= 100%
- **最低阈值**：>= 99%（低于此值为 FAIL）

### 事实核查覆盖率

```
事实核查覆盖率 = (已核查的可验证声明数) / (可验证声明总数)
```

- **目标阈值**：>= 95%
- **最低阈值**：>= 85%（低于此值为 WARNING）

---

## 五、是否允许部分结果

### 允许部分结果的情况

| 情况 | 允许的部分结果 | 必须标注 |
|------|----------------|----------|
| 批量处理中部分文档失败 | 成功文档的翻译结果 | 标注失败文档列表与失败原因 |
| 某分块翻译反复失败 | 其他分块的翻译结果 | 标注失败分块位置，占位符标注[翻译失败] |
| 非关键Agent被降级跳过 | 跳过Agent后的输出 | 标注跳过的Agent与降级原因 |
| 术语冲突未裁定 | 含[术语待定]标注的译文 | 标注待定术语列表 |

### 不允许部分结果的情况

| 情况 | 原因 |
|------|------|
| 单篇文档核心章节翻译失败 | 核心内容缺失不可交付 |
| 输出格式损坏 | 文件不可用 |
| 数据错误未修正 | 事实性错误不可交付 |

---

## 六、验收标准模板（JSON 格式）

以下模板可在 `requirements.json` 中使用，定义具体任务的验收标准。

```json
{
  "acceptance_criteria": {
    "verdict_rules": {
      "pass": "无critical问题且所有指标达到目标阈值",
      "partial": "无critical问题但存在warning或指标在最低-目标阈值之间",
      "fail": "存在critical问题或指标低于最低阈值"
    },
    "metrics": [
      {
        "name": "terminology_consistency_rate",
        "description": "术语一致性率",
        "target_threshold": 0.95,
        "minimum_threshold": 0.90,
        "calculation": "正确翻译次数 / 术语出现总次数",
        "fail_below_minimum": true
      },
      {
        "name": "paragraph_completeness_rate",
        "description": "段落完整率",
        "target_threshold": 1.00,
        "minimum_threshold": 0.98,
        "calculation": "已翻译段落数 / 源文本总段落数",
        "fail_below_minimum": true
      },
      {
        "name": "citation_preservation_rate",
        "description": "引用保留率",
        "target_threshold": 1.00,
        "minimum_threshold": 1.00,
        "calculation": "保留引用数 / 源文本引用总数",
        "fail_below_minimum": true
      },
      {
        "name": "data_accuracy_rate",
        "description": "数据准确率",
        "target_threshold": 1.00,
        "minimum_threshold": 0.99,
        "calculation": "正确数据项数 / 数据项总数",
        "fail_below_minimum": true
      },
      {
        "name": "fact_check_coverage_rate",
        "description": "事实核查覆盖率",
        "target_threshold": 0.95,
        "minimum_threshold": 0.85,
        "calculation": "已核查声明数 / 可验证声明总数",
        "fail_below_minimum": false
      }
    ],
    "critical_error_types": [
      "missing_content",
      "data_error",
      "terminology_severe_inconsistency",
      "citation_loss",
      "format_corruption",
      "system_crash"
    ],
    "warning_error_types": [
      "minor_terminology_inconsistency",
      "format_nonstandard",
      "awkward_expression",
      "unresolved_term_conflict",
      "non_critical_agent_skipped"
    ],
    "partial_result_allowed": true,
    "partial_result_conditions": [
      "批量处理中部分文档失败时，成功文档可交付",
      "非关键Agent降级跳过时，输出可交付但需标注",
      "术语冲突未裁定时，含标注的译文可交付"
    ]
  }
}
```

---

## 七、验收流程

```
系统执行完成
    │
    ▼
┌─────────────────┐
│ 1. 文件存在性检查 │  → 失败 → FAIL
└────────┬────────┘
         │ 通过
         ▼
┌─────────────────┐
│ 2. 格式校验      │  → 失败 → 尝试自动修复 → 仍失败 → FAIL
└────────┬────────┘
         │ 通过
         ▼
┌─────────────────┐
│ 3. 指标计算      │  → 计算所有 metrics
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 阈值判定      │  → 任一 fail_below_minimum 指标低于最低阈值 → FAIL
└────────┬────────┘         │ 所有指标 >= 最低阈值
         │                   │
         ▼                   ▼
┌─────────────────┐   ┌─────────────┐
│ 5. 问题分级检查  │   │  PARTIAL     │
└────────┬────────┘   └─────────────┘
         │
    有critical? ──是──→ FAIL
         │ 否
    有warning? ──是──→ PARTIAL
         │ 否
         ▼
    所有指标达标? ──是──→ PASS
         │ 否
         ▼
       PARTIAL
```

---

## 八、示例

### 示例 1：翻译任务验收

```json
{
  "task_id": "translation_001",
  "verdict": "PASS",
  "metrics": {
    "terminology_consistency_rate": {"value": 0.97, "target": 0.95, "status": "pass"},
    "paragraph_completeness_rate": {"value": 1.00, "target": 1.00, "status": "pass"},
    "citation_preservation_rate": {"value": 1.00, "target": 1.00, "status": "pass"},
    "data_accuracy_rate": {"value": 1.00, "target": 1.00, "status": "pass"},
    "fact_check_coverage_rate": {"value": 0.93, "target": 0.95, "status": "warning"}
  },
  "critical_issues": [],
  "warning_issues": [
    {"id": "W-001", "type": "fact_check_coverage_below_target", "detail": "事实核查覆盖率93%，低于目标95%但高于最低85%"}
  ],
  "summary": "所有critical指标达标，1个warning，判定为PASS"
}
```

### 示例 2：批量翻译部分失败

```json
{
  "task_id": "batch_translation_001",
  "verdict": "PARTIAL",
  "total_documents": 20,
  "successful_documents": 18,
  "failed_documents": [
    {"file": "paper_07.pdf", "reason": "PDF解析失败，无法提取文本"},
    {"file": "paper_15.pdf", "reason": "翻译重试次数耗尽，术语冲突过多"}
  ],
  "metrics": {
    "terminology_consistency_rate": {"value": 0.96, "target": 0.95, "status": "pass"},
    "paragraph_completeness_rate": {"value": 1.00, "target": 1.00, "status": "pass"}
  },
  "summary": "20篇中18篇成功翻译，2篇失败，成功部分质量达标，判定为PARTIAL"
}
```
