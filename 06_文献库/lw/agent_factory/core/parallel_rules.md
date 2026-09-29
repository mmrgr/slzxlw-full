# 并行调度规则与冲突检测

> **本文件是 Workflow Planner（Phase 3）和执行引擎的核心调度规则。** 定义了如何识别可并行任务、如何检测冲突、如何控制并发、如何处理失败。所有生成的多Agent系统的 `workflow.json` 必须符合本文件的规则。

---

## 一、核心原则

| 原则 | 说明 |
|------|------|
| 安全并行优先 | 不确定能否并行时，默认串行 |
| 单写者原则 | 同一文件同一时间只能被一个任务写入 |
| 读多写一 | 多个任务可以同时读同一文件，但不能同时写 |
| 失败隔离 | 一个并行任务的失败不影响其他并行任务 |
| 资源受控 | 并发数不超过系统承载能力 |

---

## 二、可并行任务识别规则

### 2.1 可并行的充分条件

两个任务可以并行，当且仅当以下条件**全部满足**：

| 条件 | 编号 | 说明 |
|------|------|------|
| 无依赖关系 | R1 | 任务B不在任务A的 `depends_on` 列表中，反之亦然 |
| 无写冲突 | R2 | 两个任务的 `write_scope` 没有交集 |
| 无读写冲突 | R3 | 任务A的 `write_scope` 与任务B的 `read_scope` 没有交集（反之亦然） |
| 资源充足 | R4 | 当前并发数未达到上限 |
| 同优先级或可抢占 | R5 | 不存在高优先级任务等待该资源 |

### 2.2 并行识别算法

```
function identify_parallel_groups(dag):
    groups = []
    remaining = all_tasks(dag)
    completed = set()

    while remaining is not empty:
        # 找出所有依赖已满足的任务
        ready = [t for t in remaining
                 if all(dep in completed for dep in t.depends_on)]

        # 在ready集合中识别可并行的任务
        group = []
        for task in ready:
            if can_parallel_with_all(task, group):
                group.append(task)

        groups.append(group)
        completed.update(group)
        remaining -= group

    return groups

function can_parallel_with_all(task, group):
    for t in group:
        if not can_parallel(task, t):
            return False
    return True

function can_parallel(taskA, taskB):
    if intersects(taskA.write_scope, taskB.write_scope):  # R2
        return False
    if intersects(taskA.write_scope, taskB.read_scope):   # R3
        return False
    if intersects(taskA.read_scope, taskB.write_scope):   # R3
        return False
    return True
```

### 2.3 并行识别示例

```
场景：5个任务的工作流

T1: 提取Agent     read: input/material.txt    write: output/T1/facts.json
T2: 提纲Agent     read: output/T1/facts.json  write: output/T2/outline.json
T3: 撰写Agent     read: output/T2/outline.json write: output/T3/draft.md
T4: 语言审核Agent  read: output/T3/draft.md    write: output/T4/review_lang.json
T5: 逻辑审核Agent  read: output/T3/draft.md    write: output/T5/review_logic.json

依赖分析：
  T1 → T2 → T3 → {T4, T5}

冲突检测：
  T4.write(output/T4/) vs T5.write(output/T5/)  → 无交集 ✓
  T4.read(output/T3/)  vs T5.write(output/T5/)  → 无交集 ✓
  T4.write(output/T4/) vs T5.read(output/T3/)   → 无交集 ✓

结论：T4和T5可以并行

并行分组：
  Group 1: [T1]           ← 串行
  Group 2: [T2]           ← 串行（依赖T1）
  Group 3: [T3]           ← 串行（依赖T2）
  Group 4: [T4, T5]       ← 并行（都依赖T3，且互不冲突）
```

---

## 三、不应并行任务识别规则

### 3.1 禁止并行的情形

| 情形 | 编号 | 说明 | 示例 |
|------|------|------|------|
| 有依赖关系 | X1 | B依赖A的输出 | T2需要T1的facts.json |
| 写同一文件 | X2 | 两个任务写同一文件 | T4和T5都写output/summary.json |
| 读写冲突 | X3 | A写B读的文件 | A写config.json时B读config.json |
| 共享状态修改 | X4 | 都修改同一状态文件 | 两个Agent都更新workflow_state.json |
| 资源互斥 | X5 | 竞争同一独占资源 | 两个Agent都需要GPU |
| 顺序语义 | X6 | 业务逻辑要求顺序 | 必须先审核再发布 |

### 3.2 禁止并行示例

