"""Add an exact-binomial upper bound to the probabilistic summaries.

Background / why this exists
----------------------------
The 1024-sample batches report ``exceedance_probability`` (the share of draws
whose estimated capacity falls below the proposed 1000 MW).  For CO the
observed count is 0/1024, and the bootstrap interval for a zero count collapses
to ``[0.0, 0.0]``.  A bootstrap interval computed on a degenerate proportion is
*not* a risk statement: it only reflects the within-batch resampling of a
sample in which the event never occurred.  Reading ``[0, 0]`` as "risk is zero"
is a statistical error.

The honest statement for a zero count is:

    "0 exceedances were observed in n draws; the one-sided exact (Clopper-
     Pearson) 95% upper bound on the exceedance probability is X%."

This script recomputes, from the existing ``probabilistic_corrected.csv``
artifacts (no re-simulation), the following fields and writes them back into
each ``probabilistic_corrected_summary.json``:

- ``exceedance_count`` / ``exceedance_n`` — the raw count and denominator
- ``exceedance_probability_exact_ci95`` — Clopper-Pearson two-sided interval
- ``exceedance_probability_exact_upper95`` — one-sided upper bound (the number
  to quote when the count is zero)
- ``exceedance_probability_interpretation`` — a Chinese-language sentence that
  the narrative documents can quote verbatim

The same treatment is applied to the policy-threshold exceedance, which is also
0/n for both domains.

Clopper-Pearson is computed without SciPy: the upper bound for a zero count is
``1 - (alpha/2)**(1/n)`` and the general case uses the Beta quantile inverted
via ``scipy`` if available, otherwise a bisection on the regularized incomplete
beta function implemented here.

Usage::

    python scripts/add_exact_binomial_bound.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "validation_artifacts" / "r2"

ALPHA = 0.05


# --------------------------------------------------------------------------- #
# Regularized incomplete beta function and its inverse (no SciPy dependency). #
# --------------------------------------------------------------------------- #
def _betacf(a: float, b: float, x: float, max_iter: int = 200, eps: float = 3e-16) -> float:
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + b * math.log1p(-x)
        + a * math.log(x)
    ) * _betacf(b, a, 1.0 - x) / b


def beta_ppf(p: float, a: float, b: float) -> float:
    """Inverse regularized incomplete beta via bisection on [0, 1]."""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _betainc(a, b, mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def clopper_pearson(k: int, n: int, alpha: float = ALPHA) -> tuple[float, float]:
    """Two-sided Clopper-Pearson interval for k successes in n trials."""
    if n <= 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else beta_ppf(alpha / 2.0, k, n - k + 1)
    hi = 1.0 if k == n else beta_ppf(1.0 - alpha / 2.0, k + 1, n - k)
    return (float(lo), float(hi))


def one_sided_upper95(k: int, n: int, alpha: float = ALPHA) -> float:
    """One-sided exact 95% upper bound on the probability.

    For k == 0 this reduces to ``1 - alpha**(1/n)``; for the general case it is
    the ``1 - alpha`` quantile of ``Beta(k+1, n-k)``.
    """
    if n <= 0:
        return float("nan")
    if k == 0:
        return float(1.0 - alpha ** (1.0 / n))
    return float(beta_ppf(1.0 - alpha, k + 1, n - k))


# --------------------------------------------------------------------------- #
# Rewrite the summaries.                                                      #
# --------------------------------------------------------------------------- #
def _interpretation(count: int, n: int, upper: float, proposed: float) -> str:
    pct = 100.0 * upper
    if count == 0:
        return (
            f"在 {n} 次抽样中观察到 0 次越过 {proposed:.0f} MW 的容量不足；"
            f"bootstrap 区间退化为 [0, 0] 不等于风险为零——"
            f"精确二项（Clopper-Pearson）单侧 95% 上界为 {pct:.2f}%，"
            f"这才是可引用的检出限。"
        )
    return (
        f"在 {n} 次抽样中观察到 {count} 次越过 {proposed:.0f} MW 的容量不足"
        f"（点估计 {count / n:.4f}）；精确二项单侧 95% 上界为 {pct:.2f}%。"
    )


def _augment(block: dict, series: np.ndarray, proposed: float, prefix: str = "") -> None:
    """Attach exact-binomial fields to a summary block in place."""
    n = int(len(series))
    count = int((series < proposed).sum())
    lo, hi = clopper_pearson(count, n)
    upper = one_sided_upper95(count, n)
    block["exceedance_count"] = count
    block["exceedance_n"] = n
    block["exceedance_probability_exact_ci95"] = [lo, hi]
    block["exceedance_probability_exact_upper95"] = upper
    if prefix:
        block["exceedance_note"] = prefix
    block["exceedance_interpretation"] = _interpretation(count, n, upper, proposed)


def main() -> None:
    for domain in ("ha", "co"):
        csv_path = R2 / domain / "probabilistic_corrected.csv"
        summary_path = R2 / domain / "probabilistic_corrected_summary.json"
        if not csv_path.exists() or not summary_path.exists():
            print(f"[{domain}] 缺少产物，跳过")
            continue

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        proposed = float(summary.get("proposed_mw", 1000.0))

        frame = pd.read_csv(csv_path)
        series = pd.to_numeric(
            frame["maximum_safe_ai_capacity_mw"], errors="coerce"
        ).dropna().to_numpy()

        _augment(summary, series, proposed)

        pol = summary.get("policy_threshold")
        pol_series = pd.to_numeric(
            frame.get("policy_maximum_safe_ai_capacity_mw", pd.Series(dtype=float)),
            errors="coerce",
        ).dropna().to_numpy()
        if isinstance(pol, dict) and len(pol_series):
            n = int(len(pol_series))
            count = int((pol_series < proposed).sum())
            lo, hi = clopper_pearson(count, n)
            upper = one_sided_upper95(count, n)
            pol["exceedance_count_at_proposed_mw"] = count
            pol["exceedance_n_at_proposed_mw"] = n
            pol["exceedance_probability_exact_ci95_at_proposed_mw"] = [lo, hi]
            pol["exceedance_probability_exact_upper95_at_proposed_mw"] = upper
            pol["exceedance_interpretation_at_proposed_mw"] = _interpretation(
                count, n, upper, proposed
            )

        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            f"[{domain}] n={len(series)} 超限计数={summary['exceedance_count']} "
            f"精确95%上界={summary['exceedance_probability_exact_upper95']:.5f} "
            f"-> {summary_path.name}"
        )


if __name__ == "__main__":
    main()
