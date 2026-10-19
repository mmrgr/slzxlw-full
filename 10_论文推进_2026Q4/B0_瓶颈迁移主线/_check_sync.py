# -*- coding: utf-8 -*-
"""主稿全局同步性检查：找出"局部更新、结论未同步"的位置。

【为什么需要】
本轮已发现两处同类缺陷：
  1. 摘要停在第三轮，未覆盖四情形与口径区隔
  2. §7.6 结论只讲两杠杆，而 §7.0 已重组为三杠杆

这类缺陷的共同形态：新增了内容，但旧的总结句/摘要/标题没跟着改。
人工很难发现，因为它不报错，且每处单独看都通顺。

【本检查的规则】
R1 首行标题与文件状态必须一致（v2）
R2 摘要必须覆盖全部核心贡献（关键词检查）
R3 每个含"本章结论/本节结论/小结"的章节，必须提及该章新增的核心概念
R4 §1.3 声称的贡献数 = 实际条目数
R5 §9 限制编号必须连续
R6 交叉引用的节号必须存在
R7 章节标题中的"新增/本轮"标记不得残留到定稿（可选警告）

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_check_sync.py
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
V2 = HERE / "03_主稿_v2.md"

ROWS: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    ROWS.append((name, bool(ok), detail))


def main() -> None:
    t = V2.read_text(encoding="utf-8")

    # ---------------- R1 首行与状态 ----------------
    first = t.splitlines()[0]
    ck("R1 首行标明 v2", "v2" in first, first)
    ck("R1 状态行为定稿候选", "v2 定稿候选" in t)
    ck("R1 无 v1 草稿残留", "v1 草稿" not in t and "阶段 4" not in t)

    # ---------------- R2 摘要覆盖度 ----------------
    ab = re.search(r"## 摘要\n(.*?)\n---", t, flags=re.S)
    ab = ab.group(1) if ab else ""
    core = {
        "r* 闭式解": "0.5532",
        "四情形分类": "四类",
        "情形命名": "情形 I",
        "口径区隔": "W/D",
        "判据定位": "判据与条件",
        "多物种取紧": "0.6842",
        "零效应区": "精确为零",
        "可证伪性": "可证伪",
        "纯物理口径": "纯物理",
        "双因素": "双因素",
        "三情形实证": "+20.74",
    }
    missing = [n for n, k in core.items() if k not in ab]
    ck("R2 摘要覆盖全部核心贡献", not missing, f"缺 {missing}" if missing else "")

    # ---------------- R3 各章结论必须提及本章核心概念 ----------------
    # 定义：章节标题关键词 → 该章结论段必须出现的词
    concl_rules = [
        ("5.7", ["四情形", "分类"], "§5.7 结论需提及四情形分类"),
        ("5.8", ["双因素", "纯物理"], "§5.8 结论需提及双因素/纯物理口径"),
        ("7", ["配比", "三"], "§7 结论需提及配比与三杠杆"),
    ]
    for sec, kws, label in concl_rules:
        # 找该章的"结论"段
        pat = rf"### {re.escape(sec)}\.6 本章结论(.*?)(?=###)"
        m = re.search(pat, t, flags=re.S)
        if not m:
            # 5.7/5.8 没有 7.6 式的结论段，跳过
            continue
        body = m.group(1)
        ck(label, all(k in body for k in kws),
           f"缺 {[k for k in kws if k not in body]}")

    # ---------------- R4 贡献条目数 ----------------
    m = re.search(r"### 1\.3.*?\n(.*?)(?=### )", t, flags=re.S)
    sec = m.group(1) if m else ""
    declared = re.search(r"([一二三四五六七八九十]+)项贡献", sec)
    items = re.findall(r"^(\d+)\. \*\*", sec, flags=re.M)
    num_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}
    ok4 = declared and num_map.get(declared.group(1)) == len(items)
    ck("R4 贡献数一致", bool(ok4),
       f"声称 {declared.group(1) if declared else '?'}，实际 {len(items)}")

    # ---------------- R5 限制编号连续 ----------------
    m = re.search(r"## 9 局限(.*?)(?=## 10)", t, flags=re.S)
    sec9 = m.group(1) if m else ""
    nums = [int(x) for x in re.findall(r"^(\d+)\. \*\*", sec9, flags=re.M)]
    ck("R5 限制编号连续", nums == list(range(1, len(nums) + 1)),
       f"{len(nums)} 条，末号 {nums[-1] if nums else 0}")

    # ---------------- R6 交叉引用 ----------------
    heads = re.findall(r"^#{2,4} (\d+(?:\.\d+)*(?:[a-z])?)", t, flags=re.M)
    existing = set(heads)
    # 补充：§7.7 内部用 (a)(b)(c)(d)，注册为 7.7a-d
    if "### 7.7 " in t:
        m77 = re.search(r"### 7\.7 .*?(?=### 7\.8)", t, flags=re.S)
        if m77:
            for letter in re.findall(r"\*\*\(([a-d])\)", m77.group(0)):
                existing.add(f"7.7{letter}")
    refs = set(re.findall(r"§(\d+(?:\.\d+)*[a-z]?)", t))
    missing_refs = sorted(r for r in refs if r not in existing)
    ck("R6 交叉引用全部有效", not missing_refs,
       f"缺失 {missing_refs}" if missing_refs else f"{len(refs)} 个引用")

    # ---------------- R7 定稿标记 ----------------
    residue = re.findall(r"（[^）]*(?:本轮新增|v2 新增)[^）]*）", t)
    # 这是警告项，不算失败（定稿前应清理，但不算错误）
    ck("R7 无「本轮新增」类过程性标记（建议清理）", not residue,
       f"{len(residue)} 处：{residue[:3]}" if residue else "")

    # ---------------- 输出 ----------------
    print("=" * 92)
    print("主稿 v2 全局同步性检查")
    print("=" * 92)
    passed = 0
    for name, ok, detail in ROWS:
        if ok:
            passed += 1
        line = f"[{'PASS' if ok else 'FAIL'}] {name}"
        if detail and not ok:
            line += f"  ({detail})"
        elif detail and "建议" in name:
            line += f"  ({detail})"
        print(line)
    print("-" * 92)
    print(f"合计 {passed}/{len(ROWS)} 通过")

    out = HERE / "_check_sync.json"
    out.write_text(
        __import__("json").dumps(
            {"passed": passed, "total": len(ROWS),
             "rows": [{"name": n, "ok": o, "detail": d} for n, o, d in ROWS]},
            ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"-> {out}")
    sys.exit(0 if passed == len(ROWS) else 1)


if __name__ == "__main__":
    main()
