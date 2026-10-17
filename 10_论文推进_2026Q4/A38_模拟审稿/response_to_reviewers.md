# 逐条答复（Response to Reviewers）· AI-UWM 项目

> ⚠️ **本文件含 2026-10-17 之前的历史数字**（如 n=813、643/134/36）。
> 当日修复 P0-1（Figshare 水样回灌 A19 提取的 SO4/碱度）后，现行值为
> **n=839、626/177/36、q 分组 263/288/288**。
> 本文件作为审计留痕保留原值，**当前结论请以主稿与 SI 为准**。
## Point-by-Point Response — Adversarial Red-Team Review

> **纪律声明**：本文档遵守本项目既定纪律（`证据台账` §A、SI §S15 门禁 3/4/7/8/9）。
> ① 每条答复必须写明**我们做了什么**并引用具体文件与数值；
> ② **若无法解决，如实承认并写入 Limitations，不得狡辩**；
> ③ 凡需新实验者标注 `REQUIRES_NEW_EXPERIMENT` 并给出可行方案；
> ④ **若某条批评不成立或已被 Limitations 覆盖，如实说明"此条不成立/已覆盖"，不为凑数而接受。**
>
> 对应文件：`A38_模拟审稿/reviewer_reports.md`（三份审稿意见）。
> **本轮的元结论：本轮答复中，`ACCEPTED`（须改稿）24 条，`ALREADY_COVERED`（已覆盖，不改）4 条，`REJECTED_AS_INVALID`（批评不成立）3 条。**

---

## 第 0 节 · 我们对审稿意见的总体判断

三份意见的核心指控可以归结为一句：**摘要与其自身 Limitations 之间存在系统性落差（"分层表述"）**。我们**接受这一元批评**，并认为它是本轮最有价值的发现。诚实性不等于可发表性；把限定语全部堆在 Limitations、把强表述全部留在摘要，事实上等于**把识别性问题转嫁给了读者**。

我们同时明确拒绝三类"为凑数"的批评（见第 3 节），因为它们与产物不符或已被 Limitations 实质覆盖。

---

## 第 1 节 · 审稿人 1（水系统 / 政策）逐条答复

### M1-1 —— "relevant to most real systems"（L64–66）是未识别的市场断言

**裁定：`ACCEPTED`（必须改稿）。**

**批评成立且致命。** 我们核对主稿 L58–63 与 L64–66，确认二者不可同时为真：前者声明 committed 占比"**not identified**，界 [0%,100%]"，后者却断言本文结果"**relevant to most real systems**"。这是一个**需求侧占比陈述**（"most real systems" = 多数真实设施的城市结果形态），而我们自己在 `A30_WP0取证/a24b_partial_id_summary.json` 中已把它判为不可识别（`provable_bounds_committed_pct: {lower: 0.0, upper: 100.0}`）。

**我们做了什么**：确认该句不能被现有产物支持。

**改稿方案（已写入待办，指向 `A16_英文稿/manuscript_en_v3.md` L64–66）**：

> 原文："The result is thus relevant to most real systems, while the supply-expansion route that does reduce withdrawal is realistic only for the largest ones."
>
> **改为**："The mechanism we identify applies to any system whose quality constraint binds and whose reclaimed pool is committed to incumbents. **How prevalent that configuration is cannot be determined from the data we have** (§6b), and we therefore do not estimate it. What the external data do bound is the *capacity* route: the supply-expansion path that reduces withdrawal is confined to a small minority of observed plants (§6b)."

**为什么不狡辩**：我们本可以辩称"relevant to most real systems"指的是"机制相关"而非"占比"。但该句紧随 [0%,100%] 之后、且与"only for the largest ones"对举，读者必然读成占比陈述。**语义歧义由作者承担，不由读者承担。**

---

### M1-2 —— §6b 产能比例建立在被事后调整的阈值上，应报区间而非单点

**裁定：`ACCEPTED`（必须改稿，但不需要新实验）。**

**批评成立。** 我们核对主稿 L521–524，确认作者**主动弃用**闭式阈值 `elig/P0`（2.384/2.567），改用经验阈值 `pool_scale` = 2.0。我进一步在 `A31_WP2_假设冻结/wp2_e3_predictions.csv` 上复算阈值稳健性：

| `pool_scale` 阈值 | 全样本准确率（$n_{\rm eff}=733$） |
|---:|---:|
| ≥1.2 | 0.8909 |
| ≥1.5 | 0.8909 |
| **≥2.0** | **0.9059** |
| ≥2.2 | 0.8731 |
| ≥2.4 | 0.8349 |
| ≥2.6 | 0.7940 |
| ≥3.0 | 0.7531 |

**阈值 2.0 是一个刀锋点**，而它正是我们从同一模型网格"经验测得"的（L521–524）。用它回算 L513–516 的"2.1–6.6% 产能充分比例"，该区间**必然**携带未量化的阈值不确定性。

**我们做了什么**：`REQUIRES_NEW_EXPERIMENT` **不需要**——我们已有 `A30_WP0取证/a24b_capacity_table.csv` 与 `a24b_partial_id_summary.json`（含 `thresholds_ml_per_day.first.ha=66.86`、`first.co=61.41`、`half.ha=73.55`、`half.co=73.69`）。

**改稿方案**：
1. L513–516 的"2.1–6.6%"改为**阈值区间对应的比例区间**：以 $r=1.0$ 为例，阈值取 61.4 ML/d 得 6.55%，取 73.5 ML/d 得 5.34%（均见 `a24b_partial_id_summary.json`）；再叠加闭式阈值 2.384/2.567 对应的更严比例，报出**下界与上界**。
2. L483–484 与 L521–524 明示选择 2.0 的**理由与其对结论的敏感性**，并承认该选择影响比例数值。

---

### M1-3 —— 外部锚定的语言掩盖了"中国污水厂分布 vs 合成模型"的落差

