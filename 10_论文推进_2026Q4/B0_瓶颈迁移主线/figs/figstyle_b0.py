# -*- coding: utf-8 -*-
"""B0 瓶颈迁移主线 —— 六主图共享样式与数据加载工具。

设计原则（继承 A37_六主图_v4/figstyle_a37.py 的框架，不改动该文件）:
1. **单一数据入口**: 所有数值一律经 load_* 函数从权威产物读取, 图脚本内不得手写数值。
2. **样式复用**: 复用 `10_论文推进_2026Q4/figstyle.py` 的调色板, 叠加 Nature 风格。
3. **门禁**: 每个 load_* 返回的 DataFrame 带 n; 图注必须显式写出限定。
4. **溯源**: SOURCE 字典登记每个数据文件的相对路径, 供 figure_index 使用。

⚠ 导入顺序: 必须先 matplotlib.use("Agg") 再 import 本模块 (它 import pyplot)。
"""
from __future__ import annotations

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
HERE = Path(__file__).resolve().parent          # B0_瓶颈迁移主线/figs/
B0 = HERE.parent                                # B0_瓶颈迁移主线/
ROOT = B0.parent                                # 10_论文推进_2026Q4/
PROJ = ROOT.parent                              # 算力中心/
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
OUT = HERE                                      # 图件输出到 figs/

# 复用既有样式模块（只读导入）
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from figstyle import BLUE, ORANGE, RED, GREY, GREEN  # noqa: E402
except Exception:  # 回退：样式模块缺失时用等价色
    BLUE, ORANGE, RED, GREY, GREEN = "#2b6cb0", "#c05621", "#9b2c2c", "#a0aec0", "#2c7a7b"

PURPLE, TEAL, BROWN, PINK = "#6b46c1", "#2c7a7b", "#8b5a2b", "#b83280"

# 语义固定配色 —— 全册统一
C_WATER = "#2b6cb0"      # 水源侧约束
C_GRID = "#c05621"       # 电网侧约束
C_POLICY = "#6b46c1"     # 政策约束
C_OTHER = "#a0aec0"      # 其他/非 informative
C_HA = "#2b6cb0"
C_CO = "#c05621"

DOMAIN_LABEL = {"ha": "D-HA (缺水—高冷负荷端)", "co": "D-CO (气候凉爽端)"}

# 约束的侧别分类（用于配色与叙事）
CONSTRAINT_SIDE = {
    "max_source_abstraction_ratio": "water",
    "max_wtw_utilization": "water",
    "peak_capacity_ratio": "water",
    "mean_source_abstraction_ratio": "water",
    "mean_wtw_utilization": "water",
    "mean_total_demand_to_wtw_capacity": "water",
    "max_wwtw_utilization": "water",
    "mean_wwtw_utilization": "water",
    "max_daily_average_grid_connection_ratio": "grid",
    "max_local_connection_ratio": "water",
    "mean_daily_average_grid_connection_ratio": "grid",
    "mean_local_connection_ratio": "water",
    "reclaimed_water_substitution_ratio": "policy",
    "system_reliability_fraction": "social",
    "domestic_unmet_ml": "social",
    "unmet_cooling_water_ml": "social",
}

SIDE_COLOR = {"water": C_WATER, "grid": C_GRID, "policy": C_POLICY,
              "social": C_OTHER, "other": C_OTHER}

# 约束的中文简称（图内标签用）
CONSTRAINT_SHORT = {
    "max_source_abstraction_ratio": "水源取水比",
    "max_wtw_utilization": "给水厂利用率",
    "max_wwtw_utilization": "污水厂利用率",
    "peak_capacity_ratio": "峰值能力比",
    "max_daily_average_grid_connection_ratio": "电网接网比",
    "max_local_connection_ratio": "本地配水接入比",
    "reclaimed_water_substitution_ratio": "再生水替代率",
    "system_reliability_fraction": "系统可靠度",
    "domestic_unmet_ml": "居民未满足量",
    "unmet_cooling_water_ml": "冷却未满足量",
    "mean_source_abstraction_ratio": "水源取水比(年)",
    "mean_wtw_utilization": "给水厂利用率(年)",
    "mean_wwtw_utilization": "污水厂利用率(年)",
    "mean_daily_average_grid_connection_ratio": "电网接网比(年)",
    "mean_local_connection_ratio": "本地配水接入比(年)",
    "mean_total_demand_to_wtw_capacity": "峰值能力比(年)",
}

