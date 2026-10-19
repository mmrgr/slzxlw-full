# -*- coding: utf-8 -*-
"""补齐论文自述的结构性缺口：9 项干预的**两两交互**。

【为什么做】
主稿 §5.6、§9.2 第 6 条均登记："9 项干预为一对一施加，**未做全因子或两两交互**"。
这是论文唯一一处"自己列出来但没做"的可做缺口（其余缺口或缺数据、或需实测率定）。

【设计】
- 干预规格已存在于 `specs/interventions_{ha,co}.json`，每项是一组 path→value 覆盖；
- 两两交互 = 把两个 set 合并后同时应用（后者覆盖前者，若路径冲突则记录冲突）；
- 在 50 MW 网格（与主结果同网格）上重算 CAWCC 与首失效约束；
- 判据：
    * 若 g(A+B) ≈ g(A) + g(B)  → 可加，无交互
    * 若 g(A+B) < 两者之和      → 次可加（竞争同一约束，边际递减）
    * 若 g(A+B) > 两者之和      → 超可加（互补）
    * 若 g(A)=0 且 g(B)=0 而 g(A+B)>0 → 纯交互（单独无效、组合有效）

【产物】
  {ha,co}/interaction_pairs_50mw.csv
  interaction_pairs_50mw_summary.json
"""
from __future__ import annotations

import copy
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.ai_capacity import find_ai_carrying_capacity  # noqa: E402
from run_r2 import daily_constraints, scan_with_mean  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"
CAP = list(np.arange(0, 2001, 50, dtype=float))


def apply_set(project: dict, entries: list[dict]) -> list[str]:
    """按 path 把 value 写入项目；返回被覆盖的路径列表。"""
    touched = []
    for e in entries:
        parts = e["path"].split(".")
        node = project
        for p in parts[:-1]:
            node = node[p]
        node[parts[-1]] = e["value"]
        touched.append(e["path"])
    return touched


def main() -> None:
    summary: dict = {"grid_mw": 50.0, "bases": {}}

    for base in ([b.strip() for b in sys.argv[1].split(",")] if len(sys.argv)>1 else ["ha", "co"]):
        print(f"\n{'='*76}\n[{base.upper()}]\n{'='*76}")
        project0 = json.loads((R2 / base / "project.json").read_text(encoding="utf-8"))
        ts = pd.read_csv((R2 / base / "timeseries.csv"))
        spec = json.loads((R2 / "specs" / f"interventions_{base}.json").read_text(encoding="utf-8"))
        cons_json = json.loads((R2 / "specs" / f"constraints_{base}.json").read_text(encoding="utf-8"))
        day = {"constraints": daily_constraints(cons_json)}
        phys = {"constraints": {k: v for k, v in day["constraints"].items()
                                if k != "reclaimed_water_substitution_ratio"}}

        items = {it["name"]: it["set"] for it in spec["interventions"] if it["name"] != "baseline"}

        def cawcc(sets: list[list[dict]]) -> tuple[float, str, float, str]:
            """返回 (联合 CAWCC, 联合限制, 纯物理 CAWCC, 纯物理限制)。"""
            trial = copy.deepcopy(project0)
            for s in sets:
                apply_set(trial, s)
            scan = scan_with_mean(trial, ts, CAP)
            pos = scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True)
            gj = find_ai_carrying_capacity(pos, day)
            gp = find_ai_carrying_capacity(pos, phys)
            return (float(gj["maximum_safe_ai_capacity_mw"]), str(gj["limiting_constraint"]),
                    float(gp["maximum_safe_ai_capacity_mw"]), str(gp["limiting_constraint"]))

        base_j, base_con_j, base_p, base_con_p = cawcc([])
        print(f"基线（50 MW 网格）: 联合 {base_j} MW [{base_con_j}] / 纯物理 {base_p} MW [{base_con_p}]")

        # 单干预增益
        single: dict[str, float] = {}
        single_p: dict[str, float] = {}
        single_con: dict[str, str] = {}
        single_con_p: dict[str, str] = {}
        for name, s in items.items():
            cj, cj_con, cp, cp_con = cawcc([s])
            single[name] = cj - base_j
            single_p[name] = cp - base_p
            single_con[name] = cj_con
            single_con_p[name] = cp_con
        print("\n单干预增益（联合 / 纯物理）：")
        for n in sorted(single, key=lambda k: -(single[k] + single_p[k])):
            print(f"  {n:<32}{single[n]:+7.0f} / {single_p[n]:+7.0f} MW")

        # 两两交互
        rows = []
        names = list(items)
        for a, b in itertools.combinations(names, 2):
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
                })

        df = pd.DataFrame(rows)
        df.to_csv(OUT / base / "interaction_pairs_50mw.csv", index=False, encoding="utf-8-sig")

        # 汇总
        print(f"\n两两交互（共 {len(df)} 行 = 36 对 × 2 口径）：")
        for cal in ("joint", "physical"):
            sub = df[df["caliber"] == cal]
            kinds = sub["kind"].value_counts().to_dict()
            print(f"  [{cal}] " + "  ".join(f"{k}={v}" for k, v in kinds.items()))
        nz = df[df["interaction_mw"].abs() > 1e-6]
        print(f"  非可加对：{len(nz)} 对")
        if len(nz):
            print("\n  非可加对明细（|交互| ≥ 1 MW）：")
            for _, r in nz.reindex(nz["interaction_mw"].abs().sort_values(ascending=False).index).head(12).iterrows():
                print(f"    [{r['caliber']:<8}] {r['a']:<26} + {r['b']:<26} "
                      f"交互 {r['interaction_mw']:+6.0f} MW  [{r['kind']}]")

        summary["bases"][base] = {
            "baseline_joint_mw": base_j,
            "baseline_joint_limiting": base_con_j,
            "baseline_physical_mw": base_p,
            "baseline_physical_limiting": base_con_p,
            "single_gains_joint": single,
            "single_gains_physical": single_p,
            "single_limiting_joint": single_con,
            "single_limiting_physical": single_con_p,
            "pairs": df.to_dict("records"),
            "kind_counts": kinds,
            "n_nonadditive": int(len(nz)),
        }

    # 合并已有 summary，避免只跑单基底时覆盖另一基底结果
    out_path = OUT / "interaction_pairs_50mw_summary.json"
    if out_path.exists():
        try:
            prev = json.loads(out_path.read_text(encoding="utf-8"))
            merged = prev.get("bases", {})
            merged.update(summary["bases"])
            summary = {"grid_mw": summary["grid_mw"], "bases": merged}
        except Exception:
            pass
    out_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}/interaction_pairs_50mw_summary.json")


if __name__ == "__main__":
    main()
