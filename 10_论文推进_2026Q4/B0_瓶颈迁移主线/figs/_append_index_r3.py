# -*- coding: utf-8 -*-
"""把 FigR3 与第三轮增量追加到图件索引。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
INDEX = HERE / "图件索引.md"

APPEND = """

---

# 第三轮新增图件（2026-10-18，r* 分类学）

| 图 | 文件 | 论证任务 | 核心数值 |
|---|---|---|---|
| **Fig R3** | `FigR3_rstar_regime_and_sensitivity.pdf/png` | `r*` 是**分类判据**而非常数 | **四情形 I/II/III/IV；三种情形的 CoC 轨迹定性不同；四参数弹性** |

## Fig R3 三个面板

- **(a) 四情形分类相图**：横轴 `C* = L/CoC_design`，纵轴 `r*`。三条边界线（`C* = C_p`、`C* = C_r`、`r* = 0/1`）把参数空间分成四个区。标出本文两端点位置（星号，`r*=0.553`）。320 个参数组合的分类结果作为散点呈现（情形 I 81 / II 156 / III 63 / IV 20）。
- **(b) 三情形的 CoC 轨迹**：三个不同 `CoC_design`（15 / 5 / 2.5）下，CoC 归一化后随 r 的变化。情形 I 从 r=0 即下降；情形 II 在 r≤r\* 平坦后下降；情形 III 全程恒定。
- **(c) 单参数敏感性**：四个参数各自扫描时 `r*` 的响应（对数横轴）。标出标称点（`r*=0.553`）。展示 `L` 与 `CoC_design` 的斜率最陡、`C_p` 最平。

## 新增图件的限定（已硬编码进图注）

| 图 | 限定 |
|---|---|
| Fig R3 | 合成端点、未经实测率定；四情形分类边界由参数决定，不声称任何真实城市归类；情形 I 的 `CoC_design=15` 属逻辑验证构造，工程上不现实 |

## 新增门禁（本轮追加 13 项，合计 70 项）

```
文件存在（2 项）：FigR3 有 pdf+png
源码检查（3 项）：源码存在、携带「未经实测率定」「合成端点」、无承诺性表述
分类一致性（6 项）：四情形齐全、网格 320、情形 I 无平坦点、II 有平坦区、III 全平坦
重合规律（2 项）：情形 I≡II 在 r=0.8 重合、情形 III 不重合
```

**复现命令**：
```bash
cd 10_论文推进_2026Q4/B0_瓶颈迁移主线/figs
python make_fig_r3.py
python _gate_check_b0.py       # 应为 70/70 PASS
```

## 第三轮图件生成中修正的 2 处问题（留痕）

| # | 问题 | 修正 |
|---|---|---|
| 1 | (a) 图例压住散点、(c) 图例与曲线交叉 | 两处图例均移到图外下方（`bbox_to_anchor=(0.5, -0.22)`） |
| 2 | 首版误写"三情形 r=0.8 取水一致" | 实测只有情形 I≡II，情形 III 不同；已修正文档、图注与门禁判据 |
"""


def main() -> None:
    text = INDEX.read_text(encoding="utf-8")
    if "第三轮新增图件" in text:
        print("[SKIP] 已追加")
        return
    INDEX.write_text(text + APPEND, encoding="utf-8")
    print(f"[OK  ] 已追加；{len(text):,} -> {len(text + APPEND):,} 字符")


if __name__ == "__main__":
    main()
