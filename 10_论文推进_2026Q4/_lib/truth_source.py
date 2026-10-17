"""单一真相源: 从权威产物实时计算所有"结论级"数字 (2026-10-17).

【解决的根因】
本项目的核心架构债是: 数字散落在主稿/SI 各处, 靠人工同步,
已三次出现"改了 A 漏了 B"。

本模块把这些**结论级**数字集中计算一次, 供门禁与审计脚本调用。
**注意**: 它不重写主稿(那会破坏可读性), 而是提供"唯一真相"用于**比对**。

【用法】
    from truth_source import TRUTH
    TRUTH["n_reliable"]  # 839
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def _rel(d):
    return d[(d.status == "converged_unique") & (~d.coc_floor_degenerate.astype(bool))]


def compute() -> dict:
    d = pd.read_csv(ROOT / "A13_可靠性机制/supply_state_regimes.csv")
    rel = _rel(d).copy()
    C = rel.inc_B2_ml - rel.inc_B1_ml
    F = rel.M0_ml - rel.M1_ml
    x = rel.x_ai_B1_ml
    q = (rel.M0_ml - rel.M1_ml) / rel.M1_ml
    pure = np.isclose(x, C, rtol=1e-9)
    nodisp = np.isclose(C, 0, atol=1e-9)
    resid = (rel.dS_pot_ml - (C - F - x)).abs()
    scale = rel[["M0_ml", "M1_ml"]].abs().max(axis=1)

    out = {
        # 样本量
        "n_all": int(len(d)),
        "n_reliable": int(len(rel)),
        "status_fail": int((d.status != "converged_unique").sum()),
        "no_convergence": int((d.status == "no_convergence").sum()),
        "non_unique": int((d.status == "non_unique").sum()),
        "coc_degenerate": int(d.coc_floor_degenerate.sum()),
        # 头条符号统计(严格口径)
        "neg": int((rel.dS_pot_ml < 0).sum()),
        "pos": int((rel.dS_pot_ml > 0).sum()),
        "zero": int((rel.dS_pot_ml == 0).sum()),
        # q 分组
        "q_pos": int((q > 1e-9).sum()),
        "q_zero": int((q.abs() <= 1e-9).sum()),
        "q_neg": int((q < -1e-9).sum()),
        "q_pos_harmful": int(((q > 1e-9) & (rel.dS_pot_ml > 0)).sum()),
        # 分支
        "pure_disp": int(pure.sum()),
        "nodisp": int(nodisp.sum()),
        "nodisp_neg": int((rel[nodisp].dS_pot_ml < 0).sum()),
        # 恒等式残差
        "resid_abs": float(resid.max()),
        "resid_rel": float((resid / scale).max()),
        # 不变量
        "contradiction": int(((rel.dS_pot_ml > 1e-6) & (F > 1e-6)).sum()),
    }
    # 分组成
    for s, g in rel.groupby("sample"):
        key = {"LADWP": "ladwp", "IEUA": "ieua",
               "Figshare": "figshare", "AI-UWM": "assumed"}
        for k, v in key.items():
            if s.startswith(k) or (k == "assumed" and "assumption" in s):
                out[f"{v}_n"] = int(len(g))
                out[f"{v}_neg"] = int((g.dS_pot_ml < 0).sum())
                out[f"{v}_pos"] = int((g.dS_pot_ml > 0).sum())
                break
    return out


TRUTH = compute()

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print("单一真相源 (从主网格实时计算)")
    print("=" * 60)
    for k, v in TRUTH.items():
        vs = f"{v:.6g}" if isinstance(v, float) else str(v)
        print(f"  {k:<20} {vs}")
    (ROOT / "_lib/truth_source.json").write_text(
        json.dumps(TRUTH, ensure_ascii=False, indent=1, default=float),
        encoding="utf-8")
    print("\n[write] _lib/truth_source.json")
