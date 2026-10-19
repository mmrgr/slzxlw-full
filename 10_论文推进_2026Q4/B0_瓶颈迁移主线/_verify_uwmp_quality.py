# -*- coding: utf-8 -*-
"""核验 UWMP 中关于"冷却塔补水水质"的一手陈述，并把它们写入论文。

【发现（UWMP p.62，2026-06 市府法定文件）】
以下三句直接支持本文的机制假设，此前论文完全没有引用：

1. "In areas of the City served by groundwater, industrial customers will find the quality of
    treated recycled water to be more consistent than groundwater for cooling towers."
   → 官方文件明确讨论**冷却塔**的水源水质

2. "Those cooling towers that receive groundwater could also receive a blend of multiple water
    sources based on system demand (e.g., groundwater blended with imported surface water)
    with slight variations in water quality, whereas those that receive recycled water would
    receive one consistent water source."
   → 官方确认冷却塔补水是**混合水源**，且水质随配比变化
   → 这正是本文 r（再生水替代率）与 C_mix = r·C_r + (1−r)·C_p 所建模的对象

3. "The enhanced blend of water will help industrial users reduce operating costs, and it can be
    used on a wider variety of landscapes, due to a much lower level of salinity."
   → 官方文件明确用 **salinity（含盐量）** 描述再生水水质，并把它与工业用户联系起来

【价值】
此前论文的 §5.9 只用了 UWMP 的**水量**数据；其**水质**叙述从未被使用。
这三句为以下三点提供一手支撑：
  (a) 该市冷却塔确实使用再生水与其它水源的混合补水（机制前提）；
  (b) 官方以含盐量（salinity）刻画该水质问题（本文判据变量）；
  (c) 官方认为再生水水质比地下水更稳定（支持"以水质而非水量为约束"的问题设定）。

【限制】
UWMP 未给出任何 TDS / 电导率 / 氯化物的**数值**（全文 TDS 仅出现于 p.12 缩写表、
p.86 定性陈述、p.153 法规条文）。故这三句**只能支撑机制前提，不能锚定 C_p 或 C_r 的数值**。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PDF = Path(r"C:/Users/mmrgr/Desktop/000/2025 Urban Water Management Plan_Final.pdf")

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    doc = fitz.open(PDF)
    p62 = " ".join(doc[61].get_text().split())
    p86 = " ".join(doc[85].get_text().split())
    full = " ".join(" ".join(doc[i].get_text().split()) for i in range(doc.page_count))

    # ---- 三句机制支撑证据 ----
    ck("p.62 提及 cooling towers",
       "cooling towers" in p62, "")
    ck("p.62 说明再生水对冷却塔水质更稳定",
       "more consistent than groundwater for cooling towers" in p62, "")
    ck("p.62 说明冷却塔补水为混合水源",
       "blend of multiple water sources" in p62, "")
    ck("p.62 用 salinity 描述再生水",
       "lower level of salinity" in p62, "")

    # ---- 反证：全文无 TDS 数值 ----
    ck("p.86 有 TDS 定性陈述（不受 TDS 困扰）",
       "total dissolved solids (TDS) is not a concern" in p86, "")
    # 找任何 TDS 后跟数字的模式
    num_after_tds = re.findall(r"TDS[^.]{0,40}?\b\d{2,4}\b", full)
    ck("全文无 TDS 数值（故不能锚定 C_p）",
       len(num_after_tds) == 0, f"命中 {num_after_tds[:3]}")

    # 电导率、氯化物、硬度均不出现
    for kw in ("onductivity", "hloride", "ardness", "µmhos", "μS/cm"):
        n = full.count(kw)
        ck(f"全文无 '{kw}'（无水质数值）", n == 0, f"{n} 次")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\nUWMP 水质证据核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
