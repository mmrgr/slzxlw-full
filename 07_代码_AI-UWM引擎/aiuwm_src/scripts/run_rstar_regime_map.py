# -*- coding: utf-8 -*-
"""r* 的完整分类学：三种情形与临界判据。

【为什么需要这个】
敏感性分析发现 81 个参数组合中只有 45 个落在 r*∈(0,1)：
  - 13 个 r* ≤ 0
  - 14 个 r* ≥ 1
  -  9 个无解（C_r ≤ C_p）

起初这看起来像"参数不合理"。进一步分析发现：**这些不是错误，而是三种物理上
不同且都有意义的情形**。仅当一个城市落在 r*∈(0,1) 时，"提高再生水比例"才是
一个有代价的政策选择；否则它要么恒有害、要么恒无害。

这把 r* 从"一个数字"升级为"一个分类判据"。这是论文更强的表述。

【三种情形】

情形 I   r* ≤ 0   ⟺  L/CoC_design ≤ C_potable
    物理含义：在设计浓缩倍数下，补水允许的最高含盐量**低于自来水本身的含盐量**。
    即：即使完全不用再生水（r=0），水质约束也是紧的。
    政策含义：**任何**再生水替代都会推高补水需求（不存在"纯收益区"）。
    典型：低 TDS 限值（1000）+ 高 CoC_design（8）+ 高自来水 TDS（400）。

情形 II  0 < r* < 1   （本文两端点所在）
    物理含义：存在一个真实的政策相关阈值。r ≤ r* 时纯收益，r > r* 时部分侵蚀。
    政策含义：**这是唯一"政策可选"的情形**——城市可以通过控制 r 来避免反噬。
    典型：本文 L=2200, CoC_d=5, C_p=180, C_r=650 → r*=0.5532。

情形 III  r* ≥ 1   ⟺  L/CoC_design ≥ C_reclaimed
    物理含义：即使 100% 用再生水，混合补水含盐量仍在允许范围内。
    政策含义：**水质约束永不生效**，提高 r 永远不反噬。
    典型：高 TDS 限值（3000）+ 低 CoC_design（3）+ 低再生水 TDS（400）。

情形 IV  C_reclaimed ≤ C_potable
    物理含义：再生水比自来水还干净（如 RO 产水）。
    政策含义：r 越大越好，无任何反噬；此时问题本身消失。

【产物】
  rstar_regime_map.csv        81 组合的分类结果
  rstar_regime_boundaries.json 三个临界条件的解析表达

【用法】python scripts/run_rstar_regime_map.py
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


def classify(L: float, coc_d: float, c_p: float, c_r: float) -> tuple[str, float, str]:
    """返回 (情形代码, r*, 说明)。"""
    if c_r <= c_p:
        return ("IV", float("nan"), "再生水不比自来水脏（C_r ≤ C_p），无反噬")
    r = (L / coc_d - c_p) / (c_r - c_p)
    if r <= 0.0:
        return ("I", r, "水质恒紧：r=0 时已触及浓缩倍数上限")
    if r >= 1.0:
        return ("III", r, "水质永不紧：100% 再生水仍不超限")
    return ("II", r, "存在政策相关阈值：r≤r* 纯收益，r>r* 部分侵蚀")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------- 全因子网格 + 分类 ----------
    levels = {
        "L": [1000.0, 1600.0, 2200.0, 3000.0],
        "coc_design": [2.0, 3.0, 5.0, 8.0, 10.0],
        "c_potable": [100.0, 180.0, 300.0, 400.0],
        "c_reclaimed": [400.0, 650.0, 900.0, 1200.0],
    }
    rows = []
    for L in levels["L"]:
        for coc in levels["coc_design"]:
            for cp in levels["c_potable"]:
                for cr in levels["c_reclaimed"]:
                    code, r, note = classify(L, coc, cp, cr)
                    l_over_coc = L / coc
                    # 2026-10-19 审计修复：三个 cond 是**各自独立**的原始判定，
                    # 在 c_reclaimed == c_potable（分母为 0、r* 发散）时会同时为真。
                    # 例：20 个 C_r==C_p 组合中 cond_IV 全 True，同时 cond_I 11 个、
                    # cond_III 9 个也为 True。最终 regime 由 classify() 的判定顺序
                    # （先 IV → 再 I → 再 III → 否则 II）保证互斥，但若下游复用 cond_*
                    # 列做筛选会得到矛盾结论。
                    # 故另加一组 condx_* 列（互斥化、按同一优先级），并保留 cond_* 原值。
                    raw_iv = bool(cr <= cp)
                    raw_i = bool(l_over_coc <= cp)
                    raw_iii = bool(l_over_coc >= cr)
                    if raw_iv:
                        x_iv, x_i, x_iii = True, False, False
                    elif raw_i:
                        x_iv, x_i, x_iii = False, True, False
                    elif raw_iii:
                        x_iv, x_i, x_iii = False, False, True
                    else:
                        x_iv = x_i = x_iii = False   # 落在情形 II
                    rows.append({
                        "L": L, "coc_design": coc, "c_potable": cp, "c_reclaimed": cr,
                        "regime": code, "r_star": r, "note": note,
                        # 三个临界条件（原始、非互斥；仅供逐条解读）
                        "L_over_coc": l_over_coc,
                        "cond_I": raw_i,
                        "cond_III": raw_iii,
                        "cond_IV": raw_iv,
                        # 互斥化版本（与 regime 列严格一致；下游筛选请用这组）
                        "condx_I": x_i,
                        "condx_III": x_iii,
                        "condx_IV": x_iv,
                        "condx_II": not (x_i or x_iii or x_iv),
                    })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "rstar_regime_map.csv", index=False, encoding="utf-8-sig")

    print("=" * 86)
    print("r* 分类学（%d 组合）" % len(df))
    print("=" * 86)
    counts = df["regime"].value_counts().sort_index()
    names = {
        "I": "情形 I  r*≤0   水质恒紧（任何替代都有代价）",
        "II": "情形 II 0<r*<1 存在政策相关阈值（本文所在）",
        "III": "情形 III r*≥1 水质永不紧（替代永远无代价）",
        "IV": "情形 IV C_r≤C_p 再生水不比自来水脏（无反噬）",
    }
    for code in ("I", "II", "III", "IV"):
        n = int(counts.get(code, 0))
        print(f"  {names[code]:<46s} {n:3d}  ({100*n/len(df):5.1f}%)")

    # ---------- 情形 II 的 r* 分布 ----------
    sub2 = df[df["regime"] == "II"]
    print("\n" + "-" * 86)
    print("情形 II 内部 r* 分布（这些城市才存在「政策选择」问题）")
    print("-" * 86)
    print(f"  n={len(sub2)}   min={sub2['r_star'].min():.4f}  "
          f"p25={sub2['r_star'].quantile(.25):.4f}  median={sub2['r_star'].median():.4f}  "
          f"p75={sub2['r_star'].quantile(.75):.4f}  max={sub2['r_star'].max():.4f}")

    # ---------- 临界条件的解析形式 ----------
    print("\n" + "-" * 86)
    print("三个临界条件的解析表达（可直接代入任意城市参数）")
    print("-" * 86)
    print("  情形 I   ⟺  L/CoC_design ≤ C_potable")
    print("              → 补水允许浓度低于自来水本身，r=0 时水质已紧")
    print("  情形 III ⟺  L/CoC_design ≥ C_reclaimed")
    print("              → 即使 100% 再生水也不超限，水质永不紧")
    print("  情形 IV  ⟺  C_reclaimed ≤ C_potable")
    print("              → 再生水更干净，问题消失")

    # ---------- 本文两端点的定位 ----------
    print("\n" + "-" * 86)
    print("本文两端点的定位")
    print("-" * 86)
    L, coc, cp, cr = 2200.0, 5.0, 180.0, 650.0
    code, r, note = classify(L, coc, cp, cr)
    print(f"  D-HA / D-CO:  L={L:.0f}, CoC_d={coc:.1f}, C_p={cp:.0f}, C_r={cr:.0f}")
    print(f"  → 情形 {code}，r* = {r:.4f}")
    print(f"  → {note}")
    print(f"  临界条件核验: L/CoC_d = {L/coc:.1f}")
    print(f"    vs C_p={cp:.0f}  → {'≤ C_p（情形I）' if L/coc <= cp else '> C_p（非I）'}")
    print(f"    vs C_r={cr:.0f}  → {'≥ C_r（情形III）' if L/coc >= cr else '< C_r（非III）'}")

    # ---------- 政策含义 ----------
    print("\n" + "-" * 86)
    print("政策含义（这是论文可以主张的强表述）")
    print("-" * 86)
    print("  只有情形 II 的城市面临「提高再生水比例是否有代价」的权衡问题。")
    print("  - 情形 I  的城市：任何替代都有代价 → 应优先降低再生水含盐量或提高 TDS 限值")
    print("  - 情形 III 的城市：替代永远无代价 → 可放心提高比例")
    print("  - 情形 IV  的城市：问题不存在")
    print("  → r* 不只是一个数，而是一个**城市分类判据**。")

    summary = {
        "n_total": len(df),
        "counts": {k: int(v) for k, v in counts.items()},
        "regime_II_stats": {
            "n": len(sub2),
            "min": float(sub2["r_star"].min()),
            "p25": float(sub2["r_star"].quantile(.25)),
            "median": float(sub2["r_star"].median()),
            "p75": float(sub2["r_star"].quantile(.75)),
            "max": float(sub2["r_star"].max()),
        },
        "boundaries": {
            "I": "L/CoC_design <= C_potable",
            "II": "C_potable < L/CoC_design < C_reclaimed",
            "III": "L/CoC_design >= C_reclaimed",
            "IV": "C_reclaimed <= C_potable",
        },
        "nominal_city": {
            "L": L, "coc_design": coc, "c_potable": cp, "c_reclaimed": cr,
            "regime": code, "r_star": r,
        },
    }
    (OUT / "rstar_regime_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n产物: rstar_regime_map.csv / rstar_regime_summary.json")


if __name__ == "__main__":
    main()
