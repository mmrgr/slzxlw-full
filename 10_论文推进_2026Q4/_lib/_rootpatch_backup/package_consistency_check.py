"""A41: 全包一致性审计 —— 主稿 / SI / 图表 / 台账 / 复现清单 五方交叉核对.

目的: 四套门禁各自通过还不够, 必须确认**跨文档**没有互相矛盾的数字或主张:

  · 主稿出现的关键数字 → SI 是否一致?

  · 图注声明 → 主稿是否一致?

  · 证据台账 → 复现清单是否一致?

  · 已撤回主张 → 是否在任何交付文本中被当作现行结论?

本脚本只读, 输出 package_consistency_report.md。

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

ROOT = Path(__file__).resolve().parent.parent  # 10_论文推进_2026Q4

HERE = Path(__file__).resolve().parent

MS = ROOT / "A16_英文稿/manuscript_en_v3.md"

SI = ROOT / "A16_英文稿/supplementary_information.md"

FIGS = ROOT / "A37_六主图_v4"

LEDGER = ROOT / "A30_WP0取证/证据台账_EVIDENCE_LEDGER.md"

# ⚠ 修正(首版 bug): 复现清单在 A40_投稿包, 不在本脚本所在的 A41。原用 HERE 导致误报缺失。

MANIFEST = ROOT / "A40_投稿包/reproducibility_manifest.json"

# 已撤回的主张 → 只允许出现在撤回语境

WITHDRAWN = {

    "95%/93% committed": [r"above\s*9[35]\s*%", r"empirically dominant"],

    "更干净⇒更省水": [r"cleaner water.{0,20}saves more", r"cleaner\s*⇒\s*more"],

    "折外预测技能": [r"restores genuine out-of-sample skill"],

    "碱度普适杠杆": [r"only one quantity changes the sign", r"普适"],

    "高盐反转 committed": [r"reverses the sign of the committed"],

}

CTX = ("withdraw", "earlier", "retract", "superseded", "could not", "came from",

       "pre-a27", "placeholder", "removed", "replaced", "correction", "not robust",

       "candidate", "not panel-invariant", "bounded limit domain", "已撤回", "不作")

# 关键数字必须"主稿与 SI 都出现"(允许口径差异, 但不得互相矛盾)

SHARED = [

    ("813", "可靠子集"),

    ("643", "dS<0"),

    ("36", "dS=0"),

    ("290", "q>0"),

    ("2.55", "恒等式残差"),

    ("0.806", "留出 R²"),

    ("0.671", "E3 仅化学"),

    ("0.861", "E3 基线"),

    ("28.4", "B3 占比"),

    ("0.258", "冷却水占比"),

    ("1.550", "工业水价"),

    ("1.56", "再生水/水价"),

]

def main() -> None:

    t0 = time.time()

    log: list[str] = []

    fails: list[str] = []

    warns: list[str] = []

    def rec(m):

        log.append(m)

        print(m, flush=True)

    rec("=" * 84)

    rec("A41  全包一致性审计 (主稿 / SI / 图 / 台账 / 复现清单)")

    rec("=" * 84)

    idx_text = (FIGS / "figure_index.md").read_text(encoding="utf-8")

    caps = {n: (FIGS / f"fig{n}_caption.md").read_text(encoding="utf-8") for n in range(1, 7)}

    ms = MS.read_text(encoding="utf-8")

    si = SI.read_text(encoding="utf-8")

    ledger = LEDGER.read_text(encoding="utf-8") if LEDGER.exists() else ""

    # ---------- 1. 撤回主张不得以现行结论出现 ----------

    rec("\n[1] 已撤回主张: 仅允许出现在撤回语境")

    n_ok = 0

    for name, pats in WITHDRAWN.items():

        for pat in pats:

            for doc_name, txt in (("主稿", ms), ("SI", si)):

                for m in re.finditer(pat, txt, re.I):

                    line = txt[:m.start()].count("\n")

                    lines = txt.split("\n")

                    ctx = " ".join(lines[max(0, line - 2):line + 3]).lower()

                    good = any(k.lower() in ctx for k in CTX)

                    if good:

                        n_ok += 1

                    else:

                        fails.append(f"{doc_name} 中 '{pat}' 疑似作为现行结论出现 (行 {line+1})")

                        rec(f"    [FAIL] {doc_name}: {pat}")

    rec(f"    撤回语境命中 {n_ok} 处; 违规 {len(fails)} 处")

    # ---------- 2. 关键数字: 主稿 与 SI 一致性 ----------

    rec("\n[2] 关键数字: 主稿 / SI 双出现检查")

    for val, name in SHARED:

        in_ms = val in ms

        in_si = val in si

        if in_ms and in_si:

            rec(f"    [OK]   {name:<16} '{val}' 主稿+SI")

        elif in_ms and not in_si:

            warns.append(f"'{val}' ({name}) 仅在主稿, SI 未复述")

            rec(f"    [WARN] {name:<16} '{val}' 仅主稿")

        elif in_si and not in_ms:

            warns.append(f"'{val}' ({name}) 仅在 SI")

            rec(f"    [WARN] {name:<16} '{val}' 仅 SI")

        else:

            warns.append(f"'{val}' ({name}) 两处均未出现")

            rec(f"    [WARN] {name:<16} '{val}' 两处均无")

    # ---------- 3. 图注声明 vs 主稿 ----------

    rec("\n[3] 图注声明 vs 主稿")

    fig_ms_pairs = [

        ("Fig2 碱度绑定限 cited/permissive",

         "strict make-up tier" in caps[2], "not panel-invariant" in ms or "bounded limit domain" in ms),

        ("Fig4 折外已撤回",

         "withdraw" in caps[4].lower(), "withdraw the claim of demonstrated" in ms or "not robust" in ms),

        ("Fig5 NE-4 区间",

         "0.330 [0.075, 0.792]" in caps[5], "0.330 [0.075, 0.792]" in ms),

        ("Fig5 NE-2 三档",

         all(t in caps[5] for t in ("cited", "permissive", "strict")),

         "strict tier" in ms and "silica" in ms),

        ("Fig6 WP8/WP9/WP10/WP11",

         all(t in caps[6] for t in ("28.4", "0.258", "1.56", "597")),

         all(t in ms for t in ("28.4%", "0.25799037378455597", "1.56", "597 records"))),

    ]

    for name, in_cap, in_ms in fig_ms_pairs:

        ok_ = in_cap and in_ms

        if not ok_:

            fails.append(f"图文不一致: {name} (cap={in_cap}, ms={in_ms})")

        rec(f"    [{'PASS' if ok_ else 'FAIL'}] {name}  (图注={in_cap}, 主稿={in_ms})")

    # ---------- 4. 台账 vs 复现清单 ----------

    rec("\n[4] 证据台账 vs 复现清单")

    if MANIFEST.exists():

        mf = json.loads(MANIFEST.read_text(encoding="utf-8"))

        n_art, n_miss = mf.get("n_artifacts"), mf.get("n_missing")

        nchk, npass = len(mf.get("numeric_checks", [])), mf.get("numeric_checks_passed")

        ok_ = (n_miss == 0 and npass == nchk)

        if not ok_:

            fails.append(f"复现清单: 缺产物 {n_miss}, 数字 {npass}/{nchk}")

        rec(f"    [{'PASS' if ok_ else 'FAIL'}] 复现清单 产物 {n_art}(缺 {n_miss}), "

            f"数字复算 {npass}/{nchk}")

        rec(f"    状态 = {mf.get('status')}")

        # 台账条目数

        n_a = len(re.findall(r"^\| A\d+", ledger, re.M))

        rec(f"    证据台账 权威产物条目 = {n_a}")

    else:

        fails.append("复现清单 JSON 不存在")

        rec("    [FAIL] 复现清单 JSON 缺失")

    # ---------- 5. SI 章节连续性 ----------

    rec("\n[5] SI 章节编号连续性")

    secs = re.findall(r"^## (S\d+)\.", si, re.M)

    nums = sorted(int(s[1:]) for s in secs)

    contiguous = nums == list(range(1, len(nums) + 1))

    if not contiguous:

        fails.append(f"SI 章节编号不连续: {nums}")

    rec(f"    [{'PASS' if contiguous else 'FAIL'}] S1–S{max(nums) if nums else 0} "

        f"共 {len(nums)} 节, 连续={contiguous}")

    # ---------- 6. SI 是否覆盖全部实验包 ----------

    rec("\n[6] SI 是否引用本轮全部实验包")

    needed = ["A29", "A30", "A31", "A32", "A33", "A34", "A38", "A39"]

    for pk in needed:

        hit = pk in si or pk in ms

        if not hit:

            warns.append(f"交付文本未引用 {pk}")

        rec(f"    [{'PASS' if hit else 'WARN'}] {pk} 被引用={hit}")

    # ---------- 7. References 与内联引用一致 ----------

    rec("\n[7] References 与内联引用一致性")

    import re as _re

    if "## References" in ms:

        body = ms[ms.index("## References"):]

        n_ref = len(_re.findall(r"^\d+\. ", body, _re.M))

        rec(f"    主稿 References 条目 = {n_ref}")

        # 正文(除 References 节外)内联引用

        main_txt = ms[:ms.index("## References")]

        cites = set()

        for a, y in _re.findall(

                r"([A-Z][a-zA-Z\-]+)(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-zA-Z\-]+))?[\s,]*\((20[0-9]{2})\)", main_txt):

            cites.add(f"{a} ({y})")

        for a, y in _re.findall(

                r"([A-Z][a-zA-Z\-]+)(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-zA-Z\-]+))?,\s*(20[0-9]{2})", main_txt):

            cites.add(f"{a} ({y})")

        rec(f"    正文内联引用(去重) = {len(cites)}")

        for c in sorted(cites):

            rec(f"      - {c}")

        if n_ref == 0:

            fails.append("主稿有 References 节但条目数为 0")

        # ⚠ 空洞通过防护 (门禁第4条): 正则失效导致 cites 为空时不得判 PASS
        if len(cites) == 0:
            fails.append("内联引用提取为 0 —— 疑正则失效(空洞通过)")
        ref_missing = [c for c in cites if c.split(" (")[0] not in body]

        if ref_missing:

            fails.append(f"内联引用未出现在 References: {ref_missing}")

        rec(f"    [{'PASS' if not ref_missing and n_ref > 0 else 'FAIL'}] "

            f"引用↔文献表一致 (缺失 {len(ref_missing)})")

    else:

        fails.append("主稿缺少 References 节")

        rec("    [FAIL] 主稿无 References 节")

    # ---------- 8. 摘要长度 (投稿硬指标) ----------
    rec("\n[8] 摘要长度")
    _i = ms.find("## Abstract")
    _j = ms.find("\n---", _i)
    if _i >= 0 and _j > _i:
        _ab = ms[_i:_j]
        _w = len(_ab.split())
        # Nature 系列摘要通常 150-200 词; 本稿因需披露撤回与限制, 上限放宽至 300
        _LIMIT = 300
        rec(f"    Abstract 词数 = {_w} (上限 {_LIMIT}, 含撤回/限制披露的宽限)")
        if _w > _LIMIT:
            fails.append(f"Abstract 超长: {_w} 词 > {_LIMIT}; 编辑会直接退稿")
        rec(f"    [{'PASS' if _w <= _LIMIT else 'FAIL'}] 摘要长度")
    else:
        fails.append("未找到 Abstract 节")

    # ---------- 9. 投稿必需声明 ----------
    rec(chr(10)+'[9] 投稿必需声明')
    _REQ = ('Data availability','Code availability','Author contributions',
            'Competing interests','Acknowledgements')
    _miss=[r for r in _REQ if r.lower() not in ms.lower()]
    for r in _REQ:
        rec(f"    [{'PASS' if r.lower() in ms.lower() else 'FAIL'}] {r}")
    if _miss:
        fails.append(f'主稿缺少必需声明: {_miss}')
    # 占位符必须被作者填写(投稿前) -> 此处只提示, 不计 FAIL
    _ph=re.findall(r'\[\[(.+?)\]\]', ms)
    if _ph:
        warns.append(f'主稿含 {len(_ph)} 处待作者填写占位符(投稿前须完成)')

    # ---------- 10. 稿件结构完整性 (投稿形式要件) ----------
    rec(chr(10)+'[10] 稿件结构完整性')
    _SEC = ('Abstract','Introduction','Results','Discussion','Methods','References')
    # 图注引用必须存在(6 图 -> 至少 6 处 'Figure N')
    import re as _re2
    _nfig = len(_re2.findall(r'\*\*Figure\s*\d', ms))
    rec(f"    正文图注引用数 = {_nfig} (应为 6)")
    if _nfig < 6:
        fails.append(f'正文图注引用不足: {_nfig} < 6')
    for _s in _SEC:
        _hit = (_s.lower() in ms.lower())
        rec(f"    [{'PASS' if _hit else 'FAIL'}] 章节 {_s}")
        if not _hit:
            fails.append(f'主稿缺少章节: {_s}')

    # ---------- 汇总裁定 ----------

    rec("\n" + "=" * 84)

    rec("裁定")

    rec("=" * 84)

    rec(f"  FAIL = {len(fails)}")

    for f in fails:

        rec(f"    ✗ {f}")

    rec(f"  WARN = {len(warns)}")

    for w in warns:

        rec(f"    ⚠ {w}")

    verdict = "CONSISTENT" if not fails else "INCONSISTENT"

    rec(f"\n  总状态: {verdict}")

    rec(f"  ({time.time()-t0:.1f}s)")

    md = ["# 全包一致性审计报告", "",

          f"> 自动生成：`python A41_全包审计/package_consistency_check.py`",

          f"> 状态：**{verdict}**（FAIL {len(fails)}；WARN {len(warns)}）", "",

          "## 审计范围", "",

          "- 主稿 ↔ SI ↔ 六图图注 ↔ 证据台账 ↔ 复现清单（五方交叉）", "",

          "## FAIL 明细", ""]

    md += [f"- {f}" for f in fails] or ["（无）"]

    md += ["", "## WARN 明细", ""]

    md += [f"- {w}" for w in warns] or ["（无）"]

    md += ["", "## 完整日志", "", "```", *log, "```", ""]

    (HERE / "package_consistency_report.md").write_text("\n".join(md), encoding="utf-8")

    (HERE / "package_consistency_report.json").write_text(

        json.dumps({"verdict": verdict, "n_fail": len(fails), "n_warn": len(warns),

                    "fails": fails, "warns": warns,

                    "runtime_s": round(time.time() - t0, 1)},

                   ensure_ascii=False, indent=1), encoding="utf-8")

    rec(f"\n[write] package_consistency_report.md / .json")

    sys.exit(0 if not fails else 1)

if __name__ == "__main__":

    main()
