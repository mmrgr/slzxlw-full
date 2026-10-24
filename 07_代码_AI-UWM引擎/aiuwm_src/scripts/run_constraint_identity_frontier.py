# -*- coding: utf-8 -*-
"""E-B1b 约束身份分界线的精确定位（利用 9×9 相图做种子区间的二分）。

【为什么重新设计】
上一版对每个 a 都从 [850, 2250] 全区间二分，需要 11 次评估 × 41 容量点，
16 个组合要跑十几分钟。但实际上 9×9 粗网格已经把分界线夹在相邻两格之间
（如 HA 的 G*=1200–1350）。从粗网格给出的 [G_水侧最大, G_电网侧最小] 作为
种子区间，只需 6–7 次二分即到 50 MW 分辨率以下，评估数减半。

【判据】
约束身份 = "电网侧"（G 偏小）还是 "水侧"（G 偏大）。二分收缩到区间宽度
小于容量网格步长（50 MW）即停，此时结论已到分辨率极限。

【种子区间来源】
  constraint_identity_phase.csv 的粗网格：对每个 (域, a)，
    水侧最大 G 与 电网侧最小 G 之间的区间就是种子
  若该 a 下没有切换（全水侧 / 全电网侧 / 基线不可行），直接沿用粗网格结论。

【产物】
  constraint_identity_frontier_refined.csv
  constraint_identity_frontier_summary.json

【用法】
  PYTHONPATH="src;scripts" python scripts/run_constraint_identity_frontier.py --workers 6
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
GRID_STEP = 50.0
POLICY = "reclaimed_water_substitution_ratio"

WATER_SIDE = {
    "max_source_abstraction_ratio", "max_wtw_utilization", "max_wwtw_utilization",
    "peak_capacity_ratio", "max_local_connection_ratio", "unmet_cooling_water_ml",
    "domestic_unmet_ml", "system_reliability_fraction",
}
GRID_SIDE = {"max_daily_average_grid_connection_ratio"}

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


def _evaluate(domain: str, a_abs: float, g_val: float) -> dict:
    find_ai_carrying_capacity, summarize_ai_water_kpis, FullAIUWMModel = _import_engine()
    d = _W[domain]
    project = copy.deepcopy(d["project"])
    project["components"]["RES1"]["abstraction_capacity_ml_day"] = float(a_abs)
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

    physical, _ = _W["_constraint_sets"][domain]
    found = find_ai_carrying_capacity(scan, physical)
    limiting = found["limiting_constraint"]
    try:
        cawcc = float(found["maximum_safe_ai_capacity_mw"])
    except (TypeError, ValueError):
        cawcc = float("nan")
    if not np.isfinite(cawcc):
        ident = "基线不可行"
    elif limiting in GRID_SIDE:
        ident = "电网侧"
    elif limiting in WATER_SIDE:
        ident = "水侧"
    else:
        ident = "其他"
    return {"identity": ident, "cawcc": cawcc, "limiting": limiting or ""}


def _bisect_task(job: tuple[str, float, float, float, str, float]) -> dict:
    """job = (域, a倍数, 种子下界, 种子上界, 种子类型, 绝对取水能力 ML/d)

    ⚠ `_evaluate` 的第二个参数是**绝对**取水能力（ML/d），不是倍数。
    """
    domain, a_ratio, lo, hi, seed_kind, a_abs = job
    base = {"域": domain, "取水倍数a": float(a_ratio),
            "种子下界_MW": lo, "种子上界_MW": hi, "种子类型": seed_kind}

    if seed_kind != "有切换":
        return {**base, "G星_MW": float("nan"), "判定": seed_kind,
                "分辨率_MW": float("nan"), "G星CAWCC_MW": float("nan"),
                "G星身份": seed_kind}

    # 确认种子区间端点身份
    lo_rec = _evaluate(domain, a_abs, lo)
    hi_rec = _evaluate(domain, a_abs, hi)
    if hi_rec["identity"] != "水侧" or lo_rec["identity"] == "水侧":
        # 种子不可靠：退回全区间
        lo, hi = 900.0, 2100.0
        lo_rec = _evaluate(domain, a_abs, lo)
        hi_rec = _evaluate(domain, a_abs, hi)
        if lo_rec["identity"] == "水侧" or hi_rec["identity"] != "水侧":
            return {**base, "G星_MW": float("nan"),
                    "判定": f"全区间不单调({lo_rec['identity']}→{hi_rec['identity']})",
                    "分辨率_MW": float("nan"), "G星CAWCC_MW": float("nan"),
                    "G星身份": "未知"}

    iters = 0
    while hi - lo > GRID_STEP:
        mid = 0.5 * (lo + hi)
        rec = _evaluate(domain, a_abs, mid)
        iters += 1
        if rec["identity"] == "水侧":
            hi = mid
        else:
            lo = mid
    g_star = 0.5 * (lo + hi)
    rec_star = _evaluate(domain, a_abs, g_star)
    return {**base, "G星_MW": g_star, "判定": "二分收敛",
            "分辨率_MW": hi - lo, "二分次数": iters,
            "G星CAWCC_MW": rec_star["cawcc"], "G星身份": rec_star["identity"]}


def prepare_domains() -> dict:
    from run_r2 import load_domain

    out = {}
    for domain in ("ha", "co"):
        project, timeseries, _raw = load_domain(domain)
        out[domain] = {
            "project": project, "timeseries": timeseries,
            "base_a_ml_day": float(project["components"]["RES1"]["abstraction_capacity_ml_day"]),
            "base_g_mw": float(project["components"]["AI_DC1"]["grid_connection_capacity_mw"]),
        }
    return out


def _init_full(domains: dict, constraint_sets: dict) -> None:
    _W.update(domains)
    _W["_constraint_sets"] = constraint_sets


def build_jobs(phase: pd.DataFrame, domains: dict) -> list[tuple]:
    """从 9×9 粗网格提取每个 (域, a) 的种子区间。"""
    jobs = []
    for domain in ("ha", "co"):
        base_a = domains[domain]["base_a_ml_day"]
        sub = phase[(phase["域"] == domain) & phase["CAWCC_物理_MW"].notna()]
        for a_ratio, blk in sub.groupby("取水倍数a"):
            blk = blk.sort_values("电网接入容量_MW")
            water = blk[blk["身份_物理"] == "水侧"]["电网接入容量_MW"]
            grid = blk[blk["身份_物理"] == "电网侧"]["电网接入容量_MW"]
            if len(water) and len(grid):
                # 电网侧最大 G 与水侧最小 G 之间即为分界线所在区间
                lo = float(grid.max())
                hi = float(water.min())
                kind = "有切换" if hi > lo else "临界落在单格"
                if hi <= lo:  # 非单调（中间夹了基线不可行），退回全区间
                    lo, hi = 900.0, 2100.0
            elif len(water):
                lo, hi, kind = float(water.min()), float(water.max()), "全水侧"
            elif len(grid):
                lo, hi, kind = float(grid.min()), float(grid.max()), "全电网侧"
            else:
                lo, hi, kind = float("nan"), float("nan"), "基线不可行"
            jobs.append((domain, float(a_ratio), lo, hi, kind,
                         float(a_ratio) * base_a))
    return jobs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
        if _p not in sys.path:
            sys.path.insert(0, _p)

    phase_path = OUT / "constraint_identity_phase.csv"
    if not phase_path.exists():
        raise SystemExit("缺少 constraint_identity_phase.csv，请先跑 run_constraint_identity_phase.py")
    phase = pd.read_csv(phase_path, encoding="utf-8-sig")

    domains = prepare_domains()
    constraint_sets = {}
    for domain in ("ha", "co"):
        raw = json.loads((R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8"))
        constraint_sets[domain] = _constraint_sets(raw)

    raw_jobs = build_jobs(phase, domains)
    jobs = raw_jobs  # 已是 (域, a倍数, lo, hi, 类型, 绝对A_ML/day)
    n_switch = sum(1 for j in jobs if j[4] == "有切换")
    print(f"[E-B1b] {len(jobs)} 个 (域, a) 组合，其中 {n_switch} 个需要二分细化")

    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init_full,
                             initargs=(domains, constraint_sets)) as pool:
        for i, row in enumerate(pool.map(_bisect_task, jobs, chunksize=1), 1):
            row["取水能力_ML_day"] = row["取水倍数a"] * domains[row["域"]]["base_a_ml_day"]
            rows.append(row)
            print(f"  {i}/{len(jobs)} {time.time()-t0:.0f}s {row['域']} "
                  f"a={row['取水倍数a']:.2f} → G*={row['G星_MW']:.0f} MW "
                  f"({row['判定']})", flush=True)

    df = pd.DataFrame(rows).sort_values(["域", "取水倍数a"])
    df.to_csv(OUT / "constraint_identity_frontier_refined.csv",
              index=False, encoding="utf-8-sig")
    print(f"[OK] {OUT / 'constraint_identity_frontier_refined.csv'} rows={len(df)}")

    summary: dict = {"方法": "以 9×9 粗相图为种子，二分到 <50 MW（容量网格步长）",
                     "容量网格_MW": GRID_STEP, "域": {}}
    for domain in ("ha", "co"):
        sub = df[df["域"] == domain]
        conv = sub[sub["G星_MW"].notna()]
        base_g = domains[domain]["base_g_mw"]
        entry: dict = {"标称电网容量_MW": base_g,
                       "收敛组合数": int(len(conv)),
                       "总组合数": int(len(sub))}
        if len(conv):
            at1 = conv[np.isclose(conv["取水倍数a"], 1.0)]
            if len(at1):
                g_star = float(at1["G星_MW"].iloc[0])
                entry["标称a下的G星_MW"] = g_star
                entry["标称点距分界线_MW"] = base_g - g_star
                entry["标称点所处区域"] = "水侧主导" if base_g > g_star else "电网侧主导"
            entry["G星范围_MW"] = [float(conv["G星_MW"].min()), float(conv["G星_MW"].max())]
            if len(conv) >= 2:
                entry["G星对a的斜率_MW"] = float(
                    np.polyfit(conv["取水倍数a"], conv["G星_MW"], 1)[0])
            entry["逐a结果"] = [
                {"a": float(r["取水倍数a"]), "G星_MW": float(r["G星_MW"])}
                for _, r in conv.iterrows()
            ]
        entry["未收敛明细"] = [
            {"a": float(r["取水倍数a"]), "判定": str(r["判定"])}
            for _, r in sub[sub["G星_MW"].isna()].iterrows()
        ]
        summary["域"][domain] = entry
    (OUT / "constraint_identity_frontier_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {OUT / 'constraint_identity_frontier_summary.json'}")
    for domain, s in summary["域"].items():
        print(f"  {domain}: G*={s.get('标称a下的G星_MW')} MW, "
              f"裕度={s.get('标称点距分界线_MW')} MW, 区域={s.get('标称点所处区域')}, "
              f"范围={s.get('G星范围_MW')}")


if __name__ == "__main__":
    main()
