# WP3 · 水化学机制验证报告（2026-10-16）

> 任务：检验 H4（水质组成能否**反转** $dS_{\rm pot}$ 符号）——这是本项目唯一有资格
> 称为"机制"的候选，也是论文能否上 Nature 子刊的关键。
>
> 产出：`wp3_h4_robustness.py` / `wp3_h4_robustness_summary.json` / `_cases.csv` / `_log.txt`

---

## ⚠️ 重要更正（2026-10-16，由 A33/WP4 实验推翻本文档初版结论）

**本文档初版曾声称："再生水更干净 ⇒ CoC 更高 ⇒ 更省补水 ⇒ 回用更有利"（H4 机制链）。**
**该机制链被 A33 在完整城市级口径上的实测否证，现予更正。**

A33 在 **IEUA 与 LADWP 两个完整物种水样**上算出城市级 $dS_{\rm pot}$（$n_{\rm eff}=47$）：

| 量 | 与 $dS_{\rm pot}$ 的相关性 |
|---|---:|
| $x_{\rm AI}$（实际取用再生水量） | **−0.9287** ← 主导 |
| $q$（水质项） | −0.1596 ← 微弱且**反向** |
| $M_0-M_1$（补水节省） | −0.1075 |

同情景（$\varphi$=0.6, pool_scale=1）对照：

| 水样 | $q$ | $x_{\rm AI}$ | $M_0-M_1$ | $dS_{\rm pot}$ |
|---|---:|---:|---:|---:|
| IEUA（较脏） | −0.0439 | **8905.6** | +1320.5 | −7585.1 |
| LADWP（较干净） | **+0.1069** | **8154.4** | −2777.3 | **−10931.7** |

**关键**：LADWP 水质更有利（$q>0$），但其 $x_{\rm AI}$ **更小**（8154 < 8906）——
因为 CoC 更高 ⇒ 排污更少 ⇒ **达到同一掺混比所需再生水量更少**。
而 $x_{\rm AI}$ 的量级与影响力都远大于补水节省项。

> **⇒ 真正驱动城市节水的是"取用了多少再生水（从而替代了多少自来水）"，
> 而不是"水质省了多少补水"。**
> **H4 作为"符号反转机制"的表述必须降级**（见 §1 修订版）。

---

## 1. 裁定（修订版）

### 1.1 $q$ 的方向**确实**由水质决定（这一条仍成立）
在**完整物种**水样上，$q$ 的符号逐水样完全一致、远离退化：
- IEUA（比自来水脏）：$q\in[-0.128,-0.017]$，**恒负**（24/24）；
- LADWP（比自来水干净）：$q\in[+0.040,+0.120]$，**恒正**（23/23）。
⇒ **"再生水是否比自来水干净决定 CoC 的升降方向"** 成立，且可由干预前化学预测。

### 1.2 但 $q$ **不**决定城市级结果 —— H4 降级
- $q$ 与 $dS_{\rm pot}$ 相关性仅 **−0.16**（且符号与直觉相反）；
- $x_{\rm AI}$ 与 $dS_{\rm pot}$ 相关性 **−0.93**；
- 可靠子集内 $dS_{\rm pot}$ **全部为负（47/47）**，故 $q$ 的正负**不区分**结果符号。

> **⇒ 修订后的机制陈述（这才是可主张的）**：
> 再生水冷却的城市级净收益主要由**取水量** $x_{\rm AI}$ 决定（它替代自来水）；
> 水质通过 $q$ 改变**允许浓缩倍数**，进而影响**所需取水量**与补水节省，
> 但其净效应**不是**简单的"越干净越有利"，
> 而是经由 $x_{\rm AI}$ 与 $\rho(\kappa-1)$ 的**竞争**间接体现。
>
> **H4 由"机制"降级为"中间量关系"**：水质决定 $q$ 的符号（已验证），
> 但 $q$ 到 $dS$ 的传递需要分配信息（与 WP2-E3 的结构性不可识别结论一致）。

---

## 2. H3 的鉴别力问题（必须承认）

A33 判定 H3（$q>0$ ⇒ 受益）为 **SUPPORTED 但属"空洞通过"**：
可靠子集内 $dS_{\rm pot}$ **无正例**（47/47 全负），故该检验**不具鉴别力**——
$q<0 \Rightarrow$ 受益**同样成立**。

⇒ **正文不得**把 H3写成"有力证实"；应写为
"在样本内无正例，故该充分条件未被证伪，但**亦未被有效检验**"（遵门禁第 4 条）。

---

## 3. ⚠️ 支撑缺陷（须披露）

### 3.1 引擎对不完整组成**会拒绝**，但分析路径**绕过了该检查**
- 直接调用 `FullAIUWMModel`：不完整组成 ⇒ **报错**
  ```
  ProjectValidationError: ...quality_mg_l 缺少质量指标: ['alkalinity','silica']
  ```
- 但主扫描所用路径 `city_model.calculate_data_center_plan` **不触发该校验**，
  缺失物种被**按 0 处理**。

### 3.2 权威水样表（来自 `city_model.load_samples()`，非自造）

