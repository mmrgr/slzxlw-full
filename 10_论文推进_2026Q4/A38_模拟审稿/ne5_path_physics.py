"""阶段 2：两路径的物理正确性判决性检验 (2026-10-17).

【问题】引擎有两条水质求解路径, 同输入下 CoC 分别约 1.82 与 7.99 (差 ≈800×):
  A. volume-only  : 回路浓度 = 补水瞬时混合, 不保留溶质存量
  B. R10a 动态    : 逐日累积回路溶质存量 (quality_state_enabled=True)

【判决依据 — 稳态质量平衡】
冷却塔稳态下, 溶质进出必须平衡:
        M · C_makeup  =  B · C_blowdown  +  D · C_blowdown   (D=drift)
  且  C_blowdown = CoC · C_makeup
  =>  M = (B + D) · CoC
  又水量平衡: E = (B + D)(CoC - 1)/CoC  =>  M = E·CoC/(CoC-1)

**关键**: 若 CoC 因掺混 (φ 升高) 而"塌陷"到 1.82, 则按上式 M 必须**显著增大**
(M = E·1.82/0.82 ≈ 2.22E, 而设计 CoC=5 时 M≈1.25E), 即多取水约 78%.

因此**判据**: 哪条路径给出的 (M, CoC) 组合满足
        M_actual / [E·CoC/(CoC-1)]  = 1
即为物理自洽的那条。

【输出】两条路径的质量平衡残差 + 裁定。
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
OUT = HERE / "ne5_path_physics_summary.json"

# 完整水样 (IEUA 绑定碱度; LADWP 约束不绑定 → 对照)
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
        coc_design: float = 5.0) -> dict:
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
    d = res.data_center_daily
    return {
        "M": float(d["external_makeup_ml"].sum()),
        "E": float(d["evaporation_ml"].sum()),
        "B": float(d["blowdown_ml"].sum()) if "blowdown_ml" in d else None,
        "CoC_mean": float(d["cycles_of_concentration"].mean()),
        "CoC_min": float(d["cycles_of_concentration"].min()),
        "CoC_max": float(d["cycles_of_concentration"].max()),
    }


def mass_residual(r: dict) -> float:
    """稳态质量平衡残差: M 应等于 E·CoC/(CoC-1)。返回相对偏差。"""
    coc = r["CoC_mean"]
    if coc is None or not (coc > 1.000001):
        return float("nan")
    m_required = r["E"] * coc / (coc - 1.0)
    if m_required <= 0:
        return float("nan")
    return r["M"] / m_required


def main() -> int:
    print("=" * 78)
    print("阶段 2 ｜ 两路径物理正确性判决性检验")
    print("=" * 78)
    print("\n判据: M_actual / [E·CoC/(CoC-1)] 应 = 1 (稳态质量平衡自洽)")
    print("     偏离 1 表示该路径的 (M, CoC) 组合不满足守恒\n")

    rows = []
    for dom in ("ha", "co"):
        for name, q in RECLAIMED.items():
            for phi in (0.0, 0.4, 0.6):
                for qs, tag in ((False, "volume-only"), (True, "R10a-dynamic")):
                    r = run(dom, q, phi, qs)
                    ratio = mass_residual(r)
                    rows.append({"domain": dom, "sample": name, "phi": phi,
                                 "path": tag, **r, "balance_ratio": ratio})
                    print(f"  {dom} {name:<6} φ={phi}  {tag:<13} "
                          f"CoC={r['CoC_mean']:.4f}  M={r['M']:>10.1f}  "
                          f"M/[E·CoC/(CoC-1)]={ratio:.4f}")

    df = pd.DataFrame(rows)
    print("\n" + "=" * 78)
    print("裁定")
    print("=" * 78)
    for tag, g in df.groupby("path"):
        dev = (g["balance_ratio"] - 1.0).abs()
        print(f"  {tag:<14} 平均|偏离1| = {dev.mean():.4f}  最大 = {dev.max():.4f}")

    vo = df[df.path == "volume-only"]["balance_ratio"]
    r10 = df[df.path == "R10a-dynamic"]["balance_ratio"]
    vo_dev = float((vo - 1).abs().mean())
    r10_dev = float((r10 - 1).abs().mean())
    verdict = ("VOLUME_ONLY_SELF_CONSISTENT" if vo_dev < r10_dev
               else "R10A_SELF_CONSISTENT" if r10_dev < vo_dev else "INDISTINGUISHABLE")
    print(f"\n  ⇒ {verdict}")

    OUT.write_text(json.dumps({
        "criterion": "M_actual / [E*CoC/(CoC-1)] should equal 1 under steady mass balance",
        "rows": rows,
        "mean_abs_dev_volume_only": vo_dev,
        "mean_abs_dev_r10a": r10_dev,
        "verdict": verdict,
        "caveat": ("本检验判定的是【水量-浓度组合是否满足稳态质量平衡】; "
                   "两条路径都不违反质量守恒时, 需另找物理判据(如与实测 CoC 对比)。"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[write] {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
