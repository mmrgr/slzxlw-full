# -*- coding: utf-8 -*-
"""隔离验证：动态路径下 CoC 锁死在 5.0，是「储池缓冲」还是「补水无盐」？

【要干净的因果归因，需要 2×2 设计】
  因子 A: quality_state（legacy / dynamic）
  因子 B: 市政 TDS 入流（缺 / 补齐到 C_r≈650）

四种组合：
  1. legacy  × 缺 TDS   → 当前主分析（C_r 由声明 650 主导，正常）
  2. dynamic × 缺 TDS   → 上一轮 §5.7.9「事实二」（C_r 被覆盖为 ≈8.4）
  3. legacy  × 补 TDS   → 对照
  4. dynamic × 补 TDS   → 真正的「储池缓冲」检验

若 CoC 锁死只在组合 2 出现、组合 4 不出现，则成因是「补水无盐」，
不是储池缓冲 —— §5.7.9「事实三」必须推翻。
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
OUT = HERE / "_twobytwo_attribution.txt"
TDS_LOAD = 0.121664
CL_LOAD = 0.024333
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))
    print(s, flush=True)


BASE = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
TS = pd.read_csv(R2 / "ha" / "timeseries.csv")


def make(enable: bool, r: float, aligned: bool) -> dict:
    p = json.loads(json.dumps(BASE))
    dc = p["components"]["AI_DC1"]
    dc["quality_state_enabled"] = enable
    dc["water_sources"]["reclaimed"]["target_fraction"] = r
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - r
    dc["installed_it_capacity_mw"] = 1100.0
    dc.pop("capacity_schedule", None)
    if aligned:
        loads = p["local_areas"]["LA1"]["sanitary_pollutant_load_kg_capita_day"]
        loads["TDS"] = TDS_LOAD
        loads["chloride"] = CL_LOAD
    return p


def run(proj: dict) -> tuple[list[float], dict]:
    seen: list[float] = []
    orig = full_engine._reuse_output_quality

    def spy(model, reuse_id, reuse_component):
        v = orig(model, reuse_id, reuse_component)
        seen.append(float(v.get("TDS", 0.0)))
        return v

    full_engine._reuse_output_quality = spy
    try:
        res = FullAIUWMModel(proj, TS).run()
    finally:
        full_engine._reuse_output_quality = orig
    d = res.data_center_daily
    mk = float(pd.to_numeric(d["external_makeup_ml"], errors="coerce").sum())
    gross = float(pd.to_numeric(d["gross_makeup_ml"], errors="coerce").sum())
    blow = float(pd.to_numeric(d["blowdown_ml"], errors="coerce").sum())
    fbal = pd.to_numeric(d.get("quality_coc_fallback"), errors="coerce") \
        if "quality_coc_fallback" in d.columns else None
    return seen, {"makeup_ml": mk, "gross_makeup_ml": gross,
                  "blowdown_ml": blow,
                  "coc_fallback_n": int(fbal.notna().sum()) if fbal is not None else -1}


def main() -> None:
    w("=" * 78)
    w("2×2 归因：quality_state × 市政 TDS 入流")
    w("=" * 78)
    w(f"{'组合':>26}{'r':>6}{'C_r 中位':>12}{'年补水 ML':>13}{'毛补水 ML':>14}{'排污 ML':>12}")
    w("-" * 83)
    table: dict[str, dict] = {}
    for aligned in (False, True):
        for enable in (False, True):
            for r in (0.5, 0.9):
                seen, m = run(make(enable, r, aligned))
                med = sorted(seen)[len(seen) // 2] if seen else float("nan")
                tag = ("dynamic" if enable else "legacy") + \
                      ("+TDS" if aligned else "-TDS")
                w(f"{tag:>26}{r:>6.1f}{med:>12.2f}{m['makeup_ml']:>13.1f}"
                  f"{m['gross_makeup_ml']:>14.1f}{m['blowdown_ml']:>12.1f}")
                table[f"{tag}|{r}"] = {"Cr_med": med, **m}

    w("\n" + "=" * 78)
    w("判定")
    w("=" * 78)
    a = table["dynamic-TDS|0.9"]
    b = table["dynamic+TDS|0.9"]
    w(f"  组合2 dynamic×缺TDS (r=0.9): C_r={a['Cr_med']:.2f}  补水={a['makeup_ml']:,.1f}")
    w(f"  组合4 dynamic×补TDS (r=0.9): C_r={b['Cr_med']:.2f}  补水={b['makeup_ml']:,.1f}")
    l9 = table["legacy-TDS|0.9"]
    l5 = table["legacy-TDS|0.5"]
    w(f"  参照 legacy×缺TDS  : r=0.5 补水={l5['makeup_ml']:,.1f} → "
      f"r=0.9 补水={l9['makeup_ml']:,.1f}  (+{100*(l9['makeup_ml']/l5['makeup_ml']-1):.3f}%)")
    w("")
    w("  归因逻辑：")
    w("   - 若『储池缓冲』成立，则组合4（动态+正确C_r）也应补水几乎不随 r 变；")
    w("   - 若『补水无盐』才是成因，则组合4 的补水应重新随 r 上升。")
    w("")
    d1 = 100 * (a["makeup_ml"] / table["dynamic-TDS|0.5"]["makeup_ml"] - 1)
    d2 = 100 * (b["makeup_ml"] / table["dynamic+TDS|0.5"]["makeup_ml"] - 1)
    w(f"  动态×缺TDS: r=0.5→0.9 补水变化 = {d1:+.3f}%")
    w(f"  动态×补TDS: r=0.5→0.9 补水变化 = {d2:+.3f}%")
    if abs(d1) < 0.1 and d2 > 0.5:
        w("  ✅ 归因成立：『锁死』只在缺 TDS 时出现。成因是补水无盐，不是储池缓冲。")
        w("     §5.7.9『事实三』必须推翻重写。")
    elif abs(d1) < 0.1 and abs(d2) < 0.1:
        w("  ⚠ 补齐后仍锁死 → 储池缓冲解释可能成立。")
    else:
        w("  ⚠ 需人工判读。")

    Path(OUT).write_text("\n".join(lines), encoding="utf-8")
    print(f"\n写入 {OUT}")


if __name__ == "__main__":
    main()
