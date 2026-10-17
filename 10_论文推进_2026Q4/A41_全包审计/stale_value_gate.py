"""门禁 10: 关键计数与残差不得为陈旧值 (2026-10-17).

【为何需要】
本轮发现: 用 grep 追特定数字会**漏掉表格内的计数**。
具体漏网:
  · 主稿 Discussion "残差 2.55e-11 / 相对 2.9e-16"（应为 4.37e-11 / 3.55e-16）—— 4 处
  · 主稿分支表 "232 cases"（应为 234）、"369 of 372"（应为 380 of 391）
  · SI 3 处旧残差
这些都是**结论变更后未同步**的陈旧值, 但九道门禁都没抓到。

【本门禁的做法】
不再 grep 具体数字, 而是:
  1. 从**权威产物**实时计算一组"关键量";
  2. 扫描主稿, 检查是否存在**已知陈旧值**(黑名单);
  3. 并验证权威量确实出现在主稿中(白名单必须命中)。

黑名单是"曾被修正过的值", 一旦它们重新出现就说明回退或漏改。
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
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
SI = ROOT / "A16_英文稿/supplementary_information.md"

import numpy as np
import pandas as pd

d = pd.read_csv(ROOT / "A13_可靠性机制/supply_state_regimes.csv")
rel = d[(d.status == "converged_unique") & (~d.coc_floor_degenerate.astype(bool))].copy()
C = rel.inc_B2_ml - rel.inc_B1_ml
x = rel.x_ai_B1_ml
pure = np.isclose(x, C, rtol=1e-9)
nodisp = np.isclose(C, 0, atol=1e-9)

# --- 权威量(实时计算) ---
truth = {
    "n_reliable": len(rel),
    "n_all": len(d),
    "status_fail": int((d.status != "converged_unique").sum()),
    "neg": int((rel.dS_pot_ml < 0).sum()),
    "pos": int((rel.dS_pot_ml > 0).sum()),
    "zero": int((rel.dS_pot_ml == 0).sum()),
    "pure_disp": int(pure.sum()),
    "nodisp": int(nodisp.sum()),
    "nodisp_neg": int((rel[nodisp].dS_pot_ml < 0).sum()),
}

# --- 黑名单: 曾出现过的陈旧值(一旦重现即 FAIL) ---
STALE = {
    "2.55 × 10⁻¹¹": "旧恒等式残差(A19修复前)",
    "2.5 × 10⁻¹¹": "旧恒等式残差简写",
    "2.9 × 10⁻¹⁶": "旧相对残差",
    "| 232 cases": "旧纯挤占计数(应 234)",
    "**369 of 372**": "旧无挤占负值计数(应 380 of 391)",
    "| 813 ": "旧可靠子集(应 839)",
    "643 beneficial": "旧符号统计(应 626)",
    "134 harmful": "旧符号统计(应 177)",
    "290 of 290": "旧 q>0 计数(应 263)",
}

# --- 白名单: 权威量必须在主稿出现 ---
MUST_APPEAR = ["n_reliable", "neg", "pos", "pure_disp", "nodisp_neg"]


def main() -> int:
    ms = MS.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    both = ms + "\n" + si
    print("=" * 74)
    print("关键计数与残差陈旧值门禁")
    print("=" * 74)
    fails = 0

    print("\n[黑名单] 陈旧值不得重现:")
    for s, why in STALE.items():
        hit = s in both
        print(f"  [{'FAIL' if hit else 'PASS'}] {s!r}  ({why})")
        if hit:
            fails += 1

    print("\n[白名单] 权威量必须出现:")
    for k in MUST_APPEAR:
        v = str(truth[k])
        hit = re.search(r"(?<![\d.])" + v + r"(?![\d.])", ms) is not None
        print(f"  [{'PASS' if hit else 'FAIL'}] {k} = {v}")
        if not hit:
            fails += 1

    print(f"\n裁定: {'无陈旧值 ✓' if fails == 0 else f'{fails} 项不合格 ✗'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
