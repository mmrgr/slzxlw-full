"""A26-S3: 给 A15 ablation/holdout 产物补权威语义列.

新增: limit_scale / chi_strictness / quality_binding
⚠ 不改任何数值, 只加列。
"""
from __future__ import annotations

from pathlib import Path

A15 = Path(__file__).resolve().parent.parent / "A15_稳健性"
REF = 5.0


def patch_ablation() -> None:
    p = A15 / "ablation_matrix_corrected.py"
    s = p.read_text(encoding="utf-8")
    old = '''                    "chi": chi, "dp_scale": dp, "phi": PHI,'''
    new = '''                    "chi": chi, "dp_scale": dp, "phi": PHI,
                    # ---- A26 权威语义列 (见 A26_语义统一/CHI_SEMANTICS.md) ----
                    "limit_scale": float(chi),
                    "chi_strictness": float(r1["CoC_ai"]) / REF_COC_DESIGN,
                    "quality_binding": bool(float(r1["CoC_ai"]) < REF_COC_DESIGN * (1 - 1e-9)),'''
    assert old in s, "ablation 段未匹配"
    s = s.replace(old, new, 1)
    s = s.replace("def run_cell(", "REF_COC_DESIGN = 5.0   # 引擎默认设计 CoC (A26 语义列用)\n\n\ndef run_cell(", 1)
    if "REF_COC_DESIGN = 5.0" not in s:
        # 备用: 插在第一个 def 前
        idx = s.index("\ndef ")
        s = s[:idx] + "\n\nREF_COC_DESIGN = 5.0   # 引擎默认设计 CoC (A26 语义列用)\n" + s[idx:]
    p.write_text(s, encoding="utf-8")
    print("[patched] ablation_matrix_corrected.py")


def patch_holdout() -> None:
    p = A15 / "holdout_validation_corrected.py"
    s = p.read_text(encoding="utf-8")
    old = '''                    "domain": dom, "sample": smp, "chi": chi, "phi": float(phi),'''
    new = '''                    "domain": dom, "sample": smp, "chi": chi, "phi": float(phi),
                    # ---- A26 权威语义列 (见 A26_语义统一/CHI_SEMANTICS.md) ----
                    "limit_scale": float(chi),
                    "chi_strictness": float(r1["CoC_ai"]) / REF_COC_DESIGN,
                    "quality_binding": bool(float(r1["CoC_ai"]) < REF_COC_DESIGN * (1 - 1e-9)),'''
    assert old in s, "holdout 段未匹配"
    s = s.replace(old, new, 1)
    s = s.replace("CHI = (1.0, 0.5, 0.25)", "REF_COC_DESIGN = 5.0   # 引擎默认设计 CoC (A26 语义列用)\nCHI = (1.0, 0.5, 0.25)", 1)
    p.write_text(s, encoding="utf-8")
    print("[patched] holdout_validation_corrected.py")


patch_ablation()
patch_holdout()
