# -*- coding: utf-8 -*-
"""把 UWMP p.62 / p.86 的水质一手证据写入母稿、英文稿、SI。

【为什么重要】
论文 §5.9 此前只用了 UWMP 的**水量**数据。但 UWMP 的**水质**叙述直接支撑了
本文机制的三项前提，此前从未被引用：

  (1) 该市冷却塔确实使用多水源混合补水  → 机制前提（C_mix = r·C_r + (1−r)·C_p）
  (2) 官方以 salinity（含盐量）刻画该水质问题 → 本文判据变量正是含盐量
  (3) 官方认为再生水对冷却塔的水质比地下水更稳定 → 支持"约束在水质侧"的问题设定

同时必须如实写明：UWMP **全文无 TDS/电导率/氯化物数值**，
故这些证据只能支撑机制前提，**不能锚定 C_p 或 C_r 的具体值**。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ================= 母稿：新增 5.9.2c =================
MS_ANCHOR = "### 5.9.3 由份额反推园区配比"
MS_NEW = """#### 5.9.2c 机制前提的一手支撑：UWMP 对冷却塔补水水质的官方叙述

本文机制假设园区冷却补水是**多水源混合**，且其约束在**含盐量**一侧。此前这一前提只能由模型设定支撑，无城市层面的文档依据。查 `Santa Clara 2025 Urban Water Management Plan` 发现其**第 62 页**（市府法定文件，2026-06）直接讨论了冷却塔补水水质：

> "In areas of the City served by groundwater, industrial customers will find the quality of treated recycled water to be **more consistent than groundwater for cooling towers**. Those cooling towers that receive groundwater could also receive a **blend of multiple water sources** based on system demand (e.g., groundwater blended with imported surface water) with slight variations in water quality, whereas those that receive recycled water would receive one consistent water source."

> "The enhanced blend of water will help industrial users reduce operating costs, and it can be used on a wider variety of landscapes, due to a **much lower level of salinity**."

**这三句为本文提供三项一手支撑**：

| # | 官方陈述 | 支撑本文哪一前提 |
|---|---|---|
| 1 | 冷却塔补水为 "blend of multiple water sources"，水质随配比变化 | `C_mix(r) = r·C_r + (1−r)·C_p` 的建模对象 |
| 2 | 以 "salinity"（含盐量）刻画该水质问题 | 本文判据的自变量正是含盐量（TDS/氯化物） |
| 3 | 再生水对冷却塔的水质比地下水**更稳定** | "约束在水质侧而非水量侧"的问题设定 |

另在**第 86 页**，UWMP 就地下水水质写道：

> "In contrast to other areas adjacent to San Francisco Bay where saltwater intrusion has been an issue, **total dissolved solids (TDS) is not a concern for the City**."

这与 GAMA 全州地下水 TDS 中位 420 mg/L 并不矛盾——420 是**全州**中位，而该市明确不属于受 TDS 困扰的地区。**该陈述支持把 `C_p = 180 mg/L` 视为合理甚至偏保守的取值**（若实际更淡，`r*` 会更高，"未越过"的结论更稳）。

> ⚠️ **必须同时声明的限制**：UWMP **全文未给出任何 TDS、电导率、氯化物或硬度的数值**（这些词在 282 页中仅出现于缩写表、上述定性陈述与法规条文附录）。因此本小节的三句只能**支撑机制前提与参数方向的合理性**，**不能用来锚定 `C_p` 或 `C_r` 的具体数值**。§9.7 第 44 条关于"四参数无实测锚点"的限制仍然成立。

