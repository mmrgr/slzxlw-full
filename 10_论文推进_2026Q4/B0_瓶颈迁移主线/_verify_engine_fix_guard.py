# -*- coding: utf-8 -*-
"""新增门禁：引擎修复的回归守卫（_verify_engine_fix_guard.py）。

断言三件事：
  A. 引擎修复仍然生效（动态路径 CoC 不再锁 5.0）
  B. 修复对 legacy 主流程零影响（关键不变量保持不变）
  C. 论文三份文档已同步到修复后的数值（不再含旧值）

设计原则：用**最小运行**（单点 r 扫描，不跑全容量扫描）保证门禁快速，
核心判断靠"数值是否落在预期区间"，而非逐位比对（那样太慢）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


_cache: dict = {}


def run(r: float, enable: bool) -> dict:
    key = (r, enable)
    if key in _cache:
        return _cache[key]
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    dc = proj["components"]["AI_DC1"]
    dc["quality_state_enabled"] = enable
    dc["water_sources"]["reclaimed"]["target_fraction"] = r
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - r
    dc["installed_it_capacity_mw"] = 1100.0
    dc.pop("capacity_schedule", None)
    res = FullAIUWMModel(proj, ts).run()
    d = res.data_center_daily
    out = {
        "makeup": float(pd.to_numeric(d["external_makeup_ml"], errors="coerce").sum()),
        "coc_mean": float(pd.to_numeric(d["cycles_of_concentration"], errors="coerce").mean()),
    }
    _cache[key] = out
    return out


def main() -> None:
    # ---------- A. 引擎修复仍生效 ----------
    d07 = run(0.7, True)
    d09 = run(0.9, True)
    ck("A1 动态路径 CoC r=0.7 不再锁在 5.0",
       abs(d07["coc_mean"] - 4.3709) < 0.02, f"{d07['coc_mean']:.4f}")
    ck("A2 动态路径 CoC r=0.9 = 4.1364（非 4.9981）",
       abs(d09["coc_mean"] - 4.1364) < 0.02, f"{d09['coc_mean']:.4f}")
    chg = 100.0 * (d09["makeup"] / d07["makeup"] - 1.0)
    # r=0.7→0.9 区间内 CoC 已接近设计值下限，增幅小于 0.5→0.9 的全区间，
    # 故此处只断言"仍为正且非零"，全区间幅度由 A4 断言。
    ck("A3 动态路径补水仍随 r 上升（非零）", chg > 0.5, f"{chg:+.3f}%（r=0.7→0.9）")
    d05 = run(0.5, True)
    chg_full = 100.0 * (d09["makeup"] / d05["makeup"] - 1.0)
    ck("A4 动态路径 r=0.5→0.9 补水变化 ≈ +5.012%（不再是 +0.011%）",
       abs(chg_full - 5.012) < 0.15, f"{chg_full:+.3f}%")

    # ---------- B. legacy 主流程不受影响 ----------
    l07 = run(0.7, False)
    l09 = run(0.9, False)
    ck("B1 legacy CoC r=0.7 仍为 4.3222（与解析式一致）",
       abs(l07["coc_mean"] - 4.3222) < 1e-3, f"{l07['coc_mean']:.4f}")
    ck("B2 legacy CoC r=0.9 仍为 3.6484",
       abs(l09["coc_mean"] - 3.6484) < 1e-3, f"{l09['coc_mean']:.4f}")
    ck("B3 legacy 补水 r=0.7 = 31,923.9 ML",
       abs(l07["makeup"] - 31923.9) < 0.2, f"{l07['makeup']:,.1f}")
    ck("B4 legacy 补水 r=0.9 = 33,655.1 ML",
       abs(l09["makeup"] - 33655.1) < 0.2, f"{l09['makeup']:,.1f}")
    lchg = 100.0 * (l09["makeup"] / l07["makeup"] - 1.0)
    ck("B5 legacy r=0.7→0.9 变化 = +5.42%（主结论链）",
       5.0 < lchg < 6.0, f"{lchg:+.3f}%")

    # 两条路径方向一致（这是修复后最重要的定性结论）
    ck("B6 两条路径的反噬方向一致（都为正）", chg > 0 and lchg > 0,
       f"dynamic {chg:+.2f}% / legacy {lchg:+.2f}%")

    # ---------- C. 文档已同步 ----------
    ms = MS.read_text(encoding="utf-8")
    en = EN.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")

    # 旧值只允许出现在"修订说明"语境中（母稿需记录此前报告过什么）。
    # 判定：每个旧值出现处的**前 200 字符**内须含修订语（此前/上一版本/撤回/曾/更正）。
    import re as _re

    def stale_ok(txt: str, needle: str) -> bool:
        for m in _re.finditer(_re.escape(needle), txt):
            ctx = txt[max(0, m.start() - 200): m.start()]
            if not any(k in ctx for k in ("此前", "上一版本", "撤回", "曾报告",
                                          "更正", "旧", "earlier", "previous", "previously")):
                return False
        return True

    for label, txt in (("母稿", ms), ("英文稿", en), ("SI", si)):
        for needle in ("4.9991", "4.9981", "0.011%"):
            ck(f"C  {label}：{needle} 仅出现在修订语境",
               stale_ok(txt, needle), needle)

    ck("C  母稿含修复后动态 CoC 4.1364", "4.1364" in ms)
    ck("C  母稿含修复后变化 +5.012%", "5.012" in ms)
    ck("C  英文稿含修复后变化 5.012", "5.012" in en)
    ck("C  母稿写明两处代码根因", "整体替换" in ms and "合并" in ms)
    ck("C  母稿保留 legacy 主结论 +9.373%", "9.373" in ms)

    # ---------- 输出 ----------
    npass = sum(1 for _, ok, _ in RES if ok)
    print("=" * 78)
    print(f"引擎修复回归守卫　通过 {npass}/{len(RES)}")
    print("=" * 78)
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
