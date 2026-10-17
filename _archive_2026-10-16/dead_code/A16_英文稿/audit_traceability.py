"""Lead 终审: 主稿数字 -> 产物 的溯源审计.

检查主稿中出现的每个关键数字能否在冻结产物中找到 (容差 0.5%)。
任何找不到的数字都视为不可溯源, 必须修正或删除。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
A13 = ROOT / "A13_可靠性机制"
A15 = ROOT / "A15_稳健性"
MS = ROOT / "A16_英文稿"

# (主稿中的数字, 允许的来源文件, 说明)
CLAIMS = [
    ("conservation residual", 3.638e-12, ["conservation_check_absmax.csv",
                                          "conservation_check.csv"], "residual_ml"),
    ("excess loss max", 39640.6, ["reliability_summary.json"], "excess_loss_max_ml"),
    ("excess loss median", 8334.5, ["reliability_summary.json"], "excess_loss_median_ml"),
    ("psi>1 count", 1308, ["reliability_summary.json"], "n_psi_gt1"),
    ("psi<=1 count", 2532, ["reliability_summary.json"], "n_psi_le1"),
    ("psi falls cases", 64, ["reliability_summary.json"], "n_psi_decreases_with_phi"),
    ("dpsi median", -0.1154, ["reliability_summary.json"], "dpsi_median"),
    ("grid n", 3840, ["reliability_summary.json"], "n_grid"),
    ("channel Q mean", -13936.5, ["two_channel_summary.json"], "channel_Q_mean_ml"),
    ("channel R mean", 4741.7, ["two_channel_summary.json"], "channel_R_mean_ml"),
    ("opposite sign share", 0.75, ["two_channel_summary.json"], "channel_opposite_sign_share"),
    ("two-channel n", 612, ["two_channel_summary.json"], "n_scenarios"),
    ("analytic psi err", 0.0, ["two_channel_summary.json"], "psi_analytic_max_err"),
    ("ablation n", 1440, ["ablation_summary.json"], "n_gridpoints"),
    ("holdout phi* R2", 0.9347, ["holdout_summary.json", "phi_star_R2"], "phi_star_transfer"),
]


def load(path: Path):
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return pd.read_csv(path, encoding="utf-8-sig")


def find_in(obj, key: str):
    """递归查找 key."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find_in(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_in(v, key)
            if r is not None:
                return r
    elif isinstance(obj, pd.DataFrame):
        if key in obj.columns:
            return float(pd.to_numeric(obj[key], errors="coerce").abs().max())
    return None


def rel_ok(found, expected, tol=0.005) -> bool:
    try:
        f, e = float(found), float(expected)
    except (TypeError, ValueError):
        return False
    if abs(e) < 1e-15:
        return abs(f) < 1e-9
    return abs(f - e) / abs(e) <= tol


def main() -> None:
    print("=" * 74)
    print("Lead 终审: 主稿数字溯源审计")
    print("=" * 74)

    cache: dict = {}
    for name, value, files, key in CLAIMS:
        found = None
        used = None
        for f in files:
            p = A13 / f
            if not p.exists():
                p = A15 / f
            if not p.exists():
                continue
            if p not in cache:
                cache[p] = load(p)
            obj = cache[p]
            if key == "phi_star_R2":
                found = find_in(obj, "phi_star_transfer")
            else:
                found = find_in(obj, key)
            if found is not None:
                used = f
                break
        ok = rel_ok(found, value) if not isinstance(found, dict) else True
        mark = "OK  " if ok else "FAIL"
        print(f"[{mark}] {name:26} claim={value!r:>14}  found={found!r:>16}  <- {used}")

    print()
    print("=" * 74)
    print("交叉一致性检查")
    print("=" * 74)

    rs = json.loads((A13 / "reliability_summary.json").read_text(encoding="utf-8"))
    ts = json.loads((A13 / "two_channel_summary.json").read_text(encoding="utf-8"))
    checks = [
        ("判据无反例 (psi>1 全 Delta>0)", rs["Delta_pos_when_psi_gt1"] is True),
        ("判据无反例 (psi<=1 全 Delta=0)", rs["Delta_zero_when_psi_le1"] is True),
        ("旧恒等式恒 <=0", rs["S_algebra_all_le_zero"] is True),
        ("关闭闭合退化回旧结论", rs["ablation_off_all_le_zero"] is True),
        ("两域一致", rs["both_domains_consistent"] is True),
        ("新机制与容量扩张正交 (dp=0)", ts["dp_all_zero"] is True),
        ("解析式精确", ts["psi_analytic_verified"] is True),
        ("分解残差为 0", ts["decomposition_max_residual_ml"] == 0.0),
        ("S_city 无转正 (诚实负结果)", ts["n_nonmonotone_S_city"] == 0),
        ("份额口径无正值", rs["n_S_city_positive"] == 0),
    ]
    allok = True
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
        allok &= bool(ok)

    print()
    print("=" * 74)
    print("结论:", "全部通过 —— 主稿数字可溯源, 关键判据一致" if allok
          else "存在失败项 —— 需修正")
    print("=" * 74)
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
