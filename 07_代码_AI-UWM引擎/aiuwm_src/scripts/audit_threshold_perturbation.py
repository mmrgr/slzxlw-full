"""实验3：迁移点阈值扰动敏感性（±2%）

【为什么做】
`假设预注册_R5.md:76` 登记了一项未完成的证据要求：
  "字典序敏感性检验 | ❌ 未实现 | 在约束接近阈值的点附近做 ±2% 阈值扰动，
   检查主导约束是否翻转"

这是外部评审（建议 6）明确指出、且本项目已承认的方法缺口。若某迁移点在
±2% 阈值扰动下主导约束发生翻转，则迁移序列的细部结构会被削弱。

【为什么不需要重跑模型】
CAWCC 与"首失效约束"是**容量扫描结果 + 约束阈值**的确定性函数：
  CAWCC = f(scan KPI 矩阵, 约束定义)
扰动阈值只改变 `constraints[*]['value']`，不改变 scan KPI。因此本实验是
**纯后处理**，不需要跑引擎。这使它成为性价比最高的补做项。

【扰动设计（关键：不能用盲目的相对扰动）】
首轮实现用"全部阈值 × {0.98..1.02}"，结果 ×1.02 时 CAWCC 变成 None、
主导约束翻成 `system_reliability_fraction`。**这是扰动设计的伪影，不是真实敏感性**：

  `system_reliability_fraction >= 0.99`，×1.02 = 1.0098 > 1.0
  → 可靠度在物理上不可能超过 1.0，该约束因此恒失败，任何容量点都不安全。

同理：
  `domestic_unmet_ml <= 0.0` 与 `unmet_cooling_water_ml <= 0.0`
  → 阈值是 0，×任何系数仍是 0，相对扰动无效。

因此本脚本按约束的**阈值量纲**分类扰动：

  A. 零容忍约束（阈值 = 0）：**不扰动**。它们是物理零容忍（居民/冷却未满足量必须为 0），
     没有"±2% 裕度"的语义。在输出中标记 `perturbation_skipped_reason`。
  B. 有物理上界的比例型约束（阈值 = 0.99 可靠度）：**只向下扰动**
     （0.98/0.99，即收紧方向），因为向上会越过 1.0 的物理上界。
  C. 规划裕度/比值型约束（阈值 = 0.95 / 1.0 / 0.65 / 0.40）：**双向相对扰动 ±2%**。

这个分类本身就是对"±2% 阈值扰动"这条预注册要求的正确执行方式——盲目套用会产生伪影。

【输出】
- `validation_artifacts/r2/threshold_perturbation_sensitivity.csv`
  逐 (域, 扰动, 约束) 的首失效容量与是否位移
- `validation_artifacts/r2/threshold_perturbation_summary.json`
  汇总：每域 CAWCC 稳健区间、翻转的约束清单、扰动设计说明、裁定

用法:
    PYTHONPATH="src;scripts" python scripts/audit_threshold_perturbation.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.ai_capacity import (  # noqa: E402
    find_ai_carrying_capacity,
    summarize_constraint_boundaries,
)
from run_r2 import daily_constraints  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUT = ROOT / "validation_artifacts" / "r2"

FACTORS = (0.98, 0.99, 1.00, 1.01, 1.02)
GRID_STEP_MW = 50.0

# 分类规则（按约束名，不按阈值数值猜测，避免歧义）
ZERO_TOLERANCE = {
    "domestic_unmet_ml": "阈值=0 的零容忍物理约束，无 ±2% 裕度语义，不扰动",
    "unmet_cooling_water_ml": "阈值=0 的零容忍物理约束，无 ±2% 裕度语义，不扰动",
}
UPPER_BOUNDED = {
    "system_reliability_fraction": (
        "阈值 0.99 接近物理上界 1.0；向上扰动会越过 1.0 使约束恒失败（伪影），"
        "故只做向下（收紧）扰动"
    ),
}


def classify(name: str, value: float) -> tuple[str, str]:
    if name in ZERO_TOLERANCE:
        return "A_zero_tolerance", ZERO_TOLERANCE[name]
    if name in UPPER_BOUNDED:
        return "B_upper_bounded", UPPER_BOUNDED[name]
    return "C_regular", "规划裕度/比值型约束，双向 ±2% 相对扰动"


def build_perturbed(raw: dict, factor: float) -> tuple[dict, dict]:
    """Return (constraints, per-constraint perturbation record)."""
    base = daily_constraints(raw)
    out = copy.deepcopy(base)
    records: dict[str, dict] = {}

    for name, definition in out.items():
        original = float(definition["value"])
        kind, reason = classify(name, original)

        if kind == "A_zero_tolerance":
            records[name] = {
                "kind": kind,
                "original": original,
                "applied": original,
                "perturbation_skipped_reason": reason,
            }
            continue

        if kind == "B_upper_bounded" and factor > 1.0:
            # 向上扰动会越过物理上界：保持原值，并显式记录
            records[name] = {
                "kind": kind,
                "original": original,
                "applied": original,
                "perturbation_skipped_reason": reason + "（本扰动水平为向上，已跳过）",
            }
            continue

        applied = original * factor
        definition["value"] = applied
        records[name] = {
            "kind": kind,
            "original": original,
            "applied": applied,
            "perturbation_skipped_reason": None,
        }

    return {"constraints": out}, records


def main() -> None:
    rows: list[dict] = []
    summary: dict = {}

    for domain in ("ha", "co"):
        scan = pd.read_csv(OUT / domain / "capacity_scan.csv")
        raw = json.loads((R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8"))
        positive = scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True)

        base_defs = daily_constraints(raw)
        base_threshold = find_ai_carrying_capacity(positive, {"constraints": base_defs})
        base_boundaries = summarize_constraint_boundaries(positive, {"constraints": base_defs})
        base_first = {
            str(r["constraint"]): r["first_failed_capacity_mw"]
            for _, r in base_boundaries.iterrows()
        }
        base_cawcc = base_threshold["maximum_safe_ai_capacity_mw"]
        base_limiting = base_threshold["limiting_constraint"]

        domain_records = {
            "baseline_cawcc_mw": base_cawcc,
            "baseline_limiting_constraint": base_limiting,
            "baseline_first_failed_capacity_mw": base_threshold["first_failed_capacity_mw"],
            "grid_step_mw": GRID_STEP_MW,
            "perturbation_design": {
                "factors": list(FACTORS),
                "A_zero_tolerance_not_perturbed": sorted(ZERO_TOLERANCE),
                "B_upper_bounded_only_downward": sorted(UPPER_BOUNDED),
                "C_regular_bidirectional": sorted(
                    k for k in base_defs
                    if k not in ZERO_TOLERANCE and k not in UPPER_BOUNDED
                ),
                "rationale": (
                    "首轮盲目对全部阈值做相对扰动时，system_reliability_fraction 的 ×1.02 "
                    "越过物理上界 1.0，导致该约束恒失败、CAWCC 变为 None——这是伪影。"
                    "本设计按阈值量纲分类扰动。"
                ),
            },
            "perturbations": {},
        }

        for factor in FACTORS:
            defs, pert_records = build_perturbed(raw, factor)
            threshold = find_ai_carrying_capacity(positive, defs)
            boundaries = summarize_constraint_boundaries(positive, defs)
            first = {
                str(r["constraint"]): r["first_failed_capacity_mw"]
                for _, r in boundaries.iterrows()
            }

            cawcc = threshold["maximum_safe_ai_capacity_mw"]
            limiting = threshold["limiting_constraint"]
            cawcc_shift = (
                None if (cawcc is None or base_cawcc is None) else float(cawcc) - float(base_cawcc)
            )
            limiting_flipped = bool(limiting != base_limiting)

            constraint_shifts = {}
            for name in base_first:
                before = base_first[name]
                after = first.get(name)
                if before is None and after is None:
                    shift = 0.0
                elif before is None or after is None:
                    shift = None
                else:
                    shift = float(after) - float(before)
                constraint_shifts[name] = {
                    "before": before,
                    "after": after,
                    "shift_mw": shift,
                    "perturbation": pert_records[name],
                }

            moved = [
                name for name, info in constraint_shifts.items()
                if info["shift_mw"] is None or abs(info["shift_mw"]) > 1e-9
            ]

            domain_records["perturbations"][f"{factor:.2f}"] = {
                "factor": factor,
                "cawcc_mw": cawcc,
                "cawcc_shift_mw": cawcc_shift,
                "first_failed_capacity_mw": threshold["first_failed_capacity_mw"],
                "limiting_constraint": limiting,
                "limiting_flipped": limiting_flipped,
                "constraints_with_shifted_first_failure": moved,
                "constraint_first_failure": constraint_shifts,
            }

            for name, info in constraint_shifts.items():
                pert = info["perturbation"]
                rows.append({
                    "域": domain,
                    "扰动系数": factor,
                    "约束": name,
                    "约束类别": pert["kind"],
                    "原阈值": pert["original"],
                    "施加阈值": pert["applied"],
                    "是否跳过扰动": pert["perturbation_skipped_reason"] is not None,
                    "跳过原因": pert["perturbation_skipped_reason"],
                    "基准首失效_MW": info["before"],
                    "扰动后首失效_MW": info["after"],
                    "位移_MW": info["shift_mw"],
                    "是否改变": (
                        info["shift_mw"] is None or abs(info["shift_mw"]) > 1e-9
                    ),
                    "域基准CAWCC_MW": base_cawcc,
                    "扰动后CAWCC_MW": cawcc,
                    "CAWCC位移_MW": cawcc_shift,
                    "主导约束是否翻转": limiting_flipped,
                    "主导约束_基准": base_limiting,
                    "主导约束_扰动后": limiting,
                })

        # ---- 汇总裁定 ----
        cawcc_values = [
            domain_records["perturbations"][f"{f:.2f}"]["cawcc_mw"] for f in FACTORS
        ]
        cawcc_values = [v for v in cawcc_values if v is not None]
        max_span = float(max(cawcc_values) - min(cawcc_values)) if cawcc_values else None

        flipped_at = [
            f"{f:.2f}" for f in FACTORS
            if domain_records["perturbations"][f"{f:.2f}"]["limiting_flipped"]
        ]

        # 只统计"真正被扰动"的约束的位移（跳过的不算敏感性证据）
        moved_perturbed = sorted({
            name
            for f in FACTORS
            for name in domain_records["perturbations"][f"{f:.2f}"][
                "constraints_with_shifted_first_failure"
            ]
            if domain_records["perturbations"][f"{f:.2f}"][
                "constraint_first_failure"][name]["perturbation"]["perturbation_skipped_reason"]
            is None
        })

        base_order = [k for k, _ in sorted(
            ((k, v) for k, v in base_first.items() if v is not None), key=lambda kv: kv[1]
        )]
        order_stable = True
        for f in FACTORS:
            pert = domain_records["perturbations"][f"{f:.2f}"]["constraint_first_failure"]
            order = [k for k, _ in sorted(
                ((k, info["after"]) for k, info in pert.items() if info.get("after") is not None),
                key=lambda kv: kv[1],
            )]
            if order != base_order:
                order_stable = False
                domain_records["perturbations"][f"{f:.2f}"]["order_changed"] = True

        if max_span is not None and max_span <= GRID_STEP_MW and not flipped_at and order_stable:
            verdict = "STABLE_WITHIN_PM2PCT"
        elif max_span is not None and max_span <= GRID_STEP_MW and not flipped_at:
            verdict = "CAWCC_AND_LIMITING_STABLE_BUT_ORDER_SHIFTS"
        elif max_span is not None and max_span <= GRID_STEP_MW:
            verdict = "CAWCC_STABLE_BUT_LIMITING_FLIPS"
        else:
            verdict = "CAWCC_SENSITIVE_TO_THRESHOLD"

        domain_records["verdict"] = verdict
        domain_records["max_cawcc_span_mw"] = max_span
        domain_records["perturbations_with_limiting_flip"] = flipped_at
        domain_records["constraints_with_any_shift_under_real_perturbation"] = moved_perturbed
        domain_records["migration_order_stable"] = order_stable
        summary[domain] = domain_records

        print(f"\n{'=' * 78}\n{domain.upper()}  threshold perturbation (+/-2%)\n{'=' * 78}")
        print(f"  baseline CAWCC = {base_cawcc} MW, limiting = {base_limiting}")
        for f in FACTORS:
            rec = domain_records["perturbations"][f"{f:.2f}"]
            print(
                f"  x{f:.2f}  CAWCC={rec['cawcc_mw']}  shift={rec['cawcc_shift_mw']}  "
                f"limiting={rec['limiting_constraint']}  "
                f"{'FLIP!' if rec['limiting_flipped'] else 'ok'}"
            )
        print(f"  CAWCC span = {max_span} MW (grid step {GRID_STEP_MW})")
        print(f"  perturbations with limiting flip = {flipped_at or 'none'}")
        print(f"  constraints whose first-failure moved (real perturbation) = {moved_perturbed or 'none'}")
        print(f"  migration order stable = {order_stable}")
        print(f"  verdict = {verdict}")

    frame = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT / "threshold_perturbation_sensitivity.csv", index=False, encoding="utf-8-sig")
    (OUT / "threshold_perturbation_summary.json").write_text(
        json.dumps({
            "purpose": "迁移点 ±2% 阈值扰动敏感性（假设预注册_R5.md:76 登记的方法缺口）",
            "method": (
                "纯后处理：对 capacity_scan.csv 的 KPI 矩阵重施加扰动后的约束阈值，"
                "不重跑引擎。扰动按阈值量纲分类（见 perturbation_design）。"
            ),
            "grid_step_mw": GRID_STEP_MW,
            "domains": summary,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n-> {OUT / 'threshold_perturbation_sensitivity.csv'}")
    print(f"-> {OUT / 'threshold_perturbation_summary.json'}")


if __name__ == "__main__":
    main()
