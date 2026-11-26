# 静态 SVG 图表规范

本文件规定本技能所有报告的图表画法。**默认不使用 ECharts 或任何第三方图表库**，图表一律为内联静态 SVG。

## 一、总原则

1. **构建期算坐标，产物里是字面 SVG**：在生成报告时用脚本（Python/手算）算好每个 `<rect>` / `<path>` / `<text>` 的坐标，直接写成静态字面值。运行时不再计算，保证离线、转发、打印都不失败。
2. **不引入图表库**：禁止 `echarts.min.js`、Chart.js、D3、Highcharts；禁止任何 CDN 引用。报告是自包含单文件。
3. **不默认加交互**：不加 tooltip、hover 高亮、图例联动、动画、缩放。只有用户明确要求交互时，才用原生 CSS/JS 补最小交互。
4. **一张图只回答一个问题**：图题写成陈述句或明确指标名，不写"数据分析"这类空标题。
5. **必须有完整要素**：图题、单位、坐标轴刻度（或直接数值标签）、来源与口径脚注。

## 二、画布与坐标约定

推荐两档 `viewBox`：

| 用途 | viewBox | 边距 left/top/right/bottom |
|---|---|---|
| 单图（半栏） | `0 0 520 300` | 56 / 32 / 24 / 44 |
| 通栏图 | `0 0 1040 360` | 64 / 36 / 32 / 48 |

绘图区：

```text
plotW = W - left - right
plotH = H - top - bottom
```

数值 → 像素（柱/折线通用）：

```text
y(v) = top + plotH - (v / maxV) * plotH
```

分类 → 像素（n 个类别）：

```text
band   = plotW / n
center(i) = left + band * (i + 0.5)
```

字号：图题 13px、轴标签 11px、数据标签 10–11px、来源 10px。字体 `"Microsoft YaHei", sans-serif`。

## 三、五类图的标准画法

### 1. 纵向柱状图（对比）

- 柱宽 `barW = band * 0.56`，`x(i) = center(i) - barW/2`，高度 `top + plotH - y(v)`。
- 数值标签放柱顶上方 4px，`text-anchor="middle"`；数值为 0 时不出标签。
- 网格线 4–5 条：`y = top + plotH * k/4`，`stroke="#DDE0E4" stroke-width="1"`。
- 强调项用 `#c0392b`，其余 `#1A2B4A` / `#3d5a80`。

```xml
<svg viewBox="0 0 520 300" role="img" aria-label="图表标题" style="width:100%;height:auto">
  <text x="56" y="20" font-size="13" font-weight="600" fill="#1A2B4A">图1 · 图表标题</text>
  <line x1="56" y1="256" x2="496" y2="256" stroke="#BABFC9" stroke-width="1"/>
  <rect x="80" y="96" width="48" height="160" fill="#1A2B4A"/>
  <text x="104" y="90" font-size="11" text-anchor="middle" fill="#1A2B4A">50</text>
  <text x="104" y="272" font-size="11" text-anchor="middle" fill="#758092">类别A</text>
</svg>
```

### 2. 横向条形图（排名 / 长标签）

- 行高 `rowH = plotH / n`，条高 `rowH * 0.56`，条长 `v / maxV * plotW`。
- 类别名放左侧、右对齐（`text-anchor="end"`），数值放条右端外 6px。
- 类别名超过 6 字优先改横向条形，避免斜排文字。

### 3. 折线图（趋势）

- `x(i) = left + (plotW / (n-1)) * i`（n>1）；n=1 时放中间。
- 连线 `<path d="M x0 y0 L x1 y1 ..." stroke="#c0392b" stroke-width="3" fill="none">`。
- 数据点用 `<circle r="3">`；只标首、末、峰、谷四个值，避免标签拥挤。
- 缺失年份不要补 0：用断线或省略该点，并在脚注写明缺测。

### 4. 环形图（占比）

用描边圆弧法，最稳且不用算扇形：

```text
r = 88; C = 2 * Math.PI * r   // 552.9
segmentLen = C * value / total
stroke-dasharray="segmentLen (C - segmentLen)"
transform="rotate(-90 + 360 * startRatio, cx, cy)"
```

```xml
<circle cx="260" cy="160" r="88" fill="none" stroke="#1A2B4A" stroke-width="26"
        stroke-dasharray="276.5 276.5" transform="rotate(-90 260 160)"/>
```

- 扇区不超过 5 个，多于 5 个合并为"其他"。
- 中心放合计口径（如"合计 100%"），环外放百分比标签，不放在环内。
- 相邻扇区颜色差异不足时，加 2px 白色描边分隔。

### 5. 区间条（价格 / 上下限对比）

- 用一条粗横条表示 `[low, high]`：`x = x(low)`，`width = x(high) - x(low)`。
- 中位数或均值用一条竖线或圆点标在条上，旁边标数值。
- 低价端与高价端各标数值，单位写在轴或图题里。

### 6. 堆叠条形（结构构成）

- 各段宽度按占比累计：`w_k = plotW * v_k / total`，起始 x 为前面各段之和。
- 段内文字若放不下（段宽 < 40px），改为段外引线标注或只在图例/表格中给出数值。
- 百分比堆叠必须标出总和 100% 的口径。

## 四、可读性硬约束

- 单张图数据序列不超过 4 条；超过则拆图或改表格。
- 单张图类别不超过 10 个；超过则取 TOP N + "其他"。
- 标签放不下时的处理优先级：减少标签数量 → 改横向条形 → 数值外置到右侧 → 拆图。**不得把字号压到 9px 以下，不得旋转文字。**
- 不得只靠颜色区分序列：必须同时有直接数值标签、线型差异（实线/虚线）或形状差异。
- 文字与背景对比度足够：深色底不用小字，浅灰文字只用于脚注。
- 所有元素必须落在 `viewBox` 内，右侧和底部各留至少 24px 安全边距。

## 五、验收

1. 用 XML 解析器校验一遍 SVG 片段闭合正确（可把 `<svg>` 单独抽出来解析）。
2. 用 headless Chromium 截图，逐张确认：图形可见、坐标轴与刻度齐全、文字无重叠无截断、无空白图框。
3. 对照数据复核：抽查 2–3 个数值标签与源数据一致，比例尺未被误归一化。
4. 确认全文没有 `echarts`、`cdn.`、`unpkg`、`jsdelivr` 等字样。
