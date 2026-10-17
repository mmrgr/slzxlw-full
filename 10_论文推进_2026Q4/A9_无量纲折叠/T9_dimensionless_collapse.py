"""T9: 无量纲折叠的代数化简 + 跨参数域检验 (审计修复版, 2026-10-14).

科学问题
--------
T1/T2 揭示城市级节水 S_city 由水质与分配共同决定。但 S_city 同时依赖
大量维度的量: 城市规模(E)、再生水池规模(P0)、既有用户缺口(gap)、
扩容规模(dP)、掺混比(phi)、水化学。若这些维度不能降维, 结论就只是
"两个合成城市的特例", 无法迁移。

本脚本证明并检验一个 2-群折叠:

    y := S_city / M0 = Phi(phi) * [ phi*delta - u(phi) ]
    Phi(phi) = M(phi)/M0      (无量纲水质因子)
    u(phi)   = 1 - 1/Phi(phi) (无量纲质量惩罚)
    w        = phi * delta    (无量纲新增供给, delta = 新增产能占 AI 再生水需求之比)

关键非平凡内容 (重述):
  (1) E 消去: g = M/E 与城市/IT 容量无关 (可独立检验, 见 Stage 1b);
  (2) 破坏条件化简: y > 0 <=> dP > dP* = M(phi) - M0 (恰好等于水质惩罚造成的额外补水);
  (3) 折叠坐标 vs 朴素坐标的散度对照 —— **事后诊断指标**。

审计修正 (2026-10-14, 见 05_方法审计_v1 §A1/A2/D5):
  y = Phi*(w-u) 是**代数恒等式**, 不是经验发现。delta 的定义
      delta := 1 - (pool - inc_recl)/x_ai
  正是为使该式成立而设: 代入即得 Phi*(w-u) == S_city/m0。因此
  "残差 ~ 1e-15 / R^2 = 1" 在数学上必然 —— 它证明的是"引擎三个模块
  没有引入第三个变量", 而不是"发现了可迁移的降维规律"。
  所谓 "6 维 -> 2 维" 实为把 6 个量**重参数化**为 2 个量; delta 本身是
  (pool, gap, dP, 分配规则) 的函数, 把待解释的变异搬进了坐标轴。
  => delta 的**外生可预测性**由 T9b 单独检验 (那才是可迁移性)。
  => delta 的抽样上界 (pool 缩放到 4x) 已含城市/池规模, 故"E 消去"须
     限定为"给定 delta 后的条件陈述", 不得读成"与城市规模无关的半句"。

方法
----
全部经仓库真实模块求解, 未重写规则:
  物理/水化学: data_center.calculate_data_center_plan (coc_mode='quality_limited')
  分配:       reclaimed_allocation.solve_joint_quality_allocation
城市参数由 LHS 空间填充抽样 (池规模、缺口、扩容、AI 目标掺混比、水样、Q)。

Gate 说明 (A2 修正):
  原 Gate G-B 判据 (残差 < 1e-6 且 散度比 > 3x) 系看到数据后设定、未预注册,
  现予作废。折叠残差与散度比降级为**事后诊断指标**, 不代表任何通过/失败结论。
  真正的可迁移性检验移至 T9b (delta 的外生解析预测), 其判据已预先写入
  预注册补丁 A0_预注册/preregistration_amendment_1.md。
"""
# ⚠ 清理轮 2026-10-14 (E-1): 本文件内嵌了一套 city_model.py 的**旧副本**, 语义已落后。
#
# 与 A10_敏感性与边界/city_model.py 同名但降级的 7 个函数:
#   quality_dict (md5 逐字相同) / load_samples / baseline / base_comp /
#   make_evaluators / m0_of / solve_city
# 其中 make_evaluators 的缓存键不含代表日 (M5)、reclaimed_available_ml 硬编码
# `/ N_DAYS` (M6)、m0_of 未透传冷却技术 (M4) —— 即 **M4/M5/M6 三个缺陷在本副本中
# 依然存在**, 而 city_model.py 已在修复轮中修好。
#
# 为什么本轮只加警示、不同步修复 (方案①, 用户拍板):
#   T9 的结论是"代数恒等式 + 事后诊断", 480 情景的评估器**从不进入窗口/多技术
#   语义**, 故 M4/M5/M6 不影响本文件任何数值; 而重构为 `import city_model` 会改变
#   抽样/求解路径, 必须全量重跑并逐位比对 T9_summary.json
#   (max|Δy| = 7.11e-15, 降维比 19.37x, Φ 上界 36.578), 一旦有变将牵连
#   04/05/06/07/11/12 六份文档 —— 风险大于收益。
# ⇒ 纪律: **任何针对 city_model 的修复都必须同步检查本文件**; 若确要动本文件,
#   须重跑并逐位比对 T9_summary.json / T9_collapse_points.csv。
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(REPO / "src"))
from aiuwm.data_center import calculate_data_center_plan  # noqa: E402
from aiuwm.reclaimed_allocation import (  # noqa: E402
    JointPlanEvaluation,
    JointQualityRequest,
    solve_joint_quality_allocation,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
R2 = REPO / "examples" / "cawcc_r2"
DOMAINS = ("ha", "co")
N_DAYS = 730
RNG = np.random.default_rng(20261014)

PANEL_A = {"TDS": 2200.0, "chloride": 500.0}
PANEL_B = {"TDS": 2200.0, "chloride": 500.0, "hardness": 700.0,
           "alkalinity": 500.0, "silica": 150.0}
POTABLE_EXTRA = {"hardness": 120.0, "alkalinity": 100.0, "silica": 10.0}
PANELS = {"A_engine2": PANEL_A, "B_full": PANEL_B}


# ----------------------------------------------------------------- 输入
def load_samples() -> pd.DataFrame:
    d = pd.read_csv(ROOT / "A4_水化学参数域" / "T6_water_chemistry_samples.csv",
                    encoding="utf-8-sig").rename(columns={"source": "sample"})
    return d[["sample", "sclass", "TDS", "chloride", "hardness",
              "alkalinity", "silica"]].copy()


def quality_dict(row: pd.Series, panel: dict) -> dict:
    return {sp: float(row[sp]) for sp in panel
            if sp in row.index and pd.notna(row.get(sp))}


def baseline(dom: str) -> dict:
    """城市基线: 从 T2 冻结摘要读取 P0/gap, 从 timeseries 复原代表日与驱动."""
    summ = json.loads((ROOT / "A7_质量分配联合" / "T2_summary.json")
                      .read_text(encoding="utf-8"))
    b = summ["baselines"][dom]
    ts = pd.read_csv(R2 / dom / "timeseries.csv")
    i = int(ts["wet_bulb_c"].sub(ts["wet_bulb_c"].median()).abs().idxmin())
    r = ts.iloc[i]
    drv = {"temperature_c": float(r.temperature_c),
           "relative_humidity": float(r.relative_humidity_pct),
           "load_factor": float(r.ai_load_factor_a30)}
    return {"domain": dom, "P0": float(b["P0_ml"]), "gap": float(b["gap_ml"]),
            "E_total": float(b["E_total_ml"]),
            "date_rep": pd.Timestamp(r.date), "drivers_rep": drv,
            "proj": json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))}


