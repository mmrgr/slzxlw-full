"""T1b — 既有用户"权利认定"口径扫描: 决定新增供给门槛的是制度, 不是物理。

预注册: ../A0_预注册/preregistration.md

T1 已证: 固定池下任何分配规则都给出 S_city <= 0, 正收益只能来自新增供给 ΔP。
T1b 追问: 需要多少 ΔP?

关键: 既有用户存在**大量未被满足的回用需求** (D - P ≈ 33 779 ML, HA)。
若这部分被认定为"既有权利"(rights), 新增能力必须先补它, 数据中心排在后面;
若只按"已交付存量"记账(booked), 新增能力立刻可给数据中心。

→ 门槛 ΔP* 从 ~0 (booked) 到 D-P (rights), 跨一个数量级。**门槛是政策变量。**
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(REPO / "src"))

from aiuwm.reclaimed_allocation import (  # noqa: E402
    AllocationRequest,
    allocate_shared_surplus,
)

R2 = REPO / "examples" / "cawcc_r2"
CURVE = HERE.parent / "A2_规则实验" / "stage1_cooling_curve.csv"
REUSE_FRACTION = {"ha": 0.16, "co": 0.15}
OMEGAS = [0.0, 0.25, 0.5, 0.75, 1.0]          # 权利认定: C = P + omega*(D-P)
DP_GRID = [0.0] + [round(1000.0 * i, 1) for i in range(1, 41)]   # 0..40000 ML 新增能力


def incumbent_demand(domain: str) -> tuple[float, float]:
    """返回 (已交付存量 P, 可回用总需求 D)。"""
    from aiuwm.full_engine import FullAIUWMModel
    proj = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / domain / "timeseries.csv")
    t = copy.deepcopy(proj)
    dc = t["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["cooling_storage_capacity_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["initial_cooling_storage_ml"] = 0.0
    dc["water_sources"]["reclaimed"]["target_fraction"] = 0.0
    dc["water_sources"]["potable"]["target_fraction"] = 1.0
    r = FullAIUWMModel(t, ts).run()
    a = r.area_daily
    d_total = float((a["demand_industrial_ml"] + a["demand_municipal_misc_ml"]).sum())
    p_deliv = float(a["reuse_delivered_ml"].sum())
    return p_deliv, d_total


def solve(domain: str, omega: float, d_p: float, phi_req: float,
          m_grid: np.ndarray, phi_grid: np.ndarray, p_base: float, d_dem: float) -> dict:
    m0 = float(np.interp(0.0, phi_grid, m_grid))
    claim = p_base + omega * (d_dem - p_base)      # 既有用户受保护的权利
    available = p_base + d_p
    phi = min(phi_req, 0.95)
    for _ in range(80):
        m = float(np.interp(phi, phi_grid, m_grid))
        ai_cap = phi * m
        res = allocate_shared_surplus(
            "t1b", available,
            [AllocationRequest("AI", demand_ml=ai_cap, potable_baseline_ml=m),
             AllocationRequest("INC", demand_ml=max(claim, 1e-9),
                               incumbent_reclaimed_ml=min(claim, available),
                               potable_baseline_ml=d_dem)],
        )
        ai = sum(a.total_allocated_ml for a in res.allocations if a.consumer_id == "AI")
        phi_new = ai / m if m > 0 else 0.0
        if abs(phi_new - phi) < 1e-12:
            phi = phi_new
            break
        phi = 0.5 * (phi + phi_new)
    m = float(np.interp(phi, phi_grid, m_grid))
    res = allocate_shared_surplus(
        "t1b", available,
        [AllocationRequest("AI", demand_ml=phi * m, potable_baseline_ml=m),
         AllocationRequest("INC", demand_ml=max(claim, 1e-9),
                           incumbent_reclaimed_ml=min(claim, available),
                           potable_baseline_ml=d_dem)],
    )
    ai = sum(a.total_allocated_ml for a in res.allocations if a.consumer_id == "AI")
    inc = sum(a.incumbent_allocated_ml for a in res.allocations if a.consumer_id == "INC")
    phi = ai / m if m > 0 else 0.0
    # 城市级: AI 少取的自来水 + 既有用户因多拿回用水而少取的自来水
    s_ai = m0 - (m - ai)
    s_city = s_ai + (inc - p_base)
    return {
        "domain": domain, "omega": omega, "dP_ml": d_p, "phi_requested": phi_req,
        "claim_ml": claim, "phi_actual": phi, "M_ml": m,
        "AI_reclaimed_ml": ai, "INC_reclaimed_ml": inc,
        "S_AI_ml": s_ai, "S_city_ml": s_city,
        "delta": (d_p / (phi_req * m)) if phi_req > 0 and m > 0 else np.nan,
        "eta_transfer": (s_city / s_ai) if s_ai > 1e-9 else np.nan,
        "AI_share_of_new": (ai / d_p) if d_p > 0 else np.nan,
    }


def main() -> int:
    c = pd.read_csv(CURVE)
    rows = []
    for domain in ("ha", "co"):
        d_curve = c[c.domain == domain].sort_values("phi_actual")
        phi_grid = d_curve["phi_actual"].to_numpy()
        m_grid = d_curve["M_ml"].to_numpy()
        p_base, d_dem = incumbent_demand(domain)
        print(f"[{domain}] P(已在用)={p_base:,.0f} ML  D(可回用需求)={d_dem:,.0f} ML  "
              f"缺口={d_dem-p_base:,.0f} ML")
        for omega in OMEGAS:
            for d_p in DP_GRID:
                for phi_req in (0.3, 0.5, 0.7):
                    rows.append(solve(domain, omega, d_p, phi_req, m_grid, phi_grid, p_base, d_dem))
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "T1b_claim_convention.csv", index=False, encoding="utf-8-sig")

    print("\n===== 城市净收益 S_city (ML) — HA, phi_req=0.7, 按权利认定 omega")
    piv = (df[(df.domain == "ha") & np.isclose(df.phi_requested, 0.7)]
           .pivot_table(index="dP_ml", columns="omega", values="S_city_ml"))
    print(piv.round(0).iloc[::5].to_string())

    print("\n===== AI 在新增能力中的份额 (HA, phi_req=0.7)")
    piv2 = (df[(df.domain == "ha") & np.isclose(df.phi_requested, 0.7)]
            .pivot_table(index="dP_ml", columns="omega", values="AI_share_of_new"))
    print(piv2.round(2).iloc[::5].to_string())

    thr = {}
    for dom in ("ha", "co"):
        for om in OMEGAS:
            s = df[(df.domain == dom) & np.isclose(df.omega, om) & np.isclose(df.phi_requested, 0.7)]
            s = s.sort_values("dP_ml")
            pos = s[s.S_city_ml > 1e-6]
            ai_pos = s[s.AI_reclaimed_ml > 1e-6]
            thr[f"{dom}|omega={om}"] = {
                "dP_star_city_benefit_ml": float(pos.dP_ml.min()) if len(pos) else None,
                "dP_star_AI_gets_water_ml": float(ai_pos.dP_ml.min()) if len(ai_pos) else None,
            }
    print("\n===== 门槛 ΔP* (phi_req=0.7)")
    for k, v in thr.items():
        print(f"  {k:18s} 城市获益需 {v['dP_star_city_benefit_ml']} ML  |  AI 拿到水需 {v['dP_star_AI_gets_water_ml']} ML")
    (HERE / "T1b_summary.json").write_text(
        json.dumps({"thresholds": thr,
                    "pool_and_demand": {d: incumbent_demand(d) for d in ("ha", "co")}},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[write] {HERE/'T1b_claim_convention.csv'}  {HERE/'T1b_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
