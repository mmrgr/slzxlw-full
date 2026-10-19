# -*- coding: utf-8 -*-
"""主稿 v2 第三轮增量（r* 分类学与敏感性）的数值核对。

覆盖 §5.7.3b / §5.7.3c / §9.6 第 30–34 条引入的全部数值。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_verify_regime_numbers.py
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
V2 = HERE / "03_主稿_v2.md"

ROWS: list[tuple[str, str, str, bool]] = []


def ck(claim: str, value: str, source: str, ok: bool) -> None:
    ROWS.append((claim, value, source, bool(ok)))


def main() -> None:
    text = V2.read_text(encoding="utf-8")

    rmap = pd.read_csv(R2 / "rstar_regime_map.csv", encoding="utf-8-sig")
    rval = pd.read_csv(R2 / "rstar_regime_validation.csv", encoding="utf-8-sig")
    sens = pd.read_csv(R2 / "rstar_sensitivity.csv", encoding="utf-8-sig")
    sens_sum = json.loads((R2 / "rstar_sensitivity_summary.json").read_text(encoding="utf-8"))
    regime_sum = json.loads((R2 / "rstar_regime_summary.json").read_text(encoding="utf-8"))

    # ---- 分类计数 ----
    counts = rmap["regime"].value_counts()
    for code, expect in (("I", 81), ("II", 156), ("III", 63), ("IV", 20)):
        got = int(counts.get(code, 0))
        ck(f"分类计数 情形{code} = {expect}", f"{got}",
           "r2/rstar_regime_map.csv", got == expect)
    ck("分类网格总数 = 320", f"{len(rmap)}", "同上", len(rmap) == 320)

    # 百分比
    for code, pct in (("I", 25.3), ("II", 48.8), ("III", 19.7), ("IV", 6.2)):
        real_pct = 100.0 * int(counts.get(code, 0)) / len(rmap)
        ck(f"分类占比 情形{code} ≈ {pct}%", f"{real_pct:.1f}%",
           "同上", abs(real_pct - pct) < 0.15)

    # ---- 情形 II 的 r* 分布 ----
    sub2 = rmap[rmap["regime"] == "II"]
    for name, got, expect in (
        ("min", float(sub2["r_star"].min()), 0.0196),
        ("median", float(sub2["r_star"].median()), 0.3298),
        ("max", float(sub2["r_star"].max()), 0.9167),
    ):
        ck(f"情形 II r* {name} = {expect}", f"{got:.4f}", "同上",
           abs(got - expect) < 5e-4)

    # ---- 弹性 ----
    for param, expect in (("L", 1.6923), ("coc_design", -1.6921),
                          ("c_reclaimed", -1.3828), ("c_potable", -0.3093)):
        got = float(sens_sum["elasticity"][param])
        ck(f"弹性 {param} = {expect:+.4f}", f"{got:+.4f}",
           "r2/rstar_sensitivity_summary.json", abs(got - expect) < 5e-4)

    # ---- 单参数扫描范围 ----
    for param, lo, hi in (("L", 0.0426, 0.8936), ("coc_design", 0.0851, 1.9574),
                          ("c_potable", -10.20, 0.6500), ("c_reclaimed", 0.1970, 2.1667)):
        s = sens[sens["parameter"] == param].dropna(subset=["r_star"])
        ck(f"单参数扫描 {param} r* 范围", f"[{s['r_star'].min():.4f}, {s['r_star'].max():.4f}]",
           "r2/rstar_sensitivity.csv",
           abs(s["r_star"].min() - lo) < 5e-3 and abs(s["r_star"].max() - hi) < 5e-3)

    # ---- 三情形验证 ----
    for code, expect_coc0 in (("II", 5.0), ("I", 12.2222), ("III", 2.5)):
        s = rval[rval["regime"] == code].sort_values("target_r")
        got = float(s.iloc[0]["coc_model"])
        ck(f"情形 {code} 在 r=0 的 CoC = {expect_coc0}", f"{got:.4f}",
           "r2/rstar_regime_validation.csv", abs(got - expect_coc0) < 1e-3)

    # 取水增幅
    for code, expect_pct in (("I", 20.74), ("II", 6.48), ("III", 0.0)):
        s = rval[rval["regime"] == code].sort_values("target_r")
        w0 = float(s.iloc[0]["total_withdrawal_ml"])
        w8 = float(s.iloc[-1]["total_withdrawal_ml"])
        got = 100.0 * (w8 / w0 - 1.0)
        ck(f"情形 {code} r=0→0.8 取水增幅 = {expect_pct:+.2f}%", f"{got:+.2f}%",
           "同上", abs(got - expect_pct) < 0.02)

    # 情形 I 首个非零 r 立即为正
    s1 = rval[rval["regime"] == "I"].sort_values("target_r")
    first_inc = 100.0 * (float(s1.iloc[1]["total_withdrawal_ml"]) / float(s1.iloc[0]["total_withdrawal_ml"]) - 1.0)
    ck("情形 I 在 r=0.2 即 +4.43%（任何替代都有代价）", f"{first_inc:+.2f}%",
       "同上", abs(first_inc - 4.43) < 0.02)

    # 平坦点数
    for code, expect in (("II", 3), ("III", 5), ("I", 0)):
        s = rval[rval["regime"] == code]
        got = int(s["coc_equal_design"].sum())
        ck(f"情形 {code} 的平坦点数（CoC==设计值）= {expect}/{len(s)}", f"{got}/{len(s)}",
           "同上", got == expect)

    # ---- 重合规律（本轮修正的关键）----
    r08 = rval[(rval["target_r"] - 0.8).abs() < 1e-9]
    w_i = float(r08[r08["regime"] == "I"]["total_withdrawal_ml"].iloc[0])
    w_ii = float(r08[r08["regime"] == "II"]["total_withdrawal_ml"].iloc[0])
    w_iii = float(r08[r08["regime"] == "III"]["total_withdrawal_ml"].iloc[0])
    ck("情形 I 与 II 在 r=0.8 逐位重合", f"{w_i:.2f} / {w_ii:.2f}",
       "同上", abs(w_i - w_ii) < 1e-6)
    ck("情形 III 在 r=0.8 不重合（29,241.45 ML）", f"{w_iii:.2f}",
       "同上", abs(w_iii - 29241.45) < 0.02)
    ck("主稿已修正「三者一致」的错误表述",
       "I≡II 且 III 不同" if ("情形 I 与 II 在高替代率端精确重合" in text
                             and "三情形在 r=0.8 取水一致" not in text) else "MISSING",
       "03_主稿_v2.md", "情形 I 与 II 在高替代率端精确重合" in text)

    # ---- 主稿文本包含关键新内容 ----
    for kw in ("四情形分类学", "5.7.3c", "情形 IV", "C* ≡ L/CoC_design", "弹性",
               "阈值型响应是否存在", "32. ", "34. **分类边界"):
        ck(f"主稿含「{kw}」", "OK" if kw in text else "MISSING", "03_主稿_v2.md", kw in text)

    # ---- 输出 ----
    print("=" * 100)
    print("第三轮增量（分类学与敏感性）数值核对")
    print("=" * 100)
    print(f"{'判定':<6} {'声称':<46} {'产物取值':<28} 来源")
    print("-" * 100)
    passed = 0
    for claim, value, source, ok in ROWS:
        if ok:
            passed += 1
        print(f"{'PASS' if ok else 'FAIL':<6} {claim[:46]:<46} {value[:28]:<28} {source}")
    print("-" * 100)
    print(f"合计 {passed}/{len(ROWS)} 通过")

    out = HERE / "_verify_regime_numbers.json"
    out.write_text(json.dumps(
        {"passed": passed, "total": len(ROWS),
         "rows": [{"claim": c, "value": v, "source": s, "ok": o} for c, v, s, o in ROWS]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out}")
    sys.exit(0 if passed == len(ROWS) else 1)


if __name__ == "__main__":
    main()
