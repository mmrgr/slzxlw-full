# -*- coding: utf-8 -*-
"""小规模验证：水质约束能否成为承载瓶颈？

【背景】
Saleh 2026 (ES&T Viewpoint) 指出"水量口径已不足，前沿是水质兼容性"。
AI-UWM 拥有五物种追踪 + CoC + 限值，但水质只作冷却塔内部参数，不进承载判据。
本脚本验证：若把水质升级为第 11 条承载约束，它会在哪个容量点首失效？
是否可能成为"水质先卡"这一新瓶颈类型？

【关键预判（须验证，不可假定）】
现有 capacity_scan 显示再生水替代率随容量**单调下降**（HA: 1150MW 时 0.6976 → 2000MW 时 0.4370）。
若如此，容量越大再生水掺混越少 → 补水水质越好 → CoC 越高 → 水质约束反而**变松**。
那么水质约束不会成为首失效约束，候选 1 不成立。

本脚本只跑 5-7 个容量点做判定，不重跑全网格。

【用法】
    PYTHONPATH="src;scripts" python scripts/probe_water_quality_constraint.py
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

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.ai_metrics import summarize_ai_water_kpis  # noqa: E402
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

# 取关键容量点：基线、首失效前后、上限
CAPACITIES = [50.0, 500.0, 1100.0, 1150.0, 1200.0, 1300.0, 1500.0, 2000.0]

# GB/T 50050-2017 循环水限值（与 city_model LIMIT_SET 一致）
LIMITS = {"TDS": 2200.0, "chloride": 500.0}


def run_point(project: dict, timeseries: pd.DataFrame, capacity: float) -> dict:
    cfg = json.loads(json.dumps(project))
    for comp in cfg["components"].values():
        if comp.get("kind") == "data_center":
            comp["installed_it_capacity_mw"] = float(capacity)
            comp.pop("capacity_schedule", None)
    result = FullAIUWMModel(cfg, timeseries).run()
    daily = result.data_center_daily
    kpi = summarize_ai_water_kpis(result, cfg)

    rec = {
        "capacity_mw": capacity,
        "reclaimed_substitution_ratio": kpi.get("reclaimed_water_substitution_ratio"),
        "reclaimed_use_ml": kpi.get("reclaimed_water_use_ml"),
        "freshwater_withdrawal_ml": kpi.get("freshwater_withdrawal_ml"),
        "unmet_cooling_ml": kpi.get("unmet_cooling_water_ml"),
    }

    # 从 data_center_daily 里找 CoC 与水质列
    for col in daily.columns:
        low = col.lower()
        if "cycles_of_concentration" in low:
            rec["coc_mean"] = float(pd.to_numeric(daily[col], errors="coerce").mean())
            rec["coc_min"] = float(pd.to_numeric(daily[col], errors="coerce").min())
        if "quality_coc_fallback" in low:
            rec["coc_fallback_days"] = int(
                pd.to_numeric(daily[col], errors="coerce").fillna(0).sum()
            )
        for species in ("tds", "chloride"):
            if species in low and ("loop" in low or "concentration" in low or "quality" in low):
                rec[f"{col}_max"] = float(
                    pd.to_numeric(daily[col], errors="coerce").max()
                )
    rec["daily_columns"] = "|".join(
        c for c in daily.columns
        if any(k in c.lower() for k in ("coc", "quality", "tds", "chlor", "concen"))
    )
    return rec


def main() -> None:
    rows = []
    for domain in ("ha", "co"):
        project = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
        timeseries = pd.read_csv(R2 / domain / "timeseries.csv")
        print(f"\n=== {domain.upper()} ===", flush=True)
        for cap in CAPACITIES:
            rec = run_point(project, timeseries, cap)
            rec["domain"] = domain
            rows.append(rec)
            print(
                f"  {cap:6.0f} MW  recl={rec['reclaimed_substitution_ratio']:.4f}  "
                f"CoC_mean={rec.get('coc_mean', float('nan')):.3f}  "
                f"CoC_min={rec.get('coc_min', float('nan')):.3f}",
                flush=True,
            )

    frame = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT / "probe_water_quality_constraint.csv", index=False, encoding="utf-8-sig")

    # ---- 判定 ----
    print("\n" + "=" * 74)
    print("判定：水质约束是否可能成为首失效约束？")
    print("=" * 74)
    print(f"限值: TDS <= {LIMITS['TDS']}, chloride <= {LIMITS['chloride']}")
    print("\n可用水质列:", frame["daily_columns"].iloc[0] or "（无）")

    for domain in ("ha", "co"):
        sub = frame[frame["domain"] == domain].sort_values("capacity_mw")
        print(f"\n{domain.upper()}:")
        coc = sub["coc_mean"].to_numpy()
        if len(coc) >= 2:
            trend = "下降" if coc[-1] < coc[0] else ("上升" if coc[-1] > coc[0] else "不变")
            print(f"  CoC 从 {coc[0]:.3f}（{sub['capacity_mw'].iloc[0]:.0f}MW）"
                  f" 到 {coc[-1]:.3f}（{sub['capacity_mw'].iloc[-1]:.0f}MW）→ {trend}")
        # 若 CoC 低于设计值，说明水质在起作用
        design = 5.0
        below = sub[sub["coc_mean"] < design - 1e-6]
        if len(below):
            print(f"  [!] CoC 低于设计值 {design} 的容量点: "
                  f"{below['capacity_mw'].tolist()}（水质已在起作用）")
        else:
            print(f"  [OK] CoC 全程等于设计值 {design}（水质未约束）")

    frame.to_csv(OUT / "probe_water_quality_constraint.csv", index=False, encoding="utf-8-sig")
    print(f"\n-> {OUT / 'probe_water_quality_constraint.csv'}")


if __name__ == "__main__":
    main()
