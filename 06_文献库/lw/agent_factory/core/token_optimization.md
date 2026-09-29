# Token 优化策略 — 6 种核心方法

> **本文件是 Efficiency Optimizer（Phase 6c）的执行依据，也是所有 Agent 定义的约束条件。** Agent Factory 的核心设计目标之一是"最小化 Token"。本文件定义了 6 种互补的 Token 优化策略，每种策略都包含原理、配置示例和代码示例。

---

## 策略总览

| 策略 | 编号 | 核心思想 | 预期节省 |
|------|------|----------|----------|
| 上下文最小化 | S1 | 每个Agent只获得必需信息 | 40-60% |
| 引用路径而非复制内容 | S2 | 传递路径不传递内容 | 50-80% |
| 分层摘要与压缩 | S3 | 大文件先摘要，按需展开 | 30-50% |
| 缓存和增量执行 | S4 | 输入不变时复用结果 | 70-100%（增量场景） |
| Token预算与Agent预算 | S5 | 为每个Agent设定Token上限 | 控制总量 |
| 确定性程序替代语言Agent | S6 | 能用代码的不用Agent | 100%（替代场景） |

---

## S1. 上下文最小化

### 原理

AI Coding Agent 的上下文窗口是有限资源。上下文中包含的无关信息越多，有效信息的注意力权重越低（注意力稀释），同时Token消耗越大。上下文最小化的目标是：**每个Agent的上下文中只包含完成当前任务所必需的最小信息集。**

### 最小化操作清单

| 操作 | 说明 | 节省效果 |
|------|------|----------|
| 只传当前步骤输入 | 不传全局历史 | 高 |
| 只传相关Schema | 不传全部Schema | 中 |
| 角色定义按需加载 | 不预加载所有Agent定义 | 高 |
| 规则文件按需读取 | 只读取当前阶段需要的规则 | 高 |
| 去除冗余说明 | 精简角色定义中的说明文字 | 中 |

### 配置示例

```yaml
# config/context_budget.yaml
context_budget:
  # 每种Agent类型的上下文Token上限
  agent_types:
    extractor:
      max_context: 4000
      required:
        - role_definition       # 角色定义
        - input_path            # 输入文件路径
        - output_schema         # 输出Schema
      optional:
        - style_guide           # 风格指南（按需）

    drafter:
      max_context: 6000
      required:
        - role_definition
        - input_paths           # 多个输入路径
        - output_schema
        - style_guide           # 撰写需要风格指引
      optional:
        - examples              # 范文（按需）

    reviewer:
      max_context: 3000
      required:
        - role_definition
        - review_target_path    # 待审内容路径
        - review_criteria       # 审核标准
      optional: []

    planner:
      max_context: 8000
      required:
        - role_definition
        - requirements          # 需求文件
        - constraints           # 约束条件
      optional:
        - historical_patterns   # 历史模式
```

### 代码示例：上下文组装器

```python
class ContextAssembler:
    """根据Agent类型和任务，组装最小上下文"""

    BUDGETS = {
        "extractor": 4000,
        "drafter": 6000,
        "reviewer": 3000,
        "planner": 8000,
    }

    def assemble(self, agent_type, task):
        budget = self.BUDGETS[agent_type]
        context_parts = []
        current_tokens = 0

        # 1. 必需部分（优先加载）
        for item in self._get_required_items(agent_type, task):
            tokens = self._estimate_tokens(item)
            if current_tokens + tokens <= budget:
                context_parts.append(item)
                current_tokens += tokens

        # 2. 可选部分（预算允许时加载）
        for item in self._get_optional_items(agent_type, task):
            tokens = self._estimate_tokens(item)
            if current_tokens + tokens <= budget:
                context_parts.append(item)
                current_tokens += tokens

        return context_parts

    def _get_required_items(self, agent_type, task):
        """返回必需的上下文项"""
        items = []
        items.append(self._load_role_definition(agent_type))

        # 输入只传路径，不传内容
        for input_path in task.get("inputs", []):
            items.append(f"输入文件: {input_path}")

        # 只加载当前任务的输出Schema
        schema_path = task.get("output_schema")
        if schema_path:
            items.append(self._load_file(schema_path))

        return items

    def _estimate_tokens(self, text):
        """粗略估算Token数（中文约1.5字/Token，英文约4字符/Token）"""
        return int(len(text) / 2.5)
```

