"""A26-S2: 给 A17/A22 产物补权威语义列.

新增三列 (定义见 A26_语义统一/CHI_SEMANTICS.md):
  limit_scale      —— 传给引擎的限值缩放因子 (权威列, 等于原 chi)
  chi_strictness   —— CoC_lim_realized / CoC_design (无量纲严格度)
  quality_binding  —— 布尔: chi_strictness < 1 - tol (限值是否真在起作用)

⚠ 不改任何数值, 只加列 + 加注。
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A13 = ROOT / "A13_可靠性机制"


def patch_a17() -> None:
    p = A13 / "supply_state_regimes.py"
    s = p.read_text(encoding="utf-8")

    # 1. 在返回 dict 中补三列
    old = '''        "pool_scale": float(pool_scale), "phi": float(phi), "chi": float(chi),'''
    new = '''        "pool_scale": float(pool_scale), "phi": float(phi), "chi": float(chi),
        # ---- A26 权威语义列 (见 A26_语义统一/CHI_SEMANTICS.md) ----
        # 注: 本脚本的 `chi` **就是** limit_scale; 此处显式并列以便跨表安全。
        "limit_scale": float(chi),
        "chi_strictness": float(r1["CoC_ai"]) / float(COC_DESIGN_REF),
        "quality_binding": bool(float(r1["CoC_ai"]) < COC_DESIGN_REF * (1.0 - 1e-9)),'''
    assert old in s, "A17 返回段未匹配"
    s = s.replace(old, new, 1)

    # 2. 定义参考设计值常量
    s = s.replace("def run_case(", "COC_DESIGN_REF = 5.0   # 引擎默认设计 CoC (见 city_model.COC_DESIGN_DEFAULT)\n\n\ndef run_case(", 1)

    # 3. summary 中登记语义
    s = s.replace('        "runtime_s": round(time.time() - t0, 1),',
                  '''        "semantics": {
            "chi_meaning": ("本产物的 `chi` **就是** limit_scale (限值整体缩放因子), "
                            "**不是** chi=CoC_lim/CoC_design。权威定义见 A26_语义统一/CHI_SEMANTICS.md。"),
            "authoritative_columns": ["limit_scale", "chi_strictness", "quality_binding"],
            "chi_strictness_note": "由引擎实测 CoC 反解, 仅具相对意义(依赖占位限值)。",
        },
        "runtime_s": round(time.time() - t0, 1),''', 1)

    p.write_text(s, encoding="utf-8")
    print("[patched] supply_state_regimes.py (+3 语义列)")


if __name__ == "__main__":
    patch_a17()
