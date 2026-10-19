# -*- coding: utf-8 -*-
"""登记 SI S7.12 中的页码等非数值 token，并把 UWMP 水质核验加入总门禁。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

# 1) SI 数字门禁：页码不是数据
p = HERE / "_si_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "38700": ["UWMP p.65 原文 about 38,700"],\n}'
NEW = ('    "38700": ["UWMP p.65 原文 about 38,700"],\n'
       '    # ---- UWMP 页码（S7.12 引用 p.62 / p.86）----\n'
       '    "62": ["UWMP 页码 p.62"],\n'
       '    "86": ["UWMP 页码 p.86"],\n'
       '    "282": ["UWMP 总页数"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK SI 门禁 +3")
else:
    print("SI 门禁未匹配")

# 2) 总门禁加入 UWMP 水质核验
p = HERE / "_wr_final_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    ("UWMP 原始 PDF 核验（20 项）", "_verify_uwmp_pdf.py"),\n'
NEW = OLD + '    ("UWMP 水质证据核验（11 项）", "_verify_uwmp_quality.py"),\n'
if OLD in t and "_verify_uwmp_quality" not in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 总门禁已加入")
else:
    print("总门禁未匹配或已存在")