""" + MS_ANCHOR

# ================= 英文：§3.4 末补一段 =================
EN_ANCHOR = "Those two shares are a transcribed government statement, not a first-hand measurement (SI S7.2)."
EN_ADD = (" The mechanism's premise — that campus cooling make-up is a blend whose constraint sits on "
          "the salinity side — also has first-hand documentary support that we had not previously "
          "used: the city's statutory water plan states that cooling towers receiving groundwater "
          "\"could also receive a blend of multiple water sources ... with slight variations in "
          "water quality\", describes recycled water as advantageous for cooling towers because of "
          "\"a much lower level of salinity\", and records that TDS \"is not a concern for the "
          "City\". These statements support the premise and the direction of the parameter choice, "
          "but the plan contains no numerical TDS, conductivity, chloride or hardness values, so "
          "they cannot anchor $C_p$ or $C_r$ (SI S7.12).")

# ================= SI：新增 S7.12 =================
SI_ANCHOR = "## S8 Data-reliability warnings for reviewers"
SI_NEW = """### S7.12 First-hand documentary support for the mechanism's premise

The main text's mechanism assumes that campus cooling make-up is a blend of sources and that the
binding property is salinity. That premise had rested on model construction alone; the city's
statutory water plan supplies documentary support that we had not previously drawn on.

From the 2025 Urban Water Management Plan, page 62:

> "In areas of the City served by groundwater, industrial customers will find the quality of
> treated recycled water to be more consistent than groundwater for cooling towers. Those cooling
> towers that receive groundwater could also receive a blend of multiple water sources based on
> system demand (e.g., groundwater blended with imported surface water) with slight variations in
> water quality, whereas those that receive recycled water would receive one consistent water
> source."

> "The enhanced blend of water will help industrial users reduce operating costs, and it can be
> used on a wider variety of landscapes, due to a much lower level of salinity."

And from page 86:

> "In contrast to other areas adjacent to San Francisco Bay where saltwater intrusion has been an
> issue, total dissolved solids (TDS) is not a concern for the City."

These support three things respectively: that cooling towers in this city do receive blended
make-up water whose quality varies with the mix, which is precisely the object of
$C_{\\mathrm{mix}}(r)=rC_r+(1-r)C_p$; that the utility frames the relevant water-quality attribute
as salinity, which is the variable our criterion uses; and that the city's potable supply is not
TDS-stressed, which makes the assumed $C_p=180$ mg L⁻¹ plausible or even conservative rather than
arbitrary. The last point is consistent with the statewide groundwater median of 420 mg L⁻¹: that
figure is a state-wide median, and the plan states this city is not among the TDS-affected areas.

**A limit that must be stated in the same breath.** The plan contains no numerical TDS,
conductivity, chloride or hardness values at all — across 282 pages these terms appear only in the
abbreviation list, in the qualitative passages quoted above, and in a regulatory appendix. The
quotations therefore support the premise and the direction of the parameter choice; they cannot
anchor $C_p$ or $C_r$. Item 44 of the limitation register, on the four unanchored threshold
parameters, is unaffected.

**Evidence:** `_verify_uwmp_quality.py` (11/11), reading `2025 Urban Water Management Plan_Final.pdf`
pp. 62 and 86 directly.

---

""" + SI_ANCHOR

n = 0
t = MS.read_text(encoding="utf-8")
if MS_ANCHOR in t and "5.9.2c" not in t:
    MS.write_text(t.replace(MS_ANCHOR, MS_NEW, 1), encoding="utf-8")
    print("OK 母稿 §5.9.2c")
    n += 1
else:
    print("母稿锚点问题")

t = EN.read_text(encoding="utf-8")
if EN_ANCHOR in t and "mechanism's premise" not in t:
    EN.write_text(t.replace(EN_ANCHOR, EN_ANCHOR + EN_ADD, 1), encoding="utf-8")
    print("OK 英文 §3.4")
    n += 1
else:
    print("英文锚点问题")

t = SI.read_text(encoding="utf-8")
if SI_ANCHOR in t and "S7.12" not in t:
    SI.write_text(t.replace(SI_ANCHOR, SI_NEW, 1), encoding="utf-8")
    print("OK SI S7.12")
    n += 1
else:
    print("SI 锚点问题")

print(f"完成 {n}/3")

import re
print("英文词数:", len(re.sub(r"\$[^$]*\$", " MATH ", EN.read_text(encoding='utf-8')).split()))
