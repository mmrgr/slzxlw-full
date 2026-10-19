# -*- coding: utf-8 -*-
"""登记 UWMP 原文数字 38,700，并处理页码 6-11 被误识为 -11 的问题。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

# 1) 英文门禁
p = HERE / "_wr_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "230.8": ["cp_precision: r=0.499 的临界 C_p"],\n}'
NEW = ('    "230.8": ["cp_precision: r=0.499 的临界 C_p"],\n'
       '    # ---- UWMP 原文数字（_verify_uwmp_pdf.py 已核：p.65 写 about 38,700）----\n'
       '    "38700": ["UWMP p.65 原文 about 38,700 AFY"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 英文 +1")
else:
    print("英文未匹配")

# 2) SI 门禁：加 38700；页码 "6-11" 的 -11 需要用排除规则处理
p = HERE / "_si_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "81.4": ["cp_precision: C_r=800 时临界"],\n}'
NEW = ('    "81.4": ["cp_precision: C_r=800 时临界"],\n'
       '    # ---- UWMP 原文数字 ----\n'
       '    "38700": ["UWMP p.65 原文 about 38,700"],\n'
       '}')
if OLD in t:
    t = t.replace(OLD, NEW, 1)
    # 页码形如 Table 6-11 / DWR Table 4-1 会被切成 -11、-1，属表格编号非数值
    t = t.replace(
        '    body = re.sub(r"^#{2,4}\\s+[\\d.]+", "##", body, flags=re.M)',
        '    body = re.sub(r"^#{2,4}\\s+[\\d.]+", "##", body, flags=re.M)\n'
        '    # 表号（Table 6-11 / DWR Table 4-1）与页码形如 6-11，不是数值\n'
        '    body = re.sub(r"(?:Table|Tables)\\s*\\d+-\\d+", " TABLE ", body)\n'
        '    body = re.sub(r"DWR\\s+Table\\s*\\d+-\\d+", " TABLE ", body)')
    p.write_text(t, encoding="utf-8")
    print("OK SI +38700 并加表号排除规则")
else:
    print("SI 未匹配")
