#!/usr/bin/env python3
"""
my_step_config 单页阶梯图 PPTX 渲染器

与 render_step_config.py 共用同一份 JSON 数据，输出一页 16:9 原生 .pptx：
- X 向按能源类型分列；Y 向同列指导价自下而上递增
- 方框：增程/混动浅蓝，纯电浅绿；居中两行（版型名-能源码-驱动 / 指导价）
- 同列相邻版型单线向上箭头；箭头右侧差异文本框（无底纹、无边框）
  ● 实心＝标配/升级包含；○ 空心＝选装

用法：
    python3 render_step_config_pptx.py data.json -o step_config.pptx
"""

import argparse
import json
import math
import pathlib

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

# 与 HTML 渲染器一致的 px 坐标系（1280×720），96 dpi 换算为英寸
PX = 1 / 96
W, H = 1280, 720
PAD_L, PAD_R = 70, 70
CHART_TOP, CHART_BOTTOM = 108, 650
BOX_W, BOX_H = 228, 70
GROUP_GAP = 36
BOX_ANN_GAP = 26
MIN_GAP = 30
ANN_LINE_H = 15
ANN_PAD = 8

FONT = "微软雅黑"
RED = RGBColor(0xC0, 0x00, 0x00)
BLACK = RGBColor(0x00, 0x00, 0x00)
GRAY = RGBColor(0x59, 0x59, 0x59)
LIGHT_GRAY = RGBColor(0x8C, 0x8C, 0x8C)
DARK_DOT = RGBColor(0x33, 0x33, 0x33)
HOLLOW_DOT = RGBColor(0x88, 0x88, 0x88)
ARROW = RGBColor(0x59, 0x59, 0x59)

THEME = {
    "blue": {"bg": "EAF2FC", "border": "9DBFE8", "badge": "2B6CB0"},
    "green": {"bg": "EAF5EC", "border": "9CCBA6", "badge": "2F855A"},
}
ENERGY_THEME = {
    "EVR": "blue", "REEV": "blue", "增程": "blue",
    "混动": "blue", "PHEV": "blue", "HEV": "blue",
    "EV": "green", "纯电": "green",
}


def rgb(hexstr):
    return RGBColor(int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16))


def theme_for(group):
    key = group.get("theme") or ENERGY_THEME.get(group["energy"].upper(), "blue")
    return THEME[key]


def fmt_price(trim):
    return trim.get("price_text") or "¥{:,}".format(trim["price"])


def seat_diff_text(trim):
    if trim.get("six_price"):
        diff = trim["six_price"] - trim["price"]
        return "五座→六座 +{:.1f}万".format(diff / 10000)
    return ""


def est_wrapped_lines(text, width_px, font_px=11):
    units = sum(1 if ord(c) > 0x2E7F else 0.55 for c in text)
    cpl = max(1, width_px / font_px)
    return max(1, math.ceil(units / cpl))


def ann_height(adds, ann_w):
    lines = sum(est_wrapped_lines(a["text"], ann_w) for a in adds)
    return ANN_PAD * 2 + lines * ANN_LINE_H


def disable_shadow(shape):
    spPr = shape._element.spPr
    for e in spPr.findall(qn("a:effectLst")):
        spPr.remove(e)
    spPr.append(spPr.makeelement(qn("a:effectLst"), {}))
    style = shape._element.find(qn("p:style"))
    if style is not None:
        shape._element.remove(style)