**裁定：`PARTIALLY_ACCEPTED`。**

**批评部分成立。** 我们确认：主稿 L655 自承"Two homologous synthetic domains; no independent city calibration"，L469–473 也已写"they do **not** validate city-level predictions"。**这些限定是充分的，批评指出的实质问题不在 Limitations，而在摘要的措辞。**

具体地，摘要 L56–58 以"Anchoring against a public dataset of 10,826 observed wastewater treatment plants shows our supply parameter sits at the 81st percentile of that distribution"开头。"Anchoring"一词在摘要中易被读作"外部验证"。

**改稿方案**：摘要 L56–58 改为"**A parameter-range check** against a public dataset of 10,826 observed wastewater treatment plants places our supply parameter at the 81st percentile of that distribution"；并在同一句内保留"most plants retain spare treatment capacity (median utilisation 0.594)"，但**紧跟一句**承认其与本文需求侧机制的断裂（现仅见于 L462–467）。

**为什么不完全接受**：审稿人 1 暗示我们"把中国数据当作普适锚"——**这一指控与产物不符**。我们在 L432–438 与 SI §S6b L399–407 中明确记录了数据集来源（Shen et al. 2026, Zenodo 10.5281/zenodo.22138940, CC-BY-4.0）与中国范围，并在 L474 标注了一级来源。**我们接受措辞批评，不接受"隐瞒数据来源"的暗示。**

---

### M1-4 —— O2（既有用户服务缺口）被声明却未被报告

**裁定：`ACCEPTED`（最有价值的操作性建议）。**

**批评完全成立，且这是本轮最容易补救的缺陷。** 我们核对 `A31_WP2_假设冻结/WP2_假设与主估计量冻结.md` §3，确认 O2 被**明确列为四类结局之一**并特别标注"**可能 O1 改善而 O2 恶化**"。但主稿 Results 全篇只报 $dS_{\rm pot}$（O1）。

**我们做了什么**：`A13_可靠性机制/supply_state_regimes.csv` 中已含 `inc_B1_ml` / `inc_B2_ml`（= $r_{\rm inc}^{B_1}, r_{\rm inc}^{B_2}$），因此 $C = r_{\rm inc}^{B_2}-r_{\rm inc}^{B_1}$ **已可直接产出 O2 分布**。无需任何新实验。

**改稿方案（`REQUIRES_NEW_EXPERIMENT`：否）**：
1. 新增 SI 小节 **§S16 "Incumbent service outcomes (O2)"**：给出 $C$ 的分布（按 $q$ 分组、按域、按组成），并**明确报告 $dS_{\rm pot}<0$ 而 $C>0$ 的情景数**——这才是"公平性代价"的量化。
2. 在 Fig. 3 增加一个面板或在新 SI 图中呈现 $C$ 与 $dS_{\rm pot}$ 的散点，检验两者是否反向。
3. 主稿 §3 末尾加一段：报告"城市净取水下降"中有多少比例伴随"既有用户取水上升"。

**诚实预告**：我们**尚不知道该分析的结果**。若结果显示 O2 与 O1 大量反向，则摘要"city benefits"的表述需要进一步限定（应写"city-level potable withdrawal falls, **while incumbent reclaimed users may withdraw more potable water**"）。我们承诺按结果改稿，不倒推结论。

---

### m1-1 —— 68 runs 缺独立核验产物

**裁定：`ACCEPTED`（须补产物）。** 我们确认 `A30_WP0取证/证据台账_EVIDENCE_LEDGER.md` 未收录 68 这一量（§A 表中无对应行）。**补做**：在 A30 下新增 run 清单 CSV 并在台账 §A 登记。

### m1-2 —— 水价与本文无关

**裁定：`ACCEPTED`（建议删除）。** 主稿 L663 自承"Costs are declared values; no cost claim is made"，而 L450 报水价中位数 1.45 CNY/m³。**改稿**：移入 SI 背景段。

### m1-3 —— "mean of sector means" 未加权

**裁定：`ACCEPTED`（须披露）。** 主稿 L446 与 SI L417 均用"mean of sector means (39 sectors)"。**改稿**：明示该量**未按部门用水量加权**，因此不是全国工业冷却用水占比。

### m1-4 —— 与 Wang/Han/Shen 的比较；"measurable threshold" 过强

**裁定：`ACCEPTED`。** 主稿 L632"we make that dependence a **measurable threshold**"确实过强——该阈值正是 M1-2 所指的不稳健量。**改为**："we express that dependence as a threshold **within our modelled envelope**, and report its sensitivity to the threshold definition (§6b)."

### m1-5 —— 单一极值 27,354 ML

**裁定：`ACCEPTED`。** **改稿**：摘要与 §2 同时报中位与极值。

---

## 第 2 节 · 审稿人 2（方法学 / 统计）逐条答复

### M2-1 —— §3 头条表（L164–168）与"严格符号约定"不符

**裁定：`ACCEPTED`（本轮最严重的内部矛盾，必须立即改稿）。**

**批评完全成立。** 我们在 `A13_可靠性机制/supply_state_regimes.csv` 上独立复算（双门禁后 $n=813$）：

| $q$ 组 | 表内 $n$ | 表内 falls | 表内 rises | **严格口径实际（负/正/零）** |
|---|---:|---:|---:|---|
| $q>0$ | 290 | 290 | 0 | 290 / 0 / 0 |
| $q\approx0$ | 288 | **208** | **0** | **220 / 32 / 36** |
| $q<0$ | 235 | 133 | 102 | 133 / 102 / 0 |
| **合计** | **813** | **631** | **102** | **643 / 134 / 36** |

**表内 falls+rises = 733，与表头 $n=813$ 差 80 行。** 我进一步定位了这 80 行：**全部是 $q$ 恰为 0 的情景**，其中 36 行 $dS_{\rm pot}$ 精确为零，**另有 32 行 $dS_{\rm pot}>0$（有害）**。

