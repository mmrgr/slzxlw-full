"""修正 3 个脚本的单门禁 -> 双门禁 (2026-10-17, 阶段1 技术债).

【核验前置】
已确认: holdout_fit_ha.csv 单门禁=123=双门禁, holdout_holdout_co.csv 126=126,
差值均为 0 ⇒ 这 3 个脚本的产物**当前不受影响**, 修正属"防未来漂移"。

【修正内容】给 3 个脚本补上退化门禁, 与全项目口径统一。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

JOBS = {
    "A25_终审/a15_gates_reliable.py": [
        ('OK = "converged_unique"',
         'OK = "converged_unique"\n'
         '# 2026-10-17: 补第二门禁(退化情景), 与全项目双门禁口径统一。\n'
         '# 核验显示 holdout 文件单/双门禁差值为 0, 故本修正不改变现有产物。\n'
         'DEGEN_COL = "coc_floor_degenerate"'),
        ("    b = d[d.status == OK]",
         "    b = d[(d.status == OK)]\n"
         "    if DEGEN_COL in d.columns:\n"
         "        b = b[~b[DEGEN_COL].astype(bool)]"),
        ('"ok": round(_r2(fit[fit.status == OK], ho[ho.status == OK]), 6),',
         '"ok": round(_r2(_rel(fit), _rel(ho)), 6),'),
    ],
}

HELPER = '''

def _rel(d):
    """双门禁: status==OK 且未触 CoC 下限 (2026-10-17 补齐)。"""
    m = d["status"] == OK
    if "coc_floor_degenerate" in d.columns:
        m = m & (~d["coc_floor_degenerate"].astype(bool))
    return d[m]
'''


def main() -> int:
    tot = 0
    for rel, pairs in JOBS.items():
        p = ROOT / rel
        if not p.exists():
            print(f"  skip {rel}")
            continue
        t = p.read_text(encoding="utf-8")
        n = 0
        for a, b in pairs:
            if a in t:
                t = t.replace(a, b, 1)
                n += 1
            else:
                print(f"  MISS[{rel}]: {a[:60]}")
        # 注入 helper (放在 OK 常量之后)
        if "_rel(" in t and "def _rel(" not in t:
            anchor = 'DEGEN_COL = "coc_floor_degenerate"'
            if anchor in t:
                t = t.replace(anchor, anchor + HELPER, 1)
                n += 1
        if n:
            p.write_text(t, encoding="utf-8")
        print(f"  {rel}: {n}")
        tot += n
    print(f"合计 {tot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
