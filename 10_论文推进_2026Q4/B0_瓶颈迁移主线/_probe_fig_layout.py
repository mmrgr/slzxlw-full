# -*- coding: utf-8 -*-
"""探测论文图件的版面结构：标题行、图表主体、脚注行的 y 位置。

论文图（matplotlib suptitle + fig.text 脚注）放进 PPT 时，标题和脚注与
幻灯片的标题/说明重复，需要裁掉，只留图表主体。

本脚本按"水平方向有多少非白像素"投影来判断：
  - 标题区：顶部若干行，非白像素少但集中在左侧长条
  - 图表主体：非白像素密度高
  - 脚注区：底部若干行，非白像素少且零散
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
FIGS = ["Fig1_framework", "Fig2_bottleneck_migration", "Fig3_constraint_trajectories",
        "Fig4_interventions", "Fig5_city_gradient_policy", "Fig6_timescale_reservoir"]


def profile(path: Path) -> None:
    im = Image.open(path).convert("RGB")
    a = np.array(im)
    ink = (a < 245).any(axis=2)          # 非白像素
    density = ink.sum(axis=1)            # 每行非白像素数
    h, w = density.shape[0], ink.shape[1]
    print("=" * 70)
    print(path.name, im.size)
    # 每 5 行打印一次密度，找出空白带
    print("  y范围        密度   说明")
    prev_blank = True
    for y0 in range(0, h, 5):
        seg = density[y0:y0 + 5]
        d = int(seg.max())
        blank = d == 0
        if blank != prev_blank:
            print("  y=%4d-%4d  %5d  %s" % (y0, y0 + 5, d, "空白带开始" if blank else "内容开始"))
            prev_blank = blank
    print("  末行密度:", int(density[-1]))


def main() -> None:
    for name in FIGS:
        p = HERE / (name + ".png")
        if p.exists():
            profile(p)


if __name__ == "__main__":
    main()
