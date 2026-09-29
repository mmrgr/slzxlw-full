# 错误处理与重试协议

> **本文件定义了 Agent Factory 生成的多Agent系统在运行时的错误处理、重试、降级与恢复规范。** 错误是不可避免的——Agent 会犯错、文件会丢失、网络会超时、权限会不足。本协议确保错误发生时系统行为可控：失败被隔离、数据不丢失、执行可恢复、降级有预案。本协议贯穿执行引擎、Orchestrator 和所有 Agent 的错误处理逻辑，与 `protocols/agent_contract.md` 中的错误类型分类配合使用。

---

## 一、四大基础原则

### 1.1 失败隔离原则

> **一个 Agent 失败不导致整个任务丢失。**

并行任务组中的一个失败，其他继续执行。失败任务的状态记录在独立文件中，由 Orchestrator 统一决策后续处理。

```
场景：T4（语言审核）和 T5（逻辑审核）并行执行

T4 执行中...
T5 执行中...

T5 完成 → status: completed
T4 失败 → status: failed (Schema 错误)

Orchestrator 检查：
  - T4 不在关键路径上（输出是建议性的，非阻塞性）
  - 后续 T6（汇总）可以缺少 T4 的结果

Orchestrator 决策：
  - 标记 T4 为 failed
  - T6 继续执行，但标注"缺少语言审核结果"
  - 在最终报告中标注风险

结果：系统降级运行，部分完成而非全部失败
```

**失败隔离的实现**：
- 每个任务有独立的状态文件（`output/T{n}/status.json`）
- 失败任务的状态不影响其他任务的状态文件
- Orchestrator 汇总各任务状态，统一决策

### 1.2 原子写入原则

> **所有文件写入采用"临时文件后原子替换"策略，确保任何时刻文件系统处于一致状态。**

```
原子写入流程：

步骤1：写入临时文件
  Agent 输出 → output/T2/draft.md.tmp

步骤2：校验临时文件
  Schema 校验 → 通过？
    通过 → 步骤3
    不通过 → 删除临时文件，报告错误

步骤3：原子替换
  mv output/T2/draft.md.tmp output/T2/draft.md
  （原子操作：要么成功替换，要么原文件不变）

步骤4：更新状态
  写入 output/T2/status.json: {"status": "completed", ...}
```

**原子写入的好处**：
- 中断时不会产生半写的损坏文件
- 下游 Agent 读取的文件要么是完整的旧版本，要么是完整的新版本
- 断点恢复时不需要判断文件是否写完整

### 1.3 幂等执行原则

> **同一任务多次执行产生相同结果，重复执行不会产生副作用。**

幂等性保证：重试不会导致数据重复或状态不一致。

```
幂等执行规则：
  1. 输出路径固定：同一任务的输出始终写到同一路径
     → 重复执行覆盖之前的输出，不产生多个副本

  2. 状态更新可重入：状态文件可以被安全地重复更新
     → 重复写入 status: completed 不会出错

  3. 无副作用操作：Agent 不执行写入输出之外的副作用操作
     → 不发送邮件、不调用外部 API（除非明确声明且可重试）

  4. 输入不变则输出不变：相同输入产生相同输出
     → 这是缓存复用的基础
```

### 1.4 断点续跑原则

> **任何时刻中断后，系统可从上次完成的位置恢复执行，不丢失已完成的工作。**

```
断点续跑流程：

步骤1：读取全局状态文件
  output/workflow_state.json → 记录每个任务的完成状态

步骤2：识别已完成任务
  status == "completed" → 跳过，复用已有输出

步骤3：识别缓存可复用任务
  cache_key 匹配且输入哈希不变 → 跳过，复用已有输出

步骤4：识别需重新执行的任务
  status == "running"（中断时正在执行）→ 重新执行（幂等性保证安全）
  status == "failed" → 根据重试策略决定是否重试
  status == "pending" → 正常执行

步骤5：从断点继续
  按 DAG 依赖顺序，执行所有未完成的任务
```

---

## 二、重试策略表

### 2.1 错误类型与重试策略

