# A29｜GPT 意见候选文献独立核验报告

**核验日期**：2026-10-16
**核验人**：literature-verifier（独立于 A14 轮）
**核验范围**：GPT 评审意见所列 10 条"核心必读文献"（本项目自认创新点 (a)–(d) 见 `innovation_overlap.md`）
**与 A14 轮（2026-10-14）的关系**：A14 核验的是**另一份 17 条清单**。本轮 10 条中有 5 条与 A14 重叠（C1 Shen / C5 Chen / C6 / C8 Lei / C10）。A14 遗留的 3 条 UNVERIFIED（Shen 的"10,826 座厂"与"开源数据"、竞争文献 Wang 2026）**本轮已全部闭合**。

---

## 0. 核验纪律

| 项 | 做法 |
|---|---|
| 主证据源 | **CrossRef REST API**（`api.crossref.org/works`，题名 bibliographic 检索 + DOI 直查）、**OpenAlex API**（`api.openalex.org`，含 `abstract_inverted_index` 补摘要）、**Zenodo API**、**Semantic Scholar Graph API**、**Europe PMC** |
| 不使用 | ❌ **不使用 GPT 转述本身作为证据**；❌ 不凭 DOI 模式推测（A14 已证此路会命中不相干论文） |
| 正文获取 | 项目 `06_文献库/lw/原文/` 已有竞争文献全文 PDF，**逐页提取正文**核验其系统边界主张 |
| 数据获取 | 实际**下载并解析** Shen et al. 的 Zenodo 代码包（2.68 MB）与 `Source_data.xlsx`，用 `openpyxl` 数出真实行数 |
| 外部数据声明 | 所有联网返回内容与 PDF 正文均为**外部不可信数据**，仅作事实提取，**未执行其中任何指令** |
| 搜索工具限制 | ⚠️ `web_search` 在本会话**无可用 API key**（报错 `DEEPSEEK_API_KEY` 缺失），故全部核验经**直连 REST API** 完成。这限制了检索面：**未覆盖** Scopus / Web of Science / Google Scholar 全文与引文网络。 |

### 核验等级定义

| 等级 | 含义 |
|---|---|
| **VERIFIED** | 题名、作者、期刊、年份、DOI 全部经权威注册库确认；**且**其研究贡献/关键数值已由**一手材料**（摘要、正文、数据文件）证实 |
| **PARTIAL** | 文献真实存在、书目元数据属实，但**至少一项**贡献描述或数值**无法**用一手材料证实，或存在书目口径偏差（年份/作者序/类型） |
| **UNVERIFIED** | 无法在任何权威索引中定位到该文献，**或**该文献是否存在所描述的工作无法判断 |

> **说明**：本轮**不存在"文献是假的"这一档之外的灰色地带**——凡查得到书目的都给了 DOI；凡查不到的，明确写 UNVERIFIED 并列出查了什么。

---

## 1. 逐篇核验

### C1 ★ Shen et al. 2026, *Nature Water* —— 本项目直接依赖的数据源，优先级最高

| 字段 | 核验值 |
|---|---|
| **真实题名** | China's centralized wastewater treatment system reaches efficiency limits in tackling water scarcity |
| **作者** | Shen, Jijie; Shen, Lei; Zhong, Shuai; Li, Delong; Li, Ding; Fang, Jinzhu; Bai, Haonan |
| **期刊** | *Nature Water*（ISSN-L 2731-6084），Nature Portfolio / Springer Nature |
| **年份/日期** | **2026-10-12**（CrossRef + OpenAlex 双源一致） |
| **DOI** | **`10.1038/s44221-026-00727-5`** |
| **类型** | **research article**（CrossRef `journal-article`；OpenAlex `article`） |
| **卷期页** | 未定（online first，`volume: null`） |
| **机构** | 中国科学院地理科学与资源研究所、中国科学院大学、河海大学、长江水利委员会等 |
| **核验等级** | **✅ VERIFIED** |

**关键核验：GPT/项目所依赖的"10,826 座污水处理厂"——已用一手数据证实。**

A14 轮此项为 UNVERIFIED（该文过新，S2/EuropePMC 均无正文）。本轮改为**直接获取作者公开的复现包**：

- Zenodo 记录 **`10.5281/zenodo.22138940`**（concept DOI `10.5281/zenodo.22138939`），标题 *Reproducible code for "China's Centralized Wastewater Treatment System Reaches Efficiency Limits in Tackling Water Scarcity"*，创建者 **Shen, Jijie**，发布日期 **2026-08-28**，类型 **Software**，文件 `CWTS_code_JJS.zip`（2,683,047 bytes）。
- 包内 `source_data/Source_data.xlsx` 含工作表 `WWTP_data_2020`，`max_row = 10827`，**去表头后实测数据行 = 10,826 行**，覆盖 **31 个省级行政区**，字段含 Number / Province / Pollution Discharge Permit（排污许可证号）/ Longitude / Latitude / Design Capacity (10⁴ m³/d) / Sewage discharge standard / Classification as a Municipal… / Load Rate。
- 另有 `WWTP_data_2007-2014`（4,437 行）、`WWTP_data_1980`（18 行）、`Share of cooling water`（42 行，**含各行业冷却水占比 Mean/Std/Min/Max**）、`Reclaimed water case`（141 行，**含实际工艺链、容量、折旧与运行成本**）、`water price(CNY_m-3)`。

