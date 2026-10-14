"""T6 v2 — 水化学参数域界定（审计修复版, 2026-10-14）

修复 05_方法审计_v1 中的:
  A5  chi 未截断 -> 改用 chi_eff = min(CoC_lim, CoC_design)/CoC_design
  B1  保守物种判据与沉淀物种判据混用 -> 分开报告:
         (i) 工程限值-保守物种比值法 (TDS / chloride / SO4)
         (ii) 非保守物种比值法 (hardness / alkalinity / silica) —— 仅提示
         (iii) PHREEQC 矿物饱和度判据 (Calcite/Dolomite/Gypsum/Anhydrite/硅相)
  B2  panel A/B 与样本完整性混淆 -> 先出完整性矩阵, 只在完整样本上做多判据比较
  B3  阈值来源是引擎占位值 -> 给出保守/基准/宽松三档 + 敏感性扫描
  C1  Figshare 的 TDS 是 EC 估算值, 且 chloride 键名 bug -> 修正并标注电荷平衡误差
  C2  苦咸水(BW)不是再生水 -> 剔出再生水分布, 单列为非再生水边界情形

输出:
  T6_water_chemistry_samples.csv   增强样本表 (含完整性/估算标记/电荷平衡)
  T6_coc_limits.csv                逐样本多判据 CoC 与 chi_eff
  T6_threshold_sensitivity.csv     阈值三档敏感性
  T6_summary.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src"
EV = REPO / "research_2026" / "external_evidence"

COC_DESIGN = 5.0
POTABLE = {"TDS": 180.0, "chloride": 35.0}
MODEL_ASSUMED = {"TDS": 650.0, "chloride": 130.0}

# B3: 冷却水工程准则的常用取值区间 (保守 / 基准 / 宽松)
# 基准档 = 引擎内占位值 (data/ai_data_center_database.json, type="assumption");
# 区间端点代表公开冷却水指南常见量级, 论文定稿前需补具体引用.
LIMIT_SETS = {
    "conservative": {"TDS": 1500.0, "chloride": 300.0, "hardness": 400.0,
                     "alkalinity": 300.0, "silica": 100.0},
    "baseline": {"TDS": 2200.0, "chloride": 500.0, "hardness": 700.0,
                 "alkalinity": 500.0, "silica": 150.0},
    "permissive": {"TDS": 3000.0, "chloride": 800.0, "hardness": 1000.0,
                   "alkalinity": 700.0, "silica": 200.0},
}
CONSERVATIVE_SPECIES = ("TDS", "chloride", "SO4")
PRECIPITATION_SPECIES = ("hardness", "alkalinity", "silica")
PHASES = ("Calcite", "Dolomite", "Gypsum", "Anhydrite", "SiO2(a)")

MM = {"Na": 22.99, "K": 39.10, "HCO3": 61.02, "Cl": 35.45,
      "Ca": 40.08, "Mg": 24.31, "SO4": 96.06}


def hardness_as_caco3(ca: float, mg: float) -> float:
    return 2.497 * ca + 4.118 * mg


# ---------------------------------------------------------------- 数据源
def load_ieua() -> dict:
    d = pd.read_csv(EV / "ieua_recycled_water_reports" / "RP1_2025_normalized.csv")
    g = {r.metric: float(r.average) for r in d.itertuples()}
    return {"sample": "IEUA RP-1 (2025, tertiary)",
            "sclass": "municipal tertiary reclaimed", "is_reclaimed": True,
            "TDS": g["tds_mg_l"], "chloride": g["chloride_mg_l"],
            "Ca": g["calcium_mg_l"], "Mg": g["magnesium_mg_l"],
            "Na": g["sodium_mg_l"], "SO4": g["sulfate_mg_l"],
            "alkalinity": g["alkalinity_mg_l_as_caco3"],
            "silica": g["silica_mg_l"], "pH": g["pH"], "TDS_is_estimated": False}


def load_ladwp() -> dict:
    d = pd.read_csv(EV / "ladwp_gwr_2012" / "AWPF_RO_product_normalized.csv")
    g = {}
    for r in d.itertuples():
        try:
            g[r.metric] = float(r.reported_value)
        except (TypeError, ValueError):
            pass
    return {"sample": "LADWP AWPF (2012, RO product)",
            "sclass": "RO product (advanced treated)", "is_reclaimed": True,
            "TDS": g.get("tds_mg_l", np.nan), "chloride": g.get("chloride_mg_l", np.nan),
            "Ca": g.get("calcium_mg_l", np.nan), "Mg": g.get("magnesium_mg_l", np.nan),
            "Na": g.get("sodium_mg_l", np.nan), "SO4": g.get("sulfate_mg_l", np.nan),
            "alkalinity": g.get("alkalinity_mg_l_as_caco3", np.nan),
            "silica": g.get("silica_mg_l", np.nan), "pH": g.get("pH", np.nan),
            "TDS_is_estimated": False}


def load_figshare() -> list[dict]:
    """C1 修复: 键名 Cl -> chloride; 标记 TDS 为 EC 估算; BW 单列非再生水."""
    p = EV / "figshare_reclaimed_water_2025" / "Table_2.xls"
    raw = pd.read_excel(p, header=None)
    hdr = [str(x) for x in raw.iloc[0].tolist()]
    names = ["Na", "K", "HCO3", "Cl", "Ca", "Mg", "SO4"]
    idx = {}
    for n in names:
        for j, h in enumerate(hdr):
            if f"<b>{n}<sup" in h or f"{n}<sup" in h.replace("<b>", "").replace("</b>", ""):
                idx[n] = j
                break
    out = []
    for i in (1, 2):
        row = raw.iloc[i].tolist()
        label = str(row[0]).strip()
        comp = {}
        for n, j in idx.items():
            comp[n] = float(row[j]) * MM[n] if pd.notna(row[j]) else np.nan
        ec = float(row[1]) if pd.notna(row[1]) else np.nan
        chloride = comp.get("Cl", np.nan)
        alk = comp.get("HCO3", np.nan) * (50.04 / 61.02) if pd.notna(comp.get("HCO3")) else np.nan
        is_recl = (label == "RW")
        out.append({
            "sample": f"Figshare {label} (2025, paired study)",
            "sclass": "reclaimed (RW, high-salinity)" if is_recl else
                      "brackish (BW) — NOT reclaimed water",
            "is_reclaimed": bool(is_recl),
            "TDS": 0.65 * ec, "chloride": chloride,
            "Ca": comp.get("Ca", np.nan), "Mg": comp.get("Mg", np.nan),
            "Na": comp.get("Na", np.nan), "SO4": comp.get("SO4", np.nan),
            "alkalinity": alk, "silica": np.nan,
            "pH": float(row[2]) if pd.notna(row[2]) else np.nan,
            "TDS_is_estimated": True,   # C1: 由 EC×0.65 换算, 非实测
        })
    return out


def build_samples() -> pd.DataFrame:
    rows = [load_ieua(), load_ladwp()] + load_figshare()
    rows.append({"sample": "AI-UWM model assumption", "sclass": "assumed in main model",
                 "is_reclaimed": True, "TDS": MODEL_ASSUMED["TDS"],
                 "chloride": MODEL_ASSUMED["chloride"], "Ca": np.nan, "Mg": np.nan,
                 "Na": np.nan, "SO4": np.nan, "alkalinity": np.nan, "silica": np.nan,
                 "pH": np.nan, "TDS_is_estimated": False})
    d = pd.DataFrame(rows)
    d["hardness"] = hardness_as_caco3(d["Ca"].fillna(0), d["Mg"].fillna(0))
    d.loc[d["hardness"] <= 0, "hardness"] = np.nan
    return d


# ---------------------------------------------------------------- 判据
def completeness(d: pd.DataFrame) -> pd.DataFrame:
    """B2: 样本完整性矩阵."""
    cols = ["TDS", "chloride", "Ca", "Mg", "Na", "SO4", "alkalinity", "silica", "pH"]
    out = []
    for r in d.itertuples():
        present = [c for c in cols if pd.notna(getattr(r, c, np.nan))]
        err = charge_imbalance(r)
        out.append({"sample": r.sample, "n_present": len(present),
                    "missing": ",".join([c for c in cols if c not in present]),
                    "charge_error_pct": err,
                    "charge_balanced": bool(np.isfinite(err) and abs(err) <= 10.0)})
    return pd.DataFrame(out)


def charge_imbalance(r) -> float:
    """C1: 主要离子电荷平衡误差 % (阳离子/阴离子最大值为分母)."""
    try:
        ca, mg, na = float(r.Ca), float(r.Mg), float(r.Na)
        cl, so4, alk = float(r.chloride), float(r.SO4), float(r.alkalinity)
    except (TypeError, ValueError):
        return np.nan
    if not all(np.isfinite([ca, mg, na, cl, so4, alk])):
        return np.nan
    cations = 2 * ca / 40.078 + 2 * mg / 24.305 + na / 22.98977
    anions = cl / 35.453 + 2 * so4 / 96.06 + alk / 50.043
    denom = max(cations, anions)
    return 100.0 * abs(cations - anions) / denom if denom > 0 else np.nan


def coc_lim_ratio(comp: dict, limits: dict, species) -> tuple[float, str]:
    """比值法 CoC_lim (仅对给定物种子集)."""
    best, who = np.inf, "none"
    for k in species:
        lim = limits.get(k)
        v = comp.get(k, np.nan)
        if lim and v and np.isfinite(v) and v > 0:
            ratio = lim / v
            if ratio < best:
                best, who = ratio, k
    return (float(best), who) if np.isfinite(best) else (np.nan, "n/a")


def phreeqc_safe_multiplier(row, database="vitens.dat", upper=100.0) -> dict:
    """B1(iii): 独立矿物饱和度判据 —— 最大浓缩倍数使所有目标 SI <= 0."""
    try:
        from phreeqpython import PhreeqPython
    except ImportError:
        return {"phreeqc_available": False}
    pp = PhreeqPython(database=database)

    def solution(mult):
        comp = {
            "-units": "mg/L", "-temp": "25", "pH": str(float(row.pH)),
            "Ca": str(float(row.Ca) * mult),
            "Mg": str(float(row.Mg if pd.notna(row.Mg) else 0.0) * mult),
            "Na": str(float(row.Na) * mult),
            "Cl": str(float(row.chloride) * mult),
            "S(6)": f"{float(row.SO4) * mult} as SO4",
            "Alkalinity": f"{float(row.alkalinity) * mult} as CaCO3",
            "Si": str(float(row.silica) * mult),
        }
        return pp.add_solution(comp)

    def safe(mult):
        s = solution(mult)
        for ph in PHASES:
            v = float(s.phases.get(ph, np.nan))
            if math.isfinite(v) and v > 0.0:   # NaN 相(如缺 Mg 时的 Dolomite)不代表超饱和
                return False
        return True

    if not safe(1.0):
        return {"phreeqc_available": True, "safe_multiplier": 0.0,
                "limiting_phase": "already_supersaturated_at_1x"}
    if safe(upper):
        return {"phreeqc_available": True, "safe_multiplier": upper,
                "limiting_phase": "none_below_upper"}
    lo, hi = 1.0, upper
    for _ in range(30):
        mid = (lo + hi) / 2.0
        if safe(mid):
            lo = mid
        else:
            hi = mid
    s_lo = solution(lo)
    sis = {ph: float(s_lo.phases.get(ph, np.nan)) for ph in PHASES}
    finite = {k: v for k, v in sis.items() if math.isfinite(v)}
    limiting = max(finite, key=finite.get) if finite else "n/a"
    return {"phreeqc_available": True, "safe_multiplier": lo, "limiting_phase": limiting,
            "SI_at_limit": round(sis.get(limiting, float("nan")), 3)}


def f_star_2ind(tds: float, cl: float, limits: dict) -> float:
    """仅 TDS/Cl 的掺混临界比 (与自来水质比较)."""
    if not (np.isfinite(tds) and np.isfinite(cl)):
        return np.nan
    for phi in np.linspace(0, 1, 2001):
        mix = {"TDS": POTABLE["TDS"] + phi * (tds - POTABLE["TDS"]),
               "chloride": POTABLE["chloride"] + phi * (cl - POTABLE["chloride"])}
        c, _ = coc_lim_ratio(mix, limits, ("TDS", "chloride"))
        if c <= COC_DESIGN:
            return float(phi)
    return np.nan


# ---------------------------------------------------------------- 主流程
def main() -> int:
    d = build_samples()
    comp_df = completeness(d)
    d = d.merge(comp_df[["sample", "n_present", "missing", "charge_error_pct"]],
                on="sample", how="left")
    # 保持向后兼容的列名 "source" (T2 / T8 / T9 均按此读取)
    d.rename(columns={"sample": "source"}).to_csv(
        HERE / "T6_water_chemistry_samples.csv", index=False, encoding="utf-8-sig")
    print("===== B2 样本完整性矩阵")
    print(comp_df.round(2).to_string(index=False))

    rows = []
    for r in d.itertuples():
        comp = {k: getattr(r, k) for k in
                ("TDS", "chloride", "SO4", "hardness", "alkalinity", "silica")
                if pd.notna(getattr(r, k, np.nan))}
        eng_coc, eng_who = coc_lim_ratio(comp, LIMIT_SETS["baseline"], CONSERVATIVE_SPECIES)
        ppt_coc, ppt_who = coc_lim_ratio(comp, LIMIT_SETS["baseline"], PRECIPITATION_SPECIES)
        full_coc, full_who = coc_lim_ratio(comp, LIMIT_SETS["baseline"],
                                           CONSERVATIVE_SPECIES + PRECIPITATION_SPECIES)
        # PHREEQC: 需完整离子 + pH
        ph_res = {"phreeqc_available": False}
        if all(pd.notna(getattr(r, k, np.nan)) for k in
               ("Ca", "Na", "chloride", "SO4", "alkalinity", "silica", "pH")) \
                and pd.notna(r.hardness):
            ph_res = phreeqc_safe_multiplier(r)
        ph_coc = ph_res.get("safe_multiplier", np.nan)

        def chi(v):
            return min(v, COC_DESIGN) / COC_DESIGN if np.isfinite(v) else np.nan

        rows.append({
            "sample": r.sample, "sclass": r.sclass, "is_reclaimed": bool(r.is_reclaimed),
            "TDS_is_estimated": bool(r.TDS_is_estimated),
            "n_present": r.n_present, "charge_error_pct": r.charge_error_pct,
            "CoC_lim_engine_conservative": eng_coc, "who_engine": eng_who,
            "CoC_lim_precipitation_ratio": ppt_coc, "who_precipitation": ppt_who,
            "CoC_lim_all_ratio": full_coc, "who_all": full_who,
            "CoC_lim_phreeqc": ph_coc, "limiting_phase_phreeqc": ph_res.get("limiting_phase", "n/a"),
            "chi_eff_conservative": chi(eng_coc),      # A5 截断
            "chi_eff_all_ratio": chi(full_coc),
            "chi_eff_phreeqc": chi(ph_coc),
            "f_star_2ind": f_star_2ind(r.TDS, r.chloride, LIMIT_SETS["baseline"]),
        })
    a = pd.DataFrame(rows)
    a.to_csv(HERE / "T6_coc_limits.csv", index=False, encoding="utf-8-sig")

    pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40)
    print("\n===== 多判据 CoC_lim 与 chi_eff (A5: chi 已截断到 <=1)")
    print(a[["sample", "CoC_lim_engine_conservative", "who_engine",
             "CoC_lim_precipitation_ratio", "who_precipitation",
             "CoC_lim_phreeqc", "limiting_phase_phreeqc",
             "chi_eff_conservative", "chi_eff_all_ratio", "chi_eff_phreeqc"]]
          .round(3).to_string(index=False))

    # ---- B3 阈值敏感性 ----
    srows = []
    for r in d.itertuples():
        if not pd.notna(r.TDS):
            continue
        comp = {k: getattr(r, k) for k in
                ("TDS", "chloride", "SO4", "hardness", "alkalinity", "silica")
                if pd.notna(getattr(r, k, np.nan))}
        for tier, lim in LIMIT_SETS.items():
            c_all, who = coc_lim_ratio(comp, lim, CONSERVATIVE_SPECIES + PRECIPITATION_SPECIES)
            srows.append({"sample": r.sample, "tier": tier, "CoC_lim_all": c_all,
                          "who": who, "chi_eff": min(c_all, COC_DESIGN) / COC_DESIGN
                          if np.isfinite(c_all) else np.nan})
    sdf = pd.DataFrame(srows)
    sdf.to_csv(HERE / "T6_threshold_sensitivity.csv", index=False, encoding="utf-8-sig")
    print("\n===== B3 阈值三档敏感性 (全物种比值法)")
    print(sdf.pivot_table(index="sample", columns="tier", values="CoC_lim_all")
          .round(2).to_string())

    # ---- C2: 只在再生水样本上报告 chi 跨度 ----
    recl = a[(a.is_reclaimed) & (~a["sample"].str.contains("model assumption"))]
    all_chi = recl.chi_eff_all_ratio.dropna()
    print(f"\n===== 再生水样本 chi_eff (A5 截断后), n={len(recl)}")
    print(f"  conservative 判据: {recl.chi_eff_conservative.min():.3f} – "
          f"{recl.chi_eff_conservative.max():.3f}")
    print(f"  全物种比值法:      {all_chi.min():.3f} – {all_chi.max():.3f}  "
          f"(跨度 {all_chi.max()/max(all_chi.min(),1e-9):.1f}x, 非旧报告的 200x)")
    ph_chi = recl.chi_eff_phreeqc.dropna()
    if len(ph_chi):
        print(f"  PHREEQC 判据:      {ph_chi.min():.3f} – {ph_chi.max():.3f} (n={len(ph_chi)})")
    bw = a[a["sample"].str.contains("BW ")]
    if len(bw):
        print(f"  [C2] 苦咸水 BW 已剔出再生水分布: chi_eff_all = "
              f"{bw.chi_eff_all_ratio.iloc[0]:.3f} (非再生水边界情形)")

    summary = {
        "n_samples": int(len(a)),
        "n_complete_ion_panel": int((comp_df.n_present >= 9).sum()),
        "chi_eff_definition": "min(CoC_lim, CoC_design)/CoC_design  (A5 fix)",
        "reclaimed_chi_eff_range_all_ratio": [float(all_chi.min()), float(all_chi.max())],
        "reclaimed_chi_eff_range_conservative": [
            float(recl.chi_eff_conservative.min()), float(recl.chi_eff_conservative.max())],
        "phreeqc_chi_eff_range": ([float(ph_chi.min()), float(ph_chi.max())]
                                  if len(ph_chi) else None),
        "limiting_species_counts_all_ratio": recl.who_all.value_counts().to_dict(),
        "limiting_phase_counts_phreeqc": (recl.limiting_phase_phreeqc.value_counts().to_dict()
                                          if len(ph_chi) else None),
        "threshold_tiers": LIMIT_SETS,
        "model_assumed_TDS": MODEL_ASSUMED["TDS"],
        "charge_balance": comp_df[["sample", "charge_error_pct"]].round(2).to_dict("records"),
        "claim_boundary": "chi_eff <= 1 only; values >1 have no physical meaning "
                          "because the engine itself caps CoC at the design value.",
    }
    (HERE / "T6_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n[write] {HERE/'T6_coc_limits.csv'}  {HERE/'T6_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
