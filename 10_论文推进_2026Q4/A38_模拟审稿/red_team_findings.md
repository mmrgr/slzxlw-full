# 红队自审发现（Red-Team Self-Audit Findings）
## 审稿人未问、但审查中发现的新问题

> **范围**：`A38_模拟审稿/` 红队审查过程中，通过独立复算与跨文件核对发现的**新增**问题。
> **不含**任何已在 `reviewer_reports.md` 中由审稿人提出的条目（那些去 `response_to_reviewers.md`）。
> **纪律**：每条均引用**实际读取**的文件、行号或机器产物字段；按严重度排序。
> **统计**：`CRITICAL` **2** 条 · `MAJOR` **5** 条 · `MINOR` **6** 条。

---

# CRITICAL

## F-1. §3 头条表的容差口径矛盾，实际丢掉 **32 个有害案例**（不只是"近零"）

**发现路径**：我按 `A13_可靠性机制/supply_state_regimes.csv` 复算主稿 L164–168 的 $q$ 分组表。

**复算结果**：

| $q$ 组 | 主稿表内 n | 表内 falls | 表内 rises | **严格口径实际（负/正/零）** |
|---|---:|---:|---:|---|
| $q>0$ | 290 | 290 | 0 | 290 / 0 / 0 |
| $q\approx0$ | 288 | **208** | **0** | **220 / 32 / 36** |
| $q<0$ | 235 | 133 | 102 | 133 / 102 / 0 |
| **合计** | **813** | **631** | **102** | **643 / 134 / 36** |

表内 falls+rises = **733**，与表头 $n=813$ 差 **80 行**。

**新问题的关键（审稿人 2 只看到"口径不一致"这一表象）**：我进一步定位了这 80 行——

```python
nz = rel[rel.dS_pot_ml.abs() <= 1e-9]   # 80 行
nz.q 分布: {'q=0': 80}                   # 全部落在 q==0 组
其中 dS_pot_ml == 0 精确零: 36 行
其中 dS_pot_ml > 0 (有害):  32 行
按水样各 20 行: IEUA 20, LADWP 20, Figshare RW 20, AI-UWM 20
```

**即：被容差带丢掉的 80 行中，只有 36 行是真正的零，另有 32 行是 $dS_{\rm pot}>0$ 的明确有害案例。** 更巧的是，这 80 行**均匀分布在 4 个水样上（各 20 行）**，说明它们恰好是 `pool_scale` 扫描中"池充分大、挤占项归零"的格点。

**为何这是 CRITICAL**：
1. 主稿 L184–191 刚以加粗批评旧口径"silently drops 80 near-zero scenarios … while still labelling the sample as 813"，**然后本节表中原样复现该口径**——自我否定。
2. 表中 $q\approx0$ 行的"rises = 0"是**假象**：真实值 32。这直接削弱本文"$q>0$ 之外伤害集中在 $q<0$"的整个符号叙事。
3. 这 80 行正是 `pool_scale` 最大的一档，与 §3d 的 C4 判据（`pool_scale ≥ 2`）**高度重合**——意味着 §3 与 §3d 的表在样本上**不可比**。

**应改成什么**：见 `response_to_reviewers.md` M2-1 给出的严格三列表。

**审稿人是否发现**：审稿人 2 发现了"合计 733 ≠ 813"（M2-1），**但未发现丢失的 32 个是有害案例，也未发现 80 行按水样均匀分布**。这两点由红队自审补出。

---

## F-2. §3d 的"折外 0.901"在**排除不完整水样**后，增益结构完全改变——但作者从未做此分解

**发现路径**：审稿人 2 指出"增益由单折驱动"后，我进一步按**本文自己声明的可用子集**（仅 IEUA + LADWP 两个完整水样）重算留一验证。

**复算结果**：

| 范围 | $n$ | 多数类基线 | C4 准确率 | 折外均值 vs 基线 | 增益 |
|---|---:|---:|---:|---|---:|
| **全部 4 水样**（主稿口径） | 733 | 0.8594 | 0.9059 | 0.9009 vs 0.8594 | **+0.0415** |
| **仅 2 个完整水样**（声明可用子集） | **379** | **0.8734** | **0.9683** | **0.9694 vs 0.8776** | **+0.0918** |

