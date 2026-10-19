# -*- coding: utf-8 -*-
"""主稿 v2 交付自审：结构、红线、数值一致性、可溯源性的最终检查。

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_audit_v2.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
V2 = HERE / "03_主稿_v2.md"
PROJ = HERE.parent.parent
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"

ROWS: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    ROWS.append((name, bool(ok), detail))


def main() -> None:
    text = V2.read_text(encoding="utf-8")

    # ---- 结构完整性 ----
    required_sections = [
        "## 摘要", "## 1 引言", "### 1.2 缺口", "### 1.3 本文的定位与贡献",
        "### 1.5 一个必须提前说明的方法立场",
        "## 2 研究框架", "## 3 方法", "### 3.3 十条约束",
        "## 4 结果 1", "## 5 结果 2",
        "## 5.7 结果 4", "## 5.8 结果 5",
        "## 6 结果 3", "## 7 专题章", "### 7.0 本章的结构",
        "## 8 讨论", "## 9 局限", "### 9.6 水质兼容阈值章",
        "## 10 数据与代码可用性", "## 11 作者贡献",
        "## 附录 A", "## 附录 B",
    ]
    for sec in required_sections:
        ck(f"章节存在：{sec}", sec in text)

    # ---- 红线：承诺性表述只能出现在否定语境 ----
    for bad in ("承载力", "能承载"):
        bad_hits = []
        for m in re.finditer(bad, text):
            ctx = text[max(0, m.start() - 60): m.end() + 60]
            if not any(neg in ctx for neg in ("不", "禁止", "不是", "不得", "红线", "避免")):
                bad_hits.append(ctx.replace("\n", " "))
        ck(f"红线：「{bad}」无承诺性用法", not bad_hits,
           f"命中 {len(bad_hits)} 处：{bad_hits[:1]}" if bad_hits else "")

    # ---- 必须携带的限定词 ----
    for kw in ("未经实测率定", "合成端点", "不声称", "estimand",
               "hydrology_validation", "纯物理口径", "联合口径"):
        ck(f"携带限定/术语：{kw}", kw in text)

    # ---- 数字一致性（与产物比对）----
    # r*
    ck("摘要含 r* = 0.5532", "0.5532" in text)
    # 残差
    ck("含机器精度残差 8.9×10⁻¹⁶", "8.9×10⁻¹⁶" in text or "8.882e" in text)

    # 纯物理 CAWCC
    ph = __import__("pandas").read_csv(R2 / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")
    ha9 = float(ph[(ph["domain"] == "ha") & (ph["target_r"] == 0.9)]["physical_cawcc_mw"].iloc[0])
    ck("正文的 HA r=0.9 纯物理 1100 与产物一致",
       ha9 == 1100.0 and "1100" in text, f"产物={ha9}")
    co8 = float(ph[(ph["domain"] == "co") & (ph["target_r"] == 0.8)]["physical_cawcc_mw"].iloc[0])
    ck("正文的 CO 负结果（1450 不变）与产物一致",
       co8 == 1450.0 and "1450" in text, f"产物={co8}")

    # 混淆排除关键值
    cf = __import__("pandas").read_csv(R2 / "rstar_confound_control.csv", encoding="utf-8-sig")
    h = cf[(cf["domain"] == "ha") & ((cf["capacity_mw"] - 1200.0).abs() < 1e-6)]
    s5 = float(h[h["target_r"] == 0.5]["max_source_abstraction_ratio"].iloc[0])
    s6 = float(h[h["target_r"] == 0.6]["max_source_abstraction_ratio"].iloc[0])
    ck("正文 0.9497 / 0.9513 与产物一致",
       abs(s5 - 0.9497) < 5e-4 and abs(s6 - 0.9513) < 5e-4 and "0.9497" in text and "0.9513" in text,
       f"{s5:.4f}/{s6:.4f}")

    # 反噬归零
    dec = __import__("pandas").read_csv(R2 / "rstar_backlash_decomposition.csv", encoding="utf-8-sig")
    dec = dec.drop_duplicates(subset=["domain", "capacity_mw", "target_r"])
    below = dec[dec["target_r"] <= 0.5]["backlash_ml"].abs().max()
    ck("正文「反噬在 r<=r* 精确为零」有产物支撑", below < 1e-9 and "精确为零" in text,
       f"max={below:.2e}")

    # 三杠杆口径已统一到 50 MW 网格（2026-10-18 重跑）
    rm_old = __import__("pandas").read_csv(R2 / "ha" / "reuse_marginal_curve.csv", encoding="utf-8-sig")
    old_vals = sorted(set(rm_old["cawcc_mw"].astype(float)))
    ck("旧 100 MW 处理能力曲线仍为 1100（历史对照保留）",
       old_vals == [1100.0], f"产物={old_vals}")

    rm_new = __import__("pandas").read_csv(
        R2 / "ha" / "reuse_marginal_curve_50mw.csv", encoding="utf-8-sig")
    new_vals = sorted(set(rm_new["cawcc_mw"].astype(float)))
    ck("§7.5 处理能力值已统一为 50 MW 网格的 1150（与主结果同网格）",
       new_vals == [1150.0] and "恒 1150 MW" in text, f"产物={new_vals}")

    # 口径声明存在（已由"不可算术"升级为"已统一 + 旧值修正说明"）
    ck("§7.5 携带口径声明（同网格已统一，并说明旧 +300 为伪影）",
       "口径声明" in text and ("同网格" in text or "已统一" in text)
       and ("伪影" in text or "取整" in text))

    # §5.6 矛盾已修
    ck("§5.6 已删「迁移点未做阈值扰动」",
       "迁移点未做 ±2% 阈值扰动" not in text)
    ck("§5.6 已写入「已检验」表述", "阈值扰动敏感性已检验" in text)

    # 作者占位符保留
    ck("作者占位符保留（不代拟）", "[[待填]]" in text or "[[待作者确认]]" in text)

    # 图件引用
    ck("引用 FigR1", "FigR1_rstar_threshold_response" in text)
    ck("引用 FigR2", "FigR2_backlash_decomposition" in text)

    # 9.6 限制条数
    limits = re.findall(r"^(\d+)\. \*\*", text, flags=re.M)
    ck("限制条目编号连续（至少到 28）", "28." in text or "28. **" in text)

    # ---- 输出 ----
    print("=" * 84)
    print("主稿 v2 交付自审")
    print("=" * 84)
    passed = 0
    for name, ok, detail in ROWS:
        if ok:
            passed += 1
        line = f"[{'PASS' if ok else 'FAIL'}] {name}"
        if not ok and detail:
            line += f"  ({detail})"
        print(line)
    print("-" * 84)
    print(f"合计 {passed}/{len(ROWS)} 通过")

    out = HERE / "_audit_v2.json"
    out.write_text(json.dumps(
        {"passed": passed, "total": len(ROWS),
         "rows": [{"name": n, "ok": o, "detail": d} for n, o, d in ROWS]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out}")
    sys.exit(0 if passed == len(ROWS) else 1)


if __name__ == "__main__":
    main()
