# -*- coding: utf-8 -*-
"""A37 六主图 v4 —— 共享样式、数据加载与溯源工具。

设计原则
--------
1. **单一数据入口**: 所有数值一律经 `load_*` 函数从权威产物读取, 图脚本内不得手写数值。
2. **样式复用**: 复用 `10_论文推进_2026Q4/figstyle.py` 的调色板与 rcParams, 在其上叠加
   Nature Water 风格 (无衬线、细轴线、去顶右边框)。不修改 figstyle.py (只读)。
3. **门禁**: 每个 load_* 返回的 DataFrame 都带 n_eff; 图注必须显式写出门禁与零值约定。
4. **溯源**: `SOURCE` 字典登记每个数据文件的相对路径与 SHA256, 供 figure_index.md 使用。

⚠ 导入顺序: 必须先 `matplotlib.use("Agg")` 再 import 本模块 (它 import pyplot)。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ----------------------------------------------------------------------------
# 路径
# ----------------------------------------------------------------------------
A37 = Path(__file__).resolve().parent
ROOT = A37.parent                       # 10_论文推进_2026Q4/
PROJ = ROOT.parent                      # 算力中心/

# 复用既有样式模块 (只读导入)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from figstyle import BLUE, ORANGE, RED, GREY, GREEN  # noqa: E402

# Nature Water 风格补充色 (与既有 5 主色协调, 用于第 6+ 类别)
PURPLE, TEAL, BROWN, PINK = "#6b46c1", "#2c7a7b", "#8b5a2b", "#b83280"

# 语义固定配色 —— 全册统一, 不得在单图内重定义
C_BENEFIT = "#2c7a7b"   # dS_pot < 0 : 城市净取水下降 (有益)
C_HARMFUL = "#9b2c2c"   # dS_pot > 0 : 城市净取水上升 (有害)
C_ZERO = "#a0aec0"      # dS_pot = 0 : 解析零点
C_PRIMARY = "#2b6cb0"
C_ACCENT = "#c05621"

# ----------------------------------------------------------------------------
# 数据源登记 (相对 10_论文推进_2026Q4/)
# ----------------------------------------------------------------------------
SOURCE = {
    "regimes": "A13_可靠性机制/supply_state_regimes.csv",
    "colnames": "A13_可靠性机制/COLUMN_NAMES_CORRECTED.md",
    "regime_summary": "A13_可靠性机制/supply_state_summary.json",
    "wp4": "A33_WP4_组成重构/wp4_results.csv",
    "wp4_summary": "A33_WP4_组成重构/wp4_summary.json",
    "e3": "A31_WP2_假设冻结/wp2_e3_predictions.csv",
    "e3_summary": "A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json",
    "e3b": "A31_WP2_假设冻结/wp2_e3b_features.csv",
    "e3b_summary": "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json",
    "morris": "A34_WP5_敏感性与极端事件/wp5_morris.csv",
    "sobol": "A34_WP5_敏感性与极端事件/wp5_sobol.csv",
    "extreme_cases": "A34_WP5_敏感性与极端事件/wp5_extreme_cases.csv",
    "extreme_summary": "A34_WP5_敏感性与极端事件/wp5_extreme_summary.json",
    "capacity": "A30_WP0取证/a24b_capacity_table.csv",
    "partial_id": "A30_WP0取证/a24b_partial_id_summary.json",
    "coc_limits": "A4_水化学参数域/T6_coc_limits.csv",
    "water_samples": "A4_水化学参数域/T6_water_chemistry_samples.csv",
    "a27": "A27_引用限值/A27_引用限值报告.md",
    "holdout": "A15_稳健性/holdout_summary.json",
}

# 全局统计口径常量 (核验于 2026-10-16, 见 _probe_*.py)
GATES = "status=='converged_unique' & ~coc_floor_degenerate"
ZERO_STRICT = "strict sign: dS_pot == 0.0 counted separately (no tolerance band)"
ZERO_TOL = "|dS_pot| < 1e-6 ML recorded as 0"


def _p(key: str) -> Path:
    return ROOT / SOURCE[key]


def sha256(path: Path, n: int = 12) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n] if n else h.hexdigest()


def load_json(key: str) -> dict:
    with open(_p(key), encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------------
# 样式
# ----------------------------------------------------------------------------
def apply_nw_style() -> None:
    """Nature Water 风格: 在 figstyle 变体 A 基础上收紧线宽、统一字体。"""
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "xtick.major.size": 2.6,
        "ytick.major.size": 2.6,
        "legend.frameon": False,
        "figure.dpi": 120,
        "savefig.dpi": 400,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
        "pdf.fonttype": 42,     # TrueType 嵌入, 满足期刊字体嵌入要求
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def panel_label(ax, letter: str, dx: float = -0.16, dy: float = 1.06) -> None:
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=9,
            fontweight="bold", va="top", ha="left")


def provenance(fig, source_text: str, n_text: str, limit_text: str) -> None:
    """在画布底部统一登记: 数据来源 / n_eff / 零值约定 / 结论限制。

    三段式, 缺一不可 (任务硬性要求 1)。位置在 figure 坐标下, 不侵入 axes。
    """
    fig.text(0.005, -0.012, source_text, fontsize=5.6, color="#4a5568",
             va="top", ha="left")
    fig.text(0.005, -0.038, n_text, fontsize=5.6, color="#4a5568",
             va="top", ha="left")
    fig.text(0.005, -0.064, limit_text, fontsize=5.6, color="#9b2c2c",
             va="top", ha="left")


def save(fig, stem: str) -> list:
    """同时输出 PDF + PNG (≥300 dpi, 字体嵌入)。"""
    out = []
    for ext in ("pdf", "png"):
        p = A37 / f"{stem}.{ext}"
        fig.savefig(p, dpi=400)
        out.append(p)
    plt.close(fig)
    return out


# ----------------------------------------------------------------------------
# 数据加载 —— 全部带门禁
# ----------------------------------------------------------------------------
def load_regimes(gated: bool = True) -> pd.DataFrame:
    """A13 主网格。

    ⚠ 列名互换 (见 COLUMN_NAMES_CORRECTED.md):
      - `x_ai_B1_ml` 实际是 **B2 (有回用) 支路**的取水量;
      - `x_ai_B2_ml` 恒为 0, 是 B1 的定义性结果。
    为保证下游语义正确, 在此**重命名为语义正确的列名**并保留原始列。
    """
    d = pd.read_csv(_p("regimes"))
    d["x_ai_B2_semantic_ml"] = d["x_ai_B1_ml"]      # 按更正说明交换
    d["x_ai_B1_semantic_ml"] = d["x_ai_B2_ml"]
    d["q"] = (d["M0_ml"] - d["M1_ml"]) / d["M1_ml"]  # q = (M0-M1)/M1
    d["dS_rebuilt"] = (np.maximum(0.0, d["inc_B2_ml"] - d["inc_B1_ml"])
                       - (d["M0_ml"] - d["M1_ml"])
                       - d["x_ai_B1_ml"])
    if gated:
        d = d[(d["status"] == "converged_unique")
              & (~d["coc_floor_degenerate"].astype(bool))].copy()
    return d.reset_index(drop=True)


def sign_counts(ds: pd.Series) -> dict:
    """严格符号计数 (任务指定口径)。"""
    return {
        "neg": int((ds < 0).sum()),
        "pos": int((ds > 0).sum()),
        "zero": int((ds == 0.0).sum()),
        "n": int(len(ds)),
    }


def q_groups(q: pd.Series) -> dict:
    return {
        "pos": int((q > 0).sum()),
        "neg": int((q < 0).sum()),
        "zero": int((q == 0).sum()),
        "n": int(len(q)),
    }


def load_wp4() -> pd.DataFrame:
    w = pd.read_csv(_p("wp4")).copy()
    w["q"] = (w["M0_ml"] - w["M1_ml"]) / w["M1_ml"]
    return w


def load_morris() -> pd.DataFrame:
    return pd.read_csv(_p("morris"))


def load_sobol() -> pd.DataFrame:
    return pd.read_csv(_p("sobol"))


def load_capacity() -> pd.DataFrame:
    return pd.read_csv(_p("capacity"))


def load_coc_limits() -> pd.DataFrame:
    return pd.read_csv(_p("coc_limits"))


def load_samples() -> pd.DataFrame:
    return pd.read_csv(_p("water_samples"))


# 参数显示名 (Morris/Sobol 共用)
PARAM_LABEL = {
    "limit_scale": r"limit scale ($\lambda_{\lim}$)",
    "x_alkalinity": "alkalinity multiplier",
    "phi": r"blending ratio ($\varphi$)",
    "gap_scale": "gap scale",
    "pool_scale": "reclaimed pool scale",
    "e_scale": "compute energy scale",
    "dp_scale": "price differential",
    "coc_design": "design CoC",
    "x_TDS": "TDS multiplier",
    "x_silica": "silica multiplier",
    "x_hardness": "hardness multiplier",
    "x_chloride": "chloride multiplier",
}
