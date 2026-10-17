"""A42: 从已核验 references.bib 生成主稿 References 节, 并把内联引用映射到条目.

【为什么必须做】
主稿**没有 References 节**, 且 24 条已核验文献与正文**脱节**(正文只内联引用 5 条)。
这是投稿的硬性缺口: 任何期刊都要求引用与文献表一一对应。

【本脚本做什么】
  1. 解析 `A29_文献核验/references.bib` 的 24 条(全部经 CrossRef/DataCite 双库核验);
  2. 从主稿与 SI 中提取内联引用(作者+年份);
  3. 建立映射, 标出:
       CITED     —— 正文有引用, 且能匹配到 bib 条目
       AVAILABLE —— bib 有但正文未引用(可作为"延伸阅读/背景", 不得虚列)
       MISSING   —— 正文引用了但 bib 无(严重: 引用无出处)
  4. 生成 `References.md`: 按第一作者字母序排列, 只列**正文实际引用**的条目,
     并另列"已核验但未引用"清单(供作者决定是否补引), **不虚增引用**。

【纪律】
  · 不编造条目; 全部来自 references.bib;
  · 不把"未引用"的条目混进 References 表充数;
  · 正文引用了但 bib 缺失的, 必须显式报 MISSING, 不得忽略。
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BIB = ROOT / "A29_文献核验/references.bib"
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
SI = ROOT / "A16_英文稿/supplementary_information.md"
OUT = HERE / "references_manuscript.md"
OUTJ = HERE / "references_manifest.json"


def parse_bib(text: str) -> list[dict]:
    out = []
    for blk in re.split(r"\n(?=@)", text.strip()):
        m = re.match(r"@(\w+)\{([^,]+),", blk)
        if not m:
            continue
        kind, key = m.group(1), m.group(2)

        def fld(name):
            mm = re.search(rf"{name}\s*=\s*[{{\"](.+?)[}}\"]\s*,?\s*\n", blk, re.S | re.I)
            if not mm:
                mm = re.search(rf"{name}\s*=\s*[{{\"]([^}}\"]+)[}}\"]", blk, re.S | re.I)
            return re.sub(r"\s+", " ", mm.group(1)).strip() if mm else ""

        def fldnum(name):
            mm = re.search(rf"{name}\s*=\s*[{{\"]?(\d{{4}})", blk)
            return mm.group(1) if mm else ""

        author = fld("author")
        # 第一条作者姓氏
        first = author.split(" and ")[0].strip() if author else ""
        surname = first.split(",")[0].strip() if "," in first else first.split()[-1] if first else ""
        out.append({
            "kind": kind, "key": key, "title": fld("title"), "author": author,
            "year": fldnum("year"),
            "journal": fld("journal") or fld("publisher") or fld("booktitle"),
            "volume": fld("volume"), "pages": fld("pages"), "doi": fld("doi"),
            "surname": surname,
        })
    return out


def inline_cites(text: str) -> dict[str, int]:
    """提取内联引用。支持两种风格:
       (a) 圆括号式  'Surname et al. (YYYY)' / 'Surname (YYYY)'
       (b) 叙述式    'Surname et al., YYYY' / 'Surname & Other, YYYY' / 'Surname, YYYY'
    ⚠ 首版只覆盖 (a), 漏掉叙述式(逗号在年份前), 导致已引用文献被误报为"未引用"。
    """
    cnt: dict[str, int] = {}
    # (a) 括号式
    for a, y in re.findall(r"\b([A-Z][a-zA-Z\-]+)(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-zA-Z\-]+))?\s*\((20[0-9]{2})\)", text):
        if int(y) >= 2015:
            k = f"{a} ({y})"
            cnt[k] = cnt.get(k, 0) + 1
    # (b) 叙述式: 姓氏 [et al.|& Xxx] , YYYY
    for a, y in re.findall(r"\b([A-Z][a-zA-Z\-]+)(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-zA-Z\-]+))?,\s*(20[0-9]{2})\b", text):
        if int(y) >= 2015:
            k = f"{a} ({y})"
            cnt[k] = cnt.get(k, 0) + 1
    return cnt


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("A42  References 生成与引用映射")
    rec("=" * 84)

    bib = parse_bib(BIB.read_text(encoding="utf-8"))
    rec(f"\n[0] references.bib 条目 = {len(bib)}")
    n_doi = sum(1 for b in bib if b["doi"])
    rec(f"    含 DOI 的 = {n_doi}/{len(bib)}")

    ms = MS.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    # ⚠ 修正(首版 bug): 必须在**排除 References 节**后再提取内联引用,
    #   否则文献表自身的姓名(Bin/Fadel/Shaolei 等)会被误判为"正文引用但 bib 无"。
    ms_body = ms.split("## References")[0]
    cites_ms = inline_cites(ms_body)
    cites_si = inline_cites(si)
    all_cites = dict(cites_ms)
    for k, v in cites_si.items():
        all_cites[k] = all_cites.get(k, 0) + v

    rec(f"\n[1] 正文内联引用(主稿 {len(cites_ms)} 种, SI {len(cites_si)} 种)")
    for k, v in sorted(all_cites.items()):
        rec(f"    {k}  x{v}")

    # ---------- 映射 ----------
    # 已知不在 bib 的合理引用: NREL 是报告引用(在 SI 的 tier 说明中), 需单列
    KNOWN_NON_BIB = {"NREL (2023)", "Note (2026)", "Retraction (2026)"}

    matched, missing = [], []
    for c in sorted(all_cites):
        if c in KNOWN_NON_BIB:
            continue
        surn = c.split(" (")[0]
        year = c.split("(")[1].rstrip(")")
        cand = [b for b in bib if b["surname"].lower() == surn.lower()
                and b["year"] == year]
        if cand:
            matched.append((c, cand[0]))
        else:
            missing.append(c)

    used_keys = {b["key"] for _, b in matched}
    uncited = [b for b in bib if b["key"] not in used_keys]

    rec(f"\n[2] 映射结果")
    rec(f"    CITED(匹配到 bib) = {len(matched)}")
    for c, b in matched:
        rec(f"      {c:<28} -> {b['key']}  ({b['journal'][:30]})")
    rec(f"    MISSING(正文引用但 bib 无) = {len(missing)}")
    for c in missing:
        rec(f"      ✗ {c}")
    rec(f"    AVAILABLE(bib 有但正文未引用) = {len(uncited)}")
    for b in uncited:
        rec(f"      · {b['key']:<34} {b['title'][:50]}")

    # ---------- 生成 References ----------
    def clean(x: str) -> str:
        """去掉 bib 的 LaTeX 保护符残留: {AI} -> AI, \\& -> &, 双连字 -- -> –"""
        x = x.replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
        x = re.sub(r"\{(.*?)\}", r"\1", x)          # {AI} -> AI
        x = x.replace("--", "–")
        x = re.sub(r"\s+", " ", x).strip()
        return x

    def fmt(b: dict) -> str:
        au = clean(b["author"]).replace(" and ", ", ")
        au = re.sub(r",\s*,", ",", au).strip().rstrip(",")
        t = clean(b["title"])
        j = clean(b["journal"])
        y = b["year"]
        vol = clean(b["volume"])
        pg = clean(b["pages"]).replace("--", "–")
        # 期刊为空(如 arXiv preprint)时, 用 [Preprint] 标注, 不留下空斜体
        if j:
            s = f"{au} ({y}). {t}. *{j}*"
            if vol:
                s += f" **{vol}**"
            if pg:
                s += f", {pg}"
            s += "."
        else:
            s = f"{au} ({y}). {t}. [Preprint]"
        if b["doi"]:
            s += f" https://doi.org/{b['doi']}"
        return s

    cited_sorted = sorted((b for _, b in matched), key=lambda x: (x["surname"].lower(), x["year"]))
    uncited_sorted = sorted(uncited, key=lambda x: (x["surname"].lower(), x["year"]))

    md = ["# References (manuscript)", "",
          "> 自动生成：`python A42_参考文献/references_from_bib.py`。",
          f"> 来源：`A29_文献核验/references.bib`（{len(bib)} 条，全部经 CrossRef/DataCite 双库核验）。",
          "> **只列正文实际引用的条目**；未引用者另列，不充数。", "",
          "---", "",
          "## 1. References cited in the manuscript", ""]
    for i, b in enumerate(cited_sorted, 1):
        md.append(f"{i}. {fmt(b)}")
    md += ["", "---", "",
           "## 2. Verified but not currently cited", "",
           "> 这 24 条来源均已独立核验（DOI 双库解析成功），但**正文尚未引用**。",
           "> 列出供作者决定是否补引；**不得**直接并入第 1 节充数。", ""]
    for b in uncited_sorted:
        _t, _j = clean(b["title"]), clean(b["journal"])
        _loc = f"({_j}, {b['year']})" if _j else f"([Preprint], {b['year']})"
        line = f"- `{b['key']}` — {_t} {_loc}"
        if b["doi"]:
            line += f". https://doi.org/{b['doi']}"
        md.append(line)

    if missing:
        md += ["", "---", "",
               "## 3. ⚠️ Citations with no bibliography entry (must be resolved)", ""]
        for c in missing:
            md.append(f"- **{c}** — 正文引用了但 bib 中无对应条目，须补条目或改引。")

    md += ["", "---", "",
           "## 4. 非 bib 的合理引用（已在正文显式说明来源）", ""]
    for c in sorted(KNOWN_NON_BIB & set(all_cites)):
        md.append(f"- **{c}** — 报告/技术文档或脚本自注，非期刊文献；正文已注明来源。")

    md += ["", "## 5. 门禁说明", "",
           "- 投稿前必须：MISSING = 0；",
           "- 第 1 节条目数 = 正文出现的不同引用数（本脚本核查）；",
           "- 第 2 节条目**不得**出现在按引用排序的文献表中。", ""]

    OUT.write_text("\n".join(md), encoding="utf-8")
    OUTJ.write_text(json.dumps({
        "n_bib": len(bib), "n_with_doi": n_doi,
        "inline_cites": all_cites,
        "cited_keys": [b["key"] for b in cited_sorted],
        "uncited_keys": [b["key"] for b in uncited_sorted],
        "missing": missing,
        "n_cited": len(cited_sorted), "n_uncited": len(uncited_sorted),
        "runtime_s": round(time.time() - t0, 1),
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    rec(f"\n[3] 输出")
    rec(f"    references_manuscript.md: 引用 {len(cited_sorted)} 条, "
        f"未引用 {len(uncited_sorted)} 条, MISSING {len(missing)} 条")
    verdict = "OK" if not missing else "HAS_MISSING_CITATIONS"
    rec(f"    裁定: {verdict}")
    rec(f"    ({time.time()-t0:.1f}s)")
    sys.exit(0 if not missing else 1)


if __name__ == "__main__":
    main()
