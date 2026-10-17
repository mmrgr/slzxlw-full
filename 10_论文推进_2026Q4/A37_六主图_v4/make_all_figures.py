# -*- coding: utf-8 -*-
"""A37 六主图 v4 —— 一键复现。

用法
----
    cd "10_论文推进_2026Q4/A37_六主图_v4"
    PYTHONIOENCODING=utf-8 python make_all_figures.py

产出
----
    Fig1..Fig6 的 .pdf + .png (400 dpi, 字体嵌入)
    figure_index.md  (图号 -> 科学问题 -> 数据源 -> 生成脚本 -> 输出 -> SHA256)

前置
----
    python >= 3.10, matplotlib, numpy, pandas
    权威数据源位于上级目录 A13/A30/A31/A33/A34/A4/A15 (只读)。

数据纪律
--------
    本脚本**不产生任何数值**: 它只调用 E 各 `make_figN.py`, 后者一律经
    `figstyle_a37.load_*` 从权威产物读取。若某数据文件缺失, 相应图会明确失败,
    而不是回退到硬编码值 (任务要求: 不编造数据)。
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGS = [
    ("Fig 1", "make_fig1.py", "Fig1_boundary_counterfactuals"),
    ("Fig 2", "make_fig2.py", "Fig2_water_quality_coc"),
    ("Fig 3", "make_fig3.py", "Fig3_city_results_signs"),
    ("Fig 4", "make_fig4.py", "Fig4_independent_prediction"),
    ("Fig 5", "make_fig5.py", "Fig5_sensitivity_extremes"),
    ("Fig 6", "make_fig6.py", "Fig6_external_anchor_partial_id"),
]


def sha256(p: Path, n: int = 16) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n]


def main() -> int:
    print("=" * 78)
    print("A37 六主图 v4 —— 一键复现")
    print("=" * 78)
    fail = []
    for name, script, stem in FIGS:
        t0 = time.time()
        print(f"\n[{name}] {script} ...", flush=True)
        r = subprocess.run([sys.executable, str(HERE / script)],
                           cwd=str(HERE), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        dt = time.time() - t0
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode != 0:
            print(f"  FAILED (rc={r.returncode}, {dt:.1f}s)")
            print("  " + "\n  ".join(out.strip().splitlines()[-12:]))
            fail.append((name, script))
            continue
        arts = [HERE / f"{stem}.pdf", HERE / f"{stem}.png"]
        if not all(a.exists() for a in arts):
            print(f"  FAILED: 输出缺失 {[str(a.name) for a in arts if not a.exists()]}")
            fail.append((name, script))
            continue
        sizes = ", ".join(f"{a.name} {a.stat().st_size/1024:.0f} KB" for a in arts)
        print(f"  OK ({dt:.1f}s)  {sizes}")
        if "Warning" in out and "Glyph" in out:
            print("  WARNING: 存在缺字形 (中文可能渲染为方框)")

    print("\n" + "=" * 78)
    if fail:
        print(f"完成 {len(FIGS)-len(fail)}/{len(FIGS)}; 失败: {fail}")
        return 1
    print(f"全部 {len(FIGS)} 张图完成。运行 make_figure_index.py 生成索引。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
