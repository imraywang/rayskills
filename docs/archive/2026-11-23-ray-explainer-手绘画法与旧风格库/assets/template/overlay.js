// ray-explainer overlay: burned-in captions + progress bar + header, drawn on top of ANY scene
// (kit scenes and huashu grammar clips alike), so the whole film shares one caption style.
// Needs window.TIMELINE; reads window.META.header. Exposes window.RXO = { ready, prep(t), draw(ctx, t) }.
// Optional host (digital presenter): drawn only when the project has host/plan.json (scripts/host.py writes it).
// Deterministic: everything is a function of t.
(() => {
  const TL = window.TIMELINE;
  const FONT_URL = window.RX_CAPTION_FONT || '/huashu/lib/fonts/NotoSansSC-700.woff';
  const FAM = '"RX-Caption","PingFang SC","Hannotate SC",sans-serif';
  // 版位来自 assets/canvas.json（render.js 注入 window.CANVAS）；没注入就是竖屏：字幕底边 1656，躲开平台底部的作者名/文案/互动栏
  const CV = window.CANVAS || { caption: { y: 1560, h: 96, size: 54, maxw: 15 }, bar: { x0: 80, x1: 1000, y: 252, h: 8, header_y: 222, header_size: 30 } };
  let CAP_Y = CV.caption.y; const CAP_H = CV.caption.h, CAP_SIZE = CV.caption.size;

  // split a line into ≤15-wide caption chunks at punctuation; time each chunk from per-char timing when present.
  // Width counts ASCII as half a CJK char; long pieces split near equal widths, only at Chinese word boundaries
  // (Intl.Segmenter) and never inside a Latin word, number, or a Latin phrase like "Search Console".
  const MAXW = CV.caption.maxw, cw = ch => /[\x20-\x7e]/.test(ch) ? 0.55 : 1, width = s => [...s].reduce((a, ch) => a + cw(ch), 0);
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

  // ---- 数字人主持人（角落是 IP 默认）：大机位播视频帧序列（默认 MiniMax H3，可选 Kling），其余时间左下角换嘴型图层 ----
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
  const ease = x => x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;   // power2.inOut
  const ease3 = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  const T_IN = .6, HOLD = .15, T_OUT = .8;   // 段首提前 0.6s 放大；段尾停 0.15s 再用 0.8s 缩回角落
  const openBig = () => HOST.segments.length && HOST.segments[0].start < 1;   // 开场就是大机位：第 0 帧就在大机位淡入，不先滑入再放大
  function bigAt(t) {   // 当前离大机位有多近（0 角落 … 1 大机位），以及对应段落
    let k = 0, seg = null;
    HOST.segments.forEach((s, i) => {
      const v = i === 0 && openBig() && t < s.start ? 1
        : t < s.start ? ease(clamp((t - s.start + T_IN) / T_IN))
        : t < s.end + HOLD ? 1 : 1 - ease(clamp((t - s.end - HOLD) / T_OUT));
      if (v > k) { k = v; seg = s; }
    });
    return { k, seg };
  }
  const mouthAt = t => { const M = HOST.mouth; let lo = 0, hi = M.length - 1, r = -1; while (lo <= hi) { const m = (lo + hi) >> 1; if (M[m][0] <= t) { r = m; lo = m + 1; } else hi = m - 1; } return r < 0 ? 'X' : M[r][1]; };
  // 横屏：Screen Studio 式气泡。气泡（圆角矩形）在角落和大机位之间插值，形象按 crop 只露头肩，大机位时气泡放大露出半身
  // 换边（学小Lin说）：HOST.sides = [[时刻, 'left' | 'right'], …]，主画面在哪边、气泡就去另一边。换边时刻前后各 switch 秒：缩小消失 → 换到另一角 → 放大出现
  const sideAt = t => { let sd = 'left'; for (const [a, v] of HOST.sides || []) if (t >= a) sd = v; return sd; };
  const switchScale = t => { let m = 1; for (const [a] of (HOST.sides || []).slice(1)) { const d = Math.abs(t - a); if (d < HOST.switch) m = Math.min(m, ease(d / HOST.switch)); } return m; };
  // 只在关键句出现（plan.show = [[开口, 说完], …]）：开口前 show_in 秒弹出，说完停 show_hold 秒再用 show_out 秒淡出；没有 show 字段＝全程都在
  const showAt = t => { if (!HOST.show) return 1; let m = 0; for (const [a, b] of HOST.show)
    m = Math.max(m, t < a ? ease(clamp((t - a + HOST.show_in) / HOST.show_in)) : t <= b + HOST.show_hold ? 1 : 1 - ease(clamp((t - b - HOST.show_hold) / HOST.show_out))); return m; };
  function drawBubble(ctx, t) {
    const vis = showAt(t); if (vis <= 0.001) return;
    const s = segAt(t), { k, seg } = bigAt(t), A0 = HOST.bubble, B = { ...HOST.big_bubble, ...((seg && seg.big) || {}) }, cr = HOST.crop;
    const L = key => A0[key] + ((B[key] ?? A0[key]) - A0[key]) * k;
    const slide = openBig() || HOST.show ? 0 : (1 - ease3(clamp(t / .5))) * (ctx.canvas.height - A0.y);   // 全程都在时开头从画面下方滑入
    let fx = L('x'); const fy = L('y') + slide, fw = L('w'), fh = L('h'), r = A0.r * A0.w + ((B.r ?? A0.r) * B.w - A0.r * A0.w) * k;
    if (sideAt(t) === 'right') fx = ctx.canvas.width - fx - fw;   // 坐标按左下写，右下是镜像
    if (openBig()) { const f = clamp((t - .05) / .35); ctx.globalAlpha = 1 - (1 - f) * (1 - f); }
    const sc = switchScale(t) * (0.6 + 0.4 * vis); ctx.globalAlpha *= vis; if (sc < 1) { ctx.globalAlpha *= sc; ctx.save(); ctx.translate(fx + fw / 2, fy + fh); ctx.scale(Math.max(sc, .01), Math.max(sc, .01)); ctx.translate(-(fx + fw / 2), -(fy + fh)); }
    ctx.save();
    ctx.shadowColor = A0.shadow; ctx.shadowBlur = A0.blur; ctx.shadowOffsetY = A0.dy;
    ctx.fillStyle = A0.fill; ctx.beginPath(); ctx.roundRect(fx, fy, fw, fh, r); ctx.fill();
    ctx.shadowColor = 'transparent'; ctx.clip();
    const w = fw / cr.w, x = fx - cr.x * w, y = fy - cr.y * w;
    drawBody(ctx, t, s, x, y, w, w * HOST.aspect);
    ctx.restore();
    if (A0.ring) { ctx.save(); ctx.strokeStyle = A0.ring; ctx.lineWidth = A0.ring_w || 4; ctx.beginPath(); ctx.roundRect(fx, fy, fw, fh, r); ctx.stroke(); ctx.restore(); }   // 细描边：签名幕墨绿底上也看得出气泡
    if (sc < 1) ctx.restore();
  }
  function drawBody(ctx, t, s, x, y, w, h) {   // 大机位帧（有就画它），否则形象底图 + 口型 + 眨眼，带轻微摆动
    if (s) { const im = FRAMES.get(frameUrl(s, t)); if (im) {   // pad：帧四周比形象图多出的边（占形象宽 / 高），往外画，形象和角落图层对齐
      const [l, tp, r, b] = s.pad || [0, 0, 0, 0]; ctx.drawImage(im, x - l * w, y - tp * h, w * (1 + l + r), h * (1 + tp + b)); return; } }
    const A = HOST.avatar, sc = w / A.size[0];
    ctx.save(); ctx.translate(x + w / 2, y + h); ctx.rotate(Math.sin(t / 1.6 * Math.PI) * .02); ctx.translate(-(x + w / 2), -(y + h));
    ctx.drawImage(HIMG.base, x, y, w, h);
    const put = key => { const [px, py, pw, ph] = A.patches[key]; ctx.drawImage(HIMG[key], x + px * sc, y + py * sc, pw * sc, ph * sc); };
    const m = mouthAt(t); if (m !== 'X' && HIMG[m]) put(m);
    if (HIMG.B && HOST.blinks.some(b => t >= b && t < b + .12)) put('B');
    ctx.restore();
  }
  function drawHost(ctx, t) {
    if (HOST.bubble) return drawBubble(ctx, t);
    const s = segAt(t), C = HOST.corner, { k, seg } = bigAt(t), B = (seg && seg.big) || HOST.big;   // 段落可以自带位置（host.big[].pos）
    const w = C.w + (B.w - C.w) * k, x = C.x + (B.x - C.x) * k, h = w * HOST.aspect;
    const slide = openBig() ? 0 : (1 - ease3(clamp(t / .5))) * 420;   // 默认开头从角落下方滑入
    const y = C.y + (B.y - C.y) * k + slide;
    if (openBig()) { const f = clamp((t - .05) / .35); ctx.globalAlpha = 1 - (1 - f) * (1 - f); }   // power1.out 淡入
    drawBody(ctx, t, s, x, y, w, h);
  }

  // theme colours for bar / captions; window.SIG (render.js, from script.json "sig"): signature scenes, where the bar turns light
  const OV = (window.THEME && window.THEME.overlay) || {}, SIG = window.SIG || [];
  const sigAt = t => SIG.find(s => t >= s.start && t < s.end);

  function draw(ctx, t) {
    const W = ctx.canvas.width;
    if (window.RX_CLEAN) return;   // clean frames (cover): no captions / progress
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.shadowBlur = 0;
    if (HOST) { drawHost(ctx, t); ctx.globalAlpha = 1; }   // under captions: the caption sits on the presenter's chest
    // progress bar + header
    const pr = clamp(t / TL.duration), BR = CV.bar, bw = BR.x1 - BR.x0;
    if (BR.show !== false) {   // 横屏不放进度条和小标题   // 竖屏 y 200 以上会被灵动岛/状态栏挡住：小标题 y 222，进度条 y 252
    ctx.fillStyle = 'rgba(128,128,128,.25)'; ctx.fillRect(BR.x0, BR.y, bw, BR.h);
    ctx.fillStyle = (sigAt(t) && OV.sigBar) || OV.bar || '#e8743b'; ctx.fillRect(BR.x0, BR.y, bw * pr, BR.h);
    const header = (window.META && window.META.header) || (window.SCRIPT && window.SCRIPT.header) || '';
    if (header) { ctx.font = `500 ${BR.header_size}px ${FAM}`; ctx.fillStyle = 'rgba(140,140,140,.95)'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(header, W / 2, BR.header_y); }
    }
    // caption
    const c = CAPS.find(c => t >= c.start - .05 && t < c.end + .25);
    if (c) {
      ctx.font = `700 ${CAP_SIZE}px ${FAM}`;
      const w = ctx.measureText(c.s).width + 70, x = W / 2 - w / 2;
      ctx.globalAlpha = clamp((t - c.start + .05) / .12);
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      if (CV.caption.style === 'outline') {   // 横屏：白字 + 黑描边 + 柔和阴影，无底框（小Lin说、差评、漫士都这么做）
        const cy = CAP_Y + CAP_H / 2 + 2; ctx.lineJoin = 'round'; ctx.miterLimit = 2;
        ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 14; ctx.shadowOffsetY = 3;
        ctx.strokeStyle = 'rgba(0,0,0,.92)'; ctx.lineWidth = CV.caption.stroke || 9; ctx.strokeText(c.s, W / 2, cy);
        ctx.shadowColor = 'transparent'; ctx.fillStyle = '#ffffff'; ctx.fillText(c.s, W / 2, cy);
      } else {
        ctx.fillStyle = OV.caption || 'rgba(30,27,24,.86)'; ctx.beginPath(); ctx.roundRect(x, CAP_Y, w, CAP_H, 22); ctx.fill();
        ctx.fillStyle = OV.captionInk || '#fff8ec'; ctx.fillText(c.s, W / 2, CAP_Y + CAP_H / 2 + 2);
      }
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
