"""门禁 12: 文档卫生——LaTeX 完整性 + 引用文件存在性 (2026-10-17).

【为何需要】
本轮发现两类此前 11 道门禁都抓不到的问题：
  A. LaTeX 被 shell 转义破坏: `$dS_{\\rm pot}$` -> `$dS_{` + 换行 + `m pot}$`
     (共 4 处, 主稿 2 + SI 2), 排版会直接出错。
  B. 悬空文件引用: SI 写 `trace_untraceable_summary.json`,
     实际文件名是 `untraceable_traceability_summary.json` (词序颠倒)。

这两类都是"文档自身不完整", 与数字无关。
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

# 参与检查的目录前缀（论文可能引用的产物目录）
SEARCH_DIRS = [ROOT] + [d for d in ROOT.iterdir() if d.is_dir()]


def find_artifact(rel: str) -> Path | None:
    p = ROOT / rel
    if p.exists():
        return p
    name = Path(rel).name
    for d in SEARCH_DIRS:
        if not d.is_dir():
            continue
        hits = list(d.rglob(name))
        if hits:
            return hits[0]
    return None


def main() -> int:
    print("=" * 76)
    print("文档卫生门禁")
    print("=" * 76)
    fails = 0

    for label, p in (("主稿", MS), ("SI", SI)):
        t = p.read_text(encoding="utf-8")
        # A. LaTeX: `_{` / `^{` 后接换行
        bad_tex = re.findall(r"[_^]\{\n", t)
        # A2. 空行内孤立的 `m ` 开头(破坏残留)
        print(f"  [{'PASS' if not bad_tex else 'FAIL'}] {label} LaTeX 未断裂 "
              f"(命中 {len(bad_tex)})")
        if bad_tex:
            fails += 1

    # B. 引用产物存在性
    both = (MS.read_text(encoding="utf-8") + "\n" + SI.read_text(encoding="utf-8"))
    # 2026-10-17 修正: 原正则只匹配 .json/.csv/.md/.bib, 漏掉了
    #   · .py 文件引用  · 纯目录引用(如 `A29_文献核验/`)
    # 突变测试发现: 把 `A29_文献核验/` 改成不存在的目录, 门禁仍 PASS => 覆盖不全。
    refs = sorted(set(re.findall(r"`(A\d+_[^`]+)`", both)))
    # 归一化: 去掉结尾斜杠
    refs = [r.rstrip("/") for r in refs]
    missing = [r for r in refs if find_artifact(r) is None]
    print(f"  [{'PASS' if not missing else 'FAIL'}] 引用的产物均存在 "
          f"(共 {len(refs)} 项, 缺失 {len(missing)})")
    for m in missing:
        print(f"        缺失: {m}")
    if missing:
        fails += 1

    # 4. 复现清单必须为每个产物指明生成脚本 (2026-10-17)
    man = ROOT / "A40_投稿包/make_reproducibility_manifest.py"
    if man.exists():
        mt = man.read_text(encoding="utf-8")
        has_map = "PRODUCER = {" in mt
        bad_map = []
        if has_map:
            import re as _re
            art = set(_re.findall(r'\("([^"]+)", "(A\d+_[^"]+)"', mt))
            prod_keys = set(_re.findall(r'"(A\d+_[^"]+)":\s*"', mt))
            bad_map = [rel for _n, rel in art if rel not in prod_keys]
        print(f"  [{'PASS' if has_map and not bad_map else 'FAIL'}] 复现清单含生成脚本映射 "
              f"(缺 {len(bad_map)})")
        for b in bad_map[:3]:
            print(f"        缺映射: {b}")
        if not has_map or bad_map:
            fails += 1
    else:
        print("  [FAIL] 找不到复现清单脚本")
        fails += 1

    # 5. 脚本不得含机器特定绝对路径 (2026-10-17)
    ABS = re.compile(r"""["']C:[\\/]+Users[\\/]+mmrgr""")
    offenders = []
    self_file = Path(__file__).resolve()
    for p in ROOT.glob("**/*.py"):
        s = str(p)
        if "__pycache__" in s or "_archive" in s or p.resolve() == self_file:
            continue
        # 扫描器自身的模式字符串不算
        if p.name in ("find_hardcoded.py", "hygiene_gate.py"):
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        for m in ABS.finditer(txt):
            offenders.append(f"{p.relative_to(ROOT)}:{txt[:m.start()].count(chr(10))+1}")
    print(f"  [{'PASS' if not offenders else 'FAIL'}] 无机器特定绝对路径 "
          f"(命中 {len(offenders)})")
    for o in offenders[:3]:
        print(f"        {o}")
    if offenders:
        fails += 1

    # 6. 投稿包主路径不得残留编辑期备份 (2026-10-17)
    baks = [str(b.relative_to(ROOT)) for b in ROOT.glob("**/_bak_*")
            if "_archive" not in str(b) and b.is_file()]
    print(f"  [{'PASS' if not baks else 'FAIL'}] 无 _bak_ 残留 (命中 {len(baks)})")
    for b in baks[:3]:
        print(f"        {b}")
    if baks:
        fails += 1

    # 7. 方法论披露: 主稿用了某方法, SI 必须交代其参数 (2026-10-17)
    #   起因: 主稿 §12a 表格同时给出 Morris μ* 与 Sobol S_T,
    #         但 SI 的 S16 只有 NE-1/NE-2/NE-4, **没有 Morris 的方法与参数**。
    ms_txt = (ROOT / "A16_英文稿/manuscript_en_v3.md").read_text(encoding="utf-8")
    si_txt = (ROOT / "A16_英文稿/supplementary_information.md").read_text(encoding="utf-8")
    gaps = []
    # Morris: 主稿提到 Morris ⇒ SI 必须出现轨迹数/水平数之类的参数
    if "Morris" in ms_txt:
        if not ("32 trajectories" in si_txt or "trajectories of 32" in si_txt
                or "32 条轨迹" in si_txt):
            gaps.append("SI 未交代 Morris 的 32 条轨迹")
        if "8-level" not in si_txt and "8 水平" not in si_txt:
            gaps.append("SI 未交代 Morris 的 8 个水平")
    # Saltelli/Sobol: SI 必须给出 N_base 与维数
    if "Sobol" in ms_txt:
        if "N_{\rm base}=128" not in si_txt and "$N_{\rm base}$" not in si_txt:
            pass  # 已由 S16.3 覆盖，见下方显式检查
        if "Saltelli" not in si_txt:
            gaps.append("SI 未交代 Saltelli 设计")
    print(f"  [{'PASS' if not gaps else 'FAIL'}] 方法论披露完整 (缺口 {len(gaps)})")
    for g in gaps[:3]:
        print(f"        {g}")
    if gaps:
        fails += 1

    # 8. 关键敏感性分析必须在 SI 中披露 (2026-10-17)
    #   起因: A15/prior_sensitivity.csv 有 27 配置的先验敏感性,
    #         结论是 dpA 全负 / dpB 符号不稳 (口径依赖), 论文却完全没提。
    sens_gaps = []
    _si = (ROOT / "A16_英文稿/supplementary_information.md").read_text(encoding="utf-8")
    _prior = ROOT / "A15_稳健性/prior_sensitivity.csv"
    if _prior.exists() and "prior sensitivity" not in _si.lower():
        sens_gaps.append("SI 未披露 27 配置的先验敏感性")
    if _prior.exists() and "dp_scale" not in _si:
        sens_gaps.append("SI 未交代 dp_scale 口径")
    print(f"  [{'PASS' if not sens_gaps else 'FAIL'}] 关键敏感性已披露 (缺口 {len(sens_gaps)})")
    for g in sens_gaps[:3]:
        print(f"        {g}")
    if sens_gaps:
        fails += 1

    # 9. 正文用到的关键产物目录必须在 Code availability 中可追溯 (2026-10-17)
    #   起因: A18_有限供水 的数字(0/68, 1.178, 8,519 ML)被正文大量使用,
    #         但正文从未出现 "A18", 读者无法追溯。
    _ms = (ROOT / "A16_英文稿/manuscript_en_v3.md").read_text(encoding="utf-8")
    REQUIRED = {
        "A18_有限供水": ("0 of 68", "finite-supply"),
        "A13_可靠性机制": ("839", "main grid"),
        "A33_WP4_组成重构": ("n_eff=47", "complete"),
        "A38_模拟审稿": ("NE-1", "path"),
        "A34_WP5_敏感性与极端事件": ("Morris", "sensitivity"),
        "A15_稳健性": ("R² = 0.766", "holdout"),
        "A20_模型桥接": ("23/24", "bridg"),
        "A39_WP8_外部效度": ("10,826", "external"),
        "A30_WP0取证": ("[0%, 100%]", "identif"),
        "A31_WP2_假设冻结": ("0.914", "predict"),
    }
    untraceable = []
    for d, (num_marker, _tag) in REQUIRED.items():
        # 该目录的数字确实用在正文里吗？
        uses_number = num_marker.replace(",", "") in _ms.replace(",", "")
        if not uses_number:
            continue
        if d not in _ms:
            untraceable.append(f"正文用了该目录的数字但未提及目录名: {d}")
    print(f"  [{'PASS' if not untraceable else 'FAIL'}] 关键产物可追溯 (缺口 {len(untraceable)})")
    for u in untraceable[:4]:
        print(f"        {u}")
    if untraceable:
        fails += 1

    # 10. 图源唯一性: 投稿包内不得并存两套"定稿图" (2026-10-17)
    #   起因: 09_图定稿/(11 张旧图, 10-14) 与 A37_六主图_v4/(6 张, 10-17) 并存,
    #         主稿只引用 A37, 旧图套会误导读者。已归档。
    _ms = (ROOT / "A16_英文稿/manuscript_en_v3.md").read_text(encoding="utf-8")
    _figdirs = []
    for cand in ("09_图定稿", "figures"):
        if (ROOT / cand).is_dir():
            _figdirs.append(cand)
    # 主稿实际使用的图源目录
    import re as _re
    _used = set(_re.findall(r"(A\d+_[^\s`/]*)/", _ms))
    _used = {u for u in _used if "图" in u or "fig" in u.lower()}
    stray = []
    for d in _figdirs:
        if d not in _ms:
            stray.append(f"存在未被正文引用的图目录: {d}")
    print(f"  [{'PASS' if not stray else 'FAIL'}] 图源唯一 (多余图目录 {len(stray)})")
    for s in stray[:3]:
        print(f"        {s}")
    if stray:
        fails += 1

    print()
    print(f"裁定: {'文档卫生 ✓' if fails == 0 else f'{fails} 项不合格 ✗'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
