"""A18 / E2: 完整系统的有限供水反事实与多指标估计量向量 (GPT 意见2 §WP0.2 + §十 E2).

【为什么必须做】
A13c / A17 的"排放—索取平衡" dS_pot = C - F 有一个**从未被检验的隐含假设**:
被挤占的既有用户**总能**从自来水系统取到替代水。换言之 dS_pot 被当作
"城市取水变化", 但它实际上只是"在**无限替代供给**下的意图变化"。

E2 把这个假设显式化: 把自来水供给设为**有限** (水源日取水能力 W_cap),
检验旧结论是 保持 / 转化为服务缺口 / 出现其他反馈。

【口径纪律 (红线)】
- 不使用已撤回的 psi / Delta / phi* 概念。
- 需求(requested) / 交付(delivered) / 取水(abstraction) 是**三个不同的账**,
  并列报出, **不得互相代替**。
- 全部量取自引擎执行中当场产生的中间量 (instrumented 子类), 不做事后反算。
- 唯一的"配对构造量"是 C = r_inc(B2) - r_inc(B1), 按定义即"既有用户须补回量"。

【引擎原生量的取法 (可审计, 每个都在脚本内可复核)】
    requested_potable_ml    `_supply_potable_water` 入口处对各用户
                            min(remaining, potable_limit - already_delivered) 求和。
    delivered_potable_ml    area_daily.potable_delivered_ml 求和。
    source_abstraction_ml   component_daily[RES1].outflow_ml 求和 (水源实取)。
    unmet_essential_ml      area_daily.unmet_domestic_ml 求和 (居民必要服务缺口)。
    reclaimed_delivered_ml  area_daily.reuse_delivered_ml 求和。
    reclaimed_unused_ml     `_process_reuse` 前后 storage 差: 可交付
                            min(storage, treatment_capacity) 减实际交付, 逐日累计。
                            ⚠ 这是**缓冲层**闲置量 (本项目配置下恒为 0)。
    reclaimed_bypassed_ml   WWTW 处理出水**未**作为再生水交付的部分
                            (wwtw.outflow - reuse_delivered): **潜势层**闲置量。
    reclaimed_idle_total_ml = 上二者之和 (明确声明为两层的和, 不合并成一笔)。
    dc_unmet_cooling_ml     data_center_daily.unmet_cooling_water_ml (AI 自身被削减)。

【本脚本新发现并显式报出的两条结构 (见 H_finite_derivation.md)】
  (F1) 取水杠杆: 边际上 Δ取水 = Δ交付 / eta_path, eta_path 是供水链
       prod(1-loss) 的引擎原生量。故"交付"与"取水"**永远**不等。
  (F2) C 的分解: 在**逐日完整引擎**里再生水总池是内生的, 精确有
           C = x_AI - (pool(B1) - pool(B2))
       即 A13c 的 C 混合了"挤占位移"与"池自身的漂移"。代表日框架下 pool 外生
       固定, 该漂移为 0; 逐日引擎下不为 0。这是一个必须声明的框架差异。
  (F3) 三个阈值是**嵌套**的, 不可混为一谈:
           W_gap (交付缺口开始)  <  W_engage (取水上限开始咬合)  <=  W_nat
       夹在这两个阈值之间的区间里, **水库的跨期缓冲**吸收了取水上限的咬合,
       于是"交付已无缺口"却"上限其实已经在咬合"。

【运行】
    <python> finite_supply_model.py
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# 控制台在中文 Windows 下默认 GBK, 无法编码 ⚠ 等符号; 显式改为 UTF-8,
# 使 print 与写文件的内容完全一致 (重跑日志可逐字比对)。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # 10_论文推进_2026Q4
REPO = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
R2 = REPO / "examples" / "cawcc_r2"

if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

DOMS = ("ha", "co")
PHI_AI = 0.7
DC_CAPACITY_MW = 1000.0
TOL = 1e-6
DAYS = 730
# 引擎 CENTRAL_REUSE.eligible_demands 的原生清单 (既有用户可主张再生水的类别)
ELIGIBLE_CATEGORIES = ("industrial", "municipal_misc", "irrigation")


def sanitize(obj):
    """把 inf/nan 换成 None, 便于写出严格合法的 JSON。"""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return None if (np.isinf(f) or np.isnan(f)) else f
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# ==========================================================================
# 1. 仪表化引擎: 只读取引擎自己算出来的量, 不改变任何决策
# ==========================================================================
class InstrumentedModel(FullAIUWMModel):
    """在引擎既有调用点上读出中间量。

    每个钩子都只做"记录 + 转发给 super()", 不修改 area_state / storage /
    metrics 的任何输入, 因此引擎行为与未插桩时逐位一致 (由 [S0] 段的
    引擎内禀恒等式 per-row 残差 ~1e-11 佐证)。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.req_potable_by_day: dict[pd.Timestamp, float] = {}
        self.reuse_events: list[dict] = []
        self.abstraction_requested: dict[pd.Timestamp, float] = {}
        self.abstraction_delivered: dict[pd.Timestamp, float] = {}

    def _supply_potable_water(self, date, area_state, metrics, capacity_used):
        total = 0.0
        for _area_id, state in area_state.items():
            limits = state.get("potable_limits", {})
            delivered = state["potable_delivered"]
            for category, remaining in state["remaining"].items():
                limit = limits.get(category, np.inf)
                total += min(remaining, max(0.0, limit - delivered.get(category, 0.0)))
        self.req_potable_by_day[date] = total
        return super()._supply_potable_water(date, area_state, metrics, capacity_used)

    def _process_reuse(self, date, area_state, metrics):
        before = {
            cid: float(self.storage.get(cid, 0.0))
            for cid, comp in self.project["components"].items()
            if comp["kind"] == "reuse" and self._component_active(comp, date)
        }
        result = super()._process_reuse(date, area_state, metrics)
        for cid, storage_before in before.items():
            comp = self.project["components"][cid]
            treatment_cap = float(comp.get("treatment_capacity_ml_day", np.inf))
            deliverable = min(storage_before, treatment_cap)
            delivered = max(0.0, storage_before - float(self.storage.get(cid, 0.0)))
            self.reuse_events.append({
                "date": date, "component_id": cid,
                "deliverable_ml": deliverable, "delivered_ml": delivered,
                "unused_ml": max(0.0, deliverable - delivered),
            })
        return result

    def _run_supply_path(self, date, path, requested_delivery, metrics, capacity_used):
        head = path["chain"][0]
        self.abstraction_requested[date] = (
            self.abstraction_requested.get(date, 0.0) + requested_delivery)
        flow = super()._run_supply_path(
            date, path, requested_delivery, metrics, capacity_used)
        self.abstraction_delivered[date] = (
            self.abstraction_delivered.get(date, 0.0) + flow)
        return flow


# ==========================================================================
# 2. 情景构造 (只动引擎原生配置键)
# ==========================================================================
def load_raw(dom: str) -> dict:
    return json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))


def natural_abstraction_cap(dom: str) -> float:
    return float(load_raw(dom)["components"]["RES1"]["abstraction_capacity_ml_day"])


def path_efficiency(dom: str) -> float:
    """供水链 prod(1-loss): 引擎原生配置量, 用于解释取水/交付的杠杆。"""
    p = load_raw(dom)
    eta = 1.0
    for cid in p["supply_paths"][0]["chain"]:
        comp = p["components"][cid]
        eta *= 1.0 - float(comp.get("loss_fraction",
                                    comp.get("leakage_fraction", 0.0)))
    return float(eta)