**这句话的严重性在于**：主稿 L184–191 刚刚以加粗方框批评旧口径"**silently drops 80 near-zero scenarios and leaves $n_{\rm eff}=733$ while still labelling the sample as 813**"，然后**在同一小节的表中原样使用了该口径**。更糟的是，被丢掉的不只是"近零"，而是 **32 个明确的有害案例**——它们使"$q\approx0$ 组 0 harmful"这一视觉印象失效。

**我们做了什么**：确认该表必须重算。

**改稿方案（`REQUIRES_NEW_EXPERIMENT`：否）**：把 L164–168 表改为严格三列（falls / rises / exactly zero）：

| $q$ group | n | falls | rises | **= 0** | median $dS$ |
|---|---:|---:|---:|---:|---:|
| $q>0$ | 290 | 290 | 0 | 0 | −14,496 |
| $q\approx0$ | 288 | 220 | **32** | **36** | −7,651 |
| $q<0$ | 235 | 133 | 102 | 0 | −4,259 |

并在表下注明：本表与 L189 的严格计数（643/134/36）一致；$q\approx0$ 组的 32 个有害案例与 36 个精确零分开报告。

**对损害范围的限定（重要）**：审稿人 2 的批评**不影响**头条结论"$q>0 \Rightarrow$ 0/290 有害"（我们已独立复算确认 290/290 无例外）。**我们主动指出这一点，以免过度自我否定。** 但摘要中任何依赖"$q>0$ 之外亦无系统性伤害"的表述（L30–38）需复核措辞。

---

### M2-2 —— "$q>0$ 充分条件"在完整水样网格上完全空洞，主稿未把该事实放在结论旁

**裁定：`ACCEPTED`（须改稿，并已部分覆盖——但覆盖位置错误）。**

**批评成立，且我们自己早已知晓。** 核对结果：
- SI §S10 §5（L615–617）已写："**The $q>0$ sufficient condition could not be meaningfully tested** in the complete-composition grid: all 47 reliable cases are beneficial, so 'no exception' is a **vacuous pass** (gate 4). Stated as untested rather than confirmed."
- `A32_WP3_水化学/WP3_水化学机制验证报告.md` §2（L66–71）已写：H3 属"**空洞通过**"，"$q<0 \Rightarrow$ 受益**同样成立**"。
- `A36_终审/终审门禁报告与期刊匹配评估.md` §4 已写：充分条件"**未被有效检验**（无正例）"。

我们复算确认：`A33_WP4_组成重构/wp4_results.csv` 可靠 47 例中，$q>0$ 组 23/23 有害=0，**$q\le0$ 组 24/24 有害亦=0**。

**但——主稿 L170 仍以加粗宣称"$q>0$ is a sufficient condition for a city-level benefit: 290 of 290, with no exception."，且紧邻处无任何"空洞"提示。**

**新增的两点（我们自己的复算，审稿人未指出，但我们认为对其有利）**：
1. **全样本受益基率 = 0.791**（643/813）。在 79% 的基率下，"预测受益"这一常数规则本身就很准——**主稿从未报基率**。这是**选择性报告**，我们承认。
2. 但在 $n=813$ 上做 **Fisher 精确检验**：2×2 表 [[$q>0$, harm]=[0, 290], [$q\le0$, harm]=[134, 353]]，**$p\approx9.5\times10^{-22}$**。若 $q$ 与符号独立，期望有害数 ≈ 290/813 × 134/813 × 813 ≈ **47.8 例**，实测 0 例。**即 $q$ 与 $dS_{\rm pot}$ 符号的关联极强，远非偶然。** 这支持"$q$ 的符号结构是实质的"，但**不等于**"$q>0$ 是充分条件"。

**改稿方案**：L170 后立即加入三句：
1. 全样本受益基率 0.791；
2. 在完整水样网格（$n_{\rm eff}=47$）上该检验空洞，因为 $q\le0$ 组同样零有害（引 A32 §2 与 SI §S10 §5）；
3. Fisher $p\approx9.5\times10^{-22}$，说明 $q$ 与符号**非独立**，但该关联在诊断口径下尚未被独立检验（见 §3d）。

**为什么不辩称"已被 Limitations 覆盖"**：**覆盖位置错误。** SI §S10 与 A32/WP3 确实写了，但**主稿正文没有**。审稿人只读正文时会得到完全不同的印象。**"写在了别处"不等于"写在了该写的地方"。**

---

### M2-3 —— 折外 0.901 vs 0.859 由单一折驱动，两折基线饱和

**裁定：`ACCEPTED`（最致命，必须改摘要）。**

**批评完全成立。** 我们逐折复算 `A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json::leave_one_sample_out`：

| 留出样本 | $n$ | C4 准确率 | 多数类基线 | **增益** |
|---|---:|---:|---:|---:|
| AI-UWM model assumption（2 物种） | 184 | 1.0000 | **1.0000** | **+0.0000** |
| LADWP AWPF（完整） | 183 | 1.0000 | **1.0000** | **+0.0000** |
| IEUA RP-1（完整） | 196 | 0.9388 | 0.7551 | **+0.1837** |
| Figshare RW（不完整） | 170 | 0.6647 | 0.6824 | **−0.0177** |
| **均值** | 733 | **0.9009** | **0.8594** | **+0.0415** |

**四点认定：**
1. **两折基线 = 1.000**（该样本内 100% 情景受益），"增益 0"是构造性的，零信息量。
2. **全部 +0.0415 来自 IEUA 一折**；Figshare 折为**负**。
3. 主稿 L265–269 写"**critically — 0.901 out-of-sample versus a 0.859 out-of-sample baseline … so this is not post-hoc selection**"——**单折驱动的均值不构成此证据。**
4. **四折非独立**：我核对了 `wp2_e3_predictions.csv`，$4\ \varphi\times9$ `pool_scale` $\times$ 2 域的**参数网格对四个水样完全相同**（每个水样 9 个不同 `pool_scale`，值域一致）。留一留出的是**化学组成**，参数空间**无任何外推**。

