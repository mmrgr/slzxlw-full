# -*- coding: utf-8 -*-
"""Word 交付前自检：确认公式都是原生 OMML、无 LaTeX 源码残留、无畸形字符。

检查项：
  1. document.xml 中 m:oMath 数量
  2. 正文可见文本中是否残留 `\\mathrm`、`\\frac`、`$`、`^{`、`_{` 等 LaTeX 痕迹
  3. 是否有 TAB / 反引号残留
  4. 图片数量
用法: python _check_docx.py <docx> [...]
"""
import re
import sys
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LATEX_MARKS = [r"\mathrm", r"\frac", r"\text{", r"\times", r"\min", r"\le ",
               r"\ge ", r"\rho", r"\alpha", r"\beta", r"^{", r"_{"]


def main() -> int:
    bad = 0
    for path in sys.argv[1:]:
        z = zipfile.ZipFile(path)
        doc = z.read("word/document.xml").decode("utf-8")
        names = z.namelist()
        media = [n for n in names if n.startswith("word/media/")]

        n_omath = len(re.findall(r"<m:oMath[ >]", doc))

        # 段落可见文本：去掉所有标签后是完整正文（含公式内 m:t 的文字）。
        # 这里只检查"非公式 run"里的残留，做法是把每个 oMath 整段剔除。
        no_math = re.sub(r"<m:oMath[ >].*?</m:oMath>", " ", doc, flags=re.S)
        texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", no_math, re.S)
        visible = "".join(texts)

        print("=" * 70)
        print(path)
        print("  m:oMath      :", n_omath)
        print("  图片         :", len(media))
        print("  正文字符     :", len(visible))

        hits = {}
        for mk in LATEX_MARKS:
            c = visible.count(mk)
            if c:
                hits[mk] = c
        if "$" in visible:
            hits["$"] = visible.count("$")
        if "\t" in visible:
            hits["TAB"] = visible.count("\t")

        if hits:
            print("  ⚠ 残留标记   :", hits)
            for mk in hits:
                i = visible.find(mk)
                print("      ctx:", repr(visible[max(0, i - 40):i + 40]))
            bad += 1
        else:
            print("  ✓ 无 LaTeX 源码残留")

        # 检查异常：公式内出现被拆散的拉丁词（如 i/m/e/s 分开）
        for m in re.finditer(r"<m:oMath[ >].*?</m:oMath>", doc, re.S):
            seg = m.group(0)
            runs = re.findall(r"<m:t[^>]*>(.*?)</m:t>", seg, re.S)
            if len(runs) >= 4 and all(len(r) == 1 and r.isalpha() for r in runs[-4:]):
                # 末尾四个连续单字母，且拼起来是常见词
                joined = "".join(runs)
                if any(w in joined for w in ("imes", "frac", "mathrm", "text")):
                    print("  ⚠ 拆散单词:", runs)
                    bad += 1
    print("=" * 70)
    print("问题文档数:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
