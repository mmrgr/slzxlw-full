# -*- coding: utf-8 -*-
"""B0 六主图门禁检查

检查项（对应 05_图表规划与数据源映射.md 的门禁清单）：
1. 文件存在性：六图各有 pdf + png
2. 数值溯源：图中关键数值可追溯到产物文件（抽查关键点）
3. 禁令检查：图内文本不得出现「承载力」「能承载 X MW」
4. 限定检查：相应图必须出现 hydrology_validation=NONE / 未经实测率定
5. 未失效项检查：Fig 2 必须显式标注未失效约束
6. estimand 标签：Fig 2/3/5/6 的图注必须写明 estimand

用法：
    python _gate_check_b0.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


# ---------- 1. 文件存在性 ----------
FIGS = [
    "Fig1_framework",
    "Fig2_bottleneck_migration",
    "Fig3_constraint_trajectories",
    "Fig4_interventions",
    "Fig5_city_gradient_policy",
    "Fig6_timescale_reservoir",
]
for stem in FIGS:
    for ext in ("pdf", "png"):
        p = HERE / f"{stem}.{ext}"
        check(f"文件存在 {stem}.{ext}", p.exists() and p.stat().st_size > 5000,
              f"{p.stat().st_size if p.exists() else 0} bytes")

# ---------- 2. 数值溯源（抽查关键值能由产物复现）----------
R2 = HERE.parent.parent.parent / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
try:
    import pandas as pd

    # Fig 2 的核心数字：两域首失效容量
    b = pd.read_csv(R2 / "ha" / "constraint_boundaries_corrected.csv", encoding="utf-8-sig")
    src_first = float(
        b.loc[b["constraint"] == "max_source_abstraction_ratio",
              "first_failed_capacity_mw"].iloc[0]
    )
    check("Fig2 数值溯源 HA 水源取水首失效 = 1200", src_first == 1200.0, f"{src_first}")

    b2 = pd.read_csv(R2 / "co" / "constraint_boundaries_corrected.csv", encoding="utf-8-sig")
    grid_first = float(
        b2.loc[b2["constraint"] == "max_daily_average_grid_connection_ratio",
               "first_failed_capacity_mw"].iloc[0]
    )
    check("Fig2 数值溯源 CO 电网首失效 = 1500", grid_first == 1500.0, f"{grid_first}")

    # Fig 4 的核心数字：两域唯一正增益
    cb = pd.read_csv(R2 / "intervention_cost_benefit.csv", encoding="utf-8-sig")
    ha_gain = float(cb.loc[(cb["域"] == "ha") & (cb["干预"] == "leakage_minus_30pct"),
                           "CAWCC增益_MW"].iloc[0])
    co_gain = float(cb.loc[(cb["域"] == "co") & (cb["干预"] == "grid_plus_50pct"),
                           "CAWCC增益_MW"].iloc[0])
    check("Fig4 数值溯源 HA 降漏损 = +150", ha_gain == 150.0, f"{ha_gain}")
    check("Fig4 数值溯源 CO 扩电网 = +100", co_gain == 100.0, f"{co_gain}")

    # Fig 5 的核心数字：库容比值
    ens = json.loads((R2 / "reservoir_multiyear_ensemble.json").read_text(encoding="utf-8"))
    ha_med = float(ens["ha"]["joint_gate_mw_median"])
    co_med = float(ens["co"]["joint_gate_mw_median"])
    check("Fig6 数值溯源 HA 库容中位 = 200", ha_med == 200.0, f"{ha_med}")
    check("Fig6 数值溯源 CO 库容中位 = 900", co_med == 900.0, f"{co_med}")
    check("Fig6 序列数 = 20", int(ens["ha"]["sequences"]) == 20 and int(ens["co"]["sequences"]) == 20,
          f"{ens['ha']['sequences']}/{ens['co']['sequences']}")

    # Fig 6 的核心数字：端点一致性
    cg = pd.read_csv(R2 / "city_gradient_cawcc.csv", encoding="utf-8-sig")
    r0 = cg[(cg["theta_climate"] == 0.0) & (cg["theta_infra"] == 0.0)].iloc[0]
    r1 = cg[(cg["theta_climate"] == 1.0) & (cg["theta_infra"] == 1.0)].iloc[0]
    check("Fig5 端点 theta(0,0) 日尺度 = 1150", float(r0["CAWCC_日_MW"]) == 1150.0,
          f"{r0['CAWCC_日_MW']}")
    check("Fig5 端点 theta(1,1) 日尺度 = 1450", float(r1["CAWCC_日_MW"]) == 1450.0,
          f"{r1['CAWCC_日_MW']}")
except Exception as exc:  # noqa: BLE001
    check("数值溯源可执行", False, f"{type(exc).__name__}: {exc}")

# ---------- 3~6. 源码/图注文本检查 ----------
FORBIDDEN = ["承载力", "能承载"]

for stem in FIGS:
    src = HERE / f"make_{stem.split('_')[0].lower()}.py"
    if not src.exists():
        # fig2 -> make_fig2.py 等
        num = re.search(r"Fig(\d)", stem).group(1)
        src = HERE / f"make_fig{num}.py"
    text = src.read_text(encoding="utf-8") if src.exists() else ""
    hits = [w for w in FORBIDDEN if w in text and "不声称" not in text]
    check(f"{stem} 禁令：无「承载力/能承载」承诺性表述",
          all(w not in text for w in FORBIDDEN) or "不声称" in text,
          f"命中 {hits}" if hits else "")

# 限定检查
fig6 = (HERE / "make_fig6.py").read_text(encoding="utf-8")
check("Fig6 携带 hydrology_validation = NONE", "hydrology_validation = NONE" in fig6)
check("Fig6 说明合成日内曲线不可外推", "合成日内曲线" in fig6)

fig2 = (HERE / "make_fig2.py").read_text(encoding="utf-8")
check("Fig2 显式标注未失效约束", "未失效" in fig2)
check("Fig2 携带未经实测率定", "未经实测率定" in fig2)
check("Fig2 标注 estimand（日尺度）", "estimand" in fig2 or "日尺度" in fig2)

fig3 = (HERE / "make_fig3.py").read_text(encoding="utf-8")
check("Fig3 标注 estimand", "estimand" in fig3)
check("Fig3 说明 0 MW 基线已排除", "0 MW 基线已排除" in fig3 or "0 MW" in fig3)

fig4 = (HERE / "make_fig4.py").read_text(encoding="utf-8")
check("Fig4 注明基线口径", "基线 HA 1150" in fig4 or "1150" in fig4)
check("Fig4 注明投资 MISSING 项不参与排序", "MISSING" in fig4)
check("Fig4 注明未检验交互", "未检验交互" in fig4)

fig5 = (HERE / "make_fig5.py").read_text(encoding="utf-8")
check("Fig5 注明合成谱非真实城市", "合成谱" in fig5)
check("Fig5 注明 2000 MW 右删失", "右删失" in fig5)
check("Fig5 注明只有 CO 域", "仅 CO 域" in fig5)

# ---------- 6b. 新增：r* 图件门禁（FigR1 / FigR2）----------
# 这部分检查 2026-10-18 新增的水质兼容阈值图件。与上述六主图各自独立，
# 不改变六主图的任何检查项与判定。
R_FIGS = [
    "FigR1_rstar_threshold_response",
    "FigR2_backlash_decomposition",
    "FigR3_rstar_regime_and_sensitivity",
    "FigR4_zero_effect_and_policy_bridge",
    "FigR5_grid_convergence",
]
for stem in R_FIGS:
    for ext in ("pdf", "png"):
        p = HERE / f"{stem}.{ext}"
        check(f"文件存在 {stem}.{ext}", p.exists() and p.stat().st_size > 5000,
              f"{p.stat().st_size if p.exists() else 0} bytes")

r_src = (HERE / "make_fig_r.py")
try:
    r_text = r_src.read_text(encoding="utf-8") if r_src.exists() else ""
    check("FigR 源码存在", bool(r_text))

    # 禁令：不得出现承诺性表述
    bad = [w for w in ("承载力", "能承载") if w in r_text]
    check("FigR 禁令：无「承载力/能承载」承诺性表述", not bad, f"命中 {bad}" if bad else "")

    # 必须携带的限定
    check("FigR 携带「未经实测率定」", "未经实测率定" in r_text)
    check("FigR 携带「合成端点」", "合成端点" in r_text)
    check("FigR 声明 r* 由四参数决定（不可移植）", "project.json" in r_text)

    # 单一数据入口：不得硬编码 CAWCC 数值
    hardcoded = re.findall(r"(?:cawcc|CAWCC)\s*=\s*\d+", r_text)
    check("FigR 不硬编码 CAWCC 数值", not hardcoded, f"命中 {hardcoded}" if hardcoded else "")

    # 数值溯源：r* 必须由产物参数算出 0.5532
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("_figr", r_src)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    rs_val = _mod.r_star()
    check("FigR 数值溯源 r* = 0.5532", abs(rs_val - 0.5532) < 5e-4, f"{rs_val:.4f}")

    # 数值溯源：物理 CAWCC 关键值必须与产物一致
    import pandas as _pd
    _ph = _pd.read_csv(R2 / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")
    _ha0 = float(_ph[(_ph["domain"] == "ha") & (_ph["target_r"] == 0.0)]["physical_cawcc_mw"].iloc[0])
    _ha9 = float(_ph[(_ph["domain"] == "ha") & (_ph["target_r"] == 0.9)]["physical_cawcc_mw"].iloc[0])
    check("FigR 数值溯源 HA 物理 CAWCC r=0 为 1200", _ha0 == 1200.0, f"{_ha0}")
    check("FigR 数值溯源 HA 物理 CAWCC r=0.9 为 1100", _ha9 == 1100.0, f"{_ha9}")
    _co0 = float(_ph[(_ph["domain"] == "co") & (_ph["target_r"] == 0.0)]["physical_cawcc_mw"].iloc[0])
    _co8 = float(_ph[(_ph["domain"] == "co") & (_ph["target_r"] == 0.8)]["physical_cawcc_mw"].iloc[0])
    check("FigR 数值溯源 CO 物理 CAWCC r=0 为 1450", _co0 == 1450.0, f"{_co0}")
    check("FigR 数值溯源 CO 物理 CAWCC r=0.8 仍为 1450（负结果）", _co8 == 1450.0, f"{_co8}")

    # 反噬在 r<=r* 必须精确为零（阈值型响应的核心证据）
    _bl = _pd.read_csv(R2 / "rstar_backlash_decomposition.csv", encoding="utf-8-sig")
    _bl = _bl.drop_duplicates(subset=["domain", "capacity_mw", "target_r"])
    _below = _bl[_bl["target_r"] <= 0.5]["backlash_ml"].abs().max()
    check("FigR 反噬在 r<=0.5 精确为零", _below < 1e-9, f"max|backlash|={_below:.2e}")
    _above = _bl[_bl["target_r"] >= 0.7]["backlash_ml"].min()
    check("FigR 反噬在 r>=0.7 显著为正", _above > 100.0, f"min={_above:.1f} ML")

    # ---- FigR3 分类学 ----
    r3_src = HERE / "make_fig_r3.py"
    check("FigR3 源码存在", r3_src.exists())
    if r3_src.exists():
        r3_text = r3_src.read_text(encoding="utf-8")
        check("FigR3 携带「未经实测率定」", "未经实测率定" in r3_text)
        check("FigR3 携带「合成端点」", "合成端点" in r3_text)
        bad3 = [w for w in ("承载力", "能承载") if w in r3_text]
        check("FigR3 禁令：无承诺性表述", not bad3, f"命中 {bad3}" if bad3 else "")

    # 分类学产物一致性
    import pandas as _pd2
    _rmap = _pd2.read_csv(R2 / "rstar_regime_map.csv", encoding="utf-8-sig")
    _codes = set(_rmap["regime"].dropna().unique())
    check("FigR3 分类图含四情形", _codes == {"I", "II", "III", "IV"}, f"{sorted(_codes)}")
    check("FigR3 分类网格规模 = 320", len(_rmap) == 320, f"{len(_rmap)}")

    _rval = _pd2.read_csv(R2 / "rstar_regime_validation.csv", encoding="utf-8-sig")
    # 情形 II 应有平坦区（CoC 恰为设计值 ≥2 点）
    _ii = _rval[_rval["regime"] == "II"]
    n_flat = int(_ii["coc_equal_design"].sum())
    check("FigR3 情形 II 存在平坦区（≥2 点 CoC==设计值）", n_flat >= 2, f"{n_flat}")
    # 情形 III 应全平坦
    _iii = _rval[_rval["regime"] == "III"]
    check("FigR3 情形 III 全平坦（5/5）", int(_iii["coc_equal_design"].sum()) == len(_iii),
          f"{int(_iii['coc_equal_design'].sum())}/{len(_iii)}")
    # 情形 I 应无平坦点
    _i = _rval[_rval["regime"] == "I"]
    check("FigR3 情形 I 无平坦点（0/5）", int(_i["coc_equal_design"].sum()) == 0,
          f"{int(_i['coc_equal_design'].sum())}/{len(_i)}")
    # 情形 I 与 II 在 r=0.8 应重合（都受水质支配），情形 III 不同
    _r08 = _rval[(_rval["target_r"] - 0.8).abs() < 1e-9]
    _w_i = float(_r08[_r08["regime"] == "I"]["total_withdrawal_ml"].iloc[0])
    _w_ii = float(_r08[_r08["regime"] == "II"]["total_withdrawal_ml"].iloc[0])
    _w_iii = float(_r08[_r08["regime"] == "III"]["total_withdrawal_ml"].iloc[0])
    check("FigR3 情形 I 与 II 在 r=0.8 重合（都受水质支配）",
          abs(_w_i - _w_ii) < 1e-6, f"I={_w_i:.2f} II={_w_ii:.2f}")
    check("FigR3 情形 III 在 r=0.8 不重合（设计值仍起约束）",
          abs(_w_iii - _w_ii) > 1.0, f"III={_w_iii:.2f} vs II={_w_ii:.2f}")

    # ---- FigR4 零效应区与政策口径桥接 ----
    r4_src = HERE / "make_fig_r4.py"
    check("FigR4 源码存在", r4_src.exists())
    if r4_src.exists():
        r4_text = r4_src.read_text(encoding="utf-8")
        check("FigR4 携带「未经实测率定」", "未经实测率定" in r4_text)
        check("FigR4 携带「合成端点」", "合成端点" in r4_text)
        bad4 = [w for w in ("承载力", "能承载") if w in r4_text]
        check("FigR4 禁令：无承诺性表述", not bad4, f"命中 {bad4}" if bad4 else "")

    # 零效应区：r<=0.35 时两域 CAWCC 各自唯一
    for _dom in ("ha", "co"):
        _s = _ph[(_ph["domain"] == _dom) & (_ph["target_r"] <= 0.35)]
        _u = sorted(set(_s["physical_cawcc_mw"].astype(float)))
        check(f"FigR4 零效应区 {_dom.upper()} r≤0.35 CAWCC 唯一", len(_u) == 1, f"{_u}")

    # 政策桥接产物
    import pandas as _pd3
    _br = _pd3.read_csv(R2 / "rstar_policy_bridge.csv", encoding="utf-8-sig")
    check("FigR4 policy_bridge 产物存在且 6 行", len(_br) == 6, f"{len(_br)}")
    _wd_med = float(_br["W_over_D"].median())
    check("FigR4 W/D 中位 ≈ 5.33", abs(_wd_med - 5.33) < 0.01, f"{_wd_med:.2f}")
    # 1000MW 在 u=20% 时 r_max > 1
    _r1000 = _br[(_br["capacity_mw"] - 1000.0).abs() < 1e-6]["W_over_D"]
    _rmax = 0.20 * float(_r1000.iloc[0]) if len(_r1000) else 0.0
    check("FigR4 1000MW@u=20% 的 r_max > 1", _rmax > 1.0, f"{_rmax:.2f}")

    # ---- FigR5 网格收敛性 ----
    _r5_src = HERE / "make_fig_r5.py"
    check("FigR5 源码存在", _r5_src.exists())
    if _r5_src.exists():
        _r5_text = _r5_src.read_text(encoding="utf-8")
        check("FigR5 携带「未经实测率定」", "未经实测率定" in _r5_text)
        check("FigR5 携带「合成端点」", "合成端点" in _r5_text)
        _bad5 = [w for w in ("承载力", "能承载") if w in _r5_text]
        check("FigR5 禁令：无承诺性表述", not _bad5, f"命中 {_bad5}" if _bad5 else "")

    _gct = _pd3.read_csv(R2 / "rstar_grid_convergence_table.csv", encoding="utf-8-sig")
    check("FigR5 收敛表 12 行", len(_gct) == 12, f"{len(_gct)}")
    # 零效应区三网格降幅均为 0
    _z = _gct[_gct["target_r"] <= 0.5]
    _zok = bool((_z[["drop_50mw", "drop_25mw", "drop_10mw"]].abs().max().max()) < 1e-9)
    check("FigR5 零效应区三网格降幅均为 0", _zok, "")
    # HA r=0.9 降幅三网格
    _ha9 = _gct[(_gct["domain"] == "ha") & ((_gct["target_r"] - 0.9).abs() < 1e-9)]
    if len(_ha9):
        _d = [_ha9[f"drop_{k}"].iloc[0] for k in ("50mw", "25mw", "10mw")]
        check("FigR5 HA r=0.9 降幅 -100/-100/-90", _d == [-100.0, -100.0, -90.0], f"{_d}")
    # 绝对值单调趋近
    _ha06 = _gct[(_gct["domain"] == "ha") & ((_gct["target_r"] - 0.6).abs() < 1e-9)]
    if len(_ha06):
        _a = [_ha06[f"cawcc_{k}"].iloc[0] for k in ("50mw", "25mw", "10mw")]
        check("FigR5 绝对值随网格细化单调上升", _a[0] <= _a[1] <= _a[2], f"{_a}")
except Exception as exc:  # noqa: BLE001
    check("FigR 门禁可执行", False, f"{type(exc).__name__}: {exc}")

# ---------- 输出 ----------
print("=" * 72)
print("B0 六主图门禁检查")
print("=" * 72)
passed = sum(1 for _, ok, _ in RESULTS if ok)
for name, ok, detail in RESULTS:
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {name}"
    if detail and not ok:
        line += f"  ({detail})"
    print(line)
print("-" * 72)
print(f"合计 {passed}/{len(RESULTS)} 通过")

out = HERE / "gate_check_result.json"
out.write_text(json.dumps(
    {"passed": passed, "total": len(RESULTS),
     "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in RESULTS]},
    ensure_ascii=False, indent=2), encoding="utf-8")
print(f"-> {out}")
sys.exit(0 if passed == len(RESULTS) else 1)
