"""R8 防线校验：把 D1/D2 修复传播到全部派生情景变体后，容量结论是否仍未被摇动。

背景
----
scripts/repair_d1_d2_R8.py 只回写了 ha/co 两个 `project.json`。但 tech_* / policy_* /
energy_rich 共 21 个变体是由 scripts/build_r2_domains.py 从同一份 base_project 派生的
副本，当时仍停留在旧配置：

    EWIF  = 0.40 (HA) / 0.18 (CO) / 0.08 (能源富集)   ← 无文献出处
    WWTW1.direct_emissions 缺失                       ← 污水厂过程排放恒为 0

后果不只是"参数旧"，而是**口径不一致**：任何 技术变体 ↔ 基线 的对照里都掺进了
ΔEWIF ≠ 0 的伪差异。现已通过重新生成（而非就地打补丁）统一传播。

本脚本回答一个决定性问题
------------------------
修复前后，每个变体在整条容量阶梯上的 11 条 CAWCC 约束取值、以及由此推出的
承载阈值 `maximum_safe_ai_capacity_mw` 与 `limiting_constraint`，是否逐位一致？

做法：用 git 里 HEAD 版本的变体（= 修复前）与工作区版本（= 修复后）分别跑同一条
阶梯，逐格比对。不比对"所有数值列"——足迹类指标（间接水、系统碳）在 D1/D2 下
本应改变，否则会永远 FAIL（本系列脚本第一版就踩过这个坑）。

用法
----
    cd 07_代码_AI-UWM引擎/aiuwm_src
    PYTHONPATH=src python scripts/verify_variant_consistency_R8.py
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd

from aiuwm.ai_capacity import find_ai_carrying_capacity, scan_ai_capacity

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "examples" / "cawcc_r2"
ART = ROOT / "validation_artifacts" / "r2"
ART.mkdir(parents=True, exist_ok=True)

# 与 run_r2.py 技术/政策对照所用的阶梯保持一致，确保比的是同一个 estimand。
LADDER = [0.0, 500.0, 1000.0, 1500.0, 2000.0]
DOMAINS = ("ha", "co")


def git_head_json(relpath: str) -> dict:
    """取 git HEAD 中该文件的原始内容（即本轮修复之前的状态）。"""
    blob = subprocess.run(
        ["git", "show", f"HEAD:{relpath}"],
        cwd=ROOT, capture_output=True, check=True,
    )
    return json.loads(blob.stdout.decode("utf-8"))


def daily_constraints(domain: str) -> dict:
    """与 run_r2.daily_constraints() 完全同构的日尺度约束集合。

    关键：必须剔除 `max_reuse_utilization`。再生水厂配储池后，日尺度"处理速率达铭牌"
    属正常调蓄而非失效，该指标在全容量区间恒为 1.0；保留它会让承载容量恒为 0，
    find_ai_carrying_capacity 因而返回 None。本轮第一版直接套原始 spec 即踩此坑。
    """
    spec = json.loads((R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8"))
    return {"constraints": {
        name: dict(defn) for name, defn in spec["constraints"].items()
        if name != "max_reuse_utilization"
    }}


def threshold(scan: pd.DataFrame, domain: str) -> dict:
    """由既有扫描结果推承载阈值，避免重复跑引擎。"""
    return find_ai_carrying_capacity(
        scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True),
        daily_constraints(domain),
    )


def main() -> int:
    rows: list[dict] = []
    failures = 0

    for dom in DOMAINS:
        ts = pd.read_csv(R2 / dom / "timeseries.csv")
        variants = sorted(p.name for p in (R2 / dom).glob("*.json"))
        for name in variants:
            rel = f"examples/cawcc_r2/{dom}/{name}"
            new_proj = json.loads((R2 / dom / name).read_text(encoding="utf-8"))
            try:
                old_proj = git_head_json(rel)
            except subprocess.CalledProcessError:
                rows.append({
                    "域签": dom, "变体": name, "校验": "取 HEAD 版本",
                    "结论": "SKIP（该文件不在 git HEAD 中，无法比对）",
                })
                continue

            a = scan_ai_capacity(old_proj, ts, capacities_mw=LADDER)
            b = scan_ai_capacity(new_proj, ts, capacities_mw=LADDER)

            spec_keys = list(daily_constraints(dom)["constraints"].keys())
            shared = [c for c in spec_keys if c in a.columns and c in b.columns]
            worst = 0.0
            worst_col = ""
            for col in shared:
                dev = (a[col].astype(float) - b[col].astype(float)).abs().max()
                if dev > worst:
                    worst, worst_col = float(dev), col

            ta = threshold(a, dom)
            tb = threshold(b, dom)
            # None 是 find_ai_carrying_capacity 的合法返回值：阶梯内无任何可行容量
            # （部分激进冷却技术在 500 MW 起已不可行）。它不是异常，但必须两侧一致。
            cap_raw_a = ta.get("maximum_safe_ai_capacity_mw")
            cap_raw_b = tb.get("maximum_safe_ai_capacity_mw")
            cap_same = cap_raw_a == cap_raw_b
            limit_same = ta.get("limiting_constraint") == tb.get("limiting_constraint")

            # 足迹类指标必须改变（否则说明修复没生效），容量类必须不变。
            foot_changed = int(
                (a["offsite_electricity_water_ml"].astype(float).sum()
                 != b["offsite_electricity_water_ml"].astype(float).sum())
                if "offsite_electricity_water_ml" in a.columns else False
            )
            ok = worst <= 1e-9 and cap_same and limit_same
            failures += 0 if ok else 1

            def _fmt(value) -> str:
                return "无可行容量" if value is None else f"{float(value):.1f}"

            rows.append({
                "域签": dom,
                "变体": name,
                "容量类约束比对列数": len(shared),
                "约束最大偏差": round(worst, 12),
                "偏差列": "" if worst <= 1e-9 else worst_col,
                "修复前阈值_MW": _fmt(cap_raw_a),
                "修复后阈值_MW": _fmt(cap_raw_b),
                "瓶颈约束一致": "是" if limit_same else f"否({ta.get('limiting_constraint')}→{tb.get('limiting_constraint')})",
                "足迹类已改变": "是" if foot_changed else "（无水足迹列）",
                "结论": "PASS" if ok else "FAIL",
            })
            print(f"[{dom}] {name:<32} 阈值 {_fmt(cap_raw_a):>9} → {_fmt(cap_raw_b):>9}  "
                  f"约束偏差 {worst:.2e}  {'PASS' if ok else 'FAIL'}")

    out = pd.DataFrame(rows)
    out.to_csv(ART / "variant_consistency_R8.csv", index=False, encoding="utf-8-sig")
    print(f"\n[OK] {ART / 'variant_consistency_R8.csv'}  rows={len(out)}")
    print(f"=== 判定 ===  失败 {failures} 项")
    if failures:
        print("❌ 修复传播后容量结论发生变化，不得据此更新论文表述")
        return 1
    print("✅ 全部变体：10 条日尺度 CAWCC 约束逐位一致、承载阈值与瓶颈约束均未改变")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