# ----------------------------------------------------------------------------
# 样式
# ----------------------------------------------------------------------------
def apply_style() -> None:
    # 中文字体：优先 SimHei / Microsoft YaHei（本机已确认可用），
    # 避免 DejaVu Sans 缺 CJK 字形导致中文变方框。
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [
            "SimHei", "Microsoft YaHei", "Noto Sans CJK SC",
            "Source Han Sans SC", "DejaVu Sans",
        ],
        "axes.unicode_minus": False,
        "font.size": 8.5,
        "axes.titlesize": 9.5,
        "axes.labelsize": 8.5,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.2,
        "legend.frameon": False,
        "figure.dpi": 150,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
    })


def save(fig, stem: str) -> list[Path]:
    paths = []
    for ext in ("pdf", "png"):
        p = OUT / f"{stem}.{ext}"
        fig.savefig(p)
        paths.append(p)
    plt.close(fig)
    return paths


# ----------------------------------------------------------------------------
# 数据加载（全部从权威产物读取，禁止硬编码）
# ----------------------------------------------------------------------------
def load_capacity_thresholds() -> dict:
    """六类 estimand 的承载阈值。"""
    out = {}
    for domain in ("ha", "co"):
        p = R2 / domain / "capacity_threshold_corrected.json"
        out[domain] = json.loads(p.read_text(encoding="utf-8"))
    return out


def load_constraint_boundaries() -> pd.DataFrame:
    """逐约束首次失效容量（瓶颈迁移序列）。"""
    frames = []
    for domain in ("ha", "co"):
        p = R2 / domain / "constraint_boundaries_corrected.csv"
        df = pd.read_csv(p, encoding="utf-8-sig")
        df.insert(0, "domain", domain)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_constraint_informativeness() -> pd.DataFrame:
    frames = []
    for domain in ("ha", "co"):
        p = R2 / domain / "constraint_informativeness.csv"
        df = pd.read_csv(p, encoding="utf-8-sig")
        df.insert(0, "domain", domain)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_binding_diagnosis() -> pd.DataFrame:
    """逐容量点各约束实际值（已扩展至 50–2000 MW）。"""
    return pd.read_csv(R2 / "constraint_binding_diagnosis.csv", encoding="utf-8-sig")


def load_interventions() -> pd.DataFrame:
    """干预成本效益（已用 50 MW 同网格重跑）。"""
    return pd.read_csv(R2 / "intervention_cost_benefit.csv", encoding="utf-8-sig")


def load_interventions_50mw() -> pd.DataFrame:
    frames = []
    for domain in ("ha", "co"):
        p = R2 / domain / "intervention_marginal_50mw.csv"
        df = pd.read_csv(p, encoding="utf-8-sig")
        df.insert(0, "domain", domain)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load_reservoir_ensemble() -> dict:
    """库容多序列集合（20 序列 × 10 年，hydrology_validation = NONE）。"""
    p = R2 / "reservoir_multiyear_ensemble.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_city_gradient_cawcc() -> pd.DataFrame:
    """城市梯度 CAWCC（已修复标签与年度列）。"""
    return pd.read_csv(R2 / "city_gradient_cawcc.csv", encoding="utf-8-sig")


def load_advanced_city() -> pd.DataFrame:
    return pd.read_csv(R2 / "advanced_city_cawcc.csv", encoding="utf-8-sig")


def load_threshold_perturbation() -> dict:
    p = R2 / "threshold_perturbation_summary.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_reuse_levers() -> dict:
    """再生水两个杠杆的边际曲线（无效杠杆 vs 真杠杆）。"""
    out = {}
    for domain in ("ha", "co"):
        out[domain] = {
            "capacity": pd.read_csv(
                R2 / domain / "reuse_marginal_curve.csv", encoding="utf-8-sig"
            ),
            "production": pd.read_csv(
                R2 / domain / "reuse_production_marginal_curve.csv", encoding="utf-8-sig"
            ),
        }
    return out


def side_of(name: str) -> str:
    return CONSTRAINT_SIDE.get(name, "other")


def short_of(name: str) -> str:
    return CONSTRAINT_SHORT.get(name, name)
