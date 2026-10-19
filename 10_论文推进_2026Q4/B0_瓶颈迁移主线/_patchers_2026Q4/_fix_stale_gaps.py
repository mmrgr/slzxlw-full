# -*- coding: utf-8 -*-
"""修正母稿 §9.2 第 8 条与 §3.6 第 3 点的过时陈述。

事实：9 项干预已在 2026-10-18 于 50 MW 网格重跑
（r2/{ha,co}/intervention_marginal_50mw.csv，基线 1150/1450，增益 +150/+100）。
另：三杠杆曲线也已按 50 MW 同网格重跑（scripts/run_reuse_levers_50mw.py）。
但 §9.2 第 8 条仍写"本文未做"，§3.6 第 3 点仍写"未经验证"——均为过时陈述，
且与 §3.6 末尾"已通过重跑彻底消除该分歧"自相矛盾。
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"

OLD_8 = """8. **干预从未在 50 MW 网格上重跑。** 干预扫描为 100 MW 步长，故其增益只能与同网格基线（1100/1400）相减；主结果物理日尺度 CAWCC（1150/1450）属另一网格，**两者不可做算术**（§3.6）。要得到 50 MW 网格上的干预增益，需重跑干预扫描——**本文未做**。这是"干预增益与主结果能否直接对话"这一问题的已知缺口。"""

NEW_8 = """8. ~~**干预从未在 50 MW 网格上重跑。**~~ **该缺口已于 2026-10-18 闭合。** 9 项干预已在 **50 MW 网格**上重跑（`r2/{ha,co}/intervention_marginal_50mw.csv`，基线 **HA 1150 / CO 1450 MW**，与主结果同网格），增益为 HA `leakage_minus_30pct` **+150 MW**、CO `grid_plus_50pct` **+100 MW**，其余 7 项逐点 **0**。旧 100 MW 网格版本（基线 1100/1400）作为历史对照保留，其 +200 已证实为基线网格伪影，**不采用**。
   同期，再生水三杠杆曲线亦已按 50 MW 同网格重跑（`r2/{ha,co}/reuse_marginal_curve_50mw.csv`、`r2/{ha,co}/reuse_production_marginal_curve_50mw.csv`、`r2/reuse_levers_50mw_summary.json`），基线同为 1150/1450，产水量杠杆增益由旧 +300 修正为 **+250 MW**（旧值含基线取整伪影）。
   **仍未做的**：干预之间的**交互**（见第 6 条），以及干预在 25/10 MW 更细网格上的复算。"""

OLD_36_3 = """3. 该文件中的 **+150 / +50** 同样是跨网格插值（1300 − 1150、1500 − 1450），**未经验证**：干预从未在 50 MW 网格上重跑，故 50 MW 网格上 `leakage_minus_30pct` 的边界可能是 1300 也可能是 1350，无法从现有产物判断。本文**不将其作为数值引用**，仅作为口径说明列于 SI。"""

NEW_36_3 = """3. ~~该文件中的 +150 / +50 是跨网格插值、未经验证。~~ **该点已由重跑取代（2026-10-18）**：9 项干预已在 50 MW 网格上重跑（`intervention_marginal_50mw.csv`），`leakage_minus_30pct` 的边界确为 **1300 MW**（非 1350），增益 **+150 MW**；CO `grid_plus_50pct` 边界为 **1550 MW**，增益 **+100 MW**。正文引用的即为该重跑值，不再依赖插值。`intervention_baseline_alignment.csv` 中那两列的伪值问题（跨网格相减）仍然成立，故该文件整体不引用。"""


def main() -> None:
    text = MS.read_text(encoding="utf-8")
    n = 0
    for old, new, tag in ((OLD_8, NEW_8, "§9.2 第8条"), (OLD_36_3, NEW_36_3, "§3.6 第3点")):
        if old in text:
            text = text.replace(old, new, 1)
            n += 1
            print(f"OK {tag}")
        else:
            print(f"未匹配 {tag}")
    MS.write_text(text, encoding="utf-8")
    print(f"\n完成 {n}/2，母稿 {len(text)} 字符")


if __name__ == "__main__":
    main()
