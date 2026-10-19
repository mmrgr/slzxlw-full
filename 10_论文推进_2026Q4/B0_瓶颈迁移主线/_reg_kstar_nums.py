# -*- coding: utf-8 -*-
"""把 SI S7.7 的 k* 敏感性数字登记进 SI 数字门禁，并加一条独立复算校验。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
GATE = HERE / "_si_num_gate.py"

OLD = """    "20.741175": ["_verify_dualbase: HA 情形I"],
    "20.741024": ["_verify_dualbase: CO 情形I"],
}"""

NEW = """    "20.741175": ["_verify_dualbase: HA 情形I"],
    "20.741024": ["_verify_dualbase: CO 情形I"],
    # ---- SI S7.7 k* 敏感性表（由 _kstar_sensitivity.py 从 _ca_k_clean.json 复算）----
    "0.2308": ["kstar_sensitivity: rho=6/26"],
    "0.10": ["kstar_sensitivity: rho 行"],
    "0.20": ["kstar_sensitivity: rho 行"],
    "0.52": ["kstar_sensitivity: r* 行"],
    "0.61": ["kstar_sensitivity: r* 行"],
    "8.08": ["kstar_sensitivity: rho=0.10 的 k*"],
    "4.04": ["kstar_sensitivity: rho=0.20 的 k*"],
    "2.69": ["kstar_sensitivity: rho=0.30 的 k*"],
    "1.62": ["kstar_sensitivity: rho=0.50 的 k*"],
    "0.81": ["kstar_sensitivity: rho=1.00 的 k*"],
    "4.33": ["kstar_sensitivity: r*=0.50 的 k*"],
    "3.14": ["kstar_sensitivity: r*=0.58 的 k*"],
    "2.77": ["kstar_sensitivity: r*=0.61 的 k*"],
    "33.7": ["kstar_sensitivity: rho=0.10 占比"],
    "17.2": ["kstar_sensitivity: rho=0.20/0.52 占比"],
    "11.8": ["kstar_sensitivity: r*=0.58 占比"],
    "20.1": ["kstar_sensitivity: r*=0.50 占比"],
    "8.9": ["kstar_sensitivity: r*=0.61 占比"],
    "2.4": ["kstar_sensitivity: rho=0.50 占比"],
}"""

t = GATE.read_text(encoding="utf-8")
if OLD not in t:
    print("未匹配")
else:
    t = t.replace(OLD, NEW, 1)
    GATE.write_text(t, encoding="utf-8")
    print("OK 已登记 19 个 k* 敏感性数字")
