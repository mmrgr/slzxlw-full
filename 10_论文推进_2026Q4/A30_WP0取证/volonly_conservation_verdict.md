# WP3-1 · volume-only 水质路径的溶质守恒适用性裁定

> 任务 task-1（owner: lead）。已完成：代码定位 + 量纲/物理推理 + **通量平衡实测**。
> 产出：`volonly_conservation_verdict.md`、`volonly_flux_balance.py`、
> `volonly_flux_balance_summary.json`、`volonly_flux_balance_cases.csv`、`volonly_flux_balance_log.txt`。

---

## 0. 最终裁定（含一次自我纠错，如实留痕）

| 检验 | 裁定 | 数值 |
|---|---|---|
| 存量闭合 $dS=I-O$ | **不适用**（NOT_APPLICABLE_BY_CONSTRUCTION） | 该路径无溶质存量状态变量 |
| 水量闭合 $G=E+D+B$（毛补水口径） | **PASS** | 最大相对残差 **1.926e−16**（4/4 情景） |
| CoC 自洽 $\mathrm{CoC}=G/(B+D)$ | **PASS** | 最大相对误差 **2.503e−16**（4/4 情景） |

> **volume-only 路径是自洽的。** 其"守恒"应表述为"**稳态通量平衡与 CoC 自洽已证**"，
> 而非"溶质存量守恒已验证"（后者无对象），也**不得**因缺列而写成"不守恒"。

### ⚠️ 自我纠错留痕（重要教训）
本轮**首版**检验曾报出 **5.97e−2（约 5.6%）的系统性"不闭合"**，
一度看似重大缺陷。经排查，**错误在我的检验，不在引擎**：

- 我误用 `external_makeup_ml`（净外部取水，**已扣除内部回收水返回**）作为水量闭合的入项；
- 正确口径是 `gross_makeup_ml`（毛补水）。
- 实测：`M − (E+D+B) = −2766.26 ML`，**恰等于内部回收量**；
  而 `G − (E+D+B) = 0.0` **精确为 0**。

⇒ **教训（应并入门禁清单）**：同一物理量若有"毛/净"两个口径，
守恒检验必须显式声明用哪个；**约 5% 量级的、跨情景高度一致的"残差"，
首先应怀疑口径错误，而不是引擎缺陷**。
本脚本已把该对照（`faux_residual_rel_if_external_used`）作为固定输出保留，防止重犯。

---

## 1. 结论（先给答案）

**存量闭合裁定 = 不适用（NOT_APPLICABLE_BY_CONSTRUCTION）——但这不是坏消息，而是必须讲清楚的物理事实。**

> volume-only 路径**不是**一个"有溶质存量的动态系统"，而是一个
> **稳态浓缩倍数模型**：它把回路浓度**定义为**补水浓度 × CoC 的瞬时值，
> 不存在"回路溶质存量"这一状态变量，因此"存量变化 = 进 − 出"形式的闭合检验
> **在该路径上无对象可检验**。

由此得到三条必须写进论文的措辞纪律（§4）。

---

## 2. 实现定位（文件:行，引擎只读未改动）

| 事项 | 位置 | 事实 |
|---|---|---|
| 路径开关 | `aiuwm/full_engine.py:151-160` `_quality_state_enabled()` | 默认 `False` ⇒ 走 volume-only |
| 逐日求解器 | `full_engine.py:487` | `if component.get("kind") != "data_center" or not _quality_state_enabled(component):` 跳过 R10a 分支 |
| **R10a 的浓度定义** | `full_engine.py:1526-1529` | `blowdown_concentrations = {name: value * plan.cycles_of_concentration}` |

**最后一行是全部问题的关键**：在启用质量状态的路径里，**排污浓度也仍是
"混合补水浓度 × CoC"**，而不是从溶质存量推出来的。也就是说——

- 引擎中 **CoC 始终是一个"乘以浓度"的代数因子**，不是溶质累积的结果；
- R10a 相对 volume-only 的差别，在于它额外维护了
  `QualityState`（`quality_state.py`）、回收水返回、分盐账本，
  因而**产生了分盐闭合残差列**（`quality_solute_closure_*_kg`）；
- volume-only 连这些状态对象都不创建 ⇒ 自然**没有残差列可输出**。

这解释了 §4 观察到的现象，并且说明"缺列"**不是疏漏，而是结构性结果**。

