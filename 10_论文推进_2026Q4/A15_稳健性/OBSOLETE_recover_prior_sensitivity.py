"""从 prior_sensitivity.log 恢复结果并生成 CSV/JSON 产物.

背景: prior_sensitivity.py 完成全部 9 组先验组合的**计算与打印**后,
在写盘阶段被中断 (进程退出, 未生成 CSV/JSON)。
9 组结果完整保存在 prior_sensitivity.log 中, 本脚本从中恢复,
不重跑昂贵的 25 分钟计算, 不改动任何数值.

用法: python recover_prior_sensitivity.py
产出: prior_sensitivity_recovered.csv, prior_bounds_recovered.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
LOG = HERE / "prior_sensitivity.log"

PATTERN = re.compile(
    r"^\s*(\S+)\s+x\s+(\S+)\s+x\s+dp:(\S+)\s*\|\s*"
    r"n=\s*(\d+)\s*\|\s*"
    r"P\(dp0\)=([\d.]+)\s*P\(dp1\)=([\d.]+)\s*P\(d\*<=1\)=([\d.]+)"
)


def main() -> None:
    text = LOG.read_text(encoding="utf-8", errors="replace")
    rows = []
    for line in text.splitlines():
        m = PATTERN.match(line)
        if m:
            rows.append({
                "pool_prior": m.group(1), "gap_prior": m.group(2),
                "dp_prior": m.group(3), "n_effective": int(m.group(4)),
                "P_gt0_dpA_dp0": float(m.group(5)),
                "P_gt0_dpB_dp1": float(m.group(6)),
                "P_reach_dp_le1": float(m.group(7)),
            })
    if not rows:
        raise SystemExit("未能从日志解析出任何结果 —— 请检查 prior_sensitivity.log")

    df = pd.DataFrame(rows)
    df.to_csv(HERE / "prior_sensitivity_recovered.csv", index=False, encoding="utf-8-sig")

    def span(col: str) -> dict:
        v = pd.to_numeric(df[col], errors="coerce")
        return {"min": float(v.min()), "max": float(v.max()),
                "median": float(v.median()), "span": float(v.max() - v.min()),
                "n": int(len(v))}

    # dp 先验的边际效应
    by_dp = {p: {"P_gt0_dpB_dp1": [float(df[df.dp_prior == p].P_gt0_dpB_dp1.min()),
                                   float(df[df.dp_prior == p].P_gt0_dpB_dp1.max())],
                 "n": int((df.dp_prior == p).sum())}
             for p in sorted(df.dp_prior.unique())}
    by_pool = {p: {"P_gt0_dpB_dp1": [float(df[df.pool_prior == p].P_gt0_dpB_dp1.min()),
                                     float(df[df.pool_prior == p].P_gt0_dpB_dp1.max())],
                   "n": int((df.pool_prior == p).sum())}
               for p in sorted(df.pool_prior.unique())}
    by_gap = {p: {"P_gt0_dpB_dp1": [float(df[df.gap_prior == p].P_gt0_dpB_dp1.min()),
                                    float(df[df.gap_prior == p].P_gt0_dpB_dp1.max())],
                  "n": int((df.gap_prior == p).sum())}
              for p in sorted(df.gap_prior.unique())}

    out = {
        "source": "recovered from prior_sensitivity.log (script interrupted at write stage)",
        "n_combinations": int(len(df)),
        "n_samples_per_combination": int(df.n_effective.iloc[0]),
        "P_gt0_dp0_share_only": span("P_gt0_dpA_dp0"),
        "P_gt0_dp1_capacity_inclusive": span("P_gt0_dpB_dp1"),
        "P_reach_dp_le1": span("P_reach_dp_le1"),
        "by_dp_prior": by_dp,
        "by_pool_prior": by_pool,
        "by_gap_prior": by_gap,
        "reading": (
            "在份额口径 (dp=0) 下 P(S_city>0) 在**全部 9 组先验**下均为 0 或浮点残差量级 "
            "(0.0000-0.0033), 即'数值零'。在含容量扩张口径 (dp=1) 下, "
            "P(S_city>0) 的 9 组范围为 {min:.4f}-{max:.4f}, 中位 {median:.4f}, 跨度 {span:.4f}。"
            "即**头条数字 0.62 对先验显著敏感**: 换 pool 先验为 log-uniform 会把它压到 ~0.45-0.48, "
            "而 triangular pool 先验会把它抬到 ~0.66-0.71。趋势 (dp=0 时≈0, dp>=0.5 后进入平台) 稳健, "
            "但**绝对水平不可移植**。正文必须写成'在均匀先验下', 且不得当作现实获益概率。"
        ).format(**span("P_gt0_dpB_dp1")),
        "discipline_note": (
            "本表为**给定先验与情景下的模型概率**, 不是真实城市事件频率。"
            "由日志恢复, 数值未经重算; 与原脚本输出口径一致。"),
        "per_combination": df.to_dict(orient="records"),
    }
    (HERE / "prior_bounds_recovered.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"恢复 {len(df)} 组先验组合")
    print("P(dp=0, 份额口径):", out["P_gt0_dp0_share_only"])
    print("P(dp=1, 含容量扩张):", out["P_gt0_dp1_capacity_inclusive"])
    print("按 pool 先验:")
    for k, v in by_pool.items():
        print("   ", k, v)


if __name__ == "__main__":
    main()
