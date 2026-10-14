"""A24b-fix: 精确测量 surplus 分支的临界 pool_scale (经验值, 不用理论值).

【为什么要修】
external_validity.py 用了 A17 记录的【理论】阈值 elig/P0 = 2.3841(ha) / 2.5667(co)。
但实测 supply_state_regimes.csv 显示 surplus 在 pool_scale=2.0 就已出现(23/64), 早于 2.3841
⇒ 理论阈值与经验阈值不一致, 必须改用**经验测量值**, 否则会高估 surplus 门槛、低估 surplus 现实占比。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A13 = ROOT / "A13_可靠性机制"
ss = pd.read_csv(A13 / "supply_state_regimes.csv", encoding="utf-8-sig")

out = {}
for dom in ("ha", "co"):
    d = ss[ss.domain == dom].copy()
    d["surp"] = d.displaced_ml.abs() < 1e-6
    g = d.groupby("pool_scale").surp.agg(["size", "sum"])
    g["frac"] = g["sum"] / g["size"]
    print(f"\n=== D-{dom.upper()} 各 pool_scale 的 surplus 占比 ===")
    print(g.round(3).to_string())
    # 首次出现 surplus 的 pool_scale
    first = g[g["sum"] > 0].index.min()
    # 50% 门槛
    half = g[g["frac"] >= 0.5]
    half_th = float(half.index.min()) if len(half) else float("nan")
    print(f"  surplus 首次出现: {first}")
    print(f"  surplus 占比>=50% 的最小 pool_scale: {half_th}")
    out[dom] = {"first_appearance": float(first),
                "half_threshold": half_th,
                "grid": {str(k): float(v) for k, v in g["frac"].items()}}

summary = {
    "note": "经验测量的 surplus 阈值; 与 A17 记录的【理论】elig/P0 不同, 外部效度计算必须用经验值",
    "theoretical_elig_over_P0": {"ha": 2.3841, "co": 2.5667},
    "empirical": out,
    "implication": (
        "理论值 2.3841/2.5667 高于经验首次出现值 => 用理论值会【高估】surplus 门槛、"
        "【低估】现实 surplus 占比。external_validity.py 已改用经验值重算。"),
}
(HERE / "surplus_threshold_check.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n[write] surplus_threshold_check.json")
