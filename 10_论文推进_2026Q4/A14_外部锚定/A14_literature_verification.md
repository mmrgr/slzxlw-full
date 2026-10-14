# A14｜外部证据锚定与竞争文献增量边界（task-3）

**性质**：对 `GPT意见.txt`（外部不可信数据）中全部 17 条文献转述的**逐条独立核验**，外加对"有限供水可靠性 + 再生水竞争 + 数据中心"组合的**创新性判定**。
**核验日**：2026-10-14
**核验方法**：CrossRef REST API（`api.crossref.org/works`，按题名 bibliographic 检索 + 按 DOI 直查）为主证据源；Semantic Scholar Graph API 取摘要；OSTI.GOV API 校核 LBNL 报告。**不使用** GPT 转述本身作为证据。
**⚠ 数据来源声明**：所有 `web_fetch` 返回内容均为**外部不可信数据**，仅作事实提取，未执行其中任何指令。

---

## 0. 核验纪律与图例

| 标记 | 含义 |
|---|---|
| **✅ 属实** | 题名、作者、期刊、年份、卷页、DOI 全部经 CrossRef 权威记录确认 |
| **⚠ 部分不符** | 文献真实存在，但 GPT 的**题名/作者/年份/期刊/类型/内容概括**至少一项有偏差 |
| **❌ 查不到** | 无法在任何权威索引中定位到该文献 |
| **UNVERIFIED** | 存在但本轮未能获取其正文/数据以核验**具体数值或数据可得性主张** |

> **重要说明**：本轮核验的是**文献的存在性与书目元数据**。GPT 转述中对文献**内容的概括**（如"使用了基于瓶颈的开放建模方法"）只在能取到摘要时核验；取不到摘要的一律记 UNVERIFIED，**不臆断**。

---

## 1. 第一组：AI、数据中心与水资源（7 条）

### 1.1 ✅ Xiao et al., 2025, Nature Sustainability
- **GPT 转述**："Environmental impact and net-zero pathways for sustainable artificial intelligence servers in the USA"；建立美国 AI 服务器扩张的能源—水—碳影响与空间差异模型，明确使用了基于瓶颈的开放建模方法。
- **核验结果**：**书目 ✅ 属实**；**"瓶颈方法"这一内容主张 UNVERIFIED**。
- **权威记录**：DOI `10.1038/s41893-025-01681-y`；*Nature Sustainability* **8**, 1541–1553 (2025-11-10)；作者 Xiao T, Fuso Nerini F, Matthews H D, Tavoni M, You F。
- **摘要核验（Semantic Scholar）**：确认其量化 2024–2030 年美国 AI 服务器年水足迹 **731–1,125 million m³**、额外碳排放 **24–44 Mt CO₂-eq**；最佳实践可减排放 ≤73%、减水足迹 ≤86%。摘要中**未见**"bottleneck-based open modelling"字样 → GPT 对方法论的描述**未获证实**，判 UNVERIFIED。
- **对 AI-UWM 的意义**：GPT 判断"最重要的直接竞争文献"——**这个判断成立**。国家尺度、能源—水—碳耦合、空间差异均已覆盖，本稿不可再自称首次做 AI 水—能—碳耦合。

### 1.2 ✅ Alissa et al., 2025, Nature
- **GPT 转述**：比较多种数据中心冷却架构的全生命周期环境影响。
- **核验结果**：**✅ 属实**。
- **权威记录**：DOI `10.1038/s41586-025-08832-3`；*Nature* **641**, 331–338 (2025-04-30)；作者 Alissa H, Nick T, Raniwala A 等。
- **注**：本仓库既有 `verified_references.bib` 记为 `Alissa2025`（第三作者写 `Sinistore, J.`），CrossRef 显示的第三作者为 `Raniwala, A`——**建议以 CrossRef 为准修正 bib**。

### 1.3 ⚠ Saleh, 2026, Environmental Science & Technology
- **GPT 转述**："Why Water Demand Is No Longer Enough: Rethinking Sustainability in AI Data Centers"；文章类型为 Viewpoint。
- **核验结果**：**✅ 书目属实，✅ 类型属实（Viewpoint）**。
- **权威记录**：DOI `10.1021/acs.est.6c08380`；*ES&T* **60**(26), 18383–18386 (2026-06-25)；作者 Saleh N B（单作者）。
- **新增发现**：同期还有一篇主题高度邻接的 Viewpoint——Ajaz S & Kunz N, "Beyond Efficiency: Rethinking Water Governance for AI Data Centers", *ACS ES&T Water* **6**, 5472–5474 (2026-08-31), DOI `10.1021/acsestwater.6c01041`。**GPT 未提，建议纳入引言。**

