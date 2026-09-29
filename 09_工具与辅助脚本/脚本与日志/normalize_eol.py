# -*- coding: utf-8 -*-
"""把被脚本叠加转义的换行（\r\r\n / \r\n）统一归一化为 HEAD 原有风格（LF）。"""
import os
import subprocess

ROOT = r"C:/Users/mmrgr/WorkBuddy/2026-09-15-10-49-54/aiuwm_src"
SKIP = {".git", "node_modules", "dist", "__pycache__", ".venv", ".pytest_cache"}
EXTS = {".py", ".ts", ".tsx", ".md", ".json", ".cmd", ".toml", ".html", ".csv",
        ".yaml", ".yml", ".txt", ".cfg", ".ini"}

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


changed = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for fn in files:
        if os.path.splitext(fn)[1].lower() not in EXTS:
            continue
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        b = open(p, "rb").read()
        if b"\r\r\n" not in b and b"\r\n" not in b:
            continue

        # 先消除叠加转义，再统一到纯 LF
        lf = b.replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n")
        h = head_bytes(rel)
        use_crlf = False
        if h is not None:
            use_crlf = h.count(b"\r\n") > (h.count(b"\n") - h.count(b"\r\n"))
        new = lf.replace(b"\n", b"\r\n") if use_crlf else lf
        if new != b:
            open(p, "wb").write(new)
            changed.append((rel, len(b), len(new), "CRLF" if use_crlf else "LF"))

print("normalized:", len(changed))
for c in sorted(changed):
    print("   %-52s %d -> %d [%s]" % c)

# 复查
bad = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for fn in files:
        if os.path.splitext(fn)[1].lower() not in EXTS:
            continue
        b = open(os.path.join(root, fn), "rb").read()
        if b"\r\r\n" in b:
            bad.append(os.path.relpath(os.path.join(root, fn), ROOT))
print("remaining CRCRLF:", bad if bad else "none")
