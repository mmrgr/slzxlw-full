# A29｜创新重叠与差异表 + "不支持首次主张"清单

**编制日期**：2026-10-16
**依据**：`literature_verification.md` 中经一手材料核验的文献
**结论摘要**：本项目 4 项自认创新中，**(a) 已由项目方自认为非独立发现**，**(b)(c) 的*议程*已被 Saleh 2026 (*ES&T* Viewpoint) 占据**，**(b)(c) 的*形式化与符号反转证明*目前未检索到先例**，**(d) 的反事实框架未见直接先例但方法论上属标准做法**。**"首次"类表述须全面降级为 "to our knowledge" 措辞。**

---

## 0. 本项目自认创新候选（原文）

| 编号 | 内容 |
|---|---|
| **(a)** | 统一记账恒等式 **dS_pot = C − F**（排放—索取平衡），C = 既有用户须补回量，F = AI 少取的自来水量。**项目方已承认这是守恒代数重排，非独立发现。** |
| **(b)** | 闭式关系 **q = (CoC₁ − CoC₀) / (CoC₁(CoC₀ − 1))**，即"回用降低补水 ⟺ 回用提高允许浓缩倍数"（q>0 ⟺ CoC₁>CoC₀）。 |
| **(c)** | 冷却**水质**（多离子组分、结垢/碱度联合约束）会改变净收益**符号**——高盐再生水可反转结论。 |
| **(d)** | 三反事实框架 **B0/B1/B2** 与"纯挤占 → dS = M₁ − M₀；无挤占 → dS = −(M₀ − M₁) − x_AI"两分支。 |

---

## 1. 逐条重叠与差异对照表

### (a) dS_pot = C − F（守恒记账恒等式）

| 维度 | 判定 |
|---|---|
| **重叠文献** | **无直接先例**（未检索到该恒等式的同形式表述） |
| **但** | 质量平衡记账是城市水代谢领域的**标准做法**，已被系统化 20 年 |
| 代表文献 | Behzadian & Kapelan 2015, WaterMet²（`10.1016/j.resconrec.2015.03.015`）；Renouf et al. 2018（`10.1016/j.watres.2018.01.070`）；Wang et al. 2026 *ESE*（`10.1016/j.ese.2026.100702`） |
| **重叠程度** | 🔴 **高（方法论层面）** |
| **能否声称首创** | ❌ **不能** |
| **理由** | 项目方**自认**为"守恒代数重排，非独立发现"。且水系统质量平衡记账在 WaterMet² 等框架中已是既定操作。**任何"首次提出记账恒等式"的表述都不成立。** |
| **确有增量** | ✅ 弱增量：该恒等式**被用于分离"AI 少取的自来水 (F)"与"既有用户须补回量 (C)"这两个此前未被分开记账的项**，且服务于数据中心场景。可作为**应用层定义**而非理论创新呈现。 |
| **建议措辞** | "We adopt a conservation-based accounting identity (Eq. X) to separate …"（**陈述事实，不主张新颖**） |

---

### (b) 闭式关系 q = (CoC₁ − CoC₀) / (CoC₁(CoC₀ − 1))

