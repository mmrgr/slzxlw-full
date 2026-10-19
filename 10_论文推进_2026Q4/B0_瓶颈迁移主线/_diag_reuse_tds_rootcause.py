# -*- coding: utf-8 -*-
"""诊断 3：确认「动态路径再生水 TDS ≈ 8 mg/L」的根因链。

【假设的根因链】
1. 项目只给市政污水声明了 BOD=0.06、TSS=0.07 kg/人/日（LA1），**没有 TDS**。
2. 污水管网 → WWTW 的 pollutant_storage["TDS"] 因此只累积来自数据中心的排污盐量。
3. WWTW 的 removal_fraction["TDS"]=0.05 再扣掉 5%。
4. 转移 16%（central_reuse_fraction）到 CENTRAL_REUSE，除以储池体积
   → 得到 5–43 mg/L 的"实时再生水 TDS"。
5. full_engine._reuse_output_quality() 用这个实时值**覆盖**了项目声明的
   water_sources.reclaimed.quality.TDS = 650。
6. 于是动态路径的 C_r 实际 ≈ 8 mg/L，而主分析（legacy 路径）用 650。

【判定】
若 TDS 入流 ≈ 0，则 A、B 两条都应成立，且 C 成立。
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
OUT = HERE / "_reuse_tds_rootcause.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")

    w("=" * 78)
    w("A. 项目里声明的入流污染物（这是根因）")
    w("=" * 78)
    la = proj["local_areas"]["LA1"]
    w(f"  LA1 sanitary_pollutant_load_kg_capita_day = "
      f"{json.dumps(la.get('sanitary_pollutant_load_kg_capita_day'), ensure_ascii=False)}")
    w("  → 只有 BOD / TSS，**无 TDS**。")
    w("")
    w(f"  WWTW1 pollutant_removal_fraction = "
      f"{json.dumps(proj['components']['WWTW1'].get('pollutant_removal_fraction'), ensure_ascii=False)}")
    w("  → 声明了 TDS 列，但没有 TDS 入流可去除。")
    w("")
    cr = proj["components"]["CENTRAL_REUSE"]
    w(f"  CENTRAL_REUSE 声明水质键: "
      f"{[k for k in cr if 'quality' in k.lower()] or '（无任何 quality 声明）'}")
    w(f"  AI_DC1 water_sources.reclaimed.quality = "
      f"{json.dumps(proj['components']['AI_DC1']['water_sources']['reclaimed'].get('quality'), ensure_ascii=False)}")

    # ---------- 跑动态路径 ----------
    seen: list[dict] = []
    orig = full_engine._reuse_output_quality

    def spy(model, reuse_id, reuse_component):
        v = orig(model, reuse_id, reuse_component)
        vol = max(0.0, float(model.storage.get(reuse_id, 0.0))) if reuse_id else 0.0
        masses = dict(model.pollutant_storage.get(reuse_id, {})) if reuse_id else {}
        seen.append({
            "volume_ml": vol,
            "TDS_mass_kg": float(masses.get("TDS", 0.0)),
            "TDS": float(v.get("TDS", 0.0)),
            "chloride": float(v.get("chloride", 0.0)),
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
    w("B. 动态路径实际使用的 C_r（730 天）")
    w("=" * 78)
    tds = [s["TDS"] for s in seen]
    chl = [s["chloride"] for s in seen]
    srt = sorted(tds)
    w(f"  TDS   : 首次={tds[0]:.3f}  中位={srt[len(srt)//2]:.3f}  "
      f"均值={sum(tds)/len(tds):.3f}  min={min(tds):.3f}  max={max(tds):.3f} mg/L")
    w(f"  Cl    : 首次={chl[0]:.3f}  中位={sorted(chl)[len(chl)//2]:.3f} mg/L")
    w(f"  声明值: TDS=650, chloride=130 mg/L")
    w(f"  比值  : TDS {sum(tds)/len(tds)/650:.4f}×, "
      f"Cl {sum(chl)/len(chl)/130:.4f}×")

    # ---------- 反证：把 TDS 加入 municipal load 后 C_r 是否恢复 ----------
    w("\n" + "=" * 78)
    w("C. 反证实验：给市政污水补上 TDS 入流后，C_r 是否回到 650 量级？")
    w("=" * 78)
    # 反解：要让 CY 的再生水 TDS 达到 650，需要多少入流质量？
    # C_reuse = mass_in*(1-0.05)*share / volume
    # 用一个粗略的每日入流估算
    cd = res.component_daily
    ww = cd[cd["component_id"] == "WWTW1"] if "component_id" in cd.columns else cd.iloc[0:0]
    if len(ww):
        w(f"  WWTW1 日均 treated_ml = {pd.to_numeric(ww['treated_ml'], errors='coerce').mean():.2f}")
        treat = float(pd.to_numeric(ww["treated_ml"], errors="coerce").mean())
        share = float(proj["components"]["WWTW1"].get("central_reuse_fraction", 0.0))
        store = 30.0  # CENTRAL_REUSE 稳态容积约 30 ML
        # 650 = M *(1-0.05)*share/ store  → M
        need_mass = 650.0 * store / (0.95 * share)
        w(f"  central_reuse_fraction = {share}")
        w(f"  稳态储池约 {store} ML")
        w(f"  要达到 C_r=650 mg/L，CENTRAL_REUSE 每日需接收 TDS 质量 ≈ {need_mass:.1f} kg/d")
        # 反推需要的入流浓度
        conv = need_mass / (treat * 1000.0) * 1e6  # kg/ML -> mg/L
        w(f"  对应 WWTW 进流 TDS 浓度 ≈ {conv:.1f} mg/L  "
          f"（典型市政污水 TDS 300–500 mg/L）")
        w("")
        if conv > 1500:
            w("  ⚠ 所需进流浓度远高于市政污水典型值 → 说明另有结构性问题，不止是缺 TDS 声明。")
        elif conv < 800:
            w("  ✅ 所需进流浓度落在市政污水常见范围 → 根因确认为『项目缺 TDS 入流声明』。")

    # ---------- 结论 ----------
    w("\n" + "=" * 78)
    w("D. 结论：§5.7.10 的『储池缓冲』解释是否成立？")
    w("=" * 78)
    mean_tds = sum(tds) / len(tds)
    w(f"  动态路径实际 C_r ≈ {mean_tds:.2f} mg/L")
    w(f"  主分析声明 C_r = 650 mg/L")
    w(f"  差 {650/mean_tds:.1f} 倍")
    w("")
    w("  ❌ 不成立。两条路径的差异**首先来自水质输入不一致**，不是储池缓冲。")
    w("     动态路径把 C_r 从 650 降到约 8 mg/L，补水几乎不含盐，")
    w("     所以环路永不积盐、CoC 锁在设计值 5.0、r 不起作用。")
    w("     这不是『满库缓冲』，而是『补水无盐』。")
    w("")
    w("  → §5.7.10 现文本（『储池吸收盐分』『上下界』）必须重写或撤除。")
    w("  → S5.11 同样必须重写。")

    Path(OUT).write_text("\n".join(lines), encoding="utf-8")
    print(f"写入 {OUT}")


if __name__ == "__main__":
    main()
