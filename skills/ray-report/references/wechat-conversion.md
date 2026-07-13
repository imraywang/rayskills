# WeChat 公众号 Markdown Conversion

Turning the structured HTML version into a long-sentence narrative markdown that pastes cleanly into the WeChat 公众号 editor.

## Why this is a rewrite, not a conversion

WeChat readers don't read like web readers. The platform discourages:
- Bullet lists (hard to scan on mobile, looks "computer-generated")
- Tables (render badly, often cut off)
- Interactive components (don't exist in WeChat)
- Charts (only static images, not Chart.js)

What works on WeChat:
- Long flowing paragraphs (4-7 sentences each)
- Conversational voice ("我自己的判断是...", "你可能会想...")
- In-line emphasis with `**bold**`
- Occasional pull quote using `> ` blockquote
- Section breaks with horizontal rule `---`

So the conversion is a **rewrite**: keep all data and arguments, but reshape into prose.

## Conversion rules

### Bullet lists → flowing sentences

**Before (HTML/markdown table-rich version):**
```markdown
- 1900 年：美国 41% 劳动力在农业
- 1950 年：约 12%
- 2000 年：约 1.9%
```

**After (WeChat):**
```markdown
1900 年，美国 41% 的劳动力在农业；到 1950 年降到 12%；到 2000 年只剩 1.9%。
```

Use semicolons or sentence chaining. Keep the data, lose the bullets.

### Tables → comparison sentences

**Before:**
| 公司 | 时间 | 规模 |
|------|------|------|
| Microsoft | 2025-05+07 | 1.5 万人 |
| Meta | 2026-04 | 8000 人 |

**After:**
```markdown
具体看数据：Microsoft 在 2025 年 5 月和 7 月分两批共裁了 1.5 万人；Meta 在 2026 年 4 月宣布裁员 8000 人；Klarna 用 AI 替代了 700 个客服岗位……这些数字加起来不亚于硅谷的裁员潮。
```

Tables become narrative paragraphs. Group related rows into one sentence; use semicolons between rows.

### Headings → keep H1/H2/H3, drop章节编号

**Before:**
```markdown
## 01 · 速度
### 这次有什么不同
```

**After:**
```markdown
## 先把"快"这件事钉死

### 这次有什么不同
```

Drop the editorial chapter numbering — WeChat readers don't expect it. Keep markdown H1/H2/H3.

### Pull quote → blockquote

**Before:**
```html
<div class="pullquote">
  "未来一到五年内..."
  <span class="author">—— Dario Amodei</span>
</div>
```

**After (markdown):**
```markdown
> "未来一到五年内，AI 可能消灭初级白领岗位的一半，失业率可能上升到 10% 到 20%。"
>
> —— Dario Amodei，Anthropic CEO
```

WeChat renders `>` as a soft pull quote. Keep it.

### Charts → describe in words

**Before:** A Chart.js bar chart of "主流机构对 AI 影响岗位规模的估计"

**After (in the prose):**
```markdown
主流机构 2023–2025 年都做过 AI 对就业影响的预测。Goldman Sachs 2023 年估算 AI 可能自动化等同于 3 亿全职岗位的工作量；IMF 2024 年 1 月的报告说全球 40% 岗位有 AI 暴露，发达经济体高达 60%；麦肯锡的预测是到 2030 年全球可能有 7500 万到 3.75 亿工人被替代——占全球劳动力的 14% 左右。世界经济论坛 2025 年的《未来就业报告》给的数字相对乐观：到 2030 年 9200 万岗位被替代，1.7 亿新岗位涌现，净增 7800 万。
```

The numbers are still there — just embedded in sentences. Reader gets the same information.

### Interactive Tab section → paragraph-by-paragraph cases

**Before:** Tab with 6 company panels

**After:** Each case becomes a short paragraph or sub-section:

```markdown
**微软**的做法最干脆——2025 年 5 月和 7 月先后裁掉 1.5 万人，同时在 51 年公司历史上第一次推出员工买断计划。买断的潜台词很清楚：公司不想再无限期养着低杠杆员工。

**Meta** 2026 年 4 月底直接把动机摆上桌：裁掉 8,000 人 + 永久冻结 6,000 个开放岗位，理由就是"AI 优先"。股价的反应是上涨。

**Klarna** 的故事最有戏剧性——先用 AI 替代了 700 个客服岗位，全公司员工从 5,527 降到 3,422 减了 40%；然后在 2025 年 5 月公开承认 AI 客服质量太差，开始重新招人。但要明白多数公司不会反转，因为成本差太大。
```

Each tab becomes its own paragraph with **公司名加粗** as soft headers.

### Quiz section → drop the interactive part, keep the framework

**Before:** Interactive 4-option quiz with conditional results

**After:** Present the question + describe the framework:

```markdown
先回答一个问题。这个测试很简单：**你能否用一段 prompt 描述你今天 80% 的工作？**

能描述清楚的部分，大概率 18 到 36 个月内会被替代。判断公式不复杂——重复性、可结构化、可远程化的工作占比越高，越危险；判断、关系、责任、品味、现场感占比越高，越安全。
```

Drop the conditional outcomes; turn it into a single insight.

### Accordion / details → narrative paragraphs

Each accordion item becomes a paragraph that opens with the rule, then the explanation:

```markdown
**不要赌"我这个行业不会被替代"**——IMF 数据明明白白，发达经济体 60% 岗位都有 AI 暴露。所有人都觉得"我的行业有特殊性"，但所有人都这么想。更可怕的是这种心态会让你错过最关键的 12-24 个月窗口期。

**不要纠结"AI 写得没有人好"**——它只需要在 80% 场景下做到 80% 的质量，老板就买单了。Klarna 替代 700 个客服就是证明——虽然后来反转，但多数公司不会反转，因为成本差太大。
```

### Ornament `· · ·` → `---` horizontal rule

Replace with markdown horizontal rules between major sections.

## Voice adjustments

WeChat audience expects:
- More first-person ("我自己的判断是...", "我觉得...")
- More casual transitions ("聊到这里...", "说回正题...", "写到这里...")
- Reader address ("你可能会想...", "看看自己的岗位")
- Slightly longer sentences than web (Chinese readers tolerate longer prose on WeChat than English readers on web)

Avoid:
- Bullet-pointy structure even within sentences ("第一... 第二... 第三...")
- Subhead overload (H3 every other paragraph)
- Aggressive bolding (3-5 bolded phrases per long paragraph max)

## Output format

Standard markdown, but with WeChat-friendly rendering in mind:

```markdown
# 标题（建议带钩子）

引言段落，最好是带 lead 钩子的具体场景或数据点开头。

第二段铺垫背景。

> 引用段落（如果有 pivotal quote）
>
> —— 出处

第三段过渡到主体。

---

## 第一节标题

正文段落...

正文段落...

---

## 第二节标题

正文段落...

（结尾段落 = 收束观察 / 给读者的最后一击）
```

## Naming convention

Save as `~/<topic-slug>-公众号版.md`.

## Sample reference

A useful conversion pair is the same article in both forms:
- Source: `~/<topic-slug>.html` (HTML interactive with all components)
- Target: `~/<topic-slug>-公众号版.md` (long-sentence narrative version)

If you have such a pair on hand, read both side-by-side to internalize the conversion patterns.
