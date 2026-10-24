# Document-Consistency Resolution (2026-10-13)

The R2 consistency audit still reports 12 mismatches in historical planning text. The machine-readable artifacts are retained as the current numerical sources; the historical plan is not rewritten in place.

| Historical claim | Document value | Current artifact value | Resolution |
|---|---:|---:|---|
| HA physical CAWCC daily max-safe | 1100 | 1150 | Superseded by `ha/capacity_threshold_corrected.json`; use artifact value for new work. |
| HA composite daily max-safe | 1100 | 1150 | Superseded by `ha/capacity_threshold_corrected.json`; use artifact value for new work. |
| HA composite annual max-safe | 1250 | 1300 | Superseded by `ha/capacity_threshold_corrected.json`; use artifact value for new work. |
| HA probabilistic physical P95 | 1150 | 1200 | Superseded by `ha/probabilistic_corrected_summary.json`; use artifact value for new work. |
| Project overview HA physical daily | 1100 | 1150 | Historical snapshot; artifact is current. |
| Project overview HA daily first-fail | 1150 | 1200 | Historical snapshot; artifact is current. |
| HA reclaimed-fraction CoC reduction | 21.59 | 22.51 | Recomputed R8 artifact is current; historical summary is retained for provenance. |
| CO reclaimed-fraction CoC reduction | 18.28 | 19.20 | Recomputed R8 artifact is current; historical summary is retained for provenance. |
| HA reclaimed-fraction withdrawal rise | 7.33 | 7.14 | Recomputed R8 artifact is current; historical summary is retained for provenance. |
| CO reclaimed-fraction withdrawal rise | 5.88 | 5.75 | Recomputed R8 artifact is current; historical summary is retained for provenance. |
| HA reclaimed-fraction sewer rise | 36.70 | 38.89 | Recomputed R8 artifact is current; historical summary is retained for provenance. |
| CO reclaimed-fraction sewer rise | 29.40 | 31.35 | Recomputed R8 artifact is current; historical summary is retained for provenance. |

This resolution does not upgrade any R10 gate. New manuscripts and experiments must cite the current artifact paths and label the old plan values as superseded. A future documentation migration may update the historical plan in a separate, versioned revision after scientific sign-off.
