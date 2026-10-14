"""图样式与调色板 —— 11 张定稿图共用的**唯一实现** (清理轮 2026-10-14, E-7)。

抽取前, 各作图脚本各自重复 `plt.rcParams.update({...})`, 且已经分化为两个变体:
    变体 A (无网格)  A10/make_fig5_boundary, A12/make_fig7_daily, A9/make_fig6,
                     A11/make_fig6_adaptation, T15
    变体 B (带网格)  A3/make_fig4 (主图 Fig.2), A6/make_fig2 (SI Fig.S2)
两变体各自保留为一个函数, **字典逐字照搬抽取前的内联内容**, 故渲染结果不变
(已用 6 个可运行脚本的 PNG 逐字节哈希验证)。

用法
----
子目录脚本 (Axx/…):
    import sys
    from pathlib import Path
    HERE = Path(__file__).resolve().parent
    sys.path.insert(0, str(HERE.parent))        # 指向 10_论文推进_2026Q4/
    from figstyle import apply_style            # 变体 A
    apply_style()
根目录脚本 (T15_finalize_figures.py) 直接 `from figstyle import apply_style`。

⚠ 本模块必须在 `matplotlib.use("Agg")` **之后**导入 (它 import pyplot)。
"""
from __future__ import annotations

import matplotlib.pyplot as plt

# 统一调色板: 11 张图使用的 5 主色 (原内联常量, 值不变)
BLUE, ORANGE, RED, GREY, GREEN = "#2b6cb0", "#c05621", "#9b2c2c", "#a0aec0", "#2f855a"

# 变体 A: 原 make_fig5_boundary / make_fig7_daily / make_fig6(A9) /
#         make_fig6_adaptation(A11) / T15 的内联字典 (逐字)
_RC_A = {"font.size": 9, "axes.linewidth": 0.8, "font.family": "DejaVu Sans",
         "axes.spines.top": False, "axes.spines.right": False}

# 变体 B: 原 make_fig4(A3) / make_fig2(A6) 的内联字典 (逐字)
_RC_B = {"font.size": 9, "axes.grid": True, "grid.alpha": .25,
         "axes.spines.top": False, "axes.spines.right": False}


def apply_style() -> None:
    """套用变体 A (无网格)。等价于各脚本原先内联的 rcParams.update。"""
    plt.rcParams.update(_RC_A)


def apply_style_grid() -> None:
    """套用变体 B (带网格)。等价于 A3/make_fig4、A6/make_fig2 原先内联的字典。"""
    plt.rcParams.update(_RC_B)
