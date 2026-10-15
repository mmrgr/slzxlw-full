"""A28: 修正 SI 中 A27 切换后残留的旧数字与损坏 LaTeX。"""
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "A16_英文稿" / "supplementary_information.md"
s = p.read_text(encoding="utf-8")

# 1. q 组表 -> 引用限值权威数字
old_q = (
    "| $q$ group | n | withdrawal falls | withdrawal rises | median $dS_{\\rm pot}$ |\n"
    "|---|---:|---:|---:|---:|\n"
    "| $q>0$ | 349 | **349** | **0** | \u221214,325 |\n"
    "| $q\\approx0$ | 326 | 208 | 38 | \u22125,590 |\n"
    "| $q<0$ | 477 | 192 | 285 | +1,907 |\n"
    "\n"
    "**$q>0$ is sufficient for a city-level benefit (349/349, no exception).**"
)
new_q = (
    "| $q$ group | n | withdrawal falls | withdrawal rises | median $dS_{\\rm pot}$ |\n"
    "|---|---:|---:|---:|---:|\n"
    "| $q>0$ | 290 | **290** | **0** | \u221214,496 |\n"
    "| $q\\approx0$ | 288 | 208 | 0 | \u22127,651 |\n"
    "| $q<0$ | 235 | 133 | 102 | \u22124,259 |\n"
    "\n"
    "**$q>0$ is sufficient for a city-level benefit (290/290, no exception).**\n"
    "\n"
    "> Figures are the **A27 cited-limit** run (reliable subset $n=813$). The superseded\n"
    "> placeholder-limit figures were 349 / 326 / 477 with 285 harmful cases."
)
assert old_q in s, "q 组表未匹配"
s = s.replace(old_q, new_q, 1)

# 2. S3.0 残差表 (含损坏 LaTeX 与旧数字) -> 整段替换
start = s.index("**Effect on headline numbers (main grid)**")
end = s.index("> **An algebraic relation cannot certify its own inputs.**")
new_tbl = (
    "**Effect on headline numbers (main grid)**\n"
    "\n"
    "| quantity | all | reliable only |\n"
    "|---|---:|---:|\n"
    "| scenarios | 1,052 | **813** |\n"
    "| $dS_{\\rm pot}<0$ | \u2014 | **631** |\n"
    "| $dS_{\\rm pot}>0$ | \u2014 | **102** |\n"
    "| zero-displacement | \u2014 | 372 |\n"
    "| $q>0$ | \u2014 | **290** |\n"
    "| $q>0$ but harmful | **0** | **0** |\n"
    "| criterion agreement | 1.0000 | **1.0000** |\n"
    "| identity residual (ML) | \u2014 | **2.55e\u221211** |\n"
    "\n"
    "> This table reflects the **A27 cited-limit** run. The earlier placeholder-limit run gave\n"
    "> scenarios 1,152 / reliable 1,094, $dS<0$ 729, $dS>0$ 285, zero-displacement 441,\n"
    "> $q>0$ 329, residual 1.16e\u221210. Both runs agree on the two qualitative facts that\n"
    "> matter: criterion agreement is exactly 1.0000, and there are **zero**\n"
    "> $q>0$-but-harmful cases.\n"
    "\n"
)
s = s[:start] + new_tbl + s[end:]

p.write_text(s, encoding="utf-8")
print("[fixed] SI: q 组表 + S3.0 表 + 损坏 LaTeX")
