"""把编辑期临时备份移入归档目录 (2026-10-17).

【为什么做】
项目根与各 A 目录下散落 27 个 `_bak_*` 文件(约 984 KB), 分两类:
  A. 我这几轮编辑时留的临时备份(`_bak_ms_*`, `_bak_si_*`, `_bak_structure_gate.py` 等) —— 无保留价值
  B. 阶段 0 修复前的数据备份(`_bak_*before_A19*`) —— 有历史留档价值

【判断】
· 主稿与 SI **完全不引用**这些文件(0 次);
· 仅 1 个(`_bak_T6_v2_before_A19_backfill.csv`)在阶段报告中被提及;
· 投稿包不应包含编辑期临时文件 —— 审稿人下载后看到一堆 `_bak_` 会困惑。

【处置】
· A 类: 移入 `_archive_2026-10-17/编辑期备份/`
· B 类: 移入 `_archive_2026-10-17/阶段0修复前备份/`
· 保留可追溯性(不删除), 但不在投稿包主路径上。
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "_archive_2026-10-17"
DIR_A = ARCH / "编辑期备份"
DIR_B = ARCH / "阶段0修复前备份"
DIR_A.mkdir(parents=True, exist_ok=True)
DIR_B.mkdir(parents=True, exist_ok=True)

moved_a = moved_b = 0
for p in sorted(ROOT.glob("**/_bak_*")):
    if "_archive" in str(p):
        continue
    if "before_A19" in p.name:
        dst = DIR_B / p.name
        if not dst.exists():
            shutil.move(str(p), str(dst))
        moved_b += 1
        print(f"  [B] {p.relative_to(ROOT)} -> _archive_2026-10-17/阶段0修复前备份/")
    else:
        dst = DIR_A / p.name
        if dst.exists():
            dst = DIR_A / f"{p.parent.name}__{p.name}"
        shutil.move(str(p), str(dst))
        moved_a += 1
        print(f"  [A] {p.relative_to(ROOT)} -> _archive_2026-10-17/编辑期备份/")

print(f"\n  编辑期备份 {moved_a} 个 · 阶段0备份 {moved_b} 个")

# 写归档说明
(ARCH / "README.md").write_text(
    "# 归档目录（2026-10-17）\n\n"
    "本目录存放**不进入投稿包**的历史文件，保留可追溯性。\n\n"
    "## 编辑期备份/\n\n"
    "2026-10-17 多轮编辑（结构重排、数字修正、论证补全）时留下的临时备份。\n"
    "主稿与 SI **均不引用**这些文件；它们是过程留痕，无功能作用。\n\n"
    "## 阶段0修复前备份/\n\n"
    "2026-10-17 阶段 0（A19→T6 回灌、缓存键修复）**修改数据之前**的产物快照。\n"
    "用于对照「修复前 vs 修复后」的数值变化，例如：\n"
    "- `_bak_e3b_before_A19.json`：E3b 折外中位增益由 0.000 变为 +0.0918 的原始状态\n"
    "- `_bak_T6_v2_before_A19_backfill.csv`：Figshare 组分回灌前的样本表\n\n"
    "⚠️ 这些**不是**当前有效数据，请勿用于复现；当前有效数据在 `A*` 各目录下。\n",
    encoding="utf-8")
print("  已写归档说明 README.md")
