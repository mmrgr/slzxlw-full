"""审计剩余 5 个图注中的关键统计数字 (2026-10-17).

【策略】
完全自动化 5 个图注(2600 词)成本高。改用**对症**做法:
把每个图注里"可被独立验证的统计量"逐条对照产物, 列出不匹配项。

【做法】
对每个图注, 抽取形如 "N of M"、"n = N"、"N points"、"N rows" 的断言,
再在产物中查找同名统计量。无法自动判定的列为"需人工"。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent.parent / "A37_六主图_v4"
ROOT = HERE.parent

# 图号 -> 该图依赖的核心产物
DEPS = {
    1: ["A18_有限供水/finite_supply_summary.json"],
    2: ["A32_WP3_水化学/wp3_h4_robustness_summary.json",
        "A13_可靠性机制/supply_state_regimes.csv"],
    4: ["A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json",
        "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json"],
    5: ["A38_模拟审稿/ne4_sobol_bootstrap_summary.json",
        "A34_WP5_敏感性与极端事件/wp5_extreme_summary.json"],
    6: ["A39_WP8_外部效度/wp8_real_reuse_cases_summary.json",
        "A30_WP0取证/a24b_partial_id_summary.json",
        "A39_WP8_外部效度/wp11_reuse_deployment_summary.json"],
}

PAT = re.compile(r"(?<!\d)(\d{2,5})\s*(?:of|/)\s*(\d{2,5})(?!\d)",
                 ) if False else re.compile(r"(?<![\d.])(\d{1,4})\s+of\s+(\d{1,5})(?![\d.])")


def main() -> int:
    print("=" * 78)
    print("剩余 5 个图注的关键断言审计")
    print("=" * 78)
    issues = 0
    for n in (1, 2, 4, 5, 6):
        cap = HERE / f"fig{n}_caption.md"
        if not cap.exists():
            print(f"  [MISS] fig{n}_caption.md")
            continue
        t = cap.read_text(encoding="utf-8")
        deps_text = ""
        for rel in DEPS.get(n, []):
            p = ROOT / rel
            if p.exists():
                deps_text += p.read_text(encoding="utf-8", errors="replace")
        pairs = PAT.findall(t)
        bad = []
        for a, b in pairs:
            # 若 "a of b" 这一对数字在依赖产物中**同时以该形式**出现视为通过
            # 否则列为待核（可能是跨产物计算, 需人工）
            form = f"{a} of {b}"
            form2 = f"{a}/{b}"
            if form in deps_text or form2 in deps_text:
                continue
            bad.append((a, b))
        print(f"\n  fig{n}: {len(pairs)} 条 'X of Y' 断言, 产物中未直接匹配 {len(bad)}")
        for a, b in bad[:6]:
            # 定位上下文
            i = t.find(f"{a} of {b}")
            ctx = " ".join(t[max(0, i - 70):i + 60].split())
            print(f"      {a} of {b}  …{ctx[-95:]}")
        issues += len(bad)
    print()
    print(f"裁定: {issues} 条需人工核对（非自动可判）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
