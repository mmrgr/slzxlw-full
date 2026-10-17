r"""在 Code availability 中补入"正文数字 → 产物目录"索引 (2026-10-17).

【为什么】
扫描发现 12 个分析目录从未被论文提及。其中 **A18_有限供水** 尤其关键：
主稿多处使用它的数字（0/68、边际楔子 1.178、路径效率 0.849、8,519 ML 未满足需求），
但正文里**从未出现 "A18" 或 "finite_supply"**，读者无法追溯。

同理 A19（水化学包络）、A27（引用限值替换）、A15（稳健性）、A31/A33/A34/A38/A39
虽然个别被提到，但没有一个统一的"我该去哪找这个数"的入口。

【做法】
在 Code availability 的仓库条目之后，加一个精简的**关键产物索引表**，
只列正文中真正用到数字的目录（不含早期探索性目录）。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

ANCHOR = "- Version / commit: **[[COMMIT_OR_VERSION]]**"
BLOCK = """- Version / commit: **[[COMMIT_OR_VERSION]]**
- **Where each headline number comes from.** The analysis tree is organised by artefact rather
  than by narrative, so this table maps the numbers in the main text to the directory that
  produces them (every directory contains a `*_summary.json` with the machine-checkable value):

  | number in main text | directory | what it holds |
  |---|---|---|
  | three-account ledger, 0/68, wedge 1.178, 8,519 ML | `A18_有限供水/` | full-engine finite-supply counterfactual |
  | identity residuals, branch counts, sign statistics | `A13_可靠性机制/` | authoritative main grid |
  | composition effect, complete-species subset | `A33_WP4_组成重构/` | 47-scenario complete-composition runs |
  | solver-path comparison (volume-only vs dynamic) | `A38_模拟审稿/` | NE-1 path head-to-head |
  | Morris and Sobol indices | `A34_WP5_敏感性与极端事件/` | global sensitivity |
  | holdout and grid-resolution checks | `A15_稳健性/` | cross-domain validation, refinement |
  | cooling-water limit tiers | `A19_水化学包络/`, `A27_引用限值/` | envelope and cited-limit substitution |
  | model bridging (23/24 agreement) | `A20_模型桥接/` | two-implementation comparison |
  | external anchors (10,826 / 141 / 597 / 31 cities) | `A39_WP8_外部效度/` | CC-BY source-data derivative |
  | partial identification bounds | `A30_WP0取证/` | [0%, 100%] bound and capacity table |
  | E3 / E3b prediction tests | `A31_WP2_假设冻结/` | pre-intervention predictor evaluation |
"""
if "Where each headline number comes from" in t:
    print("已存在，跳过")
else:
    assert ANCHOR in t, "锚点缺失"
    t = t.replace(ANCHOR, BLOCK.rstrip("\n"), 1)
    MS.write_text(t, encoding="utf-8")
    print("已补入正文数字 → 产物目录索引")
