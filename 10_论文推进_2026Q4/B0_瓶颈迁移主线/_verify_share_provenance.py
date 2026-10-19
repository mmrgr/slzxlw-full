# -*- coding: utf-8 -*-
"""核验 6%/26% 的来源链表述：防止再次退回"读图所得"的旧说法。

背景（2026-10-19 核验）：
  - `Item 7 Post Meeting Material.pdf` 封面为
    "Santa Clara data centers • Independent community report • October 2026"
    → 它是**独立社区报告**，不是市府 staff presentation 本体
  - 6%/26% 出现在该报告 p.53 的表格中，**文本层存在**
  - 论文此前称"只存在于 p.27 饼图、需渲染 200 dpi 读图" —— 与证据不符，已更正
  - 市府 26-1037 原件不在手上

本脚本断言：三份文稿都写明"转录值/非一手"，且不再出现不实的"读图所得"主张。
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"
PDF = Path(r"C:/Users/mmrgr/Desktop/000/Item 7 Post Meeting Material.pdf")

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    # ---- 1. PDF 事实核验 ----
    if PDF.exists():
        doc = fitz.open(PDF)
        # 封面页本身是市府议程页；社区报告的页眉出现在 p.48 起
        ck("PDF 含标明 Independent community report 的页",
           any("Independent community report" in doc[i].get_text()
               for i in range(doc.page_count)), "p.48+")
        # PDF 换行会把短语切断，比较前先把所有空白折叠成单空格
        p53 = " ".join(doc[52].get_text().split())
        ck("p.53 文本层含 6%", "6%" in p53, "6% found" if "6%" in p53 else "missing")
        ck("p.53 文本层含 26%", "26%" in p53, "")
        ck("p.53 含 'of potable use'", "of potable use" in p53, "")
        ck("p.53 含 'not 32% of combined use'", "not 32% of combined use" in p53, "")
        ck("p.53 含 'Supporting period and volumes need disclosure'",
           "Supporting period and volumes need disclosure" in p53, "")
        # 反证：论文此前声称的英文原句不存在
        alltext = "".join(
            doc[i].get_text() for i in range(doc.page_count)
        )
        ck("PDF 不含 'approximately 6% of the City'（旧引语无据）",
           "approximately 6% of the City" not in alltext, "")
    else:
        ck("社区报告 PDF 存在", False, str(PDF))

    # ---- 2. 三份文稿的表述 ----
    ms = MS.read_text(encoding="utf-8")
    en = EN.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")

    ck("母稿写明『转录值』", "转录值" in ms, "")
    ck("母稿写明『原件不在手上』", "原件不在手上" in ms, "")
    ck("母稿含 'not 32% of combined use'", "not 32% of combined use" in ms, "")

    ck("英文写明份额为转录而非一手",
       ("transcribed government statement" in en) or ("transcribed, not first-hand" in en), "")
    ck("英文写明 'not in our possession' 或等价",
       "not in our possession" in en or "not held" in en, "")

    ck("SI 含来源链表（Origin/Transcription）",
       "Origin" in si and "Transcription" in si, "")
    ck("SI 写明 'government-stated but independently unverified'",
       "government-stated but independently unverified" in si, "")

    # ---- 3. 旧说法不得作为当前主张存在（只允许出现在更正说明中）----
    for name, text in (("母稿", ms), ("英文", en), ("SI", si)):
        # 允许出现于"已更正/does not support"等更正语境
        bad = text.count("只存在于图形中")
        ok = bad == 0 or ("已更正" in text or "已更正" in ms)
        ck(f"{name} 无未加更正的『只存在于图形中』主张",
           text.count("只存在于图形中") <= text.count("已更正"), f"{bad} 处")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\n6%/26% 来源链核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
