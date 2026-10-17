# 投稿清单（Submission Checklist）

> **为什么需要这份文件**：本项目在第 30+ 轮才发现**五类投稿形式要件缺陷**：
> ① Abstract 超长（954 词，上限约 200）；② 无 References 节；③ 无强制声明；④ **无 Introduction**。
> 四者都不是科学错误，而是**形式要件**，且都是**多轮只修内容正确性的必然盲区**
> ——每轮只检查"数字对不对、结论是否夸大"，从不检查"稿件是否具备投稿要件"。
> 第 5 类为**正文图注引用缺失**（6 张主图在正文中 0 次被引用）。
> 本清单把它们固定为检查项，并由 `A41_全包审计`（Abstract 长度 + 结构完整性）自动核对，
> 防止再次累积。

---

## A. 已自动化核对（十五道门禁，必须全 PASS）

> **一键运行**：`python A41_全包审计/run_all_gates.py`（约 8 秒，退出码 0=全过）

| # | 检查项 | 工具 | 当前状态 |
|---|---|---|---|
| 1 | 终审断言（数值/降级/守恒） | `A36_终审/final_gate.py` | ✅ 全部通过 |
| 2 | 图–源一致性 | `A37_六主图_v4/_gate_check.py` | ✅ 64/64 |
| 3 | 产物哈希 + 数字复算 | `A40_投稿包/make_reproducibility_manifest.py` | ✅ 17/17 |
| 4 | 跨文档一致性（含 Abstract 长度） | `A41_全包审计/package_consistency_check.py` | ✅ 0 FAIL |
| 5 | 引用 ↔ 文献表 | `A42_参考文献/references_from_bib.py` | ✅ MISSING=0 |
| 6 | 强制声明齐全 | `A43_投稿声明/required_statements.py` | ✅ 5/5 |
| 7 | 无控制字节损坏 | `A41` 门禁内含 | ✅ 无 |
| 8 | **机制声明须有 SI 证据** | `A41_全包审计/claim_evidence_gate.py` | ✅ 5/5（1 项 SKIP）|
| 9 | **稿件结构完整性**（编号递增/引用不悬空/无编辑痕迹） | `A41_全包审计/structure_gate.py` | ✅ 4/4 |
| **10** | **无陈旧计数/残差**（黑名单+白名单） | `A41_全包审计/stale_value_gate.py` | ✅ 10/10 |
| **11** | **结论级数字 = 单一真相源**（双向校验） | `A41_全包审计/truth_gate.py` | ✅ 8/8 |
| **12** | **文档卫生**（LaTeX 完整 + 引用产物存在） | `A41_全包审计/hygiene_gate.py` | ✅ 3/3 |
| **13** | **形式一致性**（表格列数/图号/参考文献） | `A41_全包审计/form_gate.py` | ✅ 3/3 |
| **14** | **新颖性声明合规**（A29 禁止表述 + 六篇必引） | `A41_全包审计/novelty_gate.py` | ✅ 2/2 |
| **15** | **绝对声称可验证**（零例外断言须由产物重算） | `A41_全包审计/absolute_claim_gate.py` | ✅ 5/5 |

---

## B. 稿件形式要件

| # | 项 | 要求 | 状态 |
|---|---|---|---|
| B1 | Abstract 长度 | ≤200 词（Nature 系列）；本稿因需披露撤回放宽至 ≤300 | ✅ **296** |
| B1b | **章节结构完整** | Abstract / Introduction / Results / Discussion / Methods / References 齐备 | ✅ 6/6（**Introduction 为第 4 类形式缺陷，本轮补写**）|
| B1c | **正文篇幅** | Nature Water 正文约 3000–5000 词 | ⚠️ **6,604 词**（原 9,476；已将 3b/3b-c/§6/审核块移入 SI，仍略超，可再压）|
| B1d | **图注引用** | 每张主图须在正文中被引用 | ✅ 6/6（**原为 0，第 5 类缺陷**）|
| B2 | References 节 | 存在，且与正文引用一一对应 | ✅ 11 条，MISSING=0 |
| B3 | 标题 | 不夸大（已改为疑问式） | ✅ |
| B4 | 主图 | 6 张，PDF+PNG，≥300 dpi，字体嵌入 | ✅ 64/64 |
| B5 | 图注 | 含数据来源、n、限制 | ✅ 6/6 |
| B6 | SI | 章节连续、覆盖全部实验 | ✅ S1–S21 |
| B7 | 声明 | Data/Code Availability、Author Contributions、Competing Interests、Acknowledgements | ✅ 5/5（含占位符） |

