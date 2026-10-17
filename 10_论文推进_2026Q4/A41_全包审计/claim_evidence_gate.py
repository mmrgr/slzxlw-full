"""专项门禁: 机制类强声明必须有 SI 证据支撑 (2026-10-17).

【为何需要】
七套现有门禁检查的是"数字是否一致""图与正文是否一致""引用是否齐全",
但**不检查**"正文的机制声明是否在 SI 中有对应证据"。
阶段2 发现: 主稿曾写 "path-dependent ... convention-dependent" 却没有任何量化证据;
"a high-salinity source reverses the sign" 也无证据且是错的。
这类"无证据的机制断言"是最危险的 AI 技术债——它读起来像结论, 实则没有支撑。

【检查项】
对一组**关键词/句式**, 要求: 若主稿出现, 则 SI 必须出现对应证据标记。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
SI = ROOT / "A16_英文稿/supplementary_information.md"

# (声明名, 主稿触发正则, SI 必须包含的证据标记列表[任一满足], 说明)
RULES: list[tuple[str, str, list[str], str]] = [
    ("路径依赖机制声明",
     r"path-dependent|solver-path|volume-only",
     ["S21", "ne5b_path_physics", "ne5c_convergence", "ne5d_direction"],
     "声称机制路径依赖, 必须给出双路径对照证据 (SI S21)"),
    ("面板不变量声明",
     r"not panel-invariant",
     ["panel", "strict", "NE-2", "ne2_panel"],
     "声称不跨限值档稳健, 必须有分档证据"),
    ("800× 量级声明",
     r"800\s*×|800-fold|≈800",
     ["NE1", "NE-1", "ne1_r10a"],
     "声称量级差 800×, 必须有 NE-1 证据"),
    ("partial identification 声明",
     r"not identified|provable bounds",
     ["a24b", "partial_id", "[0%, 100%]"],
     "声称不可识别+区间, 必须有 partial-ID 证据"),
    ("高盐度归因声明",
     r"high-salinity.{0,40}(revers|flip)|salinity.{0,20}(reverses|flips)",
     ["not supported", "not for salinity as such", "3 / 48", "3/48"],
     "若仍保留'高盐度翻转'表述, 必须有反证或撤回说明"),
]


def main() -> int:
    ms = MS.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    print("=" * 76)
    print("机制声明证据门禁")
    print("=" * 76)
    fails = 0
    for name, pat, markers, why in RULES:
        in_ms = bool(re.search(pat, ms, re.I))
        hit = next((m for m in markers if m in si), None)
        if not in_ms:
            print(f"  [SKIP] {name}: 主稿未出现该声明")
            continue
        if hit:
            print(f"  [PASS] {name}: SI 含证据标记 {hit!r}")
        else:
            print(f"  [FAIL] {name}: 主稿有声明但 SI 缺证据 ({why})")
            fails += 1
    print()
    print(f"裁定: {'全部有证据支撑 ✓' if fails == 0 else f'{fails} 项无证据支撑 ✗'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
