# -*- coding: utf-8 -*-
"""E-B4 三杠杆解耦矩阵：处理能力 × 产水量 × 替代率。

【为什么必须做】
主稿主张"三个常被混为一谈的杠杆"：扩再生水**处理能力**（无效）、提再生水
**产量**（有效，移动瓶颈）、提**替代率**（越过 r* 后有害）。但现有证据是三份
彼此独立的一维扫描：

  · reuse_marginal_curve_50mw         处理能力 → 恒为 0
  · reuse_production_marginal_curve   分流比 → +250 MW
  · rstar_physical_cawcc_by_r         替代率 → −100 MW

一维扫描无法回答最关键的交叉问题：**在同一个城市里，三者是否可分离**？
例如，"提产量能否抵消提替代率带来的惩罚"？如果产能扩张让再生水供给变充足，
高 r 下的交付缺口消失，惩罚是否就消失了？这是审稿人一定会问的交互问题。

【本实验要做什么】
二维网格：(WWTW 分流比 f) × (替代率 r)，各 5 档 → 25 组合 × 2 域 × 41 容量点
  f ∈ {0.16（基准）, 0.25, 0.35, 0.45, 0.60}
  r ∈ {0.0, 0.4, 0.6, 0.8, 0.9}
处理能力按既有约定随产量走（1.25 × 产量，日峰值裕度），因此这张图同时固定了
"产能配套"这一维度——即"扩产但不改变产水量"的无效性已在别处单独证明。

产出：
  (a) CAWCC 的二维等值面：哪一维真正移动承载边界
  (b) 纯物理口径下 r 的容量效应随产量的变化：惩罚是否被产量抵消
  (c) 每格的首失效约束：证明"移动瓶颈"与"不移动瓶颈"的差别

【产物】
  lever_decoupling_grid.csv       25×2 行：f、r、两口径 CAWCC、首失效、交付比例
  lever_decoupling_summary.json   交互判定：产量能否抵消替代率惩罚

【用法】
  PYTHONPATH="src;scripts" python scripts/run_lever_decoupling.py --workers 6
"""
from __future__ import annotations

import argparse
import copy
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
R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

CAPACITIES_SCAN = list(np.arange(0.0, 2001.0, 50.0))
POLICY = "reclaimed_water_substitution_ratio"

F_GRID = [0.16, 0.25, 0.35, 0.45, 0.60]
R_GRID = [0.0, 0.4, 0.6, 0.8, 0.9]
CAPACITY_MARGIN = 1.25  # 处理能力 = 产量 × 1.25，沿用 run_reuse_levers_50mw.py

WATER_SIDE = {
    "max_source_abstraction_ratio", "max_wtw_utilization", "max_wwtw_utilization",
    "peak_capacity_ratio", "max_local_connection_ratio", "unmet_cooling_water_ml",
}
GRID_SIDE = {"max_daily_average_grid_connection_ratio"}
SOCIAL_SIDE = {"system_reliability_fraction", "domestic_unmet_ml"}

_W = {}


def _import_engine():
    for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    from aiuwm.ai_capacity import find_ai_carrying_capacity
    from aiuwm.ai_metrics import summarize_ai_water_kpis
    from aiuwm.full_engine import FullAIUWMModel

    return find_ai_carrying_capacity, summarize_ai_water_kpis, FullAIUWMModel


def _constraint_sets(raw: dict) -> tuple[dict, dict]:
    full = {}
    for name, definition in raw["constraints"].items():
        if name == "max_reuse_utilization":
            continue
        full[name] = dict(definition)
    physical = {k: v for k, v in full.items() if k != POLICY}
    return physical, full


def side_of(name: str | None) -> str:
    if not name:
        return "未失效"
    if name in GRID_SIDE:
        return "电网侧"
    if name in WATER_SIDE:
        return "水侧"
    if name in SOCIAL_SIDE:
        return "社会供水"
    if name == POLICY:
        return "政策"
    return "其他"


