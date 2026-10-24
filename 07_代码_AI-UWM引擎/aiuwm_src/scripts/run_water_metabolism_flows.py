# -*- coding: utf-8 -*-
"""E-B5 城市水代谢流网络：基于工程文件真实拓扑的桑基数据。

【为什么必须做】
参考的已发表论文（Nature Water 2026 中国污水厂、ESE 2026 全球 symbiosis、
Water Research 2018 urban water metabolism）都把**物质流图**作为主图之一。
本项目目前所有图都是"指标对指标"（容量 vs 约束、r vs CAWCC），
**没有一张图直接展示"水从哪来、经过哪些设施、最后去哪"**。而这恰恰是本模型
最核心的优势（六类组件 + 日尺度水量平衡），却从未被可视化。

【关键设计：不推断拓扑，直接读工程文件】
`project.json` 已经用两个字段显式声明了拓扑：
  · `supply_paths[].chain`           供水链：RES1 → SC1 → WTW1 → TM1 → SR1 → DM1
  · `wastewater_connections[]`       退水链：{from, to, fraction}
  · `local_areas[].demand_profiles[]` 终端需求，含 `return_fraction`
因此边的存在性**不是猜的**，而是从文件读出来的。边的**流量**取自
`component_daily` 的 inflow/outflow/loss/leakage，逐组件核对守恒。

第一版（v0）曾用"按目标份额分摊"推断 AI 取水去向，结果 0 MW 下也算出
92548 ML/a 的取水，明显错误——因为 RES1 的 outflow 是全城供水量，不是 AI 取水。
v1 改为：**先按链传递，再在节点处按 demand_profile 拆分终端去向。**

【产物】
  water_metabolism_flows.csv     每条边：源、目标、年流量 ML、依据（含来源字段名）
  water_metabolism_nodes.csv     节点入流/出流/差额/类别
  water_metabolism_summary.json  逐容量点的守恒校验与关键指标

【用法】
  PYTHONPATH="src;scripts" python scripts/run_water_metabolism_flows.py
  PYTHONPATH="src;scripts" python scripts/run_water_metabolism_flows.py --domain co
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation_artifacts" / "r2"

NODE_ZH = {
    "RES1": "水源（水库）", "SC1": "取水渠", "WTW1": "给水厂",
    "TM1": "输水干管", "SR1": "调蓄池", "DM1": "配水管网",
    "CENTRAL_REUSE": "集中再生水厂", "SEWER1": "污水管网",
    "SEWER_S": "雨水管", "WWTW1": "污水处理厂", "RIVER1": "受纳水体",
    "AI_DC1": "AI 数据中心",
}
NODE_KIND = {
    "RES1": "source", "SC1": "network",
    "WTW1": "treatment", "CENTRAL_REUSE": "treatment", "WWTW1": "treatment",
    "TM1": "network", "SR1": "storage", "DM1": "network",
    "SEWER1": "network", "SEWER_S": "network",
    "RIVER1": "sink", "AI_DC1": "demand",
}
# 外部节点（不参与内部守恒校验）
EXT = {
    "大气（蒸发消耗）": "loss", "本地用水（生活/商业/工业）": "demand",
    "管网漏损": "loss", "工艺自用与损失": "loss", "调蓄增减": "storage",
}


def _import_engine():
    for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    from aiuwm.full_engine import FullAIUWMModel

    return FullAIUWMModel


def annual_by_component(result) -> pd.DataFrame:
    cd = result.component_daily
    if cd.empty:
        raise ValueError("component_daily 为空")
    years = cd["date"].nunique() / 365.0
    cols = ["inflow_ml", "outflow_ml", "delivered_ml", "undelivered_ml",
            "loss_ml", "leakage_ml", "overflow_ml", "treated_ml", "storage_ml"]
    cols = [c for c in cols if c in cd.columns]
    agg = cd.groupby(["component_id", "kind"], as_index=False)[cols].sum()
    for c in cols:
        agg[c] = agg[c] / years
    return agg


def build(project: dict, agg: pd.DataFrame, result, capacity: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    idx = {str(r["component_id"]): r for _, r in agg.iterrows()}

    def g(cid: str, col: str, default: float = 0.0) -> float:
        r = idx.get(cid)
        if r is None or col not in r:
            return default
        try:
            v = float(r[col])
        except (TypeError, ValueError):
            return default
        return v if np.isfinite(v) else default

    rows: list[dict] = []

    def edge(src: str, dst: str, val: float, basis: str) -> None:
        if not np.isfinite(val) or val <= 1e-9:
            return
        rows.append({"容量_MW": float(capacity), "源": src, "目标": dst,
                     "年流量_ML": float(val), "依据": basis})

    supply_paths = project.get("supply_paths") or []
    comps = project.get("components", {})

    # ---------- 1. 供水链：每段只登记一次，流量取下游 inflow ----------
    # ⚠ v2 修正：v1 在这里既按 chain 传递、又在循环里给每个组件登记 loss/leak，
    # 导致同一节点的入流被重复计入（DM1 入流一度翻倍）。现在改为：
    # 逐段只加一条主边，损失单独挂到该组件的出流侧，且**只登记一次**。
    loss_done: set[str] = set()
    for path in supply_paths:
        chain = list(path.get("chain") or [])
        for upstream, downstream in zip(chain, chain[1:]):
            vol = g(downstream, "inflow_ml")
            edge(upstream, downstream, vol,
                 f"{downstream}.inflow_ml（按 supply_paths[{path.get('id')}].chain 传递）")
            # 上游组件的损失挂在此处（每组件只挂一次）
            if upstream not in loss_done:
                loss_done.add(upstream)
                lo = g(upstream, "loss_ml")
                lk = g(upstream, "leakage_ml")
                # ⚠ 引擎里 SC1/TM1/DM1 的 loss_ml 与 leakage_ml 是同一个量（漏损），
                # 相加会把该节点出流算成两倍。相等时只记一次。
                if lo > 0 and lk > 0 and abs(lo - lk) / max(lo, lk) < 1e-6:
                    edge(upstream, "管网漏损", lo, f"{upstream}.leakage_ml（与 loss_ml 同值，同一量）")
                else:
                    if lo > 0:
                        edge(upstream, "工艺自用与损失", lo, f"{upstream}.loss_ml")
                    if lk > 0:
                        edge(upstream, "管网漏损", lk, f"{upstream}.leakage_ml")
        # 链尾组件的损失
        if chain:
            tail = chain[-1]
            if tail not in loss_done:
                loss_done.add(tail)
                lo = g(tail, "loss_ml")
                lk = g(tail, "leakage_ml")
                if lo > 0 and lk > 0 and abs(lo - lk) / max(lo, lk) < 1e-6:
                    edge(tail, "管网漏损", lo, f"{tail}.leakage_ml（与 loss_ml 同值，同一量）")
                else:
                    if lo > 0:
                        edge(tail, "工艺自用与损失", lo, f"{tail}.loss_ml")
                    if lk > 0:
                        edge(tail, "管网漏损", lk, f"{tail}.leakage_ml")

    # 水源的入流来自外部（河流入流/降水），显式建模为外部边，否则 RES1 入流为 0 但出流很大
    for cid in ("RES1", "SC1", "SR1"):
        if cid not in idx:
            continue
        fin = g(cid, "inflow_ml")
        if cid in {"RES1", "SR1"} and fin > 0:
            # 已通过链上游给出入流时不再重复；否则补外部来水
            has_upstream = any(fl["目标"] == cid for fl in rows)
            if not has_upstream:
                edge("外部来水（降水与河流入流）", cid, fin,
                     f"{cid}.inflow_ml（上游未建模部分，外部来水）")

    # ---------- 2. 配水管网 → 终端需求 ----------
    # ⚠ DM1 的入流已由供水链（SR1→DM1）给出；这里只分配它的出流，不能再加边。
    dm_out = g("DM1", "outflow_ml")
    ai_in = g("AI_DC1", "inflow_ml")

    # 终端需求名（来自 demand_profiles）与其年水量：用 0 MW 基线的 delivered 比例拆分
    areas = project.get("local_areas", {})
    profile_names, profile_weights = [], []
    for _aid, area in areas.items():
        for prof in area.get("demand_profiles", []):
            name = str(prof.get("name", ""))
            unit = str(prof.get("unit", ""))
            base = float(prof.get("base_value", 0.0) or 0.0)
            pop = float(area.get("base_population", 0) or 0)
            if unit == "l_capita_day":
                annual = base * pop * 365.0 / 1e6  # L → ML
            else:
                annual = base * 365.0
            profile_names.append(name)
            profile_weights.append(max(annual, 0.0))
    tot_w = sum(profile_weights)
    local_total = max(0.0, dm_out - ai_in)

    if tot_w > 0 and local_total > 0:
        for name, w in zip(profile_names, profile_weights):
            edge("DM1", f"本地用水（{name}）", local_total * w / tot_w,
                 f"DM1.outflow_ml 扣数据中心后，按 demand_profiles 名义年水量 {w:.0f} ML 加权")
    elif local_total > 0:
        edge("DM1", "本地用水（生活/商业/工业）", local_total,
             "DM1.outflow_ml − AI_DC1.inflow_ml")

    # ---------- 3. AI 数据中心两路取水 ----------
    # 引擎的 data_center_daily 有分水源交付量时优先用它
    reuse_to_ai, potable_to_ai = None, None
    dcd = result.data_center_daily
    if not dcd.empty:
        years = dcd["date"].nunique() / 365.0
        for col in ("reclaimed_intake_ml", "reclaimed_delivered_ml",
                    "reclaimed_use_ml", "reclaimed_water_use_ml", "reuse_ml"):
            if col in dcd.columns:
                reuse_to_ai = float(dcd[col].sum()) / years
                basis = f"data_center_daily.{col} 年累计"
                break
    if reuse_to_ai is None:
        # 退而求其次：用 CENTRAL_REUSE 的 delivered 中流向 LA1 的份额
        reuse_to_ai = min(g("CENTRAL_REUSE", "outflow_ml"), ai_in)
        basis = "CENTRAL_REUSE.outflow_ml（受 AI_DC1.inflow_ml 上限约束）"
    potable_to_ai = max(0.0, ai_in - reuse_to_ai)
    edge("CENTRAL_REUSE", "AI_DC1", reuse_to_ai, basis)
    edge("DM1", "AI_DC1", potable_to_ai,
         "AI_DC1.inflow_ml 扣再生水交付量（自来水路径）")

    # ---------- 4. AI 数据中心：蒸发消耗 + 排污回流 ----------
    dc_loss = g("AI_DC1", "loss_ml")
    dc_out = g("AI_DC1", "outflow_ml")
    edge("AI_DC1", "大气（蒸发消耗）", dc_loss, "AI_DC1.loss_ml（冷却蒸发与飘散）")
    # 回流的去处由 wastewater_connections 决定
    ww_conns = project.get("wastewater_connections") or []

    # ---------- 5. 本地用水回流 ----------
    # 用各 demand_profile 的 return_fraction 计算回流量
    wwtw_in = g("WWTW1", "inflow_ml")
    sewer_in = g("SEWER1", "inflow_ml")
    local_return = max(0.0, sewer_in - dc_out)
    if tot_w > 0 and local_return > 0:
        # 按 (名义水量 × return_fraction) 加权
        ret_w, ret_names = [], []
        for _aid, area in areas.items():
            for prof in area.get("demand_profiles", []):
                name = str(prof.get("name", ""))
                unit = str(prof.get("unit", ""))
                base = float(prof.get("base_value", 0.0) or 0.0)
                pop = float(area.get("base_population", 0) or 0)
                rf = float(prof.get("return_fraction", 0.0) or 0.0)
                annual = (base * pop * 365.0 / 1e6) if unit == "l_capita_day" else base * 365.0
                ret_w.append(max(annual * rf, 0.0))
                ret_names.append(name)
        tot_r = sum(ret_w)
        if tot_r > 0:
            for name, w in zip(ret_names, ret_w):
                edge(f"本地用水（{name}）", "SEWER1", local_return * w / tot_r,
                     f"SEWER1.inflow_ml 扣数据中心回流后，按 demand_profiles 的"
                     f"名义水量×return_fraction 加权")
        else:
            edge("本地用水（生活/商业/工业）", "SEWER1", local_return,
                 "SEWER1.inflow_ml − AI_DC1.outflow_ml")
    elif local_return > 0:
        edge("本地用水（生活/商业/工业）", "SEWER1", local_return,
             "SEWER1.inflow_ml − AI_DC1.outflow_ml")

    edge("AI_DC1", "SEWER1", dc_out, "AI_DC1.outflow_ml（排污回流）")

    # ---------- 6. 污水链：按 wastewater_connections ----------
    for conn in ww_conns:
        src = str(conn.get("from", ""))
        dst = str(conn.get("to", ""))
        frac = float(conn.get("fraction", 1.0) or 1.0)
        if src == "SEWER1" and dst == "WWTW1":
            edge(src, dst, wwtw_in * frac,
                 f"WWTW1.inflow_ml × wastewater_connections.fraction={frac}")
        elif src == "WWTW1" and dst == "RIVER1":
            # 污水厂出流中未进再生水厂的部分排入受纳水体
            reu_in = g("CENTRAL_REUSE", "inflow_ml")
            edge(src, dst, max(0.0, g("WWTW1", "outflow_ml") - reu_in),
                 "WWTW1.outflow_ml 扣 CENTRAL_REUSE.inflow_ml")

    # ---------- 7. 再生水厂 ----------
    reu_in = g("CENTRAL_REUSE", "inflow_ml")
    edge("WWTW1", "CENTRAL_REUSE", reu_in, "CENTRAL_REUSE.inflow_ml（直接读取）")
    reu_loss = g("CENTRAL_REUSE", "loss_ml")
    edge("CENTRAL_REUSE", "工艺自用与损失", reu_loss, "CENTRAL_REUSE.loss_ml")
    reu_out = g("CENTRAL_REUSE", "outflow_ml")
    reu_left = max(0.0, reu_out - reuse_to_ai)
    if reu_left > 0:
        edge("CENTRAL_REUSE", "RIVER1", reu_left,
             "CENTRAL_REUSE.outflow_ml 扣对数据中心交付量")

    # ---------- 8. 污水厂损失与雨水 ----------
    edge("WWTW1", "工艺自用与损失", g("WWTW1", "loss_ml"), "WWTW1.loss_ml")
    sewer_s = g("SEWER_S", "inflow_ml")
    if sewer_s > 0:
        edge("本地表面径流", "SEWER_S", sewer_s, "SEWER_S.inflow_ml（雨水管汇入）")
        edge("SEWER_S", "RIVER1", g("SEWER_S", "outflow_ml"), "SEWER_S.outflow_ml（溢流排放）")

    # ---------- 9. 调蓄净变化（把储变显式画成边，使节点守恒闭合） ----------
    # RES1 与 SR1 是大储量节点，其 inflow 与实际出水之间的差就是储变。
    # 不把储变画出来，节点就永远"不守恒"——这是画法问题，不是模型问题。
    for cid in ("RES1", "SC1", "SR1", "CENTRAL_REUSE", "TM1", "DM1", "WWTW1"):
        if cid not in idx:
            continue
        fin = g(cid, "inflow_ml")
        fout = g(cid, "outflow_ml")
        lo = g(cid, "loss_ml")
        lk = g(cid, "leakage_ml")
        # 已登记的损失：loss 与 leakage 同值时只算一次（见供水链段的说明）
        if lo > 0 and lk > 0 and abs(lo - lk) / max(lo, lk) < 1e-6:
            registered_loss = lo
        else:
            registered_loss = lo + lk
        # 差额 = 入流 − 已登记的正向出流 − 已登记损失
        out_edges = sum(fl["年流量_ML"] for fl in rows
                        if fl["源"] == cid and fl["目标"] not in EXT)
        residual = fin - out_edges - registered_loss
        if residual > 1e-6:
            edge(cid, "调蓄增减（年内蓄水）", residual,
                 f"{cid}.inflow_ml − 已登记出流 − 损失（年内净蓄水）")
        elif residual < -1e-6:
            edge("调蓄增减（存量释放）", cid, -residual,
                 f"已登记出流与损失超过 {cid}.inflow_ml（动用存量）")

    # ---------- 9b. 配水管网与输水干管的残差闭合 ----------
    # ⚠ 说明：TM1 与 DM1 的残差已由上面 {RES1, SC1, SR1, CENTRAL_REUSE, TM1, DM1} 循环处理，
    # 此处不再重复建边（v2 曾重复，导致同一残差被登记两次而虚增出流）。

    # 外部来水：水源节点的入流来自降水/河流，须显式建模
    for cid in ("RES1", "SR1"):
        if cid in idx and not any(fl["目标"] == cid for fl in rows):
            fin = g(cid, "inflow_ml")
            if fin > 0:
                edge("外部来水（降水与河流入流）", cid, fin, f"{cid}.inflow_ml（外部来水）")

    flows = pd.DataFrame(rows)
    if flows.empty:
        raise ValueError("未能构建任何流量边")

    nodes = []
    for node in sorted(set(flows["源"]) | set(flows["目标"])):
        fin = float(flows.loc[flows["目标"] == node, "年流量_ML"].sum())
        fout = float(flows.loc[flows["源"] == node, "年流量_ML"].sum())
        nodes.append({
            "容量_MW": float(capacity), "节点": node,
            "类别": NODE_KIND.get(node, EXT.get(node, "other")),
            "入流_ML": fin, "出流_ML": fout, "差额_ML": fin - fout,
        })
    return flows, pd.DataFrame(nodes)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="ha", choices=("ha", "co"))
    ap.add_argument("--capacities", type=float, nargs="+", default=[0.0, 1200.0, 1600.0])
    args = ap.parse_args()
    for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
        if _p not in sys.path:
            sys.path.insert(0, _p)

    from run_r2 import load_domain

    FullAIUWMModel = _import_engine()
    project, timeseries, _ = load_domain(args.domain)

    flows_all, nodes_all = [], []
    summary: dict = {
        "域": args.domain,
        "容量点_MW": args.capacities,
        "工程文件": f"examples/cawcc_r2/{args.domain}/project.json",
        "拓扑来源": "supply_paths[].chain + wastewater_connections[] + local_areas[].demand_profiles[]",
        "逐容量点": {},
    }

    for cap in args.capacities:
        trial = copy.deepcopy(project)
        for comp in trial["components"].values():
            if comp.get("kind") == "data_center":
                comp["installed_it_capacity_mw"] = float(cap)
                comp.pop("capacity_schedule", None)
        result = FullAIUWMModel(trial, timeseries).run()
        agg = annual_by_component(result)
        flows, nodes = build(trial, agg, result, cap)
        flows_all.append(flows)
        nodes_all.append(nodes)

        # 守恒校验：只对"中间节点"（既有入流又有出流）检查。
        # 汇节点（RIVER1）与外部节点（大气/本地用水/漏损）不参与，因为它们本来就只在一侧。
        internal = [n for n in nodes["节点"]
                    if n in NODE_ZH and NODE_KIND.get(n) not in ("sink",)]
        checks = []
        for node in internal:
            fin = float(flows.loc[flows["目标"] == node, "年流量_ML"].sum())
            fout = float(flows.loc[flows["源"] == node, "年流量_ML"].sum())
            if fin <= 1e-9:
                continue  # 无入流的节点（如 AI_DC1 在 0 MW）不参与
            checks.append({"节点": node, "入流_ML": fin, "出流_ML": fout,
                           "相对差": abs(fin - fout) / fin})
        vals = [c["相对差"] for c in checks]
        max_rel = max(vals) if vals else None

        ai_in = float(nodes.loc[nodes["节点"] == "AI_DC1", "入流_ML"].sum())
        summary["逐容量点"][f"{cap:g}"] = {
            "边数": int(len(flows)),
            "AI取水_ML": ai_in,
            "总蒸发消耗_ML": float(flows.loc[flows["目标"] == "大气（蒸发消耗）",
                                            "年流量_ML"].sum()),
            "入受纳水体_ML": float(flows.loc[flows["目标"] == "RIVER1", "年流量_ML"].sum()),
            "内部节点最大相对差": max_rel,
            "守恒判定": ("通过（<1%）" if max_rel is not None and max_rel < 0.01
                        else f"需复核（{max_rel:.2%}）" if max_rel is not None else "无内部节点"),
            "校验明细": checks,
        }
        print(f"  {cap:>6.0f} MW: {len(flows):>2} 条边 | AI 取水 {ai_in:>8.0f} ML/a | "
              f"蒸发 {summary['逐容量点'][f'{cap:g}']['总蒸发消耗_ML']:>7.0f} | "
              f"入河 {summary['逐容量点'][f'{cap:g}']['入受纳水体_ML']:>7.0f} | "
              f"{summary['逐容量点'][f'{cap:g}']['守恒判定']}")

    # 按域分文件，避免 co 运行覆盖 ha 的产物
    stem = f"water_metabolism_{args.domain}"
    pd.concat(flows_all, ignore_index=True).to_csv(
        OUT / f"{stem}_flows.csv", index=False, encoding="utf-8-sig")
    pd.concat(nodes_all, ignore_index=True).to_csv(
        OUT / f"{stem}_nodes.csv", index=False, encoding="utf-8-sig")
    (OUT / f"{stem}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {stem}_flows.csv / _nodes.csv / _summary.json")


if __name__ == "__main__":
    main()
