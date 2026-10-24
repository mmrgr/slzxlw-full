# -*- coding: utf-8 -*-
"""网格稳健性检验：−100 MW 的物理效应是真效应还是网格伪影？

【为什么这是致命检验】
本文全部容量结论基于 **50 MW 步长**的扫描。而核心物理效应只有 **−100 MW**，
恰好等于 **2 个网格步**。

审稿人完全可以说：
  「你的效应量只有 2 个网格步，换个网格就变了，这不是物理效应而是量化噪声。」

【设计】
把容量网格从 50 MW 细化到 **25 MW**，在关键 r 值上重算纯物理 CAWCC。
若 CAWCC 仍落在 −100 MW 附近（如 1100），说明效应稳健；
若显著偏移（如 1125 或 1050），说明存在网格依赖。

进一步用 **10 MW** 网格做交叉验证（只在关键区间 1000–1300 MW，
避免全扫描的计算量爆炸）。

【为什么高分辨率会更好】
CAWCC 的定义是"最大的可行容量点"。网格越细，该点越接近真实边界。
若真实边界在 1103 MW，50 MW 网格会报 1100，25 MW 网格也报 1100，
但 10 MW 网格会报 1100。若真实边界在 1087，50 MW 报 1050，25 MW 报 1075，
10 MW 报 1080——这时网格依赖就暴露了。

【产物】
  rstar_grid_convergence_25mw.csv
  rstar_grid_convergence_10mw.csv
  rstar_grid_convergence_summary.json

【用法】PYTHONPATH="src;scripts" python scripts/run_rstar_grid_convergence.py
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
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
from aiuwm.ai_metrics import summarize_ai_water_kpis  # noqa: E402
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

# 关键 r 值：跨越 r*=0.5532 的两侧
R_GRID = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9]

# 50 MW 网格（既有主结果）作为参照
CAP_50 = [float(x) for x in range(50, 2001, 50)]
# 25 MW 网格：全范围
CAP_25 = [float(x) for x in range(50, 2001, 25)]
# 10 MW 网格：只覆盖 CAWCC 附近的关键区间（HA 1000-1300 / CO 1300-1600 的并集 1000-1600）
CAP_10 = [float(x) for x in range(1000, 1601, 10)]

_W: dict = {}


def _init(domain: str):
    _W["project"] = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    _W["timeseries"] = pd.read_csv(R2 / "timeseries.csv") if False else pd.read_csv(
        R2 / domain / "timeseries.csv"
    )
    raw = json.loads((R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8"))
    day = daily_constraints(raw)
    # 纯物理口径：剔除政策约束
    _W["physical"] = {
        "constraints": {k: v for k, v in day.items()
                        if k != "reclaimed_water_substitution_ratio"}
    }


def _run_one(job: tuple[float, float]) -> dict:
    r, capacity = job
    cfg = json.loads(json.dumps(_W["project"]))
    for comp in cfg["components"].values():
        if comp.get("kind") != "data_center":
            continue
        comp["installed_it_capacity_mw"] = float(capacity)
        comp.pop("capacity_schedule", None)
        src = comp.get("water_sources", {})
        if "reclaimed" in src:
            src["reclaimed"]["target_fraction"] = float(r)
        if "potable" in src:
            src["potable"]["target_fraction"] = float(1.0 - r)

    result = FullAIUWMModel(cfg, _W["timeseries"]).run()
    kpi = summarize_ai_water_kpis(result, cfg)
    daily = result.data_center_daily
    coc_col = next((c for c in daily.columns if "cycles_of_concentration" in c.lower()), None)
    coc = float(pd.to_numeric(daily[coc_col], errors="coerce").mean()) if coc_col else float("nan")

    rec = {"target_r": r, "ai_capacity_mw": capacity, "coc_mean": coc}
    for key in (
        "total_withdrawal_ml", "freshwater_withdrawal_ml", "reclaimed_water_use_ml",
        "unmet_cooling_water_ml", "system_reliability_fraction", "domestic_unmet_ml",
        "peak_capacity_ratio", "max_wtw_utilization", "max_wwtw_utilization",
        "max_source_abstraction_ratio", "max_local_connection_ratio",
        "max_daily_average_grid_connection_ratio", "reclaimed_water_substitution_ratio",
    ):
        rec[key] = kpi.get(key)
    return rec


def _scan(domain: str, caps: list[float], label: str, workers: int = 12) -> pd.DataFrame:
    jobs = [(r, cap) for r in R_GRID for cap in caps]
    rows = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(domain,)) as ex:
        for i, rec in enumerate(ex.map(_run_one, jobs, chunksize=16), 1):
            rec["domain"] = domain
            rows.append(rec)
            if i % 200 == 0:
                print(f"    {label} {i}/{len(jobs)}  ({time.time()-t0:.0f}s)", flush=True)
    return pd.DataFrame(rows)


def _cawcc(frame: pd.DataFrame, constraints: dict) -> dict:
    """在给定扫描上求纯物理 CAWCC。"""
    positive = frame[frame["ai_capacity_mw"] >= 50].sort_values("ai_capacity_mw")
    positive = positive.reset_index(drop=True)
    # 浮点容差
    for name, d in constraints.get("constraints", {}).items():
        if name not in positive.columns or d.get("operator") not in {">=", ">"}:
            continue
        target = float(d["value"])
        vals = pd.to_numeric(positive[name], errors="coerce")
        near = (vals < target) & (vals > target - 1e-9)
        if near.any():
            positive.loc[near, name] = target
    found = find_ai_carrying_capacity(positive, constraints)
    return {
        "cawcc_mw": found["maximum_safe_ai_capacity_mw"],
        "first_failed_mw": found["first_failed_capacity_mw"],
        "limiting_constraint": found["limiting_constraint"],
    }


def main() -> None:
    summary: dict = {"r_grid": R_GRID, "grids": {}}

    for label, caps in (("50mw", CAP_50), ("25mw", CAP_25), ("10mw", CAP_10)):
        summary["grids"][label] = {}
        print(f"\n{'='*76}")
        print(f"网格 = {label}  ({len(caps)} 个容量点)")
        print(f"{'='*76}")

        frames = {}
        out_path = OUT / f"rstar_grid_convergence_{label}.csv"
        if out_path.exists():
            all_df = pd.read_csv(out_path)
            print(f"  复用已有扫描: {out_path.name} ({len(all_df)} 行)")
            for dom in ("ha", "co"):
                frames[dom] = all_df[all_df["domain"] == dom]
        else:
            parts = []
            for dom in ("ha", "co"):
                print(f"  扫描 {dom.upper()} ...", flush=True)
                df = _scan(dom, caps, f"{label}-{dom}")
                frames[dom] = df
                parts.append(df)
            all_df = pd.concat(parts, ignore_index=True)
            all_df.to_csv(out_path, index=False, encoding="utf-8-sig")
            print(f"  -> {out_path.name} ({len(all_df)} 行)")

        # 逐域逐 r 求 CAWCC
        for dom in ("ha", "co"):
            _init(dom)
            phys = _W["physical"]
            for r in R_GRID:
                sub = frames[dom][(frames[dom]["target_r"] - r).abs() < 1e-9]
                if sub.empty:
                    continue
                res = _cawcc(sub, phys)
                summary["grids"][label].setdefault(dom, {})[str(r)] = res
                print(f"  {dom.upper()} r={r:.1f}: CAWCC={res['cawcc_mw']}  "
                      f"首失效={res['first_failed_mw']}  {res['limiting_constraint']}")

    # ---------------- 收敛性比较 ----------------
    print("\n" + "=" * 84)
    print("网格收敛性比较：CAWCC 随网格细化如何变化")
    print("=" * 84)
    for dom in ("ha", "co"):
        print(f"\n--- {dom.upper()} ---")
        print(f"{'r':>5} {'50MW':>8} {'25MW':>8} {'10MW':>8} {'50→25':>8} {'25→10':>8}")
        for r in R_GRID:
            row = []
            for label in ("50mw", "25mw", "10mw"):
                v = summary["grids"][label].get(dom, {}).get(str(r), {}).get("cawcc_mw")
                row.append(v)
            d1 = (row[1] - row[0]) if (row[0] is not None and row[1] is not None) else None
            d2 = (row[2] - row[1]) if (row[1] is not None and row[2] is not None) else None
            print(f"{r:5.1f} {str(row[0]):>8} {str(row[1]):>8} {str(row[2]):>8} "
                  f"{('' if d1 is None else f'{d1:+.0f}'):>8} "
                  f"{('' if d2 is None else f'{d2:+.0f}'):>8}")

    # ---------------- 关键判定 ----------------
    print("\n" + "=" * 84)
    print("判定：−100 MW 效应是否网格稳健？")
    print("=" * 84)
    verdict = {}
    for dom in ("ha", "co"):
        v50 = summary["grids"]["50mw"].get(dom, {})
        v25 = summary["grids"]["25mw"].get(dom, {})
        base50 = v50.get("0.0", {}).get("cawcc_mw")
        base25 = v25.get("0.0", {}).get("cawcc_mw")
        drops = {}
        for r in ("0.6", "0.7", "0.8", "0.9"):
            a = v50.get(r, {}).get("cawcc_mw")
            b = v25.get(r, {}).get("cawcc_mw")
            if a is not None and base50 is not None:
                drops.setdefault("50mw", {})[r] = a - base50
            if b is not None and base25 is not None:
                drops.setdefault("25mw", {})[r] = b - base25
        verdict[dom] = {"baseline_50": base50, "baseline_25": base25, "drops": drops}
        print(f"\n{dom.upper()}:")
        print(f"  基线 CAWCC: 50MW={base50}, 25MW={base25}")
        for r in ("0.6", "0.7", "0.8", "0.9"):
            d50 = drops.get("50mw", {}).get(r)
            d25 = drops.get("25mw", {}).get(r)
            print(f"  r={r}: 相对基线 50MW={d50:+.0f}, 25MW={d25:+.0f}"
                  f"  {'✅ 一致' if d50 == d25 else '⚠ 有差异'}")

    # 结论
    ha50 = verdict["ha"]["drops"].get("50mw", {}).get("0.9")
    ha25 = verdict["ha"]["drops"].get("25mw", {}).get("0.9")
    robust = (ha50 is not None and ha25 is not None and abs(ha50 - ha25) <= 25)
    print("\n" + "-" * 84)
    print(f"总体判定：HA 在 r=0.9 的降幅 50MW={ha50}, 25MW={ha25}")
    print(f"  → {'✅ 网格稳健（差异 ≤ 一个细网格步）' if robust else '❌ 存在网格依赖'}")

    summary["verdict"] = verdict
    summary["grid_robust"] = bool(robust)
    (OUT / "rstar_grid_convergence_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n产物: rstar_grid_convergence_{{50mw,25mw,10mw}}.csv + summary.json")


if __name__ == "__main__":
    main()
