"""生成项目文件功能清单 (整理轮 2026-10-16).

【目的】用户要求"明确每个文件的功能"。本脚本**自动扫描**项目并产出
`文件功能清单.md`, 对每个目录与关键文件给出:
  · 路径 / 类型 / 大小
  · 从文件头 docstring 或首行注释提取的**功能摘要**
  · 是否为"权威产物"(被其它脚本或文档引用) —— 机械判定, 非猜测

【为什么自动而非手写】
3827 个文件无法手写; 且手写清单一旦文件改动就会过期。
本脚本可重复运行, 保证清单与现状一致。

【判定"权威产物"的方法】
对每个文件, 在全部 `.py` 与 `.md` 中搜索其文件名 —— 有引用即标 `REF`。
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def _find_root() -> Path:
    """向上寻找含 '07_代码_AI-UWM引擎' 的项目根。"""
    for base in Path(__file__).resolve().parent.parents:
        if (base / "07_代码_AI-UWM引擎").is_dir():
            return base
    return Path(__file__).resolve().parent.parent


ROOT = _find_root()      # 算力中心
SKIP = {"node_modules", ".git", "__pycache__", ".venv", "dist", ".next",
        "_archive_2026-10-16", "_logs", "_prev_2026-10-16", ".lit_extract",
        ".pytest_cache", ".r5check"}


def py_docstring(p: Path) -> str:
    """取 .py 的模块 docstring 首行(去 # 注释噪声)。"""
    try:
        src = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    try:
        d = ast.get_docstring(ast.parse(src))
        if d:
            for line in d.splitlines():
                if line.strip():
                    return line.strip()[:110]
    except Exception:
        pass
    # 回退: 首个非空注释行
    for line in src.splitlines()[:15]:
        s = line.strip()
        if s.startswith("#") and len(s) > 3:
            return s.lstrip("# ").strip()[:110]
    return ""


def md_title(p: Path) -> str:
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines()[:12]:
            s = line.strip()
            if s.startswith("# "):
                return s[2:].strip()[:110]
            if s and not s.startswith("#"):
                return s[:110]
    except Exception:
        pass
    return ""


def main() -> None:
    # 收集引用语料 (用于判定 REF)
    corpus_files = [p for p in ROOT.rglob("*")
                    if p.suffix in (".py", ".md") and p.is_file()
                    and not any(s in p.parts for s in SKIP)]
    corpus = []
    for p in corpus_files:
        try:
            corpus.append((p, p.read_text(encoding="utf-8", errors="replace")))
        except Exception:
            pass

    def refcount(name: str) -> int:
        return sum(1 for _, t in corpus if name in t)

    # 扫描目标: 各功能目录的**直接**内容(不递归太深)
    targets = [
        ("00_项目说明/总览", ["00_项目文件总览.md", "00_项目说明.md", "_迁移清单.md"]),
        ("01_方案与设计文档", ["01_方案与设计文档"]),
        ("02_开题报告", ["02_开题报告"]),
        ("03_答辩材料", ["03_答辩材料"]),
        ("04_评议与评价", ["04_评议与评价"]),
        ("05_学校模板与规定", ["05_学校模板与规定"]),
        ("06_文献库", ["06_文献库"]),
        ("07_代码_AI-UWM引擎", ["07_代码_AI-UWM引擎"]),
        ("08_实验数据", ["08_实验数据"]),
        ("09_工具与辅助脚本", ["09_工具与辅助脚本"]),
        ("10_论文推进_2026Q4", ["10_论文推进_2026Q4"]),
        ("_logs 日志中心", ["_logs"]),
        ("_archive_2026-10-16 归档", ["_archive_2026-10-16"]),
    ]

    out: list[str] = []
    out.append("# 项目文件功能清单")
    out.append("")
    out.append("> 自动生成: `python _lib/make_file_inventory.py`")
    out.append("> **可重复运行**: 文件变动后重跑即可刷新, 不会过期。")
    out.append("")
    out.append("## 怎么读这份清单")
    out.append("")
    out.append("| 列 | 含义 |")
    out.append("|---|---|")
    out.append("| 路径 | 相对项目根 |")
    out.append("| 大小 | 字节 |")
    out.append("| 功能 | 取自文件 docstring / 首行标题 |")
    out.append("| REF | 该文件名在其它 .py/.md 中被提及的次数; ≥1 表示**有下游依赖, 改名会断链** |")
    out.append("")

    total_files = 0
    for title, entries in targets:
        out.append(f"## {title}")
        out.append("")
        rows = []
        for e in entries:
            p = ROOT / e
            if p.is_file():
                cands = [p]
            elif p.is_dir():
                cands = sorted([q for q in p.iterdir() if q.is_file()])
                # 目录很大时只列顶层 + 统计子目录
                subdirs = sorted([q for q in p.iterdir() if q.is_dir()])
            else:
                continue
            for f in cands:
                name = f.name
                func = py_docstring(f) if f.suffix == ".py" else md_title(f)
                rc = refcount(name)
                tag = "**REF**" if rc > 0 else ""
                rows.append((str(f.relative_to(ROOT)).replace("\\", "/"),
                             f.stat().st_size, func, rc, tag))
        if rows:
            out.append("| 路径 | 大小 | 功能 | REF |")
            out.append("|---|---:|---|---:|")
            for path, size, func, rc, tag in rows:
                func_c = (func or "—").replace("|", "\\|")
                out.append(f"| `{path}` | {size} | {func_c} | {rc} {tag} |")
            total_files += len(rows)
        else:
            out.append("(无直接文件)")
        out.append("")
        # 子目录概览
        for e in entries:
            p = ROOT / e
            if p.is_dir():
                subs = sorted([q for q in p.iterdir() if q.is_dir()])
                if subs:
                    out.append(f"*子目录*: " + ", ".join(f"`{s.name}`" for s in subs))
                    out.append("")

    out.append("## 关键约定")
    out.append("")
    out.append("- **权威产物**(REF≥1) **不可改名**: 改名会断链。若必须改, 请同步更新")
    out.append("  引用方, 或改用 `_lib/project_paths.py` 的 `FILE_TABLE` 集中管理。")
    out.append("- 新增文件的推荐位置:")
    out.append("  - 分析脚本 / 产物 -> `10_论文推进_2026Q4/A<NN>_<主题>/`")
    out.append("  - 公共函数       -> `10_论文推进_2026Q4/_lib/`")
    out.append("  - 历史日志       -> 由 `_logs/consolidate_logs.py` 自动纳管")
    out.append("  - 一次性探针     -> 放入 `_archive_2026-10-16/dev_probes/`")
    out.append("")
    out.append(f"*本次共登记 {total_files} 个文件。*")
    out.append("")

    dest = ROOT / "文件功能清单.md"
    dest.write_text("\n".join(out), encoding="utf-8")
    print(f"[write] {dest}")
    print(f"  登记文件数 = {total_files}")


if __name__ == "__main__":
    main()
