# 四层质量检查体系

> **本文件定义了 Agent Factory 生成系统的质量保证框架。** 所有生成的多Agent系统必须通过四层质量检查才能交付。四层检查由不同角色执行，层层递进，从确定性结构检查到语义审核再到最终产物验收。

---

## 体系总览

```
产物产出
    │
    ▼
┌─────────────────────────────────────────┐
│ 第一层：确定性结构检查（自动/程序）       │
│ 文件存在 · JSON校验 · ID完整 · 数字一致  │
│ 空字段 · 重复检测                         │
└───────────────────┬─────────────────────┘
                    │ 通过
                    ▼
┌─────────────────────────────────────────┐
│ 第二层：领域Reviewer（Agent/语义）        │
│ 语言质量 · 逻辑一致性 · 专业准确性        │
│ 引用准确 · 风格合规                       │
└───────────────────┬─────────────────────┘
                    │ 通过
                    ▼
┌─────────────────────────────────────────┐
│ 第三层：冲突裁决（Agent/仅处理冲突）       │
│ Reviewer意见冲突 · 优先级裁决             │
│ 修改建议矛盾 · 方案权衡                   │
└───────────────────┬─────────────────────┘
                    │ 通过
                    ▼
┌─────────────────────────────────────────┐
│ 第四层：最终产物审核（Agent/全局视角）     │
│ 验收标准对照 · 整体质量评估               │
│ 交付就绪判定                              │
└─────────────────────────────────────────┘
```

### 四层对比

| 层级 | 执行者 | 性质 | 耗时 | Token消耗 | 可并行 |
|------|--------|------|------|----------|--------|
| 第一层 | 确定性程序 | 完全确定 | 极低 | 0 | 是 |
| 第二层 | 领域Reviewer Agent | 语义判断 | 中 | 中 | 是 |
| 第三层 | 冲突裁决Agent | 语义判断 | 低 | 低 | 否 |
| 第四层 | 最终审核Agent | 全局判断 | 中 | 中 | 否 |

---

## 第一层：确定性结构检查

### 定位

**完全由确定性程序执行，不消耗Token，结果100%可重复。** 这是质量检查的第一道关卡，拦截所有结构性错误。任何未通过第一层的产物都不会进入第二层。

### 检查项目

#### 1.1 文件存在性检查

| 检查项 | 说明 | 判定 |
|--------|------|------|
| 必需文件存在 | workflow.json中声明的所有输出文件必须存在 | 缺失 → error |
| Schema文件存在 | 每个Agent的输入输出Schema必须存在 | 缺失 → error |
| Agent定义存在 | agent_manifest.json中声明的每个Agent定义文件必须存在 | 缺失 → error |
| 配置文件存在 | 必需的配置文件必须存在 | 缺失 → error |

```python
def check_file_existence(workflow):
    """检查所有必需文件是否存在"""
    errors = []

    # 检查工作流中声明的输出文件
    for task in workflow["tasks"]:
        for output_path in task.get("output_scope", []):
            if not os.path.exists(output_path):
                errors.append({
                    "type": "missing_file",
                    "severity": "error",
                    "task_id": task["task_id"],
                    "file": output_path,
                    "message": f"输出文件不存在: {output_path}"
                })

    # 检查Agent定义文件
    manifest = load_json("agent_manifest.json")
    for agent in manifest["agents"]:
        def_path = f"agents/{agent['id']}.md"
        if not os.path.exists(def_path):
            errors.append({
                "type": "missing_agent_definition",
                "severity": "error",
                "agent_id": agent["id"],
                "message": f"Agent定义文件不存在: {def_path}"
            })

    return errors
```

#### 1.2 JSON合法性校验

| 检查项 | 说明 | 判定 |
|--------|------|------|
| JSON可解析 | 所有.json文件必须是合法JSON | 解析失败 → error |
| Schema一致性 | 所有JSON文件必须符合对应的Schema | 不符合 → error |
| 字段类型正确 | 字段类型必须与Schema定义一致 | 类型错误 → error |

