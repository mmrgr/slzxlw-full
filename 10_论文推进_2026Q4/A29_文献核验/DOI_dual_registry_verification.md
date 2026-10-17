# 参考文献双注册库核验（2026-10-16）

> 目的：闭合 A29 文献核验提出的 **CI 陷阱**——单一 CrossRef 校验会把 arXiv/LBNL 的
> DOI **误判为无效**。本项目引用库含 4 个此类 DOI，必须用 **DataCite** 解析。

---

## 1. 引用库概况

`references.bib` 共 **24** 条，DOI 前缀分布：

| 前缀 | 数量 | 注册库 | 备注 |
|---|---:|---|---|
| 10.1038 | 6 | CrossRef | Nature 系列 |
| 10.1016 | 7 | CrossRef | Elsevier |
| 10.1021 | 2 | CrossRef | ACS |
| 10.5281 | 1 | **DataCite** | Zenodo（Shen 2026 复现包） |
| 10.48550 | 3 | **DataCite** | arXiv 预印本 |
| 10.71468 | 1 | **DataCite** | LBNL 报告 |
| 10.5194 / 10.1088 / 10.1007 / 10.3390 | 各 1 | CrossRef | — |

⇒ **共 5 条走 DataCite**（10.5281×1 + 10.48550×3 + 10.71468×1）。

---

## 2. DataCite 独立核验结果（本轮实测）

| DOI | DataCite HTTP | 标题 | 年份 | 类型 |
|---|---|---|---|---|
| `10.48550/arxiv.2603.02705` | **200** | *Small Bottle, Big Pipe: Quantifying and Addressing the Impact of Data Centers on Public…* | 2026 | Preprint (arXiv) |
| `10.48550/arxiv.2609.25437` | **200** | *Small Bottle, Big Pipe: Quantifying and Addressing the Impact of Data Centers on Public…* | 2026 | Preprint (arXiv) |
| `10.48550/arxiv.2606.21760` | **200** | *AI Data Centers and the Water Use Feedback Loop* | 2026 | Preprint (arXiv) |
| `10.71468/P1RP4F` | **200** | *United States Data Center Energy Usage Report: 2025 Update* | 2026 | Report (LBNL) |

**全部 4 条解析成功（HTTP 200）**，元数据完整。

---

## 3. ⚠️ 发现的问题（须处理）

### 3.1 两条 arXiv 条目**标题相同**
`10.48550/arxiv.2603.02705` 与 `10.48550/arxiv.2609.25437` 的标题**完全一致**
（*Small Bottle, Big Pipe…*），仅 arXiv 编号不同。

**可能原因**：(a) 同一工作的两个版本（v1/v2 各自注册了 DOI）；(b) 元数据错误；
(c) 确有同题不同作者的独立投稿。

**处置**：**不得**在稿件中同时引用两条同题文献。须由人工确认二者关系后：
- 若为同一工作的不同版本 ⇒ **合并为一条**，并标注版本；
- 若确为不同工作 ⇒ 必须在正文中显式区分（否则审稿人会视为引用错误）。

> 状态：**待人工确认**。在此之前，稿件中对这两条的引用应谨慎处理。

### 3.2 预印本不得当作已发表结果
上述 3 条 arXiv 均为 **Preprint**，LBNL 为 **Report**。
引用时**不得**表述为"已发表/经同行评审"，且凡涉"首次"主张处应带 *to our knowledge*。

---

## 4. 门禁追加（第 12 条）

> **【新】DOI 校验必须双注册库并行。**
> CrossRef **不含** arXiv(`10.48550/*`)、Zenodo/LBNL(`10.5281/*`, `10.71468/*`) 等 DOI；
> 若 CI/门禁只用 CrossRef，会把预印本与数据/报告 DOI **误判为无效**并错误阻塞投稿。
> 校验流程应为：先 CrossRef，再 DataCite，任一 200 即视为有效，并记录命中的注册库。

---

## 5. 复现

```bash
# CrossRef（大部分期刊 DOI）
curl -s -o - -w "\nHTTP:%{http_code}\n" "https://api.crossref.org/works/10.1038/s44221-026-00727-5"
# DataCite（arXiv / Zenodo / LBNL）
curl -s -w "\nHTTP:%{http_code}\n" "https://api.datacite.org/dois/10.48550/arxiv.2606.21760"
curl -s -w "\nHTTP:%{http_code}\n" "https://api.datacite.org/dois/10.71468/P1RP4F"
```

---

## 6. 仍未闭合

| 项 | 状态 |
|---|---|
| 两条同题 arXiv 条目的关系确认 | **待人工确认** |
| 其余 19 条 CrossRef DOI 的逐条复验 | 由 A29 完成（24/24 报告有效）；本轮仅补验 DataCite 侧 |
| 引文网络追溯（谁引用了本项目相关工作） | 未做（无 Scopus/WoS 权限） |
| 是否遗漏关键竞争文献 | 无法证明"不存在"，措辞须带 *to our knowledge* |