逐折细节（完整水样子集）：

| 留出样本 | $n$ | C4 准确率 | 多数类基线 | 增益 |
|---|---:|---:|---:|---:|
| IEUA RP-1 | 196 | 0.9388 | 0.7551 | **+0.1837** |
| LADWP AWPF | 183 | 1.0000 | **1.0000** | **+0.0000** |
| **均值** | 379 | **0.9694** | **0.8776** | **+0.0918** |

**为何这是 CRITICAL**：
1. **两个口径给出方向一致的结论，但数量差 2.2 倍**（+0.0415 vs +0.0918），而**主稿报的是较弱的那个**——这本身说明作者没有做这个分解。
2. **但在完整水样子集上，LADWP 折的基线仍是 1.000**（183 例中 100% 受益），因此 **+0.0918 依然全部来自 IEUA 单折**。**即使换成"最干净"的口径，该结果仍是单折驱动。**
3. **完整水样子集只有 2 折**——留一验证在 2 折下**没有统计意义**（无法给方差）。
4. 主稿 L410–415 明确说"only complete-composition samples may be used for sign claims"（L174–175），**却把包含 2 个不完整水样的 0.901 当作正结果报在摘要**——口径双标。

**应改成什么**：摘要中同时报两个口径（+0.0415 全样本 / +0.0918 完整水样），并**明说两者都是单折驱动、2 折下无统计意义**。若不报，审稿人自然会算，且会认为作者在挑选口径。

**审稿人是否发现**：审稿人 2 发现单折驱动（M2-3），**未发现完整水样子集下的 +0.0918，也未发现该子集只有 2 折**。

---

# MAJOR

## F-3. 水样"物种数"存在**三套互相矛盾的口径**，且从未声明

**发现路径**：审稿人 2 指出 SI L253"5/5" vs A32 L89"9"冲突后，我追查全部来源。

**三套口径实测**：

| 来源 | IEUA | LADWP | Figshare RW | AI-UWM | 口径推测 |
|---|---:|---:|---:|---:|---|
| `A4_水化学参数域/T6_water_chemistry_samples.csv` :: `n_present` | **9** | **8** | 6 | 2 | 样本中**存在**的物种数 |
| `A32_WP3_水化学/WP3_水化学机制验证报告.md` L89–90 | **9** | **8** | 6 | 2 | 同 `T6` 的 `n_present`（一致 ✅） |
| `A33_WP4_组成重构/wp4_results.csv` :: `n_species` | **5** | **5** | — | — | **受约束物种数**（TDS/Cl/hardness/alkalinity/silica）？ |
| `A34_WP5_敏感性与极端环境/wp5_sensitivity_summary.json` :: `samples_authoritative` | **5** | **5** | 3 | 2 | 同 WP4 |
| `A16_英文稿/supplementary_information.md` L253 | **5/5** | **5/5** | 缺 2 | 仅 TDS+Cl | 同 WP4 |
| `A16_英文稿/manuscript_en_v3.md` L179–182 | **9 (complete)** | **9 (complete)** | 6 | 2 | **与 WP4/SI 冲突** |

**关键证据**——`T6_coc_limits.csv` 给出了权威解释：

```
source                            n_present  CoC_lim_engine_conservative  who_engine  CoC_lim_all_ratio  who_all_ratio  CoC_lim_phreeqc
IEUA RP-1 (2025, tertiary)            9          4.966140                   TDS          3.571429        alkalinity      2.520158
LADWP AWPF (2012, RO product)         8        100.000000                   TDS         70.422535        alkalinity    100.000000
```

**即：`n_present` = 9/8（全部物种），而受约束物种恒为 5。** 主稿 L179–182 用的是"9 (complete)"，SI L253 与 WP4/wp5 用的是"5/5"——**两者都在指"完整"，但数字不同，读者无法判断哪个是权威。**