| 维度 | 判定 |
|---|---|
| **头号重叠文献** | **Saleh, N. B. (2026)**. *Why Water Demand Is No Longer Enough: Rethinking Sustainability in AI Data Centers*. ***ES&T*** **60**(26), 18383–18386. DOI `10.1021/acs.est.6c08380`. **类型：Viewpoint** |
| **该文原文** | "As cooling systems increasingly rely on **recirculation and reuse**, the challenge extends **beyond water quantity to water compatibility**." |
| **重叠程度** | 🟠 **议程层面：高**／**形式化层面：无** |
| **能否声称首创** | ⚠️ **拆分主张**：议程 ❌ 不能；**闭式形式化 ✅ 目前未检索到先例** |
| **理由** | Saleh 2026 已在 2026-06-25 于 ES&T **公开主张**"水质兼容性（而非用水量）才是 AI 数据中心可持续性的关键"。若本项目声称"首次提出应关注水质"，属**明确的可查证重复**。**但**该文是 **Viewpoint/editorial**，**全文不含模型、不含 CoC 变量、不含闭式关系**（原文本轮已核验其类型与摘要）。 |
| **确有增量** | ✅ **中等增量**：把议程**落实为可解闭式关系**，并给出 q>0 ⟺ CoC₁>CoC₀ 的判据。 |
| **⚠️ 另一重叠风险** | **Badruzzaman et al. (2022)**, *Water Resources and Industry* **28**, 100188（`10.1016/j.wri.2022.100188`）**已实测**"用再生水替代地下水，**通过提高浓缩倍数**提升水效"。该文是 q>0 方向的**工程实证先例**——本项目**不能**声称"首次发现再生水可提高浓缩倍数"。**可主张的是：给出闭式判据 + 在数据中心/城市尺度上量化其净效应。** |
| **建议措辞** | ❌ 删除："we are the first to note that water quality matters"<br>✅ 改为："**Building on the agenda set by Saleh (2026)**, we formalise the cooling-water reuse condition as a closed-form relation (Eq. Y) and show that …" |

---

### (c) 冷却水质改变净收益符号（多离子/结垢/碱度联合约束）

| 维度 | 判定 |
|---|---|
| **头号重叠文献** | 同上：**Saleh 2026 *ES&T* Viewpoint**（议程）+ **Badruzzaman 2022**（提高 CoC 的工程实证） |
| **次号重叠** | **Wang et al. 2026 *ESE***（`10.1016/j.ese.2026.100702`）—— ⭐ **反向利用**（见下） |
| **重叠程度** | 🟠 **中等** |
| **能否声称首创** | ⚠️ **谨慎**：**符号反转的定量证明**目前**未检索到**先例，但**"水质/结垢是冷却回用的关键约束"这一判断已是领域常识** |
| **理由（关键）** | 本轮对 Wang 2026 全文做了**术语计数**：`CoC` = 0 次、`salinity` = 0 次、`conductivity` = 0 次、`TDS` = 0 次、`quality constraint` = 0 次；`scaling` 仅 2 次，且均定性为"可通过常规措施有效管理的运维关切"。**该文主动把水质排除在系统边界之外**（原文："water reused within recirculating cooling systems is not included"）。 |
| **✅ 确有增量（本项目最实质的增量）** | 在**已有强竞争文献主动排除该机制**的前提下，证明**把水质内生化会反转净收益符号**——这是从"运维关切"到"结论符号决定因素"的**层级跃迁**。 |
| **⚠️ 红线** | 该文（Wang 2026）作者群含 KWR、Exeter、Michigan、HIT，**与本项目高度同域**；其"排除循环冷却水"的边界很可能被审稿人视为**留给本项目的公开缺口**，也可能被视为**下一篇的自然延伸**。**本项目需要尽快发表以占据该缺口。** |
| **建议措辞** | ✅ "Whereas recent global assessments explicitly **exclude** water recirculated within cooling systems from their system boundary, we show that **internalising cooling-water chemistry can reverse the sign** of the net urban water benefit."（**有据、可查证、不越界**） |

---

### (d) 三反事实框架 B0/B1/B2 与两分支公式

| 维度 | 判定 |
|---|---|
| **重叠文献** | **无直接先例**（未检索到 B0/B1/B2 同构的三反事实设计） |
| **但（方法论）** | 反事实/情景对比是水系统评估的标准范式；"挤占 (crowding-out)"概念在再生水竞争文献中已存在 |
| **相关先例** | **Chen et al. 2023** *Nature Water* **1**, 534–546（`10.1038/s44221-023-00087-4`）——中国 **300 城**"水压力缓解 vs 污水 GHG 解耦"，已确立"缓解缺水与环境代价之间存在权衡"的分析范式<br>**Schwabe et al. 2020** *Nature Sustainability* **3**, 628–635（`10.1038/s41893-020-0529-2`）——节水**反噬**下游水质与可用资源的实证先例<br>**Landa-Cansigno et al. 2020** *ESPR* **27**, 4582–4597（`10.1007/s11356-019-05465-8`）——集中 vs 分散再生水策略的多情景对比 |
| **重叠程度** | 🟡 **中低** |
| **能否声称首创** | ⚠️ **可主张"据我们所知，尚无…"**，但**不可**主张"首次提出反事实比较" |
| **确有增量** | ✅ 中等增量：把"**AI 负荷引入是否挤占既有用户**"显式建模为**两个可分辨分支**，并将 dS 的**符号**作为判定对象。 |
| **建议措辞** | ✅ "To our knowledge, no published framework contrasts **with-** and **without-crowding-out** counterfactuals for AI cooling demand at the urban scale."<br>❌ 删除任何"first counterfactual framework"字样 |