### 反面 vs 正面对比

```
任务：Agent B 根据大纲撰写正文

反面方案（上下文 50,000 Token）：
  - 完整原始材料（20,000 Token）
  - Agent A 的完整推理过程（5,000 Token）
  - 所有Schema定义（8,000 Token）
  - 所有规则文件（10,000 Token）
  - 所有Agent定义（7,000 Token）

正面方案（上下文 1,500 Token）：
  - 角色定义（800 Token）
  - 输入路径引用（20 Token）
  - 输出Schema（300 Token）
  - 完成条件（200 Token）
  - 禁止行为（180 Token）

节省：97%
```

---

## S2. 引用路径而非复制内容

### 原理

Agent之间的数据传递如果通过内联内容（把文件内容嵌入JSON），会导致：
1. workflow.json 膨胀，每个Agent都要在上下文中处理大量内联数据
2. 重复数据在多个Agent间复制，Token成倍增长
3. 中间结果无法独立检查和缓存

引用路径方案：所有数据传递通过文件路径引用，Agent执行时按需读取。

### 数据传递协议

```json
// 错误：内联内容
{
  "task_id": "T2",
  "input": {
    "facts": [
      {"claim": "2024年数字经济规模53.9万亿", "source": "统计局"},
      {"claim": "占GDP比重41.5%", "source": "统计局"},
      // ... 200条，共15,000 Token
    ]
  }
}

// 正确：路径引用
{
  "task_id": "T2",
  "input": {
    "facts_ref": "output/T1/facts.json",
    "outline_ref": "output/T1/outline.json"
  },
  "output": {
    "draft_ref": "output/T2/draft.md"
  }
}
// 总计 60 Token
```

### 配置示例

```yaml
# config/data_passing.yaml
data_passing:
  mode: "path_reference"       # 强制路径引用模式
  inline_max_tokens: 100       # 超过100Token的数据必须用路径引用

  # 路径命名规范
  path_convention:
    input: "output/T{prev_task_id}/{filename}"
    output: "output/T{task_id}/{filename}"
    shared: "output/shared/{filename}"

  # 文件格式约定
  formats:
    structured: ".json"        # 结构化数据用JSON
    text: ".md"                # 文本内容用Markdown
    binary: ".bin"             # 二进制数据
```

### 代码示例：路径引用管理器

```python
class PathReferenceManager:
    """管理Agent间的路径引用"""

    def create_reference(self, task_id, data, filename):
        """将数据写入文件，返回路径引用"""
        path = f"output/T{task_id}/{filename}"
        self._write_file(path, data)
        return {"ref": path}

    def resolve_reference(self, ref, max_tokens=None):
        """按需读取引用指向的文件内容"""
        path = ref["ref"] if isinstance(ref, dict) else ref
        content = self._read_file(path)

        if max_tokens and self._estimate_tokens(content) > max_tokens:
            # 超过预算时返回摘要而非全文
            return self._summarize(content, max_tokens)
        return content

    def resolve_partial(self, ref, section_id):
        """只读取文件的特定部分"""
        path = ref["ref"] if isinstance(ref, dict) else ref
        return self._read_section(path, section_id)
```

### 路径引用的Token节省分析

```
场景：5个Agent的串行流水线，每步输出5,000 Token

内联方案：
  T1输出5K → T2上下文含T1的5K
  T2输出5K → T3上下文含T1+T2的10K
  T3输出5K → T4上下文含T1+T2+T3的15K
  T4输出5K → T5上下文含T1+T2+T3+T4的20K
  总计：5+10+15+20 = 50K Token

路径引用方案：
  每个Agent上下文只含路径引用（约20Token/个）
  T2上下文：角色定义 + 2个路径引用 ≈ 1K
  T3上下文：角色定义 + 2个路径引用 ≈ 1K
  ...
  总计：5 × 1K = 5K Token

节省：90%
```

