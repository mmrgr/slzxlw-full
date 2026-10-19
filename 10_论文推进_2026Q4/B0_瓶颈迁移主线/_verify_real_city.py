# -*- coding: utf-8 -*-
"""本轮（真实城市应用）数值溯源核对。

覆盖：6%/26%、UWMP 两套口径、k*、r 值、eAR 交叉验证、加州 k 分布。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4\B0_瓶颈迁移主线")
V2 = HERE / "03_主稿_v2.md"

ROWS = []


def ck(name, ok, detail=""):
    ROWS.append((name, bool(ok), detail))


# ---------- 基础参数 ----------
R_STAR = 0.5532
K_STAR = (1.0 / R_STAR - 1.0) / (6.0 / 26.0)

POT_CAP, REC_CAP = 32649.0, 6017.0      # UWMP p.65
POT_ACT, REC_ACT = 16857.0, 3871.0      # UWMP p.35

POT_EAR, REC_EAR = 16913.0, 3450.0      # eAR 2022

t = V2.read_text(encoding="utf-8")

# ---------- 1. 判据常数 ----------
ck("k* = 3.50", abs(K_STAR - 3.5) < 0.01, f"{K_STAR:.4f}")

# ---------- 2. 两口径 ----------
k_cap = POT_CAP / REC_CAP
r_cap = 0.26 * REC_CAP / (0.26 * REC_CAP + 0.06 * POT_CAP)
ck("供给能力口径 k=5.43", abs(k_cap - 5.43) < 0.01, f"{k_cap:.3f}")
ck("供给能力口径 r=0.444", abs(r_cap - 0.444) < 0.001, f"{r_cap:.4f}")

k_act = POT_ACT / REC_ACT
r_act = 0.26 * REC_ACT / (0.26 * REC_ACT + 0.06 * POT_ACT)
ck("实际用量口径 k=4.35", abs(k_act - 4.35) < 0.02, f"{k_act:.3f}")
ck("实际用量口径 r=0.499", abs(r_act - 0.499) < 0.002, f"{r_act:.4f}")

# ---------- 3. eAR 交叉验证 ----------
k_ear = POT_EAR / REC_EAR
ck("eAR k=4.90", abs(k_ear - 4.90) < 0.02, f"{k_ear:.3f}")

# ---------- 4. 余量与临界变化 ----------
gap_pp = (R_STAR - r_act) * 100
ck("余量 5.4 个百分点", abs(gap_pp - 5.44) < 0.05, f"{gap_pp:.2f} pp")
rel = (R_STAR - r_act) / R_STAR * 100
ck("相对余量 9.8%", abs(rel - 9.8) < 0.2, f"{rel:.1f}%")

need_rec = POT_ACT / K_STAR
inc = (need_rec / REC_ACT - 1) * 100
ck("再生水需增 24% 才越界", abs(inc - 24) < 1.0, f"{inc:.1f}%")

need_pot = REC_ACT * K_STAR
dec = (1 - need_pot / POT_ACT) * 100
ck("自来水需减 20% 才越界", abs(dec - 20) < 1.0, f"{dec:.1f}%")

# ---------- 5. 再生水利用率 ----------
util = REC_ACT / REC_CAP * 100
ck("再生水利用率 64.3%", abs(util - 64.3) < 0.2, f"{util:.1f}%")
city_load = (POT_ACT + REC_ACT) / (POT_CAP + REC_CAP) * 100
ck("城市总利用率 53.6%", abs(city_load - 53.6) < 0.3, f"{city_load:.1f}%")

# ---------- 6. 加州 k 分布（来自产物） ----------
clean_path = HERE / "_ca_k_clean.json"
if clean_path.exists():
    d = json.load(open(clean_path, encoding="utf-8"))
    recs = d["records"]
    ks = sorted(x["k"] for x in recs)
    n = len(ks)
    ck("清洗后 n=169", n == 169, f"{n}")
    med = ks[n // 2]
    ck("k 中位 13.54", abs(med - 13.54) < 0.05, f"{med:.2f}")
    below = sum(1 for x in recs if x["k"] < K_STAR)
    pct_below = 100 * below / n
    ck("k<k* 占 13.6%", abs(pct_below - 13.6) < 0.2, f"{pct_below:.1f}% ({below}/{n})")
    big = [x for x in recs if x.get("pop", 0) >= 50000]
    big_below = sum(1 for x in big if x["k"] < K_STAR)
    pct_big = 100 * big_below / len(big) if big else 0
    ck("大型系统 n=93 且 k<k* 占 8.6%",
       len(big) == 93 and abs(pct_big - 8.6) < 0.2,
       f"n={len(big)}, {pct_big:.1f}%")
else:
    ck("加州 k 分布产物存在", False, "缺 _ca_k_clean.json")

# ---------- 7. 主稿文本包含 ----------
for kw, label in [
    ("## 5.9 结果 6：判据在一个真实城市的应用", "§5.9"),
    ("k* = 3.50", "k* 判据"),
    ("6%", "6% 份额"),
    ("26%", "26% 份额"),
    ("### 9.7 真实城市应用", "§9.7 限制"),
    ("eAR", "eAR 交叉验证"),
    ("169", "169 个系统"),
    ("_ca_k_distribution.json", "产物引用"),
]:
    ck(f"主稿含「{label}」", kw in t)

# ---------- 8. 诚实性检查：必须写明"应用非验证" ----------
ck("声明白「应用非验证」", "应用，不是验证" in t or "应用，不是机制的验证" in t)
ck("声明 6%/26% 分母不可加总", "not 32%" in t or "不可加总" in t)
ck("声明样本选择偏差", "样本选择偏差" in t or "选择偏差" in t)

# ---------- 9. 两处事实错误已修 ----------
ck("物种数已改为 2", "模型实际追踪 2 个物种" in t)
ck("参数锚定已改为 20", "20 个有观测锚定" in t)
ck("原「50 个落在包络内」已移除", "50 个落在 A01–A18 观测包络内" not in t)

# ---------- 输出 ----------
print("=" * 100)
print("真实城市应用 · 数值溯源核对")
print("=" * 100)
passed = 0
for name, ok, detail in ROWS:
    if ok:
        passed += 1
    line = f"[{'PASS' if ok else 'FAIL'}] {name}"
    if detail and not ok:
        line += f"  ({detail})"
    print(line)
print("-" * 100)
print(f"合计 {passed}/{len(ROWS)} 通过")

out = HERE / "_verify_real_city.json"
json.dump({"passed": passed, "total": len(ROWS),
           "rows": [{"name": n, "ok": o, "detail": d} for n, o, d in ROWS]},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"-> {out}")
sys.exit(0 if passed == len(ROWS) else 1)
