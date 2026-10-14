"""T19b — 缺失项复核：项目报告的"缺项"里，哪些是**源数据真缺失**、哪些是**提取 bug**。

触发点（A19 审计独立发现）:
  T6_water_chemistry_samples.csv 把 Figshare RW/BW 标为 missing = "SO4,alkalinity,silica"。
  但源表 Table_2.xls 表头列 5 = HCO3, 列 9 = SO4 **都存在**。
  T6_water_chemistry_v2.load_figshare() 的表头匹配用的是
      f"<b>{n}<sup" in h  或  f"{n}<sup" in h
  —— 该模式对 "Na/K/Cl/Ca/Mg"（紧跟 <sup>）可用, 但对
     "HCO<sub ...>3</sub><sup>" 和 "SO<sub ...>4</sub><sup>"（带 <sub>）**匹配失败**。
  → 碱度与硫酸根被静默置为 NaN, 并被下游报告为"源数据缺失"。
  这与审计红线"不得把模型假设与公开观测混为一类"同属一类问题:
  把**提取失败**当成了**观测缺失**。

本脚本: (1) 复现该 bug; (2) 用正确的 HTML 标签剥离后重新提取;
        (3) 重算电荷平衡; (4) 用 PHREEQC 重跑原先"无法跑"的 Figshare RW;
        (5) 检查 LADWP 的 Mg 是否真的缺失; (6) 检查 IEUA 温度是否缺失。
只读源数据, 只写 A19 目录。
"""
from __future__ import annotations

import io
import json
import math
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src"
EV = REPO / "research_2026" / "external_evidence"

MM = {"Na": 22.99, "K": 39.10, "HCO3": 61.02, "Cl": 35.45,
      "Ca": 40.08, "Mg": 24.31, "SO4": 96.06}


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", str(s))


def old_matcher(hdr: list[str], n: str):
    """逐字复现 T6 v2 的匹配逻辑。"""
    for j, h in enumerate(hdr):
        if f"<b>{n}<sup" in h or f"{n}<sup" in h.replace("<b>", "").replace("</b>", ""):
            return j
    return None


def new_matcher(hdr: list[str], n: str):
    """先剥离 HTML 标签, 再去掉尾部电荷, 再用 '化学式 + 可选下标数字' 精确匹配。

    注意: 不能把 'SO42-' -> 'SO' 这样过度剥离 —— 尾部电荷要先于下标数字剥离,
    且下标数字只能出现在化学式**内部**。用 fullmatch 约束避免误匹配。
    """
    pat = re.compile(re.escape(n) + r"\d*")
    for j, h in enumerate(hdr):
        t = strip_tags(h).strip()
        core = re.split(r"[\s(]", t)[0]        # "SO42-" / "HCO3-" / "Na+"
        core = re.sub(r"[+-]+$", "", core)     # 去尾部电荷 -> "SO42" / "HCO3" / "Na"
        if pat.fullmatch(core):
            return j
    return None


def charge_imbalance(comp: dict) -> float:
    ca, mg, na = comp.get("Ca"), comp.get("Mg"), comp.get("Na")
    cl, so4, alk = comp.get("chloride"), comp.get("SO4"), comp.get("alkalinity")
    if not all(v is not None and np.isfinite(v) for v in (ca, mg, na, cl, so4, alk)):
        return float("nan")
    cat = 2 * ca / 40.078 + 2 * mg / 24.305 + na / 22.98977
    an = cl / 35.453 + 2 * so4 / 96.06 + alk / 50.043
    return 100.0 * abs(cat - an) / max(cat, an)


