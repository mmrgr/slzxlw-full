"""修正 SI 中 'A high-salinity source reverses the sign' 的误导性标题 (2026-10-17).

该标题把"高盐度使符号翻转"当作已证结论, 但:
  · 真正的机制是"组成接近限值 ⇒ 质量惩罚抵消挤占增益";
  · 且"最有害的组成恰是最不完整的样本(silica 缺失)", 不应据其下强结论;
  · 主稿已改为更精确的表述"One composition is genuinely adverse, and it is the saltiest one"。
本脚本把 SI 改为同一口径, 并补上 SI 版的组成论述。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = Path(__file__).resolve().parent.parent / "A16_英文稿/supplementary_information.md"
t = P.read_text(encoding="utf-8")

OLD = "**A high-salinity source reverses the sign.** Tiers:"
NEW = """**The highest-salinity composition is the only net-adverse one.** Read the table as a
mechanism, not as four equivalent panels: the identity of §S2 splits the outcome into a
displacement gain and a quality penalty, and a composition whose dissolved solids sit close to
the admissible limit (TDS 1,378 vs 2,200 mg/L) drives the penalty up until it offsets the gain.
Figshare RW is therefore the only composition with harmful outcomes outnumbering beneficial
ones (105 vs 102), while the two fully characterised lower-salinity real compositions favour
the city decisively (LADWP 186 vs 8; IEUA 151 vs 56).

Two cautions attach to that statement. (i) The "reclaimed cooling is beneficial" reading and
its opposite are **both correct within this grid**, separated by composition — which is why no
single facility-level number settles the question. (ii) The adverse composition is also the
least completely characterised (silica absent), so its 105/102 split is the panel most
sensitive to further sample data; **we flag it rather than rely on it**, and no headline claim
rests on it. Do **not** read this as "high salinity generally reverses the sign" — the series
here is four compositions with confounded salinity and completeness, not a controlled salinity
scan.

Tiers:"""
assert OLD in t, "锚点未找到"
t = t.replace(OLD, NEW, 1)
P.write_text(t, encoding="utf-8")
print("SI 组成论述已改写")
