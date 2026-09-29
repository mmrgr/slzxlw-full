"""v3 batch 3: final consistency fixes."""
from pathlib import Path

DOC = Path(r"C:\Users\mmrgr\Desktop\开题\AI-UWM下一轮模拟_情景设置与实施方案.md")
text = DOC.read_text(encoding="utf-8")
PAIRS = [
    ("| 判据 | 人工判断 | 10 项机器自检 V1–V10，写入 `r2_verification.json` |",
     "| 判据 | 人工判断 | 12 项机器自检 V1–V12 + 19 项现实性审计判据，写入 `r2_verification.json` / `realism_audit.csv` |"),
    ("| `scripts/run_r2.py`（新增） | 执行 A–I 九段实验 + V1–V10 自检 | — |",
     "| `scripts/run_r2.py`（新增） | 执行 A–I 九段实验（含新增 C4 净替代、C5 产水量边际）+ V1–V12 自检 | — |"),
    ("2. **P2 验证**：`run_r2.py` → 看 V1–V10。**V1/V2/V4/V5/V7 任一项不通过必须停下来修模型**，不能往下走。",
     "2. **P2 验证**：先 `audit_realism.py`（19 项必须 0 FAIL），再 `run_r2.py` → 看 V1–V12。**V1/V2/V4/V5/V7/V12 任一项不通过必须停下来修模型**，不能往下走。"),
    ("而库容 20 000 ML 起、干旱只压入流与取水能力时供水并未真正受限",
     "而库容 65 000 ML 起（库容的 54 %）、干旱只压入流与取水能力时供水并未真正受限"),
]
missing = []
for old, new in PAIRS:
    if old not in text:
        missing.append(old[:60])
    else:
        text = text.replace(old, new, 1)
DOC.write_text(text, encoding="utf-8")
print("applied", len(PAIRS) - len(missing), "/", len(PAIRS))
for m in missing:
    print("MISSING:", m)
