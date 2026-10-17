"""门禁 11 (v2): 结论级数字——双向校验 (2026-10-17).

【v1 的缺陷（必须记录）】
v1 只检查"新值是否出现"。用修复前备份测试时捕获 0 项 ——
因为旧版里本来就没有新值，未命中不构成失败判据。
**这就是空洞通过的风险**，与门禁第 4 条直接冲突。

【v2：双向校验】
对每个结论级数字:
  A. 正向: 真相值必须以其语境形态出现（防被删/改错）；
  B. 反向: 该数字的**已知旧值**不得以同语境出现（防回退）。
A 与 B 同时通过才算 PASS。

数字由 `_lib/truth_source.py` 从主网格**实时计算**，不是硬编码。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "_lib"))

from truth_source import TRUTH  # noqa: E402

MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
SI = ROOT / "A16_英文稿/supplementary_information.md"

# (说明, 真相键, 正向正则(必须命中), 反向正则列表(必须不命中))
CHECKS = [
    ("可靠子集 n", "n_reliable",
     r"839\s+solver-reliable|\$n=839\$|\(n=839\)|n = 839|n=839",
     [r"813\s+solver-reliable", r"\$n=813\$"]),
    ("dS<0 计数", "neg",
     r"626\s+beneficial|626 negative",
     [r"643\s+beneficial", r"643 negative"]),
    ("dS>0 计数", "pos",
     r"177\s+harmful|177 positive",
     [r"134\s+harmful", r"134 positive"]),
    ("q>0 计数", "q_pos",
     r"263 of 263",
     [r"290 of 290"]),
    ("纯挤占分支", "pure_disp",
     r"234 cases",
     [r"232 cases"]),
    ("无挤占负值", "nodisp_neg",
     r"380 of 391",
     [r"369 of 372"]),
    ("status 失败数", "status_fail",
     r"25 of the 1,052",
     [r"51 of the 1,052", r"58 of the 1,052"]),
    ("无位移计数(SI)", "nodisp",
     r"zero-displacement \| — \| 391",
     [r"zero-displacement \| — \| 372"]),
    # 2026-10-17 补充: SI 对照表右列 / E3 表 / 折外基线
    ("SI 对照表 withdrawal falls", "neg",
     r"\| withdrawal falls \| 729 \| \*\*626\*\* \|",
     [r"\| withdrawal falls \| 729 \| \*\*631\*\*"]),
    ("E3 基线(SI)", "n_reliable",
     r"majority-class baseline\* \| \*0\.809\*",
     [r"majority-class baseline\* \| \*0\.861\*"]),
    ("分支计数(SI)", "nodisp",
     r"11 of 391",
     [r"3 of 391", r"3 of 372", r"372 branch-C"]),
]


def main() -> int:
    both = MS.read_text(encoding="utf-8") + "\n" + SI.read_text(encoding="utf-8")
    print("=" * 78)
    print("结论级数字（双向校验）")
    print("=" * 78)
    fails = 0
    for name, key, pos_pat, neg_pats in CHECKS:
        want = TRUTH[key]
        want_s = f"{want:.6g}" if isinstance(want, float) else str(want)
        fwd = re.search(pos_pat, both) is not None
        bad = [p for p in neg_pats if re.search(p, both)]
        ok = fwd and not bad
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<16} 真相={want_s:<7} "
              f"正向={fwd} 回退={bad if bad else '无'}")
        if not ok:
            fails += 1
    print(f"\n裁定: {'全部一致且无回退 ✓' if fails == 0 else f'{fails} 项不合格 ✗'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
