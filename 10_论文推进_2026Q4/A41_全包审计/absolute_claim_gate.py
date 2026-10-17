"""门禁 15: 绝对声称必须可被产物验证 (2026-10-17).

【为什么需要】
论文里有若干**绝对/零例外声明**, 例如:
  · "q>0 是城市受益的充分条件: 263 of 263, no exception"
  · "三账本互不相等 (0/68 coincidences)"
  · "dS>0 且 F>0 的矛盾: 0 例"
这类声明**只要有一个反例就被推翻**, 是审稿人最容易攻击的点。
本门禁从产物**实时重算**这些断言; 算不出来就 FAIL。

【与 truth_gate 的区别】
truth_gate 校验"数字本身对不对"(839/626/177…);
本门禁校验"**逻辑断言**对不对"(充分条件是否真的零例外)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
import numpy as np                                              # noqa: E402

MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
import pandas as pd                                             # noqa: E402


def load_rel():
    d = pd.read_csv(ROOT / "A13_可靠性机制/supply_state_regimes.csv")
    return d[(d.status == "converged_unique") &
             (~d.coc_floor_degenerate.astype(bool))].copy()


def main() -> int:
    rel = load_rel()
    q = (rel.M0_ml - rel.M1_ml) / rel.M1_ml
    C = rel.inc_B2_ml - rel.inc_B1_ml
    F = rel.M0_ml - rel.M1_ml
    dS = rel.dS_pot_ml

    fs = json.loads((ROOT / "A18_有限供水/finite_supply_summary.json")
                    .read_text(encoding="utf-8"))
    tad = fs.get("three_account_divergence", {})

    checks = []

    # A1. q>0 ⇒ dS<0 (受益), 零例外
    pos = q > 1e-9
    n_pos, n_viol = int(pos.sum()), int((dS[pos] > 0).sum())
    checks.append(("q>0 零例外", n_pos == 263 and n_viol == 0,
                   f"q>0={n_pos}, 反例={n_viol}"))

    # A2. 三账本互不相等 (0/68)
    n_sc = fs.get("n_scenarios")
    never_eq = tad.get("abstraction_eq_delivered_ever") is False
    checks.append(("三账本 0/68", n_sc == 68 and never_eq,
                   f"n_scenarios={n_sc}, abstraction_never_eq_delivered={never_eq}"))

    # A3. dS>0 且 F>0 的矛盾数为 0
    contra = int(((dS > 1e-6) & (F > 1e-6)).sum())
    checks.append(("dS>0∧F>0 零矛盾", contra == 0, f"矛盾={contra}"))

    # A4. 恒等式残差到机器精度 (< 1e-9 ML)
    resid = float((dS - (C - F - rel.x_ai_B1_ml)).abs().max())
    checks.append(("恒等式残差", resid < 1e-9, f"max={resid:.3e} ML"))

    # A5. 边际楔子 1.178 (abstraction/delivered)
    wedge = tad.get("marginal_abstraction_over_delivered", {})
    vals = list(wedge.values()) if isinstance(wedge, dict) else []
    ok5 = bool(vals) and all(abs(v - 1.178) < 5e-4 for v in vals)
    checks.append(("边际楔子 1.178", ok5, f"值={vals}"))

    # A6. 11/39 曲线非单调 (SI S? / 主稿 §12) —— 注意必须**按网格级别分别计算**
    #     错误示范: 对全表 groupby(sample,limit_scale) 会把 4 个层级的行拼成一条序列,
    #     产生假性非单调 (25/39)。必须限定 n_level。
    gr = pd.read_csv(ROOT / "A15_稳健性/grid_resolution_points.csv")
    finest = gr[gr.n_level == gr.n_level.max()]
    nm = tot = 0
    for _key, g in finest.groupby(["sample", "limit_scale"]):
        feas = g.sort_values("rho")["feasible"].astype(bool).to_numpy()
        tot += 1
        if feas.any():
            i0 = int(np.argmax(feas))
            i1 = len(feas) - 1 - int(np.argmax(feas[::-1]))
            if (~feas[i0:i1 + 1]).any():
                nm += 1
    checks.append(("11/39 非单调曲线", nm == 11 and tot == 39,
                   f"最细网格 n_level={int(gr.n_level.max())}: {nm}/{tot}"))

    # A7. branch-C 例外数: 391 个 branch-C 中 11 个 F<0 (2026-10-17)
    #     主稿曾写 "372 branch-C cases with 3 exceptions"(旧值), SI 曾写 "3 of 391",
    #     两处互相矛盾且都与产物不符。现统一为 391 / 11。
    # "11 exceptions" 指的是 branch-C 中 dS>0 的情形（不是 F<0）；
    # F<0 在 branch-C 中有 92 个，是另一回事。实测: dS<0=380, dS>0=11。
    nodisp = np.isclose(C, 0, atol=1e-9)
    n_nodisp = int(nodisp.sum())
    n_neg_dS = int((dS[nodisp] < -1e-9).sum())
    n_pos_dS = int((dS[nodisp] > 1e-9).sum())
    checks.append(("branch-C 380/11", n_nodisp == 391
                   and n_neg_dS == 380 and n_pos_dS == 11,
                   f"branch-C={n_nodisp}, dS<0={n_neg_dS}, dS>0={n_pos_dS}"))

    # A8. 外部锚点断言 (2026-10-17):
    #   · "141 of 141 rows agree, zero disagreements"
    #   · "586 of 597 rows leave the capacity column at zero"
    #   · "17 of 61 city–source observations above reclaimed-water cost" (31 distinct cities)
    wp8 = json.loads((ROOT / "A39_WP8_外部效度/wp8_real_reuse_cases_summary.json")
                     .read_text(encoding="utf-8"))
    checks.append(("141/141 分类一致",
                   wp8.get("n_cases") == 141 and wp8.get("n_classified") == 141
                   and wp8.get("n_unclassified") == 0,
                   f"n_cases={wp8.get('n_cases')}, unclassified={wp8.get('n_unclassified')}"))

    wp11 = json.loads((ROOT / "A39_WP8_外部效度/wp11_reuse_deployment_summary.json")
                      .read_text(encoding="utf-8"))
    rc = wp11.get("reclaimed_capacity", {})
    checks.append(("586/597 产能列为零",
                   rc.get("n") == 597 and rc.get("n_zero") == 586,
                   f"n={rc.get('n')}, n_zero={rc.get('n_zero')}"))

    tar = pd.read_csv(ROOT / "A39_WP8_外部效度/wp10_industrial_tariff_by_city.csv")
    n_above = int((tar["median"] > 2.4125).sum())
    checks.append(("17/61 水价高于成本",
                   n_above == 17 and len(tar) == 61 and tar["city"].nunique() == 31,
                   f"above={n_above}/{len(tar)}, 唯一城市={tar['city'].nunique()}"))

    # A9. 图注中的两个关键统计量 (2026-10-17)
    #   起因: fig3 图注写 "239 rows excluded"(实际 1052-839=213);
    #         fig5 图注写 "512 points"(实际 128*(2*7+2)=2048)
    #   判据: 从产物**推算**, 再与图注文本比对。
    import re as _re
    cap3 = (ROOT / "A37_六主图_v4/fig3_caption.md").read_text(encoding="utf-8")
    n_all, n_rel = 1052, 839
    ok3 = f"{n_all - n_rel}" in cap3 and "239" not in cap3
    checks.append(("fig3 排除行数=213", ok3,
                   f"应为 {n_all - n_rel}, 图注 {'含 213' if str(n_all-n_rel) in cap3 else '缺 213'}, "
                   f"{'含旧值 239' if '239' in cap3 else '无 239'}"))

    cap5 = (ROOT / "A37_六主图_v4/fig5_caption.md").read_text(encoding="utf-8")
    ne4 = json.loads((ROOT / "A38_模拟审稿/ne4_sobol_bootstrap_summary.json")
                     .read_text(encoding="utf-8"))
    n_pts = int(ne4["N_base"]) * (2 * int(ne4["d"]) + 2)
    ok5 = str(n_pts) in cap5 and "512" not in cap5.replace("5120", "")
    checks.append((f"fig5 Saltelli 点数={n_pts}", ok5,
                   f"N_base={ne4['N_base']}, d={ne4['d']} -> {n_pts}; "
                   f"图注 {'含' if str(n_pts) in cap5 else '缺'}, "
                   f"{'含旧值 512' if '512' in cap5 else '无 512'}"))

    # A10. fig3 极值区间 (2026-10-17)
    #   旧手工图注写 -64,000 / +42,000, 实际 -44,603 / +69,749 —— **两个都错**。
    #   改为随图注自动生成后已修正; 此处设门禁防止再次偏离。
    cap3 = (ROOT / "A37_六主图_v4/fig3_caption.md").read_text(encoding="utf-8")
    lo, hi = float(dS.min()), float(dS.max())
    ok_lo = f"{abs(lo):,.0f}" in cap3
    ok_hi = f"{abs(hi):,.0f}" in cap3
    checks.append(("fig3 极值区间", ok_lo and ok_hi,
                   f"实际 {lo:,.0f} / +{hi:,.0f}; 图注 下限{'含' if ok_lo else '缺'}/上限{'含' if ok_hi else '缺'}"))

    # A11. fig5 断言 (2026-10-17)
    #   · "11 of 128 points degenerate" (IEUA)
    #   · "both configurations are identified" (产物里两个 status 都是 OK;
    #     旧图注误写 LADWP 为 NOT_IDENTIFIABLE)
    #   · "n_eff = 64 of 64" 极端事件
    ne4 = json.loads((ROOT / "A38_模拟审稿/ne4_sobol_bootstrap_summary.json")
                     .read_text(encoding="utf-8"))
    ieu = ne4["configs"]["ha|IEUA RP-1 (2025, tertiary)"]
    lad = ne4["configs"]["ha|LADWP AWPF (2012, RO product)"]
    ok11 = (ieu["n_degenerate"] == 11 and ieu["n_valid_raw"] == 128
            and lad["n_degenerate"] == 0 and lad["n_valid"] == 128
            and ieu["status"] == "OK" and lad["status"] == "OK")
    checks.append(("fig5 两配置均可识别", ok11,
                   f"IEUA {ieu['status']} degen={ieu['n_degenerate']}; "
                   f"LADWP {lad['status']} degen={lad['n_degenerate']}"))

    cap5 = (ROOT / "A37_六主图_v4/fig5_caption.md").read_text(encoding="utf-8")
    ok5b = ("NOT_IDENTIFIABLE" not in cap5) and ("11 of 128" in cap5)
    checks.append(("fig5 图注无错误 NOT_IDENTIFIABLE", ok5b,
                   f"{'含 NOT_IDENTIFIABLE' if 'NOT_IDENTIFIABLE' in cap5 else '无错误声称'}, "
                   f"{'含 11 of 128' if '11 of 128' in cap5 else '缺 11 of 128'}"))

    ext = json.loads((ROOT / "A34_WP5_敏感性与极端事件/wp5_extreme_summary.json")
                     .read_text(encoding="utf-8"))
    g = ext["gates"]
    checks.append(("极端事件 64/64", g["n_all"] == 64 and g["n_eff"] == 64
                   and g["n_excluded"] == 0,
                   f"n_all={g['n_all']}, n_eff={g['n_eff']}, excluded={g['n_excluded']}"))

    # A12. fig2/fig4/fig6 图注断言 (2026-10-17 逐条核验后固化)
    import pandas as _pd
    # fig2 的五个 limit/conc 比值
    _sm = _pd.read_csv(ROOT / "A4_水化学参数域/T6_water_chemistry_samples.csv")
    _ie = _sm[_sm["source"].str.contains("IEUA", case=False, na=False)].iloc[0]
    _lim = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
            "alkalinity": 350.0, "silica": 175.0}
    _ra = {k: _lim[k] / float(_ie[k]) for k in _lim}
    ok12 = (round(_ra["alkalinity"], 3) == 2.500
            and min(_ra, key=_ra.get) == "alkalinity")
    checks.append(("fig2 碱度比值 2.500 最小", ok12,
                   f"alkalinity={_ra['alkalinity']:.3f}; 最小物种={min(_ra, key=_ra.get)}"))

    # fig4: P2=0.6746, baseline=0.809, C4=0.9144
    _e3 = json.loads((ROOT / "A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json")
                     .read_text(encoding="utf-8"))
    _e3b = json.loads((ROOT / "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json")
                      .read_text(encoding="utf-8"))
    _p2 = _e3["predictors"]["P2 q>0 (CoC判据)"]["acc"]
    _c4 = _e3b["candidate_criteria"]["C4  q>0 或 pool_scale>=2"]["acc"]
    ok13 = (abs(_p2 - 0.675) < 5e-4 and abs(_e3b["majority_baseline"] - 0.809) < 5e-4
            and abs(_c4 - 0.914) < 5e-4)
    checks.append(("fig4 0.675/0.809/0.914", ok13,
                   f"P2={_p2:.4f}, base={_e3b['majority_baseline']:.4f}, C4={_c4:.4f}"))

    # fig6: 39 of 41 sectors; 0.258 在 61-62 分位
    _wp9 = json.loads((ROOT / "A39_WP8_外部效度/wp9_cooling_share_summary.json")
                      .read_text(encoding="utf-8"))
    _sec = _pd.read_csv(ROOT / "A39_WP8_外部效度/wp9_cooling_share_by_sector.csv")
    _v = _pd.to_numeric(_sec["share_mean"], errors="coerce").dropna()
    _pct = float((_v < _wp9["model_reference_value"]).mean() * 100)
    ok14 = (_wp9["n_sectors_total"] == 41 and _wp9["n_sectors_with_mean"] == 39
            and 60.0 <= _pct <= 63.0)
    checks.append(("fig6 39/41 与 62 分位", ok14,
                   f"sectors={_wp9['n_sectors_with_mean']}/{_wp9['n_sectors_total']}, "
                   f"分位={_pct:.1f}%"))

    # A13. branch-A "恰好为零"表述 (2026-10-17)
    #   主稿原写 "0.000000 ML exactly (80/80)" —— 但严格 0.0 只有 36/80,
    #   其余 44 个是 |dS|<1e-11 的机器精度残差。应说 "to machine precision"。
    _sub1e6 = pd.read_csv(ROOT / "A13_可靠性机制/supply_state_regimes.csv")
    _sub1e6 = _sub1e6[np.isclose(_sub1e6.limit_scale, 1e6)]
    _rel1e6 = _sub1e6[(_sub1e6.status == "converged_unique") &
                      (~_sub1e6.coc_floor_degenerate.astype(bool))]
    _C1 = _rel1e6.inc_B2_ml - _rel1e6.inc_B1_ml
    _bA = _rel1e6[np.isclose(_rel1e6.x_ai_B1_ml, _C1, rtol=1e-9)]
    _n_exact = int((_bA.dS_pot_ml == 0.0).sum())   # 严格等于 0.0
    _n_mach = int((_bA.dS_pot_ml.abs() < 1e-11).sum())
    _ms = MS.read_text(encoding="utf-8")
    _ok = (_len_helper := True) and (_n_mach == len(_bA) == 80) and (_n_exact == 36)         and ("to machine precision" in _ms) and ("0.000000 ML exactly" not in _ms)
    checks.append(("branch-A 机器精度表述", _ok,
                   f"n={len(_bA)}, |dS|<1e-11 有 {_n_mach}, 严格 0 有 {_n_exact}"))

    # A14. "61 cities" 表述 (2026-10-17)
    #   产物里 n_city=61 实为"城市×源表列"观测数, 唯一城市只有 31。
    #   主稿曾写 "61 cities"; 已改为 "31 distinct cities / 61 city-source series"。
    _wp10 = json.loads((ROOT / "A39_WP8_外部效度/wp10_water_price_summary.json")
                       .read_text(encoding="utf-8"))
    _pc = _wp10["per_city_median_stats"]
    _ms2 = MS.read_text(encoding="utf-8")
    _ok14 = (_pc.get("n_distinct_cities") == 31
             and _pc.get("n_city_source_series") == 61
             and "31 distinct cities" in _ms2
             and "61 cities" not in _ms2.replace("31 distinct cities / 61 city", ""))
    checks.append(("61→31 城市口径", _ok14,
                   f"distinct={_pc.get('n_distinct_cities')}, "
                   f"series={_pc.get('n_city_source_series')}, "
                   f"主稿含'31 distinct cities'={'31 distinct cities' in _ms2}"))

    print("=" * 74)
    print("绝对声称可验证性门禁")
    print("=" * 74)
    fails = 0
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<20} {detail}")
        if not ok:
            fails += 1

    print()
    print(f"裁定: {'全部绝对声称零例外成立 ✓' if fails == 0 else f'{fails} 项不成立 ✗'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