**一个对我们有利的补充（诚实起见一并给出）**：若**只保留两个完整水样**（IEUA + LADWP，即本文已声明唯一可用于符号主张的子集），我复算得：$n=379$，多数类基线 0.8734，C4 准确率 0.9683，两折留一均值 0.9694 vs 0.8776，**增益 +0.0918**（IEUA +0.1837，LADWP +0.0000）。**这比 0.0415 更好，但仍是单折驱动、且样本仅 2 个。**

**改稿方案（必须执行）**：
- 摘要 L43–44 与 L266–269 **删除**"0.901 vs 0.859"作为正向预测能力的表述。
- **改为**（写入 Limitations 13 的扩写版）："Under leave-one-composition-out validation the combined criterion reaches 0.901 against a 0.859 baseline. **We report that this gain originates entirely in one of four folds (IEUA, +0.184), while two folds are saturated by construction (baseline 1.000, gain 0.000) and one is negative (Figshare RW, −0.018); the parameter grid is shared across folds, so only the chemistry axis is held out. With four folds and one effective fold, this does not establish transferable out-of-sample skill**, and we therefore present the criterion as an identified relationship under a stated data requirement, not as a validated predictor."
- Discussion §6（L612–615）同步弱化。

**为什么不辩称"留一验证本身就是防泄漏的"**：留一验证防的是**同类信息泄漏**，不是**单折驱动的统计脆弱性**。审稿人 2 的批评针对后者，成立。

---

### M2-4 —— C4 的阈值是刀锋点且 `pool_scale` 是模型内规划量 ⇒ 自证

**裁定：`ACCEPTED`（须改稿并补区间）。**

**批评成立。** 两点：
1. **阈值敏感**（复算见 M1-2 表）：≥2.0 时 0.9059 为峰值，≥2.2 降至 0.8731，≥2.4 降至 0.8349。
2. **`pool_scale` 是合成扫描轴**：我核对 `wp2_e3_predictions.csv`，四个水样的 `pool_scale` 取值集合**完全相同**（{0.5, 1.0, 1.5, 2.0, 2.2, 2.4, 2.6, 3.0, 4.0}）。主稿 L480–484 自承该阈值是"Measured empirically"从模型网格读出。

**但我们必须区分两种"自证"，并如实说明哪一种是成立的：**
- **不成立的指控**：`pool_scale` 进入预测器后**完全等价于** $x_{\rm AI}$ 或 $dS_{\rm pot}$ 的某种变换。**这是错的**——`wp2_e3_independent_prediction_summary.json::forbidden_inputs` 明确列出 $x_{\rm AI}, M_0, M_1, C, F, dS_{\rm pot}, \varphi_{\rm eff}, \mathrm{CoC}_{\rm AI}$，且 `pool_scale` 是**输入**（网格设定值）而非**输出**。
- **成立的指控**：C4 判据的第二项（`pool_scale` ≥ 2）在结构上**等价于恒等式的一个分支条件**（"池足够大 ⇒ 不挤占 ⇒ 受益"，正是 §2 branch C）。因此该判据**部分是代数重述**，其"预测力"有相当部分来自分支结构而非新信息。

**改稿方案**：
1. L265–277 明确写出上述区分，并声明 C4 的第二项**在结构上对应 branch C 条件**。
2. 补充**阈值区间**的折外准确率（如阈值 ∈ {1.5, 2.0, 2.4}），而非单点 0.901。
3. 保留 L692–695（Limit 13）的 `pool_scale` 可得性声明。

---

### M2-5 —— 全文零推断统计、多重比较未校正、Sobol 降维口径未报

**裁定：`ACCEPTED`（须补，但接受分阶段处理）。**

**批评成立。** 我们确认：主稿 772 行与 SI 785 行中**未出现任何置信区间或 $p$ 值**。我们进一步在 `A34_WP5_敏感性与极端事件/wp5_sensitivity_summary.json` 中读到一个**主稿未披露的关键口径**：

```
"dimension_reduction": {
  "n_full": 12, "n_used": 7,
  "cost_full_evals": 3584, "cost_used_evals": 2304,
  "note": "显式取舍: 计算量控制。Sobol 指数只对这 7 维的条件方差有效;
           未纳入维度的方差并入 ST(总阶)。"
}
```

**即：主稿 L544 的 Sobol $S_T$（`limit_scale` 0.944、alkalinity 0.682）是 12 维降到 7 维后的条件方差结果**，且"未纳入维度的方差并入 $S_T$"。这**同时**意味着：(i) 指数与全维不可比；(ii) $\sum S_1\approx0.22$（L565–567）是 7 维口径。

**改稿方案**：
1. 主稿 §7a 明确写出 7/12 维降维与"未纳入维度方差并入 $S_T$"。
2. 对 Sobol 指数给 **bootstrap CI**（`REQUIRES_NEW_EXPERIMENT`：低，可用已有 256 样本设计重用）。
3. L226–231 的"七判据选最优"与 §3d 的"六判据选 C4"：声明为**探索性**，或做**置换检验**。
4. 全文凡出现"准确率/相关/Sobol 指数"处补 $n_{\rm eff}$ 与不确定度。

**分期承诺**：第 1 项立即执行；第 2–4 项列入下一轮。**我们不假装这三项能在本轮完成。**

---

### M2-6 —— SI 与主稿多处数字直接冲突

**裁定：`ACCEPTED`（全部确认，属必须清理项）。**

我逐条核对，**五条全部属实**：

