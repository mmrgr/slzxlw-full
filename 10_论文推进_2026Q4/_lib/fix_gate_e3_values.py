"""修 _gate_check.py 中 E3 的【比较值】(标签已改, 阈值未改)."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = Path(__file__).resolve().parent.parent / "A37_六主图_v4/_gate_check.py"
t = P.read_text(encoding="utf-8")

PAIRS = [
    # E3 单判据: 0.6712 -> 0.6746
    ('["acc"] - 0.6712) < 1e-4', '["acc"] - 0.6746) < 1e-4'),
    # 基线: 0.8608 -> 0.8090
    ('["majority_baseline_acc"] - 0.8608) < 1e-4',
     '["majority_baseline_acc"] - 0.8090) < 1e-4'),
    # C4 全样本: 0.9059 -> 0.9144
    ('>=2"]["acc"] - 0.9059) < 1e-4', '>=2"]["acc"] - 0.9144) < 1e-4'),
    # OOS 均值: 0.9009 -> 0.9171
    ('["oos_mean_test_acc"] - 0.9009) < 1e-4', '["oos_mean_test_acc"] - 0.9171) < 1e-4'),
    # OOS 基线: 0.8594 -> 0.8151
    ('["oos_mean_baseline"] - 0.8594) < 1e-4', '["oos_mean_baseline"] - 0.8151) < 1e-4'),
    # 折分布: (1,2,1) -> (2,2,0)
    ('(n_pos, n_zero, n_neg) == (1, 2, 1)', '(n_pos, n_zero, n_neg) == (2, 2, 0)'),
]

n = 0
for a, b in PAIRS:
    if a in t:
        t = t.replace(a, b)
        n += 1
    else:
        print(f"  MISS: {a[:55]}")
P.write_text(t, encoding="utf-8")
print(f"替换 {n}/{len(PAIRS)}")
