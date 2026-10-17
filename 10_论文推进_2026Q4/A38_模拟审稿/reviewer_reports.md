# 模拟审稿意见（红队）· AI-UWM 项目

> ⚠️ **本文件含 2026-10-17 之前的历史数字**（如 n=813、643/134/36）。
> 当日修复 P0-1（Figshare 水样回灌 A19 提取的 SO4/碱度）后，现行值为
> **n=839、626/177/36、q 分组 263/288/288**。
> 本文件作为审计留痕保留原值，**当前结论请以主稿与 SI 为准**。
## Simulated Peer Review Reports — Adversarial (Red Team)

> **审查对象**：`A16_英文稿/manuscript_en_v3.md`（内容 v4，772 行）、`A16_英文稿/supplementary_information.md`（785 行）、`A37_六主图_v4/`（6 图 + 6 图注 + `figure_index.md`）、`A30_WP0取证/证据台账_EVIDENCE_LEDGER.md`、`A36_终审/终审门禁报告与期刊匹配评估.md`，以及 `A31`–`A34` 各 WP 报告与机器产物。
> **审查日期**：2026-10-16
> **审查立场**：Nature Water / Nature Communications 严格审稿人。**不客气，但每条批评均指向实际读过的文件与行号/数值。**
> **声明**：本项目在诚实性上远高于同类投稿（主动撤回、负结果上报、机器门禁）。**但诚实性不是可发表性。** 下述批评集中在「能否支撑所声明的普适性」这一根本问题。

---

## 全局交叉核对结果（三份审稿意见共用的证据基础）

以下为本次审查中**实际复算**的关键事实，三份意见均引用之。

| # | 复算项 | 复算结果 | 与主稿是否一致 |
|---|---|---|---|
| V1 | 可靠子集 $n$ | 813 / 1052 行（双门禁） | ✅ 一致 |
| V2 | 严格符号计数 | 643 负 / 134 正 / **36 零**（$n=813$） | ✅ 与 §3 正文一致 |
| V3 | **§3 的 $q$ 分组表（L164–168）实际口径** | 列合计 = 290+208+133+0+0+102 = **733 行**，非 813 | ❌ **与表头 $n=813$ 矛盾**（见 Major M1） |
| V4 | $q=0$ 组严格口径 | 220 负 / 32 正 / 36 零（$n=288$） | ❌ 与表内 208/0 不符（表中少 32 正例与 36 零） |
| V5 | $q>0$ 组有害数 | **0 / 290** | ✅ 一致 |
| V6 | 独立期望有害数（若 $q$ 与符号独立） | 290/813 × 134/813 × 813 ≈ **47.8 例** | — 0 例观测（Fisher $p\approx9.5\times10^{-22}$） |
| V7 | $q>0 \Rightarrow$ 受益，但全样本受益率 | **0.791**；$q\le0$ 组受益率 0.675 | ⚠️ 主稿未报基率（见 Major M2） |
| V8 | **WP4 完整水样网格（47 例）** | $q>0$ 组 23/23 有害=0；**$q\le0$ 组 24/24 有害亦=0** | ❌ **该检验完全空洞**（见 Major M2） |
| V9 | E3b 折外增益逐折分解 | AI-UWM **+0.0000**、LADWP **+0.0000**、Figshare **−0.0177**、IEUA **+0.1837** | ❌ 4 折中 3 折无效或为负（见 Major M3） |
| V10 | E3b 折外均值 +0.0415 的来源 | **全部来自 IEUA 单一折** | ❌ 主稿称为"genuine skill"（L265–269） |
| V11 | `pool_scale` 的阈值稳健性（$n_{\rm eff}=733$） | ≥1.2: 0.891 / **≥2.0: 0.906** / ≥2.2: 0.873 / ≥2.4: 0.835 / ≥3.0: 0.753 | ❌ 阈值 2.0 为刀锋点（见 Major M3） |
| V12 | `pool_scale` 值域 | {0.5, 1.0, 1.5, 2.0, 2.2, 2.4, 2.6, 3.0, 4.0}，**每个水样完全相同** | ❌ 是合成扫描轴，非独立城市观测（见 Major M4） |
| V13 | 极端事件"1.139×"口径 | 为 **per-day** 比值；绝对量 full-year/heatwave = 7585/438 ML，**比值 0.058** | ❌ 主稿未标 per-day（见 Major M5） |
| V14 | 极端事件符号 | 观测驱动 4 窗类 × 2 水样 × 2 域，**全部为负**，0 翻转 | ✅ 一致 |
| V15 | "唯一符号杠杆"检验条件 | 固定于**单一冻结点**（$\varphi=0.6$、$\chi=1$、$\mathrm{CoC}_{\rm design}=5$、2 域 × 2 水样） | ❌ 非全局（见 Major M6） |
| V16 | SI 残留 stale 数字 | SI L390"R² = **0.558**"；SI L184 表"$dS<0$=**631**" | ❌ 与主稿 0.806 / 643 矛盾（见 Major M7） |
| V17 | SI 标题 vs 主稿标题 | SI L3 = "**Supply state, not cooling technology**, governs…"；主稿 L1 = "**What Governs the Urban Water Outcome…**" | ❌ 标题不一致 |
| V18 | SI §S3.3 vs A32/WP3 §3.2 物种数 | SI L253 "IEUA 和 LADWP are complete (**5/5**)"; A32 L89–90 IEUA **9**、LADWP **8** | ❌ SI 自相矛盾 |
| V19 | 温度缺失影响 | 主稿 L664 "can shift CoC by **−30%**" | ⚠️ 无产物可复算（见 Minor） |
| V20 | 图注 n 与正文 n | 图注标 $n_{\rm eff}=733$（Fig.4）/ 813（Fig.3）；正文 §3d 亦为 733 | ✅ 一致 |
| V21 | 部分识别界 | `a24b_partial_id_summary.json`: lower 0.0, upper 100.0 | ✅ 一致 |
| V22 | Fig. 6 视觉呈现 | Panel a 明确 "NOT IDENTIFIABLE / provable bound [0%, 100%]"，无点估计、无 CI | ✅ **无暗示**——该条批评不成立 |