```python
import json
import jsonschema

def check_json_validity(directory, schema_map):
    """校验所有JSON文件的合法性和Schema一致性"""
    errors = []

    for json_file in glob.glob(f"{directory}/**/*.json", recursive=True):
        # 1. JSON可解析性
        try:
            data = load_json(json_file)
        except json.JSONDecodeError as e:
            errors.append({
                "type": "json_parse_error",
                "severity": "error",
                "file": json_file,
                "message": str(e)
            })
            continue

        # 2. Schema一致性
        schema_path = schema_map.get(json_file)
        if schema_path:
            schema = load_json(schema_path)
            try:
                jsonschema.validate(instance=data, schema=schema)
            except jsonschema.ValidationError as e:
                errors.append({
                    "type": "schema_violation",
                    "severity": "error",
                    "file": json_file,
                    "path": list(e.absolute_path),
                    "message": e.message
                })

    return errors
```

#### 1.3 ID完整性检查

| 检查项 | 说明 | 判定 |
|--------|------|------|
| 任务ID唯一 | workflow.json中每个task_id必须唯一 | 重复 → error |
| 任务ID引用有效 | depends_on中引用的task_id必须存在 | 引用不存在 → error |
| Agent ID一致 | manifest中的agent_id与workflow中的agent引用一致 | 不一致 → error |
| Schema引用有效 | 所有引用的Schema路径必须存在 | 不存在 → error |

```python
def check_id_integrity(workflow, manifest):
    """检查ID的完整性和一致性"""
    errors = []

    # 收集所有任务ID
    task_ids = [t["task_id"] for t in workflow["tasks"]]
    
    # 1. 任务ID唯一性
    duplicates = find_duplicates(task_ids)
    for dup in duplicates:
        errors.append({
            "type": "duplicate_task_id",
            "severity": "error",
            "task_id": dup,
            "message": f"任务ID重复: {dup}"
        })

    # 2. 依赖引用有效性
    for task in workflow["tasks"]:
        for dep in task.get("depends_on", []):
            if dep not in task_ids:
                errors.append({
                    "type": "invalid_dependency",
                    "severity": "error",
                    "task_id": task["task_id"],
                    "dependency": dep,
                    "message": f"依赖的任务不存在: {dep}"
                })

    # 3. Agent ID一致性
    manifest_agent_ids = {a["id"] for a in manifest["agents"]}
    workflow_agent_refs = {t["agent"] for t in workflow["tasks"]
                          if t.get("type") != "program"}
    for agent_ref in workflow_agent_refs:
        if agent_ref not in manifest_agent_ids:
            errors.append({
                "type": "agent_id_mismatch",
                "severity": "error",
                "agent_id": agent_ref,
                "message": f"workflow引用的Agent不在manifest中: {agent_ref}"
            })

    return errors
```

#### 1.4 数字一致性检查

| 检查项 | 说明 | 判定 |
|--------|------|------|
| 源数据数字匹配 | 生成内容中的数字必须在源数据中找到对应 | 找不到 → warning |
| 数字格式一致 | 同一数字在不同位置的表述一致 | 不一致 → warning |
| 统计数字正确 | 汇总数、百分比等计算正确 | 计算错误 → error |

```python
import re

def check_number_consistency(source_file, generated_file):
    """核对生成内容中的数字是否与源数据一致"""
    errors = []

    source_text = read_file(source_file)
    generated_text = read_file(generated_file)

    # 提取所有数字（包括百分比、小数）
    source_numbers = set(re.findall(r'\d+\.?\d*%?', source_text))
    generated_numbers = set(re.findall(r'\d+\.?\d*%?', generated_text))

    # 检查生成内容中的数字是否都有来源
    for num in generated_numbers:
        if num not in source_numbers:
            # 排除明显的计算结果（如100%、总数等）
            if not is_likely_derived_number(num, source_numbers):
                errors.append({
                    "type": "unverified_number",
                    "severity": "warning",
                    "number": num,
                    "message": f"数字'{num}'在源数据中未找到对应，可能是虚构"
                })

    return errors

def is_likely_derived_number(num, source_numbers):
    """判断数字是否可能是从源数据计算得出的"""
    # 100%通常是归一化结果
    if num == "100%" or num == "100":
        return True
    # 检查是否是源数字的简单运算结果
    try:
        val = float(num.rstrip('%'))
        for src in source_numbers:
            src_val = float(src.rstrip('%'))
            # 检查加减乘除
            if abs(val - src_val) < 0.01: return True
            if src_val != 0 and abs(val / src_val) < 0.01: return True
    except ValueError:
        pass
    return False
```