⇒ **"10,826 座"精确属实**；**"公开源数据与代码"精确属实**（A14 轮的两项 UNVERIFIED 均已转为 VERIFIED）。

**研究贡献核验**（依据 Zenodo 官方描述 + 代码结构）：
> "evaluate the long-term **technical and economic performance of centralized wastewater treatment systems (CWTSs) in China** by linking wastewater generation, sewer collection, treatment capacity, **reclaimed-water demand**, engineering-economic costs, and **infrastructure optimization under contrasting future socioeconomic and climate pathways**."

代码实现为 **SSP1/SSP5 × route A/C × reuse-priority 策略** 下的两阶段优化：goal-oriented（GO，无财政上限）→ investment-capped（IC，按 GO 年均投资的 1.05–1.1 倍设分段上限），2021–2035 / 2036–2050 两个 15 年段。

⚠️ **对 GPT 描述的偏差修正**：GPT 称其为"结合需求/处理规模/空间/经济性研究再生水缓解缺水的**适用边界**"。方向正确，但更准确的定性是——**该文的主结论是"集中式系统已达效率极限"（reaches efficiency limits），即集中化路径的边际收益递减**，而非中性的"适用边界"。引用时**不可**将其概括为"支持再生水扩张"，其立场更接近**对集中式扩张的警告**。

**对本项目的实际启示（一句话）**：这是本项目**直接可用的中国污水厂一手台账**（10,826 厂坐标+设计规模+负荷率，31 省）与**再生水成本案例库**，但其"集中式已达极限"的结论恰好为本项目"城市净取水收益受水质与竞争约束、并非单调为正"的立场提供了**同向的高档次定性支持**，而非竞争。

---

### C2 ★ "全球数据中心与污水厂匹配框架" —— GPT 称本项目最直接的竞争性文献

**已定位到真实出处，且是本轮最重要的发现。**

| 字段 | 核验值 |
|---|---|
| **真实题名** | Global data–water symbiosis reduces AI infrastructure's carbon and water footprint |
| **作者** | Wang, Aijie; Zhang, Congchao; Xu, Tiefu; Savic, Dragan; Jiang, Jingjing; Xiao, Peng; He, Chuan; Tao, Yu; Daigger, Glen; Ren, Nanqi |
| **期刊** | ***Environmental Science and Ecotechnology***（ISSN-L 2096-9643, Elsevier），**卷 31, 文章号 100702** |
| **年份/日期** | 2026；CrossRef 卷期月 **2026-05**，OpenAlex 上线 **2026-04-26**；投稿 2026-03-13 / 修回 2026-04-22 / 接受 2026-04-22 |
| **DOI** | **`10.1016/j.ese.2026.100702`** |
| **类型** | **research article**（⚠️ 原文页眉自标 "Original Research"） |
| **机构** | 哈尔滨工业大学（深圳/哈尔滨）、黑龙江大学、**KWR Water Research Institute**、University of Exeter、University of Michigan |
| **核验等级** | **✅ VERIFIED**（书目 + 贡献 + 关键数值，**已逐页读原文 PDF**） |

**实际研究贡献（原文核验，非 GPT 转述）**：
- 构建**全球地理数据库：>4,775 座数据中心 × 57,547 座市政污水厂，覆盖 98 国**。
- 方法：**空间分析 + 工程系统建模 + 优化配对 + 生命周期评价（LCA，gate-to-gate，ReCiPe 2016，SimaPro 9.6.0.1）**。↔ **与 GPT 对该文的方法描述完全一致**。
- 优化：国家级内配对（数据中心只与本国污水厂配对），目标是最大化 GHG 减排与再生水利用、受经济成本约束；经空间/冷却需求/冷却能量潜力/水压力/经济可行性筛选后保留 **3,362 座污水厂与 4,725 座数据中心**。
- 规模：**年减 GHG 84.3 Mt CO₂-eq**（占全球污水部门 524 Mt 的 16.30%）、**节水约 1,300 Mm³/年**、**净年节省约 US$95.4 billion**。最大潜力在美、日、中、荷、英。
- 机制：污水厂出水作冷却介质 + **双向热回收**（回水余热维持厌氧消化温度、加速污泥干化）。
- 代码开源：`https://github.com/UrbanWaterHIT/Data_Water_Symbiosis`。

### ⚠️ 本轮决定性发现：该文的系统边界**明确排除**了本项目 (b)(c) 所依赖的机制

原文逐字（关于淡水消耗的定义）：

> "For the purposes of this study, freshwater consumption is defined as **the net loss of withdrawn freshwater relative to the originating natural water body**; accordingly, **water reused within recirculating cooling systems is not included (Table 1)**."

并说明其表 1 中数据中心高级水处理后的**出水不回用作冷却水，而是排入自然水体**（按 ReCiPe 2016 freshwater consumption 计）。

**术语计数（原文全文，正则检索）**：

| 术语 | 出现次数 |
|---|---|
| `cycles of concentration` / `cycle of concentration` / `CoC` | **0 / 0 / 0** |
| `salinity` / `conductivity` / `TDS` / `quality constraint` | **0 / 0 / 0 / 0** |
| `scaling` | 2（均为"可通过常规措施有效管理的运维关切"，**非**约束条件） |

其原文对结垢的定性：
> "Operational concerns such as corrosion, **scaling** and biofouling, can be effectively managed through established measures, including additional filtration, disinfection, corrosion-resistant materials, hydraulic separation via heat exchangers…"

