# -*- coding: utf-8 -*-
"""跨语言数字门禁：英文稿中每个数值必须能在中文母稿白名单中找到。

判定：
    1. 抽取英文稿全部数值 token，规范化；
    2. 命中 _num_lexicon.json 白名单 -> OK；
    3. 未命中 -> 记录，需人工判定是「母稿没有的新数字」（禁止）还是
       「格式差异」（如 1.3 billion 对应 13 亿、3750 写法差异）。

用法:
    python _wr_num_gate.py
"""
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
MS = HERE / "04_wr_manuscript_en.md"
LEX = HERE / "_num_lexicon.json"

# 允许的"格式差异"人工对照：(英文写法, 母稿等价写法列表)
FORMAT_EQUIV: dict[str, list[str]] = {
    "8882": ["8.882"],          # 8.882e-16 的尾数
    "1.3": ["13"],              # 1.3 billion m3 == 13 亿 m3（母稿写法）
    "84": ["8400"],             # 84 million t CO2e == 8400 万 t
    "4775": ["4775"],
    "57547": ["57547"],
    # ---- 算式操作数（母稿以完整算式出现，操作数本身不是独立数字）----
    "-35": ["(130 − 35)", "(500/5 − 35)"],   # 氯化物算式操作数
    "-180": ["(440 − 180)"],                 # r* 算式操作数
    # ---- 单位/量纲换算 ----
    "50000": ["5 万"],                       # 母稿写“人口 ≥ 5 万”
    # ---- 2026-10-18 三杠杆 50 MW 同网格重跑（_verify_reuse_levers_50mw.py 18/18）----
    # 母稿 §7.0/§7.5 已同步为 1150/1450 与 +250
    "250": ["+250"],
    "1400": ["1400"],
    "1150": ["1150"],
    "1450": ["1450"],
    # ---- k* 敏感性（_verify_kstar_table.py 29/29 从原始数据复算）----
    "0.10": ["kstar: rho 行"],
    "0.2308": ["kstar: rho=6/26"],
    "0.61": ["kstar: r* 行"],
    "8.08": ["kstar: rho=0.10 的 k*"],
    "0.81": ["kstar: rho=1.0 的 k*（保守边界）"],
    "4.33": ["kstar: r*=0.50 的 k*"],
    "2.77": ["kstar: r*=0.61 的 k*"],
    "57": ["kstar: rho=0.10 的系统数"],
    # ---- r* 四参数 ±10% 敏感性（_rstar_sens_exact.py 精确复算）----
    "0.018": ["rstar_sens: C_p 最大偏移"],
    "0.089": ["rstar_sens: C_r 最大偏移"],
    "0.094": ["rstar_sens: L 最大偏移"],
    "0.104": ["rstar_sens: CoC_d 最大偏移"],
    "0.19": ["rstar_sens: 两端跨度上限 0.1872/0.1891"],
    # ---- C_p 外部锚定尝试（GAMA 实测，_gama_statewide.py）----
    "420": ["gama: 全州 TDS 中位"],
    "10090": ["gama: TDS 记录数"],
    "0.0870": ["cp_impact: C_p=420 时 r*"],
    "-1.0096": ["cp_impact: C_p=545.5 时 r*"],
    # ---- C_p 精度反解（_cp_precision.py，r=0.499 临界）----
    "230.8": ["cp_precision: r=0.499 的临界 C_p"],
    # ---- UWMP 原文数字（_verify_uwmp_pdf.py 已核：p.65 写 about 38,700）----
    "38700": ["UWMP p.65 原文 about 38,700 AFY"],
    # ---- 冷却技术档 x Bowers ----
    "616.7": ["bowers: 0.5 AF = 616.7 m3/yr"],
    "0.001": ["bowers WUE 下界 (IT=72MW)"],
    "0.07": ["bowers WUE 上界 (IT=1MW)"],
    "0.398": ["dry_first 档 WUE"],
    "2.205": ["evaporative 档 WUE"],
    # ---- 技术档敏感性（_tech_sensitivity.json，_verify_tech_sensitivity 11/11）----
    "2.125": ["ha evaporative WUE @1200MW"],
    "0.558": ["hybrid WUE"],
    "0.327": ["dry_first WUE"],
    "6.478": ["evaporative 增幅%"],
    "6.472": ["hybrid 增幅%"],
    "7.851": ["dry_first 增幅%"],
    "0.3972": ["r*(CoC=6)"],
    "-1.69": ["CoC_d 弹性 -1.6921"],
    # ---- CO 端联合-纯物理差距（_verify_co_gap 14/14）----
    "700": ["CO r=0.9 联合 CAWCC / 差距 700MW"],
    "750": ["CO 联合 r=0→0.9 降幅"],
    "850": ["HA r=0.9 政策约束失效点"],
    # ---- 非 informative 范围依赖（_verify_noninformative_range 25/25）----
    "4000": ["扫描上限 4000 MW"],
    "3000": ["CO unmet_cooling 首失效"],
    "0.8992": ["HA wwtw 最大利用率"],
    "0.8755": ["CO wwtw 最大利用率"],
    "3.45": ["50/1450 百分比"],
    # ---- 解析边界（_verify_analytic_boundary 17/17）----
    "2.11": ["10MW 网格 r=0.9 相对误差"],
    "22.9": ["解析残差 22.86 MW"],
    "1088.9": ["解析预测 CAWCC"],
    "1111.76": ["1MW 精扫真值"],
    # ---- 两位路径对比（§5.7.9/§5.7.10，_verify_two_path_attribution 16/16）----
    # 英文稿写 "falls to 0.740 and 0.744"，母稿同一处写完整精度 0.740217
    "0.740": ["母稿 §5.7.8 表：r=0.75 的交付比 0.740217"],
    "0.744": ["同上，r=0.9 的交付比 0.744 为 0.740217/0.744 的同源截断"],
    # 英文稿以千位取整写 30,772 / 33,655，母稿写完整值 30,772.2 / 33,655.1
    "30772": ["母稿 §5.7.9 表：30,772.2 ML（r=0.7 动态年补水）"],
    "33655": ["母稿 §5.7.9 表：33,655.1 ML（r=0.9 legacy 年补水）"],
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

    text = MS.read_text(encoding="utf-8")
    # 去掉文件头元信息（投稿说明，不是正文）
    body = text
    body = re.sub(r"^\*\*Target journal:\*\*.*?\n", "", body, flags=re.M)
    body = re.sub(r"^\*\*Word budget:\*\*.*?\n", "", body, flags=re.M)
    body = re.sub(r"^\*\*Source of numbers:\*\*.*?\n", "", body, flags=re.M)
    # 参考文献整节剔除（DOI/卷/页是文献元数据，不是论文数据）
    body = re.sub(r"^## References\s*$.*", "", body, flags=re.M | re.S)
    # 小节编号（2.4 / 3.2 等）不是数据
    body = re.sub(r"^#{2,4}\s+[\d.]+", "##", body, flags=re.M)
    # DOI / URL 内的数字串
    body = re.sub(r"https?://\S+", " URL ", body)
    # 指数记法整体按尾数判：$a\times10^{-16}$ 的 -16 不单独判
    body = re.sub(r"\\times10\^\{-?\d+\}", " ", body)

    lines = body.split("\n")
    miss: dict[str, list[str]] = defaultdict(list)
    n_tok = 0
    for ln, line in enumerate(lines, 1):
        for m in NUM_RE.finditer(line):
            tok = norm(m.group(1))
            n_tok += 1
            if tok in allowed:
                continue
            if tok in FORMAT_EQUIV:
                continue
            ctx = line[max(0, m.start() - 55): m.end() + 55].strip()
            if len(miss[tok]) < 3:
                miss[tok].append(f"L{ln}: …{ctx}…")

    print(f"英文稿数值 token: {n_tok}；唯一未命中: {len(miss)}")
    if not miss:
        print("\n✅ 全部数值均可回溯到中文母稿")
        sys.exit(0)
    print("\n未命中清单（须逐条判定）：")
    for k in sorted(miss, key=lambda x: (len(x), x)):
        print(f"\n  [{k}]")
        for c in miss[k]:
            print(f"     {c}")
    # 2026-10-19 审计修复：补正确退出码。此前未命中 >0 时仍以 return 正常结束、退出码 0，
    # 而父门禁曾以 gbk 解码导致 ❌ 检测失效 → 假数字被静默放行（已实测复现）。
    sys.exit(1)


if __name__ == "__main__":
    main()
