"""T19d — 补全包络：把 T19b 修正后的 Figshare 数据纳入 CoC 包络，并汇总最终区间。

为什么需要本脚本:
  T6_water_chemistry_samples.csv 因提取 bug 缺 SO4/碱度, 导致 Figshare RW/BW 在
  T19c 中被跳过。T19b 已从源表恢复这两个值。本脚本用**修正后**的水质重跑包络,
  使"允许 CoC 区间"覆盖全部可用的真实水源。

同时输出 coc_envelope.csv 的数据行（本脚本只算, 落盘由 build_outputs 负责）。
只读, 只写 A19。
"""
from __future__ import annotations

import io
import json
import math
import re
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
A4 = HERE.parent / "A4_水化学参数域"
EV = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src" / "research_2026" / "external_evidence"

MM = {"Na": 22.99, "K": 39.10, "HCO3": 61.02, "Cl": 35.45,
      "Ca": 40.08, "Mg": 24.31, "SO4": 96.06}

INHIB = {
    "none_thermodynamic": (0.0, 1.0, "high"),
    "LSI_1.5": (1.5, 10 ** 1.5, "medium"),
    "LSI_2.0": (2.0, 100.0, "medium"),
    "LSI_2.477_300x": (2.477, 300.0, "low"),
    "LSI_3.0": (3.0, 1000.0, "low"),
}
NON_INHIBITED = ("Gypsum", "Anhydrite", "SiO2(a)")
ALL_PH = ("Calcite", "Aragonite", "Dolomite", "Gypsum", "Anhydrite",
          "SiO2(a)", "Halite", "Nahcolite", "Trona", "Quartz", "Chalcedony")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", str(s))


def corrected_figshare():
    raw = pd.read_excel(EV / "figshare_reclaimed_water_2025" / "Table_2.xls", header=None)
    hdr = [str(x) for x in raw.iloc[0].tolist()]
    idx = {}
    for n in ("Na", "K", "HCO3", "Cl", "Ca", "Mg", "SO4"):
        pat = re.compile(re.escape(n) + r"\d*")
        for j, h in enumerate(hdr):
            t = strip_tags(h).strip()
            core = re.sub(r"[+-]+$", "", re.split(r"[\s(]", t)[0])
            if pat.fullmatch(core):
                idx[n] = j
                break
    out = []
    for i in (1, 2):
        row = raw.iloc[i].tolist()
        label = strip_tags(row[0]).strip()
        c = {n: float(row[j]) * MM[n] for n, j in idx.items()}
        out.append({
            "source": f"Figshare {label} (corrected extraction)",
            "Ca": c["Ca"], "Mg": c["Mg"], "Na": c["Na"], "chloride": c["Cl"],
            "SO4": c["SO4"], "alkalinity": c["HCO3"] * 50.04 / 61.02,
            "silica": np.nan, "pH": float(row[2]),
            "TDS": 0.65 * float(row[1]),
        })
    return out


def envelope(row, target, db="vitens.dat", T=25.0, upper=1000.0):
    from phreeqpython import PhreeqPython
    buf = io.StringIO()
    with redirect_stdout(buf):
        pp = PhreeqPython(database=db)

    def sis(mult):
        """返回 SI 字典; PHREEQC 在高浓缩下会因 'Solute mass exceeds solution mass'
        报错（物理上确实无法再浓缩）, 此时返回 None 表示**该倍数不可计算**。"""
        comp = {"-units": "mg/L", "-temp": str(T), "pH": f"{float(row['pH']):.4f}"}
        for k, kk in (("Ca", "Ca"), ("Mg", "Mg"), ("Na", "Na"), ("chloride", "Cl")):
            v = row.get(k)
            comp[kk] = f"{(float(v) if pd.notna(v) else 0.0) * mult:.6f}"
        comp["S(6)"] = f"{float(row['SO4']) * mult:.6f} as SO4"
        comp["Alkalinity"] = f"{float(row['alkalinity']) * mult:.6f} as CaCO3"
        sv = row.get("silica")
        if sv is not None and pd.notna(sv):
            comp["Si"] = f"{float(sv) * mult:.6f}"
        try:
            with redirect_stdout(buf):
                s = pp.add_solution(comp)
                return {ph: (float(s.phases[ph]) if (ph in s.phases and s.phases[ph] is not None
                                                     and np.isfinite(float(s.phases[ph])))
                             else float("nan")) for ph in ALL_PH}
        except Exception:
            return None

    out = {"target_SI_calcite": target}
    s1 = sis(1.0)
    if s1 is None:
        out.update(CoC=None, note="1x 即不可计算")
        return out
    out["SI_at_1x"] = {k: _r(v) for k, v in s1.items()}
    if s1["Calcite"] > target:
        out.update(CoC=0.0, CoC_effective=0.0,
                   note="1x 已超目标(该水质本身即结垢型, 需先处理/掺混/加酸)")
        return out

    # 找一个 PHREEQC 能算的上界
    hi = upper
    while hi > 1.0 and sis(hi) is None:
        hi *= 0.7
    if hi <= 1.0 or sis(hi)["Calcite"] < target:
        out.update(CoC=None, note=f"未在可计算范围内达到目标 (最大可算 {hi:.1f}x)")
        return out
    lo = 1.0
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        sm = sis(mid)
        if sm is not None and sm["Calcite"] < target:
            lo = mid
        else:
            hi = mid
    coc = 0.5 * (lo + hi)
    out["CoC"] = round(coc, 4)
    out["SI_at_CoC"] = {k: _r(v) for k, v in (sis(coc) or {}).items()}

    non = {}
    for ph in NON_INHIBITED:
        if pd.isna(row.get("silica", np.nan)) and ph == "SiO2(a)":
            non[ph] = None; continue
        if s1.get(ph, float("nan")) > 0:
            non[ph] = 0.0; continue
        if not (sis(hi) or {}).get(ph, float("nan")) > 0:
            non[ph] = None; continue
        a, b = 1.0, hi
        for _ in range(45):
            mid = 0.5 * (a + b)
            sm = sis(mid)
            if sm is not None and sm[ph] < 0:
                a = mid
            else:
                b = mid
        non[ph] = round(0.5 * (a + b), 4)
    out["CoC_non_inhibited_phases"] = non
    cands = [coc] + [v for v in non.values() if v]
    out["CoC_effective"] = round(min(cands), 4)
    return out


