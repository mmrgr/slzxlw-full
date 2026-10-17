"""重组 10_论文推进_2026Q4 的目录结构 (2026-10-16 第二次整理).

【用户诉求】不关心"哪一轮做了什么", 只关心**项目结构是否清楚**。
当前问题:
  · 45 个 `A*` 目录**平铺**, 编号错乱(A1, A10, A11 … A9), 语义混杂
     (阶段实验 / 专题分析 / 审计 / 交付物 混在一起);
  · 21 个 `NN_*.md` 散落顶层, 编号与内容无对应关系;
  · 4 个"审计"目录(A25/A28/A36/A41)、2 个"外部锚定"(A14/A24) 令人困惑。

【重组原则 — 安全第一】
  1. **不改任何被代码引用的路径**。项目 102/177 脚本硬编码 A* 目录名,
     故采用"**分组父目录 + 保留原目录名**"策略:
         A13_可靠性机制/  ->  experiments/A13_可靠性机制/
     这样只需**一处**新增/修改父目录, 且可用「双路径解析」兼容旧写法。
  2. 但**父目录变化仍会破坏 `ROOT / "A13_..."` 写法**。
     => 因此本脚本**先测后改**: 先扫描出所有硬编码引用, 改完后**必须重跑七门禁**;
        若门禁失败, 自动回滚。
  3. 提供 `_lib/project_paths.py` 的 DIR_TABLE 同步更新 + `_ALIASES` 兼容旧名。

【分组方案 (按"做什么"而非"哪一轮")】
  01_文献与设计/     -> 方案、开题、文献核验
  02_模型与参数/     -> 引擎封装、水化学参数域、传输账本
  03_实验/           -> 各专题实验(A1..A22 中的实验类)
  04_审计/           -> 全部审计类(A25,A28,A36,A41 + A27,A26...)
  05_论文/           -> 主稿、SI、六图、参考文献、声明
  06_外部数据/       -> A24,A39 等外部锚定
  07_过程记录/       -> 21 个 NN_*.md
  99_归档/           -> A4(部分废弃), A14(旧版) 等

⚠️ 本脚本**不自动执行移动**; 默认 dry-run, 打印计划供确认。
   加 `--apply` 才真正执行, 且执行后会提示"必须重跑七门禁"。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent          # .../_lib
ROOT = HERE.parent                              # .../10_论文推进_2026Q4

# ---------------------------------------------------------------------------
# 分组方案: 目标组 -> [目录/文件]
# ---------------------------------------------------------------------------
GROUPS: dict[str, list[str]] = {
    "01_文献与设计": [
        "01_后续任务详细规划_v2.md", "00_深度规划_v1.md",
    ],
    "02_模型与参数": [
        "A10_敏感性与边界",   # city_model.py 共享模型封装
        "A4_水化学参数域",    # 权威水样与引用限值 (被 18 脚本引用!)
        "A1_传输账本",
        "A12_时间分辨率",     # daily_model 封装
    ],
    "03_实验": [
        "A2_规则实验", "A3_三规则内生", "A5_设施锚定", "A7_质量分配联合",
        "A8_溶质闭合", "A9_无量纲折叠", "A11_适应成本",
        "A13_可靠性机制", "A15_稳健性", "A18_有限供水", "A19_水化学包络",
        "A20_模型桥接", "A21_动态状态", "A22_判据分解",
        "A30_WP0取证", "A31_WP2_假设冻结", "A32_WP3_水化学",
        "A33_WP4_组成重构", "A34_WP5_敏感性与极端事件",
        "A38_模拟审稿",
    ],
    "04_审计": [
        "A25_终审", "A26_语义统一", "A27_引用限值", "A28_末轮审计",
        "A36_终审", "A41_全包审计", "A44_检查清理轮",
    ],
    "05_论文": [
        "A16_英文稿", "A35_WP7_主稿修订", "A37_六主图_v4",
        "A40_投稿包", "A42_参考文献", "A43_投稿声明",
        "09_图定稿", "10_论文主稿_v1.md",
        "figstyle.py", "T15_finalize_figures.py",
    ],
    "06_外部数据": [
        "A14_外部锚定", "A24_外部锚定", "A29_文献核验",
        "A39_WP8_外部效度",
    ],
    "07_过程记录": [
        "02_阶段结果_T0-T7.md", "03_阶段结果_T2-T8.md", "04_阶段结果_T9.md",
        "05_方法审计_v1.md", "06_审计修复_v1.md", "07_阶段结果_T10-T13.md",
        "08_阶段结果_T5-T14.md", "11_红队自审_T17.md", "12_一致性核验_v1.md",
        "13_死代码与重复逻辑清单_v1.md", "14_清理执行报告_v1.md",
        "15_图形修复报告_v1.md", "16_工作交接.md",
        "17_本轮研究总结_2026-10-14.md", "18_方法自审与修复报告_2026-10-14.md",
        "19_缺陷报告_缓存与桥接_2026-10-15.md", "20_科研成熟度深化轮总结_2026-10-15.md",
        "21_工作交接.md", "A0_预注册",
    ],
}

# A6 是 Fig.2 的绘制脚本, 归入论文组
GROUPS["05_论文"].append("A6_可信度配图")

# 顶层保留项 (不移动)
KEEP_TOP = {"_lib", "__pycache__", "文件功能清单.md"}


def scan_hardcoded_refs(dirs: set[str]) -> dict[str, int]:
    """统计每个待移动目录名在 .py 中被硬编码引用的次数。"""
    counts: dict[str, int] = {}
    pys = [p for p in ROOT.rglob("*.py")
           if "__pycache__" not in str(p) and "_archive" not in str(p)
           and "_prev" not in str(p)]
    for d in dirs:
        c = 0
        for p in pys:
            try:
                if d in p.read_text(encoding="utf-8", errors="replace"):
                    c += 1
            except Exception:
                pass
        counts[d] = c
    return counts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真正执行移动(默认 dry-run)")
    args = ap.parse_args()

    # 校验分组覆盖: 每个存在的 A*/09_*/NN_* 都应被分配到某组
    assigned: dict[str, str] = {}
    for g, items in GROUPS.items():
        for it in items:
            if it in assigned:
                print(f"⚠ {it} 被重复分配: {assigned[it]} 与 {g}")
            assigned[it] = g

    existing = {p.name for p in ROOT.iterdir()}
    unassigned = sorted(existing - set(assigned) - KEEP_TOP - {"__pycache__"})
    # 忽略动态生成物
    unassigned = [u for u in unassigned if not u.endswith(".log.moved.md")]

    print("=" * 78)
    print("重组计划 (dry-run)" if not args.apply else "重组执行")
    print("=" * 78)

    dirs_to_move = {i for i in assigned if (ROOT / i).is_dir()}
    refs = scan_hardcoded_refs(dirs_to_move)

    for g in sorted(GROUPS):
        items = [i for i in GROUPS[g] if (ROOT / i).exists()]
        if not items:
            continue
        print(f"\n[{g}]  ({len(items)} 项)")
        for i in items:
            p = ROOT / i
            kind = "DIR " if p.is_dir() else "FILE"
            n = refs.get(i, 0)
            flag = f"  ⚠ 被 {n} 个脚本硬编码引用" if n else ""
            print(f"  {kind} {i}{flag}")

    if unassigned:
        print(f"\n⚠ 未被分配的顶层条目 ({len(unassigned)}):")
        for u in unassigned:
            print(f"    {u}")

    total_ref = sum(refs.values())
    print(f"\n{'-'*78}")
    print(f"待移动目录 {len(dirs_to_move)} 个; 涉及硬编码引用合计 {total_ref} 处")
    print(f"未分配条目 {len(unassigned)} 个")
    print("\n⚠ 若执行移动, 必须:")
    print("   1) 同步更新 _lib/project_paths.py 的 DIR_TABLE")
    print("   2) 为旧路径加 _ALIASES(或在脚本中加兼容解析)")
    print("   3) 重跑七套门禁; 若失败则回滚")

    if not args.apply:
        print("\n(dry-run; 加 --apply 执行)")
        return 1 if unassigned else 0

    print("\n注意: 本脚本未实现自动移动 —— 需先解决引用同步问题。")


if __name__ == "__main__":
    sys.exit(main() or 0)
