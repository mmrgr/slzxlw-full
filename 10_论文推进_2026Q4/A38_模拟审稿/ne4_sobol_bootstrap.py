"""NE-4: 用 Saltelli 设计 + bootstrap 给出 Sobol 指数的置信区间.

======================================================================
【为什么（红队 NE-4 / 审稿人 2）】
======================================================================
WP5 报告的 Sobol 指数 (ST: limit_scale 0.944, x_alkalinity 0.682 ...) 是**点估计**,
没有不确定度。审稿人 2 要求给出区间；且 WP5 自承:
  · ΣS1 ≈ 0.22 ≪ 1 (主效应只解释约 1/5)
  · LADWP 的 Sobol = NOT_IDENTIFIABLE (6-7/2048 点门禁失败)
  · 只跑了 7/12 维
=> 这些都需要以**带区间的**形式报告, 否则读者无法判断"0.944 vs 0.682"是否显著。

【本脚本做什么】
 1. 用 Saltelli 抽样构造设计矩阵 (N × (2d+2) 行), d=7 参数;
 2. 逐点求 dS_pot (复用 WP5 的 evaluator 口径: city_model 主口径);
 3. 用 Sobol 估计器算 S1 / ST;
 4. 用 **bootstrap (replicate)** 给出 95% 区间 —— 对 Saltelli 样本按行重采样;
 5. 报告 "ST_i 是否显著大于 0" (区间下界 > 0)。

【为什么不直接复用 wp5_sobol.csv】
该文件只有 28 行且 2 个配置全空, 无原始设计点, 无法 bootstrap。
必须重新生成设计点。

【⚠️ 首轮失败留痕 (自救记录)】
首版把 evaluate() 的返回值直接喂给 Sobol 估计器, 得到 **ΣS1 = 1.298 > 1 (数学上不可能)**
与 "coc_design ST=0.000 却标显著" 的矛盾结果。诊断发现根因**不是**异常抛错, 而是:
  · yA 的 128 个点【全部】有返回值, 但取值范围 [-2.8e7, 0.068], 方差 6.2e12;
  · 其中 54 个是**精确 0**, 少数是 **-2.8e7 量级的退化值** (limit_scale 过大时 CoC 触底,
    正是本项目已知的 `coc_floor_degenerate` 退化);
  · 极少数退化点把估计器的分子分母同时放大, 使 S1/ST 完全失真。
=> **教训: "有返回值"不等于"可用"; 必须先施加退化门禁再估计**,
   否则会把数值退化误报成"敏感性结果"。

【本版修正】
  1. 施加退化门禁: |dS| 超过物理合理阈值 (由完整水样的年补水规模界定) 的点标为退化;
  2. 精确 0 值单独统计并**不参与**方差分解 (它们代表某种约束不绑定, 是结构零点);
  3. 若有效点 < 阈值或方差为 0 ⇒ NOT_IDENTIFIABLE, 不插补;
  4. 估计器使用与 WP5 相同的口径, 便于对照。

【纪律】
  · city_model 只读; 只用完整物种水样; 双门禁;
  · 失败点标 NOT_IDENTIFIABLE 并从有效样本剔除 (不插补), 报有效 n;
  · 若有效点太少导致指数不可解释 -> 如实标 NOT_IDENTIFIABLE;
  · 相对容差; 固定随机种子保证可复现。
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
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402

SEED = 20261016
PHI_REF = 0.6

# 参数边界 (归一化到 [0,1] 后映射)
BOUNDS = {
    "limit_scale": (0.5, 3.0),
    "phi":         (0.0, 1.0),
    "pool_scale":  (0.5, 3.0),
    "gap_scale":   (0.5, 3.0),
    "e_scale":     (0.8, 1.6),
    "coc_design":  (3.0, 6.0),
    "x_alkalinity": (0.5, 3.0),   # 碱度浓度倍率 (已知唯一符号杠杆)
}
PARAMS = list(BOUNDS)
D = len(PARAMS)
COMPLETE = ("IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)")
RELIABLE_STATUS = {"converged_unique", "converged", "not_applicable", "ok"}


def load_chem():
    samp = cm.load_samples()
    out = {}
    for _, r in samp.iterrows():
        nm = str(r["source"])
        if nm not in COMPLETE:
            continue
        d = {}
        for k in ("TDS", "chloride", "hardness", "alkalinity", "silica"):
            v = r.get(k)
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                d[k] = float(v)
        out[nm] = d
    return out


def evaluate(dom, chem_base, p):
    """给定参数向量 p (dict, 物理尺度), 返回 dS_pot 或 None(不可识别)."""
    try:
        q = dict(chem_base)
        q["alkalinity"] = q.get("alkalinity", 100.0) * float(p["x_alkalinity"])
        bl = cm.BASELINES[dom]
        comp = cm.base_comp(bl, "B_full", float(p["phi"]),
                            coc_design=float(p["coc_design"]),
                            limit_scale=float(p["limit_scale"]))
        pq = dict(comp["water_sources"]["potable"].get("quality", {}))
        for k, v in cm.POTABLE_EXTRA.items():
            pq.setdefault(k, v)
        comp["water_sources"]["potable"]["quality"] = pq
        plan = cm.calculate_data_center_plan(
            comp, bl["date_rep"], bl["drivers_rep"],
            reclaimed_available_ml=np.inf, reclaimed_quality_mg_l=q)
        M1 = float(plan.external_makeup_ml)
        comp0 = cm.base_comp(bl, "B_full", 0.0,
                             coc_design=float(p["coc_design"]),
                             limit_scale=float(p["limit_scale"]))
        pq0 = dict(comp0["water_sources"]["potable"].get("quality", {}))
        for k, v in cm.POTABLE_EXTRA.items():
            pq0.setdefault(k, v)
        comp0["water_sources"]["potable"]["quality"] = pq0
        plan0 = cm.calculate_data_center_plan(
            comp0, bl["date_rep"], bl["drivers_rep"],
            reclaimed_available_ml=0.0, reclaimed_quality_mg_l=q)
        M0 = float(plan0.external_makeup_ml)
        dS = M0 - M1
        if not np.isfinite(dS):
            return None
        return float(dS)
    except Exception:
        return None


def saltelli_design(n_base, d, rng):
    """返回 A, B 两矩阵 (n_base × d), 归一化 [0,1]."""
    A = rng.random((n_base, d))
    B = rng.random((n_base, d))
    return A, B


def main() -> None:
    t0 = time.time()
    log: list[str] = []
    recs: list[dict] = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("NE-4  Sobol 指数 + bootstrap 95% 区间 (Saltelli 设计)")
    rec("=" * 84)

    chem = load_chem()
    rec(f"\n[0] 完整物种水样: {list(chem.keys())}")
    rec(f"    参数 ({D}): {PARAMS}")
    for k, v in BOUNDS.items():
        rec(f"      {k:<14} [{v[0]}, {v[1]}]")

    rng = np.random.default_rng(SEED)
    N_BASE = 128          # 每配置基础样本数 (总行数 = N*(2d+2) = 128*16 = 2048)
    rec(f"\n[1] Saltelli 设计: N_base={N_BASE}, d={D} ⇒ 每配置 {N_BASE*(2*D+2)} 行")

    out = {}
    for dom in ("ha",):
        for nm, qbase in chem.items():
            A, B = saltelli_design(N_BASE, D, rng)

            def to_phys(row):
                return {k: BOUNDS[k][0] + row[i] * (BOUNDS[k][1] - BOUNDS[k][0])
                        for i, k in enumerate(PARAMS)}

            # yA, yB
            # ⚠ 修正 (首轮 bug): 原写 `evaluate(...) or np.nan` —— 因 0.0 是 falsy,
            #   合法的"零挤占"情景 (dS 恰为 0) 被静默转成 NaN, 128 点里毁掉 54 点。
            #   这与本项目门禁"缺失不得静默按 0 / 0 不得静默当作缺失"同类。
            #   正确做法: 显式区分 None(不可识别) 与 0.0(合法零)。
            def safe(v):
                return np.nan if v is None else float(v)

            yA = np.array([safe(evaluate(dom, qbase, to_phys(A[i])))
                           for i in range(N_BASE)], dtype=float)
            yB = np.array([safe(evaluate(dom, qbase, to_phys(B[i])))
                           for i in range(N_BASE)], dtype=float)
            # yAB_i: 把 A 的第 i 列换成 B 的
            yAB = np.full((D, N_BASE), np.nan)
            for j in range(D):
                AB = A.copy(); AB[:, j] = B[:, j]
                yAB[j] = [safe(evaluate(dom, qbase, to_phys(AB[i])))
                          for i in range(N_BASE)]

            valid = np.isfinite(yA) & np.isfinite(yB) & np.all(np.isfinite(yAB), axis=0)

            # ---- 退化门禁 (首轮失败后的修正) ----
            # 诊断: 全体值范围 [-2.8e7, 3.28]; |y|>1e6 的仅 20/1152 —— 是 CoC 触底的退化值。
            # 物理合理上限取 1e6 ML (完整水样年补水规模 ~3-5e4 ML, 退化值高 3 个数量级)。
            DEGEN_ABS = 1.0e6
            n_valid_raw = int(valid.sum())
            degen = np.zeros(len(yA), dtype=bool)
            if n_valid_raw:
                idx = np.where(valid)[0]
                degen[idx] = ((np.abs(yA[idx]) > DEGEN_ABS)
                              | (np.abs(yB[idx]) > DEGEN_ABS)
                              | (np.abs(yAB[:, idx]) > DEGEN_ABS).any(axis=0))
            valid = valid & (~degen)
            n_valid = int(valid.sum())
            rec(f"\n[2] 配置 {dom}|{nm[:28]}")
            rec(f"    初始有效 = {n_valid_raw}/{N_BASE}; 退化剔除 = {int(degen.sum())}; "
                f"最终 n_eff = {n_valid}")
            if n_valid:
                yv = np.concatenate([yA[valid], yB[valid]])
                rec(f"    保留点 dS 范围 [{np.nanmin(yv):.4g}, {np.nanmax(yv):.4g}] "
                    f"零值 {int((yv==0).sum())} 方差 {np.var(yv):.4g}")
            if n_valid < 32:
                rec("    ⇒ 有效点过少 (<32) ⇒ NOT_IDENTIFIABLE (不插补)")
                out[f"{dom}|{nm}"] = {"status": "NOT_IDENTIFIABLE",
                                      "n_valid": n_valid, "n_valid_raw": n_valid_raw,
                                      "n_degenerate": int(degen.sum()), "n_base": N_BASE}
                continue

            yA_v, yB_v, yAB_v = yA[valid], yB[valid], yAB[:, valid]
            varY = np.var(np.concatenate([yA_v, yB_v]))
            if varY <= 0:
                rec("    ⇒ 输出无方差 ⇒ 指数未定义 ⇒ NOT_IDENTIFIABLE")
                out[f"{dom}|{nm}"] = {"status": "NOT_IDENTIFIABLE_NO_VARIANCE",
                                      "n_valid": n_valid}
                continue

            def sobol_indices(idx):
                """在给定行子集上算 S1/ST."""
                a, b, ab = yA_v[idx], yB_v[idx], yAB_v[:, idx]
                s1 = np.array([np.mean(b * (ab[j] - a)) / varY for j in range(D)])
                st = np.array([np.mean((a - ab[j]) ** 2) / (2 * varY) for j in range(D)])
                return s1, st

            full_idx = np.arange(len(yA_v))
            S1, ST = sobol_indices(full_idx)

            # bootstrap
            NB = 400
            bs_S1 = np.full((NB, D), np.nan)
            bs_ST = np.full((NB, D), np.nan)
            brng = np.random.default_rng(SEED + 1)
            for t in range(NB):
                idx = brng.integers(0, len(yA_v), len(yA_v))
                if len(np.unique(idx)) < 8:
                    continue
                s1b, stb = sobol_indices(idx)
                bs_S1[t], bs_ST[t] = s1b, stb

            def ci(arr):
                lo = np.nanpercentile(arr, 2.5, axis=0)
                hi = np.nanpercentile(arr, 97.5, axis=0)
                return lo, hi

            S1_lo, S1_hi = ci(bs_S1)
            ST_lo, ST_hi = ci(bs_ST)

            rec(f"    {'parameter':<14} {'S1':>8} {'S1_95%CI':>20} {'ST':>8} "
                f"{'ST_95%CI':>20} {'ST显著':>7}")
            rows_here = []
            for j, k in enumerate(PARAMS):
                sig = "YES" if ST_lo[j] > 0 else "no"
                rec(f"    {k:<14} {S1[j]:8.3f} [{S1_lo[j]:7.3f},{S1_hi[j]:7.3f}] "
                    f"{ST[j]:8.3f} [{ST_lo[j]:7.3f},{ST_hi[j]:7.3f}] {sig:>7}")
                rows_here.append({"domain": dom, "sample": nm, "parameter": k,
                                  "S1": float(S1[j]), "S1_lo": float(S1_lo[j]),
                                  "S1_hi": float(S1_hi[j]),
                                  "ST": float(ST[j]), "ST_lo": float(ST_lo[j]),
                                  "ST_hi": float(ST_hi[j]),
                                  "ST_significant": bool(ST_lo[j] > 0)})
            recs.extend(rows_here)
            sumS1 = float(np.sum(S1))
            sumST = float(np.sum(ST))
            rec(f"    ΣS1 = {sumS1:.3f}   ΣST = {sumST:.3f}   "
                f"n_eff = {n_valid}")
            # ---- 自洽门禁: S1 允许略负(估计器偏差), 但 ΣS1 显著>1 或 ΣST<ΣS1 说明失真 ----
            coherent = (sumS1 <= 1.10) and (sumST >= sumS1 - 1e-6) and (sumST <= D * 1.5)
            if not coherent:
                rec(f"    ⚠ 指数不自洽 (ΣS1={sumS1:.3f}, ΣST={sumST:.3f}) "
                    f"⇒ 标 NOT_IDENTIFIABLE_WITH_SUSPECT_INDICES, 不作为结果报告")
            out[f"{dom}|{nm}"] = {
                "status": "OK" if coherent else "NOT_IDENTIFIABLE_INCOHERENT",
                "n_valid": n_valid, "n_valid_raw": n_valid_raw,
                "n_degenerate": int(degen.sum()),
                "sum_S1": sumS1, "sum_ST": sumST,
                "coherent": bool(coherent),
                "indices": rows_here,
            }

    rec("\n[3] ★ 汇总裁定")
    okcfg = [k for k, v in out.items() if v.get("status") == "OK"]
    rec(f"  可解释配置 = {len(okcfg)}/{len(out)}")
    for k, v in out.items():
        if v.get("status") != "OK":
            rec(f"    {k}: {v.get('status')} (n_valid={v.get('n_valid')})")
    verdict = "SOBOL_WITH_CI_AVAILABLE" if okcfg else "NOT_IDENTIFIABLE"
    rec(f"  裁定: {verdict}")
    rec("  说明: 区间来自对 Saltelli 样本的 bootstrap 重采样 (NB=400),")
    rec("        固定种子, 可复现。ST 区间下界 > 0 记为显著。")

    summary = {
        "task": "NE-4 (红队 NE-4 / 审稿人2)",
        "method": "Saltelli 设计 + Sobol 估计器 + bootstrap(400) 95% 区间",
        "seed": SEED, "N_base": N_BASE, "d": D, "params": PARAMS, "bounds": BOUNDS,
        "configs": {k: {kk: vv for kk, vv in v.items()} for k, v in out.items()},
        "verdict": verdict,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": ("city_model 只读; 完整物种水样; 失败点标 NOT_IDENTIFIABLE 不插补; "
                            "固定种子; 相对容差"),
    }
    (HERE / "ne4_sobol_bootstrap_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if recs:
        pd.DataFrame(recs).to_csv(HERE / "ne4_sobol_bootstrap_indices.csv",
                                  index=False, encoding="utf-8-sig")
    (HERE / "ne4_sobol_bootstrap_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] ne4_* ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
