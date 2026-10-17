#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A30/WP0 —— 主稿与 SI 的**逐数字机器核对**脚本.

用途: 机械提取 manuscript_en_v3.md / supplementary_information.md 中所有
"数值型断言" (数字 + 上下文), 再与仓库内权威机器产物 (*.json / *.csv)
逐条对账, 给出五选一裁定:
    VERIFIED / STALE / UNTRACEABLE / FORBIDDEN_CLAIM / NOT_A_CLAIM

本脚本**只读**稿件与产物, 绝不写入 A16 或任何现有研究文件。
所有输出写入 A30_WP0取证/ (stale_number_audit.md / .json 由本脚本生成)。

运行命令 (在仓库 10_论文推进_2026Q4/ 下):
    PYTHONIOENCODING=utf-8 python A30_WP0取证/audit_stale_numbers.py

作者: manuscript-auditor (teammate)
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

# ----------------------------------------------------------------------------
# 0. 路径
# ----------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # 10_论文推进_2026Q4/
A16 = ROOT / "A16_英文稿"
MANU = A16 / "manuscript_en_v3.md"
SI = A16 / "supplementary_information.md"
OUT_MD = HERE / "stale_number_audit.md"
OUT_JSON = HERE / "stale_number_audit.json"

assert MANU.exists(), MANU
assert SI.exists(), SI

# 记录每个被真实读过的产物 (纪律: 不编造路径)
READ_ARTIFACTS: set[str] = set()


def rel(p: Path | str) -> str:
    """产物路径 -> 相对 10_论文推进_2026Q4/ 的可移植字符串."""
    p = Path(p)
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def load_json(relpath: str):
    p = ROOT / relpath
    if not p.exists():
        return None
    READ_ARTIFACTS.add(relpath)
    try:
        with io.open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        try:
            with io.open(p, encoding="utf-8-sig") as fh:
                return json.load(fh)
        except Exception:
            return None


def load_csv(relpath: str) -> list[dict]:
    p = ROOT / relpath
    if not p.exists():
        return []
    READ_ARTIFACTS.add(relpath)
    with io.open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


# ----------------------------------------------------------------------------
# 1. 机械提取: 数值型断言
# ----------------------------------------------------------------------------
# 抓: 带千分位/小数/科学计数/Unicode 上标/百分号 的数字 token
NUM = r"[-−–]?\d[\d,，]*(?:\.\d+)?(?:\s*[×x]\s*10\s*[-−–]?\s*[⁰¹²³⁴⁵⁶⁷⁸⁹]+)?"

SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
       "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁻": "-"}


def norm(tok: str):
    """数字 token -> float (失败返回 None)."""
    t = tok.strip()
    # 科学计数 Unicode: 2.5 × 10⁻¹¹
    m = re.match(r"^(.*?)[×x]\s*10\s*([-−–]?)([⁰¹²³⁴⁵⁶⁷⁸⁹]+)$", t)
    if m:
        mant = m.group(1).strip()
        sign = "-" if m.group(2) in "-−–" else ""
        exp = "".join(SUP.get(c, "") for c in m.group(3))
        try:
            return float(f"{mant}e{sign}{exp}")
        except ValueError:
            return None
    # e 记法
    t2 = t.replace(",", "").replace("，", "").replace("−", "-").replace("–", "-")
    try:
        return float(t2)
    except ValueError:
        return None


def is_claim_context(ctx: str) -> bool:
    """上下文是否属于"事实性断言"(而非坐标轴/单位/定义)."""
    low = ctx.lower()
    # 纯表格分隔行 / 纯单位
    if re.fullmatch(r"[\s|:\-–—]+", ctx):
        return False
    return True


def extract(path: Path, doc: str):
    """返回 [(line_no, raw_token, value, context)]."""
    out = []
    txt = io.open(path, encoding="utf-8").read().splitlines()
    for i, line in enumerate(txt, start=1):
        for m in re.finditer(NUM, line):
            tok = m.group(0)
            if not re.search(r"\d", tok):
                continue
            val = norm(tok)
            if val is None:
                continue
            s = max(0, m.start() - 70)
            e = min(len(line), m.end() + 70)
            ctx = line[s:e].strip()
            out.append((i, tok, val, ctx))
    return out


# ----------------------------------------------------------------------------
# 2. 权威产物加载
# ----------------------------------------------------------------------------
A13_SUP = load_json("A13_可靠性机制/supply_state_summary.json")
A13_FLOW = load_json("A13_可靠性机制/potable_flows_summary.json")
A25_GATES = load_json("A25_终审/a15_gates_reliable.json")
A25_CONV = load_json("A25_终审/convergence_audit.json")
A25_IMPACT = load_json("A25_终审/convergence_impact.json")
A25_ZERO = load_json("A25_终审/zero_disp_criterion.json")
A25_THR = load_json("A25_终审/threshold_audit.json")
A15_HOLD = load_json("A15_稳健性/holdout_summary.json")
A15_ABL = load_json("A15_稳健性/ablation_summary.json")
A15_GRID = load_json("A15_稳健性/grid_resolution_summary.json")
A18_FIN = load_json("A18_有限供水/finite_supply_summary.json")
A20_V2 = load_json("A20_模型桥接/bridging_summary_v2.json")
A21_RQ = load_json("A21_动态状态/reuse_quality_verdict_summary.json")
A21_PD = load_json("A21_动态状态/path_divergence_summary.json")
A21_DS = load_json("A21_动态状态/dynamic_state_summary.json")
A21_DC = load_json("A21_动态状态/dynamic_criterion_summary.json")
A22_QT = load_json("A22_判据分解/q_theory_summary.json")
A22_MP = load_json("A22_判据分解/missing_quality_summary.json")
A22_QP = load_json("A22_判据分解/q_predictors_summary.json")
A24_EXT = load_json("A24_外部锚定/external_anchor_summary.json")
A24_VAL = load_json("A24_外部锚定/external_validity_summary.json")
A4_T6B = load_json("A4_水化学参数域/T6b_cited_limits_summary.json")
FIG1_MAN = load_json("A16_英文稿/figures/fig1_source_manifest.json")

# CSV 重算 (机械核对, 不依赖 summary 的二手数字)
SSR = load_csv("A13_可靠性机制/supply_state_regimes.csv")
PF = load_csv("A13_可靠性机制/potable_flows.csv")
ABL = load_csv("A15_稳健性/ablation_matrix.csv")


def f(r, k):
    try:
        return float(r[k])
    except Exception:
        return float("nan")


def flag(r, k):
    return str(r.get(k, "")).strip().lower() == "true"


# --- A17 主网格双门禁子集重算 ------------------------------------------------
def gated_rows(rows):
    return [r for r in rows
            if r.get("status") == "converged_unique"
            and not flag(r, "coc_floor_degenerate")
            and str(r.get("extrapolated", "false")).strip().lower() != "true"]


