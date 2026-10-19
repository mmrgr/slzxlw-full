# -*- coding: utf-8 -*-
"""把主稿 v1 升级为 v2：应用 17_v1到v2修正清单.md 中的全部修正。

本脚本只做**文本替换**，不改变任何产物、不重跑任何模型。
每处替换都断言原文存在（避免静默失败），并在末尾报告每处是否命中。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_apply_v2_patches.py

产物:
    03_主稿_v2.md       （v1 的应用结果）
    _v2_patch_report.json（逐处命中报告）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
V1 = HERE / "03_主稿_v1.md"
V2 = HERE / "03_主稿_v2.md"

# (标签, 原文, 替换文本)
PATCHES: list[tuple[str, str, str]] = []


def add(label: str, old: str, new: str) -> None:
    PATCHES.append((label, old, new))


# ---------------------------------------------------------------- 修正 1：§7.5 口径
add(
    "修正1a §7.5 处理能力行口径（1150→1100，1450→1400）",
    "| **仅扩处理能力** | `treatment_capacity_ml_day` 40→160（HA）/ 36→160（CO），**产水量不变** | CAWCC **恒 1150 MW**，边际增益 **恒 0** | CAWCC **恒 1450 MW**，边际增益 **恒 0** |",
    "| **仅扩处理能力** | `treatment_capacity_ml_day` 40→160（HA）/ 36→160（CO），**产水量不变** | CAWCC **恒 1100 MW**，边际增益 **恒 0** | CAWCC **恒 1400 MW**，边际增益 **恒 0** |",
)

add(
    "修正1b §7.5 表下追加口径声明",
    "**证据**：\n- 仅扩处理能力：`r2/ha/reuse_marginal_curve.csv`（7 个容量点，CAWCC 恒 1100）、`r2/co/reuse_marginal_curve.csv`（7 点，恒 1400）",
    """> ⚠️ **口径声明（本表必须携带）**：本表两个杠杆的数值**均取自 100 MW 网格的边际曲线产物**
> （`reuse_marginal_curve.csv` / `reuse_production_marginal_curve.csv`），基点为 **HA 1100 / CO 1400 MW**。
> **与主结果（50 MW 网格，physical_daily = 1150 / 1450）不是同一网格，不可做算术。**
> 若要得到 50 MW 网格上的对应值，须按同网格重跑这两个杠杆——**本文未做**（列为待办）。
> 本表的定性结论（零增益 vs 有效、瓶颈迁移方向）与网格无关，故不受此限制影响。

**证据**：
- 仅扩处理能力：`r2/ha/reuse_marginal_curve.csv`（7 个容量点，CAWCC 恒 1100）、`r2/co/reuse_marginal_curve.csv`（7 点，恒 1400）""",
)

add(
    "修正1c §7.5 CO 产水量行口径加注",
    "| **提高产水量** | `central_reuse_fraction` 0.16→0.60（HA）/ 0.15→0.60（CO） | CAWCC **1100 → 1400 MW**（+300），瓶颈由**水源取水→电网接网** | CAWCC **恒 1400 MW**（不动） |",
    "| **提高产水量** | `central_reuse_fraction` 0.16→0.60（HA）/ 0.15→0.60（CO） | CAWCC **1100 → 1400 MW**（+300），瓶颈由**水源取水→电网接网** | CAWCC **恒 1400 MW**（不动；同为 100 MW 网格口径） |",
)

# ---------------------------------------------------------------- 修正 2：§5.6 矛盾
add(
    "修正2 §5.6 删除\"未做阈值扰动\"（与 §9.2 第5条矛盾）",
    "- **迁移点未做 ±2% 阈值扰动敏感性检验**。这是本文的已知缺口（见 §9.2）。",
    "- **迁移点的阈值扰动敏感性已检验**（见 §9.2 第 5 条）：D-HA 日尺度 CAWCC 极差 **250 MW**（约 75 MW / 1% 阈值），D-CO 极差 **50 MW**；但**迁移结构稳健**——D-HA 首失效落在 1000–1350 MW（水源侧），D-CO 落在 1450–1500 MW（电网侧），**两域区间不重叠**。",
)

# ---------------------------------------------------------------- 修正 3：§7.2 指向 §5.7
add(
    "修正3 §7.2 追加指向 §5.7 的解析解释",
    "**证据**：`A13_可靠性机制/supply_state_regimes.csv`（`M0_ml`、`M1_ml`、`q` 可由 `(M0−M1)/M1` 计算）。",
    """**证据**：`A13_可靠性机制/supply_state_regimes.csv`（`M0_ml`、`M1_ml`、`q` 可由 `(M0−M1)/M1` 计算）。

