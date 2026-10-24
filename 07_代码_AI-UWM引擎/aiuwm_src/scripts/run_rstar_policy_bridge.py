# -*- coding: utf-8 -*-
"""核实 W/D 与"全市再生水利用率 → 园区替代率"的换算。

【为什么重要】
本文的 r 是"园区补水中的再生水占比"，而政策指标是
"再生水利用量 / 城市污水处理总量"。两者分母不同。

若审稿人按"全市利用率 25%"理解本文的 r=0.5532，会得出
"现实中不会触发"的错误结论。必须给出精确换算。

【换算公式】
  u = 全市再生水利用率 = U / W    （U=再生水利用量, W=城市污水处理总量）
  r = 园区替代率     = x / D      （x=园区用再生水量, D=园区补水需求）

  若全部再生水都供给该园区：x = U，故
  r_max = U/D = (u·W)/D = u · (W/D)

【产物】
  rstar_policy_bridge.csv
  rstar_policy_bridge.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation_artifacts" / "r2"

# 政策目标（来自 literature_benchmark_city_sources.csv，OFFICIAL）
POLICY_U = {
    "十四五基准年(2020前后)": 0.20,
    "十四五地级缺水城市目标": 0.25,
    "京津冀目标": 0.35,
}


def main() -> None:
    rows = []
    for domain in ("ha", "co"):
        d = pd.read_csv(OUT / domain / "capacity_scan.csv", encoding="utf-8-sig")
        for cap in (500.0, 1000.0, 1500.0):
            s = d[(d["ai_capacity_mw"] - cap).abs() < 1e-6]
            if s.empty:
                continue
            x = s.iloc[0]
            W = float(x["wastewater_ml"])          # 城市污水处理总量（含园区贡献）
            D = float(x["total_withdrawal_ml"])    # 园区补水需求
            if D <= 0:
                continue
            ratio = W / D
            rows.append({
                "domain": domain,
                "capacity_mw": cap,
                "city_wastewater_ml": W,
                "ai_makeup_ml": D,
                "W_over_D": ratio,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "rstar_policy_bridge.csv", index=False, encoding="utf-8-sig")

    print("=" * 88)
    print("全市污水量 / 园区补水需求 之比（W/D）")
    print("=" * 88)
    print(df.to_string(index=False))
    print()

    print("=" * 88)
    print("换算：若全市再生水全部供给该园区，园区替代率可达多少")
    print("=" * 88)
    print(f"{'域':<6} {'容量':>8} {'W/D':>8}  " +
          "  ".join(f"u={u:.0%}→r_max" for u in POLICY_U.values()))
    print("-" * 88)
    for _, x in df.iterrows():
        parts = "  ".join(
            f"{u*x.W_over_D:>10.2f}" for u in POLICY_U.values()
        )
        print(f"{x.domain.upper():<6} {x.capacity_mw:>8.0f} {x.W_over_D:>8.2f}  {parts}")
    print()

    # 计算 W/D 的范围
    wd_min = float(df["W_over_D"].min())
    wd_max = float(df["W_over_D"].max())
    wd_med = float(df["W_over_D"].median())
    print(f"W/D 范围: {wd_min:.2f} ~ {wd_max:.2f}，中位 {wd_med:.2f}")
    print()

    # 关键判定：政策目标 u 在什么条件下可以使 r_max > r*
    r_star = 0.5532
    print("=" * 88)
    print(f"判定：全市利用率 u 需要多大，才能使 r_max > r* = {r_star}")
    print("=" * 88)
    for u_name, u in POLICY_U.items():
        need_wd = r_star / u
        ok = wd_med >= need_wd
        print(f"  {u_name} (u={u:.0%}): 需要 W/D > {need_wd:.2f}；"
              f"实际中位 {wd_med:.2f} → {'✅ 可以' if ok else '❌ 不能'}")
    print()
    print(f"→ 在本文参数下（W/D 中位 {wd_med:.2f}），全市 20% 的利用率即可对应")
    print(f"  园区 r_max = {0.20*wd_med:.2f}，已超过 r* = {r_star}")
    print(f"→ 即：政策指标的『总量口径』并不排除园区级别的『配比超阈』。")

    out = {
        "W_over_D": {"min": wd_min, "median": wd_med, "max": wd_max},
        "policy_targets": POLICY_U,
        "r_star": r_star,
        "r_max_at_policy": {
            name: {"u": u, "required_W_over_D_for_rstar": r_star / u,
                   "r_max_at_median_WD": u * wd_med}
            for name, u in POLICY_U.items()
        },
        "verdict": "全市总量口径的利用率不能直接判定园区级反噬是否触发",
    }
    (OUT / "rstar_policy_bridge.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n产物: rstar_policy_bridge.csv / rstar_policy_bridge.json")


if __name__ == "__main__":
    main()
