# -*- coding: utf-8 -*-
"""验证解析预测：CAWCC(r) ∝ 1/f(r)，f = CoC/(CoC−1)。

【推导】
D-HA 首失效 = 水源取水比 ≤ 0.95：
    (base + AI取水(MW, r)) / CAP = 0.95
AI 取水 = E(MW) · f(r)，E ∝ MW
  → base + k·MW·f(r) = 0.95·CAP
  → MW*(r) = (0.95·CAP − base) / (k·f(r))
即  MW*(r) = A / f(r)，A 为常数。

【检验】
从 r ≤ r*（CoC = 5 恒定，f = 1.25）的区间取 A：
    MW*(0.5) = 1200 = A / 1.25  →  A = 1500
然后预测 r > r* 各点的 MW*：
    r=0.6: CoC=4.7619, f=1.2658 → MW* = 1500/1.2658 = 1185.0
    r=0.8: CoC=3.9568, f=1.3382 → MW* = 1500/1.3382 = 1120.9
    r=0.9: CoC=3.6484, f=1.3776 → MW* = 1500/1.3776 = 1088.9
与实测 CAWCC（1150 / 1100 / 1100）比较。

【注意】实物受 50 MW 网格量化，故预测值与实测值应在 ±1 个网格步内一致。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
OUT = HERE / "_analytic_cawcc_test.json"

L, CD, CP, CR = 2200.0, 5.0, 180.0, 650.0


def coc(r: float) -> float:
    return min(CD, L / (r * CR + (1 - r) * CP))


def f(r: float) -> float:
    c = coc(r)
    return c / (c - 1.0)


def main() -> None:
    caw = pd.read_csv(R2 / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")
    caw = caw[caw["domain"] == "ha"].sort_values("target_r")
    obs = {float(x["target_r"]): float(x["physical_cawcc_mw"]) for _, x in caw.iterrows()}

    # 从 r=0.5（CoC 仍为设计值）定标 A
    A = obs[0.5] * f(0.5)
    print(f"定标：A = CAWCC(0.5) × f(0.5) = {obs[0.5]:.0f} × {f(0.5):.4f} = {A:.2f}")
    print("\n（若 A 是常数，则解析式成立）\n")

    print(f"{'r':>5}{'CoC':>9}{'f':>8}{'预测 MW*':>11}{'实测':>7}{'差':>7}{'差/网格':>9}")
    print("-" * 60)
    rows = []
    ok_within_one_step = True
    for r in sorted(obs):
        pred = A / f(r)
        o = obs[r]
        d = o - pred
        steps = d / 50.0
        print(f"{r:>5.1f}{coc(r):>9.4f}{f(r):>8.4f}{pred:>11.1f}{o:>7.0f}{d:>7.1f}{steps:>9.2f}")
        rows.append({"r": r, "coc": round(coc(r), 4), "f": round(f(r), 4),
                     "predicted_mw": round(pred, 2), "observed_mw": o,
                     "diff_mw": round(d, 2), "diff_in_grid_steps": round(steps, 3)})
        if abs(steps) > 1.0:
            ok_within_one_step = False

    # 另一角度：A 逐点反算
    print(f"\n=== 逐点反算 A = CAWCC × f（若恒定则解析成立）===")
    print(f"{'r':>5}{'A 反算':>12}")
    A_vals = []
    for r in sorted(obs):
        a = obs[r] * f(r)
        A_vals.append(a)
        print(f"{r:>5.1f}{a:>12.1f}")
    spread = max(A_vals) - min(A_vals)
    print(f"\n  A 范围 [{min(A_vals):.1f}, {max(A_vals):.1f}]，极差 {spread:.1f}")
    print(f"  相对极差 {100*spread/min(A_vals):.1f}%")

    print(f"\n=== 判定 ===")
    if ok_within_one_step:
        print("  ✅ 所有预测值与实测值之差均 ≤ 1 个网格步（50 MW）")
        print("     → CAWCC(r) = A/f(r) 这一解析形式与模型输出一致，")
        print("       差异可完全由 50 MW 网格量化解释。")
    else:
        print("  ❌ 存在超出 1 个网格步的偏差，解析形式不成立或需修正。")

    (HERE / "_analytic_cawcc_test.json").write_text(
        pd.DataFrame(rows).to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
