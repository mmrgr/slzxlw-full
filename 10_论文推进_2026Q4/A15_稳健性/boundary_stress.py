#!/usr/bin/env python
# ⛔ OBSOLETE / 已作废 (2026-10-14) —— 请勿运行, 勿引用其产物。
# 作废原因: 见 A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md
#   该脚本使用已撤回的 psi/Delta 公式 (D 取错量 + 取水量与缺口相减)。
# 替代品: A13_可靠性机制/potable_flow_corrected.py (核心)
#        A15_稳健性/ablation_matrix_corrected.py (消融)
#        A15_稳健性/holdout_validation_corrected.py (留出+边界)
# 保留本文件仅作审计留痕。

"""task-4 / 交付物 5: 边界条件压力测试.

两个极限 + 一个附加的数值稳定性检验。

§1 W_pot -> ∞ (无限自来水供给)
   命题: 新机制应在 W->∞ 时**退化回旧结论**。
   旧结论 A13 口径: S_city ≡ S_algebra = M0 - M <= 0 (恒等式), Delta ≡ 0。
   检验: W_scale 从 1 推到 1e8, 看 (a) psi->0, (b) Delta->0, (c) S_city->S_algebra,
        (d) 增量是否按 1/W 衰减 (即收敛是一阶的, 不是病态)。
   ⚠ 关键限定: 退化到的旧结论是 **S_city <= 0**。若在 dp>0 口径下 S_algebra>0,
     则"退化"给出的是 S_algebra>0, 而不是 <=0。这不是 bug, 而是说明
     "旧结论 S_city<=0" 本身只在 dp=0 口径成立 (见 robustness_summary.md §0)。
     本表对 dp=0 与 dp=1 两个口径分别做极限检验。

§2 eps -> 0 (需求刚性极限)
   A13 的 reliability_closure 中, Delta = max(0, D + eff_ai_pot - W), 与 eps 无关
   (模块 docstring 引入 eps 但实现里未使用 —— 本身是一处不一致, 见 §3)。
   本脚本用**外部**参数化检验刚性极限: 令既有用户可让渡份额 eps,
   则 AI 挤占能被吸收的量 = eps * min(挤占量, 既有用户再生水份额),
   剩余才转化为 Delta。eps=1 完全可让渡 (无成本), eps=0 完全刚性 (全成本)。
   检验: eps 从 1 降到 0, Delta 与 S_city 的路径, 以及 S_city<=0 是否始终成立。

§3 实现一致性核查
   reliability_closure docstring 声明 eps 参数并给出 g(eps) 让渡成本项,
   但函数签名与实现里都没有 eps, 也没有 g(eps), S_city 中也没有该项。
   这是文档-实现不一致, 如实报告。

产出: boundary_stress.py (本文件) -> boundary_stress_summary.json
"""
from __future__ import annotations

import json
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

SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
           "AI-UWM model assumption"]
DOMS = ("ha", "co")
W_SWEEP = np.array([1.0, 1.2, 2.0, 5.0, 10.0, 100.0, 1e4, 1e6, 1e8])
EPS_SWEEP = np.array([1.0, 0.75, 0.5, 0.25, 0.1, 0.0])
# 让 W 真正收紧的配置: chi=0.5 使 M 上升, D_scale>1 使既有需求大
STRESS = {"D_scale": 1.5, "limit_scale": 0.5, "phi": 0.4}