所有错误归入五大类，每类有明确的重试策略（与 `protocols/agent_contract.md` 一致）：

| 错误类型 | 标识 | 触发场景 | 重试策略 | 重试次数 | 最终处理 |
|----------|------|----------|----------|----------|----------|
| Schema 错误 | `schema_error` | 输入/输出不符合 JSON Schema | 修复后重试1次 | 1 | 报告上游错误，不重复调用原 Agent |
| 文件暂时不可用 | `retryable_error` | 文件不存在（时序）、网络超时、磁盘写入失败 | 间隔后重试 | 2 | 隔离任务，通知 Orchestrator |
| 内容质量不合格 | `quality_error` | 输出通过 Schema 但质量不达标 | 交 Reviewer，不重复调用原 Agent | 0（原Agent） | 降级处理或人工介入 |
| 权限错误 | `permission_error` | 访问 write_scope 之外路径、写入受保护目录 | 立即停止 | 0 | 报告安全事件，标记 failed |
| 安全错误 | `security_error` | 提示注入、敏感数据泄露、未授权操作 | 立即停止整个工作流 | 0 | 触发 Security Auditor，通知用户 |

### 2.2 重试策略详解

#### Schema 错误 → 修复重试 1 次

```
触发：输入文件不符合 input_schema_ref
      或输出文件不符合 output_schema_ref

处理：
  1. 记录 Schema 校验失败的具体字段与原因
  2. 若是输入 Schema 错误：
     → 不重试本 Agent（上游产出不合格）
     → 报告上游 Agent 的错误
     → 标记上游任务需修复
  3. 若是输出 Schema 错误：
     → 修复后重试 1 次（可能是格式笔误）
     → 重试 1 次仍失败 → 标记 failed

理由：Schema 错误是结构性问题，盲目重试大概率犯同样的错。
      应定位根因而非重复调用。
```

#### 文件暂时不可用 → 重试 2 次

```
触发：输入文件不存在（可能时序问题，上游尚未完成）
      网络请求超时
      磁盘写入失败
      进程被意外终止

处理：
  1. 记录错误详情
  2. 等待 30 秒后重试（第一次）
  3. 等待 60 秒后重试（第二次）
  4. 两次重试仍失败 → 隔离任务，标记 failed
  5. 通知 Orchestrator 决策后续

理由：这类错误是暂时性环境问题，重试通常能解决。
      设置上限避免无限重试。
```

#### 内容质量不合格 → 交 Reviewer，不重复调用原 Agent

```
触发：输出通过 Schema 校验，但内容质量不达标
      （术语未覆盖、引用不准确、逻辑不一致、事实错误）

处理：
  1. 不重复调用原 Agent（重复调用大概率产生类似结果）
  2. 将问题交由 Reviewer Agent 审查
  3. Reviewer 生成具体的修改建议
  4. 将修改建议作为额外约束，重新调用原 Agent（计入重试）
  5. 若重试后仍不达标 → 标记 degraded，输出部分结果
  6. 在 run_report.json 中记录质量问题和降级情况

理由：质量问题是认知层面的，不是环境层面的。
      提供具体反馈后重试比盲目重试更有效。
```

#### 权限错误 → 立即停止

```
触发：Agent 试图访问 write_scope 之外的路径
      Agent 试图写入受保护目录（requirements/、agents/、config/ 等）
      Agent 试图修改其他 Agent 的输出文件

处理：
  1. 立即停止该 Agent 执行
  2. 记录安全事件到日志
  3. 标记任务为 failed（final_status: failed）
  4. 通知 Orchestrator 和 Security Auditor
  5. 不重试

理由：权限错误意味着 Agent 行为超出契约约束。
      这是安全问题，不是可重试的暂时性故障。
```

#### 安全错误 → 立即停止

```
触发：检测到提示注入（输入文件中包含伪装的指令）
      敏感数据泄露（输出中包含不应出现的隐私信息）
      未授权的危险操作

处理：
  1. 立即停止整个工作流（不只是该 Agent）
  2. 记录安全事件
  3. 触发 Security Auditor 全面审查
  4. 隔离相关输入文件
  5. 通知用户
  6. 不重试

理由：安全错误不可妥协，优先级最高（P8 防提示注入）。
```

