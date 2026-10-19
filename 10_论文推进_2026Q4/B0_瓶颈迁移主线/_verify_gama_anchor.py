# -*- coding: utf-8 -*-
"""独立复算 GAMA TDS 分布与 C_p 影响表。

从 _gama_tds_statewide.json 与 _c_p_anchor_impact.json 重新推导 SI S7.10 与
中文母稿第 44 条实证补充中的每个数字，防止正文与产物脱节。

用法: python _verify_gama_anchor.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
GAMA = HERE / "_gama_tds_statewide.json"
IMPACT = HERE / "_c_p_anchor_impact.json"
SI = HERE / "05_wr_supplementary_en.md"

RES: list[tuple[str, bool, str]] = []
L, CD, CR = 2200.0, 5.0, 650.0


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def rstar(cp: float, cr: float = CR) -> float:
    return (L / CD - cp) / (cr - cp)


def main() -> None:
    if not GAMA.exists() or not IMPACT.exists():
        print("缺少产物")
        return
    g = json.loads(GAMA.read_text(encoding="utf-8"))
    im = json.loads(IMPACT.read_text(encoding="utf-8"))
    si = SI.read_text(encoding="utf-8")

    # ---- GAMA 分位数 ----
    tds = g["tds"]
    ck("TDS 记录数 = 10,090", tds["n"] == 10090, str(tds["n"]))
    for k, want in (("p5", 120), ("p25", 239), ("p50", 420), ("p75", 650), ("p95", 2100)):
        ck(f"GAMA {k} = {want}", int(tds[k]) == want, str(tds[k]))
    ck("假设值 180 位于第 14 百分位（14.1）",
       abs(g["assumed_percentile"] - 14.1) < 0.2, str(g["assumed_percentile"]))

    # ---- C_p 影响表 ----
    base = rstar(180.0)
    ck("r*(C_p=180) = 0.5532", abs(base - 0.5532) < 5e-5, f"{base:.4f}")
    cases = {
        180: (180.0, 0.5532), 420: (420.0, 0.0870), 545.5: (545.5, -1.0096),
        550: (550.0, -1.1000), 210: (210.0, 0.5227),
    }
    for cp_int, (cp, want) in cases.items():
        got = rstar(cp)
        ck(f"r*(C_p={cp_int}) = {want}", abs(got - want) < 5e-4, f"{got:.4f}")

    # ---- C_r 影响 ----
    for cr, want in ((500, 0.8125), (650, 0.5532), (800, 0.4194), (1000, 0.3171)):
        got = rstar(180.0, cr=cr)
        ck(f"r*(C_r={cr}) = {want}", abs(got - want) < 5e-4, f"{got:.4f}")

    # ---- 判定翻转 ----
    crossed_at_median = (0.444 > rstar(420.0)) and (0.499 > rstar(420.0))
    ck("C_p=420 时 Santa Clara 两口径均判为越过", crossed_at_median,
       f"r*=0.0870 vs 0.444/0.499")
    ck("C_p=545.5 时 r* < 0（进入情形 I）", rstar(545.5) < 0, f"{rstar(545.5):.4f}")
    ck("json 记录 verdict_flips = true", im.get("verdict_flips") is True,
       str(im.get("verdict_flips")))

    # ---- SI 正文含关键数字 ----
    for needle in ("10,090", "14th percentile", "420", "0.0870", "−1.0096", "Regime I"):
        ck(f"SI 含 {needle}", needle in si, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\nGAMA 锚定复算　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
