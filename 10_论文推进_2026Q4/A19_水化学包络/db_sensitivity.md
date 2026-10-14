# A19 数据库与判据敏感性

**日期**：2026-10-14
**环境**：`phreeqpython 1.6.2`，Python 3.13.14，Windows
**结论一句话**：**做了**。数据库选择对 CoC 的影响为 **−6.8 % 至 +0.004 %**，**不改变定性结论**；
温度的影响（−30 %）**远大于**数据库选择；`minteq.v4.dat` **不可用**，如实声明。

---

## 1. `vitens.dat` 的性质与适用边界（核实）

直接读取库头（`phreeqpython/database/vitens.dat`）：

```
#  stimela.dat (version 3.1.7)
#  under development by Peter de Moel (Omnisys) for Stimela platform at
#    Delft University of Technology
#  based on: phreeqc.dat (file date 2015-01-27, as part of Phreeqc
#    Interactive 3.1.7-9213)
#  Stimela is focussed on modelling for water and waste water treatment
#  list of modifications:
#  - added [Fe+2], [Mn+2] and [N+3] (redox-uncoupled Fe+2, Mn+2, NO2-)
#  - added [N-3] (redox-uncoupled Amm)
#  - added [C-4] and [S-2] (redox-uncoupled Mtg and Sg)
#  - uncommented definitions for Amm
#  - added solid Vaterite (CaCO3) (Standard Methods 2330 (2010))
#  - modified element_gfw per CIAAW/IUPAC 2013
```

### 判定

| 项 | 结论 |
|---|---|
| 它是什么 | **不是**"饮用水标准库"。它是 **PHREEQC 官方 `phreeqc.dat` 的一个派生版**（文件名 `stimela.dat`，别名 `vitens.dat`），由代尔夫特理工大学 Stimela 平台为**水与污水处理建模**维护 |
| 与 `phreeqc.dat` 的关系 | **同源**（2015-01-27 版），差异仅在：新增氧化还原解耦物种（Fe/Mn/N）、新增球霰石 Vaterite、按 2013 年原子量修正 |
| 适用范围 | 水/污水处理过程的**平衡热力学**计算。用于冷却水结垢倾向属于**合理外推**，但需注意它并非冷却水专用库 |
| 关键相是否齐备 | Calcite ✅ Aragonite ✅ Dolomite ✅ Gypsum ✅ Anhydrite ✅ SiO2(a) ✅ Hydroxyapatite ✅ |
| 目标相缺失 | Struvite ❌ Nahcolite ❌ Trona ❌ Ca₃(PO₄)₂ ❌（**影响磷酸盐/鸟粪石结垢评估**） |
| 规模 | 77 相 / 60 主物种 |

### ⚠️ 方法学注意

`vitens.dat` 中的 **`Vaterite`（球霰石）是 CaCO₃ 的亚稳相**。
若把 Vaterite 计入"限值相集"，会得到比方解石更严的约束（亚稳相溶解度更高，先饱和）。
原实现 `T6_water_chemistry_v2.PHASES` 只用 `Calcite`，**这是正确的选择**
（热力学稳定相为方解石）。本审计记录该差异但不改动原结论。

---

## 2. 跨数据库测试（**已做**）

### 2.1 可用库清单

| 库 | 大小 | 相数 | 主物种 | PITZER 块 | LLNL 块 | Si 主物种 | 状态 |
|---|---|---|---|---|---|---|---|
| `vitens.dat` | 69 151 B | 77 | 60 | 有 | 无 | ✅ | **原实现用库** |
| `phreeqc.dat` | 46 008 B | 71 | 50 | 有 | 无 | ✅ | 可用 |
| `pitzer.dat` | 31 939 B | 72 | 28 | 有 | 无 | ✅ | 可用 |
| `wateq4f_PWN.dat` | 107 557 B | 325 | 80 | 无 | 无 | ✅ | **试跑失败** |
| `minteq.v4.dat` | — | — | — | — | — | — | **不存在** |
| `minteq.dat` / `llnl.dat` / `sit.dat` | — | — | — | — | — | — | **不存在** |

`wateq4f_PWN.dat` 失败信息：
```
Exception: An error occured.
ERROR: RunString: No database is loaded
```
该库与 phreeqpython 1.6.2 的初始化路径不兼容。**未做**，如实声明。

