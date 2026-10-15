# Scene worker brief — 《{{片名}}》

> 模板：编排者复制到 `hf/WORKER.md`，填好 `{{…}}` 的四处（片名、设计真相、图片清单、本片额外规则），硬规则一字不改。

You build HyperFrames scene sub-compositions for a vertical 1080×1920 narrated explainer (Chinese) — or 1920×1080 when `../script.json` has `"aspect": "landscape"` (then use the landscape layout rules below and `data-width="1920" data-height="1080"`). The project root is `PROJECT_DIR` (the folder holding this file). Read this whole file, then `STORYBOARD.md` (only your frames + the 设计 section), then `beats.json` (only your scenes). Look at every image you use (Read tool) before placing it, so annotations land on the right spot.

## Output per scene `<id>`

1. `compositions/s-<id>.html` — the scene.
2. `compositions/s-<id>.sfx.json` — sound cues `[[when, "name", vol], ...]`. Names = files in `assets/audio/*.mp3`. **`when` is an anchor, never a computed number**, so cues follow the voice when it is re-recorded: `{"line": 0, "phrase": "拍到", "off": 0.05}` (that word's onset), `{"clip": "c1", "t": 2.8}` (seconds into a source clip in this scene), or `{"cap": 3}` (a caption's start). **Sparse:** 0–2 cues per scene, about a dozen for the whole film — only key story moments (a reveal, a stamp, the one recurring motif such as a flash or shutter). No cue per caption, no typing/sweep/click under every event, never inside a source clip except one motif hit. Volumes 0.12–0.3, short sounds. Long hits (`hit-hero`, `impact-bass-1`) only where the storyboard names a 长重击, max one in the film.

Do NOT edit `index.html`, `build.py`, `make_beats.py`, `assets/style.css`, `assets/beats.js`, `beats.json` or other scenes. Shared styles you need go inside your scene's `<style>` with a scene prefix.

## Composition contract (exact — copy this skeleton)

```html
<!doctype html>
<html>
  <head><meta charset="UTF-8" /></head>
  <body>
    <template>
      <link rel="stylesheet" href="assets/style.css" />
      <style>
        @font-face { font-family: "HeiHeavy"; src: url("assets/fonts/NotoSansSC-900.woff") format("woff"); font-weight: 900; }
        @font-face { font-family: "HeiBold"; src: url("assets/fonts/NotoSansSC-700.woff") format("woff"); font-weight: 700; }
        @font-face { font-family: "Hei"; src: url("assets/fonts/NotoSansSC-500.woff") format("woff"); font-weight: 500; }
        #s-hook { position: absolute; inset: 0; }
        /* scene CSS, every selector prefixed (e.g. .hk-*) */
      </style>
      <div id="s-hook" data-composition-id="s-hook" data-width="1080" data-height="1920">
        <div class="scene">
          <div class="hk-bg" data-layout-ignore>…ambience (hex wall / grid / texture)…</div>
          …
        </div>
      </div>
      <script>
        (function () {
          const L = window.BEATS["hook"].lines;          // read, never paste timings into the file
          const at = (li, phrase, off = 0) => L[li].chars[L[li].text.indexOf(phrase)] + off;
          const tl = gsap.timeline({ paused: true });
          // tweens at scene-local seconds (0 = scene start), placed with at(...)
          window.__timelines["s-hook"] = tl;
        })();
      </script>
    </template>
  </body>
</html>
```

## Hard rules

Timing
- **Never inline timings.** Read `window.BEATS["<id>"]` (written by make_beats.py, loaded by index.html). `lines[].chars[i]` = when character i of `lines[].text` is spoken, scene-local seconds; `caps[]` = caption a→b. When the voice is re-recorded only beats.js changes and every scene follows. Numbers only for durations and ambient loops.
- A visual event lands within ±0.2 s of the word that names it. **One caption = one visual change**: every caption in `caps` coincides with a visible change (new shot, annotation, zoom to a new region, number tick, element entering). No dead span > 2 s.

Determinism (lint enforces most; breaking them breaks the render)
- Exactly one `gsap.timeline({ paused: true })`, registered last at `window.__timelines["s-<id>"]`. No `tl.play()`, `Date.now()`, unseeded `Math.random()` (use mulberry32), network, `repeat: -1`.
- Unique ids/classes across the film: prefix everything with your scene prefix.
- No CSS `transform` initial values on elements you tween with GSAP — set the start state in `fromTo`. Center with flex/inset, not translate(-50%).
- **Several `fromTo` on the same element/property: every one after the first gets `immediateRender: false`**, or its start state is painted at t=0 and the element flashes on screen.
- Several shots in one scene: child wrappers toggled with `tl.set(el, {opacity: 1/0}, t)`. Never tween `.clip`, `visibility`, `autoAlpha`, `display`.
- No `<br>` in body text (short display titles excepted). Transformed elements are block-level and sized.
- `font-family`: HeiHeavy / HeiBold / Hei (declared above) or "JetBrains Mono" (embedded by the renderer). Nothing else.
- Images only from the library below (`assets/img/...`). No video files unless listed.