**为何是 MAJOR**：
1. 本文最关键的**组成完整性判据**（决定哪些水样可用于符号主张，L174–175、L193–203）建立在这个数字上。**口径不明 ⇒ 判据不可审计。**
2. 更严重：`T6_coc_limits.csv` 显示 **IEUA 的"绑定物种"取决于所用判据**——`who_engine_conservative` = TDS（CoC 4.966）、`who_all_ratio` = alkalinity（3.571）、`who_precipitation` = alkalinity、`who_phreeqc` = **Calcite（2.520）**。**§7a 只用了 `who_all_ratio` 的碱度口径（2.500），完全没有讨论 TDS 口径与 PHREEQC 钙酸盐口径给出不同绑定物种这一事实。**

**应改成什么**：发布**权威物种计数口径表**（`n_present` vs `n_constrained`），统一全部文件；并在 §7a 补一段说明"绑定物种随判据而异（TDS / alkalinity / calcite）"，附 `T6_coc_limits.csv` 的四个 `who_*` 列。

**审稿人是否发现**：审稿人 2 只看到"5/5 vs 9"的表象（M2-6 第 5 项），**未发现这是三套口径、也未发现绑定物种随判据变化**。

---

## F-4. §7a 的"碱度比 2.500"与"动态临界 2.615×"之间，存在一个**未被解释的第 3 个数字**

**发现路径**：核对主稿 L548–563 与 `T6_coc_limits.csv`、`wp5_sensitivity_summary.json`。

三个数字：

| 数字 | 含义 | 来源 | 值 |
|---|---|---|---|
| **2.500** | 静态余量比 = limit/c | 主稿 L550；我复算 $350/140 = 2.500$ ✅ | 2.500 |
| **3.571** | `CoC_lim_all_ratio`（碱度口径的可达 CoC 上限） | `T6_coc_limits.csv` IEUA 行 | 3.571 |
| **2.520** | `CoC_lim_phreeqc`（PHREEQC 钙酸盐限制） | 同上 | 2.520 |
| **2.615** | 动态翻转临界（碱度浓度倍率） | 主稿 L545；`wp5` `first_flip_value_ha_IEUA` | 2.615 |

**主稿 L558–563 正确处理了 2.500 vs 2.615 的区分**（"a *static margin* … a *dynamic critical point* … must not be quoted interchangeably"）——**这一点做得好，我们不批评。**

**但主稿从未提及 3.571 与 2.520 这两个同样权威的 CoC 上限。** 而 **2.520 正是主稿 L418–419 用来锚定 0.50 质量档的那个 PHREEQC 值**（"0.50 = PHREEQC calcite-limited value for IEUA tertiary reclaimed water (2.52/5.0 = 0.504)"）——**即主稿同时使用了 2.520（作为 0.50 档锚点）与 2.500（作为静态余量），两个数字极为接近但含义完全不同，却从未对照说明。**

**为何是 MAJOR**：读者会合理地混淆 —— 2.500（limit/浓度余量比）、2.520（PHREEQC 钙酸盐 CoC）、2.615（动态翻转倍率）三者在同一小节相邻出现，量级几乎相同（2.50 / 2.52 / 2.62），**若不显式列表说明，等于制造混淆源**。

**应改成什么**：在 §7a 加一个小表，列出 2.500 / 2.520 / 2.615 三个数字的**名称、定义、单位、来源文件**，并明确三者不可互换。

---

## F-5. LADWP 全部 5 物种比值 ≥ 49.3，**没有任何质量约束**——本文存在一个"约束从不绑定"的域，其 Sobol 为 `NOT_IDENTIFIABLE`，但该域的**主网格情景仍被计入头条计数**

**发现路径**：复算限制/浓度比值（见下），并与主网格 813 行的水样分布对照。

**复算结果（我独立计算，与主稿 L550–555 完全一致）**：

| 物种 | IEUA c (mg/L) | 比值 | LADWP c (mg/L) | 比值 |
|---|---:|---:|---:|---:|
| TDS | 443.00 | 4.966 | 22.00 | 100.000 |
| chloride | 100.00 | 7.000 | 3.60 | 194.444 |
| hardness | 149.43 | 5.019 | 1.02 | 732.586 |
| **alkalinity** | **140.00** | **2.500** | 7.10 | **49.296** |
| silica | 24.00 | 7.292 | 0.52 | 336.538 |

主稿 L552–557 称 LADWP"every ratio is large (smallest 49.3), no species binds, and the quality constraint is **inactive across the sampled range**"——**这一陈述经我复算完全正确。**

