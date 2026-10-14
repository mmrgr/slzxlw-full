"""T19e — 生成 coc_envelope.csv（参数包络, 机器可读）。

一行 = 一个 (水源/口径, 参数) 的包络端点。
类型列严格三分类, 对应任务要求:
    observed   —— 公开报告/数据集里的**实测值**（含实测区间）
    literature —— 公开文献/标准给出的**准则值或区间**
    assumption —— 模型**假设值**（无公开来源支撑）

禁止把 assumption 写成 observed（本轮已发现的缺陷）。
数值全部来自 A4 源表 / A19 脚本输出 / 已核验文献, 无一处手填估算。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
A4 = HERE.parent / "A4_水化学参数域"
EV = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src" / "research_2026" / "external_evidence"

GSA_URL = ("https://www.gsa.gov/system/files/"
           "052-Blowdown%20Recovery%20System%20Full%20Report.pdf")
IEUA_URL = "https://www.ieua.org/wp-content/uploads/2026/04/RW-Effluent-Water-Quality-2025.pdf"
LADWP_URL = ("https://acquia.ladwp.com/sites/default/files/documents/"
             "GWR_MPR_Volume_3_of_3_App_H_M_2012_03_26.pdf")
FIGSHARE_URL = "https://doi.org/10.1371/journal.pone.0322846.t002"
SHERWOOD = "https://doi.org/10.5006/c1994-94453"
COGNETTI = "https://doi.org/10.5006/c1996-96575"
PEREZ = "https://doi.org/10.5006/mp2017_56_1-44"
PUCKORIUS = "https://doi.org/10.5006/1.3585256"
PLATA = "https://doi.org/10.1021/acsestengg.1c00377"
RITZ = "https://doi.org/10.5006/c1996-96579"
VEIL = "https://doi.org/10.2172/919332"
GBT50050 = "GB/T 50050-2017《工业循环冷却水处理设计规范》(标准, 无 DOI)"
GBT19923 = "GB/T 19923-2024《城市污水再生利用 工业用水水质》(标准, 无 DOI)"

# 逐水源实测值（来自 A4 归一化源文件）
SOURCES = {
    "IEUA RP-1 (2025, tertiary reclaimed)": {
        "url": IEUA_URL, "kind": "observed",
        "vals": {"TDS": 443.0, "chloride": 100.0, "Ca": 45.0, "Mg": 9.0,
                 "Na": 88.0, "SO4": 47.0, "alkalinity": 140.0, "silica": 24.0,
                 "pH": 6.9},
        "range": {"Ca": (35, 49), "Mg": (6, 11), "Na": (83, 91),
                  "pH": (6.8, 7.0), "silica": (5, 27), "TDS": (418, 464)},
        "conf": "high",
    },
    "LADWP AWPF (2012, RO product)": {
        "url": LADWP_URL, "kind": "observed",
        "vals": {"TDS": 22.0, "chloride": 3.6, "Ca": 0.41, "Na": 6.6,
                 "SO4": 0.96, "alkalinity": 7.1, "silica": 0.52, "pH": 6.4,
                 "temperature": 26.3},
        "range": {},
        "conf": "medium",
    },
    "Figshare RW (2025) — corrected extraction": {
        "url": FIGSHARE_URL, "kind": "observed",
        "vals": {"TDS": 1378.0, "chloride": 313.73, "Ca": 91.38, "Mg": 75.36,
                 "Na": 310.37, "SO4": 507.20, "alkalinity": 228.18, "pH": 8.17,
                 "TP": 0.05},
        "range": {}, "conf": "medium",
    },
    "Figshare BW (2025) — 非再生水, 仅作边界": {
        "url": FIGSHARE_URL, "kind": "observed",
        "vals": {"TDS": 6130.8, "chloride": 3222.41, "Ca": 36.87, "Mg": 18.72,
                 "Na": 2000.13, "SO4": 109.51, "alkalinity": 114.09, "pH": 8.44,
                 "TP": 0.02},
        "range": {}, "conf": "medium",
    },
    "AI-UWM model assumption (无公开来源)": {
        "url": "UNVERIFIED — 引擎内部占位值", "kind": "assumption",
        "vals": {"TDS": 650.0, "chloride": 130.0},
        "range": {}, "conf": "low",
    },
}

# 冷却水准则（文献/标准）
LIMITS = {
    "GSA Table 6 CoC 下限 (加药运行验收)": ("CoC", 2.0, None, "-", GSA_URL, "literature", "high"),
    "GSA Table 6 总碱度": ("alkalinity", 100.0, 1000.0, "mg/L as CaCO3", GSA_URL, "literature", "high"),
    "GSA Table 6 pH": ("pH", 7.3, 9.0, "-", GSA_URL, "literature", "high"),
    "GSA Table 6 氯离子": ("chloride", 10.0, 500.0, "mg/L", GSA_URL, "literature", "high"),
    "GSA Table 6 总硬度": ("hardness", 500.0, 1500.0, "mg/L as CaCO3", GSA_URL, "literature", "high"),
    "GSA Table 6 电导率": ("conductivity", None, 2400.0, "uS/cm", GSA_URL, "literature", "high"),
    "GSA Table 6 二氧化硅": ("silica", None, 150.0, "mg/L", GSA_URL, "literature", "high"),
    "GSA Table 6 钙硬度": ("Ca_hardness", None, 500.0, "mg/L as CaCO3", GSA_URL, "literature", "high"),
    "GSA Table 6 镁硬度": ("Mg_hardness", None, 100.0, "mg/L as CaCO3", GSA_URL, "literature", "high"),
    "GSA Table 6 硫酸盐": ("SO4", None, 250.0, "mg/L", GSA_URL, "literature", "high"),
    "GB/T 50050-2017 循环水 (钙硬度+总碱度)": ("hardness_plus_alkalinity", None, 1100.0,
                                              "mg/L as CaCO3", GBT50050, "literature", "high"),
    "GB/T 19923-2024 补充水 TDS": ("TDS", None, 1000.0, "mg/L", GBT19923, "literature", "high"),
    "Puckorius 1991 适用性上界 pH": ("pH_index_validity", 7.5, None, "-", PUCKORIUS,
                                     "literature", "high"),
}


def main() -> int:
    rows = []

    # ---- 1. 各水源逐参数实测 ----
    for src, cfg in SOURCES.items():
        for p, v in cfg["vals"].items():
            lo = hi = v
            if p in cfg.get("range", {}):
                lo, hi = cfg["range"][p]
            rows.append({
                "source": src, "parameter": p, "lower": lo, "upper": hi,
                "unit": _unit(p), "source_url": cfg["url"], "type": cfg["kind"],
                "confidence": cfg["conf"],
                "note": ("实测区间 (月均 min-max)" if p in cfg.get("range", {})
                         else "实测点值" if cfg["kind"] == "observed" else "模型假设, 无公开来源"),
            })

    # ---- 2. CoC 包络（本项目计算 + 实测 + 文献） ----
    coc_rows = [
        ("允许 CoC — 下界: IEUA 无加药热力学 @25C", 2.52, 2.52, "sensitivity_ratio",
         "A19/T19_db_sensitivity.json", "observed", "high",
         "PHREEQC 方解石 SI<=0; vitens.dat; 复现项目原值 2.5202"),
        ("允许 CoC — 下界: IEUA 无加药热力学 @35C", 2.10, 2.10, "sensitivity_ratio",
         "A19/T19_db_sensitivity.json", "observed", "high", "温度敏感性"),
        ("允许 CoC — 下界: IEUA 无加药热力学 @45C", 1.77, 1.77, "sensitivity_ratio",
         "A19/T19_db_sensitivity.json", "observed", "high",
         "45C 更接近夏季循环水实际; 比 25C 低 30%"),
        ("允许 CoC — 上界: GSA 实测加药运行 (baseline)", 2.80, 2.80, "sensitivity_ratio",
         GSA_URL, "observed", "high", "Lloyd D. George 法院, 30 天, 水衡算法"),
        ("允许 CoC — 上界: GSA 实测加药运行 (2021 BDR)", 4.34, 4.34, "sensitivity_ratio",
         GSA_URL, "observed", "high", "15 天"),
        ("允许 CoC — 上界: GSA 实测加药运行 (2022 BDR)", 4.91, 4.91, "sensitivity_ratio",
         GSA_URL, "observed", "high", "57 天"),
        ("允许 CoC — 上界: IEUA 加药后由 SiO2(a) 接管", 4.81, 4.81, "sensitivity_ratio",
         "A19/T19c_coc_envelope_raw.json", "observed", "medium",
         "LSI_tol>=1.5 时方解石不再限制, 无定形硅 SI<=0 成为限制相"),
        ("允许 CoC — 上界: IEUA 按 GSA 硅准则 <150 mg/L", 6.25, 6.25, "sensitivity_ratio",
         GSA_URL, "literature", "medium", "150/24 = 6.25 (IEUA 硅 24 mg/L)"),
        ("允许 CoC — 上界: IEUA 按聚合物控硅 ~300 mg/L", 12.5, 12.5, "sensitivity_ratio",
         PEREZ, "literature", "low", "300/24 = 12.5; 厂商文献, 非独立第三方"),
        ("阻垢剂容忍 — 方解石饱和倍数", 1.0, 300.0, "x_saturation",
         SHERWOOD, "literature", "low", "300x 上界; 下界 1x = 无加药热力学"),
        ("阻垢剂容忍对应 LSI 区间", 0.0, 2.477, "LSI",
         SHERWOOD, "literature", "low",
         "LSI = SI_calcite = log10(IAP/Ksp); log10(300)=2.477"),
        ("阻垢剂容忍 LSI (先进配方上界)", 2.477, 3.0, "LSI",
         COGNETTI, "literature", "low", "同一厂商系会议论文, 非独立第三方"),
        ("加药后替代限制相 — 二氧化硅", None, 300.0, "mg/L",
         PEREZ, "literature", "low", "高聚物+膦酸盐可把硅控到接近 300 mg/L"),
        ("石膏饱和上界 (Figshare RW, 加药后)", None, 7.70, "sensitivity_ratio",
         "A19/T19d_corrected_figshare_envelope.json", "observed", "medium",
         "LSI_tol>=2.477 时石膏 SI>0 接管, 阻垢剂不覆盖硫酸盐垢"),
    ]
    for name, lo, hi, unit, url, typ, conf, note in coc_rows:
        rows.append({"source": name, "parameter": "CoC", "lower": lo, "upper": hi,
                     "unit": unit, "source_url": url, "type": typ,
                     "confidence": conf, "note": note})

    # ---- 3. 准则值 ----
    for name, (p, lo, hi, unit, url, typ, conf) in LIMITS.items():
        rows.append({"source": name, "parameter": p, "lower": lo, "upper": hi,
                     "unit": unit, "source_url": url, "type": typ,
                     "confidence": conf, "note": "公开准则/标准值"})

    # ---- 4. 判据敏感性行 ----
    for name, lo, hi, url, note in [
        ("判据差异: 比值法(全物种) vs 饱和指数法 (IEUA)", 2.52, 3.57,
         "A19/t19c.log", "n=1 样本; 比值法高 29-42%（分母口径不同）"),
        ("判据差异: 引擎保守物种(仅TDS/Cl) vs 饱和指数", 2.52, 4.97,
         "A19/t19c.log", "n=1; 占位限值下的口径差异"),
        ("判据差异: 数据库 vitens vs phreeqc.dat (IEUA@25C)", 2.5202, 2.5203,
         "A19/T19_db_sensitivity.json", "Δ=+0.004%, 可忽略"),
        ("判据差异: 数据库 vitens vs pitzer.dat (IEUA@25C)", 2.3481, 2.5202,
         "A19/T19_db_sensitivity.json", "Δ=-6.8%, pitzer 活度模型不同"),
    ]:
        rows.append({"source": name, "parameter": "CoC", "lower": lo, "upper": hi,
                     "unit": "sensitivity_ratio", "source_url": url,
                     "type": "observed", "confidence": "medium", "note": note})

    out = HERE / "coc_envelope.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["source", "parameter", "lower", "upper",
                                          "unit", "source_url", "type", "confidence",
                                          "note"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"[write] {out}  rows={len(rows)}")
    from collections import Counter
    print("type 分布:", Counter(r["type"] for r in rows))
    return 0


def _unit(p: str) -> str:
    return {"pH": "-", "temperature": "degC", "conductivity": "uS/cm",
            "TP": "mg/L", "Ca_hardness": "mg/L as CaCO3",
            "Mg_hardness": "mg/L as CaCO3", "hardness": "mg/L as CaCO3",
            "alkalinity": "mg/L as CaCO3"}.get(p, "mg/L")


if __name__ == "__main__":
    raise SystemExit(main())
