"""预注册自查：单域内再生水比例 0→0.9 连续扫描。

为什么必须做这一项
------------------
00_项目说明.md §七 记载的 CoC 机制主张是：

    提高再生水比例 → 混合 TDS 升高 → CoC 被水质上限内生压低 →
    每单位散热取水量上升、排入市政下水道量上升

但该主张目前的证据只有**跨域比较**（D-HA 与 D-CO 两个端点各一个再生水比例）。
域间除再生水比例外还在气候、水资源禀赋、城市需水结构上一并不同，因此
"两个点"无法把机制与端点差异分离。已预注册：把该机制写成论文主张之前，
必须补做**单域内、其余条件全部固定**的连续扫描。

本脚本即为该项自查。做法：只改 AI_DC1 的 `water_sources.reclaimed.target_fraction`
（potable 取 1−x），其余配置、容量、时间序列一律不变，在单一域内连续取值。

判定标准（事前写明，避免事后挑结论）
------------------------------------
机制成立需同时满足：
  (1) CoC 随再生水比例单调不增；
  (2) 每单位散热取水量随再生水比例单调不减；
  (3) 排入下水道量（return_flow）随再生水比例单调不减。

质量耦合审计的冷却储水显式关闭（容量和初始库存均为 0）。模型尚未保存
冷却储水的水质状态；保留储水会把求解器的当日过程补水份额与实际进入冷却
回路的混合水质混在一起，因此不作为本轮 R8 机制证据。
若任一条不成立，则 §七 的机制主张不得作为论文结论，只能保留为"两域端点差异"。

用法
----
    PYTHONPATH=src python scripts/build_reclaimed_fraction_sweep_R8.py
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd

from aiuwm.full_engine import FullAIUWMModel

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "examples" / "cawcc_r2"
ART = ROOT / "validation_artifacts" / "r2"
ART.mkdir(parents=True, exist_ok=True)

SWEEP = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
CAP_MW = 1000.0
DOMAINS = (("ha", "D-HA"), ("co", "D-CO"))


def run_one(proj: dict, ts: pd.DataFrame, reclaimed_target: float) -> dict:
    trial = copy.deepcopy(proj)
    dc = trial["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = CAP_MW
    dc["cooling_storage_ml"] = 0.0
    dc["initial_cooling_storage_ml"] = 0.0
    ws = dc["water_sources"]
    ws["reclaimed"]["target_fraction"] = reclaimed_target
    ws["potable"]["target_fraction"] = 1.0 - reclaimed_target
    d = FullAIUWMModel(trial, ts).run().data_center_daily
    heat = float(d["cooling_heat_mwh_th"].sum())
    withdrawal = float(d["external_withdrawal_ml"].sum())
    blowdown = float(d["blowdown_ml"].sum())
    return_flow = float(d["return_flow_ml"].sum())
    consumption = float(d["consumption_ml"].sum())
    return {
        "目标再生水比例": reclaimed_target,
        # 体积加权实际份额；逐日比例的算术平均会在负荷随天气变化时产生口径偏差。
        "实际再生水比例": (
            float(d["reclaimed_water_ml"].sum()) / float(d["external_withdrawal_ml"].sum())
            if float(d["external_withdrawal_ml"].sum()) else 0.0
        ),
        "均值CoC": float(d["cycles_of_concentration"].mean()),
        "水质触顶回退天数": int(d["quality_coc_fallback"].sum()),
        "场址WUE_L每kWh": float(d["wue_l_kwh"].mean()),
        "取水量_ML": withdrawal,
        "每单位散热取水_ML每MWh": withdrawal / heat if heat else float("nan"),
        "排浓水量_ML": blowdown,
        "排入下水道量_ML": return_flow,
        "耗水量_ML": consumption,
    }


def monotone_nonincreasing(values: list[float], tol: float = 1e-9) -> bool:
    return all(b <= a + tol for a, b in zip(values, values[1:]))


def monotone_nondecreasing(values: list[float], tol: float = 1e-9) -> bool:
    return all(b >= a - tol for a, b in zip(values, values[1:]))


def main() -> int:
    rows = []
    verdicts = []
    for dom, label in DOMAINS:
        proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
        ts = pd.read_csv(R2 / dom / "timeseries.csv")
        series = [run_one(proj, ts, x) for x in SWEEP]
        for s in series:
            rows.append({"域签": label, **s})

        coc = [s["均值CoC"] for s in series]
        per_heat = [s["每单位散热取水_ML每MWh"] for s in series]
        sewer = [s["排入下水道量_ML"] for s in series]
        concentrate = [s["排浓水量_ML"] for s in series]
        c1 = monotone_nonincreasing(coc)
        c2 = monotone_nondecreasing(per_heat)
        c3 = monotone_nondecreasing(sewer)

        def pct(a: float, b: float) -> float:
            return (b / a - 1.0) * 100.0 if a else float("nan")

        verdicts.append({
            "域签": label,
            "CoC单调不增": "是" if c1 else "否",
            "每单位散热取水单调不减": "是" if c2 else "否",
            "排入下水道量单调不减": "是" if c3 else "否",
            "CoC_0到0.9变化": f"{coc[0]:.4f} → {coc[-1]:.4f}（{pct(coc[0], coc[-1]):+.2f}%）",
            "取水_0到0.9变化": f"{per_heat[0]:.6f} → {per_heat[-1]:.6f}（{pct(per_heat[0], per_heat[-1]):+.2f}%）",
            "排浓_0到0.9变化": f"{concentrate[0]:.1f} → {concentrate[-1]:.1f}（{pct(concentrate[0], concentrate[-1]):+.2f}%）",
            "排入下水道_0到0.9变化": f"{sewer[0]:.1f} → {sewer[-1]:.1f}（{pct(sewer[0], sewer[-1]):+.2f}%）",
            "机制判定": "成立" if (c1 and c2 and c3) else "不成立",
        })
        print(f"[{label}] CoC {coc[0]:.4f}→{coc[-1]:.4f}  取水/热 {pct(per_heat[0], per_heat[-1]):+.2f}%  "
              f"排入下水道 {pct(sewer[0], sewer[-1]):+.2f}%  "
              f"单调性 {int(c1)}{int(c2)}{int(c3)}")

    out = pd.DataFrame(rows)
    out.to_csv(ART / "reclaimed_fraction_sweep_R8.csv", index=False, encoding="utf-8-sig")
    ver = pd.DataFrame(verdicts)
    ver.to_csv(ART / "reclaimed_fraction_sweep_verdict_R8.csv", index=False, encoding="utf-8-sig")

    print(f"\n[OK] {ART / 'reclaimed_fraction_sweep_R8.csv'}  rows={len(out)}")
    print(f"[OK] {ART / 'reclaimed_fraction_sweep_verdict_R8.csv'}  rows={len(ver)}")
    with pd.option_context("display.width", 260, "display.max_columns", 20,
                           "display.max_colwidth", 40):
        print("\n" + ver.to_string(index=False))

    failed = ver[ver["机制判定"] == "不成立"]
    print("\n=== 预注册自查判定 ===")
    if len(failed):
        print("[FAIL] 单域连续扫描未支持该机制，§七 的 CoC 机制主张不得写成论文结论")
        return 1
    print("[PASS] 固定点值、零冷却储水的两个合成域中，三项单调性检查均通过；这不检验参数不确定性或现实外部有效性")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
