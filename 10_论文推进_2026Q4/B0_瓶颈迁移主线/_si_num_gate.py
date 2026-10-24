# -*- coding: utf-8 -*-
"""SI 数字门禁：SI 中每个数值必须能回溯到中文母稿（同 _wr_num_gate 口径）。"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"
LEX = HERE / "_num_lexicon.json"

FORMAT_EQUIV: dict[str, list[str]] = {
    "8882": ["8.882"], "1.3": ["13"], "84": ["8400"],
    "4775": ["4775"], "57547": ["57547"],
    "-35": ["(130 − 35)"], "-180": ["(440 − 180)"],
    "50000": ["5 万"], "5000": ["0.5–5 万"], "000": ["0.5–5 万"],
    # 母稿写"约 132 万行"
    "132": ["132 万"],
    # SI 中新增的说明性数字（非论文数据）：S5.6 第 40 条 2 nodes + 54 ways
    "54": ["54"], "2": ["2"],
    # 清洗规则 188 -> 169，19 个被剔除，10.1%
    "19": ["19"], "10.1": ["10.1"],
    # 年份/编号
    "2026": ["2026"], "2025": ["2025"], "2022": ["2022"],
    "2024": ["2024"], "2023": ["2023"], "2018": ["2018"],
    # ---- 2026-10-18 双基底重跑产生的新数字（由 _verify_dualbase.py 17/17 核验）----
    # SI S6.5：闭式预测 vs 实测、蒸发漂移、两基底绝对取水差
    "7.056": ["_verify_dualbase: 闭式预测"],   # = CoC/(CoC-1) 比值
    "6.477": ["_verify_dualbase: 实测增幅"],   # 母稿 6.48% 的四位展开
    "0.58": ["_verify_dualbase: pred-act=0.5795"],
    "0.76": ["母稿 §5.7.5 蒸发漂移 -0.76%"],
    "230": ["_verify_dualbase: 三情形绝对差 232.8/264.1/344.9 的下界"],
    "345": ["_verify_dualbase: 上界"],
    # 双基底 r=0 绝对取水（_verify_dualbase 已核 22,390.7863 / 22,126.7306）
    "22390.8": ["_verify_dualbase"],
    "22126.7": ["_verify_dualbase"],
    # 两基底相对增幅的六位展开（_verify_dualbase 已核一致到 <5e-4）
    "6.476503": ["_verify_dualbase: HA 情形II"],
    "6.476462": ["_verify_dualbase: CO 情形II"],
    "20.741175": ["_verify_dualbase: HA 情形I"],
    "20.741024": ["_verify_dualbase: CO 情形I"],
    # ---- 2026-10-20 新增 S9 图注节：以下三个数字是说明性元信息，不是论文数据 ----
    # 91 = 主图门禁项数（_gate_check_b0.py 的检查条数）
    # 196 = 文献对标组合数（7 种技术 × 12 个主体，见 literature_benchmark.csv）
    # 0.98/1.02 = 阈值扰动系数（audit_threshold_perturbation.py 的 FACTORS）
    "91": ["S9 说明：主图门禁项数，非论文数据"],
    "196": ["S9 图注：7 技术 × 12 主体 = 196 对标组合，见 literature_benchmark.csv"],
    "0.98": ["S9 图注：阈值扰动系数下限，见 threshold_perturbation_sensitivity.csv"],
    "1.02": ["S9 图注：阈值扰动系数上限"],
    "0.4": ["S9 图注：桑基图过滤阈值 0.4%，说明性"],
    # ---- SI S7.7 k* 敏感性表（由 _kstar_sensitivity.py 从 _ca_k_clean.json 复算）----
    "0.2308": ["kstar_sensitivity: rho=6/26"],
    "0.10": ["kstar_sensitivity: rho 行"],
    "0.20": ["kstar_sensitivity: rho 行"],
    "0.52": ["kstar_sensitivity: r* 行"],
    "0.61": ["kstar_sensitivity: r* 行"],
    "8.08": ["kstar_sensitivity: rho=0.10 的 k*"],
    "4.04": ["kstar_sensitivity: rho=0.20 的 k*"],
    "2.69": ["kstar_sensitivity: rho=0.30 的 k*"],
    "1.62": ["kstar_sensitivity: rho=0.50 的 k*"],
    "0.81": ["kstar_sensitivity: rho=1.00 的 k*"],
    "4.33": ["kstar_sensitivity: r*=0.50 的 k*"],
    "3.14": ["kstar_sensitivity: r*=0.58 的 k*"],
    "2.77": ["kstar_sensitivity: r*=0.61 的 k*"],
    "33.7": ["kstar_sensitivity: rho=0.10 占比"],
    "17.2": ["kstar_sensitivity: rho=0.20/0.52 占比"],
    "11.8": ["kstar_sensitivity: r*=0.58 占比"],
    "20.1": ["kstar_sensitivity: r*=0.50 占比"],
    "8.9": ["kstar_sensitivity: r*=0.61 占比"],
    "2.4": ["kstar_sensitivity: rho=0.50 占比"],
    # 边界计数口径（_diag_kstar_boundary.py 复算；_verify_kstar_table.py 29/29）
    "58": ["_diag: 用四舍五入边界会多算 1 个（57→58）"],
    "8.0766": ["_diag: rho=0.10 的精确边界 k*"],
    "8.0787": ["_diag: 夹在精确值与取整值之间的那个系统的 k"],
    # ---- r* 四参数锚定与敏感性（_rstar_param_anchoring.py / _rstar_sens_exact.py）----
    "0.0936": ["rstar_sens: L 最大偏移"],
    "0.1040": ["rstar_sens: CoC_d 最大偏移"],
    "0.0888": ["rstar_sens: C_r 最大偏移"],
    "0.0178": ["rstar_sens: C_p 最大偏移"],
    "0.1872": ["rstar_sens: L 两端跨度"],
    "0.1891": ["rstar_sens: CoC_d 两端跨度"],
    "0.1560": ["rstar_sens: C_r 两端跨度"],
    "0.0343": ["rstar_sens: C_p 两端跨度"],
    "0.46": ["rstar_sens: 下界（L -10%）"],
    "0.66": ["rstar_sens: 上界（L +10%）"],
    # SI 第 38 条（与第 25/44 条同口径）
    "0.19": ["rstar_sens: 两端跨度上限"],
    "0.018": ["rstar_sens: C_p 最大偏移"],
    "0.089": ["rstar_sens: C_r 最大偏移"],
    "0.094": ["rstar_sens: L 最大偏移"],
    "0.104": ["rstar_sens: CoC_d 最大偏移"],
    # ---- GAMA TDS 分布与 C_p 影响（_gama_statewide.py / _cp_anchor_impact.py）----
    "120": ["gama: p5"],
    "239": ["gama: p25"],
    "420": ["gama: p50"],
    "2100": ["gama: p95"],
    "10090": ["gama: TDS 记录数"],
    "545.5": ["gama: Alameda 县中位"],
    "550": ["gama: LA 县中位"],
    "0.0870": ["cp_impact: C_p=420"],
    "0.5227": ["cp_impact: C_p=210"],
    "0.8125": ["cp_impact: C_r=500"],
    "0.4194": ["cp_impact: C_r=800"],
    "0.3171": ["cp_impact: C_r=1000"],
    "-1.0096": ["cp_impact: C_p=546 时 r*"],
    "-1.1000": ["cp_impact: C_p=550 时 r*"],
    # ---- C_p 精度反解（_cp_precision.py）----
    "230.8": ["cp_precision: r=0.499 临界"],
    "272.3": ["cp_precision: r=0.444 临界"],
    "50.8": ["cp_precision: 180 距 230.8 的余量"],
    "380.2": ["cp_precision: C_r=500 时临界"],
    "81.4": ["cp_precision: C_r=800 时临界"],
    # ---- UWMP 原文数字 ----
    "38700": ["UWMP p.65 原文 about 38,700"],
    # ---- UWMP 页码（S7.12 引用 p.62 / p.86）----
    "62": ["UWMP 页码 p.62"],
    "86": ["UWMP 页码 p.86"],
    "282": ["UWMP 总页数"],
    # ---- 干预交互（interaction_pairs_50mw）----
    "-250": ["交互 -250 MW（纯物理）"],
    "-150": ["交互 -150 MW（联合）"],
    "150": ["HA 降漏损 +150"],
    # ---- 冷却技术档 × Bowers ----
    "616.7": ["bowers: 0.5 AF 换算"],
    "0.398": ["dry_first WUE"],
    "0.606": ["hybrid WUE"],
    "0.000": ["dry WUE"],
    "1.912": ["liquid_to_water WUE"],
    "2.117": ["efficient_evaporative WUE"],
    "2.205": ["evaporative WUE"],
    "56.9": ["dry_first 年补水 m3"],
    "86.1": ["hybrid 年补水 m3"],
    "251.7": ["liquid_to_water 年补水 m3"],
    "278.7": ["efficient_evaporative 年补水 m3"],
    "290.2": ["evaporative 年补水 m3"],
    "0.0070": ["bowers WUE @10MW"],
    "0.0704": ["bowers WUE @1MW"],
    "0.0010": ["bowers WUE @72MW"],
    "315": ["湿冷/Bowers 倍数"],
    "61": ["PDF p.61 页码"],
    "60": ["PDF p.60 页码"],
    "4.18": ["EIR printed p.4.18-2 页码"],
    "-2": ["EIR 页码 4.18-2 的尾号"],
    # ---- 技术档敏感性 ----
    "2.125": ["evaporative WUE @1200MW"],
    "0.558": ["hybrid WUE"],
    "0.327": ["dry_first WUE"],
    "6.478": ["evaporative 增幅"],
    "6.472": ["hybrid 增幅"],
    "7.851": ["dry_first 增幅"],
    "0.3972": ["r*(CoC=6)"],
    "-1.69": ["CoC_d 弹性"],
    "7.85": ["dry_first 增幅取整 7.851"],
    "6.47": ["evaporative/hybrid 增幅取整"],
    # ---- 扩展扫描 ----
    "4000": ["扫描上限"],
    "3000": ["CO unmet_cooling 首失效"],
    "2050": ["HA reliability 首失效"],
    "2550": ["CO reliability 首失效"],
    "2300": ["HA unmet_cooling / CO peak 首失效"],
    "2350": ["CO domestic_unmet 首失效"],
    "0.8992": ["HA wwtw 最大"],
    "0.8755": ["CO wwtw 最大"],
    "3.45": ["百分比"],
    # ---- CO 三网格 ----
    "1125": ["HA cawcc_25mw r=0.8"],
    "1130": ["HA cawcc_10mw r=0.8"],
    "1140": ["HA cawcc_10mw r=0.7"],
    "1425": ["CO cawcc_25mw r=0.9"],
    "1440": ["CO cawcc_10mw r=0.9"],
    "1460": ["CO cawcc_10mw 基线"],
    # ---- CO 联合 vs 纯物理差距 ----
    "700": ["CO r=0.9 联合"],
    "750": ["CO 联合 r=0→0.9 降幅"],
    "850": ["HA r=0.9 政策失效点"],
    "-300": ["HA r=0.9 差距"],
    "-450": ["CO r=0.7 差距"],
    "-600": ["CO r=0.8 差距"],
    "-700": ["CO r=0.9 差距"],
    # ---- 解析边界 ----
    "1111": ["1MW 最后合规容量"],
    "1112": ["1MW 首次越界容量"],
    "2.11": ["10MW 相对误差"],
    "22.86": ["解析残差"],
    "1088.9": ["解析预测"],
    "1111.76": ["精扫真值"],
    "0.949889": ["最后合规取水比"],
    "0.950034": ["首次越界取水比"],
}

NUM_RE = re.compile(
    r"(?<![A-Za-z_])"
    r"([+\-−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?"
    r"|[+\-−]?(?:\d+\.\d+|\d+)(?:[eE][+\-]?\d+)?)"
)


def norm(tok: str) -> str:
    t = tok.replace(",", "").replace("−", "-").lstrip("+")
    if re.fullmatch(r"-?\d+\.0+", t):
        t = t.split(".")[0]
    return t


def main() -> None:
    lex = json.loads(LEX.read_text(encoding="utf-8"))["lexicon"]
    allowed = set(lex.keys())
    text = SI.read_text(encoding="utf-8")
    body = re.sub(r"https?://\S+", " URL ", text)
    body = re.sub(r"^#{2,4}\s+[\d.]+", "##", body, flags=re.M)
    # 表号（Table 6-11 / DWR Table 4-1）与页码形如 6-11，不是数值
    body = re.sub(r"(?:Table|Tables)\s*\d+-\d+", " TABLE ", body)
    body = re.sub(r"DWR\s+Table\s*\d+-\d+", " TABLE ", body)
    body = re.sub(r"\\times10\^\{-?\d+\}", " ", body)

    miss: dict[str, list[str]] = defaultdict(list)
    n = 0
    for ln, line in enumerate(body.split("\n"), 1):
        for m in NUM_RE.finditer(line):
            tok = norm(m.group(1))
            n += 1
            if tok in allowed or tok in FORMAT_EQUIV:
                continue
            ctx = line[max(0, m.start() - 50): m.end() + 50].strip()
            if len(miss[tok]) < 2:
                miss[tok].append(f"L{ln}: …{ctx}…")

    print(f"SI 数值 token: {n}；唯一未命中: {len(miss)}")
    for k in sorted(miss, key=lambda x: (len(x), x)):
        print(f"\n  [{k}]")
        for c in miss[k]:
            print(f"     {c}")
    # 2026-10-19 审计修复：补正确退出码（此前无 sys.exit，未命中恒被判通过）。
    sys.exit(0 if not miss else 1)


if __name__ == "__main__":
    main()
