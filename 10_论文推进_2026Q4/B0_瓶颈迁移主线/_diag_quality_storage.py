# -*- coding: utf-8 -*-
"""判断：启用 quality_state 后 CoC 锁在 5.0 是否合理？

【实测】
第 1 天 CoC = 3.6484245（与解析值一致，正确）
第 2 天起 CoC = 5.0000（设计值）
quality_storage_volume: 12 → 23.9999 → 24.0 → 24.0（锁在 24 ML）

【两种解释】
A. **合理的稳态**：动态盐分平衡下，环路盐分由 blowdown 控制。
   若 blowdown 足够，稳态 CoC 会趋近设计值 5.0，而 L 限值不再起作用。
   若如此，则"动态路径下 r* 机制不存在"是真的 —— 这将是重大限制。

B. **储池饱和导致的假象**：quality_storage 锁在 24 ML（容量上限？），
   意味着盐分被"囤"在储池里，环路按纯净补水计，CoC 因此被人为抬高。

【判定方法】
1. 查 quality_storage 的容量配置（24 ML 是否为其上限）；
2. 若储池满了，看 solute 质量是否持续累积（若累积则应导致 CoC 上升而非锁死）；
3. 看 blowdown_ml 是否随 CoC 变化。
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
OUT = HERE / "_quality_storage_diag.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    # 1. 配置中的 storage 容量
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    dc = proj["components"]["AI_DC1"]
    w("=== AI_DC1 中与 storage / quality 相关的配置 ===")
    for k, v in dc.items():
        if any(x in k.lower() for x in ("storage", "quality", "coc", "cooling")):
            w(f"  {k}: {json.dumps(v, ensure_ascii=False)[:300]}")

    w(f"\n  cooling 全键: {json.dumps(dc.get('cooling', {}), ensure_ascii=False)[:700]}")

    # 2. 跑启用版，看逐日盐分
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    proj2 = json.loads(json.dumps(proj))
    dc2 = proj2["components"]["AI_DC1"]
    dc2["quality_state_enabled"] = True
    dc2["water_sources"]["reclaimed"]["target_fraction"] = 0.9
    dc2["water_sources"]["potable"]["target_fraction"] = 0.1
    dc2["installed_it_capacity_mw"] = 1100.0
    dc2.pop("capacity_schedule", None)
    res = FullAIUWMModel(proj2, ts).run()
    d = res.data_center_daily

    cols = [c for c in d.columns if any(k in c.lower() for k in
            ("quality_storage", "quality_solute", "quality_loop", "coc",
             "blowdown", "makeup"))]
    w(f"\n=== 前 12 天逐日（列：{len(cols)}）===")
    sub = d[cols].copy()
    for c in cols:
        sub[c] = pd.to_numeric(sub[c], errors="coerce")
    w(sub.head(12).to_string())

    w("\n=== 第 350-360 天 ===")
    w(sub.iloc[350:360].to_string())

    # 3. 盐分是否在累积
    sol_cols = [c for c in d.columns if "solute" in c.lower() and "residual" not in c.lower()]
    w(f"\n=== 溶质质量列: {sol_cols} ===")
    for c in sol_cols:
        s = pd.to_numeric(d[c], errors="coerce")
        w(f"  {c}: 首={s.iloc[0]:.4f} 末={s.iloc[-1]:.4f} "
          f"min={s.min():.4f} max={s.max():.4f}")

    Path(HERE / "_quality_storage_diag.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
