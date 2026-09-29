"""Cross-check every capacity claim in the narrative docs against machine artifacts.

Motivation: earlier revisions of this project published capacity numbers that
disagreed with the data files (coarse probability grid, stale KPI, over-strong
"policy constraint dominates" claim).  Those errors were only caught by manual
adversarial review.  This script makes the check automatic: it extracts the
capacity figures from the documentation, converts them into a table keyed by
estimand, and compares each one with the corresponding value in
``validation_artifacts/r2``.

Exit code is non-zero when a documented value cannot be traced to an artifact,
which makes the check usable as a pre-submission gate.

Usage::

    python scripts/audit_doc_consistency.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "validation_artifacts" / "r2"
OUT = R2 / "doc_consistency_audit.csv"

# Documentation that quotes capacity numbers.  Relative to the research root
# (parents[1] is aiuwm_src, parents[2] is 07_代码_AI-UWM引擎).
RESEARCH_ROOT = ROOT.parents[1]
DOCS = [
    ROOT / "AI_DATA_CENTER_RESEARCH_CN.md",
    RESEARCH_ROOT / "01_方案与设计文档" / "Nature级研究审查与修正计划_R3.md",
    RESEARCH_ROOT / "01_方案与设计文档" / "AI-UWM下一轮模拟_情景设置与实施方案.md",
    RESEARCH_ROOT / "00_项目说明.md",
]

# estimand key -> artifact extractor.  Keys must stay aligned with the
# vocabulary used in the documentation.
PHYSICAL = {
    "physical_daily",
    "physical_annual",
    "physical_hourly",
    "daily",
    "annual",
    "reclaimed_target",
}


def load_thresholds(domain: str) -> dict:
    path = R2 / domain / "capacity_threshold_corrected.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_summary(domain: str) -> dict:
    path = R2 / domain / "probabilistic_corrected_summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Forbidden-phrasing guards.                                                  #
# --------------------------------------------------------------------------- #
# These are NOT numeric claims; they are *wording* traps that earlier revisions
# fell into.  Each entry is (doc_key, regex, description, allowed_context).
# A match is a FAIL unless the line also contains one of the ``allowed_context``
# markers, which lets a document quote the bad phrasing while correcting it
# (e.g. "原标题为'风险为零'，属表述错误").
FORBIDDEN_PHRASINGS = [
    (
        "plan",
        r"超限概率\s*0(?:\.0+)?\s*(?:，|,)?\s*(?:95%\s*)?CI\s*\[?\s*0\s*,\s*0\s*\]?",
        "把 0/n 的超限概率写成 0 或 [0,0] 区间（应为'观察到 0 次'+ 精确二项上界）",
        ("不得", "不构成", "退化", "表述错误", "修正", "不等于风险为零", "观察到"),
    ),
    (
        "plan",
        r"风险为零|无风险|不影响|完全不构成风险",
        "把 0/n 观测写成'风险为零/无风险'的绝对断言",
        ("不得", "不构成", "不等于", "表述错误", "修正", "误读", "不能写", "不可写"),
    ),
    (
        "plan",
        r"所有承载约束都不触发|所有约束都不触发|日尺度约束不会失效|日尺度约束根本不会失效",
        "把'未越 0.95 阈值'错写为'约束不触发/不会失效'",
        ("修正", "表述错误", "未越", "不等于", "原标题", "须带", "高位运行"),
    ),
    (
        "*",
        r"\bcalibrated\b",
        "把场景反算参数标为 calibrated（应为 scenario-tuned/设计标定）",
        ("scenario-tuned", "非实测率定", "不得"),
    ),
]


def scan_forbidden(text: str, doc_key: str) -> list[dict]:
    """Scan a document for forbidden phrasings.

    ``doc_key`` of ``"*"`` applies the rule to every document; otherwise the
    rule is restricted to that routing key.  The ``calibrated`` rule uses ``"*"``
    because the term is a global vocabulary constraint.
    """
    findings: list[dict] = []
    for key, pattern, desc, allowed in FORBIDDEN_PHRASINGS:
        if key not in ("*", doc_key):
            continue
        for m in re.finditer(pattern, text):
            # Look at the surrounding line for an allowed-context marker.
            start = text.rfind("\n", 0, m.start()) + 1
            end = text.find("\n", m.end())
            line = text[start: end if end != -1 else len(text)]
            if any(marker in line for marker in allowed):
                continue
            findings.append(
                {
                    "文档": doc_key,
                    "论断": desc,
                    "匹配文本": m.group(0),
                    "文档值": "",
                    "机器值": "",
                    "判定": "FORBIDDEN_PHRASING",
                    "证据文件": "—（措辞门禁）",
                    "真值键": "forbidden",
                }
            )
    return findings


def reservoir_two_year(domain: str) -> dict:
    path = R2 / "reservoir_sustainability_corrected.json"
    return json.loads(path.read_text(encoding="utf-8"))[domain]


def reservoir_ensemble(domain: str) -> dict | None:
    """Multi-sequence ensemble (T0.4); optional — may not exist yet."""
    path = R2 / "reservoir_multiyear_ensemble.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))[domain]


def load_total_water_frontier() -> dict | None:
    """R7b 全口径水足迹前沿；产物缺失时返回 None（门禁跳过，不判失败）。"""
    path = R2 / "total_water_footprint_frontier_R7b.csv"
    if not path.exists():
        return None
    out: dict[str, dict[str, float]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("冷却技术") != "dry":
                continue
            if row.get("电网碳强度档位") != "项目现值_0.350":
                continue
            domain = "ha" if row.get("域签") == "D-HA" else "co"
            slot = out.setdefault(domain, {})

            def _num(field: str) -> float | None:
                raw = (row.get(field) or "").strip()
                return float(raw) if raw not in ("", "None") else None

            tier = row.get("EWIF档位")
            if tier == "GreenGrid_1.8":
                v = _num("全口径节水百分比")
                o = _num("站点口径高估倍数")
                if v is not None:
                    slot["dry_full_saving_18"] = v
                if o is not None:
                    slot["site_overestimate_18"] = o
            elif tier == "LBNL_4.52":
                v = _num("全口径节水百分比")
                o = _num("站点口径高估倍数")
                c = _num("全口径每m3节水碳代价_kgCO2e")
                if v is not None:
                    slot["dry_full_saving_452"] = v
                if o is not None:
                    slot["site_overestimate_452"] = o
                if c is not None:
                    slot["carbon_cost_dry_452"] = round(c, 1)
            star = _num("反转阈值EWIF_L_per_kWh")
            if star is not None:
                slot["ewif_star_dry"] = round(star, 1)
    return out


def load_literature_anchor_check() -> dict:
    """R8 锚点校验产物。缺失时返回空 dict（门禁跳过，不判失败）。

    用 stdlib csv 而不是 pandas：本文件此前只依赖 csv/json，
    为一个只读三行的小表引入新依赖不划算。
    """
    path = R2 / "literature_anchor_check_R7.csv"
    out: dict[str, dict[str, float]] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            anchor = (row.get("锚点编号") or "").strip()
            raw = (row.get("模型计算值") or "").strip()
            if not anchor or raw in ("", "None"):
                continue
            label = row.get("域签") or ""
            domain = "ha" if "HA" in label.upper() else "co"
            # 量化到 5 位小数：门禁比对容差为 1e-6，文档无法、也不宜誊抄全精度浮点。
            out.setdefault(domain, {})[anchor] = round(float(raw), 5)
    return out


def load_reclaimed_sweep() -> dict:
    """R8 预注册自查：单域再生水比例 0→0.9 扫描的全区间变化率（%）。"""
    path = R2 / "reclaimed_fraction_sweep_R8.csv"
    out: dict[str, dict[str, float]] = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_domain: dict[str, list[dict]] = {}
    for row in rows:
        label = row.get("域签") or ""
        by_domain.setdefault("ha" if "HA" in label.upper() else "co", []).append(row)

    def _f(row: dict, key: str) -> float:
        return float((row.get(key) or "0").strip())

    for domain, series in by_domain.items():
        if len(series) < 2:
            continue
        series.sort(key=lambda r: _f(r, "目标再生水比例"))
        lo, hi = series[0], series[-1]
        out[domain] = {
            "coc_drop_pct": round((1 - _f(hi, "均值CoC") / _f(lo, "均值CoC")) * 100, 2),
            "withdraw_rise_pct": round(
                (_f(hi, "每单位散热取水_ML每MWh") / _f(lo, "每单位散热取水_ML每MWh") - 1) * 100, 2),
            "sewer_rise_pct": round(
                (_f(hi, "排入下水道量_ML") / _f(lo, "排入下水道量_ML") - 1) * 100, 2),
        }
    return out


def reservoir_ten_year(domain: str) -> dict:
    path = R2 / "reservoir_multiyear_10y.json"
    return json.loads(path.read_text(encoding="utf-8"))[domain]


def build_truth_table() -> dict:
    """Every number that may be quoted, keyed by (estimand, quantity)."""
    truth: dict[tuple[str, str], dict] = {}
    for domain in ("ha", "co"):
        thr = load_thresholds(domain)
        for key, block in thr.items():
            if isinstance(block, dict) and "maximum_safe_ai_capacity_mw" in block:
                truth[(f"{domain}:threshold:{key}", "max_safe_mw")] = {
                    "value": block["maximum_safe_ai_capacity_mw"],
                    "artifact": f"{domain}/capacity_threshold_corrected.json",
                }
                truth[(f"{domain}:threshold:{key}", "first_fail_mw")] = {
                    "value": block["first_failed_capacity_mw"],
                    "artifact": f"{domain}/capacity_threshold_corrected.json",
                }
        summary = load_summary(domain)
        for q in ("p05", "p50", "p95"):
            truth[(f"{domain}:probabilistic_physical", q)] = {
                "value": summary[q],
                "artifact": f"{domain}/probabilistic_corrected_summary.json",
            }
        pol = summary["policy_threshold"]
        for q in ("p05", "p50", "p95"):
            truth[(f"{domain}:probabilistic_policy", q)] = {
                "value": pol[q],
                "artifact": f"{domain}/probabilistic_corrected_summary.json",
            }
        truth[(f"{domain}:probability", "exceedance_at_1000mw")] = {
            "value": summary["exceedance_probability"],
            "artifact": f"{domain}/probabilistic_corrected_summary.json",
        }
        truth[(f"{domain}:probability", "exceedance_ci_low")] = {
            "value": summary["exceedance_probability_ci95"][0],
            "artifact": f"{domain}/probabilistic_corrected_summary.json",
        }
        truth[(f"{domain}:probability", "exceedance_ci_high")] = {
            "value": summary["exceedance_probability_ci95"][1],
            "artifact": f"{domain}/probabilistic_corrected_summary.json",
        }
        # Exact-binomial audit trail (added 2026-09-27): a 0/n count must be
        # reported with its exact upper bound rather than a degenerate [0, 0]
        # bootstrap interval.  These fields are produced by
        # ``scripts/add_exact_binomial_bound.py``.
        for q in (
            "exceedance_count",
            "exceedance_probability_exact_upper95",
        ):
            if q in summary:
                truth[(f"{domain}:probability", q)] = {
                    "value": summary[q],
                    "artifact": f"{domain}/probabilistic_corrected_summary.json",
                }
        rb = reservoir_two_year(domain)
        truth[(f"{domain}:reservoir_2y", "max_safe_mw")] = {
            "value": rb["max_terminal_non_depleting_capacity_mw"],
            "artifact": "reservoir_sustainability_corrected.json",
        }
        truth[(f"{domain}:reservoir_2y", "first_fail_mw")] = {
            "value": rb["first_terminal_decline_capacity_mw"],
            "artifact": "reservoir_sustainability_corrected.json",
        }
        ra = reservoir_ten_year(domain)
        truth[(f"{domain}:reservoir_10y", "max_safe_mw")] = {
            "value": ra["last_joint_gate_mw"],
            "artifact": "reservoir_multiyear_10y.json",
        }
        truth[(f"{domain}:reservoir_10y", "first_fail_mw")] = {
            "value": ra["first_joint_gate_failure_mw"],
            "artifact": "reservoir_multiyear_10y.json",
        }
        ens = reservoir_ensemble(domain)
        if ens is not None:
            truth[(f"{domain}:reservoir_ensemble", "median_mw")] = {
                "value": ens["joint_gate_mw_median"],
                "artifact": "reservoir_multiyear_ensemble.json",
            }

    # R7b 全口径水足迹前沿：文档里引用的每个前沿数字都必须能回溯到机器产物
    frontier = load_total_water_frontier()
    if frontier is not None:
        for domain in ("ha", "co"):
            block = frontier.get(domain)
            if block is None:
                continue
            for key, value in block.items():
                truth[(f"{domain}:frontier", key)] = {
                    "value": value,
                    "artifact": "total_water_footprint_frontier_R7b.csv",
                }

    # R8 锚点校验：文档 §七之六 引用的 A08/A09/A22 必须回溯到机器产物
    for domain, block in load_literature_anchor_check().items():
        for anchor_id, value in block.items():
            truth[(f"{domain}:anchor", anchor_id)] = {
                "value": value,
                "artifact": "literature_anchor_check_R7.csv",
            }

    # R8 预注册自查：文档 §七之七 的再生水比例扫描变化率
    for domain, block in load_reclaimed_sweep().items():
        for key, value in block.items():
            truth[(f"{domain}:reclaim", key)] = {
                "value": value,
                "artifact": "reclaimed_fraction_sweep_R8.csv",
            }
    return truth


# Documented claims that must hold.  Each entry is
# (doc_key, regex, resolver, description).
# ``resolver`` maps the regex match to a truth-table key.
CLAIMS = [
    # Threshold triplets written as "HA 的日/年/小时代理边界为 A/B/C MW".
    (
        "research",
        r"HA 的日/年/小时代理边界为 (\d+)/(\d+)/(\d+) MW",
        lambda m: [
            (("ha:threshold:physical_daily", "max_safe_mw"), m.group(1)),
            (("ha:threshold:annual", "max_safe_mw"), m.group(2)),
            (("ha:threshold:physical_hourly", "max_safe_mw"), m.group(3)),
        ],
        "HA 日/年/小时 max-safe 三元组",
    ),
    (
        "research",
        r"CO 为 (\d+)/(\d+)/(\d+) MW",
        lambda m: [
            (("co:threshold:physical_daily", "max_safe_mw"), m.group(1)),
            (("co:threshold:annual", "max_safe_mw"), m.group(2)),
            (("co:threshold:physical_hourly", "max_safe_mw"), m.group(3)),
        ],
        "CO 日/年/小时 max-safe 三元组",
    ),
    (
        "research",
        r"HA 去除再生水目标后的物理年边界为 (\d+) MW",
        lambda m: [(("ha:threshold:physical_annual", "max_safe_mw"), m.group(1))],
        "HA 物理年边界",
    ),
    (
        "research",
        r"联合边界为 HA (\d+) MW、CO (\d+) MW",
        lambda m: [
            (("ha:reservoir_10y", "max_safe_mw"), m.group(1)),
            (("co:reservoir_10y", "max_safe_mw"), m.group(2)),
        ],
        "10 年联合边界",
    ),
    (
        "plan",
        r"HA 最后通过/首次失败为 150/200 MW，CO 为 900/950 MW",  # not present; kept as guard
        lambda m: [],
        "占位（当前文档无此句式）",
    ),
    (
        "plan",
        r"\| 物理 CAWCC（日/年/小时代理） \| (\d+)/(\d+)/(\d+) MW \| (\d+)/(\d+)/(\d+) MW",
        lambda m: [
            (("ha:threshold:physical_daily", "max_safe_mw"), m.group(1)),
            (("ha:threshold:physical_annual", "max_safe_mw"), m.group(2)),
            (("ha:threshold:physical_hourly", "max_safe_mw"), m.group(3)),
            (("co:threshold:physical_daily", "max_safe_mw"), m.group(4)),
            (("co:threshold:physical_annual", "max_safe_mw"), m.group(5)),
            (("co:threshold:physical_hourly", "max_safe_mw"), m.group(6)),
        ],
        "plan 表：物理 CAWCC 日/年/小时",
    ),
    (
        "plan",
        r"\| 综合口径（含再生水政策目标） \| (\d+)/(\d+)/(\d+) MW \| (\d+)/(\d+)/(\d+) MW",
        lambda m: [
            (("ha:threshold:daily", "max_safe_mw"), m.group(1)),
            (("ha:threshold:annual", "max_safe_mw"), m.group(2)),
            (("ha:threshold:physical_hourly", "max_safe_mw"), m.group(3)),
            (("co:threshold:daily", "max_safe_mw"), m.group(4)),
            (("co:threshold:annual", "max_safe_mw"), m.group(5)),
            (("co:threshold:physical_hourly", "max_safe_mw"), m.group(6)),
        ],
        "plan 表：综合口径 日/年/小时",
    ),
    (
        "plan",
        r"\| 两年末库容边界（期末≥初值） \| (\d+)/(\d+) MW \| (\d+)/(\d+) MW",
        lambda m: [
            (("ha:reservoir_2y", "max_safe_mw"), m.group(1)),
            (("ha:reservoir_2y", "first_fail_mw"), m.group(2)),
            (("co:reservoir_2y", "max_safe_mw"), m.group(3)),
            (("co:reservoir_2y", "first_fail_mw"), m.group(4)),
        ],
        "plan 表：两年末库容边界",
    ),
    (
        "plan",
        r"\| 10 年合成联合边界[^|]*\| (\d+)/(\d+) MW \| (\d+)/(\d+) MW",
        lambda m: [
            (("ha:reservoir_10y", "max_safe_mw"), m.group(1)),
            (("ha:reservoir_10y", "first_fail_mw"), m.group(2)),
            (("co:reservoir_10y", "max_safe_mw"), m.group(3)),
            (("co:reservoir_10y", "first_fail_mw"), m.group(4)),
        ],
        "plan 表：10 年合成联合边界",
    ),
    (
        "plan",
        r"\| 10 年\*{0,2}多序列\*{0,2}联合边界[^|]*\|[^|]*\|\s*\*\*(\d+) MW\*\*[^|]*\|\s*\*\*(\d+) MW\*\*",
        lambda m: [
            (("ha:reservoir_ensemble", "median_mw"), m.group(1)),
            (("co:reservoir_ensemble", "median_mw"), m.group(2)),
        ],
        "plan 表：10 年多序列联合边界中位数（T0.4）",
    ),
    (
        "plan",
        r"\| 概率分布（1024 样本，物理 CAWCC） \| P05/P50/P95 = (\d+)/(\d+)/(\d+) MW \| (\d+)/(\d+)/(\d+) MW",
        lambda m: [
            (("ha:probabilistic_physical", "p05"), m.group(1)),
            (("ha:probabilistic_physical", "p50"), m.group(2)),
            (("ha:probabilistic_physical", "p95"), m.group(3)),
            (("co:probabilistic_physical", "p05"), m.group(4)),
            (("co:probabilistic_physical", "p50"), m.group(5)),
            (("co:probabilistic_physical", "p95"), m.group(6)),
        ],
        "plan 表：1024 样本概率分布 P05/P50/P95",
    ),
    (
        "plan",
        r"\| 物理 CAWCC（日尺度，50 MW 网格） \|[^|]*\| (\d+) → (\d+) MW[^|]*\| (\d+) → (\d+) MW",
        lambda m: [
            (("ha:threshold:daily", "max_safe_mw"), m.group(1)),
            (("ha:threshold:daily", "first_fail_mw"), m.group(2)),
            (("co:threshold:daily", "max_safe_mw"), m.group(3)),
            (("co:threshold:daily", "first_fail_mw"), m.group(4)),
        ],
        "项目说明表：物理 CAWCC 日尺度",
    ),
    (
        "plan",
        r"\| 物理 CAWCC（年尺度） \|[^|]*\| (\d+) → (\d+) MW \| (\d+) → (\d+) MW",
        lambda m: [
            (("ha:threshold:physical_annual", "max_safe_mw"), m.group(1)),
            (("ha:threshold:physical_annual", "first_fail_mw"), m.group(2)),
            (("co:threshold:physical_annual", "max_safe_mw"), m.group(3)),
            (("co:threshold:physical_annual", "first_fail_mw"), m.group(4)),
        ],
        "项目说明表：物理 CAWCC 年尺度（纯物理子集）",
    ),
    (
        "plan",
        r"\|\s*全口径节水率（干冷却，EWIF 1\.8 / 4\.52）\s*\|\s*([\d.]+)% / ([\d.]+)%\s*\|\s*([\d.]+)% / ([\d.]+)%",
        lambda m: [
            (("ha:frontier", "dry_full_saving_18"), m.group(1)),
            (("ha:frontier", "dry_full_saving_452"), m.group(2)),
            (("co:frontier", "dry_full_saving_18"), m.group(3)),
            (("co:frontier", "dry_full_saving_452"), m.group(4)),
        ],
        "项目说明表：全口径节水率（干冷却，两档 EWIF）",
    ),
    (
        "plan",
        r"\|\s*站点口径高估倍数（干冷却，EWIF 4\.52）\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        lambda m: [
            (("ha:frontier", "site_overestimate_452"), m.group(1)),
            (("co:frontier", "site_overestimate_452"), m.group(2)),
        ],
        "项目说明表：站点 WUE 口径对节水效益的高估倍数",
    ),
    (
        "plan",
        r"\|\s*反转阈值 EWIF\*（干冷却，L/kWh）\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        lambda m: [
            (("ha:frontier", "ewif_star_dry"), m.group(1)),
            (("co:frontier", "ewif_star_dry"), m.group(2)),
        ],
        "项目说明表：全口径反转所需的电网水强度阈值",
    ),
    (
        "plan",
        r"\|\s*全口径每 m³ 节水碳代价（干冷却，EWIF 4\.52，EF 0\.35）\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        lambda m: [
            (("ha:frontier", "carbon_cost_dry_452"), m.group(1)),
            (("co:frontier", "carbon_cost_dry_452"), m.group(2)),
        ],
        "项目说明表：全口径节水的碳代价",
    ),
    # ---- R8：D1/D2 联合修复传播到全部情景变体后的锚点结果 ----------------
    (
        "plan",
        r"\|\s*WWTW 占 UWS 已造成 GHG 比（A08）\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        lambda m: [
            (("ha:anchor", "A08"), m.group(1)),
            (("co:anchor", "A08"), m.group(2)),
        ],
        "项目说明表：污水厂 GHG 占 UWS 总 GHG 份额（A08）",
    ),
    (
        "plan",
        r"\|\s*WWTW 占 UWS 已造成酸化比（A09）\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        lambda m: [
            (("ha:anchor", "A09"), m.group(1)),
            (("co:anchor", "A09"), m.group(2)),
        ],
        "项目说明表：污水厂酸化占 UWS 总酸化份额（A09）",
    ),
    (
        "plan",
        r"\|\s*间接水占数据中心总水足迹比（A22）\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        lambda m: [
            (("ha:anchor", "A22"), m.group(1)),
            (("co:anchor", "A22"), m.group(2)),
        ],
        "项目说明表：间接水占数据中心总水足迹份额（A22）",
    ),
    # ---- R8 预注册自查：再生水比例单域扫描（§七之七） ------------------
    (
        "plan",
        r"\|\s*再生水比例 0→0\.9 的 CoC 降幅（%）\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        lambda m: [
            (("ha:reclaim", "coc_drop_pct"), m.group(1)),
            (("co:reclaim", "coc_drop_pct"), m.group(2)),
        ],
        "项目说明表：再生水比例 0→0.9 的 CoC 降幅",
    ),
    (
        "plan",
        r"\|\s*再生水比例 0→0\.9 的每单位散热取水升幅（%）\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        lambda m: [
            (("ha:reclaim", "withdraw_rise_pct"), m.group(1)),
            (("co:reclaim", "withdraw_rise_pct"), m.group(2)),
        ],
        "项目说明表：再生水比例 0→0.9 的每单位散热取水升幅",
    ),
    (
        "plan",
        r"\|\s*再生水比例 0→0\.9 的排入下水道量升幅（%）\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)",
        lambda m: [
            (("ha:reclaim", "sewer_rise_pct"), m.group(1)),
            (("co:reclaim", "sewer_rise_pct"), m.group(2)),
        ],
        "项目说明表：再生水比例 0→0.9 的排入下水道量升幅",
    ),
]


def extract_claims(doc_key: str, text: str) -> list[dict]:
    found: list[dict] = []
    for key, pattern, resolver, desc in CLAIMS:
        if key != doc_key:
            continue
        for m in re.finditer(pattern, text):
            for (tkey, documented) in resolver(m):
                found.append(
                    {
                        "doc": doc_key,
                        "claim": desc,
                        "matched_text": m.group(0),
                        "truth_key": f"{tkey[0]}|{tkey[1]}",
                        "documented_value": float(documented),
                    }
                )
    return found


def doc_key_for(name: str) -> str:
    """Map a file name to the CLAIMS routing key.

    All narrative documents share the "plan" key; only the engine research
    guide has its own key because its figures are written as prose.
    """
    return "research" if name.startswith("AI_DATA_CENTER") else "plan"


def main() -> int:
    truth = build_truth_table()
    doc_texts: dict[str, str] = {}
    for path in DOCS:
        if path.exists():
            doc_texts[path.name] = path.read_text(encoding="utf-8")

    rows: list[dict] = []
    for name, text in doc_texts.items():
        doc_key = doc_key_for(name)
        if name.startswith("00_项目说明"):
            doc_key = "plan"
        for claim in extract_claims(doc_key, text):
            tk = claim["truth_key"].split("|")
            entry = truth.get((tk[0], tk[1]))
            if entry is None:
                verdict, truth_value, artifact = "UNTRACEABLE", None, ""
            elif entry["value"] is None:
                # A ``None`` machine value means the quantity is right-censored:
                # the scan never produced a first-failure point (e.g. the CO
                # reclaimed-water policy target).  There is no numeric value to
                # compare, so report it explicitly instead of crashing and let a
                # human confirm the document also treats it as a lower bound.
                verdict, truth_value, artifact = "CENSORED", None, entry["artifact"]
            elif abs(float(entry["value"]) - claim["documented_value"]) < 1e-6:
                verdict, truth_value, artifact = "PASS", entry["value"], entry["artifact"]
            else:
                verdict, truth_value, artifact = "MISMATCH", entry["value"], entry["artifact"]
            rows.append(
                {
                    "文档": claim["doc"],
                    "论断": claim["claim"],
                    "匹配文本": claim["matched_text"],
                    "文档值": claim["documented_value"],
                    "机器值": truth_value,
                    "判定": verdict,
                    "证据文件": artifact,
                    "真值键": claim["truth_key"],
                }
            )
        # Wording guards (not numeric): catch the phrasing traps that numeric
        # extraction cannot see.
        rows.extend(scan_forbidden(text, doc_key))

    # Also sweep the documentation for bare capacity numbers and report which
    # ones are covered by the truth table, so uncovered numbers stay visible.
    covered = {r["匹配文本"] for r in rows}
    sweep: list[dict] = []
    for name, text in doc_texts.items():
        for m in re.finditer(r"(\d{3,4})\s*MW", text):
            snippet = text[max(0, m.start() - 40): m.end() + 5].replace("\n", " ")
            sweep.append({"文档": name, "数字": float(m.group(1)), "上下文": snippet})

    with OUT.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["文档", "论断", "匹配文本", "文档值", "机器值", "判定", "证据文件", "真值键"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"论断检查 {len(rows)} 条 -> {OUT}")
    for r in rows:
        print(f"  {r['判定']:12s} {r['论断']}: 文档 {r['文档值']} / 机器 {r['机器值']}")
    print(f"文档中裸露容量数字 {len(sweep)} 处（需人工确认是否已在真值表内）")

    censored = [r for r in rows if r["判定"] == "CENSORED"]
    forbidden = [r for r in rows if r["判定"] == "FORBIDDEN_PHRASING"]
    bad = [r for r in rows if r["判定"] not in ("PASS", "CENSORED")]
    if censored:
        print(f"\n注意: {len(censored)} 条为右删失量（机器无首失点，只能作下界），已登记为非阻断。")
        for r in censored:
            print(f"  CENSORED     {r['论断']}: 文档 {r['文档值']} / 机器（右删失）")
    if forbidden:
        print(f"\n措辞门禁: {len(forbidden)} 条命中禁用表述（须改为可引用写法）：")
        for r in forbidden:
            print(f"  FORBIDDEN    {r['论断']} | 命中文本: {r['匹配文本']!r}")
    if bad:
        print(f"\nFAIL: {len(bad)} 条论断无法追溯到机器产物或命中措辞门禁")
        return 1
    print("\nOK: 已登记论断全部可追溯，措辞门禁通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
