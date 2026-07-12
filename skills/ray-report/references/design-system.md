# Design System

Reference for the visual language. The whole skill exists to enforce this — if you find yourself reaching for a saturated color or a drop shadow, stop and re-read this file.

## Why these choices

Editorial design (NYT, New Yorker, Bloomberg Businessweek) signals "this is something thought through, by humans, worth your reading time." SaaS design signals "this is software, click through it." For long-form analysis, we want the first signal.

Concrete differences:
- Serif headings vs. sans-everywhere → human craft vs. system UI
- Warm earthy palette vs. saturated blue/orange → considered vs. attention-grabbing
- Paper grain vs. pure flat → tactile vs. clinical
- Flat 1px borders vs. drop shadows → editorial vs. dashboard
- Tabular numerals vs. proportional → "I checked these numbers" vs. "I made them up"

## Color palette

```css
:root {
  --ink: #1a1a1a;          /* primary text */
  --ink-soft: #262421;     /* body paragraphs (slightly warmer than ink) */
  --paper: #fafaf7;        /* page background */
  --cream: #f4ede0;        /* highlight blocks (quiz, year-box highlight) */
  --cream-soft: #f7f3ea;   /* timeline-lesson, table-header background */
  --line: #e7e5e0;         /* borders, dividers */
  --line-strong: #d4cfc4;  /* strong dividers (ornament lines, byline) */
  --mute: #6b6760;         /* secondary text, captions */
  --accent: #b8553a;       /* rust — links, kickers, accent borders */
  --accent-soft: #f0d9cf;  /* rarely used; soft accent backgrounds */
  --positive: #2d6a4f;     /* "safe" callouts */
  --negative: #9c2a25;     /* "danger" callouts */
}
```

**Never use**:
- Pure white `#fff` for body background (too clinical) — use `--paper`
- Pure black `#000` for text — use `--ink`
- Saturated brand colors (`#ff5500`, `#0066ff`, `#00cc66`) — too SaaS
- Anything with > 80% saturation

## Typography

### Font stacks

```css
/* Headings — serif, this is the #1 magazine signal */
font-family: 'Noto Serif SC', Georgia, 'Songti SC', 'STSong', serif;

/* Body */
font-family: 'Inter', 'Noto Sans SC', 'PingFang SC', system-ui, -apple-system, sans-serif;

/* Small caps, kickers, numbers, dates, code */
font-family: 'JetBrains Mono', 'SF Mono', 'Menlo', monospace;
```

Load via Google Fonts in `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Serif+SC:wght@400;500;700;900&family=Noto+Sans+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Size scale

| Element | Size | Weight | Notes |
|---------|------|--------|-------|
| Hero H1 | `clamp(2.4rem, 6vw, 4rem)` | 900 | letter-spacing -0.03em |
| Section H2 | `clamp(1.8rem, 4.2vw, 2.4rem)` | 700 | letter-spacing -0.025em |
| H3 | `1.3rem` | 700 | line-height 1.4 |
| H4 (cards) | `1.2rem` | 700 | |
| Body p | `1.0625rem` | 400 | line-height 1.85 |
| Lead caption | `1.2rem` | 400 (mute) | the subtitle under H1 |
| Stat card number | `3.2rem` | 900 | serif, tabular nums |
| Quiz question | `1.05rem` | 400 | |
| Kicker / h2-num | `0.7rem` | 500 | mono, uppercase, letter-spacing 0.3em |
| Byline | `0.78rem` | 400 | letter-spacing 0.05em |

### Tabular numerals

**Every number in the document should use tabular nums**:

```css
body { font-feature-settings: "palt", "tnum"; }
.num { font-feature-settings: 'tnum' 1; font-variant-numeric: tabular-nums; }
```

Add class `num` to any element whose content is numerical or contains many numbers (stat cards, dates, year boxes, table cells with numbers). This makes columns align and gives data "credibility weight."

### Letter spacing

- Headings: tighten (`-0.025em` to `-0.035em`) — serif looks better tight
- Body: default
- Kickers / labels: spread (`0.25em` to `0.3em`) + uppercase — editorial signal
- Byline: slight spread (`0.05em`)

## Layout

### Containers

```css
.container-narrow {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 24px;
}
.container-wide {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px;
}
```

- **Narrow (720px)** — text content, paragraphs, H2 with kickers. Reading width.
- **Wide (1080px)** — charts, stat-card rows, tab sections, layer grids. Allows wider visual elements.

For sections that have both: wrap text portions in `container-narrow` inside a `container-wide` section. Like:

```html
<section class="container-wide">
  <div class="container-narrow" style="padding:0;">
    <h2><span class="h2-num">01 · X</span>Title</h2>
    <p>Body text...</p>
  </div>
  <div class="stat-row"><!-- wide --></div>
  <div class="container-narrow" style="padding:0;">
    <p>More body text...</p>
  </div>
