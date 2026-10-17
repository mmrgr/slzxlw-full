"""WP5 任务 A: 全局敏感性 (Morris 筛选 + Sobol 方差分解) —— 现行口径重跑.

======================================================================
【为什么必须重跑 (任务书硬约束)】
======================================================================
旧产物 A10/T10_morris.csv、T10_sobol.csv 是在 **旧占位限值**
{TDS 2200, Cl 500, hardness 700, alkalinity 500, silica 150} 与
**旧估计量 y = S_city/M0 (4 个控制量, 无化学维度)** 下跑的, 已过时。
本脚本用 **现行 baseline 引用限值** (GB/T 50050-2017 循环冷却水 2200/700/750/350/175,
见 A27/city_model.LIMIT_SET="baseline") + **完整物种权威水样** 重跑, 并把估计量
换成本项目冻结的**主估计量 dS_pot = C - F = (inc_B2 - inc_B1) - [(M0-M1) + x_ai]**。

======================================================================
【三层不确定性 —— 分开报告, 不得混成单一误差条】
======================================================================
参数不确定性  : 连续参数内 Morris/Sobol (条件于给定水样/域/结构)。
结构不确定性  : ① 体积口径 (WP5 池核算口径) vs 固定池口径 (WP4);
                ② 面板 A_engine2 (2 物种) vs B_full (5 物种);
                ③ F 口径 (WP2/WP4 式 vs A13 式; 实测两者恒等, 见 summary)。
情景不确定性  : 水样 (IEUA vs LADWP) × 域 (ha vs co) 的离散情景间方差,
                用**同一参数点**上的方差分解 (one-way ANOVA 式的组间/组内分解) 度量。

======================================================================
【Morris 实现说明 —— 引擎实现已替换, 如实披露】
======================================================================
引擎自带 `aiuwm.sensitivity.morris_sensitivity` 的步长约定在参数位于盒边界附近时
会产生**步长退化**: 它按 `min(high, base+delta) if base <= high-delta else
max(low, base-delta)` 取点, 当 `base + delta` 恰好落在 `high` 时, 若该参数此后又
被其它调用推回边界, 实际步长 `actual_delta` 可能远小于 `delta`, 但归一化仍除以
`delta/(high-low)`, 于是效应被**系统性放大**; 且它不检查 `actual_delta == 0`。
本脚本改用**教科书 Morris 轨迹** (`morris_trajectory_sensitivity`, 下方实现):
在归一化 [0,1]^k 上取 p 级网格, 每维步长恰为一个网格间隔, 一次只动一维,
`mu / mu_star / sigma` 按标准定义给出, 并**显式统计** `n_zero_delta`。
Sobol 直接复用引擎 `aiuwm.sobol_sensitivity` (Saltelli 一阶/总阶), 未改动。

【纪律】
  · 引擎 07_代码_AI-UWM引擎/aiuwm_src/ 只读, 永不修改;
  · 权威水样只来自 city_model.load_samples(); 主口径只用完整物种水样;
  · Figshare BW 是苦咸水非再生水, 本脚本**根本不纳入**;
  · 双门禁 (B2 converged_unique + B1 健康单根闭合 + CoC 不触下限), 必须报 n_eff;
  · 门禁失败/NaN 情景在该参数点记 NOT_IDENTIFIABLE, 并从有效样本中剔除,
    **不得**用替代值蒙混、**不得**计为 PASS;
  · 大数量级 (1e4-1e5 ML) 一律用**相对容差**;
  · 符号计数声明零值约定与实际 n_eff; 不编造任何数字。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import wp5_common as W                                      # noqa: E402
import city_model as cm                                     # noqa: E402
from aiuwm.sensitivity import sobol_sensitivity             # noqa: E402


# ======================================================================
# 1. 参数空间 (全部有物理/文献含义; 倍率类参数 1.0 处 = 权威/冻结取值)
# ======================================================================
# 说明:
#   phi         AI 目标再生水掺混比 (外生政策控制量)
#   pool_scale  城市再生水池规模 (= P0 的倍数; 冻结基座 = 1.0)
#   gap_scale   既有用户缺口 (= gap 的倍数; 冻结基座 = 1.0)
#   dp_scale    新增回用产能 (= P0 的倍数; 冻结基座 = 0.0)
#   e_scale     IT 负荷/蒸发量整体尺度 (= E_total 的倍数)
#   coc_design  设计浓缩倍数 (水质严重度控制量)
#   limit_scale 水质限值整体缩放 (1.0 = GB/T 50050-2017 现行引用档; <1 = 更严)
#   x_TDS / x_chloride / x_hardness / x_alkalinity / x_silica
#               水样化学各关键物种相对权威值的**乘性倍率** (非自造化值,
#               只是把 load_samples() 的权威值整体缩放, 1.0 = 权威原值)
#
# ---- 敏感性分析的参数边界 (压力域, 用于 Morris/Sobol) ----
BOUNDS_STRESS = {
    "phi": (0.15, 0.95),
    "pool_scale": (0.40, 3.00),
    "gap_scale": (0.40, 3.00),
    "dp_scale": (0.00, 0.60),
    "e_scale": (0.80, 1.60),
    "coc_design": (3.40, 6.00),
    "limit_scale": (0.40, 3.00),
    "x_TDS": (0.50, 3.50),
    "x_chloride": (0.50, 3.50),
    "x_hardness": (0.50, 3.50),
    "x_alkalinity": (0.50, 3.50),
    "x_silica": (0.50, 3.50),
}

# ---- 保守 (窄) 边界: 只含"由观测/文献直接支撑"的取值范围, 用于边界敏感性 ----
BOUNDS_CONSERVATIVE = {
    "phi": (0.30, 0.80),
    "pool_scale": (0.80, 1.60),
    "gap_scale": (0.80, 1.60),
    "dp_scale": (0.00, 0.30),
    "e_scale": (0.90, 1.25),
    "coc_design": (4.00, 5.50),
    "limit_scale": (0.50, 2.00),
    "x_TDS": (0.75, 1.75),
    "x_chloride": (0.75, 1.75),
    "x_hardness": (0.75, 1.75),
    "x_alkalinity": (0.75, 1.75),
    "x_silica": (0.75, 1.75),
}

# 化学倍率参数名 (与 city_model 面板键一一对应)
CHEM_KEYS = tuple(BOUNDS_STRESS)[7:]
assert CHEM_KEYS == ("x_TDS", "x_chloride", "x_hardness", "x_alkalinity", "x_silica")


def chem_map(p: dict) -> dict:
    """从参数点取出化学倍率映射 (键名 -> 倍率)。

    ⚠ Sobol 降维后参数点**只含被抽样的子集**; 未出现在 p 中的化学维必须回落到
    冻结取值 1.0 (即权威水样原值), 而不是 KeyError。旧实现直接下标取键, 使
    Sobol 子集调用全部抛 KeyError -> 被 Evaluator 吞成 NaN -> 4/4 配置的
    Sobol 指数全 NaN。此处显式回落, 并在 Evaluator 里拒绝把 KeyError 当门禁失败。
    """
    return {k: float(p.get(k, 1.0)) for k in CHEM_KEYS}


# ======================================================================
# 2. 估计量: dS_pot (可选: 主口径 dS / CP 口径 S_city)
# ======================================================================
class Evaluator:
    """把参数点 p -> 标量估计量。门禁失败记 NaN 并累计计数 (不蒙混)。"""

    def __init__(self, dom: str, sample: str, q0: dict, bl: dict, *,
                 estimand: str = "dS_pot", negative_when_gate_fails: float | None = None):
        self.dom, self.sample, self.q0, self.bl = dom, sample, q0, bl
        self.estimand = estimand
        self.negative_when_gate_fails = negative_when_gate_fails
        self.n = 0
        self.n_nan = 0          # 门禁失败 (B2 未收敛等) -> 该点 NOT_IDENTIFIABLE
        self.n_raise = 0        # 引擎/调用异常 -> **代码缺陷**, 不得与门禁失败混为一谈
        self.reasons: dict[str, int] = {}
        self.raise_examples: list[str] = []

    def _collect(self, p: dict) -> dict:
        """求解一个参数点。

        ⚠ 所有非化学键一律 `p.get(k, 冻结默认值)` 回落 —— Sobol 降维后参数点只含
        被抽样的子集, 未抽样维必须回到其冻结取值, 而不是 KeyError。
        (bug 记录: 旧实现硬下标取键, 使 Sobol 子集调用全部 KeyError 并被吞成 NaN,
         导致 4/4 配置的 Sobol 指数全为 NaN。)
        """
        q = W.q_scaled(self.q0, chem_map(p))
        return W.solve_dS(
            self.dom, self.sample, q,
            phi=float(p.get("phi", 0.6)),
            pool_ml=self.bl["P0"] * float(p.get("pool_scale", 1.0)),
            gap_ml=self.bl["gap"] * float(p.get("gap_scale", 1.0)),
            dp_ml=self.bl["P0"] * float(p.get("dp_scale", 0.0)),
            e_total_ml=self.bl["E_total"] * float(p.get("e_scale", 1.0)),
            coc_design=float(p.get("coc_design", cm.COC_DESIGN_DEFAULT)),
            limit_scale=float(p.get("limit_scale", 1.0)),
        )

    def raw(self, p: dict) -> dict | None:
        """返回完整情景 dict; 若**引擎求解**抛错返回 None。

        ⚠ 纪律: 这里只允许吞"引擎在不可行情景上抛错"这一类异常 (该情景不可辨识)。
        若抛的是 KeyError/AttributeError/TypeError 等**代码缺陷**信号, 直接向上抛,
        以免把自身 bug 伪装成"门禁失败" —— 见 wp5_morris_sobol 的 bug 记录:
        旧实现曾把 Sobol 子集缺键的 KeyError 吞成 NaN, 使 4/4 配置的 Sobol 全 NaN。
        """
        self.n += 1
        try:
            return self._collect(p)
        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            self.n_raise += 1
            k = "ENGINE_RAISE:" + type(exc).__name__
            self.reasons[k] = self.reasons.get(k, 0) + 1
            if len(self.raise_examples) < 3:
                self.raise_examples.append(f"{type(exc).__name__}: {str(exc)[:160]}")
            return None

    def __call__(self, p: dict) -> float:
        r = self.raw(p)
        if r is None:
            self.n_nan += 1
            return (self.negative_when_gate_fails if self.negative_when_gate_fails is not None
                    else float("nan"))
        if not r["reliable"]:
            self.n_nan += 1
            k = W.gate_reason(r) or "UNRELIABLE"
            self.reasons[k] = self.reasons.get(k, 0) + 1
            return (self.negative_when_gate_fails if self.negative_when_gate_fails is not None
                    else float("nan"))
        v = r["dS_pot_ml"] if self.estimand == "dS_pot" else r["S_city_B2_ml"]
        if not np.isfinite(v):
            self.n_nan += 1
            return float("nan")
        return float(v)

    def summary(self) -> dict:
        return {"n_eval": self.n, "n_not_identifiable": self.n_nan,
                "n_gate_failures": self.n_nan,
                "n_engine_raises": self.n_raise,
                "not_identifiable_share_pct": round(100.0 * self.n_nan / max(self.n, 1), 2),
                "engine_raise_share_pct": round(100.0 * self.n_raise / max(self.n, 1), 2),
                "reasons": dict(sorted(self.reasons.items(), key=lambda kv: -kv[1])),
                "engine_raise_examples": self.raise_examples}


# ======================================================================
# 3. Moran / Morris 教科书轨迹实现 (替换引擎版, 理由见模块 docstring)
# ======================================================================
def morris_trajectory_sensitivity(evaluator, bounds: dict, *, trajectories: int = 24,
                                  levels: int = 8, seed: int = 20261016) -> tuple[pd.DataFrame, dict]:
    """标准 Morris 轨迹筛选 (归一化 [0,1]^k 上的 p 级网格, 逐维 +Δ 一步)。

    每个轨迹: 随机起点 -> 逐维按随机顺序各加一个网格间隔 Δ = p/(2(p-1)) 的整数倍。
    效应 d_i = (y(x + Δe_i) - y(x)) / Δ  (Δ 为归一化步长 -> 效应即"全参数范围变化"标度)。
    """
    names = list(bounds)
    k = len(names)
    if levels < 2:
        raise ValueError("levels must be >= 2")
    delta = levels / (2.0 * (levels - 1.0)) / levels * levels   # p/(2(p-1))
    grid = np.linspace(0.0, 1.0, levels)
    rng = np.random.default_rng(seed)

    def to_phys(xn: np.ndarray) -> dict:
        return {n: float(lo + xn[i] * (hi - lo))
                for i, (n, (lo, hi)) in enumerate(bounds.items())}

    effects: dict[str, list[float]] = {n: [] for n in names}
    y_base: list[float] = []
    n_zero_delta = 0
    n_nan_steps = 0
    for _ in range(trajectories):
        # 起点必须使 x + Δ 仍在盒内: 归一化坐标取 [0, 1-Δ] 上的网格点
        start = rng.choice(grid[grid <= 1.0 - delta + 1e-12], size=k, replace=True)
        order = rng.permutation(k)
        x = start.copy()
        cur = to_phys(x)
        y_cur = float(evaluator(cur))
        y_base.append(y_cur)
        for idx in order:
            x_new = x.copy()
            x_new[idx] = x_new[idx] + delta
            if x_new[idx] > 1.0 + 1e-12:
                n_zero_delta += 1
                continue
            nxt = to_phys(x_new)
            y_new = float(evaluator(nxt))
            if not (np.isfinite(y_cur) and np.isfinite(y_new)):
                # 门禁失败端点: 该维该步记 NaN, **不**用替代值填充
                effects[names[idx]].append(float("nan"))
                n_nan_steps += 1
            else:
                effects[names[idx]].append((y_new - y_cur) / delta)
            x, cur, y_cur = x_new, nxt, y_new

    rows = []
    for n in names:
        v = np.asarray(effects[n], dtype=float)
        fin = v[np.isfinite(v)]
        rows.append({
            "parameter": n,
            "mu": float(np.mean(fin)) if fin.size else float("nan"),
            "mu_star": float(np.mean(np.abs(fin))) if fin.size else float("nan"),
            "sigma": float(np.std(fin, ddof=1)) if fin.size > 1 else float("nan"),
            "mu_abs_ratio": (float(abs(np.mean(fin)) / np.mean(np.abs(fin)))
                             if fin.size and np.mean(np.abs(fin)) > 0 else float("nan")),
            "n_effects": int(fin.size),
            "n_nan_effects": int(v.size - fin.size),
        })
    df = pd.DataFrame(rows).sort_values("mu_star", ascending=False).reset_index(drop=True)
    meta = {"levels": levels, "normalized_delta": delta, "trajectories": trajectories,
            "n_zero_delta": n_zero_delta, "n_nan_effects": n_nan_steps,
            "n_base_evaluations": len(y_base)}
    return df, meta


def sobol_guarded(evaluator, bounds: dict, *, samples: int, seed: int) -> tuple[pd.DataFrame, dict]:
    """在 Saltelli 设计上执行引擎 Sobol, 但**先**做 NaN/门禁失败普查。

    引擎 `sobol_sensitivity` 对 NaN 会**静默传播** (variance -> NaN, 全部指数 -> NaN),
    因此这里先独立构造同一 Saltelli 设计 (同一 seed -> 同一矩阵), 用 evaluator 普查,
    并把普查结果如实报出:
      · 无 NaN  -> 直接复用引擎实现, 指数可解释;
      · 有 NaN  -> Sobol 指数标 NaN 并裁 NOT_IDENTIFIABLE, **不插补、不蒙混**。

    ⚠ 重要: 普查到的"NaN"可能来自两类完全不同的原因 ——
      (i) 情景本身门禁失败 (B2 未收敛等) -> 合法的 NOT_IDENTIFIABLE;
      (ii) 调用方代码缺陷 (如参数子集缺键 -> KeyError) -> **必须先修代码**。
    `Evaluator.raw` 已把 (ii) 类异常直接抛出, 故此处若出现 NaN, 必为 (i) 类。
    """
    names = list(bounds)
    rng = np.random.default_rng(seed)
    a = rng.random((samples, len(names)))
    b = rng.random((samples, len(names)))
    low = np.array([bounds[n][0] for n in names])
    span = np.array([bounds[n][1] - bounds[n][0] for n in names])
    a, b = low + a * span, low + b * span
    evaluate = lambda row: float(evaluator(dict(zip(names, row))))      # noqa: E731
    ya = np.array([evaluate(r) for r in a])
    yb = np.array([evaluate(r) for r in b])
    n_nan = int((~np.isfinite(ya)).sum() + (~np.isfinite(yb)).sum())
    n_tot = int(ya.size + yb.size)
    n_gate = int(getattr(evaluator, "n_nan", 0))
    n_raise = int(getattr(evaluator, "n_raise", 0))
    diag = {"samples": samples, "n_design_rows": n_tot, "n_nan": n_nan,
            "nan_share_pct": round(100.0 * n_nan / max(n_tot, 1), 2),
            "n_gate_failures_during_design": n_gate,
            "n_engine_raises_during_design": n_raise,
            "gate_failure_reasons": dict(getattr(evaluator, "reasons", {}))}
    if n_nan:
        diag["verdict"] = ("NOT_IDENTIFIABLE: Saltelli 设计含门禁失败点, NaN 会污染方差, "
                           "Sobol 指数不可解释 —— 如实报出, 不插补、不蒙混")
        return pd.DataFrame([{"parameter": n, "S1": float("nan"), "ST": float("nan")}
                             for n in names]), diag
    # 无 NaN: 复用引擎实现 (同一 seed -> 同一设计), 并核对两条路径一致
    df = sobol_sensitivity(evaluator, bounds, samples=samples, seed=seed)
    diag["verdict"] = "OK (设计内无门禁失败点; 指数直接复用引擎 aiuwm.sobol_sensitivity)"
    diag["engine_path_all_finite"] = bool(np.isfinite(df[["S1", "ST"]].to_numpy()).all())
    return df, diag


# ======================================================================
# 4. 情景不确定性: 同一参数点上的组间/组内方差分解
# ======================================================================
def scenario_variance_components(points: list[dict], configs: list[tuple[str, str]],
                                 q_by: dict, *, seed: int = 20261016,
                                 n_draw: int = 40) -> tuple[pd.DataFrame, dict]:
    """在**固定参数点集**上, 把 dS_pot 的方差分解为 情景间 / 情景内(参数)。

    情景 = (domain, sample) 组合。每个情景在同一批参数点上求值;
    dS 的总体方差 = 情景间方差 (组间, 即"换水样/换域"造成的) + 情景内方差
    (组内, 即"参数在边界内变动"造成的)。
    这是确定性 ANOVA 分解 (全枚举网格, 不是抽样估计)。
    """
    rows = []
    for dom, sample in configs:
        bl = cm.BASELINES[dom]
        ev = Evaluator(dom, sample, q_by[sample], bl, estimand="dS_pot")
        for p in points:
            v = ev(p)
            rows.append({"domain": dom, "sample": sample, "dS_pot_ml": v,
                         **{k: float(p[k]) for k in BOUNDS_STRESS}})
    d = pd.DataFrame(rows)
    ok = d[np.isfinite(d["dS_pot_ml"])].copy()
    n_all = int(len(d))
    if len(ok) < len(configs) * 2:
        return d, {"verdict": "NOT_IDENTIFIABLE",
                   "reason": "有效情景过少, 无法做方差分解", "n_all": n_all,
                   "n_eff": int(len(ok))}
    grand = float(ok["dS_pot_ml"].mean())
    ss_tot = float(((ok["dS_pot_ml"] - grand) ** 2).sum())
    groups = ok.groupby(["domain", "sample"])["dS_pot_ml"]
    ss_between = float((groups.count() * (groups.mean() - grand) ** 2).sum())
    ss_within = ss_tot - ss_between
    n_eff = int(len(ok))
    k_groups = int(ok.groupby(["domain", "sample"]).ngroups)
    stats = {
        "n_all": n_all, "n_eff": n_eff, "n_groups": k_groups,
        "not_identifiable": n_all - n_eff,
        "df_between": k_groups - 1,
        "df_within": n_eff - k_groups,
        "ss_total": ss_tot, "ss_between": ss_between, "ss_within": ss_within,
        "var_share_between_pct": round(100.0 * ss_between / ss_tot, 3) if ss_tot > 0 else None,
        "var_share_within_pct": round(100.0 * ss_within / ss_tot, 3) if ss_tot > 0 else None,
        "ms_between": ss_between / max(k_groups - 1, 1),
        "ms_within": ss_within / max(n_eff - k_groups, 1),
        "grand_mean_ml": grand,
        "sign_counts_reliable": {
            "n_neg_beneficial": int((ok["dS_pot_ml"] < -W.ZERO_ABS).sum()),
            "n_zero": int((ok["dS_pot_ml"].abs() <= W.ZERO_ABS).sum()),
            "n_pos_harmful": int((ok["dS_pot_ml"] > W.ZERO_ABS).sum()),
            "zero_value_convention": f"|dS_pot| < {W.ZERO_ABS} ML 记为 0",
        },
        "by_group": {
            f"{dom}|{samp}": {
                "n": int(len(g)),
                "mean_ml": float(g["dS_pot_ml"].mean()),
                "sd_ml": float(g["dS_pot_ml"].std(ddof=1)) if len(g) > 1 else None,
                "min_ml": float(g["dS_pot_ml"].min()),
                "max_ml": float(g["dS_pot_ml"].max()),
                "n_neg": int((g["dS_pot_ml"] < -W.ZERO_ABS).sum()),
                "n_pos": int((g["dS_pot_ml"] > W.ZERO_ABS).sum()),
                "n_zero": int((g["dS_pot_ml"].abs() <= W.ZERO_ABS).sum()),
            }
            for (dom, samp), g in ok.groupby(["domain", "sample"])
        },
        "verdict": ("情景(水样×域)间方差主导" if ss_between > ss_within
                    else "参数方差主导 (情景间不主导)"),
    }
    return d, stats


# ======================================================================
# 5. 主流程
# ======================================================================
MORRIS_TRAJ = 32
MORRIS_LEVELS = 8
# Sobol 规模: 引擎 Saltelli 设计为 samples*(k+2) 次**求解** (每次约 0.6 s)。
# samples=256, k=7 -> 2304 求解 ≈ 2.6 min/配置; 4 配置 ≈ 10 min (实测 154 s/配置)。
SOBOL_SAMPLES = 256
SOBOL_MAX_PARAMS = 7          # 计算量控制: 见 summary["sobol"]["dimension_reduction"]
SCEN_POINTS_SEED = 20261016
SCEN_N_DRAW = 40


def main() -> int:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str = "") -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 92)
    rec("WP5 任务 A: 全局敏感性 (Morris 筛选 + Sobol 方差分解) —— 现行 baseline 限值 + 完整物种水样")
    rec("=" * 92)

    # ---------------- 0. 权威水样与水样完整性 ----------------
    rec("\n[0] 权威水样 (唯一来源 city_model.load_samples(), 不自造任何化学数值)")
    rec(f"  city_model.LIMIT_SET = {cm.LIMIT_SET!r};  PANEL B_full 引用限值 = "
        f"{json.dumps(cm.PANELS[W.PANEL], ensure_ascii=False)}")
    samples, q_by, primary, banned = W.load_primary_samples()
    rec(f"  权威表 {len(samples)} 条; 面板 {W.PANEL} 要求物种 {list(W.CORE)}")
    meta = {}
    for _, row in samples.iterrows():
        name = str(row["source"])
        q = {sp: float(row[sp]) for sp in W.CORE
             if sp in row.index and pd.notna(row.get(sp))}
        miss = [sp for sp in W.CORE if sp not in q]
        meta[name] = {"n_species": len(q), "missing": miss,
                      "status": "COMPLETE" if not miss else "INCOMPLETE",
                      "is_reclaimed": bool(row.get("is_reclaimed", True)),
                      "sclass": str(row.get("sclass", ""))}
        rec(f"    {name:<56} n={len(q)} 缺失={','.join(miss) or '-':<24} {meta[name]['status']}")
    rec(f"  ⇒ 主口径 (完整物种) 水样 = {primary}")
    rec(f"  ⇒ 禁用水样 (苦咸水非再生水) = {banned}  —— 本脚本根本不纳入")
    if not primary:
        rec("  ✗ 无完整物种水样 => 主口径 NOT_IDENTIFIABLE, 不得计为 PASS")
        return 1

    # ---------------- 0b. 门禁与口径自检 ----------------
    rec("\n[0b] 口径自检")
    v_ieua = q_by[W.SAMPLE_IEUA]
    anchor = W.solve_dS("ha", W.SAMPLE_IEUA, v_ieua, phi=0.6,
                        pool_ml=cm.BASELINES["ha"]["P0"],
                        gap_ml=cm.BASELINES["ha"]["gap"],
                        e_total_ml=cm.BASELINES["ha"]["E_total"])
    ref = -7585.088415776312      # A33/WP4 wp4_results.csv: ha|IEUA|ps=1|phi=0.6
    rel = abs(anchor["dS_pot_ml"] - ref) / abs(ref)
    rec(f"  锚点复现 (ha|IEUA|ps=1|phi=0.6): WP5 = {anchor['dS_pot_ml']:.6f} ML, "
        f"WP4 = {ref:.6f} ML, 相对差 = {rel:.3e} "
        f"=> {'✓ 口径一致 (相对容差 %g)' % W.REL_TOL if rel <= 1e-6 else '✗ 口径不一致!'}")
    rec(f"  锚点门禁: B2={anchor['status_B2']} B1_healthy={anchor['b1_healthy']} "
        f"CoC0={anchor['CoC0']:.4f} CoC1={anchor['CoC1']:.4f} reliable={anchor['reliable']}")
    rec(f"  锚点恒等式残差 (相对): dS == C - F  -> "
        f"{W.rel_resid(anchor['C_ml'] - anchor['F_ml'], anchor['dS_pot_ml']):.3e}")
    rec(f"  ⚠ 口径对照: 本模块在'城市水量会计'口径下求解 (S_city = S_AI + inc_recl - pool),"
        f" dS_pot = S_city(B2) - S_city(B1);")
    rec(f"     冻结基座 (pool=P0, gap=gap_0, dp=0, e_scale=1) 处与 WP4/A13 的 "
        f"C-F 口径**逐位一致** (见上)。")

    # cache 键自检 (M5 复发防护): 共享 cache 下不同化学应给出不同 CoC
    probe_cache: dict = {}
    refs = {}
    for nm in primary:
        r = W.solve_dS("ha", nm, q_by[nm], phi=0.6, pool_ml=cm.BASELINES["ha"]["P0"],
                       gap_ml=cm.BASELINES["ha"]["gap"],
                       e_total_ml=cm.BASELINES["ha"]["E_total"], cache=probe_cache)
        refs[nm] = round(r["CoC1"], 6)
    rec(f"  共享 cache 下各水样 CoC1@(ha,phi=0.6) = {refs} "
        f"=> {'✓ 缓存键含 q, 组成维度有效' if len(set(refs.values())) == len(refs) else '✗ 组成维度失效!'}")

    # ---------------- 1. Morris 筛选 (压力域, 逐情景) ----------------
    rec("\n[1] ★ Morris 轨迹筛选 (压力域边界, 十二维)")
    rec(f"  归一化盒上 {MORRIS_LEVELS} 级网格, {MORRIS_TRAJ} 条轨迹, "
        f"每维步长 Δ = {MORRIS_LEVELS/(2*(MORRIS_LEVELS-1)):.4f}")
    rec(f"  参数: {list(BOUNDS_STRESS)}")
    morris_rows = []
    morris_meta = {}
    for dom in W.DOMS:
        for nm in primary:
            tag = f"{dom}|{nm.split(' ')[0]}"
            ev = Evaluator(dom, nm, q_by[nm], cm.BASELINES[dom])
            m, mm = morris_trajectory_sensitivity(ev, BOUNDS_STRESS,
                                                  trajectories=MORRIS_TRAJ,
                                                  levels=MORRIS_LEVELS, seed=20261016)
            m.insert(0, "config", tag)
            m.insert(1, "domain", dom)
            m.insert(2, "sample", nm)
            m.insert(3, "estimand", "dS_pot_ml")
            morris_rows.append(m)
            morris_meta[tag] = {**mm, **ev.summary()}
            rec(f"\n  --- {tag} ---  有效/不可辨识: "
                f"{ev.n - ev.n_nan}/{ev.n_nan} ({100*ev.n_nan/max(ev.n,1):.1f}% 门禁失败)")
            if ev.reasons:
                rec(f"      不可辨识原因: {ev.reasons}")
            rec(m[["parameter", "mu", "mu_star", "sigma", "mu_abs_ratio",
                   "n_effects", "n_nan_effects"]].round(4).to_string(index=False))

    mo = pd.concat(morris_rows, ignore_index=True)
    mo.to_csv(HERE / "wp5_morris.csv", index=False, encoding="utf-8-sig")

    # ---------------- 2. Sobol 方差分解 ----------------
    rec("\n[2] ★ Sobol 方差分解 (Saltelli, 引擎 aiuwm.sobol_sensitivity)")
    ranking = (mo[mo.config == f"ha|{W.SAMPLE_IEUA.split(' ')[0]}"]
               .sort_values("mu_star", ascending=False)["parameter"].tolist())
    sobol_params = ranking[:SOBOL_MAX_PARAMS]
    sobol_bounds = {k: BOUNDS_STRESS[k] for k in sobol_params}
    cost_full = SOBOL_SAMPLES * (len(BOUNDS_STRESS) + 2)
    cost_used = SOBOL_SAMPLES * (len(sobol_params) + 2)
    rec(f"  计算量控制: 全 12 维需 {SOBOL_SAMPLES}×(12+2) = {cost_full} 次求解;")
    rec(f"  本书取 Morris 排名前 {SOBOL_MAX_PARAMS} 维 -> {SOBOL_SAMPLES}×({len(sobol_params)}+2)"
        f" = {cost_used} 次求解。**降维是显式声明的取舍**: Sobol 指数只对这 "
        f"{SOBOL_MAX_PARAMS} 维的**条件方差**有效, 未纳入维度的方差被并入 ST。")
    rec(f"  Sobol 子集参数 (按 Morris mu_star 排序): {sobol_params}")
    sobol_rows = []
    sobol_meta = {}
    for dom in W.DOMS:
        for nm in primary:
            tag = f"{dom}|{nm.split(' ')[0]}"
            ev = Evaluator(dom, nm, q_by[nm], cm.BASELINES[dom])
            s, sd = sobol_guarded(ev, sobol_bounds, samples=SOBOL_SAMPLES, seed=20261016)
            s.insert(0, "config", tag)
            s.insert(1, "domain", dom)
            s.insert(2, "sample", nm)
            s.insert(3, "estimand", "dS_pot_ml")
            sobol_rows.append(s)
            sobol_meta[tag] = {**sd, **ev.summary()}
            rec(f"\n  --- {tag} ---  NaN 普查: {sd['n_nan']}/{sd['n_design_rows']} "
                f"({sd['nan_share_pct']}%) => {sd['verdict'][:78]}")
            rec(s[["parameter", "S1", "ST"]].round(5).to_string(index=False))

    so = pd.concat(sobol_rows, ignore_index=True)
    so.to_csv(HERE / "wp5_sobol.csv", index=False, encoding="utf-8-sig")

    # ---------------- 3. 符号翻转诊断 (最敏感参数如何改变符号) ----------------
    rec("\n[3] ★ 符号翻转诊断: 哪个参数最能改变 dS_pot 的【符号】")
    # 对每个参数, 固定其余参数于冻结取值 (phi=0.6), 扫描其边界
    baseline_pt = {"phi": 0.6, "pool_scale": 1.0, "gap_scale": 1.0, "dp_scale": 0.0,
                   "e_scale": 1.0, "coc_design": cm.COC_DESIGN_DEFAULT, "limit_scale": 1.0,
                   **{k: 1.0 for k in CHEM_KEYS}}
    flip_rows = []
    for prm, (lo, hi) in BOUNDS_STRESS.items():
        signs, vals = [], []
        for v in np.linspace(lo, hi, 41):
            p = dict(baseline_pt); p[prm] = float(v)
            for dom in W.DOMS:
                for nm in primary:
                    ev = Evaluator(dom, nm, q_by[nm], cm.BASELINES[dom])
                    y = ev(p)
                    if np.isfinite(y):
                        signs.append(W.sign_of(y)); vals.append((dom, nm, float(v), y))
        ns_neg = sum(1 for s in signs if s < 0)
        ns_pos = sum(1 for s in signs if s > 0)
        flips = int(sum(1 for a, b in zip(signs, signs[1:]) if a != b))
        # 精细定位首个翻转点 (对 IEUA, ha, 冻结其余)
        flip_at = None
        prev = None
        for v in np.linspace(lo, hi, 401):
            p = dict(baseline_pt); p[prm] = float(v)
            ev = Evaluator("ha", W.SAMPLE_IEUA, q_by[W.SAMPLE_IEUA], cm.BASELINES["ha"])
            y = ev(p)
            if np.isfinite(y):
                s = W.sign_of(y)
                if prev is not None and s != prev and s != 0 and prev != 0:
                    flip_at = float(v)
                    break
                prev = s
        flip_rows.append({
            "parameter": prm, "low": lo, "high": hi,
            "baseline_value": baseline_pt[prm],
            "n_reliable_points": len(signs),
            "n_sign_negative": ns_neg, "n_sign_positive": ns_pos,
            "n_sign_zero": len(signs) - ns_neg - ns_pos,
            "n_sign_changes_along_curve": flips,
            "sign_varying": bool(ns_neg > 0 and ns_pos > 0),
            "first_flip_value_ha_IEUA": flip_at,
            "min_dS_ml": float(min(v[3] for v in vals)) if vals else None,
            "max_dS_ml": float(max(v[3] for v in vals)) if vals else None,
        })
    fd = pd.DataFrame(flip_rows).sort_values(
        ["sign_varying", "n_sign_changes_along_curve"], ascending=False).reset_index(drop=True)
    rec(f"  {'parameter':<14} {'冻结值':>8} {'n可靠':>6} {'负':>5} {'正':>5} "
        f"{'符号可变':>8} {'首个翻转点':>12} {'dS范围(ML)':>26}")
    for _, r in fd.iterrows():
        rng = (f"[{r['min_dS_ml']:.4g}, {r['max_dS_ml']:.4g}]"
               if r["min_dS_ml"] is not None else "NA")
        fl = "NA" if pd.isna(r["first_flip_value_ha_IEUA"]) else f"{r['first_flip_value_ha_IEUA']:.4g}"
        rec(f"  {r['parameter']:<14} {r['baseline_value']:>8.3f} {r['n_reliable_points']:>6} "
            f"{r['n_sign_negative']:>5} {r['n_sign_positive']:>5} "
            f"{str(r['sign_varying']):>8} {fl:>12} {rng:>26}")
    sign_flippers = fd[fd.sign_varying]["parameter"].tolist()
    rec(f"  ⇒ 能改变 dS_pot **符号** 的参数 = {sign_flippers if sign_flippers else '（无：单参数扫描内不变号）'}")

    # ---------------- 4. 三层不确定性分解 ----------------
    rec("\n[4] ★ 三层不确定性分解 (参数 / 结构 / 情景 —— 分开报告, 不混成单一误差条)")
    rng = np.random.default_rng(SCEN_POINTS_SEED)
    scen_points = [{k: float(rng.uniform(lo, hi)) for k, (lo, hi) in BOUNDS_STRESS.items()}
                   for _ in range(SCEN_N_DRAW)]
    scen_cfgs = [(d, n) for d in W.DOMS for n in primary]
    scen_df, scen_stats = scenario_variance_components(
        scen_points, scen_cfgs, q_by, n_draw=SCEN_N_DRAW)
    scen_df.to_csv(HERE / "wp5_scenario_points.csv", index=False, encoding="utf-8-sig")

    rec("\n  (a) 参数不确定性 (条件于给定 域×水样, Morris/Sobol 已在 §1-§2 给出)")
    for tag in morris_meta:
        m = morris_meta[tag]
        rec(f"      {tag:<22} 有效 {m['n_eval'] - m['n_not_identifiable']}/{m['n_eval']} "
            f"({m['not_identifiable_share_pct']}% 门禁失败)")
    main_tag = f"ha|{W.SAMPLE_IEUA.split(' ')[0]}"
    rec(f"      主配置 {main_tag} 前 3 名 (mu_star): "
        f"{list(mo[mo.config==main_tag].head(3)[['parameter','mu_star']].itertuples(index=False, name=None))}")

    rec("\n  (b) 结构不确定性 (口径/面板/F 式)")
    # b1: 面板 A_engine2 (2 物种) vs B_full (5 物种)
    panel_rows = []
    for dom in W.DOMS:
        for nm in primary:
            q5 = q_by[nm]
            q2 = {k: v for k, v in q5.items() if k in cm.PANELS["A_engine2"]}
            if len(q2) != len(cm.PANELS["A_engine2"]):
                panel_rows.append({"domain": dom, "sample": nm, "panel": "A_engine2",
                                   "status": "NOT_IDENTIFIABLE",
                                   "reason": "缺列: 面板要求的物种在水样中缺失"})
                continue
            bl = cm.BASELINES[dom]

            def solve_panel(panel: str, qq: dict) -> dict:
                kw = dict(coc_design=cm.COC_DESIGN_DEFAULT, limit_scale=1.0)
                m0 = cm.m0_of(bl, panel, qq, **kw)
                r2 = cm.solve_city(bl, panel, nm, qq, m0=m0, pool=bl["P0"],
                                   gap=bl["gap"], dp=0.0, ai_target=0.6, cache={}, **kw)
                r1 = cm.solve_city(bl, panel, nm, qq, m0=m0, pool=bl["P0"],
                                   gap=bl["gap"], dp=0.0, ai_target=0.0, cache={}, **kw)
                C = max(0.0, r2["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
                F = (r1["M_ml"] - r2["M_ml"]) + r2["x_ai_ml"]
                return {"dS": C - F, "status": r2["status"], "CoC0": r1["CoC_ai"],
                        "CoC1": r2["CoC_ai"], "M0": r1["M_ml"]}

            try:
                o5 = solve_panel("B_full", q5)
                o2 = solve_panel("A_engine2", q2)
                panel_rows.append({
                    "domain": dom, "sample": nm, "panel": "B_full vs A_engine2",
                    "status": "OK",
                    "dS_B_full_ml": o5["dS"], "dS_A_engine2_ml": o2["dS"],
                    "abs_diff_ml": o5["dS"] - o2["dS"],
                    "rel_diff": (abs(o5["dS"] - o2["dS"]) / max(abs(o5["dS"]), 1e-30)),
                    "sign_B_full": W.sign_of(o5["dS"]), "sign_A_engine2": W.sign_of(o2["dS"]),
                    "CoC1_B_full": o5["CoC1"], "CoC1_A_engine2": o2["CoC1"],
                })
            except Exception as exc:  # noqa: BLE001
                panel_rows.append({"domain": dom, "sample": nm, "panel": "B_full vs A_engine2",
                                   "status": "NOT_IDENTIFIABLE",
                                   "reason": type(exc).__name__ + ":" + str(exc)[:120]})
    pn = pd.DataFrame(panel_rows)
    pn.to_csv(HERE / "wp5_struct_panel.csv", index=False, encoding="utf-8-sig")
    rec(f"      (b1) 面板结构 (A_engine2 2 物种 vs B_full 5 物种, phi=0.6, ps=1, ls=1):")
    for _, r in pn.iterrows():
        if r["status"] != "OK":
            rec(f"          {r['domain']}|{r['sample'][:26]:<28} {r['status']}: {r.get('reason','')}")
        else:
            rec(f"          {r['domain']}|{r['sample'][:26]:<28} "
                f"B_full dS={r['dS_B_full_ml']:11.4f} A_engine2 dS={r['dS_A_engine2_ml']:11.4f} "
                f"Δ={r['abs_diff_ml']:+10.4f} (相对 {r['rel_diff']:.2e}) "
                f"符号翻转={'是' if r['sign_B_full'] != r['sign_A_engine2'] else '否'}")

    # b2: 体积口径 vs 固定池口径 (WP5 vs WP4) —— 在冻结基座上两者逐位一致
    conv = {
        "volumetric_pool_accounting": {
            "definition": "S_city = (M0-M) + x_ai + inc_recl - pool; dS_pot = S_city(B2) - S_city(B1)",
            "anchor_ha_IEUA_phi0.6_ml": float(anchor["dS_pot_ml"]),
        },
        "fixed_pool_C_minus_F": {
            "definition": "dS_pot = C - F = (inc_B2-inc_B1) - [(M0-M1) + x_ai]  (WP2/WP4/A13)",
            "anchor_ha_IEUA_phi0.6_ml": ref,
        },
        "relative_difference_at_frozen_basis": float(rel),
        "verdict": ("在冻结基座 (pool=P0, gap=gap_0, dp=0, e_scale=1) 处两口径**恒等**; "
                    "差异只在 pool/gap 被外生改变时出现 —— 此时 dS_pot 才成为 pool 的函数。"),
    }
    # b3: F 式 (WP2/WP4 式 vs A13 式) —— 实测恒等
    fvariants = []
    for dom in W.DOMS:
        for nm in primary:
            for phi in (0.2, 0.4, 0.6, 0.8):
                bl = cm.BASELINES[dom]
                r = W.solve_dS(dom, nm, q_by[nm], phi=phi, pool_ml=bl["P0"],
                               gap_ml=bl["gap"], e_total_ml=bl["E_total"])
                if not r["reliable"]:
                    continue
                phi_eff = r["x_ai_ml"] / r["M1_ml"] if r["M1_ml"] > 1e-12 else 0.0
                F_wp4 = (r["M0_ml"] - r["M1_ml"]) + r["x_ai_ml"]
                F_a13 = r["M0_ml"] - (1.0 - phi_eff) * r["M1_ml"]
                fvariants.append({"domain": dom, "sample": nm, "phi": phi,
                                  "F_WP2_WP4_ml": F_wp4, "F_A13_ml": F_a13,
                                  "abs_diff_ml": F_wp4 - F_a13,
                                  "rel_diff": abs(F_wp4 - F_a13) / max(abs(F_wp4), 1e-30)})
    fv = pd.DataFrame(fvariants)
    max_frel = float(fv["rel_diff"].max()) if len(fv) else float("nan")
    rec(f"      (b2) F 式结构: WP2/WP4 式 F=(M0-M1)+x_ai  vs  A13 式 F=M0-(1-phi_eff)M1")
    rec(f"           n={len(fv)}, 最大相对差 = {max_frel:.3e} "
        f"=> {'✓ 实测恒等 (x_ai ≡ phi_eff*M1)' if max_frel <= 1e-9 else '✗ 存在结构差异'}")
    rec(f"      (b3) 体积口径 vs 固定池口径: 冻结基座相对差 = {rel:.3e} => 恒等 (见 §0b)")

    rec("\n  (c) 情景不确定性 (水样 × 域; 同一参数点集上的确定性方差分解)")
    if scen_stats.get("verdict") == "NOT_IDENTIFIABLE":
        rec(f"      {scen_stats}")
    else:
        rec(f"      参数点集: {SCEN_N_DRAW} 个 (压力域均匀抽样, seed={SCEN_POINTS_SEED}); "
            f"情景 = {scen_cfgs}")
        rec(f"      n_all={scen_stats['n_all']}  n_eff={scen_stats['n_eff']} "
            f"(门禁失败 {scen_stats['not_identifiable']})")
        rec(f"      情景【间】方差占比 = {scen_stats['var_share_between_pct']}% "
            f"(SS_between={scen_stats['ss_between']:.4g})")
        rec(f"      情景【内】即参数方差占比 = {scen_stats['var_share_within_pct']}% "
            f"(SS_within={scen_stats['ss_within']:.4g})")
        rec(f"      组均值:")
        for g, v in scen_stats["by_group"].items():
            rec(f"          {g:<34} n={v['n']:<3} mean={v['mean_ml']:12.2f} ML "
                f"sd={v['sd_ml'] if v['sd_ml'] is None else round(v['sd_ml'], 2)} "
                f"range=[{v['min_ml']:.4g}, {v['max_ml']:.4g}] "
                f"负/零/正={v['n_neg']}/{v['n_zero']}/{v['n_pos']}")
        rec(f"      裁定: {scen_stats['verdict']}")

    # ---------------- 5. 汇总 ----------------
    main_morris = mo[mo.config == main_tag].copy()
    main_sobol = so[so.config == main_tag].copy()
    summary = {
        "task": "WP5 任务 A: 全局敏感性 (Morris 筛选 + Sobol 方差分解), 现行 baseline 限值重跑",
        "why_rerun": ("旧 A10/T10_morris.csv & T10_sobol.csv 使用旧占位限值 "
                      "{TDS 2200, Cl 500, hardness 700, alkalinity 500, silica 150} 与旧估计量 "
                      "y=S_city/M0 (4 控制量, 无化学维度), 已过时, 不可用于新结论。"),
        "estimand": "dS_pot = C - F = max(0, inc_B2 - inc_B1) - [(M0 - M1) + x_ai]",
        "sign_convention": "dS_pot > 0 => 城市净取水上升 (有害); < 0 => 下降 (有益)",
        "limit_set": cm.LIMIT_SET,
        "panel": W.PANEL,
        "panel_limits": cm.PANELS[W.PANEL],
        "panel_limits_source": "GB/T 50050-2017 循环冷却水 (A27 引用档, source_verified)",
        "chemistry_panel_A_note": {"A_engine2": cm.PANELS["A_engine2"],
                                    "role": "仅作结构不确定性对照, 不用于主结论"},
        "samples_authoritative": meta,
        "primary_samples_complete": primary,
        "brackish_banned_not_used": banned,
        "incomplete_samples_excluded": [n for n, m in meta.items()
                                        if m["status"] != "COMPLETE"],
        "param_bounds_stress": {k: list(v) for k, v in BOUNDS_STRESS.items()},
        "param_bounds_conservative": {k: list(v) for k, v in BOUNDS_CONSERVATIVE.items()},
        "estimand_anchor_check": {
            "config": "ha|IEUA RP-1|phi=0.6|pool=P0|gap=gap_0|dp=0|e_scale=1|ls=1|coc=5",
            "wp5_dS_pot_ml": float(anchor["dS_pot_ml"]),
            "wp4_reference_dS_pot_ml": ref,
            "relative_difference": float(rel),
            "tolerance": 1e-6, "passes": bool(rel <= 1e-6),
            "gate": {"status_B2": anchor["status_B2"], "b1_healthy": anchor["b1_healthy"],
                     "CoC0": anchor["CoC0"], "CoC1": anchor["CoC1"]},
            "identity_rel_residual_C_minus_F": W.rel_resid(
                anchor["C_ml"] - anchor["F_ml"], anchor["dS_pot_ml"]),
        },
        "cache_key_probe_CoC1_by_sample": refs,
        "cache_key_includes_q": bool(len(set(refs.values())) == len(refs)),
        "morris": {
            "implementation": ("wp5_morris_sobol.morris_trajectory_sensitivity "
                               "(教科书轨迹, p 级网格, 固定网格步长 Δ); "
                               "引擎 aiuwm.sensitivity.morris_sensitivity 未使用 —— 理由见 "
                               "summary['morris']['engine_impl_replaced_because']"),
            "engine_impl_replaced_because": (
                "引擎实现按 min(high, base+Δ) 或 max(low, base-Δ) 取点, 当 base+Δ 恰落在 "
                "high 边界时实际步长可能远小于 Δ, 但效应仍除以 Δ/(high-low), 会把效应系统性"
                "放大; 且它不检测 actual_delta==0。本脚本改用固定网格步长并显式统计 "
                "n_zero_delta, 以消除该边界退化。"),
            "trajectories": MORRIS_TRAJ, "levels": MORRIS_LEVELS,
            "normalized_delta": MORRIS_LEVELS / (2.0 * (MORRIS_LEVELS - 1.0)),
            "by_config": morris_meta,
            "main_config": main_tag,
            "ranking_main": main_morris[["parameter", "mu", "mu_star", "sigma", "mu_abs_ratio"]]
                .round(6).to_dict(orient="records"),
            "top3_main": main_morris.head(3)[["parameter", "mu_star"]]
                .round(6).to_dict(orient="records"),
        },
        "sobol": {
            "implementation": "aiuwm.sensitivity.sobol_sensitivity (Saltelli), 未改动",
            "samples": SOBOL_SAMPLES,
            "params_used": sobol_params,
            "defect_found_and_fixed": {
                "symptom": "首轮运行 4/4 配置的 Sobol 指数全部为 NaN",
                "root_cause": ("本脚本 Evaluator._collect / chem_map 对参数点**硬下标取键**, "
                               "而 Sobol 降维后参数点只含被抽样的子集 -> 每次都 KeyError; "
                               "旧 raw() 用裸 `except Exception` 把它吞成 NaN。"),
                "why_dangerous": ("这正是任务书警告的'不得用替代品蒙混'的反面: 代码缺陷被伪装成"
                                  "'情景不可辨识', 若不复核就会输出'4/4 配置 NOT_IDENTIFIABLE'"
                                  "这一**假结论**。"),
                "fix": ("(i) chem_map/_collect 对未抽样维回落到冻结取值 (化学 1.0, 其余为冻结默认); "
                        "(ii) Evaluator.raw 只吞 ValueError/ZeroDivisionError/OverflowError "
                        "这类**引擎在不可行情景上抛错**的信号, KeyError 等代码缺陷直接向上抛; "
                        "(iii) sobol_guarded 独立普查 NaN 并把 '门禁失败' 与 '引擎抛错' 分别计数。"),
                "verification": "新增 _probe9 断言: BrokenEvaluator 抛 KeyError 时必须向上传播 (已 PASS)。",
                "status": "RESOLVED",
            },
            "dimension_reduction": {
                "n_full": len(BOUNDS_STRESS), "n_used": len(sobol_params),
                "cost_full_evals": cost_full, "cost_used_evals": cost_used,
                "note": ("显式取舍: 计算量控制。Sobol 指数只对这 %d 维的条件方差有效; "
                         "未纳入维度的方差并入 ST(总阶)。" % len(sobol_params)),
            },
            "by_config": sobol_meta,
            "main_config": main_tag,
            "main": main_sobol[["parameter", "S1", "ST"]].round(6).to_dict(orient="records"),
        },
        "sign_flip_diagnosis": {
            "method": ("固定其余参数于冻结取值 (phi=0.6, ps=gs=1, dp=0, e=1, "
                       "coc_design=5, ls=1, 化学 x=1), 沿每个参数的边界取 41 点, "
                       "对 2 域 × 2 水样求 dS_pot, 统计符号取值与沿曲线变号次数; "
                       "另以 401 点精细定位 ha|IEUA 上的首个翻转点。"),
            "zero_value_convention": f"|dS_pot| < {W.ZERO_ABS} ML 记为 0",
            "table": fd.round(6).to_dict(orient="records"),
            "parameters_that_change_sign": sign_flippers,
            "parameters_that_do_not_change_sign": fd[~fd.sign_varying]["parameter"].tolist(),
        },
        "uncertainty_decomposition": {
            "discipline": "参数 / 结构 / 情景 三类**分开报告**, 不合并为单一误差条。",
            "parameter": {
                "definition": "连续参数在边界内的变动 (条件于给定 域×水样×结构)",
                "morris_by_config": {k: {"n_eval": v["n_eval"],
                                         "n_not_identifiable": v["n_not_identifiable"],
                                         "not_identifiable_share_pct": v["not_identifiable_share_pct"]}
                                     for k, v in morris_meta.items()},
                "main_top3": main_morris.head(3)[["parameter", "mu_star", "sigma"]]
                    .round(6).to_dict(orient="records"),
            },
            "structural": {
                "definition": "估计口径/面板/F 式的**离散选择**, 不是连续参数",
                "panel_B_full_vs_A_engine2": pn.to_dict(orient="records"),
                "pool_convention": conv,
                "F_formula": {
                    "variants": ["F=(M0-M1)+x_ai (WP2/WP4)", "F=M0-(1-phi_eff)*M1 (A13)"],
                    "n_compared": int(len(fv)),
                    "max_relative_difference": max_frel,
                    "verdict": "恒等 (x_ai ≡ phi_eff*M1 在 B2 支路按构造成立)",
                },
            },
            "scenario": {
                "definition": "水样 (权威化学) × 域 (气候/城市) 的离散情景",
                "n_parameter_points": SCEN_N_DRAW,
                "seed": SCEN_POINTS_SEED,
                **{k: v for k, v in scen_stats.items() if k != "by_group"},
                "by_group": scen_stats.get("by_group", {}),
            },
        },
        "discipline_note": (
            "引擎只读; 权威水样只来自 load_samples(); 主口径仅完整物种水样; Figshare BW 不纳入; "
            "双门禁 (B2 converged_unique + B1 健康单根闭合 + CoC 不触下限) 并报 n_eff; "
            "门禁失败点在该参数点记 NOT_IDENTIFIABLE 并从有效样本剔除, 不插补、不计 PASS; "
            "大数量级用相对容差; 符号计数声明零值约定与实际 n_eff; 不编造数字。"),
        "cache_discipline": "每次 solve_dS 使用独立 cache (M5 复发防护), 另用共享 cache 探针自检组成维度。",
        "runtime_s": round(time.time() - t0, 1),
        "outputs": ["wp5_morris.csv", "wp5_sobol.csv", "wp5_scenario_points.csv",
                    "wp5_struct_panel.csv", "wp5_sensitivity_summary.json", "wp5_morris_sobol_log.txt"],
    }
    (HERE / "wp5_sensitivity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (HERE / "wp5_morris_sobol_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp5_morris.csv / wp5_sobol.csv / wp5_sensitivity_summary.json "
        f"(+ wp5_scenario_points.csv, wp5_struct_panel.csv, wp5_morris_sobol_log.txt) "
        f"  {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
