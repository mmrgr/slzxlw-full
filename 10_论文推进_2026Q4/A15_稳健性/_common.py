"""A15 稳健性分析的共享装订: 路径、抽样器、几何均值口径、Gate 记录.

本目录由 task-4 (P3 稳健性) 独占。**只读**引用 A10/A13, 不写它们的任何文件。

口径说明 (重要, 影响所有下游数值)
--------------------------------
T11b_summary.json 报的 P(S_city>0)|dp=1.0 ≈ 0.62 是在 dp_scale=1.0 下算的。
但探针 (见 robustness_summary.md §0) 显示: dp_scale 在池预算里的实现是
    available = pool + dp = pool*(1 + dp_scale)
即 dp_scale=1.0 时水池预算翻倍, 而本域基线是 gap_scale ≈ 1.8*pool。
于是 dp>=1 把可用池推到 **超过既有用户缺口**, 分配器给既有用户分配的总量
超过 pool (inc_recl > pool), S_city 的"位移项" inc_recl - pool 变正,
S_city>0 变成**位移记账**的结果, 而不是 AI 挤占减少的结果。

因此本模块同时报两个互补口径, 互不替代:
    口径 A (份额口径, 论文中心风险量): dp_scale = 0
        available = pool; 此时恒有 x_ai + inc_recl ≡ pool
        => S_city ≡ M0 - M <= 0  (A13 已证的恒等式)
    口径 B (T11b 原口径): dp_scale = 1.0
        可复现 0.62, 但含容量扩张效应, 需在正文明确区分。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
A13 = ROOT / "A13_可靠性机制"

for _p in (str(A10), str(A13), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import city_model as cm        # noqa: E402
import reliability_model as rm  # noqa: E402

NP_RNG = np.random.default_rng

# ---------------------------------------------------------------- 控制量
# 与 cm.CONTROL_BOUNDS 一致, 但显式列出以便先验映射可审
CTRL = {
    "pool_scale": (0.3, 4.0),
    "gap_scale": (0.3, 4.0),
    "dp_scale": (0.0, 3.0),
}
AI_TARGET_RANGE = (0.10, 0.95)

PANEL_NAMES = ("A_engine2", "B_full")
DOMAINS = ("ha", "co")

# 水样池 (T6): 第 1 行 IEUA = 再生水锚; 末行 = 模型假定; 第 4 行 = 苦咸水(非再生)
# T11 说明: 含 1 组非再生水 + 2 组 TDS 估算值, 故水样维概率 = 模型假定, 非全球频率。


# ---------------------------------------------------------------- 抽样器
def lhs(n: int, k: int, rng) -> np.ndarray:
    """拉丁超立方 (接受外部随机源). 与 T11_uncertainty.lhs 同实现, 保证可复现."""
    u = np.empty((n, k))
    for j in range(k):
        u[:, j] = (rng.permutation(n) + rng.random(n)) / n
    return u


def map_prior(u: np.ndarray, lo: float, hi: float, kind: str) -> np.ndarray:
    """把 U(0,1) 分位映射到 [lo,hi] 上的指定先验.

    uniform     : 线性; 假设所有取值同等可能
    log-uniform : 几何; 假设只知量级不知尺度 (Jeffreys), 偏向小值
    triangular  : 众数 = 区间中点; 假设名义值最可能, 端点最不可能

    ⚠ lo = 0 的处理 (dp_scale 的区间是 [0,3], 几何先验在 0 处无定义):
    标准做法是**零点原子 + 正值上的几何律**混合:
        P(dp = 0) = p0;   在 (0, hi] 上按 log-uniform 取分位
    这不是对 log-uniform 的"修补", 而是它在含 0 支撑上的正确推广 ——
    "零新增产能"是一个有实义的**离散状态** (与"新增一点点产能"质变不同),
    不能用连续密度近似。p0 默认取 0.25 (与 uniform 下 [0,0.75] 的质量相当)。
    """
    u = np.clip(np.asarray(u, dtype=float), 1e-12, 1 - 1e-12)
    lo, hi = float(lo), float(hi)
    if kind == "uniform":
        return lo + (hi - lo) * u
    if kind == "log-uniform":
        if lo > 0:
            return lo * (hi / lo) ** u
        # lo == 0: 零点原子混合
        p0 = ZERO_ATOM_P0
        pos_lo = max(hi * 1e-4, 1e-9)          # 原子之外的连续下界
        out = np.where(u < p0, 0.0,
                       pos_lo * (hi / pos_lo) ** ((u - p0) / (1.0 - p0)))
        return np.clip(out, 0.0, hi)
    if kind == "triangular":
        mode = 0.5 * (lo + hi)
        return np.where(
            u < (mode - lo) / (hi - lo),
            lo + np.sqrt(u * (hi - lo) * (mode - lo)),
            hi - np.sqrt((1 - u) * (hi - lo) * (hi - mode)),
        )
    raise ValueError(f"未知先验 kind={kind!r}")


# log-uniform 在 lo=0 时的零点原子质量 (见 map_prior docstring)
ZERO_ATOM_P0 = 0.25


def prior_mean(lo: float, hi: float, kind: str) -> float:
    """先验均值 (用于诊断: log-uniform 均值远低于区间中点)."""
    lo, hi = float(lo), float(hi)
    if kind == "uniform":
        return 0.5 * (lo + hi)
    if kind == "log-uniform":
        if lo > 0:
            return (hi - lo) / np.log(hi / lo)
        pos_lo = max(hi * 1e-4, 1e-9)
        return (1.0 - ZERO_ATOM_P0) * (hi - pos_lo) / np.log(hi / pos_lo)
    if kind == "triangular":
        return 0.5 * (lo + hi)
    raise ValueError(kind)


def prior_median(lo: float, hi: float, kind: str) -> float:
    lo, hi = float(lo), float(hi)
    if kind == "log-uniform":
        if lo > 0:
            return float(np.sqrt(lo * hi))
        # 中位落在零点原子内 (p0=0.25 < 0.5) -> 上调到连续段的 log 中位
        pos_lo = max(hi * 1e-4, 1e-9)
        return float(pos_lo * (hi / pos_lo) ** ((0.5 - ZERO_ATOM_P0) / (1 - ZERO_ATOM_P0)))
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- 几何均值口径
def ratio_geomean_percent(resid: np.ndarray, ref: np.ndarray,
                          floor: float = 0.05) -> float:
    """比值误差的**几何均值**相对偏差 (%), 对称对待高估与低估.

    为什么不用普通 R²: 预测律给出的是比值 r = pred/ref, 其重要性在**乘性**尺度上。
    若用算术 R², 单点 100× 高估会主导全部得分, 掩盖系统性低估。
    几何均值 = exp(mean(log r)), 则:
        +x% 与 -x% 对称; 100× 高估 (log=4.6) 只惩罚一次。

    floor: 比值下限, 防止 log(0)。
    """
    resid = np.asarray(resid, dtype=float)
    ref = np.asarray(ref, dtype=float)
    m = np.isfinite(resid) & np.isfinite(ref) & (ref > 0)
    if not m.any():
        return float("nan")
    r = np.clip(resid[m] / ref[m], floor, 1.0 / floor)
    return float(100.0 * (np.exp(np.mean(np.log(r))) - 1.0))


def log_rmse(resid: np.ndarray, ref: np.ndarray, floor: float = 0.05) -> float:
    """log10 空间的 RMSE (dex 为单位). <0.3 dex ≈ 因子 2 以内."""
    resid = np.asarray(resid, dtype=float)
    ref = np.asarray(ref, dtype=float)
    m = np.isfinite(resid) & np.isfinite(ref) & (ref > 0) & (resid > 0)
    if not m.any():
        return float("nan")
    return float(np.sqrt(np.mean((np.log10(resid[m]) - np.log10(ref[m])) ** 2)))


def log_r2(resid: np.ndarray, ref: np.ndarray) -> float:
    """log10 空间的决定系数. 1 = 完美, <=0 = 不如取几何均值."""
    resid = np.asarray(resid, dtype=float)
    ref = np.asarray(ref, dtype=float)
    m = np.isfinite(resid) & np.isfinite(ref) & (ref > 0) & (resid > 0)
    if m.sum() < 3:
        return float("nan")
    y, x = np.log10(resid[m]), np.log10(ref[m])
    ss_res = float(np.sum((y - x) ** 2))          # 预测 = 参考 (y=x 线, 无自由参数)
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else float("nan")


# ---------------------------------------------------------------- Gate
class GateLog:
    """Gate 判定记录器: 每条判定必须带可追溯的证据字符串."""

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, gate: str, passed, value, rule: str, evidence: str) -> None:
        self.rows.append({
            "gate": gate,
            "passed": bool(passed) if passed is not None else None,
            "value": value,
            "rule": rule,
            "evidence": evidence,
        })

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)

    def to_json(self) -> list[dict]:
        return self.rows

    def render_md(self) -> str:
        out = ["| Gate | 判定 | 值 | 判据 | 证据 |",
               "|---|---|---|---|---|"]
        for r in self.rows:
            p = r["passed"]
            mark = "✅ PASS" if p is True else ("❌ FAIL" if p is False else "— N/A")
            out.append(f"| {r['gate']} | {mark} | {r['value']} | {r['rule']} | "
                       f"{r['evidence']} |")
        return "\n".join(out)


# ---------------------------------------------------------------- 一致性基线
# T11b_summary.json 的冻结值 —— 用作"我们的复现是否对得上"的锚
T11B_P = {0.0: 0.0029, 0.5: 0.61, 1.0: 0.62, 2.0: 0.6214}


def s_city(dom, panel, sample, *, pool=1.0, gap=1.0, dp=0.0, ai=0.7,
           limit_scale=1.0, cache=None) -> float:
    return cm.city_outcome(dom, panel, sample, pool_scale=pool, gap_scale=gap,
                           dp_scale=dp, ai_target=ai, limit_scale=limit_scale,
                           cache=cache)["S_city_ml"]


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str),
                    encoding="utf-8")
