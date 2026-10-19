# -*- coding: utf-8 -*-
"""从 UWMP 原始 PDF 逐数字核验论文 §5.9 引用的 Santa Clara 水量数据。

【修正说明 2026-10-19】
初版脚本用 r = R/(P+R) 计算，得 0.156/0.187，与论文 0.444/0.499 不符——
错的是脚本，不是论文。论文的 r 是**园区配比**，公式为
    r = 1/(1 + (6/26)·k),  k = P/R
其中 6/26 是数据中心占全市自来水/再生水的份额比。已改用正确公式。

另：38,666 与 32,649 经核对**不是** UWMP 原文数字（原文写 "about 38,700"），
它们是四项/三项之和，属推算值。本脚本按此口径断言。
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import fitz
except ImportError:
    print("需要 pymupdf")
    sys.exit(1)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PDF = Path(r"C:/Users/mmrgr/Desktop/000/2025 Urban Water Management Plan_Final.pdf")

RES: list[tuple[str, bool, str]] = []
RHO = 6.0 / 26.0


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    doc = fitz.open(PDF)
    pages = [doc[i].get_text().replace(",", "") for i in range(doc.page_count)]
    alltext = "".join(pages)

    # ---- 原文确切出现的数字 ----
    print("=== 原文数字核对 ===")
    for n, expect_pages in (("5041", [65, 66]), ("4560", [65, 66]),
                            ("23048", [65, 66]), ("6017", [65, 66]),
                            ("16857", [35]), ("3871", [35]), ("20728", [35])):
        found = n in alltext
        where = [i + 1 for i, t in enumerate(pages) if n in t][:5]
        ck(f"UWMP 含 {int(n):,}", found, f"PDF 页 {where}")
        print(f"  {int(n):>7}: {'✅' if found else '❌'}  页 {where}")

    # ---- "about 38,700" 原文 ----
    t65 = doc[64].get_text()
    has_about = "38,700" in t65 or "38,700" in t65.replace(",", "")
    ck("p.65 原文写 about 38,700", has_about, "about 38,700 AFY")
    print(f"  p.65 'about 38,700': {'✅' if has_about else '❌'}")

    # ---- 38,666 / 32,649 应为推算值（不在 p.65 原文）----
    p65_decomma = pages[64]
    ck("38,666 不在 p.65（属推算）", "38666" not in p65_decomma, "p.65 无该串")
    ck("32,649 不在 p.65（属推算）", "32649" not in p65_decomma, "p.65 无该串")
    print(f"  38666 不在 p.65: {'✅' if '38666' not in p65_decomma else '❌'}")
    print(f"  32649 不在 p.65: {'✅' if '32649' not in p65_decomma else '❌'}")

    # ---- 反算 ----
    print("\n=== 反算（用正确公式 r = 1/(1+(6/26)k)）===")
    sup = 5041 + 4560 + 23048 + 6017
    ck("四源之和 = 38,666", sup == 38666, str(sup))
    pot_a = 5041 + 4560 + 23048
    ck("potable 三项之和 = 32,649", pot_a == 32649, str(pot_a))

    k_a = pot_a / 6017
    r_a = 1.0 / (1.0 + RHO * k_a)
    print(f"  A: k={k_a:.3f}  r={r_a:.4f}（论文 5.43 / 0.444）")
    ck("A 口径 k ≈ 5.43", abs(k_a - 5.43) < 0.01, f"{k_a:.3f}")
    ck("A 口径 r ≈ 0.444", abs(r_a - 0.444) < 0.002, f"{r_a:.4f}")

    pot_b, rec_b = 16857, 3871
    k_b = pot_b / rec_b
    r_b = 1.0 / (1.0 + RHO * k_b)
    print(f"  B: k={k_b:.3f}  r={r_b:.4f}（论文 4.35 / 0.499）")
    ck("B 口径 k ≈ 4.35", abs(k_b - 4.35) < 0.01, f"{k_b:.3f}")
    ck("B 口径 r ≈ 0.499", abs(r_b - 0.499) < 0.002, f"{r_b:.4f}")

    tot = pot_b + rec_b
    ck("实际总用量 = 20,728", tot == 20728, str(tot))
    ck("总用量/供给 = 53.6%", abs(tot / sup * 100 - 53.6) < 0.1, f"{tot/sup*100:.2f}")
    ck("再生水利用率 = 64.3%", abs(rec_b / 6017 * 100 - 64.3) < 0.1, f"{rec_b/6017*100:.2f}")
    print(f"  总用量/供给 = {tot/sup*100:.1f}% | 再生水利用率 = {rec_b/6017*100:.1f}%")

    # ---- k* 与阈值 ----
    r_star = 0.5532
    k_star = (1 / r_star - 1) / RHO
    print(f"\n  k* = (1/{r_star} − 1)/(6/26) = {k_star:.3f}（论文 3.50）")
    ck("k* ≈ 3.50", abs(k_star - 3.50) < 0.01, f"{k_star:.3f}")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\nUWMP 原始 PDF 核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        if not ok:
            print(f"  ❌ {name}　[{detail}]")
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