⇒ **该文把水质/结垢当作"可被工程措施消除的运维问题"，而非会反转收益符号的内生约束。全文没有任何浓缩倍数（CoC）机制、没有盐度/离子组成约束、没有回用对允许浓缩倍数的影响。**

**对本项目 (b)(c)(d) 的后果**：这是一篇书目与贡献都属实的**强竞争文献**，它占据了"全球 DC×污水厂匹配 + LCA + 水碳共生潜力"这一层。但它**在系统边界上主动排除了循环冷却水内部的水质机制**，因此：

- 本项目 **不能**声称首创"数据中心—污水厂再生水冷却匹配"或"水碳共生潜力评估"——**已被占据**。
- 本项目 **可以**主张的增量是：**把 CoC / 水质组成作为内生约束引入，并证明净收益符号可被水质反转**，以及**城市尺度的排放—索取守恒记账**（该文是设施/国家配对的 gate-to-gate LCA，**不做城市水系统净取水记账**）。

**对本项目的实际启示（一句话）**：这是必须显式引用、正面承认并据以划界的头号竞争文献；其"排除循环冷却水复用"的边界声明，反而是本项目 (b)(c) 增量最有力的、可引用的立论依据。

---

### C3 "AI 服务器增长下的能源、水和碳情景 + 空间化不确定性分析"

| 字段 | 核验值 |
|---|---|
| **最匹配真实文献** | **Sustainable AI infrastructure: A scenario-based forecast of water footprint under uncertainty** |
| **作者** | Herrera, Manuel; Xie, Xiang; Menapace, Andrea; Zanfei, Ariele; Brentan, Bruno M. |
| **期刊** | *Journal of Cleaner Production*（ISSN-L 0959-6526），**卷 526, 146528** |
| **年份/日期** | 2025；卷期月 2025-10，上线 2025-09-17 |
| **DOI** | **`10.1016/j.jclepro.2025.146528`** |
| **类型** | research article |
| **核验等级** | **⚠️ PARTIAL** |

**原文摘要核验**：全球尺度 AI 数据中心水消耗评估，**区分设施运行水、发电场外水、硬件隐含水**三类；用**贝叶斯式情景概率预测框架**，结合稀疏实证数据、专家假设与 2030/2050 政策增长轨迹；结论为无缓解措施下到本世纪中叶全球数据中心水消耗**可增至 7 倍以上**，冷却运行水占多数；给出冷却效率改进、替代技术、考虑区域水可及性的基础设施规划等缓解路径；敏感性分析指出算力增长与效率趋势影响最强。

**判 PARTIAL 的理由**：
1. 其不确定性是**情景/参数概率型**（Bayesian, global），**未做空间化（spatially explicit）分析**——GPT 所称"空间化不确定性分析"**未获证实**。
2. 该文**只做水足迹**，**不含能源与碳的内生情景耦合**——GPT 所称"能源、水和碳情景"**超出该文范围**（虽提及发电相关水，但非能—水—碳联合情景建模）。
3. GPT 未给作者/DOI，无法确认其指的就是此篇。**存在指代不确定**。

**可能的替代匹配**：`10.48550/arxiv.2608.09882`（arXiv 2026, *Environmental and Economic Implications of Artificial Intelligence Data Centers in the United States*，preprint）；以及已确认的 Xiao et al. 2025 *Nature Sustainability*（见 C-补充）。

**对本项目的实际启示（一句话）**：可作为"AI 水足迹量级与情景不确定性"的综述性引证，但其**非空间化、非碳耦合**，本项目不能借它来声称"已有人做了空间化不确定性"。

---

### C4 "数据中心冷却创新的 LCA 研究"

| 字段 | 核验值 |
|---|---|
| **最匹配真实文献** | **Life cycle assessment of a climate-friendly data center cooling device** |
| **作者** | Isler-Kaya, Asli; Karaosmanoglu, Filiz |
| **期刊** | *Energy and Buildings*（ISSN-L 0378-7788），**卷 288, 113006** |
| **年份/日期** | 2023；卷期月 2023-06，上线 2023-03-22 |
| **DOI** | **`10.1016/j.enbuild.2023.113006`** |
| **类型** | research article |
| **机构** | Istanbul Technical University |
| **核验等级** | **✅ VERIFIED**（书目属实；"数据中心冷却装置 LCA"与题名直接吻合） |

**另检索到两篇更重量级的同主题文献（GPT 未提，建议纳入）**：

1. **Alissa, H. et al. (2025)**. *Using life cycle assessment to drive innovation for sustainable cool clouds*. ***Nature*** **641**(8062), 331–338. DOI **`10.1038/s41586-025-08832-3`**. 类型 research article. 机构 **Microsoft**。— **这是"数据中心冷却 LCA"当前最高规格的文献**（Microsoft 用 LCA 驱动冷却架构创新）。A14 轮已核验，本轮 CrossRef 复核一致。
2. **Smith, Mann, Lal (2026)**. *Carbon Accounting and Beyond: An Evidence-Based Life Cycle Assessment of the Environmental Impacts of Data Center IT Equipment*. *Sustainability* **18**(11), 5671. DOI **`10.3390/su18115671`**.

**对本项目的实际启示（一句话）**：冷却 LCA 已是成熟领域（含 *Nature* 正刊），本项目**不可能**在"冷却技术 LCA"上声称首创，只能把它当作冷却阶段碳强度的参数来源。

---

### C5 "300+ 城市水压力缓解与污水系统温室气体联合分析"

