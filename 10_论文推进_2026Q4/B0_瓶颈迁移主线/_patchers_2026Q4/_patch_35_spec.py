# -*- coding: utf-8 -*-
"""用官方核验后的规格替换 35_WR改编规划.md 的第 1 节。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DOC = HERE / "35_WR改编规划.md"

NEW_SEC1 = """## 1. 投稿规格（**已从官网原文核验**）

### 1.1 核验过程

`sciencedirect.com` / `elsevier.com` 直连与**经代理**（`127.0.0.1:7890`，出口 IP 23.237.196.226）均为 **HTTP 403**（Akamai Bot Manager，403 页 1.2 MB 挑战脚本）；`r.jina.ai` 因出口 AS 被拒（401 bad network reputation）。最终经 **Wayback Machine 存档**取得原文：

`http://web.archive.org/web/20240423181318/https://www.sciencedirect.com/journal/water-research/publish/guide-for-authors`（HTTP 200，415 KB）

存档文本落盘 `/tmp/_wr_wb.txt`。**以下条款为官方原文，不再是推测。**

### 1.2 官方硬约束（逐条摘录）

| # | 条款 | 官方原文（节录） |
|---|---|---|
| 1 | **正文全长含参考文献 ≤ 8,000 词** | "The total length of the manuscript including references **must not exceed 8000 words**." |
| 2 | 类型：Research Paper / Making Waves / Review；Review < 12,000 词；Making Waves ≤ 3,000 词 | Types of paper (a)(b)(c) |
| 3 | ⚠️ **不接受案例研究** | "Water Research **does not accept case studies**, unless it is a study that has a **wide impact on the industry**." |
| 4 | **Highlights 强制**，3–5 条，每条 ≤ 85 字符（含空格），**单独可编辑文件**，文件名含 "Highlights" | "Highlights are **mandatory** … 3 to 5 bullet points (**maximum 85 characters, including spaces**, per bullet point)." |
| 5 | **Conclusions 节强制**，**不得引文献**，建议条目列表 | "Conclusions section is **mandatory** … in form of a **bulleted list**. Conclusions **must not contain references**." |
| 6 | **Nomenclature 须列于文首**，须合 SI 单位 | "Nomenclature must be listed at the **beginning of the paper**…" |
| 7 | 关键词 ≤ 6；缩写须首次出现全称 | Keywords / Abbreviations 段 |
| 8 | 结构：Introduction / Material and methods / Results / Discussion / Conclusions；小节编号 1.1、1.1.1 | Article structure |
| 9 | **不得加行号**（出版方自动加） | "Please do **not** include line numbering" |
| 10 | 单盲审（single anonymized review） | Preparation 段 |
| 11 | **须声明生成式 AI 使用**，置于参考文献前独立小节 | "Declaration of Generative AI and AI-assisted technologies…" |
| 12 | Graphical abstract **可选但鼓励**；最小 **531 × 1328 px（h × w）**；96 dpi 下 5 × 13 cm 可读；TIFF/EPS/PDF/Office | Graphical abstract 段 |
| 13 | 摘要须独立可读，**避免文献引用**，避免缩写 | Abstract 段 |
| 14 | 表格须可编辑文本非图片；避免与正文重复 | Tables 段 |
| 15 | 无版面费 | "Water Research has no page charges." |

### 1.3 由此确定的词数预算（**本轮硬边界**）

官方口径是"正文 + 参考文献 ≤ 8,000 词"，**不是**正文 8,000 词。重新分配：

| 组成 | 预算（words） | 说明 |
|---|---:|---|
| Title / Nomenclature / Keywords | 120 | 术语表只收本文自造符号 |
| Abstract | 250 | 惯例上限 |
| 正文 1 Introduction → 5 Conclusions | **6,600** | 含各级标题 |
| 图表标题与表注（随正文） | 380 | 5 图 + 3 表 |
| References（15 条） | 520 | 约 35 词/条 |
| Data availability + AI 声明 + 致谢 | 130 | |
| **合计** | **8,000** | 目标实际 **7,700**，留 300 词余量 |

> Highlights 为独立文件，不计入 manuscripts 词数。

### 1.4 第 3 条带来的**结构风险与应对**（必须处理）

官方明说不接受 case study。本文 §5.9 是 Santa Clara 单城应用，若以"案例研究"姿态出现，可能被编辑直接拒。**应对：不写成 case study，写成"判据的可操作性演示 + 跨城市筛查"**——该节结论单位不是"Santa Clara 怎样"，而是"该判据只需两个公开数字即可筛出城市"，加州 169 个系统分布是这一点的证据。写作上：

- 节标题用 *Operationalising the criterion: a two-number city screen*，不用 "Case study"；
- 首句即声明产出是**可迁移的筛查程序**，Santa Clara 仅作代入示例；
- 单城结果与 169 系统分布**同节并列**，重心落在判据而非城市。
"""


def main() -> None:
    text = DOC.read_text(encoding="utf-8")
    start = text.index("## 1. 投稿规格")
    end = text.index("## 2. 中文母稿")
    new = text[:start] + NEW_SEC1 + "\n---\n\n" + text[end:]
    DOC.write_text(new, encoding="utf-8")
    print("OK 已替换第 1 节")
    print("新长度:", len(new), "字符")


if __name__ == "__main__":
    main()
