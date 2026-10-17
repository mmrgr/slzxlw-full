# -*- coding: utf-8 -*-
"""独立核验 A37 六主图所需的全部核心数值。只读。"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
out = {}

# ---------- A13 主网格 ----------
g = pd.read_csv(ROOT / "A13_可靠性机制" / "supply_state_regimes.csv")
out["A13_rows_total"] = len(g)
out["A13_cols"] = list(g.columns)

# 双门禁
gate = (g["status"] == "converged_unique") & (~g["coc_floor_degenerate"].astype(bool))
gm = g[gate].copy()
out["A13_n_eff"] = int(len(gm))

# 列名互换：x_ai_B1_ml 实为 B2 支路取水；x_ai_B2_ml 恒 0
out["x_ai_B1_ml_gt0_frac"] = float((g["x_ai_B1_ml"] > 0).mean())
out["x_ai_B2_ml_all0"] = bool((g["x_ai_B2_ml"] == 0).all())

# 恒等式残差。按更正说明：dS_pot_ml = max(0, inc_B2 - inc_B1) - (M0-M1) - x_ai_B1_ml
# 但原文件 dS_ident_ml 已给；直接比较 dS_pot_ml vs dS_ident_ml
resid = (gm["dS_pot_ml"] - gm["dS_ident_ml"]).abs()
out["ident_resid_absmax"] = float(resid.max())
out["ident_resid_relmax"] = float((resid / gm["dS_pot_ml"].abs().clip(lower=1e-30)).max())

# 用列重建
recon = np.maximum(0.0, gm["inc_B2_ml"] - gm["inc_B1_ml"]) - (gm["M0_ml"] - gm["M1_ml"]) - gm["x_ai_B1_ml"]
out["recon_resid_absmax_vs_dSpot"] = float((recon - gm["dS_pot_ml"]).abs().max())

d = gm["dS_pot_ml"]
tol = 1e-9
out["sym_neg"] = int((d < -tol).sum())
out["sym_pos"] = int((d > tol).sum())
out["sym_zero"] = int((d.abs() <= tol).sum())

# q 分组
out["q_gt0"] = int((gm["pool_ml"] > 0).sum())
out["q_lt0"] = int((gm["pool_ml"] < 0).sum())
out["q_eq0"] = int((gm["pool_ml"] == 0).sum())

h = gm[gm["pool_ml"] > 0]
out["q_gt0_harmful"] = int((h["dS_pot_ml"] > tol).sum())
out["q_gt0_n"] = int(len(h))
out["q_gt0_beneficial"] = int((h["dS_pot_ml"] < -tol).sum())

# inc_B2-inc_B1 分布（更正说明 §5）
diff = gm["inc_B2_ml"] - gm["inc_B1_ml"]
out["incdiff_lt0"] = int((diff < 0).sum())
out["incdiff_gt0"] = int((diff > 0).sum())
out["incdiff_eq_negxai"] = int(np.isclose(diff, -gm["x_ai_B1_ml"]).sum())

out["status_counts"] = g["status"].value_counts().to_dict()
out["coc_degen_true"] = int(g["coc_floor_degenerate"].astype(bool).sum())

# CoC_ai 与碱度关系
out["CoC_ai_describe"] = {k: float(v) for k, v in gm["CoC_ai"].describe().items()}
out["CoC_ai_pos_count"] = int((gm["CoC_ai"] > 0).sum())

print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
