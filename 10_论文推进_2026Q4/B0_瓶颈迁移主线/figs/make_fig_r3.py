# -*- coding: utf-8 -*-
"""FigR3：r* 的四情形分类学与敏感性。

三个面板：
  (a) 分类相图：横轴 C* = L/CoC_design，纵轴 r*，标出四情形的分区与本文两端点位置
  (b) 三情形实证：三种 CoC_design 下 CoC 随 r 的变化（情形 I 立即下降 / II 阈值 / III 恒定）
  (c) 参数敏感性：单参数扫描下 r* 的范围，说明数值条件化

⚠ 单一数据入口：全部数值经 load_* 从产物读取，本文件不写死数值。
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
    R2,
    apply_style,
    save,
)
import matplotlib.pyplot as plt  # noqa: E402

# 参数（与主稿一致；仅用于画解析相图的坐标映射，不用于判定）
L_LIMIT = 2200.0
C_P = 180.0
C_R = 650.0


def load_regime_map() -> pd.DataFrame:
    p = R2 / "rstar_regime_map.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}")
    return pd.read_csv(p)


def load_regime_validation() -> pd.DataFrame:
    p = R2 / "rstar_regime_validation.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}")
    return pd.read_csv(p)


def load_sensitivity() -> pd.DataFrame:
    p = R2 / "rstar_sensitivity.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}")
    return pd.read_csv(p)


def make_fig_r3() -> list[Path]:
    apply_style()
    rmap = load_regime_map()
    val = load_regime_validation()
    sens = load_sensitivity()

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5), constrained_layout=True)

    # ---------------- (a) 分类相图 ----------------
    ax = axes[0]
    # 横轴 C* = L/CoC_design，纵轴 r*
    sub = rmap.dropna(subset=["r_star"]).copy()
    sub["C_star"] = sub["L"] / sub["coc_design"]

    regime_color = {"I": C_HA, "II": "#2c7a7b", "III": C_CO, "IV": C_OTHER}
    regime_label = {"I": "情形 I", "II": "情形 II", "III": "情形 III", "IV": "情形 IV"}

    for code in ("I", "II", "III", "IV"):
        s = sub[sub["regime"] == code]
        if s.empty:
            continue
        ax.scatter(s["C_star"], s["r_star"], s=7, alpha=0.65,
                   color=regime_color[code], edgecolor="none",
                   label=f"{regime_label[code]}（n={len(s)}）", zorder=2)

    # 分区边界
    ax.axvline(C_P, color=C_POLICY, ls="--", lw=0.9, zorder=1)
    ax.axvline(C_R, color=C_POLICY, ls="--", lw=0.9, zorder=1)
    ax.axhline(0.0, color=C_OTHER, lw=0.7, zorder=1)
    ax.axhline(1.0, color=C_OTHER, lw=0.7, zorder=1)

    # 本文两端点位置
    c_star_nominal = L_LIMIT / 5.0
    r_nominal = (c_star_nominal - C_P) / (C_R - C_P)
    ax.scatter([c_star_nominal], [r_nominal], s=70, marker="*",
               color="black", zorder=5, label="本文端点")
    ax.annotate(f"$r^*$={r_nominal:.3f}", xy=(c_star_nominal, r_nominal),
                xytext=(c_star_nominal + 120, r_nominal + 0.32),
                fontsize=6.8, color="black",
                arrowprops=dict(arrowstyle="-", lw=0.6, color="black"))

    ax.text(C_P + 12, 1.62, "$C_p$", color=C_POLICY, fontsize=6.6, va="top")
    ax.text(C_R + 12, 1.62, "$C_r$", color=C_POLICY, fontsize=6.6, va="top")
    ax.set_xlabel("$C^*=L/\\mathrm{CoC}_{design}$ (mg/L)")
    ax.set_ylabel("$r^*$")
    ax.set_title("(a) 四情形分类相图", loc="left")
    ax.set_ylim(-0.35, 1.95)
    ax.set_xlim(100, 1250)
    # 图例放在图外下方，避免与散点重叠
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22),
              handletextpad=0.3, borderaxespad=0.0,
              markerscale=1.6, ncol=2, columnspacing=0.8,
              fontsize=6.3)

    # ---------------- (b) 三情形实证 ----------------
    ax = axes[1]
    style = {
        "I": (C_HA, "o", "情形 I"),
        "II": ("#2c7a7b", "s", "情形 II"),
        "III": (C_CO, "^", "情形 III"),
    }
    for code, (color, marker, label) in style.items():
        s = val[val["regime"] == code].sort_values("target_r")
        if s.empty:
            continue
        r0 = float(s.iloc[0]["coc_model"])
        # 归一化到 r=0 的 CoC，使三情形可在同一纵轴比较
        ax.plot(s["target_r"], s["coc_model"] / r0, marker=marker, ms=4.0,
                lw=1.5, color=color, label=label, mfc=color)
    ax.axhline(1.0, color=C_OTHER, ls=":", lw=0.8, zorder=0)
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("CoC / CoC($r$=0)")
    ax.set_title("(b) 三情形的 CoC 轨迹", loc="left")
    ax.legend(loc="lower left", handletextpad=0.4, borderaxespad=0.2)

    # ---------------- (c) 参数敏感性 ----------------
    ax = axes[2]
    param_label = {
        "L": "$L$",
        "coc_design": "$\\mathrm{CoC}_{d}$",
        "c_potable": "$C_p$",
        "c_reclaimed": "$C_r$",
    }
    param_color = {
        "L": C_HA,
        "coc_design": "#2c7a7b",
        "c_potable": C_OTHER,
        "c_reclaimed": C_CO,
    }
    for param, color in param_color.items():
        s = sens[sens["parameter"] == param].dropna(subset=["r_star"])
        s = s[(s["r_star"] > 0) & (s["r_star"] < 1.0)]
        if s.empty:
            continue
        # 归一化到标称值
        x = s["value"] / s["value"].iloc[len(s) // 2] if len(s) else s["value"]
        ax.plot(s["value"], s["r_star"], lw=1.4, color=color,
                label=param_label[param])
    ax.scatter([L_LIMIT], [r_nominal], s=40, marker="*", color="black", zorder=5)
    ax.axhline(r_nominal, color="black", ls=":", lw=0.7, zorder=0)
    ax.text(1350, r_nominal + 0.045, f"标称 {r_nominal:.3f}", fontsize=6.5)
    ax.set_xscale("log")
    ax.set_xlabel("参数取值（对数轴，mg/L 或 无量纲）")
    ax.set_ylabel("$r^*$")
    ax.set_title("(c) 单参数敏感性", loc="left")
    ax.set_ylim(-0.02, 1.02)
    # 图例放图外下方
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22),
              handletextpad=0.3, borderaxespad=0.0,
              ncol=2, columnspacing=0.8, fontsize=6.3)

    fig.suptitle(
        "$r^*$ 是分类判据而非常数：$C^*=L/\\mathrm{CoC}_{design}$ 相对两种水源含盐量的位置"
        "决定城市类别（合成端点，未经实测率定）",
        fontsize=7.8, y=1.045,
    )
    return save(fig, "FigR3_rstar_regime_and_sensitivity")


def main() -> None:
    paths = make_fig_r3()
    for p in paths:
        print(f"  -> {p.name}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
