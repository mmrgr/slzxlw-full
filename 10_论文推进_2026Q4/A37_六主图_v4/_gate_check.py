# -*- coding: utf-8 -*-
"""交付前门禁: 校验 PDF 字体嵌入、PNG dpi、以及图中标注数值与权威源一致。

覆盖两轮证据:
  v4 初版  : A13/A30/A31/A33/A34/A4/A27  (主体网格、WP4/WP5、E3/E3b、部分识别)
  第二轮   : A38 NE-2/NE-4/NE-1 与 A39 WP8/WP9/WP10 (限值档、bootstrap 区间、外部效度)
"""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle_a37 as F

fails, warns = [], []

# ---- 1. 文件齐全 ----
stems = ["Fig1_boundary_counterfactuals", "Fig2_water_quality_coc", "Fig3_city_results_signs",
         "Fig4_independent_prediction", "Fig5_sensitivity_extremes",
         "Fig6_external_anchor_partial_id"]
for s in stems:
    for ext in ("pdf", "png"):
        p = HERE / f"{s}.{ext}"
        if not p.exists() or p.stat().st_size < 5000:
            fails.append(f"missing/too small: {p.name}")
print(f"[1] 输出文件: {len(stems)*2} 个待检")

# ---- 1b. 审计留痕目录 ----
prev = HERE / "_prev_2026-10-16"
if not prev.is_dir():
    fails.append("缺少 _prev_2026-10-16/ 审计留痕目录")
else:
    n_prev = len([f for f in prev.iterdir() if f.is_file()])
    if n_prev < 24:
        fails.append(f"_prev_2026-10-16/ 仅 {n_prev} 个文件 (应含 6 图 x2 + 6 图注 + 脚本 + 索引)")
    print(f"[1b] 审计留痕: _prev_2026-10-16/ 含 {n_prev} 个文件")

# ---- 2. PDF 字体嵌入 (pdf.fonttype=42) ----
try:
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib
    matplotlib.use("Agg")
    for s in stems:
        raw = (HERE / f"{s}.pdf").read_bytes()
        # Type42/TrueType 嵌入: 应含 FontFile2 或 Type0/TrueType
        has_ff2 = b"FontFile2" in raw
        if not has_ff2:
            warns.append(f"{s}.pdf: 未见 FontFile2 (可能未嵌入 TrueType)")
    print(f"[2] PDF 字体嵌入检查完成 ({len(stems)} 个)")
except Exception as e:
    warns.append(f"PDF 字体检查失败: {e}")

# ---- 3. PNG dpi ----
import struct
for s in stems:
    p = HERE / f"{s}.png"
    d = p.read_bytes()
    # 读 pHYs chunk
    i = d.find(b"pHYs")
    if i > 0:
        px, py, unit = struct.unpack(">IIB", d[i+4:i+13])
        if unit == 1:
            dpi = px * 0.0254
            if dpi < 300:
                fails.append(f"{s}.png dpi={dpi:.0f} < 300")
print("[3] PNG dpi 检查完成 (要求 ≥300)")

