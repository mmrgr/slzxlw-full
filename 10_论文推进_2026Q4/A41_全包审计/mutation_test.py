"""突变测试: 给每道门禁注入一个真实缺陷, 验证它会 FAIL (2026-10-17).

【为什么需要】
上一轮发现 form_gate 里有表达式**恒为空**, 因此该项检查永远不会失败。
静态扫描 `or True` 抓不到这种问题。
唯一可靠的办法是**突变测试(mutation test)**: 主动破坏一个前提, 看门禁是否报错。

【做法】
对每道门禁, 在一个**临时副本**上注入缺陷, 运行门禁, 检查它是否 FAIL。
不修改真实文件。

【若某道门禁在注入缺陷后仍 PASS => 它是形式主义的】
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # 10_论文推进_2026Q4
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
SI = ROOT / "A16_英文稿/supplementary_information.md"

# (门禁名, 脚本相对路径, 注入函数(返回需要还原的备份字典), 期望失败标记)
def _apply(path, new_text_fn, tag):
    """注入并强制校验: 突变必须真正改变文本, 否则报错(防止'突变未生效被误判')。"""
    orig = path.read_text(encoding="utf-8")
    mut = new_text_fn(orig)
    if mut == orig:
        raise RuntimeError(f"突变未生效: {tag} 中未找到目标字符串")
    path.write_text(mut, encoding="utf-8")
    return {tag: (path, orig)}


def mutate_ms(new_text_fn):
    return _apply(MS, new_text_fn, "MS")


def mutate_si(new_text_fn):
    return _apply(SI, new_text_fn, "SI")


CASES = []

# 1. 结构完整性: 打乱小节编号
def m1(t):
    return t.replace("### 5. Cooling-water limits", "### 3b-bis. Cooling-water limits", 1)
CASES.append(("结构完整性", "A41_全包审计/structure_gate.py", m1, "MS"))


# 2. 陈旧值黑名单: 写回旧值
def m2(t):
    return t.replace("839 solver-reliable", "813 solver-reliable", 1)
CASES.append(("真相源双向", "A41_全包审计/truth_gate.py", m2, "MS"))


# 3. 文档卫生: 引用不存在的产物
def m3(t):
    return t.replace("A29_文献核验/", "A29_NOTEXIST/", 1)
CASES.append(("文档卫生", "A41_全包审计/hygiene_gate.py", m3, "MS"))


# 4. 形式一致性: 文献表加孤儿条目
def m4(t):
    return t.replace("## Declarations",
                     "17. Ghostman, A. (2099). Ghost. *J* **1**, 1. "
                     "https://doi.org/10.9999/ghost\n\n## Declarations", 1)
CASES.append(("形式一致性", "A41_全包审计/form_gate.py", m4, "MS"))


# 5. 新颖性合规: 写一条肯定式违禁表述
def m5(t):
    return t.replace("## Introduction",
                     "## Introduction\n\nWe are the first global framework pairing data "
                     "centres with wastewater treatment plants.\n", 1)
CASES.append(("新颖性合规", "A41_全包审计/novelty_gate.py", m5, "MS"))


# 6. 机制声明证据: 删掉 SI 里的 S21
def m6(t):
    return t.replace("S21", "SXX")
CASES.append(("机制声明证据", "A41_全包审计/claim_evidence_gate.py", m6, "SI"))


# 7. 陈旧值黑名单: 写回黑名单旧值 (该字符串在 SI 中)
def m7(t):
    return t.replace("residual (ML, relative)", "residual 2.55 × 10⁻¹¹ (ML, relative)", 1)
CASES.append(("陈旧值黑名单", "A41_全包审计/stale_value_gate.py", m7, "SI"))


# 8. 全包一致性: 破坏 SI 章节编号连续性
def m8(t):
    return t.replace("## S21.", "## S23.", 1)
CASES.append(("全包一致性", "A41_全包审计/package_consistency_check.py", m8, "SI"))


# 9. 投稿声明: 删除 Data availability 节标题
def m9(t):
    return t.replace("### Data availability", "### Data", 1)
CASES.append(("投稿声明", "A43_投稿声明/required_statements.py", m9, "MS"))


def run_gate(script: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, script], cwd=str(ROOT / Path(script).parent),
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    print("=" * 78)
    print("门禁突变测试（验证不存在恒真检查）")
    print("=" * 78)
    survivors = []
    for name, script, mut, target in CASES:
        backup = None
        try:
            if target == "MS":
                backup = mutate_ms(mut)
            else:
                backup = mutate_si(mut)
            code, out = run_gate(script)
            killed = code != 0
            print(f"  [{'杀 死' if killed else '幸存!'}] {name:<14} (exit={code})")
            if not killed:
                survivors.append(name)
        except Exception as e:
            print(f"  [异常] {name}: {e}")
            survivors.append(name)
        finally:
            if backup:
                for f, orig in backup.values():
                    f.write_text(orig, encoding="utf-8")

    print()
    if survivors:
        print(f"⚠ 突变后仍通过的（可能是形式主义检查）: {survivors}")
    else:
        print(f"全部 {len(CASES)} 道门禁都成功杀死了注入的缺陷 ✓")
    return 0 if not survivors else 1


if __name__ == "__main__":
    sys.exit(main())
