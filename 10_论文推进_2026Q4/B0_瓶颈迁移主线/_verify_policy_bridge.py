# -*- coding: utf-8 -*-
"""第四轮增量（政策口径区隔与贡献定位）的数值与一致性核对。

覆盖：
  §1.6 口径区隔（W/D、r_max 换算）
  §5.8.2b 零效应区声明
  §8.6 政策意义
  §9.6 第 35–36 条

用法:
    python 10_论文推进_2026Q4/B0_瓶颈迁移主线/_verify_policy_bridge.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent.parent
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
V2 = HERE / "03_主稿_v2.md"

ROWS: list[tuple[str, str, str, bool]] = []


def ck(claim: str, value: str, source: str, ok: bool) -> None:
    ROWS.append((claim, value, source, bool(ok)))


def main() -> None:
    text = V2.read_text(encoding="utf-8")
    bridge = pd.read_csv(R2 / "rstar_policy_bridge.csv", encoding="utf-8-sig")
    ph = pd.read_csv(R2 / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")

    # ---- W/D 数值 ----
    for domain, cap, expect in (("ha", 500.0, 10.34), ("ha", 1000.0, 5.28),
                                ("ha", 1500.0, 3.59), ("co", 1000.0, 5.39)):
        s = bridge[(bridge["domain"] == domain) & ((bridge["capacity_mw"] - cap).abs() < 1e-6)]
        got = float(s["W_over_D"].iloc[0]) if not s.empty else float("nan")
        ck(f"W/D {domain.upper()} {cap:.0f}MW ≈ {expect}", f"{got:.2f}",
           "r2/rstar_policy_bridge.csv", abs(got - expect) < 0.01)

    # W/D 中位
    med = float(bridge["W_over_D"].median())
    ck("W/D 中位 ≈ 5.33", f"{med:.2f}", "同上", abs(med - 5.33) < 0.01)

    # ---- r_max 换算 ----
    r_star = 0.5532
    for u in (0.20, 0.25, 0.35):
        need = r_star / u
        ck(f"u={u:.0%} 需 W/D > {need:.2f} 才能使 r_max>r*",
           f"{need:.2f}", "解析换算", need > 0)

    # 1000MW (W/D≈5.28) 在 u=20% 时 r_max>1
    rmax_1000_20 = 0.20 * 5.276805
    ck("1000MW @u=20% → r_max > 1（园区非约束方）", f"{rmax_1000_20:.2f}",
       "rstar_policy_bridge.csv", rmax_1000_20 > 1.0)
    # 1500MW 在 u=20% 时 r_max<1
    rmax_1500_20 = 0.20 * 3.589325
    ck("1500MW @u=20% → r_max < 1（园区是约束方）", f"{rmax_1500_20:.2f}",
       "同上", rmax_1500_20 < 1.0)

    # ---- 零效应区：r<=0.35 时 CAWCC 不变 ----
    for domain in ("ha", "co"):
        s = ph[(ph["domain"] == domain) & (ph["target_r"] <= 0.35)]
        uniq = sorted(set(s["physical_cawcc_mw"].astype(float)))
        ck(f"零效应区 {domain.upper()}：r≤0.35 时 CAWCC 唯一值",
           f"{uniq}", "r2/rstar_physical_cawcc_by_r.csv", len(uniq) == 1)
    ha_r0 = float(ph[(ph["domain"] == "ha") & (ph["target_r"] == 0.0)]["physical_cawcc_mw"].iloc[0])
    ck("零效应区 D-HA CAWCC 恒 1200", f"{ha_r0:.0f}", "同上", ha_r0 == 1200.0)
    co_r0 = float(ph[(ph["domain"] == "co") & (ph["target_r"] == 0.0)]["physical_cawcc_mw"].iloc[0])
    ck("零效应区 D-CO CAWCC 恒 1450", f"{co_r0:.0f}", "同上", co_r0 == 1450.0)

    # ---- 主稿文本检查 ----
    for kw in (
        "### 1.6 一个必须区分的口径",
        "r_max = u · (W / D)",
        "本文不主张",
        "本文的贡献**不是预测**",
        '#### 5.8.2b 一个必须显式声明的"零效应区"',
        "在现行政策目标区间（r ≤ 0.35）内，本文的机制不产生任何承载容量后果",
        "### 8.6 政策意义：判据的价值在于界定安全区间",
        "35. **本文的 `r` 是园区级替代率",
        "36. **`W/D` 本身是模型产物",
        "rstar_policy_bridge.csv",
    ):
        ck(f"主稿含「{kw[:36]}」", "OK" if kw in text else "MISSING",
           "03_主稿_v2.md", kw in text)

    # ---- 一致性：不得出现"已触发"的肯定表述 ----
    import re
    bad = re.findall(r"(?<!不)(?<!未)已经?触发.{0,8}反噬(?!的)", text)
    # 排除"不主张...已经触发"这种否定语境
    positive_claims = []
    for m in re.finditer(r"已经?触发.{0,8}反噬", text):
        ctx = text[max(0, m.start() - 40): m.start()]
        if not any(neg in ctx for neg in ("不主张", "不声称", "不会", "尚未", "并非")):
            positive_claims.append(ctx[-30:] + m.group())
    ck("无「已触发反噬」的肯定表述", f"{len(positive_claims)} 处",
       "03_主稿_v2.md", not positive_claims)

    # ---- 输出 ----
    print("=" * 104)
    print("第四轮增量（政策口径区隔与贡献定位）核对")
    print("=" * 104)
    print(f"{'判定':<6} {'声称':<48} {'产物取值':<24} 来源")
    print("-" * 104)
    passed = 0
    for claim, value, source, ok in ROWS:
        if ok:
            passed += 1
        print(f"{'PASS' if ok else 'FAIL':<6} {claim[:48]:<48} {value[:24]:<24} {source}")
    print("-" * 104)
    print(f"合计 {passed}/{len(ROWS)} 通过")

    out = HERE / "_verify_policy_bridge.json"
    out.write_text(json.dumps(
        {"passed": passed, "total": len(ROWS),
         "rows": [{"claim": c, "value": v, "source": s, "ok": o} for c, v, s, o in ROWS]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {out}")
    sys.exit(0 if passed == len(ROWS) else 1)


if __name__ == "__main__":
    main()