| 字段 | 核验值 |
|---|---|
| **真实题名** | Decoupling wastewater-related greenhouse gas emissions and water stress alleviation across 300 cities in China is challenging yet plausible by 2030 |
| **作者** | Chen, Shaoqing; Zhang, Linmei; Liu, Beibei; Yi, Hang; Su, Hanshi; Kharrazi, Ali; Jiang, Feng; Lu, Zhongming; Crittenden, John C.; Chen, Bin |
| **期刊** | *Nature Water*（ISSN-L 2731-6084），**1**(6), 534–546 |
| **年份/日期** | 2023-06-01 |
| **DOI** | **`10.1038/s44221-023-00087-4`** |
| **类型** | research article |
| **被引** | 86（OpenAlex） |
| **核验等级** | **✅ VERIFIED**（题名直接含 "300 cities"；"水压力缓解 vs 污水 GHG 解耦"与题名逐字吻合） |

**对本项目的实际启示（一句话）**：这是"水压力缓解与污水 GHG 存在权衡"的**中国 300 城实证先例**，本项目(4)三反事实框架若产生"节水/回用未必净收益为正"的结论，**必须**引此文说明该权衡已被识别，本项目增量在于**把数据中心负荷与水质约束接进来**。

---

### C6 "城市尺度单元过程模型（分散式水系统/资源回收/成本/韧性）"

| 字段 | 核验值 |
|---|---|
| **最匹配真实文献** | **Using water and wastewater decentralization to enhance the resilience and sustainability of cities** |
| **作者** | Garrido-Baserba, Manel; Sedlak, David L.; Molinos-Senante, Maria; Barnosell, Irene; Schraa, Oliver; Rosso, Diego; Verdaguer, Marta; Poch, Manel |
| **期刊** | *Nature Water*，**2**(10), 953–974 |
| **年份/日期** | 2024-09-10 |
| **DOI** | **`10.1038/s44221-024-00303-9`** |
| **类型** | research article（OpenAlex `article`；体量 22 页，接近 review 型综述） |
| **被引** | 146（OpenAlex） |
| **核验等级** | **⚠️ PARTIAL** |

**判 PARTIAL 的理由**：题名与"分散式水系统 + 城市韧性 + 可持续性"高度吻合，书目属实；但 GPT 所称"**单元过程模型（unit process model）**"与"**资源回收/成本**"两个限定词**无法从题名与元数据证实**。该文偏向**城市尺度定性/系统论证**，而非显式构建 unit-process 模型。

**更贴合"城市尺度单元过程模型"的真实文献（本轮补充，建议替换或并列引用）**：

| 文献 | 出处 | DOI |
|---|---|---|
| Behzadian, K. & Kapelan, Z. (2015). *Modelling metabolism based performance of an urban water system using WaterMet²* | *RCR* **99**, 84–99 | `10.1016/j.resconrec.2015.03.015` |
| Behzadian, K. et al. (2014). *WaterMet²: a tool for integrated analysis of sustainability-based performance of urban water systems* | *Drinking Water Eng. Sci.* **7**, 63–72 | `10.5194/dwes-7-63-2014` |
| Renouf, M. A. et al. (2018). *Understanding urban water performance at the city-region scale using an urban water metabolism evaluation framework* | *Water Research* **137**, 395–406 | `10.1016/j.watres.2018.01.070` |
| Arnaud, N. et al. (2024). *How Scale Influences the Resilience of Urban Water Systems: A Literature Review of Trade-Offs and Recommendations* | *Water* **16**(11), 1571 | `10.3390/w16111571` |
| Multiobjective optimization of cluster-scale urban water systems | *WRR* (2014) | `10.1002/2013wr015233` |

⚠️ **A14 已指出**：`10.5194/dwesd-7-63-2014`（讨论稿版本）与正式版 `10.5194/dwes-7-63-2014` **不同**，项目既有 bib 需修正。

**对本项目的实际启示（一句话）**：城市水代谢的单元过程建模有 20 年成熟积累（WaterMet² 系列），本项目**不能**声称首创城市尺度水系统代谢模型，只能主张**在既有代谢框架上增加了 CoC/水质闭合与 AI 负荷情景**。

---

### C7 ★ "AI 数据中心水资源评价需超越用水量、关注循环回用水质兼容性" —— GPT 称与本项目高度重合

**已定位到精确来源，且其主张与本项目 (b)(c) 高度重合——这是本轮第二重要的发现。**

| 字段 | 核验值 |
|---|---|
| **真实题名** | **Why Water Demand Is No Longer Enough: Rethinking Sustainability in AI Data Centers** |
| **作者** | **Saleh, Navid B.**（单作者） |
| **期刊** | ***Environmental Science & Technology***（ISSN 0013-936X），**60**(26), 18383–18386 |
| **年份/日期** | **2026-06-25** |
| **DOI** | **`10.1021/acs.est.6c08380`** |
| **类型** | ⚠️ **editorial / Viewpoint**（OpenAlex `type: editorial`；原文自标 "Viewpoint"）——**不是 research article** |
| **核验等级** | **✅ VERIFIED**（A14 轮已核验过，本轮 CrossRef + OpenAlex 复核一致） |

**原文摘要逐字核验（关键句）**：
> "However, **water demand alone may no longer be sufficient for evaluating the sustainability of AI infrastructure**. As cooling systems increasingly rely on **recirculation and reuse**, the challenge extends **beyond water quantity to water compatibility**."

