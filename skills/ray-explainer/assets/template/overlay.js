// ray-explainer overlay: burned-in captions + progress bar + header, drawn on top of ANY scene
// (kit scenes and huashu grammar clips alike), so the whole film shares one caption style.
// Needs window.TIMELINE; reads window.META.header. Exposes window.RXO = { ready, draw(ctx, t) }.
// Deterministic: everything is a function of t.
(() => {
  const TL = window.TIMELINE;
  const FONT_URL = window.RX_CAPTION_FONT || '/huashu/lib/fonts/NotoSansSC-700.woff';
  const FAM = '"RX-Caption","PingFang SC","Hannotate SC",sans-serif';
  const CAP_Y = 1640, CAP_H = 96, CAP_SIZE = 54;

  // split a line into ≤15-char caption chunks at punctuation; time each chunk from per-char timing when present
  function chunks(line) {
    const parts = line.text.split(/(?<=[，。：？！、；])/).filter(s => s.trim());
    const out = []; let pos = 0;
    for (const p of parts) {
      const lead = p.length - p.trimStart().length, s = p.trim().replace(/[，。：、；]$/, '');
      const at = line.text.indexOf(p, pos) + lead; pos = at + p.trim().length;
      if (s.length > 15) { const h = Math.ceil(s.length / 2); out.push({ s: s.slice(0, h), i: at }, { s: s.slice(h), i: at + h }); }
      else out.push({ s, i: at });
    }
    const T = i => line.chars && line.chars.length === line.text.length ? line.chars[Math.min(i, line.text.length - 1)]
      : line.start + (line.end - line.start) * i / line.text.length;
    return out.map((c, k) => ({ s: c.s, start: T(c.i), end: k + 1 < out.length ? T(out[k + 1].i) : line.end }));
  }
  const CAPS = TL.scenes.flatMap(s => s.lines.flatMap(chunks));
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));

  function draw(ctx, t) {
    const W = ctx.canvas.width;
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.shadowBlur = 0;
    // progress bar + header
    const pr = clamp(t / TL.duration);
    ctx.fillStyle = 'rgba(128,128,128,.25)'; ctx.fillRect(80, 90, W - 160, 10);
    ctx.fillStyle = '#e8743b'; ctx.fillRect(80, 90, (W - 160) * pr, 10);
    const header = (window.META && window.META.header) || '';
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
    try { const f = new FontFace('RX-Caption', `url(${FONT_URL})`, { weight: '100 900' }); await f.load(); document.fonts.add(f); return true; }
    catch (e) { console.warn('caption font not loaded, falling back to system font:', FONT_URL); return false; }
  })();
  window.RXO = { ready, draw, CAPS };
})();
