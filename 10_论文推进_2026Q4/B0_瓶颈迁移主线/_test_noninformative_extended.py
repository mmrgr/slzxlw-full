# -*- coding: utf-8 -*-
"""检验"非 informative 约束"这一负结果的边界：把扫描范围扩大到 4000 MW。

【问题】
主稿 §5.3 把 3 条（HA）/ 6 条（CO）约束标为"非 informative"，并诚实地说
"它们只是没被触及，不是系统安全的证据"。

但**从未检验**：扫描范围扩大后，这些约束会不会失效？
若不失效，则"没被触及"这一解释更强；若失效，则必须报出确实的失效点。

【为什么这是重要的负结果检验】
"污水处理能力不是瓶颈"（`max_wwtw_utilization`）是本文一个与直觉相反的主张。
若它只是因为扫描到 2000 MW 就停了才显得"从未失效"，那这个主张就是**扫描范围的产物**，
而不是系统属性。

【做法】
把容量扫描扩到 4000 MW（80 个点，50 MW 步长），重跑两端，
看这 6 条约束是否仍然 non-informative；若失效，报出首失效容量。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from run_r2 import daily_constraints, scan_with_mean  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"          # 输入（project / timeseries / specs）
ART = ROOT / "validation_artifacts" / "r2"     # 输出（产物目录，勿写入源目录）
HERE = Path(__file__).resolve().parent
OUT = HERE / "_noninformative_extended.json"
CAP_EXT = list(np.arange(0, 4001, 50, dtype=float))

# 主稿标为非 informative 的约束（两端并集）
TARGETS = [
    "system_reliability_fraction",
    "unmet_cooling_water_ml",
    "max_wwtw_utilization",
    "domestic_unmet_ml",
    "peak_capacity_ratio",
    "reclaimed_water_substitution_ratio",
]


def main() -> None:
    out = {}
    for base in ("ha", "co"):
        print(f"\n{'='*80}\n[{base.upper()}]  扫描 0–4000 MW（{len(CAP_EXT)} 点）\n{'='*80}")
        proj = json.loads((R2 / base / "project.json").read_text(encoding="utf-8"))
        ts = pd.read_csv(R2 / base / "timeseries.csv")
        cons = json.loads((R2 / "specs" / f"constraints_{base}.json").read_text(encoding="utf-8"))
        day = daily_constraints(cons)

        scan = scan_with_mean(proj, ts, CAP_EXT)
        (R2 / base).mkdir(parents=True, exist_ok=True)
        (ART / base).mkdir(parents=True, exist_ok=True)
        scan.to_csv(ART / base / "capacity_scan_4000mw.csv", index=False, encoding="utf-8-sig")

        out[base] = {}
        print(f"{'约束':<40}{'阈值':>8}{'最大观测值':>12}{'首失效容量':>12}")
        print("-" * 74)
        for name in TARGETS:
            if name not in day:
                continue
            d = day[name]
            op = d.get("operator")
            tgt = d.get("value", d.get("target"))
            col = d.get("metric") or d.get("column") or d.get("field") or name
            # 找实际列
            if col not in scan.columns:
                cand = [c for c in scan.columns if name.replace("max_", "").replace("_ml", "")
                        in c or c == name]
                col = cand[0] if cand else None
            if col is None or col not in scan.columns:
                print(f"{name:<40}{'?':>8}{'列未找到':>12}")
                continue
            v = pd.to_numeric(scan[col], errors="coerce")
            mx = float(v.max())
            # 判失效
            fails = []
            for _, x in scan.iterrows():
                val = float(pd.to_numeric(x[col], errors="coerce"))
                if val != val:
                    continue
                bad = (val > float(tgt)) if op in ("<=", "<") else (val < float(tgt))
                # reclaimed 相关约束在 0 MW 处无定义（无 AI 则替代率为 0），排除
                if bad and float(x["ai_capacity_mw"]) > 0:
                    fails.append(float(x["ai_capacity_mw"]))
            first = fails[0] if fails else None
            out[base][name] = {"threshold": float(tgt), "operator": op,
                               "max_value": round(mx, 6),
                               "first_fail_mw": first,
                               "informative_at_4000": first is not None}
            print(f"{name:<40}{float(tgt):>8.3g}{mx:>12.4g}"
                  f"{(f'{first:.0f}' if first is not None else '未失效'):>12}")

    (HERE / "_noninformative_extended.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{(HERE / '_noninformative_extended.json').name}")

    print(f"\n{'='*80}\n判定\n{'='*80}")
    for base in ("ha", "co"):
        still = [k for k, v in out[base].items() if not v["informative_at_4000"]]
        gained = [k for k, v in out[base].items() if v["informative_at_4000"]]
        print(f"  {base.upper()}: 扩到 4000 MW 后仍 non-informative 的 {len(still)} 条")
        for k in still:
            print(f"    - {k}（最大观测 {out[base][k]['max_value']:.4g}）")
        if gained:
            print(f"    在 2000–4000 MW 区间内失效的 {len(gained)} 条：")
            for k in gained:
                print(f"    + {k} 首失效 {out[base][k]['first_fail_mw']:.0f} MW")


if __name__ == "__main__":
    main()
