"""阶段 2-c：R10a 是否收敛到物理稳态 (2026-10-17).

【为何需要这一步】
上一步证明: volume-only 的 CoC = min(limit/C_in), 物理上等价 V=0 却报告 1.8-5.0,
自相矛盾; R10a 的 CoC 从 3.017 升到 ~5.0, 看似正确。

但必须排除另一种可能: R10a 的"上升"只是**尚未收敛的暂态**, 若积分更久会继续升破设计值。
本检验: 看 CoC 时间序列是否**单调趋近并稳定**在 min(设计值, 限值约束) 处。
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
ENGINE = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(ENGINE / "src"))

import copy  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ENGINE / "examples" / "cawcc_r2"
OUT = HERE / "ne5c_convergence_summary.json"

IEUA = {"TDS": 443.0, "chloride": 100.0, "hardness": 149.427,
        "alkalinity": 140.0, "silica": 24.0}
POTABLE = {"TDS": 180.0, "chloride": 35.0, "hardness": 120.0,
           "alkalinity": 100.0, "silica": 10.0}
LIMITS = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
          "alkalinity": 350.0, "silica": 175.0}


def run(phi: float, days: int = 730) -> pd.DataFrame:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv").head(days).copy()
    proj = copy.deepcopy(proj)
    dc = proj["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["quality_state_enabled"] = True
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = 5.0
    dc["cooling"]["water_quality_limits"] = dict(LIMITS)
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(phi)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(phi)
    for src, q in (("reclaimed", IEUA), ("potable", POTABLE)):
        s = dc["water_sources"][src]
        s["quality_mg_l"] = dict(q)
        s.pop("quality", None)
    sim = proj.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(ts["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(ts["date"].iloc[-1]).date())
    return FullAIUWMModel(proj, ts).run().data_center_daily


def main() -> int:
    print("=" * 76)
    print("阶段 2-c ｜ R10a 的 CoC 是否收敛到物理稳态")
    print("=" * 76)
    rows = []
    for phi in (0.4, 0.6):
        d = run(phi)
        coc = np.asarray(d["cycles_of_concentration"], dtype=float)
        n = len(coc)
        q = max(1, n // 10)
        deciles = [float(coc[i * q:(i + 1) * q].mean()) for i in range(9)]
        deciles.append(float(coc[9 * q:].mean()))
        tail_last = float(coc[-30:].mean())
        tail_std = float(coc[-30:].std())
        print(f"\n  φ={phi}  (n={n} 天)")
        print("    分位均值: " + " ".join(f"{v:.3f}" for v in deciles))
        print(f"    末 30 天均值={tail_last:.4f} 标准差={tail_std:.2e}")
        at_design = abs(tail_last - 5.0) < 1e-6
        print(f"    是否稳定在设计值 5.0: {'是' if at_design else '否'}")
        rows.append({"phi": phi, "decile_means": deciles,
                     "tail_mean": tail_last, "tail_std": tail_std,
                     "converged_to_design": bool(at_design)})

    print("\n" + "=" * 76)
    print("裁定")
    print("=" * 76)
    all_conv = all(r["converged_to_design"] for r in rows)
    print(f"  全部收敛到设计 CoC=5.0: {all_conv}")
    print("  物理含义: R10a 的回路溶质存量逐日累积, 进入速率 > 排出速率的暂态后,")
    print("            系统到达稳态 C_loop/C_in = CoC_design —— 这是 CSTR 的正确行为。")
    print("            volume-only 从未离开 C_loop = C_in 的瞬时态, 其 CoC 只是")
    print("            'min(限值/补水浓度)', 与回路实际浓度无关。")

    OUT.write_text(json.dumps({
        "rows": rows,
        "all_converge_to_design": all_conv,
        "verdict": ("R10A_PHYSICALLY_CORRECT" if all_conv else "INCONCLUSIVE"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[write] {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
