"""修正主稿中被 `\\r` 吃掉的 LaTeX (2026-10-17).

`$n_{\\rm eff}$` -> 被破坏为 `$n_{` + 换行 + `m eff}$`
`$dS_{\\rm pot}$` -> 同样问题
共 2 处。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

before = len(re.findall(r'[_^]\{\n', t))
# 把 `_{` + 换行 + `m ` 还原为 `_{\rm `
t2 = re.sub(r'([_^])\{\nm\s', r'\1{\\rm ', t)
after = len(re.findall(r'[_^]\{\n', t2))

MS.write_text(t2, encoding="utf-8")
print(f"_{{ 后接换行: {before} -> {after}")

# 复验两处
for pat in (r'\$n_\{\\rm eff\}=117\$', r'\$dS_\{\\rm pot\}\$'):
    print(f"  {pat}: {len(re.findall(pat, t2))} 处")
