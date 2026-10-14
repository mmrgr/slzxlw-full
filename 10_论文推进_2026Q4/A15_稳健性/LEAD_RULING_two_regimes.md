# Lead 裁定：两口径问题（dp=0 份额口径 vs dp>0 容量扩张口径）

**日期**：2026-10-14 ｜ **针对**：task-4 中途预警（robustness agent 的发现）

---

## 0. 结论先行

**robustness agent 的发现完全正确**，Lead 已独立复算确认。这不是错误，而是
本稿**必须显式区分的两个口径**。正文必须**并列报告**，不得只写一个。

---

## 1. 实测对照（Lead 独立复算，ha / B_full / IEUA，pool_scale=1，gap_scale=1，ai_target=0.7）

| dp_scale | available | x_ai | inc_recl | sum | pool | S_AI | S_city | inc_recl − pool |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 24,404 | 9,118 | 15,286 | 24,404 | 24,404 | 8,281 | **−837** | **−9,118** |
| 0.5 | 36,607 | 13,805 | 22,801 | 36,607 | 24,404 | 12,536 | +10,933 | −1,603 |
| 1.0 | 48,809 | 18,579 | 30,230 | 48,809 | 24,404 | 16,869 | **+22,694** | **+5,825** |
| 2.0 | 73,213 | 20,912 | 33,779 | 54,691 | 24,404 | 18,986 | +28,360 | +9,374 |

**基线**：`gap/pool = 33,779/24,404 = 1.38`。
故 **dp ≥ 1 时可用池超过既有用户缺口**，`inc_recl` 才会 > `pool`。

### 1.1 守恒的正确对象

`x_ai + inc_recl ≡ pool + dp`（残差 3.6e-12），**不是** `≡ pool`。
A13 早期表述简写为 `pool` 是不精确的，**正确形式见下**。

---

## 2. 正确的通式

$$S_{\rm city} = \underbrace{(M_0 - M)}_{\text{水质通道}\ \le 0}
\;+\;\underbrace{(r_{\rm inc} - P)}_{\text{既有用户净得失}}$$

其中 $r_{\rm inc}$ 为既有用户分到的再生水，$P$ 为原池。关键：

- **dp = 0**：$r_{\rm inc} \le P$，故 $r_{\rm inc}-P \le 0$ → $S_{\rm city} \equiv M_0-M \le 0$（**恒等式**）
- **dp > 0**：$r_{\rm inc}$ 可以 > $P$ → $r_{\rm inc}-P > 0$ 变为可能 → $S_{\rm city} > 0$ 变为可能

> 即 **$S_{\rm city}$ 转正的途径是"既有用户从新增产能中获益"**，
> 这**不是**"再生水竞争被缓解"。

---

## 3. 两个口径的正式定义（正文用语）

### 口径 A —— 份额口径（share-only），dp = 0

- **语义**：再生水供给不变，数据中心只是在**存量池**里与既有用户竞争。
- **性质**：$S_{\rm city} \equiv M_0 - M \le 0$，**恒等式，无经验内容**。
- **$P(S_{\rm city}>0)$**：**≈ 0（数值零）**。
- **A13 的机制分析（两通道、$\varphi^*$、$\psi$ 判据）全部在此口径下完成**
  （`two_channel_summary.json` 的 `dp_all_zero = true` 是**刻意设计**，确保与容量扩张正交）。

### 口径 B —— 含容量扩张口径（capacity-inclusive），dp > 0

- **语义**：新增再生水产能，既有用户也从增量中受益。
- **$P(S_{\rm city}>0)$**：**0.62**（T11b 原口径）。
- ⚠ **成因是容量扩张的归属记账**，不是再生水竞争的缓解。

---

## 4. 正文必须这样写（英文稿措辞建议）

> **Do not merge the two.** In the **share-only** regime (no new capacity), the probability
> that the city-level water-volume account is positive is **zero** (numerically zero):
> reclaimed cooling only reallocates a fixed pool.
> In the **capacity-inclusive** regime, where new reclaimed capacity is added and incumbent
> users also draw from the increment, that probability rises to **0.62**.
> The two are not contradictory: the former is the outcome of *competition* for a fixed
> resource; the latter is mainly the outcome of *capacity expansion and its attribution*.
> All mechanism results reported here (§2–4) are obtained in the **share-only** regime.

**中文对应**：
> 在**份额口径**（不新增产能）下，城市级水量净收益为正的概率为 **0（数值零）**；
> 在**含容量扩张口径**下该概率升至 **0.62**。两者不矛盾：前者是再生水**竞争**的结果，
> 后者主要是**新增产能归属**的结果。本文的机制分析（第 2–4 节）全部在**份额口径**下进行。

---

## 5. 关于 0.003 的更正（审计员发现，Lead 复核确认）

T11b 在 dp=0 处报出的 $P(S_{\rm city}>0)=0.003$ **不是物理概率**：

| 项 | 值 |
|---|---|
| 700 样本中 $S_{\rm city}>0$ 的个数 | 2 |
| 这 2 个的取值 | $3.64\times10^{-12}$、$9.09\times10^{-13}$ ML |
| 该列 $\lvert S_{\rm city}\rvert$ 中位数 | $3.20\times10^{2}$ ML |
| 量级差 | **约 14 个数量级** |

→ 属**浮点残差**，应记作 **0（数值零）**。
中文主稿 §2.6 已修正。**所有下游文档一律采用"0（数值零）"，不得再写 0.003。**

---

## 6. 对 task-4 交付的具体要求

1. **先验敏感性**：**两个口径都做**。
   - 口径 B（dp=1）：复现 0.62，报告其在 uniform / log-uniform / triangular 下的漂移（红队 M5/P2 阻塞项）
   - 口径 A（dp=0）：报告 ≈0 在各先验下的稳定性
2. **消融矩阵**：**必须含 dp 轴**，量化"容量扩张"与"可靠性闭合"的**独立贡献**——
   这是证明 A13 机制与容量扩张正交的关键证据。
3. 留出验证 / 网格分辨率 / 边界压力测试：照常。
4. `robustness_summary.md` 中显式写入本文件 §3 的两口径定义，
   并**直接采用 §1 的对照表**（它将作为 SI 中解释"两个数字为何不矛盾"的关键材料）。

---

## 7. 对英文稿的连带影响

`manuscript_en_core.md` §1 的恒等式写法**需按 §2 的通式修正**（`pool` → `pool + dp`），
并在 §5 明确：A13 全部检验在 dp=0 下完成，故与容量扩张正交。