#### 1.5 空字段检查

| 检查项 | 说明 | 判定 |
|--------|------|------|
| 必填字段非空 | Schema中required的字段不能为空/null | 空 → error |
| 关键内容非空 | 正文、标题等关键内容不能为空字符串 | 空 → error |
| 数组非空 | 应至少有1个元素的数组不能为空 | 空 → warning |

```python
def check_empty_fields(data, schema, path=""):
    """检查必填字段是否为空"""
    errors = []

    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    for field in required_fields:
        current_path = f"{path}.{field}" if path else field
        value = data.get(field)

        # 检查null
        if value is None:
            errors.append({
                "type": "null_required_field",
                "severity": "error",
                "field": current_path,
                "message": f"必填字段为null: {current_path}"
            })
        # 检查空字符串
        elif isinstance(value, str) and value.strip() == "":
            errors.append({
                "type": "empty_required_field",
                "severity": "error",
                "field": current_path,
                "message": f"必填字段为空字符串: {current_path}"
            })
        # 检查空数组
        elif isinstance(value, list) and len(value) == 0:
            errors.append({
                "type": "empty_required_array",
                "severity": "warning",
                "field": current_path,
                "message": f"必填数组为空: {current_path}"
            })

    return errors
```

#### 1.6 重复检测

| 检查项 | 说明 | 判定 |
|--------|------|------|
| 内容重复 | 同一文档内不应有大段重复内容 | 重复 → warning |
| 引用重复 | 引用列表中不应有重复引用 | 重复 → warning |
| Agent输出重复 | 不同Agent不应产出相同内容 | 重复 → warning |

```python
def check_duplicates(content):
    """检测内容中的重复段落"""
    errors = []
    paragraphs = content.split('\n\n')

    # 使用SimHash或简单的n-gram比对
    for i, para_a in enumerate(paragraphs):
        for j, para_b in enumerate(paragraphs):
            if i < j and similarity(para_a, para_b) > 0.85:
                errors.append({
                    "type": "duplicate_content",
                    "severity": "warning",
                    "location_a": f"段落{i+1}",
                    "location_b": f"段落{j+1}",
                    "similarity": similarity(para_a, para_b),
                    "message": f"段落{i+1}和段落{j+1}高度相似({similarity:.0%})"
                })

    return errors
```

### 第一层检查报告格式

```json
{
  "layer": 1,
  "name": "确定性结构检查",
  "executor": "program",
  "timestamp": "2026-07-27T10:00:00Z",
  "summary": {
    "total_checks": 247,
    "passed": 244,
    "errors": 1,
    "warnings": 2
  },
  "results": [
    {
      "type": "missing_file",
      "severity": "error",
      "task_id": "T3",
      "file": "output/T3/draft.md",
      "message": "输出文件不存在: output/T3/draft.md"
    },
    {
      "type": "unverified_number",
      "severity": "warning",
      "number": "53.9万亿",
      "message": "数字'53.9万亿'在源数据中未找到对应，可能是虚构"
    }
  ],
  "verdict": "FAIL",
  "blocking_errors": 1
}
```

---

## 第二层：领域Reviewer

### 定位

**由多个专业领域的Reviewer Agent并行执行语义层面的质量审核。** 每个Reviewer只关注自己的专业维度，给出专业判断。Reviewer之间可以并行，互不干扰。

### Reviewer类型

