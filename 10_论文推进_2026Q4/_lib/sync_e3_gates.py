"""同步 E3 相关门禁期望值 (2026-10-17)."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

JOBS = {
    "A37_六主图_v4/_gate_check.py": [
        ("E3 chem 0.6712", "E3 chem 0.6746"),
        ("baseline 0.8608", "baseline 0.8090"),
        ("C4 0.9059", "C4 0.9144"),
        ("OOS 0.9009/0.8594", "OOS 0.9171/0.8151"),
        ("OOS gain single-fold (1 pos/2 zero/1 neg)", "OOS gain (2 pos/2 zero/0 neg)"),
    ],
    "A37_六主图_v4/make_figure_index.py": [
        ('"0.6712 vs 基线 0.8608"', '"0.6746 vs 基线 0.8090"'),
        ('"0.9059 全样本; 折外 0.9009 vs 0.8594"', '"0.9144 全样本; 折外 0.9171 vs 0.8151"'),
    ],
    "A40_投稿包/make_reproducibility_manifest.py": [
        ("0.6712", "0.6746"),
        ("0.8608", "0.8090"),
        ("0.90593", "0.9144"),
    ],
}


def main() -> int:
    total = 0
    for rel, pairs in JOBS.items():
        p = ROOT / rel
        if not p.exists():
            print(f"  skip {rel}")
            continue
        t = p.read_text(encoding="utf-8")
        n = 0
        for a, b in pairs:
            if a in t:
                cnt = t.count(a)
                t = t.replace(a, b)
                n += cnt
        if n:
            p.write_text(t, encoding="utf-8")
        print(f"  {rel}: {n}")
        total += n
    print(f"合计 {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
