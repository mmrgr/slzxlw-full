"""修正 Results 小节编号错乱 (2026-10-17).

【问题】反复插入导致编号顺序为:
  1, 2, 3, 3d, 3b, 3b-bis, 3c, 4, 5, 6, 6b, 7, 7a, 7b
  即 3d 出现在 3b/3c 之前, 且存在 3b-bis 这种非标准编号。

【修正】重排为连续编号, 并保持小节内容不变:
  1 三账本
  2 精确恒等式
  3 符号判据
  4 数据完整性缺口            (原 3b)
  5 冷却水限值取值            (原 3b-bis)
  6 求解器可靠性门禁          (原 3c)
  7 这些能否预测?             (原 3d)
  8 有限供水
  9 质量与组成
  10 外部锚定
  11 真实系统处于哪个分支      (原 6b)
  12 稳健性与证伪
  12a 全局敏感性               (原 7a)
  12b 极端事件                 (原 7b)

【安全】只改标题行 + 正文中对小节号的交叉引用; 内容一字不动。改完必须重跑八门禁。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

# 旧标题片段 -> 新标题 (用唯一前缀匹配)
TITLE_MAP = [
    ("### 1. Three accounts, not one", "### 1. Three accounts, not one"),
    ("### 2. An exact identity covering two opposite regimes",
     "### 2. An exact identity covering two opposite regimes"),
    ("### 3. What decides the sign", "### 3. What decides the sign"),
    ("### 3b. Data-integrity gap", "### 4. Data-integrity gap"),
    ("### 3b-bis. Cooling-water limits", "### 5. Cooling-water limits"),
    ("### 3c. Solver reliability gate", "### 6. Solver reliability gate"),
    ("### 3d. Is any of this *predictive*?", "### 7. Is any of this *predictive*?"),
    ("### 4. Finite supply transforms", "### 8. Finite supply transforms"),
    ("### 5. Quality and composition together", "### 9. Quality and composition together"),
    ("### 6. External anchoring against", "### 10. External anchoring against"),
    ("### 6b. Which regime do real systems occupy?", "### 11. Which regime do real systems occupy?"),
    ("### 7. Robustness and falsification", "### 12. Robustness and falsification"),
    ("#### 7a. Global sensitivity", "#### 12a. Global sensitivity"),
    ("#### 7b. Extreme events", "#### 12b. Extreme events"),
]

# 正文交叉引用 (只替换明确的 "§N" 形式)
CROSSREF = [
    ("§3d", "§7"),
    ("§6b", "§11"),
    ("§7a", "§12a"),
    ("§3b", "§4"),
    ("§3c", "§6"),
    ("§6 ", "§10 "),
]

n_title = 0
for old, new in TITLE_MAP:
    if old in t:
        t = t.replace(old, new, 1)
        n_title += 1
    else:
        print(f"  MISS title: {old[:50]}")

n_ref = 0
for old, new in CROSSREF:
    c = t.count(old)
    if c:
        t = t.replace(old, new)
        n_ref += c

MS.write_text(t, encoding="utf-8")
print(f"标题替换 {n_title}/{len(TITLE_MAP)}; 交叉引用替换 {n_ref} 处")

# 复验顺序
r = t[t.index("## Results"):t.index("## Discussion")]
print("\n新顺序:")
for i, m in enumerate(re.finditer(r"^(###|####) (.+)$", r, re.M), 1):
    print(f"  {i:>2}. {m.group(2)[:58]}")
