# -*- coding: utf-8 -*-
"""诊断：找出被去名脚本插入多余空行（每行后多一个空行）的文件。"""
import os
import re
import subprocess

ROOT = r"C:/Users/mmrgr/WorkBuddy/2026-09-15-10-49-54/aiuwm_src"
SKIP = {".git", "node_modules", "dist", "__pycache__", ".venv", ".pytest_cache"}
EXTS = {".py", ".ts", ".tsx", ".md", ".json", ".cmd", ".toml", ".html", ".csv", ".yaml", ".yml", ".txt"}
BINARY = {".png", ".jpg", ".ico", ".pdf", ".xlsx", ".woff", ".woff2", ".ttf", ".parquet"}


def head_blob(rel):
    """返回 HEAD 中对应路径的字节；重命名过的文件用旧路径回退。"""
    for cand in (rel,):
        try:
            return subprocess.check_output(
                ["git", "show", "HEAD:" + cand], cwd=ROOT, stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            pass
    return None


def stats(path):
    b = open(path, "rb").read()
    if not b:
        return None
    # 归一化为 LF 统计
    t = b.replace(b"\r\n", b"\n")
    lines = t.split(b"\n")
    if lines and lines[-1] == b"":
        lines = lines[:-1]
    total = len(lines)
    empty = sum(1 for l in lines if l.strip() == b"")
    if total == 0:
        return None
    # 连续换行 runs 长度分布
    runs = re.findall(rb"\n+", t)
    even = all(len(r) % 2 == 0 for r in runs)
    return {
        "total": total,
        "empty": empty,
        "ratio": empty / total,
        "all_even_runs": even,
        "crlf": b.count(b"\r\n"),
    }


report = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext in BINARY:
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        if ext not in EXTS and ext != "":
            continue
        s = stats(p)
        if not s:
            continue
        h = head_blob(rel)
        hlines = None
        if h is not None:
            hlines = len(h.replace(b"\r\n", b"\n").split(b"\n"))
            if h.endswith(b"\n"):
                hlines -= 1
        suspect = s["all_even_runs"] and s["ratio"] > 0.35 and s["total"] > 3
        if suspect:
            report.append((rel, s["total"], s["empty"], round(s["ratio"], 2), hlines, s["crlf"]))

print("SUSPECT FILES (插入了多余空行):", len(report))
for r in sorted(report):
    print("  %-55s lines=%-6d empty=%-6d ratio=%.2f head_lines=%s crlf=%d" % r)
