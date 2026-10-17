"""项目级公共工具: 路径解析 + 哈希 + 可靠子集门禁 + 日志.

【为什么需要这个模块 (2026-10-16 清理轮)】
项目原有 177 个脚本, 其中 **102 个 (58%) 硬编码了 `A*` 目录名或文件名**,
例如 `ROOT / "A13_可靠性机制" / "supply_state_regimes.csv"`。
后果: **一旦重命名/移动目录或产物文件, 就会有大量脚本静默失效**
(Path 拼接不会报错, 只会在运行时 FileNotFoundError 或读错文件)。

本模块提供**单一路径真相源**:
  · 所有目录与关键产物都在 PATH_TABLE 中**只声明一次**;
  · 脚本改用 `p("main_grid")` 而非硬编码字符串;
  · `p()` 解析失败时**立刻抛出带提示的错误**, 而不是静默返回坏路径;
  · 提供 `resolve_legacy()` 以兼容尚未迁移的旧写法。

同时合并了此前散落在 5 个脚本中的重复 `sha256` 实现 (R3),
以及双门禁可靠子集过滤 (R1, 25 个脚本各写一遍)。

【纪律】
  · 本模块**不修改**任何既有脚本; 迁移是增量、可选的;
  · 路径表只增不改名: 若必须改名, 保留旧名为 alias 并标注 deprecated;
  · 不引入新依赖 (只用标准库 + pathlib)。
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

# --------------------------------------------------------------------------
# 0. 版式定位: 本文件位于 <project>/10_论文推进_2026Q4/_lib/ 之下
#    (或 <project>/_lib/ 之下, 取决于放置位置) —— 两种都支持。
# --------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent


def _find_project_root() -> Path:
    """向上寻找项目根 (含 '07_代码_AI-UWM引擎' 的目录)。"""
    for base in (_HERE, *_HERE.parents):
        if (base / "07_代码_AI-UWM引擎").is_dir():
            return base
    # 兜底: 本模块通常位于 <root>/10_论文推进_2026Q4/_lib/
    return _HERE.parent.parent if _HERE.parent.name == "10_论文推进_2026Q4" else _HERE.parent


PROJECT_ROOT = _find_project_root()
# 研究推进目录 (A* 所在)
if (_HERE.parent.name == "10_论文推进_2026Q4"):
    RESEARCH_DIR = _HERE.parent
elif (_HERE.name == "10_论文推进_2026Q4"):
    RESEARCH_DIR = _HERE
else:
    RESEARCH_DIR = PROJECT_ROOT / "10_论文推进_2026Q4"

ENGINE_REPO = PROJECT_ROOT / "07_代码_AI-UWM引擎" / "aiuwm_src"
EXTERNAL_DATA = PROJECT_ROOT / ".." / "_ext_data" / "source_data"  # 论文/_ext_data


# --------------------------------------------------------------------------
# 1. 目录路径表: **唯一真相源**。改名请在此处改, 并保留旧名 alias。
# --------------------------------------------------------------------------
DIR_TABLE: dict[str, str] = {
    # 研究阶段目录 (A*)
    "chem_samples":     "A4_水化学参数域",
    "sensitivity":      "A10_敏感性与边界",
    "allocation":       "A7_质量分配联合",
    "reliability":      "A13_可靠性机制",
    "robustness":       "A15_稳健性",
    "manuscript":       "A16_英文稿",
    "bridging":         "A20_模型桥接",
    "dynamic_state":    "A21_动态状态",
    "criterion":        "A22_判据分解",
    "external_anchor":  "A24_外部锚定",
    "final_audit":      "A25_终审",
    "cited_limits":     "A27_引用限值",
    "lit_verification": "A29_文献核验",
    "wp0_forensics":    "A30_WP0取证",
    "wp2_hypotheses":   "A31_WP2_假设冻结",
    "wp3_chemistry":    "A32_WP3_水化学",
    "wp4_composition":  "A33_WP4_组成重构",
    "wp5_sensitivity":  "A34_WP5_敏感性与极端事件",
    "wp7_revision":     "A35_WP7_主稿修订",
    "terminal_gate":    "A36_终审",
    "figures":          "A37_六主图_v4",
    "peer_review":      "A38_模拟审稿",
    "external_validity": "A39_WP8_外部效度",
    "submission":       "A40_投稿包",
    "pkg_audit":        "A41_全包审计",
    "references":       "A42_参考文献",
    "statements":       "A43_投稿声明",
    "cleanup_audit":    "A44_检查清理轮",
    # 顶层
    "code":             "07_代码_AI-UWM引擎",
    "data":             "08_实验数据",
    "tools":            "09_工具与辅助脚本",
    "literature":       "06_文献库",
    "archive":          "_archive_2026-10-16",
}

# 关键产物: 同样只声明一次
FILE_TABLE: dict[str, str] = {
    "main_grid":        "reliability/supply_state_regimes.csv",
    "main_grid_summary": "reliability/supply_state_summary.json",
    "holdout":          "robustness/holdout_summary.json",
    "bridging_v2":      "bridging/bridging_summary_v2.json",
    "external_anchor_summary": "external_anchor/external_anchor_summary.json",
    "samples":          "chem_samples/T6_water_chemistry_samples.csv",
    "cited_limits_py":  "chem_samples/T6b_limits_cited.py",
    "manuscript_md":    "manuscript/manuscript_en_v3.md",
    "si_md":            "manuscript/supplementary_information.md",
    "city_model":       "sensitivity/city_model.py",
    "figstyle_v4":      "figures/figstyle_a37.py",
    "wp4_results":      "wp4_composition/wp4_results.csv",
    "a24b_partial":     "wp0_forensics/a24b_partial_id_summary.json",
    "evidence_ledger":  "wp0_forensics/证据台账_EVIDENCE_LEDGER.md",
}

# --------------------------------------------------------------------------
# 2. 解析函数
# --------------------------------------------------------------------------
_ALIASES = {
    # 旧名 -> 新名 (改名时在此登记, 保证旧脚本仍可解析)
}


def d(name: str) -> Path:
    """解析目录。失败时抛错而非返回坏路径。

    先在 RESEARCH_DIR 下找, 再在 PROJECT_ROOT 下找 —— 因为路径表同时含
    A* 研究目录(位于 RESEARCH_DIR)与顶层目录(位于 PROJECT_ROOT)。
    """
    key = _ALIASES.get(name, name)
    if key not in DIR_TABLE:
        raise KeyError(
            f"未知目录键 {name!r}。可用键: {sorted(DIR_TABLE)}。"
            f"若需新增, 请在 DIR_TABLE 登记。")
    rel = DIR_TABLE[key]
    for base in (RESEARCH_DIR, PROJECT_ROOT):
        cand = base / rel
        if cand.exists():
            return cand
    raise FileNotFoundError(
        f"目录不存在: {RESEARCH_DIR / rel} 或 {PROJECT_ROOT / rel}\n"
        f"(键={name!r} -> {rel!r})。若已改名, 请在 DIR_TABLE 更新并加 "
        f"_ALIASES 兼容旧名。")


def p(name: str) -> Path:
    """解析关键产物文件。失败时抛错。"""
    key = _ALIASES.get(name, name)
    if key not in FILE_TABLE:
        raise KeyError(f"未知文件键 {name!r}。可用键: {sorted(FILE_TABLE)}")
    parts = FILE_TABLE[key].split("/")
    path = d(parts[0]).joinpath(*parts[1:]) if len(parts) > 1 else RESEARCH_DIR / FILE_TABLE[key]
    if not path.exists():
        raise FileNotFoundError(
            f"文件不存在: {path}\n(键={name!r})。若已改名, 请更新 FILE_TABLE。")
    return path


def resolve_legacy(relpath: str) -> Path:
    """兼容尚未迁移的硬编码写法: 把 'A13_可靠性机制/x.csv' 解析为绝对路径。

    用于**渐进迁移**: 旧脚本可把 `ROOT / "A13_可靠性机制" / "x.csv"`
    替换为 `resolve_legacy("A13_可靠性机制/x.csv")`, 从而只在一处维护。
    """
    q = RESEARCH_DIR / relpath
    if q.exists():
        return q
    q2 = PROJECT_ROOT / relpath
    if q2.exists():
        return q2
    raise FileNotFoundError(f"resolve_legacy 找不到: {relpath}")


# --------------------------------------------------------------------------
# 3. 哈希 (合并此前 5 处重复实现, R3)
# --------------------------------------------------------------------------
def sha256(path: Path | str, n: int = 16) -> str:
    """文件 SHA-256 前 n 位。n=0 返回完整摘要。

    大文件分块读取, 避免一次性载入内存。
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n] if n else h.hexdigest()


