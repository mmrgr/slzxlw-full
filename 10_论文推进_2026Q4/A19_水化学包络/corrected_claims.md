# A19 修正后的表述与禁用措辞清单

**日期**：2026-10-14
**依据**：`chemistry_audit.md`、`db_sensitivity.md`、`T19*` 脚本输出
**纪律**：本文件只做**表述修正**，不修改任何既有报告文件（A4/A13/A15/A16/07 均未改动）。

---

## 第一部分：禁止使用的原措辞清单

以下措辞**不得再出现在论文、补充材料、答辩稿或任何对外文本中**。
每条给出：原文位置 → 为何禁止 → 替换为。

### ❌ 禁用 #1

> "工程比值判据**系统性高估约 40%**"
> "the engineering ratio screens **over-estimate it by ~40%**"
> "比值法**系统性高估**可用浓缩倍数（4.97 vs 2.52，约 2.0×）"

**出现位置**：
- `10_论文推进_2026Q4/10_论文主稿_v1.md` L39–40, L65–66, L126, L182–183, L396
- `10_论文推进_2026Q4/02_阶段结果_T0-T7.md` L7–8, L110
- `10_论文推进_2026Q4/06_审计修复_v1.md` L155, L159–160, L216
- `10_论文推进_2026Q4/08_阶段结果_T5-T14.md` L284
- `10_论文推进_2026Q4/11_红队自审_T17.md` L94–95, L224, L231
- `10_论文推进_2026Q4/A16_英文稿/supplementary_information.md` L143–144
- `10_论文推进_2026Q4/01_后续任务详细规划_v2.md` L262
- `10_论文推进_2026Q4/A0_预注册/preregistration_amendment_3.md` L88

**为何禁止**：
1. 该 40%（实为 +41.7%）**只在未引用的引擎占位限值下成立**；
2. 换成带引用的 GB/T 50050-2017 后，比值法 2.500 vs 饱和指数 2.5202，**差 0.8%**；
3. 换成 GB/T 19923-2024 严格档后**符号反转**（比值法更保守 −50.4%）；
4. 它把**限值取值问题**误述为**判据方法论的系统性偏差**；
5. "系统性"一词要求跨样本、跨情景成立——而**只有 n = 1 个样本**（IEUA）满足完整离子面板。

**数值溯源（必须同时说明）**：
- 3.57 = 引擎占位限值 {TDS 2200, Cl 500, hardness 700, alkalinity 500, silica 150}，**无引用**
- 2.52 = PHREEQC/`vitens.dat`，相集 {Calcite, Dolomite, Gypsum, Anhydrite, SiO₂(a)}，25 °C

### ❌ 禁用 #2

> "方解石饱和约束使 CoC 从 3.57 降到 2.52"（不加限定的裸陈述）

**为何禁止**：3.57 与 2.52 **不是同一限值口径下的两个判据**。
3.57 来自**无引用的假设限值**，2.52 来自**热力学平衡**。
把两者并列会造成"我们改进了判据"的错觉，实为"我们改了限值表"。

### ❌ 禁用 #3

> "**水质硬约束 = 方解石饱和 → CoC 2.52**"（把方解石饱和当作普遍硬上限）

**为何禁止**（GPT 意见2 §问题4 的核心，本轮已证实）：
1. **Puckorius & Brooke 1991** 明确证明 LSI/RSI 在 pH > 7.5 的浓缩冷却水中**不准确、不适用**；
2. 饱和指数是**结垢风险指标**，不是所有冷却塔都必须遵循的 CoC 上限；
3. 真实冷却塔普遍投加阻垢剂，**GSA 实机观测到 4.34 / 4.91**；
4. 加药后限制相**从方解石切换到无定形二氧化硅**（本审计实测 CoC 4.81 处 SiO₂(a) 饱和）；
5. 上限还依赖温度、pH、离子活度、材料、停留时间与操作制度。

### ❌ 禁用 #4

> "χ = 0.25 是代表性严苛情景"

**为何禁止**：IA-UWM 自审报告（`18_方法自审与修复报告` L163）已自行标注
"$\chi=0.25$ 比任何实测更严，属**外推压力档**"。
在 IEUA 上 χ_eff 的下界实测为 **0.504**（2.52/5），加药后上界约 **0.98**（4.91/5）。
**0.25 无任何实测支撑**，只能作**外推压力测试**，不得称"代表性"。

### ❌ 禁用 #5

> "`vitens.dat` 是**饮用水库**"（或用它论证"结论局限于饮用水情景"）