---

# 审稿意见 1 · 审稿人 1（水系统 / 政策视角）

**Reviewer 1 — Urban water systems, infrastructure policy**

## 总体评价

本文提出的三分账（requested / delivered / abstracted）与统一恒等式 $dS_{\rm pot}=C-F$ 在城市水核算上是有价值的澄清，作者对"旧设施—城市恒等式其实是完全承诺分支"的重述（L144–145）是克制且正确的。作者主动撤回"95% 真实设施已承诺"（L496–507）与"更干净⇒更省水"（L672–677）两项主张，诚实程度在我审过的稿件中位居前列。

**然而，正因为诚实，本文的可发表内容被压缩得比作者意识到的更少。** 本文对政策读者的核心承诺——"什么决定再生水冷却的城市净效应"——最终只能回答"取决于一个我们无法观测的需求侧变量"。这不是一篇 Water 类论文能接受的落点。更严重的是，**全文最强的政策化表述（L65–66"result is thus relevant to most real systems"）与本文自己的部分识别结论直接冲突**。

## 主要问题（Major）

**M1-1. "relevant to most real systems"（L64–66）是未识别的市场断言，应当删除。**
摘要 L64–66 写："The result is thus relevant to most real systems, while the supply-expansion route that does reduce withdrawal is realistic only for the largest ones." 但同一摘要 L58–63 刚刚声明 committed 占比"**not identified**，界 [0%,100%]"。既然**两个分支的占比都不可识别**，作者**没有资格**断言本文结果"relevant to most real systems"——这正是一个需求侧占比陈述。**这与本文核心的诚实性主张自相矛盾。**
> **应改为**："The mechanism we identify applies to any system whose quality constraint binds and whose reclaimed pool is committed; **how prevalent that configuration is cannot be determined from the data we have**, and we therefore do not estimate it."

**M1-2. §6 与 §6b 的政策叙事实际上是"大厂才有救"的容量论，但该结论建立在模型的阈值回解上，而阈值的定义本身经过事后调整。**
L521–524 载明：作者**弃用**闭式阈值 `elig/P0`（2.384/2.567），改用"经验测得"的 `pool_scale` = 2.0，理由是"闭式值会高估所需供水量"。但 `pool_scale=2.0` 是**合成网格上的一个扫描点**（V12），且 V11 显示阈值 ≥2.2 时准确率即从 0.906 掉到 0.873、≥2.4 掉到 0.835。**用一条精度对阈值高度敏感的扫描线去推"2.1–6.6% 的厂具备产能"（L513–516），这条百分比本身带有一个未被量化的阈值不确定性。** 换用闭式阈值，该比例会系统性变小；换用 2.4，会变大。作者应当给出**阈值区间对应的比例区间**，而不是单一区间。
> **补救（不需新实验）**：报出 $r$ 表在阈值 ∈ {2.0, 2.384, 2.567} 下的比例区间，并把 L513–516 的"2.1–6.6%"改为区间值。

**M1-3. 全球外推的语言掩盖了数据来源是**中国 10,826 座污水厂**，而模型域是合成城市。**
L432–438 与 S6b 把该数据集作为"external anchoring"，L456 说"above-median reclaimed-water provision"。但该数据集的**处理量分布**（中位 3.0 ML/d）与中国城镇污水厂规模结构有关，而模型的两个域（D-HA/D-CO）是**同源合成**域（L655 自承"Two homologous synthetic domains"）。**把中国污水厂的处理量分布与合成模型的供水量参数对比，得到"81st percentile"（L456）这一结论，其解释力远低于行文给人的印象**：它只说明"我们的参数不是离谱的"。作者已在 L469–473 作了限定，但摘要 L56–58 又一次以"Anchoring against a public dataset of 10,826 observed wastewater treatment plants"起头，读者会读成外部验证。
> **应改为**：摘要中明确写"**parameter-range check, not validation**"，并把"most plants retain spare treatment capacity (median utilisation 0.594)"（L57–58）这一**供给侧**事实与**本文的需求侧机制**之间的断裂写清楚——本文已识别该断裂（L462–467），但摘要中缺失。