def _num(value, default: float = float("nan")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _run_cell(job: tuple[str, float, float, float]) -> dict:
    find_ai_carrying_capacity, summarize_ai_water_kpis, FullAIUWMModel = _import_engine()
    domain, f_val, r_val, base_prod = job
    d = _W[domain]
    project = copy.deepcopy(d["project"])

    # 杠杆一+二：分流比决定产量，处理能力按 1.25 倍产量配套
    project["components"]["WWTW1"]["central_reuse_fraction"] = float(f_val)
    production = float(f_val) * base_prod
    project["components"]["CENTRAL_REUSE"]["treatment_capacity_ml_day"] = round(
        production * CAPACITY_MARGIN, 3
    )
    # 杠杆三：替代率
    dc = project["components"]["AI_DC1"]
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(r_val)
    dc["water_sources"]["potable"]["target_fraction"] = float(1.0 - r_val)

    rows = []
    for capacity in CAPACITIES_SCAN:
        trial = copy.deepcopy(project)
        for component in trial["components"].values():
            if component.get("kind") == "data_center":
                component["installed_it_capacity_mw"] = float(capacity)
                component.pop("capacity_schedule", None)
        result = FullAIUWMModel(trial, d["timeseries"]).run()
        record = {"ai_capacity_mw": float(capacity),
                  **summarize_ai_water_kpis(result, trial)}
        rows.append(record)
    scan = pd.DataFrame(rows)

    physical, full = _W["_constraint_sets"][domain]
    p = find_ai_carrying_capacity(scan, physical)
    j = find_ai_carrying_capacity(scan, full)
    p_max = _num(p["maximum_safe_ai_capacity_mw"])
    j_max = _num(j["maximum_safe_ai_capacity_mw"])

    # 交付比例与总取水（在若干容量点上取平均，用于解释机制）
    deliver_col = None
    for cand in ("reclaimed_water_substitution_ratio", "actual_reclaimed_fraction"):
        if cand in scan.columns:
            deliver_col = cand
            break
    sub_col = None
    for cand in ("reclaimed_water_substitution_ratio",):
        if cand in scan.columns:
            sub_col = cand
            break

    return {
        "域": domain,
        "分流比f": float(f_val),
        "替代率r": float(r_val),
        "估计产量_ML_day": production,
        "处理能力_ML_day": production * CAPACITY_MARGIN,
        "CAWCC_物理_MW": p_max,
        "首失效约束_物理": p["limiting_constraint"] or "",
        "侧别_物理": side_of(p["limiting_constraint"]),
        "CAWCC_联合_MW": j_max,
        "首失效约束_联合": j["limiting_constraint"] or "",
        "侧别_联合": side_of(j["limiting_constraint"]),
        "实际替代份额_均值": _num(scan[sub_col].mean()) if sub_col else None,
    }


def prepare_domains() -> dict:
    """准备两域的工程与驱动。

    基准产量取 `run_reuse_levers_50mw.py` 的同一口径：
    0 MW 基线年污水量 ÷ 730 天 × 基准分流比。这里直接用处理能力 ÷ 1.25 反推，
    与既有产物的 `estimated_production_ml_day` 首行一致（HA 32.22 ML/d）。
    """
    from run_r2 import load_domain

    out = {}
    for domain in ("ha", "co"):
        project, timeseries, _raw = load_domain(domain)
        base_prod = float(
            project["components"]["CENTRAL_REUSE"]["treatment_capacity_ml_day"]
        ) / CAPACITY_MARGIN
        out[domain] = {
            "project": project, "timeseries": timeseries,
            "base_prod_ml_day": base_prod if base_prod > 0 else 40.3 / CAPACITY_MARGIN,
        }
    return out


def _init_full(domains: dict, constraint_sets: dict) -> None:
    _W.update(domains)
    _W["_constraint_sets"] = constraint_sets


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
        if _p not in sys.path:
            sys.path.insert(0, _p)

    domains = prepare_domains()
    constraint_sets = {}
    for domain in ("ha", "co"):
        raw = json.loads((R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8"))
        constraint_sets[domain] = _constraint_sets(raw)

    jobs = []
    for domain in ("ha", "co"):
        base_prod = domains[domain]["base_prod_ml_day"]
        for f_val in F_GRID:
            for r_val in R_GRID:
                jobs.append((domain, float(f_val), float(r_val), float(base_prod)))

    print(f"[E-B4] {len(jobs)} 个 (域, f, r) 组合 × {len(CAPACITIES_SCAN)} 容量点 = "
          f"{len(jobs) * len(CAPACITIES_SCAN)} 次仿真")
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init_full,
                             initargs=(domains, constraint_sets)) as pool:
        for i, row in enumerate(pool.map(_run_cell, jobs, chunksize=1), 1):
            rows.append(row)
            if i % 5 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)} {time.time()-t0:.0f}s {row['域']} "
                      f"f={row['分流比f']:.2f} r={row['替代率r']:.1f} "
                      f"→ {row['CAWCC_物理_MW']:.0f} MW ({row['侧别_物理']})", flush=True)

    df = pd.DataFrame(rows).sort_values(["域", "分流比f", "替代率r"])
    df.to_csv(OUT / "lever_decoupling_grid.csv", index=False, encoding="utf-8-sig")
    print(f"[OK] {OUT / 'lever_decoupling_grid.csv'} rows={len(df)}")

    summary: dict = {"分流比网格": F_GRID, "替代率网格": R_GRID,
                     "处理能力配套系数": CAPACITY_MARGIN,
                     "容量网格_MW": [CAPACITIES_SCAN[0], CAPACITIES_SCAN[-1], 50.0],
                     "域": {}}
    for domain in ("ha", "co"):
        sub = df[df["域"] == domain]
        piv = sub.pivot_table(index="替代率r", columns="分流比f",
                              values="CAWCC_物理_MW")
        keep_piv = sub.pivot_table(index="替代率r", columns="分流比f",
                                   values="首失效约束_物理", aggfunc="first")
        # 产量效应：固定 r=0.6，f 从最小到最大的容量差
        prod_effect = {}
        for r_val in R_GRID:
            blk = sub[np.isclose(sub["替代率r"], r_val)].sort_values("分流比f")
            if len(blk) >= 2:
                prod_effect[f"r={r_val:.1f}"] = float(
                    blk["CAWCC_物理_MW"].iloc[-1] - blk["CAWCC_物理_MW"].iloc[0]
                )
        # 替代率效应：固定 f=0.16，r 从 0 到 0.9 的容量差
        ratio_effect = {}
        for f_val in F_GRID:
            blk = sub[np.isclose(sub["分流比f"], f_val)].sort_values("替代率r")
            if len(blk) >= 2:
                ratio_effect[f"f={f_val:.2f}"] = float(
                    blk["CAWCC_物理_MW"].iloc[-1] - blk["CAWCC_物理_MW"].iloc[0]
                )
        # 交互：产量能否抵消替代率惩罚
        offset = {}
        for key in ratio_effect:
            f_val = float(key.split("=")[1])
            offset[key] = prod_effect.get("r=0.6", 0.0) + ratio_effect[key]
        summary["域"][domain] = {
            "CAWCC矩阵_r乘f": {str(round(float(i), 1)): {str(round(float(c), 2)): _num(v)
                                                    for c, v in row.items()}
                            for i, row in piv.iterrows()},
            "首失效矩阵_r乘f": {str(round(float(i), 1)): {str(round(float(c), 2)): str(v)
                                                    for c, v in row.items()}
                            for i, row in keep_piv.iterrows()},
            "产量效应_按r_MW": prod_effect,
            "替代率效应_按f_MW": ratio_effect,
            "CAWCC范围_MW": [float(sub["CAWCC_物理_MW"].min()),
                             float(sub["CAWCC_物理_MW"].max())],
        }
    (OUT / "lever_decoupling_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {OUT / 'lever_decoupling_summary.json'}")
    for domain, s in summary["域"].items():
        print(f"\n  {domain}: CAWCC 范围 {s['CAWCC范围_MW']}")
        print(f"    产量效应（f 最小→最大）: {s['产量效应_按r_MW']}")
        print(f"    替代率效应（r 0→0.9）: {s['替代率效应_按f_MW']}")


if __name__ == "__main__":
    main()
