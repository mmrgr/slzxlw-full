# -*- coding: utf-8 -*-
"""提取 18 篇参考文献的标题/摘要/关键词/结论要点，输出到 _extract/。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf

SRC = Path(r"C:\Users\mmrgr\Desktop\算力中心论文")
OUT = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4\B0_瓶颈迁移主线\_lit_extract")
OUT.mkdir(parents=True, exist_ok=True)


def clean(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def head_region(doc: "fitz.Document", n_pages: int = 2) -> str:
    """前两页（标题+摘要+引言开头）。"""
    parts = []
    for i in range(min(n_pages, doc.page_count)):
        parts.append(doc[i].get_text("text"))
    return clean("\n".join(parts))


def find_section(doc: "fitz.Document", patterns: list[str], max_chars: int = 3000) -> str:
    """在全文里找指定小节的起始位置并截取其后文本。"""
    full = clean("\n".join(doc[i].get_text("text") for i in range(doc.page_count)))
    for pat in patterns:
        m = re.search(pat, full, flags=re.IGNORECASE)
        if m:
            return full[m.start(): m.start() + max_chars]
    return ""


index = []
for pdf in sorted(SRC.glob("*.pdf")):
    stem = pdf.stem
    try:
        doc = fitz.open(pdf)
        n = doc.page_count
        head = head_region(doc)
        abstract = find_section(doc, [r"\bAbstract\b", r"\bABSTRACT\b"], 2600)
        concl = find_section(
            doc,
            [r"\bConclusions?\b", r"\bConcluding remarks\b",
             r"\bDiscussion and conclusions?\b", r"\bSummary and conclusions?\b"],
            2600,
        )
        result = {
            "file": pdf.name,
            "pages": n,
            "title_guess": head.split("\n")[0][:220] if head else "",
            "head": head[:4200],
            "abstract": abstract,
            "conclusions": concl,
        }
        (OUT / f"{stem[:80]}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        (OUT / f"{stem[:80]}.txt").write_text(
            f"=== {pdf.name} ===\nPAGES: {n}\n\n"
            f"--- HEAD ---\n{head[:4200]}\n\n"
            f"--- ABSTRACT ---\n{abstract}\n\n"
            f"--- CONCLUSIONS ---\n{concl}\n",
            encoding="utf-8",
        )
        index.append({"file": pdf.name, "pages": n, "chars_head": len(head)})
        print(f"[OK] {pdf.name}  pages={n}")
        doc.close()
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {pdf.name}: {type(exc).__name__}: {exc}")

(OUT / "_index.json").write_text(
    json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8"
)
print(f"\n-> {OUT}")
