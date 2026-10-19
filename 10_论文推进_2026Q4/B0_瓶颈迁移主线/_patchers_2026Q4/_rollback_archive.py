# -*- coding: utf-8 -*-
"""一键还原 _patchers_2026Q4 的归档（把文件移回主目录）。"""
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MAN = json.loads((HERE / "_MANIFEST.json").read_text(encoding="utf-8"))
SRC = Path(MAN["source_dir"])
n = 0
for name in MAN["moved"]:
    f = HERE / name
    if not f.exists():
        continue
    dst = SRC / name
    if dst.exists():
        print("跳过（目标已存在）:", name)
        continue
    shutil.move(str(f), str(dst))
    n += 1
print(f"已还原 {n} 个文件到 {SRC}")