**为何禁止**：核实库头后，`vitens.dat` **不是**饮用水标准库。
它是 PHREEQC 官方 `phreeqc.dat`（2015-01-27 版）的派生版（原名 `stimela.dat`），
由代尔夫特理工大学 Stimela 平台为**水与污水处理建模**维护。
声称它是"饮用水库"是**事实错误**，会误导审稿人对适用边界的判断。

### ❌ 禁用 #6

> "阻垢剂可把 LSI 维持到 2–3，因此 CoC 可达 12"（作为结论陈述）

**为何禁止**：该数字来自**厂商会议论文**（Calgon；Sherwood 1994 / Cognetti 1996），
非独立第三方验证；且"LSI 2–3"与"300× 方解石饱和度"是同一事实的两种表述
（LSI = log₁₀(300) = 2.477），**不是两个独立证据**。
只能作为"技术上界"提及，且必须标注来源性质。

### ❌ 禁用 #7

> 把 `AI-UWM model assumption`（TDS 650 / Cl 130）与实测水源放在同一分布中做统计

**为何禁止**：这与"把模型假设与公开观测混为一类"同源，是本轮审计已发现的缺陷。
引擎自身在 `ai_data_center_database.json` 中明确标注
`"type": "assumption"`、`"site-specific design placeholder"`。

### ❌ 禁用 #8

> "Figshare RW/BW 缺失 SO₄ 与碱度"（作为"源数据缺失"陈述）

**为何禁止**：这两项**在源表中存在**（SO₄²⁻ 5.28 / 1.14 mmol·L⁻¹；
HCO₃⁻ 4.56 / 2.28 mmol·L⁻¹），是**项目提取脚本的表头匹配 bug** 导致丢失，
下游却报告为"观测缺失"。这是**把提取失败误报为数据缺失**。
正确说法见 §第二部分 #8。

---

## 第二部分：修正后的准确表述

### ✅ 修正 #1 —— 允许 CoC 的包络（核心替换）

**旧**：
> 方解石饱和约束使 CoC 从 3.57 降到 2.52，说明工程比值判据系统性高估约 40%。

**新（中文）**：
> 允许浓缩倍数 CoC 应表述为**区间**而非单值。对 IEUA 三级再生水，
> **无加药的热力学下界**为 **CoC ≈ 2.52**（25 °C，方解石 SI ≤ 0，PHREEQC/`vitens.dat`）；
> 考虑冷却塔循环水实际温度 35–45 °C，该下界降至 **2.10–1.77**。
> **加药运行的上界**由 GSA/NREL 在 Lloyd D. George 法院（Las Vegas）的实机观测给出，
> 为 **CoC = 4.34–4.91**（投加阻垢剂并运行 15–57 天）。
> 值得注意的是，加药后**限制相并非方解石而是无定形二氧化硅**：
> 即使把方解石饱和度容忍度提高到 300 倍，IEUA 的 CoC 仍被 SiO₂(a) 饱和限制在 **4.81**，
> 与实机观测的上界一致。
> 因此本研究采用 **CoC ∈ [2.1, 4.9]** 作为包络，
> 并将"方解石饱和"定位为**无加药情景下的热力学下界**，
> 而非所有冷却塔的普遍上限。

**新（English）**：
> The admissible cycles of concentration should be stated as an **envelope, not a point value**.
> For IEUA tertiary reclaimed water the **un-inhibited thermodynamic lower bound** is
> **CoC ≈ 2.52** (25 °C, calcite SI ≤ 0, PHREEQC/`vitens.dat`); at realistic circulating-water
> temperatures of 35–45 °C this falls to **2.10–1.77**. The **inhibited operating upper bound**
> comes from metered field observations at the Lloyd D. George U.S. Courthouse (Las Vegas,
> GSA/NREL): **CoC = 4.34–4.91** with antiscalant dosing. Notably, once calcite is inhibited the
> **limiting phase is amorphous silica, not calcite**: even at a 300-fold calcite saturation
> tolerance, IEUA remains capped at **CoC = 4.81** by SiO₂(a) saturation, consistent with the
> field upper bound. We therefore adopt **CoC ∈ [2.1, 4.9]** as the envelope and treat calcite
> saturation as the *un-inhibited thermodynamic lower bound* rather than a universal ceiling.

### ✅ 修正 #2 —— 判据差异的正确表述（替换"40%"）

**旧**：
> 判据由"组分比值"改为"PHREEQC 饱和"使允许浓缩倍数从 3.57 降至 2.52，
> 说明工程比值判据系统性高估约 40%。