```
反面案例1：写同一文件
  T4: write_scope = ["output/summary.json"]
  T5: write_scope = ["output/summary.json"]
  → 禁止并行。必须串行，或拆分为不同文件。

反面案例2：读写冲突
  T4: write_scope = ["output/T3/draft.md"]   ← 修改草稿
  T5: read_scope  = ["output/T3/draft.md"]   ← 读取草稿
  → 禁止并行。T5必须在T4完成后执行。

反面案例3：共享状态修改
  T4: 修改 workflow_state.json（标记T4完成）
  T5: 修改 workflow_state.json（标记T5完成）
  → 禁止并行修改。状态文件只能由Orchestrator更新。
    T4和T5各自写自己的状态文件，由Orchestrator汇总。
```

### 3.3 解决冲突的方法

当检测到冲突时，按以下优先级解决：

| 优先级 | 方法 | 说明 |
|--------|------|------|
| 1 | 拆分输出文件 | 让每个任务写不同文件 |
| 2 | 改为串行 | 接受性能损失，保证正确性 |
| 3 | 引入中间层 | 先各自写到临时文件，再由脚本合并 |
| 4 | 由Orchestrator统一管理 | 共享状态由Orchestrator更新 |

```
冲突解决示例：
  原始：T4和T5都写 output/summary.json
  解决：T4写 output/T4/review_lang.json
        T5写 output/T5/review_logic.json
        T6（脚本）合并为 output/summary.json
  → T4和T5可以并行，T6在两者完成后串行执行
```

---

## 四、最大并发数

### 4.1 默认值

| 资源类型 | 默认最大并发 | 说明 |
|----------|-------------|------|
| AI Coding Agent子代理 | 4-6 | 受AI Coding Agent能力限制 |
| 文件I/O | 8 | 磁盘I/O不是瓶颈 |
| 网络请求 | 4 | 避免被目标站点限流 |
| CPU密集脚本 | CPU核心数 | 避免过度竞争 |

### 4.2 并发数决策因素

```
有效并发数 = min(
    可并行任务数,
    资源限制并发数,
    用户配置并发数,
    任务优先级调整后的并发数
)
```

| 因素 | 影响 | 调整方向 |
|------|------|----------|
| AI Coding Agent支持子代理并行 | 决定是否真能并行 | 不支持则强制串行 |
| 任务Token消耗 | 大任务减少并发 | 单任务>10K Token时，并发数减半 |
| 任务耗时差异 | 避免长任务阻塞 | 短任务优先，长任务单独组 |
| 用户预算 | Token预算限制 | 预算紧张时减少并发 |

### 4.3 并发数配置

```yaml
# config/factory_config.yaml 中的并发配置
parallel:
  max_concurrency: 6              # 全局最大并发
  agent_concurrency: 4            # AI Coding Agent子代理并发
  script_concurrency: 8           # 脚本并发
  network_concurrency: 4          # 网络请求并发
  per_task_override:              # 特定任务覆盖
    "T1_report_analysis":
      max_concurrency: 10         # 报告分析任务可以更高并发
      reason: "轻量级任务，Token消耗小"
    "T3_drafting":
      max_concurrency: 2          # 撰写任务降低并发
      reason: "单任务Token消耗大"
```

---

## 五、文件锁与单写者原则

### 5.1 单写者原则

**核心规则：同一文件在同一时间只能被一个任务写入。**

这是文件级一致性的基础保证。实现方式：

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| 路径隔离 | 每个任务写不同路径 | 首选方案 |
| 逻辑锁 | 写入前获取文件锁 | 路径无法隔离时 |
| Orchestrator代理 | 所有写入通过Orchestrator | 共享状态文件 |

### 5.2 路径隔离（推荐）

```
推荐方案：每个任务有独立的输出目录

output/
├── T1/
│   └── facts.json          ← 只有T1能写
├── T2/
│   └── outline.json        ← 只有T2能写
├── T3/
│   └── draft.md            ← 只有T3能写
├── T4/
│   └── review_lang.json    ← 只有T4能写
├── T5/
│   └── review_logic.json   ← 只有T5能写
└── final/
    └── summary.json        ← 只有汇总脚本能写

→ 天然无写冲突，无需锁机制
```

### 5.3 逻辑锁（备选）

当路径无法隔离时（如多个任务需要更新同一索引文件），使用逻辑锁：