def base_comp(bl: dict, panel_name: str, phi: float) -> dict:
    comp = copy.deepcopy(bl["proj"]["components"]["AI_DC1"])
    comp["installed_it_capacity_mw"] = 1000.0
    comp["cooling"]["coc_mode"] = "quality_limited"
    comp["cooling"]["water_quality_limits"] = dict(PANELS[panel_name])
    comp["water_sources"]["reclaimed"]["target_fraction"] = phi
    comp["water_sources"]["potable"]["target_fraction"] = 1.0 - phi
    pq = dict(comp["water_sources"]["potable"].get("quality", {}))
    if panel_name == "B_full":
        for k, v in POTABLE_EXTRA.items():
            pq.setdefault(k, v)
    comp["water_sources"]["potable"]["quality"] = pq
    return comp


# ----------------------------------------------------------------- 物理
def g_curve(bl: dict, panel_name: str, q: dict, phi_grid: list[float]) -> pd.DataFrame:
    """g(phi) = M(phi)/E  (逐日代表日), 与城市规模 E 无关."""
    out = []
    for phi in phi_grid:
        comp = base_comp(bl, panel_name, phi)
        p = calculate_data_center_plan(comp, bl["date_rep"], bl["drivers_rep"],
                                       reclaimed_available_ml=1e9,
                                       reclaimed_quality_mg_l=q)
        ev = float(p.evaporation_ml)
        out.append({"phi": phi, "CoC": float(p.cycles_of_concentration),
                    "g": (float(p.external_makeup_ml) / ev) if ev > 1e-12 else np.nan,
                    "status": str(p.quality_solver_status)})
    return pd.DataFrame(out)


