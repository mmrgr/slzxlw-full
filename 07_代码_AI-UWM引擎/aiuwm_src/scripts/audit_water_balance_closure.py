"""系统层水量闭合检验（对应外部建议 4 的「先验证水量闭合」）。

背景：建议 4 的验收目标为"水量闭合误差 ≤5%"。该目标**不依赖真实观测数据**——
它检验的是模型自身的守恒性，无实测数据也应完成。本脚本用已产出的逐日
`system_daily.csv` 做核算，不重跑引擎。

做法：不预先假设模型的守恒恒等式，而是**尝试若干候选恒等式**，报告哪一个真正
闭合。这比强行套用一个可能错误的公式更诚实。

用法：
    PYTHONPATH=src python scripts/audit_water_balance_closure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TS = ROOT / "validation_artifacts" / "timeseries"
OUT = ROOT / "validation_artifacts" / "r2" / "water_balance_closure.csv"

TOLERANCE_PCT = 5.0


def candidate_identities(df: pd.DataFrame) -> dict[str, pd.Series | None]:
    """返回守恒恒等式的残差序列。残差应恒等于 0 表示该式成立。

    式 (1) 由 2026-09-27 对本 ha/cap_1000 产物做数值判定得出——
    `ΔS == inflow - outflow - loss` 在所有日期残差为机器精度 0，
    而漏掉 `loss_ml` 的朴素式残差达 2.8%，故 `loss_ml` 是本模型的一个独立出流项。
    """
    out: dict[str, pd.Series | None] = {}
    storage = df["storage_ml"] if "storage_ml" in df else None

    if storage is not None and {"inflow_ml", "outflow_ml", "loss_ml"} <= set(df.columns):
        # 系统节点质量守恒（实测判定为本模型的真实恒等式）
        delta = storage.diff()
        out["dStorage == inflow - outflow - loss"] = delta - (
            df["inflow_ml"] - df["outflow_ml"] - df["loss_ml"]
        )

    if {"delivered_ml", "potable_delivered_ml", "reuse_delivered_ml"} <= set(df.columns):
        # 配送拆分口径：总送达 = 自来水 + 再生水（+ 其他源，若存在）
        parts = df["potable_delivered_ml"] + df["reuse_delivered_ml"]
        if "other_delivered_ml" in df.columns:
            parts = parts + df["other_delivered_ml"]
        out["delivered == potable + reuse + other"] = df["delivered_ml"] - parts

    return out


def evaluate(df: pd.DataFrame) -> dict:
    """对每个候选式算相对闭合误差（相对同期总入流）。"""
    if len(df) < 3:
        return {}
    scale = float(df["inflow_ml"].abs().sum()) if "inflow_ml" in df else 1.0
    if scale <= 0:
        scale = 1.0
    result: dict = {}
    for name, residual in candidate_identities(df).items():
        if residual is None:
            continue
        # 跳过第一行（diff 产生 NaN）
        series = residual.iloc[1:].astype(float)
        if len(series) == 0:
            continue
        abs_sum = float(series.abs().sum())
        result[name] = {
            "rel_error_pct": abs_sum / scale * 100.0,
            "max_abs_ml": float(series.abs().max()),
        }
    return result


def main() -> int:
    if not TS.exists():
        print(f"未找到逐日产物目录：{TS}")
        return 1

    rows: list[dict] = []
    for domain_dir in sorted(p for p in TS.iterdir() if p.is_dir()):
        domain = domain_dir.name
        for cap_dir in sorted(q for q in domain_dir.iterdir() if q.is_dir()):
            path = cap_dir / "system_daily.csv"
            if not path.exists():
                continue
            try:
                df = pd.read_csv(path)
            except Exception as exc:  # noqa: BLE001
                print(f"  跳过 {path}: {exc}")
                continue
            if df.empty:
                continue
            metrics = evaluate(df)
            if not metrics:
                continue
            passed = all(v["rel_error_pct"] <= TOLERANCE_PCT for v in metrics.values())
            for name, value in metrics.items():
                rows.append(
                    {
                        "域": domain,
                        "容量点": cap_dir.name,
                        "恒等式": name,
                        "相对闭合误差_pct": round(value["rel_error_pct"], 9),
                        "最大绝对残差_ML": round(value["max_abs_ml"], 9),
                        "是否满足<=5%": "PASS" if value["rel_error_pct"] <= TOLERANCE_PCT else "FAIL",
                    }
                )
            flag = "PASS" if passed else "FAIL"
            print(f"[{domain}/{cap_dir.name}] {flag}")
            for name, value in metrics.items():
                print(f"    {name}: {value['rel_error_pct']:.3e}%")

    if not rows:
        print("未找到可核算的 system_daily.csv")
        return 1

    out_df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT, index=False, encoding="utf-8-sig")

    worst = out_df["相对闭合误差_pct"].max()
    n_fail = int((out_df["是否满足<=5%"] == "FAIL").sum())
    print(f"\nwritten -> {OUT}  ({len(out_df)} 条)")
    print(f"最大相对闭合误差 = {worst:.3e}% ；FAIL 条数 = {n_fail}")

    if worst <= TOLERANCE_PCT:
        print(f"✅ 水量闭合满足 ≤{TOLERANCE_PCT}% 验收目标（注意：这是模型内部守恒性，不代表与实测一致）")
    else:
        print(f"❌ 存在超出 {TOLERANCE_PCT}% 的闭合残差，需检查上式是否为模型真实恒等式")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
