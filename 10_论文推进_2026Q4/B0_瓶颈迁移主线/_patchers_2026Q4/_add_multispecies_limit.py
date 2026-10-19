# -*- coding: utf-8 -*-
"""在 §9.6 追加第 29 条限制：r* 当前只用了 TDS，多物种版本取 min。

同时更新 §5.7.2，说明该简化的含义。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_add_multispecies_limit.py
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

OLD = """28. **`r*` 判据的适用条件：应代入实际交付的再生水比例，而非政策目标值。** 当再生水池受限使实际比例低于目标时，两者不同。交叉验证中出现的 2e−3 ~ 6e−3 量级偏差即由此产生：CoC 是逐日受 `min()` 约束的非线性函数，其时间平均不等于"用时间平均比例算出的值"（`min` 与求均值不可交换）。"""

NEW = """28. **`r*` 判据的适用条件：应代入实际交付的再生水比例，而非政策目标值。** 当再生水池受限使实际比例低于目标时，两者不同。交叉验证中出现的 2e−3 ~ 6e−3 量级偏差即由此产生：CoC 是逐日受 `min()` 约束的非线性函数，其时间平均不等于"用时间平均比例算出的值"（`min` 与求均值不可交换）。

29. **`r*` 的多物种取紧核验：TDS 确为最紧约束（已核验，非假定）。** 模型的限值表含 **TDS（2200 mg/L）** 与 **氯化物（500 mg/L）** 两个物种，两者都有完整的水源水质参数。逐物种计算：

    ```
    TDS:      r*_TDS      = (2200/5 − 180)/(650 − 180) = **0.5532**
    chloride: r*_chloride = (500/5  − 35 )/(130 − 35 ) = **0.6842**
    ```

    取紧：`r* = min(0.5532, 0.6842) = 0.5532`。**本文报出的值即为两物种的最小者**，故数值无需修正。

    **但两点必须声明**：
    - 模型追踪 5 个物种（TDS、氯化物、硬度、碱度、硅），**其余 3 个物种在当前项目文件中只有限值或只有部分源水质，无法计算其 `r*`**。若它们的临界值更低，真实 `r*` 会更低、反噬更早开始。**这是本文数值的一个未闭合边界。**
    - 通用判据形式应为 `r* = min over s of [(L_s/CoC_design − C_p,s)/(C_r,s − C_p,s)]`。本文给出了两物种的完整计算，其余 3 个物种留待水质参数补齐后完成。"""

INTRO_OLD = """代入两端点参数（`L = 2200 mg/L`、`CoC_design = 5.0`、`C_p = 180 mg/L`、`C_r = 650 mg/L`）：

```
r* = (2200/5 − 180) / (650 − 180) = (440 − 180)/470 = **0.5532**
```"""

INTRO_NEW = """代入两端点参数（`L = 2200 mg/L`、`CoC_design = 5.0`、`C_p = 180 mg/L`、`C_r = 650 mg/L`）：

```
r* = (2200/5 − 180) / (650 − 180) = (440 − 180)/470 = **0.5532**
```

> **多物种取紧（已核验）**：模型限值表还含氯化物（500 mg/L，淡水 35、再生水 130），其临界值为
> `r*_chloride = (500/5 − 35)/(130 − 35) = 0.6842`。取两物种的紧者：
> `r* = min(0.5532, 0.6842) = 0.5532`——**TDS 确为最紧约束，故本文数值无需修正**。
> 其余 3 个物种（硬度、碱度、硅）因源水质参数不完整无法计算，见 §9.6 第 29 条。"""


def main() -> None:
    text = V2.read_text(encoding="utf-8")
    ok = True

    if OLD in text:
        text = text.replace(OLD, NEW, 1)
        print("[OK  ] §9.6 追加第 29 条（多物种简化披露）")
    else:
        print("[MISS] 未找到 §9.6 第 28 条")
        ok = False

    if INTRO_OLD in text:
        text = text.replace(INTRO_OLD, INTRO_NEW, 1)
        print("[OK  ] §5.7.2 追加多物种简化说明")
    else:
        print("[MISS] 未找到 §5.7.2 推导段")
        ok = False

    V2.write_text(text, encoding="utf-8")
    print(f"字数 {len(text):,}；行数 {text.count(chr(10)) + 1}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
