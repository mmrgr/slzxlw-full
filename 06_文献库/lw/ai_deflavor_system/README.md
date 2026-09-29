# 去AI味系统

## 系统简介

本系统是一个**去AI味文本处理系统**。用户提交AI生成的文本（小说、论文、文章），系统通过6个Agent协作分析AI味特征、执行人性化修改、模拟检测验证，输出低AI率的文本。系统采用"检测-修改-模拟检测"的迭代流程（最多3轮），确保最终文本能通过主流AI检测工具（GPTZero、Turnitin、知网AIGC等），同时严格保持原意、逻辑和数据准确。

---

## 核心特性

| 特性 | 实现方式 |
|------|----------|
| **全面检测** | 基于AI味特征知识库，六大类特征（结构/词汇/统计/逻辑/情感/文体）逐项扫描 |
| **靶向修改** | 不是盲目重写，而是针对检测报告中标注的特征精准修改，每处修改可追溯 |
| **三路并行** | Phase 2中结构重组、语言人性化、逻辑深化三个Agent同时工作，互不冲突 |
| **多轮迭代** | 修改→模拟检测→再修改，最多3轮，每轮修改密度递减，直到AI率达标 |
| **文体适配** | 学术论文/小说/新闻/博客四种文体，不同策略和AI率阈值 |
| **记忆进化** | 记录哪些修改策略有效/失败，越用越精准 |

---

## 6个Agent角色

| Agent | 角色 | 核心职责 | 活跃阶段 |
|-------|------|----------|----------|
| **ai_detector** | AI特征检测员 | 扫描文本，识别AI味特征，生成检测报告 | Phase 1（每次迭代开头） |
| **structure_reorganizer** | 结构重组师 | 打破AI结构模式（三明治/三段式/均匀段落） | Phase 2（并行） |
| **language_humanizer** | 语言人性化师 | 词汇替换+句式变化+情感注入+标点个性化 | Phase 2（并行） |
| **logic_enhancer** | 逻辑深化师 | 打破完美逻辑链，引入矛盾/反例/不确定性 | Phase 2（并行） |
| **detection_simulator** | 检测模拟员 | 模拟GPTZero/Turnitin/知网检测，7维度评分 | Phase 3（每次迭代结尾） |
| **quality_controller** | 质量把控师 | 合并3路修改，确保原意/逻辑/数据不被破坏，终审 | Phase 2（合并）+ Phase 3（终审） |

> **编排者（Orchestrator）**：quality_controller（质量把控师），负责Phase 2合并与Phase 3终审，是系统质量最后一道防线。

---

## 3阶段流程图

```
用户提交文本 + 文体类型 + 目标AI率
    │
    ▼
Phase 1: AI味检测 ──────────── AI特征检测员
         （串行，深度思考）
         输出：detection_report.json（AI味特征清单 + 严重程度 + 位置标注）
              │
              ▼
Phase 2: 人性化修改 ── 结构重组师 ────┐
         （3路并行）   语言人性化师 ──┤── 互不依赖，同时工作
                       逻辑深化师 ───┘
              │
              ▼
         质量把控师（合并3路修改，解决冲突，检查一致性）
              │
              ▼
Phase 3: 检测模拟 ──────────── 检测模拟员
         （串行，深度思考）
         输出：simulation_report.json（7维度评分 + AI率 + 高风险清单）
              │
         AI率达标? ──是──→ 质量把控师终审 → 输出最终文本
              │
              否
              │
              ▼
         回到 Phase 1（最多3轮迭代）
```

**迭代控制**：

| 轮次 | 修改密度 | 说明 |
|------|----------|------|
| 第1轮 | 全面修改 | 处理所有高/中/低严重度特征 |
| 第2轮 | 重点修改 | 仅处理高严重度和上轮残留高风险段落 |
| 第3轮 | 微调 | 仅处理上轮检测模拟标记的具体问题 |

---

## 如何使用

### 对 AI Coding Agent 说

```
请阅读 ai_deflavor_system/AGENTS.md，
然后帮我去除以下文本的AI味：

[粘贴文本]

文本类型：[学术论文/小说/新闻/博客]
目标AI率：[10%/15%/5%]
```

### 输入要求

| 参数 | 必填 | 说明 |
|------|------|------|
| 文本内容 | 是 | 需要去AI味的文本 |
| 文本类型 | 是 | 影响修改策略和目标AI率（学术论文/小说/新闻/博客/其他） |
| 目标AI率 | 否 | 默认：学术论文15%、小说5%、新闻10%、博客10% |
| 特殊要求 | 否 | 如"保留所有引用""不要加个人经历"等 |

### 输出内容

```
输出/
├── 最终文本.txt              ← 去AI味后的文本
├── 修改对照表.md             ← 原文vs修改后，逐处对照
├── 检测报告_round1.json      ← 第1轮检测报告
├── 检测报告_round2.json      ← 第2轮检测报告（如有）
├── 模拟检测_final.json       ← 最终模拟检测报告
└── 处理摘要.md               ← 处理过程摘要
```