### 2.2 跨库结果（IEUA RP-1，同一 SOLUTION 输入）

输入溶液逐字保持一致（`-units mg/L`，Ca/Mg/Na/Cl/S(6) as SO4/Alkalinity as CaCO3/Si，pH 固定）。
因此所测为**纯数据库效应**（含活度模型差异），未做人工修正。

**限值相集 = 原实现 `(Calcite, Dolomite, Gypsum, Anhydrite, SiO2(a))`**

| 数据库 | T = 25 °C | T = 35 °C | T = 45 °C | 限制相 |
|---|---|---|---|---|
| `vitens.dat`（原） | **2.5202** | **2.1033** | **1.7717** | Calcite |
| `phreeqc.dat` | 2.5203 | 2.1034 | 1.7718 | Calcite |
| `pitzer.dat` | **2.3481** | **1.8777** | **1.5401** | Calcite |
| `wateq4f_PWN.dat` | 不可算 | 不可算 | 不可算 | — |

### 2.3 方解石 / 石膏 / 二氧化硅饱和状态是否改变？

**饱和状态（SI 符号）不改变；数值有系统性偏移。** 以 25 °C、CoC=1 为例：

| 相 | vitens.dat | phreeqc.dat | pitzer.dat | 符号是否一致 |
|---|---|---|---|---|
| Calcite | −0.6856 | −0.6856 | −0.6511 | ✅ 均 <0 |
| Gypsum | −2.0857 | −2.0858 | −2.0514 | ✅ 均 <0 |
| SiO₂(a) | −0.6863 | −0.6863 | −0.7370 | ✅ 均 <0 |
| Dolomite | −1.7241 | −1.7242 | −1.7023 | ✅ 均 <0 |
| Halite | −6.6204 | −6.6204 | −6.6250 | ✅ 均 <0 |

### 2.4 相对差异

| 对比 | 25 °C | 判读 |
|---|---|---|
| vitens → `phreeqc.dat` | **+0.004 %**（2.5202 → 2.5203） | 同源，差异可忽略 ✅ |
| vitens → `pitzer.dat` | **−6.83 %**（2.5202 → 2.3481） | 由**离子活度模型**（Pitzer 比 Debye–Hückel 在中高离子强度下更准）导致 |

**IEUA 在 CoC=2.52 时离子强度约 0.022 mol/kg**——属于**低离子强度**，
Debye–Hückel（vitens/phreeqc）完全适用，无需 Pitzer。
因此 **vitens.dat 的选择在本场景是恰当的**，但 Pitzer 给出了**更保守**的 −6.8 %。
把该偏移纳入包络不确定度是稳妥的。

> **对高盐水源（Figshare BW，TDS 6131 mg/L，I ≈ 0.13）**，Pitzer 与 Debye–Hückel 的差异会更大，
> 此时**应优先用 `pitzer.dat`**。这是一个此前未被记录的**适用边界**。

---

## 3. 温度敏感性（原模型固定 25 °C —— 这是被忽略的强约束）

| T | CoC（Calcite SI ≤ 0） | 相对 25 °C |
|---|---|---|
| 25 °C | 2.5202 | — |
| 35 °C | 2.1033 | **−16.5 %** |
| 45 °C | 1.7717 | **−29.7 %** |

**机制**：方解石溶解度随温度**降低**（放热溶解），故升温 → 更易结垢 → 允许 CoC 下降。

冷却塔循环水实际温度常在 30–45 °C（GSA 实机报告 Table 4 即为夏季工况）。
原实现硬编码 `-temp 25`，**系统性高估了约 17–30 % 的允许 CoC**。

> 这个影响**远大于**数据库选择（0.004–6.8 %）。
> **建议**：论文中把温度从"固定假设"改为显式参数，报告 25/35/45 °C 三档。

---

## 4. 判据敏感性：比值法 vs 饱和指数法（**已做，且否证了旧表述**）

### 4.1 结果

IEUA RP-1，`CoC_design = 5`：

