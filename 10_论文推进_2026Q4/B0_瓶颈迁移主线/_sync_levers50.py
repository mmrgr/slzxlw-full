# -*- coding: utf-8 -*-
"""把母稿 §7.0 / §7.5 同步为 50 MW 同网格重跑后的真实值。

背景：2026-10-18 用 scripts/run_reuse_levers_50mw.py 在与主结果相同的 50 MW 网格上
重跑了两个杠杆，结果：
  - 基线 HA 1150 / CO 1450（与 physical_daily 一致）
  - 处理能力杠杆：两端恒 0 增益
  - 产水量杠杆：HA +250 MW（1150→1400），CO 0 增益
旧 100 MW 网格的 +300（1100→1400）里含基线取整伪影，真增益是 +250。
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"

OLD_70 = """| 杠杆 | 操作 | 机制 | D-HA 效果 | D-CO 效果 |
|---|---|---|---|---|
| **处理能力** | 扩大再生水厂处理规模，产水量不变 | 无（产水量才是约束） | CAWCC 恒 **1100**，增益 **0** | CAWCC 恒 **1400**，增益 **0** |
| **产水量** | 提高 WWTW 分流比 0.16→0.25 | 增加可用再生水总量 | CAWCC **1100→1400**（+300），瓶颈迁移至电网 | 无效（瓶颈本在电网） |
| **配比 r** | 提高替代率目标 0.5→0.8 | 混合水质压低 CoC，推高补水需求 | 纯物理 CAWCC **1200→1100**（−100） | 基本无变化（条件②不满足） |

> ⚠️ **口径声明**：表中"处理能力"与"产水量"两行取自 **100 MW 网格**的边际曲线产物（基点 HA 1100 / CO 1400）；"配比 r"行取自 **50 MW 网格**的全网格扫描。**两者不是同一网格，其 MW 数值不可直接相减或相加。** 该表的用途是展示三者的**方向差异**，不是数值比较。"""

NEW_70 = """| 杠杆 | 操作 | 机制 | D-HA 效果 | D-CO 效果 |
|---|---|---|---|---|
| **处理能力** | 扩大再生水厂处理规模，产水量不变 | 无（产水量才是约束） | CAWCC 恒 **1150**，增益 **0** | CAWCC 恒 **1450**，增益 **0** |
| **产水量** | 提高 WWTW 分流比 0.16→0.25 | 增加可用再生水总量 | CAWCC **1150→1400**（+250），瓶颈迁移至电网 | 无效（瓶颈本在电网） |
| **配比 r** | 提高替代率目标 0.5→0.8 | 混合水质压低 CoC，推高补水需求 | 纯物理 CAWCC **1200→1100**（−100） | 基本无变化（条件②不满足） |

> ✅ **口径已统一（2026-10-18 重跑）**：表中三行现在全部来自 **50 MW 网格**，与主结果
> `physical_daily`（1150 / 1450 MW）**同网格**，故其 MW 数值可直接比较与相减。
> 两个杠杆曲线已按同网格重跑（`reuse_marginal_curve_50mw*.csv`、
> `reuse_production_marginal_curve_50mw*.csv`、`reuse_levers_50mw_summary.json`）。
>
> ⚠️ **本表修订了此前的一个数值**：产水量杠杆的增益由旧版 **+300 MW** 改为 **+250 MW**。
> 旧值取自 100 MW 网格（基线 HA 1100 / CO 1400），而该网格从未评估 1150 这一点，
> 故 1400−1100=+300 中混入了基线取整伪影。**+250 才是真实增益。**
> 定性结论不变且更强：增益真实存在、瓶颈确实迁移、处理能力杠杆恒为零。
> 另需记录：本次扫描中联合口径与纯物理口径在两端数值相同（1150 / 1450），
> 因该区间的政策约束并非紧约束——此点已核验而非假定（主稿 §5.8 的替代码扫描则相差 300 MW）。"""

OLD_75 = """| 杠杆 | 操作 | D-HA 结果 | D-CO 结果 |
|---|---|---|---|
| **仅扩处理能力** | `treatment_capacity_ml_day` 40→160（HA）/ 36→160（CO），**产水量不变** | CAWCC **恒 1100 MW**，边际增益 **恒 0** | CAWCC **恒 1400 MW**，边际增益 **恒 0** |
| **提高产水量** | `central_reuse_fraction` 0.16→0.60（HA）/ 0.15→0.60（CO） | CAWCC **1100 → 1400 MW**（+300），瓶颈由**水源取水→电网接网** | CAWCC **恒 1400 MW**（不动；同为 100 MW 网格口径） |

> ⚠️ **口径声明（本表必须携带）**：本表两个杠杆的数值**均取自 100 MW 网格的边际曲线产物**
> （`reuse_marginal_curve.csv` / `reuse_production_marginal_curve.csv`），基点为 **HA 1100 / CO 1400 MW**。
> **与主结果（50 MW 网格，physical_daily = 1150 / 1450）不是同一网格，不可做算术。**
> 若要得到 50 MW 网格上的对应值，须按同网格重跑这两个杠杆——**本文未做**（列为待办）。
> 本表的定性结论（零增益 vs 有效、瓶颈迁移方向）与网格无关，故不受此限制影响。"""

NEW_75 = """| 杠杆 | 操作 | D-HA 结果 | D-CO 结果 |
|---|---|---|---|
| **仅扩处理能力** | `treatment_capacity_ml_day` 40→160（HA）/ 36→160（CO），**产水量不变** | CAWCC **恒 1150 MW**，逐点边际增益 **恒 0** | CAWCC **恒 1450 MW**，逐点边际增益 **恒 0** |
| **提高产水量** | `central_reuse_fraction` 0.16→0.60（HA）/ 0.15→0.60（CO） | CAWCC **1150 → 1400 MW**（**+250**），瓶颈由**水源取水→电网接网** | CAWCC **恒 1450 MW**（不动） |

> ✅ **口径声明（本表必须携带）**：本表两个杠杆的数值均取自 **50 MW 网格**，与主结果
> （`physical_daily` = HA 1150 / CO 1450 MW）**同网格**，可直接比较。
> 产物：`r2/{ha,co}/reuse_marginal_curve_50mw.csv`、
> `r2/{ha,co}/reuse_production_marginal_curve_50mw.csv`、
> `r2/reuse_levers_50mw_summary.json`。
> 旧 100 MW 网格版本（`reuse_marginal_curve.csv` 等，基线 1100/1400、增益 +300）
> 作为历史对照保留，其 +300 已证实含基线取整伪影，**不采用**。"""


def main() -> None:
    text = MS.read_text(encoding="utf-8")
    n = 0
    for old, new, tag in ((OLD_70, NEW_70, "§7.0"), (OLD_75, NEW_75, "§7.5")):
        if old in text:
            text = text.replace(old, new, 1)
            n += 1
            print(f"OK {tag}")
        else:
            print(f"未匹配 {tag}")
    MS.write_text(text, encoding="utf-8")
    print(f"\n完成 {n}/2，母稿长度 {len(text)} 字符")


if __name__ == "__main__":
    main()