| Reviewer | 关注维度 | 输入 | 输出 |
|----------|----------|------|------|
| 语言审核Agent | 语法、用词、表达 | 待审文本路径 | 语言问题列表+修改建议 |
| 逻辑审核Agent | 论证逻辑、因果一致 | 待审文本路径 | 逻辑问题列表+修改建议 |
| 事实核查Agent | 数据准确性、引用正确 | 待审文本路径+源数据路径 | 事实问题列表 |
| 专业审核Agent | 专业领域准确性 | 待审文本路径+领域知识 | 专业问题列表 |
| 格式审核Agent | 格式规范、排版合规 | 待审文本路径+格式标准 | 格式问题列表 |

### Reviewer执行规则

```
1. 每个Reviewer只审核自己的专业维度，不越界
2. Reviewer的输入是文件路径（引用路径原则）
3. Reviewer的输出是结构化的问题列表，不是修改后的文档
4. Reviewer不直接修改文档，只提出问题和建议
5. 多个Reviewer可以并行执行
```

### Reviewer输出格式

```json
{
  "reviewer_id": "language_reviewer",
  "review_target": "output/T3/draft.md",
  "timestamp": "2026-07-27T10:05:00Z",
  "issues": [
    {
      "id": "ISS-001",
      "severity": "high",
      "category": "grammar",
      "location": "第3段第2句",
      "original": "通过数字化转型，企业效率提高了大约2倍左右。",
      "problem": "语义重复：'大约'和'左右'都表示约数，不应同时使用",
      "suggestion": "通过数字化转型，企业效率提高了大约2倍。"
    },
    {
      "id": "ISS-002",
      "severity": "medium",
      "category": "word_choice",
      "location": "第5段第1句",
      "original": "该政策对中小企业的影响很大。",
      "problem": "用词模糊：'很大'缺乏具体性",
      "suggestion": "该政策显著降低了中小企业的运营成本。"
    }
  ],
  "summary": {
    "total_issues": 2,
    "high": 1,
    "medium": 1,
    "low": 0,
    "overall_quality": "良好，存在少量语言问题"
  }
}
```

### 风险驱动审核策略

并非所有内容都需要全部Reviewer审核。根据风险等级选择审核力度：

| 风险等级 | 触发条件 | 审核策略 | Reviewer数量 |
|----------|----------|----------|-------------|
| 高风险 | 涉及数据/引用/公开发布/不可逆操作 | 全量审核 | 全部5个 |
| 中风险 | 普通文档/内部使用 | 标准审核 | 语言+逻辑+事实（3个） |
| 低风险 | 草稿/内部草稿/非正式 | 轻量审核 | 语言（1个） |

```python
def select_reviewers(risk_level):
    """根据风险等级选择Reviewer"""
    REVIEWER_SETS = {
        "high": ["language", "logic", "fact_check", "domain_expert", "format"],
        "medium": ["language", "logic", "fact_check"],
        "low": ["language"]
    }
    return REVIEWER_SETS.get(risk_level, REVIEWER_SETS["medium"])
```

### 风险等级判定

```python
def determine_risk_level(task, requirements):
    """判定任务的风险等级"""
    risk_score = 0

    # 涉及公开发布
    if requirements.get("will_publish", False):
        risk_score += 3

    # 涉及数据引用
    if task.get("contains_citations", False):
        risk_score += 2

    # 涉及数字/统计
    if task.get("contains_statistics", False):
        risk_score += 2

    # 涉及专业领域
    if task.get("domain_specific", False):
        risk_score += 1

    # 不可逆操作
    if task.get("irreversible", False):
        risk_score += 3

    if risk_score >= 5:
        return "high"
    elif risk_score >= 2:
        return "medium"
    else:
        return "low"
```

---

## 第三层：冲突裁决

### 定位

**只处理Reviewer之间的意见冲突，不重新审核。** 当多个Reviewer对同一内容给出矛盾的建议时，由冲突裁决Agent做出最终决定。

### 冲突类型

