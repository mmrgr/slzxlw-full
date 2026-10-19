# -*- coding: utf-8 -*-
"""诊断：动态盐分路径下，"储池盐量从 603 mg/L 掉到 35 mg/L"是缓冲还是补水水质崩了？

【可疑点】
_quality_storage_diag.txt 显示
  day0: storage_start_TDS 7236 kg / 12 ML = 603 mg/L
        storage_end_TDS  13145 kg / 24 ML = 547.7 mg/L
  day1: storage_end_TDS  5890 kg / 24 ML = 245.4 mg/L
  ...
  day11: storage_end_TDS  855.6 kg / 24 ML = 35.7 mg/L
排污 TDS 降到 194 mg/L，**低于 r=0.9 的混合补水浓度 603 mg/L**。
排污浓度低于补水浓度在稳态下不可能（除非有脱盐）。

【本脚本要回答】
1. 逐日反解实际补水 TDS（质量守恒）：
   start + Σ(source_amount × source_quality) - withdrawn - end = 0
   → C_in 可解
2. 拆解 reclaimed / potable / other 三股的量与浓度，看是哪一股在变
3. day0 与 day1 的补水水质为何跳变（scenario prior vs 实时 treated output）
4. 储池初始 12 ML 的 603 mg/L 与逐日实际补水浓度是否一致
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

from aiuwm.full_engine import (  # noqa: E402
    FullAIUWMModel,
    _initial_quality_concentrations,
    _source_quality,
)

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
OUT = HERE / "_dynamic_inflow_diag.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    dc = proj["components"]["AI_DC1"]

    w("=" * 78)
    w("A. 项目里声明的各水源水质")
    w("=" * 78)
    for sname, src in dc.get("water_sources", {}).items():
        w(f"  {sname}: target_fraction={src.get('target_fraction')}")
        w(f"      quality = {json.dumps(_source_quality(dc, sname), ensure_ascii=False)}")
    w(f"\n  初始储池浓度 _initial_quality_concentrations = "
      f"{json.dumps(_initial_quality_concentrations(dc), ensure_ascii=False)}")
    w(f"  cooling.blowdown_quality_mg_l = "
      f"{json.dumps(dc.get('cooling', {}).get('blowdown_quality_mg_l'), ensure_ascii=False)}")

    # 再生水组件声明水质
    for cid, comp in proj["components"].items():
        if comp.get("kind") == "reuse":
            w(f"\n  复用组件 {cid}:")
            for k in ("quality_mg_l", "treated_quality_mg_l",
                      "quality_provenance", "quality_evidence_type",
                      "pollutant_removal_fraction"):
                if k in comp:
                    w(f"      {k} = {json.dumps(comp[k], ensure_ascii=False)[:300]}")

    # 跑 r=0.9 动态路径
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

    base = ["date", "blowdown_ml", "gross_makeup_ml", "external_makeup_ml",
            "quality_storage_volume_start_ml", "quality_storage_volume_end_ml",
            "quality_storage_start_TDS_kg", "quality_storage_end_TDS_kg",
            "quality_blowdown_TDS_mg_l", "quality_process_TDS_mg_l",
            "quality_reclaimed_quality_provenance"]
    cols = [c for c in base if c in d.columns]
    sub = d[cols].copy()
    for c in cols:
        if c not in ("date", "quality_reclaimed_quality_provenance"):
            sub[c] = pd.to_numeric(sub[c], errors="coerce")

    w("\n" + "=" * 78)
    w("B. 逐日反解实际混合补水 TDS（质量守恒）")
    w("   start + C_in*V_in_eff - withdrawn - end = 0")
    w("   其中 mixed = start + V_in_eff，withdrawn = C_mix * process")
    w("=" * 78)
    w(f"{'day':>4} {'V_start':>9} {'V_end':>9} {'V_in':>9} {'process':>9} "
      f"{'M_start':>11} {'M_end':>11} {'C_end':>8} {'Cin_req':>9} {'C_blow':>8} {'prov':>14}")
    for i in range(min(20, len(sub))):
        r = sub.iloc[i]
        vs = r["quality_storage_volume_start_ml"]
        ve = r["quality_storage_volume_end_ml"]
        vin = r["external_makeup_ml"]
        ms = r["quality_storage_start_TDS_kg"]
        me = r["quality_storage_end_TDS_kg"]
        vmix = vs + vin
        if vmix <= 1e-12:
            continue
        # process_volume = min(external_makeup, vmix)
        proc = min(vin, vmix)
        # 守恒: ms + vin*Cin = (ms + vin*Cin)/vmix * proc + me
        # 令 x=Cin: ms + vin*x - me = proc/vmix*(ms + vin*x)
        # => (ms - me) + vin*x = (proc/vmix)*ms + (proc/vmix)*vin*x
        # => x*(vin - proc*vin/vmix) = (proc/vmix)*ms - (ms - me)
        a = vin - proc * vin / vmix
        b = proc / vmix * ms - (ms - me)
        cin = b / a if abs(a) > 1e-12 else float("nan")
        cend = me / ve if ve > 0 else float("nan")
        w(f"{i:>4} {vs:>9.3f} {ve:>9.3f} {vin:>9.3f} {proc:>9.3f} "
          f"{ms:>11.2f} {me:>11.2f} {cend:>8.2f} {cin:>9.2f} "
          f"{r['quality_blowdown_TDS_mg_l']:>8.2f} "
          f"{str(r['quality_reclaimed_quality_provenance'])[:14]:>14}")

    w("\n" + "=" * 78)
    w("C. 关键判断题")
    w("=" * 78)
    cen = pd.to_numeric(sub["quality_storage_end_TDS_kg"], errors="coerce") / \
        pd.to_numeric(sub["quality_storage_volume_end_ml"], errors="coerce")
    w(f"  储池 TDS 轨迹: day0={cen.iloc[0]:.1f}  min={cen.min():.1f}  "
      f"末值={cen.iloc[-1]:.1f} mg/L")
    cbl = pd.to_numeric(sub["quality_blowdown_TDS_mg_l"], errors="coerce")
    w(f"  排污 TDS 轨迹: day0={cbl.iloc[0]:.1f}  末值={cbl.iloc[-1]:.1f} mg/L")
    w(f"  环内 process TDS 末值 = "
      f"{pd.to_numeric(sub['quality_process_TDS_mg_l'], errors='coerce').iloc[-1]:.2f} mg/L")
    w("")
    if cen.iloc[-1] < 100:
        w("  ⚠ 储池 TDS 末值 < 100 mg/L，远低于设计的混合补水浓度。")
        w("    若逐日补水浓度也是这个量级，说明模型内部再生水 TDS 约 50 mg/L，")
        w("    与论文使用的 C_r = 650 mg/L 完全不在一个量级 —— 需披露。")

    Path(OUT).write_text("\n".join(lines), encoding="utf-8")
    print(f"写入 {OUT}")


if __name__ == "__main__":
    main()