**但由此产生的新问题（主稿未处理）**：`A13_可靠性机制/supply_state_regimes.csv` 的 813 行可靠子集中，**LADWP 占 203 行**（主稿 L179 表：186+8+9 = 203）。**这 203 行的质量约束从未绑定**，即它们的 $q$ 与 $M_0-M_1$ 恒等于 0 或接近于 0，$dS_{\rm pot}$ 完全由挤占项决定。**把这 203 行与 IEUA 的 216 行、以及两个不完整水样的行混在同一张头条表（L164–168）与同一个 $q$ 分组里，等于混合了"质量约束活跃"与"质量约束不活跃"两类物理上不同的系统。**

这与 SI §S2b（L98–112）对 `limit_scale` 的批评**完全同构**——SI 已经认识到名义档位与实际绑定脱钩，并为此新增了 `quality_binding` 列。**但本文没有把这个认识应用到"水样维度"上**：LADWP 在整个采样域内 `quality_binding ≡ False`。

**为何是 MAJOR**：这直接关系到 §7a"碱度是唯一杠杆"的解释力——**如果 203/813 = 25% 的情景中约束根本不绑定，那么"唯一杠杆"的检验其实是"在剩下的 75% 上做的"**，而主稿从未报出这个比例。

**应改成什么**：(i) 报出 813 行中 `quality_binding == True` 的行数；(ii) 头条表（L164–168）按 `quality_binding` 分层重报；(iii) §7a 明确"唯一杠杆"是在约束绑定的子集上识别的。

**审稿人是否发现**：审稿人 3 发现了名义档位与绑定脱钩（M3-3），**但未发现 LADWP 这一整个水样在其采样域内约束从不绑定**。

---

## F-6. 摘要 L47–48"changes its magnitude by at most 1.139× **without ever reversing it**"的因果方向被写反

**发现路径**：核对主稿 L47–48 与 `wp5_extreme_cases.csv` / `wp5_extreme_summary.json`。

**主稿原文（L47–48）**："while exposing the effect to observed heatwaves and droughts changes its magnitude by at most 1.139× **without ever reversing it**."

**主稿 §7b（L571–575）**："Under observation-driven extremes … the sign of $dS_{\rm pot}$ does **not** flip in **any** of 8 tests."

**复算事实**：观测驱动窗口下，**所有情景 $dS_{\rm pot} < 0$（有益）**，0 翻转 ✅。**但主稿在 §7b 末尾（L585–587）自己写了**："This is a **negative result reported as such**: within the observation-driven envelope, water scarcity and heat intensify the effect rather than reversing it."

**这里存在一个措辞上的因果混淆**：既然全部 64 个情景（含 full-year）**本来就都是负的**，那么"极端事件不翻转符号"这一事实**并不构成"极端事件不危险"的证据**——它只说明**在这个已经全部有益的样本里，没有出现翻转**。这与 §7b 的正面陈述风格（"Observed heatwaves do **not** by themselves curtail the data centre"）给读者的印象不符。

更关键：**`wp5_extreme_summary.json` 的 `gates.zero_value_convention` 是 `|dS_pot| < 1e-06 ML 记为 0`，而主网格用的是严格符号约定（无容差带）。极端事件实验使用了与主网格不同的零值约定**——这在 SI §S15 门禁 8（"Sign counts must declare the zero convention and the effective $n$"）下**必须声明，但主稿 L571–575 与 SI §S5 均未声明**。

**为何是 MAJOR**：极端事件的 0/8 是本稿摘要中的四项实证之一，若其零值约定与主网格不一致且未声明，则该结论与主网格不可直接比较。

**应改成什么**：(i) 在 §7b 明示零值约定 `|dS| < 1e-6`；(ii) 说明该实验的 64 个情景**全部为负**，因此"不翻转"是**在该有偏样本上的观察**，而非对"极端事件安全性"的一般结论；(iii) 摘要 L47–48 加限定"within the observation-driven envelope, in a sample in which all scenarios are already beneficial"。

**审稿人是否发现**：审稿人只对"1.139× 是 per-day 口径"提出质疑（M2/V13）；**零值约定不一致是本项自审新发现**。

---

