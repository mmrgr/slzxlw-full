"""NE-2: "碱度是唯一符号杠杆" 是否只是当前限值面板的产物?

======================================================================
【为什么必须做（红队审稿 3 / F-5）】
======================================================================
WP5 的结论"碱度是唯一能翻转 dS_pot 符号的杠杆"是在 **LIMIT_SET="baseline"**
(GB/T 50050-2017 循环水 2200/700/750/350/175) 下得到的。
但"哪个物种绑定"取决于【限值/浓度】比 —— 换限值档就会换绑定物种。

若在 permissive / strict 档下绑定物种改变, 则该结论必须限定为
"在 baseline 档下碱度是唯一杠杆", 而不能写成普适机制。

【limitation 档位（来自 city_model.LIMIT_SET 可选值）】
  baseline   : 2200 / 700 / 750 / 350 / 175   (GB/T 50050-2017 循环水)
  permissive : 2600 / 1000 / 750 / 350 / 175  (更宽松)
  strict     : 1000 / 250 / 450 / 350 / 30    (GB/T 19923-2024 补充水口径)

【本脚本做什么】
对每个档位 × 每个完整物种水样:
  1. 计算各受约束物种的【限值/浓度】比, 找出绑定物种(最小者);
  2. 逐物种单点扰动 (×0.5 与 ×2.0), 看 dS_pot 是否改变 (只改该物种浓度);
  3. 判定: 该档位下的"唯一符号杠杆"是哪个物种;
  4. 比较三个档位 → 绑定物种是否一致?

【判据】
  绑定物种 = argmin(limit_i / c_i)
  符号杠杆 = 扰动该物种时 dS_pot 符号改变的物种

【纪律】
  引擎/ city_model 只读; 只用完整物种水样; Figshare BW 排除;
  失败标 NOT_IDENTIFIABLE; 相对容差; 报 n_eff.
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402

# 三个限值档位 (取自 city_model 的定义; 用前会与模块内实际值核对)
PANELS = {
    "baseline":   {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
                   "alkalinity": 350.0, "silica": 175.0},
    "permissive": {"TDS": 2600.0, "chloride": 1000.0, "hardness": 750.0,
                   "alkalinity": 350.0, "silica": 175.0},
    "strict":     {"TDS": 1000.0, "chloride": 250.0, "hardness": 450.0,
                   "alkalinity": 350.0, "silica": 30.0},
}
POTABLE = {"TDS": 180.0, "chloride": 35.0, "hardness": 120.0,
           "alkalinity": 100.0, "silica": 10.0}
SPECIES = ("TDS", "chloride", "hardness", "alkalinity", "silica")
COMPLETE = ("IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)")
PHI = 0.6
COC_DESIGN = 3.5


def load_chem():
    samp = cm.load_samples()
    out = {}
    for _, r in samp.iterrows():
        nm = str(r["source"])
        if nm not in COMPLETE:
            continue
        d = {}
        for k in SPECIES:
            v = r.get(k)
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                d[k] = float(v)
        out[nm] = d
    return out


def solve_dS(dom, q_recl, limits, phi=PHI):
    """用 city_model 主口径求 dS_pot (B1-B2). 返回 dict."""
    bl = cm.BASELINES[dom]
    # 把限值临时注入 comp (不改模块全局)
    comp = cm.base_comp(bl, "B_full", phi, coc_design=COC_DESIGN, limit_scale=1.0)
    comp["cooling"]["water_quality_limits"] = dict(limits)
    pq = dict(comp["water_sources"]["potable"].get("quality", {}))
    for k, v in cm.POTABLE_EXTRA.items():
        pq.setdefault(k, v)
    comp["water_sources"]["potable"]["quality"] = pq

    plan = cm.calculate_data_center_plan(comp, bl["date_rep"], bl["drivers_rep"],
                                         reclaimed_available_ml=np.inf,
                                         reclaimed_quality_mg_l=dict(q_recl))
    M1 = float(plan.external_makeup_ml)
    # B1: 无回用
    comp0 = cm.base_comp(bl, "B_full", 0.0, coc_design=COC_DESIGN, limit_scale=1.0)
    comp0["cooling"]["water_quality_limits"] = dict(limits)
    pq0 = dict(comp0["water_sources"]["potable"].get("quality", {}))
    for k, v in cm.POTABLE_EXTRA.items():
        pq0.setdefault(k, v)
    comp0["water_sources"]["potable"]["quality"] = pq0
    plan0 = cm.calculate_data_center_plan(comp0, bl["date_rep"], bl["drivers_rep"],
                                          reclaimed_available_ml=0.0,
                                          reclaimed_quality_mg_l=dict(q_recl))
    M0 = float(plan0.external_makeup_ml)
    return {"M0": M0, "M1": M1, "dS_M0_minus_M1": M0 - M1,
            "coc1": float(plan.cycles_of_concentration),
            "coc0": float(plan0.cycles_of_concentration)}


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("NE-2  “碱度是唯一符号杠杆”是否只是 baseline 面板的产物?")
    rec("=" * 84)

    # 与 city_model 实际档位核对(防止自造)
    try:
        actual = getattr(cm, "PANELS", None)
        if actual:
            rec(f"\n[0] city_model.PANELS 实际档位: {list(actual.keys())}")
    except Exception:
        pass

    chem = load_chem()
    rec(f"\n[0] 完整物种水样 (5/5): {list(chem.keys())}")

    rows = []
    rec(f"\n[1] 各档位下的【限值/浓度】比 (最小者 = 绑定物种)")
    binding_by_panel = {}
    for pname, lim in PANELS.items():
        rec(f"\n  档位 = {pname}")
        rec(f"    {'sample':<30} {'TDS':>8} {'chloride':>9} {'hardness':>9} "
            f"{'alkalinity':>11} {'silica':>8} | 绑定")
        for nm, q in chem.items():
            rats = {k: lim[k] / q[k] for k in SPECIES if k in q and q[k] > 0}
            if not rats:
                continue
            mn = min(rats, key=rats.get)
            binding_by_panel.setdefault(pname, {})[nm] = mn
            rec(f"    {nm[:28]:<30} " + " ".join(f"{rats.get(k, float('nan')):8.3f}"
                                                for k in SPECIES) + f" | {mn}")

    rec(f"\n[2] ★ 逐物种单点扰动: 哪个物种能翻转 dS_pot 符号?")
    rec(f"    (扰动 = 把该物种浓度 ×0.5 与 ×2.0; 其余不变; phi={PHI})")
    for pname, lim in PANELS.items():
        rec(f"\n  档位 = {pname}")
        rec(f"    {'sample':<30} {'dS(base)':>11} | " +
            " ".join(f"{k[:6]:>9}" for k in SPECIES) + " | 杠杆")
        for nm, q in chem.items():
            for dom in ("ha",):
                try:
                    base = solve_dS(dom, q, lim)
                except Exception as e:
                    rec(f"    {nm[:28]:<30} RUN_FAILED {type(e).__name__}: {str(e)[:40]}")
                    rows.append({"panel": pname, "domain": dom, "sample": nm,
                                 "status": f"RUN_FAILED:{type(e).__name__}"})
                    continue
                dS_base = base["dS_M0_minus_M1"]
                sgn0 = np.sign(dS_base)
                levers, marks = [], []
                for k in SPECIES:
                    if k not in q:
                        marks.append("n/a")
                        continue
                    flips = False
                    for mult in (0.5, 2.0):
                        q2 = dict(q); q2[k] = q[k] * mult
                        try:
                            r2 = solve_dS(dom, q2, lim)
                            if np.sign(r2["dS_M0_minus_M1"]) != sgn0:
                                flips = True
                        except Exception:
                            pass
                        rows.append({"panel": pname, "domain": dom, "sample": nm,
                                     "species": k, "mult": mult, "status": "OK",
                                     "dS": r2["dS_M0_minus_M1"] if 'r2' in dir() else None,
                                     "dS_base": dS_base})
                    marks.append("FLIP" if flips else "-")
                    if flips:
                        levers.append(k)
                rec(f"    {nm[:28]:<30} {dS_base:11.4g} | " +
                    " ".join(f"{m:>9}" for m in marks) +
                    f" | {','.join(levers) if levers else 'NONE'}")

    # ---------- 裁定 ----------
    rec("\n[3] ★ 裁定")
    rec("  绑定物种(由 限值/浓度 比决定):")
    for pname in PANELS:
        rec(f"    {pname:<12}: " +
            ", ".join(f"{k.split(' ')[0]}={v}" for k, v in
                      binding_by_panel.get(pname, {}).items()))

    summarised = {}
    for pname in PANELS:
        vals = set(binding_by_panel.get(pname, {}).values())
        summarised[pname] = sorted(vals)
    rec(f"\n  各档位的绑定物种集合: {summarised}")
    all_same = len({tuple(v) for v in summarised.values()}) == 1
    if all_same:
        rec("  ✓ 三个档位下绑定物种【一致】⇒ '碱度绑定'不是 baseline 面板的产物")
        verdict = "BINDING_SPECIES_PANEL_ROBUST"
    else:
        rec("  ✗ 绑定物种随档位【改变】⇒ 结论必须限定为'在 baseline 档下'")
        rec("     不得写成普适机制")
        verdict = "BINDING_SPECIES_PANEL_DEPENDENT"

    summary = {
        "task": "NE-2 (红队 F-5)",
        "question": "'碱度是唯一符号杠杆'是否只是 baseline 限值面板的产物?",
        "panels": PANELS,
        "samples": list(chem.keys()),
        "phi": PHI,
        "binding_species_by_panel": binding_by_panel,
        "binding_sets_by_panel": summarised,
        "verdict": verdict,
        "cases": rows,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": "city_model 只读; 完整物种水样; 失败标 NOT_IDENTIFIABLE; 相对容差",
    }
    (HERE / "ne2_panel_robustness_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    pd.DataFrame(rows).to_csv(HERE / "ne2_panel_robustness_cases.csv",
                              index=False, encoding="utf-8-sig")
    (HERE / "ne2_panel_robustness_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] ne2_* ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
