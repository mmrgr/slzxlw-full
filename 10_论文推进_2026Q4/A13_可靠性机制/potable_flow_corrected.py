"""A13c: 修正后的机制 —— 城市自来水取水的两个相反流向.

【为什么重写】
原 A13 的实现有三处实质错误 (Lead 自审发现):

错误 A (范畴错误): D_inc 取自 city_model.BASELINES[dom]["gap"],
    而引擎定义 gap = reuse_elig - P0 = 既有用户【未满足的再生水需求】,
    不是【自来水需求】(见 A7/T2_joint_quality_allocation.py:98-102)。
    把它放进 psi 的分子, 是把两种不同资源混为一谈。

错误 B (重复计数): W_AI,pot=(1-phi_eff)*M 把 AI 的非再生水补水全当自来水,
    而被挤占的既有用户也转回自来水 —— 二者在 D 与 W_AI,pot 中被分别计入,
    实为同一股水流的两次计数。

错误 C (量纲/语义错误): S_city 是【城市取水量变化】(ML),
    而 Delta 是【未满足需求缺口】(ML)。原式 S_city = S_algebra - lam*Delta
    把"取了多少水"与"多少需求没被满足"相减 —— 这是把两条不同的账混在一起,
    违反项目自己的纪律 (指标 A/B/C 不得合并)。

【正确的物理】
AI 改用再生水后, 城市【自来水】系统上出现两股方向相反的流:

    释放量  F = AI 少取的自来水 = W_AI,pot(B2) - W_AI,pot(B1)
    索取量  C = 被挤占的既有用户必须补回的自来水 = 挤占量

  城市自来水取水的净变化:
    dS_pot = C - F
      > 0  => 城市自来水取水【增加】(转移的代价)
      = 0  => 纯账面转移 (守恒)
      < 0  => 城市自来水取水【下降】(真正的净节约)

符号由 C 与 F 的相对大小决定。⚠ 修正 (2026-10-14 晚, 见 A17_统一恒等式推导.md):
  早期版本文档曾称"存在一个 phi 使 C = F, 即净效应过零点 phi0" —— 该表述已修正:
  phi0 不是由 phi 单独决定, 而是由**供给状态**决定。
  统一通式 (288 情景, 残差 3.9e-12):
      dS_pot = (r_inc(B2) - r_inc(B1)) - (M0 - M1) - x_ai
             = 挤占位移 - 水质惩罚 - AI 取用的再生水
  两分支:
      A 池被用尽 => 位移 = x_ai  => dS = M1 - M0        >= 0 (城市取水上升)
      C 存在余量 => 位移 = 0      => dS = -(M0-M1) - x_ai <  0 (城市取水下降)
  符号判据 (实测吻合率 1.000): dS < 0  <=>  x_ai + (M0-M1) > 位移
  转捩点出现在归一化供给余量 (P-elig)/elig ~= -0.15 ~ -0.37, 而非 P > elig。
  详见 supply_state_regimes.py。

【与旧结论的关系】
旧恒等式 S_city = M0 - M <= 0 是**供给状态 A (池被用尽)** 这一分支的结果,
并非普遍规律。本模块分离两条账后, dS_pot 的符号成为可检验命题,
其分界由可测的供给余量决定 (A17 已证实)。
"""
from __future__ import annotations

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

DAYS = cm.N_DAYS
SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
           "Figshare RW (2025, paired study)", "AI-UWM model assumption"]


