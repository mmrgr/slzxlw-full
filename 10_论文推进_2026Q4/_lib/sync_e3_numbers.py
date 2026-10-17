"""同步 E3/E3b 数字 (2026-10-17). 用脚本文件避免 heredoc 转义。"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
SI = ROOT / "A16_英文稿/supplementary_information.md"

MS_PAIRS = [
    ("| Chemistry only ($c^{\\rm rec}_i<c^{\\rm pot}_i$ for all species) | 0.389 | 0.861 |",
     "| Chemistry only ($c^{\\rm rec}_i<c^{\\rm pot}_i$ for all species) | 0.432 | 0.809 |"),
    ("| Closed form $q>0$ | **0.671** | 0.861 |",
     "| Closed form $q>0$ | **0.675** | 0.809 |"),
    ("| $q>0$ **or** deliverable pool $\\ge 2\\times$ baseline demand | **0.906** | 0.861 |",
     "| $q>0$ **or** deliverable pool $\\ge 2\\times$ baseline demand | **0.914** | 0.809 |"),
    ("(i) *Chemistry alone cannot predict the city-level sign* (0.671 **below** the 0.861",
     "(i) *Chemistry alone cannot predict the city-level sign* (0.675 **below** the 0.809"),
    ("6. **The sign is not predictable from chemistry alone** — 0.671 without a demand-side",
     "6. **The sign is not predictable from chemistry alone** — 0.675 without a demand-side"),
    ("quantity, below the 0.861 majority-class baseline (§3d). Adding one demand-side quantity\n"
     "lifts in-sample accuracy to 0.906 but does **not** survive fold-wise validation (median",
     "quantity, below the 0.809 majority-class baseline (§3d). Adding one demand-side quantity\n"
     "lifts in-sample accuracy to 0.914 and gains **+0.092 median** under fold-wise validation,"),
]

SI_PAIRS = [
    ("accounting consistency check; the strict pre-intervention test gives 0.671 against a 0.861",
     "accounting consistency check; the strict pre-intervention test gives 0.675 against a 0.809"),
    ("4. **Chemistry-only prediction fails** (0.671 < 0.861 baseline) — reported, not hidden.",
     "4. **Chemistry-only prediction fails** (0.675 < 0.809 baseline) — reported, not hidden."),
    ("| Closed form $q>0$ | 0.671 | 390 | 0 | 102 | 241 |",
     "| Closed form $q>0$ | 0.675 | 367 | 0 | 145 | 247 |"),
]


def apply(p: Path, pairs: list[tuple[str, str]], tag: str) -> int:
    if not p.exists():
        print(f"  skip {tag}")
        return 0
    t = p.read_text(encoding="utf-8")
    n = 0
    for a, b in pairs:
        if a in t:
            t = t.replace(a, b, 1)
            n += 1
        else:
            print(f"  MISS[{tag}]: {a[:60]}")
    p.write_text(t, encoding="utf-8")
    print(f"  {tag}: {n}/{len(pairs)}")
    return n


if __name__ == "__main__":
    apply(MS, MS_PAIRS, "manuscript")
    apply(SI, SI_PAIRS, "SI")