def main() -> int:
    t0 = time.time()
    cache: dict = {}
    print("=" * 78)
    print("task-4 / 交付物5: 边界条件压力测试")
    print("=" * 78)

    # ---------------- §1 W_pot -> ∞ ----------------
    print("\n[§1] W_pot -> ∞ 退化检验")
    rows = []
    for dom in DOMS:
        for smp in SAMPLES:
            for dp in (0.0, 1.0):
                for ws in W_SWEEP:
                    r = rm.solve_with_reliability(
                        dom, "B_full", smp, W_scale=float(ws),
                        D_scale=STRESS["D_scale"], ai_target=STRESS["phi"],
                        dp_scale=dp, limit_scale=STRESS["limit_scale"],
                        cache=cache)
                    rows.append({
                        "domain": dom, "sample": smp, "dp_scale": dp,
                        "W_scale": float(ws),
                        "psi": r["psi"], "Delta_ml": r["Delta_ml"],
                        "S_city_ml": r["S_city_ml"],
                        "S_algebra_ml": r["S_algebra_ml"],
                        "gap_ml": r["S_city_ml"] - r["S_algebra_ml"],
                        "W_ml": r["W_ml"],
                        "status": str(r["status"]),
                    })
    w = pd.DataFrame(rows)
    w.to_csv(HERE / "boundary_stress_W.csv", index=False, encoding="utf-8-sig")

    # 大 W 极限 (取 W_scale=1e8 作为 ∞ 的数值代理)
    big = w[np.isclose(w.W_scale, 1e8)]
    print(f"  W_scale=1e8 时: max psi = {big.psi.max():.3e}, "
          f"max |Delta| = {big.Delta_ml.abs().max():.3e} ML")
    print(f"  max |S_city - S_algebra| = {big.gap_ml.abs().max():.3e} ML")
    # 收敛阶: gap ~ C/W ?
    order_rows = []
    for (dom, smp, dp), sub in w.groupby(["domain", "sample", "dp_scale"]):
        s = sub[np.isfinite(sub.gap_ml)].sort_values("W_scale")
        s = s[s.W_scale >= 1.0]
        if len(s) < 3:
            continue
        # 只对有 Delta>0 的配置做阶数估计 (否则 gap 恒 0)
        pos = s[s.gap_ml.abs() > 1e-9]
        if len(pos) < 3:
            continue
        x = np.log(pos.W_scale.values)
        y = np.log(np.abs(pos.gap_ml.values))
        slope = float(np.polyfit(x, y, 1)[0])
        order_rows.append({"domain": dom, "sample": smp, "dp_scale": dp,
                           "log_log_slope": slope, "n": len(pos)})
    order = pd.DataFrame(order_rows)
    if len(order):
        order.to_csv(HERE / "boundary_stress_W_order.csv", index=False,
                     encoding="utf-8-sig")
        print(f"  |S_city - S_algebra| ~ W^slope, slope 中位 = "
              f"{order.log_log_slope.median():.4f} (期望 -1.0)")

    # dp=0 口径下 W->∞ 是否退化回 S_city<=0
    dp0_big = big[np.isclose(big.dp_scale, 0.0)]
    dp1_big = big[np.isclose(big.dp_scale, 1.0)]
    print(f"  dp=0 口径 @W->∞: S_city ∈ [{dp0_big.S_city_ml.min():.1f}, "
          f"{dp0_big.S_city_ml.max():.1f}] ML (应 <=0)")
    print(f"  dp=1 口径 @W->∞: S_city ∈ [{dp1_big.S_city_ml.min():.1f}, "
          f"{dp1_big.S_city_ml.max():.1f}] ML (可 >0, 见表注)")

    # ---------------- §2 eps -> 0 刚性极限 ----------------
    print("\n[§2] eps -> 0 刚性极限 (外部参数化)")
    # eps 的物理含义: 既有用户在缺水时能被"让渡"吸收的份额。
    # 实现: Delta_eps = eps * (被挤占的既有再生水) + max(0, 刚性缺口 - 挤占)
    #       更简洁且可辩护的口径: AI 挤占量 pc = max(0, pool - inc_recl_baseline)
    #       这里改用引擎给出的量: 挤占 = AI 分到的 x_ai 相对"无 AI 时既有用户可拿"的差额
    erows = []
    for dom in DOMS:
        for smp in SAMPLES:
            # 基准: 无 AI (phi=0) 时既有用户可拿多少再生水
            base = cm.city_outcome(dom, "B_full", smp, pool_scale=1.0,
                                   gap_scale=1.0, dp_scale=0.0, ai_target=0.0,
                                   limit_scale=STRESS["limit_scale"], cache=cache)
            inc_noai = base["inc_reclaimed_ml"]
            for ws in (1.0, 1.2, 2.0, 5.0):
                r = rm.solve_with_reliability(
                    dom, "B_full", smp, W_scale=ws,
                    D_scale=STRESS["D_scale"], ai_target=STRESS["phi"],
                    dp_scale=0.0, limit_scale=STRESS["limit_scale"], cache=cache)
                D = r["D_ml"]
                W = r["W_ml"]
                M, m0, phi_eff = r["M_ml"], r["m0_ml"], r["phi_eff"]
                # AI 实际占用的自来水
                ai_pot = (1.0 - phi_eff) * M
                # 刚性缺水缺口 (既有用户部分, 不含 AI)
                rigid_gap = max(0.0, D - W + ai_pot)   # = max(0, D + ai_pot - W)
                # 被 AI 挤走的再生水 (既有用户相对无 AI 基准的损失)
                displaced = max(0.0, inc_noai - r["inc_reclaimed_ml"])
                for eps in EPS_SWEEP:
                    # eps 表示可让渡份额: 挤占中可被吸收 = eps * displaced
                    residual = max(0.0, displaced - eps * displaced)
                    # 总失配 = 刚性缺口下既有用户承担的部分 + 未被吸收的挤占
                    Delta_eps = rigid_gap + residual
                    S = r["S_algebra_ml"] - Delta_eps
                    erows.append({
                        "domain": dom, "sample": smp, "W_scale": ws, "eps": float(eps),
                        "D_ml": D, "W_ml": W, "ai_pot_ml": ai_pot,
                        "rigid_gap_ml": rigid_gap, "displaced_ml": displaced,
                        "Delta_eps_ml": Delta_eps, "S_city_ml": S,
                        "S_algebra_ml": r["S_algebra_ml"],
                        "Delta_a13_ml": r["Delta_ml"],
                    })
    e = pd.DataFrame(erows)
    e.to_csv(HERE / "boundary_stress_eps.csv", index=False, encoding="utf-8-sig")
    e0 = e[np.isclose(e.eps, 0.0)]
    e1 = e[np.isclose(e.eps, 1.0)]
    print(f"  eps=0 (全刚性): S_city ∈ [{e0.S_city_ml.min():.1f}, "
          f"{e0.S_city_ml.max():.1f}] ML; 全部 <=0 = {bool((e0.S_city_ml <= 1e-6).all())}")
    print(f"  eps=1 (全可让渡): S_city ∈ [{e1.S_city_ml.min():.1f}, "
          f"{e1.S_city_ml.max():.1f}] ML; 全部 <=0 = {bool((e1.S_city_ml <= 1e-6).all())}")
    # eps 单调性: S_city 随 eps 上升 (损失减少)
    mono = []
    for (dom, smp, ws), sub in e.groupby(["domain", "sample", "W_scale"]):
        s = sub.sort_values("eps")
        mono.append(bool((np.diff(s.S_city_ml.values) >= -1e-9).all()))
    print(f"  S_city 随 eps 单调不减的比例 = {np.mean(mono):.3f}")

    # ---------------- §3 文档-实现一致性 ----------------
    print("\n[§3] eps 声明的文档 vs 实现一致性")
    import inspect
    sig = inspect.signature(rm.reliability_closure)
    has_eps = "eps" in sig.parameters
    fn_doc = rm.reliability_closure.__doc__ or ""
    mod_doc = rm.__doc__ or ""
    fn_src = inspect.getsource(rm.reliability_closure)
    # eps 出现在**模块** docstring (净效益定义 / 弹性参数) 与函数体内注释, 但不在签名
    mod_has_eps = "eps" in mod_doc
    body_comment_eps = "eps" in fn_src
    # docstring 定义的净效益式含 + Lambda*Delta 与 - g(eps); 实现是 - lam*Delta
    doc_defines_g_eps = "g(eps)" in mod_doc
    print(f"  模块 docstring 提到 eps = {mod_has_eps} "
          f"(声明弹性参数与 g(eps) 让渡成本 = {doc_defines_g_eps})")
    print(f"  reliability_closure 签名含 eps 参数 = {has_eps}")
    print(f"  函数体注释提到 eps (('既有用户按 1-eps 承担')) = {body_comment_eps}")
    print(f"  实现式 = S_algebra - lam*Delta (无 g(eps) 项) = {'lam * Delta' in fn_src}")

    # ---------------- Gate ----------------
    g = C.GateLog()
    max_gap_big = float(big.gap_ml.abs().max())
    max_psi_big = float(big.psi.max())
    g.add("边界1: W->∞ 时 Delta->0", bool(max_gap_big < 1e-3),
          f"max |S_city - S_algebra| = {max_gap_big:.3e} ML",
          "W_scale=1e8 时新机制的额外项必须消失",
          f"同时 max psi = {max_psi_big:.3e} -> 0, 即供水宽松极限")
    g.add("边界1b: W->∞ 退化回旧结论 (dp=0 口径)",
          bool((dp0_big.S_city_ml <= 1e-6).all()),
          f"max S_city = {dp0_big.S_city_ml.max():.3f} ML",
          "dp=0 时旧结论 S_city<=0 必须被恢复",
          "dp=0 口径下 available=pool, S_algebra 恒 <=0, 极限为其本身")
    g.add("边界1c: 收敛阶为一阶 (非病态)", bool(len(order) and
          abs(order.log_log_slope.median() + 1.0) < 0.35),
          f"slope 中位 = {order.log_log_slope.median():.3f}" if len(order) else "n/a",
          "|S_city-S_algebra| ~ W^-1 => |slope+1| < 0.35",
          f"{len(order)} 组配置可估阶")
    g.add("边界2: eps->0 刚性极限下仍 S_city<=0",
          bool((e0.S_city_ml <= 1e-6).all()),
          f"max S_city(eps=0) = {e0.S_city_ml.max():.3f} ML",
          "刚性极限不应产生正的净效益",
          f"{len(e0)} 个 eps=0 格点全部非正")
    g.add("边界2b: S_city 对 eps 单调不减", bool(np.mean(mono) >= 0.99),
          f"单调比例 = {np.mean(mono):.3f}",
          "可让渡份额越大, 城市损失越小 (>=0.99)",
          "外部参数化口径, 见脚本 §2")
    g.add("实现一致性: eps 参数在文档与实现中一致",
          not (mod_has_eps and not has_eps),
          f"模块 docstring 含 eps={mod_has_eps}, 签名含 eps={has_eps}",
          "文档声明的参数应在实现中存在",
          "模块 docstring 声明弹性参数 eps 与让渡成本 g(eps)>0, 但 "
          "reliability_closure 签名无 eps, 实现为 S_city=S_algebra-lam*Delta "
          "-> 文档-实现不一致 (g(eps) 从未实现)")

    summary = {
        "W_sweep": W_SWEEP.tolist(), "eps_sweep": EPS_SWEEP.tolist(),
        "stress_config": STRESS,
        "W_limit": {
            "max_psi_at_1e8": max_psi_big,
            "max_abs_gap_ml_at_1e8": max_gap_big,
            "dp0_S_city_range_at_1e8": [float(dp0_big.S_city_ml.min()),
                                        float(dp0_big.S_city_ml.max())],
            "dp1_S_city_range_at_1e8": [float(dp1_big.S_city_ml.min()),
                                        float(dp1_big.S_city_ml.max())],
            "convergence_slope_median": (float(order.log_log_slope.median())
                                         if len(order) else None),
            "n_slope_estimates": int(len(order)),
        },
        "eps_limit": {
            "n_rows": int(len(e)),
            "S_city_range_eps0": [float(e0.S_city_ml.min()), float(e0.S_city_ml.max())],
            "S_city_range_eps1": [float(e1.S_city_ml.min()), float(e1.S_city_ml.max())],
            "all_le_zero_eps0": bool((e0.S_city_ml <= 1e-6).all()),
            "all_le_zero_eps1": bool((e1.S_city_ml <= 1e-6).all()),
            "monotone_share": float(np.mean(mono)),
            "note": ("eps 在 A13 的实现中未被使用; 本表用**外部**参数化检验刚性极限: "
                     "Delta_eps = rigid_gap + (1-eps)*displaced, "
                     "其中 displaced = max(0, inc_noai - inc_recl) 为 AI 挤占量。"),
        },
        "impl_consistency": {
            "module_docstring_mentions_eps": bool(mod_has_eps),
            "signature_has_eps": bool(has_eps),
            "module_docstring_defines_g_eps": bool(doc_defines_g_eps),
            "has_g_eps_term_in_S_city": False,
            "finding": ("reliability_model **模块** docstring (第 10-26 行) 声明弹性参数 "
                        "eps∈[0,1] 与让渡成本项 g(eps)>=0, 并把净效益定义为 "
                        "S_city = (M0-M) + Lambda*Delta - g(eps); "
                        "但 reliability_closure 的签名没有 eps, 实现为 "
                        "S_city = S_algebra - lam*Delta, g(eps) 从未实现。"
                        "另外模块 docstring 写 '+ Lambda*Delta' 而实现的该项是负的 "
                        "(- lam*Delta), 符号相反。两处均为文档-实现不一致, 需 Lead 统一: "
                        "要么实现 g(eps), 要么删掉 docstring 中的 eps/g(eps)。"),
        },
        "gates": g.to_json(),
        "runtime_s": round(time.time() - t0, 1),
    }
    C.write_json(HERE / "boundary_stress_summary.json", summary)

    print(f"\n耗时 {summary['runtime_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
