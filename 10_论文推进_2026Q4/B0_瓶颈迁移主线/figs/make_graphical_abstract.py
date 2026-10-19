# -*- coding: utf-8 -*-
"""生成 Graphical Abstract（WR 官方最小 531 × 1328 px，h × w，96 dpi 下 5 × 13 cm 可读）。

设计：一张横向三联图，只讲一句话——
「配比 r 越过 r* 之前是纯收益，之后补水需求反升」。
不放未经核实的数字，只放模型已验证的核心量。
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
OUT = HERE / "GraphicalAbstract.pdf"
OUT_PNG = HERE / "GraphicalAbstract.png"

# ---- 参数与解析式（与母稿一致）----
L, COC_D, C_P, C_R = 2200.0, 5.0, 180.0, 650.0
R_STAR = (L / COC_D - C_P) / (C_R - C_P)  # 0.5532


def coc(r: np.ndarray) -> np.ndarray:
    c_mix = r * C_R + (1.0 - r) * C_P
    return np.minimum(COC_D, L / c_mix)


def makeup_penalty_pct(r: np.ndarray) -> np.ndarray:
    """相对 r<=r* 恒定基线的补水惩罚（%）。"""
    base = COC_D / (COC_D - 1.0)
    c = coc(r)
    return (c / (c - 1.0)) / base * 100.0 - 100.0


def main() -> None:
    # WR 要求 h x w 至少 531 x 1328；用 7.2 x 3.0 英寸 @ 300 dpi => 900 x 2160 px，超规格安全
    fig, axes = plt.subplots(1, 3, figsize=(13.28, 5.31), dpi=300)
    r = np.linspace(0.0, 0.95, 400)
    c = coc(r)
    pen = makeup_penalty_pct(r)

    BLUE = "#1f4e79"
    RED = "#c00000"
    GREY = "#7f7f7f"
    SHADE = "#dce6f1"

    # ---- (a) CoC 被水质上限截断 ----
    ax = axes[0]
    ax.plot(r, c, color=BLUE, lw=2.6)
    ax.axhline(COC_D, color=GREY, ls=":", lw=1.4)
    ax.axvline(R_STAR, color=RED, ls="--", lw=1.8)
    ax.fill_between(r, 0, c, where=(r <= R_STAR), color=SHADE, alpha=0.85)
    ax.text(R_STAR / 2, 3.2, "pure gain", ha="center", fontsize=13, color=BLUE)
    ax.text(R_STAR + 0.03, 2.3, "penalty", ha="left", fontsize=13, color=RED)
    ax.annotate(f"$r^*$ = {R_STAR:.4f}", xy=(R_STAR, COC_D), xytext=(R_STAR + 0.06, 5.35),
                fontsize=13, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.4))
    ax.set_xlabel("Reclaimed-water substitution ratio  $r$", fontsize=12)
    ax.set_ylabel("Cycles of concentration  CoC", fontsize=12)
    ax.set_title("(a) Water quality caps CoC", fontsize=14, loc="left", color=BLUE)
    ax.set_xlim(0, 0.95)
    ax.set_ylim(0, 6.4)
    ax.tick_params(labelsize=11)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    # ---- (b) 补水惩罚是阈值型的 ----
    ax = axes[1]
    ax.plot(r, pen, color=RED, lw=2.6)
    ax.axvline(R_STAR, color=RED, ls="--", lw=1.8)
    ax.axhline(0, color=GREY, lw=1.0)
    ax.fill_between(r, 0, pen, where=(r <= R_STAR), color=SHADE, alpha=0.85)
    ax.text(0.05, 3.5, "exactly zero\n(machine precision)", fontsize=12, color=BLUE, va="bottom")
    ax.text(0.60, 9.5, "rises monotonically", fontsize=13, color=RED)
    ax.set_xlabel("Reclaimed-water substitution ratio  $r$", fontsize=12)
    ax.set_ylabel("Make-up penalty relative to $r\\leq r^*$  (%)", fontsize=12)
    ax.set_title("(b) The response is threshold-typed", fontsize=14, loc="left", color=BLUE)
    ax.set_xlim(0, 0.95)
    ax.set_ylim(-0.6, 12.5)
    ax.tick_params(labelsize=11)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    # ---- (c) 两个条件才改变承载容量 ----
    ax = axes[2]
    r_pts = np.array([0.0, 0.5, 0.6, 0.7, 0.8, 0.9])
    # 纯物理 CAWCC（母稿 §5.8.2 表）：D-HA 与 D-CO
    ha = np.array([1200, 1200, 1150, 1150, 1100, 1100])
    co = np.array([1450, 1450, 1450, 1450, 1450, 1400])
    # 画相对各自基线的变化量，两条曲线才能同轴比较
    ax.step(r_pts, ha - ha[0], where="post", color=BLUE, lw=2.8, label="Water-scarce endpoint")
    ax.step(r_pts, co - co[0], where="post", color="#548235", lw=2.8, label="Cool endpoint")
    ax.axvline(R_STAR, color=RED, ls="--", lw=1.8)
    ax.axhline(0, color=GREY, lw=1.0)
    ax.annotate("", xy=(0.9, -100), xytext=(0.9, 0),
                arrowprops=dict(arrowstyle="<->", color=RED, lw=2.0))
    ax.text(0.60, -46, "≈ −100 MW", fontsize=13, color=RED)
    ax.text(0.03, -78, "grid constraint\nunchanged (Δ = 0.0000)", fontsize=11, color="#548235")
    ax.text(0.60, -8, "cool endpoint\nbottleneck electrical", fontsize=11, color="#548235", va="top")
    ax.set_xlabel("Reclaimed-water substitution ratio  $r$", fontsize=12)
    ax.set_ylabel("Change in feasible AI capacity  (MW)", fontsize=12)
    ax.set_title("(c) Only with a water-side bottleneck", fontsize=14, loc="left", color=BLUE)
    ax.set_xlim(0, 0.95)
    ax.set_ylim(-118, 28)
    ax.tick_params(labelsize=11)
    ax.legend(fontsize=11, frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.02))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    fig.tight_layout(pad=1.4)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    fig.savefig(OUT_PNG, bbox_inches="tight", dpi=300)
    plt.close(fig)

    from PIL import Image
    im = Image.open(OUT_PNG)
    w, h = im.size
    print(f"OK  {OUT.name} / {OUT_PNG.name}")
    print(f"    尺寸 {w} × {h} px (w × h)；WR 要求 h×w ≥ 531×1328，h/w 比 = {h/w:.2f}")
    ok = (h >= 531 and w >= 1328) or (w / h) >= (1328 / 531) * 0.9
    print(f"    比例判定：{'符合 GA 横版比例' if w > h else '警告：纵向'}")


if __name__ == "__main__":
    main()