| 冲突类型 | 说明 | 示例 |
|----------|------|------|
| 修改建议矛盾 | 两个Reviewer对同一内容给出不同修改 | 语言审核要简化，专业审核要详细 |
| 严重度分歧 | 两个Reviewer对同一问题的严重度判断不同 | 语言审核认为是high，逻辑审核认为是low |
| 方案权衡 | 两个合理的修改方向互相排斥 | 保持简洁 vs 保持完整 |
| 优先级冲突 | 多个问题的修复顺序有依赖 | 先改逻辑还是先改语言 |

### 冲突裁决规则

```
裁决优先级（高→低）：
  1. 安全性 > 其他所有维度（安全问题优先修复）
  2. 事实准确性 > 语言美观性（事实错误比语言瑕疵更重要）
  3. 逻辑正确性 > 格式规范性（逻辑错误比格式问题更严重）
  4. 专业准确性 > 通用表达（专业术语以领域专家为准）
  5. 用户需求 > Reviewer偏好（用户要求优先于审核建议）
```

### 冲突裁决流程

```
┌─────────────────────────────────────┐
│ 收集所有Reviewer的issues            │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 按location分组：同一位置的issues归组 │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│ 对每组检测冲突：                     │
│ - 建议矛盾？                        │
│ - 严重度分歧？                      │
│ - 方案互斥？                        │
└──────────────────┬──────────────────┘
                   │
          ┌────────┴────────┐
         有冲突             无冲突
          │                  │
          ▼                  ▼
┌────────────────┐  ┌──────────────┐
│ 冲突裁决Agent   │  │ 直接汇总     │
│ 按优先级裁决    │  │ 无冲突的     │
└────────┬───────┘  │ issues       │
         │          └──────────────┘
         ▼
┌────────────────┐
│ 输出裁决结果    │
│ 包含最终修改   │
│ 建议和理由     │
└────────────────┘
```

### 冲突裁决示例

```json
{
  "arbitrator_id": "conflict_arbitrator",
  "conflicts_resolved": 2,
  "resolutions": [
    {
      "conflict_id": "CF-001",
      "location": "第3段第2句",
      "conflict_type": "suggestion_contradiction",
      "reviewer_a": {
        "id": "language_reviewer",
        "suggestion": "简化为：'效率提高2倍'",
        "reason": "语言简洁"
      },
      "reviewer_b": {
        "id": "domain_expert",
        "suggestion": "保持原文：'效率提高了大约2倍左右'",
        "reason": "'大约'和'左右'在专业语境中强调不确定性"
      },
      "resolution": "采纳reviewer_a的建议，简化为'效率提高2倍'",
      "reason": "语言简洁性原则优先。专业不确定性可通过上下文表达，不需要双重约数修饰。",
      "priority_rule": "语言准确性 > 专业修饰偏好"
    }
  ]
}
```

### 冲突裁决代码示例

```python
class ConflictArbitrator:
    """检测和裁决Reviewer之间的冲突"""

    PRIORITY = {
        "security": 5,
        "fact_accuracy": 4,
        "logic_correctness": 3,
        "domain_accuracy": 3,
        "language_quality": 2,
        "format_compliance": 1
    }

    def detect_conflicts(self, all_issues):
        """检测同一位置的冲突issues"""
        conflicts = []
        
        # 按位置分组
        by_location = {}
        for issue in all_issues:
            loc = issue.get("location", "unknown")
            by_location.setdefault(loc, []).append(issue)

        # 检测每组中的冲突
        for location, issues in by_location.items():
            if len(issues) > 1:
                conflict = self._analyze_conflict(location, issues)
                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def arbitrate(self, conflict):
        """裁决单个冲突"""
        # 按优先级排序reviewer意见
        ranked = sorted(
            conflict["issues"],
            key=lambda x: self.PRIORITY.get(x["category"], 0),
            reverse=True
        )
        
        # 最高优先级的意见胜出
        winner = ranked[0]
        
        return {
            "conflict_id": conflict["id"],
            "location": conflict["location"],
            "resolution": winner["suggestion"],
            "reason": f"优先级规则：{winner['category']} > 其他维度",
            "winner": winner["reviewer_id"],
            "loser": [r["reviewer_id"] for r in ranked[1:]]
        }
```

