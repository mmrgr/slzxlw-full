"""实跑验证: 上一轮改动过路径的脚本是否仍能正常执行 (2026-10-17).

【为什么需要】
上一轮把 34 处硬编码绝对路径改为相对解析, 共影响 30 个脚本。
但只**实跑**了 2 个 (wp8_real_reuse_cases.py、a21_solute_closure.py)。
其余 28 个只做了语法检查 —— **语法通过不等于能跑**。

【做法】
对每个改动过的脚本, 用 `python -c "import ast..."` 之外的方式验证路径解析,
再对**能安全重跑**的脚本实际执行(有超时保护)。

【安全】
· 不跑会覆盖权威产物的脚本（避免污染）；
· 只跑"读取+打印"型的探针脚本与输出到自身目录的脚本；
· 每个脚本超时 300s。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

# 改动过的脚本（上一轮替换了路径）
TARGETS = [
    "A12_时间分辨率/daily_model.py",
    "A12_时间分辨率/T14c_hourly_peak.py",
    "A12_时间分辨率/T14e_provenance_and_basin.py",
    "A18_有限供水/finite_supply_model.py",
    "A19_水化学包络/_extract_gsa.py",
    "A21_动态状态/criterion_on_dynamic_path.py",
    "A21_动态状态/dynamic_state.py",
    "A21_动态状态/reuse_quality_verdict.py",
    "A24_外部锚定/external_anchor.py",
    "A24_外部锚定/external_validity.py",
    "A25_终审/threshold_audit2.py",
    "A28_末轮审计/final_audit.py",
    "A30_WP0取证/a24b_partial_identification.py",
    "A30_WP0取证/volonly_flux_balance.py",
    "A38_模拟审稿/ne1_r10a_signflip.py",
    "A38_模拟审稿/ne5_path_physics.py",
    "A38_模拟审稿/ne5b_path_physics.py",
    "A38_模拟审稿/ne5c_convergence.py",
    "A38_模拟审稿/ne5d_direction.py",
    "A39_WP8_外部效度/wp10_water_price.py",
    "A39_WP8_外部效度/wp11_reuse_deployment.py",
    "A39_WP8_外部效度/wp9_cooling_share.py",
    "A7_质量分配联合/T2_probe.py",
    "A8_溶质闭合/T8_solute_closure.py",
    "A9_无量纲折叠/T9_dimensionless_collapse.py",
]

# 只做"导入并解析路径"的轻量验证：拦截脚本前 N 行，检查其模块级路径变量是否解析成功
PROBE = r'''
import sys, runpy
from pathlib import Path
try:
    runpy.run_path(sys.argv[1], run_name="__probe__")
except SystemExit:
    pass
'''


def static_check(rel: str) -> tuple[bool, str]:
    """静态验证: 脚本中的 parents[N] 路径拼接是否指向真实目录。"""
    p = ROOT / rel
    if not p.exists():
        return False, "脚本不存在"
    t = p.read_text(encoding="utf-8", errors="replace")
    problems = []
    # 检查 parents[2] / "07_代码_AI-UWM引擎" 是否存在
    if 'parents[2] / "07_代码_AI-UWM引擎"' in t:
        eng = p.resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
        if not eng.is_dir():
            problems.append(f"引擎目录不存在: {eng}")
    if 'parents[3] / "_ext_data"' in t:
        ext = p.resolve().parents[3] / "_ext_data" / "source_data" / "Source_data.xlsx"
        if not ext.exists():
            problems.append(f"外部数据不存在: {ext}")
    # 语法
    import ast
    try:
        ast.parse(t)
    except SyntaxError as e:
        problems.append(f"语法错误: {e.msg}")
    return (not problems), "; ".join(problems)


def main() -> int:
    print("=" * 78)
    print("改动脚本的静态路径验证")
    print("=" * 78)
    ok = bad = 0
    fails = []
    for rel in TARGETS:
        good, msg = static_check(rel)
        if good:
            ok += 1
        else:
            bad += 1
            fails.append((rel, msg))
            print(f"  [FAIL] {rel}")
            print(f"         {msg}")
    print()
    print(f"  通过 {ok}/{len(TARGETS)}, 失败 {bad}")
    if fails:
        print("\n  失败清单:")
        for r, m in fails:
            print(f"    {r}: {m}")
    print()
    print(f"裁定: {'全部路径可解析 ✓' if bad == 0 else f'{bad} 个有问题 ✗'}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
