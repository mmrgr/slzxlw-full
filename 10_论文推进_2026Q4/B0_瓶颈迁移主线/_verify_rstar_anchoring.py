# -*- coding: utf-8 -*-
"""独立核验 r* 四参数的锚定状态与敏感性数字。

与 _rstar_param_anchoring.py（生成器）分工：本脚本从 project.json 与
parameter_envelope_R7.csv 重新读取并断言，防止正文与产物脱节。

用法: python _verify_rstar_anchoring.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
PROJ_HA = (PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "examples"
           / "cawcc_r2" / "ha" / "project.json")

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    env = pd.read_csv(R2 / "parameter_envelope_R7.csv", encoding="utf-8-sig")
    paths = set(env["参数路径"].astype(str))

    proj = json.loads(PROJ_HA.read_text(encoding="utf-8"))
    dc = next(v for v in proj["components"].values() if v.get("kind") == "data_center")
    L = float(dc["cooling"]["water_quality_limits"]["TDS"])
    CD = float(dc["cooling"]["cycles_of_concentration"])
    CP = float(dc["water_sources"]["potable"]["quality"]["TDS"])
    CR = float(dc["water_sources"]["reclaimed"]["quality"]["TDS"])

    ck("参数包络表共 54 行", len(env) == 54, str(len(env)))
    ck("L = 2200", L == 2200.0, str(L))
    ck("CoC_d = 5.0", CD == 5.0, str(CD))
    ck("C_p = 180", CP == 180.0, str(CP))
    ck("C_r = 650", CR == 650.0, str(CR))

    # ---- 锚定状态 ----
    p_coc = "components.AI_DC1.cooling.cycles_of_concentration"
    p_l = "components.AI_DC1.cooling.water_quality_limits.TDS"
    p_cp = "components.AI_DC1.water_sources.potable.quality.TDS"
    p_cr = "components.AI_DC1.water_sources.reclaimed.quality.TDS"

    ck("CoC_d 在包络表内", p_coc in paths, p_coc)
    ck("L 不在包络表内（缺口）", p_l not in paths, p_l)
    ck("C_p 不在包络表内（缺口）", p_cp not in paths, p_cp)
    ck("C_r 不在包络表内（缺口）", p_cr not in paths, p_cr)

    row = env[env["参数路径"].astype(str) == p_coc].iloc[0]
    ck("CoC_d 标注为『无锚点』", str(row["是否落在包络内"]) == "无锚点",
       str(row["是否落在包络内"]))

    n_in = sum(1 for p in (p_l, p_coc, p_cp, p_cr) if p in paths)
    ck("四参数中仅 1 个在包络表内", n_in == 1, f"{n_in}/4")

    anchored = sum(
        1 for p in (p_l, p_coc, p_cp, p_cr)
        if p in paths and str(env[env["参数路径"].astype(str) == p].iloc[0]["是否落在包络内"])
        in ("是", "边界命中")
    )
    ck("四参数中实际有锚点者 = 0", anchored == 0, f"{anchored}/4")

    # ---- 敏感性数字 ----
    def rstar(l=L, cd=CD, cp=CP, cr=CR):
        return (l / cd - cp) / (cr - cp)

    base = rstar()
    ck("r* = 0.5532", abs(base - 0.5532) < 5e-5, f"{base:.4f}")

    expect = {
        "L": ("l", 0.0936, 0.1872),
        "CoC_d": ("cd", 0.1040, 0.1891),
        "C_r": ("cr", 0.0888, 0.1560),
        "C_p": ("cp", 0.0178, 0.0343),
    }
    for name, (kw, maxdev_e, span_e) in expect.items():
        args = {"l": L, "cd": CD, "cp": CP, "cr": CR}
        lo = dict(args); lo[kw] = args[kw] * 0.9
        hi = dict(args); hi[kw] = args[kw] * 1.1
        r_lo, r_hi = rstar(**lo), rstar(**hi)
        span = abs(r_hi - r_lo)
        maxdev = max(abs(r_lo - base), abs(r_hi - base))
        ok = abs(maxdev - maxdev_e) < 5e-4 and abs(span - span_e) < 5e-4
        ck(f"{name} ±10%: 最大偏移 {maxdev_e}, 跨度 {span_e}", ok,
           f"复算 {maxdev:.4f} / {span:.4f}")

    # ---- 区间 0.46-0.66 ----
    # 单参数 ±10% 能达到的最低 r* 与最高 r*：
    #   最低来自 L×0.9（0.4596）；最高来自 CoC_d×0.9（0.6572，因 CoC_d 在分母）
    lo_all = min(rstar(l=L * 0.9), rstar(cd=CD * 0.9), rstar(cr=CR * 0.9))
    hi_all = max(rstar(l=L * 1.1), rstar(cd=CD * 0.9), rstar(cr=CR * 0.9),
                 rstar(cp=CP * 1.1))
    ck("单参数 ±10% 可把 r* 推入约 0.46–0.66", abs(lo_all - 0.4596) < 1e-3
       and abs(hi_all - 0.6572) < 1e-3, f"[{lo_all:.4f}, {hi_all:.4f}]")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\nr* 锚定与敏感性核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
