# WP7 · 主稿与 SI 修订报告（v3 → v4，2026-10-16）

> 本轮对 `A16_英文稿/manuscript_en_v3.md` 与 `supplementary_information.md` 做了
> **实质性修订**，含**多项撤回**。本文件是修订的唯一索引，供终审与审稿人追溯。
>
> ⚠️ 文件名仍为 `manuscript_en_v3.md`（沿用原有文件名以便追溯），
> **内容已标为 working draft v4**。

---

## 1. 修订摘要

| 类别 | 数量 | 说明 |
|---|---:|---|
| **撤回的主张** | **2 项** | "95% 真实设施已承诺"、"更干净⇒更节水" |
| **降级的主张** | **2 项** | "吻合率 1.0000 是发现"、"H3 有力证实" |
| **数字更正** | **6 组** | R²、分支 C 计数、组成表、头条计数口径、CoC 下限理由、残差统一 |
| **新增章节** | **2 处** | 主稿 §3d（独立预测检验）；SI S11–S15 |
| **新增 Limitations** | **6 条** | 见主稿 Limitations 9–14 |
| **标题与定位** | 已改 | 见 §4 |

---

## 2. 逐项修订明细

### 2.1 【撤回】"95% 真实设施已处于已承诺状态"
- **位置**：Abstract L43、§6b（原 L480–493）
- **原因**：判据只观测**供方产能**，未观测**需方已承诺需求**；可证明界 = [0%, 100%]
- **改为**：明确写出"**not identified**"，给出 [0%,100%] 界；保留**可识别**的产能可行性
  陈述（2.1–6.6%，随 $r$）；只支撑"扩产路径受产能限制"这一**范围限定**结论
- **依据**：`A30_WP0取证/a24b_partial_id_summary.json`

### 2.2 【撤回】"再生水更干净 ⇒ CoC 更高 ⇒ 更省补水 ⇒ 更有利"
- **位置**：原 §5 机制归因、Limitations
- **原因**：城市级口径实测 $\mathrm{corr}(x_{\rm AI},dS)=-0.93$（主导）vs
  $\mathrm{corr}(q,dS)=-0.16$（微弱且**反向**）；CoC 高 ⇒ 排污少 ⇒ 所需再生水量**更少**
- **改为**：Limitations 第 10 条明确撤回该归因链；
  保留"水质决定 $q$ 的符号"这一**中间量**结论
- **依据**：`A33_WP4_组成重构/wp4_results.csv`；`A32_WP3_水化学/` 更正节

### 2.3 【降级】"符号判据吻合率 1.0000"
- **位置**：Abstract、§2、Discussion
- **改为**：明确为**记账一致性检验**，零预测内容；SI S11 报告严格检验结果
  （0.671 < 基线 0.861）
- **依据**：`A31_WP2_假设冻结/wp2_e3_*`

### 2.4 【降级】H3"有力证实" → "鉴别力不足"
- **位置**：§2 头条、§7 robustness 表
- **原因**：完整水样 47 情景内 $dS$ **全为负**，无正例 ⇒ 该充分条件**未被有效检验**
- **改为**：SI S10 保留为 negative result 第 5 条（"vacuous pass"，遵门禁第 4 条）

### 2.5 【数字更正】
| 项 | 原值 | 新值 | 依据 |
|---|---|---|---|
| 跨域留出 R² | 0.557 / baseline −0.050 | **0.806 / −0.073** | `A15_稳健性/holdout_summary.json` |
| 分支 C 无挤占 | 429 of 446，17 例外 | **369 of 372，3 例外** | Lead 复算 |
| 分支退化残差 | 1.1e−11 / 1.5e−11 | **1.27e−11 / 1.46e−11**（相对 2.0e−16 / 1.6e−16） | Lead 复算 |
| 组成表 | 183/0、184/0、148/48、116/54 | **186/8/9、187/8/9、151/56/9、119/62/9**（含物种数与 $n$） | Lead 复算 |
| 头条计数 | 631/102（标 $n$=813） | **643/134/36（$n$=813）**，并说明 631/102 的容差带口径 | `WP0_补充_头条计数口径分歧.md` |
| Discussion 残差 | 2.9e−11 | **2.55e−11**（相对 2.9e−16） | Lead 复算 |

### 2.6 【新增】主稿 §3d 独立预测检验
- 表格：化学判据 0.389 / $q>0$ 0.671 / 联合 0.906 vs 基线 0.861；$n_{\rm eff}=733$
- 折外（leave-one-composition-out）：**0.901 vs 0.859**
- 结构性解释：$dS/M_1=\rho(\kappa-1)-q$，两项可反号 ⇒ 化学单独不可判定
- **含负结果**，并声明 $pool$ ratio 的数据可得性限制

### 2.7 【新增】SI S11–S15
- **S11** 干预前预测检验（含负结果与折外验证）
- **S12** 制度占比的**部分识别**（撤回点估计，给出 [0%,100%] 界与可识别的产能表）
- **S13** 两条水质路径的守恒检验（R10a 相对残差 5.71e−19；volume-only 通量平衡
  1.93e−16 / 2.50e−16；并记录 `gross vs external_makeup` 的**口径陷阱**）
