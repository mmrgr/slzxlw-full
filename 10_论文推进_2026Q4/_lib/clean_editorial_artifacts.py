"""清理投稿版中的内部编辑痕迹 (2026-10-17).

【分类原则】
  A. 标题里的 "(new in v4)" —— 纯编辑痕迹, **删除**;
  B. 正文的 Correction/Retraction/Composition completeness —— **保留内容**, 仅去掉版本号,
     因为它们是学术诚信披露, 但读者不需要知道"v4"。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

PAIRS = [
    # A: 标题去掉编辑痕迹
    ("### 7. Is any of this *predictive*? A strict pre-intervention test (new in v4)",
     "### 7. Is any of this *predictive*? A strict pre-intervention test"),
    ("#### 12a. Global sensitivity: a single sign lever, **within a stated limit tier** (new in v4)",
     "#### 12a. Global sensitivity: a single sign lever, **within a stated limit tier**"),
    ("#### 12b. Extreme events change magnitude, not sign (new in v4)",
     "#### 12b. Extreme events change magnitude, not sign"),
    # B: 正文去掉版本号, 保留内容
    ("**Correction (v4, after red-team review).**", "**Correction, after red-team review.**"),
    ("**⚠️ Composition completeness (new in v4).**", "**⚠️ Composition completeness.**"),
    ("**⚠️ Retraction (v4): the regime shares are *not identified* by this dataset.**",
     "**⚠️ Retraction: the regime shares are *not identified* by this dataset.**"),
    ("**Uncertainty on these indices (added in v4).**", "**Uncertainty on these indices.**"),
]

n = 0
for a, b in PAIRS:
    if a in t:
        t = t.replace(a, b, 1)
        n += 1
    else:
        print(f"  MISS: {a[:70]}")

MS.write_text(t, encoding="utf-8")
print(f"替换 {n}/{len(PAIRS)}")

import re
left = re.findall(r"(new in v4|\(v4|in v4|Correction \(v4)", t)
print("残留编辑痕迹:", left if left else "无")