| 限值档 | 比值法 CoC | 饱和指数法 CoC | 差异 | 限制物种 |
|---|---|---|---|---|
| 引擎占位值（**无引用**） | 3.571 | 2.5202 | **+41.7 %** | alkalinity |
| GB/T 50050-2017 基准（**有引用**） | 2.500 | 2.5202 | **−0.8 %** | alkalinity |
| GB/T 50050-2017 宽松（**有引用**） | 2.500 | 2.5202 | −0.8 % | alkalinity |
| GB/T 19923-2024 补充水严格（**有引用**） | 1.250 | 2.5202 | **−50.4 %** | silica |

### 4.2 判读

**"比值法系统性高估 40 %" 不成立。** 它只在**未引用的占位限值**下出现。
换成带引用准则后，两个判据**几乎重合（差 0.8 %）**；
在严格档下**符号反转**（比值法更保守 50 %）。

### 4.3 差异的真正来源（诊断）

差异**不来自判据方法论**，而来自**限值集的取值**：

| 占位限值 vs GB/T 50050-2017 | 方向 | 对 CoC 的影响 |
|---|---|---|
| 硬度+碱度：占位 700+500 = **1200** vs 标准 **1100** | 占位**偏松** | 比值法算出更高的 CoC（偏乐观） |
| Cl⁻：占位 **500** vs 标准 **700** | 占位**偏严** | 比值法算出更低的 CoC（偏保守） |
| TDS：占位 **2200** vs 电导率换算 **2200**（等价） | 一致 | 无 |

净效应在 IEUA 上"偏松"占主导 → 3.57 > 2.52 → 表现为"高估"。

### 4.4 如何在包络上体现

比值法与饱和指数法**不应二选一**，而应作为**包络的两个边界来源**：

- **比值法（带引用限值）** → 工程可执行、可合规审计的**上界候选**；
- **饱和指数法（无加药）** → 热力学**下界**；
- 报告时**同时给出**，并显式说明两者在何种限值下收敛、在何种限值下分叉。

---

## 5. 相选择敏感性（本审计新增）

`Quartz`（石英）与 `Chalcedony`（玉髓）在 <100 °C 冷却水时间尺度上**受动力学抑制**，
天然水几乎恒为过饱和：

| 相 | SI @ 1×（IEUA，25 °C） | 是否应作限值相 |
|---|---|---|
| Quartz | **+0.5823** | ❌ 否（动力学抑制） |
| Chalcedony | +0.1533 | ❌ 否（动力学抑制） |
| SiO₂(a)（无定形） | −0.6863 | ✅ **是**（这才是实际控制相） |

**实测确认**：若误把 Quartz 计入限值相集，会得到 **CoC_safe = 0** 的荒谬结果
（本审计首轮运行即复现了该错误，后修正）。

> **结论**：相选择（phase selection）对结果的影响**可以是从"2.52"到"0"的量级**，
> 远大于数据库选择。论文中必须显式声明所用相集。
> 本审计采用的划分：
> - **限值相**：`Calcite, Dolomite, Gypsum, Anhydrite, SiO₂(a)`（+ Aragonite/羟基磷灰石等动力学可行相）
> - **仅报 SI、不作限值**：`Quartz, Chalcedony, Vaterite, Ca₃(PO₄)₂`

---

## 6. 结论（供论文引用）

> **数据库敏感性已测试**（`vitens.dat` / `phreeqc.dat` / `pitzer.dat`，`phreeqpython 1.6.2`）。
> 同一输入溶液下，IEUA 的允许 CoC 在原相集下为
> 2.5202（vitens，原实现）→ 2.5203（phreeqc.dat，**+0.004 %**）→
> 2.3481（pitzer.dat，**−6.83 %**）。
> 各库下**方解石均为限制相，饱和状态符号一致，定性结论不变**。
> 差异主因是**离子活度模型**（Pitzer vs Debye–Hückel）；
> 对低离子强度（I ≈ 0.022 mol/kg）的 IEUA，vitens.dat 适用。
> **未做**：`minteq.v4.dat` 等库在 phreeqpython 1.6.2 中不存在；
> `wateq4f_PWN.dat` 初始化失败。
> **重要补充**：**温度**的影响（25→45 °C，−29.7 %）和**相选择**的影响
> （Quartz 误计入 → CoC=0）都**大于**数据库选择。
> **判据敏感性**：比值法与饱和指数法的差异（+41.7 % 至 −50.4 %）**完全由限值集决定**，
> 在带引用准则（GB/T 50050-2017）下差异降到 **0.8 %**。
