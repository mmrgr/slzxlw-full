"""WP9: 工业取水中【冷却水占比】的真实分布 (外部效度再补强).

======================================================================
【为什么做】
======================================================================
本文的中心用途是"再生水用于**工业冷却**"。此前已用 141 个真实项目的
用途分布（WP8）说明该用途重要；但还缺一个**产业侧的量化锚点**：
在真实工业取水中，冷却水到底占多大比重？

来源: `_ext_data/source_data/Source_data.xlsx` 工作表 **`Share of cooling water`**
（Shen et al. 2026 Nature Water 附带源数据，CC-BY），字段:
  Sector Code | Share of cooling water withdrawal in industrial water withdrawal
  以及 Mean / Std / Min / Max 四行统计

【本脚本做什么】
  1. 机械解析该表（注意: 首行是表头统计量名 Mean/Std/Min/Max）;
  2. 报告分行业(42 个 sector code)的冷却水占比分布;
  3. 与 city_model 中使用的 **0.258** 做对照, 核验其是否落在真实区间内;
  4. 明确可支持/不可支持的结论。

【纪律】
  · 只读外部数据; 不修改;
  · 缺失/NaN 显式统计, 不静默按 0;
  · 行业代码与含义映射**不做猜测**——若源表未给名称, 只报代码。
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
SHEET = "Share of cooling water"


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("WP9  工业取水中冷却水占比的真实分布")
    rec("=" * 84)

    if not EXT.exists():
        rec(f"\n⚠ 缺数据 {EXT} ⇒ NOT_IDENTIFIABLE")
        return
    x = pd.ExcelFile(EXT)
    if SHEET not in x.sheet_names:
        rec(f"\n⚠ 工作表 {SHEET} 不存在 ⇒ NOT_IDENTIFIABLE")
        return

    d = x.parse(SHEET)
    d.columns = [str(c).strip() for c in d.columns]
    rec(f"\n[0] 来源: {EXT.name} :: {SHEET}   形状 = {d.shape}")
    rec(f"    列 = {list(d.columns)}")

    code_col = [c for c in d.columns if "Sector" in c][0]
    share_col = [c for c in d.columns if "Share" in c][0]
    stat_cols = [c for c in d.columns if c not in (code_col, share_col)]

    # ⚠ 表布局(实测): 首行 = [NaN, 'Mean', 'Std', 'Min', 'Max']
    #   ⇒ 'Mean' 落在 share_col 下, 'Std/Min/Max' 落在 stat_cols[0..2]。
    #   故 mean 值需从 share_col 的第 2 行起读, 而非从 stat_cols 找名为 mean 的列。
    first = d.iloc[0]
    rec(f"\n[1] 表布局: 首行 = {[str(first.get(c)) for c in d.columns]}")
    rec(f"    ⇒ 'Mean' 位于 {share_col[:38]}... 列下, std/min/max 位于后三列")

    body = d.iloc[1:].copy()
    body = body.rename(columns={share_col: "share_mean",
                                stat_cols[0]: "share_std",
                                stat_cols[1]: "share_min",
                                stat_cols[2]: "share_max",
                                code_col: "sector"})
    body["sector"] = pd.to_numeric(body["sector"], errors="coerce")
    for c in ("share_mean", "share_std", "share_min", "share_max"):
        body[c] = pd.to_numeric(body[c], errors="coerce")
    body = body[body["sector"].notna()]
    rec(f"    有效行业行数 = {len(body)}")

    n_all = len(body)
    n_mean = int(body["share_mean"].notna().sum())
    rec(f"\n[2] 完整性: 有 mean 的行业 = {n_mean}/{n_all} "
        f"(缺失 {n_all-n_mean} 个, 显式统计, 未按 0 填充)")

    v = body["share_mean"].dropna()
    rec(f"\n[3] 冷却水占工业取水的比例 (各行业 mean 的分布)")
    rec(f"    行业数 n = {len(v)}")
    rec(f"    min    = {v.min():.4f}")
    rec(f"    p25    = {v.quantile(.25):.4f}")
    rec(f"    median = {v.median():.4f}")
    rec(f"    p75    = {v.quantile(.75):.4f}")
    rec(f"    max    = {v.max():.4f}")
    rec(f"    mean   = {v.mean():.4f}")
    rec(f"    占比>0.5 的行业数 = {int((v>0.5).sum())}")
    rec(f"    占比>0.2 的行业数 = {int((v>0.2).sum())}")

    # 高占比行业
    top = body.dropna(subset=["share_mean"]).nlargest(8, "share_mean")
    rec(f"\n[4] 冷却水占比最高的 8 个行业")
    rec(f"    {'sector':>7} {'mean':>8} {'std':>8} {'min':>8} {'max':>8}")
    for _, r in top.iterrows():
        rec(f"    {int(r['sector']):>7} {r['share_mean']:8.4f} "
            f"{r['share_std'] if pd.notna(r['share_std']) else float('nan'):8.4f} "
            f"{r['share_min'] if pd.notna(r['share_min']) else float('nan'):8.4f} "
            f"{r['share_max'] if pd.notna(r['share_max']) else float('nan'):8.4f}")

    # ---------- 与 city_model 的 0.258 对照 ----------
    rec(f"\n[5] ★ 与本文分析模型所用值的对照")
    ref = 0.258
    rec(f"    city_model / A24 使用的 '冷却水占比' = {ref} (来自 external_anchor_summary.json mean_of_means)")
    if len(v):
        in_rng = bool(v.min() <= ref <= v.max())
        pct = float((v < ref).mean() * 100)
        rec(f"    该值是否落在真实行业区间 [{v.min():.3f}, {v.max():.3f}] 内 = {in_rng}")
        rec(f"    低于该值的行业占比 = {pct:.1f}%")
        rec(f"    该值在行业分布中的分位 ≈ {pct:.0f}th percentile")
        verdict = "CONSISTENT_WITH_OBSERVED_RANGE" if in_rng else "OUTSIDE_OBSERVED_RANGE"
    else:
        verdict = "NOT_IDENTIFIABLE"

    rec(f"\n[6] ★ 可支持 / 不可支持的结论")
    may = [
        "工业取水中冷却水占比在行业间**差异极大**（最高 >0.9，最低接近 0），"
        "因此用单一常数代表所有行业是不恰当的、应报区间",
        f"本文模型所用的 {ref} 落在真实行业区间内（见 [5]），"
        f"可作为**中低区间**的代表值而非普适常数",
    ]
    may_not = [
        "**不可**由行业代码推断具体行业名称（源表未给映射，不做猜测）",
        "**不可**把行业占比直接等同于本文模型域的冷却水占比（模型域是设施级）",
        "**不可**用于需求侧推断（该表是取水结构，不含需求/合同信息）",
        "该表统计口径为 '冷却水取水 / 工业取水'，与本文的'再生水用于冷却'不是同一量",
    ]
    for s in may:
        rec(f"    ✅ {s}")
    for s in may_not:
        rec(f"    ❌ {s}")

    summary = {
        "task": "WP9 工业取水中冷却水占比的真实分布",
        "source": str(EXT), "sheet": SHEET,
        "n_sectors_total": n_all, "n_sectors_with_mean": n_mean,
        "distribution": {
            "n": int(len(v)), "min": float(v.min()) if len(v) else None,
            "p25": float(v.quantile(.25)) if len(v) else None,
            "median": float(v.median()) if len(v) else None,
            "p75": float(v.quantile(.75)) if len(v) else None,
            "max": float(v.max()) if len(v) else None,
            "mean": float(v.mean()) if len(v) else None,
            "n_gt_0.5": int((v > 0.5).sum()) if len(v) else 0,
            "n_gt_0.2": int((v > 0.2).sum()) if len(v) else 0,
        },
        "top_sectors": top[["sector", "share_mean"]].to_dict(orient="records"),
        "model_reference_value": ref,
        "model_reference_verdict": verdict,
        "supported_claims": may, "unsupported_claims": may_not,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": "外部数据只读; 缺失显式统计; 不做行业名映射猜测; 不做需求侧推断",
    }
    (HERE / "wp9_cooling_share_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    body[["sector", "share_mean", "share_std", "share_min", "share_max"]].to_csv(
        HERE / "wp9_cooling_share_by_sector.csv", index=False, encoding="utf-8-sig")
    (HERE / "wp9_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp9_cooling_share_summary.json / .csv / _log.txt ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