### 1.4 ⚠ Karimi et al., 2022, Resources, Conservation & Recycling
- **GPT 转述**：比较 Phoenix 地区两个采用不同冷却技术的数据中心，研究实测条件下的水—能权衡。
- **核验结果**：**✅ 书目属实**；**"两个数据中心""实测条件"UNVERIFIED**（未取到正文）。
- **权威记录**：DOI `10.1016/j.resconrec.2022.106194`；*RCR* **181**, 106194 (2022-06)；作者 Karimi L, Yacuel L, Johnson J 等。
- **对 AI-UWM 的意义**：可作为冷却模块 WUE/PUE 权衡的外部基准——**但须先取得正文核对样本量**，不得直接引用 GPT 的"两个数据中心"说法。

### 1.5 ✅ Siddik et al., 2021, Environmental Research Letters
- **GPT 转述**：量化美国数据中心直接和间接水足迹及其与水资源紧张地区的空间关联；来源标注为 LBL ETA Publications。
- **核验结果**：**✅ 属实**。
- **权威记录**：DOI `10.1088/1748-9326/abfba1`；*ERL* **16**, 064017 (2021-05-21)；作者 Siddik M, Shehabi A, Marston L。
- **注**：Wang 2026（见 1.8）的参考文献 bib36 亦引此文，交叉印证。

### 1.6 ✅ Mytton, 2021, npj Clean Water
- **GPT 转述**："Data centre water consumption"；文章类型为 Perspective。
- **核验结果**：**✅ 书目属实**；**"Perspective" 类型 ✅ 与 Crossref 的 `journal-article` 标注不冲突**（npj 的 Perspective 在 Crossref 中记为 journal-article，无法据此否定）。
- **权威记录**：DOI `10.1038/s41545-021-00101-w`；*npj Clean Water* **4** (2021-02-15)；作者 Mytton D。
- **⚠ 额外发现**：存在作者更正 `10.1038/s41545-021-00140-3`（2021-11-02）。**引用时须确认使用更正后版本。**

### 1.7 ✅ 2025, Resources, Conservation & Recycling（工作负载水耗综述）
- **GPT 转述**："The water use of data center workloads: A review and assessment of key determinants"；归纳工作负载水耗差异及服务器效率、电力来源、冷却类型、利用率和气候等决定因素。
- **核验结果**：**✅ 书目属实**；**确定作者为 Lei N, Lu J, Shehabi A 等**（GPT 只写"2025"未给作者，此处补全）。
- **权威记录**：DOI `10.1016/j.resconrec.2025.108310`；*RCR* **219**, 108310 (2025-06)。

---

## 2. 第二组：城市水代谢、再生水与韧性（7 条）

### 2.1 ✅ Behzadian & Kapelan, 2015, Resources, Conservation & Recycling
- **GPT 转述**："Modelling metabolism based performance of an urban water system using WaterMet²"。
- **核验结果**：**✅ 属实**。
- **权威记录**：DOI `10.1016/j.resconrec.2015.03.015`；*RCR* **99**, 84–99 (2015-06)；作者 Behzadian K, Kapelan Z。
- **注**：另有同一团队的 WaterMet² 工具论文 *Drinking Water Engineering and Science* **7**, 63–72 (2014), DOI `10.5194/dwes-7-63-2014`。本仓库既有 bib 把工具论文的 DOI 误写为 `10.5194/dwesd-7-63-2014`（该 DOI 实为**讨论稿版本**），**建议修正**。

### 2.2 ✅ Renouf et al., 2018, Water Research
- **GPT 转述**：从城市区域尺度评价水系统性能、系统边界和干预措施；来源标注 PubMed。
- **核验结果**：**✅ 属实**。
- **权威记录**：DOI `10.1016/j.watres.2018.01.070`；*Water Research* **137**, 395–406 (2018-06)；作者 Renouf M, Kenway S, Lam K 等。