---

## S3. 分层摘要与压缩

### 原理

大文件如果直接进入Agent上下文，会消耗大量Token。分层摘要策略：先将大文件压缩为摘要，Agent主要基于摘要工作；只有当摘要信息不足以完成任务时，才按需读取原文的特定部分。

### 三层摘要架构

```
Layer 1: 全文（Full Text）
  → 原始文件，如 input/material.txt（20,000 Token）
  → 仅在需要精确细节时读取

Layer 2: 结构化摘要（Structured Summary）
  → 提取关键信息和结构，如 output/T1/summary.json（2,000 Token）
  → Agent日常工作的主要信息源

Layer 3: 要点列表（Key Points）
  → 极简要点，如 output/T1/keypoints.json（200 Token）
  → 用于快速判断和路由决策
```

### 配置示例

```yaml
# config/summarization.yaml
summarization:
  # 触发摘要的阈值
  trigger_threshold: 3000      # 文件超过3000 Token时生成摘要

  # 摘要层级
  layers:
    keypoints:
      max_tokens: 200
      content: "核心论点、关键数据、主要结论"
      used_by: ["planner", "orchestrator"]  # 谁使用这层

    summary:
      max_tokens: 2000
      content: "结构化摘要，保留逻辑结构和关键细节"
      used_by: ["drafter", "analyzer"]

    full_text:
      max_tokens: null          # 无限制
      content: "原始全文"
      used_by: ["fact_checker"] # 只有核查需要全文

  # 按需展开策略
  on_demand_expansion:
    enabled: true
    trigger: "agent_requests_detail"
    method: "section_retrieval"  # 按章节读取
```

### 代码示例：分层摘要生成器

```python
class LayeredSummarizer:
    """生成和管理分层摘要"""

    def generate_layers(self, full_text_path):
        """为大文件生成三层摘要"""
        full_text = self._read_file(full_text_path)
        full_tokens = self._estimate_tokens(full_text)

        if full_tokens < 3000:
            # 小文件不需要摘要
            return {"full_text": full_text_path}

        # 生成结构化摘要
        summary = self._agent_summarize(
            full_text,
            instruction="提取以下信息的结构化摘要：1.主要论点 2.关键数据 3.逻辑结构 4.结论。保留所有数字和引用。",
            max_tokens=2000
        )
        summary_path = full_text_path.replace(".txt", "_summary.json")
        self._write_file(summary_path, summary)

        # 生成要点列表
        keypoints = self._agent_summarize(
            summary,
            instruction="从摘要中提取3-5个核心要点，每个要点不超过50字。",
            max_tokens=200
        )
        keypoints_path = full_text_path.replace(".txt", "_keypoints.json")
        self._write_file(keypoints_path, keypoints)

        return {
            "keypoints": keypoints_path,    # 200 Token
            "summary": summary_path,         # 2,000 Token
            "full_text": full_text_path      # 20,000 Token
        }

    def get_for_agent(self, agent_type, layers):
        """根据Agent类型返回合适层级"""
        if agent_type in ["planner", "orchestrator"]:
            return self._read_file(layers["keypoints"])  # 200 Token
        elif agent_type in ["drafter", "analyzer"]:
            return self._read_file(layers["summary"])     # 2,000 Token
        elif agent_type in ["fact_checker"]:
            return self._read_file(layers["full_text"])   # 20,000 Token
```

### 按需展开示例

```python
class OnDemandExpander:
    """Agent在摘要信息不足时，按需读取原文片段"""

    def expand_section(self, full_text_path, section_id):
        """只读取原文的特定章节"""
        full_text = self._read_file(full_text_path)
        sections = self._parse_sections(full_text)
        return sections.get(section_id, "Section not found")

# Agent使用示例：
# 1. Agent读取摘要，发现需要某数据的原始上下文
# 2. Agent调用 expand_section("input/material.txt", "section_3")
# 3. 只读取第3节的内容（约500 Token），而非全文（20,000 Token）
```

