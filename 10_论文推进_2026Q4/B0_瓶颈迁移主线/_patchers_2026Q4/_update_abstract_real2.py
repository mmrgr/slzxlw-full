# -*- coding: utf-8 -*-
"""把 §5.9 真实城市应用写入摘要（按实际文本定位）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
V2 = HERE / "03_主稿_v2.md"

NEW_SECTION = """

**第六，判据可化为一个只需两个数的城市级筛查条件，并已在一个真实城市上应用。** 令 `k ≡ 全市自来水总量 / 全市再生水总量`，则园区配比 `r = 1/(1 + (6/26)·k)`；令 `r = r*` 解出 **`k* = 3.50`**——**`k < 3.50` 的城市，其数据中心配比必然越过 `r*`**。我们把判据用于加州 Santa Clara：市府 2026 年文件给出数据中心占全市自来水 **6%**、占全市再生水 **26%**；市府《2025 Urban Water Management Plan》给出两套口径的全市水量。供给能力口径下 `k = 5.43`、`r = 0.444`；2025 实际用量口径下 `k = 4.35`、`r = 0.499`——**两者均低于 `r* = 0.5532`，即尚未越过，但实际用量口径的余量仅 5.4 个百分点（9.8%）**。同一城市的两个独立官方数据源（UWMP 与加州 eAR）分别给出 `k = 4.35` 与 `4.90`，互为佐证。进一步用加州 eAR 2022 年全量数据（约 132 万行）算出 **169 个**同时报告两类水量的公共供水系统的 `k` 分布：中位 **13.54**，其中 **13.6%（大型系统 8.6%）的 `k < 3.50`**——这些城市若出现同等份额的数据中心，其配比将越过阈值。**这一节是判据的应用，不是机制的验证**：本文没有观测到"`r` 越过 `r*` 时补水需求确实上升"，那需要逐设施时序数据。
"""


def main() -> None:
    t = V2.read_text(encoding="utf-8")
    if "k* = 3.50" in t and "第六，判据可化为" in t:
        print("[SKIP] 摘要已含第六段")
        return

    # 定位摘要中"第五"段末尾（到"**本文不声称任何真实城市的承载容量"之前）
    m = re.search(
        r"(\*\*第五，在现行政策区间内.*?换算关系为 `r_max = u·\(W/D\)`。)\n\n(\*\*本文不声称任何真实城市的承载容量)",
        t, flags=re.S)
    if not m:
        print("[MISS] 未匹配到第五段末尾")
        # 退回到更宽松的定位
        idx = t.find("**本文不声称任何真实城市的承载容量")
        if idx < 0:
            print("[MISS] 也未找到收尾句")
            sys.exit(1)
        # 在收尾句前插入
        t = t[:idx] + NEW_SECTION.strip() + "\n\n" + t[idx:]
        print("[OK  ] 已在收尾句前插入第六段（宽松定位）")
    else:
        t = t[:m.end(1)] + NEW_SECTION + "\n\n" + t[m.start(2):]
        print("[OK  ] 已在第五段后插入第六段")

    V2.write_text(t, encoding="utf-8")
    print(f"字数 {len(t):,}；行数 {t.count(chr(10)) + 1}")


if __name__ == "__main__":
    main()
