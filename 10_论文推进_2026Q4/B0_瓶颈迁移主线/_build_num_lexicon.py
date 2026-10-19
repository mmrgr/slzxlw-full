# -*- coding: utf-8 -*-
"""从中文母稿抽取全部数值 token，作为英文稿数字合法性的唯一白名单。

用途：
    python _build_num_lexicon.py
产出：
    _num_lexicon.json  —— { 规范化数字 -> [中文母稿中的出现上下文...] }
    _num_lexicon.md    —— 人工可读清单

判定规则（用于 _wr_gate.py）：
    英文稿中出现的每个数值，其规范化形式必须命中本白名单；
    未命中者必须登记在 _num_allowlist_extra.json（并注明理由）。
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SRC = HERE / "03_主稿_v2.md"

# 数字 token：整数、小数、科学计数、带千分位、带负号/正负号
NUM_RE = re.compile(
    r"(?<![A-Za-z_])"
    r"([+\-−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?"
    r"|[+\-−]?(?:\d+\.\d+|\d+)(?:[eE][+\-]?\d+)?"
    r"|10\^?\{?[−\-]?\d+\}?"
    r")"
)

# 这些不是"论文数值"，是编号/章节/年份/文件名等，白名单外允许
STRUCTURAL = re.compile(
    r"^(?:§|图|表|第|见|如|和|与|或|的|至|到|个|条|项|类|次|轮|年|月|日|版|v)"
)


def norm(tok: str) -> str:
    """规范化：去千分位、统一负号、去前导 +、去尾随 .0 之外的冗余。"""
    t = tok.replace(",", "").replace("−", "-").replace("--", "-")
    t = t.lstrip("+")
    if re.fullmatch(r"-?\d+\.0+", t):
        t = t.split(".")[0]
    return t


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    lines = text.split("\n")

    lex: dict[str, list[str]] = defaultdict(list)
    total = 0
    for ln, line in enumerate(lines, 1):
        # 跳过代码块与表格分隔线不影响：全部保留，宁可多留
        for m in NUM_RE.finditer(line):
            tok = m.group(1)
            key = norm(tok)
            total += 1
            if len(lex[key]) < 6:
                ctx = line[max(0, m.start() - 45): m.end() + 45].strip()
                ctx = ctx.replace("|", "/")
                lex[key].append(f"L{ln}: …{ctx}…")

    out = {
        "source": str(SRC.relative_to(HERE)),
        "n_tokens": total,
        "n_unique": len(lex),
        "lexicon": dict(sorted(lex.items(), key=lambda kv: kv[0])),
    }
    (HERE / "_num_lexicon.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    # 人工可读
    md = [
        "# 数字白名单（源自中文母稿）",
        "",
        f"- 来源：`{out['source']}`",
        f"- token 总数：{total}；唯一数值：{len(lex)}",
        "- **英文稿中出现的每个数值都必须命中本清单**（或登记在 `_num_allowlist_extra.json`）。",
        "",
        "| 数值 | 母稿上下文（最多 3 条） |",
        "|---|---|",
    ]
    for k, v in sorted(lex.items(), key=lambda kv: (len(kv[0]), kv[0])):
        ctxs = "<br>".join(x.replace("`", "'") for x in v[:3])
        md.append(f"| `{k}` | {ctxs} |")
    (HERE / "_num_lexicon.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"OK  token={total}  unique={len(lex)}  -> _num_lexicon.json / .md")


if __name__ == "__main__":
    main()
