# -*- coding: utf-8 -*-
"""给交互扫描脚本增加双口径输出（联合 / 纯物理），避免与论文 §5.4 的联合口径表混淆。

【为什么必须改】
论文 §5.4 干预表用**联合口径**（含政策约束），HA `leakage_minus_30pct` = +150 MW（1150→1300）。
本脚本初版只用**纯物理口径**，得 +250 MW（1150→1400）。
两者都对，但口径不同；若只报一个，读者会以为论文数字有误。

纯物理下增益更大，是因为联合口径下政策约束 `reclaimed_water_substitution_ratio ≥ 0.65`
会在 1400 之前先失效——这本身是一个值得报告的发现：
**干预的真实效果取决于是否把政策约束留在判据集内。**
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src" / "scripts" / "run_interaction_pairs_50mw.py"

t = P.read_text(encoding="utf-8")

# 1) cawcc 函数改为同时返回两口径
t = t.replace(
    """        def cawcc(sets: list[list[dict]]) -> tuple[float, str]:
            trial = copy.deepcopy(project0)
            for s in sets:
                apply_set(trial, s)
            scan = scan_with_mean(trial, ts, CAP)
            got = find_ai_carrying_capacity(
                scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True), phys)
            return float(got["maximum_safe_ai_capacity_mw"]), str(got["limiting_constraint"])""",
    """        def cawcc(sets: list[list[dict]]) -> tuple[float, str, float, str]:
            \"\"\"返回 (联合 CAWCC, 联合限制, 纯物理 CAWCC, 纯物理限制)。\"\"\"
            trial = copy.deepcopy(project0)
            for s in sets:
                apply_set(trial, s)
            scan = scan_with_mean(trial, ts, CAP)
            pos = scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True)
            gj = find_ai_carrying_capacity(pos, day)
            gp = find_ai_carrying_capacity(pos, phys)
            return (float(gj["maximum_safe_ai_capacity_mw"]), str(gj["limiting_constraint"]),
                    float(gp["maximum_safe_ai_capacity_mw"]), str(gp["limiting_constraint"]))""")

# 2) 基线
t = t.replace(
    """        base_cawcc, base_con = cawcc([])
        print(f"基线（50 MW 网格，纯物理口径）: {base_cawcc} MW  限制约束 {base_con}")""",
    """        base_j, base_con_j, base_p, base_con_p = cawcc([])
        print(f"基线（50 MW 网格）: 联合 {base_j} MW [{base_con_j}] / 纯物理 {base_p} MW [{base_con_p}]")""")

# 3) 单干预
t = t.replace(
    """        single: dict[str, float] = {}
        single_con: dict[str, str] = {}
        for name, s in items.items():
            c, con = cawcc([s])
            single[name] = c - base_cawcc
            single_con[name] = con
        print("\\n单干预增益：")
        for n, g in sorted(single.items(), key=lambda kv: -kv[1]):
            print(f"  {n:<32}{g:+7.0f} MW")""",
    """        single: dict[str, float] = {}
        single_p: dict[str, float] = {}
        single_con: dict[str, str] = {}
        single_con_p: dict[str, str] = {}
        for name, s in items.items():
            cj, cj_con, cp, cp_con = cawcc([s])
            single[name] = cj - base_j
            single_p[name] = cp - base_p
            single_con[name] = cj_con
            single_con_p[name] = cp_con
        print("\\n单干预增益（联合 / 纯物理）：")
        for n in sorted(single, key=lambda k: -(single[k] + single_p[k])):
            print(f"  {n:<32}{single[n]:+7.0f} / {single_p[n]:+7.0f} MW")""")

# 4) 交互对
t = t.replace(
    """        for a, b in itertools.combinations(names, 2):
            c, con = cawcc([items[a], items[b]])
            g_ab = c - base_cawcc
            g_sum = single[a] + single[b]
            inter = g_ab - g_sum
            if single[a] == 0 and single[b] == 0 and g_ab != 0:
                kind = "pure"
            elif abs(inter) < 1e-9:
                kind = "additive"
            elif inter < 0:
                kind = "sub-additive"
            else:
                kind = "super-additive"
            rows.append({
                "base": base, "a": a, "b": b,
                "gain_a_mw": single[a], "gain_b_mw": single[b],
                "gain_ab_mw": g_ab, "gain_sum_mw": g_sum,
                "interaction_mw": inter, "kind": kind,
                "limiting_constraint_ab": con,
            })""",
    """        for a, b in itertools.combinations(names, 2):
            cj, cj_con, cp, cp_con = cawcc([items[a], items[b]])
            for tag, g_ab, base_c, sg, con in (
                    ("joint", cj - base_j, base_j, single, cj_con),
                    ("physical", cp - base_p, base_p, single_p, cp_con)):
                g_sum = sg[a] + sg[b]
                inter = g_ab - g_sum
                if sg[a] == 0 and sg[b] == 0 and g_ab != 0:
                    kind = "pure"
                elif abs(inter) < 1e-6:
                    kind = "additive"
                elif inter < 0:
                    kind = "sub-additive"
                else:
                    kind = "super-additive"
                rows.append({
                    "base": base, "caliber": tag, "a": a, "b": b,
                    "gain_a_mw": sg[a], "gain_b_mw": sg[b],
                    "gain_ab_mw": g_ab, "gain_sum_mw": g_sum,
                    "interaction_mw": inter, "kind": kind,
                    "limiting_constraint_ab": con,
                })""")

# 5) 汇总按口径分组
t = t.replace(
    """        kinds = df["kind"].value_counts().to_dict()
        print(f"\\n两两交互（{len(df)} 对）：")
        for k, v in kinds.items():
            print(f"  {k:<16}{v} 对")
        nz = df[df["interaction_mw"].abs() > 1e-9]""",
    """        print(f"\\n两两交互（共 {len(df)} 行 = 36 对 × 2 口径）：")
        for cal in ("joint", "physical"):
            sub = df[df["caliber"] == cal]
            kinds = sub["kind"].value_counts().to_dict()
            print(f"  [{cal}] " + "  ".join(f"{k}={v}" for k, v in kinds.items()))
        nz = df[df["interaction_mw"].abs() > 1e-6]""")

t = t.replace(
    """                print(f"    {r['a']:<28} + {r['b']:<28} 交互 {r['interaction_mw']:+6.0f} MW  [{r['kind']}]")""",
    """                print(f"    [{r['caliber']:<8}] {r['a']:<26} + {r['b']:<26} "
                      f"交互 {r['interaction_mw']:+6.0f} MW  [{r['kind']}]")""")

t = t.replace(
    """            "baseline_cawcc_mw": base_cawcc,
            "baseline_limiting": base_con,
            "single_gains": single,
            "single_limiting": single_con,""",
    """            "baseline_joint_mw": base_j,
            "baseline_joint_limiting": base_con_j,
            "baseline_physical_mw": base_p,
            "baseline_physical_limiting": base_con_p,
            "single_gains_joint": single,
            "single_gains_physical": single_p,
            "single_limiting_joint": single_con,
            "single_limiting_physical": single_con_p,""")

P.write_text(t, encoding="utf-8")
print("OK 已改为双口径输出")