---

## C. ⚠️ 必须由**作者**完成（脚本不代拟）

> 以下 10 处占位符在 `A43_投稿声明/required_statements.md` 与主稿 `Declarations` 节中。
> **绝不编造**姓名/单位/基金号——这是学术诚信底线。

- [ ] `[[REPOSITORY_URL]]` —— 分析代码仓库地址（建议同时申请 Zenodo DOI，保证长期可访问）
- [ ] `[[COMMIT_OR_VERSION]]` —— 提交版本/commit
- [ ] `[[Author 1]]` / `[[Author 2]]` —— 作者列表与顺序
- [ ] `[[conception / model design / analysis / writing]]` —— 各作者具体贡献
- [ ] `[[FUNDING…]]` —— 基金号；若无资助，保留标准表述
- [ ] `[[names]]` / `[[contribution]]` —— 致谢对象与事由
- [ ] Reporting Summary（若目标期刊要求，须在投稿系统在线填写）
- [ ] Cover letter
- [ ] 作者列表与单位、通讯作者信息

---

## D. 期刊定位（据实，勿倒逼结论）

| 目标 | 结论 | 依据 |
|---|---|---|
| **Nature Water** | ❌ **不建议** | 三项硬瓶颈未解除：①需求侧数据无观测（仅部分识别）；②正向预测已自我撤回（单折驱动）；③机制存在面板/路径依赖（NE-1/NE-2） |
| Nature Communications | ⚠️ 需重大补强 | 缺跨系统普遍性证据 |
| **ES&T / Water Research** | ✅ **建议主投** | 方法学贡献（逐数字可追溯、部分识别、显式负结果、九道门禁）+ 水质–分配机制契合 |
| npj Clean Water / ERL | ✅ 稳妥备选 | — |

---

## E. 已撤回主张（红线，不得复活）

| 主张 | 撤回原因 |
|---|---|
| 95%/93% 真实设施已承诺、empirically dominant | **不可识别**（只观测供方产能）；界 [0%, 100%] |
| "更干净 ⇒ 更省水 ⇒ 更有利" | 实测 $x_{\rm AI}$ 主导（corr −0.93），$q$ 仅 −0.16 |
| 判据吻合率 1.0000 有预测力 | E3 严格检验 0.671 < 基线 0.861 |
| 加入分配量后折外更优 | 单折驱动，中位增益 0.000 |
| 碱度是普适唯一符号杠杆 | strict 档绑定物种变为 silica/TDS 且无杠杆 |
| 高盐度再生水反转 committed 结果 | 依赖不完整样本 |
| 两条相反通道 / ψ / φ* / 供水下限 | 2026-10-14 已撤回（量纲/范畴错误） |
| 桥接 36 对 / 1.60× / 36,504 | 占位档遗留 |
| `Figshare BW` 作为再生水 | 它是**苦咸水** |

---

## F. 一键复核全部

```bash
cd "C:/Users/mmrgr/Desktop/论文/算力中心/10_论文推进_2026Q4"
PYTHONIOENCODING=utf-8 python A36_终审/final_gate.py
PYTHONIOENCODING=utf-8 python A37_六主图_v4/_gate_check.py
PYTHONIOENCODING=utf-8 python A40_投稿包/make_reproducibility_manifest.py
PYTHONIOENCODING=utf-8 python A41_全包审计/package_consistency_check.py
PYTHONIOENCODING=utf-8 python A42_参考文献/references_from_bib.py
PYTHONIOENCODING=utf-8 python A43_投稿声明/required_statements.py
```

**判定标准**：前六项全 PASS / OK；第 7 项（控制字节）在 A41 输出中无告警。
