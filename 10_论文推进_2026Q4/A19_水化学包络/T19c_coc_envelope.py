"""T19c — 允许 CoC 包络：无加药热力学下界 vs 加药运行上界。

核心桥接（本脚本的关键一步）:
  公开阻垢剂文献给出的是"可控制到 N 倍方解石饱和度"。
  Langelier 饱和指数与 PHREEQC 的方解石饱和指数在定义上同为
      LSI = SI_calcite = log10(IAP / K_sp(calcite))
  因此"300 倍饱和度" ⇔ IAP/Ksp = 300 ⇔ LSI = SI_calcite = log10(300) = 2.477。
  → 文献里的"LSI 维持到 2–3"与"300 倍方解石饱和度"是同一件事的两种说法。
  本脚本据此把**文献给出的阻垢剂耐受限**换算成本项目的 CoC 上界。

判据（同一水质、同一数据库 vitens.dat 下逐一计算）:
  A. 比值法 (TDS/Cl/hardness/alkalinity/silica 限值) —— 工程筛选口径
  B. 饱和指数法, **不设阻垢剂** (SI_calcite <= 0) —— 热力学下界（原报告口径）
  C. 饱和指数法, **设阻垢剂** (SI_calcite <= LSI_tol), LSI_tol ∈ {1.5, 2.0, 2.5, 3.0}
     —— 但**同时**要求石膏/硅相等"阻垢剂不覆盖"的相不越界（否则上界由它们决定）
  D. 观测 CoC（GSA 实测运行值）

诚实性约定:
  - C 是"阻垢剂把方解石约束放松后, 其他相/其他判据接管"的**条件上界**, 不是保证值。
  - 文献 300× 来自厂商会议论文 (Calgon), 非独立第三方, 标注 confidence=low。
只读, 只写 A19。
"""
from __future__ import annotations

import io
import json
import math
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
A4 = HERE.parent / "A4_水化学参数域"

# 文献给出的阻垢剂耐受限（以方解石饱和倍数表示 → LSI）
INHIBITOR_TOLERANCE = {
    "none_thermodynamic": {"ratio_x": 1.0, "LSI": 0.0,
                           "source": "热力学平衡（无加药）", "confidence": "high"},
    "LSI_1.5": {"ratio_x": 10 ** 1.5, "LSI": 1.5,
                "source": "阻垢剂典型运行窗口下界", "confidence": "medium"},
    "LSI_2.0": {"ratio_x": 100.0, "LSI": 2.0,
                "source": "阻垢剂运行窗口（LSI 2 量级）", "confidence": "medium"},
    "LSI_2.477_300x": {"ratio_x": 300.0, "LSI": 2.477,
                       "source": "Sherwood 1994 / Cognetti 1996: 控制到 300 倍方解石饱和度",
                       "confidence": "low"},
    "LSI_3.0": {"ratio_x": 1000.0, "LSI": 3.0,
                "source": "阻垢剂先进配方上界", "confidence": "low"},
}

# 阻垢剂"不覆盖"的相（其沉淀不受膦酸盐/聚合物阈值效应抑制到同样程度）
NON_INHIBITED = ("Gypsum", "Anhydrite", "SiO2(a)")
ALL_PH = ("Calcite", "Aragonite", "Dolomite", "Gypsum", "Anhydrite",
          "SiO2(a)", "Halite", "Nahcolite", "Trona", "Quartz", "Chalcedony")


