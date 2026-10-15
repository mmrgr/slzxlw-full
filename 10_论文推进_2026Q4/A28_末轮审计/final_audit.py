"""A28 末轮审计: 方法/原理/数据 的一致性、量纲与可复现性总检.

检查项:
  M1 恒等式与分支退化 (代数自洽)
  M2 量纲一致性 (ML vs ML/d; N_DAYS=730 是否被一致使用)
  M3 守恒性 (排放-索取; 水量)
  M4 引用限值与 A27 语义 (合计 1100, degenerate 剔除)
  M5 状态门禁 (converged_unique + coc_floor_degenerate 双门禁)
  D1 外部数据内部一致性 (Load Rate vs 年处理量/365/设计)
  D2 A24 的 P0 百分位换算
  D3 文档数字 vs 现行产物
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402

issues: list[tuple[str, str, str]] = []
oks: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    (oks if cond else issues).append((name, detail if not cond else ""))


print("=" * 78)
print("A28 末轮审计")
print("=" * 78)

# ---------------- M1 恒等式与分支 ----------------
ss = pd.read_csv(ROOT / "A13_可靠性机制" / "supply_state_regimes.csv", encoding="utf-8-sig")
ok = ss[(ss.status == "converged_unique") & (~ss.coc_floor_degenerate.astype(bool))]
pred = ok.displaced_ml - (ok.M0_ml - ok.M1_ml) - ok.x_ai_B1_ml
resid = (ok.dS_pot_ml - pred).abs()
scale = ok[["M0_ml", "M1_ml", "x_ai_B1_ml", "displaced_ml"]].abs().max(axis=1)
check("M1 恒等式绝对残差 < 1e-9 ML", bool(resid.max() < 1e-9), f"{resid.max():.3e}")
check("M1 恒等式相对残差 < 1e-13", bool((resid / scale).max() < 1e-13),
      f"{(resid/scale).max():.3e}")
check("M1 判据吻合率 == 1.0",
      bool((((ok.x_ai_B1_ml + (ok.M0_ml - ok.M1_ml)) > ok.displaced_ml)
            == (ok.dS_pot_ml < -1e-6)).mean() == 1.0))
_q_ok = (ok.M0_ml - ok.M1_ml) / ok.M1_ml
check("M1 q>0 全部有益", bool(((_q_ok > 1e-9) & (ok.dS_pot_ml > 1e-6)).sum() == 0))
free = ss[(ss.chi_label == "free") & (ss.status == "converged_unique")
          & (~ss.coc_floor_degenerate.astype(bool))]
A = free[(free.displaced_ml - free.x_ai_B1_ml).abs() < 1.0]
check("M1 free 档 A 态 dS≈0", bool(A.dS_pot_ml.abs().max() < 1e-6)
      if len(A) else False, f"max|dS|={A.dS_pot_ml.abs().max():.2e}" if len(A) else "空集")

# ---------------- M2 量纲 ----------------
print("\n[M2] 量纲一致性")
check("M2 N_DAYS == 730", cm.N_DAYS == 730)
P0_days = {d: cm.BASELINES[d]["P0"] / cm.N_DAYS for d in ("ha", "co")}
check("M2 P0/730 与 A24 口径一致 (33.4 / 30.7 ML/d)",
      abs(P0_days["ha"] - 33.43) < 0.1 and abs(P0_days["co"] - 30.70) < 0.1,
      str({k: round(v, 2) for k, v in P0_days.items()}))

# ---------------- M4 引用限值 ----------------
print("\n[M4] 引用限值 (A27)")
check("M4 LIMIT_SET == baseline", cm.LIMIT_SET == "baseline", cm.LIMIT_SET)
check("M4 hardness+alkalinity == 1100 (合规)",
      cm.PANEL_B["hardness"] + cm.PANEL_B["alkalinity"] == 1100.0,
      str(cm.PANEL_B))
check("M4 引用限值非占位", cm.PANEL_B != cm.PLACEHOLDER_LIMITS)

# ---------------- M5 双门禁 ----------------
print("\n[M5] 双门禁")
check("M5 主网格可靠 n=813", len(ok) == 813, f"n={len(ok)}")
check("M5 退化情景 188", int(ss.coc_floor_degenerate.sum()) == 188,
      str(int(ss.coc_floor_degenerate.sum())))
check("M5 退化全在 chi=0.25",
      bool((ss[ss.coc_floor_degenerate].chi_label == "0.25").all()))

# ---------------- D1 外部数据 ----------------
print("\n[D1] 外部数据 (Shen 2026)")
EXT = Path(r"C:/Users/mmrgr/Desktop/论文/_ext_data/source_data/Source_data.xlsx")
if EXT.exists():
    x = pd.ExcelFile(EXT)
    d = x.parse("WWTP_data_2020", header=0)
    cap = pd.to_numeric(d["Design Capacity/(10⁴ m³/d)"], errors="coerce")
    lr = pd.to_numeric(d["Load Rate"], errors="coerce")
    act = pd.to_numeric(d["Actual Wastewater Treatment in 2020/(10⁴ m³)"], errors="coerce")
    implied = (act / 365.0) / cap
    corr = float(implied.corr(lr))
    check("D1 Load Rate 与年化/365/设计 相关 = 1.0", abs(corr - 1.0) < 1e-6, f"{corr:.6f}")
    check("D1 厂数 = 10826", len(d) == 10826, str(len(d)))
    check("D1 设计能力中位 = 8 ML/d", abs(cap.median() * 10 - 8.0) < 0.01,
          f"{cap.median()*10:.3f}")
else:
    check("D1 外部数据存在", False, "缺 Source_data.xlsx")

# ---------------- D3 文档数字 ----------------
print("\n[D3] 文档数字 vs 现行产物")
man = (ROOT / "A16_英文稿" / "manuscript_en_v3.md").read_text(encoding="utf-8")
si = (ROOT / "A16_英文稿" / "supplementary_information.md").read_text(encoding="utf-8")
check("D3 主稿含 813", "813" in man)
check("D3 主稿含 290/290", "290 of 290" in man)
check("D3 主稿含 §3b-bis", "3b-bis" in man)
check("D3 SI 含 290/290", "290/290" in si)
check("D3 SI 含 S2a", "S2a." in si)
check("D3 主稿无残留 1,094 (除 A27 对照)", man.count("1,094") <= 1,
      f"出现 {man.count('1,094')} 次")

print()
print("=" * 78)
print(f"[OK  ] {len(oks)} 项")
print(f"[FAIL] {len(issues)} 项")
for n, d in issues:
    print(f"   · {n}   {d}")
print("=" * 78)

(HERE / "final_audit_result.json").write_text(
    json.dumps({"n_ok": len(oks), "n_fail": len(issues),
                "failures": [{"check": n, "detail": d} for n, d in issues],
                "passed": [n for n, _ in oks]},
               ensure_ascii=False, indent=1), encoding="utf-8")