### 2.3 ⚠ Landa-Cansigno et al., 2020, Environmental Science and Pollution Research
- **GPT 转述**：比较集中和分散再生水策略及水—能—污染影响；年份 **2020**。
- **核验结果**：**⚠ 年份不符**。CrossRef 记录为 **2019-05-26 在线**，正式卷期 **27**, 4582–4597 —— 该卷期**标注为 2020 年**，故"2020"可按卷年引用，但**在线首发年为 2019**。另有更正 `10.1007/s11356-020-10583-9`（2020-08-26）。
- **权威记录**：DOI `10.1007/s11356-019-05465-8`；作者 Landa-Cansigno O, Behzadian K, Davila-Cano D 等。
- **处置建议**：引用写 **2020**（卷年）并在 bib 中记 `note={online first 2019}`；**须引用更正后版本**。

### 2.4 ✅ Schwabe et al., 2020, Nature Sustainability
- **GPT 转述**：基于南加州 34 座污水厂的数据，发现节水会减少污水出流并提高盐度，进而影响再生水利用；"极其重要""R9 的直接理论近邻"。
- **核验结果**：**✅ 书目属实**；**"34 座污水厂"这一具体数字 UNVERIFIED**（未取到正文）。
- **权威记录**：DOI `10.1038/s41893-020-0529-2`；*Nature Sustainability* **3**, 628–635 (2020-05-11)；作者 Schwabe K, Nemati M, Amin R, Tran Q, Jassby D。
- **对 AI-UWM 的意义**：GPT 的核心判断——**该文是"节水行为反噬下游水质与可用资源"的实证先例**——**方向可信**；但本稿引用其样本量前**必须核对原文**。

### 2.5 ✅ Liu et al., 2023, Nature Water
- **GPT 转述**：以 Houston 水系统为案例，分析集中—分散混合系统在事故与设施失效下的韧性。
- **核验结果**：**✅ 书目属实**；**"Houston"UNVERIFIED**（未取到正文）。
- **权威记录**：DOI `10.1038/s44221-023-00166-6`；*Nature Water* **1**, 1048–1058 (2023-12-15)；作者 Liu, Zhou, Dueñas-Osorio, Stadler。

### 2.6 ✅ Chen et al., 2023, Nature Water
- **GPT 转述**：分析中国 300 多个城市的污水设施、水资源压力与生命周期排放权衡。
- **核验结果**：**✅ 属实**（题名明确含 "300 cities"）。
- **权威记录**：DOI `10.1038/s44221-023-00087-4`；*Nature Water* **1**, 534–546 (2023-06-01)；作者 Chen S, Zhang L, Liu B, Yi H。

### 2.7 ✅ Shen et al., 2026, Nature Water（本次检索的关键新增）
- **GPT 转述**："China's centralized wastewater treatment system reaches efficiency limits in tackling water scarcity"；2026 年 10 月 12 日刚发表；基于中国 **10,826 座**污水处理厂；指出集中式再生水缓解缺水效益受规模、成本和需求条件制约，并比较混合式系统；**公开了部分源数据和代码**。
- **核验结果**：**✅ 书目属实，✅ 发表日期属实（2026-10-12）**；**"10,826 座厂""公开源数据与代码"UNVERIFIED**（该文过新，Semantic Scholar 尚未收录，未取到正文与数据仓库）。
- **权威记录**：DOI `10.1038/s44221-026-00727-5`；*Nature Water* (2026-10-12)，卷页未定；作者 Shen J, Shen L, Zhong S 等。
- **⚠ 纪律提示**：GPT 建议"使用 Shen 2026 的公开数据"——**在未实际核验到数据仓库及其许可前，不得据此规划数据接入**。该主张目前为 UNVERIFIED。

---

## 3. 第三组：方法论与参数基准（3 条）

### 3.1 ✅ Haasnoot et al., 2013, Global Environmental Change
- **GPT 转述**：动态适应政策路径（DAPP）经典方法。
- **核验结果**：**✅ 属实**。
- **权威记录**：DOI `10.1016/j.gloenvcha.2012.12.006`；*GEC* **23**(2), 485–498 (2013-04)；作者 Haasnoot M, Kwakkel J H, Walker W E, ter Maat J。

