# -*- coding: utf-8 -*-
"""核对 32,649 在 p.66 的上下文，以及 p.65 是否有 potable 小计。"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
doc = fitz.open(Path(r"C:/Users/mmrgr/Desktop/000/2025 Urban Water Management Plan_Final.pdf"))

t66 = doc[65].get_text()  # PDF p.66
print("=== p.66 含 32,649 的上下文 ===")
i = t66.replace(",", "").find("32649")
print(t66[max(0, i - 600):i + 400])

print("\n=== p.65 是否出现 '32,649' 或 potable 小计 ===")
t65 = doc[64].get_text()
print("含 32649:", "32649" in t65.replace(",", ""))
print("含 'potable':", "potable" in t65.lower())

print("\n=== p.66 开头 800 字（表 6-10/6-11 内容）===")
print(t66[:800])