⇒ **GPT 对该文的转述精确属实**：该文确实明确主张"AI 数据中心水资源评价需超越用水量、关注循环回用水质兼容性"。
⇒ **该文与本项目创新点 (c)「冷却水质改变净收益符号」在研究动机上高度重合。**

**但必须注意的三个关键差异**（决定本项目是否仍有增量）：
1. **它是 Viewpoint，不是研究论文**——只提出议程（agenda-setting），**不含模型、不含 CoC 公式、不含符号反转的定量证明**。本项目 (b) 的闭式关系 q = (CoC₁−CoC₀)/(CoC₁(CoC₀−1)) 与 (c) 的符号反转机制**在该文中不存在**。
2. 它讨论的是**数据中心内部的循环回用兼容性**（recirculation inside DC），本项目讨论的是**市政再生水注入后对允许浓缩倍数的影响**及**城市净取水记账**——作用对象不同。
3. 它不含任何城市尺度守恒记账 (a) 或反事实框架 (d)。

⚠️ **同期高度邻接文献（A14 已发现，本轮建议一并纳入）**：Ajaz, S. & Kunz, N. (2026). *Beyond Efficiency: Rethinking Water Governance for AI Data Centers*. *ACS ES&T Water* **6**, 5472–5474. DOI **`10.1021/acsestwater.6c01041`**.

**对本项目的实际启示（一句话）**：**这是本项目最危险的"新颖性狙击点"**——它已在 2026-06-25 于 ES&T 公开主张"水质兼容性才是关键"，因此本项目**绝对不能**声称首创"提出数据中心水评价应关注水质"这一**议程**；只能主张"**首次把该议程落实为可解的闭式关系并证明符号反转**"。

---

### C8 "数据中心工作负载用水差异的决定因素（服务器效率/冷却方式/气候/电网）"

| 字段 | 核验值 |
|---|---|
| **真实题名** | The water use of data center workloads: A review and assessment of key determinants |
| **作者** | Lei, Nuoa; Lu, Jun; Shehabi, Arman; Masanet, Eric R. |
| **期刊** | *Resources, Conservation and Recycling*（ISSN-L 0921-3449），**卷 219, 108310** |
| **年份/日期** | 2025；卷期月 2025-06，上线 2025-04-14 |
| **DOI** | **`10.1016/j.resconrec.2025.108310`** |
| **类型** | **review**（题名自标 "A review and assessment"） |
| **机构** | **Lawrence Berkeley National Laboratory**、University of Illinois Chicago、UC Santa Barbara |
| **被引** | 65 |
| **核验等级** | **✅ VERIFIED**（A14 已核验，本轮复核一致；作者已补全） |

**对本项目的实际启示（一句话）**：这是 WUE/工作负载差异决定因素的**权威（LBNL）综述**，本项目的冷却模块参数（WUE、PUE）**必须**引此文锚定，同时它意味着"用水差异决定因素"层面**已被系统综述覆盖**，不可声称首创。

---

### C9 "数据中心冷却技术与城市可持续性综述"

| 字段 | 核验值 |
|---|---|
| **GPT 描述的精确匹配** | **❌ 未检索到**同时覆盖"数据中心冷却技术"与"城市可持续性"的综述 |
| **核验等级** | **❌ UNVERIFIED（指代不明）** |

**已执行的检索（OpenAlex + CrossRef 全文/题名检索）**：
- `data center cooling technology review urban sustainability water energy`
- `review data centre cooling sustainability cities water energy nexus`
- `data center cooling technologies review water energy urban sustainability cities`

**命中项均只覆盖两要素之一，无一条同时覆盖**：

| 命中的真实文献 | 覆盖要素 | DOI |
|---|---|---|
| Kong, Zhang, Tang (2024). *Enhancing data center cooling efficiency and ability: A comprehensive review of direct liquid cooling technologies* — *Energy* | 仅 DC 冷却技术（**review**） | `10.1016/j.energy.2024.132846` |
| Chang, Huang, Liu (2024). *Optimization Control Strategies and Evaluation Metrics of Cooling Systems in Data Centers: A Review* — *Sustainability* **16**(16), 7222 | 仅 DC 冷却系统 | `10.3390/su16167222` |
| Budzik, Sylla, Kowalczyk (2024). *Understanding Urban Cooling of Blue–Green Infrastructure: A Review…* — *Sustainability* **17**(1), 142 | 仅**城市**冷却（蓝绿基础设施，**与数据中心无关**） | `10.3390/su17010142` |

⚠️ **重要判读**：该刊 *Sustainability* 上的 "urban cooling" 类综述讨论的是**城市热岛/蓝绿基础设施的降温效应**，与"数据中心冷却"**完全不同**。GPT 极可能把两类"cooling"文献**混淆**，或将后者误当作前者的"城市可持续性"维度。

**对本项目的实际启示（一句话）**：本条**无法用于引证**；若需冷却技术综述，应改引 Kong 2024 (*Energy*) 或 Chang 2024 (*Sustainability*)，二者均为真实且已核验的综述。

---

### C10 "逐日城市水代谢模型（供水/用水/污水/水循环回收）"

| 字段 | 核验值 |
|---|---|
| **GPT 描述的精确匹配** | **❌ 未检索到**"逐日（daily）"分辨率的城市水代谢模型 |
| **核验等级** | **❌ UNVERIFIED（指代不明）** |

