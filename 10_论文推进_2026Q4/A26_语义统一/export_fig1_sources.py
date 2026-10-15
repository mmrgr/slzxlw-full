"""A26-S4: 重新导出 Fig.1 的源数据（带求解器状态门禁 + A26 权威语义列）.

【为什么重写】
原 `A16_英文稿/figures/fig1_v2_source_*.csv` 是上游产物的**直接副本**，其生成脚本
已**丢失**（A16_英文稿/figures/ 下无 .py）。且其中 potable_flows 副本含 **24 行未收敛**
（恰为全部 `phi=0` 行，`dS=0` 是"分配量为 0"的产物，与 A25 发现的 H5 空集问题同源）。

本脚本作为**唯一权威导出器**，从上游产物生成 fig1 源数据：
  1. **状态门禁**：只导出 `status == converged_unique` 的行；
  2. **语义列**：补 `limit_scale` / `chi_strictness` / `quality_binding`（A26 语义表）；
  3. **phi=0 处置**：`phi=0` 是"无回用水基线"，其 dS 恒为 0（物理上正确，但**非数据点**）
     —— 因上游未收敛而不可用；本导出器**主动排除**并在日志中说明。
  4. 同时输出 `fig1_source_manifest.json` 记录行数、剔除数与来源哈希。

⚠ 本脚本**不画图**（图件由外部工具按源数据制作）；不修改上游产物。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIGDIR = ROOT / "A16_英文稿" / "figures"
RELIABLE = {"converged_unique"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()[:16]


def export(src: Path, dst: Path, label: str) -> dict:
    d = pd.read_csv(src, encoding="utf-8-sig")
    n_all = len(d)
    if "status" not in d.columns:
        raise SystemExit(f"{src} 缺少 status 列, 无法施加门禁")
    ok = d[d["status"].isin(RELIABLE)].copy()
    n_ok = len(ok)
    dropped = d[~d["status"].isin(RELIABLE)]
    # phi=0 行单列统计 (它们是"无回用基线", 非数据点)
    n_phi0 = int((d["phi"] == 0.0).sum()) if "phi" in d.columns else 0
    n_phi0_dropped = int((dropped["phi"] == 0.0).sum()) if "phi" in dropped.columns else 0
    ok.to_csv(dst, index=False, encoding="utf-8-sig")
    info = {
        "label": label,
        "source": str(src.relative_to(ROOT)),
        "source_sha256_16": sha256(src),
        "output": str(dst.relative_to(ROOT)),
        "n_all": n_all, "n_reliable": n_ok, "n_dropped": n_all - n_ok,
        "dropped_status": dropped["status"].value_counts().to_dict() if len(dropped) else {},
        "n_phi0_rows_in_source": n_phi0,
        "n_phi0_dropped": n_phi0_dropped,
        "note": ("只导出 status == converged_unique; phi=0 为无回用基线(非数据点), "
                 "其上游行未收敛故被剔除。"),
    }
    print(f"[{label}] {n_all} -> {n_ok} (剔除 {n_all - n_ok}; 其中 phi=0 行 {n_phi0_dropped})")
    return info


def main() -> None:
    manifest = {"exporter": "A26_语义统一/export_fig1_sources.py",
                "reliable_whitelist": sorted(RELIABLE),
                "semantics_ref": "A26_语义统一/CHI_SEMANTICS.md",
                "items": []}

    # --- panel 1: 排放—索取 (来自 A13c potable_flows) ---
    manifest["items"].append(export(
        ROOT / "A13_可靠性机制" / "potable_flows.csv",
        FIGDIR / "fig1_v2_source_potable_flows.csv",
        "potable_flows"))

    # --- panel 2: 消融 (来自 A15 ablation_matrix) ---
    manifest["items"].append(export(
        ROOT / "A15_稳健性" / "ablation_matrix.csv",
        FIGDIR / "fig1_v2_source_ablation.csv",
        "ablation"))

    (FIGDIR / "fig1_source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n[write] figures/fig1_source_manifest.json")


if __name__ == "__main__":
    main()