| 编号 | 冲突内容 | 证据 | 裁定 |
|---|---|---|---|
| 1 | SI L390"the genuine out-of-sample number is **0.558**"，而 SI L374 与主稿 L591 均为 **0.806** | SI 自相矛盾 | ✅ 属实 |
| 2 | SI L184 表"$dS<0$ = **631**"未同步为 643 | SI L752 自己说严格口径是 643 | ✅ 属实 |
| 3 | SI L227"best of seven predictors: **0.768**"，而 SI L240 表与主稿 L228 均为 **0.803** | 同一 SI 内两值 | ✅ 属实 |
| 4 | SI L3 标题"**Supply state, not cooling technology**, governs…" vs 主稿 L1 标题"**What Governs the Urban Water Outcome…**" | 标题不一致 | ✅ 属实 |
| 5 | SI L253"IEUA and LADWP are complete (**5/5**)" vs A32/WP3 L89–90"IEUA **9** 物种、LADWP **8** 物种" | 跨文件矛盾 | ✅ 属实 |

**我们做了什么**：全部确认。**这说明我们的"数字同步"流程存在漏洞**——而该流程正是本文的核心卖点。**我们把它当作流程缺陷而非笔误处理。**

**改稿方案**：五项全部同步；并在 `A36_终审/final_gate.py` 中**新增跨文件一致性断言**（主稿 vs SI 的标题、R²、符号计数、物种数必须逐项匹配），使此类问题**机器可拦截**。

**⚠️ 诚实补记（我们自己的调查）**：第 5 项**不只是笔误**。A32/WP3 §3.2 的"IEUA 9 物种、LADWP 8 物种"与 SI §S3.3 的"5/5"、以及 `wp5_sensitivity_summary.json::samples_authoritative` 的"IEUA n_species 5、LADWP n_species 5"**互相冲突**。可能的解释是计数口径不同（A32 数全部质量指标；SI/`wp5` 数**受约束的 5 个物种**：TDS/Cl/hardness/alkalinity/silica）。**但该口径差异从未在任何文件中声明。**

> **这是红队自审发现的新问题（见 `red_team_findings.md` F-3），审稿人 2 只看到了表象。** 我们把它升级为 `MAJOR` 处理：必须发布权威物种计数口径表，重算所有"完整/不完整"判定，并复核 L174–182 的组成表分类。

---

### m2-1 —— $n_{\rm eff}=733$ 与"严格符号"口径互斥

**裁定：`ACCEPTED`。** 见 M2-1 与 M2-2。**改稿**：统一为严格口径 643/134/36（$n=813$）；若保留 733 的分析，须显式标为第二套口径并解释为何需要它。

### m2-2 —— 相对容差在 $M_0/M_1\to1$ 时失效

**裁定：`ACCEPTED`（表述修正）。** **改为**："relative tolerance referenced to the larger operand"。

### m2-3 —— `r = 1.0000` 是定义自洽而非数据质量证据

**裁定：`ACCEPTED`。** 主稿 L435–438 称"integrity was confirmed by a perfect internal consistency check"。load rate 按定义就是 annual/(365×capacity)，**该 $r$ 不能作为数据质量证据**。**改稿**：改为"the reported load rate reproduces its definitional expression ($r=1.0000$), confirming the release is internally self-consistent"，并不再以之支撑"integrity confirmed"。

### m2-4 —— 桥接 23/24 中不一致对的定位

**裁定：`ACCEPTED`（须补细节）。** 主稿 L745 给出"IEUA 12/12、LADWP 11/12"，即不一致在 LADWP。**改稿**：给出该对的具体参数点、$M_0/M_1$ 值、其结论是否落在质量约束绑定区。

### m2-5 —— 列名互换的论证未经机器检验

**裁定：`ACCEPTED`（补断言脚本）。** 我们确认 `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md` 存在、主稿 L686–691 已披露。**但审稿人 2 说得对：L688–690 的"三个标签组一起被换，故所有派生数值不受影响"是论述而非检验。** **补做**：新增断言脚本（$B_1 \Rightarrow x_{\rm AI}\equiv0$）并对所有下游消费者运行。`REQUIRES_NEW_EXPERIMENT`：否。

### m2-6 —— "$\varphi\to0 \Rightarrow dS\to0$ 被否证"应有分布证据

**裁定：`ACCEPTED`。** 主稿 L354 用单一情景（`limit_scale`=0.25, $\varphi$=0.05, $M_0$=104,948 vs $M_1$=93,414）支撑一般性论断。**改稿**：给出 $\varphi\to0$ 极限下 $|dS|$ 在 813 网格上的分布（最小值、四分位）。

---

## 第 3 节 · 审稿人 3（水质工程 / 冷却化学）逐条答复

### M3-1 —— volume-only vs R10a 分歧是核心机制的否证，选择理由不成立

**裁定：`ACCEPTED`（最致命，须在摘要加限定语 + `REQUIRES_NEW_EXPERIMENT`）。**

**批评完全成立，我们无辩解空间。** 核对 SI §S4.0（L296–303）：

| | volume-only（主） | R10a 动态溶质状态 |
|---|---:|---:|
| CoC at $\varphi=0.4$ | 2.292 | **7.801** |
| CoC at $\varphi=0.6$ | **1.824** | **7.986** |
| makeup at $\varphi=0.6$ | 47,735 ML | **25,804 ML（−46%）** |

SI L308–310 自承："**The quality penalty $(M_0-M_1)$ that drives our mechanism is large on the volume-only path and ≈0 on the dynamic path.**"

**这意味着：本文的质量惩罚机制、$q$ 的符号结构、"质量约束是开关"、"碱度是唯一杠杆"——其驱动力在另一条同样满足质量守恒的路径上消失。**

**审稿人对我们三条理由的批评，我们逐条承认：**

