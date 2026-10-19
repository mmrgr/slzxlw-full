# -*- coding: utf-8 -*-
"""把 FigR4 引用插入主稿 v2（§5.8.2b 零效应区段落）。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
V2 = HERE / "03_主稿_v2.md"

OLD = """#### 5.8.2b 一个必须显式声明的"零效应区"

上表同时显示："""

NEW = """#### 5.8.2b 一个必须显式声明的"零效应区"

> **图 R4**（`figs/FigR4_zero_effect_and_policy_bridge.pdf`）：(a) 零效应区（阴影为现行政策区间 20%–35%，该区间内 CAWCC 完全不变）；(b) 全市利用率 `u` 到园区替代率上界 `r_max = u·(W/D)` 的换算。

上表同时显示："""


def main() -> None:
    text = V2.read_text(encoding="utf-8")
    if "FigR4_zero_effect_and_policy_bridge" in text:
        print("[SKIP] 已引用 FigR4")
        return
    if OLD not in text:
        print("[MISS] 未找到 §5.8.2b 锚点")
        sys.exit(1)
    text = text.replace(OLD, NEW, 1)
    V2.write_text(text, encoding="utf-8")
    print("[OK  ] 已插入 FigR4 引用")
    print(f"字数 {len(text):,}；行数 {text.count(chr(10)) + 1}")


if __name__ == "__main__":
    main()
