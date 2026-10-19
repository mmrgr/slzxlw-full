# -*- coding: utf-8 -*-
"""核验"阈值可解析、效应量不可"这一边界结论。

断言：
  1. 50/25 MW 网格下解析近似误差 ≤ 1 个网格步；
  2. 10 MW 网格下 r=0.9 误差 > 1 个网格步（即形态失效）；
  3. 1 MW 精扫得真值 1111.76 MW（最后合规 1111、首次越界 1112）；
  4. 解析预测 1088.9 MW，差 22.86 MW；
  5. 偏差随 r 单调增大；
  6. 三处正文均已写入该边界。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MG = HERE / "_analytic_cawcc_multigrid.json"
FINE = HERE / "_fine_r09.json"
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    if not MG.exists() or not FINE.exists():
        print("缺产物")
        return
    mg = json.loads(MG.read_text(encoding="utf-8"))
    fine = json.loads(FINE.read_text(encoding="utf-8"))

    ck("50 MW 最大误差 ≤ 1 步",
       mg["50mw"]["max_rel_steps"] <= 1.0, f"{mg['50mw']['max_rel_steps']:.2f}")
    ck("25 MW 最大误差 ≤ 1 步",
       mg["25mw"]["max_rel_steps"] <= 1.0, f"{mg['25mw']['max_rel_steps']:.2f}")
    ck("10 MW 最大误差 > 1 步（形态失效）",
       mg["10mw"]["max_rel_steps"] > 1.0, f"{mg['10mw']['max_rel_steps']:.2f}")
    ck("10 MW 的 r=0.9 误差 ≈ 2.11 步",
       abs(mg["10mw"]["max_rel_steps"] - 2.11) < 0.05,
       f"{mg['10mw']['max_rel_steps']}")

    # 1 MW 精扫
    ck("1 MW 扫描：最后合规 = 1111",
       fine["last_ok_mw"] == 1111.0, str(fine["last_ok_mw"]))
    ck("1 MW 扫描：首次越界 = 1112",
       fine["first_bad_mw"] == 1112.0, str(fine["first_bad_mw"]))
    ck("最后合规取水比 < 0.95", fine["ratio_last_ok"] < 0.95,
       f"{fine['ratio_last_ok']:.6f}")
    ck("首次越界取水比 > 0.95", fine["ratio_first_bad"] > 0.95,
       f"{fine['ratio_first_bad']:.6f}")

    # 线性插值真值
    x1, y1 = fine["last_ok_mw"], fine["ratio_last_ok"]
    x2, y2 = fine["first_bad_mw"], fine["ratio_first_bad"]
    xc = x1 + (0.95 - y1) * (x2 - x1) / (y2 - y1)
    ck("插值真值 ≈ 1111.76 MW", abs(xc - 1111.76) < 0.5, f"{xc:.2f}")

    # 解析预测与差
    pred = 1088.9
    ck("解析预测 = 1088.9 MW", abs(mg["10mw"]["rows"][-1]["pred"] - pred) < 0.5,
       str(mg["10mw"]["rows"][-1]["pred"]))
    ck("差值 = +22.86 MW（非量化可解释）", abs((xc - pred) - 22.86) < 0.6,
       f"{xc-pred:.2f}")

    # 偏差随 r 单调
    rows = mg["10mw"]["rows"]
    diffs = [abs(r["diff"]) for r in rows if r["r"] >= 0.5]
    ck("10 MW 下 |偏差| 随 r 增大（r≥0.5）",
       diffs == sorted(diffs), str([round(d, 1) for d in diffs]))

    # 正文
    ms = MS.read_text(encoding="utf-8")
    en = EN.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    ck("母稿含 §5.7.7 解析边界", "5.7.7" in ms and "阈值可解析，效应量不可" in ms, "")
    ck("母稿写明 −100 MW 不是解析预测",
       "−100 MW 始终是模型输出，不是解析预测" in ms, "")
    ck("英文写明 model output, never an analytic prediction",
       "never an analytic prediction" in en, "")
    ck("SI 含 S5.8", "S5.8" in si, "")
    ck("SI 含 22.86 MW", "22.86" in si, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"解析边界核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
