"""WP3 第一步: 分配规则对城市级水效益的影响 (三规则 × 保护强度 λ).

设计
----
阶段1  用主模型在细网格上取冷却物理曲线: phi -> (M, CoC, potable, reclaimed)。
       蒸发量 E 与 phi 无关, 所以 M 完全由质量限定 CoC 决定。
阶段2  在该曲线上解城市再生水池的分配固定点:
           池容量 P(=WWTW 可回用量), 既有用户索取 I = lambda * P, AI 索取 D = phi * M(phi)
       三种规则:
           AI-priority      : AI 先取, 既有用户拿剩余
           incumbent-first  : 既有用户先取, AI 拿剩余
           proportional     : 按索取比例分配
       固定点: phi = R_AI / M(phi)
阶段3  输出 S_AI / S_city / eta_transfer 与闭合审计。

口径
----
* 共享情景下, 既有用户被挤占的自来水增量 = 从既有用户手里转走的再生水量,
  故 S_city = S_AI - (挤占量) + (回流再生量)。
* eta_transfer = S_city / S_AI; S_AI<=0 记 NA。
* 本脚本只读运行主模型, 不写回仓库目录, 不改变任何门禁。结果是模型诊断,
  不是经过设施验证的现实结论。
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(REPO / "src"))
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = REPO / "examples" / "cawcc_r2"
OUT = Path(__file__).resolve().parent
CAP_MW = 1000.0
GRID = [round(i / 40, 4) for i in range(0, 39)]          # 0.000 .. 0.950
RULES = {"ai_priority": 1.0, "proportional": 0.5, "incumbent_first": 0.0}


# ---------------------------------------------------------------- 阶段 1
def run_point(project: dict, timeseries: pd.DataFrame, target: float) -> dict:
    trial = copy.deepcopy(project)
    dc = trial["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = CAP_MW
    dc["cooling_storage_capacity_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["initial_cooling_storage_ml"] = 0.0
    dc["water_sources"]["reclaimed"]["target_fraction"] = target
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - target
    res = FullAIUWMModel(trial, timeseries).run()
    d = res.data_center_daily
    comp = res.component_daily
    m = float(d["external_withdrawal_ml"].sum())
    rec = float(d["reclaimed_water_ml"].sum())
    return {
        "f_requested": target,
        "phi_actual": rec / m if m else 0.0,
        "M_ml": m,
        "potable_ml": float(d["potable_water_ml"].sum()),
        "reclaimed_ml": rec,
        "CoC_mean": float(d["cycles_of_concentration"].mean()),
        "evap_ml": float(d["evaporation_ml"].sum()) if "evaporation_ml" in d else np.nan,
        "blowdown_ml": float(d["blowdown_ml"].sum()),
        "wwtw_treated_ml": float(comp.loc[comp["component_id"] == "WWTW1", "treated_ml"].sum()),
        "city_potable_ml": float(res.area_daily["potable_delivered_ml"].sum()),
    }


def build_curve(domain: str) -> pd.DataFrame:
    project = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / domain / "timeseries.csv")
    rows = [dict(run_point(project, ts, g), domain=domain) for g in GRID]
    return pd.DataFrame(rows).drop_duplicates(subset="phi_actual", keep="first")


# ---------------------------------------------------------------- 阶段 2
def solve_allocation(curve: pd.DataFrame, rule: str, gam: float) -> pd.DataFrame:
    """按规则把 AI 的再生水索取拆成"新供给"与"挤占既有用户"两部分.

    gamma = 挤占份额: AI 每用 1 单位再生水, 从既有用户手里转走 gamma 单位,
    其余 (1-gamma) 单位来自新增供给(扩容/回流再生/新处理能力)。
        机器人优先/AI-priority       : gamma = 1
        按比例 / proportional        : gamma 居中
        既有用户优先/incumbent-first: gamma = 0 (AI 只能用新增供给)
    """
    phi_grid = curve["phi_actual"].to_numpy()
    m_grid = curve["M_ml"].to_numpy()
    phi_max = float(phi_grid.max())
    out = []
    for _, row0 in curve.iterrows():
        f_req = float(row0["f_requested"])
        phi = float(np.clip(f_req, 0.0, phi_max))
        m = float(np.interp(phi, phi_grid, m_grid))
        r_ai = phi * m
        out.append({
            "rule": rule, "gamma": gam, "f_requested": f_req,
            "phi_effective": phi, "M_ml": m,
            "AI_reclaimed_ml": r_ai, "AI_potable_ml": m - r_ai,
            "reallocated_ml": gam * r_ai, "new_supply_ml": (1.0 - gam) * r_ai,
            "quality_limited": bool(f_req > phi_max),
        })
    return pd.DataFrame(out)


# ---------------------------------------------------------------- 阶段 3
def add_estimands(df: pd.DataFrame, curve: pd.DataFrame) -> pd.DataFrame:
    """S_city = (1-gamma)*R_AI - [M(phi) - M(0)]  (质量惩罚项)."""
    m0 = float(np.interp(0.0, curve["phi_actual"], curve["M_ml"]))
    res = []
    for _, r in df.iterrows():
        m = r["M_ml"]
        r_ai = r["AI_reclaimed_ml"]
        s_ai = m0 - r["AI_potable_ml"]                 # 园区自来水节约
        quality_penalty = m - m0                       # 总补水因 CoC 下降而增加的量
        s_city = (1.0 - r["gamma"]) * r_ai - quality_penalty
        res.append({
            **r.to_dict(),
            "M0_ml": m0,
            "S_AI_ml": s_ai,
            "S_city_ml": s_city,
            "quality_penalty_ml": quality_penalty,
            "eta_transfer": (s_city / s_ai) if s_ai > 1e-9 else np.nan,
        })
    return pd.DataFrame(res)


def gamma_star(df_curve: pd.DataFrame) -> pd.DataFrame:
    """临界挤占份额 gamma*(phi) = 1 - (M(phi)-M(0)) / (phi*M(phi))."""
    c = df_curve.sort_values("phi_actual")
    m0 = float(c["M_ml"].iloc[0])
    out = []
    for _, r in c.iterrows():
        phi, m = float(r["phi_actual"]), float(r["M_ml"])
        mu = phi * m
        g = 1.0 - (m - m0) / mu if mu > 1e-9 else np.nan
        out.append({"domain": r["domain"], "phi": phi, "M_ml": m, "mu_ml": mu,
                    "quality_penalty_ml": m - m0, "gamma_star": g})
    return pd.DataFrame(out)


def main() -> int:
    curves = []
    for domain in ("ha", "co"):
        c = build_curve(domain)
        curves.append(c)
        print(f"[curve] {domain}: {len(c)} 点, phi {c.phi_actual.min():.3f}->{c.phi_actual.max():.3f}, "
              f"evap std={c.evap_ml.std():.3g}, M0={c.M_ml.iloc[0]:.0f}")
    curve_all = pd.concat(curves, ignore_index=True)
    curve_all.to_csv(OUT / "stage1_cooling_curve.csv", index=False, encoding="utf-8-sig")

    gs = pd.concat([gamma_star(curve_all[curve_all.domain == d]) for d in ("ha", "co")], ignore_index=True)
    gs.to_csv(OUT / "stage1b_gamma_star.csv", index=False, encoding="utf-8-sig")
    print("\n[gamma*] 临界挤占份额 (S_city>0 当且仅当 gamma < gamma*):")
    print(gs.round(3).to_string(index=False))

    rows = []
    for domain in ("ha", "co"):
        c = curve_all[curve_all.domain == domain].sort_values("phi_actual")
        for rule, gam in RULES.items():
            rows.append(add_estimands(solve_allocation(c, rule, gam), c).assign(domain=domain))
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(OUT / "stage2_allocation_rules.csv", index=False, encoding="utf-8-sig")

    summary = (
        out.groupby(["domain", "rule", "gamma"])
        .apply(lambda g: pd.Series({
            "max_S_city_ml": g["S_city_ml"].max(),
            "S_AI_at_max_ML": g.loc[g["S_city_ml"].idxmax(), "S_AI_ml"],
            "eta_at_max": g.loc[g["S_city_ml"].idxmax(), "eta_transfer"],
            "phi_at_max": g.loc[g["S_city_ml"].idxmax(), "phi_effective"],
            "min_S_city_ml": g["S_city_ml"].min(),
        }), include_groups=False)
        .reset_index()
    )
    summary.to_csv(OUT / "stage3_summary.csv", index=False, encoding="utf-8-sig")
    print("\n[summary] 三规则下的城市效益:")
    print(summary.round(2).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