---

## 文体特殊处理

| 文体 | 目标AI率 | 重点维度 | 允许的AI特征 | 关键策略 |
|------|----------|----------|-------------|----------|
| **学术论文** | <15% | 词汇模式、逻辑模式 | 适度结构化、被动语态（方法部分） | 方法部分容忍结构化；讨论部分重点人性化；文献综述改叙事式；保留所有引用和数据 |
| **小说/创意写作** | <5% | 情感模式、突发性 | 极少，需最大化人性化 | 对话口语化且有角色特征；描写含感官细节；情感有层次不直说；允许碎片化、意识流 |
| **新闻文章** | <10% | 结构模式、情感模式 | 基本新闻结构（倒金字塔） | 导语可保留基本结构；正文有现场感；引用有姓名职务 |
| **博客/自媒体** | <10% | 词汇模式、结构模式 | 适度结构化 | 强烈个人风格；语言更口语化；结构更灵活 |

---

## 目录结构

```
ai_deflavor_system/
├── AGENTS.md                          ← AI Coding Agent 执行入口
├── README.md                          ← 本文件（系统说明）
├── agent_manifest.json                ← Agent清单（6个Agent定义）
├── workflow.json                      ← DAG工作流（7个task的依赖关系）
├── knowledge/                         ← 知识库（3个文件）
│   ├── ai_signatures.md               ← AI味特征知识库
│   ├── detection_rules.md             ← AI检测规则手册
│   └── humanization_techniques.md     ← 人性化技术手册
├── schemas/                           ← 数据格式（3个JSON Schema）
│   ├── detection_report.schema.json   ← 检测报告Schema
│   ├── simulation_report.schema.json  ← 模拟检测报告Schema
│   └── modification_record.schema.json← 修改记录Schema
├── config/                            ← 配置
│   └── system_config.yaml             ← 系统配置文件
├── memory/                            ← 记忆系统（4个JSON + 说明）
│   ├── effective_strategies.json      ← 有效策略记录
│   ├── failed_strategies.json         ← 失败策略记录
│   ├── text_patterns.json             ← AI味模式记录
│   ├── user_preferences.json          ← 用户偏好
│   └── README.md                      ← 记忆系统说明
├── tests/
│   └── system_validation.md           ← 系统验证
└── reports/
    └── generation_report.md           ← 生成报告
```

---

## 与 Agent Factory 的关系

本系统基于 [Agent Factory](../agent_factory/) 框架生成。Agent Factory 提供了多Agent系统的设计范式、工作流规划原则、质量保障框架和记忆系统架构。

- **架构原则对齐**：遵循最小权限（read_scope/write_scope）、单写者（并行Agent写权限不重叠）、确定性优先（Schema校验）。
- **角色定义**：6个Agent的定义参考了 Agent Factory 的 `templates/agent_roles/` 和 `agents/agent_designer.md` 模式。
- **工作流规划**：DAG工作流参考了 `agents/workflow_planner.md` 和 `protocols/parallel_rules.md`。
- **质量保障**：质量检查清单和不可修改内容清单参考了 `core/quality_assurance.md` 和 `core/safety_rules.md`。
- **记忆系统**：记忆文件设计和更新规则参考了 `agents/memory_curator.md` 和 `memory/README.md`。
- **深度思考**：Phase 1检测和Phase 3模拟的深度思考集成参考了 `thinking/deep_thinking_protocol.md`。

**格式扩展说明**：为适配去AI味场景，本系统的 agent_manifest.json 与 workflow.json 在字段上做了语义化扩展（如 responsibilities 为数组、parallel_group、iteration_config 等），与 Agent Factory 原始 JSON Schema 非严格一致，但均为合法JSON。

---

## 设计哲学

1. **检测先于修改**：不盲目重写，先通过系统化检测定位AI味的具体位置和类型，再靶向修改。每处修改都有据可查。
2. **分而治之**：将AI味问题拆解为六大类，由三个修改Agent分别处理不同类别（结构/语言/逻辑），互不冲突，可并行执行。
3. **迭代逼近**：修改不可能一步到位。通过"修改→模拟检测→再修改"的闭环迭代，每轮聚焦上轮残留问题，逐步逼近目标AI率。
4. **质量底线不可妥协**：无论AI率多么诱人，原意、数据、引用、术语不可修改。质量把控师作为编排者守护这条底线。
5. **文体差异化**：不同文体有不同的"正常"标准。学术论文允许适度结构化，小说需要最大化人性化。一刀切只会适得其反。
6. **记忆驱动进化**：系统记录哪些策略有效、哪些失败，随着使用积累越来越精准。记忆系统是系统的"经验"。
