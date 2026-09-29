# 单元测试模板

> 本模板说明如何为单个 Agent 编写输入输出校验测试。
> 每个 Agent 应有对应的单元测试文件，验证其在给定输入下能否产出符合预期的输出。

---

## 一、单元测试目标

单元测试验证**单个 Agent** 的行为正确性：

1. **输入校验**：Agent 能否正确接收并解析输入数据。
2. **输出校验**：Agent 的输出是否符合预期的格式和内容。
3. **边界条件**：Agent 在边界输入（空输入、超长输入、异常格式）下的行为。
4. **完成条件**：Agent 是否正确判定自身任务完成。
5. **错误处理**：Agent 在输入异常时是否优雅降级而非崩溃。

---

## 二、测试文件结构

```
tests/
├── test_planner.py          # 规划师单元测试
├── test_researcher.py       # 研究员单元测试
├── test_writer.py           # 写作者单元测试
├── test_reviewer.py         # 审校员单元测试
├── test_fact_checker.py     # 事实核查员单元测试
└── test_fixtures/           # 测试数据
    ├── sample_input/        # 样例输入
    │   ├── planner_input.json
    │   ├── researcher_input.json
    │   └── writer_input.json
    ├── expected_output/     # 预期输出
    │   ├── planner_expected.json
    │   ├── researcher_expected.json
    │   └── writer_expected.json
    └── schemas/             # 输出 Schema
        ├── workflow_schema.json
        └── terminology_schema.json
```

---

## 三、测试用例编写规范

### 3.1 测试用例命名

```
test_<agent>_<场景>_<预期结果>
```

示例：
- `test_planner_normal_input_pass`
- `test_writer_empty_source_warning`
- `test_reviewer_critical_issue_retry`

### 3.2 测试用例结构（Arrange-Act-Assert）

```python
import json
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "test_fixtures"

class TestPlanner:
    """规划师单元测试"""

    def test_planner_normal_input_pass(self):
        """测试：正常输入 → 规划师应产出有效的 DAG"""
        # === Arrange（准备）===
        with open(FIXTURES_DIR / "sample_input" / "planner_input.json") as f:
            input_data = json.load(f)
        with open(FIXTURES_DIR / "expected_output" / "planner_expected.json") as f:
            expected = json.load(f)

        # === Act（执行）===
        result = run_agent("planner", input_data)

        # === Assert（断言）===
        assert result is not None, "规划师输出不应为None"
        assert "tasks" in result, "输出应包含tasks字段"
        assert len(result["tasks"]) > 0, "任务列表不应为空"
        assert len(result["tasks"]) <= 12, "任务数不应超过max_agents"
        assert validate_dag_no_cycles(result["tasks"]), "DAG不应有循环依赖"

    def test_planner_empty_requirements_warning(self):
        """测试：空需求输入 → 规划师应返回警告而非崩溃"""
        # === Arrange ===
        input_data = {"goal": "", "constraints": {}}

        # === Act ===
        result = run_agent("planner", input_data)

        # === Assert ===
        assert result is not None, "即使输入异常也不应崩溃"
        assert result.get("status") == "warning", "空需求应返回warning状态"
        assert "error_message" in result, "应包含错误说明"
```

---

## 四、各 Agent 的测试要点

### 4.1 规划师（Planner）测试要点

| 测试项 | 验证内容 | 通过条件 |
|--------|----------|----------|
| 正常规划 | 给定完整需求，产出有效 DAG | DAG 无循环、任务数 <= max_agents |
| 空需求 | 给定空需求 | 返回 warning，不崩溃 |
| 超大需求 | 需求涉及 50+ 子任务 | 自动降级，任务数 <= max_agents |
| 并行标注 | DAG 中可并行任务有 parallel_group | 所有无依赖任务同组 |
| Agent 分配 | 每个任务有 agent 字段 | 无空 agent 字段 |
| 上下文估算 | 每个任务有 context_estimate | 估算值 > 0 且 <= max_context_chars |