---

## S4. 缓存和增量执行

### 原理

当系统因中断恢复或输入未变化而重新执行时，如果每个任务都能检查自己的输入是否变化，未变化则直接复用上次的输出，可以避免大量重复计算。缓存以输入文件的哈希值为键，输出文件路径为值。

### 缓存机制

```
任务执行前：
  1. 计算所有输入文件的哈希值
  2. 查询缓存：hash → output_path
  3. 如果缓存命中且输出文件存在 → 跳过执行，直接复用
  4. 如果缓存未命中 → 执行任务，完成后写入缓存
```

### 配置示例

```yaml
# config/cache.yaml
cache:
  enabled: true
  store: "output/.cache/"

  # 缓存键的构成
  key_components:
    - task_id              # 任务ID
    - agent_id             # Agent定义的哈希
    - input_hashes         # 所有输入文件的哈希
    - schema_hash          # 输出Schema的哈希
    - config_hash          # 相关配置的哈希

  # 缓存失效条件
  invalidation:
    - input_changed        # 输入文件变化
    - agent_definition_changed  # Agent定义变化
    - schema_changed       # Schema变化
    - manual_clear         # 手动清除

  # 缓存TTL
  ttl: 7d                  # 7天后自动失效
```

### 代码示例：缓存管理器

```python
import hashlib
import json
import os
from pathlib import Path

class CacheManager:
    """任务级缓存管理"""

    def __init__(self, cache_dir="output/.cache/"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "cache_index.json"
        self.index = self._load_index()

    def get_cache_key(self, task):
        """生成缓存键"""
        components = []

        # 任务ID
        components.append(task["task_id"])

        # Agent定义哈希
        agent_def = self._read_file(task["agent_definition_path"])
        components.append(hashlib.sha256(agent_def.encode()).hexdigest()[:16])

        # 输入文件哈希
        for input_path in sorted(task.get("inputs", [])):
            file_hash = self._file_hash(input_path)
            components.append(f"{input_path}:{file_hash}")

        # Schema哈希
        if "output_schema" in task:
            schema = self._read_file(task["output_schema"])
            components.append(hashlib.sha256(schema.encode()).hexdigest()[:16])

        return hashlib.sha256("|".join(components).encode()).hexdigest()

    def try_cache(self, task):
        """尝试从缓存获取结果"""
        key = self.get_cache_key(task)

        if key not in self.index:
            return None  # 缓存未命中

        cache_entry = self.index[key]
        output_path = cache_entry["output_path"]

        # 验证输出文件仍然存在
        if not os.path.exists(output_path):
            return None  # 缓存失效

        # 验证输出文件未被修改
        current_hash = self._file_hash(output_path)
        if current_hash != cache_entry["output_hash"]:
            return None  # 输出被篡改

        return {
            "cache_hit": True,
            "output_path": output_path,
            "cached_at": cache_entry["created_at"]
        }

    def save_to_cache(self, task, output_path):
        """将结果保存到缓存"""
        key = self.get_cache_key(task)
        self.index[key] = {
            "task_id": task["task_id"],
            "output_path": output_path,
            "output_hash": self._file_hash(output_path),
            "created_at": self._now_iso()
        }
        self._save_index()

    def _file_hash(self, path):
        """计算文件内容的SHA256"""
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
```

### 增量执行示例

```python
class IncrementalExecutor:
    """增量执行器：跳过已完成的任务"""

    def execute_workflow(self, workflow):
        results = {}
        for task in workflow["tasks"]:
            # 尝试缓存
            cached = self.cache.try_cache(task)
            if cached:
                print(f"[CACHE] {task['task_id']} 跳过，复用缓存结果")
                results[task["task_id"]] = cached
                continue

            # 检查依赖是否已完成
            deps = task.get("depends_on", [])
            if not all(d in results for d in deps):
                print(f"[SKIP] {task['task_id']} 依赖未完成")
                continue

            # 执行任务
            print(f"[EXEC] {task['task_id']} 开始执行")
            output_path = self._execute_task(task)

            # 保存到缓存
            self.cache.save_to_cache(task, output_path)
            results[task["task_id"]] = {
                "cache_hit": False,
                "output_path": output_path
            }

        return results
```

