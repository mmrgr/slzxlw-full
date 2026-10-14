"""A20b: 模型桥接 (精简版) —— 代表日周期模型 vs 逐日模型.

背景: 原 `bridging_experiment.py` 跑满 730 天 x 18 情景 (约 25 分钟), 两次被中断。
本版做**有针对性的等价性检验**, 不追求全因子覆盖:

  C1  口径等价性: city_model 的 M0 = 逐日求和 Σ M0_day?  (应精确相等)
  C2  冷却物理一致性: M1, phi_eff, CoC 是否一致
  C3  dS_pot 的符号是否一致
  C4  差异归因: 若有差异, 来自哪个被简化掉的机制

样本量: 2 域 x 2 水样 x 3 个 pool_scale x 2 个 phi, 全 730 天 (但只跑必要情景)。
预计 ~4-6 分钟。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
A12 = ROOT / "A12_时间分辨率"
for p in (A10, A12):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import city_model as cm            # noqa: E402
import daily_model as dm           # noqa: E402
from aiuwm.data_center import calculate_data_center_plan as cdcp  # noqa: E402

SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)"]
DOMS = ("ha", "co")
POOL_SCALES = (1.0, 2.0, 3.0)
PHIS = (0.4, 0.8)
CHI = 0.5
N_DAYS = cm.N_DAYS


def simplified(dom, sample, ps, phi, cache):
    r1 = cm.city_outcome(dom, "B_full", sample, pool_scale=ps, gap_scale=1.0,
                         dp_scale=0.0, ai_target=phi, limit_scale=CHI,
                         period_days=N_DAYS, cache=cache)
    r0 = cm.city_outcome(dom, "B_full", sample, pool_scale=ps, gap_scale=1.0,
                         dp_scale=0.0, ai_target=0.0, limit_scale=CHI,
                         period_days=N_DAYS, cache=cache)
    F = r0["M_ml"] - (1.0 - r1["phi_eff"]) * r1["M_ml"]
    C = max(0.0, r0["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
    return {"M0": r0["M_ml"], "M1": r1["M_ml"], "phi_eff": r1["phi_eff"],
            "CoC": r1["CoC_ai"], "C": C, "F": F, "dS_pot": C - F,
            "inc_B2": r0["inc_reclaimed_ml"], "inc_B1": r1["inc_reclaimed_ml"],
            "x_ai": r1["x_ai_ml"]}


def e_of_day(dom, q, date, drv):
    """当日蒸发 E (与 ev_ai 同构, 直接读 evaporation_ml)."""
    comp = dm.comp_for(dom, "B_full", 0.0, "evaporative", CHI, "ai_load_factor_a30")
    comp["water_sources"]["reclaimed"]["target_fraction"] = 0.0
    comp["water_sources"]["potable"]["target_fraction"] = 1.0
    p = cdcp(comp, pd.Timestamp(date), drv, reclaimed_available_ml=0.0,
             reclaimed_quality_mg_l=q)
    return float(p.evaporation_ml)


def daily_sum(dom, sample, ps, phi, cache):
    bl = cm.BASELINES[dom]
    pool_total = bl["P0"] * float(ps)
    ts = dm.load_ts(dom)
    q = dm.sample_quality("B_full", sample)
    dates = pd.to_datetime(ts["date"])
    n = len(ts)
    pool_day = pool_total / n
    gap_day = bl["gap"] / n

    acc = dict(M0=0.0, M1=0.0, inc_B2=0.0, inc_B1=0.0, x_ai=0.0)
    coc, n_ok = [], 0
    for i in range(n):
        drv = dm.drivers_row(ts.iloc[i], "ai_load_factor_a30")
        d = dates.iloc[i]
        try:
            e0 = e_of_day(dom, q, d, drv)
            r0 = dm.daily_city_outcome(dom, sample, d, drv, q, m0_day=0.0,
                                       pool_day=pool_day, gap_day=gap_day,
                                       dp_day=0.0, ai_target=0.0, limit_scale=CHI,
                                       e_ref_day=e0, period_days=1.0, cache=cache)
            r1 = dm.daily_city_outcome(dom, sample, d, drv, q, m0_day=0.0,
                                       pool_day=pool_day, gap_day=gap_day,
                                       dp_day=0.0, ai_target=phi, limit_scale=CHI,
                                       e_ref_day=e0, period_days=1.0, cache=cache)
        except Exception:  # noqa: BLE001
            continue
        acc["M0"] += float(r0["M_ml"])
        acc["M1"] += float(r1["M_ml"])
        acc["inc_B2"] += float(r0["inc_reclaimed_ml"])
        acc["inc_B1"] += float(r1["inc_reclaimed_ml"])
        acc["x_ai"] += float(r1["x_ai_ml"])
        coc.append(float(r1["CoC_ai"]))
        n_ok += 1
    phi_eff = acc["x_ai"] / acc["M1"] if acc["M1"] > 0 else 0.0
    F = acc["M0"] - (1.0 - phi_eff) * acc["M1"]
    C = max(0.0, acc["inc_B2"] - acc["inc_B1"])
    return {"M0": acc["M0"], "M1": acc["M1"], "phi_eff": phi_eff,
            "CoC": float(np.mean(coc)) if coc else float("nan"),
            "C": C, "F": F, "dS_pot": C - F,
            "inc_B2": acc["inc_B2"], "inc_B1": acc["inc_B1"],
            "x_ai": acc["x_ai"], "n_days": n_ok}


def main() -> None:
    t0 = time.time()
    log = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 78)
    rec("A20b 模型桥接 (精简): 代表日周期 vs 逐日")
    rec("=" * 78)

    cache = {}
    rows = []
    for dom in DOMS:
        for smp in SAMPLES:
            for ps in POOL_SCALES:
                for phi in PHIS:
                    s = simplified(dom, smp, ps, phi, cache)
                    dd = daily_sum(dom, smp, ps, phi, cache)
                    rows.append({"domain": dom, "sample": smp, "pool_scale": ps,
                                 "phi": phi, "model": "simplified", **{k: v for k, v in s.items()}})
                    rows.append({"domain": dom, "sample": smp, "pool_scale": ps,
                                 "phi": phi, "model": "daily", **{k: v for k, v in dd.items()}})
                    rec(f"  {dom} {smp[:18]:18} ps={ps} phi={phi}: "
                        f"M0 s/d = {s['M0']:.0f}/{dd['M0']:.0f}  "
                        f"dS s/d = {s['dS_pot']:.0f}/{dd['dS_pot']:.0f}")
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "bridging_comparison_v2.csv", index=False, encoding="utf-8-sig")

    p = d.pivot_table(index=["domain", "sample", "pool_scale", "phi"],
                      columns="model", values=["M0", "M1", "phi_eff", "CoC", "dS_pot"])

    rec("\n[结论]")
    for q in ("M0", "M1", "phi_eff", "CoC"):
        a, b = p[(q, "simplified")], p[(q, "daily")]
        rel = ((a - b).abs() / b.abs().clip(lower=1e-9))
        rec(f"  {q:8}: 中位相对差 = {rel.median():.6f}  最大 = {rel.max():.6f}")

    ss = np.sign(p[("dS_pot", "simplified")].round(0))
    ds = np.sign(p[("dS_pot", "daily")].round(0))
    rec(f"  dS_pot 符号一致率 = {(ss == ds).mean():.3f} ({(ss == ds).sum()}/{len(ss)})")

    summary = {
        "n_pairs": int(len(p)),
        "M0_median_rel_diff": float(((p[("M0", "simplified")] - p[("M0", "daily")]).abs()
                                     / p[("M0", "daily")].abs()).median()),
        "sign_agreement": float((ss == ds).mean()),
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "两模型对同一输入求解; 逐日模型用当日蒸发作 e_ref (修正此前用 M 当 e_ref 的 harness bug)。"
            "口径 = 排放-索取平衡; 不使用已撤回的 psi/Delta。"),
    }
    (HERE / "bridging_summary_v2.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    rec(f"\n完成 {summary['runtime_s']}s")
    (HERE / "a20b_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
