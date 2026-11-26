# 分析报告结构模板

## 标准章节结构（演绎式逻辑）

```
1. 开头 callout（核心结论）
   - 一句话说明本文回答的核心问题
   - 3-5个要点：核心发现、结论、行动建议
   - 不超过300字

2. 模块化目录（卡片网格，必做）
   - 位置：开头 callout 之后、正文第一章节之前
   - 4-8 个卡片，等宽等高，2-4 列；编号 M1…M6 + 章节标题 + 该节解决什么问题 + 可视化形式
   - 卡片为 <a href="#mN"> 锚点，对应 <h2 id="mN">，纯静态、无 JS
   - 卡片标题取自 h2 主干（冒号前），与正文一一对应；只写问题，不复述数据

3. 一图看懂（h1，无编号）
   - 仅用 HTML5 block 呈现全文摘要
   - 必须直接回答核心问题
   - 覆盖核心判断、2-3个最重要发现、主要建议
   - 后续一级标题从"1."开始自动编号

4. 范围与口径（h1）
   - 分析对象、时间范围、数据来源、关键定义
   - 如有分类框架（如向往型/真野型），在此定义

5. 现状与趋势（h1）
   - 市场规模、增长趋势、结构变化
   - 必须有 HTML5 趋势图 + 数据表格
   - 每段先给结论，再给数据

6. 核心分析章节（h1，按决策需要设2-4节）
   - 每节聚焦一个分判断
   - 节内结构：结论 → 证据（数据/案例/对比）→ 含义
   - 每节至少一个可视化元素（表格或HTML5）
   - 超过3个二级标题时，节首加HTML5内容地图

7. 排除法/反证（可选h1）
   - 列出替代解释，逐一排除
   - 用表格呈现"验证维度-证据-指向"

8. 空间估算与核心判断（h1）
   - 测算口径表 + HTML5对比图
   - 结尾用 callout 给出核心判断

9. 行动建议/启示（h1）
   - 3-5条可执行建议
   - 每条：做什么 + 为什么 + 怎么做

10. 参考来源（h1）
   - 包含两个子节：
     a. 数据核实说明：列出实际使用的核实平台、数据截止日期、经用户确认的事项（无则写"无"）
     b. 引用来源：按正文引用顺序编号，格式：[n] 发布方：《标题》，平台名，YYYY-MM-DD，完整链接
   - 每条来源标注权威等级（🔴官方 / 🟠行业权威 / 🟡媒体二手）
   - 正文引用编号与本列表一一对应，禁止出现无编号引用或编号无对应来源
```

## 证据分级标注

在正文中对关键事实标注状态：

| 标记 | 含义 | 用法 |
|---|---|---|
| 已证实 | 有可追溯原始来源 | 直接陈述，附引用编号 |
| 推算 | 基于公开数据的合理推算 | 标注"预估/推算"，说明口径 |
| 待验证 | 缺少数据支撑的假设 | 标注"待验证"，不参与结论 |
| 产品建议 | 分析得出的行动建议 | 与事实分开表述 |

## 篇幅控制

| 报告类型 | 正文字数 | 可视化元素 |
|---|---|---|
| 快速分析/简报 | 1,500–2,000字 | 2-3个 |
| 标准分析报告 | 2,000–3,500字 | 4-6个 |
| 深度调研 | 3,500–5,000字 | 6-8个 |

字数口径：正文含摘要，不含可视化中的文字、封面、尾注。

## 模块化目录组件（HTML 规范）

位置：核心结论 callout 之后、正文第一章之前。纯 CSS 布局，无脚本。

### 结构

```html
<section class="outline">
  <div class="outline-head">报告结构 · 6 个模块<span>点击标题可跳转</span></div>
  <div class="outline-grid">
    <a class="module" href="#m1">
      <span class="no">M1</span>
      <div class="mt">双减后的格局</div>
      <div class="mq">学科类还剩多少？素质类顶上了吗？</div>
      <div class="mv">折线图 + 数据表</div>
    </a>
    <!-- M2 … Mn -->
  </div>
</section>
```

对应正文：`<h2 id="m1">一、双减后的格局：学科类腰斩，素质类成主力</h2>`

### CSS 基线

```css
.outline { margin: 0 0 26px; }
.outline-head { font-size: 12.5px; color: #758092; letter-spacing: .5px;
  margin-bottom: 10px; display:flex; justify-content:space-between; }
.outline-head span { color: #9aa1ad; }
.outline-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.module { position: relative; display:block; background:#fff; border:1px solid #DDE0E4;
  border-left:3px solid #1A2B4A; border-radius:6px; padding:14px 14px 12px 16px;
  text-decoration:none; color:inherit; }
.module .no { position:absolute; right:12px; top:10px; font-size:15px; font-weight:700;
  color:#DDE0E4; letter-spacing:.5px; }
.module .mt { font-size:14px; font-weight:700; color:#1A2B4A; margin-bottom:6px; padding-right:34px; }
.module .mq { font-size:12px; color:#5a6472; line-height:1.55; min-height:37px; }
.module .mv { font-size:11px; color:#758092; margin-top:8px; padding-top:7px;
  border-top:1px dashed #E4E7EC; }
@media (max-width:760px){ .outline-grid{ grid-template-columns:1fr; } }
@media print { .module{ break-inside:avoid; } }
```

### 文案规则

- 卡片数 4–8 个；模块数与正文一级标题数一致，一一对应。
- `.mq` 写"这节解决什么问题"，控制在 18–30 字；不写数字结论，不复述 callout。
- `.mv` 只写可视化形式与数量，如"折线图 + 2 列表格"，让读者知道每节有图可看。
- 卡片标题取自 `h2` 主干（冒号前的短语），不得自造新标题；正文调整章节后同步改目录，交付前核对。
