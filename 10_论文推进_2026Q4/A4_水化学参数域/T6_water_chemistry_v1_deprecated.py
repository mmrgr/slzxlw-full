"""⚠ 已废弃 (DEPRECATED) —— 改名保留作历史对照, 请勿运行。

清理轮 2026-10-14 处置 (用户拍板: "保留"):
  本文件是 T6 的 **v1**, 已被 `T6_water_chemistry_v2.py` (审计修复版) 取代:
    A5  chi 未截断 -> v2 改用 chi_eff = min(CoC_lim, CoC_design)/CoC_design
    B1  保守判据与沉淀判据混用 -> v2 分开报告
    B2  panel 与样本完整性混淆 -> v2 先出完整性矩阵
    B3  阈值来源是引擎占位值 -> v2 给三档敏感性 (定稿前由 T6b 换成带引用准则)
    C1  Figshare 的 TDS 是 EC 估算、chloride 键名 bug -> v2 修正
    C2  苦咸水不是再生水 -> v2 单列为非再生水边界情形

  ⚠ v1 与 v2 **写同一批文件名, 且列模式互不兼容**:
      v1 写出  CoC_lim_full_panel / chi_full / f_star
      v2 写出  CoC_lim_all_ratio / chi_eff_* / f_star_2ind / n_present / charge_error_pct
  故本文件已把输出名统一加 `_v1legacy` 后缀 —— 否则一旦误跑就会**静默覆写**
  `T6_coc_limits.csv` / `T6_water_chemistry_samples.csv`,
  使 T15 (Fig.3) 与 A6 (Fig.S2) 直接 KeyError。

  重跑水化学参数域请用:
      python A4_水化学参数域/T6_water_chemistry_v2.py

  ⚠ 相关遗留: `A6_可信度配图/make_fig2.py` 仍按 v1 的列名 (source/TDS/chloride/f_star)
    读取上述文件, 自 v2 于 11:19 覆写产物后即无法运行 —— 见
    `13_死代码与重复逻辑清单_v1.md` §B-1 与 `14_清理执行报告_v1.md`。

原始说明
--------
T6 — 水化学参数域: 用公开再生水实测组成界定 chi = CoC_lim/CoC_design

预注册: ../A0_预注册/preregistration.md  (§7 判据一致性)

目的 (G2 降级实现, 不等私有设施数据):
  1. 用真实水样的完整离子组成, 反推冷却塔可达浓缩倍数 CoC_lim
  2. 给出 chi = CoC_lim / CoC_design 的真实分布与**限值物种排序**
  3. 检验模型内假设的再生水 (TDS 650, Cl 130) 在实测数据包络中的位置
  4. 分别报告"工程限值判据"与"矿物饱和度判据", 不混合 (P0 修正)

阈值 (与引擎一致, 只读, 不得回标定): TDS 2200 / chloride 500 /
  hardness 700 / alkalinity 500 / silica 150  (mg/L; 硬度/碱度 as CaCO3)
设计 CoC = 5.0;  自来水质 TDS 180 / Cl 35 (引擎内给定)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src"
EV = REPO / "research_2026" / "external_evidence"

LIMITS = {"TDS": 2200.0, "chloride": 500.0, "hardness": 700.0,
          "alkalinity": 500.0, "silica": 150.0}
COC_DESIGN = 5.0
POTABLE = {"TDS": 180.0, "chloride": 35.0}
MODEL_ASSUMED = {"TDS": 650.0, "chloride": 130.0}

MM = {"Na": 22.99, "K": 39.10, "HCO3": 61.02, "Cl": 35.45,
      "Ca": 40.08, "Mg": 24.31, "SO4": 96.06}


def hardness_as_caco3(ca: float, mg: float) -> float:
    return 2.497 * ca + 4.118 * mg


def coc_lim(comp: dict[str, float], limits=LIMITS) -> tuple[float, str]:
    """返回 (CoC_lim, 限值物种)。comp 为冷却水中的浓度 (mg/L)。"""
    best, who = np.inf, "none"
    for k, lim in limits.items():
        if k in comp and comp[k] > 0:
            v = lim / comp[k]
            if v < best:
                best, who = v, k
    return (best, who) if np.isfinite(best) else (np.nan, "n/a")


# ---------------------------------------------------------------- 数据源
def load_ieua() -> dict:
    d = pd.read_csv(EV / "ieua_recycled_water_reports" / "RP1_2025_normalized.csv")
    g = {r.metric: float(r.average) for r in d.itertuples()}
    return {
        "source": "IEUA RP-1 (2025, tertiary)",
        "sclass": "municipal tertiary reclaimed",
        "TDS": g["tds_mg_l"], "chloride": g["chloride_mg_l"],
        "Ca": g["calcium_mg_l"], "Mg": g["magnesium_mg_l"],
        "Na": g["sodium_mg_l"], "SO4": g["sulfate_mg_l"],
        "alkalinity": g["alkalinity_mg_l_as_caco3"],
        "silica": g["silica_mg_l"], "pH": g["pH"],
    }


def load_ladwp() -> dict:
    d = pd.read_csv(EV / "ladwp_gwr_2012" / "AWPF_RO_product_normalized.csv")
    g = {}
    for r in d.itertuples():
        try:
            g[r.metric] = float(r.reported_value)
        except (TypeError, ValueError):
            pass
    return {
        "source": "LADWP AWPF (2012, RO product)",
        "sclass": "RO product (advanced treated)",
        "TDS": g.get("tds_mg_l", np.nan), "chloride": g.get("chloride_mg_l", np.nan),
        "Ca": g.get("calcium_mg_l", np.nan), "Mg": g.get("magnesium_mg_l", np.nan),
        "Na": g.get("sodium_mg_l", np.nan), "SO4": g.get("sulfate_mg_l", np.nan),
        "alkalinity": g.get("alkalinity_mg_l_as_caco3", np.nan),
        "silica": g.get("silica_mg_l", np.nan), "pH": g.get("pH", np.nan),
    }


def load_figshare() -> list[dict]:
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
        # EC(uS/cm) -> TDS(mg/L), 常用近似 TDS ~ 0.65 * EC
        comp["TDS"] = 0.65 * ec
        comp["alkalinity"] = comp.get("HCO3", np.nan) * (50.04 / 61.02)
        comp["silica"] = np.nan
        comp["pH"] = float(row[2]) if pd.notna(row[2]) else np.nan
        out.append({
            "source": f"Figshare {label} (2025, paired study)",
            "sclass": "reclaimed (RW, high-salinity)" if label == "RW" else "brackish (BW)",
            **{k: comp.get(k, np.nan) for k in
               ("TDS", "chloride", "Ca", "Mg", "Na", "SO4", "alkalinity", "silica", "pH")},
        })
    return out


# ---------------------------------------------------------------- 主流程
def build_samples() -> pd.DataFrame:
    rows = [load_ieua(), load_ladwp()] + load_figshare()
    rows.append({
        "source": "AI-UWM model assumption", "sclass": "assumed in main model",
        "TDS": MODEL_ASSUMED["TDS"], "chloride": MODEL_ASSUMED["chloride"],
        "Ca": np.nan, "Mg": np.nan, "Na": np.nan, "SO4": np.nan,
        "alkalinity": np.nan, "silica": np.nan, "pH": np.nan,
    })
    d = pd.DataFrame(rows)
    d["hardness"] = hardness_as_caco3(d["Ca"].fillna(0), d["Mg"].fillna(0))
    d.loc[d["hardness"] <= 0, "hardness"] = np.nan
    return d


def analyse(d: pd.DataFrame) -> pd.DataFrame:
    rec = []
    for r in d.itertuples():
        comp_full = {k: getattr(r, k) for k in LIMITS if pd.notna(getattr(r, k, np.nan))}
        coc_full, who_full = coc_lim(comp_full)
        comp_2 = {k: getattr(r, k) for k in ("TDS", "chloride") if pd.notna(getattr(r, k, np.nan))}
        coc_2, who_2 = coc_lim(comp_2)
        # 混合扫描: 只对 TDS/Cl 可比的源做
        fstar = np.nan
        if pd.notna(r.TDS) and pd.notna(r.chloride):
            for phi in np.linspace(0, 1, 1001):
                mix = {"TDS": POTABLE["TDS"] + phi * (r.TDS - POTABLE["TDS"]),
                       "chloride": POTABLE["chloride"] + phi * (r.chloride - POTABLE["chloride"])}
                c, _ = coc_lim(mix, {"TDS": LIMITS["TDS"], "chloride": LIMITS["chloride"]})
                if c <= COC_DESIGN:
                    fstar = phi
                    break
        rec.append({
            "source": r.source, "sclass": r.sclass,
            "TDS": r.TDS, "chloride": r.chloride, "hardness": getattr(r, "hardness", np.nan),
            "alkalinity": r.alkalinity, "silica": r.silica,
            "CoC_lim_full_panel": coc_full, "limiting_species_full": who_full,
            "CoC_lim_TDS_Cl_only": coc_2, "limiting_species_2": who_2,
            "chi_full": coc_full / COC_DESIGN if np.isfinite(coc_full) else np.nan,
            "chi_2indicator": coc_2 / COC_DESIGN if np.isfinite(coc_2) else np.nan,
            "f_star": fstar,
        })
    return pd.DataFrame(rec)


def main() -> int:
    # ⚠ 输出名已加 `_v1legacy` 后缀, 防止误跑覆写 v2 的产物 (见文件头说明)。
    d = build_samples()
    d.to_csv(HERE / "T6_water_chemistry_samples_v1legacy.csv", index=False, encoding="utf-8-sig")
    a = analyse(d)
    a.to_csv(HERE / "T6_coc_limits_v1legacy.csv", index=False, encoding="utf-8-sig")

    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    print("===== 公开再生水水样 → CoC_lim 与限值物种")
    print(a[["source", "TDS", "chloride", "hardness", "silica",
             "CoC_lim_full_panel", "limiting_species_full",
             "CoC_lim_TDS_Cl_only", "chi_full", "f_star"]].round(2).to_string(index=False))

    real = a[~a.source.str.contains("model assumption")]
    print(f"\nchi_full: 实测范围 {real.chi_full.min():.2f} – {real.chi_full.max():.2f} "
          f"(n={len(real)})")
    print(f"限值物种分布: {real.limiting_species_full.value_counts().to_dict()}")
    print(f"模型假设 TDS=650 → chi = "
          f"{a[a.source.str.contains('model assumption')].chi_2indicator.iloc[0]:.2f}")

    summary = {
        "n_real_samples": int(len(real)),
        "chi_full_range": [float(real.chi_full.min()), float(real.chi_full.max())],
        "chi_2ind_range": [float(real.chi_2indicator.min()), float(real.chi_2indicator.max())],
        "limiting_species_counts": real.limiting_species_full.value_counts().to_dict(),
        "model_assumed_TDS": MODEL_ASSUMED["TDS"],
        "model_assumed_chi": float(a[a.source.str.contains("model assumption")].chi_2indicator.iloc[0]),
        "f_star_by_source": {r.source: (None if pd.isna(r.f_star) else float(r.f_star))
                             for r in a.itertuples()},
    }
    (HERE / "T6_summary_v1legacy.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n[write] {HERE/'T6_coc_limits_v1legacy.csv'}  {HERE/'T6_summary_v1legacy.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
