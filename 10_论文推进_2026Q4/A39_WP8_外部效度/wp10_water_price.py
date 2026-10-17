"""WP10: 城市水价 vs 再生水成本 —— 经济可行性的量级检验.

======================================================================
【为什么做】
======================================================================
WP8 给出真实 B3(工业冷却) 再生水项目的**总单位成本中位 2.413 CNY/m3**。
但"再生水贵不贵"只有与**自来水工业水价**比较才有意义。
本轮在同一数据包中发现 `water price(CNY_m-3)` 工作表, 含
**多城市、多年月的分类自来水价**（居民/工业/公共机构/商业/特种用水）。

本脚本:
  1. 机械解析价格表（首两行是"年-月"与"用水类别"表头, 需正确对齐）;
  2. 提取**工业水价**的时间序列;
  3. 与 WP8 的 B3 再生水成本中位做量级对照;
  4. 明确可支持/不可支持的结论。

【纪律】
  · 只读外部数据;
  · 表头为两层(Year–Month + 类别), 必须显式处理, 不得按首行直接当列名;
  · 缺失显式统计, 不静默按 0;
  · 只做**量级**对照, 不做投资/成本结论（无规模/寿命/折现数据）。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXT = Path(__file__).resolve().parents[3] / "_ext_data" / "source_data" / "Source_data.xlsx"
SHEET = "water price(CNY_m-3)"
# WP8 的 B3 成本 (来自 wp8_real_reuse_cases_summary.json)
WP8 = HERE / "wp8_real_reuse_cases_summary.json"


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("WP10  城市自来水价 vs 再生水成本: 经济可行性量级检验")
    rec("=" * 84)

    if not EXT.exists():
        rec(f"\n⚠ 缺数据 ⇒ NOT_IDENTIFIABLE")
        return
    x = pd.ExcelFile(EXT)
    if SHEET not in x.sheet_names:
        rec(f"\n⚠ 工作表不存在 ⇒ NOT_IDENTIFIABLE")
        return

    # ⚠ 表布局(实测, header=None 时):
    #   第0行 = ['City Name','Shanghai','Shanghai',...]        <- 城市名(pandas 会 ffill 到多列)
    #   第1行 = ['Year–Month','Tap Water Tariff (excluding...)', NaN, ...]  <- 第一类标题
    #   第2行 = [NaN,'Residential','Industrial','Public Institutions',...]  <- 真正的类别名
    #   第3行起 = 数据
    raw = x.parse(SHEET, header=None)
    rec(f"\n[0] 来源: {EXT.name} :: {SHEET}   形状 = {raw.shape}")

    row_city = raw.iloc[0].tolist()
    row_t1 = raw.iloc[1].tolist()
    row_t2 = raw.iloc[2].tolist()
    rec(f"    第0行(城市) 前6: {[str(v)[:20] for v in row_city[:6]]}")
    rec(f"    第1行(类型1) 前4: {[str(v)[:38] for v in row_t1[:4]]}")
    rec(f"    第2行(类别)  前6: {[str(v)[:24] for v in row_t2[:6]]}")

    cities = [str(v) for v in row_city]
    cats = [str(v) for v in row_t2]
    rec(f"    列数 = {len(cities)}")

    # 找 'Industrial' 列 (真实类别名在第2行)
    ind_idx = [i for i, c in enumerate(cats) if "industrial" in c.lower()]
    res_idx = [i for i, c in enumerate(cats) if "residential" in c.lower()]
    rec(f"\n[1] 类别列定位(基于第2行): 'Industrial' {len(ind_idx)} 列; "
        f"'Residential' {len(res_idx)} 列")
    if not ind_idx:
        rec(f"    第2行全部非空值样本: "
            f"{[c for c in cats if c != 'nan'][:12]}")
        rec("    ⇒ 未找到工业水价列 ⇒ NOT_IDENTIFIABLE")
        return

    body = raw.iloc[3:].copy()
    date_col = body.iloc[:, 0]
    ts = pd.to_datetime(date_col, errors="coerce")
    if ts.notna().any():
        rec(f"    时间列: 可解析 {int(ts.notna().sum())}/{len(body)}"
            f"  范围 [{ts.min().date()}, {ts.max().date()}]")

    # 聚合所有城市的工业水价
    vals = []
    for i in ind_idx:
        v = pd.to_numeric(body.iloc[:, i], errors="coerce")
        vals.append(v.dropna())
    allv = pd.concat(vals) if vals else pd.Series(dtype=float)
    n_city_cols = len(ind_idx)
    rec(f"\n[2] 工业水价 (汇总 {n_city_cols} 个城市列)")
    if len(allv) == 0:
        rec("    ⇒ 无有效值 ⇒ NOT_IDENTIFIABLE")
        return
    rec(f"    观测数 = {len(allv)}")
    rec(f"    min    = {allv.min():.3f} CNY/m3")
    rec(f"    p25    = {allv.quantile(.25):.3f}")
    rec(f"    median = {allv.median():.3f}")
    rec(f"    p75    = {allv.quantile(.75):.3f}")
    rec(f"    max    = {allv.max():.3f}")

    # 每城市一个中位, 再取城市间分布(避免月份数不等导致的城市权重偏差)
    per_city = []
    for i in ind_idx:
        v = pd.to_numeric(body.iloc[:, i], errors="coerce").dropna()
        if len(v):
            per_city.append({"col": i, "city": cities[i], "n": int(len(v)),
                             "median": float(v.median()), "min": float(v.min()),
                             "max": float(v.max())})
    med_by_city = np.array([c["median"] for c in per_city])
    rec(f"\n[3] 按城市汇总 (每城市取中位后, 再跨城市统计; n_city={len(med_by_city)})")
    if len(med_by_city):
        rec(f"    城市中位数的中位 = {np.median(med_by_city):.3f}")
        rec(f"    城市中位数区间   = [{med_by_city.min():.3f}, {med_by_city.max():.3f}]")
        rec(f"    城市间 p25/p75  = {np.percentile(med_by_city,25):.3f} / "
            f"{np.percentile(med_by_city,75):.3f}")

    # ---------- 4. 与再生水成本对照 ----------
    rec(f"\n[4] ★ 与再生水成本的量级对照")
    reuse_med = reuse_range = None
    if WP8.exists():
        w = json.loads(WP8.read_text(encoding="utf-8"))
        b3 = w.get("b3_industrial_cooling", {})
        costs = b3.get("costs", {})
        tc = None
        for k, v in costs.items():
            if "Total unit cost" in k:
                tc = v
        if tc:
            reuse_med = tc.get("median")
            reuse_range = (tc.get("p25"), tc.get("p75"))
            rec(f"    B3 再生水总单位成本 (WP8, n={tc['n']}): "
                f"中位 {reuse_med:.3f}, p25-p75 [{tc['p25']:.3f}, {tc['p75']:.3f}] CNY/m3")
    else:
        rec(f"    ⚠ 未找到 {WP8.name} ⇒ 无法对照")

    if reuse_med is not None and len(med_by_city):
        tap_med = float(np.median(med_by_city))
        ratio = reuse_med / tap_med
        rec(f"    工业自来水价中位 = {tap_med:.3f} CNY/m3")
        rec(f"    ⇒ 再生水成本 / 自来水价 = {ratio:.3f}")
        if ratio < 1:
            rec("    ⇒ 在该量级上, 再生水成本【低于】工业自来水价"
                "（经济上具备替代动机）")
            verdict = "REUSE_CHEAPER_THAN_TAP_AT_TYPICAL_CITY"
        else:
            rec("    ⇒ 在该量级上, 再生水成本【高于】工业自来水价"
                "（需政策/补贴或非价格动机驱动）")
            verdict = "REUSE_MORE_EXPENSIVE_AT_TYPICAL_CITY"
        # 城市间差异
        n_below = int((reuse_med < med_by_city).sum())
        rec(f"    再生水成本中位低于多少个城市的水价: {n_below}/{len(med_by_city)} "
            f"({100.0*n_below/len(med_by_city):.1f}%)")
    else:
        verdict = "NOT_COMPARABLE"

    rec(f"\n[5] ★ 可支持 / 不可支持的结论")
    may = [
        f"城市间与城市内的工业自来水价存在**可观差异**"
        f"（列上 min {allv.min():.2f} – max {allv.max():.2f} CNY/m3）",
        f"由 WP8 与本地数据可给出再生水成本相对自来水价的**量级比**（见 [4]）",
        "该对照为本文的'经济合理性'提供**数量级层面**的外部依据",
    ]
    may_not = [
        "**不可**做投资回报/净现值结论（无设施寿命、折现率、规模经济数据）",
        "**不可**把该价格等同于本文模型域的城市水价（模型域为合成域）",
        "**不可**用于需求侧推断（价格不是需求量/合同）",
        "价格表含多城市多年月, 但**无供水结构/用途占比**字段",
        "**不可**据此声称'池被占用是因为再生水贵'——本数据无合同/分配字段, "
        "价格与占用之间**不存在可建立的因果链**（价格 ≠ 需求 ≠ 合同）",
    ]
    for s in may:
        rec(f"    ✅ {s}")
    for s in may_not:
        rec(f"    ❌ {s}")

    summary = {
        "task": "WP10 城市水价 vs 再生水成本量级对照",
        "source": str(EXT), "sheet": SHEET,
        "n_industrial_cols": n_city_cols,
        "n_obs_industrial": int(len(allv)),
        "industrial_tariff": {
            "min": float(allv.min()), "p25": float(allv.quantile(.25)),
            "median": float(allv.median()), "p75": float(allv.quantile(.75)),
            "max": float(allv.max()),
        },
        "per_city_median_stats": {
            # 2026-10-17 修正: 此处的 n 是"城市×源表列"的**观测数**(61)，
            # **不是**唯一城市数(实为 31)。旧字段名 n_city 有误导性，
            # 故新增语义明确的字段，同时保留 n_city 以兼容既有引用。
            "n_city_source_series": int(len(med_by_city)),
            "n_distinct_cities": int(len({c["city"] for c in per_city})),
            "n_city": int(len(med_by_city)),
            "median": float(np.median(med_by_city)) if len(med_by_city) else None,
            "min": float(med_by_city.min()) if len(med_by_city) else None,
            "max": float(med_by_city.max()) if len(med_by_city) else None,
        },
        "reuse_total_unit_cost_median": reuse_med,
        "reuse_cost_over_tap_ratio": (
            float(reuse_med / float(np.median(med_by_city)))
            if (reuse_med is not None and len(med_by_city)) else None),
        "verdict": verdict,
        "supported_claims": may, "unsupported_claims": may_not,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": "外部数据只读; 两层表头显式处理; 缺失显式统计; 只做量级对照",
    }
    (HERE / "wp10_water_price_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    pd.DataFrame(per_city).to_csv(HERE / "wp10_industrial_tariff_by_city.csv",
                                  index=False, encoding="utf-8-sig")
    (HERE / "wp10_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp10_water_price_summary.json / .csv / _log.txt ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
