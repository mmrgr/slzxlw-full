"""A25 修复(续2): 给 A15 三个脚本加求解器状态门禁.

【缺陷】ablation / holdout / grid_resolution 均未按 status 过滤,
        未收敛情景(分配量为 0, phi_eff=0)会污染 gate 统计。

【修法】在每个脚本中:
  1. 载入/生成数据后, 过滤 status == "converged_unique" 再算 gate;
  2. summary 中同时报告 n_all / n_reliable / n_excluded;
  3. 保留一份"全样本"对照, 便于审计。
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "A15_稳健性"


def patch_ablation() -> None:
    p = HERE / "ablation_matrix_corrected.py"
    s = p.read_text(encoding="utf-8")
    # 在 gates 计算之前插入可靠子集过滤
    old = "    gates = []"
    new = '''    # ---- A25: 求解器状态门禁 (未收敛情景分配量为 0, 必须剔除) ----
    _d_all = d.copy()
    d = d[d["status"].astype(str) == "converged_unique"].copy()
    _n_all, _n_ok = int(len(_d_all)), int(len(d))
    rec(f"\\n[A25 门禁] 全样本 {_n_all} -> 可靠 {_n_ok} "
        f"(剔除 {_n_all - _n_ok} 个未收敛/多解情景)")
    if len(d) == 0:
        raise SystemExit("可靠子集为空")

    gates = []'''
    if old in s and "A25" not in s:
        s = s.replace(old, new, 1)
    # summary 增加计数
    s = s.replace('        "n_rows": int(len(d)),',
                  '        "n_rows": int(len(d)),\n'
                  '        "n_rows_all": int(len(_d_all)),\n'
                  '        "n_excluded_unreliable": int(len(_d_all) - len(d)),')
    p.write_text(s, encoding="utf-8")
    print("[patched] ablation_matrix_corrected.py")


def patch_holdout() -> None:
    p = HERE / "holdout_validation_corrected.py"
    s = p.read_text(encoding="utf-8")
    old = "    # ---------- H1: 闭式"
    new = '''    # ---- A25: 求解器状态门禁 ----
    _na, _nb = int(len(fit)), int(len(hold))
    fit = fit[fit["status"].astype(str) == "converged_unique"].copy()
    hold = hold[hold["status"].astype(str) == "converged_unique"].copy()
    rec(f"\\n[A25 门禁] fit {_na}->{len(fit)}, hold {_nb}->{len(hold)} "
        f"(剔除未收敛情景)")

    # ---------- H1: 闭式'''
    if old in s and "A25" not in s:
        s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8")
    print("[patched] holdout_validation_corrected.py")


def patch_grid() -> None:
    p = HERE / "grid_resolution_check.py"
    s = p.read_text(encoding="utf-8")
    # 找到状态统计位置, 插入过滤
    if "A25" in s:
        print("[skip] grid_resolution_check.py 已有 A25")
        return
    print("[info] grid_resolution_check.py 需人工确认插入点")


patch_ablation()
patch_holdout()
patch_grid()
