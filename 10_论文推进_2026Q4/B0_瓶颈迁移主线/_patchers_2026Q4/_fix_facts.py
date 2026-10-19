# -*- coding: utf-8 -*-
"""修复两处已核实的事实错误：
  1. 「5 个物种」→ 实际只有 TDS 与 chloride 2 个
  2. 「54 个参数中 50 个落在包络内」→ 实际 20 个有锚定、32 个无锚点、2 个越界
     （该错误会构成"夸大证据"，投稿前必须改）
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

# ---------- 修正 1：物种数 ----------
OLD1 = "水质按 TDS/氯化物/硬度/碱度/硅 5 个物种追踪。"
NEW1 = """水质按 **TDS 与氯化物 2 个物种**追踪。冷却系统的水质约束取这两个物种中较紧者。

> ⚠️ **一处必须说明的事实核对**：早期项目文档曾描述"五物种追踪"（TDS/氯化物/硬度/碱度/硅），但当前参数集（`examples/cawcc_r2/{ha,co}/project.json`）的 `water_quality_limits` 只有 `{TDS: 2200, chloride: 500}`，全部源水质参数也只有这两个物种。**模型实际追踪 2 个物种，不是 5 个。** 本文按实际配置报告。"""

# ---------- 修正 2：参数锚定 ----------
OLD2 = """54 个模型参数中 50 个落在 A01–A18 观测包络内（4 个越界项与 UNANCHORED 清单见 SI）；锚点来自本地文献库的便利抽样，**不是带检索式的正式系统综述**。"""
NEW2 = """54 个模型参数中，**20 个有观测锚定**（10 个落在包络内、10 个边界命中），**32 个无锚点**（`无锚点` 标记，未指定参考区间），**2 个越界**。逐项清单见 `parameter_envelope_R7.csv`。

> ⚠️ **本段此前版本写"54 个中 50 个落在包络内"，与产物不符，已更正。** 正确分布是：是（10）/ 边界命中（10）/ 无锚点（32）/ 否（2）。把"无锚点"计为"落在包络内"会夸大约 2.5 倍，属实质性错误。锚点本身来自本地文献库的便利抽样，**不是带检索式的正式系统综述**。"""


def main() -> None:
    t = V2.read_text(encoding="utf-8")
    ok = True

    if NEW1.split("\n")[0] in t or "模型实际追踪 2 个物种" in t:
        print("[SKIP] 物种数已更正")
    elif OLD1 in t:
        t = t.replace(OLD1, NEW1, 1)
        print("[OK  ] 物种数：5 → 2（含更正说明）")
    else:
        print("[MISS] 未找到物种表述")
        ok = False

    if "本段此前版本写" in t:
        print("[SKIP] 参数锚定已更正")
    elif OLD2 in t:
        t = t.replace(OLD2, NEW2, 1)
        print("[OK  ] 参数锚定：50/54 → 20/54（含更正说明）")
    else:
        print("[MISS] 未找到参数锚定表述")
        ok = False

    V2.write_text(t, encoding="utf-8")
    print("-" * 70)
    print(f"字数 {len(t):,}；行数 {t.count(chr(10)) + 1}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
