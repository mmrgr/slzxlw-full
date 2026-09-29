"""把 12 条序列与新增 8 条合并为 20 条多序列集合（对应外部建议 5）。

第 12–19 条由 `seed = 20260918 + i×100003` (i=12..19) 生成，即
`--sequences 8 --base-seed 1220954 --stride 100003`，与原 12 条**同属一个确定性种子族**，
且扫描网格（max-mw 1200 / step 100）与原 run 完全一致，因此前 12 条数值原样保留。

★ 重要限定（务必随产物引用）：新增序列**仍是同一套合成驱动规则的不同种子抽样**，
并非独立气候假设。本脚本在产物里显式写入 `hydrology_validation = "NONE"`，
防止读者把"序列条数增加"误读为"水文不确定性已被外部观测表征"。

用法：
    PYTHONPATH=src python scripts/merge_reservoir_ensemble.py
"""
from __future__ import annotations

import json
import shutil
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

R2 = ROOT / "validation_artifacts" / "r2"
BASE = R2 / "reservoir_multiyear_ensemble.json"       # 原 12 条
EXT = R2 / "reservoir_multiyear_ensemble_ext.json"    # 新增 8 条（索引 12–19）
BACKUP = R2 / "reservoir_multiyear_ensemble_12seq.json"
OUT = R2 / "reservoir_multiyear_ensemble.json"

WARNING = (
    "合成驱动规则的不同种子抽样，非观测水文；序列条数增加提高的是采样精度，"
    "不提高证据等级——序列生成器本身未经任何外部观测验证"
)


def merge_domain(base: dict, ext: dict, offset: int) -> dict:
    values = list(base["joint_gate_mw_values"])
    term = list(base["last_terminal_ge_100pct_mw_values"])
    per = list(base["per_sequence"])

    if ext is not None:
        values += list(ext["joint_gate_mw_values"])
        term += list(ext["last_terminal_ge_100pct_mw_values"])
        for row in ext["per_sequence"]:
            row = dict(row)
            row["sequence_index"] = int(row["sequence_index"]) + offset
            per.append(row)

    numeric = [float(v) for v in values if v is not None]
    return {
        "domain": base["domain"],
        "years": base["years"],
        "sequences": len(values),
        "base_seed": base["base_seed"],
        "stride": base["stride"],
        "grid": {"max_mw": 1200.0, "step_mw": 100.0, "note": "与原 12 条 run 完全一致"},
        "hydrology_basis": base["hydrology_basis"] + f"；并扩展到 {len(values)} 条独立序列",
        "hydrology_validation": "NONE",
        "hydrology_validation_note": WARNING,
        "joint_gate_mw_values": values,
        "last_terminal_ge_100pct_mw_values": term,
        "joint_gate_mw_min": min(numeric) if numeric else None,
        "joint_gate_mw_max": max(numeric) if numeric else None,
        "joint_gate_mw_median": statistics.median(numeric) if numeric else None,
        "joint_gate_mw_stdev": statistics.stdev(numeric) if len(numeric) > 1 else 0.0,
        "censored_sequences": sum(1 for v in values if v is None),
        "per_sequence": per,
    }


def main() -> int:
    if not BASE.exists():
        print(f"缺少原集合文件：{BASE}")
        return 1
    if not EXT.exists():
        print(f"缺少扩展集合文件：{EXT}（需先跑 audit_reservoir_ensemble.py）")
        return 1

    base = json.loads(BASE.read_text(encoding="utf-8"))
    ext = json.loads(EXT.read_text(encoding="utf-8"))

    if not BACKUP.exists():
        shutil.copyfile(BASE, BACKUP)
        print(f"原 12 条已备份 -> {BACKUP}")

    offset = base["ha"]["sequences"] if "ha" in base else 12
    merged: dict = {}
    for domain, report in base.items():
        merged[domain] = merge_domain(report, ext.get(domain), offset)

    OUT.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten -> {OUT}")
    for domain, report in merged.items():
        print(
            f"{domain}: 序列 {report['sequences']} 条 | 联合门槛中位 "
            f"{report['joint_gate_mw_median']:.0f} MW | 范围 "
            f"[{report['joint_gate_mw_min']}, {report['joint_gate_mw_max']}] | "
            f"std={report['joint_gate_mw_stdev']:.1f} | "
            f"删失={report['censored_sequences']}/{report['sequences']}"
        )
    print("\n⚠️  hydrology_validation = NONE —— 序列未经观测验证，引用时必须携带该限定")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
