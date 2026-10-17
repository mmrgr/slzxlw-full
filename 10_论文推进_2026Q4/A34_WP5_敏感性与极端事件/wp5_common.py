"""WP5 共享口径模块 —— 主估计量 dS_pot 与全局敏感性/极端事件复用的公共代码.

======================================================================
【主估计量 —— 唯一口径, 来自 WP2 §2 (B1 − B2), 不得混入 B0】
======================================================================
    dS_pot = C - F = max(0, inc_B2 - inc_B1) - [ (M0 - M1) + x_ai ]

    B1 = 有数据中心, **不用**再生水 (ai_target=0)     -> M0, inc_B1, CoC0
    B2 = 有数据中心, **使用**再生水 (ai_target=phi)   -> M1, inc_B2, CoC1, x_ai
    C  = max(0, inc_B2 - inc_B1)  既有用户被挤占后须补回量
    F  = (M0 - M1) + x_ai         数据中心净索取

符号约定 (WP2 §2 纪律 2):
    dS_pot > 0  => 城市净取水【上升】(有害)
    dS_pot < 0  => 城市净取水【下降】(有益)

`max(0, .)` 的必要性: 池在 B1 被既有用户用尽时带符号位移恒等于 -x_ai, 若直接取负值
则 dS 会重复扣减 x_ai (双计)。见 A33/WP4 §(c) 与 A13/COLUMN_NAMES_CORRECTED.md。

【与 WP4 的差异 (刻意为之, 非口径漂移)】
WP4 在"固定池"口径下扫描 (pool = P0·pool_scale, gap = gap_0)。
本模块在"城市水量会计恒等式"口径下求解:
    S_AI  = (M0 - M) + x_ai
    S_city = S_AI + inc_recl - pool
    dS_pot = S_city(B2) - S_city(B1)
⇒ dS_pot 成为 pool / gap / 需求 / 化学 / 技术的显式函数, 才有可做敏感性分析的控制量。
两口径在 pool=P0, gap=gap_0 处的关系为 dS_pot(WP5) = dS_pot(WP4) - P0 + x_ai,
见 WP5_报告.md §1.2 的口径对照表 (已实测核验)。

【门禁 (双门禁 + 纪律)】
  ① B2 支路 status == "converged_unique"
  ② B1 支路 单根且闭合 (roots==1 且 |closure_residual| <= 1e-9, M0 > 0)
  ③ 两支路 CoC 均不触引擎下限 (CoC > 1.000001)
  任一门禁不通过或出现 NaN/缺列 => 该情景标 NOT_IDENTIFIABLE, **不计入 PASS**。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # 10_论文推进_2026Q4
A10 = ROOT / "A10_敏感性与边界"
if str(A10) not in sys.path:
    sys.path.insert(0, str(A10))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import city_model as cm  # noqa: E402

PANEL = "B_full"                        # 5 物种引用档 (GB/T 50050-2017), 见 A27
DOMS = ("ha", "co")
COC_FLOOR = 1.000001
ZERO_ABS = 1e-6                         # 符号计数零值约定: |dS| < 1e-6 ML 记为 0
REL_TOL = 1e-9

# 主口径水样: 必须经 load_samples() 权威确认 COMPLETE 后填入 (见 load_primary_samples)
SAMPLE_IEUA = "IEUA RP-1 (2025, tertiary)"
SAMPLE_LADWP = "LADWP AWPF (2012, RO product)"
BANNED = ("Figshare BW",)               # 苦咸水非再生水, 见任务书硬约束

CORE = tuple(cm.PANELS[PANEL].keys())   # TDS/chloride/hardness/alkalinity/silica


# ---------------------------------------------------------------- 水样
def load_primary_samples() -> tuple[pd.DataFrame, dict[str, dict], list[str], list[str]]:
    """权威水样读取 (唯一来源 city_model.load_samples(), 不自造任何化学数值).

    返回 (samples_df, q_by_name, primary_names, banned_names)。
    primary = 面板 5 个约束物种**全部非缺失**的水样。
    """
    samples = cm.load_samples()
    q_by, primary, banned = {}, [], []
    for _, row in samples.iterrows():
        name = str(row["source"])
        if any(b in name for b in BANNED):
            banned.append(name)
            continue
        q = {sp: float(row[sp]) for sp in CORE
             if sp in row.index and pd.notna(row.get(sp))}
        q_by[name] = q
        if len(q) == len(CORE):
            primary.append(name)
    return samples, q_by, primary, banned


def q_scaled(q: dict[str, float], chem: dict[str, float]) -> dict[str, float]:
    """按外部倍率构造水样化学 (敏感性分析的化学控制量).

    chem 键为 'x_TDS' 或裸 'TDS'。倍率 1.0 => 完全等于权威水样值。
    """
    out = {}
    for sp, v in q.items():
        k = chem.get(f"x_{sp}", chem.get(sp, 1.0))
        out[sp] = float(v) * float(k)
    return out


# ---------------------------------------------------------------- 求解
def make_bl(dom: str, *, pool_ml: float, gap_ml: float, e_total_ml: float,
            date_rep=None, drivers_rep: dict | None = None) -> dict:
    """构造一个窗口基座 (全年窗口 = 冻结基座)."""
    bl = dict(cm.BASELINES[dom])
    bl["P0"] = float(pool_ml)
    bl["gap"] = float(gap_ml)
    bl["E_total"] = float(e_total_ml)
    if date_rep is not None:
        bl["date_rep"] = pd.Timestamp(date_rep)
    if drivers_rep is not None:
        bl["drivers_rep"] = dict(drivers_rep)
    return bl


def solve_dS(dom: str, sample: str, q: dict, *, phi: float, pool_ml: float,
             gap_ml: float, e_total_ml: float, dp_ml: float = 0.0,
             coc_design: float = cm.COC_DESIGN_DEFAULT, limit_scale: float = 1.0,
             cooling_tech: str | None = None, wet_fraction: float | None = None,
             period_days: float = cm.N_DAYS, date_rep=None,
             drivers_rep: dict | None = None, cache: dict | None = None,
             q_probe: dict | None = None) -> dict:
    """求 B1/B2 两支路并返回主估计量全部构成量 (含门禁字段).

    ⚠ 每次调用默认使用独立 cache —— 与 WP4 同一纪律, 彻底排除 M5(缓存键缺 q)
      历史缺陷复发。`q_probe` 仅用于 cache 键自检。
    """
    cache = {} if cache is None else cache
    bl = make_bl(dom, pool_ml=pool_ml, gap_ml=gap_ml, e_total_ml=e_total_ml,
                 date_rep=date_rep, drivers_rep=drivers_rep)
    kw = dict(coc_design=float(coc_design), limit_scale=float(limit_scale),
              cooling_tech=cooling_tech, wet_fraction=wet_fraction)
    kw_m0 = dict(kw, e_scale=1.0)
    kw_solve = dict(kw, period_days=float(period_days))
    # dp: 专用增量产能 -> 池 + dp (与 city_model.solve_city 的既有约定一致)
    m0 = cm.m0_of(bl, PANEL, q, **kw_m0)
    r2 = cm.solve_city(bl, PANEL, sample, q, m0=m0,
                       pool=pool_ml, gap=gap_ml, dp=dp_ml,
                       ai_target=float(phi), cache=cache, **kw_solve)
    r1 = cm.solve_city(bl, PANEL, sample, q, m0=m0,
                       pool=pool_ml, gap=gap_ml, dp=dp_ml,
                       ai_target=0.0, cache=cache, **kw_solve)

    M0, M1 = float(r1["M_ml"]), float(r2["M_ml"])
    CoC0, CoC1 = float(r1["CoC_ai"]), float(r2["CoC_ai"])
    x_ai = float(r2["x_ai_ml"])
    inc_B1, inc_B2 = float(r1["inc_reclaimed_ml"]), float(r2["inc_reclaimed_ml"])
    displaced_raw = inc_B2 - inc_B1
    C = max(0.0, displaced_raw)
    F = (M0 - M1) + x_ai
    dS = C - F

    den = CoC1 * (CoC0 - 1.0)
    q_chem = ((CoC1 - CoC0) / den) if abs(den) > 1e-300 else float("nan")

    status_B2 = str(r2["status"])
    b1_healthy = bool(int(r1["roots"]) == 1
                      and abs(float(r1["closure_residual_ml"])) <= 1e-9
                      and np.isfinite(M0) and M0 > 0)
    degenerate = bool(min(CoC0, CoC1) <= COC_FLOOR + 1e-12)
    converged_unique = status_B2 == "converged_unique"
    finite = bool(np.isfinite(dS) and np.isfinite(M0) and np.isfinite(M1)
                  and np.isfinite(x_ai) and np.isfinite(C) and np.isfinite(F))
    reliable = bool(converged_unique and b1_healthy and not degenerate and finite)

    return {
        "domain": dom, "sample": sample, "phi": float(phi),
        "M0_ml": M0, "M1_ml": M1, "CoC0": CoC0, "CoC1": CoC1,
        "inc_B1_ml": inc_B1, "inc_B2_ml": inc_B2, "displaced_raw_ml": displaced_raw,
        "C_ml": C, "F_ml": F, "x_ai_ml": x_ai,
        "S_AI_B2_ml": (M0 - M1) + x_ai, "S_city_B2_ml": ((M0 - M1) + x_ai) + inc_B2 - pool_ml,
        "S_city_B1_ml": (M0 - M0) + inc_B1 - pool_ml,
        "dS_pot_ml": dS, "q": q_chem,
        "status_B2": status_B2, "status_B1": str(r1["status"]),
        "roots_B1": int(r1["roots"]), "roots_B2": int(r2["roots"]),
        "closure_residual_B1_ml": float(r1["closure_residual_ml"]),
        "closure_residual_B2_ml": float(r2["closure_residual_ml"]),
        "b1_healthy": b1_healthy, "converged_unique": converged_unique,
        "coc_floor_degenerate": degenerate, "finite": finite,
        "reliable": reliable,
        "period_days": float(period_days), "e_total_ml": float(e_total_ml),
        "pool_ml": float(pool_ml), "gap_ml": float(gap_ml), "dp_ml": float(dp_ml),
        "coc_design": float(coc_design), "limit_scale": float(limit_scale),
        "cooling_tech": str(cooling_tech), "wet_fraction": wet_fraction,
    }


def gate_reason(r: dict) -> str:
    """不可靠情景的显式原因串; 可靠则返回空串。"""
    if r["reliable"]:
        return ""
    why = []
    if not r["converged_unique"]:
        why.append("B2_NOT_CONVERGED_UNIQUE:" + str(r["status_B2"]))
    if not r["b1_healthy"]:
        why.append("B1_UNHEALTHY")
    if r["coc_floor_degenerate"]:
        why.append("COC_FLOOR_DEGENERATE")
    if not r["finite"]:
        why.append("NON_FINITE")
    return "+".join(why)


# ---------------------------------------------------------------- 统计工具
def rel_resid(pred, obs) -> float:
    """相对残差 (量级可达 1e4-1e5 ML, 绝对容差无意义)。"""
    pred, obs = np.asarray(pred, float), np.asarray(obs, float)
    scale = np.maximum(np.abs(obs), 1e-30)
    return float(np.max(np.abs(pred - obs) / scale)) if pred.size else float("nan")


def sign_of(v: float, zero_abs: float = ZERO_ABS) -> int:
    """符号计数约定: |v| < zero_abs 记为 0 (不计入正/负)。"""
    if not np.isfinite(v):
        return 0
    return int(np.sign(v)) if abs(v) >= zero_abs else 0
