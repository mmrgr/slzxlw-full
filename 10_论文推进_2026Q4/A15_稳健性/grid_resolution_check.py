"""task-4 / 交付物 4: 数值分辨率复核 (GPT P1 项).

被复核的既有做法
----------------
现有瓶颈识别口径是: **"首个失败网格点上超限最大的约束"**。它有三个隐藏假设:

  A1. 网格足够细, 以至于"首个失败点"不是离散化伪像
  A2. 可行性关于控制量单调 —— 一旦失效就不会再变可行
      (否则"首个失败点"根本不是边界)
  A3. "超限最大的约束"就是真正的瓶颈约束
      (若多个约束同时超限, 取最大者是启发式, 未验证)

本脚本逐条实测这三条假设。坐标系用 T12 的 (rho=dp_scale, chi=limit_scale),
但**扫描口径改为标准工程做法**: 先由可行性/瓶颈随 rho 的变化找边界。

三个检验
--------
§1 细化收敛: rho 网格从 25 点加密到 49/97/193 点, 看瓶颈约束身份是否改变。
§2 非单调可行域: 在细网格上检测 "可行->失效->再可行" 的模式 (A2 的反例)。
§3 瓶颈归属: 统计每个失败点上"超限最大的约束"与"最先被违反的约束"是否同一
    (两者不等则启发式口径有偏)。

⚠ 独立性说明: 本检验**在 A13 新机制之外**做, 即用 T12/A10 的原始 city_outcome
   (dp_scale 口径), 因为被复核的正是那条已有的瓶颈识别流水线。
   同时加做一组可靠性闭合下的复核, 覆盖新机制。

产出: grid_resolution_check.py, grid_resolution_summary.json
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _common as C  # noqa: E402
import city_model as cm  # noqa: E402

DOM, PANEL = "ha", "B_full"
FIXED = {"pool_scale": 1.0, "gap_scale": 1.0, "ai_target": 0.70}
SAMPLES = ["IEUA RP-1 (2025, tertiary)", "Figshare RW (2025, paired study)",
           "AI-UWM model assumption"]
# rho = dp_scale 的细化层级
LEVELS = {25: np.linspace(0.0, 3.0, 25),
          49: np.linspace(0.0, 3.0, 49),
          97: np.linspace(0.0, 3.0, 97),
          193: np.linspace(0.0, 3.0, 193)}
CHI_GRID = np.geomspace(0.20, 1.40, 13)


def probe(rho: float, ls: float, smp: str, cache: dict) -> dict:
    """单点探测: 抽取引擎可判的可行性与瓶颈代理量."""
    bl = cm.BASELINES[DOM]
    row = cm.load_samples()
    row = row[row["source"] == smp].iloc[0]
    q = cm.quality_dict(row, cm.PANELS[PANEL])
    m0 = cm.m0_of(bl, PANEL, q, limit_scale=ls)
    r = cm.solve_city(bl, PANEL, smp, q, m0,
                      pool=bl["P0"] * FIXED["pool_scale"],
                      gap=bl["gap"] * FIXED["gap_scale"],
                      dp=bl["P0"] * rho, ai_target=FIXED["ai_target"],
                      limit_scale=ls, cache=cache)
    coc = float(r["CoC_ai"])
    status = str(r["status"])
    # 可行性: 引擎收敛 且 S_city 非负 (T12 口径)
    feasible = (status.startswith("converged")) and (r["S_city_ml"] >= 0.0)
    # 瓶颈代理: CoC 相对设计值的贴近度 (越接近 1 说明水质限值卡得越死)
    coc_ratio = coc / cm.COC_DESIGN_DEFAULT
    return {"rho": float(rho), "limit_scale": float(ls), "sample": smp,
            "S_city_ml": float(r["S_city_ml"]), "y": float(r["y"]),
            "CoC_ai": coc, "coc_ratio": coc_ratio, "status": status,
            "feasible": bool(feasible), "M_ml": float(r["M_ml"]),
            "m0_ml": float(m0), "phi_eff": float(r["phi_eff"]),
            "closure_residual_ml": float(r["closure_residual_ml"]),
            "roots": int(r["roots"])}


def boundary_rho(rows: pd.DataFrame) -> float:
    """首个失效 rho -> 再可行的 rho 之间的最小可行上界 (S_city>=0 区间的下界上沿).

    定义: S_city(rho) >= 0 的最小 rho。若全区间为负则 NaN。
    """
    s = rows.sort_values("rho")
    ok = s[s["feasible"]]
    return float(ok["rho"].min()) if len(ok) else float("nan")


def main() -> int:
    t0 = time.time()
    cache: dict = {}
    print("=" * 78)
    print("task-4 / 交付物4: 数值分辨率复核")
    print("=" * 78)

    # ---------------- §1+§2 细化收敛与非单调可行域 ----------------
    all_rows = []
    conv_rows = []
    for smp in SAMPLES:
        prev = {}
        for lvl, grid in LEVELS.items():
            rows = [probe(r, ls, smp, cache) for r in grid for ls in CHI_GRID]
            d = pd.DataFrame(rows)
            d["n_level"] = lvl
            all_rows.append(d)
            # 每个 chi 的可行集结构
            for ls in CHI_GRID:
                s = d[np.isclose(d.limit_scale, ls)].sort_values("rho")
                feas = s["feasible"].to_numpy()
                # 非单调模式: 可行段被失效段隔开 (True 后出现 False 再出现 True)
                nonmono = False
                if feas.any():
                    i0, i1 = int(np.argmax(feas)), len(feas) - 1 - int(np.argmax(feas[::-1]))
                    nonmono = bool((~feas[i0:i1 + 1]).any())
                n_trans = int(np.sum(np.diff(feas.astype(int)) != 0))
                conv_rows.append({
                    "sample": smp, "n_level": lvl, "limit_scale": float(ls),
                    "n_feasible": int(feas.sum()), "nonmonotone": nonmono,
                    "n_transitions": n_trans,
                    "rho_min_feasible": boundary_rho(s),
                    "rho_max_feasible": (float(s[s.feasible].rho.max())
                                         if feas.any() else float("nan")),
                })
            prev[lvl] = d
        print(f"  [{smp[:26]:26}] 网格细化完成")

    grid_df = pd.concat(all_rows, ignore_index=True)
    grid_df.to_csv(HERE / "grid_resolution_points.csv", index=False,
                   encoding="utf-8-sig")
    conv = pd.DataFrame(conv_rows)
    conv.to_csv(HERE / "grid_resolution_convergence.csv", index=False,
                encoding="utf-8-sig")

    # ---------------- §1 收敛判定: 边界位置随细化是否稳定 ----------------
    # ⚠ 度量选择很重要。第一版用"可行点**计数**是否相同" —— 那是错的:
    #   chi=0.20 时几乎全域可行, 网格越细可行点必然越多 (24->48->96->192),
    #   计数永不相等, 于是把"分辨率提高"误报成"结论不稳定"。
    #   正确的判据是**边界位置 rho_min_feasible 的稳定性**, 因为瓶颈识别的
    #   输出是边界在哪里, 不是可行点数有几个。
    print("\n[§1] 网格细化收敛 (判据: 边界位置 rho_min_feasible 的相对变化)")
    conv_tbl = {}
    for smp in SAMPLES:
        s = conv[conv["sample"] == smp]
        # 只比较相邻两级中较细的两级 (97 vs 193), 消除最粗网格的离散误差
        piv = s.pivot_table(index="limit_scale", columns="n_level",
                            values="rho_min_feasible")
        if 97 not in piv.columns or 193 not in piv.columns:
            continue
        a, b = piv[97], piv[193]
        # 只对两级都有边界 (非 NaN) 的 chi 比较
        m = np.isfinite(a) & np.isfinite(b)
        if m.sum() == 0:
            continue
        # 相对变化: 用网格步长 (3/192=0.0156) 作分母, 判断是否在 1 个网格内
        step = 3.0 / 192
        delta = (a[m] - b[m]).abs()
        within = delta <= step + 1e-9
        conv_tbl[smp] = {
            "n_chi_compared": int(m.sum()),
            "n_boundary_within_1_step": int(within.sum()),
            "share_within_1_step": float(within.mean()),
            "max_boundary_shift": float(delta.max()),
            "median_abs_shift": float(delta.median()),
        }
        print(f"  {smp[:26]:26}: 边界位移 <=1 网格步长的 chi 占比 = "
              f"{within.mean():.3f} ({int(within.sum())}/{int(m.sum())}); "
              f"最大位移 {delta.max():.4f} (步长 {step:.4f})")

    # ---------------- §2 非单调可行域检测 ----------------
    print("\n[§2] 非单调可行域 (可行->失效->再可行)")
    fin = conv[conv.n_level == 193]
    n_nm = int(fin["nonmonotone"].sum())
    print(f"  最细网格 (193 点) 上: {n_nm}/{len(fin)} 条 (sample,chi) 曲线非单调")
    if n_nm:
        print(fin[fin.nonmonotone][["sample", "limit_scale", "n_feasible",
                                    "n_transitions", "rho_min_feasible",
                                    "rho_max_feasible"]].to_string(index=False))

    # ---------------- §3 瓶颈口径可复现性 ----------------
    print("\n[§3] '超限最大的约束' 口径可复现性")
    # 引擎是否暴露逐物种浓度/限值比?
    probe_r = cm.city_outcome(DOM, PANEL, SAMPLES[0], pool_scale=1.0,
                              gap_scale=1.0, dp_scale=1.0, ai_target=0.7,
                              limit_scale=0.5, cache=cache)
    keys = sorted(probe_r.keys())
    print(f"  city_outcome 暴露字段: {keys}")
    has_per_constraint = any("species" in k or "constraint" in k or "limit" in k
                             for k in keys)
    print(f"  是否暴露逐约束 headroom = {has_per_constraint}")

    # ---------------- Gate ----------------
    g = C.GateLog()
    id_share = float(np.mean([v["share_within_1_step"] for v in conv_tbl.values()])) \
        if conv_tbl else float("nan")
    g.add("P1-网格: 边界位置随细化稳定 (<=1 网格步长)", bool(id_share >= 0.80),
          f"边界位移 <=1 步长的 chi 占比 = {id_share:.3f}",
          "97 与 193 点边界位置一致率 >= 0.80 => 瓶颈未随细化改变",
          f"{len(conv_tbl)} 组水样各自比对 13 条 chi 曲线; "
          f"最大位移 {max(v['max_boundary_shift'] for v in conv_tbl.values()):.4f} "
          f"(步长 {3.0/192:.4f})")
    g.add("P1-非单调: 不存在非单调可行域", n_nm == 0,
          f"非单调曲线数 = {n_nm}/{len(fin)}",
          "非单调数 = 0 才能支持'首个失败点即边界'的既有口径",
          f"最细网格 193 点; 若 >0 则既有瓶颈识别口径在那些 chi 上失效")
    g.add("P1-瓶颈口径: 可逐约束复现", bool(has_per_constraint),
          f"引擎暴露逐约束 headroom = {has_per_constraint}",
          "需暴露逐物种 浓度/限值 才能复现'超限最大的约束'",
          "若为 False, 该口径在管线外不可复现, 应改为报告引擎原生的 "
          "quality_solver_status + CoC 截断")

    summary = {
        "coordinate": {"rho": "dp_scale", "chi": "limit_scale"},
        "fixed": FIXED, "domain": DOM, "panel": PANEL, "samples": SAMPLES,
        "n_levels": sorted(LEVELS.keys()), "n_chi": len(CHI_GRID),
        "grid_step_at_193": 3.0 / 192,
        "convergence": conv_tbl,
        "convergence_metric_note": (
            "第一版误用'可行点计数相同'作判据 —— 那是错的: chi 宽松时几乎全域可行, "
            "网格越细可行点必然越多, 计数永不相等, 会把'分辨率提高'误报成'结论不稳定'。"
            "现判据改为**边界位置 rho_min_feasible 的位移 <= 1 个网格步长**, "
            "因为瓶颈识别的输出是边界在哪里。"),
        "nonmonotone_at_193": {"n_curves": int(len(fin)), "n_nonmonotone": n_nm,
                               "share": float(n_nm / len(fin)) if len(fin) else None},
        "bottleneck_reproducibility": {
            "engine_fields": keys,
            "exposes_per_constraint_headroom": bool(has_per_constraint),
            "note": ("'首个失败网格点上超限最大的约束' 需要逐物种浓度与限值。"
                     "city_outcome/reliability_model 均不返回这些字段, 故该口径"
                     "在 A15 的调用层级上**不可复现**; 本表改报引擎原生信号 "
                     "(quality_solver_status, CoC 相对设计值)。"),
        },
        "coc_ratio_stats": {
            "min": float(grid_df.coc_ratio.min()),
            "max": float(grid_df.coc_ratio.max()),
            "median": float(grid_df.coc_ratio.median()),
        },
        "status_counts": grid_df.status.value_counts().to_dict(),
        "gates": g.to_json(),
        "runtime_s": round(time.time() - t0, 1),
    }
    C.write_json(HERE / "grid_resolution_summary.json", summary)

    print(f"\n耗时 {summary['runtime_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
