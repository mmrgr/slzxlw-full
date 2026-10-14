"""T19 — 热力学数据库与判据敏感性（A19 水化学包络）

目的（GPT 意见2 §问题4 的"不同热力学数据库/物种定义会改变预测"）:
  1. 核实 vitens.dat 的性质与适用边界（读库头 + 统计相/物种/元素）。
  2. 在**同一输入溶液**下换库（vitens.dat / phreeqc.dat / pitzer.dat /
     wateq4f_PWN.dat），比较方解石/石膏/二氧化硅等相的饱和状态是否改变，
     以及"最大安全浓缩倍数 CoC_safe"是否改变。
  3. 温度敏感性：原模型固定 -temp 25；冷却塔实际循环水常高于此。
  4. 判据敏感性：比值法 vs 饱和指数法。

相分类（这是本脚本的关键方法学决定）:
  - SAFE_PHASES_ORIG : 原实现 T6_water_chemistry_v2.PHASES —— 逐字复现项目数字。
  - SAFE_PHASES_EXT  : ORIG + 动力学上"可能在冷却塔时间尺度内实际沉淀"的相
                       (Aragonite/Hydroxyapatite/Struvite/Halite/Nahcolite/Trona)。
  - REPORT_ONLY      : Quartz / Chalcedony / Vaterite / Ca3(PO4)2 —— **仅报 SI, 不作限值**。
                       理由: 石英与玉髓在 <100 °C 的冷却水时间尺度上受动力学抑制,
                       天然水几乎恒为过饱和(本脚本 SI@1x ≈ +0.4~0.7), 若计入会给出
                       无意义的 CoC_safe = 0; 球霰石(Vaterite)是 CaCO3 亚稳相,
                       热力学稳定相是方解石。这是"相选择"敏感性本身的一部分,
                       在报告中显式记录, 不隐藏。

输出: T19_db_sensitivity.json / T19_db_sensitivity.csv / t19.log（只写 A19 目录）
"""
from __future__ import annotations

import io
import json
import math
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
A4 = HERE.parent / "A4_水化学参数域"
DBDIR = Path(sys.executable).resolve().parents[1] / "Lib" / "site-packages" / "phreeqpython" / "database"

# 逐字复现原实现
SAFE_PHASES_ORIG = ("Calcite", "Dolomite", "Gypsum", "Anhydrite", "SiO2(a)")
# 扩展：动力学上可能实际沉淀的其他结垢相
SAFE_PHASES_EXT = SAFE_PHASES_ORIG + ("Aragonite", "Hydroxyapatite", "Struvite",
                                      "Halite", "Nahcolite", "Trona")
# 仅报告 SI，不作限值（动力学亚稳 / 抑制相）
REPORT_ONLY = ("Quartz", "Chalcedony", "Vaterite", "Ca3(PO4)2", "Fluorite",
               "Celestite", "Barite", "Siderite", "Fe(OH)3(a)")
ALL_PHASES = tuple(dict.fromkeys(SAFE_PHASES_EXT + REPORT_ONLY))

DBS = ("vitens.dat", "phreeqc.dat", "pitzer.dat", "wateq4f_PWN.dat")
TEMPS = (25.0, 35.0, 45.0)