**新**：
> 比值法与饱和指数法给出的允许 CoC 差异**取决于限值集的取值，而非判据方法本身**。
> 在 IEUA 上：采用**未引用的引擎占位限值**时，比值法给 3.57 而饱和指数法给 2.52（差 +42%）；
> 但采用**带引用的 GB/T 50050-2017** 循环水准则时，比值法给 **2.500**，
> 与饱和指数法的 **2.5202** **仅差 0.8%**；采用 GB/T 19923-2024 补充水严格档时，
> 比值法反而**更保守**（1.250，−50%）。
> 差异的根源是占位限值把结垢侧（硬度 700 + 碱度 500 = 1200 as CaCO₃）
> 设得**宽于** GB/T 50050-2017 的 1100，同时把 Cl⁻ 设得**紧于**标准的 700。
> 因此本文不再声称"比值法系统性高估"，而报告**两种判据在何种限值下收敛、在何种限值下分叉**。

### ✅ 修正 #3 —— 数据库选择

**旧**：
> PHREEQC 库 `vitens.dat` 为饮用水库，结论限定在该库下。

**新**：
> 所用 `vitens.dat` 是 PHREEQC 官方 `phreeqc.dat`（2015-01-27 版）的派生版，
> 由代尔夫特理工大学 Stimela 平台为水与污水处理建模维护，
> 并非饮用水标准库；其与 `phreeqc.dat` 的差异仅在新增氧化还原解耦物种、
> 球霰石相与 2013 年原子量修正。
> 数据库敏感性已测试（`phreeqpython 1.6.2`）：同一输入下 IEUA 的允许 CoC 为
> **2.5202**（`vitens.dat`，原实现）→ **2.5203**（`phreeqc.dat`，**+0.004%**）→
> **2.3481**（`pitzer.dat`，**−6.83%**）；各库下**方解石均为限制相，定性结论不变**。
> `minteq.v4.dat` 在 `phreeqpython 1.6.2` 中**不存在**，该测试**未做**。
> 比较之下，**温度**（25→45 °C，−29.7%）与**相选择**（误把石英计入限值相 → CoC = 0）
> 对结果的影响都**大于**数据库选择。

### ✅ 修正 #4 —— χ 档位的定位

**旧**：
> χ = 0.25 作为代表性严苛情景。

**新**：
> χ_eff = min(CoC_lim, 5)/5。在 IEUA 上，**无加药热力学下界**给出 χ_eff = 0.504，
> **加药运行上界**给出 χ_eff ≈ 0.98（GSA 实测 4.91/5）。
> **χ = 0.25 无任何实测或文献支撑，仅作为外推压力档**用于边界测试，
> 不得称为代表性情景。主结论应以 **χ_eff ∈ [0.50, 0.98]** 为观测区间，
> χ = 0.25 明确标注为"外推"。

### ✅ 修正 #5 —— 阻垢剂上界

**旧**：
> 真实冷却塔用阻垢剂可把 LSI 维持到 2–3。

**新**：
> 厂商会议文献（Sherwood 1994；Cognetti 1996，均出自 Calgon）报告
> 有机阻垢剂可把碳酸钙控制在**至多 300 倍方解石饱和度**，
> 换算为 Langelier 饱和指数即 **LSI ≤ log₁₀(300) = 2.477**
> （因 LSI ≡ SI_calcite ≡ log₁₀(IAP/K_sp)）。
> 该数值**仅来自厂商会议论文，无独立第三方验证**，故本文只将其作为
> **技术上界（technical upper bound）备查**，不作为包络上界。
> 与之独立的第三方证据是 GSA/NREL 的实机运行观测（CoC 4.34–4.91）。

### ✅ 修正 #6 —— 温度必须显式化

**旧**：
> （PHREEQC 计算固定 `-temp 25`，未在正文说明）

**新**：
> 饱和指数计算对温度敏感：方解石溶解度随温度升高而降低，
> 使 IEUA 的允许 CoC 从 **2.52**（25 °C）降至 **2.10**（35 °C）、**1.77**（45 °C），
> 即 **−16.5% 至 −29.7%**。冷却塔循环水实际温度常在 30–45 °C。
> 因此本文将温度从固定假设改为**显式参数**，报告 25/35/45 °C 三档，
> 并在主结果中采用 35 °C 作为代表性工况。

### ✅ 修正 #7 —— 混样纪律

**旧**：
> （`AI-UWM model assumption` 行与 4 个实测水源同表并列，`is_reclaimed=True`）

**新**：
> 包络表严格区分三类：**observed**（公开报告/数据集实测）、
> **literature**（公开文献/标准准则）、**assumption**（无公开来源的模型假设）。
> `AI-UWM model assumption`（TDS 650 / Cl 130）仅标记为 assumption，
> **不进入**任何以观测为基础的分布统计或"再生水"归类；
> 引擎自身在 `ai_data_center_database.json` 中即标注
> `type="assumption"`、`site-specific design placeholder`。

