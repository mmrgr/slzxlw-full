# -*- coding: utf-8 -*-
"""FigR1 / FigR2：水质兼容阈值 r* 的核心图件。

FigR1 —— 阈值型响应
  (a) CoC 随 r 的变化（模型点 vs 解析曲线），标出 r*=0.5532
  (b) 物理 CAWCC 随 r 的变化（两域），证明 r<=r* 平坦、跨 r* 后下降
  (c) 同一容量点跨 r 的水量侧约束 vs 电网侧约束（混淆排除）

FigR2 —— 反噬分解
  (a) 反噬贡献（ML）随 r：r<=r* 恒为 0，之后单调上升
  (b) 补水惩罚（相对 CoC_design 的 %）

⚠ 导入顺序: 必须先 matplotlib.use("Agg") 再 import figstyle_b0。
⚠ 单一数据入口：全部数值经 load_* 从权威产物读取，本文件不写死任何数值。
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from figstyle_b0 import (  # noqa: E402
    C_CO,
    C_GRID,
    C_HA,
    C_OTHER,
    C_POLICY,
    C_WATER,
    R2,
    apply_style,
    save,
)
import matplotlib.pyplot as plt  # noqa: E402

# ---------------------------------------------------------------------------
# 单一数据入口
# ---------------------------------------------------------------------------
LIMIT_TDS = 2200.0
COC_DESIGN = 5.0
C_POTABLE = 180.0
C_RECLAIMED = 650.0


def r_star() -> float:
    """临界替代率。参数来自 examples/cawcc_r2/{ha,co}/project.json 的 cooling 与 water_sources。"""
    return (LIMIT_TDS / COC_DESIGN - C_POTABLE) / (C_RECLAIMED - C_POTABLE)


def coc_analytic(r: np.ndarray | float) -> np.ndarray | float:
    c_mix = np.asarray(r) * C_RECLAIMED + (1.0 - np.asarray(r)) * C_POTABLE
    return np.minimum(COC_DESIGN, LIMIT_TDS / c_mix)


def load_physical_cawcc() -> pd.DataFrame:
    p = R2 / "rstar_physical_cawcc_by_r.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}（请先跑 scripts/run_rstar_physical_probe.py）")
    return pd.read_csv(p)


def load_confound() -> pd.DataFrame:
    p = R2 / "rstar_confound_control.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}")
    return pd.read_csv(p)


def load_backlash() -> pd.DataFrame:
    p = R2 / "rstar_backlash_decomposition.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}")
    return pd.read_csv(p)


def load_probe() -> pd.DataFrame:
    p = R2 / "probe_rstar_mechanism.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}")
    return pd.read_csv(p)


# ---------------------------------------------------------------------------
def make_fig_r1() -> list[Path]:
    apply_style()
    cawcc = load_physical_cawcc()
    confound = load_confound()
    probe = load_probe()
    rs = r_star()

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.45), constrained_layout=True)

    # ---- (a) CoC 随 r：模型点 vs 解析曲线 ----
    ax = axes[0]
    rr = np.linspace(0.0, 0.9, 400)
    ax.plot(rr, coc_analytic(rr), color=C_OTHER, lw=1.6, zorder=1,
            label="解析式 $\\min(CoC_d,\\ L/C_{mix})$")
    for domain, color, mfc in (("ha", C_HA, C_HA), ("co", C_CO, "white")):
        sub = probe[probe["domain"] == domain].dropna(subset=["coc_mean"])
        if domain == "ha":
            ax.scatter(sub["target_r"], sub["coc_mean"], s=22, color=mfc,
                       edgecolor="white", linewidth=0.5, zorder=3,
                       label="模型输出（D-HA / D-CO）")
        else:
            ax.scatter(sub["target_r"], sub["coc_mean"], s=22, facecolor="white",
                       edgecolor=color, linewidth=1.0, zorder=3)
    ax.axvline(rs, color=C_POLICY, ls="--", lw=1.0, zorder=0)
    ax.annotate(f"$r^*={rs:.3f}$", xy=(rs, 4.62), xytext=(0.12, 4.28),
                color=C_POLICY, fontsize=7.0,
                arrowprops=dict(arrowstyle="-", color=C_POLICY, lw=0.7))
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("浓缩倍数 CoC")
    ax.set_title("(a) 水质约束在 $r^*$ 处开始生效", loc="left")
    ax.set_ylim(3.4, 5.15)
    ax.legend(loc="lower left", handletextpad=0.5, borderaxespad=0.2)

    # ---- (b) 物理 CAWCC 随 r ----
    ax = axes[1]
    for domain, color, label, marker in (
        ("ha", C_HA, "D-HA（水源侧先卡）", "o"),
        ("co", C_CO, "D-CO（电网侧先卡）", "s"),
    ):
        sub = cawcc[cawcc["domain"] == domain].sort_values("target_r")
        ax.plot(sub["target_r"], sub["physical_cawcc_mw"], marker=marker, ms=4.0,
                lw=1.5, color=color, label=label, mfc=color)
    ax.axvline(rs, color=C_POLICY, ls="--", lw=1.0, zorder=0)
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("纯物理 CAWCC (MW)")
    ax.set_title("(b) 物理承载容量：$r\\leq r^*$ 平坦", loc="left")
    ax.set_ylim(650, 1550)
    ax.legend(loc="lower left", handletextpad=0.5, borderaxespad=0.2)

    # ---- (c) 同一容量点跨 r：水量侧 vs 电网侧 ----
    ax = axes[2]
    sub = confound[(confound["domain"] == "ha")
                   & ((confound["capacity_mw"] - 1200.0).abs() < 1e-6)].sort_values("target_r")
    ax.plot(sub["target_r"], sub["max_source_abstraction_ratio"], marker="o", ms=4.0,
            lw=1.5, color=C_WATER, label="水源取水比")
    ax.plot(sub["target_r"], sub["max_wtw_utilization"], marker="^", ms=4.0,
            lw=1.5, color=C_WATER, ls="--", alpha=0.75, label="给水厂利用率")
    ax.plot(sub["target_r"], sub["max_daily_average_grid_connection_ratio"],
            marker="s", ms=4.0, lw=1.5, color=C_GRID, label="电网接网比")
    ax.axhline(0.95, color=C_POLICY, ls=":", lw=1.0, zorder=0)
    ax.text(0.02, 0.9535, "约束阈值 0.95", color=C_POLICY, fontsize=6.6)
    ax.axvline(rs, color=C_POLICY, ls="--", lw=1.0, zorder=0)
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("约束取值（峰值）")
    ax.set_title("(c) D-HA @1200 MW：仅水量侧恶化", loc="left")
    ax.set_ylim(0.82, 0.975)
    ax.legend(loc="center left", handletextpad=0.5, borderaxespad=0.2)

    fig.suptitle(
        "水质兼容阈值 $r^*$：超过后浓缩倍数下降、补水需求上升，"
        "水量侧约束前移而电力侧不动（合成端点，未经实测率定）",
        fontsize=8.0, y=1.045,
    )
    return save(fig, "FigR1_rstar_threshold_response")


def make_fig_r2() -> list[Path]:
    apply_style()
    dec = load_backlash()
    dec = dec.drop_duplicates(subset=["domain", "capacity_mw", "target_r"])
    rs = r_star()

    fig, axes = plt.subplots(1, 2, figsize=(5.4, 2.45), constrained_layout=True)

    # ---- (a) 反噬贡献（ML）----
    ax = axes[0]
    for domain, color, label, marker in (
        ("ha", C_HA, "D-HA", "o"),
        ("co", C_CO, "D-CO", "s"),
    ):
        sub = dec[(dec["domain"] == domain)
                  & ((dec["capacity_mw"] - 1200.0).abs() < 1e-6)].sort_values("target_r")
        ax.plot(sub["target_r"], sub["backlash_ml"], marker=marker, ms=4.0,
                lw=1.5, color=color, label=f"{label} @1200 MW", mfc=color)
    ax.axvline(rs, color=C_POLICY, ls="--", lw=1.0, zorder=0)
    ax.axhline(0.0, color=C_OTHER, lw=0.7, zorder=0)
    ax.annotate(f"$r^*={rs:.3f}$", xy=(rs, 900.0), xytext=(0.10, 1700.0),
                color=C_POLICY, fontsize=7.0,
                arrowprops=dict(arrowstyle="-", color=C_POLICY, lw=0.7))
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("反噬贡献 (ML)")
    ax.set_title("(a) $r\\leq r^*$ 时反噬精确为零", loc="left")
    ax.legend(loc="upper left", handletextpad=0.5, borderaxespad=0.2)

    # ---- (b) 补水惩罚 % ----
    ax = axes[1]
    rr = np.linspace(0.0, 0.9, 300)
    coc = coc_analytic(rr)
    penalty = 100.0 * ((coc / (coc - 1.0)) / (COC_DESIGN / (COC_DESIGN - 1.0)) - 1.0)
    ax.plot(rr, penalty, color=C_OTHER, lw=1.8, zorder=1, label="解析式")
    for domain, color, marker in (("ha", C_HA, "o"), ("co", C_CO, "s")):
        sub = dec[(dec["domain"] == domain)
                  & ((dec["capacity_mw"] - 1200.0).abs() < 1e-6)].sort_values("target_r")
        ax.plot(sub["target_r"], sub["watering_penalty_pct"], marker=marker, ms=4.0,
                lw=0, mfc=color, mec="white", mew=0.5, label=f"{domain.upper()} 实测")
    ax.axvline(rs, color=C_POLICY, ls="--", lw=1.0, zorder=0)
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("补水需求增幅 (%)")
    ax.set_title("(b) 补水惩罚与容量无关", loc="left")
    ax.legend(loc="upper left", handletextpad=0.5, borderaxespad=0.2)

    fig.suptitle(
        "水质反噬的定量分解：增幅由 $CoC/(CoC-1)$ 决定，与容量无关"
        "（合成端点，未经实测率定）",
        fontsize=8.0, y=1.045,
    )
    return save(fig, "FigR2_backlash_decomposition")


def main() -> None:
    paths = []
    paths += make_fig_r1()
    paths += make_fig_r2()
    print(f"r* = {r_star():.4f}")
    for p in paths:
        print(f"  -> {p.name}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
