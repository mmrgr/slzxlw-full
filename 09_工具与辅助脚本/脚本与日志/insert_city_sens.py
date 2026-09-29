"""在方案第 12 节后插入 12.4 城市侧参数敏感性（v4 新增）。

对应 nature-skills 审查的 M1（阻塞项）：头号结论建立在城市侧【设定】参数上，
但 v3 的敏感性分析只覆盖 AI 侧，结论对设定值的稳健性未知。
表格由产物自动生成。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DOC = Path(r"C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.md")
R2 = Path(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\aiuwm_src\validation_artifacts\r2")

CN = {
    "components.DM1.leakage_fraction": "配水漏损率",
    "local_areas.LA1.demand_profiles.0.base_value": "居民用水定额",
    "components.RES1.abstraction_capacity_ml_day": "水源取水能力",
    "components.WTW1.daily_capacity_ml": "给水处理能力",
    "components.WWTW1.daily_capacity_ml": "污水处理能力",
    "components.CENTRAL_REUSE.treatment_capacity_ml_day": "再生水处理能力",
    "components.RES1.capacity_ml": "水库库容",
}


def morris_table() -> str:
    frames = {}
    for d in ("ha", "co"):
        df = pd.read_csv(R2 / d / "city_morris.csv")
        for metric in ("max_source_abstraction_ratio", "max_wtw_utilization"):
            sub = df[df["metric"] == metric][["parameter", "mu_star"]]
            frames[(d, metric)] = dict(zip(sub["parameter"], sub["mu_star"]))

    params = list(CN.keys())
    out = [
        "| 城市侧参数 | HA 年尺度约束 `mu*` | HA 日尺度约束 `mu*` | CO 年尺度约束 `mu*` | CO 日尺度约束 `mu*` |",
        "|---|---|---|---|---|",
    ]
    rows = []
    for p in params:
        vals = [
            frames.get(("ha", "max_source_abstraction_ratio"), {}).get(p, 0.0),
            frames.get(("ha", "max_wtw_utilization"), {}).get(p, 0.0),
            frames.get(("co", "max_source_abstraction_ratio"), {}).get(p, 0.0),
            frames.get(("co", "max_wtw_utilization"), {}).get(p, 0.0),
        ]
        rows.append((max(vals), CN[p], vals))
    for _, name, vals in sorted(rows, reverse=True):
        cells = " | ".join(f"{v:.3g}" for v in vals)
        out.append(f"| **{name}** | {cells} |")
    return "\n".join(out)


def sobol_table() -> str:
    frames = {}
    for d in ("ha", "co"):
        df = pd.read_csv(R2 / d / "city_sobol.csv")
        frames[d] = dict(zip(df["parameter"], zip(df["S1"], df["ST"])))
    out = [
        "| 城市侧参数 | HA `S1` | HA `ST` | CO `S1` | CO `ST` |",
        "|---|---|---|---|---|",
    ]
    rows = []
    for p, name in CN.items():
        ha = frames.get("ha", {}).get(p, (0.0, 0.0))
        co = frames.get("co", {}).get(p, (0.0, 0.0))
        rows.append((max(ha[1], co[1]), name, ha, co))
    for _, name, ha, co in sorted(rows, reverse=True):
        out.append(f"| {name} | {ha[0]:.3f} | {ha[1]:.3f} | {co[0]:.3f} | {co[1]:.3f} |")
    return "\n".join(out)


ANCHOR = "---\n\n## 13. 执行方案"

INSERT = """#### 12.4 城市侧参数敏感性【计算】（v4 新增）

**为什么补这一块。** 第 9.4 节的头号结论——"承载容量上限由水源取水与给水处理决定"——建立在一组城市侧【设定】参数之上（库容、取水/给水/污水/再生水能力、漏损率、用水定额，见第 15 节）。v3 的敏感性分析只覆盖 AI 侧 6 个参数，**城市侧从未做过检验**，因此无法回答"这个结论是不是设定值的产物"。这是 v3 最实质的漏洞。

