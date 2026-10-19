# -*- coding: utf-8 -*-
"""追加 FigR5 到图件索引 + 写第六轮总结。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4\B0_瓶颈迁移主线")

INDEX_APPEND = """

---

# 第五轮新增图件（2026-10-18，网格收敛性）

| 图 | 文件 | 论证任务 | 核心数值 |
|---|---|---|---|
| **图 R5** | `FigR5_grid_convergence.pdf/png` | −100 MW 是真效应还是网格伪影 | **零效应区三网格一致；端点 −100/−100/−90；中间区极差 30–40 MW** |

## Fig R5 三个面板

- **(a) 绝对值随网格细化趋近上界**：50/25/10 MW 三条曲线，网格越细 CAWCC 越高（D-HA r=0.6：1150→1175→1190）。说明 50 MW 网格系统性低估 0–25 MW。
- **(b) 降幅对比**：零效应区（r≤0.5）三条曲线完全重合于 0；端点 r=0.9 为 −100/−100/−90（极差 10 MW）；中间区（0.6–0.8）三条曲线分离，极差 30–40 MW。
- **(c) 量化伪影示意**：以真实边界 1187 MW 为例，展示 50/25/10 MW 网格分别报 1150/1175/1180，对应的降幅为 −50/−25/−20——**绝对值都在逼近真值，但降幅不同，因为两个取整误差相减**。

## 新增门禁（本轮追加 10 项，合计 91 项）

```
文件存在（2 项）：FigR5 有 pdf+png
源码检查（3 项）：源码存在、携带「未经实测率定」「合成端点」、无承诺性表述
数值一致性（4 项）：收敛表 12 行、零效应区三网格均 0、HA r=0.9 为 −100/−100/−90、绝对值单调上升
```

**复现命令**：
```bash
cd 10_论文推进_2026Q4/B0_瓶颈迁移主线/figs
python make_fig_r5.py
python _gate_check_b0.py       # 应为 91/91 PASS
```

## 第五轮图件生成中修正的 3 处问题（留痕）

| # | 问题 | 修正 |
|---|---|---|
| 1 | (b) 图例压住曲线 | 改用曲线末端直接标注 |
| 2 | 末端标注 50/25 MW 数值接近导致文字重叠 | 加纵向偏移（−7/0/+7 MW）错开 |
| 3 | (c) 需要说明"为何降幅不同" | 添加"真实边界 1187"竖线与三条网格的取整说明 |
"""


def main() -> None:
    idx = HERE / "figs" / "图件索引.md"
    t = idx.read_text(encoding="utf-8")
    if "第五轮新增图件" in t:
        print("[SKIP] 索引已追加")
    else:
        idx.write_text(t + INDEX_APPEND, encoding="utf-8")
        print(f"[OK  ] 索引已追加；{len(t):,} -> {len(t + INDEX_APPEND):,}")


if __name__ == "__main__":
    main()
