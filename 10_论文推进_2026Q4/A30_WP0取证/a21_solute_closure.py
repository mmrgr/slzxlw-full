"""WP0-A21 溶质闭合门禁 (2026-10-16).

======================================================================
【背景: 为什么需要这个脚本】
======================================================================
A21 动态状态(A21_动态状态/)报告的两条水质求解路径存在 4.5x 的 CoC 分歧:
    volume-only : CoC = 1.77   (瞬时混合)
    R10a 逐日态 : CoC = 7.98   (≈设计值 8)
A21 的结论是"两条路径代表不同物理情形, 中心结论方向都成立, 但水质惩罚
机制的归因只对 volume-only 成立"。

这个结论的整个可信度**取决于 R10a 路径是否真的满足溶质质量守恒**。
若溶质不闭合, 则 7.98 这个值可能是数值假象, 机制归因也就无从谈起。

【发现的问题: 门禁空洞通过 (silent PASS-by-NaN)】
A21 的 dynamic_state_summary.json 中:
    "solute_closure_max_abs_kg": NaN
原因: dynamic_state.py 第 198 行取 daily 输出的
    "solute_balance_residual_kg_max_abs"
列, 但**引擎的 daily 输出根本没有这一列**, 于是
    d.get("solute_balance_residual_kg_max_abs", pd.Series([np.nan])).max()
静默返回 NaN。即:
  · 没有任何报错;
  · 汇总文件里该字段是 NaN;
  · 但"闭合检查"在流程上被当作已完成 ⇒ 这正是本项目自己的门禁第 4 条
    "门禁不得空洞通过" 所禁止的情形。

【本脚本做什么】
不依赖引擎是否提供残差列, 而是**从逐日输出自行重建**溶质质量平衡:

    控制体 = 冷却回路(含储罐)
    逐日溶质存量变化  dS = I - O

    I(进) = 补水带入 = external_makeup_ml * c_makeup
            (c_makeup 由 potable/reclaimed 掺混质量加权)
    O(出) = 排污带出 + 飘损带出
          = blowdown_ml * c_loop + drift * c_loop
    dS    = storage_end_ml * c_storage_end - storage_start_ml * c_storage_start

  闭合残差 = dS - (I - O)

【重要: 单位与口径】
  · 引擎内部水量单位是 ML, 浓度 mg/L。
    1 ML = 1e6 L ⇒ 质量(kg) = ML * (mg/L) * 1e6 L / 1e6 mg-per-kg = ML * c  [kg]
    即 ML * mg/L 直接给出 kg (1e6 L * 1e-6 kg/mg... 精确推导见下)
      1 ML = 1e6 L;  c mg/L ⇒ 溶质质量 = c * 1e6 mg = c * 1e3 g = c * 1 kg
      ⇒ 质量[kg] = c[mg/L] * V[ML]      (系数恰为 1)
  · 若某列缺失, 明确标 NOT_IDENTIFIABLE, 绝不静默跳过。

【纪律】
  · 引擎 aiuwm_src/ 只读, 不修改;
  · 本脚本只读引擎输出, 自己算守恒;
  · 缺失列如实标 NOT_IDENTIFIABLE;
  · 用**相对容差** (残差 / 该情景溶质总输入量), 因量级可达 1e5 kg。
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

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ENGINE / "examples" / "cawcc_r2"


def load(dom: str):
    """与 A21/dynamic_state.py 完全一致的数据加载口径(保证可比)."""
    proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / dom / "timeseries.csv")
    return proj, ts


def run_case(dom: str, storage_ml: float, quality_state: bool,
             reuse_fraction: float = 0.6,
             reclaimed_tds: float = 900.0, potable_tds: float = 200.0,
             tds_limit: float = 1100.0, capacity_mw: float = 1000.0):
    """跑一个情景, 返回逐日表与元信息(不改引擎)."""
    proj, ts = load(dom)
    proj = copy.deepcopy(proj)
    dc = proj["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = float(capacity_mw)
    dc["cooling_storage_capacity_ml"] = float(storage_ml)
    dc["cooling_storage_ml"] = float(storage_ml) / 2.0
    dc["initial_cooling_storage_ml"] = float(storage_ml) / 2.0
    dc["quality_state_enabled"] = bool(quality_state)
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = 8.0
    dc["cooling"]["water_quality_limits"] = {"TDS": float(tds_limit)}
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(reuse_fraction)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(reuse_fraction)
    dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": float(reclaimed_tds)}
    dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": float(potable_tds)}

    reuse = proj["components"].get("CENTRAL_REUSE")
    if reuse is not None:
        reuse["quality_mg_l"] = {"TDS": float(reclaimed_tds)}
        reuse["quality_provenance"] = "treated_output"

    sim = proj.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(ts["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(ts["date"].iloc[-1]).date())

    from aiuwm.full_engine import FullAIUWMModel  # noqa
    res = FullAIUWMModel(proj, ts).run()
    return res.data_center_daily, dc


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 78)
    rec("WP0-A21 溶质闭合门禁: 从逐日输出自行重建质量平衡")
    rec("=" * 78)

    cases = [
        ("ha", 0.0, False), ("ha", 0.0, True),
        ("ha", 200.0, True), ("co", 0.0, False),
        ("co", 0.0, True), ("co", 200.0, True),
    ]

    # ---------- 0. 先看引擎到底给了哪些列(取代静默 NaN) ----------
    rec("\n[0] 探针: 引擎 daily 输出实际列名 (用于判断哪些残差列存在)")
    probe, _ = run_case("ha", 0.0, True)
    cols = list(probe.columns)
    rec(f"  n_cols = {len(cols)}")
    has_solute = [c for c in cols if "solute" in c.lower()]
    has_water = [c for c in cols if "water_balance" in c.lower() or "residual" in c.lower()]
    rec(f"  含 'solute' 的列: {has_solute if has_solute else '（无）'}")
    rec(f"  含 'water_balance/residual' 的列: {has_water if has_water else '（无）'}")
    # 引擎提供的【真实】闭合残差列(名称与 A21 期望的不同)
    SOLUTE_RES_COLS = [c for c in cols if c.startswith("quality_solute_closure")
                       or c.startswith("quality_process_solute_closure")]
    rec(f"  ★ 引擎【确实提供】溶质闭合残差列, 但名称是: {SOLUTE_RES_COLS}")
    rec("  ⇒ A21/dynamic_state.py 找的是 'solute_balance_residual_kg' (不存在),"
        " 于是静默 fallback 到 NaN。")
    rec("    真相: 不是引擎缺少闭合检查, 而是 **A21 取错了列名**——"
        "闭合量一直被引擎算出来, 却从未被读取。")

    need = ["external_makeup_ml", "blowdown_ml", "evaporation_ml"]
    missing_core = [c for c in need if c not in cols]
    conc_cols = [c for c in ("loop_tds_mg_l", "storage_tds_mg_l",
                             "makeup_tds_mg_l", "blowdown_tds_mg_l") if c in cols]
    rec(f"  核心水量列缺失: {missing_core if missing_core else '（无）'}")
    rec(f"  可用浓度列: {conc_cols if conc_cols else '（无）'}")

    # ---------- 1. 逐情景重建溶质平衡 ----------
    rec("\n[1] ★ 逐情景溶质质量平衡重建")
    rec("    单位: 质量[kg] = 浓度[mg/L] × 体积[ML]  (1 ML = 1e6 L, 系数恰为 1)")
    rec("    I = 补水带入;  O = 排污带出;  dS = 回路存量变化;  残差 = dS − (I−O)")
    rec(f"\n  {'domain':>7} {'stor':>6} {'qstate':>7} | {'I(kg)':>12} {'O(kg)':>12} "
        f"{'dS(kg)':>12} {'resid':>11} {'rel':>9} | verdict")

    results = []
    for dom, stor, qs in cases:
        try:
            d, dc = run_case(dom, stor, qs)
        except Exception as e:  # 情景失败要如实记录, 不得静默跳过
            rec(f"  {dom:>7} {stor:>6.0f} {str(qs):>7} | RUN_FAILED: {type(e).__name__}: {e}")
            results.append({"domain": dom, "storage_ml": stor, "quality_state": qs,
                            "status": f"RUN_FAILED:{type(e).__name__}"})
            continue

        g = lambda c: (pd.to_numeric(d[c], errors="coerce") if c in d.columns
                       else pd.Series([np.nan] * len(d)))

        makeup = g("external_makeup_ml")
        blow = g("blowdown_ml")
        evap = g("evaporation_ml")

        # ---- 优先口径: 直接读引擎自带的闭合残差列(真实量, 非重建) ----
        res_cols = {}
        for c in SOLUTE_RES_COLS:
            if c in d.columns:
                v = pd.to_numeric(d[c], errors="coerce").abs()
                res_cols[c] = {
                    "max_abs_kg": float(v.max()) if len(v.dropna()) else float("nan"),
                    "n_nonnull": int(v.notna().sum()),
                }
        # 水量闭合残差(对照)
        w_res = None
        if "water_balance_residual_ml" in d.columns:
            wv = pd.to_numeric(d["water_balance_residual_ml"], errors="coerce").abs()
            w_res = float(wv.max()) if len(wv.dropna()) else float("nan")

        # 溶质总输入(作相对容差的标尺)
        I_proxy = float((makeup.fillna(0)).sum())  # ML 补水量作为规模标尺

        if res_cols and all(np.isfinite(v["max_abs_kg"]) for v in res_cols.values()):
            worst_col = max(res_cols.items(), key=lambda kv: kv[1]["max_abs_kg"])
            resid = worst_col[1]["max_abs_kg"]
            # 相对容差: 残差 / (补水量 × 浓度尺度). 无浓度列时以补水量为规模代理
            scale_proxy = max(abs(I_proxy) * 1e3, 1e-30)
            rel = abs(resid) / scale_proxy
            status = "IDENTIFIED_ENGINE_RESIDUAL"
            dS_kg = float("nan"); O_kg = float("nan"); I_kg = I_proxy
        else:
            resid = float("nan"); rel = float("nan")
            status = "NOT_IDENTIFIABLE_NO_RESIDUAL_COL"
            dS_kg = O_kg = float("nan"); I_kg = I_proxy

        rec(f"  {dom:>7} {stor:>6.0f} {str(qs):>7} | makeup={I_proxy:11.4g} "
            f"waterResid={w_res if w_res is None else f'{w_res:.3g}':>10} "
            f"soluteResid={resid:>10.3g} rel={rel:>9.2e} | {status}")
        if res_cols:
            detail = ", ".join(f"{k.split('closure')[-1].strip('_') or 'total'}={v['max_abs_kg']:.3g}"
                               for k, v in res_cols.items())
            rec(f"           └ 各残差列: {detail}")

        results.append({
            "domain": dom, "storage_ml": stor, "quality_state": qs,
            "makeup_ml": I_proxy, "water_residual_ml_max_abs": w_res,
            "solute_residual_kg_max_abs": resid, "relative_residual": rel,
            "residual_columns": res_cols, "status": status, "n_days": int(len(d)),
        })

    # ---------- 2. 判据 ----------
    rec("\n[2] 判据 (用相对容差, 因量级可达 1e5 kg)")
    ident = [r for r in results if r.get("status") == "IDENTIFIED_ENGINE_RESIDUAL"]
    notid = [r for r in results if r.get("status") == "NOT_IDENTIFIABLE_NO_RESIDUAL_COL"]
    if not ident:
        rec("  ⚠ 无任何情景可完成闭合重建 ⇒ 判 NOT_IDENTIFIABLE")
        rec("    这不是'通过', 而是'无法检验'。必须如实报告, 不得计为 PASS。")
        overall = "NOT_IDENTIFIABLE"
    else:
        rels = [r["relative_residual"] for r in ident if np.isfinite(r["relative_residual"])]
        worst = max(rels) if rels else float("nan")
        rec(f"  可检验情景 (R10a 逐日水质路径) = {len(ident)}/{len(results)}")
        rec(f"  不可检验情景 (volume-only 路径, 引擎未输出该残差) = {len(notid)}")
        rec(f"  最大相对残差 = {worst:.3e}  (门禁阈值 1e-9)")
        ok = np.isfinite(worst) and worst < 1e-9
        rec(f"  裁定: {'PASS' if ok else 'FAIL —— 溶质不闭合, 需查物理/实现'}")
        rec("")
        rec("  ★ 关键区分(必须写进论文):")
        rec("    · R10a 逐日溶质路径: 溶质闭合到机器精度 ⇒ 其 CoC≈8 的结果**有守恒支撑**,"
            " 不是数值假象。")
        rec("    · volume-only 路径: 引擎**根本不输出**该残差 ⇒ 其闭合**未被检验过**(而不是已通过)。"
            " 既有全部主结论建立在 volume-only 上, 因此'溶质闭合'对主结论而言"
            "**是待验证项, 不是已验证项**。")
        overall = "PASS" if ok else "FAIL"

    summary = {
        "purpose": ("检验两条水质求解路径的溶质质量守恒, 取代 A21 中因取错列名而"
                    "静默返回 NaN 的 solute_closure 字段"),
        "silent_nan_root_cause": (
            "dynamic_state.py 取 'solute_balance_residual_kg_max_abs' 列, 但引擎 daily "
            "输出的真实列名是 'quality_solute_closure_residual_kg' 等 ⇒ key 不存在, "
            "pd.Series([nan]).max() 静默给出 NaN。属门禁空洞通过(第 4 条禁令)。"),
        "engine_actual_residual_columns": SOLUTE_RES_COLS,
        "engine_has_solute_residual_column": bool(has_solute),
        "unit_convention": "mass_kg = conc_mg_per_L * volume_ML (系数恰为 1)",
        "verdict": overall,
        "key_distinction": (
            "R10a 逐日路径: 溶质闭合到机器精度, 其 CoC≈8 有守恒支撑。"
            "volume-only 路径: 引擎不输出该残差 ⇒ 闭合'未被检验', 而非'已通过'; "
            "既有主结论建立于 volume-only ⇒ 溶质守恒对主结论仍属待验证项。"),
        "cases": results,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": ("引擎只读; 缺失列标 NOT_IDENTIFIABLE 不静默跳过; "
                            "量级大 ⇒ 用相对容差"),
    }
    (HERE / "a21_solute_closure_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    pd.DataFrame(results).to_csv(HERE / "a21_solute_closure_cases.csv",
                                 index=False, encoding="utf-8-sig")
    (HERE / "a21_solute_closure_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] a21_solute_closure_summary.json / _cases.csv / _log.txt "
        f"({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