**M1-4. 公平性维度（O2：既有用户服务缺口）在正文中被声明却未被报告。**
`WP2_假设与主估计量冻结.md` §3 明确列出四类结局，并特别标注 O2"**可能 O1 改善而 O2 恶化**"——这正是政策读者最关心的问题。但主稿 Results 全篇只报 $dS_{\rm pot}$（O1），O2 只在 L365–374 的"necessary-service gap"中间接出现，且**没有任何按组成/分场景的 O2 分布**。对一篇 Water 政策论文，**"谁的水被拿走了"是核心问题，不能只作为 $M_0-M_1$ 的副产品出现**。
> **补救（不需新实验）**：从既有 `supply_state_regimes.csv` 的 `inc_B1_ml`/`inc_B2_ml` 直接产出 $r_{\rm inc}$ 变化的分布，作为新的 SI 小节与 Fig. 3 的附加面板。**这是本文最明显的"唾手可得却未做"的分析。**

## 次要问题（Minor）

- **m1-1.** L21–22 摘要称"68 engine runs"，但 L76 与 L732 亦为 68；`A30_WP0取证` 未见 68 的独立核验产物。请提供 run 清单。
- **m1-2.** L450"urban water price (n = 39,083), median 1.45 CNY/m³"与本文零成本分析无关（L663 自承"no cost claim is made"）。建议删除，或明确其为背景信息。
- **m1-3.** L446"industrial cooling-water share"用"mean of sector means"，未加权，且 39 个部门的等权平均是否代表全国用水结构存疑。至少应披露权重缺失。
- **m1-4.** L629–633 与 Wang et al. (2026)、Han et al. (2026)、Shen et al. (2026) 的关系陈述为定性；L632"we make that dependence a **measurable threshold**"是本文**最强的优先权主张**，但该阈值正是 M1-2 所指的不稳健量。建议弱化为"a threshold within our modelled envelope"。
- **m1-5.** 摘要 L26–28"by up to 27,354 ML per period"给出单一极值。政策读者需要的是分布而非极大值；建议同时给中位变化。

## 建议决定

> ## **大修（Major Revision）** — 若 M1-1、M1-3、M1-4 得证，可再议；否则 **拒稿**。

理由：方法学诚实度高，但**摘要的政策化表述（M1-1）与本文核心的不识别结论直接冲突**，且**公平性维度（M1-4）缺失**。这两点在 Water 类期刊是实质性缺陷。若作者把 M1-1 删除、M1-4 补齐、M1-2/M1-3 改为区间与限定语，本文对该刊的适配度会显著上升。

---

# 审稿意见 2 · 审稿人 2（方法学 / 统计视角）

**Reviewer 2 — Methodology, statistics, identification**

## 总体评价

作者对认识论地位的自我分级（`证据台账` §D 的 E1–E5，L76–87 SI §S11）是**教科书级的诚实**，把恒等式与预测严格区分、并主动报告负结果（0.671 < 0.861），这在环境建模文献中极为罕见。门禁体系的自我审计（SI §S15 十一条）也值得肯定。

**但本文的核心"正结果"——§3d 的 0.901 vs 0.859——在统计上站不住。** 我在复算后认为，**这个数字不应以现在的形式出现在摘要中**。此外，本文存在**多处内部口径矛盾**，其中一处（$q$ 分组表）足以让审稿人质疑全文其他数字的可靠性。

## 主要问题（Major）

**M2-1.【最严重】§3 头条表（L164–168）与本文自己声明的"严格符号约定"不符，列合计只有 733 行却被标为 $n=813$。**

我按 `A13_可靠性机制/supply_state_regimes.csv` 复算（双门禁后 $n=813$）：

| $q$ 组 | 表内 n | 表内"falls" | 表内"rises" | **严格口径实际（负/正/零）** |
|---|---:|---:|---:|---|
| $q>0$ | 290 | 290 | 0 | 290 / 0 / 0 ✅ |
| $q\approx0$ | 288 | **208** | **0** | **220 / 32 / 36** ❌ |
| $q<0$ | 235 | 133 | 102 | 133 / 102 / 0 ✅ |
| **合计** | **813** | **631** | **102** | 643 / 134 / 36 |

表中"falls+rises"合计 = 631+102 = **733**，与表头 $n=813$ **差 80 行**——正是 L187–191 与 L249–250 承认的"被 $|dS|\le10^{-9}$ 容差带静默丢弃的 80 个近零情景"。**换言之：本文在 L184–191 郑重声明采用严格符号约定、并批评旧口径"silently drops 80 near-zero scenarios while still labelling the sample as 813"，然后在本节自己的头条表里原封不动地保留了那个旧口径。** 而且 $q\approx0$ 组漏掉的不是 80 个"零"，其中 **32 个是明确的有害（正）案例**——这直接改变"$q\approx0$ 组 0 harmful"这一视觉印象。