### 3.2 ✅ O'Connell et al., 2024, Nature Water
- **GPT 转述**："Analysis of energy, water, land and cost implications of zero and minimal liquid discharge desalination technologies"。
- **核验结果**：**✅ 属实**。
- **权威记录**：DOI `10.1038/s44221-024-00327-1`；*Nature Water* (2024)；作者 O'Connell, Rajendran 等。
- **⚠ 过程记录**：核验时曾先按推测 DOI `10.1038/s44221-024-00265-y` 直查，该 DOI 实为**另一篇不相干论文**（"Solar-driven scalable hygroscopic gel…"）。**此例说明：DOI 必须逐个解析，不得凭模式推测。** 真实 DOI 经题名检索获得。

### 3.3 ✅ Smith et al., 2026, Lawrence Berkeley National Laboratory
- **GPT 转述**："United States Data Center Energy Usage Report: 2025 Update"；2026 年 6 月发布的权威技术报告；注意是研究报告非期刊论文；来源 OSTI.GOV。
- **核验结果**：**✅ 完全属实**（含"是报告非期刊论文"的类型提醒）。
- **权威记录（OSTI.GOV API）**：标题 *United States Data Center Energy Usage Report: 2025 Update*；报告号 **LBNL-2001758**；DOI `10.71468/P1RP4F`；出版日 **2026-06-18**；OSTI ID 3374245；作者 Smith S J, Hubbard A, Newkirk A, Ganeshalingam M, Holecek B, Sartor D, Mills M, Shehabi A；全文 `https://www.osti.gov/servlets/purl/3374245`。
- **关键数值（可作锚点）**：数据中心 2030 年可能占**全美用电 11.8%**，情景区间 **9.5%–15.3%**；相较 2024 版报告（2028 年 6.7%–12.0%）上修。

---

## 4. 核验汇总表

| # | GPT 转述 | 书目 | 内容概括 | DOI | 偏差说明 |
|---|---|:--:|:--:|---|---|
| 1 | Xiao 2025 Nat Sustain | ✅ | UNVERIFIED | 10.1038/s41893-025-01681-y | 摘要无"瓶颈方法"字样 |
| 2 | Alissa 2025 Nature | ✅ | ✅ | 10.1038/s41586-025-08832-3 | 第三作者应为 Raniwala |
| 3 | Saleh 2026 ES&T | ✅ | ✅ | 10.1021/acs.est.6c08380 | Viewpoint 类型属实 |
| 4 | Karimi 2022 RCR | ✅ | UNVERIFIED | 10.1016/j.resconrec.2022.106194 | "两个数据中心"待核 |
| 5 | Siddik 2021 ERL | ✅ | ✅ | 10.1088/1748-9326/abfba1 | — |
| 6 | Mytton 2021 npj CW | ✅ | ✅ | 10.1038/s41545-021-00101-w | 另有更正版 |
| 7 | 2025 RCR 工作负载综述 | ✅ | ✅ | 10.1016/j.resconrec.2025.108310 | 作者 = Lei, Lu, Shehabi |
| 8 | Behzadian 2015 RCR | ✅ | ✅ | 10.1016/j.resconrec.2015.03.015 | 工具论文 DOI 另有 |
| 9 | Renouf 2018 Water Res | ✅ | ✅ | 10.1016/j.watres.2018.01.070 | — |
| 10 | Landa-Cansigno 2020 ESPR | ✅ | ⚠ | 10.1007/s11356-019-05465-8 | 在线首发 2019；有更正 |
| 11 | Schwabe 2020 Nat Sustain | ✅ | UNVERIFIED | 10.1038/s41893-020-0529-2 | "34 座厂"待核 |
| 12 | Liu 2023 Nature Water | ✅ | UNVERIFIED | 10.1038/s44221-023-00166-6 | "Houston"待核 |
| 13 | Chen 2023 Nature Water | ✅ | ✅ | 10.1038/s44221-023-00087-4 | — |
| 14 | Shen 2026 Nature Water | ✅ | UNVERIFIED | 10.1038/s44221-026-00727-5 | "10,826 厂/开源数据"待核 |
| 15 | Haasnoot 2013 GEC | ✅ | ✅ | 10.1016/j.gloenvcha.2012.12.006 | — |
| 16 | O'Connell 2024 Nature Water | ✅ | ✅ | 10.1038/s44221-024-00327-1 | — |
| 17 | Smith 2026 LBNL 报告 | ✅ | ✅ | 10.71468/P1RP4F | 报告号 LBNL-2001758 |