def main() -> int:
    logf = open(HERE / "t19b.log", "w", encoding="utf-8", errors="replace")

    def P(*a):
        line = " ".join(str(x) for x in a).encode("utf-8", "replace").decode("utf-8")
        try:
            print(line)
        except UnicodeEncodeError:
            print(line.encode("ascii", "replace").decode("ascii"))
        print(line, file=logf); logf.flush()

    rep: dict = {"script": "T19b_missing_recheck.py"}

    P("=" * 100)
    P("T19b 缺失项复核 —— 源数据真缺失 vs 提取 bug")
    P("=" * 100)

    # ---------------- 1. Figshare ----------------
    p = EV / "figshare_reclaimed_water_2025" / "Table_2.xls"
    raw = pd.read_excel(p, header=None)
    hdr = [str(x) for x in raw.iloc[0].tolist()]
    P("\n[1] Figshare Table_2.xls 表头（剥离标签后）:")
    for j, h in enumerate(hdr):
        P(f"    col{j:2d}  {strip_tags(h)[:60]:60s}")

    names = ["Na", "K", "HCO3", "Cl", "Ca", "Mg", "SO4"]
    P("\n    匹配结果对比 (old = T6 v2 的 <b>N<sup 逻辑; new = 剥离标签后匹配):")
    idx_old, idx_new = {}, {}
    for n in names:
        idx_old[n] = old_matcher(hdr, n)
        idx_new[n] = new_matcher(hdr, n)
        flag = "" if idx_old[n] == idx_new[n] else "   <== 差异!"
        P(f"      {n:5s} old={str(idx_old[n]):>4s}  new={str(idx_new[n]):>4s}{flag}")
    rep["figshare_header_match"] = {
        "old_index": idx_old, "new_index": idx_new,
        "mismatches": [n for n in names if idx_old[n] != idx_new[n]]}

    P("\n    逐样本重算:")
    fs = []
    for i in (1, 2):
        row = raw.iloc[i].tolist()
        label = strip_tags(row[0]).strip()
        comp_old, comp_new = {}, {}
        for n in names:
            v = row[idx_old[n]] if idx_old[n] is not None else np.nan
            comp_old[n] = float(v) * MM[n] if pd.notna(v) else np.nan
            v2 = row[idx_new[n]]
            comp_new[n] = float(v2) * MM[n] if pd.notna(v2) else np.nan
        alk_new = comp_new["HCO3"] * (50.04 / 61.02) if pd.notna(comp_new["HCO3"]) else np.nan
        ec = float(row[1])
        rec = {
            "label": label, "EC_uS_cm": ec, "pH": float(row[2]),
            "TDS_by_EC_x0.65": 0.65 * ec,
            "old": {k: (None if not np.isfinite(v) else round(v, 3))
                    for k, v in comp_old.items()},
            "new": {k: (None if not np.isfinite(v) else round(v, 3))
                    for k, v in comp_new.items()},
            "alkalinity_new_as_CaCO3": (None if not np.isfinite(alk_new) else round(alk_new, 3)),
        }
        o = {"Ca": comp_old["Ca"], "Mg": comp_old["Mg"], "Na": comp_old["Na"],
             "chloride": comp_old["Cl"], "SO4": comp_old["SO4"],
             "alkalinity": comp_old["HCO3"] * 50.04 / 61.02}
        nn = {"Ca": comp_new["Ca"], "Mg": comp_new["Mg"], "Na": comp_new["Na"],
              "chloride": comp_new["Cl"], "SO4": comp_new["SO4"], "alkalinity": alk_new}
        rec["charge_error_pct_old"] = _r(charge_imbalance(o))
        rec["charge_error_pct_new"] = _r(charge_imbalance(nn))
        fs.append(rec)
        P(f"      [{label}] EC={ec} pH={rec['pH']}  TDS(est)={0.65*ec:.1f}")
        P(f"        old: SO4={rec['old']['SO4']}  HCO3->alk={rec['old']['HCO3']} "
          f"  电荷误差={rec['charge_error_pct_old']}")
        P(f"        new: SO4={rec['new']['SO4']}  alk(as CaCO3)="
          f"{rec['alkalinity_new_as_CaCO3']}  电荷误差={rec['charge_error_pct_new']}")
    rep["figshare_recomputed"] = fs

    # ---------------- 2. LADWP ----------------
    P("\n[2] LADWP AWPF: 项目标注 missing='Mg' —— 核对源文件是否真的没有 Mg")
    lp = EV / "ladwp_gwr_2012" / "AWPF_RO_product_normalized.csv"
    ldf = pd.read_csv(lp)
    P("    列: " + str(list(ldf.columns)))
    P(ldf.to_string(index=False))
    metrics = [str(m).lower() for m in ldf.get("metric", [])]
    mg_rows = [r for r in ldf.to_dict("records")
               if "magnes" in str(r.get("metric", "")).lower()
               or re.search(r"\bmg\b", str(r.get("metric", "")).lower())]
    rep["ladwp_mg_rows"] = mg_rows
    P(f"    含 'magnes' 的行: {mg_rows if mg_rows else '无'}")
    rep["ladwp_has_magnesium"] = bool(mg_rows)

    # ---------------- 3. IEUA 温度 ----------------
    P("\n[3] IEUA RP-1: 项目样本表没有 temperature 列 —— 核对源文件")
    ip = EV / "ieua_recycled_water_reports" / "RP1_2025_normalized.csv"
    idf = pd.read_csv(ip)
    P("    指标: " + ", ".join(idf["metric"].astype(str)))
    rep["ieua_metrics"] = idf["metric"].astype(str).tolist()
    rep["ieua_has_temperature"] = bool(
        idf["metric"].astype(str).str.lower().str.contains("temp").any())
    rep["ieua_has_phosphate"] = bool(
        idf["metric"].astype(str).str.lower().str.contains("phos").any())
    P(f"    含温度: {rep['ieua_has_temperature']}   含磷酸盐: {rep['ieua_has_phosphate']}")

    # ---------------- 4. 用修正后的 Figshare RW 重跑 PHREEQC ----------------
    P("\n[4] 用修正后的 Figshare RW 重跑 PHREEQC（原报告因'缺 SO4/碱度'直接判为不可跑）")
    rw = fs[0]
    if rw["charge_error_pct_new"] is not None and rw["charge_error_pct_new"] < 10:
        comp = {
            "Ca": rw["new"]["Ca"], "Mg": rw["new"]["Mg"], "Na": rw["new"]["Na"],
            "chloride": rw["new"]["Cl"], "SO4": rw["new"]["SO4"],
            "alkalinity": rw["alkalinity_new_as_CaCO3"], "silica": None,
            "pH": rw["pH"], "TDS": rw["TDS_by_EC_x0.65"],
        }
        res = _phreeqc(comp, label="Figshare RW (corrected)", P=P)
        rep["phreeqc_figshare_rw_corrected"] = res
    else:
        P("    电荷平衡仍不合格, 不跑")
        rep["phreeqc_figshare_rw_corrected"] = None

    # ---------------- 5. 与 T6 CSV 的差异对照 ----------------
    P("\n[5] 与项目 T6_water_chemistry_samples.csv 的 missing 列对照")
    t6 = pd.read_csv(HERE.parent / "A4_水化学参数域" / "T6_water_chemistry_samples.csv")
    diffs = []
    for _, r in t6.iterrows():
        src = str(r["source"])
        if src.startswith("Figshare"):
            lab = "RW" if " RW " in src else "BW"
            rec = next((x for x in fs if str(x["label"]).startswith(lab)), None)
            if rec is None:
                P(f"    [warn] 未匹配到 {lab}"); continue
            claimed = str(r["missing"])
            real = []
            if not np.isfinite(rec["new"]["SO4"]):
                real.append("SO4")
            if not np.isfinite(rec["alkalinity_new_as_CaCO3"]):
                real.append("alkalinity")
            real.append("silica")   # 源表确实没有 Si 列（列头无 Si/SiO2）
            diffs.append({"source": src, "claimed_missing_in_T6": claimed,
                          "actually_missing_in_source": ",".join(real),
                          "extraction_bug_lost": [k for k in ("SO4", "alkalinity")
                                                  if k in claimed and k not in real]})
            P(f"    {lab}: T6 声称缺 [{claimed}]  |  源表实际缺 [{','.join(real)}]")
            P(f"        → 提取 bug 丢失了: "
              f"{[k for k in ('SO4','alkalinity') if k in claimed and k not in real]}")
    rep["missing_column_discrepancies"] = diffs

    (HERE / "T19b_missing_recheck.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    P(f"\n写出 {HERE/'T19b_missing_recheck.json'}")
    logf.close()
    return 0


def _r(v):
    return None if (v is None or not np.isfinite(v)) else round(float(v), 3)


def _phreeqc(comp, label, P):
    try:
        from phreeqpython import PhreeqPython
    except Exception as e:
        return {"ok": False, "error": str(e)}
    buf = io.StringIO()
    PHASES = ("Calcite", "Aragonite", "Dolomite", "Gypsum", "Anhydrite",
              "SiO2(a)", "Hydroxyapatite", "Struvite", "Halite", "Nahcolite", "Trona")
    try:
        with redirect_stdout(buf):
            pp = PhreeqPython(database="vitens.dat")
    except Exception as e:
        return {"ok": False, "error": f"init: {e}"}

    def card(mult, T):
        d = {"-units": "mg/L", "-temp": str(T), "pH": f"{comp['pH']:.3f}"}
        m = {"Ca": "Ca", "Mg": "Mg", "Na": "Na", "chloride": "Cl"}
        for k, kk in m.items():
            d[kk] = f"{comp[k]*mult:.5f}"
        d["S(6)"] = f"{comp['SO4']*mult:.5f} as SO4"
        d["Alkalinity"] = f"{comp['alkalinity']*mult:.5f} as CaCO3"
        return d

    out = {"ok": True, "label": label, "database": "vitens.dat"}
    for T in (25.0, 35.0):
        def sis(mult):
            with redirect_stdout(buf):
                s = pp.add_solution(card(mult, T))
                return {ph: (float(s.phases[ph]) if (ph in s.phases and s.phases[ph] is not None
                                                     and np.isfinite(float(s.phases[ph])))
                             else float("nan")) for ph in PHASES}
        s1 = sis(1.0)
        out[f"SI_at_1x_T{int(T)}"] = {k: _r(v) for k, v in s1.items()}

        def safe(mult):
            d = sis(mult)
            for k in ("Calcite", "Dolomite", "Gypsum", "Anhydrite", "SiO2(a)"):
                v = d.get(k, float("nan"))
                if np.isfinite(v) and v > 0:
                    return False, k
            return True, None

        ok1, who1 = safe(1.0)
        if not ok1:
            out[f"CoC_safe_T{int(T)}"] = 0.0
            out[f"limiting_T{int(T)}"] = f"already_supersat:{who1}"
        else:
            lo, hi = 1.0, 200.0
            if safe(hi)[0]:
                out[f"CoC_safe_T{int(T)}"] = 200.0
                out[f"limiting_T{int(T)}"] = "none_below_upper"
            else:
                for _ in range(45):
                    mid = 0.5 * (lo + hi)
                    if safe(mid)[0]:
                        lo = mid
                    else:
                        hi = mid
                d = sis(lo)
                fin = {k: v for k, v in d.items() if np.isfinite(v)}
                who = max(fin, key=fin.get) if fin else "n/a"
                out[f"CoC_safe_T{int(T)}"] = round(lo, 4)
                out[f"limiting_T{int(T)}"] = who
                out[f"SI_at_limit_T{int(T)}"] = {k: _r(v) for k, v in fin.items()}
    P(f"    [{label}] " + "  ".join(
        f"T={int(T)}: CoC_safe={out.get(f'CoC_safe_T{int(T)}')} "
        f"({out.get(f'limiting_T{int(T)}')})" for T in (25.0, 35.0)))
    for T in (25.0,):
        si = out.get(f"SI_at_1x_T{int(T)}", {})
        P(f"      SI@1x: " + "  ".join(f"{k}={v}" for k, v in si.items() if v is not None))
    return out


if __name__ == "__main__":
    raise SystemExit(main())
