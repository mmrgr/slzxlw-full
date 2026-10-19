# -*- coding: utf-8 -*-
"""用实际存在的英文锚点插入机制前提的一手支撑段落。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
EN = HERE / "04_wr_manuscript_en.md"

t = EN.read_text(encoding="utf-8")
ANCHOR = "This is a transferable screening procedure, not an assessment of one city"
ADD = ("The mechanism's premise — that campus cooling make-up is a blend whose constraint sits on "
       "the salinity side — also has first-hand documentary support we had not previously used: the "
       "city's statutory water plan states that cooling towers receiving groundwater \"could also "
       "receive a blend of multiple water sources ... with slight variations in water quality\", "
       "describes recycled water as advantageous for cooling towers through \"a much lower level of "
       "salinity\", and records that TDS \"is not a concern for the City\". These support the premise "
       "and the direction of the parameter choice, but the plan contains no numerical TDS, "
       "conductivity, chloride or hardness values, so they cannot anchor $C_p$ or $C_r$ (SI S7.12). ")

if ANCHOR in t and "first-hand documentary support" not in t:
    t = t.replace(ANCHOR, ADD + ANCHOR, 1)
    EN.write_text(t, encoding="utf-8")
    print("OK 已插入")
else:
    print("锚点未匹配或已存在")

s = re.sub(r"\$[^$]*\$", " MATH ", t)
print("英文词数:", len(s.split()))