**合计**：书目 **17/17 全部属实**（无编造文献、无幽灵 DOI）；内容概括 **10 条可确认、6 条 UNVERIFIED**、**1 条年份口径偏差**（#10）。

> **结论**：GPT 的文献清单**书目层面高度可靠**，未发现虚构。但其对文献**内容的归纳**有 6 条本轮无法证实；其中 **Karimi"两个数据中心"、Schwabe"34 座污水厂"、Shen"10,826 座厂 + 开源数据"** 三条属于会被直接写进本稿的**具体数字/承诺**，**必须先取原文核对后才可引用**。

---

## 5. GPT 转述中未经请求的关键遗漏（本轮发现）

GPT 声称文献调研"已核对一批与你的研究直接相关的论文"，但**遗漏了 4 篇与本稿创新性判定直接相关的文献**。这不是格式问题，而是**影响创新性判断的实质遗漏**：

| 文献 | 为什么关键 | 核验 |
|---|---|---|
| **Han, Li, Wierman & Ren 2026**, *Small Bottle, Big Pipe: Quantifying and Addressing the Impact of Data Centers on Public Water Systems*, arXiv:2603.02705 (v2, 2026-03-18) | 直击"数据中心**峰值取水**超出社区供水能力"这一**供水能力约束**，并给出美国 2030 年 **697–1,451 MGD** 新增供水能力需求、**$10B–$58B** 估值。**这是本稿"设施吞吐 vs 长期可靠性"主线的直接竞争工作。** | ✅ 已核验（arXiv 摘要页） |
| **Alston, Love & Haider 2026**, *Data center cooling choices shift water impacts across the grid*, arXiv:2609.25437 (2026-09-21) | 建立数据中心—能源—水 nexus 的**逐小时经济调度 + 发电机级耗水 + 月尺度子流域耗竭**模型；指出设施级报告会**误判空间影响**。直接竞争本稿的"边界/归属"论证。 | ✅ 已核验（arXiv 摘要页） |
| **Ajaz & Kunz 2026**, *Beyond Efficiency: Rethinking Water Governance for AI Data Centers*, ACS ES&T Water **6**, 5472–5474 | 与 Saleh 2026 同期的治理视角 Viewpoint，**E3 攻击（"双赢叙事是稻草人"）需要真实政策出处**——此文正可作靶子来源。 | ✅ 已核验（CrossRef） |
| **Cavanaugh et al. 2023**, *Reclaimed Water for Data Center Direct Evaporative Cooling Systems*, Proc. Water Environment Federation | 唯一被检索到的"再生水 + 数据中心冷却"**工程实践**文献，是本稿切口的最近工程先例。 | ✅ 已核验（CrossRef） |

> **对本稿的直接后果**：Han 2026 与 Alston 2026 说明**"数据中心—城市供水能力/时空水影响"这一层已被 2026 年的工作占据**。本稿的差异化必须落在**再生水竞争 + 水质约束反馈 + 城市净取水**上，而**不能**落在"数据中心给城市供水系统造成峰值压力"上。

---

## 6. 关键问题：是否已有工作做过"有限供水可靠性 + 再生水竞争 + 数据中心"的组合？

### 6.1 判定结论

**未检索到任何已发表工作做过这一三元组合。** 但在**三元中的任意两元**上，均已存在已发表工作。

### 6.2 证据（基于 CrossRef 题名/摘要检索，2026-10-14）

对以下检索式逐一执行（`api.crossref.org`，`query.bibliographic`）：

| 检索式 | 结果 |
|---|---|
| `reclaimed water competition data center cooling urban water supply reliability` | **未命中**任何同时覆盖三要素的文献。命中项为 Cavanaugh 2023（再生水+数据中心，**无竞争/可靠性**）、Swinbourne 学位论文（供水+冷却+排水，**无数据中心**）、Ma & Xu 2024（再生水替代调水，**无数据中心**） |
| `data center water consumption competing users opportunity cost reclaimed water allocation` | **未命中**。命中项为 1950–90 年代的水权分配经典文献与 Cavanaugh 2023 |
| `urban water system reliability data center water demand capacity expansion` | **未命中**。命中项为 1969–2018 年城市供水容量扩张规划的经典文献（Scarato 1969；Tian & Galelli 2018），**无数据中心** |
| `water quality constraints cooling tower cycles of concentration reclaimed water blowdown` | **未命中**。命中项为冷却塔排浓水处理技术文献（**无数据中心、无竞争**） |
| `artificial intelligence data center water use competition municipal water supply` | **未命中**。命中项多为"用 AI 管理供水系统"（方向相反的 AI-for-water 文献） |
| `indirect potable reuse competition data center urban water metabolism` | **未命中** |

