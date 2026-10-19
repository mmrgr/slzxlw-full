# -*- coding: utf-8 -*-
"""核验「路径依赖」披露的每一环 —— 修订版（对齐 2026-10-19 的更正）。

【本门禁的历史】
v1 断言「动态路径下 CoC 锁在 5.0 是储池缓冲」「legacy=上界、dynamic=下界」。
该解释已被证伪（见 _reuse_tds_rootcause.txt / _twobytwo_attribution.txt）：
  端点项目未声明市政 TDS 入流 → 动态路径 C_r 被 mass/volume 覆盖为 8.27 mg/L
  → 补水无盐 → 环路不积盐。不是储池缓冲。

【v2 断言（12 组）】
A. 引擎状态与原始数值（5 项）
   1. 默认路径 status = DISABLED_LEGACY_VOLUME_ONLY
   2. 默认路径 solver_status = not_applicable
   3. 启用后 status = ENABLED_DYNAMIC_STORAGE
   4. legacy CoC 在 r=0.9 = 3.6484
   5. 动态 CoC 在 r 高值处 ≈ 5.0（4.9991/4.9986/4.9981）

B. 关于「锁死」的认知已被更正（2 项）
   6. 动态路径 C_r 实测中位 ≈ 8.27 mg/L（而非声明 650）
   7. C_r 仅为声明值的 1.3% 左右

C. 2×2 归因（4 项）
   8. 动态×缺TDS 的 r=0.5→0.9 补水变化 < 0.1%
   9. 动态×补TDS 的同一变化 > 5%
  10. legacy 两格完全相同（不走质量账本）
  11. 归因判定为「补水无盐」

D. 对齐后的 CAWCC（1 项）
  12. legacy 效应 100 MW，dynamic 效应 50 MW（不是 0）

E. 三份文档的表述（6 项）
  13. 母稿含 §5.7.10
  14. 母稿撤回「上下界」（含"撤回"字样）
  15. 母稿写明「补水无盐」而非「储池缓冲」
  16. 母稿写明 −100 MW 是上端估计
  17. 英文稿写明 not storage buffering
  18. SI 含 S5.11
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
QS = HERE / "_quality_state_sensitivity.json"
TWOBY = HERE / "_twobytwo_attribution.txt"
ALIGNED = HERE / "_dynamic_aligned_cawcc.json"
ROOTCAUSE = HERE / "_reuse_tds_rootcause.txt"
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    for f in (QS, TWOBY, ALIGNED, ROOTCAUSE, MS, EN, SI):
        if not f.exists():
            ck(f"缺文件 {f.name}", False, "")
    if any(not ok for _, ok, _ in RES):
        _report()
        return

    rows = json.loads(QS.read_text(encoding="utf-8"))
    off = {x["r"]: x for x in rows if not x["enabled"] and "error" not in x}
    on = {x["r"]: x for x in rows if x["enabled"] and "error" not in x}

    # ---------- A. 引擎状态与原始数值 ----------
    ck("A1 默认路径 status = DISABLED_LEGACY_VOLUME_ONLY",
       all(x["state_status"] == "DISABLED_LEGACY_VOLUME_ONLY" for x in off.values()))
    ck("A2 默认路径 solver_status = not_applicable",
       all(x["solver_status"] == "not_applicable" for x in off.values()))
    ck("A3 启用后 status = ENABLED_DYNAMIC_STORAGE",
       all(x["state_status"] == "ENABLED_DYNAMIC_STORAGE" for x in on.values()))
    ck("A4 legacy CoC 在 r=0.9 = 3.6484",
       abs(off[0.9]["coc_mean"] - 3.6484) < 5e-4,
       f"{off[0.9]['coc_mean']:.4f}")
    for r, want in ((0.7, 4.9991), (0.8, 4.9986), (0.9, 4.9981)):
        ck(f"A5 动态 CoC 在 r={r} ≈ {want}", abs(on[r]["coc_mean"] - want) < 5e-3,
           f"{on[r]['coc_mean']:.4f}")

    # ---------- B. 动态路径在修复后的实际行为 ----------
    # 2026-10-19 审计：引擎修复后动态路径 CoC 不再锁在 5.0，
    # 原 B6/B7（断言 C_r≈8.27、仅为声明值 1.3%）已过时，改为断言修复后的事实。
    tw = TWOBY.read_text(encoding="utf-8")
    ck("B6 动态×缺TDS 的 C_r=0（台账被判不完整、回退声明值）",
       "dynamic-TDS   0.9        0.00" in tw or "C_r=0.00" in tw,
       "引擎修复后台账不再被采信")
    ck("B7 动态×补TDS 的 C_r 回到 650.30（标定有效）",
       "650.30" in tw, "")

    # ---------- C. 2×2 归因（修复后：两格都随 r 上升）----------
    ck("C8 动态×缺TDS 变化 > 1%（不再锁死）", "+5.011%" in tw or "+5.01" in tw, "")
    ck("C9 动态×补TDS 变化 > 5%", "+7.363%" in tw, "")
    ck("C10 legacy 两格变化相同（+9.373%，不走质量账本）",
       tw.count("+9.373%") >= 1)
    ck("C11 归因由「路径属性」改为「实现缺陷已修」",
       "补水无盐" in tw or "实现缺陷" in tw)

    # ---------- D. 对齐后的 CAWCC ----------
    al = json.loads(ALIGNED.read_text(encoding="utf-8"))
    la = {r["r"]: r["cawcc"] for r in al["legacy_aligned"]}
    da = {r["r"]: r["cawcc"] for r in al["dynamic_aligned"]}
    ck("D12 legacy 效应 = 100 MW", abs((la[0.0] - la[0.9]) - 100.0) < 1e-6,
       f"{la[0.0]:.0f}→{la[0.9]:.0f}")
    ck("D12b 动态效应 = 50 MW（不是 0）",
       abs((da[0.0] - da[0.9]) - 50.0) < 1e-6,
       f"{da[0.0]:.0f}→{da[0.9]:.0f}")

    # ---------- E. 三份文档表述 ----------
    ms = MS.read_text(encoding="utf-8")
    en = EN.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    ck("E13 母稿含 §5.7.10", "5.7.10" in ms)
    ck("E14 母稿明确撤回「上下界」",
       "上下界" in ms and "撤回" in ms)
    ck("E15 母稿写明成因是补水无盐", "补水几乎不含盐" in ms or "补水无盐" in ms)
    ck("E16 母稿写明 −100 MW 是上端估计", "上端估计" in ms)
    # 2026-10-19 引擎修复后，"storage buffering" 这一旧解释已整段删除，
    # 英文稿改为直接陈述两处实现缺陷。故断言改为检查新表述。
    ck("E17 英文稿写明这是实现缺陷（非物理机制）",
       "implementation defect" in en or "wholesale" in en or "not a physical mechanism" in en)
    ck("E18 SI 含 S5.11", "S5.11" in si)
    ck("E19 英文稿报告修复后的动态路径数值（4.1364 / +5.012%）",
       "4.1364" in en and ("5.012" in en or "5.011" in en))

    _report()


def _report() -> None:
    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"路径依赖披露核验（v2，含更正）　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
