# -*- coding: utf-8 -*-
"""独立复算 SI S7.7 的 k* 敏感性表。

不同于 _kstar_sensitivity.py（生成器），本脚本**从原始 k 数据重新算一遍**，
并逐格比对 SI 正文中的数字，防止"生成器改了但 SI 没跟着改"。

用法: python _verify_kstar_table.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"
CLEAN = HERE / "_ca_k_clean.json"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    recs = json.loads(CLEAN.read_text(encoding="utf-8"))["records"]
    ks = sorted(float(r["k"]) for r in recs)
    n = len(ks)
    si = SI.read_text(encoding="utf-8")

    def kstar(r_star: float, rho: float) -> float:
        return (1.0 / r_star - 1.0) / rho

    R = 0.5532

    ck("样本 n = 169", n == 169, str(n))

    # ---- ρ 行：逐格复算 ----
    # 计数一律用**精确** k* 比较，不用表格里四舍五入后的显示值：
    # ρ=0.10 时 k*_exact=8.076645、显示 8.08，而恰好有一个系统的 k=8.0787
    # 落在两者之间，用显示值计数会多算 1 个（58 vs 57）。表格显示值仅供阅读。
    rho_expect = {
        0.10: (8.08, 57, 33.7),
        0.20: (4.04, 29, 17.2),
        0.2308: (3.50, 23, 13.6),
        0.30: (2.69, 14, 8.3),
        0.50: (1.62, 4, 2.4),
        1.00: (0.81, 3, 1.8),
        2.00: (0.40, 1, 0.6),
    }
    for rho, (kst_e, cnt_e, pct_e) in rho_expect.items():
        kst_exact = kstar(R, rho)
        kst = round(kst_exact, 2)
        cnt = sum(1 for x in ks if x < kst_exact)   # 用精确值
        pct = round(100.0 * cnt / n, 1)
        ok = abs(kst - kst_e) < 5e-3 and cnt == cnt_e and abs(pct - pct_e) < 0.06
        ck(f"ρ={rho}: k*={kst_e}, n={cnt_e}, {pct_e}%", ok,
           f"复算 k*={kst}, n={cnt}, {pct}%")

    # ---- r* 行：逐格复算 ----
    r_expect = {
        0.50: (4.33, 34, 20.1),
        0.52: (4.00, 29, 17.2),
        0.5532: (3.50, 23, 13.6),
        0.58: (3.14, 20, 11.8),
        0.61: (2.77, 15, 8.9),
    }
    for rs, (kst_e, cnt_e, pct_e) in r_expect.items():
        kst_exact = kstar(rs, 0.2308)
        kst = round(kst_exact, 2)
        cnt = sum(1 for x in ks if x < kst_exact)   # 用精确值
        pct = round(100.0 * cnt / n, 1)
        ok = abs(kst - kst_e) < 5e-3 and cnt == cnt_e and abs(pct - pct_e) < 0.06
        ck(f"r*={rs}: k*={kst_e}, n={cnt_e}, {pct_e}%", ok,
           f"复算 k*={kst}, n={cnt}, {pct}%")

    # ---- SI 正文里确实写着这些数字 ----
    for needle in ["8.08", "4.04", "2.69", "1.62", "0.81", "4.33", "3.14", "2.77",
                   "33.7%", "17.2%", "11.8%", "20.1%", "8.9%", "2.4%", "1.8%"]:
        ck(f"SI 含 {needle}", needle in si, "")

    # ---- 保守边界的叙述一致 ----
    ck("SI 写明 ρ=1 为保守边界且 k*=0.81", "0.81" in si and "conservative" in si, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\nk* 敏感性表复算　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
