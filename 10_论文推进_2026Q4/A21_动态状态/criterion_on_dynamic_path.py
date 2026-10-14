"""A21d: 三量判据在动态路径（R10a）下是否仍成立？

【为什么做】
A21 发现两条水质路径给出 4.5× 不同的 CoC。既有中心结论（A17 三量判据）
建立在 volume-only 路径上。**必须检验**：换成带循环滞留的 R10a 路径后，
判据是否仍成立、符号是否改变。

【设计】
配对设计：同域、同掺混比、同限值，只切换
  (a) 水质路径 volume-only / R10a
  (b) 掺混比 φ ∈ {0.2, 0.4, 0.6, 0.8}
逐情景输出三量判据所需的量：
  x_AI (再生水取用) / M0 (φ=0 基准补水) / M1 (φ 情景补水) / 挤占位移
用完整日尺度引擎（FullAIUWMModel）在 volume-only 与 R10a 下各跑一遍。

【口径】
dS_pot = C - F，F = M0 - (1-φ_eff)*M1，C = 挤占位移
三量判据：dS<0 <=> x_AI + (M0-M1) > 位移
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ENGINE = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
if str(ENGINE / "src") not in sys.path:
    sys.path.insert(0, str(ENGINE / "src"))

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ENGINE / "examples" / "cawcc_r2"
TDS_LIMIT = 1100.0
C_REC, C_POT = 900.0, 200.0
PHIS = (0.0, 0.2, 0.4, 0.6, 0.8)


def run(dom: str, phi: float, *, quality_state: bool) -> dict:
    proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / dom / "timeseries.csv")
    proj = copy.deepcopy(proj)
    dc = proj["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["cooling_storage_capacity_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["initial_cooling_storage_ml"] = 0.0
    dc["quality_state_enabled"] = bool(quality_state)
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = 8.0
    dc["cooling"]["water_quality_limits"] = {"TDS": TDS_LIMIT}
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(phi)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(phi)
    dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": C_REC}
    dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": C_POT}
    ru = proj["components"].get("CENTRAL_REUSE")
    if ru is not None:
        ru["treatment_capacity_ml_day"] = 400.0
        ru["initial_ml"] = 100.0
        ru["quality_mg_l"] = {"TDS": C_REC}
        ru["quality_provenance"] = "treated_output"
    sim = proj.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(ts["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(ts["date"].iloc[-1]).date())

    res = FullAIUWMModel(proj, ts).run()
    d = res.data_center_daily

    def col_sum(name):
        if name not in d.columns:
            return float("nan")
        return float(pd.to_numeric(d[name], errors="coerce").sum())

    M = col_sum("external_makeup_ml")
    rec_used = col_sum("reclaimed_used_ml")
    pot_used = col_sum("potable_used_ml")
    # 若引擎未给分项，用 target_fraction × M 估 (仅作诊断)
    if not np.isfinite(rec_used) or rec_used == 0.0:
        rec_used = float(phi) * M
    if not np.isfinite(pot_used) or pot_used == 0.0:
        pot_used = (1.0 - float(phi)) * M
    return {
        "domain": dom, "phi": float(phi), "quality_state": bool(quality_state),
        "M_ml": M, "reclaimed_used_ml": rec_used, "potable_used_ml": pot_used,
        "coc_mean": float(pd.to_numeric(d["cycles_of_concentration"], errors="coerce").mean()),
        "coc_min": float(pd.to_numeric(d["cycles_of_concentration"], errors="coerce").min()),
        "blowdown_ml": col_sum("blowdown_ml"),
        "evaporation_ml": col_sum("evaporation_ml"),
        "water_closure_max_abs": float(pd.to_numeric(
            d["water_balance_residual_ml"], errors="coerce").abs().max())
        if "water_balance_residual_ml" in d.columns else float("nan"),
        "n_days": int(len(d)),
    }


def main() -> None:
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 80)
    rec("A21d  三量判据在动态路径 (R10a) 下是否仍成立")
    rec("=" * 80)

    rows = []
    for dom in ("ha", "co"):
        for qs in (False, True):
            for phi in PHIS:
                try:
                    r = run(dom, phi, quality_state=qs)
                    rows.append(r)
                    rec(f"  {dom} qs={str(qs):5} phi={phi:.1f} | M={r['M_ml']:11.0f} "
                        f"pot={r['potable_used_ml']:10.0f} rec={r['reclaimed_used_ml']:10.0f} "
                        f"coc={r['coc_mean']:6.3f}")
                except Exception as e:  # noqa: BLE001
                    rec(f"  ERROR {dom} qs={qs} phi={phi}: {type(e).__name__}: {e}")
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "dynamic_criterion_grid.csv", index=False, encoding="utf-8-sig")
    rec(f"\n完成 {len(d)} 情景")

    if len(d) == 0:
        raise SystemExit("全部失败")

    rec("\n[闭合]")
    rec(f"  水量闭合 max|残差| = {d['water_closure_max_abs'].max():.3e} ML")

    # ---------- 三量判据 ----------
    rec("\n[判据] 对每个 (域, 路径), 用 phi=0 作 B2 基准计算三量")
    results = []
    for (dom, qs), g in d.groupby(["domain", "quality_state"]):
        g = g.sort_values("phi")
        b2 = g[g.phi == 0.0]
        if not len(b2):
            continue
        M0 = float(b2["M_ml"].iloc[0])
        for _, r in g.iterrows():
            if r.phi == 0.0:
                continue
            M1 = float(r["M_ml"])
            x_ai = float(r["reclaimed_used_ml"])
            phi_eff = x_ai / M1 if M1 > 0 else 0.0
            F = M0 - (1.0 - phi_eff) * M1
            # 挤占位移: 无既有用户分项时的诊断估计 -> 用 (x_ai - 该情景与B2的差额)
            # 引擎未直接给 r_inc, 故此处只检验 F 与 M0/M1 的关系
            results.append({
                "domain": dom, "quality_state": qs, "phi": float(r.phi),
                "M0_ml": M0, "M1_ml": M1, "x_ai_ml": x_ai, "phi_eff": phi_eff,
                "F_ml": F, "potable_used_ml": float(r["potable_used_ml"]),
                "coc_mean": float(r["coc_mean"]),
            })
    res = pd.DataFrame(results)
    res.to_csv(HERE / "dynamic_criterion_derived.csv", index=False, encoding="utf-8-sig")

    rec("\n  路径对比（同域同 φ 的补水）:")
    piv = d.pivot_table(index=["domain", "phi"], columns="quality_state",
                        values="M_ml")
    rec(piv.round(0).to_string())

    rec("\n  路径对比（同域同 φ 的 CoC 均值）:")
    piv2 = d.pivot_table(index=["domain", "phi"], columns="quality_state",
                         values="coc_mean")
    rec(piv2.round(3).to_string())

    summary = {
        "n_scenarios": int(len(d)),
        "water_closure_max_abs_ml": float(d["water_closure_max_abs"].max()),
        "makeup_by_path": {
            f"{dom}|qs={qs}": {str(float(r.phi)): float(r.M_ml)
                               for _, r in g.sort_values("phi").iterrows()}
            for (dom, qs), g in d.groupby(["domain", "quality_state"])},
        "coc_by_path": {
            f"{dom}|qs={qs}": {str(float(r.phi)): float(r.coc_mean)
                               for _, r in g.sort_values("phi").iterrows()}
            for (dom, qs), g in d.groupby(["domain", "quality_state"])},
        "reading": (
            "比较 volume-only 与 R10a 两条路径在相同 φ 下的补水与 CoC。"
            "若 R10a 的补水显著更低且两路径的趋势方向一致，"
            "则既有结论的**方向**稳健，但**量级**依赖路径选择。"),
        "discipline_note": (
            "完整日尺度引擎配对运行; 只切换 quality_state_enabled 与掺混比。"
            "引擎未直接输出 r_inc 分项, 故本脚本只对比 F / M / CoC, "
            "不强行套用需要 r_inc 的三量判据。"),
    }
    (HERE / "dynamic_criterion_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rec(f"\n[write] dynamic_criterion_grid.csv / _derived.csv / _summary.json")
    (HERE / "a21d_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
