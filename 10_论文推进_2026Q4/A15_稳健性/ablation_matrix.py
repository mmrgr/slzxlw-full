#!/usr/bin/env python
# ⛔ OBSOLETE / 已作废 (2026-10-14) —— 请勿运行, 勿引用其产物。
# 作废原因: 见 A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md
#   该脚本使用已撤回的 psi/Delta 公式 (D 取错量 + 取水量与缺口相减)。
# 替代品: A13_可靠性机制/potable_flow_corrected.py (核心)
#        A15_稳健性/ablation_matrix_corrected.py (消融)
#        A15_稳健性/holdout_validation_corrected.py (留出+边界)
# 保留本文件仅作审计留痕。

"""task-4 / 交付物 2: 新机制消融矩阵.

设计: {可靠性闭合 on/off} x {水质反馈 on/off} x {存量池 vs 增量供给}

三个因子的物理含义
------------------
1) 可靠性闭合 (reliability closure)
   on : S_city = S_algebra - lam*Delta,  Delta = W*max(0, psi-1)
        有限自来水供水, 挤占在缺水时产生真实社会成本
   off: S_city = S_algebra                (旧口径, 无限回补, Delta≡0)
        —— A13 已证此时 S_city ≡ M0-M <= 0

2) 水质反馈 (quality feedback)
   on : AI 外部补水 M 随混合比 phi 变化 (经引擎 quality_limited 求解),
        水质受限使 M 上升 -> 质量通道 Q = (M0-M) 变负
   off: 冻结 M = M0 (强制无水回用基线), 即人为切断 "浓缩倍数下降->补水上升"
        的反馈链。此时质量通道 Q ≡ 0 (恒为零惩罚), 只剩可靠性通道。
        ⚠ 这是**反事实手术**, 不是可选设计: 它检验 "若水质惩罚不存在,
          净效应会怎样", 用于把两通道贡献分离。

3) 存量池 vs 增量供给 (stock vs flow)
   stock (存量池): dp_scale = 0, available = pool
       再生水总量固定; AI 多拿 = 既有用户少拿 (纯零和份额问题)
   flow (增量供给): dp_scale = 1.0, available = pool*(1+1) = 2*pool
       另有新增产能注入, 池子变大, 可能超过既有用户缺口

⚠ 引擎实现注意 (探针实测): dp_scale 不是"独立新增水量", 而是把池预算
   按 available = pool*(1+dp_scale) 放大。故 flow 档必然引入容量效应,
   而不仅是"分配规则"变化。本表据此如实标注。

量化指标: 相对基线 (三因子全关) 的 S_city 增量, 以及各因子的主效应/交互项
(2^3 全因子设计, 可做标准方差分解)。

产出: ablation_matrix.csv
"""
from __future__ import annotations

import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _common as C  # noqa: E402
import city_model as cm  # noqa: E402
import reliability_model as rm  # noqa: E402

# 消融情景网格: 覆盖缺水/宽松 x 水质严/宽 x 两域
W_GRID = (0.80, 0.90, 0.95, 1.00, 1.20)
CHI_GRID = (1.0, 0.5)
PHI_GRID = (0.0, 0.4, 0.8)
SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
           "AI-UWM model assumption"]
DOMS = ("ha", "co")
LAM = 1.0


def run_cell(dom, smp, ws, chi, phi, closure, quality, stock, cache):
    """一个消融格点. 返回 S_city 及分通道量."""
    dp = 0.0 if stock == "stock" else 1.0
    r = rm.solve_with_reliability(dom, "B_full", smp, W_scale=ws, D_scale=1.0,
                                  ai_target=phi, dp_scale=dp, limit_scale=chi,
                                  lam=LAM, cache=cache)
    M, m0 = r["M_ml"], r["m0_ml"]
    # --- 因子 2: 水质反馈 off => 冻结 M=M0 => 质量通道 Q 恒为 0
    M_eff = m0 if quality == "off" else M
    x_ai, inc, pool = r["x_ai_ml"], r["inc_reclaimed_ml"], r["pool_ml"]
    S_alg = (m0 - M_eff) + inc - pool
    # --- 因子 1: 可靠性闭合 off => Delta 不计
    Delta = 0.0 if closure == "off" else r["Delta_ml"]
    S = S_alg - LAM * Delta
    return {
        "S_city_ml": float(S),
        "S_algebra_ml": float(S_alg),
        "channel_Q_ml": float(m0 - M_eff),   # <=0 质量惩罚
        "channel_R_ml": float(-LAM * Delta),  # <=0 失配惩罚 (改善=0)
        "M_ml": float(M_eff), "m0_ml": float(m0),
        "x_ai_ml": float(x_ai), "inc_reclaimed_ml": float(inc),
        "pool_ml": float(pool), "psi": float(r["psi"]),
        "Delta_ml": float(Delta), "phi_eff": float(r["phi_eff"]),
        "status": str(r["status"]),
    }


