# -*- coding: utf-8 -*-
"""在 §5.7.3b 开头插入 FigR3 的引用。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_cite_figr3.py
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

OLD = """#### 5.7.3b 四情形分类学：`r*` 是一个判据，不是一个常数

上述公式中的 `r*` 容易被视为一个城市常数。"""

NEW = """#### 5.7.3b 四情形分类学：`r*` 是一个判据，不是一个常数

> **图 R3**（`figs/FigR3_rstar_regime_and_sensitivity.pdf`）：(a) 四情形分类相图（横轴 `C* = L/CoC_design`、纵轴 `r*`，含 320 个参数组合）；(b) 三种情形下的 CoC 轨迹；(c) 四参数的单参数敏感性。

上述公式中的 `r*` 容易被视为一个城市常数。"""


def main() -> None:
    text = V2.read_text(encoding="utf-8")
    if "FigR3_rstar_regime_and_sensitivity" in text:
        print("[SKIP] 已引用 FigR3")
        return
    if OLD not in text:
        print("[MISS] 未找到 §5.7.3b 锚点")
        sys.exit(1)
    text = text.replace(OLD, NEW, 1)
    V2.write_text(text, encoding="utf-8")
    print("[OK  ] 已插入 FigR3 引用")
    print(f"字数 {len(text):,}；行数 {text.count(chr(10)) + 1}")


if __name__ == "__main__":
    main()
