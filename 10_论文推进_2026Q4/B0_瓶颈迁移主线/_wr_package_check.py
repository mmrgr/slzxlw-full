# -*- coding: utf-8 -*-
"""投稿包完整性检查：文件是否齐备、格式是否合规。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def wc(p: Path) -> int:
    s = re.sub(r"\$[^$]*\$", " MATH ", p.read_text(encoding="utf-8"))
    return len(s.split())


def main() -> None:
    MS = HERE / "04_wr_manuscript_en.md"
    SI = HERE / "05_wr_supplementary_en.md"
    HL = HERE / "05_wr_highlights_en.txt"
    GA_PDF = HERE / "figs" / "GraphicalAbstract.pdf"
    GA_PNG = HERE / "figs" / "GraphicalAbstract.png"
    GUIDE = HERE / "_wr_guide" / "WR_guide_for_authors_20240423.txt"
    PLAN = HERE / "35_WR改编规划.md"
    SUMMARY = HERE / "36_第八轮工作总结.md"

    for p, label in [(MS, "英文正文"), (SI, "SI"), (HL, "Highlights"),
                     (GA_PDF, "GA PDF"), (GA_PNG, "GA PNG"),
                     (GUIDE, "官方指南存档"), (PLAN, "改编规划"), (SUMMARY, "轮次总结")]:
        ck(f"存在：{label}", p.exists(), f"{p.stat().st_size:,} B" if p.exists() else "缺失")

    if not MS.exists():
        return

    text = MS.read_text(encoding="utf-8")
    n = wc(MS)
    ck("正文含参考文献 ≤ 8000 words（官方硬限）", n <= 8000, f"{n}")
    ck("目标 ≤ 7700 words（留余量）", n <= 7700, f"{n}")

    # 官方格式：不得有行号
    ck("无行号（官方禁止）", not re.search(r"^\s*\d+\s{2,}\S", text, re.M), "")

    # 必备节
    for head in ["Nomenclature", "Abstract", "1. Introduction", "2. Material and methods",
                 "3. Results", "4. Discussion", "5. Conclusions", "References"]:
        ck(f"含必备节：{head}",
           re.search(r"^##\s+" + re.escape(head) + r"\s*$", text, re.M) is not None, "")

    # AI 声明（官方强制）
    ck("含生成式 AI 使用声明（官方强制）",
       "Declaration of Generative AI" in text, "")

    # 摘要
    m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", text, re.M | re.S)
    if m:
        ab = m.group(1)
        ck("摘要 ≤ 250 words", len(re.sub(r"\$[^$]*\$", " MATH ", ab).split()) <= 250,
           f"{len(re.sub(r'\\$[^$]*\\$', ' MATH ', ab).split())}")

    # Highlights
    if HL.exists():
        items = [ln.strip().lstrip("-•* ").strip()
                 for ln in HL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        ck("Highlights 3–5 条", 3 <= len(items) <= 5, f"{len(items)}")
        ck("Highlights 每条 ≤ 85 字符", all(len(i) <= 85 for i in items),
           ",".join(str(len(i)) for i in items))

    # 无中文残留（正文）
    body_no_refs = re.sub(r"^## References\s*$.*", "", text, flags=re.M | re.S)
    ck("正文无中文残留", not re.search(r"[\u4e00-\u9fff]", body_no_refs), "")

    # 待填占位符必须显式可见（投稿前由作者补齐）
    ph = re.findall(r"\[To be completed by the authors[^\]]*\]", text)
    # 2026-10-19 审计修复：原为 ck(..., True, ...) 恒真 —— 占位符即使被误删也照样过。
    # 该检查的真实含义是"占位符尚未被擅自填成 AI 代拟内容"，故断言其存在且 ≥1。
    ck("作者待填项已显式标注（供作者补齐）", len(ph) >= 1, f"{len(ph)} 处占位符")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\n投稿包完整性　通过 {npass}/{len(RES)}")
    print("=" * 68)
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    print("=" * 68)
    print("完整" if npass == len(RES) else f"缺 {len(RES)-npass} 项")
    # 2026-10-19 审计修复：补正确退出码（此前无 sys.exit，失败被父门禁静默吞掉）。
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
