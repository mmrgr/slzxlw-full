# -*- coding: utf-8 -*-
"""更新 _final_check.py：加入第 8 套核对（真实城市），更新文件/产物清单。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

p = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4\B0_瓶颈迁移主线\_final_check.py")
t = p.read_text(encoding="utf-8")

# 1) 门禁列表加入真实城市核对
old = '''        ("同步性检查", HERE / "_check_sync.py", "9/9"),
    ]'''
new = '''        ("同步性检查", HERE / "_check_sync.py", "9/9"),
        ("真实城市核对", HERE / "_verify_real_city.py", "30/30"),
    ]'''
if old in t:
    t = t.replace(old, new, 1); print("[OK] 门禁列表")
else:
    print("[MISS] 门禁列表")

# 2) 文件清单加入 32/33 号文档
old2 = '''        "图 FigR5.pdf": FIGDIR / "FigR5_grid_convergence.pdf",
        "图 FigR5.png": FIGDIR / "FigR5_grid_convergence.png",'''
new2 = '''        "图 FigR5.pdf": FIGDIR / "FigR5_grid_convergence.pdf",
        "图 FigR5.png": FIGDIR / "FigR5_grid_convergence.png",
        "SC一手证据": HERE / "32_SantaClara一手证据核实.md",
        "SC判据应用": HERE / "33_SantaClara判据应用结果.md",'''
if old2 in t:
    t = t.replace(old2, new2, 1); print("[OK] 文件清单")
else:
    print("[MISS] 文件清单")

# 3) 产物清单
old3 = '''        "rstar_grid_convergence_table.csv",
    ]'''
new3 = '''        "rstar_grid_convergence_table.csv",
        "_ca_k_distribution.json", "_ca_k_clean.json",
    ]'''
if old3 in t:
    t = t.replace(old3, new3, 1); print("[OK] 产物清单")
else:
    print("[MISS] 产物清单")

# 4) v2 指标
old4 = '''    ck("v2 含第 37-38 条", "37. **网格量化对效应量的影响" in t2
       and "38. **网格不一致的成因" in t2)'''
new4 = '''    ck("v2 含第 37-38 条", "37. **网格量化对效应量的影响" in t2
       and "38. **网格不一致的成因" in t2)
    ck("v2 含 §5.9 真实城市应用", "## 5.9 结果 6" in t2)
    ck("v2 含 §9.7 限制", "### 9.7 真实城市应用" in t2)
    ck("v2 含 k*=3.50 判据", "k* = 3.50" in t2)
    ck("v2 含第 39-44 条", "39. **§5.9 是应用，不是验证" in t2
       and "44. **`r*` 本身的参数不确定性" in t2)
    ck("v2 物种数已更正为 2", "模型实际追踪 2 个物种" in t2)
    ck("v2 参数锚定已更正为 20", "20 个有观测锚定" in t2)'''
if old4 in t:
    t = t.replace(old4, new4, 1); print("[OK] v2 指标")
else:
    print("[MISS] v2 指标")

p.write_text(t, encoding="utf-8")
print("已更新 _final_check.py")