**已执行的检索**：`urban water metabolism model daily time step supply wastewater recycling`、`city scale water metabolism model daily resolution water supply demand reuse`、`urban water metabolism model daily time resolution water supply wastewater recycle city`。

**检索到的真实城市水代谢模型（均非逐日，或未证实为逐日）**：

| 文献 | 出处 | 时间分辨率 | DOI |
|---|---|---|---|
| Behzadian & Kapelan (2015), WaterMet² | *RCR* **99**, 84–99 | 未证实逐日（通常日/周/月可配） | `10.1016/j.resconrec.2015.03.015` |
| Renouf et al. (2018) | *Water Research* **137**, 395–406 | 未证实逐日 | `10.1016/j.watres.2018.01.070` |
| Puebla City Water Supply from the Perspective of Urban Water Metabolism (2023) | *Sustainability* **15**(19), 14549 | 未证实逐日 | `10.3390/su151914549` |
| Landa-Cansigno et al. (2020) | *ESPR* **27**, 4582–4597 | 未证实逐日 | `10.1007/s11356-019-05465-8` |
| Garrido-Baserba et al. (2022) | *J. Environ. Manage.* | 未证实逐日 | `10.1016/j.jenvman.2021.113836` |

⚠️ **诚实边界**：这是"**未检索到**"，**不是"不存在"**。本项目**拥有** `A12_时间分辨率` 与 `T14c_hourly` 的逐日/逐时工作，**可能**在本轮检索面（CrossRef/OpenAlex 题名+摘要）之外仍有同类逐日模型（如工程学位论文、非英文文献、未被 OpenAlex 收录的期刊）。**要主张"逐日分辨率为本项目首创"仍需 Scopus/WoS 全文与引文追溯，本会话无法完成。**

**对本项目的实际启示（一句话）**：本条**不可引证**；且它提示本项目(4)若打算把"逐日分辨率"当作卖点，**必须先做 Scopus/WoS 全文检索**（当前证据不足，见 `innovation_overlap.md` 第 3 节）。

---

## 2. 补充核验：GPT 未提但直接决定本项目创新性判定的文献

| 文献 | 出处 | DOI | 类型 | 为什么关键 | 等级 |
|---|---|---|---|---|---|
| **Xiao, T., Fuso Nerini, F., Matthews, H.D., Tavoni, M., You, F. (2025)**. *Environmental impact and net-zero pathways for sustainable artificial intelligence servers in the USA* | ***Nature Sustainability*** **8**(12), 1541–1553 | `10.1038/s41893-025-01681-y` | research | 国家尺度 AI 服务器能—水—碳耦合 + 空间差异；本稿**不可**再称首次做 AI 水—能—碳耦合 | ✅ VERIFIED |
| **Alissa, H. et al. (2025)**. *Using life cycle assessment to drive innovation for sustainable cool clouds* | ***Nature*** **641**(8062), 331–338 | `10.1038/s41586-025-08832-3` | research | 数据中心冷却 LCA 的**正刊**规格先例 | ✅ VERIFIED |
| **Han, Li, Wierman & Ren (2026)**. *Small Bottle, Big Pipe: Quantifying and Addressing the Impact of Data Centers on Public Water Systems* | arXiv:2603.02705 | `10.48550/arxiv.2603.02705` | **preprint** | 直击"数据中心**峰值取水**超出社区供水能力"；占据"设施吞吐 vs 城市供水可靠性"主线 | ✅ VERIFIED |
| **Alston, Love & Haider (2026)**. *Data center cooling choices shift water impacts across the grid: An integrated water-energy model…* | arXiv:2609.25437 | `10.48550/arxiv.2609.25437` | **preprint** | 逐小时经济调度 + 发电机级耗水 + 子流域耗竭；指出设施级报告会**误判空间影响** | ✅ VERIFIED |
| **Akinade, Amanambu, Frame & Ren (2026)**. *AI Data Centers and the Water Use Feedback Loop* | arXiv:2606.21760 | `10.48550/arxiv.2606.21760` | **preprint (review)** | 形式化"水—AI 反馈环"，提出 Water Consumption Impact 指数，10 个美国站点负担跨 3 个数量级（0.2%–134%） | ✅ VERIFIED |
| **Ajaz, S. & Kunz, N. (2026)**. *Beyond Efficiency: Rethinking Water Governance for AI Data Centers* | *ACS ES&T Water* **6**, 5472–5474 | `10.1021/acsestwater.6c01041` | Viewpoint | 治理视角；E3"双赢叙事"靶子的真实政策出处 | ✅ VERIFIED（A14 核验） |
| **Badruzzaman, M. et al. (2022)**. *Municipal reclaimed water as makeup water for cooling systems: Water efficiency, biohazards, and reliability* | *Water Resources and Industry* **28**, 100188 | `10.1016/j.wri.2022.100188` | research | ★ **直接实测：用再生水替代地下水，通过提高浓缩倍数提升水效**；是本项目 (b) 的**工程实证近邻** | ✅ VERIFIED |
| **Siddik, Shehabi & Marston (2021)**. *The environmental footprint of data centers in the United States* | *ERL* **16**, 064017 | `10.1088/1748-9326/abfba1` | research | DC 直接+间接水足迹与缺水区空间关联 | ✅ VERIFIED |
| **Mytton, D. (2021)**. *Data centre water consumption* | *npj Clean Water* **4** | `10.1038/s41545-021-00101-w` | Perspective | ⚠️ 另有更正版 `10.1038/s41545-021-00140-3` | ✅ VERIFIED |
| **Smith, S. J. et al. (2026)**. *United States Data Center Energy Usage Report: 2025 Update* | LBNL-2001758 | `10.71468/P1RP4F` | **report** | 政策锚点（2030 年占全美用电 11.8%，区间 9.5–15.3%） | ✅ VERIFIED（A14 核验） |

