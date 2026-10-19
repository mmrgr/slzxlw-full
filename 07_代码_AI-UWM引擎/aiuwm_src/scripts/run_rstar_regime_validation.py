# -*- coding: utf-8 -*-
"""验证 r* 分类学：三种情形在模型里是否表现为三种定性不同的行为。

【为什么必须做实证】
`run_rstar_regime_map.py` 从解析式推出四种情形（I/II/III/IV），并声称它们对应
"任何替代都有代价 / 存在政策阈值 / 替代永远无代价 / 问题消失"。

这是**解析推论**，必须用模型验证。若模型行为与解析分类不符，则分类学不成立。

【设计】
以 D-HA 或 D-CO 为基底，只改 cooling.cycles_of_concentration（控制 L/CoC_design）：
  - 情形 II（标称）：CoC_design = 5   → L/CoC_d = 440，C_p=180, C_r=650 → r*=0.5532
  - 情形 I：       CoC_design = 15  → L/CoC_d = 146.7 ≤ C_p=180 → r*<0
  - 情形 III：     需 L/CoC_d ≥ C_r=650，即 CoC_design ≤ 2200/650 = 3.385
                   取 CoC_design = 2.5 → L/CoC_d = 880 > 650 → r*>1

每个情形扫 r ∈ {0.0, 0.2, 0.4, 0.6, 0.8}，固定容量 800 MW，提取 CoC 与总取水。

【判据（预测，须被数据证实）】
  情形 I：  r=0 时 CoC 已由水质决定（< CoC_design）；
            r 增大 → CoC 立即单调下降 → 总取水单调上升（任何替代都有代价）
  情形 II： r ≤ r* 时 CoC ≡ CoC_design（恒定）→ 总取水恒定；
            r > r* 后 CoC 下降 → 总取水上升（阈值型）
  情形 III：r ≤ 1 时 CoC ≡ CoC_design（恒定）→ 总取水恒定（永不反噬）

【2026-10-18 扩展：双基底】
原版只跑 D-HA 基底，被登记为一项局限（"未做 D-CO 基底或容量维度的重复"）。
两个基底的水质参数完全相同（L=2200/chloride=500；C_p=180、C_r=650；CoC_d=5），
故解析 r* 相同，但气候驱动与设施参数不同。若三情形的定性行为在两个基底上都成立，
则分类学的实证基础从"单基底抽样"升级为"双基底抽样"（仍非全网格确认）。

【产物】
  rstar_regime_validation.csv         （含 base 列）
  rstar_regime_validation.json

【用法】PYTHONPATH="src;scripts" python scripts/run_rstar_regime_validation.py
        PYTHONPATH="src;scripts" python scripts/run_rstar_regime_validation.py --bases ha,co
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.ai_metrics import summarize_ai_water_kpis  # noqa: E402
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

CAPACITY = 800.0
R_GRID = [0.0, 0.2, 0.4, 0.6, 0.8]

# 情形定义：(代码, CoC_design, 说明)
REGIMES = [
    ("II", 5.0, "标称：L/CoC_d=440，介于 C_p=180 与 C_r=650 之间"),
    ("I", 15.0, "L/CoC_d=146.7 ≤ C_p=180，水质恒紧"),
    ("III", 2.5, "L/CoC_d=880 ≥ C_r=650，水质永不紧"),
]

L_LIMIT = 2200.0
C_P = 180.0
C_R = 650.0

DEFAULT_BASES = ["ha"]


def parse_bases(argv: list[str]) -> list[str]:
    for i, a in enumerate(argv):
        if a == "--bases" and i + 1 < len(argv):
            return [b.strip().lower() for b in argv[i + 1].split(",") if b.strip()]
        if a.startswith("--bases="):
            return [b.strip().lower() for b in a.split("=", 1)[1].split(",") if b.strip()]
    return DEFAULT_BASES


def analytic_coc(r: float, coc_design: float) -> float:
    c_mix = r * C_R + (1.0 - r) * C_P
    return min(coc_design, L_LIMIT / c_mix)


def analytic_rstar(coc_design: float) -> float:
    return (L_LIMIT / coc_design - C_P) / (C_R - C_P)


def run_base(base: str) -> list[dict]:
    """跑一个基底上的三种情形 × 五个 r 点。"""
    project0 = json.loads((R2 / base / "project.json").read_text(encoding="utf-8"))
    timeseries = pd.read_csv(R2 / base / "timeseries.csv")

    rows: list[dict] = []
    for code, coc_design, note in REGIMES:
        r_star = analytic_rstar(coc_design)
        print(f"\n{'='*78}")
        print(f"[{base.upper()}] 情形 {code}: CoC_design = {coc_design}  "
              f"→  L/CoC_d = {L_LIMIT/coc_design:.1f}  →  r* = {r_star:.4f}")
        print(f"{'='*78}")
        for r in R_GRID:
            cfg = json.loads(json.dumps(project0))
            for comp in cfg["components"].values():
                if comp.get("kind") != "data_center":
                    continue
                comp["installed_it_capacity_mw"] = CAPACITY
                comp.pop("capacity_schedule", None)
                comp["cooling"]["cycles_of_concentration"] = coc_design
                src = comp.get("water_sources", {})
                if "reclaimed" in src:
                    src["reclaimed"]["target_fraction"] = float(r)
                if "potable" in src:
                    src["potable"]["target_fraction"] = float(1.0 - r)

            result = FullAIUWMModel(cfg, timeseries).run()
            daily = result.data_center_daily
            kpi = summarize_ai_water_kpis(result, cfg)

            coc_col = next((c for c in daily.columns if "cycles_of_concentration" in c.lower()), None)
            coc = float(pd.to_numeric(daily[coc_col], errors="coerce").mean()) if coc_col else float("nan")
            fb_col = next((c for c in daily.columns if "quality_coc_fallback" in c.lower()), None)
            fallback = int(pd.to_numeric(daily[fb_col], errors="coerce").fillna(0).sum()) if fb_col else -1

            rows.append({
                "base": base,
                "regime": code,
                "coc_design": coc_design,
                "r_star_analytic": r_star,
                "target_r": r,
                "coc_model": coc,
                "coc_analytic": analytic_coc(r, coc_design),
                "coc_equal_design": bool(abs(coc - coc_design) < 1e-6),
                "total_withdrawal_ml": kpi.get("total_withdrawal_ml"),
                "freshwater_withdrawal_ml": kpi.get("freshwater_withdrawal_ml"),
                "reclaimed_use_ml": kpi.get("reclaimed_water_use_ml"),
                "coc_fallback_days": fallback,
            })
            print(f"  r={r:.1f}  CoC_model={coc:8.4f}  CoC_analytic={analytic_coc(r, coc_design):8.4f}  "
                  f"总取水={kpi.get('total_withdrawal_ml'):10.1f}  "
                  f"CoC==设计值: {abs(coc - coc_design) < 1e-6}")
    return rows


def judge(df: pd.DataFrame, base: str) -> dict:
    """对一个基底的三情形做定性判定。"""
    print("\n" + "=" * 84)
    print(f"判定 [{base.upper()}]：三种情形是否表现为三种定性行为")
    print("=" * 84)

    verdicts = {}
    for code in ("I", "II", "III"):
        sub = df[(df["regime"] == code)].sort_values("target_r")
        base_w = float(sub.iloc[0]["total_withdrawal_ml"])
        increases = [
            100.0 * (float(x["total_withdrawal_ml"]) / base_w - 1.0)
            for _, x in sub.iterrows()
        ]
        equal_design = list(sub["coc_equal_design"])

        print(f"\n情形 {code}  (r*={sub.iloc[0]['r_star_analytic']:.4f})")
        print(f"  总取水相对 r=0 的增幅: " +
              ", ".join(f"r={x['target_r']:.1f}:{y:+.2f}%"
                        for (_, x), y in zip(sub.iterrows(), increases)))
        print(f"  CoC == 设计值的点: {sum(equal_design)}/{len(equal_design)}")

        if code == "I":
            ok = increases[1] > 0.01
            verdicts["I"] = {
                "prediction": "任何替代都有代价（r>0 立即推高取水）",
                "first_increase_pct": increases[1],
                "confirmed": bool(ok),
            }
            print(f"  → 预测「{verdicts['I']['prediction']}」: "
                  f"{'✅ 证实' if ok else '❌ 否证'}（首个非零 r 增幅 {increases[1]:+.3f}%）")

        elif code == "II":
            flat = [bool(e) for e in equal_design]
            n_flat = sum(1 for f in flat if f)
            ok = n_flat >= 2 and increases[-1] > increases[0]
            verdicts["II"] = {
                "prediction": "阈值型（r≤r* 平坦，r>r* 上升）",
                "n_flat_points": n_flat,
                "max_increase_pct": max(increases),
                "confirmed": bool(ok),
            }
            print(f"  → 预测「阈值型」: {'✅ 证实' if ok else '❌ 否证'}"
                  f"（{n_flat} 个点 CoC 恰为设计值，末端增幅 {max(increases):+.2f}%）")

        else:  # III
            ok = all(equal_design) and max(abs(v) for v in increases) < 1e-6
            verdicts["III"] = {
                "prediction": "替代永远无代价（取水与 r 无关）",
                "max_abs_increase_pct": max(abs(v) for v in increases),
                "confirmed": bool(ok),
            }
            print(f"  → 预测「替代永远无代价」: {'✅ 证实' if ok else '❌ 否证'}"
                  f"（最大 |增幅| {max(abs(v) for v in increases):.2e}%）")

    all_ok = all(v["confirmed"] for v in verdicts.values())
    print("\n" + "-" * 84)
    print(f"[{base.upper()}] 分类学判定: {'✅ 三情形全部证实' if all_ok else '❌ 存在否证项'}")
    return {"verdicts": verdicts, "all_confirmed": bool(all_ok)}


def main() -> None:
    bases = parse_bases(sys.argv[1:])
    print(f"基底: {bases}")

    rows: list[dict] = []
    for base in bases:
        rows.extend(run_base(base))

    df = pd.DataFrame(rows)

    # 【向后兼容】单基底（默认 ha）仍写回原文件名与**原列结构**：
    #   既有核验脚本 _verify_regime_numbers.py / _verify_abstract_numbers.py 按此文件的
    #   首行与列名取基线，若把双基底混入同一个文件会破坏它们的隐含假设。
    # 多基底结果另存 _dualbase 后缀文件，避免污染主产物。
    if bases == DEFAULT_BASES:
        out_df = df.drop(columns=["base"])
        out_csv = OUT / "rstar_regime_validation.csv"
        out_json = OUT / "rstar_regime_validation.json"
    else:
        out_df = df
        out_csv = OUT / "rstar_regime_validation_dualbase.csv"
        out_json = OUT / "rstar_regime_validation_dualbase.json"

    out_df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    per_base = {b: judge(df[df["base"] == b], b) for b in bases}
    all_ok = all(v["all_confirmed"] for v in per_base.values())

    if len(bases) > 1:
        print("\n" + "=" * 84)
        print("跨基底一致性")
        print("=" * 84)
        for code in ("I", "II", "III"):
            oks = [per_base[b]["verdicts"][code]["confirmed"] for b in bases]
            print(f"  情形 {code}: " + ", ".join(
                f"{b.upper()}={'✅' if per_base[b]['verdicts'][code]['confirmed'] else '❌'}"
                for b in bases))

    out = {
        "bases": bases,
        "capacity_mw": CAPACITY,
        "r_grid": R_GRID,
        "params": {"L": L_LIMIT, "c_potable": C_P, "c_reclaimed": C_R},
        "per_base": per_base,
        "all_confirmed": bool(all_ok),
    }
    # 单基底时保持原 json 结构（顶层 verdicts），供既有核验脚本按老键名读取
    if bases == DEFAULT_BASES:
        out = {
            "capacity_mw": CAPACITY,
            "r_grid": R_GRID,
            "params": {"L": L_LIMIT, "c_potable": C_P, "c_reclaimed": C_R},
            "verdicts": per_base[DEFAULT_BASES[0]]["verdicts"],
            "all_confirmed": bool(all_ok),
            # 双基底扩展信息，不影响老键
            "per_base": per_base,
            "bases": bases,
        }
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物: {out_csv.name} / {out_json.name}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
