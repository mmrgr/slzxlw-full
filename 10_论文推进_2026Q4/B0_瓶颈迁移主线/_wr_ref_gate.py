# -*- coding: utf-8 -*-
"""参考文献 ↔ 正文引用 一一对应门禁（WR 官方要求）。

规则：
  - 正文用 [n] 引用；每条 [n] 必须在 References 里存在；
  - References 每一条必须至少被正文引用一次（禁止充数）；
  - 编号必须连续、无重复、无空洞。
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
MS = HERE / "04_wr_manuscript_en.md"

RESULTS: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def main() -> None:
    text = MS.read_text(encoding="utf-8")

    m = re.search(r"^## References\s*$", text, re.M)
    if not m:
        print("找不到 References 节")
        return
    body = text[: m.start()]
    refs = text[m.end():]

    # 正文引用：去掉 References 与文件头
    body = re.sub(r"^\*\*Target journal:\*\*.*?\n", "", body, flags=re.M)
    body = re.sub(r"^\*\*Word budget:\*\*.*?\n", "", body, flags=re.M)
    body = re.sub(r"^\*\*Source of numbers:\*\*.*?\n", "", body, flags=re.M)

    cited: set[int] = set()
    # 支持 [3]、[1,9,13]、[1, 9, 13]、[1-3] 多种写法
    for mm in re.finditer(r"\[([\d,\s\-–]+)\]", body):
        chunk = mm.group(1)
        for part in chunk.split(","):
            part = part.strip()
            rng = re.fullmatch(r"(\d+)\s*[-–]\s*(\d+)", part)
            if rng:
                a, b = int(rng.group(1)), int(rng.group(2))
                cited.update(range(min(a, b), max(a, b) + 1))
            elif part.isdigit():
                cited.add(int(part))

    listed: list[int] = []
    for mm in re.finditer(r"^\[(\d+)\]", refs, re.M):
        listed.append(int(mm.group(1)))

    # 2026-10-19 审计修复：原为 ck("References 节存在", True, ...)，恒真。
    # 且 "编号连续 1..N"、"无重复编号" 在 listed 为空时也恒真（[] == []），
    # 于是整个 References 节丢失时这 3 项仍全过。现改为对 listed 非空性做真断言。
    ck("References 节存在且非空", len(listed) > 0, f"{len(listed)} 条")
    ck("编号连续 1..N", listed == list(range(1, len(listed) + 1)),
       f"{listed[:3]}…{listed[-3:]}" if listed else "")
    ck("无重复编号", len(listed) == len(set(listed)), "")
    ck("正文引用了某条参考文献", len(cited) > 0, f"引用到 {sorted(cited)}")

    missing = sorted(cited - set(listed))
    uncited = sorted(set(listed) - cited)
    ck("正文所有 [n] 都在 References 中", not missing, f"缺 {missing}")
    ck("References 每条都被正文引用（无充数）", not uncited, f"未引用 {uncited}")

    npass = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"\n参考文献门禁　通过 {npass}/{len(RESULTS)}")
    for name, ok, detail in RESULTS:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    if cited:
        print(f"\n正文引用编号：{sorted(cited)}")
    if uncited:
        print(f"未被引用的条目：{uncited}  ← 投稿前必须删除或补引")
    # 2026-10-19 审计修复：补正确退出码。此前无 sys.exit，失败只靠 ❌ 传递，
    # 而父门禁曾以 gbk 解码导致 ❌ 检测失效 → 该门禁无论成败都判通过。
    sys.exit(0 if npass == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