def style_run(run, size, color, bold=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font._rPr.set(qn("w:eastAsia"), FONT)


def add_textbox(slide, left, top, width, height, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(left * PX), Inches(top * PX),
                                  Inches(width * PX), Inches(height * PX))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Pt(2)
    tf.margin_right = Pt(2)
    tf.margin_top = Pt(1)
    tf.margin_bottom = Pt(1)
    return tb, tf


def render(data, out_path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白版式

    groups = data["groups"]
    n = len(groups)
    slot_w = (W - PAD_L - PAD_R - GROUP_GAP * (n - 1)) / n

    all_prices = [t["price"] for g in groups for t in g["trims"]]
    pmin, pmax = min(all_prices), max(all_prices)
    span = (pmax - pmin) or 1
    usable_h = CHART_BOTTOM - CHART_TOP - BOX_H

    def y_top(price):
        return CHART_BOTTOM - BOX_H - (price - pmin) / span * usable_h

    # 标题 / 副标题（副标题留空则不渲染）
    _, tf = add_textbox(slide, PAD_L, 30, W - 2 * PAD_L, 34)
    r = tf.paragraphs[0].add_run()
    r.text = data.get("title", "车型版型阶梯图")
    style_run(r, 20, RED, bold=True)

    if data.get("subtitle"):
        _, tf = add_textbox(slide, PAD_L, 66, W - 2 * PAD_L, 22)
        r = tf.paragraphs[0].add_run()
        r.text = data["subtitle"]
        style_run(r, 10.5, GRAY)

    for gi, g in enumerate(groups):
        gx = PAD_L + gi * (slot_w + GROUP_GAP)
        theme = theme_for(g)
        trims = sorted(g["trims"], key=lambda t: t["price"])
        ann_w = slot_w - BOX_W - BOX_ANN_GAP - 12

        transitions = []
        for lo, hi in zip(trims[:-1], trims[1:]):
            adds = lo.get("adds", [])
            ah = ann_height(adds, ann_w) if adds else 0
            transitions.append((lo, hi, adds, ah))

        # 按售价比例定位；相邻版型不足最小间隙时上抬上方版型保证箭头长度
        pos = [(trims[0], y_top(trims[0]["price"]))]
        for lo, hi, adds, ah in transitions:
            price_top = y_top(hi["price"])
            upper_top = min(price_top, pos[-1][1] - MIN_GAP - BOX_H)
            pos.append((hi, upper_top))

        for t, top in pos:
            box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, Inches(gx * PX), Inches(top * PX),
                Inches(BOX_W * PX), Inches(BOX_H * PX))
            box.adjustments[0] = 0.08
            box.fill.solid()
            box.fill.fore_color.rgb = rgb(theme["bg"])
            box.line.color.rgb = rgb(theme["border"])
            box.line.width = Pt(1)
            disable_shadow(box)
            tf = box.text_frame
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.word_wrap = True
            tf.margin_top = Pt(2)
            tf.margin_bottom = Pt(2)
            tf.margin_left = Pt(4)
            tf.margin_right = Pt(4)
            p1 = tf.paragraphs[0]
            p1.alignment = PP_ALIGN.CENTER
            r1 = p1.add_run()
            r1.text = t["name"]
            style_run(r1, 11, BLACK, bold=True)
            p2 = tf.add_paragraph()
            p2.alignment = PP_ALIGN.CENTER
            re = p2.add_run()
            re.text = g["energy"] + " " + t["drive"] + " "
            style_run(re, 11, BLACK, bold=True)
            r2 = p2.add_run()
            r2.text = fmt_price(t)
            style_run(r2, 12, RED, bold=True)
            seat = seat_diff_text(t)
            if seat:
                p3 = tf.add_paragraph()
                p3.alignment = PP_ALIGN.CENTER
                r3 = p3.add_run()
                r3.text = seat
                style_run(r3, 10, GRAY)

        # 分组标签：置于本列最高版型框上方，列内居中（各列无需水平对齐）
        top_box = min(top for _, top in pos)
        label_text = g.get("label", g["energy"])
        text_w = len(label_text) * 16
        total_w = 58 + 8 + text_w
        start_x = gx + (BOX_W - total_w) / 2
        badge = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(start_x * PX), Inches((top_box - 30) * PX),
            Inches(58 * PX), Inches(22 * PX))
        badge.adjustments[0] = 0.12
        badge.fill.solid()
        badge.fill.fore_color.rgb = rgb(theme["badge"])
        badge.line.fill.background()
        disable_shadow(badge)
        btf = badge.text_frame
        btf.margin_top = Pt(0)
        btf.margin_bottom = Pt(0)
        bp = btf.paragraphs[0]
        bp.alignment = PP_ALIGN.CENTER
        br = bp.add_run()
        br.text = g["energy"]
        style_run(br, 11, RGBColor(0xFF, 0xFF, 0xFF), bold=True)

        _, tf = add_textbox(slide, start_x + 66, top_box - 30, text_w, 22, MSO_ANCHOR.MIDDLE)
        tf.word_wrap = False
        r = tf.paragraphs[0].add_run()
        r.text = label_text
        style_run(r, 12, BLACK, bold=True)

        # 相邻版型：向上箭头 + 右侧差异标注（无底纹、无边框）
        for i, (t_lo, t_hi, adds, ah) in enumerate(transitions):
            top_lo, top_hi = pos[i][1], pos[i + 1][1]
            cx = gx + BOX_W / 2
            y1 = top_lo            # 下框上沿
            y2 = top_hi + BOX_H   # 上框下沿
            conn = slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                Inches(cx * PX), Inches(y1 * PX),
                Inches(cx * PX), Inches(y2 * PX))
            conn.line.color.rgb = ARROW
            conn.line.width = Pt(1.5)
            ln = conn.line._get_or_add_ln()
            tail = ln.makeelement(qn("a:tailEnd"),
                                  {"type": "triangle", "w": "med", "len": "med"})
            ln.append(tail)

            if adds:
                ann_left = gx + BOX_W + BOX_ANN_GAP
                y_low, y_high = top_lo, top_hi + BOX_H
                mid = (y_low + y_high) / 2
                ann_top = max(y_high, min(mid - ah / 2, y_low - ah))
                _, atf = add_textbox(slide, ann_left, ann_top, ann_w, ah)
                for i2, a in enumerate(adds):
                    para = atf.paragraphs[0] if i2 == 0 else atf.add_paragraph()
                    para.space_after = Pt(3)
                    glyph = "●" if a.get("mark", "solid") == "solid" else "○"
                    dot_color = DARK_DOT if glyph == "●" else HOLLOW_DOT
                    rd = para.add_run()
                    rd.text = glyph + " "
                    style_run(rd, 9.5, dot_color)
                    rt = para.add_run()
                    rt.text = a["text"]
                    style_run(rt, 9.5, BLACK)

    # 图例（仅保留标配/选装说明）
    _, ltf = add_textbox(slide, PAD_L, 684, 500, 22)
    p = ltf.paragraphs[0]
    rd = p.add_run(); rd.text = "● "; style_run(rd, 10, DARK_DOT)
    r = p.add_run(); r.text = "标配 / 升级包含    "; style_run(r, 10, GRAY)
    rd = p.add_run(); rd.text = "○ "; style_run(rd, 10, HOLLOW_DOT)
    r = p.add_run(); r.text = "选装"; style_run(r, 10, GRAY)

    if data.get("source"):
        _, stf = add_textbox(slide, W - PAD_R - 520, 684, 520, 22)
        sp = stf.paragraphs[0]
        sp.alignment = PP_ALIGN.RIGHT
        sr = sp.add_run()
        sr.text = data["source"]
        style_run(sr, 8.5, LIGHT_GRAY)

    prs.save(out_path)
    print("written:", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()
    data = json.loads(pathlib.Path(args.data).read_text(encoding="utf-8"))
    out = pathlib.Path(args.out) if args.out else pathlib.Path(args.data).with_suffix(".pptx")
    render(data, out)


if __name__ == "__main__":
    main()