### 2.3 重试次数与风险等级

| risk_level | max_retries | 理由 |
|------------|-------------|------|
| high | 1 | 高风险任务重试可能重复犯错，尽快报告 |
| medium | 3 | 常规任务，允许有限重试 |
| low | 5 | 低风险可重做任务，允许较多重试 |

**重要**：`max_retries` 是整个 Agent 执行的**总重试次数上限**。各错误类型的重试次数之和不得超过此值。达到上限后，输出错误报告，不静默失败。

---

## 三、降级模式表

当运行环境受限时，系统按以下降级模式运行。降级模式确保功能受限时系统仍能产出（可能质量降低），而非直接崩溃。

### 3.1 降级模式总表

| 降级场景 | 触发条件 | 降级措施 | 影响评估 |
|----------|----------|----------|----------|
| 不支持子代理并行 | AI Coding Agent 不支持 subagent 并行 | 并行任务改为顺序执行 | 性能下降，结果不变 |
| 不支持图像处理 | 环境无法处理图像 | 生成待人工确认列表，跳过图像相关任务 | 部分功能缺失 |
| 不支持联网 | 环境无网络访问 | 仅用本地资料，跳过联网检索任务 | 数据覆盖面降低 |
| Token 预算不足 | 剩余 Token 不够执行全部任务 | 减少审核环节，合并小任务 | 质量保障降低 |
| 磁盘空间不足 | 磁盘空间低于阈值 | 清理中间产物，保留最终输出 | 断点恢复能力降低 |
| Agent 频繁失败 | 多个 Agent 连续失败 | 全量审核改为风险审核，只审核高风险节点 | 审核覆盖面降低 |
| Schema 校验工具缺失 | 无 jsonschema 等校验工具 | 用基础 JSON 解析做最小校验 | 校验严格度降低 |

### 3.2 不支持子代理并行 → 顺序执行

```
检测：AI Coding Agent 不支持同时启动多个子代理

降级措施：
  - Phase 4 和 Phase 6 的并行角色改为顺序执行
  - DAG 中同一 parallel_group 的任务改为顺序执行
  - 在 workflow_state.json 中标注 "parallel_mode: sequential"

影响：
  - 执行时间增加（无并行加速）
  - 结果质量不变（顺序执行不改变逻辑）

示例：
  原计划：T4（语言审核）‖ T5（逻辑审核）并行
  降级后：T4 → T5 顺序执行
```

### 3.3 不支持图像 → 生成待人工确认列表

```
检测：环境无法处理图像（如 PDF 中的图表、扫描件）

降级措施：
  - 图像相关任务标记为 skipped
  - 生成 output/pending_images.json，记录所有待人工处理的图像
  - 在最终报告中标注"以下内容需人工处理"

影响：
  - 图像内容缺失，文档完整性降低
  - 需要人工补全

示例（pending_images.json）：
{
  "pending_items": [
    {
      "task_id": "T1",
      "image_ref": "input/paper_A_page3_figure1.png",
      "description": "数字经济规模增长趋势图",
      "context": "论文A第3页，需要提取图中数据",
      "action_needed": "人工提取图中数据并补充到 facts.json"
    }
  ]
}
```

### 3.4 不支持联网 → 仅用本地资料

```
检测：环境无网络访问（或网络不可用）

降级措施：
  - needs_internet=true 的任务标记为 degraded
  - 跳过联网检索任务
  - 仅使用本地已有资料完成任务
  - 在报告中标注"未联网，数据可能不完整"

影响：
  - 数据时效性降低
  - 无法获取最新信息
  - 适用于本地资料充足的场景

示例：
  原计划：联网检索最新政策文件
  降级后：使用本地已有的政策文件（可能过时）
         标注"数据截止日期：本地资料最后更新日期"
```

### 3.5 降级决策流程

