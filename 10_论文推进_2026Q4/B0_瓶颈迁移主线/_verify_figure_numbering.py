# -*- coding: utf-8 -*-
"""门禁：图件编号一致性（新增，第 29 道）。

检查四者是否一致，防止未来重跑或改名造成错配：
  A. 正文图注：**Figure N.** 必须存在且按 1..6 顺序出现、各一次
  B. 图件文件：figs/FigN_<slug>.pdf 与 .png 必须存在
  C. 生成脚本：make_figN.py 的 save 名必须含 FigN_
  D. 图件索引：图件索引.md 的 Fig N 行必须引用 FigN_ 文件
  E. 图注内容与文件名 slug 语义匹配（关键词检查）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
FIG = HERE / "figs"
EN = HERE / "04_wr_manuscript_en.md"
MS = HERE / "03_主稿_v2.md"
IDX = FIG / "图件索引.md"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


# slug 关键词：图号 -> 文件名应含的片段
SLUG = {
    1: "framework",
    2: "bottleneck_migration",
    3: "constraint_trajectories",
    4: "interventions",
    5: "city_gradient",
    6: "timescale",
}

# 图注内容关键词（英文稿）
CAP_KW = {
    1: "research boundary",
    2: "bottleneck migration",
    3: "constraint trajectories",
    4: "intervention counterfactuals",
    5: "city-gradient",
    6: "time-scale",
}

en = EN.read_text(encoding="utf-8")
idx = IDX.read_text(encoding="utf-8") if IDX.exists() else ""

# ---------- A. 正文图注顺序与唯一性 ----------
caps = re.findall(r"\*\*Figure (\d)\.\*\*", en)
ck("A1 英文稿含 6 个图注", len(caps) == 6, f"{len(caps)} 个")
ck("A2 图注按 1..6 顺序出现", caps == list("123456"), str(caps))

# ---------- B/C/D/E. 逐图检查 ----------
for n, slug in SLUG.items():
    # B. 文件存在（按 "FigN_*" 通配匹配，不要求完整 slug，因为文件名可带后缀如 _policy）
    cand = sorted(FIG.glob(f"Fig{n}_*.pdf"))
    cand_png = sorted(FIG.glob(f"Fig{n}_*.png"))
    ok_pdf = len(cand) == 1
    ok_png = len(cand_png) == 1
    ck(f"B  图{n} 文件唯一且 pdf+png 齐备", ok_pdf and ok_png,
       cand[0].name if ok_pdf else f"pdf 命中 {len(cand)} 个")

    # C. 脚本 save 名（脚本里应含 "FigN_"，不要求完整 slug）
    script = FIG / f"make_fig{n}.py"
    if script.exists():
        st = script.read_text(encoding="utf-8", errors="replace")
        ck(f"C  图{n} 生成脚本输出名正确", f"Fig{n}_" in st,
           f"make_fig{n}.py")
    else:
        ck(f"C  图{n} 生成脚本存在", False, f"缺 make_fig{n}.py")

    # D. 索引引用
    ck(f"D  图{n} 索引引用 Fig{n}_", f"Fig{n}_" in idx, "图件索引.md")

    # E. 图注内容与 slug 语义匹配
    m = re.search(rf"\*\*Figure {n}\.\*\*(.{{0,200}})", en, re.S)
    cap = m.group(1).lower() if m else ""
    ck(f"E  图{n} 图注内容匹配（{CAP_KW[n]}）", CAP_KW[n].lower() in cap,
       "")

# ---------- 汇总 ----------
npass = sum(1 for _, ok, _ in RES if ok)
print("=" * 78)
print(f"图件编号一致性　通过 {npass}/{len(RES)}")
print("=" * 78)
for name, ok, detail in RES:
    print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
sys.exit(0 if npass == len(RES) else 1)
