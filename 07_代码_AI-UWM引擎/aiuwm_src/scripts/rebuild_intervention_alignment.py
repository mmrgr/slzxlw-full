"""重建干预基线对齐表（同网格口径，消除跨网格 −50 伪值）

【为什么重建】
旧 `intervention_baseline_alignment.csv` 的「物理日尺度口径增益」列是跨网格相减：
    `干预后CAWCC(100 MW 网格) − 物理日尺度基线(50 MW 网格)`
结果对**所有零增益干预**都给出 **−50 MW**（如 HA `grid_plus_50pct`、CO
`leakage_minus_30pct`）——一个什么都没改变的干预不可能造成 50 MW 容量损失。
这是网格混算伪值，不是物理效应（`run_r2.py:400-403` 的注释已警告同类错误）。

【新表的口径】
三列**全部同网格**，任一列内部可相减：

  1. `干预表口径_100MW`：基线 1100/1400，干预后值来自 100 MW 网格
     （`{ha,co}/intervention_marginal.csv`）
  2. `同网格_50MW`：基线 1150/1450，干预后值来自 50 MW 网格
     （`{ha,co}/intervention_marginal_50mw.csv`）——**本文正文采用此列**
  3. `物理日尺度基准`：`capacity_threshold_corrected.json` 的
     `physical_daily.maximum_safe_ai_capacity_mw`（1150/1450），
     **仅作参考基线，不与任何干预后值相减**

并显式列出**旧表的伪值列**，注明为何不可用。

【输出】
- `validation_artifacts/r2/intervention_baseline_alignment_50mw.csv`
- `validation_artifacts/r2/intervention_baseline_alignment_50mw.md`（人类可读说明）

用法:
    PYTHONPATH="src;scripts" python scripts/rebuild_intervention_alignment.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation_artifacts" / "r2"


def load_cawcc(domain: str) -> dict:
    return json.loads(
        (OUT / domain / "capacity_threshold_corrected.json").read_text(encoding="utf-8")
    )


def main() -> None:
    rows: list[dict] = []

    for domain in ("ha", "co"):
        m100 = pd.read_csv(OUT / domain / "intervention_marginal.csv")
        m50 = pd.read_csv(OUT / domain / "intervention_marginal_50mw.csv")
        cawcc = load_cawcc(domain)

        base100 = float(
            m100.loc[m100["intervention"] == "baseline", "maximum_safe_ai_capacity_mw"].iloc[0]
        )
        base50 = float(
            m50.loc[m50["intervention"] == "baseline", "maximum_safe_ai_capacity_mw"].iloc[0]
        )
        physical_daily = float(cawcc["physical_daily"]["maximum_safe_ai_capacity_mw"])

        m100_by = {r["intervention"]: r for _, r in m100.iterrows()}
        m50_by = {r["intervention"]: r for _, r in m50.iterrows()}

        # 顺序以 50 MW 表为准（它是正文口径）
        for name in m50_by:
            r50 = m50_by[name]
            r100 = m100_by.get(name)
            after50 = float(r50["maximum_safe_ai_capacity_mw"])
            after100 = float(r100["maximum_safe_ai_capacity_mw"]) if r100 is not None else None

            rows.append({
                "域": domain,
                "干预": name,
                # --- 口径 1：100 MW 同网格 ---
                "干预表口径_基线_MW": base100,
                "干预表口径_干预后_MW": after100,
                "干预表口径_增益_MW": (after100 - base100) if after100 is not None else None,
                # --- 口径 2：50 MW 同网格（正文采用）---
                "同网格50MW_基线_MW": base50,
                "同网格50MW_干预后_MW": after50,
                "同网格50MW_增益_MW": after50 - base50,
                # --- 参考基线（不相减）---
                "物理日尺度基准_MW": physical_daily,
                # --- 限制约束（以 50 MW 为准）---
                "限制约束_50MW": r50["limiting_constraint"],
                "限制约束_100MW": r100["limiting_constraint"] if r100 is not None else None,
            })

    frame = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        OUT / "intervention_baseline_alignment_50mw.csv", index=False, encoding="utf-8-sig"
    )

    # ---- 人类可读说明 ----
    lines = [
        "# 干预基线口径对齐表（重建版，2026-10-18）",
        "",
        "## 为什么重建",
        "",
        "旧 `intervention_baseline_alignment.csv` 的「物理日尺度口径增益」列是**跨网格相减**：",
        "`干预后CAWCC(100 MW 网格) − 物理日尺度基线(50 MW 网格)`。",
        "结果对**所有零增益干预**都给出 **−50 MW**——一个什么都没改变的干预",
        "不可能造成 50 MW 容量损失。这是网格混算伪值，不是物理效应。",
        "",
        "## 新表的三列（全部同网格，任一列内部可相减）",
        "",
        "| 列组 | 基线 | 网格 | 用途 |",
        "|---|---:|---|---|",
        f"| 干预表口径_* | {frame['干预表口径_基线_MW'].iloc[0]:.0f} | 100 MW | 历史对照 |",
        f"| **同网格50MW_*** | **{frame['同网格50MW_基线_MW'].iloc[0]:.0f}** | **50 MW** | **本文正文采用** |",
        f"| 物理日尺度基准_MW | {frame['物理日尺度基准_MW'].iloc[0]:.0f} | 50 MW | 仅参考，不相减 |",
        "",
        "## 关键结果（同网格 50 MW 口径）",
        "",
    ]
    for domain in ("ha", "co"):
        sub = frame[(frame["域"] == domain) & (frame["同网格50MW_增益_MW"] > 0)]
        lines.append(f"### {domain.upper()}")
        lines.append("")
        if sub.empty:
            lines.append("无正增益干预。")
        else:
            lines.append("| 干预 | 干预后 CAWCC | 增益 | 限制约束 |")
            lines.append("|---|---:|---:|---|")
            for _, r in sub.iterrows():
                lines.append(
                    f"| {r['干预']} | {r['同网格50MW_干预后_MW']:.0f} | "
                    f"**+{r['同网格50MW_增益_MW']:.0f}** | {r['限制约束_50MW']} |"
                )
        lines.append("")

    lines += [
        "## 结论",
        "",
        "- **HA 端唯一有效干预**：`leakage_minus_30pct`，+150 MW（1150→1300）。",
        "  旧 100 MW 口径报 +200 MW，差异**纯由基线网格分辨率造成**（100 MW 网格上",
        "  基线是 1100，从未评估 1150 这一点）。",
        "- **CO 端唯一有效干预**：`grid_plus_50pct`，+100 MW（1450→1550）。",
        "  该值在两口径下相同，但旧表的 −50 伪值列会让人误读为「扩电网无效」。",
        "- **所有零增益干预的增益为 0，不是 −50。**",
        "",
        "## 不可引用的旧列",
        "",
        "旧文件的以下列**不得引用**：",
        "- `物理日尺度口径增益_MW`：跨网格相减，零增益干预给出 −50 伪值。",
        "",
    ]
    (OUT / "intervention_baseline_alignment_50mw.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    # ---- 控制台汇总 ----
    print("=" * 78)
    print("干预基线口径对齐（同网格重建）")
    print("=" * 78)
    for domain in ("ha", "co"):
        sub = frame[frame["域"] == domain]
        print(f"\n{domain.upper()}  同网格基线 = {sub['同网格50MW_基线_MW'].iloc[0]:.0f} MW")
        print(sub[[
            "干预", "同网格50MW_干预后_MW", "同网格50MW_增益_MW", "限制约束_50MW"
        ]].to_string(index=False))

    print(f"\n-> {OUT / 'intervention_baseline_alignment_50mw.csv'}")
    print(f"-> {OUT / 'intervention_baseline_alignment_50mw.md'}")


if __name__ == "__main__":
    main()
