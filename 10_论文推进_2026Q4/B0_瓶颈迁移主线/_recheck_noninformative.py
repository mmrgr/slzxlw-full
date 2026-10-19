# -*- coding: utf-8 -*-
"""核对扩展扫描结果与原结论的差异，并解释 reclaimed_water_substitution_ratio 首失效为 0 的异常。

【扩展扫描结果（0–4000 MW）】
HA 端原本标"非 informative"的 6 条：扩到 4000 后**只有 max_wwtw_utilization 仍不失效**，
其余 5 条首失效为：
  system_reliability_fraction 2050（注：本次打印 2550，需复核两份输出差异）
  unmet_cooling_water_ml      2300（打印 3000）
  domestic_unmet_ml           1850（与论文一致）
  peak_capacity_ratio         1750（与论文一致）
  reclaimed_water_substitution_ratio **0**  ← 异常

【异常 1：reclaimed 首失效 = 0 MW】
r=0 时无 AI，园区再生水替代率 = 0，而约束要求 ≥0.40，故 0 MW 必然"违约"。
这是**定义域边界伪影**，不是真实失效。论文 §3.6 已记录过同类问题
（"0 MW 必须排除：没有数据中心时替代率无定义"）。

【异常 2：打印的两组首失效值不一致】
上面判定段落打印 2050 / 2300，而表格打印 2550 / 3000。
原因是判定段落读的是 json，而 json 在表格循环中被覆盖写入？
需核实。

本脚本：排除 0 MW 点、重新统计，并核对两份输出。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
J = HERE / "_noninformative_extended.json"


def first_fail(scan: pd.DataFrame, col: str, op: str, tgt: float,
               exclude_zero: bool = True) -> float | None:
    sub = scan[scan["ai_capacity_mw"] > 0] if exclude_zero else scan
    for _, x in sub.iterrows():
        v = float(pd.to_numeric(x[col], errors="coerce"))
        if v != v:
            continue
        bad = (v > tgt) if op in ("<=", "<") else (v < tgt)
        if bad:
            return float(x["ai_capacity_mw"])
    return None


def main() -> None:
    print("=== 复核 json 内容 ===")
    d = json.loads(J.read_text(encoding="utf-8"))
    for base in ("ha", "co"):
        print(f"\n  {base.upper()}:")
        for k, v in d[base].items():
            print(f"    {k:<40} first_fail={v['first_fail_mw']}  max={v['max_value']}")

    print("\n=== 从 capacity_scan_4000mw.csv 重算（排除 0 MW）===")
    cons_all = {}
    for base in ("ha", "co"):
        f = R2 / base / "capacity_scan_4000mw.csv"
        if not f.exists():
            print(f"缺失 {f}")
            continue
        scan = pd.read_csv(f, encoding="utf-8-sig")
        cons = json.loads((R2 / "specs" / f"constraints_{base}.json").read_text(encoding="utf-8"))
        print(f"\n  --- {base.upper()}（{len(scan)} 行）---")
        print(f"  {'约束':<40}{'阈值':>8}{'首失效(>0MW)':>14}{'首失效(含0)':>13}")
        cons_all[base] = {}
        for name, spec in cons["constraints"].items():
            col = name if name in scan.columns else None
            if col is None:
                print(f"  {name:<40}{'列缺失':>8}")
                continue
            op, tgt = spec["operator"], float(spec["value"])
            f1 = first_fail(scan, col, op, tgt, exclude_zero=True)
            f2 = first_fail(scan, col, op, tgt, exclude_zero=False)
            cons_all[base][name] = {"first_fail_excl0": f1, "first_fail_incl0": f2}
            s1 = f"{f1:.0f}" if f1 is not None else "未失效"
            s2 = f"{f2:.0f}" if f2 is not None else "未失效"
            mark = "  ← 0MW 伪影" if f2 == 0 and f1 != 0 else ""
            print(f"  {name:<40}{tgt:>8.3g}{s1:>14}{s2:>13}{mark}")

    print("\n=== 结论：扩到 4000 MW 后真正从不失效的约束 ===")
    for base in ("ha", "co"):
        never = [k for k, v in cons_all[base].items() if v["first_fail_excl0"] is None]
        print(f"  {base.upper()}: {len(never)} 条 → {never}")

    (HERE / "_noninformative_recheck.json").write_text(
        json.dumps(cons_all, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：_noninformative_recheck.json")


if __name__ == "__main__":
    main()
