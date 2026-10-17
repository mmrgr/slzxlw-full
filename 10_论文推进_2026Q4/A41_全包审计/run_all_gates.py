"""总门禁入口: 一次运行全部 11 道门禁 (2026-10-17).

【为什么需要】
投稿前要跑 11 个脚本、看 11 份输出, 人工容易漏跑或误读。
本脚本串行运行全部门禁, 给出**单一裁定**, 退出码 0=全过。

【用法】
    python A41_全包审计/run_all_gates.py            # 全部
    python A41_全包审计/run_all_gates.py --quick    # 跳过耗时项
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # 10_论文推进_2026Q4

# (编号, 名称, 工作目录, 脚本, 通过标记正则, 是否耗时)
GATES = [
    (1, "终审断言", "A36_终审", "final_gate.py", r"全部通过", False),
    (2, "图–源一致", "A37_六主图_v4", "_gate_check.py", r"GATE PASSED", False),
    (3, "复现清单", "A40_投稿包", "make_reproducibility_manifest.py", r"ALL_CHECKS_PASS", False),
    (4, "全包一致性", "A41_全包审计", "package_consistency_check.py", r"CONSISTENT", False),
    (5, "机制声明证据", "A41_全包审计", "claim_evidence_gate.py", r"全部有证据支撑", True),
    (6, "参考文献", "A42_参考文献", "references_from_bib.py", r"裁定: OK", False),
    (7, "投稿声明", "A43_投稿声明", "required_statements.py", r"占位符", False),
    (8, "结构完整性", "A41_全包审计", "structure_gate.py", r"结构完整", True),
    (9, "陈旧值黑名单", "A41_全包审计", "stale_value_gate.py", r"无陈旧值", True),
    (10, "真相源双向", "A41_全包审计", "truth_gate.py", r"全部一致且无回退", True),
    (11, "文档卫生", "A41_全包审计", "hygiene_gate.py", r"文档卫生 ✓", True),
    (12, "形式一致性", "A41_全包审计", "form_gate.py", r"形式一致 ✓", True),
    (13, "新颖性合规", "A41_全包审计", "novelty_gate.py", r"合规 ✓", True),
    (14, "绝对声称", "A41_全包审计", "absolute_claim_gate.py", r"零例外成立", True),
]

# 文档完整性单独检查(不是脚本)
DOC_FILES = ["A16_英文稿/manuscript_en_v3.md", "A16_英文稿/supplementary_information.md"]


def check_docs() -> tuple[bool, str]:
    bad = []
    for rel in DOC_FILES:
        p = ROOT / rel
        if not p.exists():
            bad.append(f"{rel} 不存在")
            continue
        ctl = [b for b in p.read_bytes() if b < 32 and b not in (9, 10, 13)]
        if ctl:
            bad.append(f"{rel} 有 {len(ctl)} 个控制字节")
    return (not bad), ("; ".join(bad) if bad else "无控制字节")


def main() -> int:
    t0 = time.time()
    print("=" * 78)
    print("AI-UWM 投稿门禁 · 总入口")
    print("=" * 78)
    results = []
    for num, name, wd, script, marker, _slow in GATES:
        d = ROOT / wd
        p = d / script
        if not p.exists():
            print(f"  [{num:>2}] {'MISS':<4} {name:<14} 脚本不存在: {wd}/{script}")
            results.append(False)
            continue
        t = time.time()
        try:
            r = subprocess.run([sys.executable, script], cwd=str(d),
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=1200)
            out = (r.stdout or "") + (r.stderr or "")
            ok = marker in out
        except subprocess.TimeoutExpired:
            out, ok = "TIMEOUT", False
        dt = time.time() - t
        print(f"  [{num:>2}] {'PASS' if ok else 'FAIL':<4} {name:<14} {dt:>5.1f}s")
        if not ok:
            # 打印失败摘要
            for line in out.split("\n"):
                if any(k in line for k in ("FAIL", "✗", "mismatch", "错误", "MISS")):
                    print(f"        {line.strip()[:100]}")
        results.append(ok)

    ok_doc, msg = check_docs()
    print(f"  [15] {'PASS' if ok_doc else 'FAIL':<4} {'文档完整性':<14} {msg}")

    n_pass = sum(results) + int(ok_doc)
    n_total = len(results) + 1
    print()
    print("=" * 78)
    print(f"总判定: {n_pass}/{n_total} 通过"
          + (" ✓ 可投稿" if n_pass == n_total else " ✗ 存在不合格项"))
    print(f"用时 {time.time()-t0:.1f}s")
    print("=" * 78)
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    sys.exit(main())