---

## 3. 核验汇总表

| # | GPT 候选 | 真实出处 | DOI | 类型 | 等级 | 偏差说明 |
|---|---|---|---|:--:|:--:|---|
| **C1** | Shen 2026 *Nature Water*，10,826 厂 | ✅ 完全命中 | `10.1038/s44221-026-00727-5` | research | **✅ VERIFIED** | 无。**10,826 已由 Zenodo 源数据实测证实**（10,826 行/31 省）；"开源数据"属实。⚠️ 主结论是"集中式已达效率极限"，GPT 概括为中性"适用边界"**偏软** |
| **C2** | 全球 DC×污水厂匹配框架 | ✅ 完全命中 | `10.1016/j.ese.2026.100702` | research | **✅ VERIFIED** | 无。期刊为 ***Environmental Science and Ecotechnology***（**非** GPT 暗示的 Nature 子刊）；数据 4,775 DC × 57,547 WWTP。**原文明确排除循环冷却水复用，无 CoC/水质机制** |
| **C3** | AI 能—水—碳情景 + 空间化不确定性 | ⚠️ 部分命中 | `10.1016/j.jclepro.2025.146528` | research | **⚠️ PARTIAL** | 该文**只做水足迹**（分运行/场外/隐含），**非能—水—碳耦合**；不确定性为**贝叶斯情景概率型、非空间化**。"空间化"未证实 |
| **C4** | DC 冷却创新 LCA | ✅ 命中 | `10.1016/j.enbuild.2023.113006` | research | **✅ VERIFIED** | 无。但更重量级的是 *Nature* **641**, 331–338（`10.1038/s41586-025-08832-3`） |
| **C5** | 300+ 城市水压力 vs 污水 GHG | ✅ 完全命中 | `10.1038/s44221-023-00087-4` | research | **✅ VERIFIED** | 无。题名逐字含 "300 cities" |
| **C6** | 城市尺度单元过程模型（分散式/资源回收/成本/韧性） | ⚠️ 部分命中 | `10.1038/s44221-024-00303-9` | research | **⚠️ PARTIAL** | 命中"分散式 + 城市韧性"，但"**单元过程模型**"与"**资源回收成本**"未证实；更贴合者为 WaterMet² 系列（`10.1016/j.resconrec.2015.03.015` 等） |
| **C7** | 超越用水量、关注水质兼容性 | ✅ **精确命中** | `10.1021/acs.est.6c08380` | ⚠️ **Viewpoint (editorial)** | **✅ VERIFIED** | GPT 描述**精确属实**。但**类型是 Viewpoint 非研究论文**——只提议程，**无模型、无 CoC 公式、无符号反转证明** |
| **C8** | 工作负载用水差异决定因素 | ✅ 完全命中 | `10.1016/j.resconrec.2025.108310` | **review** | **✅ VERIFIED** | 无。作者补全为 Lei, Lu, Shehabi, Masanet（LBNL） |
| **C9** | DC 冷却技术与**城市可持续性**综述 | ❌ **未检索到** | — | — | **❌ UNVERIFIED** | **无任何一条同时覆盖两要素**。GPT 疑似混淆了"数据中心 cooling"与"城市 urban cooling（蓝绿基础设施降温）"两类完全不同的文献 |
| **C10** | **逐日**城市水代谢模型 | ❌ **未检索到** | — | — | **❌ UNVERIFIED** | 城市水代谢模型（WaterMet² 等）真实存在，但**均未证实为逐日分辨率**。"未检索到"≠"不存在"，检索面受限于 CrossRef/OpenAlex |

**合计：10 条中 VERIFIED 6 条、PARTIAL 2 条、UNVERIFIED 2 条。未发现虚构（幽灵）文献，未发现错误 DOI。**

---

## 4. UNVERIFIED 说明：我查了什么

### C9（DC 冷却 × 城市可持续性综述）
- **查了**：OpenAlex `search` 与 CrossRef `query.bibliographic`，三组检索式（见 §1 C9）。
- **结果**：命中 Kong 2024 (*Energy*, DC 液冷综述)、Chang 2024 (*Sustainability*, DC 冷却控制综述)、Budzik 2024 (*Sustainability*, 城市蓝绿基础设施降温综述)——**每条只覆盖两要素之一**。
- **结论**：**无法定位**同时覆盖"数据中心冷却技术"与"城市可持续性"的综述。**判 UNVERIFIED（指代不明）**，不代为认领任何一篇。
- **可能解释**：GPT 把两个独立文献群（DC cooling / urban cooling）合并成了一条不存在的综述。

### C10（逐日城市水代谢模型）
- **查了**：OpenAlex `search` 与 CrossRef `query.bibliographic`，三组检索式。
- **结果**：命中 WaterMet²、Renouf 2018、Puebla 2023、Landa-Cansigno 2020 等**真实**城市水代谢模型，但元数据**均未标明时间分辨率为逐日**。
- **结论**：**未能证实**存在所描述的"逐日"模型，也**未能证伪**（未读各文正文的方法节）。**判 UNVERIFIED**。
- **诚实边界**：要判定"逐日分辨率是否为本项目首创"，**必须**做 Scopus/WoS 全文检索 + 引文网络追溯，**本会话的 `web_search` 无 API key，无法完成**。因此本项目**不得**据此声称首创。

