# -*- coding: utf-8 -*-
"""把第 6 套核对（摘要溯源）纳入 _final_check.py，并更新 v2 指标检查。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

p = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4\B0_瓶颈迁移主线\_final_check.py")
t = p.read_text(encoding="utf-8")

# 1) 门禁列表
old = '''        ("政策区隔核对", HERE / "_verify_policy_bridge.py", "25/25"),
    ]'''
new = '''        ("政策区隔核对", HERE / "_verify_policy_bridge.py", "25/25"),
        ("摘要溯源核对", HERE / "_verify_abstract_numbers.py", "26/26"),
    ]'''
if old in t:
    t = t.replace(old, new, 1)
    print("[OK] 门禁列表加入摘要溯源")
else:
    print("[MISS] 门禁列表")

# 2) v2 指标：检查首行、摘要覆盖、§7 标题
old_ck = '''    ck("v2 含第 35–36 条", "35. **本文的 `r` 是园区级替代率" in t2
       and "36. **`W/D` 本身是模型产物" in t2)'''
new_ck = '''    ck("v2 含第 35–36 条", "35. **本文的 `r` 是园区级替代率" in t2
       and "36. **`W/D` 本身是模型产物" in t2)
    ck("v2 首行已改为 v2", t2.startswith("# 主稿 v2"))
    ck("v2 状态行已改为定稿候选", "v2 定稿候选" in t2 and "v1 草稿" not in t2)
    ck("v2 §7 标题已改为三杠杆", "再生水的三个杠杆" in t2)
    # 摘要覆盖度
    import re as _re
    _ab = _re.search(r"## 摘要\\n(.*?)\\n---", t2, flags=_re.S)
    _ab = _ab.group(1) if _ab else ""
    for _kw, _name in (("四类", "四情形分类"), ("情形 I", "情形命名"),
                       ("W/D", "口径区隔"), ("判据与条件", "判据定位"),
                       ("0.6842", "多物种取紧"), ("精确为零", "零效应"),
                       ("可证伪", "可证伪性")):
        ck(f"摘要覆盖：{_name}", "OK" if _kw in _ab else "MISSING", "摘要", _kw in _ab)'''
if old_ck in t:
    t = t.replace(old_ck, new_ck, 1)
    print("[OK] v2 指标加入首行/摘要/§7 检查")
else:
    print("[MISS] v2 指标")

p.write_text(t, encoding="utf-8")
print("已更新 _final_check.py")
