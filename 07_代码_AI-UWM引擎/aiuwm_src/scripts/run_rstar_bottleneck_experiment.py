# -*- coding: utf-8 -*-
"""实验 R*：水质兼容阈值如何移动承载瓶颈。

【科学问题】
第 7 章（再生水）此前只在一个默认 r 下看容量维，因此没看到 r 本身是承载判据的
驱动变量。本实验把 r（再生水替代率政策）当作**自变量**，回答：

  当城市把再生水替代率目标 r 从低到高推进时，
  (a) 浓缩倍数 CoC 如何变化（解析式已证：r > r* 时跌破设计值）；
  (b) 单位补水需求如何变化（CoC 下降 → M = E·CoC/(CoC-1) 上升）；
  (c) **首失效约束是谁、在哪个容量**——即承载瓶颈是否被 r 推动而迁移。

【设计】
- r ∈ {0.00, 0.10, ..., 0.90}（10 点）
- 容量 ∈ 50..2000 MW，50 MW 步长（40 点）
- 2 域（HA / CO）
- 每点：跑模型 → 取 10 条日尺度约束 → 找首失效
共 2 × 10 × 40 = 800 次运行，约 16 分钟（单次 1.2 s）。

【与既有产物的关系】
不改任何既有文件；新产物写 rstar_*.csv。
约束集沿用 run_r2.daily_constraints()（剔除 max_reuse_utilization，理由见其 docstring）。

【用法】PYTHONPATH="src;scripts" python scripts/run_rstar_bottleneck_experiment.py
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
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
from aiuwm.ai_metrics import summarize_ai_water_kpis  # noqa: E402
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

R_GRID = [round(0.1 * i, 2) for i in range(10)]
CAPACITIES = [float(x) for x in range(50, 2001, 50)]

_W: dict = {}


def _init(domain: str):
    project = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    timeseries = pd.read_csv(R2 / domain / "timeseries.csv")
    constraints = json.loads(
        (R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8")
    )
    _W["project"] = project
    _W["timeseries"] = timeseries
    _W["day_constraints"] = {"constraints": daily_constraints(constraints)}


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
        "total_withdrawal_ml",
        "freshwater_withdrawal_ml",
        "reclaimed_water_use_ml",
        "maximum_daily_withdrawal_ml",
        "unmet_cooling_water_ml",
        "freshwater_dependency_ratio",
        "reclaimed_water_substitution_ratio",
        "urban_water_circularity_ratio",
        "system_reliability_fraction",
        "domestic_unmet_ml",
        "peak_capacity_ratio",
        "max_wtw_utilization",
        "max_wwtw_utilization",
        "max_source_abstraction_ratio",
        "max_local_connection_ratio",
        "max_daily_average_grid_connection_ratio",
        "system_energy_kwh",
        "system_carbon_kg_co2e",
        "it_energy_mwh",
    ):
        rec[key] = kpi.get(key)
    rec["_coc_fallback"] = float(
        pd.to_numeric(
            daily.get(next((c for c in daily.columns if "quality_coc_fallback" in c.lower()), ""),
                      pd.Series([0.0])),
            errors="coerce",
        ).fillna(0).sum()
    ) if any("quality_coc_fallback" in c.lower() for c in daily.columns) else 0.0
    return rec


def _apply_float_tolerance(
    positive: pd.DataFrame, constraints: dict, tol: float = 1e-9
) -> pd.DataFrame:
    """对"≥ 目标值"型约束做浮点容差修正。

    现象：目标的再生水替代率 r 在模型里是精确交付的（如 r=0.1 时交付 0.1），
    但浮点表示会使实际值比目标小 1.11e-16。`find_ai_carrying_capacity` 用严格
    比较，这会让整条容量阶梯在 200 MW 处就判"政策未达标"，得到纯伪结果。
    本函数只在容差范围内把略小的值拉回目标值，不改变任何真实缺口
    （真实缺口量级为 1e-2 ~ 1e-1，比容差大 7 个数量级）。
    """
    out = positive.copy()
    for name, definition in constraints.get("constraints", {}).items():
        if name not in out.columns:
            continue
        if definition.get("operator") not in {">=", ">"}:
            continue
        target = float(definition["value"])
        values = pd.to_numeric(out[name], errors="coerce")
        near = (values < target) & (values > target - tol)
        if near.any():
            out.loc[near, name] = target
    return out


def _load_day_constraints(domain: str, r: float | None = None) -> dict:
    """在主进程里独立加载约束集（ProcessPoolExecutor 的 initializer 不会污染主进程）。

    ``r`` 给定时，把 ``reclaimed_water_substitution_ratio`` 的政策阈值同步设为 r。
    这保证 r 是"城市自己设定的再生水替代率目标"，而不是与固定阈值冲突的
    强制配比——否则 r < 阈值时首失效会恒为 50 MW（政策自我冲突），
    得到的是伪结果而非机制。
    """
    constraints = json.loads(
        (R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8")
    )
    out = daily_constraints(constraints)
    if r is not None and "reclaimed_water_substitution_ratio" in out:
        out["reclaimed_water_substitution_ratio"] = dict(
            out["reclaimed_water_substitution_ratio"]
        )
        out["reclaimed_water_substitution_ratio"]["value"] = float(r)
    return {"constraints": out}


def main() -> None:
    t_start = time.time()
    all_rows: list[dict] = []
    boundary_rows: list[dict] = []
    threshold_rows: list[dict] = []

    for domain in ("ha", "co"):
        print(f"\n{'='*70}\n{domain.upper()}\n{'='*70}", flush=True)
        scan_path = OUT / f"rstar_scan_{domain}.csv"
        jobs = [(r, cap) for r in R_GRID for cap in CAPACITIES]
        t0 = time.time()
        if scan_path.exists():
            frame = pd.read_csv(scan_path)
            print(f"  复用已有扫描: {scan_path.name}  shape={frame.shape}", flush=True)
        else:
            rows: list[dict] = []
            with ProcessPoolExecutor(max_workers=12, initializer=_init, initargs=(domain,)) as ex:
                for i, rec in enumerate(ex.map(_run_one, jobs, chunksize=8), 1):
                    rec["domain"] = domain
                    rows.append(rec)
                    if i % 40 == 0:
                        print(f"  {i}/{len(jobs)}  ({time.time()-t0:.0f}s)", flush=True)
            frame = pd.DataFrame(rows).sort_values(["target_r", "ai_capacity_mw"])
            frame.to_csv(scan_path, index=False, encoding="utf-8-sig")
        rows = frame.to_dict("records")

        day_constraints = _load_day_constraints(domain)

        # 逐 r 求首失效约束与 CAWCC（政策阈值同步为 r）
        for r in R_GRID:
            sub = frame[frame["target_r"] == r].sort_values("ai_capacity_mw").reset_index(drop=True)
            positive = sub[sub["ai_capacity_mw"] >= 50].reset_index(drop=True)
            r_constraints = _load_day_constraints(domain, r=r)
            positive = _apply_float_tolerance(positive, r_constraints)
            found = find_ai_carrying_capacity(positive, r_constraints)
            bnd = summarize_constraint_boundaries(positive, r_constraints)
            threshold_rows.append({
                "domain": domain,
                "target_r": r,
                "cawcc_mw": found["maximum_safe_ai_capacity_mw"],
                "first_failed_mw": found["first_failed_capacity_mw"],
                "limiting_constraint": found["limiting_constraint"],
                "feasible_intervals": json.dumps(found["feasible_intervals_mw"]),
                "mean_coc_at_1200": float(
                    sub.loc[(sub["ai_capacity_mw"] - 1200).abs().idxmin(), "coc_mean"]
                ),
            })
            for _, b in bnd.iterrows():
                boundary_rows.append({
                    "domain": domain,
                    "target_r": r,
                    **b.to_dict(),
                })
            print(
                f"  r={r:.1f}  CAWCC={found['maximum_safe_ai_capacity_mw']}  "
                f"首失效={found['first_failed_capacity_mw']}  "
                f"约束={found['limiting_constraint']}",
                flush=True,
            )

        all_rows.extend(rows)

    pd.DataFrame(threshold_rows).to_csv(
        OUT / "rstar_cawcc_by_r.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(boundary_rows).to_csv(
        OUT / "rstar_boundaries_by_r.csv", index=False, encoding="utf-8-sig"
    )
    print(f"\n全部完成，用时 {time.time()-t_start:.0f}s")


if __name__ == "__main__":
    main()
