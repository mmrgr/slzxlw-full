"""SI 数字同步脚本 (2026-10-17, A19 回灌后).

把 SI 中所有与主网格相关的旧数字批量更新为 A19 回灌后的新值。
**使用本脚本而非 heredoc**, 因为 heredoc 会把 \\a \\r \\b \\v 等解释成控制字符
(本项目已三次踩此坑)。

映射依据: A13_可靠性机制/supply_state_summary.json (n_reliable=839, strict 626/177/36)
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SI = HERE.parent / "A16_英文稿" / "supplementary_information.md"

# (旧文本, 新文本) —— 精确串, 逐条替换
REPS: list[tuple[str, str]] = [
    # q 分组表 (L74 附近)
    ("| $q>0$ | 290 | **290** | **0** | −14,496 |",
     "| $q>0$ | 263 | **263** | **0** | −17,264 |"),
    ("| $q\\approx0$ | 288 | 220 | **32** | 36 | −7,651 |",
     "| $q\\approx0$ | 288 | 220 | **32** | 36 | −7,651 |"),
    ("**$q>0$ is sufficient for a city-level benefit (290/290, no exception).**",
     "**$q>0$ is sufficient for a city-level benefit (263/263, no exception).**"),
    ("run (reliable subset $n=813$). The superseded",
     "run (reliable subset $n=839$). The superseded"),
    # 新旧对照表
    ("| reliable scenarios | 1,094 | **813** |",
     "| reliable scenarios | 1,094 | **839** |"),
    ("| $q>0$ | 329 | 290 |",
     "| $q>0$ | 329 | 263 |"),
    # 头条统计表 (L185-190)
    ("| scenarios | 1,052 | **813** |",
     "| scenarios | 1,052 | **839** |"),
    ("| $dS_{\\rm pot}<0$ | — | **643** |",
     "| $dS_{\\rm pot}<0$ | — | **626** |"),
    ("| $dS_{\\rm pot}>0$ | — | **134** |",
     "| $dS_{\\rm pot}>0$ | — | **177** |"),
    ("| $q>0$ | — | **290** |",
     "| $q>0$ | — | **263** |"),
    # 更正说明
    ("> exact zeros, the other 32 being genuinely harmful. The corrected strict counts are 643 / 134 /",
     "> exact zeros, the other 32 being genuinely harmful. The corrected strict counts are 626 / 177 /"),
    ("> 36 at $n=813$. Note that the earlier \"1,152 scenarios / 58 unreliable\" entry in this table",
     "> 36 at $n=839$. Note that the earlier \"1,152 scenarios / 51 unreliable\" entry in this table"),
    # Figshare 表
    ("| Figshare RW (TDS 1,378) | 1.15–5.00 | 119 / 62 / 9 |",
     "| Figshare RW (TDS 1,378) | 1.15–5.00 | 102 / 105 / 9 |"),
    # 其余
    ("\"290/290, no exception\" sufficient condition — is computed with *post-simulation* quantities",
     "\"263/263, no exception\" sufficient condition — is computed with *post-simulation* quantities"),
    ("**Results** ($n_{\\rm eff}=733$; the 813 reliable scenarios less 80 within $10^{-9}$ ML of zero,",
     "**Results** ($n_{\\rm eff}=759$; the 839 reliable scenarios less 80 within $10^{-9}$ ML of zero,"),
    ("strict convention gives 643 / 134 / 36 ($n=813$); an earlier convention applied",
     "strict convention gives 626 / 177 / 36 ($n=839$); an earlier convention applied"),
    ("convention and report $n_{\\rm eff}$ explicitly. The $q>0$ sufficient condition (290/290)",
     "convention and report $n_{\\rm eff}$ explicitly. The $q>0$ sufficient condition (263/263)"),
    ("table was labelled $n=813$. The silently removed 80 scenarios were not all near-zero: **36",
     "table was labelled $n=839$. The silently removed 80 scenarios were not all near-zero: **36"),
]


def main() -> int:
    t = SI.read_text(encoding="utf-8")
    hit, miss = 0, []
    for old, new in REPS:
        if old == new:
            continue
        if old in t:
            t = t.replace(old, new, 1)
            hit += 1
        else:
            miss.append(old[:70])
    SI.write_text(t, encoding="utf-8")
    print(f"SI 替换 {hit}/{len([r for r in REPS if r[0] != r[1]])} 条")
    for m in miss:
        print("  未命中:", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
