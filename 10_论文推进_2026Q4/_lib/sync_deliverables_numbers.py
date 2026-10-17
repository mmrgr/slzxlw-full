"""同步交付物中的旧数字 (2026-10-17).

只改**交付物**(主稿/SI/主图图注/复现清单/终审报告),
**不改历史记录**(A25/A28/A30/A38/过程记录)——那些应保留原值并标注已过时。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

# (相对路径, [(旧, 新), ...])
TARGETS: list[tuple[str, list[tuple[str, str]]]] = [
    ("A16_英文稿/supplementary_information.md", [
        ("| $q<0$ | 235 | 133 | 102 | −4,259 |",
         "| $q<0$ | 288 | 143 | 145 | 200 |"),
        ("| $q>0$ | 263 | **263** | **0** | −17,264 |",
         "| $q>0$ | 263 | **263** | **0** | −17,264 |"),
    ]),
    ("A37_六主图_v4/fig3_caption.md", []),
]

# 通用: 对交付物做全局数值替换
GLOBAL = [
    # 只在明确交付物中替换; 顺序: 长串优先
    ("643 negative", "626 negative"),
    ("134 positive", "177 positive"),
    ("**643**", "**626**"),
    ("**134**", "**177**"),
    ("n=813", "n=839"),
    ("813 可靠", "839 可靠"),
    ("813 reliable", "839 reliable"),
    ("813 solver", "839 solver"),
    ("=813", "=839"),
    ("**813**", "**839**"),
    ("290/288/235", "263/288/288"),
    ("290 (q > 0)", "263 (q > 0)"),
    ("235 (q < 0)", "288 (q < 0)"),
    ("0 of 290", "0 of 263"),
    ("0/290", "0/263"),
    ("(290/290", "(263/263"),
    ("290 of 290", "263 of 263"),
]

DELIVERABLES = [
    "A16_英文稿/supplementary_information.md",
    "A37_六主图_v4/fig3_caption.md",
    "A37_六主图_v4/fig4_caption.md",
    "A37_六主图_v4/figure_index.md",
    "A37_六主图_v4/README.md",
    "A40_投稿包/reproducibility_manifest.md",
    "A36_终审/终审门禁报告与期刊匹配评估.md",
]


def main() -> int:
    total = 0
    for rel in DELIVERABLES:
        p = ROOT / rel
        if not p.exists():
            print(f"  跳过(不存在): {rel}")
            continue
        t = p.read_text(encoding="utf-8")
        n = 0
        for a, b in GLOBAL:
            if a in t:
                n += t.count(a)
                t = t.replace(a, b)
        # 特殊: SI 的 q<0 行
        old_row = "| $q<0$ | 235 | 133 | 102 | −4,259 |"
        new_row = "| $q<0$ | 288 | 143 | 145 | 200 |"
        if old_row in t:
            t = t.replace(old_row, new_row, 1)
            n += 1
        if n:
            p.write_text(t, encoding="utf-8")
        print(f"  {rel}: 替换 {n} 处")
        total += n
    print(f"\n合计 {total} 处")
    return 0


if __name__ == "__main__":
    sys.exit(main())
