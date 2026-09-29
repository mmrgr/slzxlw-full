# 记忆系统说明 — 去AI味系统

> 本目录是去AI味系统的记忆系统。系统在每次处理文本后会自动更新记忆文件，记录哪些修改策略有效、哪些无效、遇到过的AI味模式以及用户偏好，使系统越用越精准。

---

## 文件清单与用途

| 文件 | 初始状态 | 用途 |
|------|----------|------|
| `effective_strategies.json` | 空数组 `[]` | 记录有效的修改策略。每条记录包含：策略名称、适用文体、针对的AI味特征类别、使用的人性化技术、AI率下降幅度、使用次数。检测到策略使AI率下降≥0.05时自动写入。 |
| `failed_strategies.json` | 空数组 `[]` | 记录失败的修改策略。每条记录包含：策略名称、适用文体、失败原因（AI率不降反升/文本质量下降/过度修改）、具体表现。避免后续重复使用无效策略。 |
| `text_patterns.json` | 空数组 `[]` | 记录遇到过的AI味模式。每条记录包含：模式名称、特征类别、典型表现、出现频率、有效应对策略。AI特征检测员参考历史模式提高检测准确度。 |
| `user_preferences.json` | 空对象 `{}` | 记录用户偏好。包含版本号、最后更新时间和偏好键值对。例如"不要加个人经历""保留所有引用""修改密度偏保守"等。 |

---

## 更新规则

### effective_strategies.json

**触发时机**：每次处理完成后，质量把控师评估修改策略效果。

**写入条件**：某策略使AI率下降幅度≥0.05。

**记录格式**：
```json
{
  "strategy_name": "案例先行法替代三明治结构",
  "text_type": "academic_paper",
  "feature_category": "structural",
  "technique": "T1-案例先行法",
  "ai_rate_before": 0.75,
  "ai_rate_after": 0.20,
  "improvement": 0.55,
  "usage_count": 1,
  "last_used": "2026-08-04",
  "notes": "对学术论文开头段落效果显著"
}
```

**容量限制**：最多保留200条记录。超限时按improvement降序保留Top 200。

### failed_strategies.json

**触发时机**：修改后AI率不降反升，或文本质量明显下降。

**记录格式**：
```json
{
  "strategy_name": "过度碎片化句式",
  "text_type": "academic_paper",
  "failure_reason": "文本质量下降",
  "description": "学术论文中过多碎片化句子导致可读性严重下降",
  "ai_rate_before": 0.45,
  "ai_rate_after": 0.50,
  "recorded_at": "2026-08-04"
}
```

### text_patterns.json

**触发时机**：AI特征检测员发现新的、未记录的AI味模式。

**记录格式**：
```json
{
  "pattern_name": "AI式情感两分法",
  "category": "emotional",
  "typical_expression": "一方面让人感到X，另一方面也带来了Y",
  "detection_frequency": 3,
  "effective_counter": "改用具体情感反应+感官细节",
  "first_seen": "2026-08-04",
  "last_seen": "2026-08-04"
}
```

### user_preferences.json

**触发时机**：用户明确表达偏好，或系统从交互中推断出偏好。

**记录格式**：
```json
{
  "version": "1.0",
  "last_updated": "2026-08-04",
  "preferences": {
    "no_personal_experience": true,
    "preserve_all_citations": true,
    "modification_density": "conservative",
    "preferred_text_type": "academic_paper"
  }
}
```

---

## 记忆使用方式

| Agent | 使用的记忆文件 | 使用方式 |
|-------|---------------|----------|
| AI特征检测员 | `text_patterns.json` | 参考历史模式提高检测准确度，识别已知AI味模式 |
| 结构重组师 | `effective_strategies.json` | 参考有效策略优先使用，参考`failed_strategies.json`避免无效策略 |
| 语言人性化师 | `effective_strategies.json` | 同上，优先使用对词汇/句式修改有效的策略 |
| 逻辑深化师 | `effective_strategies.json` | 同上，优先使用对逻辑修改有效的策略 |
| 检测模拟员 | `text_patterns.json` | 参考历史数据校准评分，对比已知模式判断风险 |
| 质量把控师 | `failed_strategies.json` | 参考失败策略避免重复犯错，检查是否触发已知失败模式 |

---

## 注意事项

1. **不删除用户偏好**：`user_preferences.json` 中的偏好记录除非用户明确要求，否则不删除。
2. **版本管理**：`user_preferences.json` 更新时递增version字段，保留last_updated时间戳。
3. **初始为空**：首次运行时所有记忆文件为空，系统完全依赖知识库执行。随着使用积累，记忆系统逐渐提升检测精度与修改效率。
4. **自动保存**：`config/system_config.yaml` 中 `memory.auto_save: true`，每次处理后自动更新记忆文件，无需手动触发。
