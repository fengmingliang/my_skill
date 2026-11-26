#!/usr/bin/env python3
"""
my_step_config 单页阶梯图渲染器

读取一份车型版型配置 JSON，输出独立可离线打开的 16:9 HTML 单页：
- X 向：按能源类型分列；Y 向：同列内指导价自下而上递增
- 每个版型一个方框；增程/混动浅蓝，纯电浅绿；信息居中两行
- 同列相邻版型间单线向上箭头；箭头右侧文本框标注关键差异
  实心圆点 = 标配/升级包含；空心圆点 = 选装

用法：
    python3 render_step_config.py data.json -o step_config.html
"""

import argparse
import html
import json
import math
import pathlib

W, H = 1280, 720
PAD_L, PAD_R = 70, 70
CHART_TOP, CHART_BOTTOM = 108, 650
BOX_W, BOX_H = 228, 70
GROUP_GAP = 36
BOX_ANN_GAP = 26
MIN_GAP = 30
ANN_LINE_H = 15
ANN_PAD = 8

THEME = {
    "blue": {
        "bg": "#EAF2FC",
        "border": "#9DBFE8",
        "badge_bg": "#2B6CB0",
        "badge_fg": "#FFFFFF",
    },
    "green": {
        "bg": "#EAF5EC",
        "border": "#9CCBA6",
        "badge_bg": "#2F855A",
        "badge_fg": "#FFFFFF",
    },
}

ENERGY_THEME = {
    "EVR": "blue",
    "REEV": "blue",
    "增程": "blue",
    "混动": "blue",
    "PHEV": "blue",
    "HEV": "blue",
    "EV": "green",
    "纯电": "green",
}


def esc(s):
    return html.escape(str(s), quote=True)


def theme_for(group):
    if group.get("theme"):
        return THEME[group["theme"]]
    return THEME[ENERGY_THEME.get(group["energy"].upper(), "blue")]


def fmt_price(trim):
    if trim.get("price_text"):
        return trim["price_text"]
    return "¥{:,}".format(trim["price"])


def seat_diff_text(trim):
    """六座版存在时，返回第三行『五座→六座 +X万』；否则空串。"""
    if trim.get("six_price"):
        diff = trim["six_price"] - trim["price"]
        return "五座→六座 +{:.1f}万".format(diff / 10000)
    return ""


def est_wrapped_lines(text, width_px, font_px=11):
    """估算中文/混排在给定宽度下折成的行数。"""
    units = sum(1 if ord(c) > 0x2E7F else 0.55 for c in text)
    cpl = max(1, width_px / font_px)
    return max(1, math.ceil(units / cpl))


def ann_height(adds, ann_w):
    lines = sum(est_wrapped_lines(a["text"], ann_w) for a in adds)
    return ANN_PAD * 2 + lines * ANN_LINE_H


