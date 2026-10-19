"""X4 修复：统一 ne1 / ne5d 的口径，重跑求解路径对照

【问题】
`A38_模拟审稿/` 下两个脚本对"R10a 动态路径是否改变 dS_pot 符号"给出**相反结论**：

| 脚本 | coc_design | CENTRAL_REUSE 质量 | 结论 |
|---|---:|---|---|
| `ne1_r10a_signflip.py:70` | **3.5** | 设 `quality_mg_l` + `quality_provenance="treated_output"` | **4/4 符号一致** |
| `ne5d_direction.py:68` | **5.0** | 只设 `AI_DC1.water_sources.*` | **12/16 符号相反** |

对同一情景（ha/IEUA/φ=0.6），ne1 的 R10a 值 = −3.716，ne5d = −3075.33，相差约 827 倍。

**这不是"两条求解路径的差异"，而是两个设计参数设定的差异。** 把它当作路径差异
引用（如旧稿的 "800×"）是错的。

【本脚本做什么】
用**同一套设定**（`coc_design = 5.0`，与主网格
`examples/cawcc_r2/{ha,co}/project.json` 的
`components.AI_DC1.cooling.cycles_of_concentration` 一致）重跑两件事：

  1. **真路径差异**：volume-only (`quality_state_enabled=False`) vs
     R10a (`quality_state_enabled=True`)，其余设定完全相同
  2. **设计 CoC 敏感性**：在 R10a 路径下扫 `coc_design ∈ {3.5, 4.0, 5.0}`，
     说明 ne1 与 ne5d 的差异来自哪里

【输出】
- `10_论文推进_2026Q4/A38_模拟审稿/ne_unified_path_summary.json`
- `10_论文推进_2026Q4/A38_模拟审稿/ne_unified_path_cases.csv`

用法:
    python A38_模拟审稿/ne_unified_path.py
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENGINE = ROOT.parent / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(ENGINE / "src"))

import pandas as pd  # noqa: E402

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ENGINE / "examples" / "cawcc_r2"
OUT_JSON = HERE / "ne_unified_path_summary.json"
OUT_CSV = HERE / "ne_unified_path_cases.csv"

# 完整组成水样（5 物种齐全）——符号主张只允许用这两个
SAMPLES = {
    "IEUA": {"TDS": 443.0, "chloride": 100.0, "hardness": 149.427,
             "alkalinity": 140.0, "silica": 24.0},
    "LADWP": {"TDS": 22.0, "chloride": 3.6, "hardness": 1.024,
              "alkalinity": 7.1, "silica": 0.52},
}
POTABLE = {"TDS": 180.0, "chloride": 35.0, "hardness": 120.0,
           "alkalinity": 100.0, "silica": 10.0}
LIMITS = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
          "alkalinity": 350.0, "silica": 175.0}

MAIN_GRID_COC = 5.0          # 与主网格一致
COC_SENSITIVITY = (3.5, 4.0, 5.0)
PHIS = (0.4, 0.6)
DOMAINS = ("ha", "co")


def run_case(domain: str, q_recl: dict, phi: float, *, quality_state: bool,
             coc_design: float, set_central_reuse_quality: bool) -> dict:
    project = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    timeseries = pd.read_csv(R2 / domain / "timeseries.csv")
    project = copy.deepcopy(project)

    dc = project["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["quality_state_enabled"] = bool(quality_state)
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = float(coc_design)
    dc["cooling"]["water_quality_limits"] = dict(LIMITS)
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(phi)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(phi)
    dc["water_sources"]["reclaimed"]["quality_mg_l"] = dict(q_recl)
    dc["water_sources"]["potable"]["quality_mg_l"] = dict(POTABLE)

    if set_central_reuse_quality:
        reuse = project["components"].get("CENTRAL_REUSE")
        if reuse is not None:
            reuse["quality_mg_l"] = dict(q_recl)
            reuse["quality_provenance"] = "treated_output"

    sim = project.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(timeseries["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(timeseries["date"].iloc[-1]).date())

    result = FullAIUWMModel(project, timeseries).run()
    daily = result.data_center_daily
    makeup = float(daily["external_makeup_ml"].sum())
    coc_mean = float(daily["cycles_of_concentration"].mean())
    return {"makeup_ml": makeup, "coc_mean": coc_mean}


def main() -> None:
    started = time.time()
    rows: list[dict] = []

    for domain in DOMAINS:
        for sample, q in SAMPLES.items():
            for phi in PHIS:
                # ---- 1. 真路径差异（同一 coc_design = 5.0，同一 CENTRAL_REUSE 设定）----
                m0_vol = run_case(domain, q, 0.0, quality_state=False,
                                  coc_design=MAIN_GRID_COC, set_central_reuse_quality=False)
                m1_vol = run_case(domain, q, phi, quality_state=False,
                                  coc_design=MAIN_GRID_COC, set_central_reuse_quality=False)
                m0_r10 = run_case(domain, q, 0.0, quality_state=True,
                                  coc_design=MAIN_GRID_COC, set_central_reuse_quality=False)
                m1_r10 = run_case(domain, q, phi, quality_state=True,
                                  coc_design=MAIN_GRID_COC, set_central_reuse_quality=False)

                ds_vol = m1_vol["makeup_ml"] - m0_vol["makeup_ml"]
                ds_r10 = m1_r10["makeup_ml"] - m0_r10["makeup_ml"]
                sign_vol = (ds_vol > 1e-9) - (ds_vol < -1e-9)
                sign_r10 = (ds_r10 > 1e-9) - (ds_r10 < -1e-9)

                rows.append({
                    "域": domain, "水样": sample, "phi": phi,
                    "检验": "true_path_difference",
                    "coc_design": MAIN_GRID_COC,
                    "set_central_reuse_quality": False,
                    "M0_volume_only": m0_vol["makeup_ml"],
                    "M1_volume_only": m1_vol["makeup_ml"],
                    "M0_r10a": m0_r10["makeup_ml"],
                    "M1_r10a": m1_r10["makeup_ml"],
                    "dS_volume_only": ds_vol,
                    "dS_r10a": ds_r10,
                    "coc_volume_only": m1_vol["coc_mean"],
                    "coc_r10a": m1_r10["coc_mean"],
                    "sign_volume_only": sign_vol,
                    "sign_r10a": sign_r10,
                    "sign_flips": bool(sign_vol != sign_r10),
                })

                # ---- 2. 设计 CoC 敏感性（R10a 路径）----
                for coc in COC_SENSITIVITY:
                    a0 = run_case(domain, q, 0.0, quality_state=True,
                                  coc_design=coc, set_central_reuse_quality=False)
                    a1 = run_case(domain, q, phi, quality_state=True,
                                  coc_design=coc, set_central_reuse_quality=False)
                    rows.append({
                        "域": domain, "水样": sample, "phi": phi,
                        "检验": "coc_sensitivity_r10a",
                        "coc_design": coc,
                        "set_central_reuse_quality": False,
                        "M0_volume_only": None, "M1_volume_only": None,
                        "M0_r10a": a0["makeup_ml"], "M1_r10a": a1["makeup_ml"],
                        "dS_volume_only": None,
                        "dS_r10a": a1["makeup_ml"] - a0["makeup_ml"],
                        "coc_volume_only": None, "coc_r10a": a1["coc_mean"],
                        "sign_volume_only": None,
                        "sign_r10a": (a1["makeup_ml"] - a0["makeup_ml"] > 1e-9)
                                     - (a1["makeup_ml"] - a0["makeup_ml"] < -1e-9),
                        "sign_flips": None,
                    })

                # ---- 3. 复现 ne1 的设定（coc=3.5 + CENTRAL_REUSE 质量），说明差异来源 ----
                for coc in (3.5, 5.0):
                    b0 = run_case(domain, q, 0.0, quality_state=True,
                                  coc_design=coc, set_central_reuse_quality=True)
                    b1 = run_case(domain, q, phi, quality_state=True,
                                  coc_design=coc, set_central_reuse_quality=True)
                    rows.append({
                        "域": domain, "水样": sample, "phi": phi,
                        "检验": "ne1_style_with_central_reuse_quality",
                        "coc_design": coc,
                        "set_central_reuse_quality": True,
                        "M0_volume_only": None, "M1_volume_only": None,
                        "M0_r10a": b0["makeup_ml"], "M1_r10a": b1["makeup_ml"],
                        "dS_volume_only": None,
                        "dS_r10a": b1["makeup_ml"] - b0["makeup_ml"],
                        "coc_volume_only": None, "coc_r10a": b1["coc_mean"],
                        "sign_volume_only": None,
                        "sign_r10a": (b1["makeup_ml"] - b0["makeup_ml"] > 1e-9)
                                     - (b1["makeup_ml"] - b0["makeup_ml"] < -1e-9),
                        "sign_flips": None,
                    })

        print(f"  [{domain}] done ({time.time() - started:.0f}s)", flush=True)

    frame = pd.DataFrame(rows)
    frame.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    # ---- 汇总 ----
    path = frame[frame["检验"] == "true_path_difference"]
    n_path = len(path)
    n_flip_path = int(path["sign_flips"].sum())

    coc_sens = frame[frame["检验"] == "coc_sensitivity_r10a"]
    coc_pivot = (
        coc_sens.groupby("coc_design")["dS_r10a"]
        .agg(["min", "median", "max", "count"])
        .reset_index()
    )

    ne1_style = frame[frame["检验"] == "ne1_style_with_central_reuse_quality"]
    ne1_pivot = (
        ne1_style.groupby("coc_design")["dS_r10a"]
        .agg(["min", "median", "max", "count"])
        .reset_index()
    )

    summary = {
        "purpose": (
            "X4 修复：统一 ne1 / ne5d 口径。旧对照把「设计 CoC 不同」误当作"
            "「求解路径不同」。"
        ),
        "main_grid_coc_design": MAIN_GRID_COC,
        "main_grid_source": "examples/cawcc_r2/{ha,co}/project.json 的 "
                            "components.AI_DC1.cooling.cycles_of_concentration",
        "complete_species_samples": list(SAMPLES),
        "excluded_samples": ["AI-UWM assumption (2/5 物种，物种不完整偏置)",
                             "Figshare RW (原缺 2 物种)"],
        "test1_true_path_difference": {
            "description": (
                "同一 coc_design=5.0、同一 CENTRAL_REUSE 设定下，"
                "volume-only vs R10a 的差异——这是真正的路径差异"
            ),
            "n_scenarios": n_path,
            "n_sign_flips": n_flip_path,
            "sign_flip_fraction": (n_flip_path / n_path) if n_path else None,
            "dS_volume_only_range": [
                float(path["dS_volume_only"].min()),
                float(path["dS_volume_only"].max()),
            ],
            "dS_r10a_range": [
                float(path["dS_r10a"].min()),
                float(path["dS_r10a"].max()),
            ],
            "verdict": (
                "PATH_ROBUST" if n_flip_path == 0
                else f"PATH_CHANGES_SIGN_IN_{n_flip_path}_OF_{n_path}"
            ),
        },
        "test2_coc_sensitivity_r10a": {
            "description": "R10a 路径下扫设计 CoC，说明 ne1(3.5) 与 ne5d(5.0) 差异来源",
            "by_coc": coc_pivot.to_dict("records"),
        },
        "test3_ne1_style_with_central_reuse_quality": {
            "description": "复现 ne1 的额外设定（CENTRAL_REUSE 质量 + provenance）",
            "by_coc": ne1_pivot.to_dict("records"),
        },
        "conclusion": (
            "1) 真路径差异（同 coc=5.0）见 test1；"
            "2) ne1 与 ne5d 的差异主要来自 coc_design 与 CENTRAL_REUSE 质量设定，"
            "不是求解路径；3) 旧稿的「800×」不得作为路径差异引用。"
        ),
        "runtime_s": round(time.time() - started, 1),
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 78)
    print("X4 修复结果")
    print("=" * 78)
    print(f"主网格 coc_design = {MAIN_GRID_COC}")
    print(f"\n[检验1] 真路径差异（同 coc={MAIN_GRID_COC}）")
    print(f"  情景数 = {n_path}，符号翻转 = {n_flip_path}")
    print(f"  dS volume-only 范围 = [{path['dS_volume_only'].min():.1f}, "
          f"{path['dS_volume_only'].max():.1f}] ML")
    print(f"  dS R10a 范围        = [{path['dS_r10a'].min():.1f}, "
          f"{path['dS_r10a'].max():.1f}] ML")
    print(f"  裁定 = {summary['test1_true_path_difference']['verdict']}")

    print("\n[检验2] R10a 路径下的设计 CoC 敏感性")
    print(coc_pivot.to_string(index=False))

    print("\n[检验3] 复现 ne1 设定（含 CENTRAL_REUSE 质量）")
    print(ne1_pivot.to_string(index=False))

    print(f"\n-> {OUT_JSON}")
    print(f"-> {OUT_CSV}")


if __name__ == "__main__":
    main()
