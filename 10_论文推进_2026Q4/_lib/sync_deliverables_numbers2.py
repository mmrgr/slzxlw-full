"""清理交付物中剩余的混合旧数字 (2026-10-17)."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

REPS: dict[str, list[tuple[str, str]]] = {
    "A37_六主图_v4/figure_index.md": [
        ("**改用** 643/134/36 并披露容差口径", "**改用** 626/177/36 并披露容差口径"),
    ],
    "A37_六主图_v4/README.md": [
        ("独立复算探针 (643/134/36、q 分组、残差)", "独立复算探针 (626/177/36、q 分组、残差)"),
        ("严格符号 **643 负 / 134 正 / 36 零**", "严格符号 **626 负 / 177 正 / 36 零**"),
    ],
    "A40_投稿包/reproducibility_manifest.md": [
        ("| q 分组 | **290 / 288 / 235** |", "| q 分组 | **263 / 288 / 288** |"),
    ],
    "A36_终审/终审门禁报告与期刊匹配评估.md": [
        ("| 2 | 可靠子集 $n$=839 | ✅ 实测 813 |", "| 2 | 可靠子集 $n$=839 | ✅ 实测 839 |"),
        ("| 2 | 严格符号 643/134/36 | ✅ 实测 643/134/36 |",
         "| 2 | 严格符号 626/177/36 | ✅ 实测 626/177/36 |"),
        ("$q>0$ 的 290/263 头条**不受影响**", "$q>0$ 的 263/263 头条**不受影响**"),
        ("**改用严格符号 643/134/36**", "**改用严格符号 626/177/36**"),
    ],
}


def main() -> int:
    tot = 0
    for rel, pairs in REPS.items():
        p = ROOT / rel
        if not p.exists():
            print(f"  skip {rel}")
            continue
        t = p.read_text(encoding="utf-8")
        n = 0
        for a, b in pairs:
            if a in t:
                t = t.replace(a, b)
                n += 1
            else:
                print(f"  MISS {rel}: {a[:50]}")
        if n:
            p.write_text(t, encoding="utf-8")
        print(f"  {rel}: {n}")
        tot += n
    print(f"合计 {tot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
