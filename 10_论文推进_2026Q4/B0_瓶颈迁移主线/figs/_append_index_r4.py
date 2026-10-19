# -*- coding: utf-8 -*-
"""追加第四轮图件索引。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

INDEX = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4\B0_瓶颈迁移主线\figs\图件索引.md")

APPEND = """

---

# 第四轮新增图件（2026-10-18，零效应区与政策口径桥接）

| 图 | 文件 | 论证任务 | 核心数值 |
|---|---|---|---|
| **Fig R4** | `FigR4_zero_effect_and_policy_bridge.pdf/png` | 回答"政策区间内为何无效应"；澄清总量口径与配比口径 | **零效应区（r≤0.35 内 CAWCC 恒 1200/1450）；W/D 3.59–10.59、中位 5.33** |

## Fig R4 两个面板

- **(a) 政策区间内零效应**：纯物理 CAWCC 随 r 的变化，阴影标出现行政策区间（20%–35%）。该区间内两条曲线**完全水平**（D-HA 恒 1200、D-CO 恒 1450）；r\*=0.553 之后 D-HA 才开始下降（1200→1100）。**直观回答"为什么现行政策下机制不触发"。**
- **(b) 总量口径 → 配比口径**：横轴全市再生水利用率 `u`，纵轴园区替代率上界 `r_max = u·(W/D)`。三条线对应 W/D=10.3（500 MW）/5.3（1000 MW）/3.6（1500 MW）。标出 `r_max=1` 与 `r*=0.553`，并用箭头标出"政策区间内 1000 MW 案例已越过 r\*"。**解释"25% 政策目标"与"55% 园区替代率"不矛盾。**

## 新增图件的限定（已硬编码进图注）

| 图 | 限定 |
|---|---|
| Fig R4 | 合成端点、未经实测率定；W/D 是模型产物而非实测；不据此推断任何真实城市 |

## 新增门禁（本轮追加 11 项，合计 81 项）

```
文件存在（2 项）：FigR4 有 pdf+png
源码检查（3 项）：源码存在、携带「未经实测率定」「合成端点」、无承诺性表述
零效应区（2 项）：HA/CO 在 r≤0.35 时 CAWCC 各自唯一
政策桥接（3 项）：产物 6 行、W/D 中位 5.33、1000MW@u=20% 的 r_max>1
```

**复现命令**：
```bash
cd 10_论文推进_2026Q4/B0_瓶颈迁移主线/figs
python make_fig_r4.py
python _gate_check_b0.py       # 应为 81/81 PASS
```

## 第四轮图件生成中修正的 2 处问题（留痕）

| # | 问题 | 修正 |
|---|---|---|
| 1 | (a) "零效应区"文字压住数据点 | 移到图上方空白区（y=1435） |
| 2 | (b) `r*` 标注被曲线穿过 | 移到右侧空白区（x=0.505），并加"已越过 r\\*"箭头标注 |
"""

text = INDEX.read_text(encoding="utf-8")
if "第四轮新增图件" in text:
    print("[SKIP] 已追加")
else:
    INDEX.write_text(text + APPEND, encoding="utf-8")
    print(f"[OK  ] 已追加；{len(text):,} -> {len(text + APPEND):,} 字符")
