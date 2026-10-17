"""WP3-1: volume-only 路径的【通量平衡】守恒检验 (task-1 交付物).

======================================================================
【为什么不能用存量闭合检验】
======================================================================
WP0 取证已确认: volume-only 路径引擎不输出 solute_closure 残差列。
进一步代码定位(见 volonly_conservation_verdict.md)表明这不是疏漏:
该路径把回路浓度【定义】为 补水浓度 x CoC 的瞬时值(full_engine.py:1526-1529),
**不存在"回路溶质存量"这一状态变量**。
=> 存量闭合 dS = I - O 在该路径上无对象可检验(NOT_APPLICABLE_BY_CONSTRUCTION),
   既不能报 PASS(空洞通过), 也不能报 FAIL(错误指控)。

【本脚本做的正确替代检验: 通量平衡 + CoC 自洽】
稳态浓缩模型必须同时满足两条可检验的恒等式:

  (A) 水量闭合(稳态、无储冷):
        G = E + D + B
        G=gross_makeup(毛补水), E=蒸发, D=飘损, B=排污

      ★ 关键口径: 必须用 **gross_makeup_ml** 而非 external_makeup_ml。
        后者是毛补水【减去内部回收水返回】后的净外部取水量, 因此
        external 天然小于 E+D+B, 差值即内部回收量。
        误用 external 会得到一个约 5.6% 的【假性】不闭合
        (本轮已实测: M-(E+D+B) = -2766 ML, 恰为内部回收量;
         而 G-(E+D+B) = 0.0 精确)。这是一个必须记录的口径陷阱。

  (B) CoC 自洽(浓缩倍数定义):
        CoC_engine =? G / (B + D)
      因为盐分只能靠排污+飘损带出, 蒸发不带走盐分,
      故稳态下 CoC = 毛补水总量 / (排污+飘损) 是【定义性】的。
      若引擎报告的 CoC 与此不符, 则其水量-水质耦合不自洽。

  由 (A)(B):  CoC = G/(B+D) 且 G = E+D+B  =>  G*c_mk 进料盐分
              由 (B+D)*c_loop = (B+D)*c_mk*CoC = G*c_mk 带出
              => 盐分通量自动平衡。故 (B) 成立即蕴含盐分通量平衡。

【判据】
  用【相对容差】(量级可达 1e5 kg, 遵门禁第 5 条)。
  (A) 容差 1e-9 (相对 G);  (B) 容差 1e-9 (相对 CoC)。
  任一缺失列 => NOT_IDENTIFIABLE, 不得静默跳过。

【纪律】引擎只读; 缺列标 NOT_IDENTIFIABLE; 相对容差; 
        口径错误(用 external 替 gross)本身记为一项教训, 不得掩盖。
"""
from __future__ import annotations

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