```json
// lock_manager.json — 由Orchestrator管理
{
  "locks": {
    "output/index.json": {
      "holder": "T4",
      "acquired_at": "2026-07-27T10:00:00Z",
      "timeout": 300
    }
  }
}
```

```python
# 获取锁的伪代码
def acquire_lock(file_path, task_id, timeout=300):
    while True:
        if lock_is_free(file_path):
            write_lock(file_path, task_id, timeout)
            return True
        if waited_too_long(timeout):
            return False  # 获取锁失败
        sleep(1)

def release_lock(file_path, task_id):
    if lock_holder(file_path) == task_id:
        clear_lock(file_path)
```

### 5.4 Orchestrator代理写入

共享状态文件（如 `workflow_state.json`）只能由Orchestrator写入：

```
规则：
  - 执行Agent不能直接写 workflow_state.json
  - Agent完成后将状态写入自己的 output/T{n}/status.json
  - Orchestrator读取各Agent的status.json，统一更新workflow_state.json

好处：
  - 避免多个Agent同时写状态文件
  - Orchestrator可以全局视角决定下一步
  - 状态更新是原子操作
```

---

## 六、共享资源访问规则

### 6.1 共享资源分类

| 资源类型 | 并发访问策略 | 说明 |
|----------|-------------|------|
| 只读文件 | 自由并发读 | 多个Agent同时读同一文件无风险 |
| 配置文件 | 只读 | 执行Agent不应修改配置 |
| Schema文件 | 只读 | Agent只读取Schema进行校验 |
| 记忆文件 | 只读 | 执行Agent只读不写（详见principles.md P5） |
| 状态文件 | Orchestrator独占写 | 只有Orchestrator能写 |
| 输出文件 | 单写者 | 每个文件只有一个写者 |
| 网络资源 | 限流并发 | 避免被限流或封禁 |
| 外部API | 限流并发 | 遵守API速率限制 |

### 6.2 共享资源访问矩阵

```
                读          写
只读文件       ✓(无限)     ✗
配置文件       ✓(无限)     ✗(仅配置工具)
输出文件       ✓(无限)     ✓(仅文件所有者)
状态文件       ✓(无限)     ✓(仅Orchestrator)
记忆-正式      ✓(无限)     ✗(仅Memory Curator)
记忆-候选      ✓(无限)     ✓(追加，任何Agent)
网络资源       ✓(限流)     ✓(限流)
```

### 6.3 共享资源冲突检测表

Workflow Planner在生成DAG时，必须填写以下冲突检测表：

| 任务对 | A.read vs B.write | A.write vs B.read | A.write vs B.write | 结论 |
|--------|-------------------|-------------------|-------------------|------|
| T1-T2 | 无交集 | 无交集 | 无交集 | 可并行 |
| T4-T5 | 无交集 | 无交集 | 无交集 | 可并行 |
| T2-T3 | 有交集 | - | - | 不可并行（T3读T2写） |

---

## 七、任务优先级

### 7.1 优先级定义

| 优先级 | 编号 | 说明 | 调度策略 |
|--------|------|------|----------|
| 紧急 | P0 | 阻塞后续所有任务 | 独占资源，立即执行 |
| 高 | P1 | 阻塞关键路径 | 优先分配并发槽 |
| 中 | P2 | 普通任务 | 按FIFO调度 |
| 低 | P3 | 非关键路径 | 空闲时执行 |

### 7.2 优先级判定规则

```
function determine_priority(task):
    # P0: 关键路径上的任务，且后续任务都在等待
    if task.is_critical_path and all_followers_waiting(task):
        return P0

    # P1: 关键路径上的任务
    if task.is_critical_path:
        return P1

    # P1: 高风险任务（需要优先完成以尽早发现问题）
    if task.risk_level == "high":
        return P1

    # P3: 非关键路径且非必须
    if task.optional:
        return P3

    # P2: 默认
    return P2
```

### 7.3 优先级调度示例

```
场景：6个任务，最大并发4
  T1 (P0, 紧急) — 关键路径，后续全等它
  T2 (P1, 高)   — 关键路径
  T3 (P1, 高)   — 高风险
  T4 (P2, 中)   — 普通
  T5 (P2, 中)   — 普通
  T6 (P3, 低)   — 非必须

调度顺序：
  第1批：T1(P0) + T2(P1) + T3(P1) + T4(P2)  ← 4个并发槽满
  第2批：T5(P2) + T6(P3)                      ← T4完成后释放槽位

  注意：T6(P3)不会抢占高优先级任务的资源
```

---

## 八、超时机制

