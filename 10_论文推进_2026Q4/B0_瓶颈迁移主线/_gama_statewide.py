# -*- coding: utf-8 -*-
"""从 GAMA 全量提取 Total Dissolved Solids 与 Specific Conductivity 的全州分布，
用于检验项目假设值 C_p = 180 mg/L 的量级是否合理。

注意：本文件只覆盖加州 19 个县（不含 Santa Clara），故不能直接替换
Santa Clara 的自来水 TDS，只能用于判断假设值的量级。
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SRC = Path(r"C:/Users/mmrgr/AppData/Local/Temp/_gama.csv")
OUT = HERE / "_gama_tds_statewide.json"

TDS = "Total Dissolved Solids"
EC = "Specific Conductivity"


def quantiles(v: list[float], qs=(0.05, 0.25, 0.5, 0.75, 0.95)) -> dict:
    v = sorted(v)
    n = len(v)
    return {f"p{int(q*100)}": v[min(n - 1, int(q * n))] for q in qs}


def main() -> None:
    by_county: dict[str, list[float]] = defaultdict(list)
    ec_by_county: dict[str, list[float]] = defaultdict(list)
    all_tds: list[float] = []
    all_ec: list[float] = []

    with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
        for row in csv.DictReader(f):
            chem = (row.get("gm_chemical_name") or "").strip()
            if chem not in (TDS, EC):
                continue
            try:
                val = float(row.get("gm_result") or "nan")
                un = (row.get("gm_chemical_units") or "").strip().upper()
            except ValueError:
                continue
            if val != val or val <= 0:
                continue
            county = (row.get("gm_county_name") or "").strip()
            if chem == TDS and un in ("MG/L", "PPM"):
                all_tds.append(val)
                by_county[county].append(val)
            elif chem == EC and un in ("US/CM", "UMHO/CM", "US/CM @ 25 C", "US/CM@25C"):
                all_ec.append(val)
                ec_by_county[county].append(val)

    print(f"TDS 记录 {len(all_tds):,}（{len(by_county)} 个县）")
    print(f"EC  记录 {len(all_ec):,}（{len(ec_by_county)} 个县）")

    out = {"source": "GAMA DDW 2020-present", "note": "仅 19 个县，不含 Santa Clara"}

    if all_tds:
        q = quantiles(all_tds)
        print(f"\n全州 TDS 分布 (mg/L)：中位 {q['p50']:.0f}  "
              f"p5-p95 [{q['p5']:.0f}, {q['p95']:.0f}]")
        out["tds"] = {"n": len(all_tds), **{k: round(v, 1) for k, v in q.items()},
                      "mean": round(statistics.mean(all_tds), 1)}

    if all_ec:
        q = quantiles(all_ec)
        print(f"全州 EC  分布 (µS/cm)：中位 {q['p50']:.0f}  "
              f"p5-p95 [{q['p5']:.0f}, {q['p95']:.0f}]")
        out["ec"] = {"n": len(all_ec), **{k: round(v, 1) for k, v in q.items()}}
        # 经验换算 TDS ≈ k × EC，k ~ 0.55-0.75
        for k in (0.55, 0.65, 0.75):
            print(f"   若 TDS = {k} × EC  →  中位 TDS ≈ {k*q['p50']:.0f} mg/L")
            out.setdefault("tds_from_ec", {})[f"k={k}"] = round(k * q["p50"], 1)

    # 与项目假设比较
    print("\n项目假设 C_p = 180 mg/L（Santa Clara 自来水 TDS）")
    if all_tds:
        med = out["tds"]["p50"]
        p95 = out["tds"]["p95"]
        print(f"  全州地下水 TDS 中位 {med:.0f}，p95 {p95:.0f}")
        print(f"  假设值 180 位于全州分布的 "
              f"{100*sum(1 for v in all_tds if v<=180)/len(all_tds):.1f} 百分位")
        out["c_p_assumed_mg_l"] = 180.0
        out["assumed_percentile"] = round(
            100 * sum(1 for v in all_tds if v <= 180) / len(all_tds), 1)

    # 各县中位（前 10）
    print("\n各县 TDS 中位（样本 ≥ 30）：")
    rows = [(c, statistics.median(v), len(v)) for c, v in by_county.items() if len(v) >= 30]
    rows.sort(key=lambda x: -x[1])
    for c, m, n in rows[:10]:
        print(f"  {c:<16}{m:8.0f} mg/L  (n={n:,})")
    out["county_median"] = {c: round(m, 1) for c, m, _ in rows}

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