def render(data):
    groups = data["groups"]
    n = len(groups)
    slot_w = (W - PAD_L - PAD_R - GROUP_GAP * (n - 1)) / n

    all_prices = [t["price"] for g in groups for t in g["trims"]]
    pmin, pmax = min(all_prices), max(all_prices)
    span = (pmax - pmin) or 1
    usable_h = CHART_BOTTOM - CHART_TOP - BOX_H

    def y_top(price):
        return CHART_BOTTOM - BOX_H - (price - pmin) / span * usable_h

    boxes, anns, arrows = [], [], []
    group_labels = []

    for gi, g in enumerate(groups):
        gx = PAD_L + gi * (slot_w + GROUP_GAP)
        theme = theme_for(g)
        trims = sorted(g["trims"], key=lambda t: t["price"])
        label = g.get("label", g["energy"])
        ann_w = slot_w - BOX_W - BOX_ANN_GAP - 12

        transitions = []
        for lo, hi in zip(trims[:-1], trims[1:]):
            adds = lo.get("adds", [])
            ah = ann_height(adds, ann_w) if adds else 0
            transitions.append((lo, hi, adds, ah))

        # 按售价比例定位；相邻版型不足最小间隙时，把上方版型整体上抬保证箭头长度
        pos = [(trims[0], y_top(trims[0]["price"]))]
        for lo, hi, adds, ah in transitions:
            price_top = y_top(hi["price"])
            upper_top = min(price_top, pos[-1][1] - MIN_GAP - BOX_H)
            pos.append((hi, upper_top))

        for t, top in pos:
            seat = seat_diff_text(t)
            seat_html = '<div class="box-seat">{seat}</div>'.format(seat=esc(seat)) if seat else ""
            boxes.append(
                """
                <div class="box" style="left:{left:.1f}px;top:{top:.1f}px;width:{bw}px;height:{bh}px;
                     background:{bg};border-color:{border};">
                  <div class="box-name">{name}</div>
                  <div class="box-price"><span class="box-energy">{energy} {drive}</span>{price}</div>
                  {seat_html}
                </div>""".format(
                    left=gx, top=top, bw=BOX_W, bh=BOX_H,
                    bg=theme["bg"], border=theme["border"],
                    name=esc(t["name"]), energy=esc(g["energy"]),
                    drive=esc(t["drive"]), price=esc(fmt_price(t)),
                    seat_html=seat_html,
                )
            )

        for i, (lo, hi, adds, ah) in enumerate(transitions):
            top_lo, top_hi = pos[i][1], pos[i + 1][1]
            cx = gx + BOX_W / 2
            y1, y2 = top_lo, top_hi + BOX_H
            arrows.append(
                '<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                'stroke="#595959" stroke-width="1.5"/>'
                '<polygon points="{cx:.1f},{yt:.1f} {cl:.1f},{yb:.1f} {cr:.1f},{yb:.1f}" '
                'fill="#595959"/>'.format(
                    x1=cx, y1=y1, x2=cx, y2=y2, cx=cx,
                    yt=y2, cl=cx - 5, cr=cx + 5, yb=y2 + 9,
                )
            )

            if adds:
                ann_left = gx + BOX_W + BOX_ANN_GAP
                y_low, y_high = top_lo, top_hi + BOX_H
                mid = (y_low + y_high) / 2
                ann_top = max(y_high, min(mid - ah / 2, y_low - ah))
                items_html = []
                for a in adds:
                    mark = "solid" if a.get("mark", "solid") == "solid" else "hollow"
                    items_html.append(
                        '<li><span class="dot {mark}"></span><span class="ann-text">{text}</span></li>'.format(
                            mark=mark, text=esc(a["text"]),
                        )
                    )
                anns.append(
                    """
                    <div class="ann" style="left:{al:.1f}px;top:{at:.1f}px;width:{aw:.1f}px;">
                      <ul>{items}</ul>
                    </div>""".format(
                        al=ann_left, at=ann_top, aw=ann_w, items="".join(items_html),
                    )
                )

        group_labels.append((gx, slot_w, g["energy"], label, theme, min(top for _, top in pos)))

    labels_html = []
    for gx, sw, energy, label, theme, top_box in group_labels:
        labels_html.append(
            '<div class="glabel" style="left:{gx:.1f}px;top:{gt:.1f}px;width:{bw:.1f}px;">'
            '<span class="badge" style="background:{bb};color:{bf};">{energy}</span>'
            '<span class="glabel-text">{label}</span></div>'.format(
                gx=gx, gt=top_box - 32, bw=BOX_W, energy=esc(energy), label=esc(label),
                bb=theme["badge_bg"], bf=theme["badge_fg"],
            )
        )

    source = ""
    if data.get("source"):
        source = '<div class="source">{src}</div>'.format(src=esc(data["source"]))

    subtitle_html = ""
    if data.get("subtitle"):
        subtitle_html = '<div class="subtitle">{subtitle}</div>'.format(
            subtitle=esc(data["subtitle"]))

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:"Microsoft YaHei","微软雅黑","PingFang SC","Source Han Sans SC",sans-serif; background:#FFFFFF; }}
  .page {{ position:relative; width:{W}px; height:{H}px; margin:0 auto; background:#FFFFFF; overflow:hidden; }}
  .title {{ position:absolute; left:{PAD_L}px; top:30px; font-size:26px; font-weight:700; color:#C00000; }}
  .subtitle {{ position:absolute; left:{PAD_L}px; top:66px; font-size:14px; color:#595959; }}
  .glabel {{ position:absolute; height:24px; display:flex; align-items:center; justify-content:center; gap:8px; }}
  .badge {{ display:inline-block; padding:2px 10px; border-radius:4px; font-size:13px; font-weight:700; }}
  .glabel-text {{ font-size:15px; color:#000; font-weight:700; }}
  .box {{ position:absolute; border:1.5px solid; border-radius:6px; display:flex; flex-direction:column;
          align-items:center; justify-content:center; gap:5px; }}
  .box-name {{ font-size:15px; font-weight:700; color:#000; text-align:center; line-height:1.3; padding:0 10px; }}
  .box-price {{ font-size:16px; font-weight:700; color:#C00000; }}
  .box-energy {{ color:#000; font-weight:700; margin-right:6px; }}
  .box-seat {{ font-size:10px; color:#595959; }}
  .ann {{ position:absolute; background:transparent; border:none; padding:8px 10px; }}
  .ann ul {{ list-style:none; }}
  .ann li {{ display:flex; align-items:flex-start; gap:7px; margin:4px 0; }}
  .dot {{ flex:none; width:9px; height:9px; border-radius:50%; margin-top:5px; }}
  .dot.solid {{ background:#333; }}
  .dot.hollow {{ background:#FFF; border:1.5px solid #888; }}
  .ann-text {{ font-size:11px; color:#000; line-height:1.35; }}
  .arrows {{ position:absolute; left:0; top:0; }}
  .legend {{ position:absolute; left:{PAD_L}px; bottom:22px; font-size:13px; color:#595959;
             display:flex; align-items:center; gap:18px; }}
  .legend .dot {{ margin-top:0; }}
  .source {{ position:absolute; right:{PAD_R}px; bottom:22px; font-size:12px; color:#8C8C8C; }}
</style>
</head>
<body>
<div class="page">
  <div class="title">{title}</div>
  {subtitle}
  {labels}
  <svg class="arrows" width="{W}" height="{H}">{arrows}</svg>
  {boxes}
  {anns}
  <div class="legend">
    <span><span class="dot solid"></span> 标配 / 升级包含</span>
    <span><span class="dot hollow"></span> 选装</span>
  </div>
  {source}
</div>
</body>
</html>""".format(
        W=W, H=H, PAD_L=PAD_L, PAD_R=PAD_R,
        title=esc(data.get("title", "车型版型阶梯图")),
        subtitle=subtitle_html,
        labels="".join(labels_html),
        arrows="".join(arrows),
        boxes="".join(boxes),
        anns="".join(anns),
        source=source,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", help="配置 JSON 文件路径")
    ap.add_argument("-o", "--out", help="输出 HTML 路径")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.data).read_text(encoding="utf-8"))
    html_out = render(data)
    out = pathlib.Path(args.out) if args.out else pathlib.Path(args.data).with_suffix(".html")
    out.write_text(html_out, encoding="utf-8")
    print("written:", out)


if __name__ == "__main__":
    main()