> **必须修改**：把 L164–168 表改为严格三列（负/正/零），$q\approx0$ 行填 **220 / 32 / 36**；或在表下显式注明"本表沿用容差口径、合计 733"并给出严格口径对照。**现状是不可接受的——它使本文最重要的"口径统一"主张失去说服力。** 相应地，L167 的"0"不应再作为 $q\approx0$ 组无有害案例的证据；摘要中任何依赖"$q>0$ 之外也有伤害"的表述需复核。
> 注：头条结论"$q>0$ ⇒ 0/290 有害"**不受影响**（V5 已验），这一点应当明说以限制损害范围。

**M2-2.【严重】"$q>0$ 是充分条件"在完整水样网格上完全空洞，但主稿未把这一事实放在该结论旁。**

主稿 L170 以加粗宣称"**$q>0$ is a sufficient condition for a city-level benefit: 290 of 290, with no exception.**" SI §S10 §5（L615–617）与 A32/WP3 §2（L66–71）**都已承认**：在完整水样网格（$n_{\rm eff}=47$）上 $dS_{\rm pot}$ **无任何正例**，故 $q>0\Rightarrow$ 受益是"空洞通过"，因为 $q<0\Rightarrow$ 受益**同样成立**。我复算确认：WP4 可靠 47 例中，$q>0$ 组 23/23 有害=0，**$q\le0$ 组 24/24 有害也=0**（V8）。

但主稿 L408–415 在呈现完整水样结果时，仍写"The two complete-composition samples diverge in the direction of $q$… which is the defensible composition result"，**没有说明该网格对符号检验零鉴别力**。更关键的是：主稿的主网格（813）上，**全样本受益率高达 0.791**（V7）——即"预测受益"这一常数规则本身就有 79% 准确率。在这个基率下，"290/290 无例外"的信息量远小于字面印象。（我在 $n=813$ 上做 Fisher 精确检验得 $p\approx9.5\times10^{-22}$，说明 $q$ 与符号**并非独立**——这一点**对作者有利**，但主稿完全没有报基率、没有报检验、没有说 47 例子集空洞——三重缺失并存。）

> **必须修改**：L170 后立即加入（i）全样本受益基率 0.791；（ii）完整水样子集该检验空洞的事实；（iii）$q$ 与符号的关联检验（Fisher $p$）及其对"非独立"的支持。**只报 290/290 而不报基率，是选择性报告。**

**M2-3.【最致命】§3d 的折外 0.901 vs 0.859 由**单一折**驱动，且其中两折的基线饱和至 1.000——该结果不构成"genuine out-of-sample skill"。**

我逐折复算 `wp2_e3b_combined_prediction_summary.json`（V9）：

| 留出样本 | $n$ | C4 准确率 | 多数类基线 | **增益** |
|---|---:|---:|---:|---:|
| AI-UWM model assumption（2 物种，不完整） | 184 | 1.0000 | **1.0000** | **+0.0000** |
| LADWP AWPF（完整） | 183 | 1.0000 | **1.0000** | **+0.0000** |
| IEUA RP-1（完整） | 196 | 0.9388 | 0.7551 | **+0.1837** |
| Figshare RW（不完整） | 170 | 0.6647 | 0.6824 | **−0.0177** |
| **均值** | 733 | **0.9009** | **0.8594** | **+0.0415** |

**四点致命问题：**

1. **两折的基线是 1.000**（该样本内 100% 情景都受益），因此"增益 = 0"是**构造性的**，不携带任何信息。均值基线 0.859 被这两个饱和样本抬高——**去掉它们，真实基线是 (0.755+0.682)/2 = 0.719，而 C4 是 (0.939+0.665)/2 = 0.802**，增益变为 +0.083 但**其中一折为负**。
2. **全部 +0.0415 来自 IEUA 一折。** 三折（AI-UWM、LADWP、Figshare）的贡献是 0、0、−0.018。主稿 L265–269 却写"**critically — 0.901 out-of-sample versus a 0.859 out-of-sample baseline … so this is not post-hoc selection**"。**单折驱动的均值不是"genuine skill"，也不是"not post-hoc selection"的证据。**
3. **C4 判据是在全样本上被选中的**（摘要表 C1–C6 中 C4 胜出，L247），随后才做留一验证。留一验证中每折都"picked C4"——但这是因为**候选池里 C4 在训练折上也最优**，属于**同一判据在几乎相同数据上的重复评价**，不是独立检验。
4. **"leave-one-sample-out" 的四折并非独立**：$4\ \varphi\times9$ `pool_scale` $\times$ 2 域的**参数网格对每个水样完全相同**（V12）。留出的是化学组成，**参数空间没有任何外推**。