> **该现象在 §5.7 得到解析解释。** 它不是情景间的偶然散布，而是 `CoC = min(CoC_design, L/C_mix)` 这一结构的必然结果：临界替代率 `r* = (L/CoC_design − C_p)/(C_r − C_p)` 可由水质参数闭式算出（两端点参数下为 **0.5532**）；超过它后补水需求单调上升，且该效应**与容量无关**。**上述 263/1027 是这一机制在参数抽样下的经验投影。**""",
)

# ---------------------------------------------------------------- 修正 4：§3.3 增加口径说明
add(
    "修正4 §3.3 十条约束表后补纯物理口径定义",
    "**(b) `max_reuse_utilization` 被剔除。**",
    """**(c) 本文报告两个口径，且主结论只基于其一。**
- **联合口径**：包含第 7 条 `reclaimed_water_substitution_ratio`（再生水替代率政策约束）；
- **纯物理口径**：**剔除**该条政策约束后的物理约束集。

这个区分在本文 §5.7–§5.8 具有实质意义：本文的自变量正是再生水替代率目标 r，若把"实际交付 ≥ 目标 r"留在判据集中，则提高 r 必然使约束更易失效——这是**自指**，不构成物理证据。因此**关于"r 是否改变承载容量"的主结论只基于纯物理口径**；联合口径仅作对照，并须明示两者差距（D-HA 在 r=0.9 时相差 **300 MW**）。

**(b) `max_reuse_utilization` 被剔除。**""",
)

# ---------------------------------------------------------------- 修正 5：§9 追加限制
add(
    "修正5 §9.5 后追加 23–28 条限制",
    "22. **本章统计基于 1027 个收敛唯一解情景**，剔除 16 个 `no_convergence` 与 9 个 `non_unique`。",
    """22. **本章统计基于 1027 个收敛唯一解情景**，剔除 16 个 `no_convergence` 与 9 个 `non_unique`。

### 9.6 水质兼容阈值章（§5.7–§5.8）的专门限定

23. **`r* = 0.5532` 不是普适常数。** 它是两端点水质参数（`L = 2200 mg/L`、`CoC_design = 5.0`、`C_potable = 180`、`C_reclaimed = 650`）下的取值。任何城市的 `r*` 须代入其自身参数：`r* = (L/CoC_design − C_p)/(C_r − C_p)`。两端点水质参数相同，故 `r*` 相同；真实城市各异。

24. **纯物理 CAWCC 的 −100 MW 受网格量化限制。** 容量扫描步长为 50 MW，真实降幅在 −50 至 −150 MW 之间。本文不声称精确值。

25. **联合口径与纯物理口径的差距（D-HA 在 r=0.9 时 300 MW）不得混报。** 联合口径包含"政策目标未达成"的成分，不是物理能力下降。本文主结论只基于纯物理口径（−100 MW），**主动拒绝较大的那个数（−400 MW）**。

26. **D-CO 的负结果必须报告。** 水质反噬在 D-CO 同样发生（CoC 同样由 5.0 降至 3.648），但因其瓶颈位于电力侧，纯物理 CAWCC 基本不变（1450，仅 r=0.9 时 1400）。**这恰好是"双因素判据"第二个条件的反证**，不隐藏。

27. **反噬百分比不可换算为 MW 降幅。** 响应是阈值穿越 + 网格量化的结果，本文不建立"反噬 % → MW"的换算公式。