def coc_for_si(row, target_SI_calcite: float, db="vitens.dat", T=25.0, upper=1000.0):
    """求使 SI_calcite ≈ target 的 CoC, 同时报告该点所有相 SI, 以及'非阻垢相'的越界 CoC。"""
    from phreeqpython import PhreeqPython
    buf = io.StringIO()
    with redirect_stdout(buf):
        pp = PhreeqPython(database=db)

    def sis(mult):
        comp = {"-units": "mg/L", "-temp": str(T), "pH": f"{float(row['pH']):.4f}"}
        for k, kk in (("Ca", "Ca"), ("Mg", "Mg"), ("Na", "Na"), ("chloride", "Cl")):
            v = row.get(k)
            comp[kk] = f"{(float(v) if pd.notna(v) else 0.0) * mult:.6f}"
        comp["S(6)"] = f"{float(row['SO4']) * mult:.6f} as SO4"
        comp["Alkalinity"] = f"{float(row['alkalinity']) * mult:.6f} as CaCO3"
        comp["Si"] = f"{float(row['silica']) * mult:.6f}"
        with redirect_stdout(buf):
            s = pp.add_solution(comp)
            return {ph: (float(s.phases[ph]) if (ph in s.phases and s.phases[ph] is not None
                                                 and np.isfinite(float(s.phases[ph])))
                         else float("nan")) for ph in ALL_PH}

    def si_cal(mult):
        return sis(mult)["Calcite"]

    _cache: dict = {}

    def d0sis_cache(ph, m):
        key = (ph, round(m, 8))
        if key not in _cache:
            _cache[key] = sis(m).get(ph, float("nan"))
        return _cache[key]

    # 单调二分求 SI_calcite = target（CoC 增大 → SI 增大）
    lo, hi = 1.0, upper
    f_lo, f_hi = si_cal(lo) - target_SI_calcite, si_cal(hi) - target_SI_calcite
    out = {"target_SI_calcite": target_SI_calcite, "db": db, "temp_C": T}
    if f_lo > 0:
        out["CoC"] = 0.0; out["note"] = "1x 已超目标"
        return out
    if f_hi < 0:
        out["CoC"] = None; out["note"] = f"未在 {upper} 内达到目标"
        return out
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if si_cal(mid) - target_SI_calcite < 0:
            lo = mid
        else:
            hi = mid
    coc = 0.5 * (lo + hi)
    d = sis(coc)
    out["CoC"] = round(coc, 4)
    out["SI_at_CoC"] = {k: (round(v, 4) if math.isfinite(v) else None) for k, v in d.items()}

    # 非阻垢相的越界 CoC（这些相不受膦酸盐阈值效应保护）
    non = {}
    for ph in NON_INHIBITED:
        lo2, hi2 = 1.0, upper
        if d0sis_cache(ph, 1.0) > 0:
            non[ph] = 0.0; continue
        if d0sis_cache(ph, upper) < 0:
            non[ph] = None; continue
        for _ in range(45):
            mid = 0.5 * (lo2 + hi2)
            if d0sis_cache(ph, mid) < 0:
                lo2 = mid
            else:
                hi2 = mid
        non[ph] = round(0.5 * (lo2 + hi2), 4)
    out["CoC_non_inhibited_phases"] = non
    cands = [coc] + [v for v in non.values() if v is not None and v > 0]
    out["CoC_effective"] = round(min(cands), 4)
    return out


def main() -> int:
    logf = open(HERE / "t19c.log", "w", encoding="utf-8", errors="replace")

    def P(*a):
        line = " ".join(str(x) for x in a).encode("utf-8", "replace").decode("utf-8")
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("ascii", "replace").decode("ascii"))
        print(line, file=logf); logf.flush()

    P("=" * 104)
    P("T19c 允许 CoC 包络：无加药热力学下界 → 加药运行上界")
    P("=" * 104)
    P("\n阻垢剂耐受限（LSI ↔ 方解石饱和倍数, 二者同定义 LSI = SI_calcite = log10(IAP/Ksp)）:")
    for k, v in INHIBITOR_TOLERANCE.items():
        P(f"  {k:22s} {v['ratio_x']:8.1f}x  LSI={v['LSI']:5.3f}  conf={v['confidence']:6s}  {v['source']}")

    samp = pd.read_csv(A4 / "T6_water_chemistry_samples.csv")
    recs = samp.to_dict("records")

    # 只对能跑 PHREEQC 的样本（有完整离子 + pH + silica）
    need = ("Ca", "Na", "chloride", "SO4", "alkalinity", "silica", "pH")
    out = {}
    P("\n" + "-" * 104)
    for row in recs:
        name = str(row["source"])
        ok = all(pd.notna(row.get(k)) for k in need) and pd.notna(row.get("Mg", np.nan))
        if not ok:
            miss = [k for k in need if pd.isna(row.get(k))]
            P(f"\n[{name[:60]}]  跳过: 缺 {miss}")
            out[name] = {"skipped": True, "missing": miss}
            continue
        P(f"\n[{name[:60]}]")
        blk = {}
        for tag, cfg in INHIBITOR_TOLERANCE.items():
            r = coc_for_si(row, cfg["LSI"])
            blk[tag] = {**cfg, **r}
            P(f"    {tag:22s} LSI_tol={cfg['LSI']:.3f}  "
              f"CoC(SI_calcite={cfg['LSI']:.3f})={r.get('CoC')}  "
              f"非阻垢相上界={r.get('CoC_non_inhibited_phases')}  "
              f"有效={r.get('CoC_effective')}")
            if r.get("SI_at_CoC"):
                si = r["SI_at_CoC"]
                P("        SI: " + "  ".join(
                    f"{k}={si[k]}" for k in ("Calcite", "Aragonite", "Gypsum",
                                             "SiO2(a)", "Halite") if si.get(k) is not None))
        out[name] = blk

    (HERE / "T19c_coc_envelope_raw.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    P(f"\n写出 {HERE/'T19c_coc_envelope_raw.json'}")
    logf.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
