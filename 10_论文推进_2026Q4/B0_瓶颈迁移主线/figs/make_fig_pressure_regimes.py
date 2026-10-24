# -*- coding: utf-8 -*-
"""E-B2 图件：外部压力情景下的承载瓶颈。

三张图：
  FigB2a  四情景（G0/G1/G2/G3）× 两域的 CAWCC 柱状 + 首失效侧别
  FigB2b  CAWCC 对 r 的响应族（每情景一条曲线，看水质效应是否被压力放大）
  FigB2c  压力损失热图（情景 × 域，相对 G0 的容量损失）

用法: python figs/make_fig_pressure_regimes.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from figstyle_b0 import (  # noqa: E402
    C_CO, C_GRID, C_HA, C_OTHER, C_POLICY, C_WATER, R2, apply_style, save,
)

apply_style()

DOMAIN_NAME = {"ha": "D-HA 缺水端", "co": "D-CO 凉爽端"}
SCEN_ZH = {"G0": "G0 基准", "G1": "G1 高温", "G2": "G2 干旱", "G3": "G3 复合"}
SIDE_COLOR = {"水侧": C_WATER, "电网侧": C_GRID, "政策": C_POLICY,
              "社会供水": C_OTHER, "其他": C_OTHER, "未失效": "#cbd5e0"}
SCEN_ORDER = ["G0", "G1", "G2", "G3"]


def load() -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(R2 / "pressure_regime_scan.csv", encoding="utf-8-sig")
    summ_path = R2 / "pressure_regime_summary.json"
    summary = json.loads(summ_path.read_text(encoding="utf-8")) if summ_path.exists() else {}
    return df, summary


# ---------------------------------------------------------------- B2a
def fig_b2a(df: pd.DataFrame) -> list[Path]:
    """四情景 CAWCC 柱状（r=0.5 切片）+ 首失效侧别着色。"""
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 2.9), sharey=True)
    for ax, domain in zip(axes, ("ha", "co")):
        sub = df[(df["域"] == domain) & np.isclose(df["替代率r"], 0.5)]
        sub = sub.set_index("情景").reindex(SCEN_ORDER)
        vals = pd.to_numeric(sub["CAWCC_物理_MW"], errors="coerce").to_numpy(float)
        cols = [SIDE_COLOR.get(str(s), C_OTHER) for s in sub["侧别_物理"]]
        x = np.arange(len(SCEN_ORDER))
        ax.bar(x, vals, color=cols, width=0.62, alpha=0.92, edgecolor="white",
               linewidth=0.6)
        for i, v in enumerate(vals):
            if np.isfinite(v):
                ax.text(i, v + 14, f"{v:.0f}", ha="center", fontsize=6.9)
                side = str(sub["侧别_物理"].iloc[i])
                ax.text(i, max(v * 0.12, 30), side, ha="center", fontsize=6.0,
                        color="white", rotation=90)
            else:
                # 显式标出不可行情景，而不是让它静默缺柱
                ax.text(i, 40, "基线\n不可行", ha="center", va="bottom", fontsize=6.4,
                        color="#742a2a")
        ax.set_xticks(x)
        ax.set_xticklabels([SCEN_ZH[s] for s in SCEN_ORDER], fontsize=6.6)
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) {DOMAIN_NAME[domain]}", loc="left")
        ax.set_ylabel("CAWCC（MW）")
        ax.grid(axis="y", color="#edf2f7", lw=0.5)
        ax.set_axisbelow(True)
        ax.set_ylim(0, max(np.nanmax(vals) * 1.20, 200))
    for key, color in (("水侧", C_WATER), ("电网侧", C_GRID), ("社会供水", C_OTHER)):
        axes[0].bar(0, 0, color=color, label=key)
    axes[0].legend(loc="upper right", fontsize=6.2, title="首失效侧别", title_fontsize=6.0)

    fig.suptitle("外部压力情景：高温压缩容量但瓶颈身份不变；干旱使容量崩溃并翻转瓶颈",
                 fontsize=9.0)
    fig.text(0.01, 0.02,
             "切片 $r$ = 0.5（阈值以下，无水质惩罚）。柱色为首失效约束的侧别。"
             "复合情景 G3 在两域均无可行解，故以「基线不可行」标注而非省略。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.10, left=0.075, right=0.985, top=0.79, bottom=0.215)
    return save(fig, "FigS12_pressure_regimes")


# ---------------------------------------------------------------- B2b
def fig_b2b(df: pd.DataFrame) -> list[Path]:
    """CAWCC 对 r 的响应族：每情景一条曲线。"""
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 2.9), sharey=True)
    palette = {"G0": "#2d3748", "G1": "#c53030", "G2": "#c05621", "G3": "#6b46c1"}
    for ax, domain in zip(axes, ("ha", "co")):
        sub = df[df["域"] == domain]
        for scen in SCEN_ORDER:
            s = sub[sub["情景"] == scen].sort_values("替代率r")
            if s.empty:
                continue
            ax.plot(s["替代率r"], s["CAWCC_物理_MW"], marker="o", ms=3.4, lw=1.3,
                    color=palette[scen], label=SCEN_ZH[scen])
        ax.set_xlabel("再生水替代率 $r$")
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) {DOMAIN_NAME[domain]}", loc="left")
        ax.grid(color="#edf2f7", lw=0.5)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("CAWCC（MW）")
    axes[0].legend(loc="lower left", fontsize=6.0, ncol=2)
    fig.suptitle("水质惩罚的容量效应在压力情景下是否放大：各情景曲线的下降斜率对比",
                 fontsize=9.0)
    fig.text(0.01, 0.02,
             "纯物理约束口径。曲线下降的陡缓即水质惩罚的容量后果，"
             "不同情景的斜率差异说明压力是否放大该效应。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.10, left=0.075, right=0.985, top=0.79, bottom=0.215)
    return save(fig, "FigS13_pressure_ratio_response")


# ---------------------------------------------------------------- B2c
def fig_b2c(summary: dict) -> list[Path]:
    """压力损失热图：情景 × 域，相对 G0 的容量损失。"""
    rows, domains = [], ["ha", "co"]
    for domain in domains:
        entry = summary.get("域", {}).get(domain, {})
        ref = entry.get("G0", {}).get("CAWCC_r0.5_MW")
        row = {}
        for scen in SCEN_ORDER:
            cur = entry.get(scen, {}).get("CAWCC_r0.5_MW")
            row[scen] = (None if (cur is None or ref is None) else float(cur - ref))
        rows.append(row)
    mat = pd.DataFrame(rows, index=domains)

    fig, ax = plt.subplots(figsize=(5.2, 2.3))
    data = mat.to_numpy(float)
    vmax = max(abs(np.nanmin(data)), abs(np.nanmax(data)), 50.0)
    im = ax.imshow(data, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(SCEN_ORDER)))
    ax.set_xticklabels([SCEN_ZH[s] for s in SCEN_ORDER], fontsize=7)
    ax.set_yticks(np.arange(len(domains)))
    ax.set_yticklabels([DOMAIN_NAME[d] for d in domains], fontsize=7)
    for i in range(len(domains)):
        for j in range(len(SCEN_ORDER)):
            v = data[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:+.0f}", ha="center", va="center", fontsize=7.4,
                        color="white" if abs(v) > vmax * 0.55 else "#1a202c")
    ax.set_title("相对 G0 的承载容量变化（MW，r = 0.5）", loc="left")
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("ΔCAWCC（MW）", fontsize=7)
    cb.ax.tick_params(labelsize=6)

    fig.suptitle("压力情景的容量代价：干旱与复合情景使缺水端损失最多", fontsize=9.0)
    fig.text(0.01, 0.015,
             "G0 为同一 r 下的基准；负值表示压力降低容量。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(left=0.20, right=0.90, top=0.80, bottom=0.20)
    return save(fig, "FigS14_pressure_loss_heatmap")


def main() -> None:
    df, summary = load()
    out = []
    out += fig_b2a(df)
    out += fig_b2b(df)
    if summary:
        out += fig_b2c(summary)
    print(f"[OK] {len(out)} files")
    for p in out:
        print(" ", p.name)


if __name__ == "__main__":
    main()
