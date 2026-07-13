---
name: ray-report
description: 生成长文 / 深度报告 / 数据型内容,三格式协同产出——交互式 HTML(magazine 杂志排版,含 Tab/Quiz/Chart.js/Timeline 组件)、A4 PDF(headless Chrome 渲染)、公众号 markdown(长句叙事)。采用精修的编辑设计语言(衬线中文标题、锈红点缀、纸张颗粒、drop cap、装饰分隔、等宽数字),读起来像真正的杂志文章而非 SaaS dashboard。当用户要做长篇分析、白皮书、深度报告、多段数据型长文,或说「做一个报告」「深度分析」「长文章」「报告版」「PDF 报告」「html version」「pdf report」,或丢来一份提纲期待成品时使用;格式没点名也默认走 HTML,再 offer PDF+公众号。不用于短文、dashboard、UI 组件、或公众号自动发布流程(那用 wewrite)。触发 /ray-report
---

# Editorial Report Builder

Generate a long-form editorial article in three coordinated formats. The three formats share the same underlying content — they just present it differently.

| Format | Use case | How |
|--------|----------|-----|
| **HTML (interactive)** | Web reading, sharing, archiving | Single self-contained file with Tab / Quiz / Chart.js / Timeline / Accordion components |
| **PDF (report)** | Print, distribution, formal/PDF reading | Headless Chrome render of HTML with `@media print` expanding interactive components |
| **WeChat markdown** | 公众号 paste, long-form newsletter | Flowing long-sentence narrative, no tables/lists, data embedded inline |

Build the **content as HTML first**, then derive PDF and 公众号 Markdown from it.

## Why this skill exists

Generic AI-generated HTML defaults to SaaS dashboard aesthetics — dark hero with gradients, saturated neon accents, rounded card shadows, big CTA buttons. That look is wrong for long-form analysis.