28. **`r*` 判据的适用条件：应代入实际交付的再生水比例，而非政策目标值。** 当再生水池受限使实际比例低于目标时，两者不同。交叉验证中出现的 2e−3 ~ 6e−3 量级偏差即由此产生：CoC 是逐日受 `min()` 约束的非线性函数，其时间平均不等于"用时间平均比例算出的值"（`min` 与求均值不可交换）。""",
)

# ---------------------------------------------------------------- 修正 6：§10 追加产物
add(
    "修正6 §10 数据可用性追加 r* 产物与脚本",
    "- `water_balance_closure.csv`（水量闭合校验）",
    """- `water_balance_closure.csv`（水量闭合校验）

**§5.7–§5.8 新增产物**（均位于 `validation_artifacts/r2/`）：

| 文件 | 内容 | 行数 |
|---|---|---:|
| `rstar_scan_ha.csv` / `rstar_scan_co.csv` | 10 个 r × 40 个容量点的全量扫描 | 各 400 |
| `rstar_cawcc_by_r.csv` | 联合口径逐 r 的 CAWCC 与首失效 | 20 |
| `rstar_physical_cawcc_by_r.csv` | 纯物理口径逐 r 的 CAWCC 与首失效 | 20 |
| `rstar_boundaries_by_r.csv` / `rstar_physical_boundaries_by_r.csv` | 逐约束首失效容量随 r 的变化 | 200 / 160 |
| `rstar_confound_control.csv` | 同一容量点跨 r 的约束取值（混淆排除） | 40 |
| `rstar_backlash_decomposition.csv` | 反噬贡献分解 | 40 |
| `probe_rstar_mechanism.csv` | 解析式 vs 模型的逐点核验 | 40 |

**新增脚本**：
- `scripts/run_rstar_bottleneck_experiment.py`：r 维度全网格扫描（2 域 × 10 r × 40 容量 = 800 次模型运行）
- `scripts/run_rstar_physical_probe.py`：纯物理口径分离与混淆排除（复用扫描产物，不重跑模型）
- `scripts/probe_rstar_mechanism.py`：解析式逐点核验

**三处必须随产物声明的实现细节**：
1. **政策阈值必须与 r 同步**。首次运行时未同步，导致 r < 固定阈值（HA 0.65 / CO 0.40）时出现"政策自始失败、首失效恒为 50 MW"的伪结果——该次结果已废弃，不计入任何图表。
2. **浮点容差 1e−9 必需**。模型交付比例与目标 r 之间存在 1.11e−16 级舍入，严格 `>=` 比较会使整条阶梯在最底端误判。真实缺口量级为 1e−2 ~ 1e−1，比容差大 7 个数量级，不影响任何真实判断。
3. **`max_reuse_utilization` 沿用 §3.3 的剔除处理**（理由见该节）。本实验使用同一约束集，未新增或删除其他约束。""",
)

# ---------------------------------------------------------------- 修正 7：标题与摘要
add(
    "修正7 标题替换为 v2 版本",
    """> **标题（拟）**：**约束结构决定 AI 算力扩张的城市水系统瓶颈迁移：一个机制研究**
>
> **英文标题（拟）**：*Constraint structure, not facility scale, determines where AI data-centre expansion binds an urban water system: a mechanism study*""",
    """> **标题（拟）**：**再生水替代率的水质兼容阈值决定 AI 算力扩张的水系统瓶颈位置：一个机制研究**
>
> **英文标题（拟）**：*A water-quality compatibility threshold in reclaimed-water substitution governs where AI data-centre expansion binds an urban water system: a mechanism study*""",
)


def main() -> None:
    text = V1.read_text(encoding="utf-8")
    original_len = len(text)
    report = []
    for label, old, new in PATCHES:
        hit = old in text
        if hit:
            text = text.replace(old, new, 1)
        report.append({"label": label, "hit": hit, "old_len": len(old)})
        print(f"[{'OK  ' if hit else 'MISS'}] {label}")

    V2.write_text(text, encoding="utf-8")
    print("-" * 78)
    n_hit = sum(1 for r in report if r["hit"])
    print(f"命中 {n_hit}/{len(report)}；字数 {original_len:,} → {len(text):,}")
    print(f"-> {V2}")

    out = HERE / "_v2_patch_report.json"
    out.write_text(json.dumps(
        {"hits": n_hit, "total": len(report), "len_before": original_len,
         "len_after": len(text), "patches": report},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out}")
    sys.exit(0 if n_hit == len(report) else 1)


if __name__ == "__main__":
    main()
