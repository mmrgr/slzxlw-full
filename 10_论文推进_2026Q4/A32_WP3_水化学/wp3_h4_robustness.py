"""WP3-2: H4(组成反转符号) 在【完整物种】水样上的稳健性检验.

======================================================================
【为什么要做这个检验】
======================================================================
WP2 §6 登记了一个致命风险: 项目最核心的"机制"候选 H4
(水质组成可反转 dS_pot 的符号) 目前的部分支撑可能来自【退化情形】:

  Figshare RW (2025)      : 仅 3 物种 (缺 alkalinity/silica) -> CoC1 = 1.000001 (触下限)
  AI-UWM model assumption : 仅 2 物种 (缺 3 项)             -> CoC1 = 2.161
  IEUA RP-1 / LADWP AWPF  : 5 物种 (完整)

证据来源:
  A22_判据分解/q_theory_summary.json 的 per_sample
  A22_判据分解/missing_quality_summary.json (缺失物种按 0 处理 => 水样显得更"干净")

若"符号反转"主要由 Figshare(缺 2 物种且触 CoC 下限)驱动, 则该发现不可靠,
不能作为论文核心机制。**这是决定论文有无真机制的关键检验。**

【本脚本做什么】
1. 读取四个水样的完整/缺失物种构成;
2. 对每个水样, 在【同一套】参数网格上跑引擎, 取 CoC0/CoC1 与 dS_pot;
3. 判定每个水样属于 正常 / 退化(CoC 触限) / 组成不完整;
4. 分别报告: 仅完整物种水样 vs 含不完整水样 时的"符号反转"结论是否仍然成立;
5. 给出裁定: H4 在完整物种上是否成立。

【纪律】
  · 引擎只读; 不改 city_model;
  · 缺失物种必须显式标记, 不得静默按 0;
  · 退化情景(CoC<=1.000001)必须单列, 不与正常情景混算;
  · 用相对容差.
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
A10 = ROOT / "A10_敏感性与边界"
sys.path.insert(0, str(A10))

# 复用 A30 已验证的引擎调用口径
_src = (ROOT / "A30_WP0取证" / "a21_solute_closure.py").read_text(encoding="utf-8")
_src = _src.replace('if __name__ == "__main__":\n    main()', "")
_ns: dict = {"__file__": str(ROOT / "A30_WP0取证" / "a21_solute_closure.py"), "__name__": "_reuse"}
exec(compile(_src, "a21_solute_closure.py", "exec"), _ns)

# 五物种引用档限值 (LIMIT_SET=baseline, GB/T 50050-2017 循环水)
LIMITS = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
          "alkalinity": 350.0, "silica": 175.0}
POTABLE = {"TDS": 180.0, "chloride": 35.0, "hardness": 120.0,
           "alkalinity": 100.0, "silica": 10.0}

# SAMPLES 在 main() 中由 city_model.load_samples() 权威读取后覆盖(见 [0])。
# 此处留空占位, 避免自造化学值。
SAMPLES: dict = {}
CORE = ("TDS", "chloride", "hardness", "alkalinity", "silica")
COC_FLOOR = 1.000001


def make_proj(dom, sample_name, species, tds_override=None):
    """构造一个配置: 把再生水化学设为给定物种; 缺失物种【不写入】(引擎按 0)."""
    proj, ts = _ns["load"](dom)
    import copy as _c
    proj = _c.deepcopy(proj)
    dc = proj["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = 8.0
    dc["cooling"]["water_quality_limits"] = dict(LIMITS)
    q = dict(species)
    if tds_override is not None:
        q["TDS"] = float(tds_override)
    dc["water_sources"]["reclaimed"]["quality_mg_l"] = q
    dc["water_sources"]["potable"]["quality_mg_l"] = dict(POTABLE)
    sim = proj.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(ts["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(ts["date"].iloc[-1]).date())
    return proj, ts, dc


def run_phi(dom, sample_name, species, phi, tds_override=None):
    """跑给定掺混比 phi, 返回 M1(补水) 与 CoC_ai."""
    proj, ts, dc = make_proj(dom, sample_name, species, tds_override)
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(phi)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(phi)
    res = _ns["FullAIUWMModel"](proj, ts).run()
    d = res.data_center_daily
    g = lambda c: (pd.to_numeric(d[c], errors="coerce") if c in d.columns
                   else pd.Series([np.nan] * len(d)))
    return {
        "M1": float(g("external_makeup_ml").sum()),
        "coc_mean": float(g("cycles_of_concentration").mean()),
        "coc_min": float(g("cycles_of_concentration").min()),
        "blowdown": float(g("blowdown_ml").sum()),
        "n_days": int(len(d)),
    }


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("WP3-2  H4(组成反转符号) 在完整物种水样上的稳健性检验")
    rec("=" * 84)

    # ---------- 0. 权威水样化学(从 city_model.load_samples 读取, 非自造) ----------
    rec("\n[0] 权威水样化学 (来源: city_model.load_samples())")
    import sys as _s
    _s.path.insert(0, str(A10))
    import city_model as cm
    samp = cm.load_samples()
    engine_samples = {}
    for _, row in samp.iterrows():
        q = {}
        for sp in CORE:
            v = row.get(sp)
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                q[sp] = float(v)
        # 引擎侧 hardness 由 Ca+Mg 推导; load_samples 已给 hardness 列
        hv = row.get("hardness")
        if hv is not None and not (isinstance(hv, float) and np.isnan(hv)):
            q["hardness"] = float(hv)
        engine_samples[str(row["source"])] = q
        rec(f"  {str(row['source']):<48} 本脚本用物种={sorted(q)}")
    rec(f"  ℹ 权威表共 {len(samp)} 条, 其中 Figshare BW 为 brackish(非再生水), 不纳入本检验")

    # 只保留被主扫描使用的 4 个再生水水样
    global SAMPLES
    SAMPLES = {k: v for k, v in engine_samples.items()
               if k in ("IEUA RP-1 (2025, tertiary)",
                        "LADWP AWPF (2012, RO product)",
                        "Figshare RW (2025, paired study)",
                        "AI-UWM model assumption")}

    # ---------- 1. 组成完整性登记 ----------
    rec("\n[1] 水样组成完整性登记 (缺失物种不写入引擎 => 按 0)")
    rec(f"  {'sample':<34} {'物种数':>6} {'缺失':<28} 状态")
    samples_meta = {}
    for name, sp in SAMPLES.items():
        miss = [c for c in CORE if c not in sp]
        has = len([c for c in CORE if c in sp])
        status = "COMPLETE" if not miss else "INCOMPLETE"
        samples_meta[name] = {"n_species": has, "missing": miss, "status": status}
        rec(f"  {name:<34} {has:>6} {','.join(miss) if miss else '-':<28} {status}")

    # ---------- 2. 逐水样跑 phi 扫描 ----------
    rec("\n[2] 逐水样 phi 扫描 (phi=0 无回用 / phi=0.6 回用), CoC 与补水")
    rec(f"  {'domain':>6} {'sample':<30} {'phi':>5} {'M1(ML)':>12} {'CoC_mean':>9} "
        f"{'CoC_min':>10} 判定")
    rows = []
    for dom in ("ha",):
        for name, sp in SAMPLES.items():
            for phi in (0.0, 0.6):
                try:
                    r = run_phi(dom, name, sp, phi)
                except Exception as e:
                    rec(f"  {dom:>6} {name:<30} {phi:>5} RUN_FAILED {type(e).__name__}: {e}")
                    continue
                degenerate = r["coc_min"] <= COC_FLOOR + 1e-12
                tag = "DEGENERATE" if degenerate else "ok"
                rec(f"  {dom:>6} {name:<30} {phi:>5.1f} {r['M1']:12.4g} "
                    f"{r['coc_mean']:9.5f} {r['coc_min']:10.5f} {tag}")
                rows.append({"domain": dom, "sample": name, "phi": phi, **r,
                             "degenerate": bool(degenerate),
                             **samples_meta[name]})

    df = pd.DataFrame(rows)

    # ---------- 3. q 与符号反转判定 ----------
    rec("\n[3] ★ 逐水样 q 与 dS_pot 符号 (q>0 <=> CoC1>CoC0)")
    rec(f"  {'sample':<34} {'CoC0':>8} {'CoC1':>9} {'q':>10} {'状态':<12} 说明")
    per_sample = []
    for name in SAMPLES:
        s0 = df[(df["sample"] == name) & (df["phi"] == 0.0)]
        s1 = df[(df["sample"] == name) & (df["phi"] == 0.6)]
        if len(s0) == 0 or len(s1) == 0:
            continue
        CoC0 = float(s0["coc_mean"].iloc[0])
        CoC1 = float(s1["coc_mean"].iloc[0])
        M0 = float(s0["M1"].iloc[0])
        M1 = float(s1["M1"].iloc[0])
        q = (CoC1 - CoC0) / (CoC1 * (CoC0 - 1)) if (CoC1 * (CoC0 - 1)) != 0 else float("nan")
        meta = samples_meta[name]
        deg = bool(s1["degenerate"].iloc[0])
        if deg:
            st = "DEGENERATE"
        elif meta["status"] == "INCOMPLETE":
            st = "INCOMPLETE"
        else:
            st = "VALID"
        note = ("触 CoC 下限 => 结果不可用于机制归因" if deg
                else ("组成不完整, 缺失按 0" if meta["status"] == "INCOMPLETE"
                      else "可用"))
        rec(f"  {name:<34} {CoC0:8.4f} {CoC1:9.4f} {q:10.5f} {st:<12} {note}")
        per_sample.append({"sample": name, "CoC0": CoC0, "CoC1": CoC1, "q": q,
                           "M0": M0, "M1": M1, "status": st, "n_species": meta["n_species"],
                           "missing": meta["missing"], "degenerate": deg})

    # ---------- 4. 裁定 ----------
    rec("\n[4] ★ 裁定: H4 在【完整物种】水样上是否成立")
    valid = [p for p in per_sample if p["status"] == "VALID"]
    invalid = [p for p in per_sample if p["status"] != "VALID"]
    rec(f"  完整且非退化的水样 = {len(valid)}: {[p['sample'] for p in valid]}")
    rec(f"  退化或组成不完整   = {len(invalid)}: {[p['sample'] for p in invalid]}")
    if len(valid) >= 2:
        qs = [p["q"] for p in valid]
        has_pos = any(q > 0 for q in qs)
        has_neg = any(q < 0 for q in qs)
        if has_pos and has_neg:
            verdict = "SUPPORTED_ON_VALID_SAMPLES"
            rec("  ✓ 在两个【完整物种、非退化】水样间观察到 q 的符号分化")
            rec("    => H4(组成反转符号) 在有效样本上仍然成立 ⇒ 可作为核心机制")
        else:
            verdict = "NOT_SUPPORTED_ON_VALID_SAMPLES"
            rec("  ✗ 完整物种水样的 q 符号【未分化】")
            rec("    => 此前的'符号反转'可能主要由 Figshare(缺 2 物种, 触下限)驱动")
            rec("    => 必须降级 H4: 不得作为核心机制主张")
    else:
        verdict = "INSUFFICIENT_VALID_SAMPLES"
        rec("  ⚠ 完整物种水样不足 2 个 ⇒ 无法判定 ⇒ 不得声称 H4 成立")

    rec("\n[5] 附: 弱化后的可主张范围")
    rec("  若 H4 仅在有效样本上部分成立, 可主张的是:")
    rec("    '在完整物种组成下, 再生水是否比自来水更清洁决定了 q 的符号,")
    rec("     进而决定回用是降低还是升高补水' (闭式, 可检验)")
    rec("  不可主张: '水质普遍能反转结论' (需跨更多真实水样验证)")

    summary = {
        "purpose": "检验 H4(组成反转 dS_pot 符号) 是否仅在退化/不完整水样上成立",
        "samples_meta": samples_meta,
        "per_sample": per_sample,
        "valid_samples": [p["sample"] for p in valid],
        "invalid_samples": [p["sample"] for p in invalid],
        "verdict": verdict,
        "coc_floor": COC_FLOOR,
        "limits_used": LIMITS,
        "potable_used": POTABLE,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": ("引擎只读; 缺失物种显式标记; 退化情景单列; 不用绝对容差"),
    }
    (HERE / "wp3_h4_robustness_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    df.to_csv(HERE / "wp3_h4_robustness_cases.csv", index=False, encoding="utf-8-sig")
    (HERE / "wp3_h4_robustness_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp3_h4_robustness_summary.json / _cases.csv / _log.txt ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
