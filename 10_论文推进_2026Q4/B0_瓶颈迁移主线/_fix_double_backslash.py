# -*- coding: utf-8 -*-
"""修复英文稿第 270 行的误写双反斜杠（应为单反斜杠 LaTeX）。

背景：`04_wr_manuscript_en.md` L270 有 9 处 `\\times`、`\\mathrm` 等，
是 Markdown 中转义残留。真正的 LaTeX 应为单反斜杠。此脚本只改该行，
并断言全文件再无 `\\` 出现。
"""
import io
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
P = HERE / "04_wr_manuscript_en.md"


def main() -> int:
    lines = P.read_text(encoding="utf-8").split("\n")
    before_total = sum(l.count("\\\\") for l in lines)
    print("修复前全文件 `\\\\` 计数:", before_total)
    if before_total == 0:
        print("无需修复")
        return 0

    hit = [i for i, l in enumerate(lines) if "\\\\" in l]
    print("受影响行号(1-based):", [i + 1 for i in hit])
    for i in hit:
        n = lines[i].count("\\\\")
        lines[i] = lines[i].replace("\\\\", "\\")
        print("  L%d 替换 %d 处" % (i + 1, n))

    new_text = "\n".join(lines)
    after_total = new_text.count("\\\\")
    print("修复后 `\\\\` 计数:", after_total)
    assert after_total == 0, "仍有残留"

    if "--apply" in sys.argv:
        P.write_text(new_text, encoding="utf-8", newline="")
        print("[APPLY] 已写回", P.name)
    else:
        print("[DRY-RUN] 未写回，加 --apply 生效")
    return 0


if __name__ == "__main__":
    sys.exit(main())