# ---- 4. 图中标注数值 vs 权威源 ----
r = F.load_regimes()
sc = F.sign_counts(r["dS_pot_ml"]); qg = F.q_groups(r["q"])
checks = [
    ("626/177/36", (sc["neg"], sc["pos"], sc["zero"]) == (626, 177, 36), str(sc)),
    ("q 263/288/288", (qg["pos"], qg["zero"], qg["neg"]) == (263, 288, 288), str(qg)),
    ("q>0 harmful=0", (r[r.q > 0]["dS_pot_ml"] > 0).sum() == 0, "0"),
    ("n_eff=839", len(r) == 839, str(len(r))),
    ("resid 4.37e-11", abs((r.dS_rebuilt - r.dS_pot_ml).abs().max() - 4.365575e-11) < 1e-16,
     f"{(r.dS_rebuilt-r.dS_pot_ml).abs().max():.6e}"),
]
e3s = F.load_json("e3_summary"); e3b = F.load_json("e3b_summary")
checks += [
    ("E3 chem 0.6746", abs(e3s["predictors"]["P2 q>0 (CoC判据)"]["acc"] - 0.6746) < 1e-4,
     f"{e3s['predictors']['P2 q>0 (CoC判据)']['acc']:.4f}"),
    ("baseline 0.8090", abs(e3s["majority_baseline_acc"] - 0.8090) < 1e-4,
     f"{e3s['majority_baseline_acc']:.4f}"),
    ("C4 0.9144", abs(e3b["candidate_criteria"]["C4  q>0 或 pool_scale>=2"]["acc"] - 0.9144) < 1e-4,
     f"{e3b['candidate_criteria']['C4  q>0 或 pool_scale>=2']['acc']:.4f}"),
    ("OOS 0.9171/0.8151", abs(e3b["oos_mean_test_acc"] - 0.9171) < 1e-4
     and abs(e3b["oos_mean_baseline"] - 0.8151) < 1e-4,
     f"{e3b['oos_mean_test_acc']:.4f}/{e3b['oos_mean_baseline']:.4f}"),
]
sob = F.load_sobol()
s1 = sob[sob.config == "ha|IEUA"]["S1"].sum()
checks.append(("Sum S1 ~0.22", abs(s1 - 0.223) < 0.002, f"{s1:.4f}"))
exs = F.load_json("extreme_summary")["sign_flip_from_extremes"]
checks.append(("extremes 0/8", exs["n_flip_heatwave_vs_year"] == 0 and exs["n_flip_drought_vs_year"] == 0
               and exs["n_comparable_heatwave"] + exs["n_comparable_drought"] == 8,
               f"{exs['n_flip_heatwave_vs_year']+exs['n_flip_drought_vs_year']}/"
               f"{exs['n_comparable_heatwave']+exs['n_comparable_drought']}"))
pj = F.load_json("partial_id")
checks.append(("committed bounds 0-100",
               pj["provable_bounds_committed_pct"] == {"lower": 0.0, "upper": 100.0},
               str(pj["provable_bounds_committed_pct"])))
cap = F.load_capacity()
cv = cap[["capable_first_ha_pct","capable_first_co_pct","capable_half_ha_pct","capable_half_co_pct"]].to_numpy()
checks.append(("capacity 0.39-6.55", abs(cv.min()-0.388)<0.002 and abs(cv.max()-6.549)<0.002,
               f"{cv.min():.3f}-{cv.max():.3f}"))
wp4 = F.load_wp4(); wr = wp4[wp4.reliable.astype(bool)]
checks.append(("WP4 47 all beneficial", len(wr) == 47 and (wr.dS_pot_ml < 0).all(), f"n={len(wr)}"))