### 8.1 超时配置

| 任务类型 | 默认超时 | 说明 |
|----------|----------|------|
| 轻量Agent（提取/校验） | 5分钟 | Token消耗小，应快速完成 |
| 中量Agent（撰写/分析） | 15分钟 | 需要一定时间生成内容 |
| 重量Agent（综述/规划） | 30分钟 | 复杂任务需要更多时间 |
| 确定性脚本 | 2分钟 | 脚本应快速完成 |
| 网络请求 | 30秒 | 避免长时间等待 |
| 人工确认 | 72小时 | 给用户足够时间 |

### 8.2 超时处理策略

```yaml
# 超时处理配置
timeout:
  default_agent: 15m
  default_script: 2m
  default_network: 30s
  human_checkpoint: 72h

  on_timeout:
    # 重试策略
    max_retries: 2
    retry_delay: 30s

    # 重试失败后的处理
    on_retry_exhausted:
      action: "isolate"          # 隔离失败任务
      notify: true                # 通知Orchestrator
      fallback: "skip_or_manual"  # 跳过或转人工

    # 特定任务覆盖
    per_task_override:
      "T1_large_analysis":
        timeout: 30m
        on_timeout:
          action: "checkpoint"    # 保存进度，稍后继续
```

### 8.3 超时处理流程

```
任务执行
    │
    ▼
┌─────────┐    超时     ┌──────────────┐
│ 执行中  │──────────→ │ 记录当前状态  │
└─────────┘            │ 到status.json│
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ 重试次数<max? │
                       └──────┬───────┘
                         YES  │  NO
                    ┌─────────┴─────────┐
                    ▼                   ▼
              ┌──────────┐       ┌──────────────┐
              │ 等待后重试│       │ 隔离失败任务  │
              └──────────┘       │ 通知Orchestrator│
                                 └──────┬───────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │ Orchestrator │
                                 │ 决定后续处理  │
                                 └──────────────┘
```

---

## 九、失败隔离

### 9.1 失败隔离原则

**一个并行任务的失败不影响其他并行任务。**

| 原则 | 说明 |
|------|------|
| 独立失败 | 并行任务组中的一个失败，其他继续执行 |
| 状态记录 | 失败任务的状态记录在独立文件中 |
| Orchestrator决策 | 失败后的处理由Orchestrator统一决策 |
| 降级可用 | 失败任务的结果缺失时，系统可降级运行 |

### 9.2 失败隔离实现

```json
// 每个任务有独立的状态文件
// output/T4/status.json
{
  "task_id": "T4",
  "status": "failed",
  "error": "Schema validation failed: missing field 'summary'",
  "failed_at": "2026-07-27T10:05:32Z",
  "partial_output": "output/T4/review_lang_partial.json",
  "retry_count": 2
}

// output/T5/status.json
{
  "task_id": "T5",
  "status": "completed",
  "output_ref": "output/T5/review_logic.json",
  "completed_at": "2026-07-27T10:03:15Z"
}
```

### 9.3 Orchestrator的失败处理决策

```
当Orchestrator检测到任务失败时，按以下决策树处理：

┌─────────────────────────┐
│ 任务T失败               │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ T是否在关键路径上？      │
└────────────┬────────────┘
        YES  │  NO
   ┌─────────┴─────────┐
   ▼                   ▼
┌────────────┐  ┌──────────────┐
│ 重试T      │  │ 标记T为失败   │
│ (max 2次)  │  │ 继续其他任务  │
└──────┬─────┘  └──────┬───────┘
       │               │
       ▼               ▼
┌────────────┐  ┌──────────────┐
│ 重试成功？  │  │ 后续任务是否  │
└──────┬─────┘  │ 依赖T的输出？ │
   YES │  NO    └──────┬───────┘
   ┌───┴────┐     YES  │  NO
   ▼        ▼    ┌─────┴─────┐
┌──────┐ ┌────────┐ │ 标记后续   │ │ 跳过T，继续 │
│继续  │ │降级处理 │ │ 任务为     │ │ 执行       │
│执行  │ │或人工  │ │ blocked    │ └────────────┘
└──────┘ │介入    │ └───────────┘
         └────────┘
```

### 9.4 失败隔离示例

