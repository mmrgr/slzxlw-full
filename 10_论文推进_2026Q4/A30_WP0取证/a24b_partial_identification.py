"""A24b 修正版 (WP0 取证, 2026-10-16): 用【部分识别】替代"真实已承诺占比"的点估计.

======================================================================
【为什么必须改】—— 对 external_validity.py 的方法学否证
======================================================================
A24b 原脚本把
    undershoot = "实际处理量 × r  低于  A17 反解阈值"
直接读作 "该设施处于 committed(已承诺用尽) 分支", 并报出 93–99%。
主稿据此写出 "above 95% of real facilities are fully committed" 的【实证主张】。

该推断在逻辑上不成立, 原因是它把两个不同的量等同:

  (i)  生产能力 (供方): 该厂能产出多少可交付再生水  = 处理量 × r
  (ii) 已承诺需求 (需方): 既有用户实际已申领/合同锁定的再生水量

原脚本只观测到 (i), 却据此对 (ii) 下结论。判据 "处理量×r < 阈值" 的
真实含义只是: "该厂的【潜在产水能力】不足以满足模型阈值所代表的那个需求量",
它【完全不能】说明既有用户是否真的已经申领了这些水。

  反例(逻辑上充分): 一座处理量很小的厂, 产水能力 1 ML/d, 而既有用户
  实际只申领 0.1 ML/d —— 池子大部分闲置(surplus), 但原脚本仍判它 committed,
  因为它 1 < 33。可见该判据与"是否已承诺用尽"无因果关系。
  同理, 一座处理量极大的厂即使既有用户申领很多, 也会被判 surplus。

⇒ 结论: committed/surplus 占比在本数据下【不可识别(unidentified)】。
   原脚本报出的 93–99% 是【特定假设下的情景比例】, 不是对真实设施的观测,
   绝不能写成"empirical prevalence"。

======================================================================
【正确做法】—— 部分识别 (partial identification)
======================================================================
设厂 i 的可交付再生水 D_i = 处理量_i × r (供方上限, 已观测)。
既有用户已承诺需求 E_i 完全未观测, 但其取值必然落在 [0, D_i] 区间内
(不可能申领超过可交付量的水; 若申领超过则可交付量会被截断到 D_i)。

分支判据 (按 A17 语义): 若 E_i 达到"使池子无剩余"的水平, 则属 committed。
在本数据下 E_i 只能取 [0, D_i] 内任意值 ⇒ 对每座厂, committed 与否都可能成立。

因此可得【可证明的界】:
  下界 (最少可能的 committed 占比) = 0       —— 若所有厂 E_i=0, 则全为 surplus
  上界 (最多可能的 committed 占比) = 100%    —— 若所有厂 E_i=D_i, 则全为 committed

这个界太宽 ⇒ 说明【该数据无法识别分支占比】。这正是必须如实报告的结论,
而不是硬报一个点估计。

【能做什么】—— 报告"产能可达性"这个【可识别】的量
虽然分支占比不可识别, 但有一个量是可识别的且有政策意义:
   P_surplus_capable = P( 处理量_i × r >= D_required )
即"该厂的产水能力【足以】支撑一个 surplus 型方案"的比例。
这是个关于【产能上限】的陈述, 与需求侧无关, 因此严格成立。
注意其正确读法: 它【不是】"现实中有多少厂处于 surplus 分支",
而是"有多少厂的产能【足以】让 surplus 方案在物理上可行"。

【纪律】
  · 不报 committed 占比的点估计; 只报可识别量的界与产能可达性;
  · 保留原脚本输出作审计留痕, 但明确标注其解释错误;
  · 不修改引擎, 不改动 A24 其他产物。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Windows 控制台默认 GBK, 日志含数学符号时会 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A24 = ROOT / "A24_外部锚定"
EXT = Path(__file__).resolve().parents[3] / "_ext_data" / "source_data" / "Source_data.xlsx"

# 沿用原脚本的经验阈值与模型基准(不改), 以便与旧结果直接对照
THRESHOLD_FIRST = {"ha": 2.0, "co": 2.0}
THRESHOLD_HALF = {"ha": 2.2, "co": 2.4}
P_MODEL = {"ha": 24404.451231393024 / 730.0, "co": 22413.97659165322 / 730.0}
R_GRID = (1.0, 0.8, 0.5, 0.3, 0.2)


def main() -> None:
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 78)
    rec("A24b 修正版: 部分识别 (取代 '真实已承诺占比' 点估计)")
    rec("=" * 78)

    if not EXT.exists():
        raise SystemExit(f"缺少外部数据 {EXT}")

    # ---------- 1. 需求侧的不可识别性论证 ----------
    rec("\n[1] ★ 核心方法学结论: 分支占比在本数据下【不可识别】")
    rec("""
  原脚本判据:  处理量 × r  <  阈值   ⇒  判为 'committed'
  该判据只观测到【生产能力】(供方), 未观测【已承诺需求】(需方)。
  二者独立: 小厂可以池子闲置(需求极低), 大厂可以池子用尽(需求高)。
  ⇒ '处理量×r < 阈值' 与 '既有用户已申领用尽' 之间【无因果/蕴含关系】。

  形式化: 设 D_i = 处理量_i × r 为可交付上限(已观测), E_i 为已承诺需求(未观测)。
          物理约束给出 0 <= E_i <= D_i。
          对任意厂, E_i 遍历 [0, D_i] 时 committed 与 surplus 两种状态【都能出现】。
  ⇒ 可证明的界为
        最少 committed 占比 = 0%
        最多 committed 占比 = 100%
     这个界【不含信息】, 说明本数据无法回答问题。
