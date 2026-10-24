"""task-1 独立复现: 用 city_model.py 复算 T11 的 5 个情景, 与冻结 CSV 比对.

只读: 不写 A10/ 下任何文件.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

A10 = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4\A10_敏感性与边界")
sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402

d = pd.read_csv(A10 / "T11_uncertainty_samples.csv", encoding="utf-8-sig")
print("csv rows (incl header):", len(d) + 1, "| cols:", len(d.columns))

# 取 5 个情景: 覆盖 ha/co 与不同 S_city 符号
idx = [0, 1, 2, 3, 4]
rows = d.iloc[idx]

out = []
for i, r in rows.iterrows():
    rec = cm.city_outcome(
        str(r["domain"]),
        str(r["panel"]),
        str(r["sample"]),
        pool_scale=float(r["pool_scale"]),
        gap_scale=float(r["gap_scale"]),
        ai_target=float(r["ai_target"]),
    )
    got = {
        "i": int(i),
        "domain": str(r["domain"]),
        "panel": str(r["panel"]),
        "sample": str(r["sample"])[:28],
        "S_city_dp1_repro": float(rec["S_city_ml"]),
        "S_city_dp1_frozen": float(r["S_city_dp1_ml"]),
        "y_repro": float(rec["y"]),
        "y_frozen": float(r["y_dp1"]),
        "status": rec["status"],
        "closure_residual_ml": rec["closure_residual_ml"],
    }
    got["dS_abs"] = abs(got["S_city_dp1_repro"] - got["S_city_dp1_frozen"])
    got["dS_rel"] = got["dS_abs"] / max(abs(got["S_city_dp1_frozen"]), 1e-12)
    got["dy_abs"] = abs(got["y_repro"] - got["y_frozen"])
    out.append(got)

print("\n=== 5 情景复现 (dp=1.0) ===")
w = max(abs(o["S_city_dp1_frozen"]) for o in out)
for o in out:
    print(
        f"[{o['i']}] {o['domain']:2s} {o['panel']:9s} {o['sample']:28s} "
        f"repro={o['S_city_dp1_repro']:16.6f} frozen={o['S_city_dp1_frozen']:16.6f} "
        f"|dS|={o['dS_abs']:.3e} rel={o['dS_rel']:.3e} dy={o['dy_abs']:.3e} "
        f"{o['status']}"
    )

mx = max(o["dS_rel"] for o in out)
mxa = max(o["dS_abs"] for o in out)
print(f"\nmax |dS| = {mxa:.6e} ML ; max rel = {mx:.6e}")
print("PASS" if mx < 1e-9 else "CHECK")

(Path(__file__).resolve().parent / "repro_5cases.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
)