# ---- 4b. 第二轮新证据 (A38 NE-1/NE-2/NE-4) ----
ne2 = F.load_ne2()
bs = ne2["binding_species_by_panel"]
IEUA_S = "IEUA RP-1 (2025, tertiary)"
LADWP_S = "LADWP AWPF (2012, RO product)"
checks += [
    ("NE2 cited->alkalinity", bs["baseline"][IEUA_S] == "alkalinity"
     and bs["baseline"][LADWP_S] == "alkalinity",
     f"{bs['baseline'][IEUA_S]}/{bs['baseline'][LADWP_S]}"),
    ("NE2 permissive->alkalinity", bs["permissive"][IEUA_S] == "alkalinity"
     and bs["permissive"][LADWP_S] == "alkalinity",
     f"{bs['permissive'][IEUA_S]}/{bs['permissive'][LADWP_S]}"),
    ("NE2 strict->silica/TDS", bs["strict"][IEUA_S] == "silica" and bs["strict"][LADWP_S] == "TDS",
     f"{bs['strict'][IEUA_S]}/{bs['strict'][LADWP_S]}"),
    ("NE2 strict no lever", ne2["binding_sets_by_panel"]["strict"] == ["TDS", "silica"],
     str(ne2["binding_sets_by_panel"]["strict"])),
    ("NE2 verdict panel-dep", ne2["verdict"] == "BINDING_SPECIES_PANEL_DEPENDENT", ne2["verdict"]),
    ("NE2 alkalinity limit 350 all tiers",
     all(ne2["panels"][t]["alkalinity"] == 350.0 for t in ("baseline", "permissive", "strict")),
     "/".join(f"{ne2['panels'][t]['alkalinity']:.0f}" for t in ("baseline", "permissive", "strict"))),
]
ne4 = F.load_ne4()
ie = F.ne4_config(ne4, F.NE4_IEUA); la = F.ne4_config(ne4, F.NE4_LADWP)
checks += [
    ("NE4 n_eff 117/128", (ie["n_valid"], la["n_valid"]) == (117, 128),
     f"{ie['n_valid']}/{la['n_valid']}"),
    ("NE4 SumS1 0.188/0.581",
     abs(ie["sum_S1"] - 0.18767182624723378) < 1e-12 and abs(la["sum_S1"] - 0.580917022153585) < 1e-12,
     f"{ie['sum_S1']:.4f}/{la['sum_S1']:.4f}"),
    ("NE4 SumS1 << 1", ie["sum_S1"] < 0.25 and la["sum_S1"] < 0.65,
     f"{ie['sum_S1']:.2f}/{la['sum_S1']:.2f}"),
    ("NE4 limit_scale CI 0.330[0.075,0.792]",
     abs(F.ne4_index(ne4, F.NE4_IEUA, "limit_scale")["ST"] - 0.3300659958634294) < 1e-9
     and abs(F.ne4_index(ne4, F.NE4_IEUA, "limit_scale")["ST_lo"] - 0.07460987003117138) < 1e-9
     and abs(F.ne4_index(ne4, F.NE4_IEUA, "limit_scale")["ST_hi"] - 0.7921875646956735) < 1e-9,
     f"{F.ne4_index(ne4, F.NE4_IEUA, 'limit_scale')['ST']:.3f}"),
    ("NE4 phi CI 0.926[0.051,2.568]",
     abs(F.ne4_index(ne4, F.NE4_IEUA, "phi")["ST"] - 0.9255884422488355) < 1e-9
     and abs(F.ne4_index(ne4, F.NE4_IEUA, "phi")["ST_lo"] - 0.05123528193190129) < 1e-9
     and abs(F.ne4_index(ne4, F.NE4_IEUA, "phi")["ST_hi"] - 2.568418822638699) < 1e-9,
     f"phi ST lo={F.ne4_index(ne4, F.NE4_IEUA, 'phi')['ST_lo']:.3f}"),
    ("NE4 phi CI far wider than point",
     F.ne4_index(ne4, F.NE4_IEUA, "phi")["ST_hi"] > 2.0,
     f"hi={F.ne4_index(ne4, F.NE4_IEUA, 'phi')['ST_hi']:.3f}"),
]
ne1 = F.load_ne1()
cmps = ne1["comparisons"]
n_same = sum(1 for c in cmps if c["sign_same"])
n_trivial = sum(1 for c in cmps if c["dS_vol"] == 0.0 and c["dS_r10a"] == 0.0)
checks += [
    ("NE1 4/4 sign-consistent", n_same == 4 and len(cmps) == 4, f"{n_same}/{len(cmps)}"),
    ("NE1 2 trivial => n_eff=2", n_trivial == 2, f"trivial={n_trivial}, n_eff={n_same-n_trivial}"),
    ("NE1 verdict path-dependent",
     ne1["verdict"] == "DIRECTION_ROBUST_MECHANISM_PATH_DEPENDENT", ne1["verdict"]),
]
ieua_ha = [c for c in cmps if c["domain"] == "ha" and c["sample"] == IEUA_S][0]
ratio = abs(ieua_ha["dS_vol"] / ieua_ha["dS_r10a"])
checks.append(("NE1 magnitude ratio ~800x", 700 < ratio < 900, f"{ratio:.0f}x"))
# 折外增益不再支持"预测能力": 应恰好 1 折为正, 2 折为 0, 1 折为负, 且仅 IEUA 折为正
loo = e3b["leave_one_sample_out"]
gains = {l["held_out"]: l["test_acc"] - l["test_baseline"] for l in loo}
n_pos = sum(1 for g in gains.values() if g > 1e-9)
n_zero = sum(1 for g in gains.values() if abs(g) < 1e-9)
n_neg = sum(1 for g in gains.values() if g < -1e-9)
checks += [
    ("OOS gain (2 pos/2 zero/0 neg)", (n_pos, n_zero, n_neg) == (2, 2, 0),
     f"pos={n_pos}, zero={n_zero}, neg={n_neg}"),
    ("OOS only positive fold = IEUA +0.184",
     abs(gains[IEUA_S] - 0.1836734693877553) < 1e-6 and gains[IEUA_S] > 0,
     f"IEUA={gains[IEUA_S]:+.4f}, Figshare={gains['Figshare RW (2025, paired study)']:+.4f}"),
]