def make_evaluators(bl: dict, panel_name: str, q: dict, phi_req: float, cache: dict):
    """返回 AI/INC 的 JointPlanEvaluation 评估器 (真实质量模型).

    重要: 缓存键必须含 trial (可得再生水量). 引擎按
        r = min(E(r)*target, available) / E(r)
    求解实际交付掺混比; 若按 target 缓存, 评估器会被冻结在
    available 未知的状态, 使 M 与 CoC 退化为常数.
    """
    e_tot = bl["E_total"]

    def ev_ai(req: JointQualityRequest, trial: float) -> JointPlanEvaluation:
        frac = float(np.clip(req.target_reclaimed_fraction, 0.0, 1.0))
        key = ("ai", round(frac, 9), round(float(trial), 6))
        if key in cache:
            return cache[key]
        comp = base_comp(bl, panel_name, frac)
        p = calculate_data_center_plan(comp, bl["date_rep"], bl["drivers_rep"],
                                       reclaimed_available_ml=float(trial) / N_DAYS,
                                       reclaimed_quality_mg_l=q)
        ev = float(p.evaporation_ml)
        g = (float(p.external_makeup_ml) / ev) if ev > 1e-12 else 0.0
        res = float(p.quality_solver_residual)
        out = JointPlanEvaluation(
            external_makeup_ml=e_tot * g,
            cycles_of_concentration=float(p.cycles_of_concentration),
            reclaimed_quality_mg_l={k: float(v) for k, v in q.items()},
            quality_solver_status=str(p.quality_solver_status),
            quality_solver_residual=(abs(res) if np.isfinite(res) else 0.0))
        cache[key] = out
        return out

    def ev_inc(req: JointQualityRequest, trial: float) -> JointPlanEvaluation:
        return JointPlanEvaluation(external_makeup_ml=float(req.max_reclaimed_ml or 0.0),
                                   cycles_of_concentration=1.0,
                                   reclaimed_quality_mg_l={},
                                   quality_solver_status="converged",
                                   quality_solver_residual=0.0)
    return ev_ai, ev_inc


def m0_of(bl: dict, panel_name: str, q: dict) -> float:
    comp = base_comp(bl, panel_name, 0.0)
    p = calculate_data_center_plan(comp, bl["date_rep"], bl["drivers_rep"],
                                   reclaimed_available_ml=0.0,
                                   reclaimed_quality_mg_l=q)
    g0 = float(p.external_makeup_ml) / max(float(p.evaporation_ml), 1e-12)
    return bl["E_total"] * g0