## F-7. `pool_scale` 扫描轴上，`harm` 率在 2.0 与 1.5 之间**陡降 3 倍**，而该落差恰好被 C4 判据的阈值切中

**发现路径**：对我复算的 `pool_scale` × 有害率表与 C4 阈值（`pool_scale ≥ 2`）做交叉检查。

**复算结果**（`wp2_e3_predictions.csv`，$n_{\rm eff}=733$）：

| `pool_scale` | $n$ | 有害率 `harm` |
|---:|---:|---:|
| 0.5 | 61 | 0.262 |
| 1.0 | 61 | 0.377 |
| **1.5** | **76** | **0.303** |
| **2.0** | **87** | **0.103** |
| 2.2 | 87 | 0.080 |
| 2.4 | 89 | 0.067 |
| 2.6 | 90 | 0.067 |
| 3.0 | 91 | 0.066 |
| 4.0 | 91 | 0.066 |

**有害率在 `pool_scale` ∈ (1.5, 2.0] 区间内从 0.303 陡降至 0.103（约 3 倍）**，此后平缓。**C4 判据的阈值 `pool_scale ≥ 2` 恰好切在这个陡降带的上沿。**

**为何是 MAJOR**：C4 是本文唯一的正向预测结果（§3d），其阈值的**唯一性**与**有效性**同时取决于这个陡降带的位置。而陡降带本身是**模型分支结构的结果**（池足够大 ⇒ 挤占项归零 ⇒ 受益），正对应 §2 的 branch C 条件。**即：C4 本质上是一个"分支判别器"，其 0.906 准确率主要反映分支结构，而非新预测信息。**

**应改成什么**：在 §3d 明确给出该表（有害率 vs `pool_scale`），并说明"the discriminating power of the threshold concentrates in a single transition band (1.5 → 2.0), which coincides with the branch-C condition of §2"。**把 C4 定位为"分支判别的可操作形式"，而不是"独立预测器"。**

**审稿人是否发现**：审稿人 2 指出阈值是刀锋点（M2-4），**但未指出陡降带与 branch C 的结构对应，也未给出有害率分档表**。

---

# MINOR

## F-8. `A34_WP5_敏感性与极端事件/_probes_dev/` 存在未被文档引用的开发探针目录

**发现路径**：`ls A34_WP5_敏感性与极端事件/` 输出含 `_probes_dev`。

主稿 L770–772 的 Reproducibility 段声明"Environment locked … Superseded scripts are marked in place"。但 `_probes_dev/` 既未被 `A36_终审/终审门禁报告与期刊匹配评估.md` §6 交付物清单收录，也未被任何报告引用。**建议**：或纳入交付物清单并说明用途，或移入明确的审计留痕目录（如 `_audit_tmp/`）。

## F-9. `A37_六主图_v4/` 同时含 `_probe_q.py` / `_probe_signs.py` / `_probe_verify.py` / `_gate_check.py` 四个未文档化脚本

`figure_index.md` §3 提到"探针脚本 `_probe_verify.py` / `_probe_signs.py` / `_probe_q.py`"，但 `_gate_check.py` **从未在任何文档中被提及**。**建议**：在 `figure_index.md` §3 补全四个探针的用途与调用方式；`_gate_check.py` 的输出应登记为图件门禁证据。

## F-10. `SI §S3.0` 与 `SI §S2a` 对 1052 / 1152 两个总情景数**同一文件内并存但未调和**

- SI L171 表：`supply_state_regimes.csv (main grid)` = **1,152** 行
- SI L183 表：`scenarios` = **1,052**
- 主稿 L328：**1,152**；主稿 L731：**813**

`figure_index.md` §2 载 `supply_state_regimes.csv` 行数 **1,053**（= 1052 + 表头），与 1,152 不符。

**我在 `A13_可靠性机制/supply_state_regimes.csv` 上实测：total rows = 1052。** 因此 **SI L171 与主稿 L328 的"1,152"是 STALE**，而 SI L183 与图索引的 1,052 正确。**建议**：全文统一为 1,052，并修正 `figure_index.md` 的 1,053（含表头）表述歧义。

## F-11. `证据台账` §E"待闭合清单"已陈旧，与主稿现状不符

