# -*- coding: utf-8 -*-
"""主稿 v2 新增数值的核对表生成器。

逐条验证主稿 v2 中引用的每个 r* 相关数值，并输出「数值 → 来源文件 → 判定」表。
任何 FAIL 都意味着主稿引用了一个产物不支持的数字。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_verify_v2_numbers.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent.parent
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"

RESULTS: list[tuple[str, str, str, bool]] = []


def check(claim: str, value: str, source: str, ok: bool) -> None:
    RESULTS.append((claim, value, source, bool(ok)))


def main() -> None:
    # ---- 参数与 r* ----
    LIMIT, COC_D, C_P, C_R = 2200.0, 5.0, 180.0, 650.0
    r_star = (LIMIT / COC_D - C_P) / (C_R - C_P)
    check("r* 闭式解", f"{r_star:.4f}", "四参数手算（11_理论推导 §2.4）", abs(r_star - 0.5532) < 5e-4)

    # 参数来源核对：必须与 project.json 一致
    proj = json.loads((PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "examples"
                       / "cawcc_r2" / "ha" / "project.json").read_text(encoding="utf-8"))
    dc = next(v for v in proj["components"].values() if v.get("kind") == "data_center")
    cool = dc["cooling"]
    check("L（TDS 限值）来自 project.json",
          f"{cool['water_quality_limits']['TDS']}",
          "examples/cawcc_r2/ha/project.json cooling.water_quality_limits.TDS",
          float(cool["water_quality_limits"]["TDS"]) == LIMIT)
    check("CoC_design 来自 project.json",
          f"{cool['cycles_of_concentration']}",
          "同项目文件 cooling.cycles_of_concentration",
          float(cool["cycles_of_concentration"]) == COC_D)
    check("C_reclaimed 来自 project.json",
          f"{dc['water_sources']['reclaimed']['quality']['TDS']}",
          "同项目文件 AI_DC1.water_sources.reclaimed.quality.TDS",
          float(dc["water_sources"]["reclaimed"]["quality"]["TDS"]) == C_R)
    check("C_potable 来自 project.json",
          f"{dc['water_sources']['potable']['quality']['TDS']}",
          "同项目文件 AI_DC1.water_sources.potable.quality.TDS",
          float(dc["water_sources"]["potable"]["quality"]["TDS"]) == C_P)

    # ---- CoC 与解析式一致性 ----
    probe = pd.read_csv(R2 / "probe_rstar_mechanism.csv", encoding="utf-8-sig")
    err = (probe["coc_mean"] - probe["coc_analytic"]).abs().max()
    check("CoC 模型 vs 解析式最大偏差 = 8.9e-16",
          f"{err:.3e}", "r2/probe_rstar_mechanism.csv", err < 1e-12)

    # r=0.9 的 CoC 出自全网格扫描（probe 只含 0.0/0.3/0.5/0.6/0.8）
    ha_scan = pd.read_csv(R2 / "rstar_scan_ha.csv", encoding="utf-8-sig")
    coc09 = float(ha_scan[ha_scan["target_r"] == 0.9]["coc_mean"].iloc[0])
    analytic09 = min(COC_D, LIMIT / (0.9 * C_R + 0.1 * C_P))
    check("CoC r=0.9 = 3.648（模型与解析一致）",
          f"模型{coc09:.3f} / 解析{analytic09:.3f}", "r2/rstar_scan_ha.csv",
          abs(coc09 - 3.648) < 5e-4 and abs(coc09 - analytic09) < 1e-12)
    check("CoC 由 5.0 降至 r=0.9 的降幅约 -27%",
          f"{100*(coc09/COC_D-1):+.2f}%", "同上", -28.0 < 100 * (coc09 / COC_D - 1) < -26.0)

    # ---- 反噬与容量无关 ----
    ha = pd.read_csv(R2 / "rstar_scan_ha.csv", encoding="utf-8-sig")
    base = ha[ha["target_r"] == 0.0].set_index("ai_capacity_mw")["total_withdrawal_ml"]
    incs = {}
    for cap in (200.0, 800.0, 1200.0, 1600.0):
        if cap not in base.index:
            continue
        v08 = ha[(ha["target_r"] == 0.8) & (ha["ai_capacity_mw"] == cap)]["total_withdrawal_ml"]
        if v08.empty:
            continue
        incs[cap] = 100.0 * (float(v08.iloc[0]) / float(base.loc[cap]) - 1.0)
    spread = (max(incs.values()) - min(incs.values())) if incs else float("inf")
    # 判据：四个容量点的增幅极差 < 0.02 个百分点（实测 0.0121）
    check("r 0.5→0.8 总取水增幅与容量无关（极差<0.02pp）",
          ", ".join(f"{k:.0f}MW:{v:+.2f}%" for k, v in incs.items()) + f" 极差={spread:.4f}pp",
          "r2/rstar_scan_ha.csv",
          spread < 0.02 and all(6.40 < v < 6.55 for v in incs.values()))

    # ---- 反噬在 r<=r* 精确为零 ----
    dec = pd.read_csv(R2 / "rstar_backlash_decomposition.csv", encoding="utf-8-sig")
    dec = dec.drop_duplicates(subset=["domain", "capacity_mw", "target_r"])
    below = dec[dec["target_r"] <= 0.5]["backlash_ml"].abs().max()
    above = dec[dec["target_r"] >= 0.7]["backlash_ml"].min()
    check("反噬在 r<=0.5 精确为零", f"{below:.3e} ML", "r2/rstar_backlash_decomposition.csv",
          below < 1e-9)
    check("反噬在 r>=0.7 显著为正（最小 1243 ML）",
          f"{above:.1f} ML", "同上", above > 1200.0)

    # ---- 纯物理 CAWCC ----
    ph = pd.read_csv(R2 / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")
    for domain, r, expect in (("ha", 0.0, 1200.0), ("ha", 0.9, 1100.0),
                              ("co", 0.0, 1450.0), ("co", 0.8, 1450.0)):
        sub = ph[(ph["domain"] == domain) & (ph["target_r"] == r)]
        got = float(sub["physical_cawcc_mw"].iloc[0]) if not sub.empty else float("nan")
        check(f"纯物理 CAWCC {domain.upper()} r={r} = {expect:.0f}",
              f"{got:.0f}", "r2/rstar_physical_cawcc_by_r.csv", got == expect)

    # HA r=0.9 首失效仍为水源取水比
    sub = ph[(ph["domain"] == "ha") & (ph["target_r"] == 0.9)]
    lim = sub["physical_limiting_constraint"].iloc[0] if not sub.empty else ""
    check("HA r=0.9 纯物理首失效仍为 max_source_abstraction_ratio",
          str(lim), "同上", lim == "max_source_abstraction_ratio")

    # ---- 混淆排除：同一容量点 ----
    cf = pd.read_csv(R2 / "rstar_confound_control.csv", encoding="utf-8-sig")
    ha1200 = cf[(cf["domain"] == "ha") & ((cf["capacity_mw"] - 1200.0).abs() < 1e-6)] \
        .sort_values("target_r")
    src5 = float(ha1200[ha1200["target_r"] == 0.5]["max_source_abstraction_ratio"].iloc[0])
    src6 = float(ha1200[ha1200["target_r"] == 0.6]["max_source_abstraction_ratio"].iloc[0])
    check("HA@1200MW 水源比 r=0.5 为 0.9497（合规）", f"{src5:.4f}",
          "r2/rstar_confound_control.csv", abs(src5 - 0.9497) < 5e-4)
    check("HA@1200MW 水源比 r=0.6 为 0.9513（超限）", f"{src6:.4f}",
          "同上", abs(src6 - 0.9513) < 5e-4)
    grid5 = float(ha1200[ha1200["target_r"] == 0.5]["max_daily_average_grid_connection_ratio"].iloc[0])
    grid9 = float(ha1200[ha1200["target_r"] == 0.9]["max_daily_average_grid_connection_ratio"].iloc[0])
    check("HA@1200MW 电网约束全程不变（Δ=0.0000）", f"{grid5:.4f}→{grid9:.4f}",
          "同上", abs(grid5 - grid9) < 1e-12)
    check("HA@1200MW 电网约束值 = 0.8326", f"{grid5:.4f}", "同上", abs(grid5 - 0.8326) < 5e-4)

    # CO@1600
    co1600 = cf[(cf["domain"] == "co") & ((cf["capacity_mw"] - 1600.0).abs() < 1e-6)] \
        .sort_values("target_r")
    src0 = float(co1600[co1600["target_r"] == 0.0]["max_source_abstraction_ratio"].iloc[0])
    src9 = float(co1600[co1600["target_r"] == 0.9]["max_source_abstraction_ratio"].iloc[0])
    check("CO@1600MW 水源比 r=0→0.9 增量 +0.0167", f"{src0:.4f}→{src9:.4f}（Δ{src9-src0:+.4f}）",
          "同上", abs((src9 - src0) - 0.0167) < 5e-4)

    # ---- 三杠杆（100 MW 网格口径，见 17_v1到v2修正清单.md 修正1）----
    rm = pd.read_csv(R2 / "ha" / "reuse_marginal_curve.csv", encoding="utf-8-sig")
    check("仅扩处理能力：HA CAWCC 恒 1100（100MW 网格口径）",
          f"{sorted(set(rm['cawcc_mw'].astype(float)))}",
          "r2/ha/reuse_marginal_curve.csv",
          set(rm["cawcc_mw"].astype(float)) == {1100.0})
    check("仅扩处理能力：HA 边际增益恒 0",
          f"{sorted(set(rm['marginal_gain_mw_per_ml_day'].dropna().astype(float)))}",
          "同上 marginal_gain_mw_per_ml_day",
          set(rm["marginal_gain_mw_per_ml_day"].dropna().astype(float)) == {0.0})
    rm_co = pd.read_csv(R2 / "co" / "reuse_marginal_curve.csv", encoding="utf-8-sig")
    check("仅扩处理能力：CO CAWCC 恒 1400（100MW 网格口径）",
          f"{sorted(set(rm_co['cawcc_mw'].astype(float)))}",
          "r2/co/reuse_marginal_curve.csv",
          set(rm_co["cawcc_mw"].astype(float)) == {1400.0})
    rpm = pd.read_csv(R2 / "ha" / "reuse_production_marginal_curve.csv", encoding="utf-8-sig")
    check("提高产水量：HA CAWCC 由 1100 升至 1400",
          f"{float(rpm['cawcc_mw'].min()):.0f}→{float(rpm['cawcc_mw'].max()):.0f}",
          "r2/ha/reuse_production_marginal_curve.csv",
          float(rpm["cawcc_mw"].min()) == 1100.0 and float(rpm["cawcc_mw"].max()) == 1400.0)
    # 瓶颈迁移：水源 -> 电网
    first = str(rpm.iloc[0]["limiting_constraint"])
    last = str(rpm.iloc[-1]["limiting_constraint"])
    check("提高产水量：瓶颈由水源迁移到电网",
          f"{first} → {last}", "同上 limiting_constraint",
          first == "max_source_abstraction_ratio"
          and last == "max_daily_average_grid_connection_ratio")

    # ---- 既有主结果未变 ----
    for domain, key, expect in (("ha", "cawcc_physical_daily", 1150.0),
                                ("co", "cawcc_physical_daily", 1450.0)):
        th = json.loads((R2 / domain / "capacity_threshold_corrected.json").read_text(encoding="utf-8"))
        node = th.get(key) or th.get("physical_daily") or {}
        got = node.get("maximum_safe_ai_capacity_mw")
        check(f"{domain.upper()} 既有 physical_daily CAWCC 未变 = {expect:.0f}",
              f"{got}", "r2/{domain}/capacity_threshold_corrected.json", got == expect)

    # ---- 输出 ----
    print("=" * 96)
    print("主稿 v2 新增数值核对表")
    print("=" * 96)
    print(f"{'判定':<6} {'声称值':<34} {'产物取值':<30} 来源")
    print("-" * 96)
    passed = 0
    for claim, value, source, ok in RESULTS:
        if ok:
            passed += 1
        print(f"{'PASS' if ok else 'FAIL':<6} {claim[:34]:<34} {value[:30]:<30} {source}")
    print("-" * 96)
    print(f"合计 {passed}/{len(RESULTS)} 通过")

    out = HERE / "_verify_v2_numbers.json"
    out.write_text(json.dumps(
        {"passed": passed, "total": len(RESULTS),
         "rows": [{"claim": c, "value": v, "source": s, "ok": o} for c, v, s, o in RESULTS]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out}")
    sys.exit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
