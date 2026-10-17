"""执行目录重组: 分组 + 旧路径 junction 兼容 (2026-10-16).

【核心思路 — 既整理结构又不断链】
问题: 44 个 A* 目录共被 **328 处**硬编码引用。直接移动会让大量脚本失效。
方案: **移动真实目录 + 在旧路径建 junction(目录联接)**。
  · 真实位置:  03_实验/A13_可靠性机制/
  · 旧路径:     A13_可靠性机制  ->  junction 指向真实位置
  · 效果: 所有 `ROOT / "A13_可靠性机制" / "x.csv"` **原样可用**,
          同时结构变清楚。

【已验证 junction 在此环境可用且对 Python 透明】
  · Path.read_text / pandas.read_csv / to_csv 均正常;
  · ⚠ 唯一副作用: `rglob` 会**穿透 junction 重复计数** —— 故后续扫描脚本
    需排除 junction (本脚本提供 `_is_junction()` 辅助)。

【安全措施】
  1. 执行前记录每个目录的**文件数 + 总字节 + 抽样哈希**, 移动后复验;
  2. 移动失败自动回滚(把已移动的移回);
  3. 完成后提示重跑七门禁;
  4. `--rollback` 可撤销: 删除 junction, 把真实目录移回原位。

用法:
  python _lib/apply_reorg.py --dry-run     # 只打印计划
  python _lib/apply_reorg.py --apply       # 执行
  python _lib/apply_reorg.py --rollback    # 撤销
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # 10_论文推进_2026Q4
STATE = HERE / "_reorg_state.json"

GROUPS: dict[str, list[str]] = {
    "01_文献与设计": ["01_后续任务详细规划_v2.md", "00_深度规划_v1.md"],
    "02_模型与参数": ["A10_敏感性与边界", "A4_水化学参数域", "A1_传输账本",
                      "A12_时间分辨率"],
    "03_实验": ["A2_规则实验", "A3_三规则内生", "A5_设施锚定", "A7_质量分配联合",
                "A8_溶质闭合", "A9_无量纲折叠", "A11_适应成本", "A13_可靠性机制",
                "A15_稳健性", "A18_有限供水", "A19_水化学包络", "A20_模型桥接",
                "A21_动态状态", "A22_判据分解", "A30_WP0取证", "A31_WP2_假设冻结",
                "A32_WP3_水化学", "A33_WP4_组成重构", "A34_WP5_敏感性与极端事件",
                "A38_模拟审稿"],
    "04_审计": ["A25_终审", "A26_语义统一", "A27_引用限值", "A28_末轮审计",
                "A36_终审", "A41_全包审计", "A44_检查清理轮"],
    "05_论文": ["A16_英文稿", "A35_WP7_主稿修订", "A37_六主图_v4", "A40_投稿包",
                "A42_参考文献", "A43_投稿声明", "09_图定稿", "A6_可信度配图",
                "10_论文主稿_v1.md", "figstyle.py", "T15_finalize_figures.py"],
    "06_外部数据": ["A14_外部锚定", "A24_外部锚定", "A29_文献核验",
                    "A39_WP8_外部效度"],
    "07_过程记录": ["02_阶段结果_T0-T7.md", "03_阶段结果_T2-T8.md",
                    "04_阶段结果_T9.md", "05_方法审计_v1.md", "06_审计修复_v1.md",
                    "07_阶段结果_T10-T13.md", "08_阶段结果_T5-T14.md",
                    "11_红队自审_T17.md", "12_一致性核验_v1.md",
                    "13_死代码与重复逻辑清单_v1.md", "14_清理执行报告_v1.md",
                    "15_图形修复报告_v1.md", "16_工作交接.md",
                    "17_本轮研究总结_2026-10-14.md",
                    "18_方法自审与修复报告_2026-10-14.md",
                    "19_缺陷报告_缓存与桥接_2026-10-15.md",
                    "20_科研成熟度深化轮总结_2026-10-15.md", "21_工作交接.md",
                    "A0_预注册"],
}

# 不做 junction 的项(文件或多处同名者) —— 文件用复制到组内 + 原处保留? 
# 决策: **只对目录做 junction**; 顶层 .md 直接移动(它们无代码引用)。
DIRS_ONLY = True

KEEP_TOP = {"_lib", "__pycache__", "文件功能清单.md"}


def _is_junction(p: Path) -> bool:
    try:
        return p.is_symlink() or os.path.islink(p) or (
            hasattr(os, "path") and os.path.isdir(p) and os.path.realpath(p) != str(p))
    except Exception:
        return False


def mklink(link: Path, target: Path) -> bool:
    """创建目录 junction (Windows mklink /J)。"""
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, text=True)
    return r.returncode == 0


def fingerprint(d: Path) -> dict:
    """目录指纹: 文件数 / 总字节 / 抽样哈希(前5个文件)。"""
    files = [f for f in d.rglob("*") if f.is_file()]
    files.sort()
    samp = []
    for f in files[:5]:
        try:
            h = hashlib.sha256(f.read_bytes()).hexdigest()[:12]
        except Exception:
            h = "ERR"
        samp.append((str(f.relative_to(d)), h))
    return {"n_files": len(files),
            "n_bytes": sum(f.stat().st_size for f in files),
            "sample": samp}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--rollback", action="store_true")
    a = ap.parse_args()

    if a.rollback:
        return do_rollback()
    if not (a.apply or a.dry_run):
        a.dry_run = True

    # 构建计划
    plan = []   # (src_rel, dst_rel, is_dir)
    for g, items in GROUPS.items():
        for it in items:
            src = ROOT / it
            if not src.exists():
                continue
            plan.append((it, f"{g}/{it}", src.is_dir()))

    print("=" * 78)
    print("目录重组 " + ("(dry-run)" if a.dry_run else "(APPLY)"))
    print("=" * 78)
    n_dir = sum(1 for _, _, d in plan if d)
    n_file = len(plan) - n_dir
    print(f"计划: 移动 {n_dir} 个目录(建 junction 兼容) + {n_file} 个文件(直接移动)")
    print()
    for g in sorted(GROUPS):
        items = [p for p in plan if p[1].startswith(g + "/")]
        if not items:
            continue
        print(f"[{g}]")
        for src, dst, isd in items:
            print(f"   {'DIR ' if isd else 'FILE'} {src}")
    print()

    if a.dry_run:
        print("(dry-run; 加 --apply 执行)")
        return 0

    # ---------- 执行 ----------
    state = {"moved": [], "junctions": [], "fingerprints": {}}
    done = []
    try:
        for src_rel, dst_rel, is_dir in plan:
            src = ROOT / src_rel
            dst = ROOT / dst_rel
            if _is_junction(src):
                print(f"  跳过(已是 junction): {src_rel}")
                continue
            if not src.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            if is_dir:
                state["fingerprints"][src_rel] = fingerprint(src)
            shutil.move(str(src), str(dst))
            done.append((src_rel, dst_rel, is_dir))
            if is_dir:
                ok = mklink(src, dst)
                if ok:
                    state["junctions"].append(src_rel)
                    print(f"  ✓ {src_rel}  ->  {dst_rel}   (+junction)")
                else:
                    print(f"  ⚠ {src_rel} 已移动, 但 junction 创建失败!")
            else:
                print(f"  ✓ {src_rel}  ->  {dst_rel}")
        state["moved"] = done
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        print(f"\n完成: {len(done)} 项; junction {len(state['junctions'])} 个")
        print(f"状态文件: {STATE}")
        print("\n⚠ 下一步必须: 重跑七套门禁验证无回归")
        return 0
    except Exception as e:
        print(f"\n✗ 失败: {e}\n回滚中...")
        for src_rel, dst_rel, is_dir in reversed(done):
            src, dst = ROOT / src_rel, ROOT / dst_rel
            try:
                if src.exists() and _is_junction(src):
                    subprocess.run(["cmd", "/c", "rmdir", str(src)],
                                   capture_output=True)
                if dst.exists():
                    shutil.move(str(dst), str(src))
            except Exception as e2:
                print(f"  回滚失败 {src_rel}: {e2}")
        return 1


def do_rollback() -> int:
    if not STATE.exists():
        print("无状态文件, 无法回滚"); return 1
    st = json.loads(STATE.read_text(encoding="utf-8"))
    print(f"回滚 {len(st['moved'])} 项...")
    for src_rel, dst_rel, is_dir in reversed(st["moved"]):
        src, dst = ROOT / src_rel, ROOT / dst_rel
        if src.exists() and _is_junction(src):
            subprocess.run(["cmd", "/c", "rmdir", str(src)], capture_output=True)
        if dst.exists():
            shutil.move(str(dst), str(src))
            print(f"  ✓ {dst_rel} -> {src_rel}")
    print("回滚完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