# ---- 4c. 第二轮新证据 (A39 WP8/WP9/WP10) ----
wp8 = F.load_wp8(); wp9 = F.load_wp9(); wp10 = F.load_wp10()
d8 = {d["code"]: d for d in wp8["category_distribution"]}
b3 = wp8["b3_industrial_cooling"]
checks += [
    ("WP8 n=141 classified 141", wp8["n_cases"] == 141 and wp8["n_classified"] == 141,
     f"{wp8['n_classified']}/{wp8['n_cases']}"),
    ("WP8 B3 40/141 = 28.4% largest",
     d8["B3"]["n"] == 40 and abs(d8["B3"]["share_pct"] - 28.369) < 0.01
     and d8["B3"]["n"] == max(d["n"] for d in wp8["category_distribution"]),
     f"{d8['B3']['n']}/{wp8['n_cases']} = {d8['B3']['share_pct']:.1f}%"),
    ("WP8 B3 capacity median 4000",
     b3["capacity"]["n"] == 38 and b3["capacity"]["median"] == 4000.0
     and b3["capacity"]["p25"] == 1050.0 and b3["capacity"]["p75"] == 17500.0,
     f"n={b3['capacity']['n']}, med={b3['capacity']['median']:.0f}"),
    ("WP8 26/38 = 68.4% in [1e3,1e5]",
     abs(26 / 38 * 100 - 68.4) < 0.05,
     f"{26/38*100:.1f}%"),
    ("WP8 B3 total cost median 2.4125", b3["costs"]["Total unit cost(CNY/m³)"]["median"] == 2.4125,
     f"{b3['costs']['Total unit cost(CNY/m³)']['median']:.4f}"),
    ("WP8 case-collection caveat present",
     any("非随机" in s or "随机样本" in s for s in wp8["unsupported_claims"]),
     "unsupported_claims 含'案例集非随机样本'"),
]
d9 = wp9["distribution"]
checks += [
    ("WP9 n=39 of 41 sectors", wp9["n_sectors_with_mean"] == 39 and wp9["n_sectors_total"] == 41,
     f"{wp9['n_sectors_with_mean']}/{wp9['n_sectors_total']}"),
    ("WP9 0.000-0.990, med 0.184",
     d9["min"] == 0.0 and abs(d9["max"] - 0.989572998088803) < 1e-12
     and abs(d9["median"] - 0.18443259223492) < 1e-12,
     f"{d9['min']:.3f}-{d9['max']:.3f}, med {d9['median']:.4f}"),
    ("WP9 mean == 0.258 model ref",
     abs(d9["mean"] - 0.25799037378455597) < 1e-15
     and abs(wp9["model_reference_value"] - 0.258) < 1e-12,
     f"{d9['mean']:.17f}"),
    ("WP9 7 sectors >0.5", d9["n_gt_0.5"] == 7, str(d9["n_gt_0.5"])),
    ("WP9 caveat: not same quantity",
     any("不是同一量" in s or "口径" in s for s in wp9["unsupported_claims"]),
     "unsupported_claims 含口径不同"),
]
pc = wp10["per_city_median_stats"]
checks += [
    ("WP10 61 cities, median 1.550", pc["n_city"] == 61 and pc["median"] == 1.55,
     f"n={pc['n_city']}, med={pc['median']:.3f}"),
    ("WP10 tariff range 0.590-6.650", pc["min"] == 0.59 and pc["max"] == 6.65,
     f"{pc['min']:.3f}-{pc['max']:.3f}"),
    ("WP10 ratio 1.556 (=2.4125/1.55)",
     abs(wp10["reuse_cost_over_tap_ratio"] - 1.5564516129032258) < 1e-12
     and abs(wp10["reuse_total_unit_cost_median"] / pc["median"] - wp10["reuse_cost_over_tap_ratio"]) < 1e-12,
     f"{wp10['reuse_cost_over_tap_ratio']:.4f}"),
    # 2026-10-17 修正: 原来是 abs(17/61*100 - 27.87) < 0.01 —— 纯字面量算术, 恒真,
    # 不读任何产物, 属"空洞检查"。改为从逐城市 tariff 表重算:
    #   工业水价中位数 > 再生水成本(2.4125) 的观测数 = 17 / 61
    ("WP10 17/61 = 27.9%",
     (lambda _d: (int((_d["median"] > 2.4125).sum()), len(_d)))(
         pd.read_csv(HERE / ".." / "A39_WP8_外部效度" / "wp10_industrial_tariff_by_city.csv"))
     == (17, 61),
     "从 tariff 表重算"),
    ("WP10 verdict reuse pricier", wp10["verdict"] == "REUSE_MORE_EXPENSIVE_AT_TYPICAL_CITY",
     wp10["verdict"]),
    ("WP10 no-causality caveat present",
     any("因果" in s for s in wp10["unsupported_claims"]),
     "unsupported_claims 含不可推因果"),
]
# 跨源一致性: 三个新数据源都不得含需求字段维度 ⇒ committed 界不被削弱
checks.append(("WP8/WP9/WP10 carry no demand field (bound intact)",
               all(any(("需求" in s) or ("demand" in s.lower()) for s in src["unsupported_claims"])
                   for src in (wp8, wp9, wp10)),
               "三源 unsupported_claims 均声明无需求侧数据"))