### 缓存节省效果

```
场景：系统执行到T4时中断，重新启动

无缓存：T1→T2→T3→T4→T5 全部重新执行
  Token消耗：100%

有缓存：T1(命中)→T2(命中)→T3(命中)→T4(执行)→T5(执行)
  Token消耗：40%（只执行T4和T5）
  节省：60%
```

---

## S5. Token 预算与 Agent 预算

### 原理

没有预算约束的系统容易Token失控。Token预算为整个系统设定总量上限，Agent预算为每个Agent设定个体上限。当预算接近上限时，系统触发降级策略。

### 预算体系

```
总预算（Total Budget）
  ├── Agent执行预算（Agent Execution Budget）
  │   ├── Agent 1 预算
  │   ├── Agent 2 预算
  │   └── ...
  ├── 审核预算（Review Budget）
  │   ├── 结构校验（确定性，不消耗Token）
  │   ├── 语义审核（消耗Token）
  │   └── 冲突裁决（消耗Token）
  └── 预留缓冲（Reserve Buffer）
      └── 用于重试和意外情况
```

### 配置示例

```yaml
# config/budget.yaml
budget:
  # 总Token预算
  total: 200000

  # 分配比例
  allocation:
    agent_execution: 0.60    # 120,000 Token
    review: 0.25             # 50,000 Token
    reserve: 0.15            # 30,000 Token

  # Agent执行预算细分
  agent_budgets:
    extractor:
      per_invocation: 4000
      max_invocations: 10     # 最多调用10次
      total: 40000

    drafter:
      per_invocation: 8000
      max_invocations: 3
      total: 24000

    reviewer:
      per_invocation: 3000
      max_invocations: 6
      total: 18000

    planner:
      per_invocation: 10000
      max_invocations: 2
      total: 20000

  # 审核预算细分
  review_budgets:
    structural_check: 0       # 确定性，不消耗Token
    semantic_review: 30000
    conflict_resolution: 15000
    final_audit: 5000

  # 降级触发点
  degradation:
    - threshold: 0.70         # 消耗70%时
      action: "reduce_alternatives"    # 减少候选方案
    - threshold: 0.85         # 消耗85%时
      action: "risk_based_review"      # 改为风险审核
    - threshold: 0.95         # 消耗95%时
      action: "deterministic_only"     # 只用确定性校验
    - threshold: 1.00         # 消耗100%时
      action: "stop_and_report"        # 停止并报告
```

### 代码示例：预算管理器

```python
class BudgetManager:
    """Token预算管理"""

    def __init__(self, config):
        self.total_budget = config["total"]
        self.consumed = 0
        self.agent_consumed = {}  # {agent_id: consumed}
        self.budgets = config["agent_budgets"]
        self.degradation = config["degradation"]
        self.current_level = 0

    def check_before_execution(self, agent_id, estimated_tokens):
        """执行前检查预算"""
        # 检查总预算
        if self.consumed + estimated_tokens > self.total_budget:
            return {"allowed": False, "reason": "total_budget_exceeded"}

        # 检查Agent预算
        agent_budget = self.budgets.get(agent_id, {})
        agent_used = self.agent_consumed.get(agent_id, 0)
        agent_total = agent_budget.get("total", float('inf'))

        if agent_used + estimated_tokens > agent_total:
            return {"allowed": False, "reason": "agent_budget_exceeded"}

        return {"allowed": True}

    def record_usage(self, agent_id, tokens_used):
        """记录Token消耗"""
        self.consumed += tokens_used
        self.agent_consumed[agent_id] = \
            self.agent_consumed.get(agent_id, 0) + tokens_used

        # 检查是否需要降级
        self._check_degradation()

    def _check_degradation(self):
        """检查降级触发点"""
        ratio = self.consumed / self.total_budget
        for level in self.degradation:
            if ratio >= level["threshold"] and level["threshold"] > \
               self.degradation[self.current_level]["threshold"]:
                self.current_level += 1
                print(f"[BUDGET] 降级到Level {self.current_level}: "
                      f"{level['action']}")

    def get_status(self):
        """获取预算状态"""
        return {
            "total_budget": self.total_budget,
            "consumed": self.consumed,
            "remaining": self.total_budget - self.consumed,
            "usage_ratio": self.consumed / self.total_budget,
            "degradation_level": self.current_level,
            "agent_usage": dict(self.agent_consumed)
        }
```

