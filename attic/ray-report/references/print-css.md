# Print CSS / PDF Mode

The `@media print` block that converts the interactive HTML into a static A4 report.

This is already included in `assets/skeleton.html` — you don't need to add it manually. But understand how it works in case you need to debug or extend.

## What the print mode does

The HTML has interactive components (tabs, quiz, accordion) that don't make sense on paper. Print CSS:

1. **Hides interactive controls** (tab buttons, quiz options)
2. **Expands all hidden content** (shows all tab panels stacked, shows all quiz results)
3. **Labels expanded content** (each tab panel gets "案例 1", "案例 2"... prefix)
4. **Makes the masthead a cover page** (full A4 page with `page-break-after: always`)
5. **Controls page breaks** to keep cards/charts/tables intact
6. **Forces color reproduction** (`print-color-adjust: exact`)
7. **Disables AOS animations** (they don't fire in headless mode)

## Key @page rules

```css
@page {
  size: A4;
  margin: 18mm 16mm 20mm 16mm;
}
@page :first {
  margin: 0;  /* cover page is full-bleed */
}
```

## The transformations

### Cover page

```css
.masthead {
  height: 100vh;
  page-break-after: always;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0;
  margin: 0;
  border-bottom: none;
}
.masthead h1 { font-size: 42pt; }
.masthead .sub { font-size: 14pt; max-width: 75%; }
.masthead::after {
  content: "<series-name> · 2026";
  position: absolute;
  bottom: 20mm;
  left: 24mm;
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--mute);
}
```

The masthead expands to fill page 1, then page-break-after pushes everything else to page 2.

### Tab expansion

```css
.tabs { display: none !important; }
.tab-panel {
  display: block !important;
  margin: 0.8rem 0;
  page-break-inside: avoid;
}

/* Case labels above each panel */
#ms::before { content: "案例 1"; }
#meta::before { content: "案例 2"; }
/* ... etc */
.tab-panel::before {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt;
  color: var(--accent);
  margin-bottom: 0.5rem;
}
```

In interactive mode, only one tab panel is visible. In print, all become stacked sections with "案例 N" labels.

### Quiz expansion

```css
.quiz-option { display: none !important; }      /* hide buttons */
.quiz-result { display: block !important; }     /* show all results */
.quiz-options::after {
  content: "根据你的回答，对照下面四种情境：";
  display: block;
  font-style: italic;
  color: var(--mute);
}
```

The interactive quiz becomes "Here are four scenarios depending on your answer" — readers self-categorize.

### Accordion expansion

```css
details > div { display: block !important; }
details:not([open]) > div { display: block !important; }
summary::after { display: none; }
```

All accordion items rendered open. The `+` icon hidden.

### Page break control

```css
h2 { page-break-after: avoid; page-break-inside: avoid; }
h3 { page-break-after: avoid; }
p { orphans: 3; widows: 3; }

.stat-row, .timeline-item, .tab-panel, .chart-box,
.danger-box, .safe-box, .quiz, .layer-card, .closing,
table, details {
  page-break-inside: avoid;
}
```

Don't break inside any "logical unit." Pages break between sections naturally.

### Color preservation

```css
* {
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
```

By default, Chrome strips backgrounds when printing. This forces all colors to print.

### AOS animation reset

```css
[data-aos] {
  opacity: 1 !important;
  transform: none !important;
}
```

AOS animations require scroll to trigger. In headless Chrome there's no scroll. Without this, AOS-animated elements would print invisible.

### Grain overlay hide

```css
body::before { display: none; }
```

The grain overlay is decorative and can interfere with print rendering. Drop it.

## Font size scaling

Print sizes (10.5pt body) are smaller than screen (17px). The skeleton handles this with `@media print` overrides on each heading/component.

## Generating PDF

Use `scripts/render-pdf.sh`:

```bash
bash <skill-base>/scripts/render-pdf.sh input.html output.pdf
```

Critical flags it uses:
- `--headless=new` — new Chrome headless mode (better rendering)
- `--no-pdf-header-footer` — drop the default URL/date header
- `--virtual-time-budget=12000` — give Chart.js 12 seconds to render before printing
- `--hide-scrollbars` — prevent scrollbar artifacts

## Common issues

**Charts blank in PDF**: Chart.js needs time to render. Make sure `--virtual-time-budget` is at least 10000ms.

**Colors missing**: Check `print-color-adjust: exact` is set on `*`.

**Tabs not expanding**: Verify the @media print CSS is loaded; check that `.tab-panel { display: block !important }` overrides the default `display: none`.

**Page breaks awkward**: Add `page-break-inside: avoid` to the offending element. Don't use `page-break-before: always` on H2 — it creates too many pages.

**Cover page not filling**: `@page :first { margin: 0 }` + `.masthead { height: 100vh }` are both required.
