# -*- coding: utf-8 -*-
"""收尾修正 SI S4.6：迁移表与结论句改为 50 MW 网格值（1150→1400, +250）。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"

OLD_TAB = """| 0.16 (baseline) | 32.2 | 40.3 | 1100 | Source abstraction ratio |"""
NEW_TAB = """| 0.16 (baseline) | 32.2 | 40.3 | **1150** | Source abstraction ratio |"""

OLD_TAB2 = """| 0.25 | 50.4 | 62.9 | 1400 | Daily-average grid connection |"""
NEW_TAB2 = """| 0.25 | 50.4 | 62.9 | **1400** | Daily-average grid connection |"""

OLD_SENT = ("Raising the diversion fraction from 0.16 to 0.25 raises CAWCC from 1100 to 1400 MW "
            "and migrates the bottleneck from source abstraction to grid connection, which is "
            "the second positive instance of the main proposition.")
NEW_SENT = ("Raising the diversion fraction from 0.16 to 0.25 raises CAWCC from 1150 to 1400 MW "
            "(+250 MW) and migrates the bottleneck from source abstraction to grid connection, "
            "which is the second positive instance of the main proposition. These values sit on "
            "the 50 MW grid shared with the main results; the corresponding 100 MW-grid run gave "
            "1100 to 1400 MW, and the difference between +300 and +250 MW is a baseline "
            "difference, not a disagreement about the mechanism.")

OLD_ASSUMP = ("The curve is nevertheless a genuine model-run product, obtained by running the "
              "capacity scan and the carrying-capacity search at each fraction, not an inference.")
NEW_ASSUMP = ("The curve is nevertheless a genuine model-run product, obtained by running the "
              "capacity scan and the carrying-capacity search at each fraction, not an inference. "
              "Both the 100 MW and the 50 MW versions are archived, the latter under the `_50mw` "
              "suffix, so the two grids can be compared directly.")


def main() -> None:
    text = SI.read_text(encoding="utf-8")
    n = 0
    for old, new in ((OLD_TAB, NEW_TAB), (OLD_TAB2, NEW_TAB2),
                     (OLD_SENT, NEW_SENT), (OLD_ASSUMP, NEW_ASSUMP)):
        if old in text:
            text = text.replace(old, new, 1)
            n += 1
    SI.write_text(text, encoding="utf-8")
    print(f"完成 {n}/4，新长度 {len(text)}")


if __name__ == "__main__":
    main()
