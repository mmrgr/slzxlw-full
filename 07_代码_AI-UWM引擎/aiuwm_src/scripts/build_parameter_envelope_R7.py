"""R7 参数包络 + 文献锚点定量对照。

产出两份表：
  1) parameter_envelope_R7.csv      —— 模型输入参数 vs 文献观测包络（可否解释、落在区间何处）
  2) literature_anchor_check_R7.csv —— 模型**衍生**比值 vs 文献报道值（定量偏差）

设计原则：锚点必须来自已精读的文献原文（本地 06_文献库/lw 的 12 篇译稿及其所引手册），
每一行的"锚点来源"都要能指回具体论文与章节/表格，不允许凭记忆填写。
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "examples" / "cawcc_r2"
sys.path.insert(0, str(ROOT / "src"))

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

PROBE = ROOT / "validation_artifacts" / "_probe_ts"
OUT = ROOT / "validation_artifacts" / "r2"
CAP_MW = 1000.0


# --------------------------------------------------------------------------
# 1. 文献锚点（全部来自本轮精读的 12 篇本地译稿及其明确引用的手册/数据库）
# --------------------------------------------------------------------------
# 每条记录： (锚点编号, 锚点名, 观测下界, 观测上界, 单位, 典型值, 出处)
ANCHORS = [
    # --- AI / 数据中心侧 ---
    ("A01", "厂外电力水强度 offsite grid water intensity", 1.80, 4.52, "L/kWh", 1.80,
     "Green Grid White Paper #35 美国平均 EWIF=1.8；LBNL 2024 间接~4.52（见文献基准矩阵 R6 §III）"),
    ("A22", "间接水占数据中心总水足迹份额", 0.548, 0.548, "—", 0.548,
     "由 LBNL 2024 反演：美国数据中心**直接**取水约 660 亿升、**间接**（电厂侧）约 800 亿升，"
     "→ 间接/(直接+间接) = 800/1460 = 0.548"),
    ("A02", "数据中心冷却占总用电比例", 0.30, 0.30, "—", 0.30,
     "Wang et al. ESE 2026 §1：现代数据中心约 30% 电力用于冷却"),
    ("A03", "基准情景淡水中蒸发份额", 0.80, 0.80, "—", 0.80,
     "Wang et al. ESE 2026 §3.2：1 m3 淡水中 80% 蒸发、20% 变废水"),
    ("A04", "基准情景淡水中排污水份额", 0.20, 0.20, "—", 0.20,
     "同上（与 A03 互补，飘水忽略）"),
    ("A05", "每吨淡水取水碳强度", 1.11, 1.21, "kgCO2e/t", 1.14,
     "Wang et al. ESE 2026 §3.2：1.14 (1.11–1.21) kg CO2 eq 每吨淡水"),
    # --- 城市水系统侧 ---
    ("A06", "生活用水回流系数", 0.85, 0.95, "—", 0.90,
     "Metcalf & Eddy (2003) 经 WaterMet2 §S2.5：生活 90%，非生活 85–95%"),
    ("A06b", "工业用水回流系数", 0.85, 0.95, "—", 0.90,
     "Metcalf & Eddy (2003) 经 WaterMet2 §S2.5：非生活 85–95%"),
    ("A06c", "灌溉回流系数（ET 消耗型）", 0.00, 0.05, "—", 0.00,
     "定义性约束：灌溉水量经蒸腾蒸发消耗，回流近零；墨西哥案 unique 灌溉 quota If=5 L/m2"),
    ("A07", "配水干管漏损率", 0.025, 0.54, "—", 0.108,
     "Paju 5.6%、韩国均值 10.8%、北欧案 22%、巴西案 54%、墨西哥案 40–50%、首尔 2.5%；"
     "注意：仅适用于配水干管 DM，不适用于输水干管/原水渠"),
    ("A08", "污水厂 GHG 占 UWS 总 GHG 份额", 0.77, 1.00, "—", 0.77,
     "WaterMet2 北欧案 §S4：WWTW >77% GHG、>88% 酸化"),
    ("A09", "污水厂酸化占 UWS 总酸化份额", 0.88, 1.00, "—", 0.88,
     "WaterMet2 北欧案 §S4 Table 8"),
    ("A10", "污水厂 BOD 去除率", 0.87, 0.91, "—", 0.91,
     "北京 ABM-SD Table 5 取 87%；墨西哥 SITRATA 2017 为 91%"),
    ("A11", "污水厂单位电耗", 0.30, 0.462, "kWh/m3", 0.462,
     "WaterMet2 北欧案 WWTW 电耗 0.462 kWh/m3；墨西哥案处理能耗另有值"),
    ("A12", "电网排放因子", 0.35, 0.458, "kgCO2e/kWh", 0.458,
     "SEMARNAT 2016 墨西哥电网 0.458 kg CO2/kWh（Behzadian WEP nexus §KPI）"),
    ("A13", "折现率（实际）", 0.03, 0.03, "—", 0.03,
     "Wang et al. ESE 2026 §2.3 取 3% 实际折现率；WaterMet2 §S2.4.8 支持折现"),
    ("A14", "人均生活用水", 90.0, 263.0, "L/cap/d", 180.0,
     "墨西哥 90–180；北欧案 180；开普敦 197–263（含水务口径）；Paju 777 m3/cap/a 含工业"),
    ("A15", "再生水/内部化占供水比", 0.05, 0.446, "—", 0.246,
     "南非 2010 回用<5%（Saldías 2016，经开普敦论文引）；Paju 内部化 24.6%、S5-2 达 44.5%"),
    ("A16", "GWP100 CH4", 25.0, 28.0, "—", 25.0,
     "IPCC 2006 GWP100 CH4=25（WaterMet2）；IPCC 2014 CH4=28（Behzadian WEP）"),
    ("A17", "GWP100 N2O", 265.0, 298.0, "—", 298.0,
     "IPCC 2006 N2O=298（WaterMet2）；IPCC 2014 N2O=265（Behzadian WEP）"),
    ("A18", "数据中心 Site WUE", 0.07, 1.28, "L/kWh", 0.58,
     "EU 数据中心能效方案 Annex I（2026-09-21）：A 级 ≤0.10、G 级 >1.00，"
     "2024 年欧盟均值 0.58，成员国区间 0.07–1.28"),
]


def _load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def ensure_probe(domain: str, cap_mw: float | None = None) -> Path:
    """跑（或复用）单个域签订点在指定 IT 容量下的日序列 dumps。"""
    cap = CAP_MW if cap_mw is None else cap_mw
    out = PROBE / domain / f"{int(cap)}MW"
    dc_csv = out / "data_center_daily.csv"
    stamp = out / "_config_hash.txt"
    fingerprint = _config_hash(R2 / domain / "project.json")
    # 只有当**现有 dump 的配置指纹与当前 project.json 一致**时才复用。
    # 此前这里只判 `dc_csv.exists()`，导致修改了参数后仍沿用旧 dump，
    # 锚点判定会静默失真（本轮 EWIF 与 WWTW 排放修复即触发过这个问题）。
    if dc_csv.exists() and stamp.exists():
        try:
            if stamp.read_text(encoding="utf-8").strip() == fingerprint:
                return out
        except OSError:
            pass
    project = _load_json(R2 / domain / "project.json")
    ts = pd.read_csv(R2 / domain / "timeseries.csv")
    trial = copy.deepcopy(project)
    for cid, comp in trial["components"].items():
        if comp.get("kind") == "data_center":
            trial["components"][cid]["installed_it_capacity_mw"] = cap
            trial["components"][cid].pop("capacity_schedule", None)
    result = FullAIUWMModel(trial, ts).run()
    result.write(out)
    stamp.write_text(fingerprint, encoding="utf-8")
    return out


def _config_hash(path: Path) -> str:
    """对 project.json 取稳定指纹，用于判断既有 dump 是否已过期。"""
    raw = path.read_text(encoding="utf-8")
    return hashlib.sha256(json.dumps(json.loads(raw), sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def derive_metrics(domain: str, out_dir: Path, base_dir: Path | None = None) -> dict:
    """从日序列计算可与文献锚点对照的**衍生**量。

    `base_dir` 为 **0 MW 无 AI 基线**的 dump。A08/A09（WWTW 占 UWS 份额）
    必须在那里计算——1000 MW 时 AI_DC1 自身排放约占总量的 98.6%，
    在该口径下算出的 WWTW 份额（本轮曾得到 0.0069）毫无意义。
    """
    if base_dir is None:
        base_dir = out_dir
    dc = pd.read_csv(out_dir / "data_center_daily.csv")
    m = {}
    # --- 冷却塔水分分配（A03/A04）---
    evap = dc["evaporation_ml"].sum()
    blow = dc["blowdown_ml"].sum()
    drift = dc["drift_ml"].sum()
    gross = dc["gross_makeup_ml"].sum()
    tot = evap + blow + drift
    if tot > 0:
        m["补水中蒸发份额"] = evap / tot
        m["补水中排污份额"] = blow / tot
        m["补水中飘水份额"] = drift / tot
    if gross > 0:
        m["补给/毛补水比"] = tot / gross
    # --- 厂外电力隐含水（A01）---
    fac_kwh = dc["facility_energy_mwh"].sum() * 1.0e3
    off_ml = dc["offsite_electricity_water_ml"].sum()
    if fac_kwh > 0:
        m["厂外电力水强度_L_per_kWh"] = off_ml * 1.0e6 / fac_kwh
    # --- 总水足迹结构 ---
    direct = dc["consumption_ml"].sum()
    total = dc["total_water_footprint_ml"].sum()
    if total > 0:
        m["直接水占总足迹比"] = direct / total
        m["间接水占总足迹比"] = off_ml / total
    # --- WUE ---
    m["平均WUE_L_per_kWh"] = dc["wue_l_kwh"].mean()
    # --- 冷却占数据中心用电比例（A02）---
    it_kwh = dc["it_energy_mwh"].sum() * 1.0e3
    if fac_kwh > 0:
        m["有效PUE"] = fac_kwh / it_kwh
        m["冷却占设施用电比"] = (fac_kwh - it_kwh) / fac_kwh
    # --- 系统级：WWTW 占"已造成"GHG / 酸化份额（A08/A09）---
    comp = pd.read_csv(base_dir / "component_annual.csv")
    ghg = comp.groupby("component_id")["ghg_caused_kg_co2e"].sum()
    aci = comp.groupby("component_id")["acidification_caused_kg_so2e"].sum()
    if ghg.sum() > 0:
        m["WWTW占已造成GHG比"] = ghg.get("WWTW1", 0.0) / ghg.sum()
    if aci.sum() > 0:
        m["WWTW占已造成酸化比"] = aci.get("WWTW1", 0.0) / aci.sum()
    return m


def param_rows() -> list[dict]:
    """模型输入参数 vs 文献观测包络。"""
    spec = [
        # (域签, 取值路径, 显示名, 锚点编号集合, 是否需乘 1e6->单位换算标记)
        ("offsite_electricity_water_intensity_l_kwh", ["components", "AI_DC1"], "A01"),
        ("cycles_of_concentration", ["components", "AI_DC1", "cooling"], "—"),
        ("drift_fraction", ["components", "AI_DC1", "cooling"], "—"),
        ("internal_recovery_fraction", ["components", "AI_DC1", "cooling"], "—"),
        ("base_pue", ["components", "AI_DC1"], "—"),
        ("central_reuse_fraction", ["components", "WWTW1"], "A15"),
        ("leakage_fraction", ["components", "DM1"], "A07"),
        ("leakage_fraction", ["components", "SC1"], "—"),
        ("leakage_fraction", ["components", "TM1"], "—"),
        ("loss_fraction", ["components", "WTW1"], "—"),
        ("electricity_kwh_m3", ["components", "WTW1"], "—"),
        ("electricity_kwh_m3", ["components", "WWTW1"], "A11"),
        ("electricity_kwh_m3", ["components", "DM1"], "—"),
        ("ghg_kg_co2e_unit", ["energy_sources", "electricity"], "A12"),
        ("discount_rate", ["finance"], "A13"),
        ("electricity_kwh_per_capita_year", ["city_context"], "—"),
    ]
    rows = []
    for domain in ("ha", "co"):
        proj = _load_json(R2 / domain / "project.json")
        for leaf, path, anchor in spec:
            node = proj
            ok = True
            for k in path:
                if isinstance(node, dict) and k in node:
                    node = node[k]
                else:
                    ok = False
                    break
            if not ok or not isinstance(node, dict) or leaf not in node:
                continue
            key = ".".join(path + [leaf])
            rows.append({
                "域签": domain.upper(),
                "参数路径": key,
                "模型取值": node[leaf],
                "锚点编号": anchor,
            })
        # 生活需水 / 回流系数 / 去除率在 local_areas 与 components 内
        la = proj["local_areas"]["LA1"]
        for prof in la["demand_profiles"]:
            rows.append({
                "域签": domain.upper(),
                "参数路径": f"local_areas.LA1.demand_profiles.{prof['name']}.base_value",
                "模型取值": prof["base_value"],
                "锚点编号": "A14" if prof["name"] == "domestic" else "—",
            })
            rows.append({
                "域签": domain.upper(),
                "参数路径": f"local_areas.LA1.demand_profiles.{prof['name']}.return_fraction",
                "模型取值": prof["return_fraction"],
                "锚点编号": {"domestic": "A06", "industrial": "A06b",
                            "irrigation": "A06c"}.get(prof["name"], "—"),
            })
        rem = proj["components"]["WWTW1"]["pollutant_removal_fraction"]
        for k, v in rem.items():
            rows.append({
                "域签": domain.upper(),
                "参数路径": f"components.WWTW1.pollutant_removal_fraction.{k}",
                "模型取值": v,
                "锚点编号": "A10" if k == "BOD" else "—",
            })
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    anchor_by_id = {a[0]: a for a in ANCHORS}

    # ---------- 表 1：参数包络 ----------
    rows = param_rows()
    for r in rows:
        aid = r["锚点编号"]
        if aid == "—" or aid not in anchor_by_id:
            r.update({"锚点名": "—", "观测下界": None, "观测上界": None,
                      "单位": "—", "典型值": None, "是否落在包络内": "无锚点",
                      "偏离说明": "", "锚点来源": "—"})
            continue
        _, name, lo, hi, unit, typ, src = anchor_by_id[aid]
        val = r["模型取值"]
        tol = 1e-9 * max(1.0, abs(lo), abs(hi))
        inside = (lo - tol) <= val <= (hi + tol)
        if inside:
            note = f"落在区间内，相对典型值 {typ:g} 偏{'高' if val > typ else '低'} {abs(val - typ) / typ * 100:.1f}%" if typ else "落在区间内"
        else:
            note = f"越界：低于下界 {lo - val:.4g}" if val < lo else f"越界：高于上界 {val - hi:.4g}"
        r.update({"锚点名": name, "观测下界": lo, "观测上界": hi, "单位": unit,
                  "典型值": typ, "是否落在包络内": (
                      "边界命中" if inside and (abs(val - lo) <= tol or abs(val - hi) <= tol)
                      else "是" if inside else "否"
                  ),
                  "偏离说明": note, "锚点来源": src})
    env = pd.DataFrame(rows)
    env = env[["域签", "参数路径", "模型取值", "锚点编号", "锚点名", "观测下界", "观测上界",
               "单位", "典型值", "是否落在包络内", "偏离说明", "锚点来源"]]
    env.to_csv(OUT / "parameter_envelope_R7.csv", index=False, encoding="utf-8-sig")

    # ---------- 表 2：衍生量 vs 锚点 ----------
    checks = [
        # (衍生指标名, 锚点编号, 计算方式标签)
        ("补水中蒸发份额", "A03", "evaporation /(evaporation+blowdown+drift)"),
        ("补水中排污份额", "A04", "blowdown /(evaporation+blowdown+drift)"),
        ("补水中飘水份额", "A04", "drift /(evaporation+blowdown+drift)，Wang 设为可忽略"),
        ("厂外电力水强度_L_per_kWh", "A01", "sum(offsite_electricity_water_ml)*1e6 / sum(facility_energy_mwh)*1e3"),
        # 不能挂 A01：那是 L/kWh，与无量纲占比不可比（此前挂 A01 得到 −69% 假警报）。
        ("间接水占总足迹比", "A22", "offsite / total_water_footprint；与 LBNL 2024 反演 0.548 仅作量级交叉检查，不是率定或外部验证"),
        ("平均WUE_L_per_kWh", "A18", "mean(wue_l_kwh)，对照 EU Annex I 成员国区间"),
        ("WWTW占已造成GHG比", "A08", "component_annual 按组件汇总 ghg_caused_kg_co2e 后取 WWTW1 占比"),
        ("WWTW占已造成酸化比", "A09", "component_annual 按组件汇总 acidification_caused_kg_so2e 后取 WWTW1 占比"),
        ("冷却占设施用电比", "A02", "(facility_energy - it_energy) / facility_energy（对照 ~30% 用于冷却）"),
    ]
    out_rows = []
    for domain, label in (("ha", "D-HA"), ("co", "D-CO")):
        try:
            d = ensure_probe(domain)                       # 带 AI 的场景（1000 MW）
            b = ensure_probe(domain, cap_mw=0.0)           # 无 AI 基线（0 MW）
        except Exception as exc:  # noqa: BLE001
            out_rows.append({"域签": label, "衍生指标": "（全部）", "模型计算值": None,
                             "锚点编号": "—", "锚点名": "probe 失败", "文献值": None,
                             "相对偏差": None, "判定": "无法计算",
                             "说明": f"{exc}"})
            continue
        m = derive_metrics(domain, d, base_dir=b)
        for metric, aid, how in checks:
            aid_inject = aid
            # 飘水份额的锚点为"可忽略"，用下界 0 上界 0 无法表达，单独处理
            _, name, lo, hi, unit, typ, src = anchor_by_id[aid_inject]
            val = m.get(metric)
            if val is None:
                continue
            if metric == "补水中飘水份额":
                lo, hi, typ = 0.0, 0.005, 0.0
                name = "飘水份额（Wang 视为可忽略）"
            dev = None if typ in (None, 0) else (val - typ) / typ * 100.0
            tol = 0.01 if aid_inject == "A22" else 1e-9 * max(1.0, abs(lo), abs(hi))
            if aid_inject == "A22" and abs(val - typ) / max(abs(typ), 1e-12) <= tol:
                judge = "量级相近（交叉检查；非率定/验证）"
            elif (lo - tol) <= val <= (hi + tol):
                judge = "边界命中" if abs(val - lo) <= tol or abs(val - hi) <= tol else "符合"
            else:
                judge = "偏离"
            out_rows.append({
                "域签": label, "衍生指标": metric, "模型计算值": round(val, 6),
                "锚点编号": aid_inject, "锚点名": name,
                "文献值": typ, "相对偏差百分比": None if dev is None else round(dev, 2),
                "判定": judge, "说明": how + "；来源：" + src,
            })
        out_rows.append({
            "域签": label, "衍生指标": "有效PUE", "模型计算值": round(m["有效PUE"], 6),
            "锚点编号": "—", "锚点名": "PUE（仅登记）", "文献值": 1.2,
            "相对偏差百分比": round((m["有效PUE"] - 1.2) / 1.2 * 100, 2),
            "判定": "参考", "说明": "base_pue=1.2，动态温度修正后的年度有效值",
        })
    chk = pd.DataFrame(out_rows)
    chk.to_csv(OUT / "literature_anchor_check_R7.csv", index=False, encoding="utf-8-sig")

    print(f"[OK] {OUT / 'parameter_envelope_R7.csv'}  rows={len(env)}")
    print(f"[OK] {OUT / 'literature_anchor_check_R7.csv'}  rows={len(chk)}")
    print()
    print("=== 衍生量 vs 文献锚点 ===")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(chk.to_string(index=False))
    print()
    bad = env[(env["是否落在包络内"] == "否")]
    print(f"=== 参数越界 {len(bad)} 项 ===")
    if len(bad):
        with pd.option_context("display.width", 250, "display.max_columns", 20):
            print(bad[["域签", "参数路径", "模型取值", "观测下界", "观测上界", "偏离说明"]].to_string(index=False))


if __name__ == "__main__":
    main()
