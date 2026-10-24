# -*- coding: utf-8 -*-
"""PPT 组件库：把「加一个矩形并设置填充」这类底层操作封装成语义化组件。

原则：页面脚本里只出现 `band()`、`title()`、`lead()`、`card()`、`kpi()` 这类
说法，不出现 EMU 数值和填充色。这样改版只需改本文件。
"""
from __future__ import annotations

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

from _ppt_design import (
    BAND_W, BLUE, BG, BG_DARK, BG_SOFT, FS_BODY, FS_DISPLAY, FS_H1, FS_H2,
    FS_LEAD, FS_META, FS_NUM, FS_SMALL, INK, INK_2, INK_3, LINE, MARGIN_BOTTOM,
    MARGIN_TOP, MARGIN_X, ORANGE, SLIDE_H, SLIDE_W, WHITE, WHITE_2, WHITE_3,
    FONT_CN, FONT_CN_LIGHT, set_font,
)


# ---------------------------------------------------------------------------
# 基础图元
# ---------------------------------------------------------------------------
def rect(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE,
         line_w=Pt(0.75)):
    sp = slide.shapes.add_shape(shape, int(x), int(y), int(w), int(h))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = line_w
    sp.shadow.inherit = False
    if sp.has_text_frame:
        sp.text_frame.word_wrap = True
    return sp


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(int(x), int(y), int(w), int(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return tb


def para(tf, text, size=FS_BODY, bold=False, color=INK, space_before=0,
         space_after=0, align=PP_ALIGN.LEFT, line_spacing=1.25, cn=FONT_CN,
         first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.line_spacing = line_spacing
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    r = p.add_run()
    r.text = text
    set_font(r, size=size, bold=bold, color=color, cn=cn)
    return p


def para_rich(tf, chunks, size=FS_BODY, space_before=0, space_after=0,
              align=PP_ALIGN.LEFT, line_spacing=1.25, first=False):
    """chunks: [(text, bold, color), ...] 用于一句话里混排强调。"""
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.line_spacing = line_spacing
    p.space_before = Pt(space_before)
    p.space_after = Pt(space_after)
    for text, bold, color in chunks:
        r = p.add_run()
        r.text = text
        set_font(r, size=size, bold=bold, color=color)
    return p


# ---------------------------------------------------------------------------
# 页面骨架
# ---------------------------------------------------------------------------
def page_bg(slide, dark=False, band_color=None) -> None:
    """铺底色 + 左侧章节色带。"""
    rect(slide, 0, 0, SLIDE_W, SLIDE_H, fill=BG_DARK if dark else BG)
    if band_color is not None:
        rect(slide, 0, 0, BAND_W, SLIDE_H, fill=band_color)


def page_title(slide, kicker: str, title: str, dark=False,
               band_color=None) -> int:
    """标题区：小标签（kicker）+ 大标题。返回正文起始 y。"""
    x = MARGIN_X
    y = MARGIN_TOP
    c_kick = WHITE_3 if dark else INK_3
    c_title = WHITE if dark else INK

    if kicker:
        tb = textbox(slide, x, y, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(260000))
        para(tb.text_frame, kicker, size=FS_SMALL, bold=True, color=band_color or BLUE,
             first=True)
        y += Emu(300000)

    tb = textbox(slide, x, y, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(700000))
    para(tb.text_frame, title, size=FS_H1, bold=True, color=c_title,
         line_spacing=1.1, first=True)
    y += Emu(640000)

    # 标题下细线
    rect(slide, x, y, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(11000),
         fill=(WHITE_3 if dark else LINE))
    return int(y + Emu(230000))


def lead(slide, y: int, text: str, dark=False, color=None, width=None) -> int:
    """结论句：每页的核心论断，比正文大一号加粗。返回其下沿 y。"""
    x = MARGIN_X
    w = width if width is not None else int(SLIDE_W - 2 * MARGIN_X)
    tb = textbox(slide, x, y, w, Emu(600000))
    para(tb.text_frame, text, size=FS_LEAD, bold=True,
         color=color or (WHITE if dark else INK), line_spacing=1.35, first=True)
    return int(y + Emu(620000))


def footer(slide, text: str, page: int | None = None, dark=False) -> None:
    y = int(SLIDE_H - MARGIN_BOTTOM - Emu(150000))
    c = WHITE_3 if dark else INK_3
    tb = textbox(slide, MARGIN_X, y, Emu(int(SLIDE_W - 2 * MARGIN_X - Emu(900000))),
                 Emu(240000))
    para(tb.text_frame, text, size=FS_META, color=c, first=True)
    if page is not None:
        tb2 = textbox(slide, int(SLIDE_W - MARGIN_X - Emu(700000)), y,
                      Emu(700000), Emu(240000))
        para(tb2.text_frame, f"{page:02d}", size=FS_META, bold=True, color=c,
             align=PP_ALIGN.RIGHT, first=True)


# ---------------------------------------------------------------------------
# 内容组件
# ---------------------------------------------------------------------------
def card(slide, x, y, w, h, title: str | None = None, body: str | None = None,
         accent=None, icon_text: str | None = None, title_size=FS_H2,
         body_size=FS_BODY, fill=None) -> object:
    """卡片：浅底 + 顶部 / 左侧强调条。

    accent 给颜色时，卡片顶部画一条 4pt 的色条作为类别标识。
    """
    sp = rect(slide, x, y, w, h, fill=fill or BG_SOFT, line=LINE)
    if accent is not None:
        rect(slide, x, y, w, Emu(46000), fill=accent)

    pad = Emu(230000)
    ty = int(y + pad + (Emu(60000) if accent is not None else 0))
    if icon_text:
        tb_i = textbox(slide, int(x + pad), ty, Emu(400000), Emu(420000))
        para(tb_i.text_frame, icon_text, size=Pt(19), bold=True,
             color=accent or BLUE, first=True)
        ty += Emu(420000)
    if title:
        tb = textbox(slide, int(x + pad), ty, int(w - 2 * pad), Emu(400000))
        para(tb.text_frame, title, size=title_size, bold=True, color=INK,
             line_spacing=1.15, first=True)
        ty += Emu(360000 if title_size <= FS_H2 else 440000)
    if body:
        tb = textbox(slide, int(x + pad), ty, int(w - 2 * pad),
                     int(y + h - ty - pad))
        para(tb.text_frame, body, size=body_size, color=INK_2,
             line_spacing=1.4, first=True)
    return sp


def kpi(slide, x, y, w, number: str, unit: str, label: str, color=None) -> int:
    """大数字组件：数字最大，单位小，说明最弱。返回下沿 y。"""
    color = color or BLUE
    tb = textbox(slide, x, y, w, Emu(700000))
    p = tb.text_frame.paragraphs[0]
    p.line_spacing = 1.0
    r = p.add_run()
    r.text = number
    set_font(r, size=FS_NUM, bold=True, color=color)
    if unit:
        r2 = p.add_run()
        r2.text = " " + unit
        set_font(r2, size=Pt(15), bold=False, color=INK_3)

    tb2 = textbox(slide, x, int(y + Emu(640000)), w, Emu(300000))
    para(tb2.text_frame, label, size=FS_SMALL, color=INK_2, line_spacing=1.3,
         first=True)
    return int(y + Emu(1000000))


def divider(slide, y: int, dark=False) -> None:
    rect(slide, MARGIN_X, y, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(11000),
         fill=(WHITE_3 if dark else LINE))


def pill(slide, x, y, text: str, color=None, text_color=None,
         w=None, h=Emu(300000)):
    """胶囊标签。用于图例、类别。"""
    color = color or BLUE
    tw = w if w is not None else Emu(150000 + len(text) * 105000)
    sp = rect(slide, x, y, tw, h, fill=color, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    sp.adjustments[0] = 0.5
    tf = sp.text_frame
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, text, size=Pt(10.5), bold=True,
         color=text_color or WHITE, align=PP_ALIGN.CENTER, first=True)
    return sp


def arrow_down(slide, x, y, w, h, color=None) -> None:
    rect(slide, x, y, w, h, fill=color or LINE, shape=MSO_SHAPE.DOWN_ARROW)


def picture(slide, path, x, y, max_w, max_h, border=False):
    """按最大框等比缩放插入图片，居中。"""
    from PIL import Image
    iw, ih = Image.open(path).size
    scale = min(max_w / iw, max_h / ih)
    w, h = int(iw * scale), int(ih * scale)
    px = int(x + (max_w - w) / 2)
    py = int(y + (max_h - h) / 2)
    pic = slide.shapes.add_picture(str(path), px, py, width=w, height=h)
    if border:
        pic.line.color.rgb = LINE
        pic.line.width = Pt(0.75)
    return pic
