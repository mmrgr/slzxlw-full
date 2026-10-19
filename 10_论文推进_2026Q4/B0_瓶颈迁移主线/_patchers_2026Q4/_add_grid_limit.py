# -*- coding: utf-8 -*-
"""修正主稿 §5.8.2：为纯物理 CAWCC 主表加网格收敛性限定。

问题：该表按 r=0.1 步长列出 CAWCC，但网格收敛检验显示：
  - 零效应区（r≤0.5）三网格一致 ✅
  - 端点（r=0.9）降幅 −100/−100/−90，极差 10 MW ✅
  - 中间区（r=0.6/0.8）极差 30–40 MW ❌

因此该表必须携带网格限定，且不得让读者把中间值当作精确降幅。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_add_grid_limit.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
V2 = HERE / "03_主稿_v2.md"

OLD = """**证据**：`r2/rstar_physical_cawcc_by_r.csv`。

**三条读数**："""

NEW = """**证据**：`r2/rstar_physical_cawcc_by_r.csv`。

> ⚠️ **本表的网格限定（2026-10-18 新增检验，必须随表出现）**
>
> 上表的 CAWCC 由 **50 MW 网格**扫描得到。我们已把网格细化到 **25 MW**（全范围）与 **10 MW**（关键区间）重算，结果分三层：
>
> | 区间 | 50 MW | 25 MW | 10 MW | 判定 |
> |---|---|---|---|---|
> | **零效应区（r ≤ 0.5）** | 降幅 **0** | **0** | **0** | ✅ **三网格完全一致** |
> | **端点（D-HA, r=0.9）** | −100 | −100 | −90 | ✅ 稳健（极差 10 MW） |
> | **中间区（r=0.6 / 0.8）** | −50 / −100 | −25 / −75 | −10 / −70 | ❌ **极差 30–40 MW** |
>
> **三条必须遵守的引用规则**：
> 1. **零效应区的"零"可以直接引用**——它在三种网格下完全一致，不受量化影响。
> 2. **端点（r=0.9）的"约 −100 MW"可以引用**，但须注明 ±25 MW 网格量化。
> 3. **中间 r 值（0.6、0.7、0.8）的精确降幅不得引用**——极差达 30–40 MW，是取整伪影。
>
> **绝对值的系统性偏差**：CAWCC 随网格细化**单调趋近上界**（D-HA r=0.6：1150 → 1175 → 1190），说明 50 MW 网格系统性低估 0–25 MW。这是"最大可行容量点"这一定义在离散网格上的必然结果，不是模型错误。
>
> **为什么不一致**：边界常落在网格点之间。若真实边界为 1187 MW，50/25/10 MW 网格分别报 1150/1175/1180，三者都在合理趋近，但**相对各自基线（1200）的降幅**分别是 −50/−25/−20——两个取整误差之差即降幅误差。
>
> **证据**：`r2/rstar_grid_convergence_{50mw,25mw,10mw}.csv`、`r2/rstar_grid_convergence_table.csv`、`r2/rstar_grid_convergence_summary.json`。

**三条读数**："""

OLD_33 = """34. **多物种取紧后分类边界可能移动。**"""

NEW_37 = """34. **多物种取紧后分类边界可能移动。**"""


def main() -> None:
    text = V2.read_text(encoding="utf-8")
    if "本表的网格限定" in text:
        print("[SKIP] 网格限定已存在")
        return
    if OLD not in text:
        print("[MISS] 未找到 §5.8.2 证据锚点")
        sys.exit(1)
    text = text.replace(OLD, NEW, 1)
    V2.write_text(text, encoding="utf-8")
    print("[OK  ] §5.8.2 已加入网格限定")
    print(f"字数 {len(text):,}；行数 {text.count(chr(10)) + 1}")


if __name__ == "__main__":
    main()
