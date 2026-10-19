# -*- coding: utf-8 -*-
"""第二轮全部交付的最终全局验证。

一次性跑完三套门禁 + 关键文件完整性 + 原稿未被破坏，给出统一结论。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_final_check.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
FIGDIR = HERE / "figs"
PROJ = HERE.parent.parent
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
PY = sys.executable

ROWS: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    ROWS.append((name, bool(ok), detail))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main() -> None:
    print("=" * 90)
    print("第二轮交付 · 全局验证")
    print("=" * 90)

    # ---------- 1. 三套门禁 ----------
    gates = [
        ("图件门禁", FIGDIR / "_gate_check_b0.py", "91/91"),
        ("数值核对", HERE / "_verify_v2_numbers.py", "28/28"),
        ("交付自审", HERE / "_audit_v2.py", "46/46"),
        ("分类学核对", HERE / "_verify_regime_numbers.py", "41/41"),
        ("政策区隔核对", HERE / "_verify_policy_bridge.py", "25/25"),
        ("摘要溯源核对", HERE / "_verify_abstract_numbers.py", "26/26"),
        ("同步性检查", HERE / "_check_sync.py", "9/9"),
        ("真实城市核对", HERE / "_verify_real_city.py", "30/30"),
    ]
    print("\n[1] 门禁检查")
    import os
    for label, script, expect in gates:
        # 子脚本的 stdout 编码随其内部配置而变（部分脚本未 reconfigure，走 GBK）。
        # 强制子进程用 UTF-8 输出，避免父进程按 UTF-8 解码时拿到替换字符而错过 "合计 X/Y"。
        r = subprocess.run([PY, str(script)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        out = (r.stdout or "") + (r.stderr or "")
        # 从输出里抓 "合计 X/Y"
        import re
        m = re.search(r"合计\s*(\d+)/(\d+)", out)
        got = f"{m.group(1)}/{m.group(2)}" if m else "?"
        ok = r.returncode == 0 and got == expect
        ck(f"{label} = {expect}", ok, f"实际 {got}, rc={r.returncode}")
        print(f"   {'PASS' if ok else 'FAIL'}  {label}: {got}")

    # ---------- 2. 关键文件存在性 ----------
    print("\n[2] 交付文件完整性")
    must = {
        "主稿 v1（原稿，应未改）": HERE / "03_主稿_v1.md",
        "主稿 v2": HERE / "03_主稿_v2.md",
        "理论推导": HERE / "11_水质兼容阈值r星_理论推导.md",
        "实验结果": HERE / "12_rstar实验_结果与判读.md",
        "纯物理口径": HERE / "13_rstar纯物理口径与双因素框架.md",
        "增量章节": HERE / "14_主稿v2增量章节_rstar机制.md",
        "文献坐标": HERE / "15_文献坐标与新颖性边界_v2.md",
        "标题摘要引言": HERE / "16_主稿v2_标题摘要引言.md",
        "修正清单": HERE / "17_v1到v2修正清单.md",
        "工作总结": HERE / "18_第二轮工作总结.md",
        "分类学文档": HERE / "19_r星分类学与敏感性.md",
        "图 FigR1.pdf": FIGDIR / "FigR1_rstar_threshold_response.pdf",
        "图 FigR1.png": FIGDIR / "FigR1_rstar_threshold_response.png",
        "图 FigR2.pdf": FIGDIR / "FigR2_backlash_decomposition.pdf",
        "图 FigR2.png": FIGDIR / "FigR2_backlash_decomposition.png",
        "图 FigR3.pdf": FIGDIR / "FigR3_rstar_regime_and_sensitivity.pdf",
        "图 FigR3.png": FIGDIR / "FigR3_rstar_regime_and_sensitivity.png",
        "现实性检验": HERE / "21_现实性检验_口径区隔.md",
        "贡献定位": HERE / "22_贡献定位_判据而非预测.md",
        "图 FigR4.pdf": FIGDIR / "FigR4_zero_effect_and_policy_bridge.pdf",
        "图 FigR4.png": FIGDIR / "FigR4_zero_effect_and_policy_bridge.png",
        "网格收敛性": HERE / "25_网格收敛性检验.md",
        "图 FigR5.pdf": FIGDIR / "FigR5_grid_convergence.pdf",
        "图 FigR5.png": FIGDIR / "FigR5_grid_convergence.png",
        "SC一手证据": HERE / "32_SantaClara一手证据核实.md",
        "SC判据应用": HERE / "33_SantaClara判据应用结果.md",
    }
    for label, p in must.items():
        ok = p.exists() and p.stat().st_size > 3000
        ck(f"文件存在：{label}", ok, f"{p.stat().st_size if p.exists() else 0} bytes")
        print(f"   {'PASS' if ok else 'FAIL'}  {label}")

    # ---------- 3. 实验产物 ----------
    print("\n[3] 实验产物完整性")
    arts = [
        "rstar_scan_ha.csv", "rstar_scan_co.csv",
        "rstar_cawcc_by_r.csv", "rstar_physical_cawcc_by_r.csv",
        "rstar_boundaries_by_r.csv", "rstar_physical_boundaries_by_r.csv",
        "rstar_confound_control.csv", "rstar_backlash_decomposition.csv",
        "probe_rstar_mechanism.csv", "probe_rstar_mechanism_meta.json",
        "rstar_regime_map.csv", "rstar_regime_summary.json",
        "rstar_regime_validation.csv", "rstar_regime_validation.json",
        "rstar_sensitivity.csv", "rstar_sensitivity_grid.csv",
        "rstar_sensitivity_summary.json",
        "rstar_policy_bridge.csv", "rstar_policy_bridge.json",
        "rstar_grid_convergence_50mw.csv", "rstar_grid_convergence_25mw.csv",
        "rstar_grid_convergence_10mw.csv", "rstar_grid_convergence_summary.json",
        "rstar_grid_convergence_table.csv",
    ]
    for a in arts:
        p = R2 / a
        ok = p.exists() and p.stat().st_size > 200
        ck(f"产物存在：{a}", ok, f"{p.stat().st_size if p.exists() else 0} bytes")
        print(f"   {'PASS' if ok else 'FAIL'}  {a}")

    # ---------- 4. 主稿 v1 未被破坏 ----------
    print("\n[4] 原稿保护")
    v1 = HERE / "03_主稿_v1.md"
    v1_hash = sha256(v1)
    # v1 的字节数在主稿创建时为 60610；这里只校验它仍是 v1 内容（含 v1 标题）
    t1 = v1.read_text(encoding="utf-8")
    ok_title = "约束结构决定 AI 算力扩张的城市水系统瓶颈迁移" in t1
    ok_not_v2 = "## 5.7 结果 4" not in t1
    ck("v1 仍为原稿（标题未变）", ok_title)
    ck("v1 未被注入 v2 章节", ok_not_v2)
    print(f"   {'PASS' if ok_title else 'FAIL'}  v1 标题未变  (sha256={v1_hash})")
    print(f"   {'PASS' if ok_not_v2 else 'FAIL'}  v1 未被注入 v2 章节")

    # ---------- 5. 主稿 v2 关键指标 ----------
    print("\n[5] 主稿 v2 指标")
    t2 = (HERE / "03_主稿_v2.md").read_text(encoding="utf-8")
    ck("v2 含 §5.7", "## 5.7 结果 4" in t2)
    ck("v2 含 §5.8", "## 5.8 结果 5" in t2)
    ck("v2 含 §7.0 三杠杆", "### 7.0 本章的结构" in t2 and "三杠杆" in t2)
    ck("v2 含 §8.5 文献对接", "### 8.5 与水质兼容性文献的对接" in t2)
    ck("v2 含 §9.6 且到第 29 条", "29. **`r*` 的多物种取紧核验" in t2)
    ck("v2 含四情形分类学", "四情形分类学" in t2 and "情形 IV" in t2)
    ck("v2 含参数敏感性节", "5.7.3c" in t2)
    ck("v2 含 §9.6 第 30–34 条", "30. **分类学的参数边界" in t2 and "34. **分类边界随物种集合而定" in t2)
    ck("v2 已修正「三情形一致」错误", "情形 I 与 II 在高替代率端精确重合" in t2)
    ck("v2 引用 FigR3", "FigR3_rstar_regime_and_sensitivity" in t2)
    ck("v2 引用 FigR4", "FigR4_zero_effect_and_policy_bridge" in t2)
    ck("v2 引用 FigR5", "FigR5_grid_convergence" in t2)
    ck("v2 含网格限定段", "本表的网格限定" in t2)
    ck("v2 含第 37-38 条", "37. **网格量化对效应量的影响" in t2
       and "38. **网格不一致的成因" in t2)
    ck("v2 含 §5.9 真实城市应用", "## 5.9 结果 6" in t2)
    ck("v2 含 §9.7 限制", "### 9.7 真实城市应用" in t2)
    ck("v2 含 k*=3.50 判据", "k* = 3.50" in t2)
    ck("v2 含第 39-44 条", "39. **§5.9 是应用，不是验证" in t2
       and "44. **`r*` 的四个参数没有一个有实测锚点" in t2)
    ck("v2 含第 45-46 条（k* 的 ρ 依赖与单城份额）",
       "45. **`k* = 3.50` 强烈依赖份额比" in t2
       and "46. **份额本身只有一城数据" in t2)
    ck("v2 物种数已更正为 2", "模型实际追踪 2 个物种" in t2)
    ck("v2 参数锚定已更正为 20", "20 个有观测锚定" in t2)
    ck("加州 k 分布产物存在", (HERE / "_ca_k_distribution.json").exists()
       and (HERE / "_ca_k_distribution.json").stat().st_size > 1000)
    ck("加州 k 清洗产物存在", (HERE / "_ca_k_clean.json").exists()
       and (HERE / "_ca_k_clean.json").stat().st_size > 1000)
    ck("v2 含 §1.6 口径区隔", "### 1.6 一个必须区分的口径" in t2)
    ck("v2 含 §5.8.2b 零效应区", "5.8.2b" in t2 and "零效应区" in t2)
    ck("v2 含 §8.6 政策意义", "### 8.6 政策意义" in t2)
    ck("v2 含判据而非预测的定位", "本文的贡献**不是预测**" in t2)
    ck("v2 含第 35–36 条", "35. **本文的 `r` 是园区级替代率" in t2
       and "36. **`W/D` 本身是模型产物" in t2)
    ck("v2 首行已改为 v2", t2.startswith("# 主稿 v2"))
    ck("v2 状态行已改为定稿候选", "v2 定稿候选" in t2 and "v1 草稿" not in t2)
    ck("v2 §7 标题已改为三杠杆", "再生水的三个杠杆" in t2)
    # 摘要覆盖度
    import re as _re
    _ab = _re.search(r"## 摘要\n(.*?)\n---", t2, flags=_re.S)
    _ab = _ab.group(1) if _ab else ""
    for _kw, _name in (("四类", "四情形分类"), ("情形 I", "情形命名"),
                       ("W/D", "口径区隔"), ("判据与条件", "判据定位"),
                       ("0.6842", "多物种取紧"), ("精确为零", "零效应"),
                       ("可证伪", "可证伪性")):
        ck(f"摘要覆盖：{_name}", _kw in _ab, "" if _kw in _ab else "MISSING")
    ck("v2 含多物种核验（TDS 0.5532 / Cl 0.6842）",
       "0.6842" in t2 and "min(0.5532, 0.6842)" in t2)
    ck("v2 含双因素框架", "双因素" in t2)
    ck("v2 保留作者占位符", "[[待填]]" in t2)

    # 红线：任何一个「能承载 / 承载力」都必须处在否定/禁令语境中。
    # 判据：向前 90 字符或向后 20 字符内出现否定词，且语境是"表述/声称/禁令"而非"主张"。
    import re as _re
    red_hits = []
    for kw in ("承载力", "能承载"):
        for m in _re.finditer(kw, t2):
            ctx = t2[max(0, m.start() - 90): m.start() + 20]
            negated = any(neg in ctx for neg in
                          ("不含", "不声称", "不是", "而非", "不得", "禁止", "避免", "红线"))
            if not negated:
                red_hits.append(ctx.replace("\n", " "))
    ck("v2 红线：承诺性表述仅在否定/禁令语境", not red_hits,
       f"违规 {len(red_hits)} 处：{red_hits[:2]}" if red_hits else "")
    for label in ("§5.7", "§5.8", "§7.0", "§8.5", "§9.6", "多物种"):
        pass
    print(f"   v2 字数 {len(t2):,}；行数 {t2.count(chr(10)) + 1}")

    # ---------- 输出 ----------
    print("\n" + "=" * 90)
    passed = sum(1 for _, ok, _ in ROWS if ok)
    for name, ok, detail in ROWS:
        if not ok:
            print(f"[FAIL] {name}  ({detail})")
    print(f"汇总：{passed}/{len(ROWS)} 通过")

    out = HERE / "_final_check.json"
    out.write_text(json.dumps(
        {"passed": passed, "total": len(ROWS),
         "rows": [{"name": n, "ok": o, "detail": d} for n, o, d in ROWS]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out}")
    sys.exit(0 if passed == len(ROWS) else 1)


if __name__ == "__main__":
    main()
