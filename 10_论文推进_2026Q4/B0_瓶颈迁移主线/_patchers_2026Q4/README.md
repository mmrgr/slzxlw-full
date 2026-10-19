# _patchers_2026Q4 —— 一次性修补脚本与诊断探针（归档，非删除）

这些脚本在 2026Q4 的论文推进过程中被逐轮执行过，**其改动早已落盘到最终文档**。
保留在此是为了保留修订轨迹（"某个数字/某段表述是怎么变成现在这样的"）。

## 不要直接重跑

它们是**一次性**的：多数用 `old_string` 精确匹配当时的文本，
现在文档已变，重跑会匹配失败或重复插入。

## 需要在别处重跑的东西

以下脚本**留在主目录、未归档**（被门禁或文档引用）：

- `_diag_2x2_attribution.py` — 门禁 ['_verify_two_path_attribution.py']；文档 ['54_第二十六轮工作总结_撤回上下界结论.md']
- `_diag_dynamic_inflow.py` — 门禁 []；文档 ['54_第二十六轮工作总结_撤回上下界结论.md']
- `_diag_kstar_boundary.py` — 门禁 ['_si_num_gate.py']；文档 []
- `_diag_quality_storage.py` — 门禁 []；文档 ['05_wr_supplementary_en.md', '_bak_05_si.md']
- `_diag_reuse_quality.py` — 门禁 []；文档 ['54_第二十六轮工作总结_撤回上下界结论.md']
- `_diag_reuse_tds_aligned.py` — 门禁 []；文档 ['54_第二十六轮工作总结_撤回上下界结论.md']
- `_diag_reuse_tds_repair.py` — 门禁 []；文档 ['54_第二十六轮工作总结_撤回上下界结论.md']
- `_diag_reuse_tds_rootcause.py` — 门禁 []；文档 ['54_第二十六轮工作总结_撤回上下界结论.md']
- `_fix_en_two_path.py` — 门禁 []；文档 ['54_第二十六轮工作总结_撤回上下界结论.md']
- `_fix_si_two_path.py` — 门禁 []；文档 ['54_第二十六轮工作总结_撤回上下界结论.md']
- `_fix_two_path_correction.py` — 门禁 []；文档 ['54_第二十六轮工作总结_撤回上下界结论.md']
- `_test_analytic_cawcc.py` — 门禁 []；文档 ['05_wr_supplementary_en.md', '_bak_05_si.md']
- `_test_analytic_multigrid.py` — 门禁 []；文档 ['05_wr_supplementary_en.md', '_bak_05_si.md']
- `_test_dynamic_path_main.py` — 门禁 []；文档 ['05_wr_supplementary_en.md', '_bak_05_si.md']
- `_test_noninformative_extended.py` — 门禁 []；文档 ['05_wr_supplementary_en.md', '_bak_05_si.md']
- `_test_quality_state.py` — 门禁 []；文档 ['05_wr_supplementary_en.md', '_bak_05_si.md']

## 统计

- 本次移入：**125** 个
- 保留原位：**16** 个
- 完整清单见 `_MANIFEST.json`
- 回滚：`python _rollback_archive.py`