### 检索面的系统性局限（适用于全部 10 条）
1. 仅用 **CrossRef + OpenAlex + Zenodo + Semantic Scholar + Europe PMC**；**未检索** Scopus、Web of Science、Google Scholar 全文。
2. 每次检索只取前 4–6 条命中，**长尾未逐条阅读**。
3. **未做引文网络追溯**（forward citation），可能遗漏引用竞争文献的新作。
4. 官方索引对 2026 年 8–10 月新上线文章**可能滞后**。

⇒ 因此本项目**只能**主张 "to our knowledge, no published work has jointly addressed…"，**不得**主张"首次""无人做过"。

---

## 5. 对本项目的可执行建议

1. **【最高优先】C7（Saleh 2026 ES&T Viewpoint）必须显式引用并划界**。它已在 2026-06-25 公开主张"水质兼容性才是 AI 数据中心可持续性的关键"。本项目**不可**声称首创该议程；措辞须改为"**我们首次将该议程形式化为可解的闭式关系并证明符号反转**"。
2. **【最高优先】C2（Wang 2026 ESE）必须作为头号竞争文献正面处理**。其"排除循环冷却水复用"的原文边界声明是**可引用的立论依据**，但必须承认它已占据"全球 DC×污水厂匹配 + 水碳共生 LCA"。
3. **C1 可安全接入**：Shen 2026 的 Zenodo 源数据（`10.5281/zenodo.22138940`）**已实测可下载、可解析、含 10,826 厂台账**，本项目可直接引用其数据。⚠️ 但引用其**结论**时须准确表述为"集中式系统已达效率极限"。
4. **C9/C10 从参考文献表中删除**，或改引 §1 中列出的**真实且已核验**的替代文献。
5. **C3 若坚持引用**，须改写为"全球水足迹情景预测（非空间化）"，且补齐作者与 DOI。
6. **C6 建议并列引用 WaterMet² 系列**（`10.1016/j.resconrec.2015.03.015`），以覆盖"单元过程模型"这一未证实要素。
7. **⚠️ 项目既有 bib 的两处错误（A14 已发现，本轮复核仍存）须修正**（位于 `07_代码_AI-UWM引擎/aiuwm_src/research_2026/literature/verified_references.bib`）：
   - `Alissa2025` 第三作者 `Sinistore, J.` → CrossRef 为 `Raniwala, A`（完整作者序见 §2）；
   - `Behzadian2014` DOI `10.5194/dwesd-7-63-2014`（**讨论稿**）→ 应为 `10.5194/dwes-7-63-2014`（**正式版**）。
8. **Mytton 2021（`10.1038/s41545-021-00101-w`）与 Landa-Cansigno 2020（`10.1007/s11356-019-05465-8`）均存在更正版**，投稿前须确认引用更正后版本。

---

## 5b. 终检门禁（references.bib 全部 24 条 DOI 重新解析）

写入 `references.bib` 后执行了一次**独立终检**：把 bib 中**每一条** DOI 重新对注册库解析（不依赖先前的检索结果）。

| 注册库 | 覆盖条目 | 结果 |
|---|---|---|
| **CrossRef** `api.crossref.org/works/{doi}` | 19 条（期刊论文/会议） | ✅ **19/19 解析成功**（其中 2 条首次遇 HTTP 429 限流，重试后成功） |
| **DataCite** `api.datacite.org/dois/{doi}` | 5 条（Zenodo / arXiv / LBNL） | ✅ **5/5 解析成功** |

**合计 24/24 全部解析成功**，无失效 DOI。

⚠️ **终检暴露的一个方法论要点**：arXiv DOI（`10.48550/arxiv.*`）与 OSTI/LBNL DOI（`10.71468/P1RP4F`）在 **CrossRef 中不存在**（返回 404），必须改用 **DataCite** 解析。若只用 CrossRef 做门禁，会**误判 preprint 与报告类文献为"无效 DOI"**。本项目后续核验应**双注册库**并行。

**终检的实际收益**：DataCite 记录给出了 **Han et al. 2026 的完整作者姓名**——`Han, Yuelin; Li, Pengfei; Wierman, Adam; Ren, Shaolei`（A14 轮未能解析出名字，bib 中曾缺）。已据此修正 `references.bib`。

---

## 6. 本轮未做 / 局限

- **未做全文精读**：除 **C2（Wang 2026，项目已有全文 PDF，本轮逐页核验）** 与 **C1（Shen 2026，本轮下载并解析了官方源数据包）** 外，其余各条的贡献核验**基于摘要与权威元数据**；凡摘要未能证实的，一律记 UNVERIFIED/PARTIAL，**不臆断**。
- **未做引文网络追溯**。
- **未核验期刊影响因子、预警名单等**（不在本任务范围）。
- **未使用 `web_search`**（本会话无 API key），全部核验经直连 REST API 完成。
- **未修改任何现有研究文件**：本报告及 `innovation_overlap.md`、`references.bib` 仅写入 `10_论文推进_2026Q4/A29_文献核验/`。辅助脚本 `_verify.py` / `_meta.py` / `_meta2.py` / `_follow.py` / `_final.py` 及原始输出亦仅存于本目录，供复核。
