"""再版复现依赖核查: 用"文件名索引"避免路径拼接误报 (2026-10-17).

上一版直接匹配完整路径, 但脚本常用 `A13 / "supply_state_regimes.csv"` 这种
变量拼接, 导致误报"未找到"。
本版改为: 收集全仓库的文件名索引, 再检查脚本引用的文件名是否在其中。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
EXT = (".csv", ".json", ".txt", ".md", ".bib")

# 全仓库文件名索引
index: dict[str, list[Path]] = {}
for p in ROOT.rglob("*"):
    if p.is_file() and p.suffix in EXT and "_archive" not in str(p):
        index.setdefault(p.name, []).append(p)

src = (ROOT / "A40_投稿包/make_reproducibility_manifest.py").read_text(encoding="utf-8")
m = re.search(r"PRODUCER = \{(.*?)\n\}", src, re.S)
PRODUCER = dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', m.group(1)))
scripts = sorted({v for v in PRODUCER.values() if not v.startswith("（")})

# 只抓"纯文件名"字面量（不含路径分隔符），避免拼接问题
NAME_RE = re.compile(r'["\']([A-Za-z0-9_\u4e00-\u9fff][^"\'/\\]{0,80}\.(?:csv|json|txt|md|bib))["\']')

print("=" * 78)
print("复现依赖核查（文件名索引版）")
print("=" * 78)
print(f"  仓库索引文件数: {sum(len(v) for v in index.values())}")
print(f"  待查生成脚本: {len(scripts)}\n")

missing: list[tuple[str, str]] = []
checked = 0
for s in scripts:
    p = ROOT / s
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    names = {n for n in NAME_RE.findall(t)}
    checked += len(names)
    for n in sorted(names):
        if n not in index:
            missing.append((s, n))

print(f"  引用到的输入文件名共 {checked} 处")
print(f"  其中包内找不到的: {len(missing)}\n")
uniq = sorted({n for _s, n in missing})
for n in uniq:
    srcs = sorted({s for s, nn in missing if nn == n})
    print(f"  [缺] {n}")
    for s in srcs[:3]:
        print(f"        引用者: {s}")

# 排除误报: "来自 summary.json" 是说明文字, 不是文件名
uniq = [n for n in uniq if not n.startswith(("来自", "见", "参见"))]

# 已知外部依赖（不在包内但可从公开来源获取）——见 Code availability 第 3 条
KNOWN_EXTERNAL = {
    "project.json": "AI-UWM 引擎示例数据 (ENGINE/examples/cawcc_r2/*)",
    "timeseries.csv": "AI-UWM 引擎示例数据 (ENGINE/examples/cawcc_r2/*)",
}
unknown = [n for n in uniq if n not in KNOWN_EXTERNAL]

print()
if not uniq:
    print("裁定: 生成脚本的输入依赖全部在包内 ✓")
    sys.exit(0)
print(f"  包内缺失 {len(uniq)} 个:")
for n in uniq:
    note = KNOWN_EXTERNAL.get(n, "⚠ 未知来源")
    print(f"    {n:<22} {note}")
print()
if not unknown:
    print(f"裁定: {len(uniq)} 个缺失项均为已知外部依赖（引擎数据），已在 Code availability 说明 ✓")
    sys.exit(0)
print(f"裁定: {len(unknown)} 个缺失项来源未知，需人工判断 ✗")
sys.exit(1)
