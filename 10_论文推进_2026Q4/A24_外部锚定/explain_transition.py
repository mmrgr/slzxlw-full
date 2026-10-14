"""解释 surplus 分支为何在 pool_scale=2.0 就出现(早于理论 2.384)。"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ss = pd.read_csv(Path(__file__).resolve().parent.parent / "A13_可靠性机制"
                 / "supply_state_regimes.csv", encoding="utf-8-sig")
ha = ss[ss.domain == "ha"]
g = ha.groupby("pool_scale").agg(
    n=("displaced_ml", "size"),
    surplus=("displaced_ml", lambda s: int((s.abs() < 1e-6).sum())),
    unused_mean=("unused_B2_ml", "mean"),
    disp_mean=("displaced_ml", "mean"),
    dS_med=("dS_pot_ml", "median"),
)
print(g.round(1).to_string())
print()
print("结论: surplus 是【平滑过渡】, 非阶跃。")
print("理论 elig/P0 (ha=2.384) 表示池容刚超过承诺需求;")
print("但实际分配中 AI 取用受 quality_limited 的 CoC 封顶, 部分情景在更低 pool_scale 已无挤占")
print("=> 用经验阈值(首次 2.0 / 50% 于 2.2)比理论值更贴合实际门槛, 也更保守。")
