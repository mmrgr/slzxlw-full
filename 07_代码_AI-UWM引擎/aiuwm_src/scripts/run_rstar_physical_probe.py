# -*- coding: utf-8 -*-
"""纯物理口径下的 r* 响应：分离政策约束，证明物理承载能力真的下降。

【为什么要做这个实验】
`run_rstar_bottleneck_experiment.py` 得到的结果显示：r ≥ 0.7 时，首失效约束变成
`reclaimed_water_substitution_ratio` 自身。这有一个致命的解释漏洞——

    政策约束失效 = "实际交付达不到目标 r"，
    而目标 r 正是我们自己调高的。这是自指，不是物理。

审稿人会直接说："你只是把目标定得更高，当然更容易达不到。"

【本实验要回答】
在**完全剔除政策约束**的纯物理口径下：
  (a) CAWCC 是否仍随 r 上升而下降？
  (b) 若下降，是哪个物理约束先失效？
  (c) 同一容量点上，物理约束取值是否随 r 单调恶化？

只有 (a)(b)(c) 都为"是"，"水质反噬压制物理承载能力"才成立。

【做法】
复用已保存的 rstar_scan_{ha,co}.csv（2 域 × 10 r × 40 容量点，无需重跑模型），
用 run_r2.daily_constraints 剔除政策约束后重新求阈值。

【产物】
  rstar_physical_cawcc_by_r.csv       每个 r 的纯物理 CAWCC 与首失效约束
  rstar_physical_boundaries_by_r.csv  每个 r 的逐约束首失效容量
  rstar_confound_control.csv          同一容量点跨 r 的物理约束取值（混淆排除）
  rstar_backlash_decomposition.csv    反噬贡献分解

【用法】PYTHONPATH="src;scripts" python scripts/run_rstar_physical_probe.py
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
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from run_r2 import daily_constraints  # noqa: E402
from aiuwm.ai_capacity import (  # noqa: E402
    find_ai_carrying_capacity,
    summarize_constraint_boundaries,
)

R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

R_GRID = [round(0.1 * i, 2) for i in range(10)]
# 政策约束名，纯物理口径要剔除它
POLICY = "reclaimed_water_substitution_ratio"
# 混淆排除使用的关键容量点
KEY_CAPACITIES = [1200.0, 1600.0]


def load_constraints(domain: str, physical_only: bool) -> dict:
    """加载约束集。physical_only=True 时剔除再生水替代率政策约束。"""
    raw = json.loads(
        (R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8")
    )
    out = daily_constraints(raw)
    if physical_only:
        out = {k: v for k, v in out.items() if k != POLICY}
    return {"constraints": out}


def apply_float_tolerance(df: pd.DataFrame, constraints: dict, tol: float = 1e-9) -> pd.DataFrame:
    """对 ">=" 型约束做浮点容差修正（模型交付与目标之间存在 1.1e-16 级舍入）。"""
    out = df.copy()
    for name, definition in constraints.get("constraints", {}).items():
        if name not in out.columns or definition.get("operator") not in {">=", ">"}:
            continue
        target = float(definition["value"])
        values = pd.to_numeric(out[name], errors="coerce")
        near = (values < target) & (values > target - tol)
        if near.any():
            out.loc[near, name] = target
    return out


def main() -> None:
    physical_rows: list[dict] = []
    boundary_rows: list[dict] = []
    cawcc_rows: list[dict] = []

    for domain in ("ha", "co"):
        scan_path = OUT / f"rstar_scan_{domain}.csv"
        if not scan_path.exists():
            raise SystemExit(f"缺少扫描产物: {scan_path}（请先跑 run_rstar_bottleneck_experiment.py）")
        frame = pd.read_csv(scan_path)
        print(f"\n{'='*74}\n{domain.upper()}  (scan shape={frame.shape})\n{'='*74}", flush=True)

        # 纯物理口径：政策约束阈值不随 r 变（因为它已被剔除），故只需加载一次
        phys = load_constraints(domain, physical_only=True)
        joint = load_constraints(domain, physical_only=False)

        print(f"{'r':>5} {'联合CAWCC':>10} {'联合首失效':>10} {'联合约束':>34} "
              f"{'物理CAWCC':>10} {'物理首失效':>10} {'物理约束':>30}", flush=True)

        for r in R_GRID:
            sub = frame[frame["target_r"] == r].sort_values("ai_capacity_mw").reset_index(drop=True)
            positive = sub[sub["ai_capacity_mw"] >= 50].reset_index(drop=True)

            # --- 联合口径（政策阈值同步为 r）---
            joint_r = json.loads(json.dumps(joint))
            if POLICY in joint_r["constraints"]:
                joint_r["constraints"][POLICY] = dict(joint_r["constraints"][POLICY])
                joint_r["constraints"][POLICY]["value"] = float(r)
            j_positive = apply_float_tolerance(positive, joint_r)
            j_found = find_ai_carrying_capacity(j_positive, joint_r)

            # --- 纯物理口径 ---
            p_positive = apply_float_tolerance(positive, phys)
            p_found = find_ai_carrying_capacity(p_positive, phys)
            p_bnd = summarize_constraint_boundaries(p_positive, phys)

            cawcc_rows.append({
                "domain": domain,
                "target_r": r,
                "joint_cawcc_mw": j_found["maximum_safe_ai_capacity_mw"],
                "joint_first_failed_mw": j_found["first_failed_capacity_mw"],
                "joint_limiting_constraint": j_found["limiting_constraint"],
                "physical_cawcc_mw": p_found["maximum_safe_ai_capacity_mw"],
                "physical_first_failed_mw": p_found["first_failed_capacity_mw"],
                "physical_limiting_constraint": p_found["limiting_constraint"],
            })
            for _, b in p_bnd.iterrows():
                boundary_rows.append({
                    "domain": domain,
                    "target_r": r,
                    "scope": "physical",
                    **b.to_dict(),
                })

            # 混淆排除：同一容量点跨 r 的物理约束取值
            for cap in KEY_CAPACITIES:
                row = sub[(sub["ai_capacity_mw"] - cap).abs() < 1e-6]
                if row.empty:
                    continue
                x = row.iloc[0]
                physical_rows.append({
                    "domain": domain,
                    "capacity_mw": cap,
                    "target_r": r,
                    "mean_coc": x.get("coc_mean"),
                    "max_source_abstraction_ratio": x.get("max_source_abstraction_ratio"),
                    "max_wtw_utilization": x.get("max_wtw_utilization"),
                    "peak_capacity_ratio": x.get("peak_capacity_ratio"),
                    "max_local_connection_ratio": x.get("max_local_connection_ratio"),
                    "max_daily_average_grid_connection_ratio": x.get(
                        "max_daily_average_grid_connection_ratio"
                    ),
                    "total_withdrawal_ml": x.get("total_withdrawal_ml"),
                    "freshwater_withdrawal_ml": x.get("freshwater_withdrawal_ml"),
                    "reclaimed_water_use_ml": x.get("reclaimed_water_use_ml"),
                    "actual_reclaimed_fraction": x.get("reclaimed_water_substitution_ratio"),
                })

            print(f"{r:5.1f} {str(j_found['maximum_safe_ai_capacity_mw']):>10} "
                  f"{str(j_found['first_failed_capacity_mw']):>10} "
                  f"{str(j_found['limiting_constraint']):>34} "
                  f"{str(p_found['maximum_safe_ai_capacity_mw']):>10} "
                  f"{str(p_found['first_failed_capacity_mw']):>10} "
                  f"{str(p_found['limiting_constraint']):>30}", flush=True)

    cawcc_df = pd.DataFrame(cawcc_rows)
    cawcc_df.to_csv(OUT / "rstar_physical_cawcc_by_r.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(boundary_rows).to_csv(
        OUT / "rstar_physical_boundaries_by_r.csv", index=False, encoding="utf-8-sig"
    )
    confound_df = pd.DataFrame(physical_rows)
    confound_df.to_csv(OUT / "rstar_confound_control.csv", index=False, encoding="utf-8-sig")

    # ---- 反噬贡献分解 ----
    decomp_rows: list[dict] = []
    for domain in ("ha", "co"):
        frame = pd.read_csv(OUT / f"rstar_scan_{domain}.csv")
        for cap in KEY_CAPACITIES:
            base = frame[(frame["target_r"] == 0.0) & ((frame["ai_capacity_mw"] - cap).abs() < 1e-6)]
            if base.empty:
                continue
            base_total = float(base.iloc[0]["total_withdrawal_ml"])
            for r in R_GRID:
                row = frame[(frame["target_r"] == r) & ((frame["ai_capacity_mw"] - cap).abs() < 1e-6)]
                if row.empty:
                    continue
                x = row.iloc[0]
                total = float(x["total_withdrawal_ml"])
                coc = float(x["coc_mean"])
                # M = E*CoC/(CoC-1)  =>  E = M*(CoC-1)/CoC
                evaporation = total * (coc - 1.0) / coc if coc > 1.0 else float("nan")
                decomp_rows.append({
                    "domain": domain,
                    "capacity_mw": cap,
                    "target_r": r,
                    "coc_mean": coc,
                    "total_withdrawal_ml": total,
                    "baseline_withdrawal_ml": base_total,
                    "backlash_ml": total - base_total,
                    "backlash_pct": 100.0 * (total / base_total - 1.0) if base_total else float("nan"),
                    "implied_evaporation_ml": evaporation,
                    "watering_penalty_pct": 100.0 * (
                        (coc / (coc - 1.0)) / (5.0 / 4.0) - 1.0
                    ) if coc > 1.0 else float("nan"),
                })
    pd.DataFrame(decomp_rows).to_csv(
        OUT / "rstar_backlash_decomposition.csv", index=False, encoding="utf-8-sig"
    )

    # ---- 判定输出 ----
    print("\n" + "=" * 78)
    print("判定 A：纯物理口径下 CAWCC 是否随 r 下降？")
    print("=" * 78)
    for domain in ("ha", "co"):
        d = cawcc_df[cawcc_df["domain"] == domain].sort_values("target_r")
        lo = d[d["target_r"] <= 0.5]["physical_cawcc_mw"]
        hi = d[d["target_r"] >= 0.7]["physical_cawcc_mw"]
        print(f"  {domain.upper()}: r<=0.5 -> {sorted(set(lo.dropna()))}   "
              f"r>=0.7 -> {list(hi)}")

    print("\n" + "=" * 78)
    print("判定 B：同一容量点上，物理约束是否随 r 单调恶化？")
    print("=" * 78)
    for domain in ("ha", "co"):
        for cap in KEY_CAPACITIES:
            sub = confound_df[(confound_df["domain"] == domain)
                              & ((confound_df["capacity_mw"] - cap).abs() < 1e-6)]
            if sub.empty:
                continue
            sub = sub.sort_values("target_r")
            src = pd.to_numeric(sub["max_source_abstraction_ratio"], errors="coerce")
            wtw = pd.to_numeric(sub["max_wtw_utilization"], errors="coerce")
            grid = pd.to_numeric(sub["max_daily_average_grid_connection_ratio"], errors="coerce")
            print(f"  {domain.upper()} {cap:.0f}MW: 水源比 {src.iloc[0]:.4f}->{src.iloc[-1]:.4f} "
                  f"(Δ{src.iloc[-1]-src.iloc[0]:+.4f}) | wtw {wtw.iloc[0]:.4f}->{wtw.iloc[-1]:.4f} "
                  f"(Δ{wtw.iloc[-1]-wtw.iloc[0]:+.4f}) | 电网 {grid.iloc[0]:.4f}->{grid.iloc[-1]:.4f} "
                  f"(Δ{grid.iloc[-1]-grid.iloc[0]:+.4f})")

    print("\n" + "=" * 78)
    print("判定 C：反噬贡献在 r<=r* 是否精确为 0？")
    print("=" * 78)
    dec = pd.DataFrame(decomp_rows)
    dec = dec.drop_duplicates(subset=["domain", "capacity_mw", "target_r"])
    for domain in ("ha", "co"):
        for cap in KEY_CAPACITIES:
            sub = dec[(dec["domain"] == domain) & ((dec["capacity_mw"] - cap).abs() < 1e-6)]
            if sub.empty:
                continue
            sub = sub.sort_values("target_r")
            below = sub[sub["target_r"] <= 0.5]["backlash_ml"]
            above = sub[sub["target_r"] >= 0.7]["backlash_ml"]
            print(f"  {domain.upper()} {cap:.0f}MW: r<=0.5 最大反噬 = {below.abs().max():.3e} ML  "
                  f"(应≈0) | r>=0.7 范围 = {above.min():.1f} ~ {above.max():.1f} ML")

    print(f"\n产物已写入 {OUT}")
    for name in (
        "rstar_physical_cawcc_by_r.csv",
        "rstar_physical_boundaries_by_r.csv",
        "rstar_confound_control.csv",
        "rstar_backlash_decomposition.csv",
    ):
        print(f"  - {name}")


if __name__ == "__main__":
    main()