def _r(v):
    return None if (v is None or not np.isfinite(v)) else round(float(v), 4)


def main() -> int:
    logf = open(HERE / "t19d.log", "w", encoding="utf-8", errors="replace")

    def P(*a):
        line = " ".join(str(x) for x in a).encode("utf-8", "replace").decode("utf-8")
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("ascii", "replace").decode("ascii"))
        print(line, file=logf); logf.flush()

    P("=" * 100)
    P("T19d 修正后 Figshare 数据的 CoC 包络")
    P("=" * 100)
    rows = corrected_figshare()
    res = {}
    for row in rows:
        P(f"\n[{row['source']}]  Ca={row['Ca']:.2f} Mg={row['Mg']:.2f} "
          f"Na={row['Na']:.1f} Cl={row['chloride']:.1f} SO4={row['SO4']:.1f} "
          f"alk={row['alkalinity']:.1f} pH={row['pH']}  (silica: 源表无)")
        blk = {}
        for tag, (lsi, ratio, conf) in INHIB.items():
            r = envelope(row, lsi)
            blk[tag] = {"LSI_tol": lsi, "ratio_x": ratio, "confidence": conf, **r}
            P(f"   {tag:22s} CoC={r.get('CoC')}  有效={r.get('CoC_effective')}  "
              f"非阻垢相={r.get('CoC_non_inhibited_phases')}  {r.get('note','')}")
            if r.get("SI_at_1x"):
                si = r["SI_at_1x"]
                P("      SI@1x: " + "  ".join(
                    f"{k}={si[k]}" for k in ("Calcite", "Dolomite", "Gypsum",
                                             "Aragonite") if si.get(k) is not None))
        res[row["source"]] = blk

    (HERE / "T19d_corrected_figshare_envelope.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ---------------- GSA 实测运行值 ----------------
    P("\n" + "=" * 100)
    P("GSA (Lloyd D. George 法院, Las Vegas) 实测运行 CoC —— 唯一可访问的运行观测")
    P("=" * 100)
    gsa = pd.read_csv(EV / "gsa_blowdown_recovery_2023" / "cooling_tower_periods_normalized.csv")
    P(gsa.to_string(index=False))
    P("\n  GSA Table 6 水质准则（加药运行下的验收窗）:")
    for k, v in (("Total Alkalinity (ppm)", "100–1,000"), ("pH", "7.3–9.0"),
                 ("Chloride (ppm)", "10–500"), ("CoC", ">2"),
                 ("Total Hardness (ppm)", "500–1,500"), ("Conductivity (uS/cm)", "<2,400"),
                 ("Silica (ppm)", "<150"), ("Calcium Hardness (ppm)", "<500"),
                 ("Magnesium Hardness (ppm)", "<100"), ("Sulfates (ppm)", "<250")):
        P(f"    {k:32s} {v}")

    summary = {
        "corrected_figshare": res,
        "gsa_observed_coc": gsa.to_dict("records"),
        "gsa_water_quality_criteria": {
            "total_alkalinity_ppm": "100-1000", "pH": "7.3-9.0",
            "chloride_ppm": "10-500", "CoC": ">2",
            "total_hardness_ppm": "500-1500", "conductivity_uS_cm": "<2400",
            "silica_ppm": "<150", "calcium_hardness_ppm": "<500",
            "magnesium_hardness_ppm": "<100", "sulfates_ppm": "<250",
            "source_url": ("https://www.gsa.gov/system/files/"
                           "052-Blowdown%20Recovery%20System%20Full%20Report.pdf"),
        },
    }
    (HERE / "T19d_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    logf.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
