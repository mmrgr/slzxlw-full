# -*- coding: utf-8 -*-
"""修正主稿 v2 §5.7.3b 中"三情形 r=0.8 取水一致"的错误表述。

正确表述：情形 I 与 II 在 r=0.6/0.8 重合（都受水质支配），情形 III 因设计值
更低（2.5）仍不触顶，取水不同。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_fix_regime_claim.py
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

OLD = """3. **三种情形在 r=0.8 时总取水完全相同（23,840.9 ML）**。原因：r=0.8 时三者 CoC 都等于 `L/C_mix(0.8) = 2200/556 = 3.9568`，小于各自的设计值，故约束都由同一混合水质决定。**这是一个精确的交叉验证：高替代率下取水行为完全由水质决定，与设计浓缩倍数无关。**"""

NEW = """3. **情形 I 与 II 在高替代率端精确重合，情形 III 不重合**。逐点比对：

| r | 情形 I（CoC_d=15） | 情形 II（CoC_d=5） | 情形 III（CoC_d=2.5） |
|---:|---:|---:|---:|
| 0.4 | 5.9783 | 5.0000 | 2.5000 |
| 0.6 | **4.7619** | **4.7619** | 2.5000 |
| 0.8 | **3.9568** | **3.9568** | 2.5000 |

当替代率上升使水质上限 `L/C_mix(r)` **低于两者的设计值**时，情形 I 与情形 II **合并**——此时二者 CoC 都由同一混合水质决定，总取水逐位相同（r=0.8 均为 23,840.93 ML）。**情形 III 不参与合并**，因其设计值 2.5 低于 `L/C_mix(0.8)=3.9568`，水质约束始终未触顶（其取水恒为 29,241.45 ML）。

→ **这条重合规律本身是一个诊断工具**：若两城市的取水曲线在高 r 端重合，说明它们都已进入"水质完全支配"区；若始终不重合，说明设计浓缩倍数仍在起约束作用。"""


def main() -> None:
    text = V2.read_text(encoding="utf-8")
    if NEW in text:
        print("[SKIP] 已修正")
        return
    if OLD not in text:
        print("[MISS] 未找到待修正段落")
        sys.exit(1)
    text = text.replace(OLD, NEW, 1)
    V2.write_text(text, encoding="utf-8")
    print("[OK  ] 已修正 §5.7.3b 的重合表述")
    print(f"字数 {len(text):,}；行数 {text.count(chr(10)) + 1}")


if __name__ == "__main__":
    main()
