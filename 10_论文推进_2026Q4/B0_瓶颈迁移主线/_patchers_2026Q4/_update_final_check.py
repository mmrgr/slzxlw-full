# -*- coding: utf-8 -*-
"""更新 _final_check.py：加入第 5 套核对与 FigR4/新增产物。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

p = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4\B0_瓶颈迁移主线\_final_check.py")
t = p.read_text(encoding="utf-8")

# 1) 门禁列表加入 policy bridge
old_gates = '''        ("分类学核对", HERE / "_verify_regime_numbers.py", "41/41"),
    ]'''
new_gates = '''        ("分类学核对", HERE / "_verify_regime_numbers.py", "41/41"),
        ("政策区隔核对", HERE / "_verify_policy_bridge.py", "25/25"),
    ]'''
if old_gates in t:
    t = t.replace(old_gates, new_gates, 1)
    print("[OK] 门禁列表加入 policy bridge")
else:
    print("[MISS] 门禁列表")

# 2) 图件门禁期望值
t = t.replace('("图件门禁", FIGDIR / "_gate_check_b0.py", "70/70")',
              '("图件门禁", FIGDIR / "_gate_check_b0.py", "81/81")')
print("[OK] 图件门禁期望 81/81")

# 3) 交付文件加入 21/22 号文档与 FigR4
old_files = '''        "图 FigR3.pdf": FIGDIR / "FigR3_rstar_regime_and_sensitivity.pdf",
        "图 FigR3.png": FIGDIR / "FigR3_rstar_regime_and_sensitivity.png",'''
new_files = '''        "图 FigR3.pdf": FIGDIR / "FigR3_rstar_regime_and_sensitivity.pdf",
        "图 FigR3.png": FIGDIR / "FigR3_rstar_regime_and_sensitivity.png",
        "现实性检验": HERE / "21_现实性检验_口径区隔.md",
        "贡献定位": HERE / "22_贡献定位_判据而非预测.md",
        "图 FigR4.pdf": FIGDIR / "FigR4_zero_effect_and_policy_bridge.pdf",
        "图 FigR4.png": FIGDIR / "FigR4_zero_effect_and_policy_bridge.png",'''
if old_files in t:
    t = t.replace(old_files, new_files, 1)
    print("[OK] 文件清单加入 21/22 与 FigR4")
else:
    print("[MISS] 文件清单")

# 4) 产物清单加入 policy bridge
old_arts = '''        "rstar_sensitivity_summary.json",
    ]'''
new_arts = '''        "rstar_sensitivity_summary.json",
        "rstar_policy_bridge.csv", "rstar_policy_bridge.json",
    ]'''
if old_arts in t:
    t = t.replace(old_arts, new_arts, 1)
    print("[OK] 产物清单加入 policy bridge")
else:
    print("[MISS] 产物清单")

# 5) v2 指标加入本轮检查
old_ck = '''    ck("v2 引用 FigR3", "FigR3_rstar_regime_and_sensitivity" in t2)'''
new_ck = '''    ck("v2 引用 FigR3", "FigR3_rstar_regime_and_sensitivity" in t2)
    ck("v2 引用 FigR4", "FigR4_zero_effect_and_policy_bridge" in t2)
    ck("v2 含 §1.6 口径区隔", "### 1.6 一个必须区分的口径" in t2)
    ck("v2 含 §5.8.2b 零效应区", "5.8.2b" in t2 and "零效应区" in t2)
    ck("v2 含 §8.6 政策意义", "### 8.6 政策意义" in t2)
    ck("v2 含判据而非预测的定位", "本文的贡献**不是预测**" in t2)
    ck("v2 含第 35–36 条", "35. **本文的 `r` 是园区级替代率" in t2
       and "36. **`W/D` 本身是模型产物" in t2)'''
if old_ck in t:
    t = t.replace(old_ck, new_ck, 1)
    print("[OK] v2 指标加入本轮检查")
else:
    print("[MISS] v2 指标")

p.write_text(t, encoding="utf-8")
print("已更新 _final_check.py")
