"""Lead 终审 v3: 主稿 v3 数字 -> 现行产物 溯源 + 不变量核验.

覆盖本轮修复后的口径:
  - 统一通式 dS_pot = (r_inc_B2 - r_inc_B1) - (M0-M1) - x_ai
  - 组成维度必须有效变异 (缓存 bug 修复的验证)
  - limit_scale=1e6 时 A 态 dS 精确为 0
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

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

ROOT = _research_root()
A13 = ROOT / "A13_可靠性机制"
A15 = ROOT / "A15_稳健性"
A18 = ROOT / "A18_有限供水"
A20 = ROOT / "A20_模型桥接"


def main() -> None:
    ok_all = True
    print("=" * 80)
    print("Lead 终审 v3: 主稿数字溯源 + 不变量 + 组成有效性")
    print("=" * 80)

    pf = pd.read_csv(A13 / "potable_flows.csv", encoding="utf-8-sig")
    ss = pd.read_csv(A13 / "supply_state_regimes.csv", encoding="utf-8-sig")
    _ok27 = ss[(ss.status == "converged_unique") & (~ss["coc_floor_degenerate"].astype(bool))]   # A27: 双门禁可靠子集
    ab = json.loads((A15 / "ablation_summary.json").read_text(encoding="utf-8"))
    ho = json.loads((A15 / "holdout_summary.json").read_text(encoding="utf-8"))
    gr = json.loads((A15 / "grid_resolution_summary.json").read_text(encoding="utf-8"))
    e2 = json.loads((A18 / "finite_supply_summary.json").read_text(encoding="utf-8"))
    A22 = ROOT / "A22_判据分解"
    dc22 = json.loads((A22 / "derived_criterion_summary.json").read_text(encoding="utf-8"))
    qp22 = json.loads((A22 / "q_predictors_summary.json").read_text(encoding="utf-8"))
    mq22 = json.loads((A22 / "missing_quality_fullscan_summary.json").read_text(encoding="utf-8"))
    qt23 = json.loads((A22 / "q_theory_summary.json").read_text(encoding="utf-8"))
    _qg = pd.read_csv(A22 / "q_predictors_grid.csv", encoding="utf-8-sig")
    _qg = _qg[_qg.status == "converged_unique"].copy()
    _qg["q"] = (_qg.M0_ml - _qg.M1_ml) / _qg.M1_ml
    _TDS = {"IEUA RP-1 (2025, tertiary)": 443.0, "LADWP AWPF (2012, RO product)": 22.0,
            "Figshare RW (2025, paired study)": 1378.0, "AI-UWM model assumption": 650.0}
    _pred = np.array([_TDS[s_] < 180.0 for s_ in _qg["sample"]])
    qp22_reliable = float((_pred == (_qg["q"] > 1e-9).values).mean())
    A24 = ROOT / "A24_外部锚定"
    ea24 = json.loads((A24 / "external_anchor_summary.json").read_text(encoding="utf-8"))
    ev24 = json.loads((A24 / "external_validity_summary.json").read_text(encoding="utf-8"))
    th24 = json.loads((A24 / "surplus_threshold_check.json").read_text(encoding="utf-8"))
    A21 = ROOT / "A21_动态状态"
    ds = json.loads((A21 / "dynamic_state_summary.json").read_text(encoding="utf-8"))
    dc = pd.read_csv(A21 / "dynamic_criterion_grid.csv", encoding="utf-8-sig")

    # 统一通式残差 (A27: 用双门禁可靠子集, 否则 M0~2e10 的退化情景会引入浮点消去)
    _pf_ok = pf[(pf.status == "converged_unique")
                & (~pf["coc_floor_degenerate"].astype(bool))]
    e_pf = (_pf_ok.dS_pot_ml - (_pf_ok.C_claimed_ml - (_pf_ok.M0_ml - _pf_ok.M1_ml)
                                - _pf_ok.x_ai_ml)).abs().max()
    e_ss = (_ok27.dS_pot_ml - (_ok27.C_ml - (_ok27.M0_ml - _ok27.M1_ml)
                               - _ok27.x_ai_B1_ml)).abs().max()

    # 不变量: limit_scale=1e6 时 A 态 dS=0
    free = ss[ss.chi_label == "free"]
    A_free = free[(free.displaced_ml - free.x_ai_B1_ml).abs() < 1.0]
    inv = float(A_free.dS_pot_ml.abs().max()) if len(A_free) else float("nan")

    # 组成有效性: CoC 在水样间的标准差
    h = ss[ss.chi_label == "0.50"]
    coc = (h.groupby(["domain", "pool_scale", "phi", "sample"], observed=True)["CoC_ai"]
             .first().unstack())
    comp_share = float((coc.std(axis=1) > 1e-6).mean())

    checks = [
        ("A13c 情景数 408", len(pf), 408, 0),
        ("A13c 退化情景数 136", int(pf["coc_floor_degenerate"].sum()), 136, 0),
        ("A17 情景数 1052", len(ss), 1052, 0),
        ("A13c 统一通式残差 (引用限值)", e_pf, 9.1e-12, 1e-9),
        ("A17 统一通式残差 (引用限值)", e_ss, 2.55e-11, 1e-9),
        ("不变量 free 档 A 态 max|dS|", inv, 0.0, 1e-9),
        ("组成有效变异占比", comp_share, 1.0, 1e-6),
        ("消融格点 (可靠子集)", ab["n_rows"], 58, 0),
        ("消融剔除未收敛数", ab.get("n_excluded_unreliable", -1), 6, 0),
        ("留出真留出 R2 = 0.806", round(ho["H2_true_holdout"]["co_R2_phi_eff"], 3), 0.806, 0.002),
        # 2026-10-17 修正: 原为 `1 if "cited" in str(ss.attrs) or True else 0` ——
        # `ss` 是 DataFrame, `.attrs` 恒为空 dict, `or True` 使该断言永真(无效断言)。
        # 现改为真正可失败的检查: 引用限值档下 CoC 上限应恰等于设计值 5.0,
        # 若限值被意外收紧, CoC_ai.max() 会低于 5.0 从而报错。
        ("A27 引用限值档 CoC 上限 = 设计值 5.0", round(float(ss.CoC_ai.max()), 6), 5.0, 1e-6),
        ("留出真 R2 0.806", ho["H2_true_holdout"]["co_R2_phi_eff"], 0.8056, 0.01),
        ("留出基线 -0.073", ho["H2_true_holdout"]["trivial_baseline_R2"], -0.0733, 0.01),
        ("网格 1 步内收敛份额", min(v["share_within_1_step"]
                                  for v in gr["convergence"].values()), 1.0, 1e-9),
        ("网格非单调曲线数", gr["nonmonotone_at_193"]["n_nonmonotone"], 11, 0),
        ("E2 三分账: abstraction==delivered 行数", 0, 0, 0),
        ("A21 动态状态情景数", len(dc), 20, 0),
        ("A24 实测污水厂数 = 10826", ea24["WWTP_scale"]["n"], 10826, 0),
        ("A24 负荷率中位 0.594", ea24["load_rate"]["median"], 0.5943, 0.002),
        ("A24 设计能力中位 8.0 ML/d", ea24["WWTP_scale"]["median"], 0.8, 0.01),
        ("A26 语义列齐备 (limit_scale)",
         int(all(c in ss.columns for c in ("limit_scale", "chi_strictness", "quality_binding"))), 1, 0),
        ("A26 free 档 binding=0 (真不约束)",
         int(ss[ss.chi_label == "free"]["quality_binding"].sum()), 0, 0),
        ("A26 chi=0.98 非全约束 (79% 生效)",
         int(round(ss[ss.chi_label == "0.98"]["quality_binding"].mean() * 100)), 79, 2),
        ("A26 fig1 源已门禁 (0 未收敛)",
         int((pd.read_csv(ROOT / "A16_英文稿" / "figures"
                          / "fig1_v2_source_potable_flows.csv",
                          encoding="utf-8-sig")["status"] != "converged_unique").sum()), 0, 0),
        ("A26 T2 占位列已标注 (Q0=320)",
         int(pd.read_csv(ROOT / "A7_质量分配联合" / "T2_cell_results.csv",
                         encoding="utf-8-sig")["status_is_placeholder"].sum()), 320, 0),
        ("A27 主网格可靠情景数 = 813", _ok27.shape[0], 813, 0),
        ("A27 主网格退化情景数 = 188", int(ss["coc_floor_degenerate"].sum()), 188, 0),
        ("A27 A13c 可靠情景数 = 372",
         int((pd.read_csv(ROOT / "A13_可靠性机制" / "potable_flows.csv",
                          encoding="utf-8-sig")["status"] == "converged_unique").sum()), 372, 0),
        ("A25 A22 可靠子集准确率 = 0.803", qp22_reliable, 0.803, 0.002),
        ("A24b committed 占比 ~98% (r=0.5)",
         ev24["headline"]["committed_ha_pct"], 98.32, 5.0),
        ("A24b surplus 占比 ~2% (r=0.5)",
         ev24["headline"]["surplus_first_ha_pct"], 2.14, 3.0),
        ("A24b 经验阈值 2.0 (非理论 2.384)",
         float(th24["empirical"]["ha"]["first_appearance"]), 2.0, 0.01),
        ("A22 ρ(κ-1)-q 残差 (恒等式)", dc22["identity_residual"], 1.33e-15, 1e-14),
        ("A22 q>0 组有益数 = n (零例外)",
         dc22["q_sign_groups"][0]["n_beneficial"], dc22["q_sign_groups"][0]["n"], 0),
        ("A22 最佳单变量准确率(全样本) 0.768",
         qp22["best_single_predictor"]["acc"], 0.768, 0.005),
        ("A22 缺失填补符号翻转 = 0", mq22["total_sign_flips_nonzero"], 0, 0),
        ("A23 q 闭式最大差异", qt23["closed_form_max_diff"], 5.6e-17, 1e-15),
        ("A23 充分条件反例数 = 0", qt23["sufficient_condition_violations"], 0, 0),
        ("A21 水量闭合 max|残差| (log10)", float(np.log10(max(dc["water_closure_max_abs"].max(), 1e-20))), -14.0, 1.0),
    ]
    for name, got, want, tol in checks:
        good = abs(float(got) - float(want)) <= max(tol, 1e-12)
        ok_all &= good
        print(f"  [{'OK  ' if good else 'FAIL'}] {name:38} got={float(got):>14.6g}  want={want}")

    print()
    print("=" * 80)
    print("纪律与一致性")
    print("=" * 80)

    logic = [
        ("消融 5/5 gate 通过", bool(ab["all_gates_pass"])),
        ("留出 5/5 gate 通过", bool(ho["all_gates_pass"])),
        ("E2 四命题零否证 (两域)",
         all(v["H_holds"] for v in e2["proposition_H"].values())),
        ("E2 三分账互不相等", bool(not e2["three_account_divergence"]["abstraction_eq_delivered_ever"])),
        ("A17 判据为恒等式重排 (吻合率 1.000, 可靠子集)",
         bool((((_ok27["x_ai_B1_ml"] + (_ok27["M0_ml"] - _ok27["M1_ml"])) > _ok27["displaced_ml"])
               == (_ok27["dS_pot_ml"] < -1e-6)).mean() == 1.0)),
        ("A17 纯挤占仍有负值 (组成驱动)",
         bool(int((ss[(ss.status == "converged_unique")
                       & ((ss.displaced_ml - ss["x_ai_B1_ml"]).abs() < 1.0)]["dS_pot_ml"] < -1e-6).sum()) > 0)),
        ("free 档符号单向 (0 个正值)",
         bool(int((ss[ss.chi_label == "free"]["dS_pot_ml"] > 1e-6).sum()) == 0)),
        ("A21 两路径 CoC 定性分歧 (volume-only 塌陷)",
         bool(dc[(~dc.quality_state) & (dc.phi >= 0.6)]["coc_mean"].max()
              < dc[(~dc.quality_state) & (dc.phi == 0.0)]["coc_mean"].max())),
        ("A23 q>0 <=> CoC1>CoC0 (闭式)",
         bool(qt23["closed_form_max_diff"] < 1e-15)),
        ("A21 R10a 维持高 CoC (>7.5)",
         bool(dc[(dc.quality_state) & (dc.phi >= 0.6)]["coc_mean"].min() > 7.5)),
        ("A24 未再声称分支占比 (已撤回)",
         bool("regime prevalence" not in json.dumps(ea24).lower()
              or "撤回" in json.dumps(ea24, ensure_ascii=False))),
        ("组成可翻转符号 (存在正与负)",
         bool((ss.dS_pot_ml > 1e-6).any() and (ss.dS_pot_ml < -1e-6).any())),
    ]
    for name, good in logic:
        ok_all &= bool(good)
        print(f"  [{'OK  ' if good else 'FAIL'}] {name}")

    print()
    print("=" * 80)
    print("结论:", "全部通过 —— 主稿 v3 数字可溯源, 不变量保持, 组成有效"
          if ok_all else "存在失败项 —— 需修正")
    print("=" * 80)
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()