# ----------------------------------------------------------------- LHS
def lhs(n: int, k: int) -> np.ndarray:
    """简单拉丁超立方: 每维分层后随机置换 (返回 n×k 单位超立方).

    清理轮 2026-10-14 (E-4): 与 `A10_敏感性与边界/T11_uncertainty.lhs(n, k, rng)`
    是同名但**已分叉**的两个实现 (本处用模块级 RNG, 不接受 rng 参数)。
    故意不统一: 统一会改变本文件抽样序列并变动冻结产物 T9_summary.json。
    """
    u = np.empty((n, k))
    for j in range(k):
        u[:, j] = (RNG.permutation(n) + RNG.random(n)) / n
    return u


def solve_city(bl, panel_name, sample, q, m0, cache, pool, gap, dp,
               ai_target, inc_claim=0.0):
    """真实模块求解一个城市情景.

    pool  : 城市再生水池规模 (基线由既有用户完全占用, = B2 中既有用户再生水量)
    gap   : 既有用户未满足的可回用需求 (其被认定的追加权利上限)
    dp    : 新增回用产能 (专用增量, 不占用既有池)
    inc_claim: 既有用户在该池中的既得权利 (默认 0 = 与 AI 竞争同一池)
    """
    ev_ai, ev_inc = make_evaluators(bl, panel_name, q, ai_target, cache)
    reqs = [
        JointQualityRequest("AI", target_reclaimed_fraction=ai_target,
                            potable_baseline_ml=m0),
        JointQualityRequest("INC", target_reclaimed_fraction=1.0,
                            incumbent_reclaimed_ml=inc_claim,
                            max_reclaimed_ml=max(inc_claim, gap, 1e-9),
                            potable_baseline_ml=gap),
    ]
    sid = (f"{bl['domain']}|{panel_name}|{sample}|Ls|{pool:.1f}|{gap:.1f}"
           f"|{dp:.1f}|{ai_target:.3f}")
    r = solve_joint_quality_allocation(
        sid, pool + dp, reqs,
        lambda req, tr: ev_ai(req, tr) if req.consumer_id == "AI" else ev_inc(req, tr))
    ai = next(x for x in r.allocations if x.consumer_id == "AI")
    inc = next(x for x in r.allocations if x.consumer_id == "INC")
    M = float(ai.external_makeup_ml)
    x_ai = float(ai.reclaimed_allocated_ml)
    inc_recl = float(inc.reclaimed_allocated_ml)
    s_ai = (m0 - M) + x_ai
    s_city = s_ai + inc_recl - pool
    disp = max(0.0, pool - inc_recl)
    return {
        "M_ml": M, "x_ai_ml": x_ai, "inc_reclaimed_ml": inc_recl, "pool_ml": pool,
        "displacement_ml": disp, "S_AI_ml": s_ai, "S_city_ml": s_city,
        "CoC_ai": float(ai.cycles_of_concentration),
        "status": r.status, "closure_residual_ml": float(r.closure_residual_ml),
        "roots": int(r.root_count),
    }


