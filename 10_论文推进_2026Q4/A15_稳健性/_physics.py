"""A15 稳健性: 修正后的物理层 (基于 A13c 撤回声明).

⚠ 为什么需要这个模块
--------------------
task-4 最初的三份脚本 (ablation / holdout / boundary_stress) 建立在
A13 `reliability_model` 的 `S_city = S_algebra - lam*Delta`,
`Delta = W*max(0, psi-1)` 上。该式已于 2026-10-14 晚被 Lead 自审**撤回**
(见 `A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md`), 三处实质错误:
  A (范畴错误): D 取自 `gap` = 既有用户【未满足的再生水需求】, 不是自来水需求
  B (重复计数): W_AI,pot 与被挤占用户的自来水回流被分别计入同一股水流
  C (量纲错误): 把【城市取水量】(ML) 与【未满足需求缺口】(ML) 相减

本模块改用 A13c 的**物理合法**口径, 只使用引擎直接给出的量:

    B2 基准 (phi=0, 全自来水)  vs  B1 情景 (掺混 phi)
    释放量  F = W_pot(B2) - W_pot(B1) = M0 - (1-phi_eff)*M1
    索取量  C = inc_recl(B2) - inc_recl(B1)        [必须用 B2 基准, 不是固定 pool]
    城市自来水取水净变化  dS_pot = C - F

已独立复核 (本目录 `_probe` 系列 + A13c): dS_pot ≡ M1 - M0, 残差 ~3e-12。

**两条账不得合并** (项目纪律: 指标 A/B/C 不得合并):
    dS_pot  : 城市**自来水取水**净变化 (供给侧账)
    S_city  : 引擎的代数账 (= M0 - M <= 0, 份额口径)
它们是不同的量, 本模块分别报出, 绝不相加。

术语 (与 LEAD_RULING_two_regimes.md §3 一致)
    份额口径 (share-only)      : dp_scale = 0, available = pool
    含容量扩张口径 (capacity)  : dp_scale > 0, available = pool*(1+dp_scale)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import _common as C  # noqa: E402
import city_model as cm  # noqa: E402

LAM = 1.0


def potable_flows(dom: str, panel: str, sample: str, phi: float, *,
                  chi: float = 0.5, dp_scale: float = 0.0,
                  pool_scale: float = 1.0, gap_scale: float = 1.0,
                  cache: dict | None = None) -> dict:
    """修正后的机制核心: 城市自来水取水的两个相反流向.

    全部量取自引擎; 不自造任何 psi / Delta。
    B2 基准必须与情景同口径求值 (dp_scale 相同), 否则 dp>0 时基准失真
    (撤回声明 §6 教训 3)。
    """
    kw = dict(pool_scale=pool_scale, gap_scale=gap_scale, dp_scale=dp_scale,
              limit_scale=chi, cache=cache)
    r1 = cm.city_outcome(dom, panel, sample, ai_target=float(phi), **kw)
    r0 = cm.city_outcome(dom, panel, sample, ai_target=0.0, **kw)

    M1, M0 = float(r1["M_ml"]), float(r0["M_ml"])
    phi_eff = float(r1["phi_eff"])
    # AI 自来水取用: 补水中的非再生水部分
    Wpot_B1 = (1.0 - phi_eff) * M1
    Wpot_B2 = M0                      # phi=0 -> 全部为自来水
    F = Wpot_B2 - Wpot_B1             # 释放量: AI 少取的自来水
    # 索取量: 既有用户在情景中少拿的再生水, 以 B2 为基准 (不能用固定 pool)
    C_claim = max(0.0, float(r0["inc_reclaimed_ml"]) - float(r1["inc_reclaimed_ml"]))
    dS = C_claim - F

    return {
        "domain": dom, "panel": panel, "sample": sample, "phi": float(phi),
        "chi": float(chi), "dp_scale": float(dp_scale),
        "M0_ml": M0, "M1_ml": M1, "phi_eff": phi_eff,
        "Wpot_B2_ml": Wpot_B2, "Wpot_B1_ml": Wpot_B1,
        "F_released_ml": float(F), "C_claimed_ml": float(C_claim),
        "dS_pot_ml": float(dS),
        "identity_resid_ml": float(dS - (M1 - M0)),   # 恒等式核验
        # 引擎代数账 (不同于 dS_pot, 不合并)
        "S_city_algebra_ml": float(r1["S_city_ml"]),
        "S_city_B2_ml": float(r0["S_city_ml"]),
        "x_ai_ml": float(r1["x_ai_ml"]),
        "inc_recl_ml": float(r1["inc_reclaimed_ml"]),
        "pool_ml": float(r1["pool_ml"]),
        "CoC_ai": float(r1["CoC_ai"]),
        "status": str(r1["status"]),
    }


def s_city_share_only(dom, panel, sample, phi, *, chi=0.5, cache=None) -> float:
    """份额口径 (dp=0) 下的引擎代数账 S_city, 供先验敏感性直接使用."""
    return cm.city_outcome(dom, panel, sample, pool_scale=1.0, gap_scale=1.0,
                           dp_scale=0.0, ai_target=float(phi),
                           limit_scale=chi, cache=cache)["S_city_ml"]


def identity_ok(df) -> tuple[bool, float]:
    """核验 dS_pot ≡ M1 - M0 (撤回声明 §2.2 的实测恒等式)."""
    r = float(np.abs(df["identity_resid_ml"]).max())
    return bool(r < 1e-6), r
