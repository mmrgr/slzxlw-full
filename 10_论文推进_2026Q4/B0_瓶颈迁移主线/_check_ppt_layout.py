# -*- coding: utf-8 -*-
"""PPT 版面自检：越界、重叠、溢出。

用几何校验替代逐页肉眼检查——眼睛容易漏掉"注解压在页脚上"这类问题，
而坐标是确定的。

检查项：
  1. 越界：任何 shape 超出页面矩形（留 1mm 容差）
  2. 重叠：两个**都有文字**的 shape 矩形相交面积超过较小者的阈值
     （图片与文字框相邻是正常设计，只对"文字压文字"报警）
  3. 底部拥挤：任何含文字的 shape 下沿进入页脚带
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from pptx import Presentation

HERE = Path(__file__).resolve().parent
DECK = HERE / "62_导师汇报_10页_20261020.pptx"

TOL = 36000            # 1mm = 36000 EMU，页面边界容差
FOOT_BAND = 300000     # 页脚带高度（从页脚行上沿起算）
OVERLAP_FRAC = 0.35    # 重叠面积 / 较小矩形面积 超过此值报警
# 文本框高度常常给得比实际文字大（排版余量），导致上下相邻的两块
# 有 20% 左右的"假重叠"。要求重叠高度占较小者高度的比例也超阈值，
# 才认为是真的叠在一起，而非仅仅是框贴框。
OVERLAP_H_FRAC = 0.45  # 重叠高度 / 较小矩形高度 也要超过，才算真重叠


def has_text(sp) -> bool:
    if not sp.has_text_frame:
        return False
    return sp.text_frame.text.strip() != ""


def main() -> int:
    prs = Presentation(str(DECK))
    W, H = prs.slide_width, prs.slide_height
    # 页脚文字实际所在行（K.footer 用的 y），只有越过它才是真压住页脚。
    # 之前从"页脚行 − 300000"起算，把正常留白也报成问题。
    foot_top = H - 430000 - 150000

    problems = 0
    for idx, slide in enumerate(prs.slides, start=1):
        boxes = []
        for sp in slide.shapes:
            try:
                x, y = sp.left or 0, sp.top or 0
                w, h = sp.width or 0, sp.height or 0
            except Exception:
                continue
            name = sp.shape_type
            txt = (sp.text_frame.text[:26].replace("\n", "⏎")
                   if sp.has_text_frame else "")
            boxes.append((x, y, w, h, txt, sp))

            # 1) 越界
            if x < -TOL or y < -TOL or x + w > W + TOL or y + h > H + TOL:
                print(f"  [越界] P{idx:02d}  {txt!r}")
                print(f"         x={x} y={y} w={w} h={h}  (页面 {W}x{H})")
                problems += 1

        # 2) 文字框互相重叠
        texts = [b for b in boxes if b[4]]
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                x1, y1, w1, h1, t1, _ = texts[i]
                x2, y2, w2, h2, t2, _ = texts[j]
                ox = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                oy = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                area = ox * oy
                if area == 0:
                    continue
                small = min(w1 * h1, w2 * h2)
                small_h = min(h1, h2)
                # 两个条件都要满足：面积占比够大，且高度方向真的叠进去
                if (small and area / small > OVERLAP_FRAC
                        and small_h and oy / small_h > OVERLAP_H_FRAC):
                    print(f"  [重叠] P{idx:02d}  {area/small:.0%}")
                    print(f"         A {t1!r}  ({x1},{y1},{w1},{h1})")
                    print(f"         B {t2!r}  ({x2},{y2},{w2},{h2})")
                    problems += 1

        # 3) 底部拥挤：检查**非页脚**元素是否侵入页脚行
        #    页脚自身（来源文字 + 页码）就画在 foot_top 上，必须排除，
        #    否则每页都会误报两条。
        for x, y, w, h, t, _ in boxes:
            if not t:
                continue
            is_footer = (y >= foot_top - 20000)
            if is_footer:
                continue
            if y + h > foot_top:
                print(f"  [压页脚] P{idx:02d}  {t!r}  下沿={y+h} 页脚上沿={foot_top}")
                problems += 1

    print()
    if problems == 0:
        print("版面自检通过：无越界、无文字重叠、无压页脚")
    else:
        print(f"发现 {problems} 处问题")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
