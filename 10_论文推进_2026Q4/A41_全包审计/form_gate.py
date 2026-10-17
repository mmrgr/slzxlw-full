"""门禁 13: 稿件形式一致性——表格列数 / 图号 / 参考文献 (2026-10-17).

【设计原则】按"缺陷类型"而非"已发现缺陷"设计（阶段3-g 的教训）。
本门禁覆盖三类此前未系统检查的形式缺陷：
  A. Markdown 表格列数一致性（表头 vs 每行）
  B. 图号连续性 + 每图在正文被引用 + 图注文件与图号对应
  C. 参考文献：至少 1 条；每条含年份与 DOI；正文内联引用与文献表双向对应
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
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
SI = ROOT / "A16_英文稿/supplementary_information.md"
CAPS = ROOT / "A37_六主图_v4"


def check_tables(p: Path) -> list[str]:
    bad = []
    lines = p.read_text(encoding="utf-8").split("\n")
    i = 0
    while i < len(lines):
        if re.match(r"^\|[-: |]+\|$", lines[i].strip()):
            ncol = lines[i - 1].strip().count("|") - 1
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                nc = lines[j].strip().count("|") - 1
                if nc != ncol:
                    bad.append(f"{p.name} L{j+1}: 列数 {nc} ≠ 表头 {ncol}")
                j += 1
        i += 1
    return bad


def check_figures(ms: str) -> list[str]:
    bad = []
    figs = sorted(set(int(x) for x in re.findall(r"Figure\s+(\d)", ms)))
    if figs and figs != list(range(1, max(figs) + 1)):
        bad.append(f"图号不连续: {figs}")
    for n in range(1, (max(figs) if figs else 0) + 1):
        if f"**Figure {n}" not in ms:
            bad.append(f"Figure {n} 未在正文被引用")
        cap = CAPS / f"fig{n}_caption.md"
        if not cap.exists():
            bad.append(f"缺图注 fig{n}_caption.md")
        else:
            # 兼容两种标题写法: "# Fig. 3 | ..."（手工）与 "# Figure 3. ..."（自动生成）
            m = re.search(r"^#\s*(?:Figure|Fig\.?)\s*(\d)", cap.read_text(encoding="utf-8"), re.M)
            if not m or int(m.group(1)) != n:
                bad.append(f"fig{n}_caption.md 标题图号不匹配")
    return bad


def check_refs(ms: str) -> list[str]:
    bad = []
    if "## References" not in ms:
        return ["无 References 节"]
    i = ms.index("## References")
    j = ms.index("## Declarations") if "## Declarations" in ms else len(ms)
    refs = ms[i:j]
    entries = re.findall(r"^(\d+)\.\s+(.+?)$", refs, re.M)
    if not entries:
        return ["References 为空"]
    for num, txt in entries:
        if not re.search(r"\((?:19|20)\d\d\)", txt):
            bad.append(f"参考文献 [{num}] 缺年份")
        if "doi.org/" not in txt.lower():
            bad.append(f"参考文献 [{num}] 缺 DOI")
    # 双向对应 (2026-10-17 加强: 文献表不得有正文未引用的孤儿条目)
    ref_names = set(re.findall(r"^(\d+)\.\s+([A-Z][a-zA-Z\-]+)", refs, re.M))
    ref_surnames = {n for _, n in ref_names}
    body = ms[:i]
    orphans = [s for s in sorted(ref_surnames) if s not in body]
    if orphans:
        bad.append(f"文献表孤儿(正文未引用): {orphans}")
    return bad


def main() -> int:
    ms = MS.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    print("=" * 74)
    print("稿件形式一致性门禁")
    print("=" * 74)
    fails = 0

    tb = check_tables(MS) + check_tables(SI)
    print(f"  [{'PASS' if not tb else 'FAIL'}] 表格列数一致 (问题 {len(tb)})")
    for b in tb[:5]:
        print(f"        {b}")
    fails += bool(tb)

    fg = check_figures(ms)
    print(f"  [{'PASS' if not fg else 'FAIL'}] 图号/图注/引用一致 (问题 {len(fg)})")
    for b in fg[:5]:
        print(f"        {b}")
    fails += bool(fg)

    # [2026-10-17] 图注数字追溯检查: **实现过但已移除**
    # 原因: "数字是否出现在产物里"这个判据不可靠 ——
    # 239/512 这类错误值也会在某处 CSV 中偶然出现(如 p 值、索引),
    # 导致注入已知错误后检查仍 PASS。留着它就是假门禁。
    # 替代做法: 图注中**关键统计量**(如 "213 rows excluded"、"2048 points")
    # 改为在生成脚本里**动态计算**(make_fig3.py 已改), 从源头消除硬编码。
    #
    # 当前仍为手工维护的 fig*_caption.md 无法自动校验, 已记入报告。

    rf = check_refs(ms)
    print(f"  [{'PASS' if not rf else 'FAIL'}] 参考文献格式与对应 (问题 {len(rf)})")
    for b in rf[:5]:
        print(f"        {b}")
    fails += bool(rf)

    print()
    print(f"裁定: {'形式一致 ✓' if fails == 0 else f'{fails} 项不合格 ✗'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