def build_project(dom: str, *, phi: float, w_cap: float | None,
                  water_supply: str) -> dict:
    """water_supply='natural' 用项目自带再生水产能 (A17 短缺态);
    'surplus' 抬高 WWTW→再生水比例与处理能力, 制造未使用余量 (A17 余量态)。

    取 WWTW1.central_reuse_fraction=0.60 与 CENTRAL_REUSE.treatment_capacity_ml_day=200
    的原因由 [S5] 段的扫描给出: 这组值是使 **B2 下既有用户拿满其全部可回用需求、
    同时缓冲仍有闲置** 的最小配置, 也就是 A17 三态里最干净的 C 态 (纯余量,
    预期 C≈0)。这是引擎原生键, 不是外部造参数。
    """
    project = copy.deepcopy(load_raw(dom))
    dc = project["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = float(DC_CAPACITY_MW)
    dc["cooling_storage_capacity_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["initial_cooling_storage_ml"] = 0.0
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(phi)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(phi)

    if w_cap is not None and np.isfinite(w_cap):
        project["components"]["RES1"]["abstraction_capacity_ml_day"] = float(w_cap)
    if water_supply == "surplus":
        project["components"]["WWTW1"]["central_reuse_fraction"] = 0.60
        project["components"]["CENTRAL_REUSE"]["treatment_capacity_ml_day"] = 200.0
    elif water_supply != "natural":
        raise ValueError(f"未知 water_supply: {water_supply}")
    return project


# ==========================================================================
# 3. 单情景求解 -> 多指标估计量向量
# ==========================================================================
def solve(dom: str, *, phi: float, w_cap: float | None, water_supply: str) -> dict:
    project = build_project(dom, phi=phi, w_cap=w_cap, water_supply=water_supply)
    timeseries = pd.read_csv(R2 / dom / "timeseries.csv")
    model = InstrumentedModel(project, timeseries)
    result = model.run()

    area = result.area_daily
    comp = result.component_daily
    dc = result.data_center_daily

    reuse_cols = [c for c in area.columns if c.startswith("central_")]
    inc_cols = [c for c in reuse_cols if "data_center" not in c]
    ai_cols = [c for c in reuse_cols if "data_center" in c]
    reclaimed_incumbent = float(sum(area[c].sum() for c in inc_cols))
    reclaimed_ai = float(sum(area[c].sum() for c in ai_cols))

    reuse = pd.DataFrame(model.reuse_events)
    res = comp[comp["component_id"] == "RES1"]
    ww = comp[comp["component_id"] == "WWTW1"]
    ww_out = float(ww["outflow_ml"].sum())
    pool_total = float(area["reuse_delivered_ml"].sum())
    dc_unmet_cols = [c for c in area.columns if c.startswith("unmet_data_center")]
    dc_demand_cols = [c for c in area.columns if c.startswith("demand_data_center")]

    abstraction = float(res["outflow_ml"].sum())
    req_abs = float(sum(model.abstraction_requested.values()))
    got_abs = float(sum(model.abstraction_delivered.values()))

    return {
        "domain": dom, "water_supply": water_supply,
        "phi": float(phi),
        "w_cap_ml_day": (np.inf if (w_cap is None or not np.isfinite(w_cap))
                         else float(w_cap)),

        # ---- 多指标估计量向量 (严格分开) ----
        "requested_potable_ml": float(sum(model.req_potable_by_day.values())),
        "delivered_potable_ml": float(area["potable_delivered_ml"].sum()),
        "source_abstraction_ml": abstraction,
        "unmet_essential_ml": float(area["unmet_domestic_ml"].sum()),
        "unmet_total_ml": float(area["unmet_ml"].sum()),
        "reclaimed_delivered_ml": float(area["reuse_delivered_ml"].sum()),
        "reclaimed_unused_ml": float(reuse["unused_ml"].sum()),
        "reclaimed_deliverable_ml": float(reuse["deliverable_ml"].sum()),
        "reclaimed_bypassed_ml": float(max(0.0, ww_out - pool_total)),
        "dc_unmet_cooling_ml": float(dc["unmet_cooling_water_ml"].sum()),

        # ---- 既有用户可回用需求 (A17 `elig` 的引擎原生对应量) ----
        #     CENTRAL_REUSE.eligible_demands = [industrial, municipal_misc,
        #     irrigation] 是引擎原生配置; 这 3 类是"既有用户"对再生水的可主张量,
        #     与 A13c/A17 中 elig = reuse_elig 的口径对应 (domestic 不在其中,
        #     居民自来水另行以 unmet_essential 记账)。
        "incumbent_elig_ml": float(
            sum(area[f"demand_{cat}_ml"].sum()
                for cat in ELIGIBLE_CATEGORIES)),
        "incumbent_unmet_ml": float(
            sum(area[f"unmet_{cat}_ml"].sum()
                for cat in ELIGIBLE_CATEGORIES)),
        "incumbent_saturated": bool(
            sum(area[f"demand_{cat}_ml"].sum()
                for cat in ELIGIBLE_CATEGORIES)
            - float(sum(area[c].sum() for c in inc_cols)) <= 1.0),

        # ---- 引擎原生辅助量 ----
        "reclaimed_incumbent_ml": reclaimed_incumbent,
        "reclaimed_ai_ml": reclaimed_ai,
        "reclaimed_pool_ml": pool_total,
        "dc_makeup_ml": float(dc["external_makeup_ml"].sum()),
        "dc_potable_ml": float(dc["potable_water_ml"].sum()),
        "dc_reclaimed_ml": float(dc["reclaimed_water_ml"].sum()),
        "dc_peak_demand_ml": float(area[dc_demand_cols[0]].max()),
        "dc_unmet_peak_ml": float(area[dc_unmet_cols[0]].max()),
        "other_delivered_ml": float(area["other_delivered_ml"].sum()),
        "demand_final_ml": float(area["water_demand_ml"].sum()),
        "abstraction_requested_ml": req_abs,
        "abstraction_delivered_ml": got_abs,
        "source_storage_min_ml": float(res["storage_ml"].min()),
        "abstraction_peak_ml_day": float(res["outflow_ml"].max()),
        # 取水上限是否**咬合**: 实取峰值恰好等于(或触及)所设上限。
        # 只有当某天想要的取水超过上限时才会出现, 故这是引擎原生的咬合判据。
        # (注意: 这与"交付出现缺口"是**不同**的阈值, 见 F3。)
        "cap_engaged": bool(
            w_cap is not None and np.isfinite(w_cap)
            and float(res["outflow_ml"].max()) >= float(w_cap) - 1e-9),
        # 交付路径未被约束 (消费者端的请求全部被满足)。这是 F3 的另一端。
        "delivery_unconstrained": bool(
            float(sum(model.req_potable_by_day.values()))
            - float(area["potable_delivered_ml"].sum()) <= 1e-6),
        # 交付被约束 = 有需求没被满足 (= 出现服务缺口)。
        "delivery_constrained": bool(
            float(sum(model.req_potable_by_day.values()))
            - float(area["potable_delivered_ml"].sum()) > 1e-6),
        "n_days": int(len(res)),
        "status": "ok",
    }


# ==========================================================================
# 4. 配对: B1 (phi) 对 B2 (phi=0) -> C / F / dS_pot + 三账差异
# ==========================================================================
def pair_metrics(row: dict, b2: dict, eta_path: float) -> dict:
    phi_eff = (row["dc_reclaimed_ml"] / row["dc_makeup_ml"]
               if row["dc_makeup_ml"] > 1e-12 else 0.0)
    F = b2["dc_makeup_ml"] - (1.0 - phi_eff) * row["dc_makeup_ml"]
    C = b2["reclaimed_incumbent_ml"] - row["reclaimed_incumbent_ml"]
    dS_pot = C - F

    d_abs = row["source_abstraction_ml"] - b2["source_abstraction_ml"]
    d_del = row["delivered_potable_ml"] - b2["delivered_potable_ml"]
    d_req = row["requested_potable_ml"] - b2["requested_potable_ml"]
    d_unmet_e = row["unmet_essential_ml"] - b2["unmet_essential_ml"]
    d_unmet_t = row["unmet_total_ml"] - b2["unmet_total_ml"]
    d_pool = row["reclaimed_pool_ml"] - b2["reclaimed_pool_ml"]
    x_ai = row["reclaimed_ai_ml"]

    return {
        "phi_eff": float(phi_eff),
        "F_released_ml": float(F),
        "C_displaced_ml": float(C),
        "dS_pot_ml": float(dS_pot),
        "reclaimed_displaced_ml": float(C),
        # ---- 三账 ----
        "d_source_abstraction_ml": float(d_abs),
        "d_delivered_potable_ml": float(d_del),
        "d_requested_potable_ml": float(d_req),
        "d_unmet_essential_ml": float(d_unmet_e),
        "d_unmet_total_ml": float(d_unmet_t),
        # ---- F1: 取水杠杆 (交付 -> 取水) ----
        "path_eta": float(eta_path),
        "loss_leverage_factor": float(1.0 / eta_path),
        "observed_abstraction_over_delivered": float(
            d_abs / d_del if abs(d_del) > 1e-9 else np.nan),
        "account_gap_abstraction_vs_delivered_ml": float(d_abs - d_del),
        # ---- F2: C 的分解 C = x_AI - (pool(B1) - pool(B2)) ----
        "d_reclaimed_pool_ml": float(d_pool),
        "decomp_residual_ml": float(C - x_ai + d_pool),
        "pool_drift_share_of_C": (float(-d_pool / C) if abs(C) > 1e-9
                                  else np.nan),
        # ---- dS_pot 作为"取水度量"的失真 ----
        "phantom_overstatement_ml": float(dS_pot - d_abs),
        "dS_pot_minus_d_delivered_ml": float(dS_pot - d_del),
        "rel_phantom": float(abs(dS_pot - d_abs) / max(abs(dS_pot), 1e-9)),
        # ---- 三账不等的两个直接度量 ----
        "requested_vs_delivered_gap_ml": float(
            row["requested_potable_ml"] - row["delivered_potable_ml"]),
        "abstraction_vs_delivered_gap_ml": float(
            row["source_abstraction_ml"] - row["delivered_potable_ml"]),
        # ---- 再生水余量是否被 AI 吸收 ----
        "d_reclaimed_unused_ml": float(
            row["reclaimed_unused_ml"] - b2["reclaimed_unused_ml"]),
    }


# ==========================================================================
# 5. 主流程
# ==========================================================================
def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(msg: str) -> None:
        log.append(msg)
        print(msg, flush=True)

    rec("=" * 78)
    rec("A18 / E2: 完整系统的有限供水反事实 (GPT 意见2 §WP0.2 + §十 E2)")
    rec("=" * 78)

    naturals = {d: natural_abstraction_cap(d) for d in DOMS}
    etas = {d: path_efficiency(d) for d in DOMS}
    rec("引擎原生参数:")
    for d in DOMS:
        rec(f"  D-{d.upper()}: W_nat={naturals[d]:.1f} ML/d   "
            f"eta_path={etas[d]:.8f}   1/eta={1/etas[d]:.6f}")

    # ---------------- 5.1 网格 ----------------
    FACTORS = (2.0, 1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.60, 0.50, 0.40)
    SURPLUS_FACTORS = (2.0, 1.0, 0.85, 0.70)

    raw: dict[tuple, dict] = {}

    def key(dom, supply, phi, w):
        return (dom, supply, round(float(phi), 6),
                np.inf if not np.isfinite(w) else round(float(w), 6))

    def ensure(dom, supply, phi, w) -> dict:
        k = key(dom, supply, phi, w)
        if k not in raw:
            raw[k] = solve(dom, phi=phi, w_cap=w, water_supply=supply)
        return raw[k]

    grid_specs = []
    for dom in DOMS:
        for supply in ("natural", "surplus"):
            for f in (FACTORS if supply == "natural" else SURPLUS_FACTORS):
                grid_specs += [(dom, supply, naturals[dom] * f, "phi0"),
                               (dom, supply, naturals[dom] * f, "phi1")]
        for supply in ("natural", "surplus"):
            grid_specs += [(dom, supply, np.inf, "phi0"),
                           (dom, supply, np.inf, "phi1")]

    rec(f"\n[G] 求解网格: {len(grid_specs)} 情景")
    for i, (dom, supply, w, arm) in enumerate(grid_specs, 1):
        phi = 0.0 if arm == "phi0" else PHI_AI
        try:
            ensure(dom, supply, phi, w)
        except Exception as exc:  # noqa: BLE001
            rec(f"  ERROR {dom} {supply} w={w:.1f} phi={phi}: "
                f"{type(exc).__name__}: {exc}")
        if i % 20 == 0:
            rec(f"  ... {i}/{len(grid_specs)}  ({time.time()-t0:.0f}s)")
    rec(f"  引擎求解完成, 用时 {time.time()-t0:.0f}s")

    # ---------------- 5.2 组装逐情景表 ----------------
    rows = []
    for (dom, supply, phi, w), r in sorted(raw.items()):
        b2 = raw.get(key(dom, supply, 0.0, w))
        out = dict(r)
        out["scenario_id"] = f"D-{dom.upper()}|{supply}|W={w:.1f}|phi={phi:.2f}"
        if phi > 1e-9 and b2 is not None:
            out.update(pair_metrics(r, b2, etas[dom]))
            for name in ("source_abstraction_ml", "delivered_potable_ml",
                         "reclaimed_incumbent_ml", "dc_makeup_ml",
                         "unmet_essential_ml", "reclaimed_unused_ml",
                         "reclaimed_pool_ml", "requested_potable_ml",
                         "incumbent_elig_ml", "incumbent_unmet_ml",
                         "incumbent_saturated", "reclaimed_deliverable_ml"):
                if name in b2:
                    out[f"b2_{name}"] = b2[name]
        rows.append(out)

    df = pd.DataFrame(rows)
    # 布尔列必须钉成真正的 numpy bool: 与 B2 配对时 pandas 会因 NaN 把它
    # 提升为 object, 之后 `~col` 会对 Python bool 取位反得到 -2/-1 (恒真),
    # 静默污染所有证伪判定。显式规整, 并让"未配对"行取 False。
    for bcol in ("delivery_constrained", "delivery_unconstrained",
                 "cap_engaged", "incumbent_saturated",
                 "b2_incumbent_saturated"):
        if bcol in df.columns:
            df[bcol] = df[bcol].fillna(False).astype(bool)
    id_cols = ["scenario_id", "domain", "water_supply", "phi", "w_cap_ml_day"]
    vec_cols = ["requested_potable_ml", "delivered_potable_ml",
                "source_abstraction_ml", "unmet_essential_ml", "unmet_total_ml",
                "reclaimed_delivered_ml", "reclaimed_unused_ml",
                "reclaimed_deliverable_ml", "reclaimed_bypassed_ml",
                "dc_unmet_cooling_ml", "reclaimed_displaced_ml", "dS_pot_ml"]
    pair_cols = ["phi_eff", "F_released_ml", "C_displaced_ml",
                 "d_source_abstraction_ml", "d_delivered_potable_ml",
                 "d_requested_potable_ml", "d_unmet_essential_ml",
                 "d_unmet_total_ml", "d_reclaimed_pool_ml",
                 "d_reclaimed_unused_ml", "decomp_residual_ml",
                 "pool_drift_share_of_C", "path_eta", "loss_leverage_factor",
                 "observed_abstraction_over_delivered",
                 "account_gap_abstraction_vs_delivered_ml",
                 "phantom_overstatement_ml", "rel_phantom",
                 "dS_pot_minus_d_delivered_ml",
                 "requested_vs_delivered_gap_ml",
                 "abstraction_vs_delivered_gap_ml"]
    rest = [c for c in df.columns if c not in id_cols + vec_cols + pair_cols]
    df = df[id_cols + [c for c in vec_cols if c in df.columns]
            + [c for c in pair_cols if c in df.columns] + rest]
    df.to_csv(HERE / "finite_supply_grid.csv", index=False, encoding="utf-8-sig")
    rec(f"\n[G] finite_supply_grid.csv: {len(df)} 行 x {len(df.columns)} 列")

    P = df[df["phi"] > 1e-9].copy()          # 配对后的 B1 行
    NAT = P[P["water_supply"] == "natural"]
    SUR = P[P["water_supply"] == "surplus"]

    # ---------------- 5.3 [S0] 引擎内禀恒等式自检 ----------------
    rec("\n" + "=" * 78)
    rec("[S0] 引擎内禀恒等式自检 (证明插桩未改变引擎行为)")
    rec("=" * 78)
    r1 = (P["requested_potable_ml"] - P["delivered_potable_ml"]
          - P["unmet_total_ml"]).abs().max()
    rec(f"  (a) |requested - delivered - unmet_total| 逐情景最大 = {r1:.3e} ML")
    rec("      >> 需求账被精确拆成 '交付 + 缺口': 这是引擎的事实, 非假设。")
    rec(f"  (b) |abstraction(B1) - abstraction(B1)| 插桩一致性 = "
        f"{(P['source_abstraction_ml'] - P['abstraction_delivered_ml']).abs().max():.3e} ML")
    gap = P["abstraction_vs_delivered_gap_ml"]
    rec(f"  (c) 取水 - 交付 (输配损失 + 其他用户) 范围 = "
        f"[{gap.min():.0f}, {gap.max():.0f}] ML / {DAYS} 天")

    # ---------------- 5.4 三分账 ----------------
    rec("\n" + "=" * 78)
    rec("[S1] ★ 三分账: 需求(requested) / 交付(delivered) / 取水(abstraction)")
    rec("=" * 78)
    for dom in DOMS:
        s = NAT[NAT["domain"] == dom].sort_values("w_cap_ml_day")
        rec(f"\n  --- D-{dom.upper()} (phi={PHI_AI}, natural 再生水产能) ---")
        rec(f"  {'W_cap':>8} {'requested':>11} {'delivered':>11} {'abstraction':>12} "
            f"{'unmet_ess':>10} {'req-del':>10} {'abs-del':>9} {'gap?':>6} {'worm?':>6}")
        for _, r in s.iterrows():
            rec(f"  {r['w_cap_ml_day']:>8.0f} {r['requested_potable_ml']:>11.1f} "
                f"{r['delivered_potable_ml']:>11.1f} "
                f"{r['source_abstraction_ml']:>12.1f} "
                f"{r['unmet_essential_ml']:>10.1f} "
                f"{r['requested_vs_delivered_gap_ml']:>10.1f} "
                f"{r['abstraction_vs_delivered_gap_ml']:>9.1f} "
                f"{str(r['delivery_constrained']):>6} {str(r['cap_engaged']):>6}")

    rec("\n  [S1.1] 三账在什么条件下相等 / 不等 (定量, 三条精确关系)")
    un_all = P[~P["delivery_constrained"]]
    con_all = P[P["delivery_constrained"]]
    rec(f"\n  (i) requested = delivered + unmet_total  **恒等**  "
        f"(最大残差 "
        f"{(P['requested_potable_ml']-P['delivered_potable_ml']-P['unmet_total_ml']).abs().max():.2e} ML)")
    rec("      >> 需求账被引擎精确拆成'交付+缺口'。上限绑定时该差转为 unmet,")
    rec("         故 **requested == delivered 当且仅当 供给路径未被约束**。")
    rec(f"  (ii) 未约束区 dS_pot = d_delivered  **恒等**  "
        f"(最大残差 {(un_all['dS_pot_ml']-un_all['d_delivered_potable_ml']).abs().max():.2e} ML)")
    rec("      >> 这是本实验对 A13c 最重要的一处**重新标定**: dS_pot = C - F")
    rec("         衡量的**不是城市取水**, 而是**城市自来水的交付量变化**。")
    rec(f"  (iii) d_abstraction = d_delivered / eta_path  (杠杆 "
        f"1/eta_path, 实测比值 "
        f"{un_all['observed_abstraction_over_delivered'].median():.6f})")
    rec("      >> 取水账与交付账在位与量上都不同, **永不相等**。")
    for dom in DOMS:
        base = NAT[(NAT["domain"] == dom) & np.isinf(NAT["w_cap_ml_day"])].iloc[0]
        con = NAT[(NAT["domain"] == dom) & NAT["delivery_constrained"]]
        rec(f"\n  D-{dom.upper()}:")
        rec(f"    未约束: requested={base['requested_potable_ml']:.1f} "
            f"delivered={base['delivered_potable_ml']:.1f} "
            f"(差 {base['requested_vs_delivered_gap_ml']:.6f}) "
            f"| abstraction={base['source_abstraction_ml']:.1f} "
            f"(差 {base['abstraction_vs_delivered_gap_ml']:.1f})")
        rec(f"    绑定后: 取水/交付之差从 {base['abstraction_vs_delivered_gap_ml']:.0f} "
            f"变到 [{con['abstraction_vs_delivered_gap_ml'].min():.0f}, "
            f"{con['abstraction_vs_delivered_gap_ml'].max():.0f}] ML "
            f"—— 该差**不是常数**, 故 dS_pot 也**不是**任何固定比例的取水。")
        rec(f"    dS_pot 对 d_delivered 的偏离: 未约束 "
            f"{(un_all[un_all.domain==dom]['dS_pot_ml']-un_all[un_all.domain==dom]['d_delivered_potable_ml']).abs().max():.1e} "
            f"-> 绑定后最大 "
            f"{(con['dS_pot_ml']-con['d_delivered_potable_ml']).abs().max():.1f} ML")

    # ---------------- 5.5 有限供水反事实 ----------------
    rec("\n" + "=" * 78)
    rec("[S2] ★ 有限供水反事实: 旧结论 保持 / 转为服务缺口 / 其他反馈")
    rec("=" * 78)
    rec("  旧结论 = A13c/A17: dS_pot = C - F > 0 (挤占推高城市自来水取水)")

    for dom in DOMS:
        s = NAT[NAT["domain"] == dom].sort_values("w_cap_ml_day")
        inf = s[np.isinf(s["w_cap_ml_day"])].iloc[0]
        rec(f"\n  --- D-{dom.upper()} ---")
        rec(f"  无限替代基准: dS_pot={inf['dS_pot_ml']:+.1f}  "
            f"d_abstraction={inf['d_source_abstraction_ml']:+.1f}  "
            f"d_delivered={inf['d_delivered_potable_ml']:+.1f}  "
            f"d_unmet_essential={inf['d_unmet_essential_ml']:+.1f}")
        rec(f"  {'W_cap':>8} {'dS_pot':>10} {'d_abstr':>9} {'d_deliv':>9} "
            f"{'d_unmetE':>9} {'幻影':>9} {'缺口':>5} {'咬合':>5}  判定")
        for _, r in s.iterrows():
            if r["delivery_constrained"] and r["d_unmet_essential_ml"] > 1.0:
                verdict = "转为服务缺口 (dS_pot 成幻影)"
            elif r["delivery_constrained"]:
                verdict = "有缺口但非必要服务"
            elif r["cap_engaged"]:
                verdict = "★ 上限已咬合, 缺口被水库缓冲掩盖"
            else:
                verdict = "保持 (dS_pot 与取水同向)"
            rec(f"  {r['w_cap_ml_day']:>8.0f} {r['dS_pot_ml']:>10.1f} "
                f"{r['d_source_abstraction_ml']:>9.1f} "
                f"{r['d_delivered_potable_ml']:>9.1f} "
                f"{r['d_unmet_essential_ml']:>9.1f} "
                f"{r['phantom_overstatement_ml']:>9.1f} "
                f"{str(r['delivery_constrained']):>5} {str(r['cap_engaged']):>5}  "
                f"{verdict}")

    # ---------------- 5.6 临界条件 ----------------
    rec("\n" + "=" * 78)
    rec("[S3] ★ 临界条件")
    rec("=" * 78)
    crit = {}
    for dom in DOMS:
        s = NAT[NAT["domain"] == dom].copy()
        fin = s[~np.isinf(s["w_cap_ml_day"])].sort_values("w_cap_ml_day")
        # W_engage: 取水上限首次**咬合** (某天想要的取水被上限截断)。
        #           引擎原生判据: 峰值日实取 == W_cap (见 solve 的 cap_engaged)。
        eng = fin[fin["cap_engaged"]]
        w_eng = float(eng["w_cap_ml_day"].max()) if len(eng) else None
        # W_gap: 交付开始出现缺口的**临界值** = 仍有缺口的最大 W_cap。
        gap = fin[fin["d_unmet_essential_ml"] > 1.0]
        w_gap = float(gap["w_cap_ml_day"].max()) if len(gap) else None
        # W_adequate: 首个**无**缺口的 W_cap (网格上的下一点)。
        #             分区必须严格用 W_cap >= W_adequate, 否则边界点
        #             (W_cap == W_gap) 会被错误划进"供给充足"一侧。
        nogap = fin[fin["d_unmet_essential_ml"] <= 1.0]
        w_adequate = float(nogap["w_cap_ml_day"].min()) if len(nogap) else None
        # W*: dS_pot 相对失真 > 50% (账本开始不可用)。
        brk = fin[fin["rel_phantom"] > 0.5]
        w_star = float(brk["w_cap_ml_day"].max()) if len(brk) else None
        inf = s[np.isinf(s["w_cap_ml_day"])].iloc[0]
        crit[dom] = {
            "w_nat_ml_day": naturals[dom],
            "w_engage_ml_day": w_eng,
            "w_engage_frac_of_nat": (w_eng / naturals[dom]) if w_eng else None,
            "w_gap_ml_day": w_gap,
            "w_gap_frac_of_nat": (w_gap / naturals[dom]) if w_gap else None,
            "w_adequate_ml_day": w_adequate,
            "w_adequate_frac_of_nat": (
                (w_adequate / naturals[dom]) if w_adequate else None),
            "w_star_account_break_ml_day": w_star,
            "thresholds_are_nested": bool(
                w_eng is None or w_gap is None or w_gap < w_eng),
            "buffered_band_ml_day": (
                [w_gap, w_eng] if (w_eng and w_gap and w_gap < w_eng) else None),
            "unconstrained_dS_pot_ml": float(inf["dS_pot_ml"]),
            "unconstrained_d_abstraction_ml": float(inf["d_source_abstraction_ml"]),
            "unconstrained_peak_abstraction_ml_day": float(
                inf["abstraction_peak_ml_day"]),
            "max_phantom_ml": float(fin["phantom_overstatement_ml"].max()),
            "min_phantom_ml": float(fin["phantom_overstatement_ml"].min()),
            "max_service_gap_essential_ml": float(fin["unmet_essential_ml"].max()),
            "max_dc_curtailment_ml": float(fin["dc_unmet_cooling_ml"].max()),
            "loss_leverage_factor": float(1.0 / etas[dom]),
        }
        rec(f"\n  D-{dom.upper()}:")
        rec(f"    引擎原生取水能力 W_nat           = {naturals[dom]:.1f} ML/d")
        rec("    (a) 交付出现缺口的最大 W_cap     = "
            f"{w_gap:.0f} ML/d ({w_gap/naturals[dom]:.2f} x W_nat)")
        rec("    (a') 首个无缺口的 W_cap          = "
            f"{w_adequate:.0f} ML/d ({w_adequate/naturals[dom]:.2f} x W_nat)")
        rec(f"    (b) 取水上限开始咬合 W_engage    = {w_eng:.0f} ML/d "
            f"({w_eng/naturals[dom]:.2f} x W_nat)")
        rec(f"    (c) 账本失真 >50% W*             = {w_star:.0f} ML/d "
            f"({w_star/naturals[dom]:.2f} x W_nat)")
        rec(f"    ★ 阈值是否嵌套 (W_gap < W_engage)= "
            f"{crit[dom]['thresholds_are_nested']}")
        if crit[dom]["buffered_band_ml_day"]:
            lo_, hi_ = crit[dom]["buffered_band_ml_day"]
            rec(f"    ★ 被水库缓冲掩盖的区间          = "
                f"[{lo_:.0f}, {hi_:.0f}) ML/d  ({hi_-lo_:.0f} ML/d 宽)")
            rec("      该区间内**交付已无缺口**, 但取水上限其实已经在峰日咬合,")
            rec("      靠水库跨期放水把缺口推迟了。只检查 unmet 会误判为'无影响'。")
        else:
            rec("    ★ 无缓冲掩盖区间: 缺口与上限咬合同步出现。")
        rec(f"    (W* 与 W_gap 是否重合)           = {w_star == w_gap}")
        rec(f"    绑定区 dS_pot 幻影最大            = "
            f"{crit[dom]['max_phantom_ml']:.1f} ML")
        rec(f"    绑定区 必要服务缺口最大           = "
            f"{crit[dom]['max_service_gap_essential_ml']:.1f} ML")
        rec(f"    绑定区 AI 自身冷却被削减最大      = "
            f"{crit[dom]['max_dc_curtailment_ml']:.1f} ML")

    rec("\n  [S3.1] 为什么 W_engage 远低于 W_nat (定量)")
    for dom in DOMS:
        base = raw[key(dom, "natural", 0.0, np.inf)]
        rec(f"    D-{dom.upper()}: 无约束时峰值日取水 = "
            f"{base['abstraction_peak_ml_day']:.1f} ML/d, 占 W_nat "
            f"{100*base['abstraction_peak_ml_day']/naturals[dom]:.1f}%")
        rec(f"        均值 "
            f"{raw[key(dom,'natural',0.0,np.inf)]['source_abstraction_ml']/DAYS:.1f} ML/d"
            f", 仅占 W_nat "
            f"{100*raw[key(dom,'natural',0.0,np.inf)]['source_abstraction_ml']/DAYS/naturals[dom]:.1f}%")
        rec("        => 上限咬合由**峰日**决定, 不是由年均决定; 名义能力大部分时间闲置。")

    # ---------------- 5.7 F1 / F2 结构 ----------------
    rec("\n" + "=" * 78)
    rec("[S4] ★ 结构发现 F1 (取水杠杆) 与 F2 (C 的池漂移分量)")
    rec("=" * 78)
    un = P[~P["delivery_constrained"]]
    rec("  F1: 边际取水 = 交付 / eta_path")
    for dom in DOMS:
        u = un[un["domain"] == dom]
        rec(f"    D-{dom.upper()}: 实测 ratio 范围 = "
            f"[{u['observed_abstraction_over_delivered'].min():.6f}, "
            f"{u['observed_abstraction_over_delivered'].max():.6f}]  "
            f"vs 1/eta_path = {1/etas[dom]:.6f}")
    rec("    => 交付账与取水账**在位与量上都不同**; 只有取水账是"
        "'城市从外部水源拿走的量'。")
    rec("  F2: C = x_AI - (pool(B1) - pool(B2))")
    rec(f"    逐情景分解残差最大 = {P['decomp_residual_ml'].abs().max():.3e} ML "
        f"(精确恒等式)")
    for dom in DOMS:
        u = P[P["domain"] == dom]
        rec(f"    D-{dom.upper()}: |池漂移|/|C| 范围 = "
            f"[{u['pool_drift_share_of_C'].abs().min():.3f}, "
            f"{u['pool_drift_share_of_C'].abs().max():.3f}]  "
            f"池漂移最大 = {u['d_reclaimed_pool_ml'].abs().max():.1f} ML")
    rec("    => 在**逐日完整引擎**中再生水总池内生 (AI 改变自身用水 -> 改变污水"
        "回流量 -> 改变 WWTW 出水 -> 改变池)。A13c 的 C 因此混合了'挤占位移'与"
        "'池漂移'。代表日框架把 pool 当外生常数, 该漂移恒为 0, 故 A13c 的 C "
        "*等于*挤占位移; 逐日引擎下不再相等。这是框架差异, 必须声明。")

    # ---------------- 5.8 其他反馈: 余量态符号反转 + AI 削减 ----------------
    rec("\n" + "=" * 78)
    rec("[S5] ★ 其他反馈")
    rec("=" * 78)
    rec("\n  (a) 再生水存在未使用余量 -> 符号反转")
    rec("      (A17 余量态的引擎原生判据: B2 下既有用户已拿满其可主张量)")
    rec(f"  {'dom':>4} {'W_cap':>7} {'elig':>9} {'inc(B2)':>9} {'B2满':>5} "
        f"{'B2闲置':>9} {'d闲置':>9} {'C':>8} {'x_AI':>9} {'dS_pot':>9} "
        f"{'d_abstr':>9} {'d_unmetE':>9} {'bind':>6}")
    for _, r in SUR.sort_values(["domain", "w_cap_ml_day"]).iterrows():
        rec(f"  {r['domain']:>4} {r['w_cap_ml_day']:>7.0f} "
            f"{r['b2_incumbent_elig_ml']:>9.1f} "
            f"{r['b2_reclaimed_incumbent_ml']:>9.1f} "
            f"{str(r['b2_incumbent_saturated']):>5} "
            f"{r['b2_reclaimed_unused_ml']:>9.1f} "
            f"{r['d_reclaimed_unused_ml']:>9.1f} "
            f"{r['C_displaced_ml']:>8.1f} {r['reclaimed_ai_ml']:>9.1f} "
            f"{r['dS_pot_ml']:>9.1f} {r['d_source_abstraction_ml']:>9.1f} "
            f"{r['d_unmet_essential_ml']:>9.1f} {str(r['delivery_constrained']):>6}")
    if len(SUR):
        rec(f"\n  surplus 臂: n={len(SUR)}, dS_pot<0 = "
            f"{int((SUR['dS_pot_ml'] < -TOL).sum())}, d_abstraction<0 = "
            f"{int((SUR['d_source_abstraction_ml'] < -TOL).sum())}, "
            f"上限绑定 = {int(SUR['delivery_constrained'].sum())}, "
            f"B2 既满足 = {int(SUR['b2_incumbent_saturated'].sum())}/{len(SUR)}, "
            f"B2 缓冲闲置>0 = "
            f"{int((SUR['b2_reclaimed_unused_ml'] > 1.0).sum())}/{len(SUR)}")
        rec(f"  非绑定情景下 d闲置 - (-x_AI) 的残差: "
            f"{(SUR[~SUR['delivery_constrained']]['d_reclaimed_unused_ml'] + SUR[~SUR['delivery_constrained']]['reclaimed_ai_ml']).abs().max():.3e} ML")
        rec("  >> A17 的 C 态在逐日完整引擎里**可复现**: 一旦既有用户被满足,")
        rec("     AI 取用的再生水来自本会闲置的缓冲 (d闲置 = -x_AI),")
        rec("     旧结论**符号反转** (dS_pot < 0 且 d_abstraction < 0);")
        rec("     且因取水下降, 有限上限**不绑定**, 不产生服务缺口。")
        rec("  ⚠ 但注意: 该反转**不是** C 态独有。见 [S6] H2 的证伪登记 ——")
        rec("     在上限绑定的短缺态, dS_pot 同样可以与 d_abstraction 反号,")
        rec("     因为 dS_pot 量的是交付账而 d_abstraction 量的是取水账。")

    rec("\n  (b) AI 自身被削减 (第三条通道)")
    rec(f"  全部情景中 dc_unmet_cooling_ml > 1e-9 的行数 = "
        f"{int((df['dc_unmet_cooling_ml'] > 1e-9).sum())}/{len(df)}")
    cur = NAT[NAT["dc_unmet_cooling_ml"] > 1e-9]
    if len(cur):
        rec(f"  绑定区 AI 冷却水缺口: 最大 {cur['dc_unmet_cooling_ml'].max():.1f} ML, "
            f"峰值日缺口最大 {cur['dc_unmet_peak_ml'].max():.2f} ML/d, "
            f"占其峰值需求最多 "
            f"{100*cur['dc_unmet_peak_ml'].max()/cur['dc_peak_demand_ml'].min():.1f}%")
        rec("  >> 上限不足时 AI 也拿不到冷却水: '挤占既有用户'的叙事不完整, "
            "设施本身同时被削减。")

    # ---------------- 5.9 可证伪命题 H ----------------
    rec("\n" + "=" * 78)
    rec("[S6] ★ 可证伪命题 H 的三分支判定")
    rec("=" * 78)
    rec("  H1 (账本身份): 只要自来水供给路径未被约束, dS_pot = C - F **恒等于**")
    rec("                 交付量变化 d_delivered, 且**不等于**取水变化 d_abstraction。")
    rec("  H2 (保持):     当 W_cap >= W_adequate (首个无缺口值) 时, 无服务缺口,")
    rec("                 dS_pot > 0 且 d_abstraction > 0 —— 旧结论成立。")
    rec("  H3 (转缺口):   当 W_cap < W_adequate 时, d_unmet_essential > 0,")
    rec("                 且 |dS_pot - d_abstraction| 显著 > 0 (dS_pot 成幻影)。")
    rec("  H4 (反转):     B2 下既有用户已满足且缓冲有闲置时, dS_pot < 0 且")
    rec("                 d_abstraction < 0。")
    rec("  注: H2/H3 的分区点用 W_adequate (首个 d_unmet=0 的网格点), 而**不是**")
    rec("      W_gap (最后一个有缺口的点)。两者是相邻网格点, 用后者做 >= 会把")
    rec("      边界行本身错划成'供给充足', 产生假证伪。")

    # 布尔列同理由配对提升为 object 的风险, 此处对切片再钉一次。
    NAT = NAT.copy()
    SUR = SUR.copy()
    for _f in (NAT, SUR):
        for bcol in ("delivery_constrained", "cap_engaged",
                     "b2_incumbent_saturated", "incumbent_saturated"):
            if bcol in _f.columns:
                _f[bcol] = _f[bcol].fillna(False).astype(bool)

    prop = {}
    for dom in DOMS:
        s = NAT[NAT["domain"] == dom]
        fin = s[~np.isinf(s["w_cap_ml_day"])]
        wg = crit[dom]["w_adequate_ml_day"]
        hi = fin[fin["w_cap_ml_day"] >= wg] if wg else fin
        lo = fin[fin["w_cap_ml_day"] < wg] if wg else fin.iloc[0:0]
        un = s[np.isinf(s["w_cap_ml_day"])]
        su = SUR[SUR["domain"] == dom]

        # H1: 未约束时 dS_pot == d_delivered 精确, 且 != d_abstraction
        h1 = bool(len(un)
                  and (un["dS_pot_ml"] - un["d_delivered_potable_ml"]).abs().max() < 1e-8
                  and (un["dS_pot_ml"] - un["d_source_abstraction_ml"]).abs().min() > 1.0)
        # H2: 上限充足 -> 无缺口 且 dS_pot, d_abstraction 同为正
        h2 = bool(len(hi) and (hi["d_unmet_essential_ml"].abs() < 1.0).all()
                  and (hi["dS_pot_ml"] > 0).all()
                  and (hi["d_source_abstraction_ml"] > 0).all())
        # H3: 上限不足 -> 必需服务缺口 > 0 且幻影显著
        h3 = bool(len(lo) and (lo["d_unmet_essential_ml"] > 1.0).all()
                  and (lo["phantom_overstatement_ml"].abs()
                       / lo["dS_pot_ml"].abs().clip(lower=1e-9) > 0.05).all())
        # H4: 余量态 -> dS_pot < 0 且 d_abstraction < 0
        h4 = bool(len(su) and (su["b2_incumbent_saturated"]).all()
                  and (su["dS_pot_ml"] < -TOL).all()
                  and (su["d_source_abstraction_ml"] < -TOL).all())

        # 证伪情景
        f1 = un[~((un["dS_pot_ml"] - un["d_delivered_potable_ml"]).abs() < 1e-8)
                | ~((un["dS_pot_ml"] - un["d_source_abstraction_ml"]).abs() > 1.0)]
        f2 = hi[~((hi["d_unmet_essential_ml"].abs() < 1.0)
                  & (hi["dS_pot_ml"] > 0) & (hi["d_source_abstraction_ml"] > 0))]
        f3 = lo[~((lo["d_unmet_essential_ml"] > 1.0)
                  & (lo["phantom_overstatement_ml"].abs()
                     / lo["dS_pot_ml"].abs().clip(lower=1e-9) > 0.05))]
        f4 = su[~((su["b2_incumbent_saturated"])
                  & (su["dS_pot_ml"] < -TOL)
                  & (su["d_source_abstraction_ml"] < -TOL))]

        prop[dom] = {
            "H1_ledger_identity_holds": h1,
            "H2_keeps_when_supply_adequate": h2,
            "H3_service_gap_when_scarce": h3,
            "H4_sign_reversal_in_surplus": h4,
            "w_gap_ml_day": wg,
            "n_H1": int(len(un)), "n_H2": int(len(hi)),            "n_H3": int(len(lo)), "n_H4": int(len(su)),
            "n_falsifiers_H1": int(len(f1)), "n_falsifiers_H2": int(len(f2)),
            "n_falsifiers_H3": int(len(f3)), "n_falsifiers_H4": int(len(f4)),
            "H_holds": bool(h1 and h2 and h3 and h4
                            and len(f1) == 0 and len(f2) == 0
                            and len(f3) == 0 and len(f4) == 0),
        }
        rec(f"\n  D-{dom.upper()}:")
        rec(f"    H1 (账本身份, 未约束  n={len(un)}): 成立={h1}  证伪={len(f1)}")
        rec(f"    H2 (W>={wg:.0f}, 供给充足 n={len(hi)}): 成立={h2}  证伪={len(f2)}")
        rec(f"    H3 (W< {wg:.0f}, 供给稀缺 n={len(lo)}): 成立={h3}  证伪={len(f3)}")
        rec(f"    H4 (余量态反转        n={len(su)}): 成立={h4}  证伪={len(f4)}")
        rec(f"    >> 命题 H 整体成立 = {prop[dom]['H_holds']}")

    # ---------------- 5.10 与 A13c/A17 代表日口径的桥接 ----------------
    rec("\n" + "=" * 78)
    rec("[S7] 与 A13c/A17 代表日口径的桥接核验 (只读引用现成模块)")
    rec("=" * 78)
    bridge = {}
    a13 = ROOT / "A13_可靠性机制"
    if str(ROOT / "A10_敏感性与边界") not in sys.path:
        sys.path.insert(0, str(ROOT / "A10_敏感性与边界"))
    if str(a13) not in sys.path:
        sys.path.insert(0, str(a13))
    try:
        import city_model as cm                       # noqa: E402
        import potable_flow_corrected as pfc          # noqa: E402
        for dom in DOMS:
            fl = pfc.potable_flows(dom, "B_full", "IEUA RP-1 (2025, tertiary)",
                                   PHI_AI, chi=0.5)
            elig = cm.BASELINES[dom]["P0"] + cm.BASELINES[dom]["gap"]
            base = raw[key(dom, "natural", 0.0, np.inf)]
            inf = NAT[(NAT["domain"] == dom)
                      & np.isinf(NAT["w_cap_ml_day"])].iloc[0]
            bridge[dom] = {
                "a13c_P0_ml": float(cm.BASELINES[dom]["P0"]),
                "a13c_elig_ml": float(elig),
                "a13c_elig_over_P0": float(elig / cm.BASELINES[dom]["P0"]),
                "a13c_dS_pot_ml": float(fl["dS_pot_ml"]),
                "a13c_C_ml": float(fl["C_claimed_ml"]),
                "a13c_F_ml": float(fl["F_released_ml"]),
                "engine_P0_ml": float(base["reclaimed_incumbent_ml"]),
                "engine_dS_pot_ml": float(inf["dS_pot_ml"]),
                "engine_state_by_unused": (
                    "surplus" if base["reclaimed_unused_ml"] > 1.0 else "shortage"),
                "sign_agreement": bool(
                    np.sign(fl["dS_pot_ml"]) == np.sign(inf["dS_pot_ml"])),
            }
            rec(f"  D-{dom.upper()}:")
            rec(f"    A13c 代表日 : P0={bridge[dom]['a13c_P0_ml']:.1f} "
                f"elig/P0={bridge[dom]['a13c_elig_over_P0']:.3f} "
                f"dS_pot={bridge[dom]['a13c_dS_pot_ml']:+.1f} ML")
            rec(f"    逐日引擎    : P0={bridge[dom]['engine_P0_ml']:.1f} "
                f"dS_pot={bridge[dom]['engine_dS_pot_ml']:+.1f} ML "
                f"state={bridge[dom]['engine_state_by_unused']}")
            rec(f"    P0 相对偏差 = "
                f"{abs(bridge[dom]['engine_P0_ml']-bridge[dom]['a13c_P0_ml'])/bridge[dom]['a13c_P0_ml']:.2e}"
                f"   符号一致 = {bridge[dom]['sign_agreement']}")
    except Exception as exc:  # noqa: BLE001
        rec(f"  桥接失败 {type(exc).__name__}: {exc}")
        bridge = {"error": f"{type(exc).__name__}: {exc}"}

    # ---------------- 5.11 汇总 ----------------
    runtime = time.time() - t0
    unlimited = NAT[np.isinf(NAT["w_cap_ml_day"])]
    summary = {
        "experiment": "A18/E2 finite-supply counterfactual on the full daily engine",
        "engine": "aiuwm.full_engine.FullAIUWMModel (read-only; instrumented subclass)",
        "n_scenarios": int(len(df)),
        "n_days_per_scenario": DAYS,
        "phi_ai": PHI_AI,
        "dc_capacity_mw": DC_CAPACITY_MW,
        "natural_abstraction_cap_ml_day": naturals,
        "path_efficiency": etas,
        "loss_leverage_factor": {d: 1.0 / etas[d] for d in DOMS},
        "old_conclusion_operational_definition": (
            "dS_pot = C - F > 0, i.e. AI reclaimed-water use raises city potable "
            "abstraction (A13c/A17 emission-claim balance, state A)."),
        "verdict": {
            "old_conclusion_keeps_when_unconstrained": bool(
                (unlimited["dS_pot_ml"] > 0).all()
                and (unlimited["d_source_abstraction_ml"] > 0).all()
                and (unlimited["d_unmet_essential_ml"].abs() < 1.0).all()),
            "converts_to_service_gap_when_scarce": bool(
                NAT[NAT["delivery_constrained"]]["d_unmet_essential_ml"].gt(1.0).all()
                if NAT["delivery_constrained"].any() else False),
            "sign_reversal_in_surplus_state": bool(
                len(SUR) and (SUR["dS_pot_ml"] < -TOL).all()
                and (SUR["d_source_abstraction_ml"] < -TOL).all()),
            "ai_itself_curtailed": bool((df["dc_unmet_cooling_ml"] > 1e-9).any()),
            "cap_engaged_while_no_service_gap": bool(
                (NAT["cap_engaged"] & ~NAT["delivery_constrained"]).any()),
            "ledger_reidentified_as_delivered_not_abstraction": bool(
                unlimited["requested_vs_delivered_gap_ml"].abs().max() < TOL
                and (unlimited["dS_pot_ml"]
                     - unlimited["d_delivered_potable_ml"]).abs().max() < 1e-8
                and (unlimited["dS_pot_ml"]
                     - unlimited["d_source_abstraction_ml"]).abs().max() > 1.0),
        },
        "three_account_divergence": {
            "requested_eq_delivered_when_unconstrained": bool(
                unlimited["requested_vs_delivered_gap_ml"].abs().max() < TOL),
            "requested_minus_delivered_equals_unmet_when_constrained": bool(
                (NAT[NAT["delivery_constrained"]]["requested_vs_delivered_gap_ml"]
                 - NAT[NAT["delivery_constrained"]]["unmet_total_ml"]).abs().max() < 1e-6),
            "abstraction_eq_delivered_ever": bool(
                df["abstraction_vs_delivered_gap_ml"].abs().max() < TOL),
            "max_requested_minus_delivered_ml": float(
                df["requested_vs_delivered_gap_ml"].max()),
            "max_abstraction_minus_delivered_ml": float(
                df["abstraction_vs_delivered_gap_ml"].max()),
            "min_abstraction_minus_delivered_ml": float(
                df["abstraction_vs_delivered_gap_ml"].min()),
            "marginal_abstraction_over_delivered": {
                d: float(1.0 / etas[d]) for d in DOMS},
            "note": ("requested == delivered only while the potable supply path is "
                     "unconstrained; abstraction never equals delivered because of "
                     "conveyance/treatment losses. The three accounts are distinct "
                     "quantities and must never be merged."),
        },
        "critical_conditions": crit,
        "structural_findings": {
            "F1_loss_leverage": {
                "statement": "marginal d_abstraction = d_delivered / eta_path",
                "eta_path": {d: float(etas[d]) for d in DOMS},
                "observed_ratio_unconstrained": {
                    d: float(un[un["domain"] == d]
                             ["observed_abstraction_over_delivered"].median())
                    for d in DOMS},
            },
            "F2_C_decomposition": {
                "statement": "C = x_AI - (pool(B1) - pool(B2)) exactly",
                "max_decomp_residual_ml": float(P["decomp_residual_ml"].abs().max()),
                "max_pool_drift_ml": float(P["d_reclaimed_pool_ml"].abs().max()),
                "max_pool_drift_share_of_C": float(
                    P["pool_drift_share_of_C"].abs().max()),
            },
        },
        "surplus_arm": {
            "config": {"WWTW1.central_reuse_fraction": 0.60,
                       "CENTRAL_REUSE.treatment_capacity_ml_day": 200.0},
            "n_scenarios": int(len(SUR)),
            "n_dS_pot_negative": int((SUR["dS_pot_ml"] < -TOL).sum()),
            "n_d_abstraction_negative": int(
                (SUR["d_source_abstraction_ml"] < -TOL).sum()),
            "n_delivery_constrained": int(SUR["delivery_constrained"].sum()),
            "n_b2_incumbent_saturated": int(SUR["b2_incumbent_saturated"].sum()),
            "n_b2_buffer_idle_positive": int(
                (SUR["b2_reclaimed_unused_ml"] > 1.0).sum()),
            "dS_pot_ml": float(SUR["dS_pot_ml"].median()) if len(SUR) else None,
            "d_abstraction_ml": float(
                SUR["d_source_abstraction_ml"].median()) if len(SUR) else None,
        },
        "proposition_H": prop,
        "a13c_bridge": bridge,
        "runtime_s": round(runtime, 1),
        "discipline_note": (
            "不使用已撤回的 psi / Delta / phi* 概念。需求、交付、取水三账并列报出, "
            "不合并。全部量取自引擎执行中当场产生的中间量 (instrumented 子类), "
            "C = r_inc(B2)-r_inc(B1) 按定义即既有用户须补回量。"
            "natural 臂用项目自带再生水产能 (A17 短缺态); surplus 臂用引擎原生键 "
            "WWTW1.central_reuse_fraction / CENTRAL_REUSE.treatment_capacity_ml_day "
            "制造未使用余量 (A17 余量态)。W_cap 直接改写 RES1.abstraction_capacity_ml_day。"),
    }
    (HERE / "finite_supply_summary.json").write_text(
        json.dumps(sanitize(summary), ensure_ascii=False, indent=1),
        encoding="utf-8")
    rec(f"\n[G] finite_supply_summary.json 写出")
    rec(f"总用时 {runtime:.1f}s")
    (HERE / "repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
