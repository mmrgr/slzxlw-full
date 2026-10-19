# -*- coding: utf-8 -*-
"""反解：要让 Santa Clara 的判定确定下来，C_p 需要多精确？

【问题】
正文已承认"C_p 未锚定，判定是标称参数下的结论"。但读者/审稿人紧接着会问：
"那需要测到什么精度才算够？" 这个问题此前没有回答。

【两条不同的判定线】
  A 口径：r_SC = 0.444（供给能力）  →  r* = 0.444 时 C_p = ?
  B 口径：r_SC = 0.499（实际用量）  →  r* = 0.499 时 C_p = ?

由 r* = (L/CoC_d − C_p)/(C_r − C_p) 解出 C_p：
  r*(C_r − C_p) = L/CoC_d − C_p
  r*C_r − r*C_p = L/CoC_d − C_p
  C_p(1 − r*) = L/CoC_d − r*C_r
  C_p = (L/CoC_d − r*C_r)/(1 − r*)

【产物】_cp_precision_requirement.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
OUT = HERE / "_cp_precision_requirement.json"

L, CD, CR = 2200.0, 5.0, 650.0
CSTAR = L / CD  # 440


def cp_at(r_star: float, cr: float = CR) -> float:
    return (CSTAR - r_star * cr) / (1.0 - r_star)


def main() -> None:
    print(f"L/CoC_d = {CSTAR:.0f} mg/L（C_p 高于此值则 r*<0，进入情形 I）\n")

    rows = []
    print(f"{'判定口径':<26}{'r_SC':>8}{'临界 C_p':>12}{'含义'}")
    print("-" * 76)
    for name, r_sc in (("A 供给能力口径", 0.444), ("B 2025 实际用量口径", 0.499)):
        cp_crit = cp_at(r_sc)
        note = ("C_p 低于此值 → 未越过；高于 → 越过" if cp_crit > 0
                else "该 r 下无正解（r* 越大所需 C_p 越低）")
        print(f"{name:<26}{r_sc:>8.3f}{cp_crit:>12.1f}  {note}")
        rows.append({"caliber": name, "r_sc": r_sc,
                     "c_p_critical": round(cp_crit, 2), "note": note})

    # 敏感性：若 C_r 也变
    print(f"\n若 C_r 同时未定（取 C_r ∈ 500…1000），临界 C_p 如何移动（B 口径 r=0.499）：")
    cr_rows = []
    for cr in (400, 500, 650, 800, 1000, 1200):
        v = cp_at(0.499, cr)
        print(f"  C_r={cr:>5.0f} → 临界 C_p = {v:7.1f} mg/L")
        cr_rows.append({"c_r": cr, "c_p_critical_at_r0499": round(v, 2)})

    # 关键结论
    a = rows[0]["c_p_critical"]
    b = rows[1]["c_p_critical"]
    print(f"\n{'='*76}")
    print("结论：")
    print(f"  若要判定'B 口径未越过'（r=0.499），需实测 C_p < {b:.1f} mg/L")
    print(f"  若要判定'A 口径未越过'（r=0.444），需实测 C_p < {a:.1f} mg/L")
    print(f"  项目假设 C_p = 180 mg/L，距 B 口径临界值尚有 {b-180:.1f} mg/L 余量。")
    print(f"  但 GAMA 加州地下水 TDS 中位为 420 mg/L，远高于两个临界值——")
    print(f"  故'实测值落在临界值哪一侧'完全取决于该市实际水源，不能由州级分布推断。")
    print(f"\n  → 所需精度：C_p 需精确到 ±{(b-180)/2:.0f} mg/L 以内，判定才不会落在模糊地带。")

    OUT.write_text(json.dumps({
        "L_over_coc_d": CSTAR,
        "calibers": rows,
        "c_r_sensitivity_at_r0499": cr_rows,
        "assumed_c_p": 180.0,
        "required_precision_mg_l": round((b - 180) / 2, 1),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
