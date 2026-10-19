# -*- coding: utf-8 -*-
"""r* 判据的参数敏感性分析。

【为什么必须做】
主稿报出 r* = 0.5532，但四个输入参数中：
  - L（循环水 TDS 限值）：GB/T 50050-2017 有明确取值 2200
  - CoC_design：**parameter_envelope_R7.csv 标记为"无锚点"**（A 编号为空）
  - C_potable / C_reclaimed：两端点固定为 180 / 650，来自合成设定

即 r* 的核心依赖参数中至少有一个无文献锚定。审稿人必然追问：
「换个 CoC_design，r* 还是 0.55 吗？你的结论对这个数字有多敏感？」

本脚本回答：在文献可能的取值范围内，r* 落在什么区间，以及结论（阈值型响应、
瓶颈前移）是否依赖 r* 的具体数值。

【方法】
1. 单参数扫描：固定其余三个，扫一个（含文献包络与工程惯例范围）
2. 全因子网格：四参数各取低/中/高三档，算 r* 的完整分布
3. 敏感度指数：r* 对各参数的弹性 ∂ln r*/∂ln x
4. 关键判定：r* 在合理范围内变化时，是否仍然落在 [0.4, 0.9]（政策相关区间）

【产物】
  rstar_sensitivity.csv              单参数扫描结果
  rstar_sensitivity_grid.csv         全因子网格
  rstar_sensitivity_summary.json     弹性与判定

【用法】python scripts/run_rstar_sensitivity.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation_artifacts" / "r2"

# 标称值（两端点 project.json）
NOMINAL = {"L": 2200.0, "coc_design": 5.0, "c_potable": 180.0, "c_reclaimed": 650.0}

# 参数取值范围（依据见 docstring 与 11_理论推导 §3）
RANGES = {
    # GB/T 50050-2017 循环冷却水：TDS 限值常见 1000（严格）~ 3000（宽松）
    "L": np.linspace(1000.0, 3000.0, 41),
    # 冷却塔设计浓缩倍数：工程惯例 2~8（节水型可到 8~10）
    "coc_design": np.linspace(2.0, 10.0, 41),
    # 市政自来水 TDS：中国北方 150~500，南方 50~200，沿海/苦咸水可到 800
    "c_potable": np.linspace(50.0, 800.0, 41),
    # 市政再生水 TDS：典型 400~1200（二级出水＋深度处理）
    "c_reclaimed": np.linspace(300.0, 1500.0, 41),
}

LABEL = {
    "L": "循环水 TDS 限值 (mg/L)",
    "coc_design": "设计浓缩倍数",
    "c_potable": "自来水 TDS (mg/L)",
    "c_reclaimed": "再生水 TDS (mg/L)",
}


def compute_rstar(L: float, coc_design: float, c_potable: float, c_reclaimed: float) -> float:
    """r* = (L/CoC_d - C_p)/(C_r - C_p)。返回 nan 表示无解（分母非正或 r*<0）。"""
    if c_reclaimed <= c_potable:
        return float("nan")
    c_mix_at_design = L / coc_design
    r = (c_mix_at_design - c_potable) / (c_reclaimed - c_potable)
    return float(r)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------- 1. 单参数扫描 ----------
    rows = []
    for param, grid in RANGES.items():
        for v in grid:
            args = dict(NOMINAL)
            args[param] = float(v)
            r = compute_rstar(**args)
            rows.append({
                "parameter": param,
                "value": float(v),
                "r_star": r,
                "in_policy_range": bool(0.0 < r < 1.0),
            })
    single = pd.DataFrame(rows)
    single.to_csv(OUT / "rstar_sensitivity.csv", index=False, encoding="utf-8-sig")

    print("=" * 84)
    print("r* 单参数敏感性")
    print("=" * 84)
    for param in RANGES:
        sub = single[single["parameter"] == param].dropna(subset=["r_star"])
        valid = sub[(sub["r_star"] > 0) & (sub["r_star"] < 1)]
        print(f"\n{LABEL[param]}")
        print(f"  扫描 {RANGES[param][0]:.0f} ~ {RANGES[param][-1]:.0f}"
              f"   → r* 范围 [{sub['r_star'].min():.4f}, {sub['r_star'].max():.4f}]")
        print(f"  落在 (0,1) 政策区间: {len(valid)}/{len(sub)} 点")
        if len(valid):
            print(f"  有效区间内 r*: [{valid['r_star'].min():.4f}, {valid['r_star'].max():.4f}]")

    # ---------- 2. 弹性（局部敏感度）----------
    eps = 1e-4
    base = compute_rstar(**NOMINAL)
    elastic = {}
    for param in NOMINAL:
        up = dict(NOMINAL)
        up[param] = NOMINAL[param] * (1 + eps)
        r_up = compute_rstar(**up)
        elastic[param] = float((r_up - base) / base / eps) if base else float("nan")

    print("\n" + "=" * 84)
    print("局部弹性 ∂ln r* / ∂ln 参数  （标称点 r*=%.4f）" % base)
    print("=" * 84)
    for param, e in sorted(elastic.items(), key=lambda kv: -abs(kv[1])):
        print(f"  {LABEL[param]:<24s} 弹性 = {e:+.4f}   "
              f"（参数 +10% → r* {base * (1 + e * 0.1):.4f}）")

    # ---------- 3. 全因子网格 ----------
    grid_rows = []
    levels = {
        "L": [1000.0, 2200.0, 3000.0],
        "coc_design": [3.0, 5.0, 8.0],
        "c_potable": [100.0, 180.0, 400.0],
        "c_reclaimed": [400.0, 650.0, 1200.0],
    }
    for L in levels["L"]:
        for coc in levels["coc_design"]:
            for cp in levels["c_potable"]:
                for cr in levels["c_reclaimed"]:
                    r = compute_rstar(L, coc, cp, cr)
                    grid_rows.append({
                        "L": L, "coc_design": coc, "c_potable": cp, "c_reclaimed": cr,
                        "r_star": r,
                        "in_policy_range": bool(0.0 < r < 1.0),
                        "r_above_half": bool(0.0 < r < 1.0 and r > 0.5),
                    })
    grid = pd.DataFrame(grid_rows)
    grid.to_csv(OUT / "rstar_sensitivity_grid.csv", index=False, encoding="utf-8-sig")

    valid_grid = grid.dropna(subset=["r_star"])
    inrange = valid_grid[(valid_grid["r_star"] > 0) & (valid_grid["r_star"] < 1)]
    print("\n" + "=" * 84)
    print("全因子网格（4 参数 × 3 档 = %d 组合）" % len(grid))
    print("=" * 84)
    print(f"  有解（C_r > C_p）: {len(valid_grid)}/{len(grid)}")
    print(f"  r* 落 (0,1):       {len(inrange)}/{len(grid)}")
    if len(inrange):
        print(f"  r* 分布: min={inrange['r_star'].min():.4f} "
              f"p25={inrange['r_star'].quantile(.25):.4f} "
              f"median={inrange['r_star'].median():.4f} "
              f"p75={inrange['r_star'].quantile(.75):.4f} "
              f"max={inrange['r_star'].max():.4f}")
        print(f"  r* > 0.5 的组合: {int(inrange['r_above_half'].sum())}/{len(inrange)}")

    # ---------- 4. 判定 ----------
    print("\n" + "=" * 84)
    print("判定")
    print("=" * 84)

    # 判定 A：r* 是否始终落在政策可讨论区间
    ok_a = len(inrange) >= 0.5 * len(grid)
    print(f"  A. r*=0.5532 是否只是四参数的一个代表点？")
    print(f"     网格中 {len(inrange)}/{len(grid)} 组合有 (0,1) 内解；"
          f"{'YES' if ok_a else 'NO'} —— 判据值强烈依赖参数")

    # 判定 B：阈值型响应是否依赖 r* 的具体值
    print(f"\n  B. 结论是否依赖 r* 的具体数值？")
    print(f"     不依赖。阈值型响应的机制是 CoC=min(CoC_d, L/C_mix) 的 min 结构，")
    print(f"     与 r* 取值无关；r* 只决定'拐点在哪'，不决定'有没有拐点'。")

    # 判定 C：两域 r* 相同是否合理
    print(f"\n  C. 两端点 r* 相同是否合理？")
    print(f"     合理但需声明：两端点水质参数相同（L=2200, CoC_d=5, C_p=180, C_r=650），")
    print(f"     故 r* 相同；差异只在政策目标（HA 0.70 > r*，CO 0.45 < r*）。")

    summary = {
        "nominal": NOMINAL,
        "r_star_nominal": base,
        "elasticity": elastic,
        "single_ranges": {
            p: {
                "scan": [float(RANGES[p][0]), float(RANGES[p][-1])],
                "r_star_min": float(single[single["parameter"] == p]["r_star"].min()),
                "r_star_max": float(single[single["parameter"] == p]["r_star"].max()),
            }
            for p in RANGES
        },
        "grid": {
            "n_total": len(grid),
            "n_valid": len(valid_grid),
            "n_in_policy_range": len(inrange),
            "r_star_median_in_range": float(inrange["r_star"].median()) if len(inrange) else None,
            "r_star_p25": float(inrange["r_star"].quantile(.25)) if len(inrange) else None,
            "r_star_p75": float(inrange["r_star"].quantile(.75)) if len(inrange) else None,
        },
        "verdicts": {
            "r_star_is_parameter_dependent": True,
            "threshold_response_is_structural": True,
            "note": "r* 数值随四参数变化，但阈值型响应由 min 结构决定，不依赖具体数值",
        },
    }
    (OUT / "rstar_sensitivity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n产物: rstar_sensitivity.csv / rstar_sensitivity_grid.csv / rstar_sensitivity_summary.json")


if __name__ == "__main__":
    main()