</section>
```

### Spacing rhythm

- Section H2: `margin: 5rem 0 1.8rem`
- Paragraph: `margin: 1.1em 0`
- Card padding: `2rem 1.8rem` (or `1.5rem 1.5rem` for compact)
- Ornament between sections: `margin: 5rem auto`

### Line height

- Body: `1.85` (generous, for slow reading)
- Headings: `1.2` (tight, for impact)
- Captions: `1.6`

## Texture: paper grain overlay

Critical for "not flat AI slop" feel. Fixed overlay covers entire page:

```css
body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: 0.5;
  background-image:
    radial-gradient(circle at 12% 18%, rgba(106,92,56,0.06), transparent 45%),
    radial-gradient(circle at 88% 72%, rgba(106,92,56,0.05), transparent 50%),
    radial-gradient(circle at 45% 90%, rgba(184,85,58,0.025), transparent 40%);
}
```

Then containers need `position: relative; z-index: 1` to sit above the overlay.

## Visual flourishes

### Drop cap on first paragraph

The first content paragraph after the masthead gets `<p class="lead">`:

```css
.lead::first-letter {
  font-family: 'Noto Serif SC', Georgia, serif;
  font-size: 4em;
  font-weight: 900;
  float: left;
  line-height: 0.85;
  margin: 0.08em 0.14em 0 0;
  color: var(--accent);
}
```

One per article. Don't put drop cap on later paragraphs.

### Pull quote — italic serif, no color box

```css
.pullquote {
  margin: 3rem 0;
  padding: 1.5rem 0 1.5rem 2rem;
  border-left: 3px solid var(--accent);
  font-family: 'Noto Serif SC', serif;
  font-style: italic;
  font-size: 1.35rem;
  line-height: 1.55;
  color: var(--ink);
}
.pullquote .author {
  display: block;
  margin-top: 1.2rem;
  font-family: 'Inter', sans-serif;
  font-style: normal;
  font-size: 0.85rem;
  color: var(--mute);
}
```

Use once or twice per article. Never use a colored box. Just italic serif with a single rust border-left.

### Ornament divider

Between every major section:

```html
<div class="ornament"><span>· · ·</span></div>
```

```css
.ornament {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin: 5rem auto;
  max-width: 720px;
  padding: 0 24px;
}
.ornament::before, .ornament::after {
  content: "";
  flex: 1;
  max-width: 80px;
  height: 1px;
  background: var(--line-strong);
}
.ornament span {
  font-size: 0.85rem;
  letter-spacing: 0.4em;
  color: var(--mute);
}
```

This is non-optional. Use between every section transition. It creates rhythm and "this is a real thing" feeling.

### Section numbering (h2-num)

Every H2 has a small monospace kicker above it:

```html
<h2 id="speed"><span class="h2-num">01 · 速度</span>先把"快"这件事钉死</h2>
```

The numbering is 01, 02, 03... (zero-padded). The label after `·` is a 2-character category tag (速度 / 历史 / 范围 / 案例 / 中国 / 自测 / 应对 / 收尾 — adapt to article).

## Component visual specs

(See `components.md` for full HTML/CSS snippets.)

- **Stat cards**: white bg, 1px grid lines between cards (`gap: 1px; background: var(--line)`), big serif rust number, mono uppercase label, body note
- **Timeline**: 1px vertical line on left, small rust dot connectors, mono date in rust, serif title, body, cream-tinted italic "lesson" callout
- **Tables**: cream-soft header bg, mono uppercase column labels, 2px ink border under header, 1px line between rows
- **Tabs**: 1px line under tab bar, rust border-bottom on active tab, white panel below
- **Quiz**: cream bg, corner-floating mono label "自测 · QUIZ", white option buttons with rust hover
- **Accordion (details)**: 1px line dividers, rust `+` icon (rotates to `−` when open)
- **Layer cards**: white bg, mono uppercase "layer-num" kicker in rust, serif h4
- **Year boxes** (closing): top + bottom 1px line, big serif rust year, mono small description
- **Danger / Safe boxes**: 3px left border (rust-red / muted-green), 1px borders on other sides

## Mobile responsive

```css
@media (max-width: 768px) {
  body { font-size: 16px; }
  .masthead { padding: 4rem 0 2.5rem; }
  .lead::first-letter { font-size: 3.5em; }
  .stat-card .number { font-size: 2.6rem; }
  h2 { margin-top: 4rem; }
  .ornament { margin: 3.5rem auto; }
  .pullquote { font-size: 1.15rem; padding: 1rem 0 1rem 1.5rem; }
}
```

## Anti-slop final checklist

Before declaring HTML done, scan for:

- [ ] Are headings serif? (if no, fix immediately)
- [ ] Is accent rust `#b8553a`, not orange `#c8501a`? (no neon)
- [ ] Is the masthead background `#fafaf7`, not dark? (no dark hero)
- [ ] Is there a grain overlay? (look at `body::before`)
- [ ] Does the first paragraph have `class="lead"`? (drop cap)
- [ ] Are there ornament dividers between every major section? (`· · ·`)
- [ ] Does every H2 have a `<span class="h2-num">` kicker?
- [ ] Are stat card numbers serif + tabular nums?
- [ ] Are tables using cream-soft header bg + mono uppercase labels?
- [ ] Are tab buttons using underline-active style, not rounded buttons?
- [ ] Are pull quotes italic serif (not colored boxes)?
- [ ] No emojis used as icons anywhere?
- [ ] No drop shadows on cards?
- [ ] No saturated colors anywhere?

If any check fails, fix before showing to user.