---

## 第四层：最终产物审核

### 定位

**全局视角的最终审核，对照验收标准判定产物是否可以交付。** 这是质量检查的最后一道关卡，由Integration Reviewer执行。

### 审核内容

| 审核项 | 说明 | 判定方式 |
|--------|------|----------|
| 验收标准对照 | 逐项检查acceptance_criteria | 自动+人工 |
| 整体质量评估 | 综合评价产物质量 | 人工判断 |
| 完整性检查 | 是否有遗漏的组成部分 | 程序检查 |
| 一致性检查 | 各部分之间是否一致 | 人工判断 |
| 交付就绪判定 | 是否可以交付给用户 | 人工最终判定 |

### 验收标准对照

```python
class AcceptanceChecker:
    """对照验收标准检查最终产物"""

    def check(self, product_path, criteria_path):
        """逐项检查验收标准"""
        criteria = load_json(criteria_path)
        results = []

        for criterion in criteria["criteria"]:
            result = self._check_criterion(criterion, product_path)
            results.append(result)

        return {
            "total": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
            "details": results,
            "verdict": "PASS" if all(r["passed"] for r in results) else "FAIL"
        }

    def _check_criterion(self, criterion, product_path):
        """检查单个验收标准"""
        if criterion["auto"]:
            # 自动可验证的标准
            return self._auto_check(criterion, product_path)
        else:
            # 需要人工判断的标准
            return {
                "id": criterion["id"],
                "description": criterion["description"],
                "passed": None,  # 待人工判定
                "method": "manual"
            }

    def _auto_check(self, criterion, product_path):
        """自动验证标准"""
        check_type = criterion.get("check_type")

        if check_type == "word_count":
            count = count_words(product_path)
            min_count = criterion.get("min", 0)
            return {
                "id": criterion["id"],
                "description": criterion["description"],
                "passed": count >= min_count,
                "actual": count,
                "expected": f">={min_count}"
            }

        elif check_type == "citation_accuracy":
            accuracy = check_citations(product_path)
            threshold = criterion.get("threshold", 0.95)
            return {
                "id": criterion["id"],
                "description": criterion["description"],
                "passed": accuracy >= threshold,
                "actual": f"{accuracy:.1%}",
                "expected": f">={threshold:.0%}"
            }

        elif check_type == "file_exists":
            return {
                "id": criterion["id"],
                "description": criterion["description"],
                "passed": os.path.exists(product_path),
                "actual": "exists" if os.path.exists(product_path) else "missing",
                "expected": "exists"
            }
```

### 最终审核报告

```json
{
  "layer": 4,
  "name": "最终产物审核",
  "executor": "integration_reviewer",
  "timestamp": "2026-07-27T10:30:00Z",
  "product": "output/final/report.docx",
  "acceptance_check": {
    "total": 8,
    "passed": 7,
    "failed": 1,
    "details": [
      {
        "id": "AC1",
        "description": "所有结构测试通过",
        "passed": true
      },
      {
        "id": "AC2",
        "description": "集成测试通过",
        "passed": true
      },
      {
        "id": "AC3",
        "description": "字数≥3000字",
        "passed": true,
        "actual": "3247字",
        "expected": ">=3000字"
      },
      {
        "id": "AC4",
        "description": "引用准确率≥95%",
        "passed": false,
        "actual": "92.3%",
        "expected": ">=95%",
        "gap": "2.7%",
        "recommendation": "核查第3段和第5段的引用来源"
      }
    ]
  },
  "quality_assessment": {
    "overall": "良好",
    "strengths": ["结构清晰", "论据充分", "语言流畅"],
    "weaknesses": ["部分引用不够准确"],
    "risk_level": "medium"
  },
  "verdict": "CONDITIONAL_PASS",
  "conditions": ["修复AC4的引用问题后可交付"],
  "delivery_ready": false
}
```

### 交付判定规则