""")

    # ---------- 2. 可识别量: 产能可达性 ----------
    x = pd.ExcelFile(EXT)
    d = x.parse("WWTP_data_2020", header=0)
    cap = pd.to_numeric(d["Design Capacity/(10⁴ m³/d)"], errors="coerce") * 10.0
    lr = pd.to_numeric(d["Load Rate"], errors="coerce")
    act = (cap * lr).dropna()
    rec(f"[2] 真实厂实际处理量 (n={len(act)}; 口径=设计能力×负荷率)")
    for q, v in (("P50", act.median()), ("P75", act.quantile(.75)),
                 ("P90", act.quantile(.90)), ("P95", act.quantile(.95)),
                 ("P99", act.quantile(.99))):
        rec(f"    {q} = {v:.1f} ML/d")

    need_first = {k: float(v * P_MODEL[k]) for k, v in THRESHOLD_FIRST.items()}
    need_half = {k: float(v * P_MODEL[k]) for k, v in THRESHOLD_HALF.items()}
    rec("\n[3] 可识别量: 产水能力【足以】支撑 surplus 型方案的厂占比")
    rec("    (正确读法: 产能可行性 上界;  *不是* 现实中处于 surplus 分支的比例)")
    rec(f"  {'r':>6} | {'HA >=first%':>12} | {'HA >=half%':>12} | "
        f"{'CO >=first%':>12} | {'CO >=half%':>12}")
    rows = []
    for r in R_GRID:
        D = act * float(r)
        row = {"r": float(r)}
        for dom, need in (("ha", need_first), ("co", need_first)):
            row[f"capable_first_{dom}_pct"] = round(float((D >= need[dom]).mean()) * 100, 3)
        for dom, need in (("ha", need_half), ("co", need_half)):
            row[f"capable_half_{dom}_pct"] = round(float((D >= need[dom]).mean()) * 100, 3)
        rows.append(row)
        rec(f"  {r:6.2f} | {row['capable_first_ha_pct']:12.2f} | "
            f"{row['capable_half_ha_pct']:12.2f} | {row['capable_first_co_pct']:12.2f} | "
            f"{row['capable_half_co_pct']:12.2f}")

    # ---------- 3. 额外可识别证据: 分布形态 ----------
    rec("\n[4] 分布形态(可识别, 支持'大型厂为少数'的定性结论)")
    n = len(act)
    for thr_name, thr in (("阈值~67 ML/d(ha first)", need_first["ha"]),
                          ("阈值~62 ML/d(co first)", need_first["co"])):
        over = int((act >= thr).sum())
        rec(f"  {thr_name}: 处理量超阈值的厂数 = {over}/{n} = {over/n*100:.2f}% "
            f"(仅说明'产能上足以'的少数性, 与需求侧无关)")

    # ---------- 4. 与旧结论的差异(审计留痕) ----------
    old = A24 / "external_validity_summary.json"
    old_read = None
    if old.exists():
        try:
            old_read = json.loads(old.read_text(encoding="utf-8"))
        except Exception:
            old_read = None
    rec("\n[5] ★ 与 A24b 原结论的对照 (审计留痕)")
    if old_read:
        oh = old_read.get("headline", {})
        rec(f"  原报(错误): committed_ha = {oh.get('committed_ha_pct')}% , "
            f"committed_co = {oh.get('committed_co_pct')}%  (r=0.5)")
        rec("  问题: 把'产能不足'读成'需求已承诺', 得到的是【假设下的情景比例】")
    rec("  新报(正确): committed 占比【不可识别】, 可证明界 = [0%, 100%]")
    rec("  可识别替代量: 产能足以支撑 surplus 方案的占比(见 [3]) —— 只陈述产能, 不涉需求")

    summary = {
        "supersedes": "external_validity_summary.json (A24b 原版, 解释错误)",
        "status_of_original_claim": "WITHDRAWN_AS_UNIDENTIFIED",
        "why_unidentified": (
            "判据 处理量×r < 阈值 只观测生产能力(供方 D_i), 未观测已承诺需求(需方 E_i); "
            "物理约束仅给出 0<=E_i<=D_i, 对任意厂两种分支状态都可能出现 ⇒ 不可识别"),
        "provable_bounds_committed_pct": {"lower": 0.0, "upper": 100.0},
        "identifiable_quantity": {
            "name": "capacity_sufficient_for_surplus_pct",
            "meaning": ("该厂产水能力(处理量×r) >= 模型反解阈值的比例。"
                        "只陈述【产能可行性】, 与既有用户实际需求无关。"),
            "table": rows,
        },
        "real_treated_volume": {
            "n": int(n), "p50": float(act.median()), "p75": float(act.quantile(.75)),
            "p90": float(act.quantile(.90)), "p95": float(act.quantile(.95)),
            "p99": float(act.quantile(.99))},
        "real_treated_volume_by_r": {
            f"{r}": {
                "capable_first_ha_pct": next(x for x in rows if x["r"] == float(r))["capable_first_ha_pct"],
                "capable_first_co_pct": next(x for x in rows if x["r"] == float(r))["capable_first_co_pct"],
            } for r in R_GRID},
        "thresholds_ml_per_day": {"first": need_first, "half": need_half},
        "permitted_claim": (
            "只可声称: (a) 真实污水厂处理量分布高度右偏, 大型厂为少数; "
            "(b) 在这些厂中仅少数(约 2–6%, 随 r)的产水能力足以支撑一个达到模型阈值的 surplus 型方案。"
            "【不可】声称现实中多少比例设施处于 committed 分支。"),
        "forbidden_claims": [
            "above 95% of real facilities are fully committed",
            "committed branch is the empirically dominant one",
            "empirical prevalence of the fully-committed regime",
        ],
        "discipline_note": (
            "外部数据仅作产能分布对照; 需求侧无观测 ⇒ 分支占比不可识别, 以可证明界报告。"),
    }
    (HERE / "a24b_partial_id_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    pd.DataFrame(rows).to_csv(HERE / "a24b_capacity_table.csv", index=False,
                             encoding="utf-8-sig")
    (HERE / "a24b_partial_id_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec("\n[write] a24b_partial_id_summary.json / a24b_capacity_table.csv / a24b_partial_id_log.txt")


if __name__ == "__main__":
    main()
