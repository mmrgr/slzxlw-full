# -*- coding: utf-8 -*-
"""裁切论文图件的标题与脚注，只留图表主体，供 PPT 使用。

【为什么不用"取最大内容段"的自动判据】
上一版试过：按行投影找连续内容段，取最长的那段当主体。结果图 1（概念图，
由多个色块行组成）和图 3（上下双面板）被切坏——它们内部有大片空白带，
"最长段"只截到了其中一块。

【本版规则：首尾夹逼，不动中间】
1. 顶部：找到第一条"长度 ≥ MIN_GAP 的空白带"，其**起始行**即为标题底边界。
   标题文本之后紧跟的就是这段空白。若第一条长空白带出现在极小 y（<15），
   说明该图没有标题，从 0 开始。
2. 底部：从底向上找第一条"长度 ≥ MIN_GAP 的空白带"，其**结束行**即为
   图表主体的底边界。其下是脚注。
3. 中间一律保留，不做任何"取最长段"的判断。

这套规则要求图的版式是"标题 / 主体 / 脚注"三段式，本项目 6 张主图
（matplotlib suptitle + axes + fig.text）都满足。

个别图（Fig1 概念图、Fig3 双面板）用 MANUAL 表覆盖，因为它们的内部
结构不适合自动判据。

用法：
    python _crop_figs_for_ppt.py            # dry-run，打印裁切范围
    python _crop_figs_for_ppt.py --apply    # 写到 figs/ppt/
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
FIGDIR = HERE / "figs"
OUTDIR = FIGDIR / "ppt"

THRESH = 245
MIN_GAP = 8
PAD = 6
# 行方向向内多收几行：中文标题字形的下伸部（"图""度"等）会越过空白带边界，
# 残留 3–6 行墨迹在画面顶端。向内多收 8 行可彻底切在空白处。
TRIM_IN = 8

# 手工覆盖：(上边界, 下边界, 左, 右)。None 表示用自动判据
# 依据见文件头说明：这几张图的内部结构会干扰自动判据。
MANUAL: dict[str, tuple[int | None, int | None, int | None, int | None]] = {
    # 依据每张图实测的内容块（见 _probe 输出）：
    #   内容块 = 标题 / 面板标题 / 主体 / 图例 / 脚注 的 y 区间
    # 截取范围 = [主体起点, 图例或主体终点]，去掉标题与脚注。

    # Fig1 概念图：11..146 是 suptitle 两行；152..943 是概念图主体；954..1114 脚注
    "Fig1_framework": (150, 947, None, None),
    # Fig2：98..668 是两块面板（含 618..632、646..668 轴标签）；811..833 是图例；876..893 脚注
    # 面板小标题（60..85）保留，它是"D-HA / D-CO"的标识，读者需要它区分左右
    "Fig2_bottleneck_migration": (56, 840, None, None),
    # Fig3：54..860 双面板（含 426..440、846..860 轴标签）；967..1036 脚注
    "Fig3_constraint_trajectories": (54, 868, None, None),
    # Fig4：79..722 双面板（含 669..686、697..722 轴标签）；805..839 脚注
    "Fig4_interventions": (79, 730, None, None),
    # Fig5：81..575 面板（含 524..575 图例）；672..705 脚注
    "Fig5_city_gradient_policy": (81, 583, None, None),
    # Fig6：69..653 双面板（含 633..653 轴标签）；755..789 脚注
    "Fig6_timescale_reservoir": (69, 661, None, None),
}


def long_blanks(d: np.ndarray, minlen: int = MIN_GAP) -> list[tuple[int, int]]:
    blank = d == 0
    runs: list[tuple[int, int]] = []
    st = None
    for y, v in enumerate(blank):
        if v and st is None:
            st = y
        elif not v and st is not None:
            if y - st >= minlen:
                runs.append((st, y - 1))
            st = None
    if st is not None and len(blank) - st >= minlen:
        runs.append((st, len(blank) - 1))
    return runs


def bounds(path: Path) -> tuple[int, int, int, int]:
    im = Image.open(path)
    w, h = im.size
    a = np.array(im.convert("RGB"))
    d = ((a < THRESH).any(axis=2)).sum(axis=1)
    runs = long_blanks(d)

    man = MANUAL.get(path.stem, (None, None, None, None))
    if man[0] is not None:
        y0, y1 = man[0], man[1] if man[1] is not None else h
    else:
        # 顶部：第一条长空白带的起点
        y0 = 0
        for s, e in runs:
            if s >= 12:                 # 太靠上的空白带是页边距，不算标题分隔
                y0 = s
                break
        # 底部：最后一条长空白带的终点
        y1 = h
        for s, e in reversed(runs):
            if h - e >= 12 or e < h - 12:
                y1 = s
                break

    # 列方向收紧
    sub = a[y0:y1]
    colink = ((sub < THRESH).any(axis=2)).sum(axis=0)
    cols = np.where(colink > 0)[0]
    x0 = max(0, int(cols[0]) - PAD) if len(cols) else 0
    x1 = min(w, int(cols[-1]) + PAD) if len(cols) else w

    # 行方向：内侧收紧，而不是向外扩。
    # 中文标题的字形有下伸部分（如"图""度""g"），首行基线之下还会留 3–6 行
    # 墨迹；若向外扩 PAD，反而把这些残字留在画面顶端。这里改为向内再收
    # TRIM_IN 行，确保切在真正的空白处。
    # 手工指定的边界已按内容块实测得到，无需再收，否则会切掉图例。
    if path.stem not in MANUAL:
        y0 = min(h, y0 + TRIM_IN)
        y1 = max(y0 + 10, y1 - TRIM_IN)
    return x0, y0, x1, y1


def squeeze_gaps(im: Image.Image, keep: int = 26, min_gap: int = 28) -> Image.Image:
    """把图内过大的行间空白压到 `keep` 行。

    matplotlib 的 axes 与图例之间常留 100–150 px 空白（figsize 未 tight 时的
    典型值）。论文里这段留白是呼吸感，投影到大屏上就变成"图没铺满"。
    这里只压缩**纯空白带**，不动任何有墨迹的行，因此不会切掉内容。

    判据：连续空白行数 ≥ min_gap 时，只保留中间 keep 行。
    """
    a = np.array(im.convert("RGB"))
    h, w = a.shape[0], a.shape[1]
    d = ((a < THRESH).any(axis=2)).sum(axis=1)
    out: list[np.ndarray] = []
    y = 0
    while y < h:
        if d[y] > 0:
            out.append(a[y])
            y += 1
            continue
        st = y
        while y < h and d[y] == 0:
            y += 1
        run = y - st
        if run >= min_gap:
            take = min(keep, run)
            out.extend([a[st]] * take)
        else:
            out.extend([a[st]] * run)
    if not out:
        return im
    return Image.fromarray(np.stack(out, axis=0))


def main() -> int:
    apply = "--apply" in sys.argv
    print("== 图件裁切 %s ==" % ("APPLY" if apply else "DRY-RUN"))
    for p in sorted(FIGDIR.glob("Fig[1-6]_*.png")):
        im = Image.open(p)
        x0, y0, x1, y1 = bounds(p)
        ow, oh = im.size
        nw, nh = x1 - x0, y1 - y0
        tag = "手工" if p.stem in MANUAL else "自动"
        print("  %-32s %4dx%-4d -> %4dx%-4d  (%.2f)  裁顶%3d 裁底%3d  左%3d 右%3d  [%s]"
              % (p.stem, ow, oh, nw, nh, nw / nh, y0, oh - y1, x0, ow - x1, tag))
        if apply:
            OUTDIR.mkdir(parents=True, exist_ok=True)
            box = im.crop((x0, y0, x1, y1))
            squeezed = squeeze_gaps(box)
            squeezed.save(OUTDIR / (p.stem + "_crop.png"))
            if squeezed.size != box.size:
                print("       └ 压缩空白后 %dx%d" % squeezed.size)
    if apply:
        print("\n输出:", OUTDIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
