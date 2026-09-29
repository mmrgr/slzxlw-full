# 集成测试模板

> 本模板说明如何测试 Agent 间的数据传递与协作。
> 集成测试验证多个 Agent 组合在一起时，数据能否正确流转、DAG 能否正确执行。

---

## 一、集成测试目标

集成测试验证**Agent 间协作**的正确性：

1. **数据传递**：上游 Agent 的输出能否被下游 Agent 正确接收和解析。
2. **DAG 执行**：编排器能否按依赖关系正确调度任务。
3. **并行正确性**：并行任务的结果能否正确合并。
4. **重试流程**：审核驳回后，重试流程能否正确触发和执行。
5. **降级正确性**：触发降级时，系统能否正确切换策略。
6. **端到端**：从用户输入到最终输出的完整流程是否正确。

---

## 二、测试文件结构

```
tests/
├── test_integration.py          # 集成测试主文件
├── test_fixtures/
│   ├── integration_input/       # 集成测试输入
│   │   ├── full_pipeline_input.json
│   │   └── batch_input.json
│   ├── integration_expected/    # 集成测试预期输出
│   │   └── full_pipeline_expected.json
│   └── mock_agents/             # 模拟 Agent（用于隔离测试）
│       ├── mock_planner.py
│       └── mock_writer.py
```

---

## 三、测试场景

### 3.1 端到端管线测试

验证从用户输入到最终输出的完整流程。

```python
import json
import pytest
from pathlib import Path
from src.orchestrator import Orchestrator

FIXTURES_DIR = Path(__file__).parent / "test_fixtures"

class TestEndToEnd:
    """端到端管线测试"""

    def test_full_translation_pipeline(self):
        """测试：完整翻译管线（规划→术语提取→翻译→审核→交付）"""
        # === Arrange ===
        with open(FIXTURES_DIR / "integration_input" / "full_pipeline_input.json") as f:
            user_input = json.load(f)

        # === Act ===
        orchestrator = Orchestrator(mode="standard")
        result = orchestrator.run(user_input)

        # === Assert ===
        # 1. 最终输出文件已生成
        assert result["output_file"] is not None
        assert Path(result["output_file"]).exists()

        # 2. 所有任务已执行
        assert len(result["executed_tasks"]) > 0
        task_ids = {t["id"] for t in result["executed_tasks"]}
        assert "T0" in task_ids  # 规划
        assert "T1" in task_ids  # 术语提取
        assert any(tid.startswith("T2") for tid in task_ids)  # 翻译
        assert "T6" in task_ids or "T4" in task_ids  # 审核

        # 3. 最终 verdict 为 pass 或 partial
        assert result["verdict"] in ["pass", "partial"]

        # 4. 执行报告已生成
        assert Path(result["report_file"]).exists()

    def test_full_research_pipeline(self):
        """测试：完整研究分析管线"""
        user_input = load_fixture("research_pipeline_input.json")
        orchestrator = Orchestrator(mode="standard")
        result = orchestrator.run(user_input)

        assert result["verdict"] in ["pass", "partial"]
        assert result["output_file"] is not None
```

### 3.2 数据传递测试

验证上游 Agent 的输出能被下游 Agent 正确接收。