```python
class TestPlanner:
    def test_dag_no_cycles(self):
        """DAG 无循环依赖"""
        result = run_agent("planner", load_fixture("planner_input.json"))
        assert validate_dag_no_cycles(result["tasks"])

    def test_parallel_group_assignment(self):
        """无依赖任务应标注同一并行组"""
        result = run_agent("planner", load_fixture("planner_input.json"))
        independent_tasks = [t for t in result["tasks"] if not t["depends_on"]]
        groups = set(t["parallel_group"] for t in independent_tasks)
        assert len(groups) == 1, "无依赖任务应在同一并行组"

    def test_max_agents_constraint(self):
        """任务数不超过 max_agents"""
        result = run_agent("planner", load_fixture("large_input.json"))
        assert len(result["tasks"]) <= 12

    def test_context_estimate_present(self):
        """每个任务有上下文估算"""
        result = run_agent("planner", load_fixture("planner_input.json"))
        for task in result["tasks"]:
            assert "context_estimate" in task
            assert 0 < task["context_estimate"] <= 30000
```

### 4.2 研究员（Researcher）测试要点

| 测试项 | 验证内容 | 通过条件 |
|--------|----------|----------|
| 正常提取 | 给定文档，提取结构化信息 | 输出通过 Schema 校验 |
| 来源标注 | 每条信息有来源标注 | 来源字段非空 |
| 空文档 | 给定空文档 | 返回 warning，不崩溃 |
| 术语提取 | 提取专业术语 | 术语表覆盖频率 >= 3 的术语 |
| 冲突标记 | 矛盾信息标记冲突 | conflict_terms 非空时 resolution = pending |

```python
class TestResearcher:
    def test_source_annotation(self):
        """每条提取的信息有来源标注"""
        result = run_agent("researcher", load_fixture("researcher_input.json"))
        for item in result["extracted_data"]:
            assert "sources" in item
            assert len(item["sources"]) > 0, "每条信息必须有来源"

    def test_terminology_coverage(self):
        """术语表覆盖高频术语"""
        result = run_agent("researcher", load_fixture("researcher_input.json"))
        terms = result.get("terminology", [])
        high_freq_terms = [t for t in terms if t.get("frequency", 0) >= 3]
        assert len(high_freq_terms) > 0, "应提取高频术语"

    def test_conflict_marking(self):
        """矛盾术语标记为 pending"""
        result = run_agent("researcher", load_fixture("conflict_input.json"))
        conflicts = result.get("conflict_terms", [])
        for conflict in conflicts:
            assert conflict["resolution"] == "pending", "冲突术语不应自动裁决"
```

### 4.3 写作者（Writer）测试要点

| 测试项 | 验证内容 | 通过条件 |
|--------|----------|----------|
| 正常生成 | 给定素材，生成目标文本 | 输出非空、格式正确 |
| 术语一致 | 使用术语表翻译 | 术语一致率 >= 95% |
| 空素材 | 给定空素材 | 返回 warning，不崩溃 |
| 引用保留 | 保留源文本引用 | 引用保留率 = 100% |
| 分块处理 | 大输入分块生成 | 分块拼接后内容完整 |
| 自检报告 | 生成自检报告 | _selfcheck.json 存在且有效 |

```python
class TestWriter:
    def test_terminology_consistency(self):
        """术语翻译一致率 >= 95%"""
        result = run_agent("writer", load_fixture("writer_input.json"))
        terminology = load_fixture("terminology.json")
        consistency = calculate_terminology_consistency(result["output"], terminology)
        assert consistency >= 0.95

    def test_citation_preservation(self):
        """引用保留率 = 100%"""
        result = run_agent("writer", load_fixture("writer_input.json"))
        source = load_fixture("source_text.txt")
        preservation = calculate_citation_preservation(result["output"], source)
        assert preservation == 1.0

    def test_no_placeholder(self):
        """输出中无未处理占位符"""
        result = run_agent("writer", load_fixture("writer_input.json"))
        text = result["output"]
        assert "[TODO]" not in text
        assert "[MISSING]" not in text
        assert "[PLACEHOLDER]" not in text

    def test_selfcheck_generated(self):
        """自检报告存在且有效"""
        result = run_agent("writer", load_fixture("writer_input.json"))
        assert "selfcheck" in result
        assert result["selfcheck"]["overall_status"] in ["pass", "pass_with_warnings"]
```

### 4.4 审校员（Reviewer）测试要点

| 测试项 | 验证内容 | 通过条件 |
|--------|----------|----------|
| 正常审核 | 给定内容，产出审核报告 | 报告通过 Schema 校验 |
| 问题分级 | 问题有 severity 字段 | 每个问题为 critical/warning/info |
| 修改建议 | 每个问题有 suggestion | suggestion 非空 |
| 通过判定 | 无问题时 verdict = pass | verdict 正确 |
| 驳回判定 | 有 critical 时 verdict = retry | verdict 正确 |

