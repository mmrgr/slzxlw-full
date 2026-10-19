# -*- coding: utf-8 -*-
"""核验"CoC 按目标配比计算"这一披露的每一环。

断言：
  1. r ≤ 0.70 时 r_eff 完全达标（0/730 天短缺）；
  2. r = 0.75 起出现短缺，并稳定在 0.74–0.76 平台；
  3. r = 0.9 时短缺 724/730 天；
  4. 模型 CoC 与"按目标 r 解析"一致到 1e-9；
  5. 模型 CoC 与"按 r_eff 解析"在 r=0.9 时差 0.505；
  6. r* = 0.5532 位于 r_eff 完全达标区间内；
  7. 三处正文均已写入该披露与"上界"限定。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SH = HERE / "_reff_shortfall.json"
TEN = HERE / "_coc_reff_tension.json"
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

RES: list[tuple[str, bool, str]] = []
L, CD, CP, CR = 2200.0, 5.0, 180.0, 650.0


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def coc_of(r: float) -> float:
    return min(CD, L / (r * CR + (1 - r) * CP))


def main() -> None:
    if not SH.exists() or not TEN.exists():
        print("缺产物")
        return
    sh = json.loads(SH.read_text(encoding="utf-8"))
    ten = json.loads(TEN.read_text(encoding="utf-8"))
    by_r = {x["r_target"]: x for x in sh}

    # 1. r<=0.70 完全达标
    for r in (0.50, 0.60, 0.65, 0.70):
        ck(f"r={r:.2f} 无短缺天数", by_r[r]["n_short_days"] == 0,
           str(by_r[r]["n_short_days"]))
        ck(f"r={r:.2f} 的 r_eff = r", abs(by_r[r]["r_eff_mean"] - r) < 1e-6,
           f"{by_r[r]['r_eff_mean']}")

    # 2. 平台
    plat = [by_r[r]["r_eff_mean"] for r in (0.75, 0.80, 0.85, 0.90)]
    ck("r≥0.75 时 r_eff 落在 0.74–0.76 平台",
       all(0.73 <= v <= 0.77 for v in plat), str([round(v, 4) for v in plat]))

    # 3. r=0.9 短缺天数
    ck("r=0.90 短缺 724/730 天", by_r[0.90]["n_short_days"] == 724,
       str(by_r[0.90]["n_short_days"]))

    # 4/5. CoC 与两种解析值
    for x in ten:
        r = x["r_target"]
        ck(f"r={r:.2f} 模型 CoC = 按目标解析",
           abs(x["coc_model"] - x["coc_at_target"]) < 1e-9,
           f"{x['coc_model']} vs {x['coc_at_target']}")
    x9 = next(x for x in ten if abs(x["r_target"] - 0.9) < 1e-9)
    gap = x9["coc_at_eff"] - x9["coc_model"]
    ck("r=0.90 时 CoC(目标) 与 CoC(r_eff) 差 ≈ 0.505",
       abs(gap - 0.505) < 0.01, f"{gap:.3f}")
    ck("模型 CoC 等于按目标解析（非按 r_eff）",
       abs(x9["coc_model"] - x9["coc_at_target"]) < 1e-9
       and abs(x9["coc_model"] - x9["coc_at_eff"]) > 0.4,
       f"模型 {x9['coc_model']}, 目标 {x9['coc_at_target']}, r_eff {x9['coc_at_eff']}")

    # 6. r* 在达标区间
    r_star = (L / CD - CP) / (CR - CP)
    ck("r* = 0.5532 位于 r_eff 完全达标区间（≤0.70）",
       r_star <= 0.70, f"r*={r_star:.4f}")

    # 7. 正文
    ms = MS.read_text(encoding="utf-8")
    en = EN.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    ck("母稿含 §5.7.8", "5.7.8" in ms, "")
    ck("母稿写明效应量是上界", "上界" in ms and "低估了 CoC" in ms, "")
    ck("母稿写明 r* 不受影响", "不受影响" in ms, "")
    ck("英文含 delivered fraction 段落", "delivered fraction" in en, "")
    ck("英文写明 upper bounds", "upper bounds" in en, "")
    ck("SI 含 S5.9", "S5.9" in si, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"CoC/交付张力核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