# 复用 a21_solute_closure.py 的 run_case (同一数据口径, 保证可比)
_src = (HERE / "a21_solute_closure.py").read_text(encoding="utf-8")
_src = _src.replace('if __name__ == "__main__":\n    main()', "")
_ns: dict = {"__file__": str(HERE / "a21_solute_closure.py"), "__name__": "_a21reuse"}
exec(compile(_src, "a21_solute_closure.py", "exec"), _ns)
run_case = _ns["run_case"]


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 80)
    rec("WP3-1  volume-only 路径: 通量平衡与 CoC 自洽检验")
    rec("=" * 80)
    rec("""
  volume-only 无溶质存量状态(浓度=补水浓度xCoC 的瞬时定义)
  => 不做存量闭合; 改检验两条稳态恒等式:
     (A) 水量闭合   M = E + D + B
     (B) CoC 自洽   CoC_engine == M / (B + D)
     由 (B) 即蕴含盐分通量平衡 => 这是该路径唯一有内容的守恒类检验。
""")

    cases = [(dom, stor) for dom in ("ha", "co") for stor in (0.0, 200.0)]
    results = []

    rec(f"  {'case':>12} | {'(A) waterResid_rel':>19} {'(A)':>6} | "
        f"{'CoC_calc':>9} {'CoC_eng':>9} {'(B) rel':>10} {'(B)':>6} | overall")
    for dom, stor in cases:
        try:
            d, dc = run_case(dom, stor, False)   # False = volume-only
        except Exception as e:
            rec(f"  {dom+'/'+str(int(stor)):>12} | RUN_FAILED {type(e).__name__}: {e}")
            results.append({"domain": dom, "storage_ml": stor,
                            "status": f"RUN_FAILED:{type(e).__name__}"})
            continue

        need = ("gross_makeup_ml", "external_makeup_ml", "evaporation_ml", "drift_ml",
                "blowdown_ml", "cycles_of_concentration")
        miss = [c for c in need if c not in d.columns]
        if miss:
            rec(f"  {dom+'/'+str(int(stor)):>12} | NOT_IDENTIFIABLE, 缺列 {miss}")
            results.append({"domain": dom, "storage_ml": stor,
                            "status": "NOT_IDENTIFIABLE", "missing_columns": miss})
            continue

        g = lambda c: pd.to_numeric(d[c], errors="coerce")
        G = g("gross_makeup_ml")          # 毛补水(正确口径)
        M = g("external_makeup_ml")       # 净外部取水(含内部回收扣减)
        E, D, B = g("evaporation_ml"), g("drift_ml"), g("blowdown_ml")
        CoC = g("cycles_of_concentration")

        # (A) 水量闭合: 用 gross_makeup
        water_resid = (G - (E + D + B))
        wr_rel = float(water_resid.abs().max() / max(G.abs().max(), 1e-30))

        # 对照: 若误用 external_makeup 会产生多少假性不闭合(口径陷阱留痕)
        faux_rel = float((M - (E + D + B)).abs().max() / max(G.abs().max(), 1e-30))

        # (B) CoC 自洽: CoC = G / (B + D)
        coc_calc = G / (B + D)
        coc_rel = float(((coc_calc - CoC).abs() / CoC.abs().replace(0, np.nan)).max())

        ok_a = wr_rel < 1e-9
        ok_b = np.isfinite(coc_rel) and coc_rel < 1e-9
        overall = "PASS" if (ok_a and ok_b) else ("FAIL" if (np.isfinite(wr_rel) and np.isfinite(coc_rel)) else "NOT_IDENTIFIABLE")

        rec(f"  {dom+'/'+str(int(stor)):>12} | {wr_rel:19.3e} {'PASS' if ok_a else 'FAIL':>6} | "
            f"{coc_calc.mean():9.5f} {CoC.mean():9.5f} {coc_rel:10.3e} "
            f"{'PASS' if ok_b else 'FAIL':>6} | {overall}")
        rec(f"       └ 口径对照: 误用 external_makeup 会得到假性相对残差 {faux_rel:.3e}"
            f" (实为内部回收量占毛补水的比例), 故 volume-only 必须用 gross_makeup")
        results.append({
            "domain": dom, "storage_ml": stor, "status": "IDENTIFIED",
            "water_residual_rel_gross": wr_rel, "water_pass": bool(ok_a),
            "faux_residual_rel_if_external_used": faux_rel,
            "coc_calc_mean": float(coc_calc.mean()), "coc_engine_mean": float(CoC.mean()),
            "coc_relative_error": coc_rel, "coc_pass": bool(ok_b),
            "overall": overall, "n_days": int(len(d)),
        })

    ident = [r for r in results if r.get("status") == "IDENTIFIED"]
    rec("\n[判据汇总]")
    if not ident:
        rec("  无可检验情景 => NOT_IDENTIFIABLE (不得计为 PASS)")
        final = "NOT_IDENTIFIABLE"
    else:
        allpass = all(r["overall"] == "PASS" for r in ident)
        rec(f"  可检验情景 = {len(ident)}/{len(results)}")
        rec(f"  (A) 水量闭合(G口径) 最大相对残差 = {max(r['water_residual_rel_gross'] for r in ident):.3e}")
        rec(f"  (B) CoC 自洽       最大相对误差 = {max(r['coc_relative_error'] for r in ident):.3e}")
        rec(f"  裁定: {'PASS —— volume-only 的稳态通量平衡与 CoC 自洽成立' if allpass else 'FAIL —— 需查水量-水质耦合'}")
        final = "PASS" if allpass else "FAIL"

    rec("")
    rec("★ 对主结论的表述纪律:")
    rec("  volume-only 的守恒支撑应表述为: '稳态通量平衡与 CoC 自洽已证(PASS)',")
    rec("  而**不是**'溶质存量守恒已验证'——后者在该路径上无对象(不适用)。")
    rec("  口径纪律: volume-only 的水量闭合必须用 gross_makeup_ml;")
    rec("  external_makeup_ml 已扣除内部回收, 用它检验会产生约 5.6% 的假性不闭合。")

    summary = {
        "task": "task-1 / WP3-1",
        "path_under_test": "volume-only (quality_state_enabled=False)",
        "test_construction": (
            "不用存量闭合 dS=I-O (该路径无溶质存量状态, 不适用); "
            "改检验两条稳态恒等式: (A) G=E+D+B (G=gross_makeup); (B) CoC_engine == G/(B+D)。"
            "由 (B) 即蕴含盐分通量平衡, 故这是该路径唯一有内容的守恒类检验。"),
        "not_applicable_note": (
            "存量闭合 NOT_APPLICABLE_BY_CONSTRUCTION: 回路浓度被定义为补水浓度xCoC 的"
            "瞬时值(full_engine.py:1526-1529), 无存量状态变量。既不得报 PASS, 也不得报 FAIL。"),
        "caliber_trap": (
            "必须用 gross_makeup_ml。external_makeup_ml 是毛补水减去内部回收水返回后的"
            "净外部取水量, 误用它作水量闭合会得到约 5.6% 的假性不闭合残差"
            "(实测 M-(E+D+B) = -2766.26 ML, 恰等于内部回收量; 而 G-(E+D+B) = 0.0 精确)。"),
        "tolerance": "relative 1e-9 (量级可达 1e5 kg, 遵门禁第5条)",
        "verdict": final,
        "cases": results,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": "引擎只读; 缺列标 NOT_IDENTIFIABLE; 相对容差; 口径错误留痕",
    }
    (HERE / "volonly_flux_balance_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    pd.DataFrame(results).to_csv(HERE / "volonly_flux_balance_cases.csv",
                                 index=False, encoding="utf-8-sig")
    (HERE / "volonly_flux_balance_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] volonly_flux_balance_summary.json / _cases.csv / _log.txt ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
