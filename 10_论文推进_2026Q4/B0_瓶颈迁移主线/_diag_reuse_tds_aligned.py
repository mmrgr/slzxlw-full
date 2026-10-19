# -*- coding: utf-8 -*-
"""对齐验证：让动态路径的 C_r 精确落在 650，然后做完整 r 扫描 + CAWCC 扫描。

【为什么需要这一步】
上一实验注入了按"进流 684 mg/L → 出流 650"反解的负荷，实测出流中位 757.9，
偏高 16.6%。原因是储池稳态并非"完全混合 + 无二次浓缩"：
数据中心排污回流的盐分会回到 WWTW（recovered_return），抬高出流浓度。
需要迭代标定负荷，使动态出流的中位数正好等于 650。

【本脚本】
1. 对负荷做二分/比例迭代，直到动态出流 TDS 中位 = 650 ± 5
2. 用标定后的负荷做 r = 0..0.9 扫描（legacy vs dynamic）
3. 用标定后的负荷做 CAWCC 二分扫描（legacy vs dynamic）
4. 输出结论：储池缓冲到底使反噬变强、变弱还是不变
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
OUT = HERE / "_reuse_tds_aligned.txt"
JSON_OUT = HERE / "_reuse_tds_aligned.json"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


BASE = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
TS = pd.read_csv(R2 / "ha" / "timeseries.csv")
POP = float(BASE["local_areas"]["LA1"]["base_population"])


def make_project(tds_load: float, cl_load: float, r: float,
                 quality: bool, mw: float = 1100.0) -> dict:
    p = json.loads(json.dumps(BASE))
    loads = p["local_areas"]["LA1"]["sanitary_pollutant_load_kg_capita_day"]
    loads["TDS"] = tds_load
    loads["chloride"] = cl_load
    dc = p["components"]["AI_DC1"]
    dc["quality_state_enabled"] = quality
    dc["water_sources"]["reclaimed"]["target_fraction"] = r
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - r
    dc["installed_it_capacity_mw"] = mw
    dc.pop("capacity_schedule", None)
    return p


def run_spy(proj: dict) -> tuple[list[float], object]:
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
    return seen, res


def calib(target: float = 650.0, iters: int = 8) -> tuple[float, list[float]]:
    """比例迭代标定 TDS 负荷，使动态出流 TDS 中位 = target。"""
    q = 209.14   # ML/d，先前测得
    load = target / 0.95 * q / POP
    hist: list[float] = []
    for i in range(iters):
        seen, _ = run_spy(make_project(load, load * 0.2, 0.9, True))
        med = sorted(seen)[len(seen) // 2] if seen else 0.0
        hist.append((load, med))
        w(f"    iter {i}: load={load:.6f} kg/人/日 → 出流中位={med:.2f} mg/L")
        if abs(med - target) < 5.0:
            break
        if med <= 0:
            load *= 2.0
        else:
            load *= target / med
    return load, hist


def main() -> None:
    result: dict = {}

    w("=" * 78)
    w("A. 标定 TDS 负荷，使动态路径出流 C_r 中位 = 650 mg/L")
    w("=" * 78)
    tds_load, _ = calib(650.0)
    cl_load = tds_load * 0.2          # 650:130 = 5:1
    w(f"  标定结果: TDS load = {tds_load:.6f} kg/人/日, "
      f"Cl load = {cl_load:.6f} kg/人/日")
    w(f"  对应进流 TDS = {tds_load * POP / 209.14:.1f} mg/L")
    result["tds_load"] = tds_load
    result["cl_load"] = cl_load

    w("\n" + "=" * 78)
    w("B. r 扫描（固定 1100 MW），两条路径水质输入已对齐")
    w("=" * 78)
    rows = []
    for r in (0.0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9):
        for mode, qual in (("legacy", False), ("dynamic", True)):
            _, rr = run_spy(make_project(tds_load, cl_load, r, qual))
            d = rr.data_center_daily
            tot = float(pd.to_numeric(d["external_makeup_ml"], errors="coerce").sum())
            rows.append({"r": r, "mode": mode, "withdrawal_ml": round(tot, 2)})
            w(f"    r={r} {mode:>8}: 总取水 {tot:,.2f} ML")
    df = pd.DataFrame(rows)
    piv = df.pivot(index="r", columns="mode", values="withdrawal_ml")
    piv["legacy_pct"] = 100.0 * (piv["legacy"] / piv.loc[0.0, "legacy"] - 1.0)
    piv["dynamic_pct"] = 100.0 * (piv["dynamic"] / piv.loc[0.0, "dynamic"] - 1.0)
    w("\n" + piv.to_string(float_format=lambda x: f"{x:,.4f}"))
    result["r_scan"] = piv.reset_index().to_dict(orient="records")

    w("\n" + "=" * 78)
    w("C. CAWCC 二分扫描（allowed load × r），两条路径")
    w("=" * 78)
    cawcc: dict[str, list[dict]] = {"legacy": [], "dynamic": []}
    for mode, qual in (("legacy", False), ("dynamic", True)):
        for r in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9):
            lo, hi = 0.0, 2000.0
            # 可行性判据：run 是否报 policy_failure / 有 unmet
            def feasible(mw: float) -> bool:
                _, rres = run_spy(make_project(tds_load, cl_load, r, qual, mw))
                d = rres.data_center_daily
                um = pd.to_numeric(
                    d.get("unmet_cooling_ml", pd.Series([0.0])), errors="coerce"
                ).sum()
                return float(um) <= 1e-6

            # 先确认上界可行
            if not feasible(hi):
                hi = 2000.0
            for _ in range(9):
                mid = 0.5 * (lo + hi)
                if feasible(mid):
                    lo = mid
                else:
                    hi = mid
            val = round(lo, 1)
            cawcc[mode].append({"r": r, "cawcc_mw": val})
            w(f"    {mode:>8} r={r}: CAWCC = {val} MW")
    result["cawcc"] = cawcc
    cdf = pd.DataFrame(cawcc["legacy"]).rename(columns={"cawcc_mw": "legacy"})
    cdf2 = pd.DataFrame(cawcc["dynamic"]).rename(columns={"cawcc_mw": "dynamic"})
    cmp = cdf.merge(cdf2, on="r")
    w("\n" + cmp.to_string(index=False))
    result["cawcc_cmp"] = cmp.to_dict(orient="records")

    w("\n" + "=" * 78)
    w("D. 结论")
    w("=" * 78)
    w(f"  r=0.9 取水变化: legacy +{piv.loc[0.9,'legacy_pct']:.3f}%  "
      f"dynamic +{piv.loc[0.9,'dynamic_pct']:.3f}%")
    w(f"  CAWCC: legacy {cmp['legacy'].tolist()}  dynamic {cmp['dynamic'].tolist()}")
    dl = cmp["legacy"].iloc[0] - cmp["legacy"].iloc[-1]
    dd = cmp["dynamic"].iloc[0] - cmp["dynamic"].iloc[-1]
    w(f"  legacy 效应 = {dl:.1f} MW；dynamic 效应 = {dd:.1f} MW")
    if dd > dl + 5:
        w("  → 对齐后，储池使反噬**更强**（不是消失）。")
        w("    『上下界』说法必须撤除；应改为『路径一致后反噬仍然存在且更强』。")
    elif abs(dd - dl) <= 5:
        w("  → 对齐后两路径效应量接近，路径不敏感。")
    else:
        w("  → 对齐后储池确实削弱反噬，但未到零。")

    Path(OUT).write_text("\n".join(lines), encoding="utf-8")
    Path(JSON_OUT).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"写入 {OUT} / {JSON_OUT}")


if __name__ == "__main__":
    main()
