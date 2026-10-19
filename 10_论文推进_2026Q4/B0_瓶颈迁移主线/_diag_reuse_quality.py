# -*- coding: utf-8 -*-
"""诊断 2：动态路径的再生水 TDS 为何从 650 变成约 50 mg/L？

【已确认（_dynamic_inflow_diag.txt）】
  day0  补水 TDS ≈ 1239（我的反解公式有偏，见下）provenance = scenario_prior
  day1+ 补水 TDS ≈ 52.7, 56.9, 49.6, 39.9 ...           provenance = treated_output
  储池 TDS: 603 → 25.7 → 33.8 mg/L
  排污 TDS: 1998 → 182.7 mg/L

【怀疑】
  full_engine._reuse_output_quality() 用 pollutant_storage 的 mass/volume
  覆盖了项目声明的 quality_mg_l（650）。若 WWTW 账本里的 TDS 质量很小，
  动态路径隐含"再生水 TDS ≈ 50 mg/L"，与主分析 C_r = 650 差一个量级。

【本脚本要回答】
1. CENTRAL_REUSE 的 pollutant_storage 逐日 TDS 质量与 volume → 直接算浓度
2. 该浓度是否 ≈ 50 mg/L
3. _reuse_output_quality 的实际返回值
4. 若这个浓度是 50 而非 650，则"上下界"解读错误，实为输入不一致
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm import full_engine  # noqa: E402
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
OUT = HERE / "_reuse_quality_ledger.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")

    # ---------- 1. CENTRAL_REUSE 组件完整定义 ----------
    w("=" * 78)
    w("A. CENTRAL_REUSE 组件定义（全部键）")
    w("=" * 78)
    for cid, comp in proj["components"].items():
        if comp.get("kind") == "reuse":
            w(f"  id = {cid}")
            w(f"  {json.dumps(comp, ensure_ascii=False, indent=2)}")

    # ---------- 2. 追踪 _reuse_output_quality 的返回 ----------
    seen: list[dict] = []
    orig = full_engine._reuse_output_quality

    def spy(model, reuse_id, reuse_component):
        v = orig(model, reuse_id, reuse_component)
        vol = max(0.0, float(model.storage.get(reuse_id, 0.0))) if reuse_id else 0.0
        masses = dict(model.pollutant_storage.get(reuse_id, {})) if reuse_id else {}
        seen.append({
            "reuse_id": reuse_id,
            "volume_ml": vol,
            "TDS_mass_kg": float(masses.get("TDS", 0.0)),
            "ret_TDS": float(v.get("TDS", 0.0)),
            "ret_chloride": float(v.get("chloride", 0.0)),
            "n_mass_keys": len(masses),
        })
        return v

    full_engine._reuse_output_quality = spy

    proj2 = json.loads(json.dumps(proj))
    dc2 = proj2["components"]["AI_DC1"]
    dc2["quality_state_enabled"] = True
    dc2["water_sources"]["reclaimed"]["target_fraction"] = 0.9
    dc2["water_sources"]["potable"]["target_fraction"] = 0.1
    dc2["installed_it_capacity_mw"] = 1100.0
    dc2.pop("capacity_schedule", None)
    res = FullAIUWMModel(proj2, ts).run()

    full_engine._reuse_output_quality = orig

    w("\n" + "=" * 78)
    w("B. _reuse_output_quality 逐次返回值（前 15 次）")
    w("=" * 78)
    w(f"{'#':>3} {'reuse_id':>16} {'volume_ML':>10} {'TDS_mass_kg':>12} "
      f"{'C_from_ledger':>13} {'ret_TDS':>9} {'ret_Cl':>8}")
    for i, s in enumerate(seen[:15]):
        c = s["TDS_mass_kg"] / s["volume_ml"] if s["volume_ml"] > 1e-12 else float("nan")
        w(f"{i:>3} {str(s['reuse_id'])[:16]:>16} {s['volume_ml']:>10.3f} "
          f"{s['TDS_mass_kg']:>12.4f} {c:>13.3f} {s['ret_TDS']:>9.3f} {s['ret_chloride']:>8.3f}")

    if seen:
        tds = [s["ret_TDS"] for s in seen]
        w(f"\n  返回 TDS 分布: 首次={tds[0]:.2f}  中位={sorted(tds)[len(tds)//2]:.2f}  "
          f"末次={tds[-1]:.2f}  min={min(tds):.2f}  max={max(tds):.2f} mg/L")
        w(f"  调用次数 = {len(seen)}")

    # ---------- 3. 再生水组件逐日 volume / TDS mass ----------
    w("\n" + "=" * 78)
    w("C. 再生水组件逐日状态（来自 component_daily）")
    w("=" * 78)
    cd = res.component_daily
    w(f"  列: {[c for c in cd.columns][:40]}")
    sub = cd[cd["component_id"].astype(str).str.contains("REUSE", case=False, na=False)] \
        if "component_id" in cd.columns else cd.iloc[0:0]
    if len(sub):
        keep = [c for c in sub.columns
                if any(k in c.lower() for k in ("storage", "volume", "tds", "pollutant"))]
        w(sub[["date"] + keep].head(8).to_string())

    # ---------- 4. 结论计算 ----------
    w("\n" + "=" * 78)
    w("D. 判定")
    w("=" * 78)
    declared = 650.0
    if seen:
        med = sorted([s["ret_TDS"] for s in seen])[len(seen) // 2]
        w(f"  项目声明的 C_r = {declared} mg/L")
        w(f"  动态路径实际使用的再生水 TDS 中位数 = {med:.2f} mg/L")
        w(f"  比值 = {med / declared:.4f}")
        if med < 0.5 * declared:
            w("  ❌ 动态路径的再生水 TDS 与主分析 C_r 不在同一量级。")
            w("     => §5.7.10 的『储池缓冲』解释不成立；两路径差异主要来自水质输入不一致。")
        else:
            w("  ✅ 量级一致，储池缓冲解释可保留。")

    Path(OUT).write_text("\n".join(lines), encoding="utf-8")
    print(f"写入 {OUT}")


if __name__ == "__main__":
    main()
