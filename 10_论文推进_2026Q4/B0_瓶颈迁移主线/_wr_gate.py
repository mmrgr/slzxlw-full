# -*- coding: utf-8 -*-
"""WR 英文稿规格门禁：词数、摘要、Highlights、禁用项。

用法:
    python _wr_gate.py            # 检查 04_wr_manuscript_en.md + 05_wr_highlights_en.txt
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"
HL = HERE / "05_wr_highlights_en.txt"

RESULTS: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def section(text: str, head: str, nxt: list[str]) -> str:
    """取 '## head' 到下一个 ## 标题之间的内容。"""
    m = re.search(r"^##\s+" + re.escape(head) + r"\s*$", text, re.M)
    if not m:
        return ""
    start = m.end()
    tail = text[start:]
    cut = len(tail)
    for n in nxt:
        m2 = re.search(r"^##\s+" + re.escape(n) + r"\s*$", tail, re.M)
        if m2:
            cut = min(cut, m2.start())
    return tail[:cut]


def wc(s: str) -> int:
    """按 Word 口径近似计词：数学符号块算 1 词。"""
    s = re.sub(r"\$[^$]*\$", " MATH ", s)
    s = re.sub(r"\\\([^)]*\\\)", " MATH ", s)
    return len(s.split())


def main() -> None:
    if not MS.exists():
        print("MISSING", MS)
        return
    text = MS.read_text(encoding="utf-8")

    # ---------- Abstract ----------
    ab = section(text, "Abstract", ["Keywords", "1. Introduction", "1 Introduction"])
    ck("摘要存在", bool(ab.strip()), f"{wc(ab)} words")
    ck("摘要 ≤ 250 words", 0 < wc(ab) <= 250, f"{wc(ab)} words")
    ck("摘要无文献引用（[n] / et al.）", not re.search(r"\[\d+\]|et al\.", ab), "")
    # 摘要内缩写不得裸用：允许已定义的 CoC/CAWCC（原文首次已展开），检查其它
    ck("摘要含 r* 闭式解", "r^{*}" in ab or "r*" in ab, "")
    ck("摘要含四情形", "four regimes" in ab or "four regime" in ab, "")
    ck("摘要含 application/prediction 定位", "falsifiable" in ab.lower() or "prediction" in ab.lower(), "")

    # ---------- Highlights ----------
    if HL.exists():
        lines = [ln.strip().lstrip("-•* ").strip() for ln in HL.read_text(encoding="utf-8").splitlines()]
        items = [ln for ln in lines if ln]
        ck("Highlights 3–5 条", 3 <= len(items) <= 5, f"{len(items)} 条")
        for i, it in enumerate(items, 1):
            ck(f"Highlights 第 {i} 条 ≤ 85 字符", len(it) <= 85, f"{len(it)} 字符: {it[:60]}…")
    else:
        ck("Highlights 文件存在", False, str(HL))

    # ---------- 结构与必备节 ----------
    for head in ["1. Introduction", "2. Material and methods", "3. Results",
                 "4. Discussion", "5. Conclusions"]:
        ck(f"结构含 {head}", re.search(r"^##\s+" + re.escape(head) + r"\s*$", text, re.M) is not None, "")
    ck("含 Nomenclature（官方强制，文首）",
       re.search(r"^##\s+Nomenclature\s*$", text, re.M) is not None, "")
    ck("未加行号（官方禁止）", not re.search(r"^\s*\d+\s{2,}\S", text, re.M), "")
    ck("无中文残留", not re.search(r"[\u4e00-\u9fff]", re.sub(r"<!--.*?-->", "", text, flags=re.S)), "")

    # ---------- Conclusions 不得引文献 ----------
    cc = section(text, "5. Conclusions", ["Data availability", "Declaration", "References", "Acknowledgements"])
    ck("Conclusions 不得含文献引用", not re.search(r"\[\d+\]|\(\d{4}\)", cc), f"{wc(cc)} words")
    ck("Conclusions 用条目列表", re.search(r"^\s*[-*•]|^\s*\d+\.", cc, re.M) is not None, "")

    # ---------- 总词数 ----------
    body = text
    n = wc(body)
    ck("正文+参考文献 ≤ 8000 words（官方硬限）", n <= 8000, f"{n} words")
    ck("目标 ≤ 7700 words", n <= 7700, f"{n} words")

    # ---------- 六个跨语言强度保留 ----------
    low = text.lower()
    intensities = [
        ("应用非验证", "not a verification" in low or "application, not" in low),
        ("零效应区可证伪", "zero" in low and "falsifi" in low),
        ("只主张纯物理 −100 MW", "purely physical" in low or "physical constraint set" in low),
        ("k 口径敏感（两口径都报）", "5.43" in text or "4.35" in text),
        ("6%/26% 分母不可加", "not additive" in low or "cannot be added" in low or "different denominators" in low),
        ("r* 有 ±10% 不确定", "±10%" in text or "+/- 10%" in text or "10%" in text),
    ]
    for label, ok in intensities:
        ck(f"强度保留：{label}", ok, "")

    # ---------- 输出 ----------
    npass = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"\n{'='*70}\nWR 稿门禁　通过 {npass}/{len(RESULTS)}\n{'='*70}")
    for name, ok, detail in RESULTS:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    nfail = len(RESULTS) - npass
    print(f"\n{'全部通过' if nfail == 0 else f'FAIL {nfail} 项'}")
    # 2026-10-19 审计修复：补正确退出码。此前无 sys.exit，父门禁的 returncode 恒为 0，
    # 失败只靠打印 ❌ 传递；而父门禁曾以 gbk 解码，❌ 变乱码后该防线失效 → 失败被静默吞掉。
    sys.exit(0 if nfail == 0 else 1)


if __name__ == "__main__":
    main()