def main() -> int:
    t0 = time.time()
    cache: dict = {}
    rows: list[dict] = []
    levels = ["on", "off"]
    stocks = ["stock", "flow"]

    print("=" * 78)
    print("task-4 / 交付物2: 消融矩阵 {可靠性} x {水质反馈} x {存量池/增量供给}")
    print("=" * 78)

    for dom in DOMS:
        for smp in SAMPLES:
            for ws in W_GRID:
                for chi in CHI_GRID:
                    for phi in PHI_GRID:
                        for cl, ql, st in itertools.product(levels, levels, stocks):
                            try:
                                c = run_cell(dom, smp, ws, chi, phi, cl, ql, st, cache)
                            except Exception as e:            # noqa: BLE001
                                c = {"S_city_ml": np.nan, "status": f"ERR:{type(e).__name__}"}
                            rows.append({
                                "domain": dom, "sample": smp, "W_scale": ws,
                                "chi": chi, "phi": phi,
                                "reliability": cl, "quality_fb": ql, "supply": st,
                                **c,
                            })

    df = pd.DataFrame(rows)
    df.to_csv(HERE / "ablation_matrix.csv", index=False, encoding="utf-8-sig")
    ok = df[np.isfinite(df.S_city_ml)].copy()
    print(f"  总格点 {len(df)}, 有效 {len(ok)}")

    # ---------------- 主效应 (2x2x2 方差分解) ----------------
    def effects(sub: pd.DataFrame) -> dict:
        """对一组 (dom,sample,ws,chi,phi) 的 8 个格点做因子主效应.

        主效应 = 因子从 off->on 时 S_city 的平均变化 (配对, 对其它因子平均)。
        """
        piv = sub.pivot_table(index=["reliability", "quality_fb", "supply"],
                              values="S_city_ml", aggfunc="mean")
        if len(piv) < 8:
            return {}
        v = piv["S_city_ml"]
        def pick(cl, ql, st):
            return float(v.loc[(cl, ql, st)])
        out = {}
        # 各因子主效应 (on - off), 对另两因子取平均
        out["main_reliability"] = float(np.mean([
            pick("on", q, s) - pick("off", q, s)
            for q, s in itertools.product(levels, stocks)]))
        out["main_quality"] = float(np.mean([
            pick(c, "on", s) - pick(c, "off", s)
            for c, s in itertools.product(levels, stocks)]))
        out["main_supply"] = float(np.mean([
            pick(c, q, "flow") - pick(c, q, "stock")
            for c, q in itertools.product(levels, levels)]))
        # 基线 = 三因子全关
        out["baseline_alloff_ml"] = pick("off", "off", "stock")
        out["full_on_flow_ml"] = pick("on", "on", "flow")
        return out

    eff_rows = []
    for (dom, smp, ws, chi, phi), sub in ok.groupby(
            ["domain", "sample", "W_scale", "chi", "phi"]):
        e = effects(sub)
        if e:
            eff_rows.append({"domain": dom, "sample": smp, "W_scale": ws,
                             "chi": chi, "phi": phi, **e})
    eff = pd.DataFrame(eff_rows)
    eff.to_csv(HERE / "ablation_effects.csv", index=False, encoding="utf-8-sig")

    # ---------------- 单因子边际汇总 ----------------
    def marg(col, a, b, name):
        """因子 col 从 a->b 时 S_city 的平均变化, 按 domain 分组."""
        r = {}
        for dom in DOMS:
            s = ok[ok.domain == dom]
            pa = s[s[col] == a].set_index(["sample", "W_scale", "chi", "phi"]
                                          + [c for c in ("reliability", "quality_fb", "supply")
                                             if c != col])["S_city_ml"]
            pb = s[s[col] == b].set_index(["sample", "W_scale", "chi", "phi"]
                                          + [c for c in ("reliability", "quality_fb", "supply")
                                             if c != col])["S_city_ml"]
            j = pd.concat([pa.rename("a"), pb.rename("b")], axis=1).dropna()
            r[dom] = float((j["b"] - j["a"]).mean()) if len(j) else float("nan")
            r[f"{dom}_n"] = int(len(j))
        return r

    summary = {
        "n_gridpoints": int(len(df)),
        "n_effective": int(len(ok)),
        "design": "2 (reliability) x 2 (quality_fb) x 2 (supply) 全因子",
        "stock_definition": "dp_scale=0 -> available=pool (纯份额, 零和)",
        "flow_definition": "dp_scale=1 -> available=2*pool (引擎口径, 含容量扩张)",
        "main_effect_mean_ml": {
            "reliability_on_minus_off": marg("reliability", "off", "on", "R"),
            "quality_fb_on_minus_off": marg("quality_fb", "off", "on", "Q"),
            "flow_minus_stock": marg("supply", "stock", "flow", "S"),
        },
        "effects_median_ml": {
            k: (float(eff[k].median()) if k in eff and len(eff) else None)
            for k in ("main_reliability", "main_quality", "main_supply",
                      "baseline_alloff_ml", "full_on_flow_ml")},
        "effects_mean_ml": {
            k: (float(eff[k].mean()) if k in eff and len(eff) else None)
            for k in ("main_reliability", "main_quality", "main_supply",
                      "baseline_alloff_ml", "full_on_flow_ml")},
        "reliability_effect_zero_share": (
            float((eff.main_reliability == 0).mean()) if len(eff) else None),
        "reliability_effect_negative_share": (
            float((eff.main_reliability < 0).mean()) if len(eff) else None),
        "runtime_s": round(time.time() - t0, 1),
    }

    # ---------------- Gate ----------------
    g = C.GateLog()
    # G1: 三因子全关 -> 必须退化回 S_city <= 0 (旧结论)
    off_all = ok[(ok.reliability == "off") & (ok.quality_fb == "off") &
                 (ok.supply == "stock")]
    mx = float(off_all.S_city_ml.max()) if len(off_all) else float("nan")
    g.add("消融 G1: 三因子全关退化回旧结论", bool(mx <= 1e-6), f"max S_city = {mx:.3f} ML",
          "全关时应等价于 T11 旧口径, S_city ≡ M0-M <= 0",
          f"{len(off_all)} 个全关格点, 最大 S_city={mx:.3f} ML")

    # G2: 可靠性闭合 off 且**存量池** -> 应 <=0
    # ⚠ 第一版漏了 supply=="stock" 限定, 于是把 flow(dp=1) 下的位移记账算进来,
    #   误报 FAIL。A13 的恒等式只在 available=pool (即 stock) 时成立, 必须限定。
    ro = ok[(ok.reliability == "off") & (ok.quality_fb == "on") &
            (ok.supply == "stock")]
    mx2 = float(ro.S_city_ml.max()) if len(ro) else float("nan")
    g.add("消融 G2: 关闭可靠性闭合(存量池)也应 <=0", bool(mx2 <= 1e-6),
          f"max S_city = {mx2:.3f} ML",
          "A13 恒等式要求 available=pool 时 S_city<=0",
          f"{len(ro)} 个存量池格点, max={mx2:.3f} ML")
    # G2b (诊断): 同样配置但在增量供给档下 -> 位移记账可使 S_city>0
    rf = ok[(ok.reliability == "off") & (ok.quality_fb == "on") &
            (ok.supply == "flow")]
    mx2b = float(rf.S_city_ml.max()) if len(rf) else float("nan")
    g.add("消融 G2b: 增量供给档下位移可使 S_city>0 (口径提示)", None,
          f"max S_city = {mx2b:.3f} ML",
          "记录而非判定: 说明 0.62 属增量供给口径, 不是纯份额口径",
          f"{len(rf)} 个 flow 格点; 关掉可靠性闭合仍有正 S_city => "
          f"正号来自 inc_recl>pool 的位移记账")

    # G3: 水质反馈必须使 S_city 下降 (质量惩罚为负)
    q_on = float(eff.main_quality.median()) if len(eff) else float("nan")
    g.add("消融 G3: 水质反馈方向为负 (打开使 S_city 下降)", bool(q_on <= 0),
          f"中位主效应 = {q_on:.1f} ML", "打开水质反馈应引入质量惩罚 <=0",
          f"{len(eff)} 组配对; 中位 {q_on:.1f} ML, "
          f"为负的比例 {float((eff.main_quality <= 0).mean()):.2f}")

    # G4: 可靠性闭合方向为负 (打开使 S_city 下降)
    # ⚠ 用**均值**而非中位: Delta>0 只在 psi>1 的子集发生, 其余格点恰好为 0,
    #   于是中位数恒为 0 (既有 A13 产物也报 0), 那会掩盖真实效应。均值才可辨。
    r_on = float(eff.main_reliability.mean()) if len(eff) else float("nan")
    r_on_med = float(eff.main_reliability.median()) if len(eff) else float("nan")
    g.add("消融 G4: 可靠性闭合方向为负", bool(r_on <= 0),
          f"均值主效应 = {r_on:.1f} ML (中位 {r_on_med:.1f})",
          "打开闭合应增加失配惩罚 <=0 (用均值, 中位被 psi<=1 的零效应格点占住)",
          f"均值 {r_on:.1f} ML; 严格为负比例 "
          f"{float((eff.main_reliability < 0).mean()):.2f}, "
          f"恰为 0 比例 {float((eff.main_reliability == 0).mean()):.2f}")

    summary["gates"] = g.to_json()
    C.write_json(HERE / "ablation_summary.json", summary)

    print("\n主效应 (on - off, ML):")
    print(f"  {'因子':<12}{'ha 均值':>12}{'co 均值':>12}{'中位':>12}")
    for lbl, key, med in (("可靠性闭合", "reliability_on_minus_off",
                           float(eff.main_reliability.median()) if len(eff) else np.nan),
                          ("水质反馈", "quality_fb_on_minus_off",
                           float(eff.main_quality.median()) if len(eff) else np.nan),
                          ("增量供给", "flow_minus_stock",
                           float(eff.main_supply.median()) if len(eff) else np.nan)):
        print(f"  {lbl:<12}{summary['main_effect_mean_ml'][key]['ha']:>12.1f}"
              f"{summary['main_effect_mean_ml'][key]['co']:>12.1f}{med:>12.1f}")
    print(f"\n耗时 {summary['runtime_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
