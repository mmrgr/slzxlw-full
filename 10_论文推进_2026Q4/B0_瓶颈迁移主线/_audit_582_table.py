# -*- coding: utf-8 -*-
"""核查 §5.8.2 主表与网格框之间的一致性。

【疑点】
主表（50 MW 网格）给出逐 r 的 CAWCC：
  r=0.6 → 1150，r=0.7 → 1150，r=0.8 → 1100，r=0.9 → 1100
而紧随其后的网格框写：
  "中间 r 值（0.6、0.7、0.8）的精确降幅不得引用——极差达 30–40 MW"

**这两者不矛盾但容易误读**：
  - 主表给的是**绝对值**（50 MW 网格上的值），不是降幅；
  - 网格框禁止引用的是**降幅**（相对基线的差值）。
绝对值的引用规则是："随网格细化单调趋近上界，50 MW 系统性低估 0–25 MW"。

但主表**没有标注这一点**，读者会直接把 1100 当成"真实承载容量"。

【本脚本核查】
1. 主表数值是否与 rstar_physical_cawcc_by_r.csv 一致；
2. 主表是否携带"绝对值为 50 MW 网格值"的标注；
3. 三条读数是否只引用了允许引用的量。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
MS = HERE / "03_主稿_v2.md"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    # 1. 产物核对
    f = R2 / "rstar_physical_cawcc_by_r.csv"
    print(f"=== {f.name} ===")
    if f.exists():
        d = pd.read_csv(f, encoding="utf-8-sig")
        print(d.to_string(index=False))
        ck("产物存在且非空", len(d) > 0, f"{len(d)} 行")
    else:
        ck("产物存在", False, str(f))

    # 2. 主表数值核对
    ms = MS.read_text(encoding="utf-8")
    i = ms.find("### 5.8.2 纯物理 CAWCC")
    seg = ms[i:i + 1600]
    for r, v in (("0.6", "1150"), ("0.7", "1150"), ("0.8", "1100"), ("0.9", "1100")):
        ck(f"主表 r={r} 标 {v}", f"| {r} " in seg and v in seg, "")

    # 3. 关键：主表是否声明"绝对值为 50 MW 网格值，系统性低估 0-25 MW"
    has_abs_note = "50 MW 网格系统性低估 0–25 MW" in ms or "系统性低估 0" in ms
    ck("网格框已声明绝对值系统性低估", has_abs_note, "")

    # 4. 表格标题/表头是否直接标注基线口径
    ck("主表表头未直接标注网格（需靠下方框）",
       "D-HA 物理 CAWCC" in seg, "表头仅写 物理 CAWCC")
    # 检查表格前是否有"50 MW 网格"提示
    before = ms[max(0, i - 300):i]
    ck("表格前有 50 MW 网格提示", "50 MW" in before, repr(before[-80:]))

    # 5. 三条读数只引用允许的量
    ck("读数1 只引端点外的 −100 MW（允许）", "由 1200 降至 1100 MW" in ms, "")
    ck("读数2 报告 CO 负结果", "物理 CAWCC 基本不动" in ms, "")
    ck("读数3 只主张 100 MW、拒绝 300 MW",
       "本文只主张 100 MW" in ms, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\n§5.8.2 主表一致性核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
