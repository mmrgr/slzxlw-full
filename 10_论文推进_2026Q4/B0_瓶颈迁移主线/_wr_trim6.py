# -*- coding: utf-8 -*-
"""第六批精简：最后 ~45 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS: list[tuple[str, str]] = [
    (
        "Here we take the position of a mechanism study. Because calibration data for a real city are unavailable, we claim no city's carrying capacity and no city's threshold value. What we deliver is a criterion, the ordering and migration structure of constraints, and the conditions under which the mechanism binds. Our contributions are five.",
        "We take the position of a mechanism study. Because calibration data for a real city are unavailable, we claim no city's carrying capacity and no city's threshold value; what we deliver is a criterion, the ordering and migration structure of constraints, and the conditions under which the mechanism binds. Our contributions are five.",
    ),
    (
        "All model outputs are archived in `validation_artifacts/r2/` of the project repository: the six-estimand capacity thresholds, per-constraint first-failure tables, constraint informativeness tables, the substitution-ratio scan products, the grid-convergence runs at 50, 25 and 10 MW, the regime-map and regime-validation products, and the confound-control table. The California system-level dataset was derived from the 2022 Electronic Annual Report published by the California State Water Resources Control Board, and the Santa Clara water balance from its 2025 Urban Water Management Plan. Code for the analytic derivations and the screening calculation accompanies the archive.",
        "All model outputs are archived in `validation_artifacts/r2/` of the project repository: the six-estimand capacity thresholds, per-constraint first-failure and informativeness tables, the substitution-ratio scan products, the grid-convergence runs at 50, 25 and 10 MW, the regime-map and validation products, and the confound-control table. The California dataset derives from the 2022 Electronic Annual Report of the California State Water Resources Control Board, and the Santa Clara water balance from its 2025 Urban Water Management Plan. Code for the analytic derivations and the screening calculation accompanies the archive.",
    ),
    (
        "During the preparation of this work the authors used a large language model-based assistant for drafting, language editing and consistency checking of numerical statements against the archived model outputs. After using this tool, the authors reviewed and edited the content as needed and take full responsibility for the content of the publication.",
        "During the preparation of this work the authors used a large language model-based assistant for drafting, language editing and consistency checking of numerical statements against the archived model outputs. After using this tool the authors reviewed and edited the content as needed and take full responsibility for the publication.",
    ),
]


def main() -> None:
    text = MS.read_text(encoding="utf-8")
    applied, missed = 0, []
    for old, new in PAIRS:
        if old in text:
            text = text.replace(old, new, 1)
            applied += 1
        else:
            missed.append(old[:70])
    MS.write_text(text, encoding="utf-8")
    print(f"已替换 {applied}/{len(PAIRS)}")
    for m in missed:
        print("  未匹配:", m, "…")
    s = re.sub(r"\$[^$]*\$", " MATH ", text)
    print("当前总词数:", len(s.split()))


if __name__ == "__main__":
    main()
