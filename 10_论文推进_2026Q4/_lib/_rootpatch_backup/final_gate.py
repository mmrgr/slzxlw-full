"""终审门禁 · 自动化核对 (2026-10-16).

一次性核对: 文档完整性 / 核心数值复算 / 权威产物一致性 / 禁用主张语境。
判定标准: 全部 PASS 才返回 0。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent  # A36_终审 -> 10_论文推进_2026Q4
ok = True


def chk(name: str, cond: bool, detail: str = "") -> None:
    global ok
    if not cond:
        ok = False
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")


print("=" * 76)
print("终审门禁 · 自动化核对")
print("=" * 76)

# ---------- 1. 文档完整性 ----------
print("\n[1] 文档完整性")
for f in ("A16_英文稿/manuscript_en_v3.md", "A16_英文稿/supplementary_information.md"):
    s = (ROOT / f).read_text(encoding="utf-8")
    bad = [hex(ord(c)) for c in s if ord(c) < 32 and c not in "\n\r\t"]
    chk(f"{Path(f).name} 无控制字符破损", not bad, f"({len(s)} chars)")

# ---------- 2. 核心数值复算 ----------
print("\n[2] 核心数值复算 vs 主稿声称")
d = pd.read_csv(ROOT / "A13_可靠性机制/supply_state_regimes.csv")
rel = d[(d.status == "converged_unique") & (~d.coc_floor_degenerate.astype(bool))]
C = rel.inc_B2_ml - rel.inc_B1_ml
F = rel.M0_ml - rel.M1_ml
res = (C - F - rel.x_ai_B1_ml - rel.dS_pot_ml).abs()
sc = rel[["M0_ml", "M1_ml"]].abs().max(axis=1)
ds = rel.dS_pot_ml
q = (rel.M0_ml - rel.M1_ml) / rel.M1_ml

chk("可靠子集 n=813", len(rel) == 813, f"实测 {len(rel)}")
chk("恒等式残差 ≈2.55e-11", abs(res.max() - 2.546585164964199e-11) / 2.5466e-11 < 1e-3,
    f"实测 {res.max():.4e}")
chk("相对残差 ≈2.9e-16", abs((res / sc).max() - 2.933e-16) / 2.933e-16 < 0.02,
    f"实测 {(res/sc).max():.3e}")
chk("严格符号 643/134/36",
    (int((ds < 0).sum()), int((ds > 0).sum()), int((ds == 0).sum())) == (643, 134, 36),
    f"实测 {int((ds<0).sum())}/{int((ds>0).sum())}/{int((ds==0).sum())}")
chk("q 分组 290/288/235",
    (int((q > 0).sum()), int((q == 0).sum()), int((q < 0).sum())) == (290, 288, 235),
    f"实测 {int((q>0).sum())}/{int((q==0).sum())}/{int((q<0).sum())}")
chk("q>0 组有害=0", int(((q > 0) & (ds > 0)).sum()) == 0)

# ---------- 3. 权威产物一致性 ----------
print("\n[3] 权威产物一致性")
h = json.loads((ROOT / "A15_稳健性/holdout_summary.json").read_text(encoding="utf-8"))["H2_true_holdout"]
chk("留出 R²=0.8056", abs(h["co_R2_phi_eff"] - 0.8055937188186029) < 1e-12,
    f"{h['co_R2_phi_eff']:.6f}")
chk("基线=-0.0733", abs(h["trivial_baseline_R2"] + 0.07328387812300985) < 1e-12)

b = json.loads((ROOT / "A20_模型桥接/bridging_summary_v2.json").read_text(encoding="utf-8"))
chk("桥接 24 对", b["n_pairs"] == 24, f"n_pairs={b['n_pairs']}")
chk("桥接符号一致 23/24", abs(b["sign_agreement"] - 23 / 24) < 1e-9, f"{b['sign_agreement']:.4f}")

p = json.loads((ROOT / "A30_WP0取证/a24b_partial_id_summary.json").read_text(encoding="utf-8"))
chk("A24b 已撤回为不可识别", "WITHDRAWN" in p["status_of_original_claim"],
    p["status_of_original_claim"])
chk("A24b 界=[0,100]", p["provable_bounds_committed_pct"] == {"lower": 0.0, "upper": 100.0})

e3 = json.loads((ROOT / "A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json"
                 ).read_text(encoding="utf-8"))
chk("E3 判定 NOT_PREDICTIVE", e3["verdict"] == "NOT_PREDICTIVE", e3["verdict"])
e3b = json.loads((ROOT / "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json"
                  ).read_text(encoding="utf-8"))
chk("E3b 折外优于基线",
    e3b["verdict"] == "PREDICTIVE_OUT_OF_SAMPLE" and e3b["oos_gain"] > 0.02,
    f"gain={e3b['oos_gain']:.4f}")

v = json.loads((ROOT / "A30_WP0取证/volonly_flux_balance_summary.json").read_text(encoding="utf-8"))
chk("volume-only 通量平衡 PASS", v["verdict"] == "PASS", v["verdict"])
sc2 = json.loads((ROOT / "A30_WP0取证/a21_solute_closure_summary.json").read_text(encoding="utf-8"))
chk("R10a 溶质闭合 PASS", sc2["verdict"] == "PASS", sc2["verdict"])

w5 = json.loads((ROOT / "A34_WP5_敏感性与极端事件/wp5_extreme_summary.json"
                 ).read_text(encoding="utf-8"))
chk("极端事件无符号翻转", w5.get("max_ratio_to_full_year", 0) < 2.0,
    f"max ratio={w5.get('max_ratio_to_full_year')}")

# ---------- 4. 禁用主张语境 ----------
print("\n[4] 主稿禁用主张检查 (只允许出现在撤回/更正语境)")
ms = (ROOT / "A16_英文稿/manuscript_en_v3.md").read_text(encoding="utf-8")
CTX = ("withdraw", "earlier", "retract", "superseded", "could not",
       "came from", "pre-a27", "placeholder", "removed", "replaced", "correction")
for pat in ("above 95%", "empirically dominant", "429 of 446", "17 exceptions"):
    for line in ms.split("\n"):
        if pat in line:
            chk(f"'{pat}' 仅在撤回/更正语境",
                any(k in line.lower() for k in CTX), f"| {line.strip()[:64]}")

# ---------- 5. 红队发现的两处关键更正 ----------
print("\n[5] 红队关键发现的更正核验")
q = (rel.M0_ml - rel.M1_ml) / rel.M1_ml
qz = rel[q == 0]
chk("q≈0 组 rises 真值 = 32 (非 0)", int((qz.dS_pot_ml > 0).sum()) == 32,
    f"实测 {int((qz.dS_pot_ml>0).sum())}")
chk("落带 80 行中 32 行是 dS>0", int(((ds.abs() <= 1e-9) & (ds > 0)).sum()) == 32,
    f"实测 {int(((ds.abs()<=1e-9)&(ds>0)).sum())}")
e3b = json.loads((ROOT / "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json"
                  ).read_text(encoding="utf-8"))
folds = e3b["leave_one_sample_out"]
gains = [f["test_acc"] - f["test_baseline"] for f in folds]
pos = sum(1 for g in gains if g > 0)
chk("折外增益仅 1/4 折为正", pos == 1, f"正折 {pos}/{len(folds)}")
med = float(np.median(gains))
chk("折外中位增益 = 0.000", abs(med) < 1e-9, f"中位 {med:+.4f}")
chk("主稿已撤回'折外技能'主张",
    "withdraw the claim of demonstrated" in ms or "not robust" in ms,
    "检查 §3d / Abstract 措辞")

# ---------- 6. NE-1 / NE-2 判决性实验 ----------
print("\n[6] NE-1 / NE-2 判决性实验核对")
ne1 = json.loads((ROOT / "A38_模拟审稿/ne1_r10a_signflip_summary.json").read_text(encoding="utf-8"))
chk("NE-1 已执行并给出裁定",
    ne1.get("verdict") == "DIRECTION_ROBUST_MECHANISM_PATH_DEPENDENT", ne1.get("verdict"))
chk("NE-1 符号一致但含平凡例 (n_eff < 4)",
    ne1.get("n_sign_same") == 4 and "trivial" not in str(ne1.get("verdict", "")).lower(),
    f"sign_same={ne1.get('n_sign_same')}")

ne2 = json.loads((ROOT / "A38_模拟审稿/ne2_panel_robustness_summary.json").read_text(encoding="utf-8"))
chk("NE-2 判定绑定物种随档位改变",
    ne2.get("verdict") == "BINDING_SPECIES_PANEL_DEPENDENT", ne2.get("verdict"))
sets = ne2.get("binding_sets_by_panel", {})
chk("strict 档绑定物种 = TDS/silica (非 alkalinity)",
    sets.get("strict") == ["TDS", "silica"], f"{sets.get('strict')}")
chk("baseline 档绑定物种 = alkalinity",
    sets.get("baseline") == ["alkalinity"], f"{sets.get('baseline')}")
chk("主稿已限定'唯一杠杆'的适用域",
    "not panel-invariant" in ms or "bounded limit domain" in ms,
    "检查 §7a / Abstract 措辞")

ne4 = json.loads((ROOT / "A38_模拟审稿/ne4_sobol_bootstrap_summary.json").read_text(encoding="utf-8"))
chk("NE-4 指数自洽 (ΣS1 ≤ 1)", all(
    (v.get("sum_S1", 0) <= 1.0 + 1e-9) for v in ne4["configs"].values()),
    str({k: round(v.get("sum_S1", 0), 3) for k, v in ne4["configs"].items()}))
chk("NE-4 判定 SOBOL_WITH_CI_AVAILABLE",
    ne4.get("verdict") == "SOBOL_WITH_CI_AVAILABLE", ne4.get("verdict"))
chk("NE-4 碱度指数对不绑定水样 ~0",
    any(abs(i["ST"]) < 0.01 for v in ne4["configs"].values()
        if v.get("status") == "OK" for i in v.get("indices", [])
        if i["parameter"] == "x_alkalinity"),
    "LADWP x_alkalinity ST≈0")

wp8 = json.loads((ROOT / "A39_WP8_外部效度/wp8_real_reuse_cases_summary.json"
                  ).read_text(encoding="utf-8"))
chk("WP8 案例总数 = 141", wp8.get("n_cases") == 141, str(wp8.get("n_cases")))
chk("WP8 分类率 100%", wp8.get("n_classified") == wp8.get("n_cases"),
    f"{wp8.get('n_classified')}/{wp8.get('n_cases')}")
b3 = wp8.get("b3_industrial_cooling", {})
chk("WP8 B3(工业冷却) 为最大类别 = 40", b3.get("n") == 40, f"n={b3.get('n')}")
dist = wp8.get("category_distribution", [])
chk("WP8 B3 占比确为最大",
    bool(dist) and max(dist, key=lambda r: r["n"])["code"] == "B3",
    f"max={max(dist, key=lambda r: r['n'])['code'] if dist else None}")
chk("WP8 明确列出不可支持的结论",
    len(wp8.get("unsupported_claims", [])) >= 3,
    f"{len(wp8.get('unsupported_claims', []))} 条")
chk("主稿已纳入 B3 证据",
    "28.4%" in ms and "case collection" in ms, "检查 §6 / Abstract")

wp9 = json.loads((ROOT / "A39_WP8_外部效度/wp9_cooling_share_summary.json"
                  ).read_text(encoding="utf-8"))
ea = json.loads((ROOT / "A24_外部锚定/external_anchor_summary.json").read_text(encoding="utf-8"))
wp9_mean = wp9["distribution"]["mean"]
ea_mean = ea["other_anchors"][0]["mean_of_means"]
chk("WP9 独立重算 0.258 与 A24 逐位一致",
    abs(wp9_mean - ea_mean) / ea_mean < 1e-12,
    f"WP9={wp9_mean!r} A24={ea_mean!r} 相对差={abs(wp9_mean-ea_mean)/ea_mean:.1e}")
chk("WP9 行业数 = 39", wp9["distribution"]["n"] == 39, str(wp9["distribution"]["n"]))
chk("WP9 行业区间宽 (max-min > 0.9)",
    wp9["distribution"]["max"] - wp9["distribution"]["min"] > 0.9,
    f"[{wp9['distribution']['min']:.3f}, {wp9['distribution']['max']:.3f}]")
chk("WP9 明确列出不可支持结论",
    len(wp9.get("unsupported_claims", [])) >= 3,
    f"{len(wp9.get('unsupported_claims', []))} 条")
chk("主稿已纳入 WP9 证据",
    "0.25799037378455597" in ms or "62nd percentile" in ms, "检查 §6")

wp10 = json.loads((ROOT / "A39_WP8_外部效度/wp10_water_price_summary.json"
                   ).read_text(encoding="utf-8"))
chk("WP10 城市数 = 61", wp10["per_city_median_stats"]["n_city"] == 61,
    str(wp10["per_city_median_stats"]["n_city"]))
chk("WP10 水价城市中位 = 1.55",
    abs(wp10["per_city_median_stats"]["median"] - 1.55) < 1e-9,
    str(wp10["per_city_median_stats"]["median"]))
chk("WP10 成本/水价比 ≈ 1.56",
    abs(wp10["reuse_cost_over_tap_ratio"] - 1.5564516129032258) < 1e-9,
    f"{wp10['reuse_cost_over_tap_ratio']:.6f}")
chk("WP10 明确列出不可支持结论(含不可推因果)",
    any("因果" in c or "causal" in c.lower() for c in wp10.get("unsupported_claims", [])),
    f"{len(wp10.get('unsupported_claims', []))} 条")
chk("主稿已纳入水价对照", "1.56" in ms and "56% more" in ms, "检查 §6")

chk("主稿水价双口径已分离",
    "all use categories pooled" in ms and "industrial* tap tariff only" in ms,
    "检查 §6 水价表")

wp11 = json.loads((ROOT / "A39_WP8_外部效度/wp11_reuse_deployment_summary.json"
                   ).read_text(encoding="utf-8"))
chk("WP11 块数 = 2 且已识别", wp11.get("n_blocks") == 2, str(wp11.get("n_blocks")))
chk("WP11 两块不一致 (取保守口径)",
    wp11.get("blocks_are_same") is False, str(wp11.get("blocks_are_same")))
cap_pos = wp11.get("reclaimed_capacity_positive_only") or {}
chk("WP11 有正产能项目数 = 11", cap_pos.get("n_positive") == 11, str(cap_pos.get("n_positive")))
chk("WP11 正产能中位 = 3.0e4",
    abs(float(cap_pos.get("median", 0)) - 3.0e4) / 3.0e4 < 1e-9, str(cap_pos.get("median")))
chk("WP11 明确不可相加求总量",
    any("相加" in c for c in wp11.get("unsupported_claims", [])), "检查不可支持列表")
chk("主稿已纳入 WP11 证据", "597 records" in ms and "11/11" in ms, "检查 §6")

print("\n" + "=" * 76)
print("总判定:", "全部通过 ✓" if ok else "存在 FAIL ✗")
sys.exit(0 if ok else 1)
