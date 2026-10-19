# -*- coding: utf-8 -*-
"""修复两处交付缺陷：
  1. FigR5 引用的路径被写坏（figs → \\f + igs，裸反斜杠 + 换页符）
  2. Fig3 已生成但正文未引用（11 张图漏 1 张）

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_fix_figrefs.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
V2 = HERE / "03_主稿_v2.md"


def main() -> None:
    t = V2.read_text(encoding="utf-8")
    orig = t
    fixed = []

    # ---------- 修复 1：FigR5 路径 ----------
    # 实际损坏内容：'（\\\x0cigs/FigR5_grid_convergence.pdf\\）'
    # 目标：'（`figs/FigR5_grid_convergence.pdf`）'
    pat_bad = re.compile(r"> \*\*图 R5\*\*（[^\n]*?FigR5_grid_convergence\.pdf[^\n]*?）")
    m = pat_bad.search(t)
    if m:
        old_line = m.group(0)
        new_line = "> **图 R5**（`figs/FigR5_grid_convergence.pdf`）：(a) CAWCC 绝对值随网格细化单调趋近上界；(b) 降幅在三网格下的对比（零效应区一致、中间区波动）；(c) 量化伪影的成因示意。"
        t = t.replace(old_line, new_line, 1)
        print("[OK  ] FigR5 路径已修复")
        fixed.append("figR5_path")
    elif "FigR5_grid_convergence" in t:
        print("[SKIP] FigR5 引用已正常")
    else:
        print("[MISS] 未找到 FigR5 引用")

    # ---------- 清理残留控制字符 ----------
    ctrl = {c: t.count(c) for c in ("\x0c", "\x0b", "\x07", "\x08", "\x00") if t.count(c)}
    if ctrl:
        for c, n in ctrl.items():
            t = t.replace(c, "")
            print(f"[OK  ] 清理控制字符 {repr(c)} × {n}")

    # ---------- 修复 2：Fig3 引用 ----------
    # Fig3 是"约束轨迹"，应插在 §5.1 逐约束首次失效容量表之后
    if "Fig3_constraint_trajectories" in t:
        print("[SKIP] Fig3 已引用")
    else:
        anchor = "**证据**：`r2/ha/constraint_boundaries_corrected.csv`、`r2/co/constraint_boundaries_corrected.csv`。"
        if anchor in t:
            new = anchor + """

> **图 3**（`figs/Fig3_constraint_trajectories.pdf`）：逐容量点展示各约束取值如何逼近其阈值，用于识别哪些约束真正具有约束力（informative）、哪些全程未触及。非 informative ≠ 系统安全——它们只是未被扫描范围触及（见 §5.3）。"""
            t = t.replace(anchor, new, 1)
            print("[OK  ] Fig3 引用已插入 §5.1")
            fixed.append("fig3")
        else:
            print("[MISS] 未找到 §5.1 证据锚点")

    # ---------- 校验 ----------
    print("-" * 66)
    refs = sorted(set(re.findall(r"figs/(Fig[A-Za-z0-9_]+)\.pdf", t)))
    print(f"正文引用图件: {len(refs)}")
    for r in refs:
        print(f"  ✅ {r}")

    import os
    actual = sorted(f[:-4] for f in os.listdir(HERE / "figs") if f.endswith(".pdf"))
    missing = [a for a in actual if a not in refs]
    unused = [r for r in refs if r not in actual]
    print()
    print(f"未引用的图: {missing if missing else '无'}")
    print(f"引用了但不存在: {unused if unused else '无'}")

    if t != orig:
        V2.write_text(t, encoding="utf-8")
        print(f"\n字数 {len(orig):,} → {len(t):,}")

    ok = not missing and not unused
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
