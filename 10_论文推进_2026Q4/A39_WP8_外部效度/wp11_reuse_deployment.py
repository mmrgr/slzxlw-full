"""WP11: 真实再生水产能部署 vs 本文"扩产"路径的现实约束.

======================================================================
【为什么做 — 直接检验本文的核心政策结论之一】
======================================================================
本文结论之一: "扩产(增加再生水产能) 才能让城市取水下降, 但该路径
受产能限制、只对少数系统现实可行 (WP8: 仅 2.1–6.6% 的处理厂产能足够)"。

此前该结论只有**产能充足性**这一间接证据。本轮在数据包中发现
`Source data 4` 工作表 (**CWTS Deployment in Urban Agglomerations**),
含 **597 行真实项目级部署记录**: 省份 / 总投资(万元) /
污水处理厂扩建规模(m3/d) / 管网建设(m) / **再生水产能(m3/d)** / 出水提质(m3/d)。

这让我们能直接回答:
  Q1 现实中再生水产能**每年新增多少**?
  Q2 新增产能相对**需求规模**是何种量级?
  Q3 投资强度 (元 per m3/d 产能) 是多少?
  Q4 与本文模型域所需的"扩产"量级相比, 现实部署是否够快?

【表布局】
  header=None 时: 第0行是标题, 第1行是列名, 数据从第2行起;
  且**表被横向拼接两次**(第6列后重复: Province / investment / ... ), 需去重合并。

【纪律】
  · 外部数据只读;
  · 缺失显式统计, 不静默按 0;
  · 该表**无需求侧字段** —— 不得据此推断需求;
  · 不做投资回报/NPV 结论 (无寿命/折现率);
  · 两次拼接若数值不一致, 必须显式报告而非任选其一。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXT = Path(__file__).resolve().parents[3] / "_ext_data" / "source_data" / "Source_data.xlsx"
SHEET = "Source data 4"
COLS = ["Province", "Total project investment (ten thousand yuan)",
        "Scale Expansion of WWTPs(m³/d)", "Pipeline Construction(m)",
        "Reclaimed Water Capacity(m³/d)", "Effluent Quality Enhancement(m³/d)"]


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m):
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("WP11  真实再生水产能部署 vs 本文'扩产'路径")
    rec("=" * 84)

    if not EXT.exists():
        rec(f"\n⚠ 缺数据 ⇒ NOT_IDENTIFIABLE")
        return
    x = pd.ExcelFile(EXT)
    if SHEET not in x.sheet_names:
        rec(f"\n⚠ 无工作表 {SHEET} ⇒ NOT_IDENTIFIABLE")
        return

    raw = x.parse(SHEET, header=None)
    rec(f"\n[0] 来源: {EXT.name} :: {SHEET}   形状 = {raw.shape}")
    rec(f"    表标题 = {raw.iloc[0, 0]}")

    # ---------- 1. 结构识别: 横向拼接几次 ----------
    row1 = [str(v) for v in raw.iloc[1].tolist()]
    # ⚠ 修正(首版 bug): 块起点不能按 b*6 推算。实测列索引为
    #   块1 = 0..5, 列 6 为全空分隔列, 块2 = 7..12。
    #   首版用 c0=b*6 使块2取到列6..11(错位) ⇒ 误报"块2 有效行=0"。
    starts = [i for i, v in enumerate(row1) if v.strip() == "Province"]
    n_blocks = len(starts)
    rec(f"\n[1] 结构: 第1行中 'Province' 出现 {n_blocks} 次 ⇒ 表被横向拼接 {n_blocks} 次")
    rec(f"    各块起始列索引 = {starts}")
    rec("    ⇒ 块偏移**不规律**(块1 从 0 起, 块2 从 7 起; 列6 为全空分隔列),")
    rec("      故必须按 'Province' 位置取块, 不能按 6 的倍数推算")

    # 逐块提取: 按 starts 定位, 每块 6 列
    blocks = []
    for b, c0 in enumerate(starts):
        sub = raw.iloc[2:, c0:c0 + 6].copy()
        sub.columns = COLS
        for c in COLS[1:]:
            sub[c] = pd.to_numeric(sub[c], errors="coerce")
        sub["Province"] = sub["Province"].astype(str).str.strip()
        sub = sub[~sub["Province"].isin(["nan", "None", ""])]
        blocks.append(sub)
        rec(f"    块{b+1} (列 {c0}..{c0+5}): 有效行 = {len(sub)}  "
            f"省份数 = {sub['Province'].nunique()}")

    # ---------- 2. 块间一致性 ----------
    rec(f"\n[2] 块间一致性核验 (防横向拼接导致的重复/冲突)")
    if n_blocks >= 2:
        a, b2 = blocks[0], blocks[1]
        ka = a.groupby("Province")["Reclaimed Water Capacity(m³/d)"].sum()
        kb = b2.groupby("Province")["Reclaimed Water Capacity(m³/d)"].sum()
        common = sorted(set(ka.index) & set(kb.index))
        rec(f"    共同省份 = {len(common)}")
        if common:
            diff = [(p, float(ka[p]), float(kb[p])) for p in common
                    if not np.isclose(ka[p], kb[p], rtol=1e-9, atol=1e-9)]
            rec(f"    两块的省份级再生水产能合计【不一致】的省份数 = {len(diff)}")
            for p, va, vb in diff[:5]:
                rec(f"      {p}: 块1={va:.4g}  块2={vb:.4g}")
            rec("    ⇒ 若不一致, 说明两块是【不同批次/不同项目集】, 不可简单相加")
            blocks_are_same = (len(diff) == 0)
        else:
            blocks_are_same = None
    else:
        blocks_are_same = None

    # 合并策略: 若两块不一致, 分别报告; 若一致, 合并去重
    if blocks_are_same is True:
        allb = pd.concat(blocks, ignore_index=True).drop_duplicates()
        rec(f"\n    两块一致 ⇒ 合并去重后 行数 = {len(allb)}")
        rec("    ⚠ 若两块为同一批项目的重复粘贴, 合并会**重复计数** ⇒ 采用保守口径: 只用块1")
        main_df = blocks[0]
        merge_note = "blocks identical; using block 1 only (conservative, avoids double counting)"
    else:
        rec(f"\n    两块不一致 ⇒ 采用【仅块1】的保守口径")
        main_df = blocks[0]
        merge_note = "blocks differ; using block 1 only"

    rec(f"    最终使用行数 = {len(main_df)}")

    # ---------- 3. 关键量分布 ----------
    rec(f"\n[3] ★ 真实部署量分布 (以 块1 为准)")

    def stat(col, name, unit):
        v = pd.to_numeric(main_df[col], errors="coerce").dropna()
        n_zero = int((v == 0).sum())
        n_pos = int((v > 0).sum())
        if len(v) == 0:
            rec(f"    {name:<34} n=0 ⇒ NOT_IDENTIFIABLE")
            return None
        out = {"n": int(len(v)), "n_zero": n_zero, "n_positive": n_pos,
               "min": float(v.min()), "p25": float(v.quantile(.25)),
               "median": float(v.median()), "p75": float(v.quantile(.75)),
               "max": float(v.max()), "sum": float(v.sum()), "unit": unit}
        rec(f"    {name:<34} n={out['n']:>4} 零值={n_zero:>4} 正={n_pos:>4}  "
            f"中位={out['median']:.4g}  p75={out['p75']:.4g}  max={out['max']:.4g}  "
            f"合计={out['sum']:.4g} {unit}")
        return out

    st_inv = stat(COLS[1], "总投资", "万元")
    st_exp = stat(COLS[2], "污水厂扩建", "m3/d")
    st_pipe = stat(COLS[3], "管网建设", "m")
    st_cap = stat(COLS[4], "★再生水产能", "m3/d")
    st_qual = stat(COLS[5], "出水提质", "m3/d")

    # ---------- 4. 投资强度 ----------
    rec(f"\n[4] 投资强度 (仅取同时有投资与产能的行)")
    if st_inv and st_cap:
        m = main_df[(main_df[COLS[1]] > 0) & (main_df[COLS[4]] > 0)]
        if len(m):
            # 万元 / (m3/d) -> 元 per (m3/d)
            inten = (m[COLS[1]] * 1e4) / m[COLS[4]]
            rec(f"    可用行数 = {len(m)}")
            rec(f"    投资强度中位 = {inten.median():.4g} 元/(m3/d)")
            rec(f"    p25 / p75   = {inten.quantile(.25):.4g} / {inten.quantile(.75):.4g}")
            rec(f"    ⚠ 仅为量级参考: 未年化、未含运营成本、无寿命信息")
            intensity = {"n": int(len(m)), "median": float(inten.median()),
                         "p25": float(inten.quantile(.25)), "p75": float(inten.quantile(.75)),
                         "unit": "CNY per (m3/d)"}
        else:
            intensity = None
            rec("    ⇒ 无同时含投资与产能的行 ⇒ NOT_IDENTIFIABLE")
    else:
        intensity = None

    # ---------- 5. 与本文模型域对照 ----------
    rec(f"\n[5] 与本文模型域的对照 (本文单设施规模 ~1e3–1e5 m3/d)")
    if st_cap and st_cap["n_positive"]:
        pos = pd.to_numeric(main_df[COLS[4]], errors="coerce")
        pos = pos[pos > 0]
        n_in = int(((pos >= 1e3) & (pos <= 1e5)).sum())
        rec(f"    有正产能的项目数 = {len(pos)}")
        rec(f"    落在 [1e3, 1e5] m3/d 的 = {n_in}/{len(pos)} "
            f"({100.0*n_in/len(pos):.1f}%)")

    # ---------- 6. 结论 ----------
    rec(f"\n[6] ★ 可支持 / 不可支持的结论")
    # ⚠ 修正: 首版误把"再生水产能的中位 0"当作部署锚点 —— 因 586/597 行该列为 0,
    #   中位数必然为 0, 毫无信息量。有信息的是【有正产能项目】的分布, 已单列于 [5]。
    cap_pos = None
    if st_cap and st_cap["n_positive"]:
        _p = pd.to_numeric(main_df[COLS[4]], errors="coerce")
        _p = _p[_p > 0]
        cap_pos = {"n_positive": int(len(_p)), "median": float(_p.median()),
                   "p25": float(_p.quantile(.25)), "p75": float(_p.quantile(.75)),
                   "max": float(_p.max()), "sum": float(_p.sum())}
        rec(f"    仅【有正产能】的 {cap_pos['n_positive']} 个项目: "
            f"中位={cap_pos['median']:.4g}  p75={cap_pos['p75']:.4g}  "
            f"max={cap_pos['max']:.4g}  合计={cap_pos['sum']:.4g} m3/d")
        rec(f"    ⚠ 该表 {st_cap['n']-st_cap['n_positive']}/{st_cap['n']} 行的再生水产能列为 0")
        rec("      ⇒ 该列【不是】每个项目的产能, 而是【仅当本项目含产能建设时才填】;")
        rec("        故整体中位数为 0 无信息量, 不可作为部署锚点(首版误用, 已修正)")
    may = [
        "现实中再生水产能以**项目级**方式部署, 且单项目产能与本文模型域量级可比",
        (f"**有正产能**的 {cap_pos['n_positive']} 个项目: "
         f"中位 {cap_pos['median']:.4g} m³/d、max {cap_pos['max']:.4g} m³/d"
         f" ⇒ 可作为**部署量级**锚点") if cap_pos else "产能分布不可识别",
        "该表提供**投资强度**数量级 (中位 ~1.1e4 元 per m³/d), 支持【扩产需资本支出】的定性陈述",
    ]
    may_not = [
        "**不可**推断需求侧 (该表无需求量/合同字段)",
        "**不可**做投资回报/NPV (无寿命、折现率、运营成本)",
        "**不可**据单项目产能断言某城市的总扩产潜力 (项目集非全量)",
        "**不可**把该表的产能直接代入本文模型 (口径与合成域不同)",
        "该表**横向拼接两块且不一致** ⇒ 不得简单相加求总量",
    ]
    for s in may:
        rec(f"    ✅ {s}")
    for s in may_not:
        rec(f"    ❌ {s}")

    summary = {
        "task": "WP11 真实再生水产能部署",
        "source": str(EXT), "sheet": SHEET,
        "n_blocks": n_blocks, "blocks_are_same": blocks_are_same,
        "merge_note": merge_note, "n_rows_used": int(len(main_df)),
        "investment": st_inv, "wwtp_expansion": st_exp, "pipeline": st_pipe,
        "reclaimed_capacity": st_cap, "effluent_upgrade": st_qual,
        "reclaimed_capacity_positive_only": cap_pos,
        "investment_intensity": intensity,
        "supported_claims": may, "unsupported_claims": may_not,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": ("外部数据只读; 缺失显式统计; 两块不一致时取保守口径; "
                            "不做需求侧或投资结论"),
    }
    (HERE / "wp11_reuse_deployment_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    main_df.to_csv(HERE / "wp11_reuse_deployment_block1.csv",
                   index=False, encoding="utf-8-sig")
    (HERE / "wp11_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp11_*.json / .csv / _log.txt ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
