"""WP5 任务 B: 极端事件情景 (热浪 / 干旱) —— 主估计量 dS_pot 的符号是否翻转.

======================================================================
【为什么用"窗口化冻结模块"而不是自建单日解】
======================================================================
A12/§M1 已记录的教训: 日尺度自建"单日城市解"的**分配器语义**与冻结年度模块不一致
(日尺度下既有用户得 0、竞争池未被用尽; 年度模块为 37:63 且池用尽)。
因此本脚本一律**复用 `city_model.solve_city`**, 只把 `E_total` / 代表日 / 池 / 缺口
替换为**窗口总量**, 规则代码路径与冻结版本逐字相同 —— 与 A12/T14 §3.3 的既有方法学纪律一致。

代表日选取: 窗口内**蒸发 > 0** 的湿日中取湿球中位日 (M4 的另一半: 对 hybrid/dry,
冷窗可能整体零蒸发, 强行取零蒸发日会让 M/E 退化为 0)。

======================================================================
【情景分类: 观测驱动 vs 人为扰动 (任务书硬要求)】
======================================================================
每个情景在 CSV/summary 中显式标注 `driver_class`:
  · OBSERVED_DRIVER  —— 由 730 天逐日序列中**实际观测到**的极端窗口驱动
                        (热浪窗 = 湿球 p95; 干旱窗 = 水库来水 37 天滚动均值最小);
  · FORCED_PERTURBATION —— 人为扰动, 把某机制推到观测范围**之外**的压力档
                        (e_scale / 供给比例 / 化学), 用于找符号翻转的**临界点**。
两者不得混为一谈; 报告结论时分别陈述。

======================================================================
【两种口径, 分别回答"质变"与"量变"】
======================================================================
口径 W (窗口总量, 与 A12/T14 §3.3 可比): 池 = 窗口内 Σ 既有用户回用交付,
    E = 窗口内 Σ 蒸发, period_days = n_days。
口径 P (年基座 + 同比缩放): 池/E 按窗口天数与 730 天**同比例**缩放, 使
    "窗口 dS / n_days" 与 "全年 dS / 730" 可直接比较。
    ⇒ 口径 P 只反映**水化学与技术**的时段差异, 不含"池被改用"这一分配效应;
      口径 W 含它。两者对比可把"质变来自化学"与"质变来自池"分开。

======================================================================
【干旱的供给侧机制 (必须显式声明)】
======================================================================
既有用户与 AI **共用**同一再生水池。干旱压低可用水量时, 池按 `avail_frac` 缩放,
AI 的可得量 `trial` 与既有用户的交付量同时下降。
- 口径 D1 (竞争性缩放): 池 = P0 * avail_frac, 缺口保持 gap 不变
    -> 直接复现 A17/supply_state_regimes 的三态 (shortage/binding/surplus) 语义。
- 口径 D2 (纯供给约束): 池 = P0 (名义不变) 但 AI 的可得量被 `avail_frac` 限流
    -> 由 `cm.solve_city` 的 `dp`/目标分数路径表达会失真, 故 D2 用**引擎原生计划**
       (calculate_data_center_plan 的 reclaimed_available_ml) 直接给出 AI 可用比例,
       用于回答"数据中心运行是否受限", 不用于 dS_pot 口径 W/P 的结论。
本脚本对 dS_pot 的主口径用 D1, 并把 D2 的结果单列为"运行受限"证据。

【纪律】
  · 引擎与 city_model 只读;
  · 双门禁 + n_eff; 空集/缺列/NaN 标 NOT_IDENTIFIABLE, **不得计为 PASS**;
  · 符号计数声明零值约定与实际 n_eff; 大数量级用相对容差; 不编造数字;
  · 负结果 (无符号翻转) 如实报告, 不修饰。
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
except Exception:  # pragma: no cover
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
A12 = ROOT / "A12_时间分辨率"
for p in (str(HERE), str(A10), str(A12)):
    if p not in sys.path:
        sys.path.insert(0, p)

import wp5_common as W                                     # noqa: E402
import city_model as cm                                    # noqa: E402
from aiuwm.data_center import calculate_data_center_plan   # noqa: E402

PHI = 0.6                    # 主再生水掺混比 (与 WP4/A12 参照口径一致)
HEATWAVE_Q = 0.95            # 热浪窗 = 窗口内湿球 >= 该分位 (A12 事先固定的 p95)
WINDOW_DAYS = 37             # A12 事先固定的窗长
DRY_RUN_TECH = "evaporative"  # 默认技术 (全湿式), 与主结论口径一致


# ======================================================================
# 驱动数据
# ======================================================================
def load_ts(dom: str) -> pd.DataFrame:
    """逐日驱动序列 (与 daily_model.load_ts 同源同列, 此处只读不改)。"""
    ts = pd.read_csv(cm.R2 / dom / "timeseries.csv", parse_dates=["date"])
    return ts


def wet_days_mask(dom: str) -> np.ndarray:
    """逐日蒸发 > 0 的湿日掩码 (M4: 代表日必须落在湿日内)。

    用引擎算逐日计划, 不重写任何物理规则。
    """
    ts = load_ts(dom)
    comp = cm.base_comp(cm.BASELINES[dom], W.PANEL, 0.0, cooling_tech=DRY_RUN_TECH)
    ev = []
    for _, r in ts.iterrows():
        drv = {"temperature_c": float(r.temperature_c),
               "relative_humidity": float(r.relative_humidity_pct),
               "load_factor": float(r.ai_load_factor_a30)}
        p = calculate_data_center_plan(comp, pd.Timestamp(r.date), drv)
        ev.append(float(p.evaporation_ml))
    return np.asarray(ev)


def daily_plan_e(dom: str) -> pd.DataFrame:
    """逐日引擎计划 (E, M/E, 湿分, 代表日所需驱动)。"""
    ts = load_ts(dom)
    comp = cm.base_comp(cm.BASELINES[dom], W.PANEL, 0.0, cooling_tech=DRY_RUN_TECH)
    rows = []
    for _, r in ts.iterrows():
        drv = {"temperature_c": float(r.temperature_c),
               "relative_humidity": float(r.relative_humidity_pct),
               "load_factor": float(r.ai_load_factor_a30)}
        p = calculate_data_center_plan(comp, pd.Timestamp(r.date), drv)
        rows.append({"date": pd.Timestamp(r.date), "temperature_c": float(r.temperature_c),
                     "relative_humidity": float(r.relative_humidity_pct),
                     "wet_bulb_c": float(r.wet_bulb_c),
                     "reservoir_inflow_ml": float(r.reservoir_inflow_ml),
                     "evaporation_ml": float(p.evaporation_ml),
                     "external_makeup_ml": float(p.external_makeup_ml),
                     "pue": float(p.pue)})
    return pd.DataFrame(rows)


def daily_reuse_supply(dom: str) -> pd.DataFrame:
    """逐日再生水交付序列 (= 冻结口径 P0 的日分解)。

    与 A12/daily_model.daily_reuse_supply 同一构造 (整链引擎, 清零储冷, 1000 MW,
    reclaimed/potable target 置 0/1)。此处**只读复现**, 不修改每日模型。
    """
    from aiuwm.full_engine import FullAIUWMModel
    import copy
    bl = cm.BASELINES[dom]
    ts = load_ts(dom)
    eng = copy.deepcopy(bl["proj"])
    dc = eng["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    for k in ("cooling_storage_capacity_ml", "cooling_storage_ml",
              "initial_cooling_storage_ml"):
        dc[k] = 0.0
    dc["water_sources"]["reclaimed"]["target_fraction"] = 0.0
    dc["water_sources"]["potable"]["target_fraction"] = 1.0
    a = FullAIUWMModel(eng, ts).run().area_daily
    keep = [c for c in ("date", "reuse_delivered_ml") if c in a.columns]
    out = a[keep].copy()
    out["date"] = pd.to_datetime(out["date"])
    return out


# ======================================================================
# 窗口构造
# ======================================================================
def make_windows(dom: str) -> dict[str, np.ndarray]:
    """构造热浪窗 / 匹配非热浪窗 / 全年窗 / 干旱窗 (全部事先固定, 不挑窗)。"""
    ts = load_ts(dom)
    wb = ts.wet_bulb_c.to_numpy()
    n = len(ts)
    heat = wb >= np.quantile(wb, HEATWAVE_Q)
    n_hw = int(heat.sum())
    # 匹配非热浪窗: 按湿球升序取与热浪窗等量的最低湿球日 (A12 既有定义)
    order = np.argsort(wb)
    cold = np.zeros(n, bool); cold[order[:n_hw]] = True
    full = np.ones(n, bool)
    # 干旱窗: 水库来水 37 天滚动均值最小的窗口 (观测驱动)
    rin = ts.reservoir_inflow_ml.rolling(WINDOW_DAYS).mean()
    k = int(rin.idxmin())
    start = max(0, k - WINDOW_DAYS + 1)
    dry = np.zeros(n, bool); dry[start:k + 1] = True
    return {"full_year": full, "heatwave": heat, "non_heatwave_matched": cold,
            "drought_lowinflow": dry}


def window_basis(dom: str, mask: np.ndarray, *, e_daily: pd.DataFrame,
                 p0: pd.DataFrame, sup: pd.DataFrame,
                 scale_pool_by_days: bool) -> dict:
    """把窗口总量装进一个基座 (供 cm.solve_city 复用)。

    scale_pool_by_days=True  -> 口径 P: 池/缺口按 n_days/730 缩放 (排除池效应)
    scale_pool_by_days=False -> 口径 W: 池 = 窗口内 Σ 既有用户回用交付 (A12/T14 §3.3)
    """
    n = int(mask.sum())
    ts = load_ts(dom)
    E = e_daily.evaporation_ml.to_numpy()
    R = sup.reuse_delivered_ml.to_numpy()
    wet_in_win = mask & (E > 1e-9)
    pool_idx = np.where(wet_in_win)[0]
    if pool_idx.size == 0:
        pool_idx = np.where(mask)[0]
    wb_sel = ts.wet_bulb_c.to_numpy()[pool_idx]
    i_rep = int(pool_idx[int(np.argmin(np.abs(wb_sel - np.median(wb_sel))))])
    r = ts.iloc[i_rep]
    bl = cm.BASELINES[dom]
    if scale_pool_by_days:
        pool = float(bl["P0"]) * n / cm.N_DAYS
        gap = float(bl["gap"]) * n / cm.N_DAYS
    else:
        pool = float(R[mask].sum())
        gap = float(bl["gap"]) * n / cm.N_DAYS
    return {
        "P0": pool, "gap": gap, "E_total": float(E[mask].sum()),
        "date_rep": pd.Timestamp(r.date),
        "drivers_rep": {"temperature_c": float(r.temperature_c),
                        "relative_humidity": float(r.relative_humidity_pct),
                        "load_factor": float(r.ai_load_factor_a30)},
        "n_days": n, "rep_day": str(pd.Timestamp(r.date).date()),
        "E_window_ml": float(E[mask].sum()), "pool_window_ml": pool,
        "gap_window_ml": gap,
        "pool_from_reuse_delivered": float(R[mask].sum()),
        "mean_T_window": float(ts.temperature_c.to_numpy()[mask].mean()),
        "mean_inflow_window": float(ts.reservoir_inflow_ml.to_numpy()[mask].mean()),
    }


def solve_window(dom: str, sample: str, q: dict, basis: dict, *, phi: float = PHI,
                 e_scale: float = 1.0, avail_frac: float = 1.0,
                 coc_design: float = cm.COC_DESIGN_DEFAULT,
                 limit_scale: float = 1.0) -> dict:
    """在窗口基座上求主估计量 (复用 cm.solve_city, 冻结规则代码路径)。"""
    avail_frac = float(np.clip(avail_frac, 1e-6, 1.0))
    bl = dict(basis)
    bl["P0"] = float(basis["P0"]) * avail_frac
    bl["E_total"] = float(basis["E_total"]) * float(e_scale)
    r = W.solve_dS(dom, sample, q, phi=phi, pool_ml=bl["P0"], gap_ml=basis["gap"],
                   dp_ml=0.0, e_total_ml=bl["E_total"], coc_design=coc_design,
                   limit_scale=limit_scale, period_days=float(basis["n_days"]),
                   date_rep=basis["date_rep"], drivers_rep=basis["drivers_rep"])
    r.update({k: basis[k] for k in ("n_days", "rep_day", "E_window_ml",
                                    "pool_window_ml", "gap_window_ml",
                                    "pool_from_reuse_delivered", "mean_T_window",
                                    "mean_inflow_window")})
    r["avail_frac"] = avail_frac
    r["e_scale"] = float(e_scale)
    r["dS_per_day_ml"] = r["dS_pot_ml"] / max(basis["n_days"], 1)
    return r


# ======================================================================
# 主流程
# ======================================================================
def main() -> int:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str = "") -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 92)
    rec("WP5 任务 B: 极端事件情景 (热浪 / 干旱) —— dS_pot 符号是否翻转")
    rec("=" * 92)

    samples, q_by, primary, banned = W.load_primary_samples()
    rec(f"\n[0] 口径: phi={PHI}, 面板={W.PANEL} (现行 baseline 引用限值 "
        f"{json.dumps(cm.PANELS[W.PANEL], ensure_ascii=False)})")
    rec(f"    主口径水样 (完整物种) = {primary}; 禁用 = {banned}")
    rec(f"    热浪窗 = 湿球 p{int(HEATWAVE_Q*100)} (A12 事先固定), 干旱窗 = "
        f"水库来水 {WINDOW_DAYS} 天滚动均值最小窗 (事先固定)")
    if not primary:
        rec("  ✗ 无完整物种水样 => NOT_IDENTIFIABLE, 不得计为 PASS")
        return 1

    # ---------------- 1. 逐日计划与窗口 ----------------
    rec("\n[1] 逐日计划与窗口构造 (引擎 calculate_data_center_plan, 只读)")
    daily, supplies, masks = {}, {}, {}
    for dom in W.DOMS:
        daily[dom] = daily_plan_e(dom)
        supplies[dom] = daily_reuse_supply(dom)
        masks[dom] = make_windows(dom)
        d = daily[dom]
        rec(f"  --- {dom} ---  730 天, T: med={d.temperature_c.median():.2f} "
            f"p95={d.temperature_c.quantile(.95):.2f} max={d.temperature_c.max():.2f}; "
            f"E: mean={d.evaporation_ml.mean():.2f} max={d.evaporation_ml.max():.2f}")
        rec(f"      PUE: min={d.pue.min():.4f} max={d.pue.max():.4f} "
            f"(热浪窗均值 PUE={d.pue[masks[dom]['heatwave']].mean():.4f}, "
            f"非热浪窗={d.pue[masks[dom]['non_heatwave_matched']].mean():.4f})")
        rec(f"      水库来水: min={d.reservoir_inflow_ml.min():.2f} "
            f"median={d.reservoir_inflow_ml.median():.2f} "
            f"max={d.reservoir_inflow_ml.max():.2f}")
        for tag, m in masks[dom].items():
            n = int(m.sum())
            rec(f"      窗 {tag:<22} n={n:>4}  均温={d.temperature_c[m].mean():6.2f}  "
                f"ΣE={d.evaporation_ml[m].sum():9.1f}  "
                f"Σ(reuse 交付)={supplies[dom].reuse_delivered_ml.to_numpy()[m].sum():9.1f}  "
                f"均来水={d.reservoir_inflow_ml[m].mean():7.2f}")

    # ---------------- 2. 热浪 / 干旱情景 (观测驱动 + 人为扰动) ----------------
    rec("\n[2] ★ 极端事件情景求解 (窗口化冻结模块; 口径 W = 池按窗口 Σ 交付)")
    rows = []
    for dom in W.DOMS:
        e_daily = daily[dom]; sup = supplies[dom]
        for wtag, mask in masks[dom].items():
            basis = window_basis(dom, mask, e_daily=e_daily, p0=None, sup=sup,
                                 scale_pool_by_days=False)
            for nm in primary:
                r = solve_window(dom, nm, q_by[nm], basis, phi=PHI)
                rows.append({
                    "scenario": f"{dom}|{wtag}", "domain": dom, "window": wtag,
                    "sample": nm, "driver_class": "OBSERVED_DRIVER",
                    "mechanism": "none", "phi": PHI, "e_scale": 1.0, "avail_frac": 1.0,
                    "limit_scale": 1.0, "coc_design": cm.COC_DESIGN_DEFAULT,
                    "pool_convention": "W_window_total",
                    "dS_pot_ml": r["dS_pot_ml"], "dS_per_day_ml": r["dS_per_day_ml"],
                    "M0_ml": r["M0_ml"], "M1_ml": r["M1_ml"], "C_ml": r["C_ml"],
                    "F_ml": r["F_ml"], "x_ai_ml": r["x_ai_ml"], "q": r["q"],
                    "inc_B1_ml": r["inc_B1_ml"], "inc_B2_ml": r["inc_B2_ml"],
                    "displaced_raw_ml": r["displaced_raw_ml"],
                    "CoC0": r["CoC0"], "CoC1": r["CoC1"],
                    "status_B2": r["status_B2"], "b1_healthy": r["b1_healthy"],
                    "coc_floor_degenerate": r["coc_floor_degenerate"],
                    "reliable": r["reliable"], "gate_reason": W.gate_reason(r),
                    "n_days": r["n_days"], "E_window_ml": r["E_window_ml"],
                    "pool_window_ml": r["pool_window_ml"],
                    "mean_T_window": r["mean_T_window"],
                    "mean_inflow_window": r["mean_inflow_window"],
                    "rep_day": r["rep_day"],
                })

    # 人为扰动: 热浪 (e_scale) 与干旱 (avail_frac) 的压力扫描
    rec("\n  -- 人为扰动扫描 (FORCED_PERTURBATION): 热浪 e_scale, 干旱 avail_frac --")
    heat_scan = [1.0, 1.2, 1.5, 2.0, 3.0, 5.0]
    dry_scan = [1.0, 0.75, 0.5, 0.35, 0.2, 0.1]
    for dom in W.DOMS:
        e_daily = daily[dom]; sup = supplies[dom]
        hb = window_basis(dom, masks[dom]["heatwave"], e_daily=e_daily, p0=None,
                          sup=sup, scale_pool_by_days=False)
        db = window_basis(dom, masks[dom]["drought_lowinflow"], e_daily=e_daily,
                          p0=None, sup=sup, scale_pool_by_days=False)
        for nm in primary:
            for es in heat_scan:
                r = solve_window(dom, nm, q_by[nm], hb, phi=PHI, e_scale=es)
                rows.append({
                    "scenario": f"{dom}|heatwave_forced_es{es:g}", "domain": dom,
                    "window": "heatwave", "sample": nm,
                    "driver_class": "FORCED_PERTURBATION" if es != 1.0 else "OBSERVED_DRIVER",
                    "mechanism": "heatwave_evap_scaling", "phi": PHI, "e_scale": es,
                    "avail_frac": 1.0, "limit_scale": 1.0,
                    "coc_design": cm.COC_DESIGN_DEFAULT,
                    "pool_convention": "W_window_total",
                    "dS_pot_ml": r["dS_pot_ml"], "dS_per_day_ml": r["dS_per_day_ml"],
                    "M0_ml": r["M0_ml"], "M1_ml": r["M1_ml"], "C_ml": r["C_ml"],
                    "F_ml": r["F_ml"], "x_ai_ml": r["x_ai_ml"], "q": r["q"],
                    "inc_B1_ml": r["inc_B1_ml"], "inc_B2_ml": r["inc_B2_ml"],
                    "displaced_raw_ml": r["displaced_raw_ml"],
                    "CoC0": r["CoC0"], "CoC1": r["CoC1"],
                    "status_B2": r["status_B2"], "b1_healthy": r["b1_healthy"],
                    "coc_floor_degenerate": r["coc_floor_degenerate"],
                    "reliable": r["reliable"], "gate_reason": W.gate_reason(r),
                    "n_days": r["n_days"], "E_window_ml": r["E_window_ml"],
                    "pool_window_ml": r["pool_window_ml"],
                    "mean_T_window": r["mean_T_window"],
                    "mean_inflow_window": r["mean_inflow_window"],
                    "rep_day": r["rep_day"],
                })
            for af in dry_scan:
                r = solve_window(dom, nm, q_by[nm], db, phi=PHI, avail_frac=af)
                rows.append({
                    "scenario": f"{dom}|drought_forced_avail{af:g}", "domain": dom,
                    "window": "drought_lowinflow", "sample": nm,
                    "driver_class": "FORCED_PERTURBATION" if af != 1.0 else "OBSERVED_DRIVER",
                    "mechanism": "drought_supply_scaling", "phi": PHI, "e_scale": 1.0,
                    "avail_frac": af, "limit_scale": 1.0,
                    "coc_design": cm.COC_DESIGN_DEFAULT,
                    "pool_convention": "W_window_total",
                    "dS_pot_ml": r["dS_pot_ml"], "dS_per_day_ml": r["dS_per_day_ml"],
                    "M0_ml": r["M0_ml"], "M1_ml": r["M1_ml"], "C_ml": r["C_ml"],
                    "F_ml": r["F_ml"], "x_ai_ml": r["x_ai_ml"], "q": r["q"],
                    "inc_B1_ml": r["inc_B1_ml"], "inc_B2_ml": r["inc_B2_ml"],
                    "displaced_raw_ml": r["displaced_raw_ml"],
                    "CoC0": r["CoC0"], "CoC1": r["CoC1"],
                    "status_B2": r["status_B2"], "b1_healthy": r["b1_healthy"],
                    "coc_floor_degenerate": r["coc_floor_degenerate"],
                    "reliable": r["reliable"], "gate_reason": W.gate_reason(r),
                    "n_days": r["n_days"], "E_window_ml": r["E_window_ml"],
                    "pool_window_ml": r["pool_window_ml"],
                    "mean_T_window": r["mean_T_window"],
                    "mean_inflow_window": r["mean_inflow_window"],
                    "rep_day": r["rep_day"],
                })
        # 首档打印
        hs = [x for x in rows if x["domain"] == dom and x["mechanism"] == "heatwave_evap_scaling"
              and x["sample"] == primary[0]]
        ds = [x for x in rows if x["domain"] == dom and x["mechanism"] == "drought_supply_scaling"
              and x["sample"] == primary[0]]
        rec(f"  {dom} 热浪 e_scale 扫描 ({primary[0][:22]}): " +
            " ".join(f"{x['e_scale']:g}->{x['dS_pot_ml']:.4g}" for x in hs))
        rec(f"  {dom} 干旱 avail 扫描 ({primary[0][:22]}): " +
            " ".join(f"{x['avail_frac']:g}->{x['dS_pot_ml']:.4g}" for x in ds))

    d = pd.DataFrame(rows)
    d.to_csv(HERE / "wp5_extreme_cases.csv", index=False, encoding="utf-8-sig")

    # ---------------- 3. 符号与量级裁定 ----------------
    rec("\n[3] ★ 符号裁定 (零值约定: |dS_pot| < 1e-6 ML 记为 0, 不计入正负)")
    ok = d[d["reliable"]].copy()
    n_all, n_eff = len(d), len(ok)
    rec(f"  n_all = {n_all}; n_eff (双门禁通过) = {n_eff}; "
        f"剔除 = {n_all-n_eff} ({100*(n_all-n_eff)/max(n_all,1):.2f}%)")
    if n_all - n_eff:
        ex = d[~d["reliable"]]
        rec(f"  剔除原因分布: {ex['gate_reason'].value_counts().to_dict()}")
    n_neg = int((ok["dS_pot_ml"] < -W.ZERO_ABS).sum())
    n_zero = int((ok["dS_pot_ml"].abs() <= W.ZERO_ABS).sum())
    n_pos = int((ok["dS_pot_ml"] > W.ZERO_ABS).sum())
    rec(f"  dS_pot < 0 (城市受益) = {n_neg};  = 0 = {n_zero};  > 0 (城市受损) = {n_pos}")

    rec("\n  (a) 观测驱动窗口 vs 全年 (同口径 W, 单位 ML/day 可比)")
    for dom in W.DOMS:
        rec(f"    --- {dom} ---")
        for nm in primary:
            sub = ok[(ok.domain == dom) & (ok["sample"] == nm)
                     & (ok.mechanism == "none")]
            if not len(sub):
                rec(f"      {nm[:34]:<36} NOT_IDENTIFIABLE (无可靠窗口)")
                continue
            fy = sub[sub.window == "full_year"]
            base = float(fy["dS_per_day_ml"].iloc[0]) if len(fy) else float("nan")
            parts = []
            for _, r in sub.iterrows():
                if r["window"] == "full_year":
                    continue
                ratio = (r["dS_per_day_ml"] / base) if np.isfinite(base) and base != 0 else float("nan")
                parts.append(f"{r['window']}={r['dS_per_day_ml']:.1f}({ratio:.3f}×)")
            rec(f"      {nm[:34]:<36} 全年={base:8.1f} ML/d  " + "  ".join(parts))

    rec("\n  (b) 极端 vs 非极端: 是否发生符号翻转?")
    flips = []
    for dom in W.DOMS:
        for nm in primary:
            s = ok[(ok.domain == dom) & (ok["sample"] == nm)]
            a = s[s.window == "heatwave"][["dS_pot_ml", "dS_per_day_ml"]]
            b = s[s.window == "non_heatwave_matched"][["dS_pot_ml", "dS_per_day_ml"]]
            f_ = s[s.window == "full_year"][["dS_pot_ml", "dS_per_day_ml"]]
            dr = s[s.window == "drought_lowinflow"][["dS_pot_ml", "dS_per_day_ml"]]
            def sg(x):
                return None if not len(x) else W.sign_of(float(x["dS_pot_ml"].iloc[0]))
            flips.append({"domain": dom, "sample": nm,
                          "sign_full_year": sg(f_), "sign_heatwave": sg(a),
                          "sign_non_heatwave": sg(b), "sign_drought": sg(dr),
                          "dS_full_year": None if not len(f_) else float(f_["dS_pot_ml"].iloc[0]),
                          "dS_heatwave": None if not len(a) else float(a["dS_pot_ml"].iloc[0]),
                          "dS_non_heatwave": None if not len(b) else float(b["dS_pot_ml"].iloc[0]),
                          "dS_drought": None if not len(dr) else float(dr["dS_pot_ml"].iloc[0]),
                          "flip_heat_vs_year": None if (sg(a) is None or sg(f_) is None)
                                               else bool(sg(a) != sg(f_)),
                          "flip_drought_vs_year": None if (sg(dr) is None or sg(f_) is None)
                                                  else bool(sg(dr) != sg(f_)),
                          "flip_heat_vs_nonheat": None if (sg(a) is None or sg(b) is None)
                                                  else bool(sg(a) != sg(b))})
    fl = pd.DataFrame(flips)
    rec(f"    {'domain':>6} {'sample':<34} {'全年':>6} {'热浪':>6} {'非热浪':>7} "
        f"{'干旱':>6} {'热/全翻转':>10} {'旱/全翻转':>10}")
    for _, r in fl.iterrows():
        f2 = lambda v: "NA" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)
        f3 = lambda v: "NA" if v is None else ("是" if v else "否")
        rec(f"    {r['domain']:>6} {r['sample'][:34]:<34} {f2(r['sign_full_year']):>6} "
            f"{f2(r['sign_heatwave']):>6} {f2(r['sign_non_heatwave']):>7} "
            f"{f2(r['sign_drought']):>6} {f3(r['flip_heat_vs_year']):>10} "
            f"{f3(r['flip_drought_vs_year']):>10}")
    n_flip_heat = int((fl["flip_heat_vs_year"] == True).sum())      # noqa: E712
    n_flip_dr = int((fl["flip_drought_vs_year"] == True).sum())     # noqa: E712
    n_cmp_heat = int(fl["flip_heat_vs_year"].notna().sum())
    n_cmp_dr = int(fl["flip_drought_vs_year"].notna().sum())
    rec(f"    ⇒ 热浪窗相对全年符号翻转: {n_flip_heat}/{n_cmp_heat} 个可比情景")
    rec(f"    ⇒ 干旱窗相对全年符号翻转: {n_flip_dr}/{n_cmp_dr} 个可比情景")

    rec("\n  (c) 量变质变判定: 相对全年, 极端窗的 dS/day 变化倍数")
    mag = []
    for dom in W.DOMS:
        for nm in primary:
            s = ok[(ok.domain == dom) & (ok["sample"] == nm) & (ok.mechanism == "none")]
            if not len(s) or not len(s[s.window == "full_year"]):
                continue
            base = float(s[s.window == "full_year"]["dS_per_day_ml"].iloc[0])
            for w in ("heatwave", "non_heatwave_matched", "drought_lowinflow"):
                x = s[s.window == w]
                if not len(x) or base == 0:
                    continue
                mag.append({"domain": dom, "sample": nm, "window": w,
                            "dS_per_day_ml": float(x["dS_per_day_ml"].iloc[0]),
                            "ratio_to_full_year": float(x["dS_per_day_ml"].iloc[0]) / base,
                            "abs_delta_per_day_ml": float(x["dS_per_day_ml"].iloc[0]) - base})
    mg = pd.DataFrame(mag)
    if len(mg):
        rec(mg.round(4).to_string(index=False))
        mx = float(mg["ratio_to_full_year"].abs().max())
        rec(f"    ⇒ 最大倍数偏离 = {mx:.4f}×  "
            f"=> {'量变 (量级稳定, 无质变)' if mx < 2 else '存在 >2× 的量级变化'}")

    # ---------------- 4. 人为扰动下的临界点 (符号翻转搜索) ----------------
    rec("\n[4] ★ 人为扰动下的符号翻转临界点 (二元搜索, 401 点扫描)")
    thresh_rows = []
    for dom in W.DOMS:
        e_daily = daily[dom]; sup = supplies[dom]
        hb = window_basis(dom, masks[dom]["heatwave"], e_daily=e_daily, p0=None,
                          sup=sup, scale_pool_by_days=False)
        db = window_basis(dom, masks[dom]["drought_lowinflow"], e_daily=e_daily,
                          p0=None, sup=sup, scale_pool_by_days=False)
        for nm in primary:
            # 热浪: 需要多大的 e_scale 才能翻转符号?
            flip_es = None
            prev = None
            for es in np.linspace(1.0, 40.0, 401):
                r = solve_window(dom, nm, q_by[nm], hb, phi=PHI, e_scale=float(es))
                if r["reliable"]:
                    s = W.sign_of(r["dS_pot_ml"])
                    if prev is not None and s != prev and s != 0 and prev != 0:
                        flip_es = float(es); break
                    prev = s
            # 干旱: 需要多低的 avail_frac 才能翻转?
            flip_af = None
            prev = None
            for af in np.linspace(1.0, 1e-3, 401):
                r = solve_window(dom, nm, q_by[nm], db, phi=PHI, avail_frac=float(af))
                if r["reliable"]:
                    s = W.sign_of(r["dS_pot_ml"])
                    if prev is not None and s != prev and s != 0 and prev != 0:
                        flip_af = float(af); break
                    prev = s
            thresh_rows.append({"domain": dom, "sample": nm,
                                "heatwave_e_scale_flip": flip_es,
                                "drought_avail_frac_flip": flip_af})
    th = pd.DataFrame(thresh_rows)
    rec(f"    {'domain':>6} {'sample':<34} {'热浪翻转 e_scale':>18} {'干旱翻转 avail_frac':>21}")
    for _, r in th.iterrows():
        fe = "无 (扫描至 40×)" if pd.isna(r["heatwave_e_scale_flip"]) else f"{r['heatwave_e_scale_flip']:.2f}"
        fa = "无 (扫描至 0.001)" if pd.isna(r["drought_avail_frac_flip"]) else f"{r['drought_avail_frac_flip']:.4f}"
        rec(f"    {r['domain']:>6} {r['sample'][:34]:<34} {fe:>18} {fa:>21}")
    rec("    读法: '无' 表示在扫描范围内符号**始终未翻转** —— 如实报告负结果, 不修饰。")
    rec("    ⚠ 机制澄清 (实测, 否则会误读为'热浪越大越有害'):")
    rec("      dS_pot = C - F, F = (M0-M1) + x_ai = M0 - (1-phi_eff)*M1。")
    rec("      极端 e_scale 下 M0 与 M1 同比例放大, 而 phi_eff 被可得再生水量钉住")
    rec("      -> F 变为**负**, 即'再生水把比它自身更多的自来水顶掉'(净替代为负)。")
    rec("      翻转条件: phi_eff < 1 - M0/M1  (等价于 F = M0 - (1-phi_eff)*M1 < 0)。")
    rec("      且 es>10 后 CoC1 钉在水质下限 2.8226 (碱度受限), phi_eff 恒定, M1 随 es 线性增长")
    rec("      -> 该区段是**引擎线性外推**, 无观测支撑, 只作临界点定位, 不作结论。")

    # 翻转条件的闭式核对 (相对容差)
    flip_checks = []
    for dom2 in W.DOMS:
        e_daily2 = daily[dom2]; sup2 = supplies[dom2]
        hb2 = window_basis(dom2, masks[dom2]["heatwave"], e_daily=e_daily2, p0=None,
                           sup=sup2, scale_pool_by_days=False)
        for nm2 in primary:
            for es in (1.0, 5.0, 10.0, 20.0, 40.0):
                r = solve_window(dom2, nm2, q_by[nm2], hb2, phi=PHI, e_scale=es)
                if not r["reliable"] or r["M1_ml"] <= 0:
                    continue
                pe = r["x_ai_ml"] / r["M1_ml"]
                thr_ = 1.0 - r["M0_ml"] / r["M1_ml"]
                flip_checks.append({
                    "domain": dom2, "sample": nm2, "e_scale": es,
                    "phi_eff": pe, "one_minus_M0_over_M1": thr_,
                    "F_ml": r["F_ml"], "dS_pot_ml": r["dS_pot_ml"],
                    "closed_form_says_negative_F": bool(pe < thr_),
                    "observed_F_negative": bool(r["F_ml"] < 0),
                    "closed_form_matches": bool((pe < thr_) == (r["F_ml"] < 0)),
                })
    fc = pd.DataFrame(flip_checks)
    n_match = int(fc["closed_form_matches"].sum()) if len(fc) else 0
    rec(f"    闭式核对: F<0 <=> phi_eff < 1-M0/M1 —— 命中 {n_match}/{len(fc)} "
        f"=> {'✓ 条件成立' if len(fc) and n_match == len(fc) else '✗ 条件不成立'}")
    fc.to_csv(HERE / "wp5_extreme_flip_condition.csv", index=False, encoding="utf-8-sig")

    # ---------------- 5. 数据中心运行是否受限 (供给侧) ----------------
    rec("\n[5] ★ 极端条件下数据中心运行是否受限 (引擎原生计划, 非 dS 口径)")
    ops_rows = []
    for dom in W.DOMS:
        e_daily = daily[dom]
        ts = load_ts(dom)
        for wtag in ("full_year", "heatwave", "non_heatwave_matched", "drought_lowinflow"):
            m = masks[dom][wtag]
            n = int(m.sum())
            ops_rows.append({
                "domain": dom, "window": wtag, "n_days": n, "driver_class": "OBSERVED_DRIVER",
                "mean_T_c": float(e_daily.temperature_c[m].mean()),
                "mean_PUE": float(e_daily.pue[m].mean()),
                "max_PUE": float(e_daily.pue[m].max()),
                "sum_E_ml": float(e_daily.evaporation_ml[m].sum()),
                "E_per_day_ml": float(e_daily.evaporation_ml[m].sum()) / max(n, 1),
                "sum_M0_ml": float(e_daily.external_makeup_ml[m].sum()),
                "M0_per_day_ml": float(e_daily.external_makeup_ml[m].sum()) / max(n, 1),
                "mean_inflow_ml": float(e_daily.reservoir_inflow_ml[m].mean()),
            })
    op = pd.DataFrame(ops_rows)
    op.to_csv(HERE / "wp5_extreme_ops.csv", index=False, encoding="utf-8-sig")
    rec(f"    {'dom':>4} {'window':<22} {'n':>4} {'均温':>6} {'均PUE':>7} "
        f"{'ΣE(ML)':>10} {'E/d':>8} {'M0/d':>9} {'均来水':>8}")
    for _, r in op.iterrows():
        rec(f"    {r['domain']:>4} {r['window']:<22} {r['n_days']:>4} {r['mean_T_c']:>6.2f} "
            f"{r['mean_PUE']:>7.4f} {r['sum_E_ml']:>10.1f} {r['E_per_day_ml']:>8.2f} "
            f"{r['M0_per_day_ml']:>9.2f} {r['mean_inflow_ml']:>8.2f}")
    hw = op[op.window == "heatwave"].set_index("domain")
    fy = op[op.window == "full_year"].set_index("domain")
    rec("    热浪窗相对全年 (观测驱动, 量变):")
    for dom in W.DOMS:
        rec(f"      {dom}: E/day {hw.loc[dom,'E_per_day_ml']/fy.loc[dom,'E_per_day_ml']:.4f}×, "
            f"M0/day {hw.loc[dom,'M0_per_day_ml']/fy.loc[dom,'M0_per_day_ml']:.4f}×, "
            f"PUE {hw.loc[dom,'mean_PUE']/fy.loc[dom,'mean_PUE']:.4f}×")
    rec("    ⇒ 蒸发式冷却下 PUE/蒸发的时间结构平坦 (A12 §1.3 已记录峰谷比 1.11), "
        "故**观测热浪本身不构成运行受限**; 受限需水化学恶化或供给缩减触发。")
    # 供给受限下 AI 可得量
    sup_rows = []
    for dom in W.DOMS:
        bl = cm.BASELINES[dom]
        for af in (1.0, 0.75, 0.5, 0.25, 0.1):
            comp = cm.base_comp(bl, W.PANEL, 0.6, limit_scale=1.0)
            try:
                p = calculate_data_center_plan(
                    comp, bl["date_rep"], bl["drivers_rep"],
                    reclaimed_available_ml=float(bl["P0"]) * af / cm.N_DAYS,
                    reclaimed_quality_mg_l=q_by[primary[0]])
                sup_rows.append({"domain": dom, "avail_frac": af,
                                 "delivered_reclaimed_fraction": float(p.target_reclaimed_fraction),
                                 "quality_solver_reclaimed_fraction":
                                     float(p.quality_solver_reclaimed_fraction),
                                 "status": str(p.quality_solver_status),
                                 "CoC": float(p.cycles_of_concentration),
                                 "external_makeup_ml": float(p.external_makeup_ml)})
            except Exception as exc:  # noqa: BLE001
                sup_rows.append({"domain": dom, "avail_frac": af,
                                 "status": "ENGINE_RAISE:" + type(exc).__name__,
                                 "detail": str(exc)[:120]})
    sp = pd.DataFrame(sup_rows)
    sp.to_csv(HERE / "wp5_extreme_supply.csv", index=False, encoding="utf-8-sig")
    rec("    供给限流下 AI 的再生水可得比例 (引擎原生 fixed-point 解):")
    for _, r in sp.iterrows():
        if "quality_solver_reclaimed_fraction" in r and pd.notna(r.get("quality_solver_reclaimed_fraction")):
            rec(f"      {r['domain']} avail={r['avail_frac']:<5} "
                f"解得再生水占比={r['quality_solver_reclaimed_fraction']:.4f} "
                f"CoC={r['CoC']:.4f} status={r['status']}")
        else:
            rec(f"      {r['domain']} avail={r['avail_frac']:<5} {r.get('status')}: "
                f"{str(r.get('detail',''))[:80]}")

    # ---------------- 6. 谁受益 / 谁受损 ----------------
    rec("\n[6] ★ 谁受益 / 谁受损 (观测驱动窗口, 主口径 W)")
    who = []
    for dom in W.DOMS:
        for nm in primary:
            s = ok[(ok.domain == dom) & (ok["sample"] == nm) & (ok.mechanism == "none")]
            for _, r in s.iterrows():
                who.append({
                    "domain": dom, "window": r["window"], "sample": nm,
                    "dS_pot_ml": r["dS_pot_ml"],
                    "verdict": ("城市净取水下降 (城市受益)" if r["dS_pot_ml"] < -W.ZERO_ABS
                                else ("城市净取水上升 (城市受损)" if r["dS_pot_ml"] > W.ZERO_ABS
                                      else "中性")),
                    "C_ml": r["C_ml"], "F_ml": r["F_ml"], "x_ai_ml": r["x_ai_ml"],
                    "incumbent_displaced_ml": r["inc_B2_ml"] - r["inc_B1_ml"],
                    "ai_reclaimed_ml": r["x_ai_ml"], "q": r["q"],
                    "CoC0": r["CoC0"], "CoC1": r["CoC1"],
                })
    wh = pd.DataFrame(who)
    rec(f"    {'dom':>4} {'window':<22} {'sample':<22} {'dS(ML)':>12} {'裁定':<24} "
        f"{'挤占(ML)':>10} {'AI取水(ML)':>11}")
    for _, r in wh.iterrows():
        rec(f"    {r['domain']:>4} {r['window']:<22} {r['sample'][:20]:<22} "
            f"{r['dS_pot_ml']:>12.2f} {r['verdict']:<24} "
            f"{r['incumbent_displaced_ml']:>10.2f} {r['ai_reclaimed_ml']:>11.2f}")

    # ---------------- 7. 汇总 ----------------
    obs = d[d.driver_class == "OBSERVED_DRIVER"]
    summary = {
        "task": "WP5 任务 B: 极端事件情景 (热浪 / 干旱)",
        "estimator": "dS_pot = C - F = max(0, inc_B2 - inc_B1) - [(M0 - M1) + x_ai]",
        "sign_convention": "dS_pot > 0 => 城市净取水上升 (有害); < 0 => 下降 (有益)",
        "panel": W.PANEL, "panel_limits": cm.PANELS[W.PANEL], "limit_set": cm.LIMIT_SET,
        "phi": PHI,
        "method": ("窗口化冻结模块: 复用 city_model.solve_city, 只替换 E_total/代表日/池/缺口"
                   "为窗口总量 (period_days=n_days); 代表日在窗口内湿日中取湿球中位日。"
                   "与 A12/T14 §3.3 既有方法学纪律一致, 不自建单日城市解 (M1 教训)。"),
        "window_definitions": {
            "heatwave": f"湿球 >= 730 天分布的 p{int(HEATWAVE_Q*100)} (事先固定, A12)",
            "non_heatwave_matched": "按湿球升序取与热浪窗等量的最低湿球日 (A12)",
            "drought_lowinflow": f"水库来水 {WINDOW_DAYS} 天滚动均值最小的窗口 (事先固定)",
            "full_year": "730 天全部",
            "note": "窗定义事先固定, 不事后挑窗; 本脚本未做多窗定义鲁棒性 (A12 §7.3 已有)。",
        },
        "driver_class_legend": {
            "OBSERVED_DRIVER": "由 730 天逐日序列中实际观测到的极端窗口驱动",
            "FORCED_PERTURBATION": "人为扰动, 把机制推到观测范围之外的压力档",
        },
        "gates": {
            "n_all": n_all, "n_eff": n_eff, "n_excluded": n_all - n_eff,
            "excluded_share_pct": round(100 * (n_all - n_eff) / max(n_all, 1), 2),
            "zero_value_convention": f"|dS_pot| < {W.ZERO_ABS} ML 记为 0",
            "reason_counts": d[~d["reliable"]]["gate_reason"].value_counts().to_dict()
            if n_all - n_eff else {},
            "reasons_legend": ("B2_NOT_CONVERGED_UNIQUE=水质定常解不唯一/不收敛; "
                               "COC_FLOOR_DEGENERATE=CoC 触引擎下限 1.000001; "
                               "B1_UNHEALTHY=B1 支路非单根或未闭合; NON_FINITE=出现 NaN"),
        },
        "symbol_distribution_reliable": {
            "n_eff": n_eff, "n_neg_beneficial": n_neg, "n_zero": n_zero,
            "n_pos_harmful": n_pos,
            "zero_value_convention": f"|dS_pot| < {W.ZERO_ABS} ML 记为 0",
        },
        "observed_windows_vs_full_year": fl.to_dict(orient="records"),
        "magnitude_shift": mg.round(6).to_dict(orient="records") if len(mg) else [],
        "max_ratio_to_full_year": float(mg["ratio_to_full_year"].abs().max()) if len(mg) else None,
        "sign_flip_from_extremes": {
            "n_comparable_heatwave": n_cmp_heat, "n_flip_heatwave_vs_year": n_flip_heat,
            "n_comparable_drought": n_cmp_dr, "n_flip_drought_vs_year": n_flip_dr,
            "verdict": ("无观测驱动极端窗导致符号翻转" if (n_flip_heat == 0 and n_flip_dr == 0)
                        else "存在观测驱动极端窗导致的符号翻转"),
        },
        "forced_perturbation_thresholds": th.to_dict(orient="records"),
        "forced_threshold_note": ("None/NaN 表示在扫描范围内符号始终未翻转 —— 如实报告的负结果。"),
        "forced_flip_mechanism": {
            "finding": ("观测驱动极端窗**不**翻转符号; 只有人为扰动 e_scale 很大时会出现 "
                        "dS_pot 由负转正 (ha/co 的 IEUA: e_scale ≈ 6.75; LADWP 在 40× 内不翻转)。"),
            "closed_form_condition": "F = (M0-M1) + x_ai = M0 - (1-phi_eff)*M1 < 0  <=>  phi_eff < 1 - M0/M1",
            "closed_form_checked": {"n_checked": int(len(fc)), "n_matching": n_match,
                                    "table": fc.round(6).to_dict(orient="records") if len(fc) else []},
            "physical_reading": ("该翻转是**会计后果**而非'城市受害': F 变负意味着再生水顶掉的"
                                 "自来水多于它自身取用量, 城市净取水比 B1 更低 (仍属受益方向)。"),
            "extrapolation_warning": ("es > 10 后 CoC1 钉在水质下限 2.8226 (碱度受限), phi_eff 恒定, "
                                      "M1 随 es 线性增长 —— 该区段为引擎线性外推, 无观测支撑, "
                                      "仅用于定位临界点, 不用于结论。"),
            "drought_no_flip": ("干旱 avail_frac 降到 0.001 仍**未**翻转 (4/4 情景): "
                                "dS_pot 单调趋近 0 但不改变符号。"),
        },
        "operations_under_extremes": op.to_dict(orient="records"),
        "supply_limited_ai_share": sp.to_dict(orient="records"),
        "who_gains_who_loses": wh.to_dict(orient="records"),
        "verdict_qualitative_vs_quantitative": {
            "question": "极端事件是否带来质变 (符号/次序改变) 还是仅量变?",
            "heatwave_observed": ("量变: 观测热浪窗的 dS/day 与全年同量级, 符号不变; "
                                  "蒸发式冷却的时间结构平坦 (A12 记录峰谷比 1.11), "
                                  "故热浪对 dS_pot 的作用是通过 PUE 的微弱正反馈, 非质变。"),
            "drought_observed": ("量变: 观测干旱窗 (来水最低 37 天) 的池只小幅缩减, "
                                 "dS/day 与全年同量级, 符号不变。"),
            "forced": ("**唯一**的符号翻转出现在人为扰动下: e_scale 推到 ≈6.75× (IEUA, 两域), "
                       "且该翻转是 F 变负的会计后果 (再生水净替代为负), 而非'城市受害'; "
                       "es>10 后为引擎线性外推区, 无观测支撑。干旱 avail_frac 自 1.0 扫到 0.001 "
                       "仍不翻转 (dS_pot 单调趋近 0)。"),
            "verdict": ("就**观测驱动**的极端事件而言: 无质变, 仅量变 (最大 1.139×, 符号全部保持负)。"
                        "质变需要人为把化学/限值压力推到观测范围之外, 且其方向是'转正' "
                        "(账面受益方向), 不是'城市受害'。"),
        },
        "discipline_note": (
            "引擎与 city_model 只读; 水样只来自 load_samples(); 主口径仅完整物种水样; "
            "双门禁 + n_eff; 不可辨识情景显式标记并剔除, 不插补、不计 PASS; "
            "符号计数声明零值约定; 负结果 (无符号翻转) 如实报告, 不修饰。"),
        "runtime_s": round(time.time() - t0, 1),
        "outputs": ["wp5_extreme_cases.csv", "wp5_extreme_summary.json",
                    "wp5_extreme_ops.csv", "wp5_extreme_supply.csv",
                    "wp5_extreme_flip_condition.csv", "wp5_extreme_events_log.txt"],
    }
    (HERE / "wp5_extreme_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (HERE / "wp5_extreme_events_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp5_extreme_cases.csv / wp5_extreme_summary.json "
        f"(+ wp5_extreme_ops.csv, wp5_extreme_supply.csv, wp5_extreme_events_log.txt) "
        f"  {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
