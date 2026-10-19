# -*- coding: utf-8 -*-
"""摘要与主稿关键数字的独立溯源核对。

摘要里的每个数字都必须能在产物中找到。这是审稿人最可能抽查的地方。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_verify_abstract_numbers.py
"""
from __future__ import annotations

import json
import re
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
V2 = HERE / "03_主稿_v2.md"

ROWS: list[tuple[str, str, str, bool]] = []


def ck(claim: str, value: str, source: str, ok: bool) -> None:
    ROWS.append((claim, value, source, bool(ok)))


def main() -> None:
    text = V2.read_text(encoding="utf-8")
    ab = re.search(r"## 摘要\n(.*?)\n---", text, flags=re.S)
    ab = ab.group(1) if ab else ""

    # ---- 摘要中出现的数字必须在正文或产物中找到 ----
    nums_in_ab = set(re.findall(r"\d+\.\d+", ab))
    print("摘要中的小数:", sorted(nums_in_ab))

    # ---- 逐个核对关键数字 ----
    # r*
    ck("摘要含 r*=0.5532", "0.5532", "解析", "0.5532" in ab)

    # 机器精度
    probe = pd.read_csv(R2 / "probe_rstar_mechanism.csv", encoding="utf-8-sig")
    err = float((probe["coc_mean"] - probe["coc_analytic"]).abs().max())
    ck("CoC 残差 8.9e-16", f"{err:.3e}", "probe_rstar_mechanism.csv", err < 1e-12)

    # 多物种 0.6842
    (L, coc, cp, cr) = (2200.0, 5.0, 35.0, 130.0)
    cl_rstar = (500.0 / coc - cp) / (cr - cp)
    ck("氯化物 r* = 0.6842", f"{cl_rstar:.4f}", "解析（L=500,Cp=35,Cr=130）",
       abs(cl_rstar - 0.6842) < 5e-4)

    # CoC r=0.9 = 3.648
    ha = pd.read_csv(R2 / "rstar_scan_ha.csv", encoding="utf-8-sig")
    coc09 = float(ha[ha["target_r"] == 0.9]["coc_mean"].iloc[0])
    ck("CoC r=0.9 = 3.648", f"{coc09:.3f}", "rstar_scan_ha.csv", abs(coc09 - 3.648) < 5e-4)
    ck("CoC 降幅 -27%", f"{100*(coc09/5.0-1):+.2f}%", "同上",
       abs(100 * (coc09 / 5.0 - 1) + 27.03) < 0.05)

    # 反噬增幅与无关性
    base = ha[ha["target_r"] == 0.0].set_index("ai_capacity_mw")["total_withdrawal_ml"]
    incs = []
    for cap in (200.0, 800.0, 1200.0, 1600.0):
        v = ha[(ha["target_r"] == 0.8) & (ha["ai_capacity_mw"] == cap)]["total_withdrawal_ml"]
        if len(v):
            incs.append(100 * (float(v.iloc[0]) / float(base.loc[cap]) - 1))
    spread = max(incs) - min(incs)
    ck("四容量点增幅 +6.47~6.48%", f"{min(incs):.2f}~{max(incs):.2f}%",
       "rstar_scan_ha.csv", 6.40 < min(incs) and max(incs) < 6.55)
    ck("极差 0.012 个百分点", f"{spread:.4f}pp", "同上", spread < 0.02)

    # E 恒定性
    dec = pd.read_csv(R2 / "rstar_backlash_decomposition.csv", encoding="utf-8-sig")
    dec = dec.drop_duplicates(subset=["domain", "capacity_mw", "target_r"])
    s = dec[(dec["domain"] == "ha") & ((dec["capacity_mw"] - 1600.0).abs() < 1e-6)] \
        .sort_values("target_r")
    e0 = float(s.iloc[0]["implied_evaporation_ml"])
    e9 = float(s.iloc[-1]["implied_evaporation_ml"])
    ck("反推 E 变化 -0.76%", f"{100*(e9/e0-1):+.2f}%", "rstar_backlash_decomposition.csv",
       abs(100 * (e9 / e0 - 1) + 0.76) < 0.05)

    # 反噬精确为零 + 再生水用量 16790
    below = dec[dec["target_r"] <= 0.5]["backlash_ml"].abs().max()
    ck("反噬 r<=0.5 精确为零", f"{below:.2e}", "同上", below < 1e-9)
    ha1200 = pd.read_csv(R2 / "rstar_scan_ha.csv", encoding="utf-8-sig")
    recl05 = float(ha1200[(ha1200["target_r"] == 0.5) & (ha1200["ai_capacity_mw"] == 1200)]["reclaimed_water_use_ml"].iloc[0])
    ck("再生水用量 0→16790 ML", f"{recl05:.1f}", "rstar_scan_ha.csv",
       abs(recl05 - 16790.1) < 1.0)

    # 情形验证
    rval = pd.read_csv(R2 / "rstar_regime_validation.csv", encoding="utf-8-sig")
    for code, expect in (("I", 20.74), ("II", 6.48), ("III", 0.0)):
        ss = rval[rval["regime"] == code].sort_values("target_r")
        got = 100 * (float(ss.iloc[-1]["total_withdrawal_ml"]) / float(ss.iloc[0]["total_withdrawal_ml"]) - 1)
        ck(f"情形 {code} 增幅 {expect:+.2f}%", f"{got:+.2f}%", "rstar_regime_validation.csv",
           abs(got - expect) < 0.02)
    s1 = rval[rval["regime"] == "I"].sort_values("target_r")
    coc0_i = float(s1.iloc[0]["coc_model"])
    ck("情形 I 在 r=0 时 CoC=12.22（非设计值 15）", f"{coc0_i:.2f}",
       "rstar_regime_validation.csv", abs(coc0_i - 12.2222) < 1e-3)

    # 弹性
    sens = json.loads((R2 / "rstar_sensitivity_summary.json").read_text(encoding="utf-8"))
    for p, expect in (("L", 1.69), ("coc_design", -1.69),
                      ("c_reclaimed", -1.38), ("c_potable", -0.31)):
        got = float(sens["elasticity"][p])
        ck(f"弹性 {p} ≈ {expect:+.2f}", f"{got:+.4f}", "rstar_sensitivity_summary.json",
           abs(got - expect) < 0.01)

    # 纯物理 CAWCC
    ph = pd.read_csv(R2 / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")
    ha0 = float(ph[(ph["domain"] == "ha") & (ph["target_r"] == 0.0)]["physical_cawcc_mw"].iloc[0])
    ha9 = float(ph[(ph["domain"] == "ha") & (ph["target_r"] == 0.9)]["physical_cawcc_mw"].iloc[0])
    co9 = float(ph[(ph["domain"] == "co") & (ph["target_r"] == 0.9)]["physical_cawcc_mw"].iloc[0])
    ck("HA 物理 CAWCC 1200→1100（−100MW）", f"{ha0:.0f}→{ha9:.0f}",
       "rstar_physical_cawcc_by_r.csv", ha0 == 1200 and ha9 == 1100)
    ck("CO 物理 CAWCC 基本不动（1450/1400）", f"{co9:.0f}",
       "同上", co9 == 1400.0)

    # 混淆排除
    cf = pd.read_csv(R2 / "rstar_confound_control.csv", encoding="utf-8-sig")
    h = cf[(cf["domain"] == "ha") & ((cf["capacity_mw"] - 1200.0).abs() < 1e-6)]
    s5 = float(h[h["target_r"] == 0.5]["max_source_abstraction_ratio"].iloc[0])
    s6 = float(h[h["target_r"] == 0.6]["max_source_abstraction_ratio"].iloc[0])
    g5 = float(h[h["target_r"] == 0.5]["max_daily_average_grid_connection_ratio"].iloc[0])
    g9 = float(h[h["target_r"] == 0.9]["max_daily_average_grid_connection_ratio"].iloc[0])
    ck("水源比 0.9497→0.9513", f"{s5:.4f}→{s6:.4f}", "rstar_confound_control.csv",
       abs(s5 - 0.9497) < 5e-4 and abs(s6 - 0.9513) < 5e-4)
    ck("电网约束 Δ=0.0000", f"{g5:.4f}→{g9:.4f}", "同上", abs(g5 - g9) < 1e-12)

    # 零效应区
    for dom, expect in (("ha", 1200.0), ("co", 1450.0)):
        s = ph[(ph["domain"] == dom) & (ph["target_r"] <= 0.35)]
        uniq = sorted(set(s["physical_cawcc_mw"].astype(float)))
        ck(f"零效应区 {dom.upper()} 恒 {expect:.0f}", f"{uniq}", "同上",
           uniq == [expect])

    # 口径桥接
    br = pd.read_csv(R2 / "rstar_policy_bridge.csv", encoding="utf-8-sig")
    wd = float(br["W_over_D"].median())
    ck("W/D 中位 5.33", f"{wd:.2f}", "rstar_policy_bridge.csv", abs(wd - 5.33) < 0.01)

    # ---- 摘要中的数字必须出现在正文 ----
    body = text.replace(ab, "")
    missing_in_body = [n for n in nums_in_ab if n not in body and n not in ("0.0", "1.0")]
    ck("摘要全部小数均出现在正文", f"缺失 {len(missing_in_body)}",
       "03_主稿_v2.md", not missing_in_body)

    # ---- 输出 ----
    print("=" * 104)
    print("摘要与关键数字溯源核对")
    print("=" * 104)
    print(f"{'判定':<6} {'项目':<40} {'取值':<24} 来源")
    print("-" * 104)
    passed = 0
    for claim, value, source, ok in ROWS:
        if ok:
            passed += 1
        print(f"{'PASS' if ok else 'FAIL':<6} {claim[:40]:<40} {value[:24]:<24} {source}")
    print("-" * 104)
    print(f"合计 {passed}/{len(ROWS)} 通过")
    if missing_in_body:
        print("摘要中未在正文出现的小数:", missing_in_body)

    out = HERE / "_verify_abstract.json"
    out.write_text(json.dumps(
        {"passed": passed, "total": len(ROWS),
         "rows": [{"claim": c, "value": v, "source": s, "ok": o} for c, v, s, o in ROWS]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out}")
    sys.exit(0 if passed == len(ROWS) else 1)


if __name__ == "__main__":
    main()
