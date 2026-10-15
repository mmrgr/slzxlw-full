# CHI 语义权威表与状态词表（A26）

> **本文件是 `chi` / `limit_scale` / 求解器状态词的唯一权威定义。**
> 任何产物、文档、审计脚本引用这些量时**必须**引用本表。
> 建立原因：A25/A26 审计发现同名参数在项目内存在**两套冲突定义**，且数值区间重叠，
> 跨表合并会静默出错。

---

## 1. `chi`：两套定义（**必读**）

| 定义 | 公式 | 取值 | 使用者 | 判定 |
|---|---|---|---|---|
| **χ 严格度** | $\chi := \mathrm{CoC_{lim}^{realized}} / \mathrm{CoC_{design}}$ | ~0.078 … 1.0（连续） | `T12_surface.csv` / `T12_boundary_curves.csv` | ✅ **正确用法** |
| **χ = limit_scale**（历史误名） | 引擎水质限值的**整体缩放因子** | 0.25 / 0.5 / 1.0（**1e6 = 不约束**） | A13c、A15、A17、A22、fig1 | ⚠ **历史命名，见 §3 过渡方案** |

### 1.1 为什么危险

**数值区间重叠但含义不同**：

| 数值 | 在 T12 中 | 在 A13c/A15 中 | 在 A17 中 |
|---|---|---|---|
| `0.25` | 严格度 0.25（CoC 压到设计 25%） | `limit_scale=0.25` | `limit_scale=0.25` |
| `1.0` | 严格度 1.0（**刚好到设计值**） | `limit_scale=1.0`（**仍受约束**，CoC=4.6034） | 未使用 |
| `1e6` | 不适用 | 未使用 | `limit_scale=1e6`（**真不约束**，CoC=5.0） |

> **`1.0` 在三处的含义互不相同。** 禁止直接把不同来源的 `chi` 列合并或比较。

### 1.2 实测锚点（ha × IEUA × φ=0.4）

| `limit_scale` | 实测 CoC | `chi_strictness` = CoC/5.0 | `quality_binding` |
|---:|---:|---:|:--:|
| 1e6 | 5.0000 | 1.0000 | ❌ 否 |
| 1.0 | 4.6034 | 0.9207 | ✅ 是 |
| 0.5 | 2.3165 | 0.4633 | ✅ 是 |
| 0.25 | 1.1952 | 0.2390 | ✅ 是 |

---

## 2. 权威列定义（所有新产物必须包含）

| 列名 | 含义 | 来源 |
|---|---|---|
| **`limit_scale`** | 传给引擎的限值整体缩放因子（**权威列**） | 实验设定 |
| **`chi_strictness`** | $\mathrm{CoC_{lim}^{realized}}/\mathrm{CoC_{design}}$（无量纲严格度） | 由引擎实测 CoC 反解 |
| **`quality_binding`** | 布尔：`chi_strictness < 1 − 1e-9`，即限值是否真的在起作用 | 派生 |
| `chi` | **历史列**，含义随文件而变 ⇒ 只读参考，**不得用于跨表运算** | 见 §1 |

> ⚠ **`chi_strictness` 是从引擎占位限值反解的，只具相对意义**，
> 不可作为绝对"水质严格度"对外引用（审计 B3 已登记）。

---

## 3. 过渡方案（为何不直接统一改名）

A17 的 `chi_label`（`free` / `0.98` / `0.50` / `0.25`）与 A13c 的 `chi` 数值
**已被主稿与 SI 引用**，直接改名会破坏可追溯性。

**故采用**：
1. **保留**原列不动（含 `chi_label`），避免破坏引用；
2. **新增** `limit_scale` / `chi_strictness` / `quality_binding` 三列；
3. 在原列名后**不加改名**，但在每个产物的 README/报告与 summary 中加注语义；
4. 任何新脚本**禁止**再用裸 `chi` 作参数名，必须写 `limit_scale`。

---

## 4. 求解器状态词表（**审计必读**）

⚠ **不同代码路径的状态字段词表不同。** A25 审计曾因"凡不含 `converged_unique` 即视为失败"
而**误报**了三处。以下为完整词表。

| 状态值 | 含义 | 是否可用于统计 | 出现位置 |
|---|---|:--:|---|
| `converged_unique` | 水质+分配联合求解唯一收敛 | ✅ 是 | 全部联合求解产物 |
| `no_convergence` | 求解器**未收敛**，分配量退化为 0 | ❌ **剔除** | 同上 |
| `non_unique` | 多个根，解不唯一 | ❌ **剔除** | 同上 |
| `quality_not_converged`（**联合求解语境**） | 同 `no_convergence`，分配量为 0 | ❌ **剔除** | A13c / holdout / A16 fig1 源 |
| `quality_not_converged`（**T2 Q0 语境**） | **占位值**：Q0 用 `coc_mode='fixed'`，**根本不调用水质求解器** | ✅ **可用** | `A7/T2_cell_results.csv` |
| `converged` | T2 曲线点收敛 | ✅ 是 | `T2_coc_curves.csv` |
| `not_applicable` | 该点不适用 | ✅ 是 | `T2_coc_curves.csv` |
| `ok` | 仪器化子类（有限供水模型）自判正常 | ✅ 是 | `A18/finite_supply_grid.csv` |
| `n_days=730` | **非状态**：A20 桥接记录的窗口标记 | ✅ 是 | `A20/bridging_comparison.csv` |
| `verification_status`（A14） | **非求解器状态**：证据核验状态（VERIFIED/UNVERIFIED） | ✅ 是 | `A14_parameter_anchors.csv` |

### 4.1 两条硬规则

1. **判据必须是"是否在收敛白名单内"**，不是"是否含 `converged` 子串"：
   ```python
   RELIABLE = {"converged_unique", "converged", "not_applicable", "ok"}
   ok = d.status.isin(RELIABLE)
   ```
2. **同一字段名在不同代码路径下可能词表不同**（最典型：T2 的 `quality_not_converged`）。
   跨产物比较状态前**必须**先查本表。

### 4.2 T2 的 Q0/Q1 辨析（A25 误报根因）

| Q | `coc_mode` | 调用水质求解器 | 实测 `closure_residual` / `fp_residual` | status |
|---|---|:--:|---:|---|
| **Q0** | `fixed` | **否** | **0.000e+00** | `quality_not_converged`（占位） |
| **Q1** | `quality_limited` | 是 | 0.000e+00 | `converged_unique` |

交叉表**完全对角**（Q0↔320、Q1↔320），且全部 640 行 `S_city_ml` 均有值
⇒ **T2 无缺陷**；该标签应改名为 `quality_solver_status` 并加注。

---

## 5. 门禁清单（引用本表执行）

| 门禁 | 规则 |
|---|---|
| G-状态 | 头条统计只含收敛白名单；报告 `n_all / n_reliable / n_excluded` |
| G-语义 | 任何 `chi` 相关列必须同时给出 `limit_scale` 与 `chi_strictness`；禁止裸 `chi` 参与跨表运算 |
| G-代数 | 恒等式/判据的吻合率**不能**作为情景可靠性的证据 |
| G-非空洞 | 任何 gate 必须验证选集非空；空集标 `VACUOUS` 且不计通过 |