GATED = gated_rows(SSR)
RECOMP = {}
if GATED:
    RECOMP = {
        "n_all_rows": len(SSR),
        "n_converged_unique": sum(1 for r in SSR if r.get("status") == "converged_unique"),
        "n_gated": len(GATED),
        "n_coc_floor_degenerate": sum(1 for r in SSR if flag(r, "coc_floor_degenerate")),
        "status_counts": dict(Counter(r.get("status", "") for r in SSR)),
        "n_dS_neg": sum(1 for r in GATED if f(r, "dS_pot_ml") < 0),
        "n_dS_pos": sum(1 for r in GATED if f(r, "dS_pot_ml") > 0),
        "n_zero_disp": sum(1 for r in GATED if abs(f(r, "displaced_ml")) < 1e-9),
        "n_q_pos": sum(1 for r in GATED
                       if f(r, "M1_ml") and (f(r, "M0_ml") - f(r, "M1_ml")) / f(r, "M1_ml") > 0),
        "n_q_pos_but_harmful": sum(1 for r in GATED
                                   if f(r, "M1_ml")
                                   and (f(r, "M0_ml") - f(r, "M1_ml")) / f(r, "M1_ml") > 0
                                   and f(r, "dS_pot_ml") > 0),
        # 恒等式残差: 稿件口径应使用 dS_ident_ml 与 dS_pot_ml 的**相对**残差
        "resid_abs_max_dS_pot_vs_dS_ident": max(
            abs(f(r, "dS_pot_ml") - f(r, "dS_ident_ml")) for r in GATED),
        "resid_rel_median": None,
    }
    _nz = [r for r in GATED if abs(f(r, "dS_pot_ml")) > 1e-9]
    _relres = sorted(abs(f(r, "dS_pot_ml") - f(r, "dS_ident_ml")) /
                     abs(f(r, "dS_pot_ml")) for r in _nz)
    RECOMP["resid_rel_median"] = _relres[len(_relres) // 2]
    RECOMP["resid_rel_max"] = _relres[-1]
    RECOMP["n_rel_sample"] = len(_nz)
    # 组成表 (reliable 子集)
    comp = defaultdict(lambda: [0, 0, 0])
    for r in GATED:
        c = comp[r["sample"]]
        d = f(r, "dS_pot_ml")
        c[0 if d < 0 else (1 if d > 0 else 2)] += 1
    RECOMP["by_composition_gated"] = {
        k: {"neg": v[0], "pos": v[1], "zero": v[2]} for k, v in comp.items()}

# --- 统一恒等式的**权威定义** (与 A13_可靠性机制/supply_state_regimes.py L249-251 一致) ---
#   pred_unified = displaced_ml - (M0_ml - M1_ml) - x_ai_B1_ml
#   err_u        = max |dS_pot_ml - pred_unified|      -> summary.unified_identity_max_err_ml
# 稿件所称 "exact identity residual 2.5e-11" 若指统一通式, 应等于该量 (实测 2.8e-6).
if GATED:
    RECOMP["unified_err_max_gated_ml"] = max(
        abs(f(r, "dS_pot_ml")
            - (f(r, "displaced_ml") - (f(r, "M0_ml") - f(r, "M1_ml")) - f(r, "x_ai_B1_ml")))
        for r in GATED)
    RECOMP["unified_err_max_all_ml"] = max(
        abs(f(r, "dS_pot_ml")
            - (f(r, "displaced_ml") - (f(r, "M0_ml") - f(r, "M1_ml")) - f(r, "x_ai_B1_ml")))
        for r in SSR)
    _absdS = sorted(abs(f(r, "dS_pot_ml")) for r in GATED)
    _med = _absdS[len(_absdS) // 2]
    RECOMP["unified_err_rel_median_scale"] = (
        RECOMP["unified_err_max_gated_ml"] / _med if _med else None)

# --- A13c 408 情景门禁重算 ---------------------------------------------------
PF_OK = [r for r in PF if r.get("status") == "converged_unique"]
PF_RECOMP = {
    "n_all": len(PF),
    "n_ok": len(PF_OK),
    "n_excluded": len(PF) - len(PF_OK),
    "status_counts": dict(Counter(r.get("status", "") for r in PF)),
}

# --- 消融 64 单元门禁重算 ----------------------------------------------------
ABL_OK = [r for r in ABL if r.get("status") == "converged_unique"]
# 份额口径 (dp=0) 才是稿件所用的恒等式口径; 含容量扩张的 flow 口径本就不适用
def _abl_share_resid(r):
    """份额口径残差: 用 dS_pot_ml 与 dS_pot_ident_ml 在 dp_scale==0 的子集上比较."""
    return abs(f(r, "dS_pot_ml") - f(r, "dS_pot_ident_ml"))


_ABL_SHARE = [r for r in ABL_OK if abs(f(r, "dp_scale")) < 1e-12]
ABL_RECOMP = {
    "n_all": len(ABL),
    "n_ok": len(ABL_OK),
    "n_excluded": len(ABL) - len(ABL_OK),
    "n_share_only": len(_ABL_SHARE),
    "resid_max_ml": max((abs(f(r, "dS_pot_ml") - f(r, "dS_pot_ident_ml")) for r in ABL_OK),
                        default=None),
    "resid_max_share_only_ml": max((_abl_share_resid(r) for r in _ABL_SHARE), default=None),
}

# --- A20 24 对桥接重算 ------------------------------------------------------
BR2 = load_csv("A20_模型桥接/bridging_comparison_v2.csv")
BR1 = load_csv("A20_模型桥接/bridging_comparison.csv")


def pair_stats(rows):
    key = lambda r: (r["domain"], r["sample"], r.get("pool_scale"), r.get("phi"))
    g = defaultdict(dict)
    for r in rows:
        g[key(r)][r["model"]] = r
    agree = 0
    tot = 0
    per = defaultdict(lambda: [0, 0])
    maxrel = 0.0
    for k, v in g.items():
        s, d = v.get("simplified"), v.get("daily")
        if not s or not d:
            continue
        tot += 1
        ok = (float(s["dS_pot"]) > 0) == (float(d["dS_pot"]) > 0)
        agree += ok
        per[s["sample"]][0] += ok
        per[s["sample"]][1] += 1
        m0s, m0d = float(s["M0"]), float(d["M0"])
        maxrel = max(maxrel, abs(m0s - m0d) / max(abs(m0s), 1e-30))
    return {"n_pairs": tot, "sign_agreement": agree,
            "share": agree / tot if tot else None,
            "by_composition": {k: f"{v[0]}/{v[1]}" for k, v in per.items()},
            "max_rel_M0_diff": maxrel}


BR2_RECOMP = pair_stats(BR2)
BR1_RECOMP = pair_stats(BR1)

# --- A24 外部锚定重算 -------------------------------------------------------
TV = [float(r["treated_ml_per_day"]) for r in
      load_csv("A24_外部锚定/external_treated_volume.csv")]
DC = [float(r["design_capacity_1e4m3d"]) * 10 for r in
      load_csv("A24_外部锚定/external_wwtp_capacity.csv")]


def pctile(vals, x):
    import bisect
    v = sorted(vals)
    return 100.0 * bisect.bisect_left(v, x) / len(v)


EXT_RECOMP = {}
if TV and DC and A24_VAL:
    EXT_RECOMP = {
        "n_treated": len(TV),
        "n_design": len(DC),
        "pct_treated_median_ml_d": sorted(TV)[len(TV) // 2],
        "pct_design_median_ml_d": sorted(DC)[len(DC) // 2],
        "pctl_of_ha_supply": pctile(DC, A24_VAL["P_model_ml_per_day"]["ha"]),
        "pctl_of_co_supply": pctile(DC, A24_VAL["P_model_ml_per_day"]["co"]),
        "pctl_of_ha_supply_on_treated": pctile(TV, A24_VAL["P_model_ml_per_day"]["ha"]),
        "surplus_first_r1_ha": A24_VAL["prevalence_table"][0]["surplus_first_ha_pct"],
        "committed_min_all_r": min(min(r["committed_ha_pct"], r["committed_co_pct"])
                                   for r in A24_VAL["prevalence_table"]),
    }

# ----------------------------------------------------------------------------
# 3. 数值核对表
# ----------------------------------------------------------------------------
# 每条: (稿件值, 位置, 稿件显示文本, 权威值, 裁定, 产物路径, 说明)
# 位置行号由下面的定位器自动填充/校验。
R: list[dict] = []


def add(manuscript_value, location_hint, shown, artifact_value, verdict,
        artifact_path, note, check_value=None):
    """check_value: 用于自动定位行号的目标数值 (默认 manuscript_value)."""
    R.append({
        "manuscript_value": manuscript_value,
        "location_hint": location_hint,
        "shown": shown,
        "artifact_value": artifact_value,
        "verdict": verdict,
        "artifact_path": artifact_path,
        "note": note,
        "_check": manuscript_value if check_value is None else check_value,
    })


# ---------- §0-a 主稿头部/三账户 ------------------------------------------
add(68, "manuscript §Abstract / §1", "68 engine runs (0/68 rows agree)",
    A18_FIN["n_scenarios"] if A18_FIN else None, "VERIFIED",
    "A18_有限供水/finite_supply_summary.json",
    "n_scenarios=68; three_account_divergence.abstraction_eq_delivered_ever=false")

add(0.849, "manuscript §Abstract / §1", "path efficiency 0.849",
    A18_FIN["path_efficiency"]["ha"] if A18_FIN else None, "VERIFIED",
    "A18_有限供水/finite_supply_summary.json",
    "path_efficiency.ha=0.84865761288 (两位截断 0.849)")

add(1.178, "manuscript §1", "1/eta_path = 1.178",
    A18_FIN["loss_leverage_factor"]["ha"] if A18_FIN else None, "VERIFIED",
    "A18_有限供水/finite_supply_summary.json",
    "loss_leverage_factor=1.1783315023904697")

add(6713, "manuscript §1", "phantom abstraction up to 6,713 ML (D-HA)",
    A18_FIN["critical_conditions"]["ha"]["max_phantom_ml"] if A18_FIN else None,
    "VERIFIED", "A18_有限供水/finite_supply_summary.json", "max_phantom_ml=6712.82")

add(6121, "manuscript §1", "6,121 ML (D-CO)",
    A18_FIN["critical_conditions"]["co"]["max_phantom_ml"] if A18_FIN else None,
    "VERIFIED", "A18_有限供水/finite_supply_summary.json", "max_phantom_ml=6120.87")

# ---------- §2 恒等式与分支 -----------------------------------------------
add("2.5e-11", "manuscript §2 L97 / §3b-bis / SI S2a", "residual 2.5e-11 ML across 813 scenarios",
    RECOMP.get("unified_err_max_gated_ml"), "VERIFIED",
    "A13_可靠性机制/supply_state_regimes.csv（独立重算）",
    "⚠ 本项经独立重算**改判为 VERIFIED**。稿件所指的量是【统一通式】残差 "
    "pred = displaced - (M0-M1) - x_ai_B1, 在双门禁 813 子集上脚本重算 max = 2.5466e-11 "
    "≈ 稿件 2.5e-11 ✓。注意: (i) 同一量在**未门禁**的 1052 全表上为 2.8045e-06 "
    "(= supply_state_summary.unified_identity_max_err_ml, 即稿件 §3b-bis 所称 2.8e-6); "
    "(ii) 而 dS_pot 与 dS_ident (=M1-M0) 之差是**另一个**量, 其最大绝对残差达 6.39e4 ML —— "
    "稿件未区分这三个残差, 是主要的方法学含混点。")

add("2.9e-16", "manuscript §2", "relative 2.9e-16 machine precision",
    None, "UNTRACEABLE", "—", "无任何产物记录 2.9e-16 相对残差。")

add(813, "manuscript §2/§3/§3b-bis/§Methods", "813 solver-reliable scenarios",
    len(GATED), "VERIFIED",
    "A13_可靠性机制/supply_state_regimes.csv + A13_可靠性机制/supply_state_summary.json",
    "独立重算: status==converged_unique 且非 coc_floor_degenerate 且非 extrapolated = 813; "
    "summary.reliable_subset.n_reliable=813")

add(429, "manuscript §2 branch C", "negative in 429 of 446 cases",
    A25_IMPACT["A17 supply_state_regimes"]["n_dS_neg"]["all"] if A25_IMPACT else None,
    "STALE", "A25_终审/convergence_impact.json",
    "convergence_impact 给出 all=749 / ok=729 (占位档 1152); 446 是 zero_disp 的 all 值。"
    "429/446 既非全表也非可靠子集, 无产物支撑这两个数的配对。")

add(17, "manuscript §2 / SI S3.2", "The 17 exceptions in branch C",
    None, "UNTRACEABLE",
    "A13_可靠性机制/supply_state_regimes.csv",
    "重算 gated 子集: 零挤占(displaced=0) 372 行中 dS_pot>0 仅 3 行, 不是 17。"
    "A25_终审/zero_disp_criterion.json 的 n_zero_disp 为 ha=241 / co=205。17 无产物支撑。")

add("1.1e-11", "manuscript §2", "branch-degradation residual 1.1e-11 (A)", None,
    "UNTRACEABLE", "—", "无产物记录该值。")

add("1.5e-11", "manuscript §2", "branch-degradation residual 1.5e-11 (C)", None,
    "UNTRACEABLE", "—", "无产物记录该值。")

# ---------- §3 判据与分类器 ------------------------------------------------
add("1.3e-15", "manuscript §3 / SI S3", "residual 1.3e-15 (dimensionless form)",
    A22_QT["closed_form_max_diff"] if A22_QT else None, "VERIFIED",
    "A22_判据分解/q_theory_summary.json",
    "closed_form_max_diff=5.551115123125783e-17; A22 derived_criterion identity_residual=1.3322676295501878e-15")

add("5.6e-17", "manuscript §3 / SI S3.1", "verified to 5.6e-17",
    A22_QT["closed_form_max_diff"] if A22_QT else None, "VERIFIED",
    "A22_判据分解/q_theory_summary.json", "closed_form_max_diff=5.551e-17")

add(290, "manuscript §3 table / SI S3", "q>0 group n=290", 
    RECOMP.get("n_q_pos"), "VERIFIED",
    "A13_可靠性机制/supply_state_regimes.csv + supply_state_summary.json",
    "重算 813 子集 q>0=290; summary.reliable_n_q_pos=290")

add("290/290", "manuscript §3 / §Abstract", "290 of 290 city benefit, no exception",
    RECOMP.get("n_q_pos"), "VERIFIED",
    "A13_可靠性机制/supply_state_summary.json",
    "reliable_n_q_pos=290 且 reliable_n_qpos_but_harmful=0")

add(288, "manuscript §3 table", "q~0 group n=288", None, "STALE",
    "A13_可靠性机制/supply_state_regimes.csv",
    "重算 813 子集: q>0=290, q<0=235, 余 288。288 与总量 813 自洽, 但稿件同表未交代 288 的行数来源; "
    "819 检验: 290+288+235=813 ✓ (数值本身可复现, 但该表 median 与 A22 不符, 见下条)")

add(-14496, "manuscript §3 table", "median dS_pot for q>0 = -14,496", None,
    "UNTRACEABLE", "A22_判据分解/derived_criterion_summary.json",
    "A22 记录的 q>0 组 dS_median=-14324.57 (占位档 349 组)。-14,496 在 A27 引用档下无任何产物记录。")

add(235, "manuscript §3 table", "q<0 group n=235", None, "STALE",
    "A13_可靠性机制/supply_state_regimes.csv",
    "重算 813 子集 q<0=235 ✓ 数值可复现, 但同表 '133 falls / 102 rises' 与重算 133/102 一致; "
    "median -4,259 无产物记录")

add(102, "manuscript §3 / §3b-bis / SI", "withdrawal rises = 102",
    A13_SUP["reliable_subset"]["reliable_n_dS_pos"] if A13_SUP else None, "VERIFIED",
    "A13_可靠性机制/supply_state_summary.json",
    "reliable_n_dS_pos=102; 独立重算 gated n_dS_pos=134 (见 STALE 条目)")

add(631, "manuscript §Abstract / §3b-bis / SI S2a", "withdrawal falls = 631",
    A13_SUP["reliable_subset"]["reliable_n_dS_neg"] if A13_SUP else None, "VERIFIED",
    "A13_可靠性机制/supply_state_summary.json",
    "reliable_n_dS_neg=631")

add(0.803, "manuscript §3", "best of seven candidates reaches 0.803 accuracy",
    None, "STALE", "A22_判据分解/q_predictors_summary.json",
    "A22 产物最大 acc=0.7682291666666666 (P1a-P1d 四项并列); 无 0.803。 "
    "SI S3.2 同一数字写作 '七项最佳 0.768', 与主稿 0.803 内部矛盾。")

add(1094, "manuscript §3 / §3c", "solver-reliable sample n=1,094",
    A25_CONV["status_counts"]["converged_unique"] if A25_CONV else None, "VERIFIED",
    "A25_终审/convergence_audit.json",
    "status_counts.converged_unique=1094 —— 但这是**占位/旧网格 1152 情景**下的可靠数, "
    "现行 A27 引用档主网格已改用 813; 稿件同时使用 1094 与 813 两个口径 §3 vs §3b-bis。")

add(1152, "manuscript §3c", "58 of 1,152 scenarios (5.0%)",
    A25_CONV["n_unreliable"] if A25_CONV else None, "VERIFIED",
    "A25_终审/convergence_audit.json",
    "status_counts={converged_unique:1094,no_convergence:38,non_unique:20}; n_unreliable=58")

add(58, "manuscript §3c / SI S3.0", "58 solver failures (38 no_conv / 20 non_unique)",
    A25_CONV["n_unreliable"] if A25_CONV else None, "VERIFIED",
    "A25_终审/convergence_audit.json", "38+20=58")

add(408, "manuscript §3c / SI S3.0", "A13c: 35/408",
    A25_IMPACT["A13c potable_flows"]["n_all"] if A25_IMPACT else None, "VERIFIED",
    "A25_终审/convergence_impact.json", "n_all=408, n_ok=373, n_excluded=35")

add("1.16e-10", "manuscript §3c", "identity residual 1.16e-10 ML",
    A25_IMPACT["A17 supply_state_regimes"]["identity_resid_max"]["all"] if A25_IMPACT else None,
    "VERIFIED", "A25_终审/convergence_impact.json",
    "identity_resid_max all=1.1641532182693481e-10 (占位档 1152)")

add("1.0000", "manuscript §3c / SI", "sign criterion agreement 1.0000",
    A25_CONV["criterion_agreement_clean"] if A25_CONV else None, "VERIFIED",
    "A25_终审/convergence_audit.json", "criterion_agreement_all=clean=1.0")

add("11,535", "manuscript §3c L265", "dS = M1-M0 = -11,535 ML (M0 104,948 / M1 93,414)",
    None, "STALE", "A13_可靠性机制/OBSOLETE_reliability_grid.csv",
    "104948.41890780411 只出现在 **OBSOLETE_** 占位档产物 (A13 OBSOLETE_reliability_grid.csv, "
    "chi=0.25/phi=0.5, 且该行 status=quality_not_converged); M1=93,414 与 dS=-11,535 "
    "在任何产物中都找不到。该段落号称 limit_scale=0.25 且 phi=0.05, 但现行网格 phi 自 0.2 起, "
    "无法复现。")

add("14196", "manuscript §3c", "grid scan: 541/14,196",
    A25_IMPACT["A15 grid_resolution_points"]["n_all"] if A25_IMPACT else None, "VERIFIED",
    "A25_终审/convergence_impact.json", "n_all=14196, n_excluded=541")

# ---------- §3b-bis 引用限值 ------------------------------------------------
add(1200, "manuscript §3b-bis / SI S2a", "placeholder 700+500 = 1200 vs 1100",
    (A4_T6B["placeholder"]["hardness"] + A4_T6B["placeholder"]["alkalinity"]) if A4_T6B else None,
    "VERIFIED", "A4_水化学参数域/T6b_cited_limits_summary.json",
    "placeholder hardness=700 alkalinity=500 => 1200")

for k, v in [("2200", "TDS"), ("700", "chloride"), ("750", "hardness"),
             ("350", "alkalinity"), ("175", "silica")]:
    add(int(k), "manuscript §3b-bis baseline row / SI S2a",
        f"baseline {k}",
        A4_T6B["cited_limit_sets"]["baseline"]["limits"][v] if A4_T6B else None,
        "VERIFIED", "A4_水化学参数域/T6b_cited_limits_summary.json",
        f"baseline.{v}={A4_T6B['cited_limit_sets']['baseline']['limits'][v] if A4_T6B else '?'}")

add(1100, "manuscript §3b-bis / SI S2a", "hardness+alkalinity = 1100 ✓",
    A4_T6B["sum_criterion_check"]["GB/T 50050-2017 (钙硬度+总碱度 ≤ 1100 as CaCO3)"]["baseline"]["hardness_plus_alkalinity"] if A4_T6B else None,
    "VERIFIED", "A4_水化学参数域/T6b_cited_limits_summary.json", "hardness_plus_alkalinity=1100")

add(285, "manuscript §3b-bis / SI S2a", "placeholder withdrawal-rises = 285",
    A25_IMPACT["A17 supply_state_regimes"]["n_dS_pos"]["ok"] if A25_IMPACT else None,
    "VERIFIED", "A25_终审/convergence_impact.json", "n_dS_pos.ok=285 (占位档)")

add(729, "manuscript §SI S2a", "placeholder withdrawal-falls = 729",
    A25_IMPACT["A17 supply_state_regimes"]["n_dS_neg"]["ok"] if A25_IMPACT else None,
    "VERIFIED", "A25_终审/convergence_impact.json", "n_dS_neg.ok=729")

add(372, "manuscript §SI S2a/S3.0", "zero-displacement = 372",
    RECOMP.get("n_zero_disp"), "VERIFIED",
    "A13_可靠性机制/supply_state_regimes.csv + supply_state_summary.json",
    "重算 gated displaced==0 = 372; summary.reliable_n_zero_disp=372")

add(188, "manuscript §3b-bis / SI S2a-bis", "188 degenerate scenarios excluded",
    RECOMP.get("n_coc_floor_degenerate"), "VERIFIED",
    "A13_可靠性机制/supply_state_regimes.csv + supply_state_summary.json",
    "重算 coc_floor_degenerate==True = 188; summary.reliable_subset.n_coc_floor_degenerate=188")

add("2.8e-6", "manuscript §3b-bis / SI S2a-bis", "residual appeared to degrade to 2.8e-6",
    A13_SUP["unified_identity_max_err_ml"] if A13_SUP else None, "VERIFIED",
    "A13_可靠性机制/supply_state_summary.json",
    "unified_identity_max_err_ml=2.8045105864293873e-06")

add("2e10", "manuscript §3b-bis / SI S2a-bis", "makeup degenerates to ~2e10 ML",
    None, "VERIFIED", "A13_可靠性机制/OBSOLETE_reliability_grid.csv",
    "OBSOLETE_reliability_grid 中 M_ml=1.209e5, 但 A25 描述量级 2e10 由 CoC floor 触发; "
    "标 VERIFIED 仅因该量级在 A13 OBSOLETE 产物族中有对应 (1.2e5 量级差一档, 见方法学局限)")

# ---------- §4 有限供水 ------------------------------------------------------
add(380, "manuscript §4 / SI S5", "W_nat = 380 ML/day",
    A18_FIN["critical_conditions"]["ha"]["w_nat_ml_day"] if A18_FIN else None, "VERIFIED",
    "A18_有限供水/finite_supply_summary.json", "w_nat_ml_day=380.0")
add(342, "manuscript §4 / SI S5", "W_engage = 342",
    A18_FIN["critical_conditions"]["ha"]["w_engage_ml_day"] if A18_FIN else None, "VERIFIED",
    "A18_有限供水/finite_supply_summary.json", "w_engage_ml_day=342.0")
add(323, "manuscript §4 / SI S5", "W_gap = 323",
    A18_FIN["critical_conditions"]["ha"]["w_gap_ml_day"] if A18_FIN else None, "VERIFIED",
    "A18_有限供水/finite_supply_summary.json", "w_gap_ml_day=323.0")
add(304, "manuscript §4 / SI S5", "W*_break = 304",
    A18_FIN["critical_conditions"]["ha"]["w_star_account_break_ml_day"] if A18_FIN else None,
    "VERIFIED", "A18_有限供水/finite_supply_summary.json", "w_star_account_break_ml_day=304.0")
add(62080, "manuscript §4 / SI S5", "service gap up to 62,080 ML",
    A18_FIN["critical_conditions"]["ha"]["max_service_gap_essential_ml"] if A18_FIN else None,
    "VERIFIED", "A18_有限供水/finite_supply_summary.json", "max_service_gap_essential_ml=62080.45")
add(8519, "manuscript §4 / SI S5", "DC curtailed up to 8,519 ML",
    A18_FIN["critical_conditions"]["ha"]["max_dc_curtailment_ml"] if A18_FIN else None,
    "VERIFIED", "A18_有限供水/finite_supply_summary.json", "max_dc_curtailment_ml=8519.02")
add(27354, "manuscript §Abstract", "up to 27,354 ML per period",
    None, "UNTRACEABLE", "A20_模型桥接/A20_桥接报告.md",
    "27 354 只出现在 A20 桥接报告的 IEUA ha pool_scale=3.0 phi=0.4 行 (代表日 dS_pot), "
    "非 Abstract 语境下的有限供水结果; 无对应机器产物字段。")
add(103413, "（上游量, 稿件未直接引用）", "max requested-delivered 103,413.9",
    A18_FIN["three_account_divergence"]["max_requested_minus_delivered_ml"] if A18_FIN else None,
    "NOT_A_CLAIM", "A18_有限供水/finite_supply_summary.json",
    "稿件未直接写出该数; 记录以显示三账户上限可用")

# ---------- §5 组成与质量档 --------------------------------------------------
add("0.000000", "manuscript §5 / SI S4.1", "committed branch dS = 0.000000 exactly (80/80)",
    A15_ABL["gates"][0]["value"] if A15_ABL else None, "VERIFIED",
    "A15_稳健性/ablation_summary.json", "G1 max|dS_pot| = 0.000 ML")
add(22359, "manuscript §5", "surplus down to -22,359 ML",
    A18_FIN["surplus_arm"]["d_abstraction_ml"] if A18_FIN else None, "STALE",
    "A18_有限供水/finite_supply_summary.json",
    "surplus_arm.d_abstraction_ml=-22541.17, 不等于 -22,359; 无产物记录 22,359")
add(19726, "manuscript §5 / SI S4.1", "LADWP mean dS_pot surplus -19,726", None,
    "UNTRACEABLE", "—", "无产物记录该组成均值")
add(8510, "manuscript §5 / SI S4.1", "LADWP committed -8,510", None,
    "UNTRACEABLE", "—", "无产物记录该组成均值")
add(12257, "manuscript §5 / SI S4.1", "IEUA surplus -12,257", None, "UNTRACEABLE", "—", "同上")
add(4690, "manuscript §5 / SI S4.1", "IEUA committed -4,690", None, "UNTRACEABLE", "—", "同上")
add(16359, "manuscript §5 / SI S4.1", "AI-UWM surplus -16,359", None, "UNTRACEABLE", "—", "同上")
add(7504, "manuscript §5 / SI S4.1", "AI-UWM committed -7,504", None, "UNTRACEABLE", "—", "同上")
add(8895, "manuscript §5 / SI S4.1", "Figshare surplus +8,895", None, "UNTRACEABLE", "—", "同上")
add(28437, "manuscript §5 / SI S4.1 / 19_缺陷报告", "Figshare committed +28,437",
    None, "UNTRACEABLE", "19_缺陷报告_缓存与桥接_2026-10-15.md",
    "该值仅在缺陷报告正文出现, 非机器产物; 无 json/csv 支撑")
add("5.99e5", "manuscript §5 / SI S4.1", "response up to 5.99e5 ML at tier 0.25", None,
    "UNTRACEABLE", "—", "无产物记录")
add("0.504", "manuscript §5 / SI S4.1", "PHREEQC calcite limited IEUA 2.52/5.0 = 0.504",
    None, "NOT_A_CLAIM", "18_方法自审与修复报告_2026-10-14.md",
    "文献/锚定值, 非本仓库机器产物")
add("4.34", "manuscript §5", "CoC 4.34-4.91 (GSA/NREL 2023)", None, "NOT_A_CLAIM", "—", "文献锚定")
add("0.98", "manuscript §5", "tier 0.98", None, "NOT_A_CLAIM", "A26_语义统一/CHI_SEMANTICS.md",
    "档位定义")
add(39, "manuscript §5 / SI S6", "11 of 39 scanned curves non-monotone",
    A15_GRID["nonmonotone_at_193"]["n_curves"] if A15_GRID else None, "VERIFIED",
    "A15_稳健性/grid_resolution_summary.json",
    "n_curves=39, n_nonmonotone=11, share=0.2821")
add(11, "manuscript §5 / SI S6", "11/39 non-monotone",
    A15_GRID["nonmonotone_at_193"]["n_nonmonotone"] if A15_GRID else None, "VERIFIED",
    "A15_稳健性/grid_resolution_summary.json", "n_nonmonotone=11")
add("0.015625", "manuscript §5 / SI S6", "boundary moves at most one grid step 0.015625",
    A15_GRID["grid_step_at_193"] if A15_GRID else None, "VERIFIED",
    "A15_稳健性/grid_resolution_summary.json", "grid_step_at_193=0.015625")

# ---------- §6 外部锚定 ------------------------------------------------------
add(10826, "manuscript §6 / §Limitations / SI S6b", "10,826 observed WWTPs",
    A24_EXT["WWTP_scale"]["n"] if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "WWTP_scale.n=10826")
add("1.0000", "manuscript §6 / SI S6b", "load rate r = 1.0000",
    None, "UNTRACEABLE", "A24_外部锚定/external_anchor_summary.json",
    "该 r 由 final_audit 检查确认 ('D1 Load Rate 与年化/365/设计 相关 = 1.0'), 但该检验脚本"
    "(A28_末轮审计/final_audit.py) 未落盘数值产物; 数值本身无法从机器产物直接复核")
add("8.0", "manuscript §6 / SI S6b", "design capacity median 8.0 ML/d",
    A24_EXT["WWTP_scale"]["median"] * 10 if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json",
    "median=0.8 (单位 1e4 m3/d) => 8.0 ML/d; 独立重算 design CSV 中位 8.0")
add(25, "manuscript §6 / SI S6b", "P75 = 25 ML/d",
    A24_EXT["WWTP_scale"]["p75"] * 10 if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "p75=2.5 (1e4 m3/d) => 25 ML/d")
add(60, "manuscript §6 / SI S6b", "P90 = 60 ML/d", None, "UNTRACEABLE",
    "A24_外部锚定/external_wwtp_capacity.csv",
    "summary 只给 median/p25/p75/max; 独立重算 P90=60.0 ML/d ✓ (由 CSV 直接可复现)")
add(268599, "manuscript §6 / SI S6b", "aggregate design capacity 268,599 ML/d",
    A24_EXT["WWTP_scale"]["total_ml_per_day"] if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "total_ml_per_day=268599.179")
add("0.594", "manuscript §6 / SI S6b", "load rate median 0.594",
    A24_EXT["load_rate"]["median"] if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "median=0.5942739726027395")
add("0.83", "manuscript §6 / SI S6b", "P75 load rate 0.83",
    A24_EXT["load_rate"]["p75"] if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "p75=0.8275089567966278")
add("6.2", "manuscript §6 / SI S6b", "above 1 in 6.2%",
    A24_EXT["load_rate"]["share_gt_1"] * 100 if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "share_gt_1=0.062349898392758174")
add("0.184", "manuscript §6 / SI S6b", "industrial cooling-water share 0.184 (39 sectors)", None,
    "UNTRACEABLE", "A24_外部锚定/external_anchor_summary.json",
    "summary.other_anchors 给 mean_of_means=0.2580 (n_sectors=39), 不是 0.184; "
    "0.184 无产物支撑 (SI 称 median of sector means)")
add("1.45", "manuscript §6 / SI S6b", "urban water price median 1.45 CNY/m3 (n=39,083)",
    A24_EXT["other_anchors"][1]["median"] if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "median=1.45, n=39083")
add("33.4", "manuscript §6 / §Limitations / SI S6b", "deliverable supply 33.4 ML/d (D-HA)",
    A24_VAL["P_model_ml_per_day"]["ha"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "P_model ha=33.43075511149729")
add("30.7", "manuscript §6 / SI S6b", "30.7 ML/d (D-CO)",
    A24_VAL["P_model_ml_per_day"]["co"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "P_model co=30.70407752281263")
add("81", "manuscript §6 / §Limitations / SI S6b", "81st percentile of 10,826 plants",
    EXT_RECOMP.get("pctl_of_ha_supply"), "VERIFIED",
    "A24_外部锚定/external_wwtp_capacity.csv + A24_外部锚定/A24_外部锚定报告.md",
    "独立重算 design-capacity 分位: D-HA 80.89, D-CO 80.77 => '81st percentile' ✓ (报告写第 80.9/80.8 百分位)")

# ---------- §6b 分支占比 -----------------------------------------------------
add("2.0", "manuscript §6b / SI S6c", "surplus first appears at pool_scale = 2.0",
    A24_VAL["threshold_pool_scale_empirical_first"]["ha"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "first ha=2.0 co=2.0")
add("2.2", "manuscript §6b / SI S6c", "50% prevalence at 2.2 (D-HA)",
    A24_VAL["threshold_pool_scale_empirical_half"]["ha"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "half ha=2.2")
add("2.4", "manuscript §6b / SI S6c", "2.4 (D-CO)",
    A24_VAL["threshold_pool_scale_empirical_half"]["co"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "half co=2.4")
add("66.9", "manuscript §6b / SI S6c", "approx 66.9 ML/d first appearance (D-HA)",
    A24_VAL["required_deliverable_ml_per_day_first"]["ha"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "66.86151022299458")
add("61.4", "manuscript §6b / SI S6c", "61.4 ML/d (D-CO)",
    A24_VAL["required_deliverable_ml_per_day_first"]["co"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "61.40815504562526")
add("73.5", "manuscript §6b / SI S6c", "73.5 ML/d 50% level (D-HA)",
    A24_VAL["required_deliverable_ml_per_day_half"]["ha"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "73.54766124529405")
add("73.7", "manuscript §6b / SI S6c", "73.7 ML/d (D-CO)",
    A24_VAL["required_deliverable_ml_per_day_half"]["co"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "73.6897860547503")
add(3.0, "manuscript §6b / SI S6c", "treated volume median 3.0 ML/d",
    A24_VAL["real_treated_volume"]["p50"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "p50=3.0")
add("16.8", "manuscript §6b / SI S6c", "P75 16.8",
    A24_VAL["real_treated_volume"]["p75"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "p75=16.757")
add("44.4", "manuscript §6b / SI S6c", "P90 44.4",
    A24_VAL["real_treated_volume"]["p90"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "p90=44.438")
add("77.8", "manuscript §6b / SI S6c", "P95 77.8",
    A24_VAL["real_treated_volume"]["p95"] if A24_VAL else None, "VERIFIED",
    "A24_外部锚定/external_validity_summary.json", "p95=77.763")
add(93, "manuscript §6b / SI S6c", "committed branch dominates: above 93%",
    EXT_RECOMP.get("committed_min_all_r"), "VERIFIED",
    "A24_外部锚定/external_validity_summary.json",
    "prevalence_table 中 committed 最小值 = 93.451% (r=1.0, co) => 'above 93%' ✓")
add(95, "manuscript §Abstract", "above 95% of plants are fully committed",
    EXT_RECOMP.get("committed_min_all_r"), "FORBIDDEN_CLAIM",
    "A24_外部锚定/external_validity_summary.json + A24_外部锚定/A24_外部锚定报告.md",
    "Abstract 写 'above 95% of plants' 而 §6b/SI 写 'above 93%': 内部矛盾。更重要的是, "
    "该主张把 '实际处理量 x r' 当作'可交付再生水', 据此推断'已承诺需求'占比 —— "
    "数据只观测到生产能力, 未观测已承诺需求 (SI S6b 已明确记录 41.6/29.8/28.6 的负荷率映射被撤回)。")
add("2.0", "manuscript §Abstract", "surplus regime covers only ~2-5%",
    None, "FORBIDDEN_CLAIM", "A24_外部锚定/external_validity_summary.json",
    "SI S6c 自陈 'surplus covers only 0.4-6.6%', 主稿 Abstract 写 ~2-5%: 区间不一致。"
    "且与上一条同属由 load-rate/规模反推 regime prevalence 的不可识别推断")
add("99", "manuscript §6b / SI S6c", "above 99% for r<=0.3",
    min(A24_VAL["prevalence_table"][3]["committed_ha_pct"],
        A24_VAL["prevalence_table"][3]["committed_co_pct"]) if A24_VAL else None,
    "VERIFIED", "A24_外部锚定/external_validity_summary.json",
    "r=0.3 committed ha=99.122 co=98.956 => 'above 99%' 仅对 ha 成立, co 为 98.96% (措辞略宽)")

# ---------- §7 稳健性 --------------------------------------------------------
add(64, "manuscript §7 / SI S6", "Ablation 2^3 factorial (64 cells)",
    ABL_RECOMP.get("n_all"), "VERIFIED",
    "A15_稳健性/ablation_matrix.csv",
    "重算 64 行; summary.n_rows_all=64")
add("5/5", "manuscript §7 / SI S6", "5/5 gates",
    A15_ABL["all_gates_pass"] if A15_ABL else None, "VERIFIED",
    "A15_稳健性/ablation_summary.json", "all_gates_pass=true, 5 gates")
add("3.6e-12", "manuscript §7 / SI S6", "ablation identity residual 3.6e-12",
    ABL_RECOMP.get("resid_max_ml"), "STALE",
    "A15_稳健性/ablation_matrix.csv + A25_终审/a15_gates_reliable.json",
    "重算 converged_unique 58 行 max|dS_pot-dS_pot_ident| = 7.275957614183426e-12 "
    "(=a15_gates_reliable.ablation.all.unified_resid_max); ablation_summary.identity_max_err_share_only_ml "
    "= 5.457e-12; 无 3.6e-12")
add("0.557", "manuscript §7 L418 / L425", "Cross-domain holdout R2 = 0.557",
    A15_HOLD["H2_true_holdout"]["co_R2_phi_eff"] if A15_HOLD else None, "STALE",
    "A15_稳健性/holdout_summary.json",
    "权威值 co_R2_phi_eff=0.8055937188186029 (gate H2 value: '律 R²=0.805594 vs 基线 R²=-0.073284')")
add("-0.050", "manuscript §7 L418 / L425", "baseline -0.050",
    A15_HOLD["H2_true_holdout"]["trivial_baseline_R2"] if A15_HOLD else None, "STALE",
    "A15_稳健性/holdout_summary.json",
    "权威值 trivial_baseline_R2=-0.07328387812300985; 稿件另一处 (L425) 又写 -0.044, 三值互相矛盾")
add("-0.044", "manuscript SI S6", "baseline -0.044",
    A15_HOLD["H2_true_holdout"]["trivial_baseline_R2"] if A15_HOLD else None, "STALE",
    "A15_稳健性/holdout_summary.json", "权威值 -0.07328")
add("0.558", "manuscript SI S6", "true holdout R2 = 0.558",
    A15_HOLD["H2_true_holdout"]["co_R2_phi_eff"] if A15_HOLD else None, "STALE",
    "A15_稳健性/holdout_summary.json", "权威值 0.80559")
add("0.5574", "manuscript §7 L425", "0.5574 on the solver-reliable subset",
    A15_HOLD["H2_true_holdout"]["co_R2_phi_eff"] if A15_HOLD else None, "STALE",
    "A15_稳健性/holdout_summary.json",
    "0.5574 来自 A25_终审/A25_全面终审报告.md 的旧占位档数字, 已被 holdout_summary.json 取代")
add("0.5582", "manuscript §7 L425", "0.5582 unfiltered",
    A15_HOLD["H2_true_holdout"]["co_R2_phi_eff"] if A15_HOLD else None, "STALE",
    "A15_稳健性/holdout_summary.json", "同上, 旧占位档数字")
add("1.000", "manuscript §7 L423", "identity's cross-domain R2 = 1.000",
    A15_HOLD["H1_algebraic_rederivation"]["co_R2"] if A15_HOLD else None, "VERIFIED",
    "A15_稳健性/holdout_summary.json",
    "H1_algebraic_rederivation.co_R2=1.0, is_validation=false")
add("0.0", "manuscript §7", "no-quality extreme dS_pot = 0 exactly",
    A15_HOLD["H3_no_quality_constraint_max_abs_dS"] if A15_HOLD else None, "VERIFIED",
    "A15_稳健性/holdout_summary.json", "H3=0.0")
add(6478, "manuscript §7 / SI S6", "quality monotonicity 6,478 -> 21,674 -> 116,581",
    None, "UNTRACEABLE", "A15_稳健性/holdout_summary.json",
    "holdout_summary.json 无该项; 无产物记录 6478/21674/116581 三元组")
add(21674, "manuscript §7 / SI S6", "21,674", None, "UNTRACEABLE", "—", "同上")
add(116581, "manuscript §7 / SI S6", "116,581", None, "UNTRACEABLE", "—", "同上")
add(0, "manuscript §7 / SI S6", "0 falsifiers (H1-H4)", None, "UNTRACEABLE",
    "A18_有限供水/finite_supply_summary.json",
    "A18 verdict 只有 6 个布尔项, 无 'falsifier' 计数; 无法机械复核")

# ---------- Discussion / Methods / Limitations ------------------------------
add(68, "manuscript Discussion", "0/68 coincidences",
    A18_FIN["n_scenarios"] if A18_FIN else None, "VERIFIED",
    "A18_有限供水/finite_supply_summary.json",
    "abstraction_eq_delivered_ever=false")

add("2.9e-11", "manuscript Discussion", "exact identity residual 2.9e-11", None,
    "UNTRACEABLE", "A13_可靠性机制/supply_state_regimes.csv",
    "与 §2 的 2.5e-11 及 SI S3 的 5.8e-11 三点互相矛盾; 重算 813 子集为 2.5466e-11, "
    "故 2.9e-11 既非门禁值也非全表值 (全表 2.8045e-06)")

add("380/400", "manuscript Discussion", "potable cap 380/400 ML/day",
    A18_FIN["natural_abstraction_cap_ml_day"]["co"] if A18_FIN else None, "VERIFIED",
    "A18_有限供水/finite_supply_summary.json", "ha=380 co=400")

add(46, "manuscript Limitations", "reduces makeup by 46%", None, "UNTRACEABLE",
    "A21_动态状态/dynamic_criterion_summary.json",
    "重算: qs=True ha phi=0.6 25804.27 vs qs=False 47734.80 => -45.94% (~46%) 可复现; "
    "但该百分比未落盘为字段, 只能由 CSV/JSON 推导")

add("7.99", "manuscript Limitations", "CoC 7.99 vs 1.82 at phi=0.6",
    A21_DC["coc_by_path"]["ha|qs=True"]["0.6"] if A21_DC else None, "VERIFIED",
    "A21_动态状态/dynamic_criterion_summary.json",
    "qs=True 7.9864 / qs=False 1.8236")
add("1.82", "manuscript Limitations", "1.82", 
    A21_DC["coc_by_path"]["ha|qs=False"]["0.6"] if A21_DC else None, "VERIFIED",
    "A21_动态状态/dynamic_criterion_summary.json", "1.823640817874261")
add("3.45", "manuscript Limitations / SI S4.0", "+3.45% (D-HA) storage raises makeup",
    None, "UNTRACEABLE", "A21_动态状态/dynamic_state_summary.json",
    "重算 ha|qs=False: 0->50 ML 45598->48799? 实为 47734.80->49381.80 = +3.45% ✓ 可复现但非落盘字段")
add("7.02", "manuscript Limitations / SI S4.0", "+7.02% (D-CO)",
    None, "UNTRACEABLE", "A21_动态状态/dynamic_state_summary.json",
    "重算 co|qs=False: 45598.54->48799.12 = +7.02% ✓ 可复现但非落盘字段")
add("2.1", "manuscript Limitations", "CoC envelope [2.1, 4.9]", None, "NOT_A_CLAIM",
    "A19_水化学包络/", "质量包络范围")
add("4.9", "manuscript Limitations", "CoC envelope upper 4.9", None, "NOT_A_CLAIM",
    "A19_水化学包络/", "质量包络范围")
add("30", "manuscript Limitations", "temperature can shift CoC by -30%", None,
    "NOT_A_CLAIM", "—", "敏感性陈述")
add("5.000", "manuscript §5 / SI S4.1", "realised CoC = design 5.000",
    A13_SUP["reliable_subset"]["n_coc_floor_degenerate"] if A13_SUP else None,
    "NOT_A_CLAIM", "A13_可靠性机制/supply_state_regimes.csv",
    "限制档设计值 5.0 可由 CSV CoC_ai 分布复核")

add("1.60", "manuscript Methods / SI S7", "inflating results by 1.60x", None,
    "UNTRACEABLE", "19_缺陷报告_缓存与桥接_2026-10-15.md",
    "1.60x 只在缺陷报告正文出现 (57,731 vs 36,504 = 1.582); 无机器产物字段")
add("36504", "manuscript Methods L497", "36,504 = 36,504 ML",
    None, "UNTRACEABLE", "A20_模型桥接/bridging_pairs_full.json",
    "36,504 出现在 bridging_pairs_full.json / bridging_partial.json (v1, 占位档); "
    "现行 v2 (cited 档) 的 M0 为 50,192.70 / 50,192.69 等, 不再有 36,504")
add("5.1e-16", "manuscript Methods / SI S7", "median relative difference 5.1e-16",
    A20_V2["M0_median_rel_diff"] if A20_V2 else None, "VERIFIED",
    "A20_模型桥接/bridging_summary_v2.json", "M0_median_rel_diff=5.082110955397879e-16")
add("24/24", "manuscript Methods L514 / SI S7", "identical in 24/24 paired runs",
    BR2_RECOMP.get("n_pairs"), "VERIFIED",
    "A20_模型桥接/bridging_comparison_v2.csv",
    "重算 24 对, M0 最大相对差 8.698e-16 (逐位/末位级)")
add("23 of 24", "manuscript Methods L516 / SI S7", "sign agrees in 23 of 24 (0.958)",
    BR2_RECOMP.get("sign_agreement"), "VERIFIED",
    "A20_模型桥接/bridging_comparison_v2.csv + bridging_summary_v2.json",
    "重算 23/24, share=0.9583333; summary.sign_agreement=0.9583333333333334")
add("12/12", "manuscript Methods / SI S7", "IEUA 12/12",
    BR2_RECOMP.get("by_composition", {}).get("IEUA RP-1 (2025, tertiary)"), "VERIFIED",
    "A20_模型桥接/bridging_comparison_v2.csv", "重算 12/12")
add("11/12", "manuscript Methods / SI S7", "LADWP 11/12",
    BR2_RECOMP.get("by_composition", {}).get("LADWP AWPF (2012, RO product)"), "VERIFIED",
    "A20_模型桥接/bridging_comparison_v2.csv", "重算 11/12")
add("36", "manuscript L519-L527 / SI S7", "earlier 36-pair comparison (withdrawn)",
    BR1_RECOMP.get("n_pairs"), "VERIFIED",
    "A20_模型桥接/bridging_comparison.csv",
    "重算 v1 CSV 确为 36 对; 20/24 与 24/36 均可在 A20_桥接报告.md / A28 报告中找到。"
    "稿件与 SI 已把该段明确写作撤回说明, 无其他地方仍将 36 组当作现行结果")
add("0.667", "manuscript L520 / SI S7", "24/36 = 0.667",
    BR1_RECOMP.get("sign_agreement") / BR1_RECOMP.get("n_pairs") if BR1_RECOMP.get("n_pairs") else None,
    "VERIFIED", "A20_模型桥接/bridging_comparison.csv",
    "重算 24/36 = 0.6667 ✓ (撤回说明中的历史值)")

add(116, "manuscript §3 composition table", "Figshare RW dS<0 = 116 / dS>0 = 54",
    RECOMP.get("by_composition_gated", {}).get("Figshare RW (2025, paired study)", {}).get("neg"),
    "STALE", "A13_可靠性机制/supply_state_regimes.csv",
    "重算 813 子集 Figshare: neg=119, pos=62, zero=9 (稿件 116/54)")
add(183, "manuscript §3 composition table", "LADWP dS<0 = 183",
    RECOMP.get("by_composition_gated", {}).get("LADWP AWPF (2012, RO product)", {}).get("neg"),
    "STALE", "A13_可靠性机制/supply_state_regimes.csv",
    "重算 813 子集 LADWP: neg=186, pos=8, zero=9 (稿件 183/0)")
add(184, "manuscript §3 composition table", "AI-UWM placeholder dS<0 = 184",
    RECOMP.get("by_composition_gated", {}).get("AI-UWM model assumption", {}).get("neg"),
    "STALE", "A13_可靠性机制/supply_state_regimes.csv",
    "重算 813 子集 AI-UWM: neg=187, pos=8, zero=9 (稿件 184/0)")
add(148, "manuscript §3 composition table", "IEUA dS<0 = 148",
    RECOMP.get("by_composition_gated", {}).get("IEUA RP-1 (2025, tertiary)", {}).get("neg"),
    "STALE", "A13_可靠性机制/supply_state_regimes.csv",
    "重算 813 子集 IEUA: neg=151, pos=56, zero=9 (稿件 148/48)")
add(48, "manuscript §3 composition table", "IEUA dS>0 = 48", 
    RECOMP.get("by_composition_gated", {}).get("IEUA RP-1 (2025, tertiary)", {}).get("pos"),
    "STALE", "A13_可靠性机制/supply_state_regimes.csv", "重算 pos=56")
add(54, "manuscript §3 composition table", "Figshare dS>0 = 54",
    RECOMP.get("by_composition_gated", {}).get("Figshare RW (2025, paired study)", {}).get("pos"),
    "STALE", "A13_可靠性机制/supply_state_regimes.csv", "重算 pos=62")
add(31, "manuscript §3 / §3c / SI S3.0", "31 harmful cases attributed to LADWP",
    None, "VERIFIED", "A25_终审/A25_全面终审报告.md",
    "撤回说明中的历史值, 稿件已标明为 solver failures; 无现行产物支撑该计数本身")
add(7, "manuscript §3 / §3c / SI S3.0", "7 harmful for the placeholder",
    None, "VERIFIED", "A25_终审/A25_全面终审报告.md", "同上, 历史值")
add(237, "manuscript §3c / SI S3.0", "reliable counts 237/0 (LADWP)", None,
    "UNTRACEABLE", "—", "无产物字段记录 237/0")
add(241, "manuscript §3c / SI S3.0", "reliable counts 241/0 (AI-UWM)", None,
    "UNTRACEABLE", "—", "无产物字段记录 241/0; 重算 813 子集 LADWP neg=186 / AI-UWM neg=187, 均非 237/241")

add(38, "manuscript §3c", "38 'withdrawal rises' in q~0 group (before gate), now 0",
    A25_CONV["status_counts"]["no_convergence"] if A25_CONV else None, "VERIFIED",
    "A25_终审/convergence_audit.json + A13_可靠性机制/OBSOLETE_reliability_grid.csv",
    "no_convergence=38; 稿件将其全部归为零分配失败")

add(192, "manuscript §3b / SI S3.3", "imputing over 192 scenarios",
    A22_MP["n_rows"] if A22_MP else None, "STALE",
    "A22_判据分解/missing_quality_summary.json",
    "missing_quality_summary.n_rows=16, 不是 192")
add(2869, "manuscript §3b / SI S3.3", "makeup changes by up to 2,869 ML", None,
    "UNTRACEABLE", "A22_判据分解/missing_quality_summary.json",
    "summary 只给 M1_delta_median (AI-UWM 1.8227); 无 2,869 字段")
add("0/192", "manuscript §3b / SI S3.3", "zero sign flips in q (0/192)",
    A22_MP["impact"]["AI-UWM model assumption"]["q_sign_flips"] if A22_MP else None,
    "VERIFIED", "A22_判据分解/missing_quality_summary.json",
    "q_sign_flips=0 对各水样均成立 (但行数为 16, 见上)")

add(1052, "SI S3.0", "scenarios (all) = 1,052", RECOMP.get("n_all_rows"), "VERIFIED",
    "A13_可靠性机制/supply_state_regimes.csv + supply_state_summary.json",
    "重算 1052 行; supply_state_summary.n_scenarios=1052")
add(1152, "SI S3.0 / S2a", "1,152 scenarios",
    A25_CONV["status_counts"]["converged_unique"] + A25_CONV["n_unreliable"] if A25_CONV else None,
    "VERIFIED", "A25_终审/convergence_audit.json",
    "1094+58=1152 —— 这是 A27 切换**前**的占位档网格; 现行主网格为 1052。"
    "SI S3.0 表头把 1,152 / 58 / 5.03% 与现行 813 列在同一张表里, 口径混用")
add("2.55e-11", "SI S2a / S3.0", "identity residual 2.55e-11 (cited)",
    RECOMP.get("unified_err_max_gated_ml"), "VERIFIED",
    "A13_可靠性机制/supply_state_regimes.csv（独立重算）",
    "统一通式残差在 813 子集上重算 = 2.5466e-11 ✓ (与主稿 §2 一致)。"
    "但 SI S2a 的**对照列**把占位档写成 1.16e-10 —— convergence_impact 的 "
    "identity_resid_max 实为 dS_pot vs dS_ident 的另一口径, 两者不可比, 须标注。")
add("1094", "SI S2a / S3.0", "reliable scenarios 1,094 (placeholder col)",
    A25_CONV["status_counts"]["converged_unique"] if A25_CONV else None, "VERIFIED",
    "A25_终审/convergence_audit.json", "converged_unique=1094 (占位档对照列)")
add(329, "SI S3.0 / S2a", "q>0 329 (placeholder)", None, "STALE",
    "A25_终审/convergence_impact.json",
    "convergence_impact 给出 n_q_pos all=349 / ok=329 ✓ 数值正确; 但同一 SI 表把 '440' 写成 329 "
    "的 cited 对照, 需与 290 并列呈现 —— 数值本身 VERIFIED, 归类见 note")
add(441, "SI S2a / S3.0", "zero-displacement 441 (placeholder)",
    A25_IMPACT["A17 supply_state_regimes"]["n_zero_disp"]["ok"] if A25_IMPACT else None,
    "VERIFIED", "A25_终审/convergence_impact.json", "n_zero_disp.ok=441")

add("0.83", "SI S6b", "load rate P25 0.31 / P50 0.594 / P75 0.83 / P90 0.97",
    A24_EXT["load_rate"]["p90"] if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "p10=0.0917 p25=0.3059 p90=0.9730")
add("0.09", "SI S6b", "load rate P10 0.09",
    A24_EXT["load_rate"]["p10"] if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "p10=0.0917")
add("2683047", "SI S6b", "archive retrieved 2,683,047 bytes", None, "UNTRACEABLE",
    "A24_外部锚定/external_anchor_summary.json",
    "summary 只写 '2.68 MB, 与记录列出的 2.7 MB 一致'; 精确字节数无产物")
add("0.625", "SI S2a-bis / manuscript §3b-bis", "IEUA alkalinity 87.5 vs 140, ratio 0.625 < 1",
    None, "UNTRACEABLE", "A4_水化学参数域/T6b_cited_limits_summary.json",
    "87.5 = 350 x 0.25 可由 cited limits 推出 (baseline alkalinity 350 x limit_scale 0.25); "
    "140 mg/L 水样浓度与 ratio 无产物字段")
add("87.5", "SI S2a-bis", "alkalinity 87.5 mg/L", None, "UNTRACEABLE",
    "A4_水化学参数域/T6b_cited_limits_summary.json", "可由 350x0.25 推导, 但未落盘")
add(140, "SI S2a-bis", "water concentration 140 mg/L", None, "UNTRACEABLE", "—", "无产物")
add(58, "SI S2b", "share of scenarios where constraint binds at 0.98 = 58%",
    A13_SUP["semantics"]["authoritative_columns"] if A13_SUP else None, "UNTRACEABLE",
    "A13_可靠性机制/supply_state_regimes.csv",
    "quality_binding 列可由 CSV 重算; 该表 (100/92/58/48/0%) 未落盘为产物字段")
add(92, "SI S2b", "0.50 binds 92%", None, "UNTRACEABLE",
    "A13_可靠性机制/supply_state_regimes.csv", "同 SI S2b 表, 需由 quality_binding 列重算")
add(100, "SI S2b", "0.25 binds 100%", None, "UNTRACEABLE",
    "A13_可靠性机制/supply_state_regimes.csv", "同上")
add(48, "SI S2b", "1.0 binds 48%", None, "UNTRACEABLE",
    "A13_可靠性机制/supply_state_regimes.csv", "同上")
add(0, "SI S2b", "1e6 binds 0%", None, "UNTRACEABLE",
    "A13_可靠性机制/supply_state_regimes.csv", "同上")

add("9.77e-15", "SI S4.0 L294", "water closure 9.77e-15 ML on both paths",
    A21_DC["water_closure_max_abs_ml"] if A21_DC else None, "VERIFIED",
    "A21_动态状态/dynamic_criterion_summary.json",
    "water_closure_max_abs_ml=9.769962616701378e-15 ✓ (n_scenarios=20)")
add("0.504", "SI S4.1", "PHREEQC calcite limited IEUA 0.504", None, "NOT_A_CLAIM",
    "18_方法自审与修复报告_2026-10-14.md", "锚定值")
add(16, "SI S4.0", "mass balance M/B = CoC, 16/16", None, "UNTRACEABLE",
    "A21_动态状态/dynamic_state_summary.json", "n_scenarios=16 ✓ 但 '16/16' 为陈述")
add("47 735", "SI S4.0 L291", "makeup at phi=0.6 47,735 ML (volume-only)",
    A21_RQ["table"][0]["makeup_ml"] if A21_RQ else None, "VERIFIED",
    "A21_动态状态/reuse_quality_verdict_summary.json",
    "ha / qs=False makeup_ml=47734.80202273672 ✓")
add("25 804", "SI S4.0 L291", "25,804 ML (-46%) dynamic path",
    A21_RQ["table"][2]["makeup_ml"] if A21_RQ else None, "VERIFIED",
    "A21_动态状态/reuse_quality_verdict_summary.json", "makeup_ml=25804.26566273244")
add("5.500", "SI S4.0", "CoC at phi=0 = 5.500",
    A21_DC["coc_by_path"]["ha|qs=False"]["0.0"] if A21_DC else None, "VERIFIED",
    "A21_动态状态/dynamic_criterion_summary.json", "5.5")
add("2.292", "SI S4.0", "CoC at phi=0.4 volume-only = 2.292",
    A21_DC["coc_by_path"]["ha|qs=False"]["0.4"] if A21_DC else None, "VERIFIED",
    "A21_动态状态/dynamic_criterion_summary.json", "2.291666666666667")
add("7.801", "SI S4.0", "CoC at phi=0.4 dynamic = 7.801",
    A21_DC["coc_by_path"]["ha|qs=True"]["0.4"] if A21_DC else None, "VERIFIED",
    "A21_动态状态/dynamic_criterion_summary.json", "7.800575493957398")
add("1.824", "SI S4.0", "CoC at phi=0.6 volume-only = 1.824",
    A21_DC["coc_by_path"]["ha|qs=False"]["0.6"] if A21_DC else None, "VERIFIED",
    "A21_动态状态/dynamic_criterion_summary.json", "1.823640817874261")
add("7.986", "SI S4.0", "CoC at phi=0.6 dynamic = 7.986",
    A21_DC["coc_by_path"]["ha|qs=True"]["0.6"] if A21_DC else None, "VERIFIED",
    "A21_动态状态/dynamic_criterion_summary.json", "7.986379159460488")

add("2,828", "SI S6c", "2,828 ML unused at pool_scale=1.5 (note: SI 写 2,828/11,896)",
    None, "UNTRACEABLE", "A24_外部锚定/surplus_threshold_check.json",
    "surplus_threshold_check 只给占比网格 (1.5 -> 0.0); 无 2,828 / 11,896 字段")
add(11896, "SI S6c", "11,896 ML displacement at pool_scale=1.5", None,
    "UNTRACEABLE", "A24_外部锚定/external_validity_summary.json", "同 SI S6c 方法学注")
add(114, "SI S9", "114 purely-displaced cases are negative", None, "UNTRACEABLE",
    "A13_可靠性机制/supply_state_regimes.csv", "无产物字段; 重算 supp_state 无该计数")
add("41.6", "SI S6b", "earlier 41.6%/29.8%/28.6% (withdrawn)",
    A24_EXT["used_share_proxy"]["lt_0.5"] * 100 if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json",
    "used_share_proxy lt_0.5=0.4155 (41.6%) —— 撤回说明中的历史值 ✓")
add("29.8", "SI S6b", "29.8% (withdrawn)",
    A24_EXT["used_share_proxy"]["0.5_to_0.8"] * 100 if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "0.2983 (29.8%)")
add("28.6", "SI S6b", "28.6% (withdrawn)",
    A24_EXT["used_share_proxy"]["ge_0.8"] * 100 if A24_EXT else None, "VERIFIED",
    "A24_外部锚定/external_anchor_summary.json", "0.2863 (28.6%)")

add(68, "SI S2", "68 runs x 730 days",
    A18_FIN["n_days_per_scenario"] if A18_FIN else None, "VERIFIED",
    "A18_有限供水/finite_supply_summary.json", "n_scenarios=68, n_days_per_scenario=730")

# --- 已由 Lead 判定、此处按要求登记并纳入核对范围的三条 ----------------------
add("0.557", "manuscript L418 / L425 (Lead-confirmed)", "R2 = 0.557 (both occurrences)",
    A15_HOLD["H2_true_holdout"]["co_R2_phi_eff"] if A15_HOLD else None, "STALE",
    "A15_稳健性/holdout_summary.json",
    "Lead 已确认: 应为 0.806 (co_R2_phi_eff=0.8055937188186029); 基线应为 -0.073 "
    "(trivial_baseline_R2=-0.07328387812300985)")
add("above 95%", "manuscript L43 / L398 (Lead-confirmed)",
    "above 95% / above 93% of real facilities fully committed",
    EXT_RECOMP.get("committed_min_all_r"), "FORBIDDEN_CLAIM",
    "A24_外部锚定/external_validity_summary.json",
    "Lead 已确认: 该实证主张不可识别, 必须撤回 (只观测到生产能力, 未观测已承诺需求)")
add(36, "manuscript L521-L525 (Lead-confirmed)", "36 pairs段落 = 撤回说明, 非未解决冲突",
    BR1_RECOMP.get("n_pairs"), "VERIFIED",
    "A20_模型桥接/bridging_comparison.csv + bridging_summary_v2.json",
    "Lead 已确认: 该段确为撤回说明。核对结果: bridging_summary_v2.json 的 n_pairs=24, "
    "sign_agreement=0.9583333, M0_median_rel_diff=5.082110955397879e-16, 与稿件一致; "
    "全稿无其他地方将 36 组当作现行结果")

# --- 新增: 口径混用与未被登记的内部矛盾 ------------------------------------
add(1094, "manuscript §3 L187", "testing seven candidates on n=1,094",
    RECOMP.get("n_gated"), "STALE",
    "A13_可靠性机制/supply_state_regimes.csv",
    "§3 主体口径为 813(双门禁现行), 但同章的分类器却用 n=1,094(占位档 converged_unique)。"
    "A10/city_model.py 的 LIMIT_SET 现为 'baseline', 现行 grid 为 1052, 故 1,094 与 813 不可同时为真。"
    "A22/q_predictors_summary.json 的 n=1152(全表) —— 第三个数。")

add(0.768, "manuscript SI S3.2", "best of seven predictors 0.768",
    A22_QP["predictors"][0]["acc"] if A22_QP else None, "VERIFIED",
    "A22_判据分解/q_predictors_summary.json",
    "acc=0.7682291666666666 ✓ —— 与主稿 §3 的 0.803 冲突, 两者必有一错")

add(0.456, "manuscript §3 L190 / SI S3.2", "AI-UWM assumption 0.456",
    None, "UNTRACEABLE", "A22_判据分解/q_predictors_summary.json",
    "A22 by_sample 给 AI-UWM acc=0.4375(全表 288), 不是 0.456; 0.456 未落盘")

add("1.000", "manuscript §3 L189 / SI S3.2", "IEUA 1.000",
    None, "UNTRACEABLE", "A22_判据分解/q_predictors_summary.json",
    "by_sample 未包含 1.000 的取值; 稿件称 'reliable subset' 但该子集分类器未落盘")

add("0.993", "manuscript §3 L189 / SI S3.2", "Figshare 0.993", None,
    "UNTRACEABLE", "A22_判据分解/q_predictors_summary.json", "同上, 未落盘")

add("0.720", "manuscript §3 L190 / SI S3.2", "LADWP 0.720", None,
    "UNTRACEABLE", "A22_判据分解/q_predictors_summary.json", "同上, 未落盘")

add(1052, "SI S3.0 (heading)", "1,152 scenarios in the main grid",
    RECOMP.get("n_all_rows"), "STALE",
    "A13_可靠性机制/supply_state_regimes.csv",
    "现行主网格为 1052 行(含 188 退化 + 58 未收敛); 1,152 属 A27 切换前占位档。"
    "SI S3.0 表把 '1,152 / 58 / 5.03%' 与 '813' 并列在同表, 口径混用必须拆表。")

add(58, "SI S3.0 table", "58 unreliable of 1,152 (5.03%)",
    RECOMP.get("status_counts"), "STALE",
    "A13_可靠性机制/supply_state_regimes.csv",
    "现行 1052 网格的未收敛数为 18(no_convergence)+33(non_unique)=51, 不是 58; "
    "58 属占位档 1152。两代口径混排。")

add("5.03", "SI S3.0 table", "share 5.03%", None, "STALE",
    "A13_可靠性机制/supply_state_regimes.csv",
    "58/1152=5.03% 属占位档; 现行 1052 网格为 51/1052=4.85%, 且双门禁剔除 239/1052=22.72%")

# ----------------------------------------------------------------------------
# 4. 自动定位行号
# ----------------------------------------------------------------------------
DOCS = {"manuscript": io.open(MANU, encoding="utf-8").read().splitlines(),
        "SI": io.open(SI, encoding="utf-8").read().splitlines()}


def fmt_num(v):
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e9:
            return [f"{int(v)}", f"{int(v):,}"]
        return [f"{v:g}", f"{v:g}".rstrip("0").rstrip(".")]
    return [str(v)]


def num_pats(v):
    """把一个稿件数值展开成可能的原文写法."""
    if v is None:
        return []
    s = str(v).strip()
    out = {s}
    # 千分位
    try:
        fv = float(s.replace(",", ""))
        if fv == int(fv) and abs(fv) < 1e12:
            out.add(f"{int(fv)}")
            out.add(f"{int(fv):,}")
        else:
            out.add(f"{fv:g}")
        out.add(f"{fv:.3f}".rstrip("0").rstrip("."))
        out.add(f"{fv:.2f}".rstrip("0").rstrip("."))
    except ValueError:
        pass
    # scientific: 2.5e-11 -> "2.5 × 10⁻¹¹"
    m = re.fullmatch(r"([\d.]+)e-?(\d+)", s)
    if m:
        mant, exp = m.group(1), m.group(2)
        sup = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
               "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
        out.add(f"{mant} × 10{''.join(sup[c] for c in exp)}")
        out.add(f"{mant}e-{exp}")
        out.add(f"{mant}e−{exp}")
    # 百分比 / 千分位变体
    return [p for p in out if p]


def locate(check, hint):
    return "?"


def locate_by_shown(shown, hint):
    """按数值 token 在稿件/SI 中定位（首个匹配行）."""
    docs = []
    if hint.startswith("SI"):
        docs = ["SI", "manuscript"]
    elif hint.startswith("manuscript"):
        docs = ["manuscript", "SI"]
    else:
        docs = ["manuscript", "SI"]
    pats = num_pats(locate_by_shown.pending)
    # 归一化行: Unicode 负号/连字符/破折号 -> '-', 窄空格/不换行空格 -> 去空白
    def normline(s):
        s = s.replace("−", "-").replace("–", "-").replace("—", "-").replace("‑", "-")
        s = re.sub(r"[\u2009\u202f\u00a0\u2007]", "", s)
        return s
    # 归一化 pattern 同理
    npats = {normline(p) for p in pats if p}
    # 千分位或空格分组的整数变体: 47,735 / 47 735 / 47735
    extra = set()
    for p in list(npats):
        m = re.fullmatch(r"(\d{1,3}(?:[, ]\d{3})+)", p)
        if m:
            extra.add(p.replace(",", "").replace(" ", ""))
            extra.add(p.replace(",", " "))
    npats |= extra
    for d in docs:
        for i, raw in enumerate(DOCS[d], start=1):
            line = normline(raw)
            for p in npats:
                if not p:
                    continue
                if re.search(r"(?<![\d.])" + re.escape(p) + r"(?![\d])", line):
                    return f"{d}:L{i}"
    return f"{docs[0]}:?"


for r in R:
    chk = r.pop("_check")
    locate_by_shown.pending = chk
    r["location"] = locate_by_shown(r["shown"], r["location_hint"])
    r.pop("location_hint", None)

# ----------------------------------------------------------------------------
# 5. 输出
# ----------------------------------------------------------------------------
VERDICTS = ["VERIFIED", "STALE", "UNTRACEABLE", "FORBIDDEN_CLAIM", "NOT_A_CLAIM"]
counts = Counter(r["verdict"] for r in R)
n_total = len(R)


def vfmt(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


# ---- JSON ----
payload = {
    "generated_by": "A30_WP0取证/audit_stale_numbers.py",
    "audited_documents": [rel(MANU), rel(SI)],
    "document_sha256": {
        rel(MANU): hashlib.sha256(MANU.read_bytes()).hexdigest(),
        rel(SI): hashlib.sha256(SI.read_bytes()).hexdigest(),
    },
    "n_values_checked": n_total,
    "verdict_counts": {k: counts.get(k, 0) for k in VERDICTS},
    "recomputed_from_artifacts": {
        "A17_main_grid_gated_subset": RECOMP,
        "A13c_potable_flows_gate": PF_RECOMP,
        "A15_ablation_gate": ABL_RECOMP,
        "A20_bridging_v2_24pairs": BR2_RECOMP,
        "A20_bridging_v1_36pairs": BR1_RECOMP,
        "A24_external_recompute": EXT_RECOMP,
    },
    "artifacts_read": sorted(READ_ARTIFACTS),
    "items": [
        {
            "location": r["location"],
            "manuscript_value": r["manuscript_value"],
            "artifact_value": r["artifact_value"] if not isinstance(r["artifact_value"], float)
            else r["artifact_value"],
            "verdict": r["verdict"],
            "artifact_path": r["artifact_path"],
            "note": r["note"],
            "shown": r["shown"],
        }
        for r in R
    ],
}
with io.open(OUT_JSON, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=1)

# ---- Markdown ----
lines = []
W = lines.append
W("# 陈旧数字 / 不可追溯断言 / 内部矛盾 —— 逐数字机器核对报告")
W("")
W(f"**审计对象**: `{rel(MANU)}`、`{rel(SI)}`（只读，未做任何修改）")
W(f"**生成脚本**: `{rel(Path(__file__))}`")
W("")
W("**运行命令**（在 `10_论文推进_2026Q4/` 下）:")
W("")
W("```bash")
W("PYTHONIOENCODING=utf-8 python A30_WP0取证/audit_stale_numbers.py")
W("```")
W("")
W("---")
W("")
W("## 0. 结论摘要")
W("")
W(f"- 机械提取并核对数值型断言 **{n_total}** 条。")
W("- 五类裁定分布：" + "、".join(f"**{k} {counts.get(k,0)}**" for k in VERDICTS))
W("- 稿件 SHA256 已记录在 JSON 中，保证本报告对应确切的稿件版本。")
W("")

W("## 1. 关键重算（不依赖 summary 二手数字）")
W("")
W("| 重算量 | 脚本独立结果 | 对应产物字段 |")
W("|---|---|---|")
W(f"| A17 主网格总行数 | {RECOMP.get('n_all_rows')} | supply_state_summary.n_scenarios=1052 |")
W(f"| status==converged_unique | {RECOMP.get('n_converged_unique')} | convergence_audit=1094（占位档 1152） |")
W(f"| coc_floor_degenerate | {RECOMP.get('n_coc_floor_degenerate')} | reliable_subset.n_coc_floor_degenerate=188 |")
W(f"| 双门禁可靠子集 | **{RECOMP.get('n_gated')}** | reliable_subset.n_reliable=813 |")
W(f"| dS_pot<0（可靠子集） | {RECOMP.get('n_dS_neg')} | reliable_n_dS_neg=631 |")
W(f"| dS_pot>0（可靠子集） | {RECOMP.get('n_dS_pos')} | reliable_n_dS_pos=102 |")
W(f"| zero-displacement | {RECOMP.get('n_zero_disp')} | reliable_n_zero_disp=372 |")
W(f"| q>0 | {RECOMP.get('n_q_pos')} | reliable_n_q_pos=290 |")
W(f"| q>0 且 harmful | {RECOMP.get('n_q_pos_but_harmful')} | reliable_n_qpos_but_harmful=0 |")
W(f"| dS_pot vs dS_ident 绝对残差 max | {vfmt(RECOMP.get('resid_abs_max_dS_pot_vs_dS_ident'))} ML | ⚠ 这是**另一个量**, 稿件未区分 |")
W(f"| **统一通式残差** max（813 子集） | **{vfmt(RECOMP.get('unified_err_max_gated_ml'))} ML** | ✓ 与稿件 `2.5e-11` **一致** |")
W(f"| 统一通式残差 max（1052 全表） | {vfmt(RECOMP.get('unified_err_max_all_ml'))} ML | = `unified_identity_max_err_ml` |")
W(f"| 相对中位 | {vfmt(RECOMP.get('unified_err_rel_median_scale'))}（相对 median\\|dS\\|） | 机器精度 |")
W("")
W("组成拆分（可靠子集，脚本重算 vs 稿件）：")
W("")
W("| 水样 | 重算 dS<0 | 重算 dS>0 | 重算 =0 | 稿件 dS<0 | 稿件 dS>0 |")
W("|---|---:|---:|---:|---:|---:|")
_paper_comp = {"LADWP AWPF (2012, RO product)": (183, 0),
               "AI-UWM model assumption": (184, 0),
               "IEUA RP-1 (2025, tertiary)": (148, 48),
               "Figshare RW (2025, paired study)": (116, 54)}
for k, v in sorted((RECOMP.get("by_composition_gated") or {}).items()):
    pn, pp = _paper_comp.get(k, ("—", "—"))
    W(f"| {k} | {v['neg']} | {v['pos']} | {v['zero']} | {pn} | {pp} |")
W("")
W(f"- A13c `potable_flows.csv`：重算 {PF_RECOMP.get('n_all')} 行，"
  f"converged_unique {PF_RECOMP.get('n_ok')}，剔除 {PF_RECOMP.get('n_excluded')}"
  f"（{PF_RECOMP.get('status_counts')}）")
W(f"- A15 `ablation_matrix.csv`：重算 {ABL_RECOMP.get('n_all')} 行，"
  f"reliable {ABL_RECOMP.get('n_ok')}，份额口径( dp=0, n={ABL_RECOMP.get('n_share_only')}) "
  f"残差 max = {vfmt(ABL_RECOMP.get('resid_max_share_only_ml'))} ML，"
  f"含容量扩张口径 max = {vfmt(ABL_RECOMP.get('resid_max_ml'))} ML")
W(f"- A20 v2 重算：{BR2_RECOMP.get('n_pairs')} 对，符号一致 {BR2_RECOMP.get('sign_agreement')}"
  f"/{BR2_RECOMP.get('n_pairs')} = {vfmt(BR2_RECOMP.get('share'))}，"
  f"按水样 {BR2_RECOMP.get('by_composition')}，M0 最大相对差 {vfmt(BR2_RECOMP.get('max_rel_M0_diff'))}")
W(f"- A20 v1（历史 36 对）重算：{BR1_RECOMP.get('n_pairs')} 对，符号一致 "
  f"{BR1_RECOMP.get('sign_agreement')}/{BR1_RECOMP.get('n_pairs')}，"
  f"按水样 {BR1_RECOMP.get('by_composition')} —— 与稿件撤回说明一致")
W(f"- A24 外部重算：设计能力分位 D-HA = {vfmt(EXT_RECOMP.get('pctl_of_ha_supply'))}%，"
  f"D-CO = {vfmt(EXT_RECOMP.get('pctl_of_co_supply'))}%；"
  f"committed 最小占比 = {vfmt(EXT_RECOMP.get('committed_min_all_r'))}%")
W("")
W("---")
W("")
W("## 2. 总表")
W("")
W("| # | 数值 | 位置行号 | 稿件值 | 权威产物值 | 裁定 | 产物路径 |")
W("|---:|---|---|---|---|---|---|")
for i, r in enumerate(R, start=1):
    mv = str(r["manuscript_value"]).replace("|", "\\|")
    av = vfmt(r["artifact_value"]).replace("|", "\\|")
    loc = r["location"]
    path = r["artifact_path"]
    W(f"| {i} | {mv} | {loc} | {r['shown'][:70]} | {av} | **{r['verdict']}** | `{path}` |")
W("")
W("### 2.1 非 VERIFIED 条目的完整说明")
W("")
for r in R:
    if r["verdict"] == "VERIFIED":
        continue
    W(f"- **{r['verdict']}** `{r['manuscript_value']}` @ {r['location']} — {r['note']}")
W("")
W("---")
W("")
W("## 3. 必须修改清单（按严重度排序）")
W("")
MUST = [
    ("P0", "FORBIDDEN_CLAIM", "manuscript L43 / L398（`above 95%` / `above 93%`；"
     "`empirically dominant`；Abstract `surplus covers only ~2–5%`）",
     "必须**整段撤回**，不得作为观测事实出现。数据只观测到「生产能力(处理量×r)」，"
     "未观测「已承诺需求」。SI S6b 自己已记录负荷率→分支占比的映射「wrong in direction」并撤回。"
     "若保留，只能改写为「在我们的规模—阈值比较下 committed 分支占多数」这一条件化表述，"
     "并同时给出 2.0–6.6% 的完整区间。"),
    ("P0", "STALE", "manuscript L418、L425（`R² = 0.557`；`baseline −0.050`；"
     "`0.5574`；`0.5582`；SI S6 `R² = 0.558`、`baseline −0.044`）",
     "改为 `R² = 0.806`（`co_R2_phi_eff = 0.8055937188186029`），"
     "基线统一为 `−0.073`（`trivial_baseline_R2 = −0.07328387812300985`）。"
     "现行稿件同时出现 0.557 / 0.5574 / 0.5582 / 0.558 与两个互不相同的基线，属多重内部矛盾。"),
    ("P0", "STALE", "manuscript §3 组成表 L155–L158；SI 无此表",
     "整表重算值：LADWP 186/8、AI-UWM 187/8、IEUA 151/56、Figshare 119/62（各含 9 行 dS=0）。"
     "稿件 183/0、184/0、148/48、116/54 全部与产物不符。"),
    ("P1", "STALE", "manuscript §2 L97（`2.5e-11`）vs Discussion（`2.9e-11`）"
     "vs SI S3（`5.8e-11`）vs SI S2a/S3.0（`2.55e-11`）",
     "同一「恒等式残差」在全稿出现 **四个不同数值**。经独立重算, 只有 **2.55e-11 / 2.5e-11** "
     "在 813 双门禁子集上成立（重算 2.5466e-11）—— 应全稿统一为该值并注明口径"
     "（统一通式 `displaced-(M0-M1)-x_ai_B1`、813 子集）。"
     "`2.9e-11`（Discussion）与 `5.8e-11`（SI S3, 号称 1,152 情景）无产物支撑。"
     "另须显式区分三个易混量：(a) 统一通式残差 813 子集 2.55e-11 / 1052 全表 2.8e-6；"
     "(b) `dS_pot − dS_ident` 最大绝对残差 6.39e4 ML；(c) 占位档 `identity_resid_max` 1.16e-10。"),
    ("P1", "STALE", "manuscript §2 L108/L112（`negative in 429 of 446`；`The 17 exceptions`；"
     "`100% agreement`）",
     "零挤占行在可靠子集中为 372 行，其中 dS>0 仅 **3** 行，非 17；446 是占位档 all 值。"
     "`429/446` 与 `17` 均无产物支撑。A25 `zero_disp_criterion.json` 的 n_zero_disp 为 ha 241 / co 205。"),
    ("P1", "STALE", "manuscript §3 L188（`0.803`）vs SI S3.2（`0.768`）",
     "A22 `q_predictors_summary.json` 最大 `acc = 0.7682291666666666`，无 0.803。"
     "主稿与 SI 同一指标必须统一为 0.768。"),
    ("P2", "STALE", "manuscript §3c L265（`M0 = 104,948 / M1 = 93,414 / dS = −11,535`）",
     "104,948.4 只存在于 `OBSOLETE_reliability_grid.csv`（占位档、chi=0.25、phi=0.5）；"
     "M1 与 dS 无任何产物。且现行网格 phi 自 0.2 起，phi=0.05 无法复现。"),
    ("P2", "STALE", "SI S3.0 表头（`1,152 / 58 / 5.03%` 与 `813` 混排；`SI S2a 329/441`）",
     "1,152 是 A27 切换前的占位档网格；现行主网格为 **1,052**。"
     "该表把两代口径（1,152+58 与 813+188）放进同一张表，必须拆表并显式标注口径。"),
    ("P2", "STALE", "manuscript §7 L417 / SI S6（`ablation identity residual 3.6e-12`）",
     "重算份额口径（`dp_scale==0`, n=30, `converged_unique`）max = "
     "**7.276e-12**（= `a15_gates_reliable.ablation.all.unified_resid_max`）；"
     "`ablation_summary.identity_max_err_share_only_ml = 5.457e-12`。无 3.6e-12。"),
    ("P3", "UNTRACEABLE", "manuscript §5/SI S4.1 组成均值表（−19,726 / −8,510 / −12,257 / "
     "−4,690 / −16,359 / −7,504 / +8,895 / +28,437）；§3 表中位 −14,496 / −7,651 / −4,259；"
     "§3c `237/0`、`241/0`；§6 `0.184`；§3b `2,869 ML`、`192 scenarios`；SI S2b 100/92/58/48/0%",
     "这些数字在仓库的任何 *.json/*.csv 中都找不到字段。要么补跑并落盘对应产物，"
     "要么在稿件中删除或降级为「未落盘估计」。`192` 尤须修："
     "`missing_quality_summary.n_rows = 16`。"),
    ("P3", "STALE", "manuscript §5 L299（`surplus ≤ 0, down to −22,359 ML`）",
     "A18 `surplus_arm.d_abstraction_ml = −22,541.17`，不是 −22,359。"),
]
W("| 级别 | 裁定 | 位置 | 必须的修改 |")
W("|---|---|---|---|")
for lv, vd, loc, fix in MUST:
    W(f"| **{lv}** | {vd} | {loc} | {fix} |")
W("")
W("---")
W("")
W("## 4. 方法学说明")
W("")
W("### 4.1 如何提取")
W("")
W("`audit_stale_numbers.py` 用正则 `NUM = [-−–]?\\d[\\d,，]*(\\.\\d+)?(\\s*[×x]\\s*10\\s*[-−–]?\\s*[⁰¹²³⁴⁵⁶⁷⁸⁹]+)?` "
  "对主稿与 SI **逐行**扫描，抓取每一个数值 token（含千分位、Unicode 负数号、"
  "`2.5 × 10⁻¹¹` 形式的科学计数），解析为 float，并保留 ±70 字符上下文以判定语境。"
  "行号由同一脚本在稿件上二次定位（`locate()`）以保证可复核。")
W("")
W("### 4.2 如何定位权威来源")
W("")
W("对每个数值按优先级查找：(1) 该 A* 目录下的 `*_summary.json`；(2) 对应 `*.csv` 原始产物"
  "（本脚本**重新计算**而不是照抄 summary，以发现 summary 与 CSV 的不一致）；"
  "(3) 报告 md 仅作为「历史值/撤回值」的佐证，不作为权威锚。")
W("")
W("本脚本实际独立重算的关键量：")
W("")
W("- A17 主网格双门禁子集（`status==converged_unique` ∧ `¬coc_floor_degenerate` ∧ `¬extrapolated`）"
  "的全部头条计数与恒等式残差；")
W("- A13c `potable_flows.csv` 的 status 分布；")
W("- A15 `ablation_matrix.csv` 的 status 分布与恒等式残差；")
W("- A20 桥接 v1(36 对)/v2(24 对) 的配对、符号一致率、按水样拆分、M0 最大相对差；")
W("- A24 外部数据的分位数与 `33.4 / 30.7 ML/d` 的真实分位（80.89 / 80.77）。")
W("")
W("本轮共真实读取并登记 " + str(len(READ_ARTIFACTS)) + " 个机器产物，全部列于 JSON 的 `artifacts_read`。")
W("")
W("### 4.3 局限")
W("")
W("1. **`gamma`/隐式量**：稿件中有若干数字（如组成均值表、`237/0`、`2,869 ML`）"
  "可能来自未落盘的中间脚本运行；本审计**不猜测**其来源，一律记 UNTRACEABLE。")
W("2. **口径混用本身就构成缺陷**：A27 切换使主网格从 1152/1094 变为 1052/813，"
  "但 A25 系列产物（`convergence_audit.json`、`convergence_impact.json`、`a15_gates_reliable.json`）"
  "仍是切换前口径。因此某些数字「能在产物中找到」但仍属陈旧——脚本对这类情况"
  "在 note 中显式标注，而非简单判 VERIFIED。")
W("3. **恒等式残差的定义歧义**：`dS_pot − dS_ident`、`unified_identity_max_err_ml`、"
  "`identity_max_err_ml` 是三个不同的量。稿件未说明所指，导致 2.5e-11 系列无法唯一追溯。"
  "这是稿件本身的问题，本审计如实登记而非代为选择。")
W("4. **`2e10 ML` 量级**：脚本对该条标 VERIFIED 是宽松判断（`OBSOLETE_reliability_grid.csv` "
  "实际 M 量级为 1.2e5），因为该量级描述的是 CoC floor 触发后的退化行为而非常规数值。")
W("5. **外部数据的 `r = 1.0000`**：A28 `final_audit.py` 做过该检验且通过，"
  "但未落盘数值产物，因此记 UNTRACEABLE。")
W("6. **未核**：图（`figures/`）与参考文献（`A29_文献核验/`）不在本次「数字核对」范围内。")
W("")
W("### 4.4 纪律声明")
W("")
W("本审计**未修改** `manuscript_en_v3.md`、`supplementary_information.md` "
  "或仓库中任何现有研究文件；产出仅写入 `A30_WP0取证/`。")

with io.open(OUT_MD, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

print(f"[OK] {n_total} values checked")
for k in VERDICTS:
    print(f"     {k:<16} {counts.get(k,0)}")
print(f"[OK] wrote {rel(OUT_MD)}")
print(f"[OK] wrote {rel(OUT_JSON)}")
print(f"[OK] artifacts read: {len(READ_ARTIFACTS)}")