1. **"conservative bound"（L637–648）**：审稿人指出"保守 ≠ 正确"。**我们承认。** volume-only 不是 bound，是另一套物理假设（回路浓度 = 瞬时掺混）。真实冷却塔有滞留，R10a 在物理上可能更接近。
2. **"engine's R10 gate marks the dynamic path `NOT_READY_FOR_E3`"**：审稿人指出这是**以工程实现状态作为科学选择依据**，逻辑循环。**我们承认。** `NOT_READY` 指该路径的 E3 门禁未通过，**不等于**其物理结论错误。
3. **"这是 SI 中最重要 caveat，不能只放 SI"**：**我们接受。** SI L293 明写"the single most important caveat"，而摘要与 §7a 完全没有提及。

**改稿方案（立即执行）**：
- 摘要 L45–47"only **one** quantity changes the sign … the alkalinity"加限定：**"on the volume-only solver path; on the engine's alternative dynamic solute-state path the quality penalty is ≈0 and this lever does not appear (SI §S4.0)"**。
- §7a 开头同款声明。
- L390"Water chemistry is a switch, not a modifier"改为条件句："On the volume-only path, and with the pool committed, water chemistry is a switch rather than a modifier."
- Limitations §1 扩写，明确"mechanism attribution is path-conditional"。

**`REQUIRES_NEW_EXPERIMENT`：是。** 可行方案：
1. 在 **R10a 路径**上重跑 §7a 的 41 点碱度扫描与 sign-flip 诊断（脚本已有：`A34_WP5_敏感性与极端事件/wp5_morris_sobol.py`，只需切换 solver 开关）。
2. 若 R10a 下**仍存在唯一符号杠杆** ⇒ 机制主张加强，可保留。
3. 若 R10a 下**不存在杠杆** ⇒ 本文机制贡献必须**降级为"路径依赖"**，摘要须相应重写，且 H4/§7a 的标题不能再称"机制"。
4. 成本估计：单个扫描 41 点 × 2 域 × 2 水样 ≈ 164 次引擎调用，与已有运行同量级。

**我们不做的事**：不会因为结果不利而把 R10a 路径继续标为"NOT_READY"从而规避。**若 R10a 重跑否定机制，我们将如实报告并重写摘要——这一点现在书面承诺。**

---

### M3-2 —— "唯一符号杠杆"仅在单一冻结点检验

**裁定：`ACCEPTED`（须改措辞 + `REQUIRES_NEW_EXPERIMENT`）。**

**批评成立。** 我实际读取 `wp5_sensitivity_summary.json::sign_flip_diagnosis.method`，原文为：

> "固定其余参数于冻结取值 (**phi=0.6, ps=gs=1, dp=0, e=1, coc_design=5, ls=1**, 化学 x=1)，沿每个参数的边界取 41 点，对 **2 域 × 2 水样**求 dS_pot…"

而主稿 L540 写"**Across twelve parameters, only one changes the sign**"——易被读作全局结论，**实际是"在其余十一维钉死于单点的条件下逐个扰动"**。

**审稿人的第二个观察极其锐利，我们确认并加强**：主稿 L542–546 表中，`limit_scale` 的 Morris $\mu^*$ = **45,062**（大于碱度的 24,841），Sobol $S_T$ = **0.944**（大于碱度的 0.682）——**效应幅度最大的其实是限值档，而非碱度**；它只是"approaches but does not cross zero"（最严端 $dS=-399$ ML）。**距零仅 399 ML，而该参数最大效应 45,062 ML ⇒ 距翻转不足 1% 的扰动幅度。**

**改稿方案**：
1. L538–547 标题与正文改为"**single sign lever at the reference point**"。
2. 从已有 41 点扫描数据报出 `limit_scale` 曲线的**最小值与是否在扫描内翻转**。
3. 明示 $\varphi=0.6$、`ls`=1 等冻结取值，并说明"唯一性"是**该参考点的性质**。

**`REQUIRES_NEW_EXPERIMENT`：是（低成本）。** 在 **permissive / strict 限值档**（主稿 L303–305）下重跑 sign-flip 诊断，检验"唯一杠杆是否仍是碱度"。
- 若换档后**仍是碱度** ⇒ "唯一杠杆"稳健性大增，可写为跨档结论。
- 若换档后**出现其他杠杆** ⇒ L540 的"only one"必须限定为 baseline 档。

---

### M3-3 —— 名义 `limit_scale` 与实际绑定脱钩，§5 组成表应按 `quality_binding` 重组

**裁定：`ACCEPTED`（须重算表）。**

**批评成立。** SI §S2b（L101–107）自曝：

| 名义 `limit_scale` | 实际绑定比例 |
|---:|---:|
| 0.25 | 100% |
| 0.50 | 92% |
| 0.98 | **58%** |
| 1.0 | **48%** |
| 1e6 | 0% |

SI L109–112 自承："almost half of the scenarios labelled 'quality-limited' at 0.98 in fact reach the design ceiling and are *not* quality-constrained. Analysing by nominal tier alone therefore mixes two different physical regimes."

**而主稿 §5（L396–415）"Once the constraint binds, composition decides the sign"正是按名义档位叙述组成效应**，L399–404 的组成表未按 `quality_binding` 重组。

**改稿方案（`REQUIRES_NEW_EXPERIMENT`：否）**：按 `quality_binding == True` 子集重算 L399–404 组成表并重报；若子集过小则如实报告 $n$ 不足。

---

### M3-4 —— 温度缺失与无出处的 −30%

**裁定：`PARTIALLY_ACCEPTED`（−30% 无出处，须删或补；温度敏感性 `REQUIRES_NEW_EXPERIMENT`）。**

