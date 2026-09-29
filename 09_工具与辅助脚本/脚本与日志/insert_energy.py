"""补 4.3 能源富集情景的结果，并修正 v3 只在 D-HA 上做该对照的设计缺陷。"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DOC = Path(r"C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.md")
R2 = Path(r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\aiuwm_src\validation_artifacts\r2")

OLD_TITLE = "### 4.3 能源富集补充情景（D-HA 上叠加）"
NEW_TITLE = "### 4.3 能源富集补充情景（v4 修订：两端点都做）"

OLD_PURPOSE = (
    "用途：把电力侧约束从瓶颈链里摘掉，单独观察水系统约束。"
    "这是**对照情景**，不是预测情景。"
)
NEW_PURPOSE = (
    "用途：把电力侧约束从瓶颈链里摘掉，单独观察水系统约束。"
    "这是**对照情景**，不是预测情景。\n\n"
    "> **v4 修订**：v3 只把它定义在 D-HA 上叠加，但 D-HA 的瓶颈在水侧"
    "（9.5 节迁移链里电力排第 3 位、1450 MW 才失效），在那里放宽电力约束"
    "**本就不会有反应**。真正电力先到顶的是 **D-CO**（迁移链第 1 位即接网容量 1500 MW）。"
    "**若只在 D-HA 上做这一对照，会得出「能源富集完全无效」的错误印象**——"
    "4.3.1 的实测证实了这一点。v4 把对照扩展到两端点。"
)

ANCHOR = "## 5. 城市水系统结构"


def energy_table() -> str:
    frames = []
    for d in ("ha", "co"):
        p = R2 / d / "energy_rich_comparison.csv"
        if p.exists():
            frames.append(pd.read_csv(p, encoding="utf-8-sig"))
    df = pd.concat(frames, ignore_index=True)
    out = [
        "| 域 | 情景 | 接网容量 (MW) | 电网间接水强度 (L/kWh) | CAWCC(年) | 年尺度限制约束 | CAWCC(日) | 日尺度限制约束 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for _, r in df.iterrows():
        bold = r["情景"] == "能源富集"

        def fmt(v):
            return "**" + str(v) + "**" if bold else str(v)

        year = "{:.0f} MW".format(r["CAWCC_年_MW"])
        day = "{:.0f} MW".format(r["CAWCC_日_MW"])
        out.append(
            "| {} | {} | {:.0f} | {:.2f} | {} | {} | {} | {} |".format(
                r["域"],
                fmt(r["情景"]),
                r["接网容量_MW"],
                r["电网间接水强度_L_per_kWh"],
                fmt(year),
                r["年尺度限制约束"],
                fmt(day),
                fmt(r["日尺度限制约束"]),
            )
        )
    return "\n".join(out)


INSERT = """#### 4.3.1 能源富集结果【计算】（v4 补）

""" + energy_table() + """

**四条结论**：

1. **D-HA 完全无反应**：年尺度与日尺度 CAWCC 均为 1150 MW，限制约束不变。这**正面印证**了第 9.4 节的核心结论——缺水端卡在水侧（水源取水、给水处理），放宽电力接网与降低电网间接水强度都无济于事。
2. **D-CO 日尺度 CAWCC 从 1450 → 1550 MW（+100），且限制约束由 `max_daily_average_grid_connection_ratio`（接网容量）迁移为 `max_wtw_utilization`（给水处理峰值利用率）**。这是「摘掉一个瓶颈，下一个瓶颈立刻接手」的直接观测，与 10.3 节 H3「边际有效性受制于下一个瓶颈的位置」是同一个机理在电力侧的重演。
3. **年尺度两端都不变**（1750 / 1150 MW），因为年尺度的首失效约束本来就是水源取水占用率（9.4 节），与电力无关。这再次说明**换尺度会换瓶颈**（H2）。
4. **同一干预在两个端点价值不同**：「扩接网 +50 %」在 D-CO 值 +100 MW，在 D-HA 值 0。这与 10.2 节结论 4（「哪个干预有效依赖端点瓶颈结构，不存在普适最优干预」）完全一致。

> **方法学提示（值得写进论文方法部分）**：这正是 1.3 节第 1 条「可失效性」纪律的价值所在。当一个对照情景在某端点上不产生任何差异时，**先要问是不是把它放错了端点**，而不是急着报告「该因素无影响」。v3 若照原计划只在 D-HA 上跑这一对照，会得到「能源富集情景完全无效」的结论，而真实情况是——**它在电力先到顶的端点上有效，在水先到顶的端点上无效**。

"""


def main() -> None:
    raw = DOC.read_bytes()
    eol = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8").replace("\r\n", "\n")

    if "#### 4.3.1 能源富集结果" in text:
        print("  [SKIP] 已存在")
        return

    for old, new, note in (
        (OLD_TITLE, NEW_TITLE, "4.3 标题"),
        (OLD_PURPOSE, NEW_PURPOSE, "4.3 用途段"),
    ):
        if old in text:
            text = text.replace(old, new, 1)
            print("  [OK  ] " + note)
        else:
            print("  [MISS] " + note)

    if ANCHOR in text:
        text = text.replace(ANCHOR, INSERT + ANCHOR, 1)
        print("  [OK  ] 4.3.1 能源富集结果")
    else:
        print("  [MISS] anchor")

    DOC.write_bytes(text.replace("\n", eol).encode("utf-8"))
    print("写入完成")


if __name__ == "__main__":
    main()
