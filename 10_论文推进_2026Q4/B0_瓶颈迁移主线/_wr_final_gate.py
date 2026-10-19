# -*- coding: utf-8 -*-
"""WR 投稿包总门禁：一次跑完全部检查。

用法:
    python _wr_final_gate.py
退出码 0 = 全过。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
PY = sys.executable


def _has_failure_marker(out: str) -> bool:
    """判断子门禁输出是否含失败信号。

    ⚠ 2026-10-19 审计修复：旧实现只检查 "❌" 与大写 "FAIL"，且**以 gbk 解码**
    子进程输出。中文经 gbk 解码后 "❌" 变成 "鉁�"，于是 `"❌" in out` 恒为 False，
    而 `_wr_gate.py` / `_wr_ref_gate.py` / `_wr_num_gate.py` / `_wr_num_reverse.py` /
    `_si_num_gate.py` / `_wr_package_check.py` 这 6 个子门禁**没有 sys.exit**，
    失败时仅打印 "❌" 与 "未命中"/"FAIL n 项"。二者叠加的结果是：
    这 6 道门禁**无论成败都被判为通过**（实测注入假数字仍返回 ok=True）。

    现改为 UTF-8 解码 + 显式失败标记白名单，并对"未命中 N>0"这类计数式失败
    做数值解析，避免只靠图标字符。
    """
    if not out:
        return False
    t = out
    # 只认明确失败图标。⚠ 不可把 "×" 当作失败标记 —— 多个门禁的输出里含
    # "315×"、"15×"、"6×" 之类倍数符号（Bowers 核验、CO 差距核验），
    # 误判会让 9/9、14/14 全过的门禁被标红。
    if "❌" in t:
        return True
    # 明确的失败字样（大小写不敏感），但排除"通过/全部通过"语境里的普通词
    up = t.upper()
    for kw in ("TRACEBACK (MOST RECENT CALL LAST)", "MISSING"):
        if kw in up:
            return True
    # "FAIL n 项"（n>0）
    for m in re.finditer(r"FAIL\s*(\d+)\s*项", t):
        if int(m.group(1)) > 0:
            return True
    # 孤立的 FAIL 标记（行首/空白后，后面不是数字 0）
    for m in re.finditer(r"(?:^|\s)FAIL(?:\s|$)", t):
        return True
    # 计数式失败："未命中: N" / "唯一未命中: N"
    for m in re.finditer(r"(?:唯一)?未命中[：: ]*(\d+)", t):
        if int(m.group(1)) > 0:
            return True
    # "通过 a/b" 中 a < b
    for m in re.finditer(r"通过\s*(\d+)\s*/\s*(\d+)", t):
        if int(m.group(1)) < int(m.group(2)):
            return True
    for m in re.finditer(r"合计\s*(\d+)\s*/\s*(\d+)", t):
        if int(m.group(1)) < int(m.group(2)):
            return True
    return False

SCRIPTS = [
    ("WR 稿规格门禁（词数/摘要/Highlights/结构/强度）", "_wr_gate.py"),
    ("参考文献双向对应门禁（正文↔文献表）", "_wr_ref_gate.py"),
    ("跨语言数字门禁（英文稿无母稿外新数字）", "_wr_num_gate.py"),
    ("反向数字门禁（核心数字未被压缩掉）", "_wr_num_reverse.py"),
    ("SI 数字门禁（SI 无母稿外新数字）", "_si_num_gate.py"),
    ("双基底分类学核验（17 项）", "_verify_dualbase.py"),
    ("三杠杆 50 MW 同网格核验（18 项）", "_verify_reuse_levers_50mw.py"),
    ("k* 敏感性表独立复算（29 项）", "_verify_kstar_table.py"),
    ("r* 参数锚定与敏感性核验（18 项）", "_verify_rstar_anchoring.py"),
    ("GAMA 外部锚定复算（26 项）", "_verify_gama_anchor.py"),
    ("C_p 精度反解复算（20 项）", "_verify_cp_precision.py"),
    ("UWMP 原始 PDF 核验（20 项）", "_verify_uwmp_pdf.py"),
    ("UWMP 水质证据核验（11 项）", "_verify_uwmp_quality.py"),
    ("冷却技术档×Bowers 核验（9 项）", "_verify_bowers_benchmark.py"),
    ("技术档敏感性核验（11 项）", "_verify_tech_sensitivity.py"),
    ("技术档网格收敛核验（20 项）", "_verify_tech_grid.py"),
    ("CO 端联合-纯物理差距核验（14 项）", "_verify_co_gap.py"),
    ("CO 端三网格检验（17 项）", "_verify_co_grid.py"),
    ("非 informative 范围依赖核验（25 项）", "_verify_noninformative_range.py"),
    ("解析边界核验（17 项）", "_verify_analytic_boundary.py"),
    ("CoC/交付张力核验（24 项）", "_verify_coc_reff_disclosure.py"),
    ("legacy 路径披露核验（22 项，含引擎修复）", "_verify_legacy_path.py"),
    ("2×2 路径归因核验（20 项，修复后）", "_verify_two_path_attribution.py"),
    ("引擎修复回归守卫（24 项）", "_verify_engine_fix_guard.py"),
    ("图件编号一致性（26 项）", "_verify_figure_numbering.py"),
    ("6%/26% 来源链核验（17 项）", "_verify_share_provenance.py"),
    ("干预两两交互核验（20 项）", "_verify_interactions.py"),
    ("中文母稿全局门禁（102 项）", "_final_check.py"),
    ("投稿包完整性（文件齐备 + 官方格式）", "_wr_package_check.py"),
]


def main() -> int:
    allok = True
    summary = []
    for label, script in SCRIPTS:
        p = HERE / script
        if not p.exists():
            summary.append((label, None, "MISSING"))
            allok = False
            continue
        r = subprocess.run([PY, str(p)], cwd=str(HERE),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        out = (r.stdout or "") + (r.stderr or "")
        ok = r.returncode == 0 and not _has_failure_marker(out)
        # 提取形如 "通过 a/b" 的计数
        m = re.search(r"通过\s*(\d+)/(\d+)", out)
        detail = f"{m.group(1)}/{m.group(2)}" if m else ("OK" if ok else "见输出")
        if "全部通过" in out or "全过" in out:
            detail += " 全部通过"
        summary.append((label, ok, detail))
        if not ok:
            allok = False
            print(f"\n{'='*72}\n[{script}] 输出：\n{out[-2500:]}")

    print(f"\n{'='*72}\nWR 投稿包总门禁\n{'='*72}")
    for label, ok, detail in summary:
        mark = "✅" if ok else "❌"
        print(f"  {mark} {label:<52}{detail}")
    print("=" * 72)
    print("全部通过" if allok else "存在失败项")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
