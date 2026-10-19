# -*- coding: utf-8 -*-
"""核查 r* 的四个参数各自的锚定状态与来源可追溯性。

【为什么必须做】
论文把 `CoC_design` 的"无锚点"（`parameter_envelope_R7.csv` 中标 `—`）作为分类学边界
最弱一环登记在案，并据此给出 `r*` 的 ±10% 参数不确定性。

但 `r* = (L/CoC_d − C_p)/(C_r − C_p)` 依赖**四个**参数：
  L       循环水 TDS 限值              2200 mg/L
  CoC_d   设计浓缩倍数                 5.0
  C_p     自来水 TDS                   180 mg/L
  C_r     再生水 TDS                   650 mg/L

本节核查这四个参数是否都出现在参数包络表里。若 L / C_p / C_r 不在表中，
则"r* 只有 CoC_d 一个弱点"的表述会低估不确定性来源——这是一处需要如实登记的证据缺口。

产物：_rstar_param_anchoring.json + 控制台表
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
PROJ_HA = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "examples" / "cawcc_r2" / "ha" / "project.json"
OUT = HERE / "_rstar_param_anchoring.json"


def main() -> None:
    env = pd.read_csv(R2 / "parameter_envelope_R7.csv", encoding="utf-8-sig")
    paths = set(env["参数路径"].astype(str))

    proj = json.loads(PROJ_HA.read_text(encoding="utf-8"))
    dc = next(v for v in proj["components"].values() if v.get("kind") == "data_center")
    cooling = dc["cooling"]
    L = float(cooling["water_quality_limits"]["TDS"])
    coc_d = float(cooling["cycles_of_concentration"])
    c_p = float(dc["water_sources"]["potable"]["quality"]["TDS"])
    c_r = float(dc["water_sources"]["reclaimed"]["quality"]["TDS"])

    params = [
        ("L", "循环水 TDS 限值", L, "components.AI_DC1.cooling.water_quality_limits.TDS"),
        ("CoC_d", "设计浓缩倍数", coc_d, "components.AI_DC1.cooling.cycles_of_concentration"),
        ("C_p", "自来水 TDS", c_p, "components.AI_DC1.water_sources.potable.quality.TDS"),
        ("C_r", "再生水 TDS", c_r, "components.AI_DC1.water_sources.reclaimed.quality.TDS"),
    ]

    print(f"{'符号':<7}{'含义':<20}{'取值':>9}  {'在包络表中':<10}{'锚定状态'}")
    print("-" * 78)
    rows = []
    for sym, name, val, path in params:
        in_table = path in paths
        if in_table:
            row = env[env["参数路径"].astype(str) == path].iloc[0]
            status = str(row["是否落在包络内"])
            anchor = str(row["锚点编号"])
        else:
            status = "未列入包络表"
            anchor = "—"
        print(f"{sym:<7}{name:<20}{val:>9.1f}  {str(in_table):<10}{status}  (锚点 {anchor})")
        rows.append({"symbol": sym, "name": name, "value": val, "path": path,
                     "in_envelope_table": in_table, "anchor_status": status,
                     "anchor_id": anchor})

    n_in = sum(1 for r in rows if r["in_envelope_table"])
    n_anchored = sum(1 for r in rows if r["anchor_status"] in ("是", "边界命中"))
    print("-" * 78)
    print(f"在包络表中: {n_in}/4    有实际锚点: {n_anchored}/4")

    # r* 与四参数弹性
    r_star = (L / coc_d - c_p) / (c_r - c_p)
    print(f"\nr* = ({L}/{coc_d} − {c_p})/({c_r} − {c_p}) = {r_star:.4f}")
    print("\n±10% 单参数扰动对 r* 的影响：")
    for sym, name, val, _ in params:
        kv = {"L": L, "CoC_d": coc_d, "C_p": c_p, "C_r": c_r}
        out = {}
        for sign, tag in ((1.1, "+10%"), (0.9, "-10%")):
            k2 = dict(kv)
            k2[sym] = kv[sym] * sign
            out[tag] = (k2["L"] / k2["CoC_d"] - k2["C_p"]) / (k2["C_r"] - k2["C_p"])
        print(f"  {sym:<7} {name:<18} r* -> {out['-10%']:.4f} ~ {out['+10%']:.4f} "
              f"(跨度 {out['+10%']-out['-10%']:+.4f})")

    OUT.write_text(json.dumps({
        "r_star": round(r_star, 4),
        "parameters": rows,
        "n_in_envelope_table": n_in,
        "n_actually_anchored": n_anchored,
        "note": ("r* 的四个参数中只有 CoC_d 被列入 parameter_envelope_R7.csv 且标记为无锚点；"
                 "L、C_p、C_r 三个水质参数根本不在该表 54 行之内，从未经过锚定核查。"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
