"""Run an independent PHREEQC saturation diagnostic for supplied water samples.

This is an evidence-producing pilot utility, not a gate switch. The output is
``PILOT_ONLY`` unless a future review replaces the input manifest with a
complete, provenance-reviewed PASS record. It requires the optional
``phreeqpython`` dependency (``pip install .[chemistry]``).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED = (
    "sample_id", "pH", "temperature_c", "Ca_mg_l", "Mg_mg_l", "Na_mg_l",
    "Cl_mg_l", "SO4_mg_l", "alkalinity_mg_l_as_CaCO3", "Si_mg_l",
)
PHASES = ("Calcite", "Dolomite", "Gypsum", "Anhydrite")
# These are the frozen reduced-order limits used by the main model.  They are
# deliberately read-only here: this pilot compares against the registered
# limits and must not tune them to the PHREEQC outputs.
REDUCED_ORDER_LIMITS = {"TDS": 2200.0, "chloride": 500.0}
REDUCED_ORDER_UPPER = 100.0


def _charge_balance_error_pct(row: dict[str, str]) -> float | None:
    """Estimate major-ion charge closure for the supplied screening fields.

    Potassium, nitrate and other minor ions are not required by this pilot, so
    this is a quality diagnostic rather than a charge-balanced PHREEQC input
    guarantee.  Keeping it explicit prevents an incomplete ion panel from
    being mistaken for a full analytical balance.
    """
    try:
        cations = (
            2.0 * float(row["Ca_mg_l"]) / 40.078
            + 2.0 * float(row["Mg_mg_l"]) / 24.305
            + float(row["Na_mg_l"]) / 22.98977
        )
        anions = (
            float(row["Cl_mg_l"]) / 35.453
            + 2.0 * float(row["SO4_mg_l"]) / 96.06
            + float(row["alkalinity_mg_l_as_CaCO3"]) / 50.043
        )
    except (KeyError, TypeError, ValueError):
        return None
    denominator = max(cations, anions)
    if denominator <= 0.0 or not math.isfinite(denominator):
        return None
    error = 100.0 * abs(cations - anions) / denominator
    return float(error) if math.isfinite(error) else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _number(row: dict[str, str], name: str) -> float:
    try:
        value = float(row[name])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def _solution(pp: Any, row: dict[str, str], multiplier: float = 1.0) -> Any:
    scale = float(multiplier)
    composition = {
        "-units": "mg/L",
        "-temp": str(_number(row, "temperature_c")),
        "pH": str(float(row["pH"])),
        "Ca": str(_number(row, "Ca_mg_l") * scale),
        "Mg": str(_number(row, "Mg_mg_l") * scale),
        "Na": str(_number(row, "Na_mg_l") * scale),
        "Cl": str(_number(row, "Cl_mg_l") * scale),
        "S(6)": f"{_number(row, 'SO4_mg_l') * scale} as SO4",
        "Alkalinity": f"{_number(row, 'alkalinity_mg_l_as_CaCO3') * scale} as CaCO3",
        "Si": str(_number(row, "Si_mg_l") * scale),
    }
    return pp.add_solution(composition)


def _safe_multiplier(pp: Any, row: dict[str, str], *, upper: float = 100.0) -> float:
    """Return the largest grid-refined multiplier with all target SI <= 0."""
    def safe(multiplier: float) -> bool:
        solution = _solution(pp, row, multiplier)
        return all(float(solution.phases.get(phase, float("nan"))) <= 0.0 for phase in PHASES)

    if not safe(1.0):
        return 0.0
    if safe(upper):
        return upper
    left, right = 1.0, upper
    for _ in range(36):
        middle = (left + right) / 2.0
        if safe(middle):
            left = middle
        else:
            right = middle
    return left


def _reduced_order_metrics(
    row: dict[str, str], *, limits: dict[str, float] | None = None,
    upper: float = REDUCED_ORDER_UPPER,
) -> dict[str, Any] | None:
    """Return the frozen linear concentration-screen metrics for one sample.

    The production reduced model treats each quality indicator as a linear
    concentration accumulator and uses the smallest limit/concentration
    ratio.  This pilot requires a *measured* ``tds_mg_l`` field; it never
    substitutes a major-ion sum for TDS.  The resulting multiplier is a
    screening comparator, not a chemical equilibrium prediction.
    """
    limits = limits or REDUCED_ORDER_LIMITS
    try:
        concentrations = {
            "TDS": _number(row, "tds_mg_l"),
            "chloride": _number(row, "Cl_mg_l"),
        }
    except (KeyError, ValueError):
        return None
    ratios = {
        indicator: float(limit) / concentrations[indicator]
        for indicator, limit in limits.items()
        if concentrations.get(indicator, 0.0) > 0.0
    }
    if len(ratios) != len(limits):
        return None
    raw = min(ratios.values())
    limiting = min(ratios, key=ratios.get)
    return {
        "reduced_order_coc": float(min(upper, max(0.0, raw))),
        "reduced_order_raw_coc": float(raw),
        "reduced_order_limiting_species": limiting,
        "reduced_order_safe_at_one": bool(raw >= 1.0),
        "reduced_order_thresholds_mg_l": dict(limits),
        "reduced_order_tds_mg_l": concentrations["TDS"],
        "reduced_order_chloride_mg_l": concentrations["chloride"],
        "reduced_order_upper_censored": bool(raw > upper),
    }


def _average_ranks(values: list[float]) -> list[float]:
    """Return one-based ascending ranks with deterministic average ties."""
    order = sorted(range(len(values)), key=lambda index: (values[index], index))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        value = values[order[cursor]]
        while end < len(order) and values[order[end]] == value:
            end += 1
        rank = (cursor + 1 + end) / 2.0
        for position in order[cursor:end]:
            ranks[position] = rank
        cursor = end
    return ranks


def _spearman(values_a: list[float], values_b: list[float]) -> float | None:
    if len(values_a) != len(values_b) or len(values_a) < 2:
        return None
    first = _average_ranks(values_a)
    second = _average_ranks(values_b)
    mean_first = sum(first) / len(first)
    mean_second = sum(second) / len(second)
    numerator = sum((a - mean_first) * (b - mean_second) for a, b in zip(first, second))
    denominator_a = sum((a - mean_first) ** 2 for a in first)
    denominator_b = sum((b - mean_second) ** 2 for b in second)
    denominator = math.sqrt(denominator_a * denominator_b)
    return None if denominator == 0.0 else float(numerator / denominator)


def run(samples: Path, output: Path) -> dict[str, Any]:
    try:
        from phreeqpython import PhreeqPython
        import phreeqpython
    except ImportError as exc:
        raise RuntimeError("phreeqpython is required; install the optional chemistry dependency") from exc

    database_path = Path(phreeqpython.__file__).resolve().parent / "database" / "vitens.dat"
    if not database_path.exists():
        raise FileNotFoundError(f"PHREEQC database not found: {database_path}")
    pp = PhreeqPython(database="vitens.dat")
    results: list[dict[str, Any]] = []
    with samples.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not set(REQUIRED).issubset(reader.fieldnames):
            raise ValueError(f"sample CSV must contain: {', '.join(REQUIRED)}")
        rows = list(reader)
    if not rows:
        raise ValueError("sample CSV is empty")
    comparable: list[dict[str, Any]] = []
    for row in rows:
        sample_id = str(row["sample_id"]).strip()
        if not sample_id:
            raise ValueError("sample_id must be non-empty")
        solution = _solution(pp, row)
        saturation = {phase: float(solution.phases.get(phase, float("nan"))) for phase in PHASES}
        safe_multiplier = _safe_multiplier(pp, row)
        result = {
            "sample_id": sample_id,
            "source_provenance": row.get("source_provenance", "unspecified"),
            "observed_flag": row.get("observed_flag", "false").strip().lower() == "true",
            "pH": float(solution.pH),
            "saturation_index": saturation,
            "limiting_phase": max(saturation, key=lambda name: saturation[name] if math.isfinite(saturation[name]) else -math.inf),
            "safe_concentration_multiplier": safe_multiplier,
            # Aliases use the terminology frozen in the G2 protocol while
            # retaining the original pilot field for backwards compatibility.
            "phreeqc_coc": safe_multiplier,
            "phreeqc_safe_at_one": bool(safe_multiplier >= 1.0),
        }
        charge_balance = _charge_balance_error_pct(row)
        if charge_balance is not None:
            result["major_ion_charge_balance_error_pct"] = charge_balance
        reduced = _reduced_order_metrics(row)
        if reduced is not None:
            result.update(reduced)
            result["limiting_species"] = result["limiting_phase"]
            result["coc_delta"] = float(reduced["reduced_order_coc"] - safe_multiplier)
            comparable.append(result)
        results.append(result)
    comparison_complete = len(comparable) == len(results)
    comparison: dict[str, Any]
    if comparison_complete:
        reduced_values = [float(item["reduced_order_coc"]) for item in comparable]
        phreeqc_values = [float(item["phreeqc_coc"]) for item in comparable]
        reduced_ranks = _average_ranks(reduced_values)
        phreeqc_ranks = _average_ranks(phreeqc_values)
        false_safe = sum(
            bool(item["reduced_order_safe_at_one"]) and not bool(item["phreeqc_safe_at_one"])
            for item in comparable
        )
        false_unsafe = sum(
            not bool(item["reduced_order_safe_at_one"]) and bool(item["phreeqc_safe_at_one"])
            for item in comparable
        )
        for item, reduced_rank, phreeqc_rank in zip(comparable, reduced_ranks, phreeqc_ranks):
            item["reduced_order_rank"] = reduced_rank
            item["phreeqc_rank"] = phreeqc_rank
        comparison = {
            "status": "CONDITIONAL_PILOT",
            "sample_count": len(comparable),
            "comparison_scope": "same_sample_ambient_screening",
            "safe_definition": "reduced order: all registered limits at COC=1; PHREEQC: all target phase SI <= 0 at concentration multiplier 1",
            "assumptions": [
                "TDS is the direct WQP 70300 measurement; no ion-sum substitute is used.",
                "Reduced order assumes linear concentration accumulation and no precipitation, complexation, or pH shift.",
                "Both safe-multiplier series are capped at 100 for the diagnostic; raw reduced ratios remain available.",
                "The comparison is conditional on the registered 2200 mg/L TDS and 500 mg/L chloride engineering limits.",
            ],
            "thresholds_mg_l": dict(REDUCED_ORDER_LIMITS),
            "reduced_order_coc_definition": "min(TDS_limit/TDS, chloride_limit/chloride)",
            "phreeqc_coc_definition": "largest tested concentration multiplier with Calcite, Dolomite, Gypsum, and Anhydrite SI <= 0",
            "rank_direction": "ascending safe multiplier; rank 1 is most constrained",
            "rank_spearman": _spearman(reduced_values, phreeqc_values),
            "false_safe_count": int(false_safe),
            "false_safe_rate": float(false_safe / len(comparable)),
            "false_unsafe_count": int(false_unsafe),
            "false_unsafe_rate": float(false_unsafe / len(comparable)),
        }
    else:
        comparison = {
            "status": "NOT_AVAILABLE",
            "sample_count": len(comparable),
            "required_fields": ["tds_mg_l", "Cl_mg_l"],
            "reason": "A direct measured TDS field is required; no partial false-safe rate is reported.",
        }
    charge_values = [
        float(item["major_ion_charge_balance_error_pct"])
        for item in results
        if "major_ion_charge_balance_error_pct" in item
    ]
    quality: dict[str, Any] = {
        "charge_balance_definition": "100*abs(sum_cation_meq_l-sum_anion_meq_l)/max(sum_cation_meq_l,sum_anion_meq_l); K, nitrate and minor ions omitted",
        "charge_balance_sample_count": len(charge_values),
        "charge_balance_missing_count": len(results) - len(charge_values),
        "charge_balance_max_error_pct": max(charge_values) if charge_values else None,
        "charge_balance_median_error_pct": sorted(charge_values)[len(charge_values) // 2] if charge_values else None,
        "charge_balance_review_flag": bool(charge_values) and max(charge_values) > 20.0,
        "interpretation": "screening diagnostic only; incomplete ion panels remain unsuitable for a formal G2 PASS",
    }
    database_hash = _sha256(database_path)
    payload = {
        "kind": "G2_PHREEQC_CROSSCHECK",
        "status": "PILOT_ONLY",
        "gate": "G2",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "sample_count": len(rows),
        "independent_solver": {"name": "IPhreeqc via phreeqpython", "database": "vitens.dat", "database_hash": database_hash},
        "input": {"path": str(samples.resolve()), "sha256": _sha256(samples), "sample_count": len(rows)},
        "sample_level_outputs": results,
        # Alias retained for the frozen gate auditor's PASS-manifest schema.
        "per_sample_outputs": results,
        "sample_level_crosscheck": bool(comparison_complete),
        "comparison": comparison,
        "input_quality": quality,
        # Keep the legacy top-level field for the gate auditor.  It is only
        # populated when every input row has a complete, directly measured
        # reduced-order comparison.
        "false_safe_rate": comparison.get("false_safe_rate"),
        "false_unsafe_rate": comparison.get("false_unsafe_rate"),
        "gate_effect": "G2 remains NOT_READY: this is a conditional ambient pilot; reclaimed-water provenance, independent review, and frozen PASS criteria are still outstanding.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args.samples.resolve(), args.output.resolve())
    print(json.dumps({"output": str(args.output.resolve()), "status": payload["status"], "sample_count": payload["input"]["sample_count"], "gate_effect": payload["gate_effect"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
