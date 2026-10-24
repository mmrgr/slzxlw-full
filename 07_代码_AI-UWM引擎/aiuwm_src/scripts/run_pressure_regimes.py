# -*- coding: utf-8 -*-
"""E-B2 外部压力情景：气候与干旱如何改变承载瓶颈。

【为什么必须做】
参考的已发表论文（Nature Water 2026 中国污水厂、ESE 2026 全球 data-water
symbiosis、Applied Energy 2025 数据中心水足迹）都把气候/干旱情景作为主图。
本项目目前只有静态参数的合成端点：r 扫描、容量扫描、城市梯度，但**没有任何
"外部压力"维度**——没有高温、没有干旱、没有复合情景。

结果是：论文能说"水质反馈在什么条件下改变瓶颈"，但无法回答审稿人必然会问的
"气候变化下这个结论是变强还是变弱"。

【本实验要回答】
在 G0（基准）/ G1（高温）/ G2（干旱）/ G3（复合）四种外部压力下：
  (a) 两域 CAWCC 如何变化？
  (b) 首失效约束是否改变身份（水侧 / 电网侧 / 社会侧）？
  (c) 水质惩罚的容量效应（r 从 0.5 到 0.9 的降幅）在压力下是放大还是缩小？
  (d) 是否存在"压力下瓶颈翻转"的临界压力强度？

【压力定义（沿用 run_r2.apply_g 的既有设计，不另造）】
  G0 基准：原序列
  G1 高温：夏季（6–8 月）干球 +4 ℃
  G2 干旱：汛期（6–9 月）入流 ×0.65，取水能力 ×0.85，夏季 +1 ℃
  G3 复合：G1 + G2 + 传统需求 ×1.12

【扫描设计】
4 情景 × 2 域 × r ∈ {0.0, 0.5, 0.6, 0.7, 0.8, 0.9} × 41 容量点
= 4 × 2 × 6 × 41 = 1968 次仿真

【产物】
  pressure_regime_scan.csv      逐情景×域×r 的 CAWCC 与首失效（两口径）
  pressure_regime_summary.json  降幅、瓶颈翻转、压力放大系数

【用法】
  PYTHONPATH="src;scripts" python scripts/run_pressure_regimes.py --workers 16
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
R_GRID = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9]

WATER_SIDE = {
    "max_source_abstraction_ratio", "max_wtw_utilization", "max_wwtw_utilization",
    "peak_capacity_ratio", "max_local_connection_ratio", "unmet_cooling_water_ml",
}
GRID_SIDE = {"max_daily_average_grid_connection_ratio", "mean_daily_average_grid_connection_ratio"}
SOCIAL_SIDE = {"system_reliability_fraction", "domestic_unmet_ml"}

SCENARIOS = {
    "G0": "基准（原序列）",
    "G1": "高温（夏季 +4 ℃）",
    "G2": "干旱（汛期入流 ×0.65、取水能力 ×0.85）",
    "G3": "复合（高温+干旱+需求 ×1.12）",
}

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


def _run_case(job: tuple[str, str, float]) -> dict:
    find_ai_carrying_capacity, summarize_ai_water_kpis, FullAIUWMModel = _import_engine()
    from run_r2 import apply_g

    scenario, domain, r_val = job
    d = _W[domain]
    # 压力层只改驱动，不改设施；apply_g 返回 (project, timeseries)
    project, timeseries = apply_g(copy.deepcopy(d["project"]), d["timeseries"], scenario)

    # 设定替代率：同时改 reclaimed 与 potable 的目标份额
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
        result = FullAIUWMModel(trial, timeseries).run()
        rows.append({"ai_capacity_mw": float(capacity), **summarize_ai_water_kpis(result, trial)})
    scan = pd.DataFrame(rows)

    physical, full = _W["_constraint_sets"][domain]
    p = find_ai_carrying_capacity(scan, physical)
    j = find_ai_carrying_capacity(scan, full)
    p_max = _num(p["maximum_safe_ai_capacity_mw"])
    j_max = _num(j["maximum_safe_ai_capacity_mw"])
    return {
        "情景": scenario,
        "情景说明": SCENARIOS[scenario],
        "域": domain,
        "替代率r": float(r_val),
        "CAWCC_物理_MW": p_max,
        "首失效约束_物理": p["limiting_constraint"] or "",
        "侧别_物理": side_of(p["limiting_constraint"]),
        "CAWCC_联合_MW": j_max,
        "首失效约束_联合": j["limiting_constraint"] or "",
        "侧别_联合": side_of(j["limiting_constraint"]),
    }


def prepare_domains() -> dict:
    from run_r2 import load_domain

    out = {}
    for domain in ("ha", "co"):
        project, timeseries, _raw = load_domain(domain)
        out[domain] = {"project": project, "timeseries": timeseries}
    return out


def _init_full(domains: dict, constraint_sets: dict) -> None:
    _W.update(domains)
    _W["_constraint_sets"] = constraint_sets


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()
    for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
        if _p not in sys.path:
            sys.path.insert(0, _p)

    domains = prepare_domains()
    constraint_sets = {}
    for domain in ("ha", "co"):
        raw = json.loads((R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8"))
        constraint_sets[domain] = _constraint_sets(raw)

    jobs = [(s, d, float(r)) for s in SCENARIOS for d in ("ha", "co") for r in R_GRID]
    print(f"[E-B2] {len(jobs)} 个情景×域×r 组合 × {len(CAPACITIES_SCAN)} 容量点 = "
          f"{len(jobs) * len(CAPACITIES_SCAN)} 次仿真")

    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init_full,
                             initargs=(domains, constraint_sets)) as pool:
        for i, row in enumerate(pool.map(_run_case, jobs, chunksize=1), 1):
            rows.append(row)
            if i % 4 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)} {time.time()-t0:.0f}s  {row['情景']} {row['域']} "
                      f"r={row['替代率r']:.1f} → {row['CAWCC_物理_MW']:.0f} MW "
                      f"({row['侧别_物理']})", flush=True)

    df = pd.DataFrame(rows).sort_values(["情景", "域", "替代率r"])
    df.to_csv(OUT / "pressure_regime_scan.csv", index=False, encoding="utf-8-sig")
    print(f"[OK] {OUT / 'pressure_regime_scan.csv'} rows={len(df)}")

    summary: dict = {"情景": SCENARIOS, "替代率网格": R_GRID,
                     "容量网格_MW": [CAPACITIES_SCAN[0], CAPACITIES_SCAN[-1], 50.0],
                     "域": {}}
    for domain in ("ha", "co"):
        entry: dict = {}
        sub = df[df["域"] == domain]
        for scenario in SCENARIOS:
            s = sub[sub["情景"] == scenario].sort_values("替代率r")
            if s.empty:
                continue
            base = s[np.isclose(s["替代率r"], 0.0)]
            high = s[np.isclose(s["替代率r"], 0.9)]
            mid = s[np.isclose(s["替代率r"], 0.5)]
            # G0 下 r=0.5 的容量作为压力损失参照
            entry[scenario] = {
                "CAWCC_r0_MW": _num(base["CAWCC_物理_MW"].iloc[0]) if len(base) else None,
                "CAWCC_r0.5_MW": _num(mid["CAWCC_物理_MW"].iloc[0]) if len(mid) else None,
                "CAWCC_r0.9_MW": _num(high["CAWCC_物理_MW"].iloc[0]) if len(high) else None,
                "侧别_r0.5": mid["侧别_物理"].iloc[0] if len(mid) else None,
                "侧别_r0.9": high["侧别_物理"].iloc[0] if len(high) else None,
                "首失效_r0.5": mid["首失效约束_物理"].iloc[0] if len(mid) else None,
                "r0.5到0.9降幅_MW": (
                    _num(mid["CAWCC_物理_MW"].iloc[0]) - _num(high["CAWCC_物理_MW"].iloc[0])
                    if len(mid) and len(high) else None
                ),
                "逐r序列": [
                    {"r": float(x["替代率r"]), "CAWCC": _num(x["CAWCC_物理_MW"]),
                     "侧别": x["侧别_物理"]}
                    for _, x in s.iterrows()
                ],
            }
        # 压力损失：G1/G2/G3 相对 G0 在同一 r=0.5 下的容量差
        if "G0" in entry:
            ref = entry["G0"].get("CAWCC_r0.5_MW")
            for scenario in ("G1", "G2", "G3"):
                if scenario in entry and ref is not None:
                    cur = entry[scenario].get("CAWCC_r0.5_MW")
                    entry[scenario]["相对G0的容量损失_MW"] = (
                        None if cur is None else float(cur - ref)
                    )
        # 水质效应在压力下是否变化
        eff = {s: entry[s].get("r0.5到0.9降幅_MW") for s in entry}
        entry["水质效应放大判定"] = {
            "各情景降幅_MW": eff,
            "G0降幅": eff.get("G0"),
            "压力下是否放大": (
                all(v is not None and eff.get("G0") is not None and v > eff["G0"]
                    for k, v in eff.items() if k != "G0")
                if eff.get("G0") is not None else None
            ),
        }
        summary["域"][domain] = entry
    (OUT / "pressure_regime_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {OUT / 'pressure_regime_summary.json'}")
    for domain, entry in summary["域"].items():
        print(f"\n  {domain}:")
        for scenario in SCENARIOS:
            if scenario in entry:
                e = entry[scenario]
                print(f"    {scenario} r=0 → {e['CAWCC_r0_MW']} | r=0.5 → {e['CAWCC_r0.5_MW']} "
                      f"({e['侧别_r0.5']}) | r=0.9 → {e['CAWCC_r0.9_MW']} ({e['侧别_r0.9']}) "
                      f"| 降幅 {e['r0.5到0.9降幅_MW']}")


if __name__ == "__main__":
    main()
