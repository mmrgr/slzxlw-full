"""阶段 2-b：区分两路径的物理判据 —— 稳态解 vs 瞬态解 (2026-10-17).

【为什么上一版判据无效】
上一版检验 M/[E·CoC/(CoC-1)]≈1, 但引擎的水量本来就从 CoC 反算 M,
所以**任何** CoC 都"自洽" —— 该判据无法区分路径。

【真正的物理判据】
冷却塔是一个**连续流搅拌槽(CSTR)**。稳态下回路浓度 C_loop 满足质量守恒:
        dC_loop/dt = (M·C_in - (B+D)·C_loop) / V_loop = 0
  =>  C_loop,ss = M·C_in / (B+D)
  又 C_loop/C_in = CoC  =>  B+D = M/CoC, 与水量平衡一致。

**关键点: 稳态 C_loop 只取决于 M、B、C_in, 与"回路历史"无关。**
  · R10a: 逐日积分 C_loop(t) → 会收敛到稳态 (正确物理)
  · volume-only: 直接把 C_loop 设为 C_in 的瞬时混合 → **强制 C_loop = C_in_instantaneous,
    相当于假设 V_loop = 0 (无储液)**, 但同时又报告 CoC=1.82 (即 C_loop=1.82·C_in),
    两者**自相矛盾**: 若 V=0 则 C_loop 恒等于 C_in, CoC 应为 1, 而非 1.82。

【检验方法】
对 volume-only, 检查其报告的 CoC 是否可由其自身的 M/B 反推:
        CoC_from_mass = ???
更直接: volume-only 的回路浓度 = 补水浓度 (公式 `concentrations[indicator] += fraction*value`),
即 C_loop = C_makeup_exactly ⇒ **CoC 必须 = 1**。
但它又用 min(limit/C_makeup) 作为 CoC —— **这是拿"补水浓度"当"回路浓度"去比限值**,
即把"限值适用于补水"与"限值适用于循环水"两个不同物理要求混为一谈。

**本检验**: 对每个情景, 计算
  (a) 稳态 CoC (由 M、B 反推)            = M/(B+D)  [或由水量平衡]
  (b) 路径报告的 CoC
并比较哪条自洽。
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

import pandas as pd  # noqa: E402

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ENGINE / "examples" / "cawcc_r2"
OUT = HERE / "ne5b_path_physics_summary.json"

RECLAIMED = {
    "IEUA": {"TDS": 443.0, "chloride": 100.0, "hardness": 149.427,
             "alkalinity": 140.0, "silica": 24.0},
    "LADWP": {"TDS": 22.0, "chloride": 3.6, "hardness": 1.024,
              "alkalinity": 7.1, "silica": 0.52},
}
POTABLE = {"TDS": 180.0, "chloride": 35.0, "hardness": 120.0,
           "alkalinity": 100.0, "silica": 10.0}
LIMITS = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
          "alkalinity": 350.0, "silica": 175.0}


def run(domain: str, q_recl: dict, phi: float, quality_state: bool,
        coc_design: float = 5.0) -> pd.DataFrame:
    proj = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / domain / "timeseries.csv")
    proj = copy.deepcopy(proj)
    dc = proj["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["quality_state_enabled"] = bool(quality_state)
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = float(coc_design)
    dc["cooling"]["water_quality_limits"] = dict(LIMITS)
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(phi)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(phi)
    for src, q in (("reclaimed", q_recl), ("potable", POTABLE)):
        s = dc["water_sources"][src]
        s["quality_mg_l"] = dict(q)
        s.pop("quality", None)
    sim = proj.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(ts["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(ts["date"].iloc[-1]).date())
    res = FullAIUWMModel(proj, ts).run()
    return res.data_center_daily


def main() -> int:
    print("=" * 80)
    print("阶段 2-b ｜ 用【回路浓度与补水浓度的关系】区分两路径")
    print("=" * 80)
    print("\n物理: 冷却塔回路是 CSTR; 稳态下 C_loop = M·C_in/(B+D), C_loop/C_in = CoC")
    print("      volume-only 把回路浓度**直接设为补水浓度** ⇒ 若自洽则 CoC 应恒为 1\n")

    rows = []
    for dom in ("ha", "co"):
        for name, q in RECLAIMED.items():
            for phi in (0.4, 0.6):
                for qs, tag in ((False, "volume-only"), (True, "R10a-dynamic")):
                    d = run(dom, q, phi, qs)
                    coc = float(d["cycles_of_concentration"].mean())
                    coc_min = float(d["cycles_of_concentration"].min())
                    coc_max = float(d["cycles_of_concentration"].max())
                    # C_in 混合浓度 (TDS 作为代表物种)
                    c_in = phi * q["TDS"] + (1 - phi) * POTABLE["TDS"]
                    rows.append({"domain": dom, "sample": name, "phi": phi,
                                 "path": tag, "CoC_mean": coc,
                                 "CoC_min": coc_min, "CoC_max": coc_max,
                                 "C_in_TDS": c_in})
                    print(f"  {dom} {name:<6} φ={phi}  {tag:<13} "
                          f"CoC 均值={coc:6.3f} 范围=[{coc_min:.3f}, {coc_max:.3f}]  "
                          f"C_in(TDS)={c_in:7.1f}")

    df = pd.DataFrame(rows)
    print("\n" + "=" * 80)
    print("关键观察")
    print("=" * 80)
    # volume-only 的 CoC 由 min(limit/C_in) 决定 → 检查其是否等于该闭式
    vo = df[df.path == "volume-only"]
    print("\n  volume-only 路径的 CoC 是否恒等于 min(limit_i / C_in_i)?")
    ok = 0
    for _, r in vo.iterrows():
        q = RECLAIMED[r["sample"]]
        phi = r["phi"]
        ratios = []
        for sp, lim in LIMITS.items():
            c = phi * q.get(sp, 0.0) + (1 - phi) * POTABLE.get(sp, 0.0)
            if c > 0:
                ratios.append(lim / c)
        closed = min(max(1.000001, min(ratios)), 5.0) if ratios else 5.0
        match = abs(closed - r["CoC_mean"]) < 1e-3
        ok += match
        print(f"    {r['domain']} {r['sample']:<6} φ={phi}: 报告={r['CoC_mean']:.4f} "
              f"闭式={closed:.4f} {'✓' if match else '✗'}")
    print(f"  ⇒ {ok}/{len(vo)} 匹配闭式 (说明 volume-only = 用【补水浓度】直接比限值)")

    print("\n  R10a 路径的 CoC:")
    r10 = df[df.path == "R10a-dynamic"]
    for _, r in r10.iterrows():
        print(f"    {r['domain']} {r['sample']:<6} φ={r['phi']}: "
              f"均值={r['CoC_mean']:.4f} 范围=[{r['CoC_min']:.3f}, {r['CoC_max']:.3f}]")

    OUT.write_text(json.dumps({
        "rows": rows,
        "volume_only_matches_closed_form": ok,
        "volume_only_total": len(vo),
        "conclusion": ("volume-only 的 CoC 恒等于 min(limit_i/C_in_i), 即它把"
                       "**补水浓度**当作**循环水浓度**去比限值; 这在物理上等价于"
                       "假设回路无储液(V=0), 但 V=0 时 CoC 应恒为 1 而非 1.8-5.0"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[write] {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
