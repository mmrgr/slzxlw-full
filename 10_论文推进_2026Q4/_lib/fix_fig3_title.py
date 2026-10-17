"""修 Fig3 标题中的 n_eff (2026-10-17).

避开 heredoc 转义问题: 用原始字符串处理 \\rm。
"""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "A37_六主图_v4" / "make_fig3.py"
t = p.read_text(encoding="utf-8")
old = r'ax.set_title("b  Strict-sign partition ($n_{\rm eff}$=813)"'
new = r'ax.set_title("b  Strict-sign partition ($n_{\rm eff}$=839)"'
if old in t:
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    print("已修 fig3 标题 n_eff=839")
else:
    import re
    m = re.search(r'ax\.set_title\("b  Strict-sign partition[^\n]*', t)
    print("未精确命中; 实际行 =", m.group(0) if m else "N/A")
