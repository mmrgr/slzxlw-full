# -*- coding: utf-8 -*-
"""敏感性检验：启用 quality_state（动态盐分追踪）后，结论是否改变？

【背景】
cawcc_r2 的两个端点项目都没有设置 `quality_state_enabled`，
故 `_quality_state_enabled()` 返回 False，模型走 `DISABLED_LEGACY_VOLUME_ONLY`：
  - CoC 由解析式 min(CoC_d, L/C_mix(目标配比)) 直接给出；
  - 不做逐日盐分质量平衡，不追踪环路累积盐分；
  - 实际交付比例 r_eff 低于目标时，CoC 仍按目标算（上轮已披露）。

【本检验】
在 1100 MW 下，对 r ∈ {0.5, 0.7, 0.8, 0.9} 两组分别跑：
  A. 默认（quality_state_enabled = False）—— 论文当前设定
  B. 启用（quality_state_enabled = True）
比较：CoC、r_eff、总取水、水源取水比。

【预期】
若 B 组 CoC 明显高于 A 组（因动态追踪会发现实际混合更淡），
则说明论文当前设定偏保守；若 B 组失败/不可用，则须如实记录。
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

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
OUT = HERE / "_quality_state_sensitivity.json"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def run(enable: bool, r: float, mw: float) -> dict | None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    dc = proj["components"]["AI_DC1"]
    if enable:
        dc["quality_state_enabled"] = True
    dc["water_sources"]["reclaimed"]["target_fraction"] = r
    dc["water_sources"]["potable"]["target_fraction"] = 1 - r
    dc["installed_it_capacity_mw"] = mw
    dc.pop("capacity_schedule", None)
    try:
        res = FullAIUWMModel(proj, ts).run()
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:80]}"}
    d = res.data_center_daily
    num = lambda c: pd.to_numeric(d[c], errors="coerce") if c in d.columns else None
    out = {
        "coc_mean": float(num("cycles_of_concentration").mean())
        if num("cycles_of_concentration") is not None else None,
        "r_eff_mean": float(num("actual_reclaimed_fraction").mean())
        if num("actual_reclaimed_fraction") is not None else None,
        "makeup_sum_ml": float(num("external_makeup_ml").sum())
        if num("external_makeup_ml") is not None else None,
        "ratio_mean": float(num("max_source_abstraction_ratio").mean())
        if num("max_source_abstraction_ratio") is not None else None,
        "state_status": str(d["quality_state_status"].iloc[0])
        if "quality_state_status" in d.columns else None,
        "solver_status": str(d["quality_solver_status"].iloc[0])
        if "quality_solver_status" in d.columns else None,
    }
    return out


def main() -> None:
    MW = 1100.0
    w(f"{'r':>5}{'启用':>6}{'CoC':>10}{'r_eff':>10}{'补水ML':>12}{'取水比':>10}  状态")
    w("-" * 82)
    rows = []
    for r in (0.5, 0.7, 0.8, 0.9):
        for enable in (False, True):
            o = run(enable, r, MW)
            if o is None or "error" in o:
                w(f"{r:>5.1f}{str(enable):>6}{'ERROR':>10}   {o.get('error') if o else '?'}")
                rows.append({"r": r, "enabled": enable, "error": o.get("error") if o else "?"})
                continue
            coc = o["coc_mean"]
            reff = o["r_eff_mean"]
            mk = o["makeup_sum_ml"]
            rt = o["ratio_mean"]
            fmt = lambda v, spec: (format(v, spec) if v is not None else "None")
            w(f"{r:>5.1f}{str(enable):>6}{fmt(coc,'>10.4f')}{fmt(reff,'>10.6f')}"
              f"{fmt(mk,'>12.1f')}{fmt(rt,'>10.6f')}  {o['state_status']}")
            rows.append({"r": r, "enabled": enable, **o})

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(HERE / "_quality_state_sensitivity.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
