"""审计所有门禁脚本的退出码语义 (2026-10-17).

【背景】本轮发现 `make_reproducibility_manifest.py` 完全没有设置退出码,
即使 HAS_FAILURES 也返回 0 —— 因为 run_all_gates 靠匹配输出文本判断, 掩盖了它。
上一轮还发现 `required_statements.py` 注释写"非零退出"但实际 sys.exit(0)。

【本脚本做什么】
对每个门禁脚本, 静态分析其 `__main__` 块与 main() 返回值,
报告它是"会按结果返回非零"还是"恒定返回 0 / 无返回"。
**这是静态审计, 不做动态验证(动态验证见 mutation_test.py)。**
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

GATES = [
    ("终审断言", "A36_终审/final_gate.py"),
    ("图–源一致", "A37_六主图_v4/_gate_check.py"),
    ("复现清单", "A40_投稿包/make_reproducibility_manifest.py"),
    ("全包一致性", "A41_全包审计/package_consistency_check.py"),
    ("机制声明证据", "A41_全包审计/claim_evidence_gate.py"),
    ("结构完整性", "A41_全包审计/structure_gate.py"),
    ("陈旧值黑名单", "A41_全包审计/stale_value_gate.py"),
    ("真相源双向", "A41_全包审计/truth_gate.py"),
    ("文档卫生", "A41_全包审计/hygiene_gate.py"),
    ("形式一致性", "A41_全包审计/form_gate.py"),
    ("新颖性合规", "A41_全包审计/novelty_gate.py"),
    ("参考文献", "A42_参考文献/references_from_bib.py"),
    ("投稿声明", "A43_投稿声明/required_statements.py"),
]


def classify(t: str) -> tuple[str, str]:
    """返回 (判定, 证据)。"""
    tail = t[-1200:]
    # 覆盖所有"按结果条件退出"的写法:
    #   sys.exit(0 if ok else 1) / sys.exit(1 if x else 0)
    #   return 0 if fails == 0 else 1 / sys.exit(1) / raise SystemExit(1)
    has_conditional = bool(re.search(r"return\s+0\s+if\s+.+?\s+else\s+1", tail)) or \
                      bool(re.search(r"sys\.exit\(0\s+if\s+.+?\s+else\s+1\)", tail)) or \
                      bool(re.search(r"sys\.exit\(1\s+if\s+.+?\s+else\s+0\)", tail)) or \
                      bool(re.search(r"sys\.exit\(1\)", tail)) or \
                      bool(re.search(r"raise\s+SystemExit\(1\)", tail))
    exits_zero = bool(re.search(r"sys\.exit\(0\)", tail))
    if has_conditional and not exits_zero:
        return "OK", "有按结果的非零退出"
    if exits_zero and not re.search(r"sys\.exit\(1", tail):
        return "BAD", "存在无条件 sys.exit(0)"
    if not has_conditional and not exits_zero:
        return "WARN", "未见显式退出码（可能靠异常）"
    return "OK", "混合"


def main() -> int:
    print("=" * 72)
    print("门禁退出码语义审计")
    print("=" * 72)
    bad = 0
    for name, rel in GATES:
        p = ROOT / rel
        if not p.exists():
            print(f"  [MISS] {name}: {rel}")
            continue
        verdict, why = classify(p.read_text(encoding="utf-8", errors="replace"))
        mark = {"OK": "PASS", "WARN": "WARN", "BAD": "FAIL"}[verdict]
        print(f"  [{mark}] {name:<14} {why}")
        if verdict == "BAD":
            bad += 1
    print()
    print(f"裁定: {'退出码语义正常 ✓' if bad == 0 else f'{bad} 个脚本无条件返回 0 ✗'}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
