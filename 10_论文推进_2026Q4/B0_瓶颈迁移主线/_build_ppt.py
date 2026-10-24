# -*- coding: utf-8 -*-
"""生成导师汇报 PPT（产品级视觉）。

【设计决策，供日后改版参考】
1. **节奏**：深色封面 → 浅色内容 → 深色收尾。深色页只用于"定调"和"收束"，
   中间全部浅色，保证投影时可读性。
2. **每页一句话**：每张内容页只有一条 `lead`（结论句），其余是支撑材料。
   这是"产品级"与"答辩模板"的核心差别——观众每页只应记住一件事。
3. **色带即章节**：左边缘 2.6mm 竖条按章节换色，观众靠颜色定位进度。
4. **图件同源**：所有图直接取 `figs/ppt/*_crop.png`（已裁掉论文式标题与脚注），
   配色与项目图件共用同一套色板，避免"两块蓝不是一块蓝"。
5. **数据标注**：每张图下只放一行口径说明（网格 / 约束集 / 路径），
   因为这是导师最可能追问的三件事。

页面结构（共 10 页）：
  01 封面
  02 一句话结论（全篇论点）
  03 问题：为什么"节水"会变成"费水"
  04 机制：冷却塔是一口锅（核心推导）
  05 证据一：阈值以下精确为零
  06 证据二：惩罚不等于城市疼（阴性对照）
  07 结果：两个城市，两种死法（图2）
  08 结果：三个杠杆量级差一个数量级（图4）
  09 我在担心什么（局限，主动交底）
 10 下一步 + 请老师定两件事
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

HERE = Path(__file__).resolve().parent
FIG = HERE / "figs" / "ppt"

sys.path.insert(0, str(HERE))
import _ppt_kit as K                                    # noqa: E402
from _ppt_design import (                               # noqa: E402
    BG_DARK, BG_SOFT, BLUE, FS_BODY, FS_DISPLAY, FS_H1, FS_H2, FS_LEAD,
    FS_META, FS_NUM, FS_SMALL, GREEN, INK, INK_2, INK_3, LINE, MARGIN_BOTTOM,
    MARGIN_TOP, MARGIN_X, ORANGE, PURPLE, RED, SLIDE_H, SLIDE_W, WHITE,
    WHITE_2, WHITE_3,
)

TOTAL = 10


def new_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


# ===========================================================================
# 01 封面
# ===========================================================================
def s01_cover(prs):
    s = blank(prs)
    K.page_bg(s, dark=True, band_color=BLUE)

    # 右上角极简装饰：一条水平细线 + 项目名
    tb = K.textbox(s, int(SLIDE_W - MARGIN_X - Emu(3800000)), MARGIN_TOP,
                   Emu(3800000), Emu(300000))
    K.para(tb.text_frame, "AI-UWM  ·  城市水代谢与算力承载",
           size=FS_META, color=WHITE_3, align=PP_ALIGN.RIGHT, first=True)

    y = int(SLIDE_H * 0.22)
    tb = K.textbox(s, MARGIN_X, y, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(400000))
    K.para(tb.text_frame, "阶段进展汇报  /  2026.10", size=FS_SMALL, bold=True,
           color=WHITE_3, first=True)

    y += Emu(700000)
    tb = K.textbox(s, MARGIN_X, y, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(1900000))
    tf = tb.text_frame
    K.para(tf, "用再生水给 AI 降温", size=FS_DISPLAY, bold=True, color=WHITE,
           line_spacing=1.15, first=True)
    K.para(tf, "掺多了，反而更费水", size=FS_DISPLAY, bold=True, color=BLUE,
           line_spacing=1.15, space_before=6)

    # 装饰短线：放在两行标题**下方**。
    # 旧写法 y2 = y + 2.05cm 是估算值，实际落到了第二行标题的中间，
    # 看起来像给文字划了下划线。这里改用实测行高推算：
    # 一行 54pt 标题 + 1.15 行距 ≈ 0.87 cm，两行 ≈ 1.74 cm，再加间距。
    y2 = int(y + Emu(1780000) + Emu(150000))
    K.rect(s, MARGIN_X, y2, Emu(1500000), Emu(36000), fill=BLUE)

    y3 = y2 + Emu(340000)
    tb = K.textbox(s, MARGIN_X, y3, Emu(int(SLIDE_W * 0.52)), Emu(900000))
    tf = tb.text_frame
    K.para(tf, "一个可以算出来的临界替代率，以及它什么时候才真的会把一座城市卡住",
           size=FS_BODY, color=WHITE_2, line_spacing=1.5, first=True)

    # 汇报人（右下）
    tb = K.textbox(s, int(SLIDE_W - MARGIN_X - Emu(4200000)),
                   int(SLIDE_H - Emu(1300000)), Emu(4200000), Emu(700000))
    tf = tb.text_frame
    K.para(tf, "邵敬哲  ·  24S129122", size=FS_BODY, bold=True, color=WHITE,
           align=PP_ALIGN.RIGHT, first=True)
    K.para(tf, "指导教师：白舜文    |    环境学院 · 资源与环境",
           size=FS_SMALL, color=WHITE_3, align=PP_ALIGN.RIGHT, space_before=4)


# ===========================================================================
# 02 一句话结论
# ===========================================================================
def s02_onesentence(prs):
    s = blank(prs)
    K.page_bg(s, band_color=BLUE)
    y = K.page_title(s, "先说结论", "这半年我算出来一个数，和它成立的条件")

    # 三块并排：数字 / 条件 / 边界
    y0 = int(y + Emu(120000))
    cw = int((SLIDE_W - 2 * MARGIN_X - Emu(260000) * 2) / 3)

    K.kpi(s, MARGIN_X, y0, cw, "0.5532", "", "临界替代率\n超过它，继续掺再生水会抬高总补水")
    K.kpi(s, int(MARGIN_X + cw + Emu(260000)), y0, cw, "精确为零", "",
          "阈值以下的响应\n不是“很小”，是数值零（1e-12 量级）", color=GREEN)
    K.kpi(s, int(MARGIN_X + (cw + Emu(260000)) * 2), y0, cw, "2 个条件", "",
          "水质惩罚 + 瓶颈在水量侧\n缺一个，容量一点都不动", color=ORANGE)

    K.divider(s, int(y0 + Emu(1250000)))

    y1 = int(y0 + Emu(1420000))
    tb = K.textbox(s, MARGIN_X, y1, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(900000))
    tf = tb.text_frame
    K.para_rich(tf, [
        ("一句话：", True, INK),
        ("再生水掺到 55% 左右是免费的安全区；过了这条线，水会变咸、浓缩倍数被压下来、"
         "要补更多的水。", False, INK_2),
    ], size=FS_BODY, line_spacing=1.55, first=True)
    K.para_rich(tf, [
        ("但这笔账只有落在“本来就卡在水上”的城市，才会真的变成容量损失。", True, INK),
    ], size=FS_BODY, line_spacing=1.55, space_before=8)

    K.footer(s, "全部结果来自两个合成参数端点的日尺度模型；不对应任何真实城市", 2)


# ===========================================================================
# 03 问题
# ===========================================================================
def s03_problem(prs):
    s = blank(prs)
    K.page_bg(s, band_color=BLUE)
    y = K.page_title(s, "问题", "“用中水冷却 = 省水”，这个等式有个洞")

    y = K.lead(s, y, "洞在两个字上：不是“水够不够”，而是“这个水咸不咸”。")

    # 左右对照
    col_w = int((SLIDE_W - 2 * MARGIN_X - Emu(300000)) / 2)
    box_h = Emu(2250000)
    y0 = int(y + Emu(180000))

    # 左：常见说法
    x1 = MARGIN_X
    K.rect(s, x1, y0, col_w, box_h, fill=BG_SOFT, line=LINE)
    K.rect(s, x1, y0, col_w, Emu(46000), fill=INK_3)
    tb = K.textbox(s, int(x1 + Emu(260000)), int(y0 + Emu(300000)),
                   int(col_w - Emu(520000)), Emu(400000))
    K.para(tb.text_frame, "常见的算法", size=FS_H2, bold=True, color=INK, first=True)
    tb = K.textbox(s, int(x1 + Emu(260000)), int(y0 + Emu(780000)),
                   int(col_w - Emu(520000)), Emu(1300000))
    tf = tb.text_frame
    K.para(tf, "再生水 1 : 1 替代自来水 → 掺得越多 → 省的自来水越多",
           size=FS_BODY, color=INK_2, line_spacing=1.5, first=True)
    K.para(tf, "结论：替代率越高越好，应该往 100% 推。",
           size=FS_BODY, bold=True, color=INK_3, line_spacing=1.5, space_before=10)

    # 右：本文
    x2 = int(MARGIN_X + col_w + Emu(300000))
    K.rect(s, x2, y0, col_w, box_h, fill=BG_SOFT, line=LINE)
    K.rect(s, x2, y0, col_w, Emu(46000), fill=ORANGE)
    tb = K.textbox(s, int(x2 + Emu(260000)), int(y0 + Emu(300000)),
                   int(col_w - Emu(520000)), Emu(400000))
    K.para(tb.text_frame, "漏掉的一环", size=FS_H2, bold=True, color=INK, first=True)
    tb = K.textbox(s, int(x2 + Emu(260000)), int(y0 + Emu(780000)),
                   int(col_w - Emu(520000)), Emu(1300000))
    tf = tb.text_frame
    K.para(tf, "再生水比自来水咸 → 混合后更咸 → 冷却塔能浓缩的倍数被压低 → "
               "散同样的热，要补更多的水",
           size=FS_BODY, color=INK_2, line_spacing=1.5, first=True)
    K.para(tf, "所以掺多了，总补水反而上升。", size=FS_BODY, bold=True,
           color=ORANGE, line_spacing=1.5, space_before=10)

    # 底部一句点题
    yb = int(y0 + box_h + Emu(300000))
    tb = K.textbox(s, MARGIN_X, yb, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(500000))
    K.para_rich(tb.text_frame, [
        ("那么问题就很具体了：", False, INK_3),
        ("掺到多少，这个反噬才开始？", True, INK),
    ], size=FS_LEAD, line_spacing=1.3, first=True)

    K.footer(s, "机制链条：混合补水含盐量 → 允许浓缩倍数 → 单位散热补水需求", 3)


# ===========================================================================
# 04 机制 / 推导
# ===========================================================================
def s04_derivation(prs):
    s = blank(prs)
    K.page_bg(s, band_color=PURPLE)
    y = K.page_title(s, "机制", "天花板是死的，但你的余量是活的")

    y = K.lead(s, y, "冷却塔像一口锅：水蒸发走了，盐留下来，越熬越咸。")

    # 左：推导过程
    lw = int(SLIDE_W * 0.46)
    ly = int(y + Emu(140000))

    steps = [
        ("① 盐不蒸发", "补水带入的盐 = 排污带走的盐：M·C_mix = B·C_loop"),
        ("② 定义浓缩倍数", "CoC = M / B，即“水被循环了几遍”"),
        ("③ 撞上天花板", "循环水不能太咸：C_loop ≤ L  ⟹  CoC ≤ L / C_mix(r)"),
        ("④ 混合浓度", "C_mix(r) = r·C_r + (1−r)·C_p，r 是再生水比例"),
    ]
    sy = ly
    for i, (h, b) in enumerate(steps):
        tb = K.textbox(s, MARGIN_X, sy, lw, Emu(300000))
        K.para(tb.text_frame, h, size=Pt(14), bold=True, color=PURPLE, first=True)
        tb = K.textbox(s, MARGIN_X, int(sy + Emu(290000)), lw, Emu(330000))
        K.para(tb.text_frame, b, size=Pt(13), color=INK_2, line_spacing=1.35, first=True)
        sy = int(sy + Emu(760000))

    # 右：结果卡片
    rw = int(SLIDE_W - 2 * MARGIN_X - lw - Emu(420000))
    rx = int(MARGIN_X + lw + Emu(420000))
    rh = int(Emu(2830000))

    K.rect(s, rx, ly, rw, rh, fill=BG_DARK, line=None)
    K.rect(s, rx, ly, rw, Emu(46000), fill=PURPLE)

    tb = K.textbox(s, int(rx + Emu(300000)), int(ly + Emu(280000)),
                   int(rw - Emu(600000)), Emu(300000))
    K.para(tb.text_frame, "令水质上限 = 设计值，解出 r", size=FS_SMALL, bold=True,
           color=WHITE_3, first=True)

    # 公式拆成两行：单行 21pt 在 46% 栏宽里会溢出卡片右边界
    # （实测越界约 1cm），拆行后每行都留足余量。
    tb = K.textbox(s, int(rx + Emu(300000)), int(ly + Emu(620000)),
                   int(rw - Emu(600000)), Emu(760000))
    tf = tb.text_frame
    K.para(tf, "r* = (L / CoC_d − C_p)", size=Pt(19), bold=True, color=WHITE,
           line_spacing=1.35, first=True)
    K.para(tf, "       / (C_r − C_p)", size=Pt(19), bold=True, color=WHITE,
           line_spacing=1.35)

    # 代入数值
    tb = K.textbox(s, int(rx + Emu(300000)), int(ly + Emu(1420000)),
                   int(rw - Emu(600000)), Emu(400000))
    K.para(tb.text_frame, "代入：L=2200、CoC_d=5、C_p=180、C_r=650",
           size=FS_SMALL, color=WHITE_3, first=True)

    tb = K.textbox(s, int(rx + Emu(300000)), int(ly + Emu(2130000)),
                   int(rw - Emu(600000)), Emu(600000))
    p = tb.text_frame.paragraphs[0]
    p.line_spacing = 1.0
    r1 = p.add_run()
    r1.text = "r* = 0.5532"
    K.set_font(r1, size=Pt(30), bold=True, color=BLUE)
    r2 = p.add_run()
    r2.text = "   ≈ 55%"
    K.set_font(r2, size=Pt(15), bold=False, color=WHITE_3)

    tb = K.textbox(s, int(rx + Emu(300000)), int(ly + Emu(2600000)),
                   int(rw - Emu(600000)), Emu(300000))
    K.para(tb.text_frame, "氯化物给出 68.4%，取较紧的仍是 TDS 的 55.3%",
           size=FS_SMALL, color=WHITE_2, first=True)

    # 底部注解：贴在卡片下方，与左侧推导列的末行对齐
    yb = int(ly + rh + Emu(240000))
    tb = K.textbox(s, MARGIN_X, yb, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(560000))
    K.para_rich(tb.text_frame, [
        ("关键直觉：", True, PURPLE),
        ("补水最多能到 440 mg/L。自来水 180，还有 260 的空间可以掺；"
         "如果某地自来水本身就 420，只剩 20 的空间——掺 8% 就到顶了。", False, INK_2),
    ], size=Pt(13), line_spacing=1.4, first=True)

    K.footer(s, "推导：稳态盐平衡 + 结垢腐蚀限值；L、CoC_d、C_p、C_r 四个参数均无实测锚点", 4)


# ===========================================================================
# 05 证据一：精确为零
# ===========================================================================
def s05_zero(prs):
    s = blank(prs)
    K.page_bg(s, band_color=GREEN)
    y = K.page_title(s, "证据一", "阈值以下，反噬是“精确的零”")

    y = K.lead(s, y, "不是“很小”，是数值零——小数点后十几位都没动。")

    # 两个数据卡
    cw = int((SLIDE_W - 2 * MARGIN_X - Emu(300000)) / 2)
    y0 = int(y + Emu(160000))
    ch = Emu(1500000)

    K.rect(s, MARGIN_X, y0, cw, ch, fill=BG_SOFT, line=LINE)
    tb = K.textbox(s, int(MARGIN_X + Emu(280000)), int(y0 + Emu(230000)),
                   int(cw - Emu(560000)), Emu(300000))
    K.para(tb.text_frame, "r ≤ r* 时", size=FS_SMALL, bold=True, color=GREEN, first=True)
    tb = K.textbox(s, int(MARGIN_X + Emu(280000)), int(y0 + Emu(540000)),
                   int(cw - Emu(560000)), Emu(600000))
    p = tb.text_frame.paragraphs[0]
    p.line_spacing = 1.0
    r = p.add_run()
    r.text = "7.3e−12"
    K.set_font(r, size=Pt(38), bold=True, color=GREEN)
    tb = K.textbox(s, int(MARGIN_X + Emu(280000)), int(y0 + Emu(1080000)),
                   int(cw - Emu(560000)), Emu(300000))
    K.para(tb.text_frame, "承载容量与总取水的响应量（数值零）", size=FS_SMALL,
           color=INK_3, first=True)

    x2 = int(MARGIN_X + cw + Emu(300000))
    K.rect(s, x2, y0, cw, ch, fill=BG_SOFT, line=LINE)
    tb = K.textbox(s, int(x2 + Emu(280000)), int(y0 + Emu(230000)),
                   int(cw - Emu(560000)), Emu(300000))
    K.para(tb.text_frame, "r > r* 后（200–1600 MW）", size=FS_SMALL, bold=True,
           color=ORANGE, first=True)
    tb = K.textbox(s, int(x2 + Emu(280000)), int(y0 + Emu(540000)),
                   int(cw - Emu(560000)), Emu(600000))
    p = tb.text_frame.paragraphs[0]
    p.line_spacing = 1.0
    r = p.add_run()
    r.text = "+6.47% ~ 6.48%"
    K.set_font(r, size=Pt(30), bold=True, color=ORANGE)
    tb = K.textbox(s, int(x2 + Emu(280000)), int(y0 + Emu(1080000)),
                   int(cw - Emu(560000)), Emu(300000))
    K.para(tb.text_frame, "总取水增幅，与数据中心容量完全无关（极差 0.012 个百分点）",
           size=FS_SMALL, color=INK_3, first=True)

    # 为什么这条重要
    yb = int(y0 + ch + Emu(360000))
    K.rect(s, MARGIN_X, yb, Emu(52000), Emu(900000), fill=GREEN)
    tb = K.textbox(s, int(MARGIN_X + Emu(240000)), yb,
                   Emu(int(SLIDE_W - 2 * MARGIN_X - Emu(300000))), Emu(900000))
    tf = tb.text_frame
    K.para(tf, "为什么这条最硬：因为它能被证伪。", size=FS_H2, bold=True,
           color=INK, first=True)
    K.para(tf, "渐变型机制永远只能给出“很小”；而“这里应该恰好不动”是一个明确的预言——"
               "任何人测到一个非零，这个结论就错了。",
           size=FS_BODY, color=INK_2, line_spacing=1.45, space_before=8)
    K.para(tf, "打个比方：汤的咸淡只跟放多少盐有关，跟煮一锅还是十锅真的没关系。"
               "而这个“没关系”，是可以拿尺子量的。",
           size=FS_BODY, color=INK_2, line_spacing=1.45, space_before=8)

    K.footer(s, "50/25/10 MW 三种网格下该零效应均复现；主结果走 legacy 体积路径", 5)


# ===========================================================================
# 06 证据二：阴性对照
# ===========================================================================
def s06_negative(prs):
    s = blank(prs)
    K.page_bg(s, band_color=ORANGE)
    y = K.page_title(s, "证据二", "惩罚发生了，但城市可能根本不疼")

    y = K.lead(s, y, "同样的水质惩罚，一个城市掉了 100 MW，另一个几乎没动。")

    # 两列对照
    cw = int((SLIDE_W - 2 * MARGIN_X - Emu(340000)) / 2)
    y0 = int(y + Emu(150000))
    ch = Emu(1750000)

    # 缺水端点
    K.rect(s, MARGIN_X, y0, cw, ch, fill=BG_SOFT, line=LINE)
    K.rect(s, MARGIN_X, y0, cw, Emu(46000), fill=BLUE)
    tb = K.textbox(s, int(MARGIN_X + Emu(270000)), int(y0 + Emu(280000)),
                   int(cw - Emu(540000)), Emu(340000))
    K.para(tb.text_frame, "D-HA  缺水—高冷负荷", size=FS_H2, bold=True,
           color=BLUE, first=True)
    tb = K.textbox(s, int(MARGIN_X + Emu(270000)), int(y0 + Emu(700000)),
                   int(cw - Emu(540000)), Emu(950000))
    tf = tb.text_frame
    K.para(tf, "替代率 0.5 → 0.9：容量掉约 100 MW", size=FS_BODY, bold=True,
           color=INK, first=True)
    K.para(tf, "而电网约束全程纹丝不动（Δ = 0.0000）", size=FS_BODY,
           color=INK_2, space_before=6)
    K.para(tf, "→ 瓶颈在水量侧，惩罚落到了容量上", size=FS_SMALL, color=BLUE,
           space_before=8)

    # 凉爽端点
    x2 = int(MARGIN_X + cw + Emu(340000))
    K.rect(s, x2, y0, cw, ch, fill=BG_SOFT, line=LINE)
    K.rect(s, x2, y0, cw, Emu(46000), fill=ORANGE)
    tb = K.textbox(s, int(x2 + Emu(270000)), int(y0 + Emu(280000)),
                   int(cw - Emu(540000)), Emu(340000))
    K.para(tb.text_frame, "D-CO  气候凉爽", size=FS_H2, bold=True,
           color=ORANGE, first=True)
    tb = K.textbox(s, int(x2 + Emu(270000)), int(y0 + Emu(700000)),
                   int(cw - Emu(540000)), Emu(950000))
    tf = tb.text_frame
    K.para(tf, "水质惩罚同样发生了", size=FS_BODY, bold=True, color=INK, first=True)
    K.para(tf, "水一样变咸、补水一样往上走", size=FS_BODY, color=INK_2, space_before=6)
    K.para(tf, "→ 但容量几乎没变：它本来就卡在电上", size=FS_SMALL, color=ORANGE,
           space_before=8)

    # 比喻
    yb = int(y0 + ch + Emu(300000))
    K.rect(s, MARGIN_X, yb, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(1000000),
           fill=BG_SOFT, line=LINE)
    tb = K.textbox(s, int(MARGIN_X + Emu(300000)), int(yb + Emu(180000)),
                   Emu(int(SLIDE_W - 2 * MARGIN_X - Emu(600000))), Emu(700000))
    tf = tb.text_frame
    K.para_rich(tf, [
        ("打个比方：", True, INK),
        ("一个人被门卡住了过不去，你给他背上加 20 斤的包。包确实重了，"
         "但他进不进得去，跟背包没关系，跟门有关系。", False, INK_2),
    ], size=Pt(14), line_spacing=1.45, first=True)

    # 结论条
    yc = int(yb + Emu(1150000))
    tb = K.textbox(s, MARGIN_X, yc, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(400000))
    K.para_rich(tb.text_frame, [
        ("所以机制要两个条件同时成立：", False, INK_3),
        ("水质惩罚（推的力气）  +  瓶颈在水量侧（门没被别的东西卡死）", True, ORANGE),
    ], size=Pt(14.5), line_spacing=1.3, first=True)

    K.footer(s, "另有气候条件：夏季 +4 ℃ 下凉爽端点降幅由 50 MW 增至 100 MW", 6)


# ===========================================================================
# 07 图 2
# ===========================================================================
def s07_fig2(prs):
    s = blank(prs)
    K.page_bg(s, band_color=BLUE)
    y = K.page_title(s, "结果 · 约束结构", "两个端点，两种死法")

    y = K.lead(s, y, "骨架完全相同，只有气候和设施参数不同——差异只能来自余量结构。")

    # 图：高度由"页脚上沿 − 注解高度"反推，而不是给经验值。
    # 之前固定 3100000 时，注解起点越过了页脚行，两段文字叠在一起。
    img = FIG / "Fig2_bottleneck_migration_crop.png"
    FOOT_TOP = int(SLIDE_H - MARGIN_BOTTOM - Emu(150000))
    NOTE_H = Emu(520000)
    iy = int(y + Emu(60000))
    ih = int(FOOT_TOP - iy - NOTE_H - Emu(180000))
    K.picture(s, img, MARGIN_X, iy, Emu(int(SLIDE_W - 2 * MARGIN_X)), ih)

    # 图下注解
    yb = int(iy + ih + Emu(130000))
    tb = K.textbox(s, MARGIN_X, yb, Emu(int(SLIDE_W - 2 * MARGIN_X)), NOTE_H)
    tf = tb.text_frame
    K.para_rich(tf, [
        ("口径：", True, INK_3),
        ("1200 / 1500 MW 是首次失效容量；对应的最大安全容量（前一个 50 MW 网格点）"
         "是 1150 / 1450 MW，两个数不能混着说。", False, INK_2),
    ], size=Pt(12), line_spacing=1.35, first=True)
    K.para_rich(tf, [
        ("另外：", True, INK_3),
        ("污水厂利用率在两端点都“从未失效”——但这不是安全，只是扫描没到达"
         "（上限翻倍到 4000 MW 后多数约束都会失效）。", False, INK_2),
    ], size=Pt(12), line_spacing=1.35, space_before=3)

    K.footer(s, "图 2｜日尺度、联合约束集、50–2000 MW 扫描；确定性单次扫描，无抽样误差估计", 7)


# ===========================================================================
# 08 图 4 / 三杠杆
# ===========================================================================
def s08_fig4(prs):
    s = blank(prs)
    K.page_bg(s, band_color=GREEN)
    y = K.page_title(s, "结果 · 干预反事实", "三个“看起来一样”的杠杆，量级差一个数量级")

    y = K.lead(s, y, "对症的干预有增益，非对症的增益恰好为零——而且两端互斥。")

    img = FIG / "Fig4_interventions_crop.png"
    ih = Emu(2750000)
    iy = int(y + Emu(60000))
    K.picture(s, img, MARGIN_X, iy, Emu(int(SLIDE_W * 0.56)), ih)

    # 右侧三杠杆
    rx = int(MARGIN_X + SLIDE_W * 0.56 + Emu(120000))
    rw = int(SLIDE_W - MARGIN_X - rx)
    ry = iy

    items = [
        ("扩处理能力", "把桶做大", "无效", "0 MW", INK_3),
        ("提再生水产量", "多接一根水管", "有效，还能挪瓶颈", "+350~400 MW", GREEN),
        ("提替代率", "往汤里多放盐", "过阈值后有害", "−50~−100 MW", ORANGE),
    ]
    # 三张卡片总高须 ≤ 左图高度，否则会压到图下的橙色注解条。
    # 卡片 880000、步进 900000，三张共 2680000 < 图高 2750000。
    for name, metaphor, verdict, num, col in items:
        K.rect(s, rx, ry, rw, Emu(880000), fill=BG_SOFT, line=LINE)
        K.rect(s, rx, ry, Emu(46000), Emu(880000), fill=col)
        tb = K.textbox(s, int(rx + Emu(220000)), int(ry + Emu(120000)),
                       int(rw - Emu(340000)), Emu(280000))
        K.para(tb.text_frame, name, size=Pt(13.5), bold=True, color=INK, first=True)
        tb = K.textbox(s, int(rx + Emu(220000)), int(ry + Emu(420000)),
                       int(rw - Emu(340000)), Emu(280000))
        K.para_rich(tb.text_frame, [
            (f"{metaphor}　", False, INK_3),
            (verdict, True, col),
        ], size=Pt(11.5), first=True)
        tb = K.textbox(s, int(rx + Emu(220000)), int(ry + Emu(620000)),
                       int(rw - Emu(340000)), Emu(240000))
        K.para(tb.text_frame, num, size=Pt(12), bold=True, color=col, first=True)
        ry = int(ry + Emu(900000))

    # 底部反直觉
    yb = int(iy + ih + Emu(190000))
    K.rect(s, MARGIN_X, yb, Emu(52000), Emu(720000), fill=ORANGE)
    tb = K.textbox(s, int(MARGIN_X + Emu(240000)), yb,
                   Emu(int(SLIDE_W - 2 * MARGIN_X - Emu(300000))), Emu(720000))
    tf = tb.text_frame
    K.para_rich(tf, [
        ("还有一条挺打脸的：", True, INK),
        ("多产水并不能抵消多掺咸水的惩罚。", True, ORANGE),
    ], size=Pt(14), first=True)
    K.para(tf, "缺水城市产量拉到最高时，惩罚反而从 −50 变成 −100。"
               "产水抬的是供水侧，惩罚打在需求侧的化学上——就像多打几口井，"
               "并不改变汤越来越咸这件事。",
           size=Pt(12.5), color=INK_2, line_spacing=1.4, space_before=5)

    K.footer(s, "图 4｜9 项干预 × 2 域，均已统一在 50 MW 网格重跑，基线 1150 / 1450 MW", 8)


# ===========================================================================
# 09 局限
# ===========================================================================
def s09_limits(prs):
    s = blank(prs)
    K.page_bg(s, band_color=RED)
    y = K.page_title(s, "我在担心什么", "这几条不说清楚，上面那些数字就不该被当真")

    y = K.lead(s, y, "我主动讲，因为它们决定这些结果现在能用到什么程度。")

    y0 = int(y + Emu(130000))
    ch = Emu(1960000)

    # 三个风险卡
    cw = int((SLIDE_W - 2 * MARGIN_X - Emu(220000) * 2) / 3)
    cards = [
        ("全是合成数据", "没碰过真城市",
         "所有容量结果来自两个合成的参数端点。这些 MW 数字不能当成"
         "“某城市能承载多少”来读。驱动是合成的，`hydrology_validation = NONE`。"),
        ("一个参数能翻盘", "自来水含盐量",
         "我取 180 mg/L，但加州一万多个地下水实测里它只在第 14 百分位，中位是 420。"
         "改成 420，安全线从 55% 掉到 8.7%——结论整个翻过来。"),
        ("效应比噪声还小", "100 MW < ±150 MW",
         "1024 次抽样下抽样带宽约 ±150 MW，比我主张的 100 MW 还大。"
         "所以这个数只能读成两个情景的差值，不是可分辨的统计信号。"),
    ]
    for i, (h, sub, body) in enumerate(cards):
        x = int(MARGIN_X + (cw + Emu(220000)) * i)
        K.rect(s, x, y0, cw, ch, fill=BG_SOFT, line=LINE)
        K.rect(s, x, y0, cw, Emu(46000), fill=RED)
        tb = K.textbox(s, int(x + Emu(240000)), int(y0 + Emu(280000)),
                       int(cw - Emu(480000)), Emu(320000))
        K.para(tb.text_frame, h, size=Pt(15), bold=True, color=INK, first=True)
        tb = K.textbox(s, int(x + Emu(240000)), int(y0 + Emu(620000)),
                       int(cw - Emu(480000)), Emu(280000))
        K.para(tb.text_frame, sub, size=Pt(11), bold=True, color=RED, first=True)
        tb = K.textbox(s, int(x + Emu(240000)), int(y0 + Emu(940000)),
                       int(cw - Emu(480000)), Emu(950000))
        K.para(tb.text_frame, body, size=Pt(11.5), color=INK_2,
               line_spacing=1.38, first=True)

    # 底部：已自查修正
    yb = int(y0 + ch + Emu(240000))
    K.rect(s, MARGIN_X, yb, Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(780000),
           fill=BG_SOFT, line=LINE)
    tb = K.textbox(s, int(MARGIN_X + Emu(280000)), int(yb + Emu(140000)),
                   Emu(int(SLIDE_W - 2 * MARGIN_X - Emu(560000))), Emu(560000))
    tf = tb.text_frame
    K.para_rich(tf, [
        ("另外，", False, INK_3),
        ("最近自查修了几个错：", True, INK),
        ("“两类情形已复现”→“除情形 IV 外均已复现”；509→603 mg/L；"
         "图 4 干预混用 50/100 MW 网格已统一。", False, INK_2),
    ], size=Pt(12), line_spacing=1.35, first=True)
    K.para_rich(tf, [
        ("最险的一个：", True, RED),
        ("我一度把动态路径“效应消失”归因于物理机制，还准备写进论文——"
         "查出来是实现 bug（水质覆盖整体替换而非合并）。修完效应减半，不是消失。", False, INK_2),
    ], size=Pt(12), line_spacing=1.35, space_before=3)

    K.footer(s, "判据本身不受这些影响：r* 是四个水质参数的代数性质，与模型走哪条路径无关", 9)


# ===========================================================================
# 10 下一步
# ===========================================================================
def s10_next(prs):
    s = blank(prs)
    K.page_bg(s, dark=True, band_color=BLUE)

    y = K.page_title(s, "下一步", "想把力气花在“更可信”上，而不是“更大”上",
                     dark=True)

    # 左：四件事
    lw = int(SLIDE_W * 0.55)
    ly = int(y + Emu(120000))
    items = [
        ("01", "统一口径", "容量定义、扫描网格、混合水质数值、干预基线收成一本可追溯的账"),
        ("02", "再验水质链", "重点：目标替代率 vs 实际交付比例——现在按目标算，高替代率段惩罚被高估"),
        ("03", "分界线敏感性", "水侧 / 电力侧那条界什么时候移动。比多跑几百个容量点有价值"),
        ("04", "找真实数据", "找得到就做外部锚定；找不到就老实说是合成情景研究"),
    ]
    sy = ly
    for num, h, b in items:
        tb = K.textbox(s, MARGIN_X, sy, Emu(500000), Emu(300000))
        K.para(tb.text_frame, num, size=Pt(13), bold=True, color=BLUE, first=True)
        tb = K.textbox(s, int(MARGIN_X + Emu(560000)), sy, int(lw - Emu(560000)),
                       Emu(300000))
        K.para(tb.text_frame, h, size=Pt(15), bold=True, color=WHITE, first=True)
        tb = K.textbox(s, int(MARGIN_X + Emu(560000)), int(sy + Emu(320000)),
                       int(lw - Emu(560000)), Emu(400000))
        K.para(tb.text_frame, b, size=Pt(11.5), color=WHITE_3, line_spacing=1.35,
               first=True)
        sy = int(sy + Emu(950000))

    # 右：两个问题
    rx = int(MARGIN_X + lw + Emu(200000))
    rw = int(SLIDE_W - MARGIN_X - rx)

    tb = K.textbox(s, rx, ly, rw, Emu(320000))
    K.para(tb.text_frame, "想请老师帮我定两件事", size=Pt(13), bold=True,
           color=WHITE_3, first=True)

    qs = [
        ("Q1", "下一步的力气往哪使？",
         "先把这个机制的判别做扎实，还是先找一个真实城市做案例？\n"
         "我倾向先做机制——真城市设施级率定数据不好拿，勉强做容易变成参数的演示。"
         "但这也可能是我在偷懒。"),
        ("Q2", "论文要不要收窄？",
         "收窄到“水质兼容性怎么影响城市约束”一条主线，还是保留水代谢框架、"
         "时间尺度、工程干预这些更宽的内容？\n"
         "我倾向收窄，但收窄了工作量看起来会薄一些。"),
    ]
    qy = int(ly + Emu(430000))
    for tag, q, a in qs:
        K.rect(s, rx, qy, rw, Emu(1420000), fill=BG_DARK_2 if False else None,
               line=WHITE_3)
        tb = K.textbox(s, int(rx + Emu(240000)), int(qy + Emu(170000)),
                       int(rw - Emu(480000)), Emu(300000))
        K.para_rich(tb.text_frame, [
            (tag + "　", True, BLUE),
            (q, True, WHITE),
        ], size=Pt(14), first=True)
        tb = K.textbox(s, int(rx + Emu(240000)), int(qy + Emu(540000)),
                       int(rw - Emu(480000)), Emu(800000))
        K.para(tb.text_frame, a, size=Pt(11.5), color=WHITE_3, line_spacing=1.38,
               first=True)
        qy = int(qy + Emu(1520000))

    # 收尾一句
    tb = K.textbox(s, MARGIN_X, int(SLIDE_H - Emu(1150000)),
                   Emu(int(SLIDE_W - 2 * MARGIN_X)), Emu(400000))
    K.para(tb.text_frame, "另外：开题承诺的“等效普通工业冷却对照”还没做，想听听是否仍需补。",
           size=Pt(11), color=WHITE_3, first=True)

    K.footer(s, "邵敬哲 · 2026.10.20", 10, dark=True)


# ===========================================================================
def main() -> int:
    prs = new_deck()
    s01_cover(prs)
    s02_onesentence(prs)
    s03_problem(prs)
    s04_derivation(prs)
    s05_zero(prs)
    s06_negative(prs)
    s07_fig2(prs)
    s08_fig4(prs)
    s09_limits(prs)
    s10_next(prs)

    out = HERE / "62_导师汇报_10页_20261020.pptx"
    prs.save(out)
    print(f"[OK] {out.name}  {out.stat().st_size/1e6:.2f} MB  {len(prs.slides)} 页")
    return 0


if __name__ == "__main__":
    sys.exit(main())