This skill enforces **editorial design language** — the look of a New Yorker article or NYT long-read. The opposite of slop. The reference repo is [nexu-io/html-anything](https://github.com/nexu-io/html-anything) (especially `article-magazine`, `data-report`, `doc-kami-parchment` templates).

## Workflow

### 1. Understand the content

Before writing anything, get clear on:
- **Topic & angle** — what's the thesis? Is this analysis, opinion, deep dive, or report?
- **Structure** — how many sections? What's the narrative arc?
- **Evidence** — what data, cases, quotes, charts are needed?
- **Audience** — general reader, sophisticated reader, or domain expert?
- **Length target** — long-read (3000-5000 字) or short essay (1500-2500 字)?

If the user gave only a topic, ask for an outline or do research first (WebSearch is OK). Don't start writing without understanding what's being said.

### 2. Choose components based on content

The interactive HTML has a fixed component library. Pick what fits the content — don't force components that don't earn their place.

See `references/components.md` for full snippets. Decision guide:

- **Stat card row** (3 cards) — when you have 3 comparable numbers that anchor the article's thesis (e.g., "100 年 / 12 年 / 12 个月"). Put near the top.
- **Timeline** — historical sequence of events, each with date + title + body + lesson. Best for 3-6 items.
- **Pull quote** — one pivotal quote per article, max two. Italic serif, no colored box.
- **Tab section** — 4-8 parallel cases (companies, scenarios, options). Each gets its own panel.
- **Quiz** — interactive self-test with 4 outcomes. Use once per article max.
- **Accordion** — list of warnings, principles, or expandable details. 3-6 items.
- **Chart.js bar/line** — quantitative data that benefits from visual comparison. Don't overdo — 1-2 charts is plenty.
- **Layer grid** (3-5 cards) — concepts/principles in parallel structure.
- **Danger / Safe box** — short callouts for "do this / don't do this" within a section.
- **Ornament divider** (`· · ·`) — between every major section. Not optional.

### 3. Build the HTML

Start from `assets/skeleton.html` — it has all the CSS, fonts, scripts loaded. Copy it to the target output path, then fill in content.

```
1. Update masthead: kicker, h1, sub, byline
2. Drop in opening paragraph with class="lead" (gets drop cap)
3. Add pullquote near opening if there's a key quote
4. Each section: <div class="ornament"><span>· · ·</span></div> + section + content
5. Each h2 needs: <span class="h2-num">01 · 标签</span>section title
6. Use snippets from references/components.md for components
7. End with closing section + epilogue + article footer
```

Save to `~/<topic-slug>.html` unless the user specified a different path.

### 4. Apply design system rigorously

The design language is **not negotiable** — the whole skill exists to enforce it. See `references/design-system.md` for tokens.

Key rules:
- **Headings** in `'Noto Serif SC', Georgia, serif` — this is the #1 magazine signal
- **Body** in `'Inter', 'Noto Sans SC', sans-serif`
- **Small caps/numbers** in `'JetBrains Mono', monospace`
- **Colors**: paper `#fafaf7`, ink `#1a1a1a`, accent `#b8553a` (rust), cream `#f4ede0`
- **Containers**: narrow 720px (text), wide 1080px (charts/tabs/grids)
- **Numbers**: enable `font-feature-settings: 'tnum'` everywhere

Anti-slop checklist (read `references/design-system.md` for full list):

| Never | Always |
|-------|--------|
| Dark hero with gradient | Cream `#fafaf7` masthead |
| Saturated neon (`#c8501a`) | Muted rust (`#b8553a`) |
| Rounded cards + drop shadows | Flat cards, 1px borders |
| Big colored CTA buttons | None — this is a report |
| Generic emoji icons | None |
| Sans-serif everywhere | Serif headings, sans body |
| Pure white background | Cream `#fafaf7` + grain overlay |
| Block-color pull quotes | Italic serif, no fill |

### 5. Ask about PDF + 公众号 markdown

After saving HTML, ask:
> "HTML 版生成好了，保存到 `~/<path>.html`。要不要也生成 PDF 报告版和公众号长句版？"

If PDF: run `scripts/render-pdf.sh <html-path>` — produces `<html-path>.pdf` next to it.

If 公众号: follow `references/wechat-conversion.md` rules to rewrite as flowing narrative, save to `~/<topic-slug>-公众号版.md`.

## Format-specific notes

### HTML mode (default)

- Self-contained single file (all CSS inline, scripts from CDN)
- Uses Chart.js, AOS, Google Fonts (Noto Serif SC, Inter, Noto Sans SC, JetBrains Mono)
- Tab buttons + Quiz options work via vanilla JS at the end of file
- The skeleton already has the JS — just add markup

### PDF mode

The skeleton already includes `@media print` CSS that:
- Makes masthead a full-page cover
- Hides tab buttons, shows all tab panels with case labels (案例 1, 案例 2 ...)
- Hides quiz options, shows all results as "对照下面四种情境" scenarios
- Forces all accordion `<details>` open
- Sets `page-break-inside: avoid` on cards/charts/tables/timeline items
- Sets `print-color-adjust: exact` to preserve colors
- Disables AOS (`[data-aos] { opacity: 1 }`)

Generate:
```bash
bash ~/.claude/skills/editorial-report/scripts/render-pdf.sh input.html [output.pdf]
```

The script uses headless Chrome with `--virtual-time-budget=12000` to ensure Chart.js renders before printing.

### WeChat markdown mode

Output is a `.md` file the user pastes into the WeChat editor. The conversion is **not** mechanical — it's a rewrite. See `references/wechat-conversion.md`.

Key rules:
- No bullet lists, no tables — fold everything into flowing sentences
- Long paragraphs (4-7 sentences each)
- Keep `**bold**` for in-line emphasis
- Drop charts (or describe their content inline)
- Drop interactive components (no quiz, tabs become paragraph-by-paragraph case discussions)
- Replace `· · ·` ornament with a blank line + `---`
- First-person voice OK ("我自己的判断是...")

## Examples of when to trigger

**Trigger**:
- "帮我写一篇关于 X 的深度分析"
- "这个内容做成 HTML 报告"
- "写一篇长文章 + 数据图表"
- "做成 PDF 报告"
- "magazine 风格的 HTML"
- "做个白皮书 / 行业分析"
- "I want a long-form article about X with charts"
- The user shares an outline and wants polished output

**Don't trigger**:
- "帮我写公众号文章" → use `wewrite`
- "做个 SaaS 落地页" → use `frontend-design`
- "写一段 tweet thread" → no skill needed
- "改一下这个按钮样式" → no skill needed
- "做个 dashboard" → use `frontend-design`
- Anything under ~800 字 → too short for this format

## Reference files

- `references/design-system.md` — Colors, fonts, spacing, anti-slop rules in detail
- `references/components.md` — Copy-pasteable HTML snippets for each component
- `references/print-css.md` — `@media print` rules + how interactive→static transformation works
- `references/wechat-conversion.md` — Rules + before/after examples for 公众号 conversion

## Assets

- `assets/skeleton.html` — Complete starter HTML with all CSS, fonts, scripts. **Start here** — copy this file and fill in content.

## Scripts

- `scripts/render-pdf.sh` — Generate PDF from HTML via headless Chrome

## Canonical example

The reference implementation built during this skill's creation:
- `~/AI裁员浪潮-数据加强版.html` — HTML interactive version
- `~/AI裁员浪潮-数据加强版.pdf` — PDF report version
- `~/AI裁员浪潮-公众号版.md` — WeChat markdown version

Read these for "how the final output looks" reference. Don't copy content — just structure and feel.
