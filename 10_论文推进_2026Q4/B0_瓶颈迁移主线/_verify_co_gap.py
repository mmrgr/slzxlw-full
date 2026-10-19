# -*- coding: utf-8 -*-
"""把"D-CO 端联合-纯物理差距更大"这一发现固化为门禁。

断言：
  1. 产物 20 行、两域各 10 个 r 点；
  2. CO 端 r=0.9 的联合-纯物理差距 = −700 MW；
  3. HA 端 r=0.9 的差距 = −300 MW；
  4. CO 差距绝对值 > HA（即 CO 更大）；
  5. 机制解释成立：CO 纯物理瓶颈为电网、HA 为水源取水；
  6. CO 纯物理 r=0→0.9 仅降 50 MW（与联合的 750 MW 形成对比）；
  7. 三处正文均已写入该对比。
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
    d = pd.read_csv(R2 / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")
    jc = next(c for c in d.columns if "joint" in c.lower() and "mw" in c.lower())
    pc = next(c for c in d.columns if "physical" in c.lower() and "mw" in c.lower())
    bc = next(c for c in d.columns if "limiting" in c.lower() and "physical" in c.lower())

    ck("产物 20 行（2 域 × 10 个 r）", len(d) == 20, str(len(d)))

    def row(dom: str, r: float):
        s = d[(d["domain"] == dom) & (d["target_r"] == r)]
        return s.iloc[0]

    ha9 = row("ha", 0.9)
    co9 = row("co", 0.9)
    ha9_gap = float(ha9[jc]) - float(ha9[pc])
    co9_gap = float(co9[jc]) - float(co9[pc])

    ck("HA r=0.9 差距 = −300", abs(ha9_gap - (-300)) < 1e-6, f"{ha9_gap:.0f}")
    ck("CO r=0.9 差距 = −700", abs(co9_gap - (-700)) < 1e-6, f"{co9_gap:.0f}")
    ck("CO 差距绝对值 > HA", abs(co9_gap) > abs(ha9_gap),
       f"CO {abs(co9_gap):.0f} vs HA {abs(ha9_gap):.0f}")

    # 机制：纯物理瓶颈
    ck("HA 纯物理瓶颈 = 水源取水",
       "source_abstraction" in str(ha9[bc]), str(ha9[bc]))
    ck("CO 纯物理瓶颈 = 电气侧（grid 或 local_connection）",
       ("grid" in str(co9[bc])) or ("local_connection" in str(co9[bc])), str(co9[bc]))

    # CO 纯物理降幅
    co0 = row("co", 0.0)
    co_drop_phys = float(co0[pc]) - float(co9[pc])
    co_drop_joint = float(co0[jc]) - float(co9[jc])
    ck("CO 纯物理 r=0→0.9 仅降 50 MW", abs(co_drop_phys - 50) < 1e-6, f"{co_drop_phys:.0f}")
    ck("CO 联合 r=0→0.9 降 750 MW", abs(co_drop_joint - 750) < 1e-6, f"{co_drop_joint:.0f}")
    ck("联合/纯物理 倍数 ≥ 10", co_drop_joint / max(co_drop_phys, 1e-9) >= 10,
       f"{co_drop_joint/max(co_drop_phys,1e-9):.0f}×")

    # 正文写入
    ms = MS.read_text(encoding="utf-8")
    en = EN.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    ck("母稿含 CO 端 −700 MW", "700 MW" in ms and "D-CO 端" in ms, "")
    ck("母稿写明机制（瓶颈位置不同）", "纯物理瓶颈位置不同" in ms, "")
    ck("英文含 700 MW at the cool endpoint", "700 MW at the cool endpoint" in en, "")
    ck("SI 含 S5.4b", "S5.4b" in si, "")
    ck("SI 含 15-fold 对比", "15-fold" in si, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"CO 端联合-纯物理差距核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
