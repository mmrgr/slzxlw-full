# -*- coding: utf-8 -*-
"""E-B3 多物种水质控制切换：r* 不是 TDS 专属，而是"最紧物种决定"。

【为什么必须做】
现有判据只用 TDS（L=2200 mg/L, C_p=180, C_r=650）推出 r*=0.5532，另有氯化物
一项（L=500, C_p=35, C_r=130）推出 0.6842。主稿只说"氯化物阈值更大，故 TDS 更紧"。
外部审计（2026-10-20 §5.1）指出：真实冷却系统的控制组分可能是钙硬度、碱度或
硅，而论文只覆盖 TDS 与氯化物，且没有说明"控制物种是否会随替代率切换"。

若判据只是恰好对 TDS 成立的一条式子，那它是个参数巧合；若它能表述为
"r* = min over species"，那它是结构性的。这个区别决定论文的定位。

【本实验要做什么（纯解析，不跑仿真）】
1. 对每个限制组分 s 计算 r*_s = (L_s/CoC_d − C_p,s)/(C_r,s − C_p,s)
2. 检查 r*_s 是否落在 (0,1)：落在区间外意味着该组分"永不约束"或"从一开始就约束"
3. 取有效组分的 min 作为系统 r*，并记录是哪个组分在控制
4. 在 r 的全域上，计算每个组分的"允许浓缩倍数上限" L_s/C_mix,s(r)，
   看控制组分是否随 r 切换（非单调情形下会切换）
5. 参数敏感性：对每个组分的 (L, C_p, C_r) 做 ±20% 扰动，看控制权归属是否翻转

【物种参数的取值与来源】
- TDS：2200 / 180 / 650 —— 项目配置（project.json cooling.water_quality_limits.TDS
  与 water_sources.*.quality.TDS）
- 氯化物：500 / 35 / 130 —— 同上（chloride）
- 钙硬度（as CaCO3）：1200 / 120 / 350 —— **需核实**：取循环冷却水常见工程区间
  （GB/T 50050 类规范对碳酸盐硬度有间接约束），非项目原配置，作为"若加入第三
  组分，结论是否改变"的压力测试，不进入主结果。

【产物】
  multispecies_rstar.csv          逐物种 r*、是否有效、控制权
  multispecies_control_map.csv    r 全域上控制物种与允许 CoC
  multispecies_sensitivity.csv    参数 ±20% 下控制权归属
  multispecies_summary.json       判定：判据是否为结构性 min 形式

【用法】python scripts/run_multispecies_threshold.py
"""
from __future__ import annotations

import argparse
import itertools
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
R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

COC_DESIGN = 5.0

# 物种参数：(限制浓度 L, 自来水浓度 C_p, 再生水浓度 C_r, 单位, 来源)
SPECIES: dict[str, dict] = {
    "TDS": {
        "L": 2200.0, "C_p": 180.0, "C_r": 650.0, "unit": "mg/L",
        "source": "project.json cooling.water_quality_limits.TDS / water_sources.*.quality.TDS",
        "in_main": True,
    },
    "chloride": {
        "L": 500.0, "C_p": 35.0, "C_r": 130.0, "unit": "mg/L",
        "source": "project.json cooling.water_quality_limits.chloride / water_sources.*.quality.chloride",
        "in_main": True,
    },
    "hardness_CaCO3": {
        "L": 1200.0, "C_p": 120.0, "C_r": 350.0, "unit": "mg/L as CaCO3",
        "source": "需核实：取循环冷却水工程常见区间，作为第三组分压力测试，非项目原配置",
        "in_main": False,
    },
}

R_GRID = np.round(np.arange(0.0, 1.0001, 0.01), 2)


def r_star(L: float, coc_d: float, c_p: float, c_r: float) -> float:
    """临界替代率。C_r <= C_p 时返回 nan（情形 IV，问题不存在）。"""
    if c_r <= c_p:
        return float("nan")
    return (L / coc_d - c_p) / (c_r - c_p)


def c_mix(r: float | np.ndarray, c_p: float, c_r: float):
    return c_p + np.asarray(r, dtype=float) * (c_r - c_p)


