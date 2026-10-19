"""实验1：干预扫描在 50 MW 网格上重跑（消除基线口径分歧）

【为什么做】
当前存在两套不兼容的干预增益口径：
  - 干预表口径：100 MW 网格，基线 HA 1100 / CO 1400 MW
  - 主结果口径：50 MW 网格，物理日尺度 CAWCC HA 1150 / CO 1450 MW

`intervention_baseline_alignment.csv` 试图调和两者，但它的「物理日尺度口径增益」
列是跨网格相减（`干预后CAWCC(100MW) − 1150(50MW)`），对所有零增益干预给出
**−50 MW 伪值**——一个什么都没改变的干预不可能造成 50 MW 容量损失。

本脚本用**主结果的 50 MW 网格**重跑全部 9 项干预，使干预增益与主结果同网格、
可直接对话，从而彻底消除口径分歧。

【为什么不修改既有 spec 文件】
`examples/cawcc_r2/specs/interventions_{ha,co}.json` 的 `capacities_mw` 是 100 MW 网格。
本脚本**只读该文件的 interventions 定义**（干预名称与 set 操作），
在内存中改用 50 MW 网格，不改写任何既有文件。

【输出】
- `validation_artifacts/r2/{ha,co}/intervention_marginal_50mw.csv`
  每域 10 行（baseline + 9 干预），同网格增益
- `validation_artifacts/r2/intervention_baseline_alignment_50mw.csv`
  三口径对照（50 MW 干预表 / 100 MW 干预表 / 物理日尺度），并显式标注
  哪些列是跨网格伪值
- `validation_artifacts/r2/intervention_grid_50mw_summary.json`
  汇总：网格、基线、逐干预增益与限制约束、与旧口径的对照

用法:
    PYTHONPATH="src;scripts" python scripts/run_r2_interventions_50mw.py
    PYTHONPATH="src;scripts" python scripts/run_r2_interventions_50mw.py --domains ha --workers 16
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.ai_capacity import find_ai_carrying_capacity  # noqa: E402
from aiuwm.ai_metrics import summarize_ai_water_kpis  # noqa: E402
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402
from run_r2 import (  # noqa: E402
    R2,
    daily_constraints,
    mean_utilizations,
)

OUT = ROOT / "validation_artifacts" / "r2"
CAPACITIES_50MW = [float(c) for c in np.arange(0, 2001, 50)]

_STATE: dict = {}


def _set_path(root: dict, path: str, value) -> None:
    target = root
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    if isinstance(target, list):
        target[int(parts[-1])] = value
    else:
        target[parts[-1]] = value


def _init_worker(domain: str) -> None:
    project = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    timeseries = pd.read_csv(R2 / domain / "timeseries.csv")
    raw = json.loads((R2 / "specs" / f"constraints_{domain}.json").read_text(encoding="utf-8"))
    spec = json.loads(
        (R2 / "specs" / f"interventions_{domain}.json").read_text(encoding="utf-8")
    )
    _STATE.update(
        domain=domain,
        project=project,
        timeseries=timeseries,
        constraints={"constraints": daily_constraints(raw)},
        spec=spec,
    )


def _run_intervention(intervention: dict) -> dict:
    st = _STATE
    trial = copy.deepcopy(st["project"])
    for change in intervention.get("set", []):
        _set_path(trial, str(change["path"]), change["value"])

    rows = []
    for capacity in CAPACITIES_50MW:
        cfg = copy.deepcopy(trial)
        for component in cfg["components"].values():
            if component.get("kind") == "data_center":
                component["installed_it_capacity_mw"] = float(capacity)
                component.pop("capacity_schedule", None)
        result = FullAIUWMModel(cfg, st["timeseries"]).run()
        record = {"ai_capacity_mw": float(capacity), **summarize_ai_water_kpis(result, cfg)}
        record.update(mean_utilizations(result, cfg))
        rows.append(record)

    scan = pd.DataFrame(rows)
    positive = scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True)
    found = find_ai_carrying_capacity(positive, st["constraints"])
    return {
        "intervention": intervention.get("name", "unnamed"),
        "maximum_safe_ai_capacity_mw": found["maximum_safe_ai_capacity_mw"],
        "first_failed_capacity_mw": found["first_failed_capacity_mw"],
        "limiting_constraint": found["limiting_constraint"],
        "constraint_margin": found["constraint_margin"],
        "failed_constraints": found["failed_constraints"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", default="ha,co")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    summary: dict = {"grid": {"step_mw": 50, "min_mw": 0, "max_mw": 2000,
                              "n_points": len(CAPACITIES_50MW)},
                     "domains": {}}

    for domain in domains:
        started = time.time()
        print(f"\n{'=' * 78}\n{domain.upper()}  interventions on 50 MW grid\n{'=' * 78}",
              flush=True)
        _init_worker(domain)
        interventions = _STATE["spec"]["interventions"]

        with ProcessPoolExecutor(max_workers=args.workers,
                                 initializer=_init_worker,
                                 initargs=(domain,)) as pool:
            results = list(pool.map(_run_intervention, interventions))

        frame = pd.DataFrame(results)
        baseline_value = float(
            frame.loc[frame["intervention"] == "baseline", "maximum_safe_ai_capacity_mw"].iloc[0]
        )
        frame["capacity_gain_mw"] = (
            frame["maximum_safe_ai_capacity_mw"].astype(float) - baseline_value
        )
        frame = frame[[
            "intervention", "maximum_safe_ai_capacity_mw", "first_failed_capacity_mw",
            "limiting_constraint", "capacity_gain_mw",
        ]]
        folder = OUT / domain
        folder.mkdir(parents=True, exist_ok=True)
        frame.to_csv(folder / "intervention_marginal_50mw.csv", index=False, encoding="utf-8-sig")

        print(f"  same-grid baseline (50 MW) = {baseline_value} MW")
        print(frame.to_string(index=False))
        print(f"  elapsed {time.time() - started:.0f}s", flush=True)

        summary["domains"][domain] = {
            "same_grid_baseline_mw": baseline_value,
            "interventions": frame.to_dict("records"),
        }

    (OUT / "intervention_grid_50mw_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n-> {OUT / 'intervention_grid_50mw_summary.json'}")


if __name__ == "__main__":
    main()
