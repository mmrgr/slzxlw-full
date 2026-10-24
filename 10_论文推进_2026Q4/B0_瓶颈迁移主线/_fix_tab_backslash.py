# -*- coding: utf-8 -*-
"""扫描三份 md 中的 TAB 字符及其上下文。

背景：`04_wr_manuscript_en.md` 里 `$8.9\\times10^{-16}$` 被写成了
`$8.9<TAB>imes10^{-16}$`——某个环节把 `\\t` 当成了转义字符。因为
`repr("\\t"+"imes")` 打印出来恰好是 `\\times`，肉眼和日志都看不出差别，
所以这个 bug 潜伏了很久，直到 Word 里显示成 `8.9imes10` 才暴露。

本脚本只列出，不修改；确认后再用 --apply 把 TAB 还原成 `\\times`。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
FILES = ["03_主稿_中文投稿版.md", "04_wr_manuscript_en.md", "05_wr_supplementary_en.md"]


def main() -> int:
    apply = "--apply" in sys.argv
    total = 0
    for f in FILES:
        p = HERE / f
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        n = s.count("\t")
        if not n:
            continue
        print("=" * 70)
        print("FILE %s  TAB=%d" % (f, n))
        for lineno, line in enumerate(s.split("\n"), 1):
            if "\t" not in line:
                continue
            for idx in range(len(line)):
                if line[idx] != "\t":
                    continue
                left = line[max(0, idx - 25):idx]
                right = line[idx + 1:idx + 22]
                print("  L%-4d ...%s<TAB>[%r]...%s" % (lineno, left, right, ""))
        total += n
        if apply:
            # TAB 是被"吃掉的反斜杠 + t"：源码本应是 \times，其中 \t 被解释成
            # TAB，于是 `\times` 变成了 `<TAB>imes`。因此正确还原是把 TAB 换成
            # 反斜杠 + t（两字符），不能直接换成 `\times`——那会得到 `\timesimes`。
            new = s.replace("\t", "\\t")
            p.write_text(new, encoding="utf-8", newline="")
            print("  [APPLY] TAB -> 反斜杠+t ; 剩余 TAB =", new.count("\t"))
            print("          复核: '\\timesimes' 出现次数 =", new.count("\\timesimes"))
    print("=" * 70)
    print("TAB 合计:", total, "| 模式:", "APPLY" if apply else "DRY-RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
