# -*- coding: utf-8 -*-
"""PPT 设计系统：配色、字体、栅格、组件。与内容脚本解耦，便于统一改版。

【设计取向】
参考产品发布会 / 顶级实验室汇报的视觉语言，而非学术答辩模板：
  - 16:9，深色标题页 + 浅色内容页，形成节奏对比
  - 左侧一条 3mm 竖色带作为"章节标识"，全篇贯穿
  - 所有页面共用同一套 12 列栅格与边距，保证视觉一致性
  - 强调用色只用一处（蓝），其余靠字重与留白建立层次
  - 每页只有一句"结论句"放大加粗，其余正文降级

配色取自项目图件的既有色系（figstyle_b0.py），保证 PPT 与图件同源：
  水源侧 #2b6cb0 / 电网侧 #c05621 / 政策 #6b46c1
"""
from __future__ import annotations

from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor

# ---------------------------------------------------------------------------
# 画布
# ---------------------------------------------------------------------------
SLIDE_W = Emu(12192000)      # 13.333 in (16:9)
SLIDE_H = Emu(6858000)       # 7.5 in

MARGIN_X = Emu(838200)       # 0.92 in 左右边距
MARGIN_TOP = Emu(600000)     # 0.66 in
MARGIN_BOTTOM = Emu(430000)

# 12 列栅格：可用宽度 / 12
CONTENT_W = SLIDE_W - MARGIN_X * 2
COL_W = int(CONTENT_W / 12)
GUTTER = Emu(120000)

# 竖色带
BAND_W = Emu(95000)          # ~2.6 mm

# ---------------------------------------------------------------------------
# 颜色
# ---------------------------------------------------------------------------
def C(hexstr: str) -> RGBColor:
    h = hexstr.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# 主色（取自项目图件）
BLUE = C("#2b6cb0")          # 水源侧 / 主强调
ORANGE = C("#c05621")        # 电网侧
PURPLE = C("#6b46c1")        # 政策
GREEN = C("#2c7a7b")         # 正向 / 有效
RED = C("#9b2c2c")           # 风险 / 警示

# 中性色（深色页与浅色页各一套）
INK = C("#1a202c")           # 正文主色（近黑，比纯黑柔和）
INK_2 = C("#4a5568")         # 次级正文
INK_3 = C("#718096")         # 说明、元信息
LINE = C("#e2e8f0")          # 分割线
BG = C("#ffffff")
BG_SOFT = C("#f7fafc")       # 卡片底
BG_DARK = C("#1a202c")       # 深色页底
BG_DARK_2 = C("#2d3748")

WHITE = C("#ffffff")
WHITE_2 = C("#cbd5e0")       # 深色页次级文字
WHITE_3 = C("#a0aec0")       # 深色页说明

# ---------------------------------------------------------------------------
# 字体
# ---------------------------------------------------------------------------
FONT_CN = "微软雅黑"          # 屏幕投影清晰，字重完整
FONT_CN_LIGHT = "微软雅黑 Light"
FONT_EN = "Segoe UI"
FONT_MONO = "Consolas"

# 字号阶梯（产品化的关键：只用少数几档）
FS_DISPLAY = Pt(54)          # 封面主标题
FS_H1 = Pt(32)               # 页标题
FS_H2 = Pt(21)               # 小节
FS_LEAD = Pt(20)             # 结论句（加粗放大）
FS_BODY = Pt(15)             # 正文
FS_SMALL = Pt(12)            # 说明
FS_META = Pt(10.5)           # 页脚、来源
FS_NUM = Pt(44)              # 大数字


def set_font(run, size=None, bold=None, color=None, cn=FONT_CN, en=FONT_EN,
             italic=None) -> None:
    """统一设置字体。中文走东亚字体，西文走 ascii，两者分开指定避免回退。"""
    from pptx.oxml.ns import qn

    f = run.font
    if size is not None:
        f.size = size
    if bold is not None:
        f.bold = bold
    if italic is not None:
        f.italic = italic
    if color is not None:
        f.color.rgb = color
    f.name = en
    rpr = run._r.get_or_add_rPr()
    ea = rpr.find(qn("a:ea"))
    if ea is None:
        from lxml import etree
        ea = etree.SubElement(rpr, qn("a:ea"))
    ea.set("typeface", cn)