# --------------------------------------------------------------- 数据库性质
def db_profile(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    txt = path.read_text(encoding="utf-8", errors="replace")
    lines = txt.splitlines()
    phases, master, species = [], [], 0
    mode = None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        u = s.upper()
        if u.startswith("SOLUTION_MASTER_SPECIES"):
            mode = "master"; continue
        if u.startswith("SOLUTION_SPECIES"):
            mode = "species"; continue
        if u.startswith("PHASES"):
            mode = "phases"; continue
        if u.startswith(("RATES", "END", "SELECTED_OUTPUT", "PITZER",
                         "EXCHANGE_MASTER_SPECIES", "SURFACE_MASTER_SPECIES",
                         "LLNL_AQUEOUS_MODEL_PARAMETERS")):
            mode = None; continue
        if s.startswith("#"):
            continue
        if mode == "phases" and not ln[0].isspace():
            phases.append(s.split()[0])
        elif mode == "master" and not ln[0].isspace():
            master.append(s.split()[0])
        elif mode == "species":
            species += 1
    phases = sorted(set(phases))
    master = sorted(set(master))
    return {
        "exists": True, "path": str(path), "bytes": path.stat().st_size,
        "header_lines": [h.rstrip() for h in lines[:14] if h.strip()][:12],
        "n_phases": len(phases), "phases": phases,
        "n_master_elements": len(master), "master_elements": master,
        "n_solution_species_lines": species,
        "has_PITZER_block": "PITZER" in txt.upper(),
        "has_LLNL_block": "LLNL_AQUEOUS_MODEL_PARAMETERS" in txt.upper(),
        "has_Si_master": any(m == "Si" for m in master),
        "has_Alkalinity_in_header": "Alkalinity" in txt,
    }


# --------------------------------------------------------------- 溶液构造
def solution_card(row: dict, mult: float, temp: float) -> dict:
    """与原 T6 v2 逐字一致的溶液定义（跨库可比的唯一前提）。"""
    def num(v):
        return float(v) if v is not None and np.isfinite(v) else 0.0

    return {
        "-units": "mg/L", "-temp": str(temp), "pH": f"{float(row['pH']):.4f}",
        "Ca": f"{num(row['Ca']) * mult:.6f}",
        "Mg": f"{num(row['Mg']) * mult:.6f}",
        "Na": f"{num(row['Na']) * mult:.6f}",
        "Cl": f"{num(row['chloride']) * mult:.6f}",
        "S(6)": f"{num(row['SO4']) * mult:.6f} as SO4",
        "Alkalinity": f"{num(row['alkalinity']) * mult:.6f} as CaCO3",
        "Si": f"{num(row['silica']) * mult:.6f}",
    }


def run_db(db: str, rows: list[dict], upper: float = 200.0) -> dict:
    out: dict = {"database": db, "ok": False, "results": []}
    try:
        from phreeqpython import PhreeqPython
    except Exception as e:
        out["error"] = f"import: {type(e).__name__}: {e}"; return out

    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            pp = PhreeqPython(database=db)
    except Exception as e:
        out["error"] = f"init {db}: {type(e).__name__}: {e}"
        out["stdout_tail"] = buf.getvalue()[-900:]
        return out
    out["ok"] = True

    for r in rows:
        if not math.isfinite(float(r["pH"])):
            out["results"].append({"sample": r["source"], "skipped": "no pH (assumption row)"})
            continue
        for T in TEMPS:
            rec: dict = {"sample": r["source"], "temp_C": T, "db": db}
            try:
                def sis(mult):
                    with redirect_stdout(buf):
                        s = pp.add_solution(solution_card(r, mult, T))
                        d = {ph: (float(s.phases[ph]) if (ph in s.phases
                                                          and s.phases[ph] is not None
                                                          and np.isfinite(float(s.phases[ph])))
                                  else float("nan"))
                             for ph in ALL_PHASES}
                    return d

                s1 = sis(1.0)
                rec["SI_at_1x"] = {k: (round(v, 4) if math.isfinite(v) else None)
                                   for k, v in s1.items()}

                # 对给定的"限值相集"做二分
                def coc_safe(safe_phases):
                    def safe(mult):
                        d = sis(mult)
                        for k in safe_phases:
                            v = d.get(k, float("nan"))
                            if math.isfinite(v) and v > 0.0:
                                return False, k
                        return True, None
                    ok1, who1 = safe(1.0)
                    if not ok1:
                        return 0.0, f"already_supersaturated_at_1x:{who1}", None
                    okU, _ = safe(upper)
                    if okU:
                        return upper, "none_below_upper", None
                    lo, hi = 1.0, upper
                    for _ in range(45):
                        mid = 0.5 * (lo + hi)
                        s_ok, _w = safe(mid)
                        if s_ok:
                            lo = mid
                        else:
                            hi = mid
                    d = sis(lo)
                    # 限值相只能在 safe_phases 内取最大 SI（修复：此前误用全相集，
                    # 会把受动力学抑制的 Quartz 误报为限制相）
                    fin = {k: d[k] for k in safe_phases
                           if k in d and math.isfinite(d[k])}
                    who = max(fin, key=fin.get) if fin else "n/a"
                    return round(lo, 4), who, {k: round(v, 4) for k, v in
                                               {kk: vv for kk, vv in d.items()
                                                if math.isfinite(vv)}.items()}

                for tag, phs in (("orig", SAFE_PHASES_ORIG), ("ext", SAFE_PHASES_EXT)):
                    c, who, si = coc_safe(phs)
                    rec[f"CoC_safe_{tag}"] = c
                    rec[f"limiting_phase_{tag}"] = who
                    if si:
                        rec[f"SI_at_limit_{tag}"] = si

                # 关键浓缩倍数处的全相 SI（用于解释判据差异）
                cmax = rec.get("CoC_safe_orig") or 1.0
                for m in (1.0, 2.0, 2.52, 3.0, 3.57, 5.0):
                    if m <= max(float(cmax), 1.0) * 2.5:
                        rec[f"SI_at_CoC_{m}"] = {
                            k: (round(v, 4) if math.isfinite(v) else None)
                            for k, v in sis(m).items()}
            except Exception as e:
                rec["error"] = f"{type(e).__name__}: {e}"
            out["results"].append(rec)
    out["stdout_tail"] = buf.getvalue()[-900:]
    return out


def main() -> int:
    logf = open(HERE / "t19.log", "w", encoding="utf-8", errors="replace")

    def P(*a):
        line = " ".join(str(x) for x in a)
        line = line.encode("utf-8", "replace").decode("utf-8")
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("ascii", "replace").decode("ascii"))
        print(line, file=logf); logf.flush()

    P("=" * 104)
    P("T19 热力学数据库 / 相选择 / 判据敏感性   (phreeqpython 自带数据库)")
    P("=" * 104)
    P(f"库目录: {DBDIR}")
    P(f"限值相集 orig : {SAFE_PHASES_ORIG}")
    P(f"限值相集 ext  : {SAFE_PHASES_EXT}")
    P(f"仅报 SI       : {REPORT_ONLY}")

    profiles, prof_light = {}, {}
    for d in DBS:
        pr = db_profile(DBDIR / d)
        plist = [str(x) for x in pr.get("phases", [])]
        prof_light[d] = {k: v for k, v in pr.items() if k != "phases"}
        prof_light[d]["phase_presence"] = {ph: (ph in plist) for ph in ALL_PHASES}
        profiles[d] = prof_light[d]
        P(f"\n[{d}] exists={pr['exists']} bytes={pr.get('bytes')} "
          f"phases={pr.get('n_phases')} master_elements={pr.get('n_master_elements')} "
          f"PITZER={pr.get('has_PITZER_block')} LLNL={pr.get('has_LLNL_block')} "
          f"Si_master={pr.get('has_Si_master')}")
        for h in pr.get("header_lines", [])[:6]:
            P("      | " + h[:118])
        miss = [ph for ph in ALL_PHASES if not prof_light[d]["phase_presence"].get(ph)]
        P(f"      目标相缺失: {miss}")
    P("\n[请求但不可用] " + str([d for d in ("minteq.v4.dat", "minteq.dat",
                                             "llnl.dat", "sit.dat")
                                 if not (DBDIR / d).exists()]))

    samp = pd.read_csv(A4 / "T6_water_chemistry_samples.csv")
    rows = samp.to_dict("records")
    P("\n样本: " + " | ".join(str(r["source"])[:44] for r in rows))

    results = {}
    for db in DBS:
        if not (DBDIR / db).exists():
            results[db] = {"ok": False, "error": "file_missing", "results": []}
            continue
        P(f"\n{'#' * 104}\n### {db}\n{'#' * 104}")
        res = run_db(db, rows)
        results[db] = res
        if not res.get("ok"):
            P(f"  !! {res.get('error')}")
            if res.get("stdout_tail"):
                P("  stdout_tail: " + res["stdout_tail"][-300:].replace("\n", " | "))
            continue
        for rec in res["results"]:
            tag = f"{str(rec.get('sample'))[:44]:46s} T={rec.get('temp_C')}"
            if "error" in rec:
                P(f"  {tag}  ERROR {rec['error'][:70]}"); continue
            if "skipped" in rec:
                P(f"  {tag}  skipped ({rec['skipped']})"); continue
            P(f"  {tag}  CoC_orig={rec.get('CoC_safe_orig')} "
              f"({rec.get('limiting_phase_orig')})  "
              f"CoC_ext={rec.get('CoC_safe_ext')} ({rec.get('limiting_phase_ext')})")
            si = rec.get("SI_at_1x", {})
            P("      SI@1x(orig相): " + "  ".join(
                f"{k}={si.get(k)}" for k in SAFE_PHASES_ORIG if si.get(k) is not None))
            P("      SI@1x(其他)  : " + "  ".join(
                f"{k}={si.get(k)}" for k in REPORT_ONLY if si.get(k) is not None))

    # ---------------- 跨库对比表 ----------------
    P("\n" + "=" * 104)
    P("跨库对比 (仅 IEUA RP-1: 唯一 9/9 离子完整且电荷平衡的样本)")
    P("=" * 104)
    hdr = (f"{'db':17s} {'T':>5s} {'CoC_orig':>9s} {'limit(orig)':>22s} "
           f"{'CoC_ext':>8s} {'limit(ext)':>20s} {'SIcal@1':>8s} {'SIgyp@1':>8s} "
           f"{'SISiO2a@1':>10s} {'SIQtz@1':>8s}")
    P(hdr); P("-" * len(hdr))
    cmp_rows = []
    for db, res in results.items():
        if not res.get("ok"):
            continue
        for rec in res.get("results", []):
            if not str(rec.get("sample", "")).startswith("IEUA"):
                continue
            si = rec.get("SI_at_1x")
            if not si:
                continue
            P(f"{db:17s} {rec['temp_C']:5.1f} {str(rec.get('CoC_safe_orig')):>9s} "
              f"{str(rec.get('limiting_phase_orig')):>22s} "
              f"{str(rec.get('CoC_safe_ext')):>8s} "
              f"{str(rec.get('limiting_phase_ext')):>20s} "
              f"{str(si.get('Calcite')):>8s} {str(si.get('Gypsum')):>8s} "
              f"{str(si.get('SiO2(a)')):>10s} {str(si.get('Quartz')):>8s}")
            cmp_rows.append({"db": db, "temp_C": rec["temp_C"],
                             "CoC_safe_orig": rec.get("CoC_safe_orig"),
                             "limiting_phase_orig": rec.get("limiting_phase_orig"),
                             "CoC_safe_ext": rec.get("CoC_safe_ext"),
                             "limiting_phase_ext": rec.get("limiting_phase_ext"),
                             **{f"SI1_{k}": v for k, v in si.items()}})
    if cmp_rows:
        pd.DataFrame(cmp_rows).to_csv(HERE / "T19_db_sensitivity.csv",
                                      index=False, encoding="utf-8-sig")

    # ---------------- 结论 ----------------
    def coc_at(db, T, tag="orig", sample="IEUA"):
        for rec in results.get(db, {}).get("results", []):
            if (str(rec.get("sample", "")).startswith(sample)
                    and rec.get("temp_C") == T):
                return rec.get(f"CoC_safe_{tag}")
        return None

    concl = []
    v25 = coc_at("vitens.dat", 25.0, "orig")
    for db in ("phreeqc.dat", "pitzer.dat", "wateq4f_PWN.dat"):
        o = coc_at(db, 25.0, "orig")
        if o is None or v25 is None:
            continue
        concl.append({"comparison": f"vitens.dat -> {db} @25C (orig phase set)",
                      "vitens": v25, "other": o,
                      "abs_diff": (float(o) - float(v25)) if (o and v25) else None,
                      "rel_diff_pct": (100.0 * (float(o) - float(v25)) / float(v25))
                      if (o and v25) else None})
    report = {
        "script": "T19_db_sensitivity.py",
        "phreeqpython_version": _ver(),
        "database_dir": str(DBDIR),
        "databases_available": [d for d in DBS if (DBDIR / d).exists()],
        "databases_requested_but_missing": [
            d for d in ("minteq.v4.dat", "minteq.dat", "llnl.dat", "sit.dat")
            if not (DBDIR / d).exists()],
        "phase_partition": {
            "SAFE_PHASES_ORIG_matches_original_implementation": list(SAFE_PHASES_ORIG),
            "SAFE_PHASES_EXT": list(SAFE_PHASES_EXT),
            "REPORT_ONLY_not_used_as_limit": list(REPORT_ONLY),
            "rationale": ("Quartz/Chalcedony 在 <100C 动力学抑制且天然水恒过饱和, "
                          "Vaterite 是 CaCO3 亚稳相; 若计入限值集会给出无意义的 "
                          "CoC_safe=0 (已实测确认)。该选择本身即'相选择敏感性',已记录。"),
        },
        "temperatures_C": list(TEMPS),
        "original_implementation": {
            "database": "vitens.dat (T6_water_chemistry_v2.py / T6b_limits_cited.py 默认)",
            "phases": list(SAFE_PHASES_ORIG), "temp_C_fixed": 25.0,
            "note": ("原实现只对同时具备 Ca/Na/Cl/SO4/alkalinity/silica/pH 的样本跑 "
                     "PHREEQC → 实际只有 IEUA 得到非 NaN 的 CoC_phreeqc = 2.5202"),
        },
        "db_profiles": profiles,
        "cross_db_ieua": concl,
        "results": results,
    }
    (HERE / "T19_db_sensitivity.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    P("\n跨库差异摘要 (25C, 原相集):")
    for c in concl:
        P(f"  {c['comparison']}: {c['vitens']} -> {c['other']}  "
          f"(Δ={c['abs_diff']}, {c['rel_diff_pct']}%)")
    P(f"\n写出 {HERE / 'T19_db_sensitivity.json'}")
    logf.close()
    return 0


def _ver():
    try:
        import importlib.metadata as md
        return md.version("phreeqpython")
    except Exception:
        return "unknown"


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