def potable_flows(dom: str, panel: str, sample: str, phi: float, *,
                  chi: float = 0.5, pool_scale: float = 1.0,
                  gap_scale: float = 1.0, cache: dict | None = None) -> dict:
    """在真实引擎上求 B2(全自来水) 与 B1(掺混 phi) 两个配对情景的自来水流量.

    全部量取自引擎, 不做任何自造公式。
    """
    bl = cm.BASELINES[dom]
    # B1: 掺混情景
    r1 = cm.city_outcome(dom, panel, sample, pool_scale=pool_scale,
                         gap_scale=gap_scale, dp_scale=0.0, ai_target=phi,
                         limit_scale=chi, cache=cache)
    # B2: 全自来水 (phi=0)
    r0 = cm.city_outcome(dom, panel, sample, pool_scale=pool_scale,
                         gap_scale=gap_scale, dp_scale=0.0, ai_target=0.0,
                         limit_scale=chi, cache=cache)

    M1, M0 = r1["M_ml"], r0["M_ml"]
    phi1 = r1["phi_eff"]
    x_ai = r1["x_ai_ml"]                    # AI 分到的再生水
    inc_recl = r1["inc_reclaimed_ml"]       # 既有用户分到的再生水
    pool = r1["pool_ml"]

    # AI 自来水取用: 补水 M 中非再生水的部分
    Wpot_ai_B1 = (1.0 - phi1) * M1
    Wpot_ai_B2 = M0                          # phi=0 时全部为自来水

    # 释放量: AI 少取的自来水
    F = Wpot_ai_B2 - Wpot_ai_B1

    # 索取量: 既有用户在 B1 相对 B2 少拿的再生水 (必须用 B2 基准, 不能用 pool)
    #   dp=0 时 r0["inc_reclaimed_ml"] == pool, 故与 pool-inc_recl 等价;
    #   dp>0 时总预算为 pool+dp, 必须用 B2 的 inc_reclaimed_ml 作基准。
    C = max(0.0, r0["inc_reclaimed_ml"] - inc_recl)

    dS_pot = C - F                           # 城市自来水取水净变化
    return {
        "domain": dom, "sample": sample, "phi": float(phi), "chi": float(chi),
        "M0_ml": M0, "M1_ml": M1, "phi_eff": phi1,
        "Wpot_ai_B2_ml": Wpot_ai_B2, "Wpot_ai_B1_ml": Wpot_ai_B1,
        "F_released_ml": F, "C_claimed_ml": C, "dS_pot_ml": dS_pot,
        "x_ai_ml": x_ai, "inc_recl_ml": inc_recl, "pool_ml": pool,
        "S_algebra_ml": r1["S_city_ml"],
        "CoC_ai": r1["CoC_ai"],
        "status": r1["status"],
    }


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 76)
    rec("A13c 修正后机制: 城市自来水取水的两个相反流向")
    rec("=" * 76)

    cache: dict = {}
    rows = []
    for dom in ("ha", "co"):
        for smp in SAMPLES:
            for chi in (1.0, 0.5, 0.25):
                for phi in np.round(np.arange(0.0, 0.81, 0.05), 2):
                    try:
                        rows.append(potable_flows(dom, "B_full", smp, float(phi),
                                                  chi=chi, cache=cache))
                    except Exception as e:  # noqa: BLE001
                        rec(f"  ERROR {dom} {smp} phi={phi} chi={chi}: {e}")
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "potable_flows.csv", index=False, encoding="utf-8-sig")
    rec(f"\n完成 {len(d)} 情景")

    # ---------- 1. 守恒核验: dp=0 时 F 与 C 的关系 ----------
    rec("\n[1] 检验: dp=0 固定池下, 释放量 F 与索取量 C 是否精确相等")
    d["diff"] = d["F_released_ml"] - d["C_claimed_ml"]
    rel = d["diff"].abs() / d["pool_ml"].clip(lower=1)
    rec(f"  |F - C| 最大绝对值 = {d['diff'].abs().max():.3e} ML")
    rec(f"  相对池的最大偏差 = {rel.max():.3e}")
    exact = bool(rel.max() < 1e-9)
    rec(f"  >> F == C 精确成立 = {exact}")

    if exact:
        rec("  >> 结论: dp=0 固定池下, AI 释放的自来水恰好等于既有用户补回量,")
        rec("     故 dS_pot == 0 —— 城市自来水取水【完全不变】。")
        rec("     这条守恒律是旧恒等式的正确版本 (不涉及 psi/Delta)。")

    # ---------- 2. dS_pot 是否恒为 0 ----------
    nz = d[d["dS_pot_ml"].abs() > 1e-6]
    rec(f"\n[2] dS_pot != 0 的情景数 = {len(nz)}/{len(d)}")
    if len(nz):
        rec(f"  非零情景的最大 dS_pot = {d['dS_pot_ml'].abs().max():.3f} ML")
        rec("  归因: 见下面的 CoC 与 phi_eff 列")

    # ---------- 3. 真正的可证伪机制: 质量惩罚使 F 与 C 不等 ----------
    rec("\n[3] 质量通道如何破坏守恒 (这才是真正的机制入口)")
    rec("  M 随 phi 上升 => B2 与 B1 的 M 不同 => F 与 C 的口径需careful")
    sub = d[(d["domain"] == "ha") & (d["sample"] == SAMPLES[0]) &
            np.isclose(d["chi"], 0.5)].sort_values("phi")
    rec(sub[["phi", "M1_ml", "Wpot_ai_B1_ml", "F_released_ml",
             "C_claimed_ml", "dS_pot_ml", "CoC_ai"]].round(1).to_string(index=False))

    summary = {
        "n_scenarios": int(len(d)),
        "F_equals_C_exact": exact,
        "max_abs_F_minus_C_ml": float(d["diff"].abs().max()),
        "max_rel_F_minus_C": float(rel.max()),
        "n_dS_nonzero": int(len(nz)),
        "max_abs_dS_pot_ml": float(d["dS_pot_ml"].abs().max()),
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "本模块只使用引擎直接给出的量 (M, phi_eff, x_ai, inc_recl, pool), "
            "不引入任何自造的 psi/Delta。dS_pot = C - F 是城市自来水取水的净变化, "
            "与 S_city (代数账) 是两条不同的账, 不合并。"),
    }
    (HERE / "potable_flows_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    rec(f"\n完成, {summary['runtime_s']}s")
    (HERE / "a13c_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