Audit hygiene (`npx hyperframes check` must end with 0 errors)
- **Mark every decorative layer `data-layout-ignore`** from the start: hex walls, grids, noise, fog rings of characters, code texture inside icons, ambience text, anything that intentionally overflows the canvas or sits under content. Unmarked texture text fails the layout and contrast audits by the dozen.
- Deliberate text-over-text (a stamp on a bill, a label on a screenshot) gets `data-layout-allow-overlap` on the covering element only.
- Real content stays readable: ≥24 px, contrast ≥3:1 for large text.

Truthfulness
- **On-screen Chinese comes from the script.** Labels, headings and annotations reuse wording from `beats.json` / `STORYBOARD.md` / `../script.json`. Don't add your own characterisations ("single witness", "far side", "first ever") — in a documentary that is a factual claim. If a scene needs a label that isn't there, keep it neutral (what is shown, not what it means) and list it in your report; `build.py` flags every Chinese phrase it can't trace to the script.
- **Don't invent specific numbers or names.** Drawn bills, documents, dashboards and stand-ins use numbers from the brief/beats/real data, or placeholders (`¥ •••`, `v•.•`). Product and repo names follow the current primary source given below (if a repo was renamed, use the new name). If you need a figure you don't have, use a placeholder and say so in your report.
- Real products (GitHub, X, the tool being explained) are always the provided screenshots or real output, never redrawn UI. Drawn mock UI only for generic things (an editor, a bill, an app icon, a terminal, an installer box).

Layout
- Phone safe area: on Douyin / 视频号 the status bar and Dynamic Island cover y 0–200 and the author name, caption text and buttons cover y 1680–1920. **Nothing that carries information goes outside y 200–1680** — only ambience/texture there.
- The global top bar (chapter progress bar + chapter title, with its own opaque backing) covers y 200–300; never put content there. Main stage y 300–1400. Captions are drawn globally at y 1420–1570 — keep key content out of y 1410–1580. The corner host occupies bottom-left x 0–380, y ≥ 1420 (Ray's IP default; if `build.py` has no host, captions move to 1500–1650 and the stage may extend to 1490). x margins ≥ 50 px.
- **Landscape films (1920×1080)** replace the two bullets above: no phone UI covers the frame, keep 5% title-safe margins (x ≥ 96, y ≥ 54). There is **no top bar** (no progress bar or chapter title in landscape) — the stage is y 60–850. Captions are drawn at y 930–1040 (white text with a black outline, no box, centered) — keep key content out of y 920–1050. The host is a small circle (164 px, bottom-left x 56–220, y 860–1024, or mirrored to bottom-right in scenes whose `script.json` entry has `"host_side": "right"`) that only appears during key lines (`host.show` / big-shot lines) — it is gone the rest of the time, so the frame must look complete without it; never put content behind it. A big-shot segment grows it to a 420 px circle on its side. Use the width: side-by-side layouts (evidence on one side, explanation on the other) instead of stacking.
- Source clips: when `BEATS[id].clips` is non-empty, the soundtrack plays the original recording there with no narration. Show it (real waveform from the clip audio, playhead synced to clip start/end, speaker + UTC/date label, transcript typed in sync with `segs`); the caption bar already shows the zh + en lines.
- Every scene keeps a persistent ambience layer drifting slowly over the whole scene, so it never looks empty.
- Hard cuts between scenes: make the first 0.3 s decisive; end on the final state held (no fade-to-black).

## Design truth

{{从 STORYBOARD 设计段 + assets/style.css 摘：概念一句话、色板（每个颜色的角色，哪一个是稀缺色）、字体角色、证据怎么钉（.shot/.pin/.redbox…）、动效词汇}}

## Image library (`assets/img/`, w×h — what is where)

{{逐张列：文件名、尺寸、画面里是什么、需要标注的区域在哪}}

## Extra rules for this film

{{可选}}

## When done

`cd PROJECT_DIR && npx hyperframes lint` (whole project; fix only findings in YOUR files). Report: files written, each caption → visual event (one line each), any placeholder you used instead of a number/name, anything you could not do.
