# -*- coding: utf-8 -*-
"""把"质量状态路径未启用，且启用后 r* 机制减弱"这一重大发现写入论文。

【完整证据链（全部可复现）】
1. cawcc_r2 的 ha/co 项目**未设置 quality_state_enabled**，默认 False
   （full_engine.py:160），故 730 天全部为 DISABLED_LEGACY_VOLUME_ONLY。
2. 该路径下 CoC = min(CoC_d, L/C_mix(目标配比)) 的解析值，
   与动态盐分无关；实测模型 CoC 与解析值一致到 1e-15。
3. 显式启用 quality_state_enabled=True 后（1100 MW，D-HA）：
     r=0.5: CoC 5.0000 → 5.0000（不变）
     r=0.7: CoC 4.3222 → 4.9991，年补水 31923.9 → 30772.2
     r=0.8: CoC 3.9568 → 4.9986，年补水 32764.8 → 30773.3
     r=0.9: CoC 3.6484 → 4.9981，年补水 33655.1 → 30774.3
   **即：动态路径下 CoC 几乎恒为设计值 5.0，补水不随 r 增长，阈值型反噬基本消失。**
4. 成因（逐日诊断）：园区 24 ML 储池在第 1 天即从 12 充到 24 ML 并保持满库，
   盐分被暂存于储池；排污浓度 quality_blowdown_TDS 从 1998 降到约 194 mg/L
   （接近补水浓度），故环路 CoC 收敛到设计值。
   **这是储池缓冲的物理后果，不是实现缺陷。**

【为什么必须写入】
论文 §5.7 的全部结论（r*、阈值型响应、反噬与容量无关）**都建立在
legacy volume-only 路径之上**。若这一路径未被声明，读者会误以为结论
在完整质量动态下也成立——而实测显示在高 r 端 CoC 差异达 1.35（3.65 vs 5.00）。

这**不否定**论文结论，但它给出了明确的适用条件：
  **机制在"冷却储池未饱和"或"储池容量可忽略"的条件下成立。**
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 母稿：§5.7.8 之后追加 5.7.9 ----------
MS_ANCHOR = "## 5.8 结果 5：瓶颈位置是政策的内生函数（纯物理口径）"
MS_NEW = """### 5.7.9 一项必须声明的模型路径设定：本文结论建立在 legacy volume-only 路径之上

§5.7.8 披露了"CoC 按目标配比计算、而实际交付不足"这一张力。追查其根源时发现了一个更基本的事实，**必须在此声明**。

**事实一：本文所用的两个端点项目未启用动态盐分追踪。** `examples/cawcc_r2/{ha,co}/project.json` 均未设置 `quality_state_enabled`，其默认值为 `False`（`full_engine.py:160`）。因此全部 730 日的诊断字段均为 `quality_state_status = DISABLED_LEGACY_VOLUME_ONLY`、`quality_solver_status = not_applicable`。在该路径下，CoC 由 `min(CoC_design, L/C_mix(r))` 直接给出，**不做逐日盐分质量守恒**。

**事实二：显式启用动态路径后，本文的阈值型反噬显著减弱。** 在 D-HA、1100 MW 下对比两条路径：

| r | CoC（legacy） | CoC（动态） | 年补水 ML（legacy） | 年补水 ML（动态） |
|---:|---:|---:|---:|---:|
| 0.5 | 5.0000 | 5.0000 | 30,770.8 | 30,770.8 |
| 0.7 | 4.3222 | **4.9991** | 31,923.9 | **30,772.2** |
| 0.8 | 3.9568 | **4.9986** | 32,764.8 | **30,773.3** |
| 0.9 | 3.6484 | **4.9981** | 33,655.1 | **30,774.3** |

**即：动态路径下 CoC 几乎恒为设计值 5.0，年补水几乎不随 r 增长（变幅 < 0.02%），阈值型反噬基本消失。**

**事实三：成因是储池缓冲，不是实现缺陷。** 逐日诊断显示，园区 24 ML 储池在第 1 天即由初值 12 ML 充至 24 ML 并保持满库；排污 TDS 浓度由 1998 mg/L 迅速降至约 **194 mg/L**（接近补水浓度），盐分被暂存于储池。这是储池缓冲的**物理后果**，符合模型设定（300 ML 储池、约 7–9 天产水量）。

**三项后果**：

1. **本文全部 r* 结论的适用条件是"冷却储池未饱和或储池容量可忽略"。** 若储池容量显著、且处于满库稳态，水质反噬会被缓冲大幅削弱。这是本文机制的**边界条件**，此前完全未声明。
2. **本文报告的 −100 MW 与 +6.48% 增幅是 legacy 路径下的值**，在动态路径下这些量级会显著缩小。因此它们应读作"**在无动态盐分缓冲的极限情形下的效应**"。
3. **`r*` 的解析式本身不受影响**：它描述的是"水质上限开始约束 CoC 的门槛"，与路径无关。但**越过门槛之后的实际补水增量**依赖路径。

> **为什么选择 legacy 路径作为主情景**：两点理由。其一，它与本文的解析推导（§5.7.2）使用同一 CoC 表达式，故解析式与模型能对到 1e-15；若改用动态路径，解析式只剩定性和近似价值。其二，legacy 路径给出的是**上界**：它假设混合水质的全部盐负荷立即作用于环路，而储池缓冲只会削弱、不会增强反噬。因此本文的机制结论方向稳健，量级为上界。

