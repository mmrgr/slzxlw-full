"""真正重排 Results 小节顺序 (2026-10-17).

上一版只改了编号, 未移动段落 —— 顺序仍错 (7 排在 4 前面)。
本版按标题切块, 重排后再拼接, 确保顺序与编号一致。
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

i_res = t.index("## Results")
i_dis = t.index("## Discussion")
head, body, tail = t[:i_res], t[i_res:i_dis], t[i_dis:]

# 按 ### / #### 切块
parts = re.split(r"\n(?=### |#### )", body)
intro = parts[0]                     # "## Results\n\n"
blocks = parts[1:]

# 用编号排序 (1..12, 12a, 12b)
def key(b: str) -> tuple:
    m = re.match(r"#{3,4}\s+(\d+)([a-z]*)\.", b)
    if not m:
        return (999, "")
    return (int(m.group(1)), m.group(2))

blocks_sorted = sorted(blocks, key=key)

new_body = intro + "\n".join(b.rstrip() for b in blocks_sorted) + "\n\n"
MS.write_text(head + new_body + tail, encoding="utf-8")

# 复验
tt = MS.read_text(encoding="utf-8")
r = tt[tt.index("## Results"):tt.index("## Discussion")]
print("新顺序:")
for k, m in enumerate(re.finditer(r"^(###|####) (.+)$", r, re.M), 1):
    print(f"  {k:>2}. {m.group(2)[:58]}")
