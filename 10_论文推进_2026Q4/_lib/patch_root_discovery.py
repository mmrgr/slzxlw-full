"""把 `parent.parent` 式根定位改为标记式根定位 (2026-10-16).

【背景】移动目录会破坏 `Path(__file__).resolve().parent.parent` 这种"按层数推算"的写法。
本脚本对每个目标文件做**最小侵入替换**:

    旧: ROOT = Path(__file__).resolve().parent.parent
    新: ROOT = _research_root()      # 由 _lib/_find_root.py 提供

并在文件顶部注入一个**无侵入的** `_research_root()` 定义(不依赖 import _lib,
这样脚本被单独拷出也能跑):

    def _research_root() -> Path:
        \"\"\"标记式定位研究目录根 (不依赖脚本层数)。\"\"\"
        import os
        for base in (Path(__file__).resolve().parent, *Path(__file__).resolve().parent.parents):
            if (base / "_lib").is_dir() or (base / "_PROJECT_ROOT").exists():
                return base
        env = os.environ.get("AIUWM_RESEARCH_DIR")
        if env and Path(env).is_dir():
            return Path(env)
        raise RuntimeError("找不到研究目录根; 请确认 _lib/ 或 _PROJECT_ROOT 存在")

【安全性】
  · 逐文件备份到 _lib/_rootpatch_backup/;
  · 替换后做语法检查 (ast.parse);
  · 失败自动还原该文件;
  · 支持 --revert 一键还原。

用法:
  python _lib/patch_root_discovery.py --dry-run
  python _lib/patch_root_discovery.py --apply
  python _lib/patch_root_discovery.py --revert
"""
from __future__ import annotations

import argparse
import ast
import re
import shutil
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BACKUP = HERE / "_rootpatch_backup"

TARGETS = [
    ("A10_敏感性与边界", "city_model.py", "ROOT = HERE.parent", "HERE_PARENT"),
    ("A16_英文稿", "audit_traceability_v2.py", "ROOT = Path(__file__).resolve().parent.parent", "PP"),
    ("A16_英文稿", "audit_traceability_v3.py", "ROOT = Path(__file__).resolve().parent.parent", "PP"),
    ("A28_末轮审计", "scan_corruption.py", "ROOT = Path(__file__).resolve().parent.parent", "PP"),
    ("A36_终审", "final_gate.py", "ROOT = Path(__file__).resolve().parent.parent", "PP"),
    ("A40_投稿包", "make_reproducibility_manifest.py", "ROOT = HERE.parent", "HERE_PARENT"),
    ("A41_全包审计", "package_consistency_check.py", "ROOT = Path(__file__).resolve().parent.parent", "PP"),
]

HELPER = '''

def _research_root() -> Path:
    """标记式定位研究目录根 (不依赖脚本所在层数)。

    2026-10-16 整理轮加入: 原写法 `Path(__file__).resolve().parent.parent`
    在脚本被移入子目录后会算错根, 导致所有相对路径断链。
    """
    import os
    _h = Path(__file__).resolve()
    for _b in (_h.parent, *_h.parent.parents):
        if (_b / "_lib").is_dir() or (_b / "_PROJECT_ROOT").exists():
            return _b
    _env = os.environ.get("AIUWM_RESEARCH_DIR")
    if _env and Path(_env).is_dir():
        return Path(_env)
    raise RuntimeError(
        "找不到研究目录根 (10_论文推进_2026Q4)。"
        "请确认该目录下存在 _lib/ 或 _PROJECT_ROOT 标记文件。")
'''


def patch_one(path: Path, old: str, kind: str, apply: bool) -> bool:
    txt = path.read_text(encoding="utf-8")
    if "_research_root" in txt:
        print(f"  跳过(已打过补丁): {path.name}")
        return False

    if old not in txt:
        print(f"  ✗ 未找到锚点: {path.name}\n      期望: {old}")
        return False

    # 生成替换
    new = "ROOT = _research_root()"
    new_txt = txt.replace(old, new, 1)

    # 注入 helper: **紧接在 `ROOT = _research_root()` 那一行之前**插入定义,
    # 保证调用点之前已有定义 (此前版本插在 import 之后, 但 ROOT 行在更后面,
    # 仍会 NameError —— 已修正)。
    lines = new_txt.splitlines()
    idx = next((i for i, l in enumerate(lines)
                if l.strip().startswith("ROOT = _research_root()")), None)
    if idx is None:
        print(f"  ✗ 找不到注入位置: {path.name}")
        return False
    helper_lines = HELPER.strip("\n").splitlines()
    lines[idx:idx] = helper_lines + [""]
    new_txt = "\n".join(lines)

    # 语法检查
    try:
        ast.parse(new_txt)
    except SyntaxError as e:
        print(f"  ✗ 语法错误, 跳过 {path.name}: {e}")
        return False

    print(f"  ✓ {path.name}:")
    print(f"      - {old}")
    print(f"      + {new}")

    if apply:
        BACKUP.mkdir(exist_ok=True)
        shutil.copy2(path, BACKUP / path.name)
        path.write_text(new_txt, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--revert", action="store_true")
    a = ap.parse_args()

    if a.revert:
        n = 0
        for f in BACKUP.glob("*.py"):
            # 找到原位置
            for d, name, _, _ in TARGETS:
                if name == f.name:
                    dst = ROOT / d / name
                    shutil.copy2(f, dst)
                    print(f"  ✓ 还原 {d}/{name}")
                    n += 1
        print(f"还原 {n} 个文件")
        return 0

    if not a.apply:
        a.dry_run = True
    print("=" * 74)
    print("根定位补丁 " + ("(dry-run)" if a.dry_run else "(APPLY)"))
    print("=" * 74)
    n = 0
    for d, name, old, kind in TARGETS:
        p = ROOT / d / name
        if not p.exists():
            print(f"  ✗ 不存在: {d}/{name}")
            continue
        if patch_one(p, old, kind, a.apply):
            n += 1
    print(f"\n{'将修改' if a.dry_run else '已修改'} {n} 个文件")
    if a.dry_run:
        print("(dry-run; 加 --apply 执行)")
    else:
        print(f"备份在 {BACKUP}")
        print("⚠ 下一步必须重跑七套门禁")
    return 0


if __name__ == "__main__":
    sys.exit(main())
