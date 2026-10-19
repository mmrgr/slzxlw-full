# -*- coding: utf-8 -*-
"""独立复算 C_p 精度反解的每个数字（SI S7.10 与母稿第 44 条）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PREC = HERE / "_cp_precision_requirement.json"
SI = HERE / "05_wr_supplementary_en.md"
MS = HERE / "03_主稿_v2.md"

RES: list[tuple[str, bool, str]] = []
L, CD, CR = 2200.0, 5.0, 650.0
CSTAR = L / CD


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def cp_at(r_star: float, cr: float = CR) -> float:
    return (CSTAR - r_star * cr) / (1.0 - r_star)


def main() -> None:
    if not PREC.exists():
        print("缺少 _cp_precision_requirement.json")
        return
    d = json.loads(PREC.read_text(encoding="utf-8"))
    si = SI.read_text(encoding="utf-8")
    ms = MS.read_text(encoding="utf-8")

    ck("L/CoC_d = 440", abs(CSTAR - 440.0) < 1e-9, f"{CSTAR}")
    ck("r=0.499 临界 C_p = 230.8", abs(cp_at(0.499) - 230.8) < 0.05, f"{cp_at(0.499):.2f}")
    ck("r=0.444 临界 C_p = 272.3", abs(cp_at(0.444) - 272.3) < 0.05, f"{cp_at(0.444):.2f}")
    ck("180 距 230.8 的余量 = 50.8", abs((230.8 - 180) - 50.8) < 0.05,
       f"{230.8-180:.1f}")
    ck("±25 mg/L 精度 = 50.8/2", abs((230.8 - 180) / 2 - 25.4) < 0.2,
       f"{(230.8-180)/2:.1f}")

    # C_r 敏感性
    for cr, want in ((500, 380.2), (650, 230.8), (800, 81.4)):
        got = cp_at(0.499, cr)
        ck(f"C_r={cr} 时临界 C_p = {want}", abs(got - want) < 0.1, f"{got:.1f}")

    # C_r 超过 ~1000 时临界转负
    ck("C_r=1000 时临界 C_p < 0", cp_at(0.499, 1000) < 0, f"{cp_at(0.499,1000):.1f}")

    # json 一致性
    ck("json 记录 required_precision_mg_l",
       "required_precision_mg_l" in d, str(d.get("required_precision_mg_l")))

    # SI 与母稿都写了这些数字
    for needle in ("230.8", "272.3", "50.8", "380.2", "81.4", "±25"):
        ck(f"SI 含 {needle}", needle in si, "")
    for needle in ("230.8", "272.3", "50.8", "±25"):
        ck(f"母稿含 {needle}", needle in ms, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\nC_p 精度反解复算　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
