"""Insert the realism-audit section as Section 3 and renumber 3..16 -> 4..17."""
import re
from pathlib import Path

DOC = Path(r"C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.md")
text = DOC.read_text(encoding="utf-8")

# 1) renumber "第 N 节" cross references, descending
for n in range(16, 2, -1):
    text = re.sub(rf"第 {n} 节", f"第 \x00{n + 1}\x00 节", text)
# 2) renumber section headers, descending
for n in range(16, 2, -1):
    text = re.sub(rf"^## {n}\. ", f"## \x00{n + 1}\x00. ", text, flags=re.M)
# 3) subsection-style references such as "第 8.4 与 10.2 节"
text = text.replace("第 8.4 与 10.2 节", "第 9.4 与 11.2 节")
text = re.sub(r"第 8\.4 节", "第 9.4 节", text)
text = re.sub(r"第 10\.2 节", "第 11.2 节", text)

text = text.replace("\x00", "")

# 4) header / verification-count touch-ups
text = text.replace(
    "# AI-UWM 下一轮（R2）模拟：情景设置与实施方案 v2（代码基准版）",
    "# AI-UWM 下一轮（R2）模拟：情景设置与实施方案 v3（现实性审计版）",
)
text = text.replace(
    "**10 项机器自检（V1–V10，两域各 10/10 通过）**，见第 14 节",
    "**12 项机器自检（V1–V12，两域各 12/12 通过）** + **19 项现实性审计判据（两域各 17 PASS / 2 NOTE / 0 FAIL）**，分别见第 14 节与第 3 节",
)
text = text.replace("## 14. 自检结果 V1–V10【计算】（两域各 10/10 通过）",
                    "## 14. 自检结果 V1–V12【计算】（两域各 12/12 通过）")

DOC.write_text(text, encoding="utf-8")
print("renumbered ->", DOC)
for line in text.splitlines():
    if line.startswith("## "):
        print(line)
