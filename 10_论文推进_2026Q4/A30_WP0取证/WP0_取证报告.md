# A30 · WP0 取证与阻断问题报告（2026-10-16）

> 目的：对 GPT 评审意见（`C:\Users\mmrgr\Desktop\GPT意见2.txt`）中的指控做**独立复核**，
> 只采纳有仓库证据支撑者，并修正 GPT 自身的误判。
> 本文件是**唯一**的 WP0 结论出处；下游改写主稿须引用本文件的行号。

---

## 0. 一句话结论

GPT 四项指控中 **3 项成立、1 项为 GPT 自身误读**。两项被判为**阻断性（P0）**并已在本轮修复/定性：
**A24b 需求侧外推**（实证主张须撤回）与 **A21 溶质闭合门禁空洞通过**（根因是取错列名）。

---

## 1. 逐项复核（Lead 独立核查，非采信 GPT 叙述）

| # | GPT 指控 | 独立核查方法与证据 | 裁定 |
|---|---|---|---|
| 1 | A20 桥接"24 组 vs 36 组"证据冲突 | `wc -l A20_模型桥接/bridging_comparison_v2.csv` = 49 行（24 对）；`bridging_summary_v2.json` `n_pairs=24`、`sign_agreement=0.9583333`、`M0_median_rel_diff=5.08e-16`；`a20b_repro_log.txt` 明示 `dS_pot 符号一致率 = 0.958 (23/24)`。**且主稿 L521–L525 本身就把 36 组写作"已撤回的早期陈述"**（因该 CSV 生成于 2026-10-14，早于 A27 限值切换） | ⚠️ **GPT 误判**：这不是未解决的遗漏冲突，而是**已披露的撤回**。但主稿 L516 附近同时残留旧叙事，需统一口径。**现存 24 对结果有效** |
| 2 | A24 的"95% 真实设施已承诺"缺需求侧证据 | 读 `A24_外部锚定/external_validity.py`：L37–44 用 A17 反解阈值（33.4/30.7 ML/d），L92–97 以"实际处理量×r < 阈值"判 `committed`，L115–119 直接称其"支持中心结论的现实相关性"；`external_validity_summary.json` 的 `headline.committed_ha_pct=97.857` | ✅ **成立，且为 P0**。见 §2 |
| 3 | 主稿残留 R²=0.557 | 主稿 L418、L425 确为 0.557；权威产物 `A15_稳健性/holdout_summary.json`：`co_R2_phi_eff=0.8055937188186029`、`trivial_baseline_R2=-0.07328387812300985` | ✅ **成立**，陈旧数字。见 §3 |
| 4 | 两条水质路径 CoC 1.82 vs 7.98 的结构分歧 | `A21_动态状态/path_divergence_summary.json` 复现比值 4.4978（`coc_volume_only_measured=1.77`、`coc_r10a_measured=7.98`）；且 `dynamic_state_summary.json` 中 **`solute_closure_max_abs_kg: NaN`** | ✅ **成立，且比 GPT 所述更严重**。见 §4 |

**GPT 未指出、由本轮新增的两点**：
- (a) 核心恒等式 $dS_{\rm pot}=C-F$ 已被项目自身降级为"记账约定"（`21_工作交接.md` L28），GPT 的"代数重排"判断正确，但**不能因此丢弃**——其价值在反例与边界识别，不在"定律"。
- (b) 唯一在恒等式之外站得住的候选核心是 **A23 的闭式 $q>0 \iff \mathrm{CoC}_1>\mathrm{CoC}_0$**，因为它是可用**干预前可观测量**检验的机制式。

---

## 2. 【P0-1】A24b 需求侧外推：从"点估计"降级为"不可识别"

### 2.1 逻辑缺陷
设厂 $i$：$D_i$ = 可交付再生水上限 = 处理量$_i$ × $r$（**已观测**，供方）；
$E_i$ = 既有用户已承诺需求（**完全未观测**，需方）。

原判据 `处理量×r < 阈值 ⇒ committed` 实际只比较了 $D_i$ 与一个由合成域反解的阈值，
**与 $E_i$ 无任何蕴含关系**。反例：小厂 $D_i=1$ ML/d 而 $E_i=0.1$ ML/d ⇒ 池子大部分闲置（surplus），
但原脚本仍判 committed。故该判据**不是**对真实竞争状态的观测。

### 2.2 正确结论
物理约束仅给出 $0 \le E_i \le D_i$，对任意厂两种分支状态都可能出现 ⇒
**committed 占比可证明界 $= [0\%, 100\%]$（不含信息）**，即**不可识别**。
原报的 97.857% 是"特定假设下的情景比例"，**不是**经验频率。

### 2.3 已执行产物
- 脚本：`A30_WP0取证/a24b_partial_identification.py`
- 结果：`a24b_partial_id_summary.json`、`a24b_capacity_table.csv`、`a24b_partial_id_log.txt`
- **可识别替代量**（产能可行性，与需求侧无关，故严格成立）：

| r | HA ≥first% | HA ≥half% | CO ≥first% | CO ≥half% |
|---|---|---|---|---|
| 1.0 | 5.99 | 5.37 | 6.55 | 5.34 |
| 0.8 | 4.50 | 4.05 | 5.07 | 4.01 |
| 0.5 | 2.14 | 1.88 | 2.48 | 1.88 |
| 0.3 | 0.88 | 0.79 | 1.04 | 0.79 |
| 0.2 | 0.47 | 0.39 | 0.54 | 0.39 |