# ----------------------------------------------------------------- 主流程
def main() -> int:
    samples = load_samples()
    bls = {d: baseline(d) for d in DOMAINS}
    for d, b in bls.items():
        print(f"[city] {d}: P0={b['P0']:,.0f} ML | gap={b['gap']:,.0f} | E_total={b['E_total']:,.0f}")

    # ---- Stage 1: 物理曲线 Phi(phi) / u(phi) ----
    phi_grid = [round(i * 0.025, 3) for i in range(0, 41)]
    curves = []
    for dom, bl in bls.items():
        for pname in PANELS:
            for _, s in samples.iterrows():
                q = quality_dict(s, PANELS[pname])
                if not q:
                    continue
                m0 = m0_of(bl, pname, q)
                gc = g_curve(bl, pname, q, phi_grid)
                g0 = float(gc.loc[gc.phi == 0.0, "g"].iloc[0])
                for _, r in gc.iterrows():
                    Phi = float(r.g) / g0
                    curves.append({
                        "domain": dom, "panel": pname, "sample": s["sample"],
                        "phi": float(r.phi), "CoC": float(r.CoC),
                        "Phi": Phi, "u": 1.0 - 1.0 / Phi,
                        "delta_star": ((1.0 - 1.0 / Phi) / float(r.phi))
                                      if r.phi > 1e-9 else np.nan,
                        "dP_star_ml": m0 * (Phi - 1.0),
                        "M0_ml": m0, "status": str(r.status),
                    })
    cv = pd.DataFrame(curves)
    cv.to_csv(HERE / "T9_phi_curves.csv", index=False, encoding="utf-8-sig")
    print(f"[Stage1] Phi/u 曲线 {len(cv)} 点 | "
          f"Phi 范围 {cv.Phi.min():.3f}–{cv.Phi.max():.3f}")

    # ---- Stage 1b: E 无关性 (容量不变性, 无需引擎循环) ----
    e_check = []
    for pname in PANELS:
        q = quality_dict(samples.iloc[0], PANELS[pname])
        for cap in (250.0, 500.0, 1000.0, 2000.0, 4000.0):
            comp = copy.deepcopy(bls["ha"]["proj"]["components"]["AI_DC1"])
            comp["installed_it_capacity_mw"] = cap
            comp["cooling"]["coc_mode"] = "quality_limited"
            comp["cooling"]["water_quality_limits"] = dict(PANELS[pname])
            comp["water_sources"]["reclaimed"]["target_fraction"] = 0.7
            comp["water_sources"]["potable"]["target_fraction"] = 0.3
            pq = dict(comp["water_sources"]["potable"].get("quality", {}))
            if pname == "B_full":
                for k_, v_ in POTABLE_EXTRA.items():
                    pq.setdefault(k_, v_)
            comp["water_sources"]["potable"]["quality"] = pq
            p = calculate_data_center_plan(comp, bls["ha"]["date_rep"],
                                           bls["ha"]["drivers_rep"],
                                           reclaimed_available_ml=1e9,
                                           reclaimed_quality_mg_l=q)
            e_check.append({"panel": pname, "it_capacity_mw": cap,
                            "CoC": float(p.cycles_of_concentration),
                            "g_ratio": float(p.external_makeup_ml) / max(float(p.evaporation_ml), 1e-12),
                            "evaporation_ml_day": float(p.evaporation_ml)})
    ec = pd.DataFrame(e_check)
    ec.to_csv(HERE / "T9_capacity_invariance.csv", index=False, encoding="utf-8-sig")
    print("[Stage1b] 容量不变性 (g_ratio 应跨 16x 容量恒定):")
    print(ec.pivot_table(index="it_capacity_mw", columns="panel",
                         values="g_ratio").round(8).to_string())

    # ---- Stage 2: LHS 城市空间填充 + 真实求解 ----
    n = 240
    U = lhs(n, 6)
    # 维度: 0 池规模倍数, 1 缺口规模倍数, 2 扩容倍数, 3 AI 目标掺混, 4 水样, 5 城市
    pool_s = 0.3 * (4.0 / 0.3) ** U[:, 0]      # 0.3 – 4.0
    gap_s = 0.3 * (4.0 / 0.3) ** U[:, 1]
    dp_s = 0.0 + 3.0 * U[:, 2]                 # 0 – 3 x P0
    ai_t = 0.10 + 0.85 * U[:, 3]               # 0.10 – 0.95
    samp_i = np.minimum((U[:, 4] * len(samples)).astype(int), len(samples) - 1)
    dom_i = (U[:, 5] > 0.5).astype(int)

    rows = []
    caches: dict = {}
    for k in range(n):
        dom = DOMAINS[dom_i[k]]
        bl = bls[dom]
        s = samples.iloc[samp_i[k]]
        for pname in PANELS:
            q = quality_dict(s, PANELS[pname])
            if not q:
                continue
            m0 = m0_of(bl, pname, q)
            pool = bl["P0"] * pool_s[k]
            gapv = bl["gap"] * gap_s[k]
            dp = bl["P0"] * dp_s[k]
            ck = (dom, pname, s["sample"])
            cache = caches.setdefault(ck, {})
            # Ls: 既有用户主张 0 (与 AI 竞争同一池)
            res = solve_city(bl, pname, s["sample"], q, m0, cache,
                             pool=pool, gap=gapv, dp=dp, ai_target=float(ai_t[k]))
            M = res["M_ml"]
            phi_eff = res["x_ai_ml"] / M if M > 1e-9 else 0.0
            Phi = M / m0 if m0 > 1e-9 else np.nan
            u = 1.0 - 1.0 / Phi if Phi else np.nan
            x_ai = res["x_ai_ml"]
            # delta := 1 - (池 - 既有用户实得)/AI再生水量
            # 注意(审计 A1): 该定义**即为**使 y = Phi*(w-u) 恒成立而设;
            # delta 是分配结果量, 不是外生参数. 其可预测性由 T9b 检验.
            delta = (1.0 - (res["pool_ml"] - res["inc_reclaimed_ml"]) / x_ai) \
                if x_ai > 1e-9 else np.nan
            w = phi_eff * delta if np.isfinite(delta) else np.nan
            y_num = res["S_city_ml"] / m0 if m0 > 1e-9 else np.nan
            y_pred = Phi * (w - u) if np.isfinite(w) else np.nan
            rows.append({
                "domain": dom, "panel": pname, "sample": s["sample"],
                "pool_scale": pool_s[k], "gap_scale": gap_s[k], "dp_scale": dp_s[k],
                "ai_target": float(ai_t[k]),
                "m0_ml": m0, "pool_ml": res["pool_ml"], "dp_ml": dp,
                "M_ml": M, "x_ai_ml": x_ai, "displacement_ml": res["displacement_ml"],
                "phi_eff": phi_eff, "Phi": Phi, "u": u, "delta": delta, "w": w,
                "CoC_ai": res["CoC_ai"],
                "y_num": y_num, "y_pred": y_pred,
                "collapse_residual": (y_num - y_pred) if np.isfinite(y_pred) else np.nan,
                "S_city_ml": res["S_city_ml"], "S_AI_ml": res["S_AI_ml"],
                "status": res["status"], "closure_residual_ml": res["closure_residual_ml"],
                "roots": res["roots"],
                # 未折叠的朴素坐标 (对照): 扩容相对量
                "naive_coord": dp / bl["P0"] if bl["P0"] else np.nan,
            })
    cdf = pd.DataFrame(rows)
    cdf.to_csv(HERE / "T9_collapse_points.csv", index=False, encoding="utf-8-sig")

    ok = cdf[np.isfinite(cdf.y_pred) & np.isfinite(cdf.y_num)].copy()
    resid = (ok.y_num - ok.y_pred)
    denom = ok.y_num.abs().clip(lower=1e-6)

    # 散度对照限定在物理可行域 (质量惩罚 <= 2x, 即 Phi <= 2):
    # 极端苦咸水掺混时 CoC->1 使 M 发散, 会以数值噪声淹没散度指标.
    disp_mask = ok.Phi <= 2.0
    dz = ok[disp_mask]

    # 散度指标: 固定坐标分箱内 y 的方差 (按样本数加权)
    def binned_dispersion(x, y, nb=12):
        x = np.asarray(x); y = np.asarray(y)
        qs = np.unique(np.quantile(x, np.linspace(0, 1, nb + 1)))
        tot, cnt = 0.0, 0
        for i in range(len(qs) - 1):
            m = (x >= qs[i]) & (x < qs[i + 1])
            if m.sum() >= 3:
                tot += float(np.var(y[m]) * m.sum()); cnt += int(m.sum())
        return tot / max(cnt, 1)

    disp_collapsed = binned_dispersion(dz.w, dz.y_num)
    disp_naive = binned_dispersion(dz.naive_coord, dz.y_num)
    disp_phi = binned_dispersion(dz.phi_eff, dz.y_num)

    summary = {
        "n_lhs_cities": int(n), "n_scenarios": int(len(cdf)),
        "n_valid": int(len(ok)),
        "statuses": sorted(cdf.status.unique().tolist()),
        "roots": sorted(int(x) for x in cdf.roots.unique()),
        "closure_residual_max_ml": float(cdf.closure_residual_ml.abs().max()),
        "collapse_residual_max_abs": float(resid.abs().max()),
        "collapse_residual_max_rel": float((resid.abs() / denom).max()),
        "collapse_R2": float(1.0 - np.var(resid) / np.var(ok.y_num)),
        "dispersion_at_w": disp_collapsed,
        "dispersion_at_naive_dp": disp_naive,
        "dispersion_at_phi": disp_phi,
        "dispersion_n_physical": int(len(dz)),
        "dispersion_excluded_extreme": int(len(ok) - len(dz)),
        "variance_reduction_ratio": float(disp_naive / disp_collapsed) if disp_collapsed else np.nan,
        "Phi_le2_share": float((cdf.Phi <= 2.0).mean()),
        "Phi_range": [float(cdf.Phi.min()), float(cdf.Phi.max())],
        "phi_eff_range": [float(cdf.phi_eff.min()), float(cdf.phi_eff.max())],
        "delta_range": [float(cdf.delta.min()), float(cdf.delta.max())],
        "y_range": [float(ok.y_num.min()), float(ok.y_num.max())],
        "collapse_status": "algebraic_identity (audit A1): residual ~ machine precision is "
                           "mathematically necessary and is NOT a transferability finding",
        "diagnostic_residual_below_1e6": bool(float(resid.abs().max()) < 1e-6),
        "diagnostic_dispersion_ratio_gt3": bool(disp_naive > 3 * disp_collapsed),
        "transferability_tested_in": "T9b (delta exogenous prediction)",
    }
    (HERE / "T9_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"\n[Stage2] LHS {n} 城市 × {len(PANELS)} 面板 = {len(cdf)} 情景")
    print(f"  状态={summary['statuses']} | 根数={summary['roots']} | "
          f"闭合残差 max={summary['closure_residual_max_ml']:.2e} ML")
    print(f"  折叠残差 max|Δ|={summary['collapse_residual_max_abs']:.2e} "
          f"(相对 {summary['collapse_residual_max_rel']:.2e}) | R2={summary['collapse_R2']:.6f}")
    print(f"  散度: @w={disp_collapsed:.3e}  @dp/P0={disp_naive:.3e}  @phi={disp_phi:.3e} "
          f"| 降维比={summary['variance_reduction_ratio']:.2f}x")
    print("  折叠定位: 代数化简 (审计 A1) — 机器精度残差为数学必然, 不作 Gate 声明")
    print(f"\n  Phi ∈ [{summary['Phi_range'][0]:.3f}, {summary['Phi_range'][1]:.3f}] | "
          f"phi_eff ∈ [{summary['phi_eff_range'][0]:.3f}, {summary['phi_eff_range'][1]:.3f}] | "
          f"delta ∈ [{summary['delta_range'][0]:.3f}, {summary['delta_range'][1]:.3f}]")

    # ---- Stage 3: 破坏阈值 delta*(phi) 与所需新增产能 ----
    thr = cv[cv.phi > 0.02].groupby(["panel", "sample", "phi"]).agg(
        delta_star=("delta_star", "first"), dP_star_ml=("dP_star_ml", "first"),
        CoC=("CoC", "first")).reset_index()
    thr.to_csv(HERE / "T9_thresholds.csv", index=False, encoding="utf-8-sig")
    print("\n[Stage3] 破坏阈值 (B_full, phi=0.7):")
    print(thr[(thr.panel == "B_full") & (thr.phi == 0.7)]
          [["sample", "CoC", "delta_star", "dP_star_ml"]].round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
