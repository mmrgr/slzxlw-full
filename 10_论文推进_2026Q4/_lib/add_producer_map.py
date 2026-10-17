"""给复现清单加入"生成脚本"列 (2026-10-17).

【问题】原清单只有"名称/哈希/存在/路径/说明", **没有说明每个产物由哪个脚本生成**。
读者拿到清单无法知道该跑什么来重建, 复现链在这里断了。

【注意】不能用"哪个脚本出现了这个文件名"来推断生成者 ——
  `final_gate.py` 读取 ne1/ne2/ne4/wp8/wp9/wp10/wp11 这些产物做断言,
  但它是**消费者**不是**生产者**。
必须在脚本中找"写入"语句, 才能确定生产者。下表为人工核实结果。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A40_投稿包/make_reproducibility_manifest.py"
t = MS.read_text(encoding="utf-8")

# 产物路径 -> 生成脚本（人工核实：脚本中确有写入该文件的语句）
PRODUCER = {
    "A16_英文稿/manuscript_en_v3.md": "（手写稿，非生成）",
    "A16_英文稿/supplementary_information.md": "（手写稿，非生成）",
    "A37_六主图_v4/figure_index.md": "A37_六主图_v4/make_figure_index.py",
    "A13_可靠性机制/supply_state_regimes.csv": "A13_可靠性机制/supply_state_regimes.py",
    "A15_稳健性/holdout_summary.json": "A15_稳健性/holdout_validation.py",
    "A20_模型桥接/bridging_summary_v2.json": "A20_模型桥接/bridging_v2.py",
    "A30_WP0取证/a24b_partial_id_summary.json": "A30_WP0取证/a24b_partial_identification.py",
    "A30_WP0取证/a24b_capacity_table.csv": "A30_WP0取证/a24b_partial_identification.py",
    "A30_WP0取证/a21_solute_closure_summary.json": "A30_WP0取证/a21_solute_closure.py",
    "A30_WP0取证/volonly_flux_balance_summary.json": "A30_WP0取证/volonly_flux_balance.py",
    "A30_WP0取证/stale_number_audit.json": "A30_WP0取证/audit_stale_numbers.py",
    "A30_WP0取证/untraceable_traceability_summary.json": "A30_WP0取证/trace_untraceable.py",
    "A30_WP0取证/证据台账_EVIDENCE_LEDGER.md": "A40_投稿包/make_reproducibility_manifest.py",
    "A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json":
        "A31_WP2_假设冻结/wp2_e3_independent_prediction.py",
    "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json":
        "A31_WP2_假设冻结/wp2_e3b_combined_prediction.py",
    "A32_WP3_水化学/wp3_h4_robustness_summary.json": "A32_WP3_水化学/wp3_h4_robustness.py",
    "A33_WP4_组成重构/wp4_results.csv": "A33_WP4_组成重构/wp4_complete_samples.py",
    "A34_WP5_敏感性与极端事件/wp5_morris.csv": "A34_WP5_敏感性与极端事件/wp5_morris_sobol.py",
    "A34_WP5_敏感性与极端事件/wp5_sobol.csv": "A34_WP5_敏感性与极端事件/wp5_morris_sobol.py",
    "A34_WP5_敏感性与极端事件/wp5_extreme_summary.json":
        "A34_WP5_敏感性与极端事件/wp5_extreme_events.py",
    "A38_模拟审稿/ne1_r10a_signflip_summary.json": "A38_模拟审稿/ne1_r10a_signflip.py",
    "A38_模拟审稿/ne2_panel_robustness_summary.json": "A38_模拟审稿/ne2_panel_robustness.py",
    "A38_模拟审稿/ne4_sobol_bootstrap_summary.json": "A38_模拟审稿/ne4_sobol_bootstrap.py",
    "A39_WP8_外部效度/wp8_real_reuse_cases_summary.json":
        "A39_WP8_外部效度/wp8_real_reuse_cases.py",
    "A39_WP8_外部效度/wp9_cooling_share_summary.json": "A39_WP8_外部效度/wp9_cooling_share.py",
    "A39_WP8_外部效度/wp10_water_price_summary.json": "A39_WP8_外部效度/wp10_water_price.py",
    "A39_WP8_外部效度/wp11_reuse_deployment_summary.json":
        "A39_WP8_外部效度/wp11_reuse_deployment.py",
    "A36_终审/final_gate.py": "（手写脚本）",
}

# 1. 在文件末尾追加 PRODUCER 表 + 校验函数
BLOCK = '''

# ---------------------------------------------------------------
# 生成脚本映射 (2026-10-17 新增)
# ---------------------------------------------------------------
# 每个权威产物由哪个脚本生成。复现者据此重建。
# 注意: 不能用"哪个脚本提到该文件名"推断 —— final_gate.py 只是消费者。
PRODUCER = {
%s}

# 运行时自检: 映射必须覆盖 ARTIFACTS 中的全部产物, 且脚本文件确实存在
def check_producer_map() -> list:
    problems = []
    for name, rel, _desc in ARTIFACTS:
        if rel not in PRODUCER:
            problems.append(f"缺生成脚本映射: {rel}")
        elif not PRODUCER[rel].startswith("（"):
            if not (ROOT / PRODUCER[rel]).exists():
                problems.append(f"映射的脚本不存在: {PRODUCER[rel]} (产物 {rel})")
    return problems
''' % "".join(
    f'    "{k}": "{v}",\n' for k, v in PRODUCER.items()
)

if "PRODUCER = {" not in t:
    t = t.rstrip() + "\n" + BLOCK
    MS.write_text(t, encoding="utf-8")
    print("已追加 PRODUCER 映射表")
else:
    print("PRODUCER 已存在，跳过")