**批评部分成立。** 我们确认主稿 L661–662 写"temperature is missing for all five water sources, which alone can shift CoC by **−30%**"。我在 `A32_WP3_水化学/`、`A34_WP5_敏感性与极端事件/`、`A4_水化学参数域/` 中检索温度相关表述，**未找到产生该 −30% 的脚本或数据文件**；`证据台账_EVIDENCE_LEDGER.md` §A 也未收录该项。**按本项目自己的纪律（台账规则："无法追溯者标 UNTRACEABLE，不得出现在主稿"），该数字应被删除或补出处。**

**但审稿人的第二半——"§7a 的 12 参数面板中没有温度维"——我们部分不同意**：温度通过 PUE 与蒸发进入模型（`wp5_extreme_cases.csv` 含 `mean_T_window`，热浪窗均值 31.58 °C vs 全年 13.52 °C），并已被 §7b 的观测驱动极端事件覆盖（0/8 翻转）。**审稿人指出的真正缺口是：温度不通过水化学限值进入**，而冷却水化学中温度经 $\mathrm{CaCO_3}$ 溶解度直接决定可达 CoC。

**改稿方案**：
1. **立即**：删除 −30%，或补产物出处。
2. **`REQUIRES_NEW_EXPERIMENT`：是**。用已有 PHREEQC 接口（主稿 L419 已使用 phreeqpython 1.6.2）在 **20 / 30 / 40 °C** 下计算 IEUA 与 LADWP 的钙酸盐限制 CoC，把温度作为**第 13 维**加入 sign-flip 诊断。这是把自认的"−30% 位移"**唯一能被真正量化**的方式。

---

### M3-5 —— SI "0/192 sign flips" 与 WP3 "符号会翻转" 直接矛盾

**裁定：`ACCEPTED`（严重科学矛盾，须查清）。**

**批评成立，且这是审稿人 3 最锐利的一击。** 核对：
- **SI §S3.3**（L256–257）："Imputing missing species from observed-source medians over 192 scenarios: makeup changes by up to **2,869 ML** …, but **zero sign flips in $q$ (0/192)**."
- **A32/WP3 §3.3**（L98）："**AI-UWM assumption（2 物种）** | $q$ 符号会翻转：+0.110 →（按观测上界填补）−0.082"
- **主稿 L196–198**（采纳 WP3 说法）："refilling its missing species from the observed range of the complete samples **flips the sign of $q$** (+0.110 → −0.082)"

**三者不能同时为真。** 最可能的解释是**两套不同的填补方案**：SI 用"observed-source medians"（中位数），WP3 用"观测上界"（upper bound）。中位数可能不足以翻转符号，上界可以。

**改稿方案**：SI §S3.3 改为与 WP3 一致，并**显式区分两种填补方案**：

| 填补方案 | 来源 | AI-UWM $q$ | Figshare RW $q$ 幅度 |
|---|---|---|---|
| 观测源中位数 | SI §S3.3 | 符号**不**翻转 | 变化至 1.6× |
| 观测上界 | A32/WP3 §3.3 | **翻转**（+0.110 → −0.082） | — |

并说明**为何两套方案给出相反结论**（中位数填补量低于翻转阈值，上界高于），以及**主稿采用上界作为保守选择**。**我们不能只报对自己有利的那一套。**

---

### m3-1 —— 占位限值表在不同文件中不一致

**裁定：`ACCEPTED`。** 不同文件对 placeholder 的表述不一（SI L125 vs SI L193 vs `wp5` 的 `chemistry_panel_A_note` 仅给 2 物种）。**改稿**：建立唯一权威限值表，所有文件引用同一份。

### m3-2 —— 0.98 档与 CoC 4.34–4.91 的换算缺失

**裁定：`ACCEPTED`（须补换算）。** 主稿 L418–419 的换算关系缺失，且 SI §S2b L89–93 明确 `limit_scale` ≠ $\chi$。**必须补**。

### m3-3 —— 建议直接删除 0.25 档

**裁定：`PARTIALLY_ACCEPTED`。**

**审稿人建议删除该档，我们认为这一建议合理但需权衡。** 该档确实：(i) 无实测支撑；(ii) 产生 188 个退化情景（主稿 L313–317）；(iii) 响应"pathologically large (up to 5.99×10⁵ ML)"（L420–422）。

**但**：该档的存在使"at the tightest tier the cited limits are stricter than the source water itself"这一**重要发现**得以暴露（L313–317），并催生了 CoC 下限门禁。**删除它会同时删除该发现的可复现基础。**

**折中方案**：**保留在 SI 作为独立诊断，但从主网格中移除**，使主网格 $n$ 口径更干净。**这一改动会改变 813 这一数字**，需重新核验全部下游产物——因此列入下一轮，并明确标注为 **breaking change**。

### m3-4 —— 0.50 档需给 PHREEQC 输入

**裁定：`ACCEPTED`（须补）。** 主稿 L418 的 0.50 档是全文最关键化学锚点之一，**却无可复核输入**。**补做**：给出温度、pH、$\mathrm{Ca^{2+}}$、碱度、离子强度与 phreeqpython 调用脚本。

### m3-5 —— 11/39 非单调曲线的组成归属

**裁定：`ACCEPTED`（须分解）。** 若集中于单一不完整水样，结论重要性大降。**改稿**：按组成/域分解 11 条曲线。

### m3-6 —— 储冷"容量无关"效应需机理说明

**裁定：`ACCEPTED`（须解释）。** 主稿 L649–651 的"+3.45%/+7.02%，对 50/200/800 ML 相同"是反直觉的离散效应，需给出机理或产物明细。

---

## 第 4 节 · 我们认为**不成立**或**已被覆盖**的批评（不为凑数而接受）

### R-1 —— "Fig. 6 是否仍在暗示点什么"

**裁定：`REJECTED_AS_INVALID`（此条批评不成立）。**