> **必须修改**：摘要 L43–44 与 L266–269 **不得**再以"0.901 vs 0.859"作为正向预测能力的证据。应改为：
> "Under leave-one-composition-out validation the combined criterion reaches 0.901 against a 0.859 baseline, **a gain that originates entirely in one of the four folds (IEUA, +0.184) while two folds are saturated (baseline 1.000, gain 0.000) and one is negative (Figshare, −0.018)**; with four folds and a partially shared parameter grid, this does not establish transferable out-of-sample skill." 
> 并把该表述从 Abstract / Discussion §6 移入 Limitations。

**M2-4. C4 的阈值 `pool_scale ≥ 2` 是刀锋点，且 `pool_scale` 是模型的规划/扫描量而非独立观测——两者叠加构成自证。**
- **阈值敏感**（V11）：≥1.2 → 0.891；**≥2.0 → 0.906**；≥2.2 → 0.873；≥2.4 → 0.835；≥3.0 → 0.753。阈值 2.0 处正好是准确率峰值，而该阈值是**从同一模型的计算网格上读取的**（L480–483"the threshold `pool_scale` times the model's per-day base supply"，并自承"Measured empirically"）。**判据的阈值由被预测系统的输出决定，构成循环。**
- **`pool_scale` 不是外部观测**，而是合成扫描轴（V12），四个水样取值完全相同。它之所以"有效"，本质是因为**大池 ⇒ 不挤占 ⇒ 受益**，这是恒等式的直接分支结构（本文 §2 已亲自证明）。

> **必须修改**：L265–277 与摘要 L42–44 应明确标注该判据等价于在恒等式的一个分支条件上分类，**并用 `pool_scale` 的外部可得性（L692–695 Limit 13 已写）与阈值敏感性（本意见 V11）作为上下界**。建议补做：报出阈值 ∈ [1.2, 2.4] 时折外准确率的区间，而非单点 0.901。

**M2-5. 无置信区间、无多重比较校正、无 $p$ 值——全文零推断统计。**
通篇（主稿 772 行、SI 785 行）**未出现任何置信区间或 $p$ 值**。§3 的七判据比较、§7a 的十二参数 Morris/Sobol 排序、§6b 的五个 $r$ 档比例，均无不确定性报告。Sobol 的 $S_T$（`limit_scale` 0.944、alkalinity 0.682）来自 **256 样本**的 Saltelli 设计且**做了 12→7 维降维**（SI 未载，`wp5_sensitivity_summary.json` 载 `dimension_reduction.n_used=7`），降维后的指数与全维不可比——主稿 L544 的 $\sum S_1\approx0.22$ 因此是**7 维口径**下的量，却被用来支持"强交互"的一般性陈述。
> **补救**：对 Sobol 指数给 bootstrap CI；明确降维口径；对"7 判据选最优"等选择步骤做置换检验或声明为探索性。

**M2-6. 图与文的一致性存在残差：SI 与主稿在多个数字上直接冲突。**
- **SI L390** 仍写"the genuine out-of-sample number is **0.558**"，而主稿 L591 与 SI L595 均将 0.806 定为权威值（V16）。**SI 内部自相矛盾**（L374 写 0.806，L390 写 0.558）。
- **SI L184 表**的"$dS<0$ = **631**"未同步为 643（V16）。
- **SI L227** 写"best of seven predictors: **0.768**"，而 SI L240 自己的表与主稿 L228 均为 **0.803**（V18 相关）。
- **SI L3** 的标题为"Supply state, not cooling technology, governs…"，与主稿 L1 标题完全不同（V17）。
- **SI L253**"IEUA and LADWP are complete (**5/5**)"与 A32/WP3 L89–90 的"IEUA **9** 物种、LADWP **8** 物种"冲突（V18）。

> 这五项每一项单独看是笔误级别，但**它们出现在一份以"数字可追溯"为核心卖点的稿件中**，审稿人会据此推断复核流程失效。**必须在投稿前逐项同步。**

## 次要问题（Minor）

- **m2-1.** L249–250 与 L636–637 都说 $n_{\rm eff}=733$ 是"813 less 80 within a $10^{-9}$ ML tolerance of zero"。但 813 − 80 = 733 这一算法与 L186–191 声明的"严格符号"口径**互斥**（严格口径不给 36 个精确零单列则不减 80）。请统一为：严格口径 643/134/36（$n=813$），如另做 733 的分析须**明示这是第二套口径**。
- **m2-2.** L321–324 的"catastrophic cancellation"说明很有价值，但结论"Gates on such quantities must use **relative** tolerances"仅在 $M_0,M_1$ 同量级时成立；若 $M_0/M_1\to1$，相对残差的分母本身趋零。建议改为"relative tolerance referenced to the larger operand"。
- **m2-3.** L474–477 以 `r = 1.0000` 作为数据集"integrity confirmed by a perfect internal consistency check"。该 r 是**恒等式验证**（load rate 本就定义为 annual/(365×capacity)），**不构成数据质量的独立证据**。建议删除或明确其为定义自洽检查。
- **m2-4.** 桥接 24 对中符号一致 23/24（L721–725）——**单个不一致对位于哪一域/组成未被说明**，而 L745 只给了 IEUA 12/12、LADWP 11/12，即不一致发生在 LADWP。请说明该对的具体参数点及其是否落在质量约束绑定区，否则"partial equivalence"过宽。
- **m2-5.** `x_ai_B1_ml`/`x_ai_B2_ml` 列名互换（L686–691）。作者论证"三个标签组一起被换，故所有派生数值不受影响"。**该论证未经机器检验**——建议补一个断言脚本（$B_1\Rightarrow x_{\rm AI}\equiv0$）并对**所有**下游消费者运行，而非仅在报告中论述。
- **m2-6.** L354 的"limit_scale = 0.25 与 phi = 0.05 时 M0=104,948 vs M1=93,414"是单一情景；主稿据此否定"$\varphi\to0\Rightarrow dS\to0$"的一般性。建议给出该论断在 813 网格上的**分布证据**（$\varphi\to0$ 极限下 $|dS|$ 的最小值）。

