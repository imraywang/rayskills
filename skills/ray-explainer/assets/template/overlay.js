// ray-explainer overlay: burned-in captions + progress bar + header, drawn on top of ANY scene
// (kit scenes and huashu grammar clips alike), so the whole film shares one caption style.
// Needs window.TIMELINE; reads window.META.header. Exposes window.RXO = { ready, prep(t), draw(ctx, t) }.
// Optional host (digital presenter): drawn only when the project has host/plan.json (scripts/host.py writes it).
// Deterministic: everything is a function of t.
(() => {
  const TL = window.TIMELINE;
  const FONT_URL = window.RX_CAPTION_FONT || '/huashu/lib/fonts/NotoSansSC-700.woff';
  const FAM = '"RX-Caption","PingFang SC","Hannotate SC",sans-serif';
  let CAP_Y = 1640; const CAP_H = 96, CAP_SIZE = 54;

  // split a line into ≤15-wide caption chunks at punctuation; time each chunk from per-char timing when present.
  // Width counts ASCII as half a CJK char; long pieces split near equal widths, only at Chinese word boundaries
  // (Intl.Segmenter) and never inside a Latin word, number, or a Latin phrase like "Search Console".
  const MAXW = 15, cw = ch => /[\x20-\x7e]/.test(ch) ? 0.55 : 1, width = s => [...s].reduce((a, ch) => a + cw(ch), 0);
  const word = ch => /[A-Za-z0-9]/.test(ch || '');
  const SEG = typeof Intl !== 'undefined' && Intl.Segmenter ? new Intl.Segmenter('zh', { granularity: 'word' }) : null;
  const bounds = s => SEG ? new Set([...SEG.segment(s)].map(x => x.index)) : null;
  function splitWide(s, at, out) {
    if (width(s) <= MAXW) { if (s.trim()) out.push({ s: s.trim(), i: at + (s.length - s.trimStart().length) }); return; }
    const n = Math.ceil(width(s) / MAXW), target = width(s) / n, B = bounds(s); let best = -1, bestCost = 1e9, acc = 0;
    for (let k = 1; k < s.length; k++) {
      acc += cw(s[k - 1]);
      if (word(s[k - 1]) && word(s[k])) continue;                                   // inside a Latin word / number
      if (s[k - 1] === ' ' && word(s[k - 2]) && word(s[k])) continue;               // between two Latin words
      if (s[k] === ' ' && word(s[k - 1]) && word(s[k + 1])) continue;
      if (B && !B.has(k) && s[k - 1] !== ' ' && s[k] !== ' ') continue;              // inside a Chinese word
      const fits = acc <= MAXW && width(s) - acc <= MAXW * (n - 1);
      const cost = Math.abs(acc - target) - (s[k - 1] === ' ' || s[k] === ' ' ? 0.8 : 0)
        - (fits && /[把会就才都也还被让在要和跟]/.test(s[k] === ' ' ? s[k + 1] : s[k]) ? 5 : 0) + (fits ? 0 : 6);   // break before a function word when both halves fit
      if (cost < bestCost) { bestCost = cost; best = k; }
    }
    if (best < 0) { out.push({ s: s.trim(), i: at }); return; }   // one unbreakable token: keep whole
    splitWide(s.slice(0, best), at, out); splitWide(s.slice(best), at + best, out);
  }
  function chunks(line) {
    const parts = line.text.split(/(?<=[，。：？！、；])/).filter(s => s.trim());
    const out = []; let pos = 0;
    for (const p of parts) {
      const lead = p.length - p.trimStart().length, s = p.trim().replace(/[，。：、；]$/, '');
      const at = line.text.indexOf(p, pos) + lead; pos = at + p.trim().length;
      splitWide(s, at, out);
    }
    const T = i => line.chars && line.chars.length === line.text.length ? line.chars[Math.min(i, line.text.length - 1)]
      : line.start + (line.end - line.start) * i / line.text.length;
    return out.map((c, k) => ({ s: c.s, start: T(c.i), end: k + 1 < out.length ? T(out[k + 1].i) : line.end }));
  }
  const CAPS = TL.scenes.flatMap(s => s.lines.flatMap(chunks));
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));

  // ---- 数字人主持人（可选）：大机位播 Kling 帧序列，其余时间左下角换嘴型图层 ----
  let HOST = null; const HIMG = {}, FRAMES = new Map();
  const loadImg = u => new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(u); im.src = u; });
  async function hostInit() {
    try { const r = await fetch('/host/plan.json'); if (!r.ok) return; HOST = await r.json(); } catch (e) { return; }
    const A = HOST.avatar; HIMG.base = await loadImg(A.dir + 'base.png');
    for (const k of Object.keys(A.patches)) HIMG[k] = await loadImg(A.dir + k + '.png');
    CAP_Y = HOST.caption_y;
  }
  const segAt = t => HOST.segments.find(s => t >= s.start && t < s.end);
  const frameUrl = (s, t) => s.dir + String(Math.min(s.count, Math.floor((t - s.start) * s.fps) + 1)).padStart(4, '0') + '.webp';
  async function prep(t) {   // render.js awaits this before each frame: the big-shot frame for t must be decoded first
    if (!HOST || window.RX_CLEAN) return; const s = segAt(t); if (!s) return; const u = frameUrl(s, t);
    if (!FRAMES.has(u)) { if (FRAMES.size > 90) FRAMES.delete(FRAMES.keys().next().value); FRAMES.set(u, await loadImg(u)); }
  }
  const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  const mouthAt = t => { const M = HOST.mouth; let lo = 0, hi = M.length - 1, r = -1; while (lo <= hi) { const m = (lo + hi) >> 1; if (M[m][0] <= t) { r = m; lo = m + 1; } else hi = m - 1; } return r < 0 ? 'X' : M[r][1]; };
  function drawHost(ctx, t) {
    const s = segAt(t), C = HOST.corner, B = (s && s.big) || HOST.big;   // 段落可以自带位置（host.big[].pos）
    const k = s ? Math.min(ease(clamp((t - s.start) / HOST.trans)), ease(clamp((s.end - t) / HOST.trans))) : 0;
    const w = C.w + (B.w - C.w) * k, x = C.x + (B.x - C.x) * k, h = w * HOST.aspect;
    const y = C.y + (B.y - C.y) * k + (1 - ease(clamp(t / .5))) * 420;   // slides up at the very start
    if (s) { const im = FRAMES.get(frameUrl(s, t)); if (im) { ctx.drawImage(im, x, y, w, h); return; } }
    const A = HOST.avatar, sc = w / A.size[0];
    ctx.save(); ctx.translate(x + w / 2, y + h); ctx.rotate(Math.sin(t / 1.6 * Math.PI) * .02); ctx.translate(-(x + w / 2), -(y + h));
    ctx.drawImage(HIMG.base, x, y, w, h);
    const put = key => { const [px, py, pw, ph] = A.patches[key]; ctx.drawImage(HIMG[key], x + px * sc, y + py * sc, pw * sc, ph * sc); };
    const m = mouthAt(t); if (m !== 'X' && HIMG[m]) put(m);
    if (HIMG.B && HOST.blinks.some(b => t >= b && t < b + .12)) put('B');
    ctx.restore();
  }

  function draw(ctx, t) {
    if (window.RX_CLEAN) return;   // clean frames (cover): no captions / progress
    const W = ctx.canvas.width;
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.shadowBlur = 0;
    if (HOST) drawHost(ctx, t);   // under captions: the caption sits on the presenter's chest
    // progress bar + header
    const pr = clamp(t / TL.duration);
    ctx.fillStyle = 'rgba(128,128,128,.25)'; ctx.fillRect(80, 90, W - 160, 10);
    ctx.fillStyle = '#e8743b'; ctx.fillRect(80, 90, (W - 160) * pr, 10);
    const header = (window.META && window.META.header) || (window.SCRIPT && window.SCRIPT.header) || '';
    if (header) { ctx.font = `500 32px ${FAM}`; ctx.fillStyle = 'rgba(140,140,140,.95)'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(header, W / 2, 140); }
    // caption
    const c = CAPS.find(c => t >= c.start - .05 && t < c.end + .25);
    if (c) {
      ctx.font = `700 ${CAP_SIZE}px ${FAM}`;
      const w = ctx.measureText(c.s).width + 70, x = W / 2 - w / 2;
      ctx.globalAlpha = clamp((t - c.start + .05) / .12);
      ctx.fillStyle = 'rgba(30,27,24,.86)'; ctx.beginPath(); ctx.roundRect(x, CAP_Y, w, CAP_H, 22); ctx.fill();
      ctx.fillStyle = '#fff8ec'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(c.s, W / 2, CAP_Y + CAP_H / 2 + 2);
    }
    ctx.restore();
  }

  const ready = (async () => {
    await hostInit();
    try { const f = new FontFace('RX-Caption', `url(${FONT_URL})`, { weight: '100 900' }); await f.load(); document.fonts.add(f); return true; }
    catch (e) { console.warn('caption font not loaded, falling back to system font:', FONT_URL); return false; }
  })();
  window.RXO = { ready, prep, draw, CAPS };
})();
