# -*- coding: utf-8 -*-
"""修正 SI 第 38 条：与第 25 条和第 44 条的口径统一（四参数全无锚点，偏移 0.018–0.104）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"

OLD = ("38. **Parameter uncertainty in $r^{*}$ could change the verdict.** A 10% error in $L$ or "
       "$\\mathrm{CoC}_d$ moves $r^{*}$ by about 0.05 to 0.09; a true value near 0.51 would put "
       "Santa Clara at or beyond the threshold. \"Not crossed\" is a nominal-parameter conclusion, "
       "not a robust one.")
NEW = ("38. **Parameter uncertainty in $r^{*}$ could change the verdict, and it has four independent "
       "sources.** A 10% error in a single threshold parameter moves $r^{*}$ by 0.018 ($C_p$), 0.089 "
       "($C_r$), 0.094 ($L$) or 0.104 ($\\mathrm{CoC}_d$); the two-endpoint span reaches 0.19, so "
       "$r^{*}$ can sit anywhere in roughly 0.46–0.66. A true value near 0.51 would put Santa Clara "
       "at or beyond the threshold, and one near 0.46 would put it clearly below. Because none of the "
       "four parameters carries a measured anchor (item 25), \"not crossed\" is a nominal-parameter "
       "conclusion rather than a robust one — and the uncertainty is not dominated by a single "
       "parameter that could be tightened first.")

t = SI.read_text(encoding="utf-8")
if OLD in t:
    SI.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK SI 第 38 条已更新")
else:
    print("未匹配")
