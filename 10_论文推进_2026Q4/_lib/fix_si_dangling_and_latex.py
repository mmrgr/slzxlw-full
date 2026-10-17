"""修正 SI 中的悬空文件名 + 被破坏的 LaTeX 转义 (2026-10-17).

问题1: 引用了不存在的 `A30_WP0取证/trace_untraceable_summary.json`,
       实际文件名是 `untraceable_traceability_summary.json` (词序颠倒)。
问题2: 同一段里 `$dS_{\\rm pot}$` 被破坏为 `$dS_{` + 换行 + `m pot}$` (\\r 被吃)。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SI = Path(__file__).resolve().parent.parent / "A16_英文稿/supplementary_information.md"
t = SI.read_text(encoding="utf-8")

PAIRS = [
    # 1. 文件名
    ("`A30_WP0取证/trace_untraceable_summary.json`",
     "`A30_WP0取证/untraceable_traceability_summary.json`"),
    # 2. 被破坏的 LaTeX (实际文本含换行)
    ("*(Columns are $dS_{\nm pot}<0$ / $>0$ / $=0$ over the reliable subset.",
     "*(Columns are $dS_{\\rm pot}<0$ / $>0$ / $=0$ over the reliable subset."),
]

n = 0
for a, b in PAIRS:
    if a in t:
        t = t.replace(a, b, 1)
        n += 1
    else:
        print(f"  MISS: {a[:60]!r}")

SI.write_text(t, encoding="utf-8")
print(f"替换 {n}/{len(PAIRS)}")

# 复验
t2 = SI.read_text(encoding="utf-8")
i = t2.find("Columns are")
print("\n复验该段:")
print(repr(t2[max(0, i - 10):i + 130]))
