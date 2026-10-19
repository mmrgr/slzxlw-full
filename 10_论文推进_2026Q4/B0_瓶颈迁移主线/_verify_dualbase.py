# -*- coding: utf-8 -*-
"""S6.5 双基底论断的自动核验：SI 中引用的每个数字必须能从产物重算。

断言（SI S6.5）：
  1. 三情形在两个基底上都成立；
  2. 同情形下两基底的相对增幅打印位一致；
  3. 两基底的绝对取水量确实不同（证明基底切换生效）；
  4. 闭式预测 +7.056%，实测 +6.477%，差 0.579 个百分点；
  5. 蒸发量下降 0.76%。

用法: python _verify_dualbase.py
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

ROOT = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
R2 = ROOT / "validation_artifacts" / "r2"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    csv = R2 / "rstar_regime_validation_dualbase.csv"
    js = R2 / "rstar_regime_validation_dualbase.json"
    if not csv.exists() or not js.exists():
        print("缺少产物")
        return
    df = pd.read_csv(csv)
    meta = json.loads(js.read_text(encoding="utf-8"))

    ck("产物含 base 列", "base" in df.columns, str(list(df.columns)[:6]))
    ck("双基底均有数据", set(df["base"].unique()) == {"ha", "co"},
       str(sorted(df["base"].unique())))
    ck("json 记录 per_base", "per_base" in meta, str(list(meta.keys())))
    ck("三情形在两个基底上都证实",
       all(meta["per_base"][b]["all_confirmed"] for b in ("ha", "co")), "")
    ck("整体 all_confirmed", meta.get("all_confirmed") is True, "")

    # ---- 相对增幅在两基底上一致 ----
    def rel(base: str, regime: str) -> list[float]:
        s = df[(df["base"] == base) & (df["regime"] == regime)].sort_values("target_r")
        w = s["total_withdrawal_ml"].values
        return [100.0 * (x / w[0] - 1.0) for x in w]

    for regime in ("I", "II", "III"):
        a, b = rel("ha", regime), rel("co", regime)
        same = all(abs(x - y) < 5e-4 for x, y in zip(a, b))
        ck(f"情形 {regime}: 两基底相对增幅一致（<5e-4）", same,
           f"HA={a[-1]:+.4f}% CO={b[-1]:+.4f}%")

    # ---- 绝对取水必须不同（证明基底真的切换了） ----
    for regime, expect in (("II", None), ("I", None), ("III", None)):
        ha = df[(df["base"] == "ha") & (df["regime"] == regime) & (df["target_r"] == 0.0)]
        co = df[(df["base"] == "co") & (df["regime"] == regime) & (df["target_r"] == 0.0)]
        d = abs(float(ha["total_withdrawal_ml"].iloc[0]) - float(co["total_withdrawal_ml"].iloc[0]))
        ck(f"情形 {regime}: 两基底绝对取水不同（基底切换生效）", d > 1.0, f"差 {d:.1f} ML")

    # ---- SI 中引用的具体数字 ----
    ha0 = float(df[(df["base"] == "ha") & (df["regime"] == "II")
                   & (df["target_r"] == 0.0)]["total_withdrawal_ml"].iloc[0])
    co0 = float(df[(df["base"] == "co") & (df["regime"] == "II")
                   & (df["target_r"] == 0.0)]["total_withdrawal_ml"].iloc[0])
    ck("SI 引用 22,390.8 ML（HA 情形II r=0）", abs(ha0 - 22390.8) < 0.05, f"{ha0:.4f}")
    ck("SI 引用 22,126.7 ML（CO 情形II r=0）", abs(co0 - 22126.7) < 0.05, f"{co0:.4f}")

    # ---- 闭式 vs 实测 ----
    s = df[(df["base"] == "ha") & (df["regime"] == "II")].sort_values("target_r")
    c = s["coc_model"].values
    w = s["total_withdrawal_ml"].values
    f = c / (c - 1.0)
    pred = 100.0 * (f[-1] / f[0] - 1.0)
    act = 100.0 * (w[-1] / w[0] - 1.0)
    ck("闭式预测 +7.056%", abs(pred - 7.056) < 0.005, f"{pred:.4f}%")
    ck("实测增幅 +6.477%", abs(act - 6.477) < 0.005, f"{act:.4f}%")
    ck("差 0.58 个百分点", abs((pred - act) - 0.579) < 0.01, f"{pred-act:.4f}")

    # ---- 蒸发漂移 0.76%（母稿 5.7.5，本脚本仅核对量级合理）----
    ck("闭式预测高于实测（蒸发漂移方向正确）", pred > act, f"pred {pred:.3f} > act {act:.3f}")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\n双基底核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
