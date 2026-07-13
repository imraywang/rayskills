# Components Reference

Quick reference for each component. The full CSS for these lives in `assets/skeleton.html` — copy that file as your starting point. This document explains **when to use** each component and shows **minimum HTML snippets**.

## Decision guide: which component for which content?

| Content type | Component | Notes |
|--------------|-----------|-------|
| 3 comparable numbers as a thesis anchor | `.stat-row` | Use near top, after opening paragraphs |
| Historical sequence of events | `.timeline` | 3-6 items; each needs date + title + body |
| Pivotal quote (≤2 per article) | `.pullquote` | Italic serif, no color box |
| 4-8 parallel cases (companies, scenarios) | `.tabs` + `.tab-panel` | Reader picks ~1-2 to read |
| Self-test with 4 outcomes | `.quiz` | One per article max |
| 3-5 parallel concepts/principles | `.layer-grid` | Cards in a row |
| Quantitative data needing visual | `.chart-box` + Chart.js | Bar / line. Max 2 per article |
| Expandable list (warnings, principles) | `<details>` | 3-6 items |
| Tabular comparison (companies, plans) | `<table>` | When list-form doesn't suit |
| In-section "do this / don't do this" | `.safe-box` / `.danger-box` | Short callouts |
| End-of-article time windows / years | `.closing` + `.year-box` | For "1995 / 2007 / 2026" style |
| Mid-paragraph emphasis | `.lead::first-letter` | First content paragraph only |
| Between every major section | `.ornament` | Non-optional |

## Snippets

### Masthead

```html
<header class="masthead">
  <div class="container-narrow">
    <div class="kicker">2026 · AI 与就业 · 深度观察</div>
    <h1>当一份工作消失，<br>意味着什么</h1>
    <p class="sub">AI 裁员浪潮真的来了。但它真正在替代的，不是"工作"，而是某种类型的人。</p>
    <div class="byline">
      <span>2026 年 5 月</span>
      <span class="byline-divider"></span>
      <span>阅读时间约 15 分钟</span>
      <span class="byline-divider"></span>
      <span>作者署名 @handle</span>
    </div>
  </div>
</header>
```

### Lead paragraph (drop cap)

```html
<section class="container-narrow" style="padding-top: 4rem;">
  <p class="lead">First content paragraph after masthead. The first character gets a drop cap.</p>
  <p>Subsequent paragraphs — no special class.</p>
</section>
```

### Pull quote

```html
<div class="pullquote">
  "Pivotal quote text here — italic serif with rust left border."
  <span class="author">—— Speaker name, context</span>
</div>
```

### Ornament divider — between every section

```html
<div class="ornament"><span>· · ·</span></div>
```

### Section header

```html
<h2 id="section-slug">
  <span class="h2-num">01 · 标签</span>
  Section title
</h2>
```

`01` is zero-padded number. `标签` is a 2-character category label. The slug should be a short lowercase English word for `id`.

### Stat card row

```html
<div class="stat-row">
  <div class="stat-card">
    <div class="label">Label / Period</div>
    <div class="number num">100<small>年</small></div>
    <div class="unit">单位说明</div>
    <div class="note">1-2 sentences explaining what this number means.</div>
  </div>
  <!-- Repeat 2-4 cards total -->
</div>
```

Wrap in `<section class="container-wide">` since `.stat-row` is wider than text column.

### Timeline

```html
<div class="timeline">
  <div class="timeline-item">
    <div class="date">YYYY – YYYY　Period name</div>
    <div class="title">Event title — what happened</div>
    <p>Body paragraph.</p>
    <p>Additional paragraph if needed.</p>
    <ul>
      <li>Optional sub-point with <strong>specific data</strong></li>
      <li>Another sub-point</li>
    </ul>
    <div class="lesson">教训：一句话点题。</div>
  </div>
  <!-- Repeat 3-6 items -->
</div>
```

### Chart (bar)

```html
<div class="chart-box">
  <div class="chart-title">Chart title</div>
  <div class="chart-subtitle">Unit / axis subtitle</div>
  <canvas id="my-chart" height="200"></canvas>
  <div class="caption">Caption explaining methodology / source.</div>
</div>
```

In the script tag at the bottom of the file:

```javascript
new Chart(document.getElementById('my-chart').getContext('2d'), {
  type: 'bar',
  data: {
    labels: ['Label 1', 'Label 2', 'Label 3'],
    datasets: [{
      data: [3.75, 3.0, 2.4],
      backgroundColor: ['#b8553a', '#c46d4f', '#d18464'],
      borderColor: '#ffffff',
      borderWidth: 1
    }]
  },
  options: {
    indexAxis: 'y',  // horizontal bars; use 'x' for vertical
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: '#f0ece5' }, ticks: { font: { family: "'JetBrains Mono', monospace" } } },
      y: { grid: { display: false } }
    }
  }
});
```