**设计。** 7 个城市侧参数按**各域自身基线**扰动（能力/需求/库容 ±25 %、漏损率 ±50 %），观测两个指标——`max_source_abstraction_ratio`（年尺度头号约束）与 `max_wtw_utilization`（日尺度头号约束）。这两个指标正是决定 CAWCC 的限制约束，因此比"AI 取水量"更直接对应承载容量。Morris 24 轨迹 + Sobol N = 64。

**Morris 结果**（`mu*`，按两域四列的最大值降序）：

""" + morris_table() + """

**三条读法**：

1. **配水漏损率是城市侧唯一有实质影响的参数**，`mu*` 比第二名高 **2–3 个数量级**（HA 0.635 vs 0.0019；CO 0.725 vs 0.0021），方向为正——漏损越大，取水与给水约束越紧。
2. **设施能力（取水/给水/污水/再生水）与库容在 ±25 % 变动下几乎不改变头号约束的取值**：`mu*` 均 ≤ 1.7e−3，库容**恒为 0**（水库在本扫描区间内不构成约束，与 3.3 节 #2 修复后的设定一致）。
3. 因此 v3 的疑问有明确答案：**头号结论对设施能力类设定值是稳健的**——这些值即使浮动四分之一，承载约束的取值与身份都不改变。

**与干预分析的独立互证。** 第 10.2 节的干预扫描是一条完全独立的路径（直接改能力值并重新扫描 CAWCC），给出"扩给水 +10 %/+20 % 增益为 **0**、降漏损 −30 % 增益 **+200 MW**"；城市侧 Morris 是另一条路径（改同一批参数但只观测约束取值、不重扫 CAWCC），给出"给水能力 `mu*` ≈ 5e−5、漏损 `mu*` 最大"。**两条路径指向同一结论**，这不是巧合而是同一机理的两次观测：城市需水量由漏损与定额决定，设施能力只在真正逼近硬截断时才起作用，而 1000 MW 下两端点的给水/取水尚未进入被能力截断的区间（这也解释了 10.3 节里再生水"处理能力"杠杆为何恒为 0）。

**Sobol 未收敛，且与 Morris 矛盾**（`max_source_abstraction_ratio`）：

""" + sobol_table() + """

`S1` 出现 **1.278（>1）** 与 **−0.413（<0）**，数学上越界，说明 **N = 64 仍未收敛**。Sobol 把首位给了水源取水能力（`ST` 0.693），与 Morris 的漏损首位**相反**。此时**不能**把两者当作互相印证——按第 16 节 #5 的既定处理，Sobol 在城市侧同样只可作排序参考；而当前排序与 Morris 冲突，故**本轮不以城市侧 Sobol 结果下任何定量结论**。R3 需 N ≥ 256 或改用 Jansen 估计器。

> **这一处修正值得写进方法部分**：v3 的 12.2 节写"Morris 与 Sobol 在'基准 PUE、排热系数、CoC 为前三'上一致"，那是**AI 侧**的情形。城市侧两者**不一致**，说明"Morris 与 Sobol 互为交叉验证"这一说法不能无条件推广——当 `S1` 越界时，分歧本身就是不收敛的证据，而不是两个方法各有侧重。

**结论（可直接写进论文）**：城市侧参数中，只有**配水漏损率**实质影响承载约束；在 ±25 % 范围内扩建设施能力（取水、给水、污水、再生水）对承载容量**几乎不起作用**。但漏损率本身是【文献】CJJ 92 中位值 0.12 的设定——**若目标城市实际漏损率显著偏离（0.08 或 0.20），承载容量会明显变化**。因此 R3 必须替换为实测漏损率；在此之前，第 9.4 节的绝对数值只可作**相对比较**用，不宜当作规划依据。

"""


def main() -> None:
    raw = DOC.read_bytes()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")

    if "#### 12.4 城市侧参数敏感性" in text:
        print("  [SKIP] 已存在")
        return
    if ANCHOR not in text:
        print(f"  [MISS] anchor: {ANCHOR!r}")
        return

    text = text.replace(ANCHOR, INSERT + ANCHOR, 1)
    DOC.write_bytes(text.replace("\n", eol).encode("utf-8"))
    print("  [OK  ] 12.4 城市侧参数敏感性")


if __name__ == "__main__":
    main()
