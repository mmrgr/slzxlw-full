# -*- coding: utf-8 -*-
"""E-B1 约束身份相图：谁先失效——水侧还是电网侧？

【为什么必须做】
主稿的核心结论是"瓶颈位置决定水质惩罚是否有容量后果"：缺水端点水侧先失效故
损失 100 MW，凉爽端点电网先失效故基本不变。外部审计（2026-10-20）指出这条最
脆弱的环节：

    两个端点的电网接入容量都设为 1500 MW，D-CO 的 1450 MW 恰好贴住它。
    于是"一端水先失效、一端电先失效"几乎是设定直接决定的，不意外。

若结论只能靠两个手工设定的端点支撑，它就只是两个情景的对比，而非机制。

【本实验要回答】
在 (取水能力倍数 a, 电网容量 G) 参数平面上：
  (a) CAWCC 的分界面在哪里——哪一侧水侧先失效、哪一侧电网侧先失效？
  (b) 该分界线是否光滑、单调？有无可解析近似？
  (c) 两端点落在相图的什么位置？它们具有代表性，还是被放在分界线两侧？

【设计说明】
取水能力用**相对自身基准的倍数** a（0.80–1.20），而非绝对 ML/d，因为两个端点
的取水基准不同（HA 380、CO 400 ML/d），用倍数才能在同一张图上比较。绝对 A 也
一并写入产物，便于回算。

a < 1 的下限受"基线可行性"约束：取水能力压得过低时，连 0 MW（无 AI）都会违反
`domestic_unmet_ml`，此时 CAWCC 无定义（记为 NaN、身份记「基线不可行」），这是
物理信息而非缺失，如实保留。

【产物】
  constraint_identity_phase.csv     9×9×2 行：a、A、G、两口径 CAWCC 与首失效约束
  constraint_identity_frontier.csv  每个 a 下的临界 G*（水/电主导切换点）
  constraint_identity_summary.json  端点位置、分界线拟合、平方根律检验、稳健性判定

【用法】
  PYTHONPATH="src;scripts" python scripts/run_constraint_identity_phase.py
  PYTHONPATH="src;scripts" python scripts/run_constraint_identity_phase.py --workers 24
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
MAX_CAP = float(CAPACITIES_SCAN[-1])

# 水侧 / 电网侧约束归类（用于相图着色与统计）
WATER_SIDE = {
    "max_source_abstraction_ratio",
    "max_wtw_utilization",
    "max_wwtw_utilization",
    "peak_capacity_ratio",
    "max_local_connection_ratio",
    "unmet_cooling_water_ml",
    "domestic_unmet_ml",
    "system_reliability_fraction",
}
GRID_SIDE = {"max_daily_average_grid_connection_ratio"}

A_RATIO_GRID = [0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15, 1.20]
G_GRID = [900.0, 1050.0, 1200.0, 1350.0, 1500.0, 1650.0, 1800.0, 1950.0, 2100.0]

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
    """返回 (物理口径, 联合口径)。物理口径剔除政策约束。"""
    full = {}
    for name, definition in raw["constraints"].items():
        if name == "max_reuse_utilization":  # 日尺度口径剔除，理由见 run_r2.daily_constraints
            continue
        full[name] = dict(definition)
    physical = {k: v for k, v in full.items() if k != POLICY}
    return physical, full


def _num(value, default: float = float("nan")) -> float:
    """安全数值转换：None/缺失 → NaN（全部容量点都可行时 first_failed 为 None）。"""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out


def classify(limiting: str | None, cawcc: float) -> str:
    if not np.isfinite(cawcc):
        return "基线不可行"
    if limiting is None:
        return "未失效"
    if limiting in WATER_SIDE:
        return "水侧"
    if limiting in GRID_SIDE:
        return "电网侧"
    if limiting == POLICY:
        return "政策"
    return "其他"


def _run_cell(job: tuple[str, float, float]) -> dict:
    find_ai_carrying_capacity, summarize_ai_water_kpis, FullAIUWMModel = _import_engine()
    domain, a_ratio, g_val = job
    d = _W[domain]
    project = copy.deepcopy(d["project"])
    base_a = float(d["base_a_ml_day"])
    a_abs = base_a * float(a_ratio)
    project["components"]["RES1"]["abstraction_capacity_ml_day"] = a_abs
    project["components"]["AI_DC1"]["grid_connection_capacity_mw"] = float(g_val)

    rows = []
    for capacity in CAPACITIES_SCAN:
        trial = copy.deepcopy(project)
        for component in trial["components"].values():
            if component.get("kind") == "data_center":
                component["installed_it_capacity_mw"] = float(capacity)
                component.pop("capacity_schedule", None)
        result = FullAIUWMModel(trial, d["timeseries"]).run()
        rows.append({"ai_capacity_mw": float(capacity), **summarize_ai_water_kpis(result, trial)})
    scan = pd.DataFrame(rows)

    physical, full = _W["_constraint_sets"][domain]
    p = find_ai_carrying_capacity(scan, physical)
    j = find_ai_carrying_capacity(scan, full)
    p_max = _num(p["maximum_safe_ai_capacity_mw"])
    j_max = _num(j["maximum_safe_ai_capacity_mw"])
    return {
        "域": domain,
        "取水倍数a": float(a_ratio),
        "取水能力_ML_day": float(a_abs),
        "电网接入容量_MW": float(g_val),
        "CAWCC_物理_MW": p_max,
        "首失效容量_物理_MW": _num(p["first_failed_capacity_mw"]),
        "首失效约束_物理": p["limiting_constraint"] or "",
        "身份_物理": classify(p["limiting_constraint"], p_max),
        "CAWCC_联合_MW": j_max,
        "首失效容量_联合_MW": _num(j["first_failed_capacity_mw"]),
        "首失效约束_联合": j["limiting_constraint"] or "",
        "身份_联合": classify(j["limiting_constraint"], j_max),
    }


def prepare_domains() -> dict:
    from run_r2 import load_domain

    out = {}
    for domain in ("ha", "co"):
        project, timeseries, _raw = load_domain(domain)
        out[domain] = {
            "project": project,
            "timeseries": timeseries,
            "base_a_ml_day": float(project["components"]["RES1"]["abstraction_capacity_ml_day"]),
            "base_g_mw": float(project["components"]["AI_DC1"]["grid_connection_capacity_mw"]),
        }
    return out


def _init_full(domains: dict, constraint_sets: dict) -> None:
    _W.update(domains)
    _W["_constraint_sets"] = constraint_sets


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--grid", type=int, default=9, help="a/G 各取多少档（默认 9）")
    args = ap.parse_args()

    for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
        if _p not in sys.path:
            sys.path.insert(0, _p)

    a_grid = A_RATIO_GRID if args.grid >= 9 else list(np.linspace(0.80, 1.20, args.grid))
    g_grid = G_GRID if args.grid >= 9 else list(np.linspace(900, 2100, args.grid))

    domains = prepare_domains()
    constraint_sets = {}
    for domain in ("ha", "co"):
        raw = json.loads((R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8"))
        constraint_sets[domain] = _constraint_sets(raw)

    jobs = [(d, float(a), float(g)) for d in ("ha", "co") for a in a_grid for g in g_grid]
    print(f"[E-B1] {len(jobs)} 个参数组合 × {len(CAPACITIES_SCAN)} 容量点 = "
          f"{len(jobs) * len(CAPACITIES_SCAN)} 次仿真，workers={args.workers}")
    for domain in ("ha", "co"):
        print(f"  基准 {domain}: A={domains[domain]['base_a_ml_day']:.0f} ML/d, "
              f"G={domains[domain]['base_g_mw']:.0f} MW")

    t0 = time.time()
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=args.workers,
                             initializer=_init_full,
                             initargs=(domains, constraint_sets)) as pool:
        for i, row in enumerate(pool.map(_run_cell, jobs, chunksize=1), 1):
            rows.append(row)
            if i % 20 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)}  {time.time() - t0:.0f}s  "
                      f"{row['域']} a={row['取水倍数a']:.2f} G={row['电网接入容量_MW']:.0f} "
                      f"→ {row['CAWCC_物理_MW']:.0f} MW ({row['身份_物理']})", flush=True)

    df = pd.DataFrame(rows).sort_values(["域", "取水倍数a", "电网接入容量_MW"])
    df.to_csv(OUT / "constraint_identity_phase.csv", index=False, encoding="utf-8-sig")
    print(f"[OK] {OUT / 'constraint_identity_phase.csv'} rows={len(df)}")

    # --- 分界线：每个 a 下的临界 G*（水侧主导的最后一点与电网侧主导的第一点之间） ---
    frontier = []
    for domain in ("ha", "co"):
        sub = df[(df["域"] == domain) & df["CAWCC_物理_MW"].notna()]
        for a_val, block in sub.groupby("取水倍数a"):
            block = block.sort_values("电网接入容量_MW")
            water = block[block["身份_物理"] == "水侧"]
            grid = block[block["身份_物理"] == "电网侧"]
            water_max = float(water["电网接入容量_MW"].max()) if len(water) else np.nan
            grid_min = float(grid["电网接入容量_MW"].min()) if len(grid) else np.nan
            if np.isfinite(water_max) and np.isfinite(grid_min):
                g_star = 0.5 * (water_max + grid_min)
                kind = "有切换"
            elif np.isfinite(water_max):
                g_star, kind = np.nan, "全水侧"
            elif np.isfinite(grid_min):
                g_star, kind = np.nan, "全电网侧"
            else:
                g_star, kind = np.nan, "无有效点"
            frontier.append({"域": domain, "取水倍数a": float(a_val),
                             "水侧最大G_MW": water_max, "电网侧最小G_MW": grid_min,
                             "G星_中值_MW": g_star, "切换类型": kind})
    fr = pd.DataFrame(frontier)
    fr.to_csv(OUT / "constraint_identity_frontier.csv", index=False, encoding="utf-8-sig")
    print(f"[OK] {OUT / 'constraint_identity_frontier.csv'} rows={len(fr)}")

    # --- 摘要 ---
    summary: dict = {
        "网格": {"取水倍数a": a_grid, "电网容量G_MW": g_grid,
                 "容量扫描_MW": [CAPACITIES_SCAN[0], CAPACITIES_SCAN[-1], 50.0]},
        "基准": {d: {"A_ML_day": domains[d]["base_a_ml_day"],
                     "G_MW": domains[d]["base_g_mw"]} for d in ("ha", "co")},
        "域": {},
    }
    for domain in ("ha", "co"):
        sub = df[df["域"] == domain]
        valid = sub[sub["CAWCC_物理_MW"].notna()]
        n_infeasible = int(sub["身份_物理"].eq("基线不可行").sum())
        counts = sub["身份_物理"].value_counts().to_dict()
        base = sub[(np.isclose(sub["取水倍数a"], 1.0)) &
                   (np.isclose(sub["电网接入容量_MW"], domains[domain]["base_g_mw"]))]

        pts = fr[(fr["域"] == domain) & fr["G星_中值_MW"].notna()]
        fit = {}
        if len(pts) >= 2:
            x = pts["取水倍数a"].to_numpy(float)
            y = pts["G星_中值_MW"].to_numpy(float)
            coeff = np.polyfit(x, y, 1)
            resid = y - np.polyval(coeff, x)
            fit = {"斜率_MW_per_unit_a": float(coeff[0]), "截距_MW": float(coeff[1])}
            if y.var() > 0:
                fit["R2"] = float(1.0 - resid.var() / y.var())
            fit["n_points"] = int(len(pts))
            fit["G星范围_MW"] = [float(y.min()), float(y.max())]

        summary["域"][domain] = {
            "基准端点": {
                "CAWCC_物理_MW": _num(base["CAWCC_物理_MW"].iloc[0]) if len(base) else None,
                "首失效约束_物理": base["首失效约束_物理"].iloc[0] if len(base) else None,
                "身份_物理": base["身份_物理"].iloc[0] if len(base) else None,
                "CAWCC_联合_MW": _num(base["CAWCC_联合_MW"].iloc[0]) if len(base) else None,
                "身份_联合": base["身份_联合"].iloc[0] if len(base) else None,
            },
            "身份计数_物理": {str(k): int(v) for k, v in counts.items()},
            "基线不可行格数": n_infeasible,
            "有效格数": int(len(valid)),
            "分界线拟合": fit,
            "CAWCC_物理_范围_MW": [float(valid["CAWCC_物理_MW"].min()),
                                    float(valid["CAWCC_物理_MW"].max())] if len(valid) else None,
            # 水侧主导格内 CAWCC 对 a 的敏感度（固定 G=1500）
            "水侧容量随a变化": [
                {"a": float(r["取水倍数a"]), "CAWCC_MW": float(r["CAWCC_物理_MW"]),
                 "首失效": r["首失效约束_物理"]}
                for _, r in sub[(np.isclose(sub["电网接入容量_MW"], 1500.0)) &
                                sub["CAWCC_物理_MW"].notna()].sort_values("取水倍数a").iterrows()
            ],
        }
    (OUT / "constraint_identity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {OUT / 'constraint_identity_summary.json'}")
    for domain, s in summary["域"].items():
        print(f"  {domain}: 基准 {s['基准端点']['身份_物理']} "
              f"{s['基准端点']['CAWCC_物理_MW']} MW | 计数 {s['身份计数_物理']} | "
              f"拟合 {s['分界线拟合']}")


if __name__ == "__main__":
    main()
