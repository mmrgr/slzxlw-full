"""给 structure_gate 增加 SI 范围一致性检查 (2026-10-17).

【背景】主稿写 "Information (S1–S20)"，但 SI 已有 S21（本轮新增路径敏感性）。
这是典型的"文档扩张后引用范围没跟着改"。

【检查】主稿/SI/投稿文档中出现的 S<n>–S<m> 范围，其终点必须等于 SI 实际最大章节号。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "A41_全包审计/structure_gate.py"
SI = ROOT / "A16_英文稿/supplementary_information.md"

t = GATE.read_text(encoding="utf-8")

BLOCK = '''
    # 6. SI 章节范围引用必须覆盖实际最大编号 (2026-10-17)
    _si = (ROOT / "A16_英文稿/supplementary_information.md").read_text(encoding="utf-8")
    _si_nums = [int(x) for x in re.findall(r"^#{2,3} S(\\d+)\\.", _si, re.M)]
    _si_max = max(_si_nums) if _si_nums else 0
    _bad_range = []
    for _m in re.finditer(r"S(\\d+)\\s*[\\u2013-]\\s*S?(\\d+)", t):
        if _si_max and int(_m.group(2)) != _si_max:
            _bad_range.append(f"S{_m.group(1)}-S{_m.group(2)} (SI 实际到 S{_si_max})")
    print(f"  [{'PASS' if not _bad_range else 'FAIL'}] SI 范围引用一致 "
          f"(SI 最大 S{_si_max}, 越界 {len(_bad_range)})")
    if _bad_range:
        for _b in _bad_range:
            print(f"        {_b}")
        fails += 1

'''

anchor = "\n    print()\n    print(f\"裁定:"
if anchor not in t:
    print("未找到插入点")
else:
    t = t.replace(anchor, BLOCK + anchor, 1)
    GATE.write_text(t, encoding="utf-8")
    print("已插入 SI 范围检查")
