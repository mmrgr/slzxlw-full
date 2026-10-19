# -*- coding: utf-8 -*-
"""从 GAMA 加州饮用水水质数据中提取 TDS 与电导率实测值，用于锚定 r* 的两个源水参数。

目的：
  r* = (L/CoC_d − C_p)/(C_r − C_p) 的四个参数中，C_p（自来水 TDS）与 C_r（再生水 TDS）
  从未有实测锚点。本脚本尝试用加州 DDW 实测数据给 C_p 一个锚点。

策略：
  1. 流式扫描（625 MB，避免一次性载入）；
  2. 保留 chemical_name ∈ {TDS, Specific Conductance, Chloride} 且 county = SANTA CLARA 的记录；
  3. 按 pwsid 汇总中位数；
  4. 与项目假设值 C_p = 180 mg/L 比较。

产物：_gama_tds_santaclara.json + 控制台统计
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SRC = Path(r"C:/Users/mmrgr/AppData/Local/Temp/_gama.csv")
OUT = HERE / "_gama_tds_santaclara.json"

TARGET_COUNTY = "SANTA CLARA"
# 关注的化学指标（大小写与写法按 GAMA 实际值匹配）
WANT = {
    "TDS": "TDS",
    "Total Dissolved Solids": "TDS",
    "Specific Conductance": "EC",
    "Chloride": "Cl",
}


def main() -> None:
    if not SRC.exists():
        print("找不到 /tmp/_gama.csv")
        return

    # 第一遍：统计全部 chemical_name（限量，避免耗时过长）
    seen: dict[str, int] = defaultdict(int)
    keep: list[dict] = []
    n = 0
    with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
        rd = csv.DictReader(f)
        for row in rd:
            n += 1
            chem = (row.get("gm_chemical_name") or "").strip()
            if chem:
                seen[chem] += 1
            county = (row.get("gm_county_name") or "").strip().upper()
            if county != TARGET_COUNTY:
                continue
            tag = WANT.get(chem)
            if not tag:
                continue
            try:
                val = float(row.get("gm_result") or "nan")
            except ValueError:
                continue
            if val != val:  # NaN
                continue
            keep.append({
                "chem": tag,
                "chem_raw": chem,
                "value": val,
                "units": (row.get("gm_chemical_units") or "").strip(),
                "well": (row.get("gm_well_id") or "").strip(),
                "date": (row.get("gm_samp_collection_date") or "").strip(),
            })
            if n % 500000 == 0:
                print(f"  已扫描 {n:,} 行，Santa Clara 命中 {len(keep):,}")

    print(f"\n总行数 {n:,}")
    print(f"Santa Clara 目标指标命中 {len(keep):,}")

    # 按指标汇总
    by: dict[str, list[float]] = defaultdict(list)
    for r in keep:
        by[r["chem"]].append(r["value"])
    print(f"\n{'指标':<8}{'n':>9}{'中位':>10}{'均值':>10}{'min':>9}{'max':>10}")
    print("-" * 58)
    summary = {}
    for tag in ("TDS", "EC", "Cl"):
        v = by.get(tag, [])
        if not v:
            print(f"{tag:<8}{0:>9}")
            continue
        med = statistics.median(v)
        print(f"{tag:<8}{len(v):>9}{med:>10.1f}{statistics.mean(v):>10.1f}"
              f"{min(v):>9.1f}{max(v):>10.1f}")
        summary[tag] = {
            "n": len(v), "median": round(med, 2),
            "mean": round(statistics.mean(v), 2),
            "min": min(v), "max": max(v),
        }

    # 项目假设值对比
    C_P_ASSUMED = 180.0
    print(f"\n项目假设值 C_p = {C_P_ASSUMED} mg/L")
    if "TDS" in summary:
        med = summary["TDS"]["median"]
        print(f"GAMA 实测 TDS 中位 = {med:.1f} mg/L  →  假设值偏高 {C_P_ASSUMED-med:+.1f}"
              f"（{100*(C_P_ASSUMED-med)/med:+.1f}%）")
    if "EC" in summary:
        # 经验换算：TDS ≈ 0.65 × EC(µS/cm)
        approx = 0.65 * summary["EC"]["median"]
        print(f"GAMA 实测 EC 中位 = {summary['EC']['median']:.1f} µS/cm"
              f"  →  估算 TDS ≈ {approx:.0f} mg/L（0.65 系数，仅量级参考）")

    OUT.write_text(json.dumps({
        "source": "GAMA / DDW 2020-present (data.ca.gov)",
        "county": TARGET_COUNTY,
        "c_p_assumed_mg_l": C_P_ASSUMED,
        "summary": summary,
        "note": ("GAMA 为地下水井监测数据，不等同于供水系统出厂水；"
                 "用于判断 C_p 假设值的量级是否偏离，不作直接替换。"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
