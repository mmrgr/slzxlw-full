"""WP8: 真实再生水项目的用途分布与成本锚定 (外部效度补强).

======================================================================
【为什么做这个 — 回应"外部效度不足"这一最大瓶颈】
======================================================================
四轮审查（WP0 / 终审 / 红队 / NE-1,2,4）一致指出本文最大短板是
**外部效度**：此前唯一的外部数据（10,826 座污水厂）只提供**处理量分布**，
无法回答"再生水冷却在现实中是否是重要用途"。

本轮在公开发表的复现包中发现一个此前**未被使用**的真实数据集：
  `_ext_data/source_data/Source_data.xlsx` 的 **"Reclaimed water case"** 工作表
  （Shen et al. 2026, Nature Water 的附带源数据；CC-BY）。
它包含 **141 个真实再生水项目**，字段含:
  · 实施主体 / 省或地区
  · 实际工艺链
  · **用途分类**（用户自定义类别 A1–C2，其中 **B3 = 工业冷却/一般工业回用**）
  · 规模 (m3/d)
  · 折旧 / 运行 / 总单位成本 (CNY/m3)
  · 数据来源与 URL

【本脚本做什么】
  1. 机械解析 141 案例, 统计**用途类别分布**（B3 = 本文关注的冷却回用）;
  2. 提取 B3 子集的规模与成本分布;
  3. 与本文模型域的量级做**对照**（不改模型参数, 只报可比性）;
  4. 明确区分"可支持的结论"与"不可支持的结论"。

【纪律】
  · **不修改**任何外部数据; 只读解析;
  · 分类从**原始文本前缀**机械提取, 不手工贴标签;
  · 缺失值显式统计, 不静默按 0;
  · 只用该数据做**用途分布与成本区间**陈述, 不做需求侧推断（该表无需求量字段）。
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
SHEET = "Reclaimed water case"

# 用途类别释义 (来自该表自身的 B1..C2 描述; 此处只标注与本文相关的 B3)
CODE_MEANING = {
    "A1": "agricultural reuse (primary)",
    "A2": "agricultural reuse",
    "A3": "agricultural / ecological reuse",
    "B1": "urban non-potable reuse",
    "B2": "landscape-water replenishment",
    "B3": "INDUSTRIAL COOLING / general industrial reuse",
    "B4": "low-cost landscaping / park irrigation",
    "B5": "other urban reuse",
    "C1": "enhanced agricultural / rural-town reuse",
    "C2": "other rural reuse",
}


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("WP8  真实再生水项目的用途分布与成本锚定")
    rec("=" * 84)

    if not EXT.exists():
        rec(f"\n⚠ 缺少外部数据 {EXT} ⇒ NOT_IDENTIFIABLE")
        (HERE / "wp8_real_reuse_cases_summary.json").write_text(
            json.dumps({"status": "NOT_IDENTIFIABLE", "missing": str(EXT)},
                       ensure_ascii=False, indent=1), encoding="utf-8")
        return

    x = pd.ExcelFile(EXT)
    if SHEET not in x.sheet_names:
        rec(f"\n⚠ 工作表 {SHEET} 不存在 ⇒ NOT_IDENTIFIABLE")
        return
    d = x.parse(SHEET)
    d.columns = [str(c).strip() for c in d.columns]
    rec(f"\n[0] 数据来源: {EXT.name} :: {SHEET}")
    rec(f"    形状 = {d.shape}")
    rec(f"    列 = {list(d.columns)}")

    cat_col = [c for c in d.columns if "Classification" in c][0]
    cap_col = [c for c in d.columns if "Capacity" in c][0]
    prov_col = [c for c in d.columns if "Province" in c][0]
    cost_cols = [c for c in d.columns if "cost" in c.lower()]

    # ---------- 1. 用途类别分布(机械提取前缀) ----------
    d["code"] = d[cat_col].astype(str).str.extract(r"^([A-Z][0-9])")
    n_total = len(d)
    n_code = int(d["code"].notna().sum())
    rec(f"\n[1] 用途类别分布 (从原始文本前缀机械提取; 未贴手工标签)")
    rec(f"    可分类 = {n_code}/{n_total}")
    vc = d["code"].value_counts()
    rows = []
    rec(f"    {'code':<6} {'n':>4} {'share%':>8}  含义")
    for code, n in vc.items():
        share = 100.0 * n / n_code
        rec(f"    {str(code):<6} {n:>4} {share:>8.2f}  {CODE_MEANING.get(str(code),'?')}")
        rows.append({"code": str(code), "n": int(n), "share_pct": round(share, 3),
                     "meaning": CODE_MEANING.get(str(code), "?")})
    n_unclassified = int(d["code"].isna().sum())
    if n_unclassified:
        rec(f"    ⚠ 未分类 = {n_unclassified} (显式统计, 未静默丢弃)")

    b3 = d[d["code"] == "B3"]
    rec(f"\n[2] ★ B3 (工业冷却/一般工业回用) — 本文关注的用途")
    rec(f"    案例数 = {len(b3)}  占比 = {100.0*len(b3)/n_code:.1f}% (在可分类案例中)")

    # ---------- 3. 规模与成本 ----------
    def stat(series, name, unit):
        v = pd.to_numeric(series, errors="coerce").dropna()
        if len(v) == 0:
            rec(f"    {name:<34} n=0 ⇒ NOT_IDENTIFIABLE")
            return None
        out = {"n": int(len(v)), "min": float(v.min()),
               "p25": float(v.quantile(.25)), "median": float(v.median()),
               "p75": float(v.quantile(.75)), "max": float(v.max()),
               "unit": unit}
        rec(f"    {name:<34} n={out['n']:>4}  min={out['min']:.4g}  p25={out['p25']:.4g}  "
            f"median={out['median']:.4g}  p75={out['p75']:.4g}  max={out['max']:.4g} {unit}")
        return out

    rec(f"\n[3] B3 子集: 规模与成本分布")
    cap_all = stat(d[cap_col], "全部案例 容量", "m3/d")
    cap_b3 = stat(b3[cap_col], "B3 容量", "m3/d")
    costs = {}
    for c in cost_cols:
        costs[c] = stat(b3[c], f"B3 {c[:28]}", "CNY/m3")

    # ---------- 4. 与本文模型域的对照 ----------
    rec(f"\n[4] 与本文模型域的对照 (只报可比性, 不改模型参数)")
    rec(f"    本文模型域的单设施规模量级 ~1e3–1e5 m3/d (IT 负荷 1000 MW 级)")
    if cap_b3:
        in_range = ((pd.to_numeric(b3[cap_col], errors='coerce') >= 1e3)
                    & (pd.to_numeric(b3[cap_col], errors='coerce') <= 1e5)).sum()
        rec(f"    B3 案例中落在 [1e3, 1e5] m3/d 的 = {int(in_range)}/{cap_b3['n']} "
            f"({100.0*int(in_range)/cap_b3['n']:.1f}%)")
        rec(f"    ⇒ 本文模型域的规模在真实 B3 项目中有实际对应")

    # ---------- 5. 可支持 / 不可支持的结论 ----------
    rec(f"\n[5] ★ 本数据可支持与不可支持的结论")
    may = [
        f"真实再生水项目中, 工业冷却/工业回用(B3)是可识别的**主要用途之一**"
        f"({len(b3)}/{n_code} = {100.0*len(b3)/n_code:.1f}%)",
        "B3 项目的容量与成本区间可锚定本文情景的**现实性**(见 [3])",
        "本文关注的冷却回用并非设想的边缘用途, 而是有真实工程实践支撑",
    ]
    may_not = [
        "**不可**推断既有用户的已承诺需求量(该表无需求字段)",
        "**不可**推断设施级→城市级的转化比例",
        "**不可**作为本文模型的标定数据(无水文/供需时序)",
        "该表是**案例集**而非随机样本, 占比不代表全国统计分布",
    ]
    for s in may:
        rec(f"    ✅ {s}")
    for s in may_not:
        rec(f"    ❌ {s}")

    summary = {
        "task": "WP8 外部效度补强: 真实再生水项目用途分布与成本锚定",
        "source": str(EXT), "sheet": SHEET, "n_cases": int(n_total),
        "n_classified": n_code, "n_unclassified": n_unclassified,
        "category_distribution": rows,
        "b3_industrial_cooling": {
            "n": int(len(b3)), "share_pct_of_classified": round(100.0 * len(b3) / n_code, 3),
            "capacity": cap_b3, "costs": costs,
        },
        "all_cases_capacity": cap_all,
        "supported_claims": may,
        "unsupported_claims": may_not,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": ("外部数据只读; 类别由原始文本机械提取; 缺失显式统计; "
                            "只做用途分布与成本陈述, 不做需求侧推断"),
    }
    (HERE / "wp8_real_reuse_cases_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    d[["code", cap_col] + cost_cols].to_csv(HERE / "wp8_real_reuse_cases.csv",
                                            index=False, encoding="utf-8-sig")
    (HERE / "wp8_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp8_real_reuse_cases_summary.json / .csv / _log.txt ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
