"""把 v3 里有产物却无正文的两块结果补进方案: 热浪(7.3) 与 S×G 矩阵(新增 7.5)。

表格由产物 CSV 自动生成，避免手抄出错。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DOC = Path(r"C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.md")
R2 = Path(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\aiuwm_src\validation_artifacts\r2")

DOMAIN_LABEL = {"ha": "D-HA", "co": "D-CO"}


def heatwave_tables() -> str:
    out = []
    for d in ("ha", "co"):
        df = pd.read_csv(R2 / d / "heatwave_stress.csv")
        out.append(f"**{DOMAIN_LABEL[d]}**\n")
        out.append("| 容量 (MW) | 全期取水 (ML) | 最大日取水 (ML/d) | 系统可靠性 | 给水处理峰值利用率 | 园区局部接入比 | 冷却缺水 (ML) |")
        out.append("|---|---|---|---|---|---|---|")
        for _, r in df.iterrows():
            out.append(
                f"| {r['capacity_mw']:.0f} | {r['total_withdrawal_ml']:.0f} "
                f"| {r['maximum_daily_withdrawal_ml']:.1f} "
                f"| {r['system_reliability_fraction']:.3f} "
                f"| {r['max_wtw_utilization']:.3f} "
                f"| {r['max_local_connection_ratio']:.3f} "
                f"| {r['unmet_cooling_water_ml']:.0f} |"
            )
        out.append("")
    return "\n".join(out)


def sg_tables() -> str:
    out = []
    for d in ("ha", "co"):
        df = pd.read_csv(R2 / d / "state_pressure_matrix.csv")
        label = DOMAIN_LABEL[d]
        for col, title, fmt in (
            ("system_reliability_fraction", "系统可靠性", "{:.3f}"),
            ("domestic_unmet_ml", "居民未满足量 (ML)", "{:.0f}"),
            ("max_source_abstraction_ratio", "水源取水占用率", "{:.3f}"),
        ):
            piv = df.pivot(index="state", columns="pressure", values=col)
            out.append(f"**{label} · {title}**\n")
            out.append("| 状态 | G0 | G1 | G2 | G3 |")
            out.append("|---|---|---|---|---|")
            for state, row in piv.iterrows():
                cells = " | ".join(fmt.format(v) for v in row.values)
                out.append(f"| {state} | {cells} |")
            out.append("")
    return "\n".join(out)


HEAT_ANCHOR = "### 7.4 分配政策（3 档）"

HEAT_INSERT = """#### 7.3.1 热浪结果【计算】（v4 补）

""" + heatwave_tables() + """读法：

- 热浪**没有**在 1500 MW 以内造成冷却缺水（`unmet_cooling_water_ml` 全为 0），也没有把系统可靠性压到 0.99 以下——说明短历时极端在本模型里**不足以单独触发供水失效**，它的作用是抬高瞬时占用率。
- 真正被推到边界的是两个输配指标：D-HA 在 1500 MW 时**园区局部接入比达 1.005（>1）**，给水处理峰值利用率 0.980（逼近规划裕度 0.95 上方）。D-CO 同容量为 0.965 / 0.968，**未越界**。
- 因此热浪情景的价值在于**区分两端点的输配裕度**，而不是制造短缺事件。这与第 9.5 节的瓶颈迁移链一致（两域的迁移顺序结构不同）。

"""

SG_ANCHOR = "## 8. 承载约束集"

SG_INSERT = """### 7.5 S×G 矩阵结果【计算】（v4 补，F 段产物）

基准容量 1000 MW。三张 4×4 表（完整表见 `state_pressure_matrix.csv`）：

""" + sg_tables() + """**三个可直接写进论文的观察**：

1. **最不利的城市状态是 S2（淡水受限—污水与再生水较强），不是 S1（给水受限）。** 两域在 S2 下系统可靠性降到 **0.601（HA）/ 0.651（CO）**、居民未满足量升到 **97 401 / 82 295 ML**，且水源取水占用率在所有压力下**恒为 1.000**（完全饱和）。S1 下可靠性仍有 0.79–0.92。这直接印证第 9.4 节的结论：**承载上限由水源取水决定**——把水源压到 0.65 倍（S2）比把给水压到 0.75 倍（S1）致命得多。
2. **S3（整体扩容—园区接入受限）在两域都是最优状态**：可靠性 1.000（CO 全域）、居民缺水 0（CO 全域；HA 仅 G3 有 12 797 ML）。因为它把所有水侧能力同时放大 1.15 倍，代价只落在园区接入上——而 1000 MW 尚未触及接入瓶颈。
3. **压力的主次与直觉相反：干旱（G2）比高温（G1）更致命。** G1（夏季 +4 ℃）对可靠性几乎无影响（HA 的 S0：1.000 → 1.000），而 G2（汛期入流 ×0.65 + 取水能力 ×0.85）立刻把取水占用率推到 1.000 并产生居民缺水。原因是本模型的蒸发量由排热量决定，气温只经 PUE 与湿冷份额间接传导（6.1 节），信号被稀释；而干旱直接削减水源侧可用量。**这意味着"AI 园区在高温城市"不是最坏组合，"AI 园区在缺水城市"才是。**

> 注意：G1 的弱响应与第 14 节 V9 的结论同源——气候信号必须按季节切片才看得见（夏季取水 +0.98 %/+1.00 %），全年或全状态平均会把它稀释掉。S×G 表用的是全年值，故 G1 列看起来"没有影响"，这不矛盾。

---

"""


def main() -> None:
    raw = DOC.read_bytes()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")

    for anchor, insert, note, marker in (
        (HEAT_ANCHOR, HEAT_INSERT, "7.3.1 热浪结果", "#### 7.3.1 热浪结果"),
        (SG_ANCHOR, SG_INSERT, "7.5 S×G 矩阵结果", "### 7.5 S×G 矩阵结果"),
    ):
        if marker in text:
            print(f"  [SKIP] {note} 已存在")
            continue
        if anchor not in text:
            print(f"  [MISS] {note} (anchor: {anchor[:40]})")
            continue
        text = text.replace(anchor, insert + anchor, 1)
        print(f"  [OK  ] {note}")

    DOC.write_bytes(text.replace("\n", eol).encode("utf-8"))
    print("写入完成")


if __name__ == "__main__":
    main()
