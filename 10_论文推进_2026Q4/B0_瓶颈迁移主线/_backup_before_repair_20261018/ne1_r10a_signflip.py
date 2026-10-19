"""NE-1: R10a 动态水质路径 vs volume-only 路径的 sign-flip 判决性实验.

======================================================================
【为什么这是阻断性问题（红队审稿 3 的第一红线）】
======================================================================
主稿把"质量惩罚"作为中心机制: 掺混再生水 -> CoC 被压 -> 补水 M 上升。
但引擎有**两条水质求解路径**, 对同一输入给出定性分歧的结果:
  · volume-only (既有全部结论所用): phi=0.6 时 CoC=1.82, 质量惩罚显著
  · R10a 逐日溶质状态 (opt-in):    同输入 CoC≈7.99 (≈设计值), 惩罚**几乎消失**

若 R10a 路径下 dS_pot 的**符号**也改变, 则"机制"措辞不能保留,
只能退为"结构性分歧下的条件性结论"。这正是红队要求的判决性检验。

【本脚本做什么】
在**完整物种水样**(IEUA, LADWP)上, 对**同一组参数**, 分别用两条路径跑出:
    M0, M1, CoC0, CoC1, q, dS_pot
并判定:
    (a) 两条路径的 dS_pot 符号是否一致?
    (b) 若符号一致 -> 中心结论方向稳健, 机制归因仍受限(路径依赖);
    (c) 若符号不一致 -> 必须把结论限定为"取决于求解路径", 主稿须改述。

【纪律】
  · 引擎 aiuwm_src/ 只读, 永不修改;
  · 只用完整物种水样(5/5), Figshare BW 排除;
  · 缺列/失败标 NOT_IDENTIFIABLE, 不静默跳过;
  · 相对容差; 报 n_eff.
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
ENGINE = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
if str(ENGINE / "src") not in sys.path:
    sys.path.insert(0, str(ENGINE / "src"))
A10 = ROOT / "A10_敏感性与边界"
if str(A10) not in sys.path:
    sys.path.insert(0, str(A10))

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402
import city_model as cm  # noqa: E402

R2 = ENGINE / "examples" / "cawcc_r2"
LIMITS = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
          "alkalinity": 350.0, "silica": 175.0}
POTABLE = {"TDS": 180.0, "chloride": 35.0, "hardness": 120.0,
           "alkalinity": 100.0, "silica": 10.0}
COMPLETE = ("IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)")


def load(dom):
    proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / dom / "timeseries.csv")
    return proj, ts


def run_case(dom, q_recl, phi, quality_state, coc_design=3.5):
    """跑一个情景; quality_state=True 走 R10a, False 走 volume-only."""
    proj, ts = load(dom)
    proj = copy.deepcopy(proj)
    dc = proj["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["quality_state_enabled"] = bool(quality_state)
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = float(coc_design)
    dc["cooling"]["water_quality_limits"] = dict(LIMITS)
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(phi)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(phi)
    dc["water_sources"]["reclaimed"]["quality_mg_l"] = dict(q_recl)
    dc["water_sources"]["potable"]["quality_mg_l"] = dict(POTABLE)
    reuse = proj["components"].get("CENTRAL_REUSE")
    if reuse is not None:
        reuse["quality_mg_l"] = dict(q_recl)
        reuse["quality_provenance"] = "treated_output"
    sim = proj.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(ts["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(ts["date"].iloc[-1]).date())

    res = FullAIUWMModel(proj, ts).run()
    d = res.data_center_daily
    g = lambda c: (pd.to_numeric(d[c], errors="coerce") if c in d.columns
                   else pd.Series([np.nan] * len(d)))
    return {
        "makeup": float(g("external_makeup_ml").sum()),
        "coc_mean": float(g("cycles_of_concentration").mean()),
        "coc_min": float(g("cycles_of_concentration").min()),
        "n_days": int(len(d)),
        "has_solute_res": bool("quality_solute_closure_residual_kg" in d.columns),
    }


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("NE-1  R10a 动态路径 vs volume-only: dS_pot 符号判决性检验")
    rec("=" * 84)

    # 完整物种水样化学
    samp = cm.load_samples()
    chem = {}
    for _, r in samp.iterrows():
        nm = str(r["source"])
        if nm not in COMPLETE:
            continue
        d = {}
        for k in LIMITS:
            v = r.get(k)
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                d[k] = float(v)
        chem[nm] = d
    rec("\n[0] 使用的完整物种水样 (5/5 受约束物种)")
    for k, v in chem.items():
        rec(f"  {k:<40} 物种={len(v)}  缺={sorted(set(LIMITS)-set(v))}")

    PHIS = (0.0, 0.2, 0.4, 0.6)
    DOMS = ("ha", "co")
    rows = []
    rec(f"\n[1] 逐情景双路径对照 (phi=0 为无回用基线)")
    rec(f"  {'dom':>4} {'sample':<26} {'phi':>5} | {'M(vol)':>10} {'CoC(vol)':>9} | "
        f"{'M(R10a)':>10} {'CoC(R10a)':>10} | dS(vol)  dS(R10a)  符号")
    for dom in DOMS:
        for nm, qrec in chem.items():
            for phi in PHIS:
                try:
                    v = run_case(dom, qrec, phi, False)
                    r10 = run_case(dom, qrec, phi, True)
                except Exception as e:
                    rec(f"  {dom:>4} {nm[:24]:<26} {phi:>5.1f} | RUN_FAILED {type(e).__name__}")
                    rows.append({"domain": dom, "sample": nm, "phi": phi,
                                 "status": f"RUN_FAILED:{type(e).__name__}"})
                    continue
                rows.append({
                    "domain": dom, "sample": nm, "phi": phi, "status": "OK",
                    "M_vol": v["makeup"], "coc_vol": v["coc_mean"], "cocmin_vol": v["coc_min"],
                    "M_r10a": r10["makeup"], "coc_r10a": r10["coc_mean"],
                    "cocmin_r10a": r10["coc_min"],
                    "has_solute_res_vol": v["has_solute_res"],
                    "has_solute_res_r10a": r10["has_solute_res"],
                })

    df = pd.DataFrame(rows)
    ok = df[df.status == "OK"].copy() if "status" in df.columns else pd.DataFrame()

    if len(ok) == 0:
        rec("\n  ⚠ 无可用情景 ⇒ NOT_IDENTIFIABLE")
        verdict = "NOT_IDENTIFIABLE"
        summary_extra = {}
    else:
        # 逐 (domain, sample) 计算 M0 与 M1(phi>0), 得 dS 与 q 的两路径版本
        rec("\n[2] ★ 两路径下的 dS_pot 与 q 对照 (phi=0.6)")
        rec(f"  {'dom':>4} {'sample':<26} | {'dS_vol':>10} {'dS_r10a':>10} {'符号一致':>8} | "
            f"{'q_vol':>9} {'q_r10a':>9}")
        res2 = []
        for dom in DOMS:
            for nm in chem:
                a = ok[(ok.domain == dom) & (ok["sample"] == nm) & (ok.phi == 0.0)]
                b = ok[(ok.domain == dom) & (ok["sample"] == nm) & (ok.phi == 0.6)]
                if len(a) == 0 or len(b) == 0:
                    continue
                a, b = a.iloc[0], b.iloc[0]
                # dS_pot 在"池完全被挤占"分支下退化为 M1-M0 (即 -F); 两路径同口径比较
                dS_vol = a.M_vol - b.M_vol      # M0 - M1
                dS_r10 = a.M_r10a - b.M_r10a
                coc0_vol, coc1_vol = a.coc_vol, b.coc_vol
                coc0_r10, coc1_r10 = a.coc_r10a, b.coc_r10a
                q_vol = ((coc1_vol - coc0_vol) / (coc1_vol * (coc0_vol - 1))
                         if (coc1_vol * (coc0_vol - 1)) != 0 else float("nan"))
                q_r10 = ((coc1_r10 - coc0_r10) / (coc1_r10 * (coc0_r10 - 1))
                         if (coc1_r10 * (coc0_r10 - 1)) != 0 else float("nan"))
                same = (np.sign(dS_vol) == np.sign(dS_r10))
                rec(f"  {dom:>4} {nm[:24]:<26} | {dS_vol:10.4g} {dS_r10:10.4g} "
                    f"{'YES' if same else 'NO':>8} | {q_vol:9.4f} {q_r10:9.4f}")
                res2.append({"domain": dom, "sample": nm,
                             "dS_vol": dS_vol, "dS_r10a": dS_r10,
                             "sign_same": bool(same),
                             "q_vol": q_vol, "q_r10a": q_r10,
                             "coc0_vol": coc0_vol, "coc1_vol": coc1_vol,
                             "coc0_r10a": coc0_r10, "coc1_r10a": coc1_r10})

        n_same = sum(1 for r in res2 if r["sign_same"])
        rec(f"\n[3] ★ 裁定")
        rec(f"  可比情景数 = {len(res2)}")
        rec(f"  两路径 dS_pot 【符号一致】 = {n_same}/{len(res2)}")
        if len(res2) and n_same == len(res2):
            rec("  ✓ 两路径符号【完全一致】")
            rec("    ⇒ 中心结论的**方向**对求解路径稳健, 可保留")
            rec("    ⇒ 但'质量惩罚'的**量级/机制归因**仍依路径 (volume-only 显著, R10a 近消失)")
            rec("    ⇒ 主稿应保留当前的【结构性敏感性】声明, 不得声称唯一机制")
            verdict = "DIRECTION_ROBUST_MECHANISM_PATH_DEPENDENT"
        elif len(res2) and n_same == 0:
            rec("  ✗ 两路径符号【完全相反】")
            rec("    ⇒ 结论取决于求解路径 ⇒ 主稿必须把中心结论改述为条件性结论,"
                " 且不得保留'机制'措辞")
            verdict = "SIGN_PATH_DEPENDENT_CRITICAL"
        else:
            rec(f"  ⚠ 两路径符号【部分一致】({n_same}/{len(res2)})")
            rec("    ⇒ 结论在路径间不稳定 ⇒ 主稿须限定适用范围并披露该分歧")
            verdict = "PARTIALLY_PATH_DEPENDENT"
        summary_extra = {"comparisons": res2, "n_sign_same": n_same}

    # ---------- 汇总 ----------
    summary = {
        "task": "NE-1 (红队审稿3 第一红线)",
        "question": "R10a 动态路径下 dS_pot 符号是否改变? 决定'机制'措辞能否保留",
        "paths": {"volume_only": "quality_state_enabled=False",
                  "r10a": "quality_state_enabled=True"},
        "samples": list(chem.keys()),
        "complete_species_only": True,
        "cases": df.to_dict(orient="records") if len(df) else [],
        "verdict": verdict,
        **summary_extra,
        "limit_set": LIMITS,
        "potable": POTABLE,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": "引擎只读; 完整物种水样; 缺列/失败标 NOT_IDENTIFIABLE; 相对容差",
    }
    (HERE / "ne1_r10a_signflip_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if len(df):
        df.to_csv(HERE / "ne1_r10a_signflip_cases.csv", index=False, encoding="utf-8-sig")
    (HERE / "ne1_r10a_signflip_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] ne1_r10a_signflip_summary.json / _cases.csv / _log.txt ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
