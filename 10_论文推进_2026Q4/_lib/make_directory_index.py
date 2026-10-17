"""生成研究目录功能索引 (2026-10-16).

【为什么用"索引"而不是"移动"】
项目 102/177 脚本硬编码 `A*` 目录名 (共 328 处), 且脚本用 `__file__` 定位,
实测**物理移动必然断链**(见 `../导航_怎么看这个目录.md` §0)。
故改用**索引层**: 目录原地不动, 但生成一份按**功能与逻辑顺序**排列的索引,
使"结构是否清楚"不再取决于 `ls` 的字典序。

【产出】
1. `_index/目录索引.md`   —— 按功能分组(模型/实验/审计/论文/外部数据/过程)
2. `_index/目录索引.json` —— 机器可读, 供脚本查询
3. `../文件功能清单.md`   —— 每个文件的用途(由 make_file_inventory.py 生成)

索引从每个目录的**报告文件标题**或 **py docstring** 自动提取功能说明,
避免手写清单过期。
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "_index"          # 索引放在研究目录下, 而非 _lib/ 内
OUT.mkdir(exist_ok=True)

# 功能分组: 组名 -> [(目录前缀, 角色说明)]
GROUPS: list[tuple[str, str, list[str]]] = [
    ("① 模型与参数（基础层）", "被所有实验依赖，改动需全量回归", [
        "A10_敏感性与边界", "A4_水化学参数域", "A12_时间分辨率", "A1_传输账本",
        "A7_质量分配联合",
    ]),
    ("② 实验（产生结论）", "各专题实验与判决性检验", [
        "A2_规则实验", "A3_三规则内生", "A5_设施锚定", "A8_溶质闭合",
        "A9_无量纲折叠", "A11_适应成本", "A13_可靠性机制", "A15_稳健性",
        "A18_有限供水", "A19_水化学包络", "A20_模型桥接", "A21_动态状态",
        "A22_判据分解", "A30_WP0取证", "A31_WP2_假设冻结", "A32_WP3_水化学",
        "A33_WP4_组成重构", "A34_WP5_敏感性与极端事件", "A38_模拟审稿",
    ]),
    ("③ 审计（验证与门禁）", "独立核对，产出 PASS/FAIL 判定", [
        "A25_终审", "A26_语义统一", "A27_引用限值", "A28_末轮审计",
        "A36_终审", "A41_全包审计", "A44_检查清理轮",
    ]),
    ("④ 论文（交付物）", "投稿所需的最终产物", [
        "A16_英文稿", "A35_WP7_主稿修订", "A37_六主图_v4", "A40_投稿包",
        "A42_参考文献", "A43_投稿声明", "A6_可信度配图", "09_图定稿",
    ]),
    ("⑤ 外部数据（独立证据）", "外部实测数据与文献", [
        "A24_外部锚定", "A39_WP8_外部效度", "A29_文献核验", "A14_外部锚定",
    ]),
    ("⑥ 过程记录（历史留痕）", "非交付物；含撤回与修复的证据链", [
        "07_过程记录", "A0_预注册",
    ]),
]


def describe(d: Path) -> str:
    """从报告标题或 py docstring 提取目录功能说明。"""
    # 优先: 报告类 md
    for pat in ("*报告*.md", "*总结*.md", "README*.md", "*索引*.md"):
        for f in sorted(d.glob(pat)):
            try:
                for line in f.read_text(encoding="utf-8", errors="replace").splitlines()[:10]:
                    s = line.strip()
                    if s.startswith("# "):
                        return s[2:].strip()[:80]
            except Exception:
                pass
    # 次选: 最大的 py 的 docstring
    pys = sorted(d.glob("*.py"), key=lambda p: -p.stat().st_size)
    for p in pys[:3]:
        try:
            ds = ast.get_docstring(ast.parse(p.read_text(encoding="utf-8", errors="replace")))
            if ds:
                for line in ds.splitlines():
                    if line.strip():
                        return line.strip()[:80]
        except Exception:
            pass
    return "—"


def refcount(name: str, corpus: list[tuple[Path, str]]) -> int:
    return sum(1 for _, t in corpus if name in t)


def main() -> None:
    corpus = []
    for p in ROOT.rglob("*"):
        if p.suffix in (".py", ".md") and p.is_file() and "__pycache__" not in str(p):
            try:
                corpus.append((p, p.read_text(encoding="utf-8", errors="replace")))
            except Exception:
                pass

    md = ["# 研究目录索引", "",
          "> 自动生成: `python _lib/make_directory_index.py`",
          "> 本文件把目录**按功能**排列（不依赖 `ls` 的字典序）。",
          "> 目录**原地未移动**（原因见 `导航_怎么看这个目录.md` §0）。", ""]
    data: dict = {"groups": {}}

    seen = set()
    for gname, gdesc, items in GROUPS:
        md.append(f"## {gname}")
        md.append("")
        md.append(f"*{gdesc}*")
        md.append("")
        md.append("| 目录 | 功能 | 文件数 | 被引用 |")
        md.append("|---|---|---:|---:|")
        rows = []
        for it in items:
            d = ROOT / it
            if not d.is_dir():
                continue
            seen.add(it)
            n = len([f for f in d.rglob("*") if f.is_file()])
            rc = refcount(it, corpus)
            desc = describe(d)
            md.append(f"| `{it}` | {desc} | {n} | {rc} |")
            rows.append({"dir": it, "desc": desc, "n_files": n, "refs": rc})
        md.append("")
        data["groups"][gname] = rows

    # 未归类
    all_dirs = {d.name for d in ROOT.iterdir()
                if d.is_dir() and re.match(r"A\d+_", d.name)}
    rest = sorted(all_dirs - seen, key=lambda n: int(re.match(r"A(\d+)", n).group(1)))
    if rest:
        md.append("## ⑦ 其它")
        md.append("")
        md.append("| 目录 | 功能 | 文件数 | 被引用 |")
        md.append("|---|---|---:|---:|")
        for it in rest:
            d = ROOT / it
            n = len([f for f in d.rglob("*") if f.is_file()])
            rc = refcount(it, corpus)
            md.append(f"| `{it}` | {describe(d)} | {n} | {rc} |")
            data["groups"].setdefault("⑦ 其它", []).append(
                {"dir": it, "desc": describe(d), "n_files": n, "refs": rc})
        md.append("")

    md += ["## 命名约定", "",
           "- `A<数字>_<主题>`：研究阶段/专题目录，编号 = 逻辑顺序（**非**时间顺序）",
           "- 编号有空洞（如 17、23）表示该编号已废弃，**不要重用**以免与历史文档冲突",
           "- 公共代码在 `_lib/`；日志在 `../../_logs/`；归档在 `../../_archive_2026-10-16/`",
           "",
           "## 维护", "",
           "新增目录后，请把其加入 `make_directory_index.py` 的 GROUPS，然后重跑本脚本。",
           ""]

    (OUT / "目录索引.md").write_text("\n".join(md), encoding="utf-8")
    (OUT / "目录索引.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[write] {OUT/'目录索引.md'}")
    print(f"[write] {OUT/'目录索引.json'}")
    print(f"  分组 {len(data['groups'])} 个; 目录 {sum(len(v) for v in data['groups'].values())} 个")


if __name__ == "__main__":
    main()
