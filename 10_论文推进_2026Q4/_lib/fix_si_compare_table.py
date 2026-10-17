"""修正 SI 新旧对照表右列 (2026-10-17).

右列应为**当前 cited-limit 运行**的实测值(truth_source), 但仍残留旧值。
左列 = 旧 placeholder-limit 运行(保留作对照), 正确。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_lib"))
from truth_source import TRUTH  # noqa: E402

SI = ROOT / "A16_英文稿/supplementary_information.md"
t = SI.read_text(encoding="utf-8")

OLD_BLOCK = """| reliable scenarios | 1,094 | **839** |
| withdrawal falls | 729 | **631** |
| **withdrawal rises** | **285** | **102** |
| zero-displacement | 441 | 372 |
| $q>0$ | 329 | 263 |
| $q>0$ but harmful | 0 | **0** |
| identity residual (ML) | 1.16e−10 | **2.55e−11** |
| criterion agreement | 1.0000 | **1.0000** |"""

NEW_BLOCK = (
    f"| reliable scenarios | 1,094 | **{TRUTH['n_reliable']}** |\n"
    f"| withdrawal falls | 729 | **{TRUTH['neg']}** |\n"
    f"| **withdrawal rises** | **285** | **{TRUTH['pos']}** |\n"
    f"| zero-displacement | 441 | {TRUTH['nodisp']} |\n"
    f"| $q>0$ | 329 | {TRUTH['q_pos']} |\n"
    f"| $q>0$ but harmful | 0 | **{TRUTH['q_pos_harmful']}** |\n"
    f"| identity residual (ML) | 1.16e−10 | **{TRUTH['resid_abs']:.2e}** |\n"
    f"| criterion agreement | 1.0000 | **1.0000** |"
)

if OLD_BLOCK in t:
    t = t.replace(OLD_BLOCK, NEW_BLOCK, 1)
    SI.write_text(t, encoding="utf-8")
    print("SI 对照表右列已修正为实测值:")
    for line in NEW_BLOCK.split("\n"):
        print("   ", line)
else:
    print("MISS: 未找到整块, 尝试逐行")
    for a, b in [
        ("| withdrawal falls | 729 | **631** |",
         f"| withdrawal falls | 729 | **{TRUTH['neg']}** |"),
        ("| **withdrawal rises** | **285** | **102** |",
         f"| **withdrawal rises** | **285** | **{TRUTH['pos']}** |"),
        ("| zero-displacement | 441 | 372 |",
         f"| zero-displacement | 441 | {TRUTH['nodisp']} |"),
        ("| identity residual (ML) | 1.16e−10 | **2.55e−11** |",
         f"| identity residual (ML) | 1.16e−10 | **{TRUTH['resid_abs']:.2e}** |"),
    ]:
        if a in t:
            t = t.replace(a, b, 1)
            print("   已修:", a[:40])
    SI.write_text(t, encoding="utf-8")