## 建议决定

> ## **大修（Major Revision）** — M2-1、M2-3、M2-4 属实质性，**必须以改稿方式解决**；M2-5、M2-6 为必须清理项。
> 若作者坚持不修改摘要中"0.901 vs 0.859"的表述，**建议拒稿**——因为该数字目前承担了全文唯一的正向认识论重量（E3），而它不成立。

---

# 审稿意见 3 · 审稿人 3（水质工程 / 冷却化学视角）

**Reviewer 3 — Water quality engineering, cooling-water chemistry**

## 总体评价

本文把冷却水浓缩倍数（CoC）与限值标准引入城市级水核算，方向正确，且 GB/T 50050-2017 / GB/T 19923-2024 的限值替换（L293–306）与对"占位限值违反标准"的自曝（L302）值得肯定。§7a 关于"碱度是绑定物种"的机理链条（限值/浓度比 + 单物种扰动 + Sobol）是我在本稿中看到的最有工程说服力的部分。

**但我作为冷却化学审稿人必须指出：本文对"哪条质量路径是对的"这一根本问题给出了一个工程上难以接受的答案，而作者用一个内部门禁标记（`NOT_READY_FOR_E3`）把该问题搁置了。** 这在本刊是必须要压力测试的。

## 主要问题（Major）

**M3-1.【最致命】volume-only 与 R10a 路径的定性分歧不是"结构性敏感性"，而是**对本文核心机制的直接否证**；作者选择优势路径的理由不成立。**

- **分歧的量级**（SI §S4.0 表，L299–303；A21 L15–30）：$\varphi=0.6$ 时 volume-only CoC = **1.824**、补水 47,735 ML；R10a CoC = **7.986**、补水 **25,804 ML（−46%）**。$\varphi=0.4$ 时 2.292 vs **7.801**。
- **这对本文机制意味着什么**：本文的质量惩罚 $(M_0-M_1)$ 在 volume-only 路径上巨大，在 R10a 路径上**≈0**（SI L308–310 自承："The quality penalty $(M_0-M_1)$ that drives our mechanism is large on the volume-only path and ≈0 on the dynamic path"）。**本文的"质量约束是开关"（L390）、"碱度是唯一符号杠杆"（§7a）、乃至 $q>0$ 的全部符号结构，其驱动力在另一条同样满足质量守恒（相对残差 5.71×10⁻¹⁹，SI §S13）的路径上消失了。**
- **作者的选择理由不成立**：
  (i) 主稿 L644–648 称 volume-only 是"conservative bound"。但 volume-only 不是 bound，它是**另一套物理假设**（回路浓度 = 瞬时掺混，而非溶质存量平衡）。**"保守"与"正确"是两件事**；若真实冷却塔有滞留（现实中必然有，冷却塔回路水龄以小时计、掺混非瞬时），R10a 更接近物理。
  (ii) 主稿以"engine's own R10 gate marks the dynamic path `NOT_READY_FOR_E3`"为由弃用（L646–648）。**这是以工程实现状态作为科学选择依据。** `NOT_READY` 指的是该路径的 E3 门禁未通过，**不是**指该路径的物理结论错误。用它来排除一个与主结论冲突的路径，逻辑上是循环的。
  (iii) 更严重：若 R10a 更接近真实，则本文的**核心机制叙事（L41–48："the sign of the outcome is decided by a decision inequality — the net discharge must outweigh the water-quality effect"）在真实系统中可能不成立**，因为质量项近乎为零。
- **作者已在 SI L293 承认这是"the single most important caveat on the 'quality penalty' mechanism"**——**既然如此重要，就不能只放在 SI。** 主稿 Limitations §1（L637–648）虽然写了，但**摘要与 Results §7a 完全没有提及**，读者会得到"碱度是唯一杠杆"是一个稳健机制结论的印象。