我们**实际查看了** `A37_六主图_v4/Fig6_external_anchor_partial_id.png`。Panel a 的呈现为：标题"Committed share is a partial-identification problem"，方框内大字"**NOT IDENTIFIABLE**"，下方"provable bound **[0%, 100%]**"，再下注"demand side unobserved: $0\le E_i\le D_i$ admits both branches for every plant, so no point estimate and no CI exist"。**无点估计、无置信区间、无条形图暗示任何占比。** Panel c 标题明确写"What IS identifiable: capacity feasibility only (**not prevalence of the committed regime**)"。图注 `fig6_caption.md` L6–8 与 L24–30 亦完整声明撤回。

**结论：Fig. 6 是本稿诚实性最强的产物之一，批评不成立。** 若审稿人有此疑虑，我们建议其直接查看 Panel a 的视觉呈现。

### R-2 —— "界 [0%,100%] 是否等于什么都没说"

**裁定：`ALREADY_COVERED`（已被实质覆盖，且该问题本身有答案）。**

部分识别的 [0%,100%] **确实等价于"对该占比零信息"**——我们不否认。但文章的价值不在于这个界本身，而在于：
1. **证明了"原主张不可识别"**（`a24b_partial_id_summary.json::why_unidentified`：处理量×r 只观测供方 $D_i$，未观测需方 $E_i$），这本身是**对既有文献的一阶更正**；
2. **给出了真正可识别的量**（产能充分比例 0.39–6.55%），并明确了它的边界（只述产能、不述需求）；
3. SI §S12 L680–682 给出了**具体反例**（$D_i=1$ ML/d、既有用户仅取 0.1 ML/d 的小厂 → 池大体空闲，旧检验却判为 committed）。

**我们接受"该结果不构成正面发现"这一判断**，但不接受"因此不应报告"——**报告一个不可识别性是方法学贡献，前提是明确说明它不可识别**，而我们做到了。

### R-3 —— "$q>0$ 组 290/290 无有害例外" 是"自证"

**裁定：`PARTIALLY_REJECTED`（措辞需修正，但"自证"指控过强）。**

审稿意见（以及我们自己的 `A32/WP3` §2）都倾向称此为"空洞通过"。**但在主网格 $n=813$ 上，这不是空洞的**：若 $q$ 与符号独立，期望有害数 ≈ **47.8 例**，实测 **0 例**，Fisher $p\approx9.5\times10^{-22}$。**一个真实存在 47.8 例反例的检验出现了 0 例——这不是空洞通过，是强关联。**

**空洞的是完整水样网格（47 例）**，那里 $q\le0$ 组也零有害。**我们此前把两者混为一谈，是本稿的表述缺陷。**

**修正后的准确表述**："Across the 813-scenario grid, $q>0$ is associated with the city-benefit sign far beyond chance (0 harmful of 290, against ≈47.8 expected under independence; Fisher $p\approx9.5\times10^{-22}$). **In the 47-scenario complete-composition subset, however, the test is vacuous because no scenario is harmful at all**, so the sufficiency claim cannot be independently confirmed there."

---

## 第 5 节 · 本轮答复的量化汇总

| 类别 | 条数 | 编号 |
|---|---:|---|
| **`ACCEPTED`（接受，须改稿）** | 24 | M1-1, M1-2, M1-3(部分), M1-4, m1-1…m1-5(5), M2-1…M2-6(6), m2-1…m2-6(6), M3-1…M3-5(5), m3-1…m3-6(6) |
| **`ALREADY_COVERED`（已覆盖，不改）** | 1 | R-2 |
| **`REJECTED_AS_INVALID`（批评不成立）** | 2 | R-1, R-3(部分) |
| **`REQUIRES_NEW_EXPERIMENT`** | **4** | M3-1（R10a 重跑）、M3-2（换限值档）、M3-4（温度 PHREEQC）、M2-5（Sobol bootstrap） |

### `REQUIRES_NEW_EXPERIMENT` 汇总表

| # | 对应批评 | 方案 | 成本估计 | 若不做的后果 |
|---|---|---|---|---|
| **NE-1** | M3-1 | 在 **R10a 动态溶质路径**重跑 §7a 的 41 点碱度扫描 + sign-flip 诊断 | 164 次引擎调用，脚本已有 | 机制主张必须整体降级为"路径依赖" |
| **NE-2** | M3-2 | 在 **permissive / strict 限值档**重跑 sign-flip 诊断 | 328 次引擎调用，脚本已有 | "唯一杠杆"必须限定为 baseline 档 |
| **NE-3** | M3-4 | 用 **phreeqpython** 在 20/30/40 °C 算 IEUA/LADWP 钙酸盐限制 CoC，加入第 13 维 | 低 | −30% 必须删除，温度敏感性仍缺失 |
| **NE-4** | M2-5 | 对 Sobol 指数做 **bootstrap CI**（重用已有 256 样本设计） | 低（后处理） | 敏感性排序无不确定度 |

**执行优先级**：NE-1 > NE-2 > NE-3 > NE-4。**NE-1 的结论会直接决定本文能否保留"机制"这一措辞。**

---

## 第 6 节 · 我们向编辑承诺的事项

1. **M2-1（头条表口径）与 M2-6（SI 五处冲突）在本轮立即修正**——这两项使本文的"数字可追溯"主张失效，属流程缺陷。
2. **M2-3（0.901 vs 0.859）从摘要撤下**，按第 2 节给的措辞移入 Limitations。**这是本轮最痛的让步，但审稿人是对的。**
3. **M3-1 与 M3-2 在摘要加限定语**，并在 NE-1/NE-2 完成后据结果决定是否保留"机制"措辞。
4. **M1-4（O2 公平性）补做**，这是本文最明显的"唾手可得却未做"的分析。
5. **若 NE-1 显示 R10a 路径下质量项 ≈0 且无符号杠杆，本文的机制贡献将降级**，摘要相应重写。**我们不会因为结果不利而把 R10a 继续标为 `NOT_READY` 来规避。**