""" + MS_ANCHOR

# ---------- 英文 ----------
EN_ANCHOR = ("The threshold itself is unaffected: $r^{*}=0.5532$ lies where delivery is complete.")
EN_NEW = ("The threshold itself is unaffected: $r^{*}=0.5532$ lies where delivery is complete. "
          "Tracing that residual one level further exposes a model-path setting that must be "
          "declared. Neither endpoint project sets `quality_state_enabled`, whose default is false, "
          "so all 730 days run the legacy volume-only path in which CoC follows the closed form "
          "directly with no day-by-day salt balance. Enabling the dynamic path changes the picture: "
          "at 1100 MW the CoC stays near its design value of 5.0 across the whole range (4.9991, "
          "4.9986 and 4.9981 at $r$ = 0.7, 0.8 and 0.9, against 4.3222, 3.9568 and 3.6484 under the "
          "legacy path), and annual make-up becomes almost invariant at about 30,772 ML instead of "
          "rising to 33,655 ML. The cause is storage buffering rather than an implementation fault: "
          "the 24 ML campus pond fills from its 12 ML initial state on day one and stays full, while "
          "blowdown TDS falls from 1998 to about 194 mg L$^{-1}$, so salts accumulate in the pond "
          "rather than in the loop. Two consequences follow for how this paper should be read. The "
          "r\\*\\ results hold under the condition that cooling storage is unsaturated or negligible "
          "— a boundary condition not previously stated. And the −100 MW and +6.48% figures are "
          "legacy-path values that should be read as the effect in the limit of no dynamic salt "
          "buffering, which is an upper bound, since buffering can only weaken the penalty.")

# ---------- SI ----------
SI_ANCHOR = "## S6 Methodological detail compressed from the main text"
SI_NEW = """### S5.10 The legacy volume-only path, and what changes under dynamic salt tracking

Tracing the delivered-fraction residual of S5.9 one level further exposes a setting that the paper
must declare.

Neither `examples/cawcc_r2/{ha,co}/project.json` sets `quality_state_enabled`, whose default is
false (`full_engine.py:160`). All 730 days therefore report
`quality_state_status = DISABLED_LEGACY_VOLUME_ONLY` and `quality_solver_status = not_applicable`.
On that path CoC is taken directly from $\\min(\\mathrm{CoC}_d, L/C_{\\mathrm{mix}}(r))$ with no
day-by-day solute balance, which is why model CoC matches the closed form to 1e-15.

Setting `quality_state_enabled = true` changes the result materially. At the water-scarce endpoint
and 1100 MW:

| $r$ | CoC, legacy | CoC, dynamic | Annual make-up ML, legacy | Annual make-up ML, dynamic |
|---:|---:|---:|---:|---:|
| 0.5 | 5.0000 | 5.0000 | 30,770.8 | 30,770.8 |
| 0.7 | 4.3222 | **4.9991** | 31,923.9 | **30,772.2** |
| 0.8 | 3.9568 | **4.9986** | 32,764.8 | **30,773.3** |
| 0.9 | 3.6484 | **4.9981** | 33,655.1 | **30,774.3** |

Under dynamic tracking CoC stays essentially at its design value and annual make-up varies by less
than 0.02% across the whole range, so the threshold-typed penalty largely disappears.

The cause is buffering, not a defect. Day-by-day diagnostics show the 24 ML campus pond filling from
its 12 ML initial state on day one and remaining full, while blowdown TDS falls from 1998 to roughly
194 mg L⁻¹, close to the make-up concentration. Salt accumulates in the pond rather than in the
loop. This is the physical consequence of the storage specification (300 ML at the reuse facility,
about 7–9 days of production), not an implementation error.

Three consequences. First, the paper's r\\* results hold under the condition that cooling storage is
unsaturated or negligible — a boundary condition not previously stated. Second, the −100 MW and
+6.48% figures are legacy-path values and should be read as the effect in the limit of no dynamic
salt buffering. Third, the closed form for $r^{*}$ is itself unaffected, since it describes where the
quality ceiling begins to bind, which is path-independent; what depends on the path is the magnitude
of the response beyond that ceiling.

The legacy path is retained as the main scenario for two reasons. It shares the CoC expression used
in the analytic derivation of §5.7.2, which is what allows the closed form to agree with the model
to 1e-15; under dynamic tracking the closed form retains only qualitative value. And it yields an
upper bound, because assuming the full salt load acts on the loop immediately can only overstate,
never understate, the penalty. The mechanism's direction is therefore robust while its magnitude is
an upper bound.

**Evidence:** `_quality_state_sensitivity.json`, `_quality_state_sensitivity.txt`,
`_quality_storage_diag.txt`, `_test_quality_state.py`, `_diag_quality_storage.py`.

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
if MS_ANCHOR in t and "5.7.9" not in t:
    MS.write_text(t.replace(MS_ANCHOR, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿 §5.7.9")
    n += 1
else:
    print("母稿未匹配")

t = EN.read_text(encoding="utf-8")
if EN_ANCHOR in t and "storage buffering" not in t:
    EN.write_text(t.replace(EN_ANCHOR, EN_NEW, 1), encoding="utf-8")
    print("OK 英文")
    n += 1
else:
    print("英文未匹配")

t = SI.read_text(encoding="utf-8")
if SI_ANCHOR in t and "S5.10" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S5.10")
    n += 1
else:
    print("SI 未匹配或已存在")
print(f"完成 {n}/3")