### ✅ 修正 #8 —— 缺失项的准确归属

**旧**：
> Figshare RW/BW 缺失 SO₄、碱度、SiO₂。

**新**：
> Figshare RW/BW 在源表中**确实没有** SiO₂ 与温度；
> 但 **SO₄²⁻ 与碱度在源表中存在**（SO₄²⁻ 5.28 / 1.14 mmol·L⁻¹；
> HCO₃⁻ 4.56 / 2.28 mmol·L⁻¹），系项目提取脚本的 HTML 表头匹配缺陷
> （`<b>N<sup` / `N<sup` 模式无法匹配含 `<sub>` 的 `HCO<sub>3</sub><sup>` 与
> `SO<sub>4</sub><sup>`）被静默置为 NaN，并被下游报告为"源数据缺失"。
> 修正后 RW 的电荷平衡误差为 **1.21%**、BW 为 **5.31%**，均合格。
> **这是提取失败，不是观测缺失。**

### ✅ 修正 #9 —— 样本代表性

**旧**：
> （用 5 个样本的 χ 跨度推论"再生水"的普遍性质）

**新**：
> 全部 5 个样本中，**仅 IEUA RP-1 一个**同时具备 9/9 离子面板且电荷平衡合格（3.19%）；
> LADWP AWPF 是 RO 产水（TDS 22 mg/L），**不代表典型再生水**；
> Figshare RW/BW 来自**灌溉研究**，非冷却塔数据集，且缺 SiO₂ 与温度；
> `AI-UWM model assumption` 是纯假设。
> 因此任何"再生水普遍如何"的推论都**不成立**；
> 本文的水化学约束**限定于 IEUA 单一水源**，并以此为包络的观测锚点。

---

## 第三部分：可直接替换的句子（速查）

| 场景 | 禁用 | 替换为 |
|---|---|---|
| 摘要/贡献点 | "ratio screens over-estimate by ~40%" | "the admissible CoC spans 2.1–4.9 depending on antiscalant dosing and temperature" |
| 结果 | "CoC from 3.57 to 2.52" | "CoC = 2.52 (un-inhibited, 25 °C) vs 4.91 (inhibited, field-observed)" |
| 讨论 | "calcite saturation is the hard constraint" | "calcite saturation bounds the un-inhibited case; with inhibition the binding phase becomes amorphous silica" |
| 局限 | "vitens.dat is a drinking-water database" | "vitens.dat is a PHREEQC phreeqc.dat derivative for water/wastewater treatment" |
| 情景 | "χ=0.25 representative" | "χ=0.25 is an extrapolated stress tier; observed range is 0.50–0.98" |
| 阻垢剂 | "inhibitors keep LSI at 2–3" | "vendor conference literature reports up to 300× calcite saturation (LSI ≤ 2.477), not independently verified" |

---

## 第四部分：需同步更新的文件（**本轮未修改，交由主会话决定**）

> ⚠️ 以下文件**不在本审计的写入权限内**（纪律红线），仅列出以便主会话统一修订。

| 文件 | 需改位置 | 改动 |
|---|---|---|
| `10_论文主稿_v1.md` | L39–40, L65–66, L126, L178–183, L190–197, L396 | 删"40%"，换包络表述 |
| `02_阶段结果_T0-T7.md` | L7–8, L102, L110 | 同上 |
| `06_审计修复_v1.md` | L155, L159–160, L178, L216 | 同上 |
| `08_阶段结果_T5-T14.md` | L284 | 同上 |
| `11_红队自审_T17.md` | L94–95, L224, L231 | 同上 |
| `01_后续任务详细规划_v2.md` | L262 | 同上 |
| `A16_英文稿/supplementary_information.md` | L143–146 | 同上 |
| `A16_英文稿/manuscript_en_v2.md` | L223, L244–249 | χ=0.25 标注为外推 |
| `A0_预注册/preregistration_amendment_3.md` | L88 | 同上 |
| `18_方法自审与修复报告_2026-10-14.md` | L162–166 | 修正"vitens 是饮用水库" |
| `12_一致性核验_v1.md` | L48 | 同步 |
| `A4_水化学参数域/T6_water_chemistry_v2.py` | `load_figshare()` 表头匹配 | 修复提取 bug |
| `07_代码_AI-UWM引擎/aiuwm_src/data/ai_data_center_database.json` | `water_quality_thresholds` | 替换无引用占位值为带引用准则 |