```
检测到环境限制
    │
    ▼
评估影响范围
    │
    ▼
影响是否可接受？──────── YES ──→ 应用降级模式
    │ NO                        │
    ▼                           ▼
是否有替代方案？──────── YES ──→ 使用替代方案
    │ NO                        │
    ▼                           ▼
通知用户并请求确认 ←───────── 记录降级情况到 run_report.json
    │                           │
    ▼                           ▼
用户同意？──────── YES ──→ 继续降级执行
    │ NO
    ▼
停止执行，报告原因
```

---

## 四、状态文件格式

### 4.1 任务状态定义

每个任务在任何时刻处于以下六种状态之一：

| 状态 | 标识 | 说明 | 转移条件 |
|------|------|------|----------|
| 待执行 | `pending` | 任务尚未开始 | → running（调度器分配） |
| 执行中 | `running` | 任务正在执行 | → completed（成功）/ failed（失败）/ skipped（跳过） |
| 已完成 | `completed` | 任务成功完成，输出已落盘 | 终态（可被缓存复用） |
| 已失败 | `failed` | 任务执行失败，重试耗尽 | → pending（手动重试）/ 终态 |
| 已跳过 | `skipped` | 任务被跳过（降级或不适用） | 终态 |
| 缓存命中 | `cached` | 输入未变化，复用上次输出 | 终态（等同于 completed） |

### 4.2 状态转移图

```
                    ┌──────────┐
         ┌─────────→│ pending  │←──────────┐
         │          └────┬─────┘           │
         │               │ 调度            │ 手动重试
         │               ▼                 │
         │          ┌──────────┐           │
         │          │ running  │──失败──→──┤
         │          └──┬───┬───┘           │
         │     成功     │   │ 跳过          │
         │             │   │（降级）        │
         │             ▼   ▼               │
         │      ┌────────┐ ┌──────────┐    │
         │      │completed│ │ skipped  │    │
         │      └────────┘ └──────────┘    │
         │                                  │
         │     缓存命中                      │
         │          ┌────────┐              │
         └──────────│ cached │              │
                    └────────┘              │
                                            │
         重试耗尽                            │
         ┌──────────┐                       │
         │  failed  │───────────────────────┘
         └──────────┘
```

### 4.3 单任务状态文件

每个任务有独立的状态文件 `output/T{n}/status.json`：

```json
{
  "task_id": "T2",
  "agent": "drafter",
  "status": "completed",
  "started_at": "2026-07-27T10:05:00Z",
  "completed_at": "2026-07-27T10:12:30Z",
  "duration_seconds": 450,
  "retry_count": 0,
  "output_ref": "output/T2/draft.md",
  "output_schema": "schemas/draft.schema.json",
  "schema_validated": true,
  "cache_key": "T2:a3f5e8d9c2b10467",
  "input_hash": "a3f5e8d9c2b10467",
  "error": null,
  "warnings": []
}
```

### 4.4 失败任务状态文件

```json
{
  "task_id": "T4",
  "agent": "language_reviewer",
  "status": "failed",
  "started_at": "2026-07-27T10:15:00Z",
  "failed_at": "2026-07-27T10:18:32Z",
  "duration_seconds": 212,
  "retry_count": 2,
  "final_status": "failed",
  "error": {
    "error_type": "schema_error",
    "category": "schema_error",
    "message": "输出缺少必填字段 'summary'",
    "failed_field": "summary",
    "schema_ref": "schemas/review.schema.json"
  },
  "partial_output": "output/T4/review_partial.json",
  "warnings": [
    "重试2次后仍失败，已隔离此任务",
    "后续T6将标注'缺少语言审核结果'"
  ]
}
```

### 4.5 全局状态文件

Orchestrator 维护全局状态文件 `output/workflow_state.json`，汇总所有任务状态：