| 水样 | 物种数 | 缺失 | 是否可再生水 |
|---|---:|---|---|
| IEUA RP-1 (2025, tertiary) | 9 | — | ✅ |
| LADWP AWPF (2012, RO product) | 8 | Mg | ✅ |
| Figshare RW (2025, paired study) | 6 | SO4, alkalinity, silica | ✅ |
| **Figshare BW (5 g/L)** | 6 | SO4, alkalinity, silica | ❌ **brackish，非再生水** |
| AI-UWM model assumption | 2 | 7 项 | ⚠️ 自设假设值 |

### 3.3 缺失按 0 的偏差（A33 已量化）
| 水样 | 偏差 |
|---|---|
| **AI-UWM assumption（2 物种）** | **$q$ 符号会翻转**：+0.110 →（按观测上界填补）−0.082 ⇒ **其"更干净"是缺失按 0 的人为产物，不得用于任何符号结论** |
| Figshare RW（缺 2 物种） | $q$ 符号稳定（恒负），但幅度可变 **1.6×** |

**偏差方向**：缺失按 0 ⇒ 使水样显得更"干净" ⇒ **系统性偏向"回用有益"**。

### 3.4 ⚠️ 修正：Figshare RW 并非"触 CoC 下限"
本文档初版称 "Figshare RW CoC1=1.000001 触下限"。**A33 实测该值仅在
`limit_scale=0.25` 出现**；项目默认 `limit_scale=1.0` 下 `CoC1=2.02`，**并不退化**。
（`limit_scale=0.25` 按 `A26_语义统一` §1 属**无实测支撑的外推档**。）
⇒ 排除 Figshare RW 的**正当理由应改为**
"组成不完整（缺 2 物种）+ 对填补量级敏感"，**而非**"触 CoC 下限"。

---

## 4. 水样纳入/排除清单（采纳 A33）

| 处置 | 水样 | 理由 |
|---|---|---|
| ✅ **主图 + 主结论** | IEUA RP-1、LADWP AWPF | 均 5 物种完整、非退化 |
| ⚠️ **仅 SI 并标注缺失** | Figshare RW（缺 alkalinity, silica） | 组成不完整、量级敏感 |
| ⚠️ **仅 SI 且须注明 $q$ 符号不稳健** | AI-UWM assumption（缺 hardness/alkalinity/silica） | $q$ 符号随填补翻转 |
| ❌ **完全排除** | Figshare BW | **是苦咸水（brackish），非再生水** |

---

## 5. 对论文的改写指令

1. **删除**："水质改变符号 ⇒ 更干净更有利"这一因果链（已被否证）。
2. **保留并强化**：$q=\frac{\mathrm{CoC}_1-\mathrm{CoC}_0}{\mathrm{CoC}_1(\mathrm{CoC}_0-1)}$
   为**恒等式**，且"再生水 vs 自来水的水质优势决定 $q$ 的符号"（$q$ 层面已验证）。
3. **新增（本文最有价值处）**：$q$ 与 $dS$ 之间的**传递需要分配信息**，
   故净收益**不能**由水质单独判定 —— 与 WP2-E3/E3b 的独立预测结果衔接。
4. **H3 标注鉴别力不足**，不得称为"有力证实"。
5. **Figshare RW 的排除理由改写**（见 §3.4）。

---

## 6. 与 A29 文献结论的衔接（创新定位）

文献核验确认：
- 头号竞争文献 **Wang et al. 2026**（*Env. Sci. Ecotech.* 31, 100702）原文明确声明
  `water reused within recirculating cooling systems is not included`，
  全文 CoC / salinity / TDS / quality **出现 0 次**；
- **Saleh 2026**（*ES&T* 60(26):18383–18386）是 **Viewpoint**，已公开主张
  "beyond water quantity to water compatibility"。

⇒ 因此本项目**不能**声称首创"应关注水质"这一议程，
**但可以**声称（且本轮已给出证据）：
> **to our knowledge, no published work formalises the quality control of
> reclaimed-water cooling as a closed-form condition, uses it to show that the
> dominant control on the city-level outcome is the volume of reclaimed water
> drawn (not the makeup saved), and demonstrates the whole thing as a
> pre-intervention prediction problem with reported out-of-sample skill.**

---

## 7. 复现

```bash
cd "C:/Users/mmrgr/Desktop/论文/算力中心/10_论文推进_2026Q4/A32_WP3_水化学"
PYTHONIOENCODING=utf-8 python wp3_h4_robustness.py    # ~3 s
# 城市级口径(推翻初版结论的依据):
cd ../A33_WP4_组成重构 && PYTHONIOENCODING=utf-8 python wp4_complete_samples.py
```

## 8. 仍未闭合

| 项 | 状态 |
|---|---|
| $\rho(\kappa-1)$ 的干预前代理（用于提升 E3b 判据） | 待 WP5 |
| 更多真实水样（≥5 个完整物种）以增强外部效度 | 待 WP4 |
| 温湿度/结垢动力学对 CoC 的二次影响 | 未建模，列入 Limitations |
