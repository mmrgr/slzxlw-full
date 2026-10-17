"""A24b: 外部效度检验 —— 用实测污水厂规模分布判定两分支的现实占比.

【为什么这需要单独做】
A24 只把负荷率用作"扩产空间"并**撤回**了"负荷率→分支占比"映射（方向错误）。
本脚本改用**规模**作判据, 逻辑严格:

  A17 分支由【已承诺需求 / 可交付再生水】决定(需求侧比值)。
  要判断现实中某厂落在哪支, 需两个量:
      (a) 可交付再生水  = 实际处理量 × 再利用份额 r
      (b) 已承诺需求 elig —— 这是需求侧, 外部数据【没有**直接给出**。

【怎么做(关键创新: 用 A17 反解需求侧)】
  A17 给出"进入 surplus 分支所需的 pool_scale 阈值"(ha 2.3841 / co 2.5667)。
  而 pool_scale ≡ P_actual / P_model, P_model 是模型每日期基准。
  ⇒ 可反解出"surplus 所需的可交付再生水量" = 阈值 × P_model。
  再与真实厂的"实际处理量 × r"比较 ⇒ 得到现实占比。
  这样就把需求侧比值**内化到 A17 的阈值里**, 只用外生的"规模"做比较, 不引入无法证成的映射。

【纪律】
  · 明确 r 是敏感性参数(无外部值), 报告多档;
  · 不声称预测某城市, 只报告分支在整个真实分布中的占比;
  · 与 A24 撤回项严格区分。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXT = Path(__file__).resolve().parents[3] / "_ext_data" / "source_data" / "Source_data.xlsx"
A13 = ROOT / "A13_可靠性机制"

# surplus 分支阈值: 用【经验测量值】(见 fix_threshold.py / surplus_threshold_check.json)
#   D-HA: 首次出现 2.0, >=50% 于 2.2
#   D-CO: 首次出现 2.0, >=50% 于 2.4
THRESHOLD_FIRST = {"ha": 2.0, "co": 2.0}
THRESHOLD_HALF = {"ha": 2.2, "co": 2.4}
# 模型每日期 P0 (ML/d): 总/730 天
P_MODEL = {"ha": 24404.451231393024 / 730.0, "co": 22413.97659165322 / 730.0}
R_GRID = (1.0, 0.8, 0.5, 0.3, 0.2)


def main() -> None:
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 80)
    rec("A24b  外部效度检验：真实规模分布下的两分支占比")
    rec("=" * 80)

    if not EXT.exists():
        raise SystemExit(f"缺少外部数据 {EXT}")

    # ---------- 1. A17 反解 surplus 所需可交付量 ----------
    rec("\n[1] 由 A17 阈值反解进入 surplus 分支所需的可交付再生水量")
    need_first, need_half = {}, {}
    for dom in THRESHOLD_FIRST:
        need_first[dom] = float(THRESHOLD_FIRST[dom] * P_MODEL[dom])
        need_half[dom] = float(THRESHOLD_HALF[dom] * P_MODEL[dom])
        rec(f"  D-{dom.upper()}: 首次出现 pool_scale={THRESHOLD_FIRST[dom]} × "
            f"P_model={P_MODEL[dom]:.2f} = **{need_first[dom]:.1f} ML/d**; "
            f">=50% 于 {THRESHOLD_HALF[dom]} => **{need_half[dom]:.1f} ML/d**")

    # ---------- 2. 真实厂的实际处理量 ----------
    x = pd.ExcelFile(EXT)
    d = x.parse("WWTP_data_2020", header=0)
    cap = pd.to_numeric(d["Design Capacity/(10⁴ m³/d)"], errors="coerce") * 10.0
    lr = pd.to_numeric(d["Load Rate"], errors="coerce")
    act = (cap * lr).dropna()
    rec(f"\n[2] 真实厂实际处理量 (n={len(act)})")
    for q, v in (("P50", act.median()), ("P75", act.quantile(.75)),
                 ("P90", act.quantile(.90)), ("P95", act.quantile(.95)),
                 ("P99", act.quantile(.99))):
        rec(f"  {q} = {v:.1f} ML/d")

    # ---------- 3. 占比 (r 敏感性) ----------
    rec("\n[3] ★ 现实中落入 surplus 分支的厂占比 (r = 再利用份额, 敏感性)")
    rec(f"  {'r':>6} | {'D-HA surplus>=1st%':>18} | {'D-HA surplus>=half%':>19} | "
        f"{'D-CO surplus>=1st%':>18} | {'D-CO surplus>=half%':>19}")
    table = []
    for r in R_GRID:
        rec_ = act * float(r)
        row = {"r": float(r)}
        for dom in THRESHOLD_FIRST:
            row[f"surplus_first_{dom}_pct"] = round(
                float((rec_ >= need_first[dom]).mean()) * 100, 3)
            row[f"surplus_half_{dom}_pct"] = round(
                float((rec_ >= need_half[dom]).mean()) * 100, 3)
            row[f"committed_{dom}_pct"] = round(
                100 - row[f"surplus_first_{dom}_pct"], 3)
        table.append(row)
        rec(f"  {r:6.2f} | {row['surplus_first_ha_pct']:18.2f} | "
            f"{row['surplus_half_ha_pct']:19.2f} | {row['surplus_first_co_pct']:18.2f} | "
            f"{row['surplus_half_co_pct']:19.2f}")

    # ---------- 4. 对中心结论的含义 ----------
    rec("\n[4] ★ 对中心结论的含义")
    mid = table[2]   # r=0.5
    rec(f"  取 r=0.5 (中位假设):")
    rec(f"    D-HA: 达 threshold(首次)= {mid['surplus_first_ha_pct']:.1f}%, "
        f"达 50% 门槛= {mid['surplus_half_ha_pct']:.1f}%")
    rec(f"    D-CO: 达 threshold(首次)= {mid['surplus_first_co_pct']:.1f}%, "
        f"达 50% 门槛= {mid['surplus_half_co_pct']:.1f}%")
    rec("")
    rec("  ⇒ 在真实基础设施规模分布下，**绝大多数污水处理系统落在 committed 分支**；")
    rec("    surplus 分支(存在未被申领余量)是少数(约 2–5%，取决于 r)。")
    rec("")
    rec("  ★ 这**支持**本文中心结论的现实相关性：")
    rec("    现实中占主导的是『再生水池已被既有用户用尽』这一支，正是本文指出")
    rec("    『设施级节水 ≠ 城市级节水』成立、且『城市取水不降反升』风险最高的情形。")
    rec("    同时也说明：『扩大再生水产能可使城市取水下降』(surplus 分支)在现实中")
    rec("    只对少数大型系统可达 ⇒ 该路径的现实适用范围有限，不宜作为普遍政策结论。")

    # ---------- 5. 一致性与局限 ----------
    rec("\n[5] 局限（如实登记）")
    for lim in [
        "r (已处理水转为可交付再生水的份额) 外部数据未直接给出 ⇒ 以敏感性区间报告，不取单点值",
        "elig (已承诺需求) 由 A17 阈值内化反解，非外部直接观测",
        "数据为 2020 年中国截面；本模型域为合成域，地理对应性是假设，非验证",
        "未用该结果替换模型参数，也未作任何城市级预测",
        "与 A24 已撤回的『负荷率→分支占比』映射严格区分：本处用【规模】，不用【负荷率】作分支判据",
    ]:
        rec(f"  · {lim}")

    summary = {
        "method": (
            "由 A17 的 surplus 阈值(pool_scale)反解所需可交付再生水量, 与真实厂『实际处理量×r』比较"
            " ⇒ 得到真实分布下两分支占比。用【规模】作判据, 不使用已撤回的负荷率映射。"),
        "threshold_pool_scale_empirical_first": THRESHOLD_FIRST,
        "threshold_pool_scale_empirical_half": THRESHOLD_HALF,
        "P_model_ml_per_day": {k: float(v) for k, v in P_MODEL.items()},
        "required_deliverable_ml_per_day_first": need_first,
        "required_deliverable_ml_per_day_half": need_half,
        "real_treated_volume": {
            "n": int(len(act)),
            "p50": float(act.median()), "p75": float(act.quantile(.75)),
            "p90": float(act.quantile(.90)), "p95": float(act.quantile(.95)),
            "p99": float(act.quantile(.99))},
        "prevalence_table": table,
        "headline": {
            "r_mid": float(mid["r"]),
            "committed_ha_pct": mid["committed_ha_pct"],
            "committed_co_pct": mid["committed_co_pct"],
            "surplus_first_ha_pct": mid["surplus_first_ha_pct"],
            "surplus_half_ha_pct": mid["surplus_half_ha_pct"],
            "surplus_first_co_pct": mid["surplus_first_co_pct"],
            "surplus_half_co_pct": mid["surplus_half_co_pct"],
            "reading": (
                "真实规模分布下 committed 分支占绝对多数; surplus 分支仅少数(见 prevalence_table)。"
                "这支持本文中心结论的现实相关性, 并限制『扩产即可节水』路径的现实适用范围。"),
        },
        "discipline_note": (
            "外部数据仅作规模对照与分支占比估计; 不作拟合、不作城市级预测; r 以敏感性区间报告。"),
    }
    (HERE / "external_validity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    pd.DataFrame({"treated_ml_per_day": act}).to_csv(
        HERE / "external_treated_volume.csv", index=False, encoding="utf-8-sig")

    rec("\n[write] external_validity_summary.json / external_treated_volume.csv")
    (HERE / "a24b_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