- **S14** 产物完整性说明（B1/B2 列名互换、头条计数约定、Figshare BW 非再生水、
  求解器状态词表不匹配）
- **S15** 门禁清单（累计 **11 条**）

### 2.8 【新增】Limitations 9–14
组成不完整偏差方向、主导控制量更正、volume-only 守恒的**适用性**说明、
列名互换、预测器的数据前提、敏感性与极端事件的口径分离。

---

## 3. 未改动但已确认正确的内容（避免过度修改）

| 项 | 状态 |
|---|---|
| 统一恒等式 $dS_{\rm pot}=C-F$ 及其残差 **2.55e−11**（相对 2.9e−16） | ✅ 主稿**原本正确** |
| $q>0$ 组 **290/290** 零例外 | ✅ 不变量，与零值口径无关 |
| $q$ 分组 290 / 288 / 235 | ✅ 正确 |
| $q<0$ 组内 133 下降 / 102 上升 | ✅ 正确（Lead 复算确认） |
| 桥接 24 对、符号一致 23/24、$M_0$ 中位相对差 5.08e−16 | ✅ 正确（36 对为已撤回陈述） |
| A20/A28 相关更正段落 | ✅ 原本即为撤回说明，保留 |

---

## 4. 标题与定位调整

**原题**：*Supply state, not cooling technology, governs the urban water outcome of
reclaimed-water cooling in AI data centres*

**新题**：*What Governs the Urban Water Outcome of Reclaimed-Water Cooling in AI Data
Centres? Competition, Water Chemistry and the Limits of Prediction*

**理由**：
1. 原题断言"supply state **而非**冷却技术"——但本轮已证 **H4 机制链被否证**，
   且水质/技术的作用未被完全排除，原题**过强**；
2. 新题如实反映本文的三个真实贡献：**竞争**（挤占项）、**水化学**（$q$）、
   **预测的边界**（0.671 不可判定 → 加入需求侧量后 0.901）；
3. 采用疑问式，避免在结果生成后才锁定夸大结论（符合 GPT 意见 §WP7 的纪律）。

**创新定位（据文献核验 A29）**：
- ❌ 不能声称首创"应关注水质"议程（Saleh 2026 *ES&T* Viewpoint 已占）；
- ❌ 不能声称首创全球 DC–污水厂匹配（Wang 2026 已占）；
- ✅ 可声称："to our knowledge, no published work formalises the quality control of
  reclaimed-water cooling as a closed-form condition **and** frames the net city outcome as a
  pre-intervention prediction problem with reported out-of-sample skill."

---

## 5. 数字核验（终审须全过）

```bash
cd "C:/Users/mmrgr/Desktop/论文/算力中心/10_论文推进_2026Q4"
# 1) 主稿/SI 无禁用主张
grep -n "95%\|93%\|empirically dominant" A16_英文稿/manuscript_en_v3.md   # 仅应出现在撤回说明中
# 2) 无陈旧数字
grep -n "0\.557\|429 of 446\|17 exceptions" A16_英文稿/*.md               # 仅应出现在撤回说明中
# 3) 无 LaTeX 破损（裸控制字符）
PYTHONIOENCODING=utf-8 python -c "
for f in ('A16_英文稿/manuscript_en_v3.md','A16_英文稿/supplementary_information.md'):
    s=open(f,encoding='utf-8').read()
    bad=[i for i,c in enumerate(s) if ord(c)<32 and c not in '\n\r\t']
    print(f, '破损:', bad if bad else '无 ✓')"
# 4) 关键数值复算（Lead 独立）
cd A13_可靠性机制 && PYTHONIOENCODING=utf-8 python -c "
import pandas as pd,numpy as np
d=pd.read_csv('supply_state_regimes.csv')
r=d[(d.status=='converged_unique')&(~d.coc_floor_degenerate.astype(bool))]
C=r.inc_B2_ml-r.inc_B1_ml;F=r.M0_ml-r.M1_ml
res=(C-F-r.x_ai_B1_ml-r.dS_pot_ml).abs();sc=r[['M0_ml','M1_ml']].abs().max(axis=1)
print('identity abs/rel:',res.max(),(res/sc).max())
print('signs:',(r.dS_pot_ml<0).sum(),(r.dS_pot_ml>0).sum(),(r.dS_pot_ml==0).sum())"
```

**预期**：`identity abs ≈ 2.55e-11`、`rel ≈ 2.9e-16`、`signs = 643 134 36`。

---

## 6. 修订后仍待处理

| 优先 | 项 |
|---|---|
| **高** | 48 处 `UNTRACEABLE` 数字逐项处置（见 `stale_number_audit.md`） |
| **高** | Fig.1–6 按新口径重绘（须含 E3 与更正后的机制） |
| **高** | WP5 敏感性与极端事件结果并入 |
| 中 | 参考文献与 Data/Code Availability 定稿（用 A29 的双注册库校验） |
| 中 | 模拟审稿意见与逐条答复 |
| 中 | 投稿前的期刊匹配评估（**据实**，证据不足则降级） |
