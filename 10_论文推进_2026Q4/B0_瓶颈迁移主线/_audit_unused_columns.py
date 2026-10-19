# -*- coding: utf-8 -*-
"""系统盘点：所有产物文件中有哪些**列/字段从未被主稿引用**。

【动机】
上一轮发现 `rstar_physical_cawcc_by_r.csv` 一直同时含 joint 与 physical 两列，
但论文只用了 physical 一列，漏掉了 CO 端 −700 MW 这一重要结果。

这不是孤例，而是**一类**问题。本轮系统地找同类问题：
  1. 列出 r2 目录下所有 CSV 的列；
  2. 找出"数值型但从未在任何文稿中出现"的列名；
  3. 人工判断哪些是真正的遗漏。

【做法】
对每个 CSV：读列名 + 数值范围；
对每个列名：在母稿/英文/SI 全文中搜索（含常见改写）。
输出：未被引用的列清单 + 该列的取值范围。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
OUT = HERE / "_unused_columns_report.txt"

DOCS = [
    HERE / "03_主稿_v2.md",
    HERE / "04_wr_manuscript_en.md",
    HERE / "05_wr_supplementary_en.md",
]

# 这些列名是标识符/时间/状态，不是"结果"，不参与判断
SKIP_PAT = ("date", "id", "domain", "target_r", "constraint", "operator",
            "status", "note", "tag", "label", "scope", "name", "path",
            "intervention", "tech", "regime", "base", "caliber")


def main() -> None:
    corpus = "\n".join(p.read_text(encoding="utf-8") for p in DOCS if p.exists())
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(str(s))

    csvs = sorted(R2.rglob("*.csv"))
    w(f"扫描 {len(csvs)} 个 CSV")
    w("")

    unused: list[tuple[str, str, str]] = []
    for f in csvs:
        try:
            d = pd.read_csv(f, encoding="utf-8-sig")
        except Exception:
            continue
        rel = str(f.relative_to(R2))
        for c in d.columns:
            cl = c.lower()
            if any(s in cl for s in SKIP_PAT):
                continue
            # 数值列才关心
            if not pd.api.types.is_numeric_dtype(d[c]):
                continue
            # 列名（或其下划线/空格变体）是否在正文出现
            variants = {c, c.replace("_", " "), c.rsplit("_", 1)[0]}
            hit = any(v in corpus for v in variants if v)
            # 也检查去掉常见后缀后是否出现
            if not hit:
                stem = c.replace("_ml", "").replace("_mw", "").replace("_pct", "")
                hit = stem and stem in corpus
            if not hit:
                try:
                    rng = f"[{d[c].min():.4g}, {d[c].max():.4g}]"
                except Exception:
                    rng = "?"
                unused.append((rel, c, rng))

    if unused:
        w(f"=== 疑似未被正文引用的数值列（{len(unused)} 项）===")
        w(f"{'文件':<58}{'列':<44}{'取值范围'}")
        w("-" * 130)
        for rel, c, rng in unused:
            w(f"{rel:<58}{c:<44}{rng}")
    else:
        w("所有数值列均已在正文出现。")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