```python
class TestDataPassing:
    """Agent 间数据传递测试"""

    def test_planner_to_researcher(self):
        """测试：planner 输出 → researcher 输入"""
        # === Arrange ===
        planner_output = run_agent("planner", load_fixture("planner_input.json"))

        # === Act ===
        # 提取 planner 输出中给 researcher 的任务
        researcher_tasks = [
            t for t in planner_output["tasks"] if t["agent"] == "researcher"
        ]
        researcher_input = {
            "task": researcher_tasks[0],
            "sources": load_fixture("source_files.json")
        }
        researcher_output = run_agent("researcher", researcher_input)

        # === Assert ===
        # researcher 能正确解析 planner 的任务描述
        assert researcher_output is not None
        assert "extracted_data" in researcher_output
        assert len(researcher_output["extracted_data"]) > 0

    def test_researcher_to_writer(self):
        """测试：researcher 输出 → writer 输入"""
        # === Arrange ===
        researcher_output = run_agent("researcher", load_fixture("researcher_input.json"))

        # === Act ===
        writer_input = {
            "task": load_fixture("writer_task.json"),
            "research_data": researcher_output["extracted_data"],
            "terminology": researcher_output.get("terminology", [])
        }
        writer_output = run_agent("writer", writer_input)

        # === Assert ===
        # writer 能正确使用 researcher 提供的素材和术语表
        assert writer_output is not None
        assert len(writer_output["output"]) > 0

        # 验证 writer 使用了 researcher 的术语表
        for term in researcher_output.get("terminology", [])[:5]:
            if term["frequency"] >= 3:
                assert term["target"] in writer_output["output"], \
                    f"术语'{term['source']}'的翻译'{term['target']}'应出现在输出中"

    def test_writer_to_reviewer(self):
        """测试：writer 输出 → reviewer 输入"""
        # === Arrange ===
        writer_output = run_agent("writer", load_fixture("writer_input.json"))

        # === Act ===
        reviewer_input = {
            "content": writer_output["output"],
            "source": load_fixture("source_text.txt"),
            "terminology": load_fixture("terminology.json"),
            "acceptance_criteria": load_fixture("acceptance_criteria.json")
        }
        reviewer_output = run_agent("reviewer", reviewer_input)

        # === Assert ===
        # reviewer 能正确接收 writer 的输出并审核
        assert reviewer_output is not None
        assert "verdict" in reviewer_output
        assert "issues" in reviewer_output

    def test_reviewer_to_writer_retry(self):
        """测试：reviewer 驳回 → writer 重试"""
        # === Arrange ===
        writer_output = run_agent("writer", load_fixture("writer_input.json"))
        reviewer_output = run_agent("reviewer", {
            "content": writer_output["output"],
            "source": load_fixture("source_text.txt"),
            "acceptance_criteria": load_fixture("strict_criteria.json")
        })

        # 假设 reviewer 驳回
        if reviewer_output["verdict"] == "retry":
            # === Act ===
            retry_input = {
                **load_fixture("writer_input.json"),
                "review_feedback": reviewer_output["issues"],
                "previous_output": writer_output["output"]
            }
            retry_output = run_agent("writer", retry_input)

            # === Assert ===
            # writer 根据 reviewer 的反馈修正了问题
            for issue in reviewer_output["issues"]:
                if issue["severity"] == "critical":
                    assert issue_resolved(retry_output["output"], issue), \
                        f"critical问题{issue['id']}应已被修正"
```

### 3.3 DAG 执行顺序测试

验证编排器按依赖关系正确调度任务。

```python
class TestDAGExecution:
    """DAG 执行顺序测试"""

    def test_dependency_order(self):
        """测试：任务按依赖顺序执行"""
        orchestrator = Orchestrator(mode="standard")
        result = orchestrator.run(load_fixture("pipeline_input.json"))

        # 获取任务执行顺序（按完成时间排序）
        executed = sorted(result["executed_tasks"], key=lambda t: t["completed_at"])

        # 验证依赖顺序：每个任务的依赖必须先完成
        for task in executed:
            for dep_id in task.get("depends_on", []):
                dep = next(t for t in executed if t["id"] == dep_id)
                assert dep["completed_at"] <= task["started_at"], \
                    f"任务{task['id']}的依赖{dep_id}必须先完成"

    def test_parallel_execution(self):
        """测试：无依赖任务并行执行"""
        orchestrator = Orchestrator(mode="standard")
        result = orchestrator.run(load_fixture("parallel_input.json"))

        # 找到同一 parallel_group 的任务
        parallel_groups = {}
        for task in result["executed_tasks"]:
            group = task.get("parallel_group")
            if group:
                parallel_groups.setdefault(group, []).append(task)

        # 验证同组任务的时间有重叠（并行执行）
        for group_id, tasks in parallel_groups.items():
            if len(tasks) > 1:
                # 检查是否有时间重叠
                tasks_sorted = sorted(tasks, key=lambda t: t["started_at"])
                first_end = tasks_sorted[0]["completed_at"]
                second_start = tasks_sorted[1]["started_at"]
                # 第二个任务应在第一个任务完成前开始（并行）
                # 或者至少不严格串行（允许调度间隙）
                assert second_start <= first_end + 1, \
                    f"并行组{group_id}的任务应有执行时间重叠"

    def test_no_deadlock(self):
        """测试：DAG 无死锁（所有任务最终都执行完成）"""
        orchestrator = Orchestrator(mode="standard")
        result = orchestrator.run(load_fixture("complex_dag_input.json"))

        planned_tasks = set(t["id"] for t in result["workflow"]["tasks"])
        executed_tasks = set(t["id"] for t in result["executed_tasks"])
        skipped_tasks = set(t.get("skipped", []) for t in [result])

        # 所有计划的任务要么执行了，要么被降级跳过
        unaccounted = planned_tasks - executed_tasks - skipped_tasks
        assert len(unaccounted) == 0, \
            f"以下任务既未执行也未跳过：{unaccounted}（可能死锁）"
```