> **必须修改**：
> 1. 摘要 L45–47"only **one** quantity changes the sign … the alkalinity of the reclaimed water"必须加限定："**on the volume-only solver path; on the engine's alternative dynamic solute-state path the quality penalty is ≈0 and this lever disappears (SI §S4.0)**"。
> 2. 主稿 §7a 开头必须同款声明。
> 3. 主稿 L48/"Water chemistry is a switch, not a modifier"（L390）应改为条件句。
> 4. **REQUIRES_NEW_EXPERIMENT**（见答复文件）：在 R10a 路径上重跑 §7a 的 41 点碱度扫描与 sign-flip 诊断，报出该路径下是否仍存在唯一符号杠杆。若 R10a 下无杠杆，本文的机制主张必须降级为"路径依赖"。

**M3-2. "碱度是唯一符号杠杆"的检验只在**单一冻结参数点**上完成，不具备"全局"含义。**

`wp5_sensitivity_summary.json::sign_flip_diagnosis.method`（我实际读取）载明：检验固定其余参数于"$\varphi=0.6$, ps=gs=1, dp=0, e=1, coc_design=5, **ls=1**, 化学 $x$=1"，沿每个参数边界取 41 点，**对 2 域 × 2 水样**求值。主稿 L540 却称"Across twelve parameters, only **one** changes the *sign*"——**"across twelve parameters"容易被读成"全局"，实际是"在其余十一个参数被钉死在单一点的条件下逐个扰动"**。这在 Morris 的原始精神（一次一个轨迹，其余维在轨迹内仍变化）与本文实现（其余维固定）之间有明显落差。

我在 §7a 表格（L542–546）看到 `limit_scale` 的 Morris $\mu^*$ = 45,062 **大于**碱度的 24,841，Sobol $S_T$ = 0.944 **大于**碱度的 0.682——即**扰动幅度最大的是限值档而非碱度**，只是限值档"approaches but does not cross zero"（L544）。**这意味着符号杠杆的唯一性高度依赖"恰好停在零的哪一侧"**：`limit_scale` 的最严端到达 $dS=-399$ ML（L544），**距零仅 399 ML，而该参数的最大效应是 45,062 ML**——即**距翻转仅差不到 1% 的扰动幅度**。

> **必须修改**：
> 1. L538–547 的标题与正文把"single sign lever"改为"**single sign lever at the reference point**"。
> 2. 补充报告 `limit_scale` 在何种取值下翻转（作者已有 41 点扫描数据，只需报出该曲线的最小值与符号）。
> 3. **REQUIRES_NEW_EXPERIMENT**：在 permissive / strict 两个限值档（L303–305）下重跑 sign-flip 诊断，检验"唯一杠杆"是否换档后仍是碱度。**这是直接回答审稿人"换限值档还成立吗"的问题，成本低（作者已有脚本 `wp5_morris_sobol.py`）。**

**M3-3. `limit_scale` 的"绑定与否"与名义档位脱钩，但主稿仍以名义档位组织结果。**

SI §S2b（L101–107）自曝：名义 `limit_scale` = 0.98 时**仅 58%** 情景真正绑定、1.0 时**仅 48%** 绑定。**即"quality-limited"这一标签近半数是错的。** 主稿 §5（L396–415）"Once the constraint binds, composition decides the sign"完全按名义档位叙述组成效应，**没有按 `quality_binding` 列重组**。这意味着 L399–404 的组成表混合了"约束绑定"与"约束未绑定"两类物理情形，**表中"realised CoC 1.84 – 5.00"这类范围正是混合的结果**。

> **必须修改**：L399–404 的表应按 `quality_binding == True` 子集重算并重报（作者有该列，`A26_语义统一/CHI_SEMANTICS.md` 已定义）。**在混合口径上做组成结论是不可接受的。**

**M3-4. 温度的缺失被写进 Limitations 却未做任何敏感性——而已有数据可以做一个粗略界。**

主稿 L661–662："temperature is missing for all five water sources, which alone can shift CoC by −30%"。**−30% 这个数字没有产物可追溯**（我在 `A32`/`A34`/`A4` 中检索温度相关表述，未找到产生该值的脚本或数据文件；`证据台账` 也未收录）。同时，§7a 的 12 参数面板中**没有温度维**——温度通过 PUE/蒸发进入（`wp5_extreme_cases.csv` 有 `mean_T_window`），但**不通过水化学限值**。而冷却水化学中，温度通过 $\mathrm{CaCO_3}$ 溶解度（LSI/PHREEQC）**直接**影响可达 CoC，这正是本文引用 PHREEQC 时隐含的机制（L418–419）。

> **必须修改**：
> 1. 删除或给出 −30% 的产物出处。
> 2. **REQUIRES_NEW_EXPERIMENT**：用已有的 PHREEQC 接口（L419 已用 phreeqpython 1.6.2）在 20/30/40 °C 下计算 IEUA 与 LADWP 的钙酸盐限制 CoC，把温度作为第 13 维加入 sign-flip 诊断。**这是本文自认的"−30% 位移"唯一能被真正量化的方式。**

**M3-5. "composition completeness" 的偏差方向已识别，但主网格 813 例的主体仍建立在不完整组成上。**