### 降级策略执行

```python
class DegradationHandler:
    """根据预算消耗程度执行降级"""

    def apply_degradation(self, level, workflow):
        if level == 1:
            # Level 1: 减少候选方案
            return self._reduce_alternatives(workflow)
        elif level == 2:
            # Level 2: 全量审核改为风险审核
            return self._switch_to_risk_based_review(workflow)
        elif level == 3:
            # Level 3: 只用确定性校验
            return self._deterministic_only(workflow)
        elif level == 4:
            # Level 4: 停止并报告
            return self._stop_and_report(workflow)
```

---

## S6. 确定性程序替代语言 Agent

### 原理

这是最彻底的Token优化：**完全不使用Agent，用确定性程序完成任务**。确定性程序不消耗Token，结果可靠可重复，速度更快。Tool Architect（Phase 4c）负责识别哪些任务可以从Agent替换为程序。

### 替换判定标准

| 判定维度 | 程序适合 | Agent适合 |
|----------|----------|----------|
| 输入输出关系 | 规则明确、可枚举 | 需要语义理解 |
| 判断标准 | 有明确的true/false | 需要模糊判断 |
| 创造性 | 不需要 | 需要创造性生成 |
| 异常处理 | 规则可覆盖 | 需要灵活应对 |
| 可重复性 | 必须完全一致 | 允许合理差异 |

### 程序可替代的任务清单

```
必须用程序（禁止用Agent）：
  - JSON Schema校验
  - 文件存在性检查
  - 数字一致性核对
  - 哈希比较
  - 字数统计
  - 文件格式转换
  - 去重、排序
  - 缓存判断
  - 文件遍历

优先用程序（能用程序就用程序）：
  - 简单文本提取（正则可匹配的）
  - 数据清洗（规则明确的）
  - 报表生成（模板填充）
  - 简单分类（规则可枚举的）

必须用Agent（程序无法可靠完成）：
  - 语义理解与分析
  - 创造性写作
  - 复杂判断与决策
  - 跨文档推理
  - 自然语言翻译
  - 异常解释
```

### 配置示例

```yaml
# config/tool_assignment.yaml
tool_assignment:
  # 强制程序的任务
  force_program:
    - task_type: "json_validation"
      tool: "jsonschema"
      reason: "JSON校验是100%确定性的，用Agent是浪费"

    - task_type: "file_existence_check"
      tool: "os.path.exists"
      reason: "文件存在性检查无需语义理解"

    - task_type: "number_verification"
      tool: "python:verify_numbers"
      reason: "数字核对是确定性比对"

    - task_type: "hash_comparison"
      tool: "sha256sum"
      reason: "哈希比较完全确定"

    - task_type: "word_count"
      tool: "wc"
      reason: "字数统计是确定性操作"

  # 优先程序的任务
  prefer_program:
    - task_type: "data_cleaning"
      tool: "pandas"
      condition: "清洗规则可用正则或条件表达"
      fallback: "agent"  # 规则无法覆盖时用Agent

    - task_type: "report_generation"
      tool: "jinja2"
      condition: "有明确模板"
      fallback: "agent"

  # 必须用Agent的任务
  require_agent:
    - task_type: "semantic_analysis"
      reason: "需要语义理解"

    - task_type: "creative_writing"
      reason: "需要创造性生成"

    - task_type: "translation"
      reason: "需要语言能力"
```

