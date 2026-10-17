"""把 fig3 图注改为脚本生成, 所有数字从主网格实时计算 (2026-10-17).

【为什么】
2026-10-17 发现 fig3 图注写 "239 rows excluded"(实际 213)——
因为 caption 是手工维护的, 与数据脱节。
本脚本把 fig3 图注的生成逻辑嵌入 make_fig3.py, 数字全部实时算。

【做法】
在 make_fig3.py 末尾追加 write_caption 调用, 内容由下面的 compute() 生成。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "A37_六主图_v4"
ROOT = HERE.parent
A13 = ROOT / "A13_可靠性机制"

sys.path.insert(0, str(HERE))
import numpy as np                                              # noqa: E402
import pandas as pd                                             # noqa: E402


def compute() -> dict:
    d = pd.read_csv(A13 / "supply_state_regimes.csv")
    rel = d[(d.status == "converged_unique") &
            (~d.coc_floor_degenerate.astype(bool))].copy()
    q = (rel.M0_ml - rel.M1_ml) / rel.M1_ml
    dS = rel.dS_pot_ml
    return {
        "n_all": len(d),
        "n_rel": len(rel),
        "n_excl": len(d) - len(rel),
        "neg": int((dS < 0).sum()),
        "pos": int((dS > 0).sum()),
        "zero": int((dS == 0).sum()),
        "q_pos": int((q > 1e-9).sum()),
        "q_zero": int((q.abs() <= 1e-9).sum()),
        "q_neg": int((q < -1e-9).sum()),
        "q_pos_harm": int(((q > 1e-9) & (dS > 0)).sum()),
        "min_dS": float(dS.min()),
        "max_dS": float(dS.max()),
    }


CAPTION_BLOCK = '''

# ---------------------------------------------------------------
# 图注自动生成 (2026-10-17): 防止手工维护导致数字脱节
# ---------------------------------------------------------------
from caption_util import write_caption as _wc

_c = compute()
write_caption(
    3,
    title="City-level outcomes and the sign structure of $dS_{\\\\rm pot}$",
    sections={
        "Summary": (
            f"Across the {_c['n_rel']} solver-reliable grid scenarios, the strict-sign partition "
            f"of the primary estimand is **{_c['neg']} negative (beneficial) / {_c['pos']} positive "
            f"(harmful) / {_c['zero']} exactly zero** (panel **b**). Panel **c** partitions the same "
            f"scenarios by $q=(M_0-M_1)/M_1$ into **{_c['q_pos']} ($q>0$) / {_c['q_zero']} ($q=0$) / "
            f"{_c['q_neg']} ($q<0$)**; within $q>0$ the number of harmful outcomes is "
            f"**{_c['q_pos_harm']} of {_c['q_pos']}**."
        ),
        "Data and methods": (
            "All panels use `A13_可靠性机制/supply_state_regimes.csv`, the authoritative main grid. "
            "$q$ is computed as (M0_ml - M1_ml)/M1_ml; the file does not carry a $q$ column. "
            "Column names `x_ai_B1_ml` / `x_ai_B2_ml` are swapped relative to their meaning and "
            "must be read per `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md`."
        ),
        "n": (
            f"$n_{{\\\\rm eff}}$ = **{_c['n_rel']}** of {_c['n_all']} grid rows after the dual gate "
            f"(`status == converged_unique` AND NOT `coc_floor_degenerate`); "
            f"**{_c['n_excl']} rows are excluded** ({_c['n_all']} - {_c['n_rel']}). "
            "Zero convention: strict sign, $dS_{\\\\rm pot}==0.0$ counted separately."
        ),
        "Limits": (
            "The $q>0$ sufficiency check has no positive counterexample because $q>0$ is "
            "algebraically tied to the same identity; it is an accounting consistency check, "
            "not an independent predictive test."
        ),
    },
)
'''

p = HERE / "make_fig3.py"
t = p.read_text(encoding="utf-8")
if "图注自动生成" in t:
    print("已存在, 跳过")
else:
    # 需要 compute() 定义
    helper = '''
def compute():
    """从主网格实时计算图注所需的全部统计量。"""
    _d = pd.read_csv(Path(__file__).resolve().parent.parent / "A13_可靠性机制"
                     / "supply_state_regimes.csv")
    _rel = _d[(_d.status == "converged_unique") &
              (~_d.coc_floor_degenerate.astype(bool))].copy()
    _q = (_rel.M0_ml - _rel.M1_ml) / _rel.M1_ml
    _ds = _rel.dS_pot_ml
    return {
        "n_all": len(_d), "n_rel": len(_rel), "n_excl": len(_d) - len(_rel),
        "neg": int((_ds < 0).sum()), "pos": int((_ds > 0).sum()),
        "zero": int((_ds == 0).sum()),
        "q_pos": int((_q > 1e-9).sum()), "q_zero": int((_q.abs() <= 1e-9).sum()),
        "q_neg": int((_q < -1e-9).sum()),
        "q_pos_harm": int(((_q > 1e-9) & (_ds > 0)).sum()),
        "min_dS": float(_ds.min()), "max_dS": float(_ds.max()),
    }

'''
    t = t.replace('\nF.provenance(', helper + '\nF.provenance(', 1)
    t = t.rstrip() + "\n" + CAPTION_BLOCK
    p.write_text(t, encoding="utf-8")
    print("已注入 compute() 与 write_caption")