---

## 2. 🔴 "不支持首次主张"清单（必须删除或弱化的具体表述）

按**威胁等级**排序。每条给出：会迫使删改的文献 → 被禁止的表述 → 替换措辞。

| # | 等级 | 会迫使删改的文献 | ❌ 禁止写入的表述 | ✅ 允许的替换 |
|---|---|---|---|---|
| **1** | 🔴 **致命** | **Saleh 2026**, *ES&T* **60**(26), 18383–18386, `10.1021/acs.est.6c08380`（**Viewpoint**，2026-06-25）<br>原文："the challenge extends **beyond water quantity to water compatibility**" | ❌ "首次提出 AI 数据中心水评价应超越用水量、关注水质兼容性"<br>❌ "first to recognise the importance of water quality in AI data-centre water assessment"<br>❌ "we are the first to shift the focus from quantity to quality" | ✅ "**Building on the agenda set by Saleh (2026)**, we formalise this condition as a closed-form relation (Eq. Y)…"<br>——把新颖性**放在形式化与定量证明**上，**不放在议程上** |
| **2** | 🔴 **致命** | **Wang et al. 2026**, *Environmental Science and Ecotechnology* **31**, 100702, `10.1016/j.ese.2026.100702`（research article；4,775 DC × 57,547 WWTP；98 国；空间+工程+优化+LCA） | ❌ "首次构建全球数据中心—污水厂匹配框架"<br>❌ "first global framework pairing data centres with wastewater treatment plants"<br>❌ "first to quantify water–carbon symbiosis potential"<br>❌ "first integrated spatial/engineering/optimisation/LCA analysis of DC–WWTP symbiosis" | ✅ 必须**正面引用为竞争文献**，并显式划界：<br>"Recent global assessments have established the DC–WWTP symbiosis potential (Wang et al., 2026). **However, that framework excludes water recirculated within cooling systems from its boundary, and does not resolve urban-scale net withdrawal.** Here we …" |
| **3** | 🟠 **高** | **Xiao et al. 2025**, *Nature Sustainability* **8**(12), 1541–1553, `10.1038/s41893-025-01681-y`（research article） | ❌ "首次量化 AI 服务器的水—能—碳耦合影响"<br>❌ "first integrated energy–water–carbon assessment of AI servers"<br>❌ "first spatially explicit AI water footprint" | ✅ "Extending national-scale AI energy–water–carbon assessments (Xiao et al., 2025), we resolve the **city-scale net withdrawal** under reuse and cooling-water-quality constraints." |
| **4** | 🟠 **高** | **Han et al. 2026**, arXiv:2603.02705（`10.48550/arxiv.2603.02705`，preprint）<br>**Alston et al. 2026**, arXiv:2609.25437（`10.48550/arxiv.2609.25437`，preprint） | ❌ "首次研究数据中心对城市公共供水系统能力的冲击"<br>❌ "first to show data centres impose peak demand on municipal water systems"<br>❌ "first to show facility-level reporting misattributes spatial water impacts" | ✅ "While peak-demand and grid-coupled water impacts of data centres are now documented (Han et al., 2026; Alston et al., 2026), **the competition for reclaimed water among urban users, and its quality-bounded limits, remain unresolved**." |
| **5** | 🟠 **高** | **Chen et al. 2023**, *Nature Water* **1**, 534–546, `10.1038/s44221-023-00087-4`（research article，300 城） | ❌ "首次识别水压力缓解与污水系统碳排放之间的权衡"<br>❌ "first to reveal the trade-off between water stress alleviation and wastewater GHG" | ✅ "The trade-off between water-stress alleviation and wastewater-related GHG emissions is established across 300 Chinese cities (Chen et al., 2023). We extend this to **AI-driven cooling demand with water-quality-bounded reuse**." |
| **6** | 🟠 **高** | **Badruzzaman et al. 2022**, *Water Resources and Industry* **28**, 100188, `10.1016/j.wri.2022.100188`（research article，实测） | ❌ "首次发现再生水回用可通过提高浓缩倍数改善水效"<br>❌ "first to show reclaimed water raises the achievable cycles of concentration" | ✅ "Field evidence that reclaimed water can raise achievable cycles of concentration exists for industrial cooling (Badruzzaman et al., 2022); **we derive the general closed-form condition and evaluate its urban-scale consequences.**" |
| **7** | 🟡 **中** | **Behzadian & Kapelan 2015** `10.1016/j.resconrec.2015.03.015`；**Renouf et al. 2018** `10.1016/j.watres.2018.01.070`；**Garrido-Baserba et al. 2024** `10.1038/s44221-024-00303-9` | ❌ "首次构建城市尺度水系统代谢/单元过程模型"<br>❌ "first urban-scale water metabolism model incorporating supply, use, wastewater and recycling" | ✅ "Using an established urban water metabolism formulation (e.g., WaterMet²; Renouf et al., 2018), we add …" |
| **8** | 🟡 **中** | **Lei et al. 2025**, *RCR* **219**, 108310, `10.1016/j.resconrec.2025.108310`（**review**, LBNL） | ❌ "首次系统归纳数据中心用水差异的决定因素"<br>❌ "first to identify server efficiency / cooling type / climate / grid as determinants" | ✅ 直接引为参数锚定来源，不主张新颖。 |
| **9** | 🟡 **中** | **Isler-Kaya & Karaosmanoglu 2023** `10.1016/j.enbuild.2023.113006`；**Alissa et al. 2025**, *Nature* **641**, 331–338, `10.1038/s41586-025-08832-3` | ❌ "首次对数据中心冷却方案做生命周期评价" | ✅ 冷却 LCA 已是成熟领域（含 *Nature* 正刊），仅作参数来源引用。 |
| **10** | 🟢 **低（但措辞仍需改）** | 全部上述文献 + **检索面局限** | ❌ "首次发现 / 首次提出 / 无人做过 / 首个"<br>❌ "the first study to …"<br>❌ "no previous work has …"（**绝对否定**） | ✅ "**To our knowledge**, no published framework simultaneously resolves (i) reclaimed-water competition, (ii) cooling-water chemistry, and (iii) city-scale net withdrawal under AI load."<br>——即 A14 第 6.4 节已确立的**措辞纪律** |