主稿 §3（L193–203）与 SI §S3.3 正确指出：缺失物种按零进入 ⇒ 样本显得更干净 ⇒ **偏向"回用有益"**。他们据此**仅在"符号主张"上排除**不完整水样（L174–175）。但**主网格 813 例中 2 个水样不完整**（Figshare RW 缺 2 物种、AI-UWM 假设缺 3 物种），而**头条计数 643/134/36、$q$ 分组 290/288/235、恒等式残差 2.55×10⁻¹¹ 全部包含它们**。作者在 L286 说"produces **zero sign flips in $q$ (0/192)**"（SI 同），**但 A32/WP3 §3.3（L98）明确写：AI-UWM 假设的 $q$ **符号会翻转**（+0.110 → −0.082），而 SI L256–257 却说"0/192 sign flips"。**

> **这是一处直接的科学矛盾**：SI §S3.3 说"零符号翻转"，WP3 §3.3 说"符号翻转"。主稿 L196–198 采纳了 WP3 的说法（"flips the sign of $q$ (+0.110 → −0.082)"）。**SI 未同步，且 SI 的"0/192"与主稿的"flips"不能同时为真。** 必须查明是两套不同的填补方法（WP3 说"按观测上界填补"，SI 说"from observed-source medians"），并统一叙述。
> **修改**：SI §S3.3 改为与 WP3 一致，并说明两者填补方案不同（若属实）。

## 次要问题（Minor）

- **m3-1.** L302 的占位限值定义为 2200/500/700/500/150，SI S2a L125 同；但 SI §S3.0 L193 的"placeholder run"写 TDS 2200 / Cl **500** / hardness **700** / alkalinity **500** / silica **150**，与 `wp5_sensitivity_summary.json` 的 `chemistry_panel_A_note` 只给 TDS/Cl 两物种不一致。请统一限值表。
- **m3-2.** L418–419 的 0.98 档来源"GSA/NREL 2023 metered cooling-tower upper bound (CoC 4.34–4.91)"——请给出 CoC 4.34–4.91 与 0.98 的换算关系（$\chi = \mathrm{CoC}_{\lim}/\mathrm{CoC}_{\rm design}$? 但 SI §S2b L89–93 明确 `limit_scale` ≠ $\chi$）。**该换算缺失，使 0.98 档的可信度不明。**
- **m3-3.** L420–422 的 0.25 档"response becomes pathologically large (up to 5.99×10⁵ ML)"。作为工程审稿人我必须指出：**该档已被作者判为无实测支撑，却在主网格中产生 188 个退化情景**（L313–317）。建议**直接删除该档**而非保留为"labelled stress case"——它除了制造门禁负担外不贡献信息。
- **m3-4.** L418 的 0.50 档"PHREEQC calcite-limited value for IEUA tertiary reclaimed water (2.52/5.0 = 0.504)"——请给出 PHREEQC 输入（温度、pH、$\mathrm{Ca^{2+}}$、碱度、离子强度）。**这是全文最关键的化学锚点之一，却无可复核输入。**
- **m3-5.** SI §S6（L375–387）"11 of 39 curves non-monotone"与主稿 L425–430 一致，但**未说明这 11 条曲线属于哪些组成/域**。若集中于单一不完整水样，结论重要性大降。请分解。
- **m3-6.** L649–651"storage raises makeup by +3.45%/+7.02%, identically for 50/200/800 ML"——"容量无关"这一反直觉结果需要解释（离散的"有/无储冷"效应）。建议给出机理说明或该效应的产物明细。

## 建议决定

> ## **大修（Major Revision）** — M3-1 属根本性；**作者必须要么在 R10a 路径上完成 M3-1 所要求的重跑，要么把机制主张整体降级为路径依赖并重写摘要**。M3-3、M3-5 为必须清理的口径问题。
> 若 M3-1 的重跑显示 R10a 路径下质量项确实≈0 且无符号杠杆，**本文的机制贡献将不足以支撑本刊，我建议拒稿**。

---

# 三份意见的决定汇总

| 审稿人 | 视角 | 建议决定 | 决定性依据 |
|---|---|---|---|
| **1** | 水系统 / 政策 | **大修**（M1-1/M1-3/M1-4 未改则拒稿） | 摘要 L64–66 与自身部分识别结论冲突；O2 公平性维度缺失 |
| **2** | 方法学 / 统计 | **大修**（若摘要保留 0.901 vs 0.859 则拒稿） | V3 头条表口径矛盾（733 标 813）；V9 折外增益由单一折驱动且两折饱和 |
| **3** | 水质工程 / 冷却化学 | **大修**（M3-1 重跑不利则拒稿） | volume-only vs R10a 定性分歧未闭合；"唯一杠杆"仅在单一冻结点验证 |

**共识（三位审稿人一致）**：本文的**诚实性与可复现性远超平均水准**，但**摘要与其自身 Limitations 之间存在系统性落差**——凡是结论性的强表述都在摘要/Results，凡是限定语都在 Limitations/SI。**这一"分层表述"模式本身，就是本稿最需要修正的问题。**