| 判定结果 | 条件 | 后续动作 |
|----------|------|----------|
| PASS | 所有验收标准通过 | 交付 |
| CONDITIONAL_PASS | 非关键标准未通过 | 修复后交付 |
| FAIL | 关键标准未通过 | 回到生成阶段修复 |
| MANUAL_REVIEW | 存在人工判断项 | 等待人工确认 |

---

## 风险驱动审核

### 审核力度分级

```
高风险产物
  → 第一层：全部6项检查
  → 第二层：全部5个Reviewer
  → 第三层：冲突裁决（如有冲突）
  → 第四层：全量验收标准对照 + 人工确认

中风险产物
  → 第一层：全部6项检查
  → 第二层：3个Reviewer（语言+逻辑+事实）
  → 第三层：冲突裁决（如有冲突）
  → 第四层：自动验收标准对照

低风险产物
  → 第一层：全部6项检查
  → 第二层：1个Reviewer（语言）
  → 第三层：跳过（低风险不裁决）
  → 第四层：自动验收标准对照（仅关键标准）
```

### 风险驱动的Token节省

```
全量审核（高风险）：
  第一层：0 Token（程序）
  第二层：5 × 3000 = 15,000 Token
  第三层：2,000 Token
  第四层：3,000 Token
  总计：20,000 Token

风险审核（中风险）：
  第一层：0 Token
  第二层：3 × 3000 = 9,000 Token
  第三层：1,000 Token
  第四层：1,500 Token
  总计：11,500 Token

轻量审核（低风险）：
  第一层：0 Token
  第二层：1 × 3000 = 3,000 Token
  第三层：0 Token（跳过）
  第四层：500 Token
  总计：3,500 Token

节省：低风险比高风险节省82%
```

---

## 质量检查完整流程示例

```
产物：output/final/report.docx
风险等级：high（涉及公开发布和数据引用）

第一层（程序执行）：
  ✓ 文件存在性：通过
  ✓ JSON合法性：通过
  ✓ ID完整性：通过
  ⚠ 数字一致性：2个数字未在源数据中找到（warning）
  ✓ 空字段检查：通过
  ⚠ 重复检测：1处段落重复（warning）
  → 结果：PASS（warnings不阻塞）

第二层（5个Reviewer并行）：
  语言审核：发现3个语言问题（1 high, 2 medium）
  逻辑审核：发现1个逻辑问题（1 high）
  事实核查：发现2个引用问题（2 high）
  专业审核：通过
  格式审核：发现1个格式问题（1 low）
  → 结果：PASS（有issues但不阻塞，进入第三层）

第三层（冲突裁决）：
  检测到1个冲突：
    事实核查建议修改第3段数据
    语言审核建议保持原表述（语言更流畅）
  裁决：采纳事实核查建议（事实准确性 > 语言流畅性）
  → 结果：PASS

第四层（最终审核）：
  验收标准对照：
    AC1 结构测试通过 ✓
    AC2 字数≥3000 ✓（实际3247）
    AC3 引用准确率≥95% ✗（实际92.3%）
    AC4 逻辑连贯 ✓
  → 结果：CONDITIONAL_PASS
  → 条件：修复引用准确率后可交付
```

---

## 质量检查输出清单

生成的多Agent系统必须包含以下质量检查文件：

```
generated_system/
├── reports/
│   ├── quality_report.json        ← 综合质量报告
│   ├── layer1_structure.json      ← 第一层检查结果
│   ├── layer2_reviews/
│   │   ├── language_review.json   ← 语言审核结果
│   │   ├── logic_review.json      ← 逻辑审核结果
│   │   ├── fact_check.json        ← 事实核查结果
│   │   ├── domain_review.json     ← 专业审核结果
│   │   └── format_review.json     ← 格式审核结果
│   ├── layer3_arbitration.json    ← 第三层裁决结果
│   └── layer4_final.json          ← 第四层最终审核
├── acceptance_criteria.json       ← 验收标准
└── tests/                         ← 测试文件
    ├── test_structure.py
    ├── test_unit.py
    └── test_integration.py
```