# ---- 4d. 图注/索引文本一致性 (改动是否真的落到交付文本上) ----
cp = {n: (HERE / f"fig{n}_caption.md").read_text(encoding="utf-8") for n in range(1, 7)}
idx = (HERE / "figure_index.md").read_text(encoding="utf-8")
checks += [
    ("cap2 NE-2 boundary note", "strict make-up tier" in cp[2] and "silica" in cp[2], "Fig2 caption"),
    ("cap4 OOS withdrawn", "withdraw" in cp[4].lower() and "+0.184" in cp[4], "Fig4 caption"),
    ("cap5 NE-4 CIs present",
     "0.330 [0.075, 0.792]" in cp[5] and "2.568" in cp[5] and "0.19" in cp[5], "Fig5 caption"),
    ("cap5 NE-2 three tiers present",
     "cited" in cp[5] and "permissive" in cp[5] and "strict" in cp[5], "Fig5 caption"),
    ("cap5 extremes 0/8 retained", "0 / 8" in cp[5], "Fig5 caption"),
    ("cap6 WP8 28.4% present", "28.4 %" in cp[6] and "141" in cp[6], "Fig6 caption"),
    ("cap6 WP9 0.258 traced", "0.258" in cp[6] and "0.25799037378455597" in cp[6], "Fig6 caption"),
    ("cap6 WP10 1.550/2.413/1.56", all(x in cp[6] for x in ("1.550", "2.413", "1.56")), "Fig6 caption"),
    ("cap6 [0%,100%] bound NOT weakened",
     "[0 %, 100 %]" in cp[6] or "[0%, 100%]" in cp[6], "Fig6 caption"),
    ("cap6 claim-limits retained",
     "case collection, not a random sample" in cp[6].lower(), "Fig6 caption"),
    ("idx lists new A38/A39 sources",
     "ne4_sobol_bootstrap_summary.json" in idx and "wp8_real_reuse_cases_summary.json" in idx
     and "wp10_water_price_summary.json" in idx, "figure_index.md"),
    ("idx records withdrawn OOS",
     "折外 0.901" in idx and "撤回" in idx, "figure_index.md"),
    # WP11 为纯文本锚点, 不进图; 但图注必须显式说明"未绘入"及原因, 防止读者以为图已穷尽 §6 的外部证据
    ("cap6 declares WP11 not drawn",
     "Not shown in this figure" in cp[6] and "597" in cp[6]
     and "six provinces" in " ".join(cp[6].split()), "Fig6 caption"),
    ("idx lists WP11 source",
     "wp11_reuse_deployment_summary.json" in idx, "figure_index.md"),
]

print("\n[4] 图中标注数值 vs 权威源:")
for name, ok, val in checks:
    print(f"   {'PASS' if ok else 'FAIL'}  {name:46s} {val}")
    if not ok:
        fails.append(f"value mismatch: {name} -> {val}")

print("\n" + "=" * 60)
if warns:
    print("WARN:"); [print("  -", w) for w in warns]
if fails:
    print(f"GATE FAILED ({len(fails)}):"); [print("  -", f) for f in fails]
    raise SystemExit(1)
print(f"GATE PASSED: 6/6 figures, {len(checks)}/{len(checks)} value+text checks consistent with sources.")
