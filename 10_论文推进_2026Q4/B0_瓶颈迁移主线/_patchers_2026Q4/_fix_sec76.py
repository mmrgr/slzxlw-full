# -*- coding: utf-8 -*-
"""修补 §7.6 本章结论：把第三杠杆（配比 r）纳入，与 §7.0 的三杠杆结构一致。

问题：§7.0 已把本章重组为"能力/产量/配比"三杠杆，但 §7.6 的结论仍只讲前两个。
这是"局部更新、结论未同步"的典型缺陷。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_fix_sec76.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
V2 = HERE / "03_主稿_v2.md"

OLD = """> **再生水不是"不能提升承载容量"，而是"只有在它真正增加产水量、且瓶颈位于水源侧时才能提升"。** 仅扩大处理能力——这正是多数政策情景的实际做法——在两端点都完全无效；提高产水量在缺水端可使承载容量提升约 300 MW 并**把瓶颈迁移到电网**，在凉爽端则无效（因瓶颈本就在电网）。"""

NEW = """> **再生水的效果取决于作用在哪个杠杆上，而三个杠杆的方向并不相同。**
>
> | 杠杆 | 机制 | 效果 |
> |---|---|---|
> | **处理能力** | 供给侧"名不副实"（不改变可用产水量） | 两端点均**完全无效**；这是多数政策情景的实际做法 |
> | **产水量** | **供给增量**（真的增加可用再生水） | 缺水端 +300 MW 并**把瓶颈迁移到电网**；凉爽端无效（瓶颈本在电网） |
> | **配比 r** | **需求膨胀**（混合水质压低浓缩倍数） | `r ≤ r*` 时**零代价**；`r > r*` 后推高补水需求，缺水端承载容量 **−100 MW** |

> **三者不可混谈。** "扩处理能力"与"提产水量"是供给侧的量变，"提配比"则是通过水质侧改变了需求——方向相反。若把三者笼统地称为"扩大再生水利用"，会得到自相矛盾的规划结论。"""


def main() -> None:
    text = V2.read_text(encoding="utf-8")
    if "三个杠杆的方向并不相同" in text:
        print("[SKIP] §7.6 已更新")
        return
    if OLD not in text:
        print("[MISS] 未找到 §7.6 结论段")
        sys.exit(1)
    text = text.replace(OLD, NEW, 1)
    V2.write_text(text, encoding="utf-8")
    print("[OK  ] §7.6 结论已纳入三杠杆")
    print(f"字数 {len(text):,}；行数 {text.count(chr(10)) + 1}")


if __name__ == "__main__":
    main()
