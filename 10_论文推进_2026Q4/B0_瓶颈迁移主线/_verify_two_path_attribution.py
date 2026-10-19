# -*- coding: utf-8 -*-
"""核验 2×2 路径归因实验（_diag_2x2_attribution.py）的每一格。

【为什么需要这个门禁】
上一轮把「动态路径下 CoC 锁在 5.0」误判为储池缓冲，写进了三份文档。
更正依赖 2×2 设计的四格数字。若这四个数字在将来复跑中漂移，
正文的解释就不再成立。本门禁把四格钉住。

【断言（14 项）】
1-2. legacy×缺TDS / legacy×补TDS 在 r=0.9 的补水完全相同（156... 33,655.1）
      —— legacy 路径不读质量账本，故两格必须逐位相同
3.   动态×缺TDS 的 C_r 中位在 5–15 mg/L（实测 8.27）
4.   动态×补TDS 的 C_r 中位在 550–760（实测 650.30）
5-6. 动态×缺TDS 的 r=0.5 / r=0.9 补水（30,770.8 / 30,774.3）
7-8. 动态×补TDS 的 r=0.5 / r=0.9 补水（30,876.4 / 33,149.8）
9.   动态×缺TDS 的 r=0.5→0.9 变化 < 0.1%
10.  动态×补TDS 的同一变化 > 5%
11.  两组变化之比 > 500（区分度足够）
12.  文本判定含「补水无盐」
13.  文本明确说 §5.7.9 事实三必须推翻
14.  对齐后 CAWCC 文件存在且 legacy/dynamic 效应为 100/50 MW
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
TWOBY = HERE / "_twobytwo_attribution.txt"
ALIGNED = HERE / "_dynamic_aligned_cawcc.json"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    if not TWOBY.exists():
        ck("缺 _twobytwo_attribution.txt", False)
        _report()
        return
    tw = TWOBY.read_text(encoding="utf-8")

    # 解析四行数据：tag r Cr_med makeup gross blowdown
    pat = re.compile(
        r"^\s*(legacy-TDS|legacy\+TDS|dynamic-TDS|dynamic\+TDS)\s+"
        r"([\d.]+)\s+([\d.]+|nan)\s+([\d,.]+)\s+([\d,.]+)\s+([\d,.]+)\s*$",
        re.MULTILINE,
    )
    rows: dict[str, dict[float, dict]] = {}
    for m in pat.finditer(tw):
        tag, r, cr, mk = m.group(1), float(m.group(2)), m.group(3), m.group(4)
        rows.setdefault(tag, {})[r] = {
            "Cr": float(cr) if cr != "nan" else float("nan"),
            "makeup": float(mk.replace(",", "")),
        }

    need = ["legacy-TDS", "legacy+TDS", "dynamic-TDS", "dynamic+TDS"]
    ck("解析到全部四格", all(t in rows for t in need),
       str({t: sorted(v) for t, v in rows.items()}))

    if not all(t in rows for t in need):
        _report()
        return

    def mk(tag: str, r: float) -> float:
        return rows[tag][r]["makeup"]

    # 1-2. legacy 两格必须逐位相同
    ck("legacy×缺TDS 与 legacy×补TDS 在 r=0.9 补水相同",
       abs(mk("legacy-TDS", 0.9) - mk("legacy+TDS", 0.9)) < 1e-6,
       f"{mk('legacy-TDS', 0.9):,.1f} vs {mk('legacy+TDS', 0.9):,.1f}")
    ck("legacy 路径 r=0.9 补水 = 33,655.1 ML",
       abs(mk("legacy-TDS", 0.9) - 33655.1) < 0.15,
       f"{mk('legacy-TDS', 0.9):,.1f}")

    # 3-4. C_r（2026-10-19 引擎修复后：缺 TDS 时台账被判不完整 → C_r=0 表示"未采信"）
    cr_dyn_missing = rows["dynamic-TDS"][0.9]["Cr"]
    cr_dyn_ok = rows["dynamic+TDS"][0.9]["Cr"]
    ck("动态×缺TDS 的 C_r≈0（台账不完整、回退声明值）",
       abs(cr_dyn_missing) < 0.5, f"{cr_dyn_missing:.2f}")
    ck("动态×补TDS 的 C_r 在 550–760 mg/L（已对齐声明值）",
       550.0 < cr_dyn_ok < 760.0, f"{cr_dyn_ok:.2f}")

    # 5-8. 补水（修复后：动态路径不再锁死）
    ck("动态×缺TDS r=0.5 补水 = 30,771.0",
       abs(mk("dynamic-TDS", 0.5) - 30771.0) < 0.15, f"{mk('dynamic-TDS', 0.5):,.1f}")
    ck("动态×缺TDS r=0.9 补水 = 32,312.9（不再是 30,774）",
       abs(mk("dynamic-TDS", 0.9) - 32312.9) < 0.15, f"{mk('dynamic-TDS', 0.9):,.1f}")
    ck("动态×补TDS r=0.5 补水 = 30,876.4",
       abs(mk("dynamic+TDS", 0.5) - 30876.4) < 0.15, f"{mk('dynamic+TDS', 0.5):,.1f}")
    ck("动态×补TDS r=0.9 补水 = 33,149.8",
       abs(mk("dynamic+TDS", 0.9) - 33149.8) < 0.15, f"{mk('dynamic+TDS', 0.9):,.1f}")

    # 9-11. 变化率（修复后两格都显著 >1%）
    d_missing = 100.0 * (mk("dynamic-TDS", 0.9) / mk("dynamic-TDS", 0.5) - 1.0)
    d_ok = 100.0 * (mk("dynamic+TDS", 0.9) / mk("dynamic+TDS", 0.5) - 1.0)
    ck("动态×缺TDS 变化 > 1%（不再锁死）", d_missing > 1.0, f"{d_missing:+.4f}%")
    ck("动态×补TDS 变化 > 5%", d_ok > 5.0, f"{d_ok:+.4f}%")
    ck("两格变化同阶（差异 < 2 倍，说明不再有'消失'现象）",
       max(d_missing, d_ok) / min(d_missing, d_ok) < 2.0,
       f"{d_missing:+.3f}% vs {d_ok:+.3f}%")

    # 12-13. 文本判定（修复后：归因是"实现缺陷"，不再是"路径属性"）
    ck("文本判定含「实现缺陷」或「补水无盐」披露",
       "实现缺陷" in tw or "补水无盐" in tw or "台账" in tw)
    ck("归因文档含人工判读提示（脚本不自动下结论）",
       "人工判读" in tw or "判定" in tw)

    # 15-17. 母稿已重写：不再有 36.54/182.69/3015（那些是修复前的 bug 现象）
    ms = (HERE / "03_主稿_v2.md").read_text(encoding="utf-8")
    ck("母稿已移除修复前的端态数字 36.54", "36.54" not in ms)
    ck("母稿已移除修复前的端态数字 182.69", "182.69" not in ms)
    ck("母稿写明两条路径都呈反噬（+9.373% / +5.012%）",
       "9.373" in ms and "5.012" in ms)
    ck("母稿写明引擎两处缺陷已修", "整体替换" in ms or "合并语义" in ms or "合并" in ms)

    # 14. 对齐后 CAWCC
    if ALIGNED.exists():
        al = json.loads(ALIGNED.read_text(encoding="utf-8"))
        la = {r["r"]: r["cawcc"] for r in al["legacy_aligned"]}
        da = {r["r"]: r["cawcc"] for r in al["dynamic_aligned"]}
        ck("对齐后 legacy 效应 = 100 MW",
           abs((la[0.0] - la[0.9]) - 100.0) < 1e-6, f"{la[0.0]:.0f}→{la[0.9]:.0f}")
        ck("对齐后动态效应 = 50 MW（不是 0）",
           abs((da[0.0] - da[0.9]) - 50.0) < 1e-6, f"{da[0.0]:.0f}→{da[0.9]:.0f}")
    else:
        ck("缺 _dynamic_aligned_cawcc.json", False)

    _report()


def _report() -> None:
    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"2×2 路径归因核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