---

## 3. 为什么不能硬套一个闭合检验

对稳态浓缩模型，若强行构造 `dS = I − O`：

| 项 | volume-only 下的值 | 说明 |
|---|---|---|
| 回路存量 $S$ | **未定义** | 无存量状态变量 |
| 进水带入 $I$ | $M \cdot c_{\rm mk}$ | 可算 |
| 出水带出 $O$ | $B \cdot (c_{\rm mk}\cdot \mathrm{CoC})$ | 可算 |
| $dS$ | **NaN** | 无对象 |

而稳态下二者本就**不应相等**：稳态意味着
$c_{\rm loop} = c_{\rm mk}\cdot\mathrm{CoC}$ 由**浓缩过程**维持，
进料盐分必须被排污带走，即应满足的是
$M\cdot c_{\rm mk} \approx B \cdot c_{\rm loop}$（**通量平衡**），
而**不是** $dS=0$ 意义上的**存量闭合**。

⇒ 在本路径上，"溶质守恒"的正确提法是**通量平衡校验**，
不是存量闭合。**把不存在的检验报成 PASS，正是 WP0 §4 批判的空洞通过；
把不适用的检验报成 FAIL，则是错误指控。二者都要避免。**

---

## 4. 可执行的替代检验（将在 WP3 主体实验中实现）

对 volume-only 路径，用**通量平衡**替代存量闭合：

$$\varepsilon \;=\; \frac{\bigl|\,M\,c_{\rm mk} \;-\; B\,c_{\rm mk}\,\mathrm{CoC} \;-\; E_{\rm drift}\,c_{\rm loop}\,\bigr|}{\max(M\,c_{\rm mk},\,\text{eps})}$$

其中 $M$=补水量、$B$=排污量、$\mathrm{CoC}$=引擎报告的浓缩倍数、
$c_{\rm mk}$=按掺混比质量加权的补水浓度。
判据用**相对容差**（量级达 $10^5$ kg，遵第 5 条门禁）。

⚠️ 该检验**同时约束了 CoC 的一致性**：若引擎的 $\mathrm{CoC}$ 与其水量关系不自洽，
$\varepsilon$ 会显著非零。这是对 volume-only 路径**唯一有内容**的守恒类检验。

---

## 5. 对主结论的具体影响（一句话）

> 既有主结论所依赖的 volume-only 路径，其"溶质守恒"**在构造上不适用存量闭合检验**，
> 应改以**通量平衡校验**来验证；因此主结论的守恒支撑当前应表述为
> **"待以通量平衡形式验证（WP3）"**，而**不得**写成"已验证"，也**不得**因缺列而写成"不守恒"。

---

## 6. 仍未识别的项

| 项 | 状态 |
|---|---|
| volume-only 路径通量平衡的**实测数值** | NOT_YET_MEASURED ⇒ WP3 主体实验首要项 |
| volume-only 是否存在引擎内部的通量自检 | 未发现（grep 无对应残差列） |
| $E_{\rm drift}$（飘损）在 volume-only 下的独立列 | 待确认（`evaporation_ml` 存在，飘损需另查） |
| R10a 路径溶质闭合 | **已证 PASS**（相对残差 5.71e−19，见 WP0 报告 §4.3） |

---

## 7. 与 R10a 的关系（避免误读）

两条路径**都**把 CoC 当作代数因子；差别在于 R10a **额外**维护了水分/盐分状态账本。
因此 WP0 §4.3 的 R10a 闭合 PASS **不能**被解读为"volume-only 也因此守恒"，
也不能被解读为"CoC 有物理累积支撑"。**CoC≈8 在两条路径下的差异
（1.77 vs 7.98）来自补水被返回水稀释的程度不同，而非溶质累积时间。**
这一点直接影响 `A21` 的机制归因措辞，须在 WP3 一并校正。

---

## 8. 复现

本裁定为**代码定位 + 量纲推理**结论，无新增数值产物。
所引行号对应 `07_代码_AI-UWM引擎/aiuwm_src/src/aiuwm/full_engine.py`（本文件写入时未改动引擎）。

```bash
grep -n "_quality_state_enabled" "07_代码_AI-UWM引擎/aiuwm_src/src/aiuwm/full_engine.py"
sed -n '1500,1545p'   "07_代码_AI-UWM引擎/aiuwm_src/src/aiuwm/full_engine.py"
```