def allowed_coc(r, L: float, c_p: float, c_r: float, coc_d: float = COC_DESIGN):
    """该物种在水质限值下允许的浓缩倍数上限（可超过设计值，截断交给 min）。"""
    cm = c_mix(r, c_p, c_r)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(cm > 0, L / cm, np.inf)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perturb", type=float, default=0.20,
                    help="参数扰动幅度（默认 ±20%%）")
    args = ap.parse_args()

    # ---------- 1. 逐物种 r* ----------
    rows = []
    for name, sp in SPECIES.items():
        rs = r_star(sp["L"], COC_DESIGN, sp["C_p"], sp["C_r"])
        if np.isnan(rs):
            regime, effective = "IV（C_r≤C_p）", False
        elif rs <= 0.0:
            regime, effective = "I（从 r=0 即约束）", True
        elif rs >= 1.0:
            regime, effective = "III（r≤1 内永不约束）", False
        else:
            regime, effective = "II（区间内阈值）", True
        rows.append({
            "物种": name, "单位": sp["unit"],
            "L": sp["L"], "C_p": sp["C_p"], "C_r": sp["C_r"],
            "CoC_d": COC_DESIGN,
            "r星": rs, "情形": regime, "r≤1内有效": effective,
            "是否主结果": sp["in_main"], "参数来源": sp["source"],
        })
    sp_df = pd.DataFrame(rows)

    # 系统 r*：取所有"r≤1 内有效"物种的最小值
    eff = sp_df[sp_df["r≤1内有效"]]
    if len(eff):
        idx = eff["r星"].idxmin()
        system_rstar = float(eff.loc[idx, "r星"])
        controlling = str(eff.loc[idx, "物种"])
    else:
        system_rstar = float("nan")
        controlling = "无"

    # ---------- 2. r 全域控制物种映射 ----------
    control_rows = []
    for r in R_GRID:
        cocs = {}
        for name, sp in SPECIES.items():
            cocs[name] = float(min(COC_DESIGN, allowed_coc(r, sp["L"], sp["C_p"], sp["C_r"])))
        binding = min(cocs, key=lambda k: cocs[k])
        row = {"r": float(r)}
        for name in SPECIES:
            row[f"CoC上限_{name}"] = cocs[name]
        row["控制物种"] = binding if cocs[binding] < COC_DESIGN - 1e-12 else "未触发（设计值起控）"
        row["系统CoC"] = cocs[binding]
        control_rows.append(row)
    ctrl = pd.DataFrame(control_rows)
    # 切换点：控制物种发生变化的位置
    switches = []
    prev = None
    for _, row in ctrl.iterrows():
        cur = row["控制物种"]
        if prev is not None and cur != prev:
            switches.append({"r": float(row["r"]), "由": prev, "转为": cur})
        prev = cur

    # ---------- 3b. 全因子网格：三个物种参数各自在文献区间内变化 -> 控制权归属 ----------
    # 目的：不依赖某一组"假定值"。把每个物种的 (L, C_r) 在合理区间上网格化，
    # 看"最紧物种"的分布，从而判断"TDS 是天然最紧"还是"取决于参数"。
    grid_L = {"TDS": (1500.0, 3000.0), "chloride": (300.0, 700.0),
              "hardness_CaCO3": (600.0, 1800.0)}
    grid_Cr = {"TDS": (450.0, 900.0), "chloride": (90.0, 220.0),
               "hardness_CaCO3": (220.0, 500.0)}
    n_axis = 5
    axes_L = {k: np.linspace(*v, n_axis) for k, v in grid_L.items()}
    axes_R = {k: np.linspace(*v, n_axis) for k, v in grid_Cr.items()}

    grid_rows = []
    for L_tds in axes_L["TDS"]:
        for cr_tds in axes_R["TDS"]:
            for L_cl in axes_L["chloride"]:
                for cr_cl in axes_R["chloride"]:
                    for L_hd in axes_L["hardness_CaCO3"]:
                        for cr_hd in axes_R["hardness_CaCO3"]:
                            cand = {
                                "TDS": r_star(L_tds, COC_DESIGN, 180.0, cr_tds),
                                "chloride": r_star(L_cl, COC_DESIGN, 35.0, cr_cl),
                                "hardness_CaCO3": r_star(L_hd, COC_DESIGN, 120.0, cr_hd),
                            }
                            valid = {k: v for k, v in cand.items()
                                     if not np.isnan(v) and v <= 1.0}
                            if not valid:
                                continue
                            win = min(valid, key=lambda k: valid[k])
                            grid_rows.append({
                                "控制物种": win,
                                "系统r星": float(valid[win]),
                                "TDS_r星": cand["TDS"],
                                "chloride_r星": cand["chloride"],
                                "hardness_r星": cand["hardness_CaCO3"],
                            })
    grid = pd.DataFrame(grid_rows)
    if len(grid):
        grid.to_csv(OUT / "multispecies_grid.csv", index=False, encoding="utf-8-sig")
        grid_counts = grid["控制物种"].value_counts()
    else:
        grid_counts = pd.Series(dtype=int)

    # ---------- 4. 参数敏感性：控制权归属是否翻转 ----------
    sens_rows = []
    keys = ("L", "C_p", "C_r")
    for name, sp in SPECIES.items():
        for key, sign in itertools.product(keys, (-1, 1)):
            trial = dict(sp)
            trial[key] = sp[key] * (1.0 + sign * args.perturb)
            rs_all = {}
            for other, osp in SPECIES.items():
                if other == name:
                    rs_all[other] = r_star(trial["L"], COC_DESIGN,
                                           trial["C_p"], trial["C_r"])
                else:
                    rs_all[other] = r_star(osp["L"], COC_DESIGN, osp["C_p"], osp["C_r"])
            valid = {k: v for k, v in rs_all.items() if not np.isnan(v) and v <= 1.0}
            if valid:
                ctrl_name = min(valid, key=lambda k: valid[k])
                sens_rows.append({
                    "扰动对象": name, "扰动参数": key,
                    "扰动方向": "+" if sign > 0 else "−",
                    "扰动后取值": trial[key],
                    f"{name}_r星": rs_all[name],
                    "系统r星": float(valid[ctrl_name]),
                    "控制物种": ctrl_name,
                    "控制权是否翻转": ctrl_name != controlling,
                })
    sens = pd.DataFrame(sens_rows)

    # ---------- 4. 恰好的巧合检验：k*=3.50 与 COC 3.5 ----------
    # 记录这一点供论文防御用：k* 是供水结构比，COC 是浓缩倍数，量纲与定义都不同
    k_star = 3.50
    coincidence = {
        "k_star": k_star,
        "k_star_定义": "城市自来水用量 / 再生水用量之比（供水结构，无量纲）",
        "中试COC上限": 3.5,
        "中试COC_定义": "冷却塔循环水浓缩倍数（设施运行，无量纲）",
        "判定": "数值相近但定义、量纲来源、计算路径均不同，属巧合，无推导关系",
    }

    # ---------- 输出 ----------
    sp_df.to_csv(OUT / "multispecies_rstar.csv", index=False, encoding="utf-8-sig")
    ctrl.to_csv(OUT / "multispecies_control_map.csv", index=False, encoding="utf-8-sig")
    sens.to_csv(OUT / "multispecies_sensitivity.csv", index=False, encoding="utf-8-sig")

    summary = {
        "CoC_design": COC_DESIGN,
        "物种": {k: {kk: vv for kk, vv in v.items()} for k, v in SPECIES.items()},
        "系统r星": system_rstar,
        "控制物种": controlling,
        "各物种r星": {r["物种"]: r["r星"] for r in rows},
        "各物种情形": {r["物种"]: r["情形"] for r in rows},
        "控制权切换点": switches,
        "控制权切换次数": len(switches),
        "全因子网格": {
            "网格轴": {"L": {k: list(map(float, v)) for k, v in axes_L.items()},
                       "C_r": {k: list(map(float, v)) for k, v in axes_R.items()}},
            "组合数": int(len(grid)),
            "控制物种分布": {str(k): int(v) for k, v in grid_counts.items()},
            "控制物种占比": {str(k): float(v / len(grid))
                             for k, v in grid_counts.items()} if len(grid) else {},
            "系统r星_范围": [float(grid["系统r星"].min()),
                             float(grid["系统r星"].max())] if len(grid) else None,
        },
        "敏感性": {
            "扰动幅度": args.perturb,
            "组合数": int(len(sens)),
            "控制权翻转次数": int(sens["控制权是否翻转"].sum()),
            "翻转明细": sens[sens["控制权是否翻转"]].to_dict("records"),
        },
        "k星与CoC数值巧合说明": coincidence,
        "结论": {},
    }
    # 结构性判定
    main_only = [r for r in rows if r["是否主结果"]]
    main_eff = [r for r in main_only if r["r≤1内有效"]]
    summary["结论"] = {
        "判据是否为min形式": len(main_eff) >= 2,
        "主结果物种数": len(main_only),
        "主结果中有效物种数": len(main_eff),
        "控制物种是否随r切换": len(switches) > 0,
        "TDS是否为主结果中的最紧物种": (
            controlling == "TDS" and any(r["物种"] == "TDS" for r in main_only)
        ),
        "第三组分是否改变系统r星": (
            any(r["物种"] == "hardness_CaCO3" and r["r≤1内有效"] for r in rows)
            and any(r["物种"] == "hardness_CaCO3"
                    for r in rows if r["r星"] == system_rstar)
        ),
    }
    (OUT / "multispecies_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("[OK] multispecies_rstar.csv")
    print(sp_df[["物种", "L", "C_p", "C_r", "r星", "情形", "r≤1内有效"]].to_string(index=False))
    print(f"\n系统 r* = {system_rstar:.4f}（控制物种：{controlling}）")
    print(f"控制权切换：{len(switches)} 次 → {switches}")
    print(f"\n敏感性：{len(sens)} 个组合，控制权翻转 {int(sens['控制权是否翻转'].sum())} 次")
    if len(sens[sens["控制权是否翻转"]]):
        print(sens[sens["控制权是否翻转"]][
            ["扰动对象", "扰动参数", "扰动方向", "控制物种"]
        ].to_string(index=False))
    print("\n[OK] multispecies_control_map.csv / multispecies_sensitivity.csv / summary.json")
    if len(grid):
        print(f"\n全因子网格 {len(grid)} 组合，控制物种分布：")
        for k, v in grid_counts.items():
            print(f"  {k:<16} {v:>5} ({v/len(grid)*100:.1f}%)")
        print(f"  系统 r* 范围：{grid['系统r星'].min():.4f} – {grid['系统r星'].max():.4f}")

    # 控制物种在 r 全域的覆盖统计
    counts = ctrl["控制物种"].value_counts()
    print(f"\nr∈[0,1] 上控制物种覆盖的格点数（共 {len(ctrl)}）：")
    print(counts.to_string())


if __name__ == "__main__":
    main()
