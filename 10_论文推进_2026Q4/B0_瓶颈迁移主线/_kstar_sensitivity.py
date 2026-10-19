# -*- coding: utf-8 -*-
"""k* 的双重敏感性：对份额比 ρ=α/β 与对 r* 的参数不确定性。

【为什么必须做】
`k* = (1/r* − 1)/ρ`，其中 ρ ≡ α/β =（数据中心占全市自来水份额）/（占全市再生水份额）。

主稿与英文稿都报 `k* = 3.50`，但它**条件于 Santa Clara 的 ρ = 6%/26% = 0.2308**，
以及标称 `r* = 0.5532`。若不加说明地把它当普适常数，判据会被误用：
ρ 越大（数据中心相对更依赖自来水），k* 越小，越多城市会"越过"。

同时 `r*` 本身有 ±10% 参数不确定性（正文已承认），而 k* 对 r* 并非线性。

本脚本给出：
  1. k* 对 ρ 的敏感性（ρ ∈ [0.1, 2.0]）；
  2. k* 对 r* 的敏感性（r* ∈ [0.50, 0.61]，覆盖 ±10%）；
  3. 加州 169 个系统在不同 ρ 下"k < k*"的计数；
  4. 一个**保守判据**：取 ρ = 1（数据中心在两类水中份额相同，最不利于"越过"的取值），
     给出该保守边界下的城市数。

产物：_ca_kstar_sensitivity.json + 控制台表
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
CLEAN = HERE / "_ca_k_clean.json"
OUT = HERE / "_ca_kstar_sensitivity.json"

R_STAR = 0.5532


def kstar(r_star: float, rho: float) -> float:
    return (1.0 / r_star - 1.0) / rho


def main() -> None:
    data = json.loads(CLEAN.read_text(encoding="utf-8"))
    recs = data["records"]
    ks = sorted(float(r["k"]) for r in recs)
    n = len(ks)
    print(f"加州系统 n = {n}")

    # ---- 1. k* 对 ρ 的敏感性 ----
    print(f"\n{'='*72}\n[1] k* 对份额比 ρ = α/β 的敏感性（r* = {R_STAR}）\n{'='*72}")
    print(f"{'ρ':>6} {'k*':>8} {'k<k* 的系统数':>14} {'占比':>8}   含义")
    rho_rows = []
    for rho in (0.10, 0.20, 0.2308, 0.30, 0.50, 1.00, 2.00):
        kst = kstar(R_STAR, rho)
        cnt = sum(1 for x in ks if x < kst)
        pct = 100.0 * cnt / n
        if abs(rho - 0.2308) < 1e-9:
            note = "← Santa Clara 6%/26%"
        elif abs(rho - 1.0) < 1e-9:
            note = "← 保守边界（两类水份额相同）"
        else:
            note = ""
        print(f"{rho:6.4f} {kst:8.3f} {cnt:14d} {pct:7.1f}%   {note}")
        rho_rows.append({"rho": rho, "k_star": round(kst, 4), "n_below": cnt,
                         "pct_below": round(pct, 2), "note": note})

    # ---- 2. k* 对 r* 的敏感性 ----
    print(f"\n{'='*72}\n[2] k* 对 r* 的敏感性（ρ = 0.2308）\n{'='*72}")
    print(f"{'r*':>8} {'k*':>8} {'k<k* 的系统数':>14} {'占比':>8}")
    r_rows = []
    for rs in (0.50, 0.52, 0.5532, 0.58, 0.61):
        kst = kstar(rs, 0.2308)
        cnt = sum(1 for x in ks if x < kst)
        pct = 100.0 * cnt / n
        print(f"{rs:8.4f} {kst:8.3f} {cnt:14d} {pct:7.1f}%")
        r_rows.append({"r_star": rs, "k_star": round(kst, 4), "n_below": cnt,
                       "pct_below": round(pct, 2)})

    # ---- 3. 二维网格：ρ × r* ----
    print(f"\n{'='*72}\n[3] 二维网格：k*（行=ρ，列=r*）\n{'='*72}")
    rs_grid = [0.50, 0.5532, 0.61]
    print(f"{'ρ\\r*':>7}" + "".join(f"{x:>9.4f}" for x in rs_grid))
    grid = []
    for rho in (0.10, 0.2308, 0.50, 1.00):
        row = [kstar(rs, rho) for rs in rs_grid]
        print(f"{rho:7.4f}" + "".join(f"{v:9.3f}" for v in row))
        grid.append({"rho": rho, "k_star_by_rstar": [round(v, 4) for v in row]})

    # ---- 4. 保守判据 ----
    kst_cons = kstar(R_STAR, 1.0)
    cnt_cons = sum(1 for x in ks if x < kst_cons)
    print(f"\n{'='*72}\n[4] 保守判据（ρ = 1，即数据中心在两类水的份额相同）\n{'='*72}")
    print(f"k* = {kst_cons:.3f}；加州 {cnt_cons}/{n} = {100*cnt_cons/n:.1f}% 的系统 k < k*")
    print("含义：即使假设数据中心在自来水与再生水中的份额相同（最不利于'越过'的设定），")
    print(f"      仍有 {cnt_cons} 个系统的 k 低于该边界。")

    # ---- 5. 分布的极端值 ----
    print(f"\n{'='*72}\n[5] 加州 k 分布的定位\n{'='*72}")
    import statistics
    print(f"  min={ks[0]:.4f}  p10={ks[int(0.10*n)]:.4f}  median={statistics.median(ks):.4f}  "
          f"p90={ks[int(0.90*n)]:.4f}  max={ks[-1]:.4f}")
    print(f"  k < 3.50（ρ=6/26）: {sum(1 for x in ks if x<3.50)}")
    print(f"  k < 4.16（r*=0.51）: {sum(1 for x in ks if x<kstar(0.51,0.2308))}")

    out = {
        "n_systems": n,
        "r_star_nominal": R_STAR,
        "k_star_nominal": round(kstar(R_STAR, 0.2308), 4),
        "rho_baseline": 0.2308,
        "rho_sensitivity": rho_rows,
        "rstar_sensitivity": r_rows,
        "grid_rho_x_rstar": grid,
        "conservative_boundary": {
            "rho": 1.0,
            "k_star": round(kst_cons, 4),
            "n_below": cnt_cons,
            "pct_below": round(100 * cnt_cons / n, 2),
        },
        "distribution": {
            "min": ks[0], "median": statistics.median(ks), "max": ks[-1],
        },
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
