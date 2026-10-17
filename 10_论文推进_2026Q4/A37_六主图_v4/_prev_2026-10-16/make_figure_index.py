# -*- coding: utf-8 -*-
"""生成 figure_index.md: 图号 -> 科学问题 -> 数据源 -> 生成脚本 -> 输出 -> SHA256。

同时写入：
  - 每个数据源的 SHA256 (可追溯: 数值来自哪一版文件)
  - 每张图的 PDF/PNG SHA256 (可校验: 交付物是否被改动)
  - 核验过的关键数值与门禁口径

用法: PYTHONIOENCODING=utf-8 python make_figure_index.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha256(p: Path, n: int = 16) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


# 图号 -> (科学问题, 数据源(相对 ROOT), 脚本, 输出 stem)
FIGDEF = [
    ("Fig. 1",
     "研究边界如何划定? 三种反事实 (B0/B1/B2) 与三分账是什么?",
     ["A13_可靠性机制/supply_state_regimes.csv",
      "A26_语义统一/CHI_SEMANTICS.md"],
     "make_fig1.py", "Fig1_boundary_counterfactuals"),
    ("Fig. 2",
     "掺混如何改变 CoC? 哪个物种绑定 CoC?",
     ["A33_WP4_组成重构/wp4_results.csv",
      "A4_水化学参数域/T6_coc_limits.csv",
      "A4_水化学参数域/T6_water_chemistry_samples.csv",
      "A27_引用限值/A27_引用限值报告.md"],
     "make_fig2.py", "Fig2_water_quality_coc"),
    ("Fig. 3",
     "dS_pot 的符号结构是什么? q>0 组是否有害?",
     ["A13_可靠性机制/supply_state_regimes.csv",
      "A33_WP4_组成重构/wp4_results.csv",
      "A13_可靠性机制/COLUMN_NAMES_CORRECTED.md"],
     "make_fig3.py", "Fig3_city_results_signs"),
    ("Fig. 4",
     "仅用干预前可观测量能否预测 dS_pot 符号?",
     ["A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json",
      "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json",
      "A31_WP2_假设冻结/wp2_e3_predictions.csv",
      "A31_WP2_假设冻结/wp2_e3b_features.csv"],
     "make_fig4.py", "Fig4_independent_prediction"),
    ("Fig. 5",
     "哪个参数主导 dS_pot? 交互多强? 极端事件会翻转吗?",
     ["A34_WP5_敏感性与极端事件/wp5_morris.csv",
      "A34_WP5_敏感性与极端事件/wp5_sobol.csv",
      "A34_WP5_敏感性与极端事件/wp5_extreme_cases.csv",
      "A34_WP5_敏感性与极端事件/wp5_extreme_summary.json"],
     "make_fig5.py", "Fig5_sensitivity_extremes"),
    ("Fig. 6",
     "真实设施中 committed 分支占比是多少?",
     ["A30_WP0取证/a24b_partial_id_summary.json",
      "A30_WP0取证/a24b_capacity_table.csv"],
     "make_fig6.py", "Fig6_external_anchor_partial_id"),
]

# 独立核验过的关键数值 (figure-builder 复算, 2026-10-16)
VERIFIED = [
    ("严格符号 dS_pot 计数", "643 负 / 134 正 / 36 零", "n_eff=813",
     "复现; 必须用 dS==0.0 精确判零。容差 1e-9 得 631/102 (旧口径, n=733)"),
    ("q 分组", "290 / 288 / 235", "n_eff=813",
     "复现; q=(M0-M1)/M1, 该列需自行计算, 源文件无 q 列"),
    ("q>0 组有害计数", "0 / 290", "n_eff=813", "复现; 无正例 ⇒ 不具鉴别力"),
    ("恒等式残差", "2.546585164964e-11", "n_eff=813",
     "复现 (相对 2.93e-16); 须用 max(0,inc_B2-inc_B1)-(M0-M1)-x_ai_B1 重建"),
    ("WP4 城市级", "47/47 全部有益; q 分组 23/24", "n_eff=47",
     "复现; 双门禁后 60 → 47, 剔除 13"),
    ("E3 仅化学", "0.6712 vs 基线 0.8608", "n_eff=733", "来自 summary.json"),
    ("E3b 联合 C4", "0.9059 全样本; 折外 0.9009 vs 0.8594", "n_eff=733",
     "复现 tp/fp/tn/fn = 602/40/62/29 (须在剔除 80 近零行的子集上)"),
    ("Sobol ΣS1", "0.223 (ha) / 0.218 (co)", "Saltelli ha|IEUA",
     "复现 ≈0.22"),
    ("极端事件翻转", "0 / 8", "n_eff=64",
     "复现 (4 热浪 + 4 干旱, 0 翻转)"),
    ("碱度保守界比", "2.500 (IEUA); 49.3 (LADWP)", "baseline 限值档",
     "复现; 静态余量比, 非动态临界值"),
    ("碱度动态翻转临界", "≈ 2.615×", "41 点 × 2 域 × 2 水样",
     "来自 WP5 报告表; 无观测支撑"),
    ("committed 占比界", "[0%, 100%] 不可识别", "n=10826 (仅产能)",
     "来自 a24b_partial_id_summary.json (WITHDRAWN_AS_UNIDENTIFIED)"),
]


def main() -> None:
    lines: list[str] = []
    A = lines.append
    A("# A37 六主图 v4 — 图件索引 (figure index)")
    A("")
    A(f"> 生成时间: {datetime.now():%Y-%m-%d %H:%M:%S}  |  "
      "生成脚本: `make_figure_index.py`  |  复现: `make_all_figures.py`")
    A("")
    A("本轮重绘动因: A27 把限值从**占位档**换成**引用档** (GB/T 50050-2017), "
      "使有害情景由 285 降至 102、可靠情景由 1094 变为 813, 并暴露出 CoC 触下限的退化情景门禁。")
    A("按项目纪律「**改了限值/门禁 ⇒ 必须重跑所有下游产物**」, 旧图 "
      "(`09_图定稿/`, `A16_英文稿/figures/`) 建于此前的旧口径, **已过时**, 全部保留仅作审计留痕。")
    A("")
    A("---")
    A("")
    A("## 1. 图件总表")
    A("")
    A("| 图号 | 科学问题 | 数据源 | 生成脚本 | 输出文件 | SHA256 (16) |")
    A("|---|---|---|---|---|---|")
    fig_hashes: dict[str, dict] = {}
    for num, q, srcs, script, stem in FIGDEF:
        outs = []
        hashes = {}
        for ext in ("pdf", "png"):
            f = HERE / f"{stem}.{ext}"
            if f.exists():
                h = sha256(f)
                hashes[f"{stem}.{ext}"] = h
                outs.append(f"`{stem}.{ext}`")
            else:
                outs.append(f"`{stem}.{ext}` ⚠️缺失")
        fig_hashes[num] = hashes
        src_html = "<br>".join(f"`{s}`" for s in srcs)
        hh = "<br>".join(f"{k.split('.')[-1]}: `{v}`" for k, v in hashes.items())
        A(f"| **{num}** | {q} | {src_html} | `{script}` | {'<br>'.join(outs)} | {hh} |")
    A("")
    A("> 图注文件: 每张图配 `figN_caption.md` (英文, 含标题句 + 数据/方法 + n + 限制)。")
    A("")

    A("---")
    A("")
    A("## 2. 数据源 SHA256 (可追溯)")
    A("")
    A("数值来自哪一版文件, 由下表锁定。若上游文件变更, 哈希不匹配即说明图需重跑。")
    A("")
    A("| 数据源 | 行数 | SHA256 (16) |")
    A("|---|---:|---|")
    allsrc = sorted({s for _, _, srcs, _, _ in FIGDEF for s in srcs})
    for s in allsrc:
        p = ROOT / s
        if p.exists():
            try:
                n = sum(1 for _ in open(p, "rb"))
                A(f"| `{s}` | {n} | `{sha256(p)}` |")
            except Exception:
                A(f"| `{s}` | — | `{sha256(p)}` |")
        else:
            tr = ROOT.parent / s
            if tr.exists():
                n = sum(1 for _ in open(tr, "rb"))
                A(f"| `{s}` | {n} | `{sha256(tr)}` |")
            else:
                A(f"| `{s}` | — | ⚠️ 未找到 |")
    A("")

    A("---")
    A("")
    A("## 3. 独立核验过的关键数值")
    A("")
    A("以下数值由 figure-builder 从**权威产物独立复算** (探针脚本 `_probe_verify.py` / "
      "`_probe_signs.py` / `_probe_q.py`), 非从文档转抄。")
    A("")
    A("| 量 | 值 | 口径 | 核验说明 |")
    A("|---|---|---|---|")
    for name, val, ns, note in VERIFIED:
        A(f"| {name} | **{val}** | {ns} | {note} |")
    A("")

    A("---")
    A("")
    A("## 4. 统一口径 (全册一致)")
    A("")
    A("| 项 | 约定 |")
    A("|---|---|")
    A("| 主估计量 | `dS_pot = C - F = max(0, inc_B2 - inc_B1) - [(M0 - M1) + x_ai]` |")
    A("| 符号语义 | `dS_pot > 0` = 城市净取水**上升 (有害)**; `< 0` = **下降 (有益)** |")
    A("| 双门禁 | `status == \"converged_unique\"` **且** `~coc_floor_degenerate` |")
    A("| 零值约定 | **严格符号**: `dS_pot == 0.0` 单列, **不设容差带**。"
      "若用 `|dS|<1e-9` 会得到旧的 631/102 且实际 n=733 |")
    A("| 样本量 | 每图必标 `n_eff`; 每图必标数据源文件 |")
    A("| 列名注意 | `x_ai_B1_ml` / `x_ai_B2_ml` **列名互换**, 见 "
      "`A13_可靠性机制/COLUMN_NAMES_CORRECTED.md` |")
    A("| 残差口径 | 用**相对**容差; 2.55e−11 (绝对) / 2.93e−16 (相对) |")
    A("")

    A("---")
    A("")
    A("## 5. 已撤回主张的隔离 (图中不得出现)")
    A("")
    A("| 原主张 | 处置 | 图中处理 |")
    A("|---|---|---|")
    A("| \"95–93% 真实设施已处于已承诺状态, empirically dominant\" | **撤回** "
      "(不可识别, 界 = [0%,100%]) | Fig.6 以部分识别呈现, 不出现任何点估计 |")
    A("| \"更干净 ⇒ CoC 更高 ⇒ 更省补水 ⇒ 更有利\" | **撤回** (x_ai 主导, corr = −0.93) | "
      "全册不出现; Fig.2 用限值/浓度比讲机理 |")
    A("| 判据吻合率 1.0000 作为预测/发现 | **降级**为记账一致性检验 | "
      "Fig.3 限制句显式声明 q>0 不具鉴别力 |")
    A("| H3 \"有力证实\" | **降级**为鉴别力不足 | Fig.3 用 \"sufficient condition\" |")
    A("| R² = 0.557 / 基线 −0.050 | **更正**为 0.806 / −0.073 | 不在六图中引用旧值 |")
    A("| 头条计数 631/102 标 n=813 | **改用** 643/134/36 并披露容差口径 | Fig.3 直接标注 |")
    A("")

    A("---")
    A("")
    A("## 6. 复现与校验")
    A("")
    A("```bash")
    A('cd "10_论文推进_2026Q4/A37_六主图_v4"')
    A("PYTHONIOENCODING=utf-8 python make_all_figures.py   # 重跑全部六图")
    A("PYTHONIOENCODING=utf-8 python make_figure_index.py  # 重算本索引与哈希")
    A("```")
    A("")
    A("规格: PDF + PNG 双份, 400 dpi, `pdf.fonttype=42` (TrueType 嵌入)。"
      "配色与 rcParams 复用上级 `figstyle.py` (只读), 在其上叠加 Nature Water 风格。")
    A("")
    A("### 与上一版图件的关系")
    A("")
    A("`09_图定稿/` 与 `A16_英文稿/figures/` **未被改动**, 保留作审计留痕。"
      "本目录 `A37_六主图_v4/` 是唯一有效的六张主图。")
    A("")

    out = HERE / "figure_index.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"written: {out}  ({out.stat().st_size} bytes)")
    # 同时落一份 JSON, 便于程序化校验
    js = HERE / "figure_index.json"
    js.write_text(json.dumps({
        "generated": datetime.now().isoformat(timespec="seconds"),
        "figures": {n: {"question": q, "sources": s, "script": sc, "hashes": fig_hashes[n]}
                    for n, q, s, sc, _ in FIGDEF},
        "verified_numbers": [{"quantity": a, "value": b, "scope": c, "note": d}
                             for a, b, c, d in VERIFIED],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"written: {js}")


if __name__ == "__main__":
    main()
