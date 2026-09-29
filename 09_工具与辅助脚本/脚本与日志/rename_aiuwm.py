"""Rename package watermet2_repro -> aiuwm and strip every watermet string."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\aiuwm_src")

# ------------------------------------------------------------------ 1) moves
MOVES = [
    ("src/watermet2_repro", "src/aiuwm"),
    ("data/watermet2_database.json", "data/uwm_database.json"),
    ("启动WaterMet2 Studio.cmd", "启动 AI-UWM Studio.cmd"),
    ("output/WaterMet2_网络资料与项目功能审计.md", "output/网络资料与项目功能审计.md"),
]
for src, dst in MOVES:
    s, d = ROOT / src, ROOT / dst
    if s.exists() and not d.exists():
        subprocess.run(["git", "mv", str(s), str(d)], cwd=ROOT, check=True)
        print("moved:", src, "->", dst)
    else:
        print("skip move:", src)

# --------------------------------------------------------------- 2) rewriting
# Order matters: longest / most specific first.
RULES = [
    ("Quantitative_UWS_performance_model_WaterMet2", "Quantitative_UWS_performance_model"),
    ("WATERMET2_STUDIO_NO_BROWSER", "AIUWM_STUDIO_NO_BROWSER"),
    ("WATERMET2_STUDIO_PORT", "AIUWM_STUDIO_PORT"),
    ("FullWaterMet2Model", "FullAIUWMModel"),
    ("WaterMet2Toolkit", "AIUWMToolkit"),
    ("WaterMetEdgeData", "UWMEdgeData"),
    ("WaterMetNodeData", "UWMNodeData"),
    ("WaterMetProject", "UWMProject"),
    ("WaterMet2Oslo", "OsloReferenceCase"),
    ("watermet2-reproduction", "aiuwm"),
    ("watermet2-studio", "aiuwm-studio"),
    ("watermet2-api", "aiuwm-api"),
    ("watermet2_database", "uwm_database"),
    ("watermet2_repro", "aiuwm"),
    ("my_watermet_case", "my_uwm_case"),
    ("启动WaterMet2 Studio.cmd", "启动 AI-UWM Studio.cmd"),
    ("WaterMet2 Studio", "AI-UWM Studio"),
    ("WaterMet² Studio", "AI-UWM Studio"),
    ("watermet2", "aiuwm"),
    ("WaterMet2", "AI-UWM"),
]

SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__", ".pytest_cache", ".venv"}
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".dll", ".pyd",
               ".xlsx", ".docx", ".zip", ".woff", ".woff2", ".ttf", ".mp4", ".parquet"}

changed = []
for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    rel = path.relative_to(ROOT)
    if any(p in SKIP_DIRS for p in rel.parts):
        continue
    if path.suffix.lower() in SKIP_SUFFIX:
        continue
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
        enc = "utf-8"
    except UnicodeDecodeError:
        try:
            text = raw.decode("gb18030")
            enc = "gb18030"
        except UnicodeDecodeError:
            print("SKIP(binary):", rel)
            continue
    original = text
    low = text.lower()
    if "watermet" not in low:
        continue
    for old, new in RULES:
        if old in text:
            text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding=enc)
        changed.append(str(rel))

print(f"\nrewritten files: {len(changed)}")
for c in changed:
    print("  ", c)
