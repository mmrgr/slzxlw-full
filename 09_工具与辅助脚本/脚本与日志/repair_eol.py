# -*- coding: utf-8 -*-
"""修复被去名脚本插入的多余空行：连续换行段长度折半，并按 HEAD 原有换行风格写回。"""
import os
import re
import subprocess

ROOT = r"C:/Users/mmrgr/WorkBuddy/2026-09-15-10-49-54/aiuwm_src"
SKIP = {".git", "node_modules", "dist", "__pycache__", ".venv", ".pytest_cache"}
EXTS = {".py", ".ts", ".tsx", ".md", ".json", ".cmd", ".toml", ".html", ".csv", ".yaml", ".yml", ".txt"}
BINARY = {".png", ".jpg", ".ico", ".pdf", ".xlsx", ".woff", ".woff2", ".ttf", ".parquet"}

# 1) 建立 新路径 -> HEAD 旧路径 的映射（处理 git mv 造成的重命名）
rename_map = {}
out = subprocess.check_output(
    ["git", "diff", "--cached", "-M", "--name-status"], cwd=ROOT
).decode("utf-8")
for line in out.splitlines():
    parts = line.split("\t")
    if parts and parts[0].startswith("R"):
        rename_map[parts[2]] = parts[1]


def head_bytes(rel):
    for cand in (rel, rename_map.get(rel)):
        if not cand:
            continue
        try:
            return subprocess.check_output(
                ["git", "show", "HEAD:" + cand], cwd=ROOT, stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            continue
    return None


def is_corrupted(text_lf: bytes) -> bool:
    lines = text_lf.split(b"\n")
    if lines and lines[-1] == b"":
        lines = lines[:-1]
    total = len(lines)
    if total < 4:
        return False
    empty = sum(1 for l in lines if l.strip() == b"")
    runs = re.findall(rb"\n+", text_lf)
    return all(len(r) % 2 == 0 for r in runs) and (empty / total) > 0.35


fixed = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext in BINARY or ext not in EXTS:
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        raw = open(p, "rb").read()
        if not raw:
            continue
        lf = raw.replace(b"\r\n", b"\n")
        if not is_corrupted(lf):
            continue

        # 连续换行段折半
        repaired = re.sub(rb"\n+", lambda m: b"\n" * (len(m.group(0)) // 2), lf)

        # 按 HEAD 原有换行风格还原
        h = head_bytes(rel)
        use_crlf = False
        if h is not None:
            use_crlf = h.count(b"\r\n") > (h.count(b"\n") - h.count(b"\r\n"))
        if use_crlf:
            repaired = repaired.replace(b"\n", b"\r\n")

        open(p, "wb").write(repaired)
        before = len(lf.split(b"\n")) - 1
        after = len(repaired.split(b"\n")) - 1
        hn = None
        if h is not None:
            hn = len(h.replace(b"\r\n", b"\n").split(b"\n")) - 1
        fixed.append((rel, before, after, hn, "CRLF" if use_crlf else "LF"))

print("repaired files:", len(fixed))
for f in sorted(fixed):
    print("  %-55s %d -> %d (HEAD %s) [%s]" % f)

# 2) 复查：不应再有“行数是 HEAD 两倍”的文件
print("\n--- 复查 ---")
left = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext in BINARY or ext not in EXTS:
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        h = head_bytes(rel)
        if h is None:
            continue
        b = open(p, "rb").read()
        n = len(b.replace(b"\r\n", b"\n").split(b"\n")) - 1
        hn = len(h.replace(b"\r\n", b"\n").split(b"\n")) - 1
        if hn > 20 and abs(n - 2 * hn) <= max(2, hn * 0.02):
            left.append((rel, n, hn))
print("still doubled:", left if left else "none")