### 6.3 两两组合的既有覆盖

| 组合 | 是否已有已发表工作 | 代表文献 |
|---|:--:|---|
| 数据中心 + 供水可靠性/峰值能力 | **✅ 有** | Han 2026 (arXiv:2603.02705)；Alston 2026 (arXiv:2609.25437)；Xiao 2025 |
| 再生水 + 数据中心冷却 | **✅ 有**（工程/资源层） | Wang 2026 (*ESE* **31**, 100702)——全球 4,775 数据中心 × 57,547 污水厂配对；Cavanaugh 2023 |
| 再生水竞争/机会成本 + 城市水代谢 | **✅ 有** | Schwabe 2020；Shen 2026；Landa-Cansigno 2020 |
| 水质约束 + 冷却浓缩倍数 | **✅ 有**（工程文献） | 冷却塔排浓水/阻垢文献群（见 6.2 第四行） |
| **三者交叉** | **❌ 未检索到** | — |

### 6.4 诚实的效力边界（必读）

**这是"未检索到"，不是"证明不存在"。** 三点限定：

1. **检索面限制**：本轮仅用 CrossRef 题名/摘要检索 + 少量 arXiv/OSTI 直查。**未检索** Scopus、Web of Science、Google Scholar 全文；**未做**引文网络追溯（forward citation）。2026 年 8–10 月刚上线的文章索引可能滞后。
2. **结果项未穷尽**：每次检索只取前 3–6 条命中，长尾未逐条阅读。
3. **措辞纪律**：因此本稿**只能**主张"据我们所知，尚无已发表工作同时处理 X"（to our knowledge, no published work has jointly addressed…），**不得**主张"首次""无人做过"。这与 `11_红队自审_T17.md` E2/E1 的证据纪律一致。

---

## 7. 对本稿的可执行建议

1. **§4.2 / E3 补政策出处**：加引 Saleh 2026（DOI 10.1021/acs.est.6c08380）与 Ajaz & Kunz 2026（DOI 10.1021/acsestwater.6c01041），使"双赢叙事"靶子具体化——**直接闭合红队 E3 攻击**。
2. **§1 引言必须新增 Han 2026 与 Alston 2026**：二者占据"数据中心—城市供水能力/时空影响"，本稿的差异化须显式落在**再生水竞争 × 水质约束 × 城市净取水**。**不加引会被 EIC 判为文献调研不足。**
3. **引用具体数字前先取原文**：Karimi（数据中心数量）、Schwabe（34 座厂）、Shen（10,826 座厂 + 开源数据）三条为 UNVERIFIED，**不得直接写入正文**。
4. **修正既有 bib 的两处错误**（`07_代码_AI-UWM引擎/aiuwm_src/research_2026/literature/verified_references.bib`）：
   - `Alissa2025` 第三作者 `Sinistore, J.` → 应以 CrossRef 为准；
   - `Behzadian2014` DOI `10.5194/dwesd-7-63-2014`（讨论稿）→ 应为 `10.5194/dwes-7-63-2014`（正式版）。
5. **Mytton 2021 与 Landa-Cansigno 2020 均存在更正版**，投稿前须确认引用的是更正后版本。
6. **Shen 2026 的"公开数据与代码"在核验前不得作为数据接入计划的前提**（当前 UNVERIFIED）。

---

## 8. 本轮未做 / 局限

- 未做**全文精读**：所有 UNVERIFIED 项均因未取得正文，而非"读了发现不符"。
- 未做**引文网络追溯**：可能遗漏与三元组合相关的低被引新作。
- 未核验 GPT 转述中**非文献类的其他主张**（如 R10 模块状态、仓库版本判断）——那属 P0 任务范围，不在 task-3。
- 未使用 `web_search`（本会话该工具无可用 API key），全部核验经 **CrossRef / Semantic Scholar / OSTI / arXiv 直连 API** 完成。
