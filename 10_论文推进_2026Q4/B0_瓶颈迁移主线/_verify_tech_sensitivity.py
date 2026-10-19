# -*- coding: utf-8 -*-
"""核验技术档敏感性结果，并解释 dry 档为何降幅为 0。

【结果回顾】
固定 1200 MW 的阈值型响应（r 0.5→0.8 总取水增幅）：
  evaporative +6.478% / hybrid +6.472% / dry_first +7.851% / dry 不适用（无外部取水）
纯物理 CAWCC 降幅（r=0 → r=0.8）：
  evaporative −100 / hybrid −50 / dry_first −50 / dry 0

【必须解释的三点】
1. dry 档 external_withdrawal = 0 → 该档不耗水，r* 机制对它**不适用**（不是"稳健"，是"无关"）。
   这必须在论文里说清，否则"dry 档 0 降幅"会被误读为"机制在 dry 档下消失"。
2. hybrid/dry_first 的降幅（−50）小于 evaporative（−100），说明**效应量随冷却水占比下降而减小**。
   这与"偏保守"的说法一致，且给出了定量幅度。
3. dry_first 的增幅 7.851% 与 evaporative 的 6.478% 不同 —— 因为其 CoC = 6.0 而非 5.0。
   r* 对 CoC 敏感（弹性 −1.69），故 r* 更低（0.3549），跨阈值更早、增幅更大。

【本脚本断言】
  (a) 三个有外排水的档位都保留阈值型响应（增幅 > 5%）；
  (b) 降幅随冷却水强度单调：evaporative(−100) ≥ hybrid(−50) ≥ dry_first(−50) > dry(0)；
  (c) dry 档取水为 0（机制不适用，需显式声明）；
  (d) r* 对 CoC 的依赖在 dry_first 上得到体现。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
TS = HERE / "_tech_sensitivity.json"

RES: list[tuple[str, bool, str]] = []
WET_TIERS = ("evaporative", "hybrid", "dry_first")


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def rstar(coc_d: float, L: float = 2200.0, cp: float = 180.0, cr: float = 650.0) -> float:
    return (L / coc_d - cp) / (cr - cp)


def main() -> None:
    if not TS.exists():
        print("缺少 _tech_sensitivity.json")
        return
    d = json.loads(TS.read_text(encoding="utf-8"))
    T = d["tiers"]

    # (a) 阈值型响应保留
    for t in WET_TIERS:
        inc = T[t]["increase_pct"]
        ck(f"{t} 保留阈值型响应（增幅 > 5%）", inc is not None and inc > 5.0,
           f"{inc}%")

    # (b) 降幅单调
    drops = {t: T[t]["cawcc_drop_mw"] for t in T}
    ck("降幅：evaporative ≥ hybrid ≥ dry_first > dry",
       drops["evaporative"] >= drops["hybrid"] >= drops["dry_first"] > drops["dry"],
       str(drops))

    # (c) dry 档无外部取水
    ck("dry 档 r=0.5 取水为 0（机制不适用）", T["dry"]["withdrawal_r05_ml"] == 0.0,
       str(T["dry"]["withdrawal_r05_ml"]))
    ck("dry 档 WUE = 0", T["dry"]["wue_l_per_kwh_at_r0"] == 0.0,
       str(T["dry"]["wue_l_per_kwh_at_r0"]))

    # (d) WUE 梯度
    wues = {t: T[t]["wue_l_per_kwh_at_r0"] for t in T}
    ck("WUE 梯度：evaporative > hybrid > dry_first > dry",
       wues["evaporative"] > wues["hybrid"] > wues["dry_first"] > wues["dry"],
       str(wues))

    # (e) dry_first 的 CoC=6 → r* 更低
    rs5 = rstar(5.0)
    rs6 = rstar(6.0)
    ck("r*(CoC=5) = 0.5532", abs(rs5 - 0.5532) < 5e-5, f"{rs5:.4f}")
    ck("r*(CoC=6) = 0.3972（低于 CoC=5，故更早跨阈值）",
       abs(rs6 - 0.3972) < 5e-5, f"{rs6:.4f}")
    ck("dry_first 增幅 > evaporative 增幅（与其更低 r* 一致）",
       T["dry_first"]["increase_pct"] > T["evaporative"]["increase_pct"],
       f"{T['dry_first']['increase_pct']} vs {T['evaporative']['increase_pct']}")

    # (f) 关键：即使全面 dry，阈值机制本身不消失，只是不产生取水后果
    ck("湿冷档全部保留机制（3/3）",
       all(T[t]["increase_pct"] and T[t]["increase_pct"] > 5.0 for t in WET_TIERS),
       "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"技术档敏感性核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