```json
{
  "workflow_id": "WF-20260727-001",
  "run_id": "run_20260727_100000_001",
  "started_at": "2026-07-27T10:00:00Z",
  "last_updated": "2026-07-27T10:20:00Z",
  "overall_status": "running",
  "parallel_mode": "parallel",
  "tasks": {
    "T1": {
      "status": "completed",
      "output_ref": "output/T1/facts.json",
      "completed_at": "2026-07-27T10:03:15Z"
    },
    "T2": {
      "status": "completed",
      "output_ref": "output/T2/draft.md",
      "completed_at": "2026-07-27T10:12:30Z"
    },
    "T3": {
      "status": "completed",
      "output_ref": "output/T3/draft.md",
      "completed_at": "2026-07-27T10:14:00Z"
    },
    "T4": {
      "status": "failed",
      "error": "schema_error: 缺少必填字段 summary",
      "failed_at": "2026-07-27T10:18:32Z"
    },
    "T5": {
      "status": "completed",
      "output_ref": "output/T5/review_logic.json",
      "completed_at": "2026-07-27T10:16:45Z"
    },
    "T6": {
      "status": "pending",
      "depends_on": ["T4", "T5"],
      "note": "T4失败，T6将降级执行（缺少语言审核）"
    }
  },
  "summary": {
    "total_tasks": 6,
    "completed": 4,
    "failed": 1,
    "pending": 1,
    "skipped": 0,
    "cached": 0
  }
}
```

### 4.6 断点续跑的状态恢复

中断后重新启动时，Orchestrator 读取 `workflow_state.json`：

```
恢复逻辑：

1. 读取 workflow_state.json
2. 对每个任务：
   - status == "completed" → 跳过，复用 output_ref
   - status == "cached" → 跳过，复用 output_ref
   - status == "running" → 重新执行（幂等性保证安全）
   - status == "failed" → 根据重试策略决定是否重试
   - status == "pending" → 正常执行
   - status == "skipped" → 保持跳过
3. 按DAG依赖顺序，执行所有需要执行的任务
4. 更新 workflow_state.json
```

---

## 五、Orchestrator 失败处理决策

### 5.1 决策树

当 Orchestrator 检测到任务失败时，按以下决策树处理：

```
任务 T 失败
    │
    ▼
T 在关键路径上吗？
    │
    ├── YES ──→ 重试 T（最多 max_retries 次）
    │              │
    │              ├── 重试成功 → 继续
    │              │
    │              └── 重试失败 → 后续任务依赖 T 吗？
    │                               │
    │                               ├── YES → 标记后续为 blocked
    │                               │        通知用户
    │                               │
    │                               └── NO → 降级处理
    │
    └── NO ───→ 后续任务依赖 T 吗？
                   │
                   ├── YES → 标记后续为 blocked
                   │        继续其他任务
                   │
                   └── NO → 标记 T 为 failed
                            继续其他任务
                            在报告中标注风险
```

### 5.2 降级执行示例

```
场景：T4（语言审核）失败，T6（汇总）依赖 T4 和 T5

T4 失败 → status: failed
T5 完成 → status: completed

Orchestrator 决策：
  - T4 不在关键路径（审核是建议性的）
  - T6 可以缺少 T4 的结果（降级执行）

T6 降级执行：
  - 输入只有 T5 的结果（缺少 T4）
  - 输出标注"缺少语言审核"
  - final_quality_score 降低
  - 在 run_report.json 的 open_issues 中记录
```

---

## 六、错误处理检查清单

### 6.1 执行前检查

- [ ] 所有任务的 `max_retries` 已设置且与 `risk_level` 匹配
- [ ] 所有任务的 `error_types` 已定义且包含五大错误类型
- [ ] 状态文件目录（`output/`）可写
- [ ] 磁盘空间充足（预留输出大小的 2 倍）
- [ ] 全局状态文件 `workflow_state.json` 已初始化

### 6.2 执行中检查

- [ ] 每个任务执行前状态为 `pending`
- [ ] 每个任务执行中状态为 `running`
- [ ] 文件写入采用原子写入（临时文件 + 替换）
- [ ] 失败任务的状态独立记录，不影响其他任务
- [ ] 重试次数不超过 `max_retries`

### 6.3 执行后检查

- [ ] 所有任务状态已更新（无 `running` 残留）
- [ ] 失败任务有错误详情记录
- [ ] 降级执行的任务有标注
- [ ] `run_report.json` 的 `failures` 数组完整
- [ ] `open_issues` 包含所有未解决问题
- [ ] 断点续跑测试通过（中断后可恢复）
