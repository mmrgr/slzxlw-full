"""把 Declarations 中的中文待填提示改为英文注释块 (2026-10-17).

【问题】投稿版正文出现:
    **⚠️ 需作者确认**（若确无，保留下述标准表述）
    **⚠️ 需作者填写（不得代拟）**
    **⚠️ 需作者填写**（基金号、数据提供者致谢等）
这不符合英文投稿格式。

【不能直接删】删掉会丢失"待填"警示, 增加作者漏填风险(10 处占位符)。

【处置】改为英文 HTML 注释, 投稿前由作者删除:
    <!-- AUTHOR ACTION: confirm no competing interests, then delete this line. -->
这样:
  · 投稿系统中不可见(HTML 注释);
  · 作者在源码中能看见警示。
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

PAIRS = [
    ("**⚠️ 需作者确认**（若确无，保留下述标准表述）",
     "<!-- AUTHOR ACTION: confirm there are no competing interests, then delete this comment. -->"),
    ("**⚠️ 需作者填写（不得代拟）**",
     "<!-- AUTHOR ACTION: fill in the author list and CRediT contributions, then delete this comment. -->"),
    ("**⚠️ 需作者填写**（基金号、数据提供者致谢等）",
     "<!-- AUTHOR ACTION: add funding numbers and acknowledgements, then delete this comment. -->"),
    ("> These statements are required by the target journal. Items marked `[[...]]` must be completed by the authors; nothing personal has been auto-filled.",
     "<!-- AUTHOR ACTION: every [[...]] below must be completed before submission. -->"),
]

n = 0
for a, b in PAIRS:
    if a in t:
        t = t.replace(a, b, 1)
        n += 1
    else:
        print(f"  MISS: {a[:60]}")

MS.write_text(t, encoding="utf-8")
print(f"替换 {n}/{len(PAIRS)}")

# 复验: Declarations 之后是否还有中文提示语
i = t.find("## Declarations")
tail = t[i:] if i > 0 else ""
cn = [l.strip()[:60] for l in tail.split("\n") if re.search(r"[\u4e00-\u9fff]", l)]
print(f"Declarations 内中文行剩余: {len(cn)}")
for c in cn[:6]:
    print("   ", c)
