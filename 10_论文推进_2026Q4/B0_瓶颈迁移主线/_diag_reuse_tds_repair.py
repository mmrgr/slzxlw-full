# -*- coding: utf-8 -*-
"""修复实验：补齐市政污水的 TDS / chloride 入流，让两条路径的水质输入一致，
然后重新回答「动态路径下 r* 机制是否消失」。

【已证实的根因】
  LA1.sanitary_pollutant_load_kg_capita_day = {BOD:0.06, TSS:0.07}  ← 无 TDS/Cl
  WWTW1 声明了 TDS 去除率 0.05，却无 TDS 入流
  → WWTW 的 pollutant_storage["TDS"] 只累积数据中心那一丁点排污盐
  → _reuse_output_quality() 用 mass/volume 覆盖声明值 650，得到 ≈8.4 mg/L
  → 动态路径的 C_r 实际是 8.4 而不是 650（差 77 倍）

【本脚本】
1. 由「声明 C_r = 650 mg/L」反解应有的入流 TDS 负荷（kg/人/日）
   —— 用人口 1e6 与实测日污水量 209 ML，使它自洽
2. 注入该负荷后重跑，检查动态路径的 C_r 是否回到 650 量级
3. 若回到 650，再做 r 扫描：此时两路径水质输入相同，
   「储池缓冲使反噬消失」才是可检验命题
4. 同时补 chloride，使 CoC 的 binding species 关系可复核
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
OUT = HERE / "_reuse_tds_repair.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def run(proj: dict, ts: pd.DataFrame) -> tuple[list[dict], object]:
    """跑一次，返回 _reuse_output_quality 的逐次返回 + 结果对象。"""
    seen: list[dict] = []
    orig = full_engine._reuse_output_quality

    def spy(model, reuse_id, reuse_component):
        v = orig(model, reuse_id, reuse_component)
        seen.append({
            "TDS": float(v.get("TDS", 0.0)),
            "chloride": float(v.get("chloride", 0.0)),
        })
        return v

    full_engine._reuse_output_quality = spy
    try:
        res = FullAIUWMModel(proj, ts).run()
    finally:
        full_engine._reuse_output_quality = orig
    return seen, res


def make_project(base: dict, tds_load: float, cl_load: float,
                 r: float, quality: bool) -> dict:
    p = json.loads(json.dumps(base))
    p["local_areas"]["LA1"]["sanitary_pollutant_load_kg_capita_day"]["TDS"] = tds_load
    p["local_areas"]["LA1"]["sanitary_pollutant_load_kg_capita_day"]["chloride"] = cl_load
    dc = p["components"]["AI_DC1"]
    dc["quality_state_enabled"] = quality
    dc["water_sources"]["reclaimed"]["target_fraction"] = r
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - r
    dc["installed_it_capacity_mw"] = 1100.0
    dc.pop("capacity_schedule", None)
    return p


def main() -> None:
    base = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")

    pop = float(base["local_areas"]["LA1"]["base_population"])
    w("=" * 78)
    w("A. 反解应有的入流负荷，使动态路径的 C_r 与声明值一致")
    w("=" * 78)
    w(f"  人口 = {pop:,.0f}")
    # 先跑一次拿到实测污水量
    _, res0 = run(make_project(base, 0.0, 0.0, 0.9, True), ts)
    cd = res0.component_daily
    ww = cd[cd["component_id"] == "WWTW1"]
    q = float(pd.to_numeric(ww["treated_ml"], errors="coerce").mean())
    w(f"  WWTW1 日均处理量 = {q:.2f} ML/d = {q * 1000:,.0f} m³/d")

    # 目标：进流 TDS 使 _reuse_output_quality 返回 ≈650
    # 稳态下 CENTRAL_REUSE 出流浓度 ≈ 0.95 × 进流浓度（去除率 0.05）
    # 故进流应 ≈ 650/0.95 = 684 mg/L
    target_tds_mg = 650.0 / 0.95
    target_cl_mg = 130.0 / 0.95
    # 单位：1 mg/L × 1 ML = 1e6 mg = 1 kg。故每日质量(kg) = C(mg/L) × Q(ML)
    tds_mass_kg = target_tds_mg * q
    cl_mass_kg = target_cl_mg * q
    tds_load = tds_mass_kg / pop                        # kg/人/日
    cl_load = cl_mass_kg / pop
    w(f"  目标出流 C_r = 650 mg/L → 进流需 ≈ {target_tds_mg:.1f} mg/L")
    w(f"  → 每日 TDS 质量 = {tds_mass_kg:,.1f} kg/d")
    w(f"  → TDS 负荷 = {tds_load:.6f} kg/人/日")
    w(f"  → chloride 负荷 = {cl_load:.6f} kg/人/日")
    # 自检：BOD 声明 0.06 → 进流浓度（kg/d = load×pop；mg/L = kg/ML）
    bod_mg = 0.06 * pop / q
    w(f"  自检：BOD 声明 0.06 kg/人/日 → 进流 {bod_mg:.0f} mg/L（市政典型 250–300）")
    tss_mg = 0.07 * pop / q
    w(f"  自检：TSS 声明 0.07 kg/人/日 → 进流 {tss_mg:.0f} mg/L（市政典型 250–350）")
    w(f"  自检：按同法，TDS {tds_load:.4f} kg/人/日 → "
      f"{tds_load * pop / q:.0f} mg/L（市政典型 300–500，含工业源可到 700）")

    w("\n" + "=" * 78)
    w("B. 注入后的动态 C_r 实测（r=0.9，quality_state=True）")
    w("=" * 78)
    seen, res1 = run(make_project(base, tds_load, cl_load, 0.9, True), ts)
    tds = [s["TDS"] for s in seen]
    chl = [s["chloride"] for s in seen]
    w(f"  TDS: 中位={sorted(tds)[len(tds)//2]:.2f}  均值={sum(tds)/len(tds):.2f}  "
      f"min={min(tds):.2f}  max={max(tds):.2f} mg/L  （目标 650）")
    w(f"  Cl : 中位={sorted(chl)[len(chl)//2]:.2f}  均值={sum(chl)/len(chl):.2f} mg/L  （目标 130）")

    # 稳态储池
    cr = cd[cd["component_id"] == "CENTRAL_REUSE"]
    st = pd.to_numeric(cr["storage_ml"], errors="coerce")
    w(f"  CENTRAL_REUSE 稳态容积 ≈ {st.tail(30).mean():.2f} ML")

    w("\n" + "=" * 78)
    w("C. 关键：注入后，动态路径下 r 还起作用吗？（固定 1100 MW）")
    w("=" * 78)
    rows = []
    for r in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9):
        for mode, qual in (("legacy", False), ("dynamic", True)):
            p = make_project(base, tds_load, cl_load, r, qual)
            _, rr = run(p, ts)
            d = rr.data_center_daily
            tot = float(pd.to_numeric(d["external_makeup_ml"], errors="coerce").sum())
            rows.append({"r": r, "mode": mode, "withdrawal_ml": tot})
    df = pd.DataFrame(rows)
    piv = df.pivot(index="r", columns="mode", values="withdrawal_ml")
    piv["legacy_vs0_pct"] = 100.0 * (piv["legacy"] / piv.loc[0.0, "legacy"] - 1.0)
    piv["dynamic_vs0_pct"] = 100.0 * (piv["dynamic"] / piv.loc[0.0, "dynamic"] - 1.0)
    w(piv.to_string(float_format=lambda x: f"{x:,.4f}"))

    w("\n" + "=" * 78)
    w("D. 判定")
    w("=" * 78)
    med = sorted(tds)[len(tds) // 2]
    ok = 550 <= med <= 760
    w(f"  注入后动态 C_r 中位 = {med:.1f} mg/L，目标 650 → "
      f"{'✅ 一致' if ok else '❌ 仍不一致'}")
    if ok:
        w("  → 现在两条路径的水质输入相同，可以公平比较。")
        w("  → 比较 r=0.9 相对 r=0 的总取水变化：")
        w(f"     legacy  +{piv.loc[0.9,'legacy_vs0_pct']:.3f}%")
        w(f"     dynamic +{piv.loc[0.9,'dynamic_vs0_pct']:.3f}%")
        if abs(piv.loc[0.9, "dynamic_vs0_pct"]) < 0.5:
            w("     → 动态路径下反噬仍近零：这一步才是真正的『储池缓冲』证据。")
        else:
            w("     → 动态路径下反噬仍在：说明此前『消失』主要是水质输入不一致造成的。")

    Path(OUT).write_text("\n".join(lines), encoding="utf-8")
    print(f"写入 {OUT}")


if __name__ == "__main__":
    main()
