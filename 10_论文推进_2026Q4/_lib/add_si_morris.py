"""在 SI 中补入 Morris 敏感性分析的方法披露 (2026-10-17).

【为什么】
主稿 §12a 的表格同时给出 Morris μ* 与 Sobol S_T，并在图注中共同展示。
但 SI 的 S16 只有 NE-1/NE-2/NE-4，**没有交代 Morris 的方法**——
其参数（32 条轨迹 × 8 水平、固定网格步长）在论文中完全没有出现。
这是"方法论披露缺口"：读者无法复现 Morris 部分。

【依据】
A34_WP5_敏感性与极端事件/wp5_sensitivity_summary.json:
  morris.trajectories = 32
  morris.levels = 8
  morris.normalized_delta = 0.5714285714285714  (= 4/7)
  morris.engine_impl_replaced_because = 引擎实现会在边界处放大效应且不检测 actual_delta==0
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SI = Path(__file__).resolve().parent.parent / "A16_英文稿/supplementary_information.md"
t = SI.read_text(encoding="utf-8")

ANCHOR = "### S16.3 Sobol indices with bootstrap intervals (NE-4)"
BLOCK = """### S16.2b Morris screening: method, and why the engine's own routine was not used

The Morris $\mu^*$ column in the main text comes from a **trajectory-based elementary-effects
design of 32 trajectories over an 8-level grid** ($\Delta = 4/7$ of each parameter's range,
fixed seed), run through the same evaluator as the rest of this paper
(`A34_WP5_敏感性与极端事件/wp5_morris_sobol.py`;
`wp5_sensitivity_summary.json → morris`).

We did **not** use the engine's own `aiuwm.sensitivity.morris_sensitivity`. Its implementation
steps from the base point by clipping to `min(high, base+Δ)` or `max(low, base−Δ)`; when the
step lands on a range boundary the *realised* step can be far smaller than $\Delta$, yet the
effect is still divided by $\Delta/(high-low)$, which systematically **inflates** the reported
effect. It also does not detect `actual_delta == 0`. Our implementation uses a fixed grid step
and normalises by the realised step, and we record which of the two is used so the two are never
pooled. This is a **methodological substitution, not a defect in the results**: the ranking it
produces is what we report, and the substitution is stated here rather than left implicit.

"""
if "S16.2b" in t:
    print("已存在，跳过")
else:
    assert ANCHOR in t, "锚点缺失"
    t = t.replace(ANCHOR, BLOCK + ANCHOR, 1)
    SI.write_text(t, encoding="utf-8")
    print("已插入 S16.2b（Morris 方法披露）")