### 3.4 重试流程测试

```python
class TestRetryFlow:
    """重试流程测试"""

    def test_retry_on_critical(self):
        """测试：critical问题触发重试"""
        # 使用故意有错误的输入
        result = run_pipeline(load_fixture("input_with_errors.json"))

        # 验证触发了重试
        assert result["retry_count"] > 0, "应触发至少1次重试"

        # 验证重试后问题被修正
        if result["verdict"] == "pass":
            assert result["retry_count"] <= 2, "重试次数不应超过max_retries"

    def test_retry_limit(self):
        """测试：重试次数达上限后标记失败"""
        # 使用无法修复的错误输入
        result = run_pipeline(load_fixture("unfixable_input.json"))

        if result["verdict"] == "fail":
            assert result["retry_count"] == 2, "应在2次重试后标记失败"

    def test_partial_retry(self):
        """测试：仅重试有问题的分块"""
        result = run_pipeline(load_fixture("multi_chunk_input.json"))

        # 验证只有有问题的分块被重试
        retried_chunks = result.get("retried_chunks", [])
        all_chunks = result.get("all_chunks", [])
        assert len(retried_chunks) < len(all_chunks), "不应重试所有分块"
```

### 3.5 降级测试

```python
class TestDegradation:
    """降级策略测试"""

    def test_level1_reduce_concurrency(self):
        """测试：Level 1 降级 - 减少并行度"""
        config = {"max_parallel": 2}  # 模拟资源受限
        result = run_pipeline(load_fixture("large_input.json"), config=config)

        assert result.get("degradation_level", 0) >= 1
        assert result["max_concurrency_used"] <= 2

    def test_level2_skip_non_critical(self):
        """测试：Level 2 降级 - 跳过非关键Agent"""
        config = {"max_agents": 3}  # 限制Agent数量
        result = run_pipeline(load_fixture("complex_input.json"), config=config)

        executed_agents = {t["agent"] for t in result["executed_tasks"]}
        # fact_checker 应被跳过
        assert "fact_checker" not in executed_agents or \
               result.get("degradation_level", 0) >= 2

    def test_level6_single_agent(self):
        """测试：Level 6 降级 - 单Agent串行"""
        config = {"max_agents": 1, "max_parallel": 1}
        result = run_pipeline(load_fixture("input.json"), config=config)

        assert result.get("degradation_level", 0) == 6
        # 只有1个Agent执行了所有任务
        assert len({t["agent"] for t in result["executed_tasks"]}) == 1
```

---

## 四、测试数据管理

### 4.1 测试数据原则

1. **最小化**：测试数据应尽量小，只包含测试所需的最少内容。
2. **代表性**：测试数据应覆盖典型场景（正常/边界/异常）。
3. **可复现**：测试数据应固定不变，确保测试可复现。
4. **隔离性**：每个测试用例的输入输出独立，不相互依赖。

### 4.2 测试数据示例

**integration_input/full_pipeline_input.json：**
```json
{
  "goal": "将1篇英文论文摘要翻译为中文",
  "constraints": {
    "source_format": "txt",
    "target_format": "md",
    "source_language": "English",
    "target_language": "Chinese"
  },
  "input_files": ["test_fixtures/sample_paper_abstract.txt"],
  "mode": "fast",
  "acceptance_criteria": {
    "terminology_consistency_rate": {"target": 0.95, "minimum": 0.90},
    "paragraph_completeness_rate": {"target": 1.00, "minimum": 0.98}
  }
}
```

---

## 五、运行集成测试

```bash
# 运行所有集成测试
pytest tests/test_integration.py -v

# 运行特定场景
pytest tests/test_integration.py -k "end_to_end" -v
pytest tests/test_integration.py -k "data_passing" -v
pytest tests/test_integration.py -k "degradation" -v

# 运行并显示详细输出
pytest tests/test_integration.py -v -s
```

**集成测试通过标准：**
- 所有端到端测试通过
- 所有数据传递测试通过
- DAG 执行无死锁
- 降级策略正确触发
- 重试流程正确执行