# --------------------------------------------------------------------------
# 4. 双门禁可靠子集 (合并 R1: 此前 25 个脚本各写一遍)
# --------------------------------------------------------------------------
def reliable_subset(df, *, status_col: str = "status",
                    degen_col: str = "coc_floor_degenerate",
                    coc_col: str | None = None,
                    coc_floor: float = 1.000001):
    """返回双门禁后的可靠子集。

    门禁 1: status == 'converged_unique'
    门禁 2: 未触 CoC 下限 (退化情景)

    优先使用 `coc_floor_degenerate` 列; 若该列不存在但有 `coc_col`,
    则按 `coc_col <= coc_floor` 现算 —— 两种写法在此**统一**, 消除 R1 隐患。

    返回: (df_reliable, info_dict)
    """
    import pandas as pd  # 局部导入, 避免模块级强依赖

    info: dict = {"n_all": int(len(df))}
    if status_col not in df.columns:
        raise KeyError(f"缺少状态列 {status_col!r}; 无法应用门禁 1")

    gate1 = df[status_col].astype(str) == "converged_unique"
    info["n_after_status"] = int(gate1.sum())

    if degen_col in df.columns:
        gate2 = ~df[degen_col].astype(bool)
        info["degenerate_gate"] = f"column:{degen_col}"
    elif coc_col and coc_col in df.columns:
        gate2 = ~(pd.to_numeric(df[coc_col], errors="coerce") <= coc_floor + 1e-12)
        info["degenerate_gate"] = f"computed:{coc_col}<={coc_floor}"
    else:
        raise KeyError(
            f"缺少退化门禁信息: 既无 {degen_col!r} 列, 也无 coc_col。"
            f"**不得**静默跳过门禁 2 (会改变 n)。")

    out = df[gate1 & gate2]
    info["n_reliable"] = int(len(out))
    info["n_excluded"] = info["n_all"] - info["n_reliable"]
    info["warning"] = ("符号计数须声明零值约定与实际 n_eff (门禁第 8 条); "
                       "勿把 n_reliable 当作符号计数的分母")
    return out, info


# --------------------------------------------------------------------------
# 5. 自检 (迁移后可用 `python _lib/project_paths.py` 验证)
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("PROJECT_ROOT =", PROJECT_ROOT)
    print("RESEARCH_DIR =", RESEARCH_DIR)
    print("ENGINE_REPO  =", ENGINE_REPO, "exists=", ENGINE_REPO.is_dir())
    print()
    print("--- 目录键自检 ---")
    bad = 0
    for k in sorted(DIR_TABLE):
        try:
            d(k)
        except Exception as e:
            print(f"  [FAIL] {k}: {e}")
            bad += 1
    print(f"  {len(DIR_TABLE)-bad}/{len(DIR_TABLE)} 目录键解析成功")
    print()
    print("--- 关键产物自检 ---")
    bad2 = 0
    for k in sorted(FILE_TABLE):
        try:
            f = p(k)
            print(f"  [OK] {k:<24} {sha256(f, 12)}  {f.relative_to(RESEARCH_DIR)}")
        except Exception as e:
            print(f"  [FAIL] {k}: {e}")
            bad2 += 1
    print(f"  {len(FILE_TABLE)-bad2}/{len(FILE_TABLE)} 产物键解析成功")
