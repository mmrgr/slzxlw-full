# -*- coding: utf-8 -*-
"""核验 D-CO 端的三网格检验已写入，且"负结果成立"这一判断有数据支撑。

断言：
  1. 网格表含 D-CO 的 6 个 r 点 × 3 网格；
  2. CO 降幅：50/25/20 MW，均 ≤ 50；
  3. CO 降幅随网格细化单调减小（50 ≥ 25 ≥ 20）；
  4. CO 相对基线 ≤ 3.4%；
  5. CO 10 MW 基线 = 1460（与 50 MW 的 1450 差 10）；
  6. 母稿网格框已含 CO 行；
  7. 母稿/英文/SI 均已写入该负结果的网格检验。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    d = pd.read_csv(R2 / "rstar_grid_convergence_table.csv", encoding="utf-8-sig")
    co = d[d["domain"] == "co"].sort_values("target_r")
    ck("CO 有 6 个 r 点", len(co) == 6, str(len(co)))
    for g in ("50mw", "25mw", "10mw"):
        ck(f"CO 含 cawcc_{g} 列", f"cawcc_{g}" in co.columns, "")

    base = {g: float(co[co["target_r"] == 0][f"cawcc_{g}"].iloc[0])
            for g in ("50mw", "25mw", "10mw")}
    end = {g: float(co[co["target_r"] == 0.9][f"cawcc_{g}"].iloc[0])
           for g in ("50mw", "25mw", "10mw")}
    drops = {g: base[g] - end[g] for g in base}

    ck("CO 降幅 50 = 50 MW", drops["50mw"] == 50.0, str(drops["50mw"]))
    ck("CO 降幅 25 = 25 MW", drops["25mw"] == 25.0, str(drops["25mw"]))
    ck("CO 降幅 10 = 20 MW", drops["10mw"] == 20.0, str(drops["10mw"]))
    ck("CO 三网格降幅均 ≤ 50 MW", all(v <= 50.0 for v in drops.values()), str(drops))
    ck("CO 降幅随网格细化单调减小",
       drops["50mw"] >= drops["25mw"] >= drops["10mw"], str(list(drops.values())))

    pct = 100.0 * max(drops.values()) / base["50mw"]
    ck("CO 相对基线 = 3.45%", abs(pct - 3.448) < 0.01, f"{pct:.2f}%")

    ck("CO 10 MW 基线 = 1460", base["10mw"] == 1460.0, str(base["10mw"]))
    ck("CO 10 MW 与 50 MW 基线差 10 MW",
       abs(base["10mw"] - base["50mw"] - 10.0) < 1e-9, f"{base['10mw']-base['50mw']:.0f}")

    # 正文
    ms = MS.read_text(encoding="utf-8")
    en = EN.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    ck("母稿网格框含 D-CO 行", "**D-CO**" in ms and "负结果成立" in ms, "")
    ck("母稿写明负结果同等检验强度", "负结果与主结论享有同等检验强度" in ms, "")
    ck("英文含 CO 三网格数字", "50, 25 and 20 MW" in en, "")
    ck("SI 含 S5.4c", "S5.4c" in si, "")
    ck("SI 写明 1460 与 1450 的差异", "1460 rather than 1450" in si, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"CO 端三网格检验核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
