"""T12: 条件边界曲面 —— S_city 在 (rho, chi) 平面上的响应与零界面.

坐标 (无量纲, 与 T9 折叠一致)
-----------------------------
    rho  := dP_scale = 新增回用产能 / 再生水池规模 P0        [0, 3]
    chi  := CoC_lim / CoC_design  (水质限值严格度, 无量纲)     [~0.2, 1.0]
            chi 由**整体缩放引擎水质限值** limit_scale 实现:
                limits <- limit_scale * LIMIT_BASE
                CoC_lim = min_i L_i / c_i  (再被设计值 CoC_design 截断)
            chi = min(limit_scale * CoC_lim_base, CoC_design) / CoC_design

图上量: S_city (ML) 与 y = S_city/M0 (无量纲).

纪律 (规划 §4 T12 + 审计教训)
    * 不预设必然存在清晰的零界面; 若 S_city 随 (rho,chi) 连续变化, 就如实报告响应曲面.
    * S_city 非负区域仅表示"在该会计口径下、该水质缺省值下"的城市净取水下降;
      不代表真实城市获益 (见主张限定 L1/L2/L3).
    * chi 的实现依赖引擎占位限值 (审计 B3): 报告的是 **无量纲** 响应, 不是绝对阈值.

固定: pool_scale=1, gap_scale=1, ai_target=0.7, domain=ha, panel=B_full, 规则 Ls.
对 3 组水样各出一张曲面 (IEUA 三级再生水 / 模型假定 / Figshare RW), 展示水样依赖.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import city_model as cm  # noqa: E402

DP_GRID = np.linspace(0.0, 3.0, 25)
LS_GRID = np.geomspace(0.30, 1.40, 17)
SAMPLES = ["IEUA RP-1 (2025, tertiary)", "AI-UWM model assumption",
           "Figshare RW (2025, paired study)"]
DOM, PANEL, POOL, GAP, AIT = "ha", "B_full", 1.0, 1.0, 0.70


def realized_chi(sample, q, limit_scale, coc_design=cm.COC_DESIGN_DEFAULT):
    """由限值缩放反解实现的 chi (保守物种比值法, 供坐标标注)."""
    coc_lim = min(float(limit_scale) * cm.PANELS[PANEL][sp] / q[sp]
                  for sp in cm.PANELS[PANEL] if sp in q and q[sp] > 0)
    return min(coc_lim, coc_design) / coc_design, min(coc_lim, coc_design)


def main() -> int:
    samples = cm.load_samples()
    rows = []
    cache: dict = {}
    for sample in SAMPLES:
        row = samples[samples["source"] == sample].iloc[0]
        q = cm.quality_dict(row, cm.PANELS[PANEL])
        if not q:
            print(f"[skip] {sample}: 无完整离子组")
            continue
        for d in DP_GRID:
            for ls in LS_GRID:
                chi, coc_lim = realized_chi(sample, q, ls)
                o = cm.city_outcome(DOM, PANEL, sample, pool_scale=POOL, gap_scale=GAP,
                                    dp_scale=float(d), ai_target=AIT, limit_scale=float(ls),
                                    cache=cache)
                rows.append({"sample": sample, "dp_scale": float(d),
                             "limit_scale": float(ls), "chi": float(chi),
                             "CoC_lim_realized": float(coc_lim),
                             "S_city_ml": o["S_city_ml"], "y": o["y"],
                             "phi_eff": o["phi_eff"], "CoC_ai": o["CoC_ai"],
                             "status": o["status"]})
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "T12_surface.csv", index=False, encoding="utf-8-sig")

    # 逐 (sample, chi) 提取零界面 dp*(chi)
    curves = []
    for (sample, chi), g in df.groupby(["sample", "chi"]):
        g = g.sort_values("dp_scale")
        s = g.S_city_ml.to_numpy()
        x = g.dp_scale.to_numpy()
        sign = np.sign(np.round(s, 9))
        idx = np.where(np.diff(sign) != 0)[0]
        if len(idx):
            i = int(idx[0])
            x0, x1, y0, y1 = x[i], x[i + 1], s[i], s[i + 1]
            root = x0 if y1 == y0 else x0 - y0 * (x1 - x0) / (y1 - y0)
        else:
            root = np.nan
        curves.append({"sample": sample, "chi": float(chi),
                       "CoC_lim_realized": float(g.CoC_lim_realized.iloc[0]),
                       "dp_star_dimensionless": float(root) if np.isfinite(root) else np.nan,
                       "found": bool(np.isfinite(root)),
                       "S_city_min": float(s.min()), "S_city_max": float(s.max())})
    cv = pd.DataFrame(curves).sort_values(["sample", "chi"])
    cv.to_csv(HERE / "T12_boundary_curves.csv", index=False, encoding="utf-8-sig")

    summary = {
        "axes": {"rho": "dP_scale = new reuse capacity / P0", "chi": "CoC_lim/CoC_design"},
        "fixed": {"domain": DOM, "panel": PANEL, "pool_scale": POOL,
                  "gap_scale": GAP, "ai_target": AIT, "rule": "Ls (incumbent claim=0)"},
        "n_points": int(len(df)),
        "samples": SAMPLES,
        "statuses": sorted(df.status.unique().tolist()),
        "boundary_found_share": float(cv.found.mean()),
        "boundary_by_sample": {
            s: cv[cv["sample"] == s][["chi", "dp_star_dimensionless", "found"]]
                .round(4).to_dict(orient="records") for s in cv["sample"].unique()},
        "y_range": [float(df.y.min()), float(df.y.max())],
        "interpretation": "conditional response surface of the city-level estimand; the "
                          "zero contour (when it exists) is the minimum new reuse capacity "
                          "rho* needed for non-negative city saving at a given water-quality "
                          "severity chi. Surface is conditional on frozen placeholder limits.",
    }
    (HERE / "T12_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"[T12] {len(df)} 点 | 状态={summary['statuses']}")
    print(f"  零界面可测比例: {summary['boundary_found_share']:.3f}")
    for s in cv["sample"].unique():
        sub = cv[(cv["sample"] == s) & cv.found]
        if len(sub):
            print(f"  {s[:34]:34s} dp*: chi=0.5->{sub.iloc[(sub.chi-0.5).abs().argmin()].dp_star_dimensionless:.2f} "
                  f"| chi=0.9->{sub.iloc[(sub.chi-0.9).abs().argmin()].dp_star_dimensionless:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
