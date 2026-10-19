# -*- coding: utf-8 -*-
"""按官方 8,000 词（含参考文献）重排 35 号文档第 2 节预算。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DOC = HERE / "35_WR改编规划.md"

NEW = """## 2. 中文母稿 → WR 英文稿的章节映射

中文母稿 23,022 汉字（≈ 14,968 English words）。官方上限是**正文 + 参考文献 8,000 词**，扣除参考文献 520 词、图表标题 380 词、文首与文末杂项 250 词后，**正文可用 6,600 词** ⇒ 相对母稿压缩率 **55.9%**（不是 46.5%）。

### 2.1 正文词数预算（合计 6,600）

| 英文节 | 来源（中文母稿） | 中文字数 | 英文预算 | 处理方式 |
|---|---|---:|---:|---|
| Abstract（不计入 6,600，单列 250） | 摘要 | 1,331 | 250 | **重写**：六段 → 单段，无引用、无缩写 |
| 1 Introduction | §1.1–1.4 | 1,100 | **750** | 四小节合并为三段：问题 / 缺口 / 贡献与不主张 |
| 2 Material and methods | §3.1–3.8 + §2.2 | 1,994 | **1,450** | 六类 estimand 压成 6 行表；阈值 0.95 的设计理由压成 2 句；§3.6 网格口径整节进 SI |
| 3.1 Bottleneck migration | §5.1–5.5 | 1,547 | **800** | 保留首失效表与迁移序列；9 项干预压成 1 表 + 3 句 |
| 3.2 The r\\* threshold | §5.7.1–5.7.6 | 1,787 | **1,050** | **论证重心**；推导、四情形表、三条实证核验全保留 |
| 3.3 Endogenous bottleneck | §5.8.1–5.8.6 | 1,732 | **750** | 零效应区 + 混淆排除 + 双因素表；交叉验证细节进 SI |
| 3.4 Two-number city screen | §5.9.1–5.9.8 | 1,017 | **550** | k\\* 判据 + Santa Clara 两口径 + 加州 169 分布；标题避开 "case study" |
| 4 Discussion | §8 + §7 摘要 + §1.5/§1.6 | 2,723 | **1,050** | 三杠杆分野压成 300 词；文献坐标（Schwabe/Tran/Wang/Badruzzaman）保留 |
| 5 Conclusions | 新增（基于 §8.6） | — | **200** | **新写**，条目列表，**不得含文献引用** |
| **正文小计** | | | **6,600** | |

### 2.2 正文外计费项（合计 1,400）

| 组成 | 预算 | 说明 |
|---|---:|---|
| Title + Nomenclature + Keywords | 120 | Nomenclature 官方强制，放文首 |
| 图表标题与表注（5 图 + 3 表） | 380 | 随正文计 |
| References（15 条） | 520 | 约 35 词/条 |
| Data availability + Declaration of Generative AI + Acknowledgements | 130 | 官方要求三块 |
| **小计** | **1,150** | 连同正文 6,600 = 7,750，余 250 词 |

> Highlights（5×85 字符）为独立文件，不计入。

### 2.3 迁入 SI（不占正文）

| SI 节 | 来源 | 中文字数 | 内容 |
|---|---|---:|---|
| S1 | §2.1–2.3 | 556 | 三个反事实、六类 estimand 完整定义、无率定前提 |
| S2 | §4.1–4.4 | 647 | 结果 1（Q1 代谢响应）整体 |
| S3 | §6.1–6.3 | 668 | 结果 3（Q2 时间尺度）整体 |
| S4 | §7 全文 | 2,632 | 三杠杆专题章完整版（正文只留 300 词） |
| S5 | §9 全文 | 2,857 | 44 条局限清单 |
| S6 | §3.6 + §5.7.3c–5.7.6 细节 | ~1,200 | 网格口径协议、敏感性全表、三维核验原始数字 |
| S7 | §5.9 细节 | ~500 | Santa Clara 两套口径推导、eAR 交叉验证、k 清洗规则 |
| S8 | 附录 B | 181 | 数据可靠性警示（附录 A 删除） |

### 2.4 删除

- 附录 A（与旧稿关系）——投稿稿不应出现，移入内部文档。
- 全部"⚠️ 标题已按写作红线检查""本稿状态""（见 §x.x）"等过程标注与内部交叉引用。
- §1.5 的口径分离论证并入 §2.1 methods，不单独成节。
"""


def main() -> None:
    text = DOC.read_text(encoding="utf-8")
    start = text.index("## 2. 中文母稿")
    end = text.index("## 3. 六个必须")
    new = text[:start] + NEW + "\n---\n\n" + text[end:]
    DOC.write_text(new, encoding="utf-8")
    print("OK 第 2 节已按 8000 词（含参考文献）重排")
    print("长度:", len(new))


if __name__ == "__main__":
    main()
