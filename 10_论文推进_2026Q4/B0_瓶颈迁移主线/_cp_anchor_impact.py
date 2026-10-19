# -*- coding: utf-8 -*-
"""用 GAMA 加州实测 TDS 检验 C_p 假设值 180 mg/L 的合理性，并计算对 r* 的影响。

【为什么这是实质性的】
r* = (L/CoC_d − C_p)/(C_r − C_p)，C_p 在分子（负号）与分母（负号）同时出现，
故 r* 对 C_p 的弹性虽小（−0.3093），但当 C_p 从 180 升到 546 时，r* 会显著变化。

本脚本给出：
  1. GAMA 实测 TDS 分布与 180 的百分位；
  2. C_p 取不同值（180 / 全州中位 420 / Alameda 546 / LA 550）时的 r*；
  3. 这些 r* 与 Santa Clara 的 r = 0.444 / 0.499 相比，判定是否翻转；
  4. 结论：C_p 的锚定状态对本文结论的实际影响量级。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
GAMA = HERE / "_gama_tds_statewide.json"
OUT = HERE / "_c_p_anchor_impact.json"

L, CD, CR = 2200.0, 5.0, 650.0


def rstar(cp: float, l=L, cd=CD, cr=CR) -> float:
    return (l / cd - cp) / (cr - cp)


def main() -> None:
    g = json.loads(GAMA.read_text(encoding="utf-8"))
    med = g["tds"]["p50"]
    print("=== GAMA 加州实测 TDS（地下水，19 县，不含 Santa Clara）===")
    for k in ("p5", "p25", "p50", "p75", "p95"):
        print(f"  {k}: {g['tds'][k]:>8.0f} mg/L")
    print(f"  假设值 C_p = 180 位于第 {g['assumed_percentile']} 百分位")

    cases = [
        ("项目假设（未锚定）", 180.0),
        ("GAMA 全州中位", med),
        ("Alameda 县中位（邻近县）", g["county_median"].get("ALAMEDA")),
        ("Los Angeles 县中位", g["county_median"].get("LOS ANGELES")),
        ("Fresno 县中位（较淡）", g["county_median"].get("FRESNO")),
    ]

    print(f"\n{'C_p 取值情形':<28}{'C_p':>8}{'r*':>10}{'vs 0.444':>12}{'vs 0.499':>12}  判定")
    print("-" * 84)
    rows = []
    R_SC_A, R_SC_B = 0.444, 0.499
    for name, cp in cases:
        if cp is None:
            continue
        rs = rstar(cp)
        d_a, d_b = R_SC_A - rs, R_SC_B - rs
        # 判定：r_SC < r* 则未越过；r_SC > r* 则已越过
        crossed_a = "越过" if R_SC_A > rs else "未越"
        crossed_b = "越过" if R_SC_B > rs else "未越"
        print(f"{name:<28}{cp:>8.0f}{rs:>10.4f}{d_a:>+12.4f}{d_b:>+12.4f}"
              f"  A:{crossed_a} B:{crossed_b}")
        rows.append({"case": name, "c_p": cp, "r_star": round(rs, 4),
                     "margin_A": round(d_a, 4), "margin_B": round(d_b, 4),
                     "crossed_A": bool(R_SC_A > rs), "crossed_B": bool(R_SC_B > rs)})

    # 多物种取紧是否仍成立（C_r 不变）
    print("\n注：C_r = 650 mg/L 亦无锚点。若 C_r 同时变化，r* 会移动更多。")
    for cr in (500.0, 650.0, 800.0, 1000.0):
        print(f"  C_r={cr:>6.0f} → r*(C_p=180) = {rstar(180.0, cr=cr):.4f}")

    flipped = any(r["crossed_A"] or r["crossed_B"] for r in rows
                  if r["c_p"] != 180.0)
    print(f"\n结论：改变 C_p 是否翻转 Santa Clara 的判定 → {'是' if flipped else '否'}")
    OUT.write_text(json.dumps({
        "gama_percentile_of_180": g["assumed_percentile"],
        "cases": rows,
        "verdict_flips": bool(flipped),
        "note": ("GAMA 为地下水监测数据，不等于供水系统出厂水；结论仅用于说明 "
                 "C_p 未锚定对判定的影响的量级，不用于替换项目参数。"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"产物：{OUT.name}")


if __name__ == "__main__":
    main()
