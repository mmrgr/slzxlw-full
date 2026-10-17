"""门禁 9: 稿件结构完整性（编号连续 + 交叉引用不悬空）(2026-10-17).

【为何需要】
反复增量编辑曾造成:
  · Results 小节编号为 1,2,3,3d,3b,3b-bis,3c,4... —— 顺序与编号不一致;
  · 标题里残留 "(new in v4)" 等内部编辑痕迹;
  · 改编号后正文 §N 交叉引用可能悬空或指错。
这些是**审稿人一眼可见**的低级缺陷, 但没有门禁覆盖。

【检查项】
 1. Results 小节编号必须**严格递增**(1,2,3,...,12,12a,12b);
 2. 正文中每个 §N 都必须对应存在的小节;
 3. 不得出现 "new in v" / "(v4" 等内部编辑痕迹;
 4. 不得出现非标准编号如 "3b-bis"。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"


def main() -> int:
    t = MS.read_text(encoding="utf-8")
    print("=" * 74)
    print("稿件结构完整性门禁")
    print("=" * 74)
    fails = 0

    # 1. Results 小节编号递增
    r = t[t.index("## Results"):t.index("## Discussion")]
    nums = re.findall(r"^#{3,4} (\d+)([a-z]*)\.", r, re.M)
    keys = [(int(n), s) for n, s in nums]
    ordered = all(keys[i] <= keys[i + 1] for i in range(len(keys) - 1))
    print(f"  [{'PASS' if ordered else 'FAIL'}] Results 小节编号递增 "
          f"({len(keys)} 个: {[str(n)+s for n,s in keys][:6]}…)")
    if not ordered:
        fails += 1
        print(f"      实际顺序: {[str(n)+s for n,s in keys]}")

    # 2. 交叉引用不悬空
    secs = set(f"{n}{s}" for n, s in keys)
    refs = set(m.group(1) for m in re.finditer(r"§\s?(\d+[a-z]?)", t))
    dangling = sorted(refs - secs)
    print(f"  [{'PASS' if not dangling else 'FAIL'}] 交叉引用不悬空 "
          f"(引用 {len(refs)} 个 §N, 悬空 {len(dangling)})")
    if dangling:
        fails += 1
        print(f"      悬空: {dangling}")

    # 3. 编辑痕迹
    artifacts = re.findall(r"new in v\d|\(v\d[,\s\)]", t)
    print(f"  [{'PASS' if not artifacts else 'FAIL'}] 无内部编辑痕迹 "
          f"(命中 {len(artifacts)})")
    if artifacts:
        fails += 1

    # 4. 非标准编号
    weird = re.findall(r"^#{3,4} \d+[a-z]?-(bis|ter)[\.\s]", r, re.M)
    print(f"  [{'PASS' if not weird else 'FAIL'}] 无非标准编号(bis/ter) "
          f"(命中 {len(weird)})")
    if weird:
        fails += 1

    # 5. 空路径 (2026-10-17: shell 反引号曾吞掉 Markdown 路径, 形成 "point ()")
    #    只匹配这一具体损坏形态, 避免误报正常括号。
    empty = re.findall(r"point \(\)", t)
    print(f"  [{'PASS' if not empty else 'FAIL'}] 无空路径/空括号 "
          f"(命中 {len(empty)})")
    if empty:
        fails += 1

    print()
    print(f"裁定: {'结构完整 ✓' if fails == 0 else f'{fails} 项不合格 ✗'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
