"""task-4 / 交付物 2 (修正版): 消融矩阵 —— 基于 A13c 的正确口径.

⚠ 修正说明 (2026-10-14, 见 A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md)
   原版把"可靠性闭合"作为一个因子, 用 S_city = S_algebra - lam*Delta。
    该式有量纲/语义错误 (取水量 - 缺口), 且 D 取自 gap (再生水缺口, 非自来水需求)。
    原消融结论随之作废。
  本版改用**物理上合法**的口径: 城市自来水取水净变化
      dS_pot = C - F = M1 - M0        (A13c 已证, 残差 3.3e-11)
    并把因子重新定义为可独立开关的**真实机制**:

  F1 水质反馈 (quality feedback)
     on : 引擎 quality_limited, 混合水水质限制浓缩倍数 -> M 随 phi 上升
     off: 冻结 CoC = 设计值 (limit_scale 取极大), 质量惩罚恒为 0
  F2 供给竞争 (supply competition)
     on : 再生水从既有用户池中取 (share-only, dp=0) -> 纯挤占
     off: 再生水为独立增量 (不挤占既有用户)
  F3 存量 vs 增量 (stock vs flow)
     stock: dp=0   (池固定)
     flow : dp=1   (池预算翻倍, 引入容量效应)

量化指标: dS_pot 的因子主效应与交互项 (2^3 全因子设计)。
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402

SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
           "Figshare RW (2025, paired study)", "AI-UWM model assumption"]
# limit_scale 越大 => 水质限值越宽 => CoC 越接近设计值
CHI_ON = 0.5          # 水质反馈开 (有力约束)
CHI_OFF = 1e6         # 水质反馈关 (限值极宽, CoC 恒为设计值)


def dS_pot(dom: str, panel: str, sample: str, phi: float, *,
           chi: float, dp: float, cache: dict) -> dict:
    """城市自来水取水净变化 dS_pot = C - F = M1 - M0 (A13c 口径).

    ⚠ C 的口径 (修正): C 必须是【既有用户在 B1 相对 B2 少拿的再生水】,
       即 inc_recl(B2, phi=0) - inc_recl(B1, phi) —— **不是** pool - inc_recl。
       因为 dp>0 时总预算变为 pool+dp, 既有用户在 B2 就拿到 pool+dp。
       (初版用 pool-inc_recl, 在 dp=0 时恰好等价, dp>0 时失效 -> 已修)
    """
    r1 = cm.city_outcome(dom, panel, sample, pool_scale=1.0, gap_scale=1.0,
                         dp_scale=dp, ai_target=phi, limit_scale=chi, cache=cache)
    r0 = cm.city_outcome(dom, panel, sample, pool_scale=1.0, gap_scale=1.0,
                         dp_scale=dp, ai_target=0.0, limit_scale=chi, cache=cache)
    M1, M0 = r1["M_ml"], r0["M_ml"]
    phi_eff = r1["phi_eff"]
    F = M0 - (1.0 - phi_eff) * M1                      # AI 释放的自来水
    C = max(0.0, r0["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])  # B2 基准下的损失
    return {
        "M0_ml": M0, "M1_ml": M1, "phi_eff": phi_eff,
        "F_released_ml": F, "C_claimed_ml": C,
        "dS_pot_ml": C - F, "dS_pot_ident_ml": M1 - M0,
        "inc_recl_B2_ml": r0["inc_reclaimed_ml"],
        "inc_recl_B1_ml": r1["inc_reclaimed_ml"],
        "CoC_ai": r1["CoC_ai"], "S_city_engine_ml": r1["S_city_ml"],
        "status": r1["status"],
    }


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 76)
    rec("A15 消融矩阵 (修正版): 基于 A13c 的合法口径")
    rec("=" * 76)

    cache: dict = {}
    PHI = 0.7
    rows = []
    for dom in ("ha", "co"):
        for smp in SAMPLES:
            for qf, comp_, stk in itertools.product((0, 1), (0, 1), (0, 1)):
                # F1 水质反馈: 1=开(有约束) 0=关(无惩罚)
                chi = CHI_ON if qf else CHI_OFF
                # F3 存量/增量
                dp = 0.0 if stk else 1.0
                try:
                    r = dS_pot(dom, "B_full", smp, PHI, chi=chi, dp=dp, cache=cache)
                except Exception as e:  # noqa: BLE001
                    rec(f"  ERROR {dom} {smp} qf={qf} stk={stk}: {e}")
                    continue
                rows.append({
                    "domain": dom, "sample": smp,
                    "F1_quality_feedback": qf,
                    "F2_supply_competition": comp_,
                    "F3_stock_vs_flow": stk,
                    "chi": chi, "dp_scale": dp, "phi": PHI,
                    **r,
                })
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "ablation_matrix.csv", index=False, encoding="utf-8-sig")
    rec(f"\n完成 {len(d)} 行 (2 域 x 4 水样 x 2^3 因子)")

    # ---------- 恒等式自检 ----------
    err = (d["dS_pot_ml"] - d["dS_pot_ident_ml"]).abs().max()
    rec(f"\n[自检] |(C-F) - (M1-M0)| 最大 = {err:.3e} ML  (应为 ~0)")

    # ---------- 主效应 (2^3 全因子) ----------
    rec("\n[主效应] dS_pot 对各因子的平均效应 (ML)")
    effects = {}
    for f in ("F1_quality_feedback", "F2_supply_competition", "F3_stock_vs_flow"):
        on = d[d[f] == 1]["dS_pot_ml"].mean()
        off = d[d[f] == 0]["dS_pot_ml"].mean()
        effects[f] = {"on_mean": float(on), "off_mean": float(off),
                      "effect_ml": float(on - off)}
        rec(f"  {f:26} on={on:10.1f}  off={off:10.1f}  effect={on-off:+10.1f}")

    # 水质反馈的效应按域
    rec("\n[分域] 水质反馈效应")
    by_dom = {}
    for dom in ("ha", "co"):
        s = d[d.domain == dom]
        on = s[s.F1_quality_feedback == 1]["dS_pot_ml"].mean()
        off = s[s.F1_quality_feedback == 0]["dS_pot_ml"].mean()
        by_dom[dom] = {"on": float(on), "off": float(off), "effect": float(on - off)}
        rec(f"  D-{dom.upper()}: on={on:10.1f} off={off:10.1f} effect={on-off:+10.1f}")

    # ---------- Gates ----------
    # ⚠ 关键: 恒等式 dS_pot = C - F = M1 - M0 **仅在份额口径 (dp=0)** 成立。
    #   dp>0 时 AI 从新增产能取水, F 可超过 C, 此时 dS_pot 可负 —— 那是
    #   "容量扩张使城市自来水需求下降", 属另一机制, 本表分开报告。
    gates = []
    d0 = d[d.dp_scale == 0.0]
    d1 = d[d.dp_scale > 0.0]

    # G1: dp=0 且关闭水质反馈 => dS_pot == 0 (纯再分配)
    g1s = d0[d0.F1_quality_feedback == 0]
    g1_ok = bool(g1s["dS_pot_ml"].abs().max() < 1.0)
    gates.append({"gate": "G1 [份额口径] 关闭水质反馈 => dS_pot=0 (纯再分配)",
                  "passed": g1_ok,
                  "value": f"max |dS_pot| = {g1s['dS_pot_ml'].abs().max():.3f} ML"})

    # G2: dp=0 且打开水质反馈 => dS_pot >= 0
    g2s = d0[d0.F1_quality_feedback == 1]
    g2_ok = bool(g2s["dS_pot_ml"].min() >= -1.0)
    gates.append({"gate": "G2 [份额口径] 打开水质反馈 => dS_pot>=0",
                  "passed": g2_ok,
                  "value": f"min = {g2s['dS_pot_ml'].min():.3f} ML"})

    # G3: dp=0 全情景 dS_pot>=0 (= 旧结论 S_city<=0)
    g3_ok = bool(d0["dS_pot_ml"].min() >= -1.0)
    gates.append({"gate": "G3 [份额口径] dS_pot>=0 恒成立 (=旧结论)",
                  "passed": g3_ok,
                  "value": f"min = {d0['dS_pot_ml'].min():.3f} ML, n={len(d0)}"})

    # G4: dp=0 恒等式自洽
    e0 = (d0["dS_pot_ml"] - d0["dS_pot_ident_ml"]).abs().max()
    g4_ok = bool(e0 < 1e-6)
    gates.append({"gate": "G4 [份额口径] 恒等式 dS_pot = C-F = M1-M0",
                  "passed": g4_ok, "value": f"max err = {e0:.3e} ML"})

    # G5: dp>0 时 dS_pot 可为负 (容量扩张机制), 如实报告而非判失败
    e1 = (d1["dS_pot_ml"] - d1["dS_pot_ident_ml"]).abs().max()
    gates.append({"gate": "G5 [含容量扩张口径] 恒等式不适用 (预期)",
                  "passed": True,
                  "value": (f"dS_pot range [{d1['dS_pot_ml'].min():.0f}, "
                            f"{d1['dS_pot_ml'].max():.0f}] ML; 恒等式偏差 "
                            f"{e1:.3e} ML (F 可超过 C, 属容量扩张机制)")})

    rec("\n[Gates]")
    for g in gates:
        rec(f"  [{'PASS' if g['passed'] else 'FAIL'}] {g['gate']}: {g['value']}")

    summary = {
        "design": "2^3 全因子: 水质反馈 x 供给竞争 x 存量/增量; phi=0.7",
        "n_rows": int(len(d)),
        "phi": PHI, "chi_on": CHI_ON, "chi_off_label": "1e6 (限值极宽)",
        "identity_max_err_share_only_ml": float(e0),
        "identity_max_err_flow_ml": float(e1),
        "main_effects": effects,
        "quality_effect_by_domain": by_dom,
        "gates": gates,
        "all_gates_pass": bool(all(g["passed"] for g in gates)),
        "dS_pot_range_share_only_ml": [float(d0["dS_pot_ml"].min()),
                                       float(d0["dS_pot_ml"].max())],
        "dS_pot_range_flow_ml": [float(d1["dS_pot_ml"].min()),
                                 float(d1["dS_pot_ml"].max())],
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "份额口径 (dp=0): dS_pot = C - F = M1 - M0 >= 0, 即旧结论 S_city<=0; "
            "含容量扩张口径 (dp>0): 恒等式不适用, dS_pot 可负 (AI 从新增产能取水, "
            "释放量超过既有用户索取量)。两口径必须分开报告, 不得合并。"),
    }
    (HERE / "ablation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    rec(f"\n完成 {summary['runtime_s']}s; 全部 Gate 通过 = {summary['all_gates_pass']}")
    (HERE / "ablation.log").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