### 代码示例：工具分配器

```python
class ToolAssigner:
    """决定每个任务用程序还是Agent"""

    FORCE_PROGRAM = {
        "json_validation": "jsonschema",
        "file_existence_check": "os.path.exists",
        "number_verification": "verify_numbers",
        "hash_comparison": "sha256sum",
        "word_count": "wc",
    }

    def assign(self, task):
        """为任务分配工具类型"""
        task_type = task["type"]

        # 强制使用程序
        if task_type in self.FORCE_PROGRAM:
            return {
                "type": "program",
                "tool": self.FORCE_PROGRAM[task_type],
                "reason": f"{task_type}是确定性任务，强制使用程序"
            }

        # 尝试使用程序
        program_candidate = self._try_program(task)
        if program_candidate:
            return program_candidate

        # 使用Agent
        return {
            "type": "agent",
            "agent": task.get("preferred_agent"),
            "reason": f"{task_type}需要语义理解，使用Agent"
        }

    def _try_program(self, task):
        """尝试为任务找到确定性程序方案"""
        task_type = task["type"]

        if task_type == "data_cleaning":
            rules = task.get("cleaning_rules", [])
            if all(self._is_deterministic_rule(r) for r in rules):
                return {
                    "type": "program",
                    "tool": "pandas",
                    "script": "clean_data.py",
                    "reason": "清洗规则全部可确定，使用程序"
                }

        if task_type == "report_generation":
            template = task.get("template")
            if template:
                return {
                    "type": "program",
                    "tool": "jinja2",
                    "script": "generate_report.py",
                    "reason": "有明确模板，使用程序填充"
                }

        return None  # 无法用程序替代
```

### 替换效果示例

```
场景：文档处理流水线

原始方案（全部用Agent）：
  T1: 格式转换Agent        → 5,000 Token
  T2: 内容提取Agent        → 8,000 Token
  T3: 数字核对Agent        → 3,000 Token
  T4: JSON校验Agent        → 2,000 Token
  T5: 撰写Agent           → 10,000 Token
  T6: 字数统计Agent        → 1,000 Token
  总计：29,000 Token

优化方案（程序替代）：
  T1: pandoc（程序）       → 0 Token
  T2: 内容提取Agent        → 8,000 Token（需要语义理解）
  T3: verify_numbers（程序）→ 0 Token
  T4: jsonschema（程序）   → 0 Token
  T5: 撰写Agent           → 10,000 Token（需要创造性）
  T6: wc（程序）           → 0 Token
  总计：18,000 Token

节省：38%（且确定性任务的结果更可靠）
```

---

## 策略组合使用建议

### 不同场景的策略组合

| 场景 | 推荐策略组合 | 说明 |
|------|-------------|------|
| 简单任务 | S1 + S6 | 上下文最小化 + 程序替代 |
| 大文档处理 | S1 + S2 + S3 | 最小化 + 路径引用 + 分层摘要 |
| 批量处理 | S2 + S4 + S6 | 路径引用 + 缓存 + 程序替代 |
| 复杂多Agent | S1 + S2 + S5 | 最小化 + 路径引用 + 预算控制 |
| 长期运行 | S2 + S4 + S5 | 路径引用 + 缓存 + 预算控制 |
| 高质量要求 | S1 + S2 + S3 + S5 | 全部优化（除S6，因可能需要Agent保证质量） |

### 优化检查清单

Efficiency Optimizer（Phase 6c）必须逐项检查：

- [ ] S1: 每个Agent的上下文是否已最小化？
- [ ] S2: 是否所有数据传递都使用路径引用？
- [ ] S3: 超过3000 Token的文件是否生成了分层摘要？
- [ ] S4: 是否所有任务都启用了缓存？
- [ ] S5: 是否设定了Token预算和降级策略？
- [ ] S6: 是否所有确定性任务都已替换为程序？