`A30_WP0取证/证据台账_EVIDENCE_LEDGER.md` §E（L105–114）仍把以下项标为"未开始/进行中"：

| 台账 §E 条目 | 台账状态 | 实际状态 |
|---|---|---|
| "独立预测检验（E3）：…**未开始**" | 未开始 | **已完成**（`A31_WP2_假设冻结/WP2_E3_独立预测检验报告.md`） |
| "组成维度重构 … **进行中**" | 进行中 | **已完成**（`A33_WP4_组成重构/WP4_报告.md`） |
| "全局敏感性 + 极端事件"（优先级"低"） | 低 | **已完成**（`A34_WP5_敏感性与极端事件/`） |
| "主稿 26 处 STALE + 48 处 UNTRACEABLE 处置" | 中 | **已完成**（`A36_终审` §2 已闭合 15/12/15） |

**证据台账是本文"数字可追溯"的核心承诺载体。若它本身滞后于事实，该承诺的说服力受损。** **建议**：按当前实际情况重写 §E，并加"最后更新"时间戳与对应提交 hash。

## F-12. 主稿 L1 标题为疑问句，而 SI L3 保留了旧陈述句标题 —— 二者语义方向相反

- 主稿 L1：**"What Governs the Urban Water Outcome of Reclaimed-Water Cooling in AI Data Centres? Competition, Water Chemistry and the Limits of Prediction"**（疑问式；"Limits of Prediction"）
- SI L3：**"Supply state, not cooling technology, governs the urban water outcome of reclaimed-water cooling in AI data centres"**（断言式；"Supply state, not cooling technology"）

**两标题不只是措辞不同，而是主张不同**：主稿标题强调"预测的极限"（呼应 §3d 的负结果），SI 标题强调"供给状态而非冷却技术决定结果"。**后者是一个更强的因果主张，而主稿正文（L608）只把 regime boundary 称作"measurable and exogenous"，并未主张"supply state 而非 technology 决定"。**

**建议**：SI 标题改为与主稿一致；若确实要保留"Supply state, not cooling technology"这一主张，则需在正文中为其提供证据（目前 §2 的两分支结构**不构成**"技术无关"的证明——技术通过 CoC 设计与 $\varphi$ 进入模型）。

---

# 附：审查方法与被否证的猜测（诚实记录）

为避免"只报对自己有利的发现"，此处记录红队审查中**提出但被证据否证**的猜测。

| # | 初始猜测 | 复算结果 | 裁定 |
|---|---|---|---|
| G-1 | "`pool_scale` 泄漏了 $x_{\rm AI}$，故 E3b 是自证" | `wp2_e3_independent_prediction_summary.json::forbidden_inputs` 明确排除 $x_{\rm AI},M_0,M_1,C,F,dS_{\rm pot}$；`pool_scale` 是网格**输入** | **猜测不成立**（但 C4 等价于 branch C 条件这一点成立，见 F-7 与 M2-4） |
| G-2 | "`q>0 ⇒ 受益` 完全空洞（无信息）" | 主网格 813 行上，独立期望有害 47.8 例、实测 0 例，Fisher $p\approx9.5\times10^{-22}$ | **猜测不成立**；空洞的是 47 例完整水样子集 |
| G-3 | "Fig. 6 仍在暗示 committed 占比" | 实际查看 PNG：Panel a 大字"NOT IDENTIFIABLE / [0%, 100%]"，无点估计、无 CI、无暗示性条形 | **猜测不成立**——Fig. 6 反而是诚实性最强的产物 |
| G-4 | "温度 −30% 位移有产物支持" | 在 `A32`/`A34`/`A4`/`证据台账` 中检索未找到出处 | **猜测不成立**（即该数字确实无出处，须删——此条转为批评 M3-4） |
| G-5 | "主稿 L548–563 混淆了静态余量与动态临界" | 实际阅读 L558–563：主稿**显式区分**二者并警告"must not be quoted interchangeably" | **猜测不成立**——此处处理正确，不应批评 |

**记录理由**：本项目的核心价值主张是"可复核的诚实"。红队若只罗列批评而不公开被否证的猜测，就与该主张相反。**上述 5 条中有 4 条被否证，说明本稿在这些点上经得起对抗性检验。**
