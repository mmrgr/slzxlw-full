"""修正 SI 中把机制归因于"高盐度"的表述 (2026-10-17).

实测依据: committed 分支内
  IEUA    n=60  负=3   正=48
  Figshare n=60 负=3   正=48
  → 两者相同, 差异不来自盐度, 而来自质量约束档位与池水平。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = Path(__file__).resolve().parent.parent / "A16_英文稿/supplementary_information.md"
t = P.read_text(encoding="utf-8")

OLD = (
    "included solver-failed rows. The mechanism is unchanged and occurs only for the high-salinity\n"
    "composition under severe quality tiers."
)
NEW = (
    "included solver-failed rows. The mechanism is unchanged and, in the repaired grid, occurs for\n"
    "the compositions whose constraint binds under severe quality tiers — **not** for salinity as\n"
    "such: within the committed branch IEUA and Figshare RW give the same 48 harmful / 3 beneficial\n"
    "split, so an earlier draft's attribution to \"high salinity\" is not supported."
)

if OLD in t:
    P.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("SI 已同步修正")
else:
    i = t.find("occurs only for the high-salinity")
    print("MISS; 实际上下文 =", repr(t[max(0, i - 120):i + 160]) if i > 0 else "N/A")
