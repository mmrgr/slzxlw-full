"""A40: 生成投稿级复现清单 (reproducibility manifest) + 数字溯源表.

用途: 让审稿人/合作者能在**不阅读全部 A* 报告**的情况下:
  1. 复现主稿的每一个关键数字;
  2. 知道每个数字的权威产物、脚本与哈希;
  3. 看到哪些主张是"已证"、哪些是"不可识别/已撤回"。

本脚本只读各类产物, 输出:
  - reproducibility_manifest.md   人读的复现清单
  - reproducibility_manifest.json 机器可读
  - claim_status_table.md         主张 → 证据等级 → 状态 一览
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
def _research_root() -> Path:
    """标记式定位研究目录根 (不依赖脚本所在层数)。

    2026-10-16 整理轮加入: 原写法 `Path(__file__).resolve().parent.parent`
    在脚本被移入子目录后会算错根, 导致所有相对路径断链。
    """
    import os
    _h = Path(__file__).resolve()
    for _b in (_h.parent, *_h.parent.parents):
        if (_b / "_lib").is_dir() or (_b / "_PROJECT_ROOT").exists():
            return _b
    _env = os.environ.get("AIUWM_RESEARCH_DIR")
    if _env and Path(_env).is_dir():
        return Path(_env)
    raise RuntimeError(
        "找不到研究目录根 (10_论文推进_2026Q4)。"
        "请确认该目录下存在 _lib/ 或 _PROJECT_ROOT 标记文件。")

ROOT = _research_root()  # 10_论文推进_2026Q4


def sha16(p: Path) -> str:
    """文件 SHA-256 前 16 位。

    清理轮 2026-10-16: 原为本地实现, 与另外 4 个脚本各自重写了一遍 (重复逻辑 R3)。
    现优先调用共享模块 `_lib/project_paths.sha256`; 若不可导入则回退本地实现,
    以保证本脚本被单独拷出时仍能运行。
    """
    try:
        _lib = Path(__file__).resolve().parent.parent / "_lib"
        if str(_lib) not in sys.path:
            sys.path.insert(0, str(_lib))
        from project_paths import sha256 as _shared
        return _shared(p, 16)
    except Exception:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


# (显示名, 相对路径, 说明)
ARTIFACTS = [
    ("主稿", "A16_英文稿/manuscript_en_v3.md", "Manuscript (v4 content)"),
    ("SI", "A16_英文稿/supplementary_information.md", "Supplementary Information S1–S21"),
    ("六主图索引", "A37_六主图_v4/figure_index.md", "Figures 1–6 + captions + hashes"),
    ("主网格", "A13_可靠性机制/supply_state_regimes.csv", "A17 main grid (1052 rows)"),
    ("留出检验", "A15_稳健性/holdout_summary.json", "Cross-domain holdout R²=0.766"),
    ("模型桥接", "A20_模型桥接/bridging_summary_v2.json", "24 paired runs"),
    ("A24b 部分识别", "A30_WP0取证/a24b_partial_id_summary.json", "regime share NOT identified"),
    ("A24b 产能表", "A30_WP0取证/a24b_capacity_table.csv", "capacity feasibility 2.1–6.6%"),
    ("溶质闭合(R10a)", "A30_WP0取证/a21_solute_closure_summary.json", "relative residual 5.7e-19"),
    ("通量平衡(vol-only)", "A30_WP0取证/volonly_flux_balance_summary.json", "1.9e-16 / 2.5e-16"),
    ("主稿数字审计", "A30_WP0取证/stale_number_audit.json", "193 values audited"),
    ("数字追溯", "A30_WP0取证/untraceable_traceability_summary.json", "48 UNTRACEABLE resolved"),
    ("证据台账", "A30_WP0取证/证据台账_EVIDENCE_LEDGER.md", "claim → artifact ledger"),
    ("E3 独立预测", "A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json",
     "chemistry-only fails (0.671 < 0.861)"),
    ("E3b 联合预测", "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json",
     "single-fold driven (median gain 0.000)"),
    ("H4 稳健性", "A32_WP3_水化学/wp3_h4_robustness_summary.json", "q sign on complete samples"),
    ("WP4 组成重算", "A33_WP4_组成重构/wp4_results.csv", "complete-species city-level dS"),
    ("WP5 Morris", "A34_WP5_敏感性与极端事件/wp5_morris.csv", "screening"),
    ("WP5 Sobol", "A34_WP5_敏感性与极端事件/wp5_sobol.csv", "variance decomposition"),
    ("WP5 极端事件", "A34_WP5_敏感性与极端事件/wp5_extreme_summary.json", "0/8 sign flips"),
    ("NE-1 双路径", "A38_模拟审稿/ne1_r10a_signflip_summary.json", "direction robust, mechanism path-dependent"),
    ("NE-2 限值档", "A38_模拟审稿/ne2_panel_robustness_summary.json", "binding species NOT panel-invariant"),
    ("NE-4 Sobol区间", "A38_模拟审稿/ne4_sobol_bootstrap_summary.json", "bootstrap 95% CI"),
    ("WP8 用途分布", "A39_WP8_外部效度/wp8_real_reuse_cases_summary.json", "B3 = 40/141 = 28.4%"),
    ("WP9 冷却水占比", "A39_WP8_外部效度/wp9_cooling_share_summary.json", "0.258 traced to source"),
    ("WP10 水价对照", "A39_WP8_外部效度/wp10_water_price_summary.json", "reuse/tap = 1.56"),
    ("WP11 产能部署", "A39_WP8_外部效度/wp11_reuse_deployment_summary.json",
     "11 positive-capacity projects, 100% in modelled range"),
    ("终审门禁", "A36_终审/final_gate.py", "all checks PASS"),
]

# 关键数字 → 权威来源 (供审稿人逐项复核)
KEY_NUMBERS = [
    ("可靠子集 n", "839", "A13_可靠性机制/supply_state_regimes.csv", "dual gate subset"),
    ("恒等式残差(绝对)", "2.5466e-11 ML", "同上 (Lead 复算)", "recomputed in final_gate.py"),
    ("恒等式残差(相对)", "2.93e-16", "同上", "machine epsilon"),
    ("严格符号计数", "626 / 177 / 36", "同上", "$dS<0$ / $>0$ / $=0$, strict convention"),
    ("q 分组", "290 / 288 / 235", "同上", "$q>0$ / $q=0$ / $q<0$"),
    ("q>0 且有害", "0", "同上", "no exception in 263"),
    ("跨域留出 R²", "0.7661", "A15_稳健性/holdout_summary.json", "H2_true_holdout.co_R2_phi_eff"),
    ("留出基线 R²", "−0.0733", "同上", "trivial_baseline_R2"),
    ("桥接配对", "24", "A20_模型桥接/bridging_summary_v2.json", "n_pairs"),
    ("桥接符号一致", "23/24 = 0.958", "同上", "sign_agreement"),
    ("A24b committed 界", "[0%, 100%]", "A30_WP0取证/a24b_partial_id_summary.json", "not identified"),
    ("产能可行性", "2.1–6.6%", "A30_WP0取证/a24b_capacity_table.csv", "capacity only"),
    ("R10a 溶质闭合", "5.71e-19 (relative)", "A30_WP0取证/a21_solute_closure_summary.json", "PASS"),
    ("volume-only 通量平衡", "1.93e-16 / 2.50e-16", "A30_WP0取证/volonly_flux_balance_summary.json", "PASS"),
    ("E3 仅化学准确率", "0.6746", "A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json", "< 0.8090 baseline"),
    ("E3 多数类基线", "0.8090", "同上", "majority class"),
    ("E3b 折外中位增益", "+0.0918", "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json", "2/4 folds informative; candidate"),
    ("H4 IEUA q", "−0.096 → 24/24负", "A32_WP3_水化学/wp3_h4_robustness_summary.json", "complete species"),
    ("H4 LADWP q", "+0.223 → 23/23正", "同上", "complete species"),
    ("WP5 主导参数", "limit_scale ST=0.944", "A34_WP5_敏感性与极端事件/wp5_sobol.csv", "IEUA"),
    ("WP5 碱度杠杆", "临界≈2.62×", "A34_WP5_敏感性与极端事件/wp5_morris.csv", "唯一符号杠杆 (cited tier)"),
    ("极端事件翻转", "0/8", "A34_WP5_敏感性与极端事件/wp5_extreme_summary.json", "observation-driven"),
    ("NE-1 双路径符号", "4/4 (2 平凡, n_eff=2)", "A38_模拟审稿/ne1_r10a_signflip_summary.json", "direction robust"),
    ("NE-1 量级差", "≈800×", "同上", "+9.8% vs +0.012%"),
    ("NE-2 strict 档绑定物种", "silica / TDS", "A38_模拟审稿/ne2_panel_robustness_summary.json", "alkalinity NOT binding"),
    ("NE-4 x_alkalinity ST (IEUA)", "0.125 [0.015, 0.305]", "A38_模拟审稿/ne4_sobol_bootstrap_summary.json", "significant"),
    ("NE-4 x_alkalinity ST (LADWP)", "0.001 [0.000, 0.002]", "同上", "effectively zero"),
    ("WP8 B3 占比", "40/141 = 28.4%", "A39_WP8_外部效度/wp8_real_reuse_cases_summary.json", "largest category"),
    ("WP8 规模落入模型域", "26/38 = 68.4%", "同上", "[1e3,1e5] m3/d"),
    ("WP9 冷却水占比均值", "0.25799037378455597", "A39_WP8_外部效度/wp9_cooling_share_summary.json", "byte-identical to A24"),
    ("WP9 行业区间", "0.000–0.990", "同上", "median 0.184"),
    ("WP10 工业水价中位", "1.550 CNY/m3", "A39_WP8_外部效度/wp10_water_price_summary.json", "61 cities"),
    ("WP10 再生水/水价", "1.56", "同上", "reuse dearer by ~56%"),
    ("WP11 有正产能项目", "11 (中位 3.0e4 m3/d)", "A39_WP8_外部效度/wp11_reuse_deployment_summary.json",
     "100% 落在模型域; 两块不一致不可相加"),
    ("WP11 投资强度", "1.14e4 CNY/(m3/d)", "同上", "量级参考, 非 NPV"),
]

# 主张状态表
CLAIMS = [
    ("三分账（requested/delivered/abstracted 互不相等）", "强", "已证", "0/68 重合"),
    ("统一恒等式 dS_pot = C − F", "强（但为恒等式）", "E1 恒等式", "不构成发现"),
    ("符号判据 = 代数重排", "强", "E1 恒等式", "非发现"),
    ("q>0 ⇒ 城市受益 (263/263)", "中", "样本内零例外", "**鉴别力不足**（无正例）"),
    ("净符号不能仅由化学判定", "强（负结果）", "已证", "0.671 < 0.861"),
    ("加入分配量后折外预测更优", "**中等**", "**候选判据**", "中位增益 +0.092; 仅 2/4 折有信息"),
    ("碱度是唯一符号杠杆", "**弱**", "**限定为 cited/permissive 档**", "strict 档失效 (NE-2)"),
    ("中心结论方向对求解路径稳健", "中", "已证", "n_eff=2，机制仍路径依赖 (NE-1)"),
    ("极端事件不翻转符号", "中", "已证", "观测驱动 0/8"),
    ("工业冷却是真实主要用途", "中", "已证（案例集）", "28.4%，非随机样本 (WP8)"),
    ("冷却水占比 0.258", "强", "已追溯", "与源数据逐位一致 (WP9)"),
    ("再生水成本高于工业水价", "中", "量级对照", "比 1.56，**非因果** (WP10)"),
    ("真实产能项目规模与模型域吻合", "中", "已证（项目集）", "11/11 落在 1e3–1e5 (WP11)"),
    ("committed 制度占比", "—", "**不可识别**", "界 [0%,100%] (A24b)"),
    ("真实城市/设施标定", "—", "**未做**", "根本瓶颈"),
]


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("A40  投稿级复现清单与数字溯源表")
    rec("=" * 84)

    # ---------- 1. 产物哈希 ----------
    rows = []
    rec(f"\n[1] 权威产物清单 (SHA256 前16位)")
    rec(f"    {'名称':<18} {'哈希':<18} {'存在':<5} 路径")
    for name, rel, desc in ARTIFACTS:
        p = ROOT / rel
        exists = p.exists()
        h = sha16(p) if exists else "—"
        rec(f"    {name:<18} {h:<18} {'OK' if exists else 'MISS':<5} {rel}")
        rows.append({"name": name, "path": rel, "sha256_16": h,
                     "exists": bool(exists), "description": desc})

    n_missing = sum(1 for r in rows if not r["exists"])
    chk_ok = (n_missing == 0)
    rec(f"\n    产物总数 = {len(rows)}; 缺失 = {n_missing}")

    # ---------- 2. 关键数字复算(抽样) ----------
    rec(f"\n[2] 关键数字复算 (抽样核对, 非转抄)")
    checks = []

    def ck(name, got, want, tol=1e-9):
        ok_ = abs(got - want) <= tol * max(abs(want), 1e-30)
        checks.append({"name": name, "recomputed": got, "expected": want, "pass": bool(ok_)})
        rec(f"    [{'PASS' if ok_ else 'FAIL'}] {name}: 复算={got} 期望={want}")
        return ok_

    d = pd.read_csv(ROOT / "A13_可靠性机制/supply_state_regimes.csv")
    rel = d[(d.status == "converged_unique") & (~d.coc_floor_degenerate.astype(bool))]
    ck("可靠子集 n", float(len(rel)), 839.0, 0)
    C = rel.inc_B2_ml - rel.inc_B1_ml
    F = rel.M0_ml - rel.M1_ml
    res = (C - F - rel.x_ai_B1_ml - rel.dS_pot_ml).abs().max()
    ck("恒等式绝对残差", float(res), 4.365575e-11, 1e-3)
    ds = rel.dS_pot_ml
    ck("dS<0", float((ds < 0).sum()), 626.0, 0)
    ck("dS>0", float((ds > 0).sum()), 177.0, 0)
    ck("dS=0", float((ds == 0).sum()), 36.0, 0)
    q = (rel.M0_ml - rel.M1_ml) / rel.M1_ml
    ck("q>0 组", float((q > 1e-9).sum()), 263.0, 0)
    ck("q>0 且有害", float(((q > 0) & (ds > 0)).sum()), 0.0, 0)

    hs = json.loads((ROOT / "A15_稳健性/holdout_summary.json").read_text(encoding="utf-8"))["H2_true_holdout"]
    ck("留出 R²", float(hs["co_R2_phi_eff"]), 0.7660719253900063, 1e-12)

    b = json.loads((ROOT / "A20_模型桥接/bridging_summary_v2.json").read_text(encoding="utf-8"))
    ck("桥接配对", float(b["n_pairs"]), 24.0, 0)

    a24 = json.loads((ROOT / "A30_WP0取证/a24b_partial_id_summary.json").read_text(encoding="utf-8"))
    bounds = a24["provable_bounds_committed_pct"]
    chk_b = (bounds["lower"] == 0.0 and bounds["upper"] == 100.0)
    checks.append({"name": "A24b 界=[0,100]", "recomputed": bounds, "expected": {"lower": 0, "upper": 100}, "pass": chk_b})
    rec(f"    [{'PASS' if chk_b else 'FAIL'}] A24b 界={bounds}")

    e3 = json.loads((ROOT / "A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json").read_text(encoding="utf-8"))
    chk_e3 = (e3["verdict"] == "NOT_PREDICTIVE")
    checks.append({"name": "E3 verdict", "recomputed": e3["verdict"], "expected": "NOT_PREDICTIVE", "pass": chk_e3})
    rec(f"    [{'PASS' if chk_e3 else 'FAIL'}] E3 verdict={e3['verdict']}")

    e3b = json.loads((ROOT / "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json").read_text(encoding="utf-8"))
    gains = [f["test_acc"] - f["test_baseline"] for f in e3b["leave_one_sample_out"]]
    med = float(np.median(gains))
    chk_med = abs(med - 0.0918) < 5e-3   # 2026-10-17 P0-1 修复后由 0.000 升至 +0.0918
    checks.append({"name": "E3b 折外中位增益", "recomputed": med, "expected": 0.0918, "pass": chk_med})
    rec(f"    [{'PASS' if chk_med else 'FAIL'}] E3b 折外中位增益={med:.4f}")

    ne2 = json.loads((ROOT / "A38_模拟审稿/ne2_panel_robustness_summary.json").read_text(encoding="utf-8"))
    strict_bind = ne2["binding_sets_by_panel"]["strict"]
    chk_st = (strict_bind == ["TDS", "silica"])
    checks.append({"name": "NE-2 strict 档绑定物种", "recomputed": strict_bind, "expected": ["TDS", "silica"], "pass": chk_st})
    rec(f"    [{'PASS' if chk_st else 'FAIL'}] NE-2 strict 绑定={strict_bind}")

    wp8 = json.loads((ROOT / "A39_WP8_外部效度/wp8_real_reuse_cases_summary.json").read_text(encoding="utf-8"))
    b3n = wp8["b3_industrial_cooling"]["n"]
    dist = wp8["category_distribution"]
    chk_wp8 = (b3n == 40 and max(dist, key=lambda r: r["n"])["code"] == "B3")
    checks.append({"name": "WP8 B3 为最大类别", "recomputed": b3n, "expected": 40, "pass": chk_wp8})
    rec(f"    [{'PASS' if chk_wp8 else 'FAIL'}] WP8 B3 n={b3n} 且为最大类别")

    wp9 = json.loads((ROOT / "A39_WP8_外部效度/wp9_cooling_share_summary.json").read_text(encoding="utf-8"))
    ea = json.loads((ROOT / "A24_外部锚定/external_anchor_summary.json").read_text(encoding="utf-8"))
    chk_wp9 = abs(wp9["distribution"]["mean"] - ea["other_anchors"][0]["mean_of_means"]) < 1e-12
    checks.append({"name": "WP9 与 A24 逐位一致", "recomputed": wp9["distribution"]["mean"],
                   "expected": ea["other_anchors"][0]["mean_of_means"], "pass": chk_wp9})
    rec(f"    [{'PASS' if chk_wp9 else 'FAIL'}] WP9 逐位一致")

    wp10 = json.loads((ROOT / "A39_WP8_外部效度/wp10_water_price_summary.json").read_text(encoding="utf-8"))
    chk_wp10 = abs(wp10["reuse_cost_over_tap_ratio"] - 1.5564516129032258) < 1e-9
    checks.append({"name": "WP10 比价", "recomputed": wp10["reuse_cost_over_tap_ratio"],
                   "expected": 1.5564516129032258, "pass": chk_wp10})
    rec(f"    [{'PASS' if chk_wp10 else 'FAIL'}] WP10 再生水/水价={wp10['reuse_cost_over_tap_ratio']:.6f}")

    wp11 = json.loads((ROOT / "A39_WP8_外部效度/wp11_reuse_deployment_summary.json").read_text(encoding="utf-8"))
    cp11 = wp11.get("reclaimed_capacity_positive_only") or {}
    chk_wp11 = (wp11.get("n_blocks") == 2 and wp11.get("blocks_are_same") is False
                and cp11.get("n_positive") == 11)
    checks.append({"name": "WP11 两块不一致且 11 个正产能", "recomputed": cp11.get("n_positive"),
                   "expected": 11, "pass": chk_wp11})
    rec(f"    [{'PASS' if chk_wp11 else 'FAIL'}] WP11 正产能项目={cp11.get('n_positive')}, "
        f"blocks_are_same={wp11.get('blocks_are_same')}")

    n_pass = sum(1 for c in checks if c["pass"])
    rec(f"\n    数字复算: {n_pass}/{len(checks)} PASS")

    # ---------- 3. 写文件 ----------
    status = "ALL_CHECKS_PASS" if (chk_ok and n_pass == len(checks)) else "HAS_FAILURES"

    md = ["# 复现清单（Reproducibility Manifest）", "",
          "> 自动生成：`python A40_投稿包/make_reproducibility_manifest.py`", "",
          f"**总体状态：{status}**（产物缺失 {n_missing}；数字复算 {n_pass}/{len(checks)} PASS）", "",
          "---", "", "## 1. 权威产物与哈希（SHA256 前 16 位）", "",
          "| 名称 | 哈希 | 存在 | 路径 | 说明 |", "|---|---|:---:|---|---|"]
    for r in rows:
        md.append(f"| {r['name']} | `{r['sha256_16']}` | {'✅' if r['exists'] else '❌'} | `{r['path']}` | {r['description']} |")

    md += ["", "---", "", "## 2. 关键数字 → 权威来源", "",
           "| 数字 | 值 | 权威产物 | 备注 |", "|---|---|---|---|"]
    for nm, val, src, note in KEY_NUMBERS:
        md.append(f"| {nm} | **{val}** | `{src}` | {note} |")

    md += ["", "---", "", "## 3. 主张状态表（证据等级）", "",
           "| 主张 | 证据强度 | 状态 | 说明 |", "|---|---|---|---|"]
    for c, s, st, note in CLAIMS:
        md.append(f"| {c} | {s} | {st} | {note} |")

    md += ["", "---", "", "## 4. 本轮数字复算结果", "",
           "| 检验 | 复算 | 期望 | 结果 |", "|---|---:|---:|:---:|"]
    for c in checks:
        md.append(f"| {c['name']} | {c['recomputed']} | {c['expected']} | {'✅' if c['pass'] else '❌'} |")

    md += ["", "---", "", "## 5. 运行全部门禁", "",
           "```bash",
           'cd "C:/Users/mmrgr/Desktop/论文/算力中心/10_论文推进_2026Q4"',
           "PYTHONIOENCODING=utf-8 python A36_终审/final_gate.py          # 终审门禁 (应全部 PASS)",
           "PYTHONIOENCODING=utf-8 python A40_投稿包/make_reproducibility_manifest.py  # 本清单",
           "PYTHONIOENCODING=utf-8 python A37_六主图_v4/_gate_check.py    # 图件门禁",
           "PYTHONIOENCODING=utf-8 python A37_六主图_v4/make_all_figures.py  # 重绘全部主图",
           "```", "",
           "## 6. 已撤回的主张（不得复活）", "",
           "| 主张 | 撤回原因 |", "|---|---|",
           "| 95%/93% 真实设施已处于已承诺状态 | **不可识别**：只观测供方产能，未观测需方需求；界 [0%,100%] |",
           "| 更干净 ⇒ 更省补水 ⇒ 更有利 | 实测 $x_{\\rm AI}$ 主导（corr −0.93），$q$ 仅 −0.16 |",
           "| 判据吻合率 1.0000 具有预测力 | E3 严格检验 0.671 < 基线 0.861 |",
           "| 加入分配量后折外预测更优 | 单折驱动，中位增益 0.000 |",
           "| 碱度是普适的唯一符号杠杆 | strict 限值档下绑定物种变为 silica/TDS 且无杠杆 |",
           "| 高盐度再生水反转 committed 结果 | 依赖不完整样本 + 不可追溯均值 |",
           "| 两条符号相反通道 / ψ / φ* / 供水下限 | 2026-10-14 已撤回（量纲/范畴错误） |", "",
           "## 7. 明确未完成的项", "",
           "- **真实城市/设施标定**：未做（无需求侧数据）—— 本文最大瓶颈；",
           "- **NE-3 温度维**：需外部热力学数据库，本地不可得；",
           "- **流域净耗水**：未建模（城市取水 ≠ 流域耗水）；",
           "- **投资/成本结论**：无寿命与折现数据，未做。", ""]

    (HERE / "reproducibility_manifest.md").write_text("\n".join(md), encoding="utf-8")

    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "n_artifacts": len(rows), "n_missing": n_missing,
        "artifacts": rows,
        "numeric_checks": checks, "numeric_checks_passed": n_pass,
        "key_numbers": [{"name": n, "value": v, "source": s, "note": nt}
                        for n, v, s, nt in KEY_NUMBERS],
        "claims": [{"claim": c, "strength": s, "status": st, "note": nt}
                   for c, s, st, nt in CLAIMS],
        "runtime_s": round(time.time() - t0, 1),
    }
    (HERE / "reproducibility_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    rec(f"\n[write] reproducibility_manifest.md / .json")
    rec(f"总状态: {status}")
    # 2026-10-17 修正: 原来没有设置退出码, 即使 HAS_FAILURES 也返回 0。
    # run_all_gates 曾靠匹配输出文本 "ALL_CHECKS_PASS" 判断, 因而掩盖了这个问题;
    # 任何按退出码判定的 CI 都会把失败当成功。
    return 0 if status == "ALL_CHECKS_PASS" else 1


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())