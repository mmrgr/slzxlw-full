# -*- coding: utf-8 -*-
"""修正 C_p 影响表：Alameda 中位是 545.5（非 546），r* 应与其一致。

原表把 C_p 写成 546 但 r* 用 545.5 算得 -1.0096，属表格内部不一致。
修法：C_p 列改为 545.5，保持 r* = -1.0096（由精确值复算）。
同时英文正文的 −1.01 保留（四舍五入一致）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"
MSI = HERE / "_c_p_anchor_impact.json"

OLD = "| Alameda county median | 546 | −1.0096 | **crossed / crossed** (Regime I) |"
NEW = "| Alameda county median | 545.5 | −1.0096 | **crossed / crossed** (Regime I) |"

t = SI.read_text(encoding="utf-8")
if OLD in t:
    SI.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK SI 表已修正 546 -> 545.5")
else:
    print("SI 未匹配")

# json 里同步为精确值
import json
d = json.loads(MSI.read_text(encoding="utf-8"))
for c in d["cases"]:
    if c["case"].startswith("Alameda"):
        c["c_p"] = 545.5
MSI.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("OK json 已同步")