```python
class TestReviewer:
    def test_issue_severity_valid(self):
        """问题分级合法"""
        result = run_agent("reviewer", load_fixture("reviewer_input.json"))
        for issue in result["issues"]:
            assert issue["severity"] in ["critical", "warning", "info"]

    def test_verdict_with_critical(self):
        """有critical问题时verdict为retry"""
        result = run_agent("reviewer", load_fixture("content_with_errors.json"))
        has_critical = any(i["severity"] == "critical" for i in result["issues"])
        if has_critical:
            assert result["verdict"] == "retry"

    def test_verdict_no_issues(self):
        """无问题时verdict为pass"""
        result = run_agent("reviewer", load_fixture("perfect_content.json"))
        if len(result["issues"]) == 0:
            assert result["verdict"] == "pass"

    def test_suggestion_present(self):
        """每个问题有修改建议"""
        result = run_agent("reviewer", load_fixture("reviewer_input.json"))
        for issue in result["issues"]:
            assert "suggestion" in issue
            assert len(issue["suggestion"]) > 0
```

### 4.5 事实核查员（Fact Checker）测试要点

| 测试项 | 验证内容 | 通过条件 |
|--------|----------|----------|
| 正常核查 | 给定内容，产出核查报告 | 报告通过 Schema 校验 |
| 数据错误 | 数字与源文本不符 | 标记为 critical |
| 引用验证 | 引用与源文本对照 | 引用准确率计算正确 |
| 置信度 | 无法验证的声明有置信度 | confidence 字段非空 |
| 核查覆盖 | 覆盖率 >= 90% | claims_checked / 总声明 >= 0.90 |

```python
class TestFactChecker:
    def test_data_error_detection(self):
        """数据错误被检测为critical"""
        result = run_agent("fact_checker", load_fixture("content_with_data_error.json"))
        data_errors = [i for i in result["issues"] if i["type"] == "data_error"]
        assert len(data_errors) > 0
        for error in data_errors:
            assert error["severity"] == "critical"

    def test_coverage_rate(self):
        """核查覆盖率 >= 90%"""
        result = run_agent("fact_checker", load_fixture("factcheck_input.json"))
        coverage = result["claims_checked"] / result.get("total_claims", result["claims_checked"])
        assert coverage >= 0.90

    def test_confidence_present(self):
        """每个问题有置信度"""
        result = run_agent("fact_checker", load_fixture("factcheck_input.json"))
        for issue in result["issues"]:
            assert "confidence" in issue
            assert issue["confidence"] in ["high", "medium", "low"]
```

---

## 五、边界条件测试

每个 Agent 都应测试以下边界条件：

```python
class TestBoundaryConditions:
    """所有 Agent 的边界条件测试"""

    def test_empty_input(self):
        """空输入：应返回 warning 而非崩溃"""
        for agent in ["planner", "researcher", "writer", "reviewer", "fact_checker"]:
            result = run_agent(agent, {})
            assert result is not None, f"{agent}不应在空输入时崩溃"
            assert result.get("status") in ["warning", "error"]

    def test_oversized_input(self):
        """超长输入：应触发分块或降级"""
        oversized = {"text": "x" * 50000}  # 超出 max_context_chars
        for agent in ["researcher", "writer"]:
            result = run_agent(agent, oversized)
            assert result is not None, f"{agent}不应在超长输入时崩溃"
            assert result.get("degradation_level") is not None, "应触发降级"

    def test_malformed_input(self):
        """格式错误输入：应返回 error 而非崩溃"""
        malformed = "this is not json"
        for agent in ["planner", "researcher", "writer"]:
            result = run_agent(agent, malformed)
            assert result is not None
            assert result.get("status") == "error"
```

---

## 六、运行测试

```bash
# 运行所有单元测试
pytest tests/ -v

# 运行特定 Agent 的测试
pytest tests/test_planner.py -v

# 运行边界条件测试
pytest tests/ -k "boundary" -v

# 生成测试覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

**测试通过标准：**
- 所有测试用例通过
- 测试覆盖率 >= 80%
- 无 critical 级别的测试失败