---

## 3. 本项目可**安全主张**的增量（经检索未发现先例）

> ⚠️ 前提：以下均为"**未检索到**"而非"证明不存在"。措辞必须带 "to our knowledge"。

| 增量 | 证据基础 | 强度 |
|---|---|---|
| **① 把冷却水质组成内生化，证明净收益符号可反转** | Wang 2026 (*ESE*) 全文 `CoC`/`salinity`/`TDS`/`conductivity`/`quality constraint` **出现次数均为 0**，且**明确声明**排除循环冷却水；Saleh 2026 仅在 Viewpoint 中**提议程**，无模型 | 🟢 **最强**（有明确的"被排除的边界"作为可查证依据） |
| **② 闭式判据 q = (CoC₁−CoC₀)/(CoC₁(CoC₀−1))** | 未检索到同形式关系；Badruzzaman 2022 只有实测方向，无一般判据 | 🟢 **强** |
| **③ 城市尺度"排放—索取"净记账在大模型负荷下的应用** | Wang 2026 是设施/国家配对的 gate-to-gate LCA，**不做城市水系统净取水记账**；Xiao 2025 是国家尺度 | 🟡 **中**（记账本身是标准做法，增量在**应用场景**） |
| **④ 三反事实 B0/B1/B2 + 挤占/无挤占两分支** | 未检索到同构框架 | 🟡 **中**（方法论上属标准反事实比较） |
| **⑤ 逐日时间分辨率** | ❌ **证据不足** | 🔴 **不可主张**（见下） |