```
场景：T4(语言审核)和T5(逻辑审核)并行执行

T4 执行中...
T5 执行中...

T5 完成 → status: completed
T4 失败 → status: failed (Schema错误)

Orchestrator检查：
  - T4不在关键路径上（T4的输出是建议性的，非阻塞性）
  - 后续T6(汇总)可以缺少T4的结果

Orchestrator决策：
  - 标记T4为failed
  - T6继续执行，但标注"缺少语言审核结果"
  - 在最终报告中标注风险

结果：系统降级运行，部分完成而非全部失败
```

---

## 十、workflow.json 中的并行声明

### 10.1 完整示例

```json
{
  "workflow_id": "WF-20260727-001",
  "version": "1.0",
  "max_concurrency": 6,
  "tasks": [
    {
      "task_id": "T1",
      "agent": "extractor",
      "depends_on": [],
      "parallel_group": 1,
      "read_scope": ["input/material.txt"],
      "write_scope": ["output/T1/facts.json"],
      "risk_level": "low",
      "priority": "P1",
      "timeout": "5m",
      "max_retries": 2
    },
    {
      "task_id": "T2",
      "agent": "outliner",
      "depends_on": ["T1"],
      "parallel_group": 2,
      "read_scope": ["output/T1/facts.json"],
      "write_scope": ["output/T2/outline.json"],
      "risk_level": "medium",
      "priority": "P1",
      "timeout": "10m",
      "max_retries": 1
    },
    {
      "task_id": "T3",
      "agent": "drafter",
      "depends_on": ["T1", "T2"],
      "parallel_group": 3,
      "read_scope": ["output/T1/facts.json", "output/T2/outline.json"],
      "write_scope": ["output/T3/draft.md"],
      "risk_level": "high",
      "priority": "P1",
      "timeout": "15m",
      "max_retries": 1
    },
    {
      "task_id": "T4",
      "agent": "language_reviewer",
      "depends_on": ["T3"],
      "parallel_group": 4,
      "read_scope": ["output/T3/draft.md"],
      "write_scope": ["output/T4/review_lang.json"],
      "risk_level": "medium",
      "priority": "P2",
      "timeout": "10m",
      "max_retries": 2
    },
    {
      "task_id": "T5",
      "agent": "logic_reviewer",
      "depends_on": ["T3"],
      "parallel_group": 4,
      "read_scope": ["output/T3/draft.md"],
      "write_scope": ["output/T5/review_logic.json"],
      "risk_level": "medium",
      "priority": "P2",
      "timeout": "10m",
      "max_retries": 2
    },
    {
      "task_id": "T6",
      "type": "program",
      "tool": "merge_reviews",
      "depends_on": ["T4", "T5"],
      "parallel_group": 5,
      "read_scope": ["output/T4/review_lang.json", "output/T5/review_logic.json"],
      "write_scope": ["output/final/summary.json"],
      "risk_level": "low",
      "priority": "P2",
      "timeout": "2m",
      "max_retries": 0
    }
  ],
  "parallel_groups": {
    "1": ["T1"],
    "2": ["T2"],
    "3": ["T3"],
    "4": ["T4", "T5"],
    "5": ["T6"]
  },
  "conflict_check": {
    "passed": true,
    "checked_pairs": 15,
    "conflicts": []
  }
}
```

### 10.2 并行声明规则

| 字段 | 说明 | 示例 |
|------|------|------|
| `parallel_group` | 同组的任务可并行执行 | T4和T5都是group 4 |
| `depends_on` | 必须完成的前置任务 | T3依赖T1和T2 |
| `read_scope` | 可读文件列表 | 用于冲突检测 |
| `write_scope` | 可写文件列表 | 用于冲突检测 |
| `risk_level` | 风险等级 | 决定审核力度 |
| `priority` | 优先级 | 决定调度顺序 |
| `timeout` | 超时时间 | 超时后触发处理 |
| `max_retries` | 最大重试次数 | 重试耗尽后隔离 |

---

## 十一、冲突检测检查清单

Workflow Planner在输出 `workflow.json` 前，必须完成以下检查：

- [ ] 所有任务的 `write_scope` 两两无交集（同一parallel_group内）
- [ ] 同一parallel_group内，任一任务的 `write_scope` 与其他任务的 `read_scope` 无交集
- [ ] `depends_on` 形成的图是无环的（DAG）
- [ ] 每个parallel_group内的任务数量 ≤ max_concurrency
- [ ] 每个任务都有明确的 `timeout` 和 `max_retries`
- [ ] 共享状态文件不在任何执行Agent的 `write_scope` 中
- [ ] 高风险任务已标注 `risk_level: high`
- [ ] 关键路径上的任务已标注 `priority: P0` 或 `P1`