For line chart (time series): use `type: 'line'`, set `tension: 0.3` for smooth curves, `borderColor: '#b8553a'`, `backgroundColor: 'rgba(184,85,58,0.08)'`, `fill: true`. See skeleton for full example.

### Tabs

```html
<div class="tabs">
  <button class="tab-btn active" data-target="case1">Tab 1</button>
  <button class="tab-btn" data-target="case2">Tab 2</button>
  <button class="tab-btn" data-target="case3">Tab 3</button>
</div>

<div class="tab-panel active" id="case1">
  <h4>Tab 1 title</h4>
  <div class="panel-meta">
    <span>Date</span>
    <span>Key fact 1</span>
    <span>Key fact 2</span>
  </div>
  <p>Tab 1 content.</p>
</div>
<div class="tab-panel" id="case2">
  <h4>Tab 2 title</h4>
  <div class="panel-meta"><span>Date</span></div>
  <p>Tab 2 content.</p>
</div>
```

**Important for PDF**: Add labels in the `@media print` block (inside `<style>`) so each panel gets a "案例 N" prefix when printed:

```css
@media print {
  #case1::before { content: "案例 1"; }
  #case2::before { content: "案例 2"; }
  #case3::before { content: "案例 3"; }
}
```

Replace the example IDs with your actual tab panel IDs.

### Quiz

```html
<div class="quiz">
  <h3>The question</h3>
  <p class="question">Context / explanation before the reader chooses.</p>
  <div class="quiz-options">
    <button class="quiz-option" data-result="result-a">Option A</button>
    <button class="quiz-option" data-result="result-b">Option B</button>
    <button class="quiz-option" data-result="result-c">Option C</button>
    <button class="quiz-option" data-result="result-d">Option D</button>
  </div>
  <div class="quiz-result" id="result-a">
    <div class="level">Outcome A label</div>
    <p>What this answer means.</p>
  </div>
  <!-- ...3 more results -->
</div>
```

### Layer grid

```html
<div class="layer-grid">
  <div class="layer-card">
    <div class="layer-num">概念 1</div>
    <h4>Concept title</h4>
    <p>Body text. <strong>Bold key phrase.</strong></p>
  </div>
  <!-- 3-5 cards total -->
</div>
```

### Accordion (details)

```html
<details>
  <summary>Question / rule headline</summary>
  <div>
    <p>Explanation paragraph.</p>
    <p>Additional context.</p>
  </div>
</details>
<details>
  <summary>Next item</summary>
  <div>
    <p>Content.</p>
  </div>
</details>
```

### Table

```html
<table>
  <thead>
    <tr>
      <th>Column 1</th>
      <th>Column 2</th>
      <th>Column 3</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Row label</strong></td>
      <td>Cell content</td>
      <td>Cell content</td>
    </tr>
  </tbody>
</table>
```

### Danger / Safe callout

```html
<div class="danger-box">
  <h4>Warning headline</h4>
  <p>Content of the warning.</p>
</div>

<div class="safe-box">
  <h4>Reassurance / Action</h4>
  <p>Content.</p>
</div>
```

### Closing (year boxes + final statement)

```html
<div class="closing">
  <div class="label">Category label</div>
  <div class="years">
    <div class="year-box">
      <div class="y num">1995</div>
      <div class="desc">First context<br>second line</div>
    </div>
    <div class="year-box">
      <div class="y num">2007</div>
      <div class="desc">Second context<br>second line</div>
    </div>
    <div class="year-box highlight">
      <div class="y num">2026</div>
      <div class="desc">Final / current context<br>highlighted</div>
    </div>
  </div>
  <p class="final">Final punchy line — the article's thesis in one sentence. <em>Highlighted phrase</em>.</p>
</div>
```

### Epilogue

```html
<div class="epilogue">
  Italic serif coda.<br>
  One or two sentences.<br>
  <strong>Bold key phrase</strong> for emphasis.
</div>
```

### Article footer

```html
<div class="article-footer">END · 2026</div>
```

## Composition guide

A typical article structure:

```
masthead
  ↓
opening section (3-5 paragraphs, lead has drop cap, optional pullquote)
  ↓ ornament
section 1 — stats / charts to anchor thesis
  ↓ ornament
section 2 — historical context (timeline)
  ↓ ornament
section 3 — data / chart
  ↓ ornament
section 4 — cases (tabs)
  ↓ ornament
section 5 — self-test (quiz) [optional]
  ↓ ornament
section 6 — what to do (layer grid + accordion)
  ↓ ornament
closing section — year-box final + epilogue
  ↓
article-footer END · YEAR
```

8 sections is on the long end. 4-6 sections is more typical. The `ornament` divider goes between every major section — including before section 1 and after the final section before the footer.