### ⚠️ 特别警示：不要把"逐日分辨率"当作卖点

C10 的核验**未能证实**存在"逐日城市水代谢模型"，但也**未能证伪**——检索面仅限 CrossRef/OpenAlex 题名+摘要，**未读各文方法节**，**未做** Scopus/WoS 全文与引文追溯。

⇒ **在完成上述检索之前，本项目不得主张"首次以逐日分辨率建模"**。若审稿人举出一篇逐日城市水代谢模型，该主张将直接崩塌。建议：要么补做检索，要么**完全不把时间分辨率作为新颖性论点**，只作为方法细节陈述。

---

## 4. 综合判定

### 4.1 逐条结论

| 编号 | 重叠度 | 能否称"首次" | 实际增量 |
|---|:--:|:--:|---|
| **(a)** dS_pot = C − F | 🔴 高（方法论已成熟 + 项目方自认非发现） | ❌ **绝对不能** | 弱：仅"分离 C 与 F 两项"的应用定义 |
| **(b)** 闭式关系 q | 🟠 议程高／形式化无 | ⚠️ **议程不能，形式化可以**（带 "to our knowledge"） | 中：议程→闭式判据 |
| **(c)** 水质改变符号 | 🟠 中 | ⚠️ **可以**（**本项目最强增量**） | **强**：从"运维关切"跃迁为"符号决定因素" |
| **(d)** 三反事实 B0/B1/B2 | 🟡 中低 | ⚠️ **可以**（带 "to our knowledge"） | 中：挤占/无挤占的可分辨分支 |

### 4.2 一句话结论

> **本项目的可辩护创新不是任何单点的"首次"，而是"水质约束下的再生水竞争会反转净收益符号"这一机制性发现（创新点 c），其最强的立论基础恰恰是头号竞争文献 Wang et al. (2026) 在原文中公开声明的系统边界排除。**
>
> **全部 "first/首次/首个" 字样必须删除**，统一替换为 A14 第 6.4 节确立的 "to our knowledge, no published work has jointly addressed…" 措辞。

### 4.3 投稿策略提示

1. **优先级**：本项目与 Wang et al. (2026)、Saleh (2026) 处在**同一窗口期**（均 2026 年）。Wang 2026 已公开排除冷却水内部水质机制，**该缺口公开可见，随时可能被其后续工作或他人填补**。建议**尽快投稿**。
2. **必须正面处理的竞争文献**：Wang 2026 (ESE)、Saleh 2026 (ES&T Viewpoint)、Xiao 2025 (Nat Sustain)、Han 2026 (arXiv)、Alston 2026 (arXiv)、Chen 2023 (Nat Water)。**六篇中任何一篇漏引，都足以被 EIC 判为文献调研不足。**
3. **不要与 Wang 2026 比规模**：它做了 4,775 DC × 57,547 WWTP × 98 国。本项目应比**机制深度**（CoC 内生、符号反转、城市净记账），而非比数据覆盖。
4. **Saleh 2026 是 Viewpoint，可被"建设性推进"**：Viewpoint 的功能就是设定议程；本项目作为研究论文去**实现**该议程，是学界正当且常见的做法——**但必须在文中显式致谢该议程来源**，否则会被视为侵占他人 idea。

---

## 5. 局限

- 所有"未检索到先例"的判定**受限于检索面**（CrossRef + OpenAlex + Zenodo + Semantic Scholar + Europe PMC；**未覆盖** Scopus / WoS / Google Scholar 全文；**未做**引文网络追溯）。
- **未精读**除 C2 (Wang 2026) 与 C1 (Shen 2026 源数据) 外的其余文献正文；(b)(c) 的"无先例"判定基于**摘要级/元数据级**检索，**存在遗漏低被引先例的风险**。
- `web_search` 在本会话**无 API key**，无法进行跨库全文检索。
- 本文件**未修改**任何现有研究文件。