### 2.4 主稿必须执行的改写
- **删除/改写**：`above 95% of real facilities are fully committed`（主稿 L43）、
  `above 93% across the entire plausible range`（L398）、`committed branch … empirically dominant`。
- **改为**：仅可声称 (i) 真实厂处理量分布高度右偏、大型厂为少数；
  (ii) 其中仅少数（约 2–6%，随 $r$）的**产水能力**足以支撑达到模型阈值的 surplus 型方案。
- 摘要（Abstract）相应句必须同步修改——该句是当前摘要中最强的实证主张。

---

## 3. 【P0-2】陈旧数字与内部一致性

| 位置 | 稿件值 | 权威产物值 | 裁定 |
|---|---|---|---|
| 主稿 L418 | `R² = 0.557` vs baseline −0.050 | `co_R2_phi_eff = 0.8056`；`trivial_baseline_R2 = −0.0733` | **STALE** ⇒ 应改为 0.806 / −0.073 |
| 主稿 L425 | `0.557 (0.5574 …vs 0.5582 unfiltered)` | 同上 | **STALE** |
| 主稿 L521–525 | 36 组叙述 | 实为**已撤回**说明；现行 24 对 | 与产物一致，**非冲突** |

完整逐数字核对见 `A30_WP0取证/stale_number_audit.md`（由 manuscript-auditor 产出）。

---

## 4. 【P0-3】A21 溶质闭合门禁空洞通过 —— 根因是"取错列名"

### 4.1 根因
`A21_动态状态/dynamic_state.py` L198 取：

```python
float(d.get("solute_balance_residual_kg_max_abs", pd.Series([np.nan])).max())
```

引擎 daily 输出**没有**该列，于是静默 fallback 得到 `NaN` ⇒
汇总里 `solute_closure_max_abs_kg: NaN`。**没有任何报错**，
流程上"闭合检查"被当作已完成 —— 正是本项目门禁第 4 条"门禁不得空洞通过"所禁止的情形。

### 4.2 引擎其实一直在算
daily 输出（100 列）中真实存在：

```
quality_solute_closure_residual_kg
quality_process_solute_closure_residual_kg
quality_solute_closure_TDS_kg / _TSS_kg / _BOD_kg
```

即**闭合量一直被引擎算出，却从未被 A21 读取**。

### 4.3 实测结果（`a21_solute_closure.py`，6 情景）
| 情景 | 路径 | 水量闭合残差 (ML) | 溶质闭合残差 (kg) | 相对残差 | 裁定 |
|---|---|---|---|---|---|
| ha, stor=0 | volume-only | 7.11e−15 | — | — | **NOT_IDENTIFIABLE**（引擎不输出该残差） |
| ha, stor=0 | R10a | 3.55e−15 | 6.82e−13 | 2.64e−20 | PASS |
| ha, stor=200 | R10a | 2.40e−14 | 1.46e−11 | 5.64e−19 | PASS |
| co, stor=0 | volume-only | 7.11e−15 | — | — | **NOT_IDENTIFIABLE** |
| co, stor=0 | R10a | 3.55e−15 | 9.09e−13 | 3.57e−20 | PASS |
| co, stor=200 | R10a | 2.53e−14 | 1.46e−11 | 5.71e−19 | PASS |

**最大相对残差 5.71e−19 ≪ 1e−9 ⇒ PASS**（按第 5 条门禁用相对容差，量级达 1e5 kg）。

### 4.4 关键区分（必须写进论文）
- **R10a 逐日路径**：溶质闭合到机器精度 ⇒ 其 CoC ≈ 8 的结果**有守恒支撑**，不是数值假象。
- **volume-only 路径**：引擎**根本不输出**该残差 ⇒ 其闭合是**"未曾检验"，而非"已通过"**。
- ⚠️ **既有全部主结论建立在 volume-only 之上** ⇒ 对主结论而言，
  **溶质守恒属"待验证项"，不得写成"已验证项"**。

> 本轮据此为 volume-only 路径补建独立守恒检验（WP3），这是把中心机制从"可信"推向"可证"的必要一步。

---

## 5. 门禁清单（本轮新增第 7 条）

1. 求解器状态白名单（`converged_unique` 等，勿用子串判断）
2. 语义表（chi 等跨表不得混用不同定义）
3. **代数关系不是正确性证据**
4. **门禁不得空洞通过**（空集/NaN/缺列均不得计为 PASS）
5. **大数量级用相对容差**（≥1e10 的量禁绝对容差）
6. 扫描器要精确（按语义白名单，不按子串猜测）
7. **【新】外部数据的"可观测性"必须与结论的"识别性"匹配**：不得用供方可观测量
   （处理量、产能、负荷率）去断言需方状态（合同、已承诺需求、竞争状态）。
   无法识别时报告**可证明的界**，不得报告点估计。

---

## 6. 复现命令

```bash
cd "C:/Users/mmrgr/Desktop/论文/算力中心/10_论文推进_2026Q4/A30_WP0取证"
PYTHONIOENCODING=utf-8 python a24b_partial_identification.py   # ~2 s
PYTHONIOENCODING=utf-8 python a21_solute_closure.py           # ~25 s
```

## 7. 未解决 / 下一步

- [ ] volume-only 路径的溶质守恒**独立补验**（WP3 首要项）
- [ ] 主稿 Abstract / Results §6b 按 §2.4 改写（须与 manuscript-auditor 的清单合并执行）
- [ ] A20 桥接 24 对结果在**引用限值**下重跑一次以确认（当前 v2 为 2026-10-15 生成，晚于 A27，应已合规，但需显式记录）
- [ ] 文献核验结论合并（`A29_文献核验/`）
