# -*- coding: utf-8 -*-
"""精确定位解析式 CAWCC(r)=A/f(r) 的偏差来源。

【新的实测（10 MW 网格，逐步扫描）】
  r=0.8: 首次越界 1140，故 CAWCC = 1130（1130 时 0.948844 < 0.95）
  r=0.9: 首次越界 1120，故 CAWCC = 1110（1110 时 0.949744 < 0.95）

解析预测（A=1500, f 用 CoC 均值）：
  r=0.8: 1500/1.3382 = 1120.9  → 实测 1130，差 +9.1
  r=0.9: 1500/1.3776 = 1088.9  → 实测 1110，差 +21.1

【偏差随 r 增大而增大 → 提示解析式缺一项】
可能原因：AI 取水中"自来水部分"不随 f(r) 变化，只有"再生水部分"受 f 影响。
若 AI 取水 = P(MW,r) + R(MW,r)，其中 P = (1−r)·M、R = r·M，
而 M = E·f(r)，则总取水 = M = E·f(r)（不含 (1−r) 分解）；
但**城市源取水**只计自来水部分 → 城市取水 = base + (1−r)·E·f(r)！

若如此，则 CAWCC(r) 的解析式应为：
    0.95·CAP = base + k·MW·(1−r)·f(r)
    → MW*(r) = A / [(1−r)·f(r)]
这与 1/f(r) 不同，且 (1−r) 项在 r 大时显著。

【检验】
比较两种预测式：
    式1: MW* = A / f(r)
    式2: MW* = A' / [(1−r)·f(r)]
看哪个在 10 MW 网格下误差更小。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"

L, CD, CP, CR = 2200.0, 5.0, 180.0, 650.0


def coc(r):
    return min(CD, L / (r * CR + (1 - r) * CP))


def f(r):
    c = coc(r)
    return c / (c - 1.0)


def main() -> None:
    d = pd.read_csv(R2 / "rstar_grid_convergence_table.csv", encoding="utf-8-sig")
    ha = d[d["domain"] == "ha"].sort_values("target_r")
    obs = {float(x["target_r"]): float(x["cawcc_10mw"]) for _, x in ha.iterrows()}

    # 式1 定标
    A1 = obs[0.5] * f(0.5)
    # 式2 定标：MW* = A2 / [(1-r) f(r)]，在 r=0.5 定标
    A2 = obs[0.5] * (1 - 0.5) * f(0.5)

    print(f"10 MW 网格；A1 = {A1:.1f}（式1）；A2 = {A2:.1f}（式2）\n")
    print(f"{'r':>5}{'f':>8}{'(1-r)f':>9}{'式1预测':>10}{'式2预测':>10}{'实测':>7}"
          f"{'式1误差':>9}{'式2误差':>9}")
    print("-" * 72)
    e1 = []
    e2 = []
    for r in sorted(obs):
        p1 = A1 / f(r)
        p2 = A2 / ((1 - r) * f(r))
        o = obs[r]
        d1, d2 = o - p1, o - p2
        e1.append(abs(d1))
        e2.append(abs(d2))
        print(f"{r:>5.1f}{f(r):>8.4f}{(1-r)*f(r):>9.4f}{p1:>10.1f}{p2:>10.1f}"
              f"{o:>7.0f}{d1:>9.1f}{d2:>9.1f}")

    print(f"\n式1 最大绝对误差 {max(e1):.1f} MW；式2 {max(e2):.1f} MW")
    print(f"式1 误差均值 {sum(e1)/len(e1):.1f} MW；式2 {sum(e2)/len(e2):.1f} MW")
    if max(e2) < max(e1):
        print("\n→ 式2（含 (1−r) 项）误差更小，提示城市源取水只计自来水部分。")
    else:
        print("\n→ 式1 更优；(1−r) 项假设不成立。")

    # 第三候选：城市取水 = base + E·f(r)·(1-r)  但 E ∝ MW  → 同上
    # 第四候选：城市取水 = base + MW·c（线性，与 r 无关，因 CoC 变化已被 M 吸收）
    print("\n=== 仅供参考：若城市取水与 r 无关（仅随 MW 线性）===")
    print("  则 CAWCC 应不随 r 变化，但实测从 1200 降到 1110，故不成立。")


if __name__ == "__main__":
    main()
