# -*- coding: utf-8 -*-
"""聚焦审计：只检查与论文核心论点直接相关的 6 个关键产物，
对每个文件的**每一列**逐一判断"论文是否用过"。

【为什么聚焦】
上一个粗筛在 130 个 CSV 中找到 652 个"未引用列"，绝大多数是逐容量点扫描的
中间量（peak/p95/7day 等），不是遗漏。噪声太大，无法判断。

本脚本只查 6 个"承载核心论断"的产物：
  1. rstar_physical_cawcc_by_r.csv      ← 主结论（上一轮在此发现 CO 遗漏）
  2. rstar_confound_control.csv         ← 混淆排除
  3. rstar_regime_validation.csv        ← 分类学验证
  4. rstar_grid_convergence_table.csv   ← 网格收敛
  5. {ha,co}/capacity_threshold_corrected.json  ← 六类 estimand
  6. {ha,co}/constraint_informathiveness.csv    ← 约束信息量

对每个：列出全部列名 + 是否在正文出现过 + 若未出现，其取值范围。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
OUT = HERE / "_key_products_audit.txt"

CORPUS = "\n".join(
    p.read_text(encoding="utf-8")
    for p in (HERE / "03_主稿_v2.md",
              HERE / "04_wr_manuscript_en.md",
              HERE / "05_wr_supplementary_en.md")
    if p.exists()
)

TARGETS = [
    "rstar_physical_cawcc_by_r.csv",
    "rstar_confound_control.csv",
    "rstar_regime_validation.csv",
    "rstar_grid_convergence_table.csv",
    "ha/constraint_informativeness.csv",
    "co/constraint_informativeness.csv",
    "ha/capacity_threshold_corrected.csv",
]


def main() -> None:
    lines: list[str] = []

    def w(s: str = "") -> None:
        lines.append(str(s))

    for t in TARGETS:
        f = R2 / t
        if not f.exists():
            w(f"\n### {t}  —— 缺失\n")
            continue
        try:
            d = pd.read_csv(f, encoding="utf-8-sig")
        except Exception as e:
            w(f"\n### {t}  —— 读取失败 {e}\n")
            continue
        w(f"\n{'='*100}")
        w(f"### {t}   {len(d)} 行 × {len(d.columns)} 列")
        w("=" * 100)
        for c in d.columns:
            hit = c in CORPUS or c.replace("_", " ") in CORPUS
            if not hit:
                # 尝试去掉常见后缀
                for suf in ("_ml", "_mw", "_pct", "_ratio"):
                    if c.endswith(suf) and c[: -len(suf)] in CORPUS:
                        hit = True
                        break
            try:
                if pd.api.types.is_numeric_dtype(d[c]):
                    rng = f"[{d[c].min():.4g}, {d[c].max():.4g}]"
                else:
                    vals = d[c].dropna().unique()[:4]
                    rng = str(list(vals))
            except Exception:
                rng = "?"
            mark = "✅" if hit else "❌ 未引用"
            w(f"  {mark:<10} {c:<46} {rng}")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
