// ray-explainer kit: deterministic hand-drawn drawing library + frame loop.
// Every frame is a pure function of t (seconds). Never use Date, Math.random or network here.
// scenes.js fills the global `S` object: S[sceneId] = (t, sc) => { ... }
const W = 1080, H = 1920;
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const TL = window.TIMELINE;
const C = { paper: '#f7f0e3', ink: '#2a2622', soft: '#8a7f72', orange: '#e8743b', blue: '#3d7fd9',
  green: '#35a372', red: '#d9483b', yellow: '#f2c14e', purple: '#8a5cd1', tint: '#fbe3cf', btint: '#dde9fb', gtint: '#d8f0e3' };
const FONT = '"Hannotate SC","HanziPen SC","PingFang SC",sans-serif';

// ---------- math / rng ----------
function rng(seed) { let a = (seed * 2654435761) >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const ap = (t, s, d) => clamp((t - s) / d);
const eOut = x => 1 - Math.pow(1 - x, 3);
const eInOut = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const eBack = x => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const lerp = (a, b, x) => a + (b - a) * x;
let BOIL = 0; // changes ~6x/sec so strokes "breathe" like hand-drawn animation

// ---------- rough drawing ----------
function densify(pts, closed, step = 26) {
  const out = []; const n = pts.length;
  for (let i = 0; i < (closed ? n : n - 1); i++) {
    const [x1, y1] = pts[i], [x2, y2] = pts[(i + 1) % n];
    const k = Math.max(1, Math.ceil(Math.hypot(x2 - x1, y2 - y1) / step));
    for (let j = 0; j < k; j++) out.push([lerp(x1, x2, j / k), lerp(y1, y2, j / k)]);
  }
  out.push(closed ? [...pts[0]] : [...pts[n - 1]]);
  return out;
}
function jitter(pts, seed, amp) {
  const r = rng(seed); const f1 = r() * 6, f2 = r() * 6;
  return pts.map(([x, y], i) => [x + Math.sin(i * .7 + f1) * amp + (r() - .5) * amp * .6, y + Math.cos(i * .6 + f2) * amp + (r() - .5) * amp * .6]);
}
function strokePts(pts, p) {
  if (p <= 0 || pts.length < 2) return;
  let total = 0; const seg = [];
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); total += d; }
  let left = total * p;
  ctx.beginPath(); ctx.moveTo(...pts[0]);
  for (let i = 1; i < pts.length && left > 0; i++) {
    const d = seg[i - 1];
    if (d <= left) ctx.lineTo(...pts[i]);
    else { const k = left / d; ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)); }
    left -= d;
  }
  ctx.stroke();
}
function rpath(pts, o = {}) {
  const { closed = false, p = 1, color = C.ink, w = 5, amp = 2.2, seed = 1, passes = 2, fill = null } = o;
  const base = densify(pts, closed);
  if (fill && p > 0) {
    ctx.save(); ctx.globalAlpha *= clamp(p * 1.5); ctx.fillStyle = fill;
    const fp = jitter(base, seed * 7 + BOIL, amp * 1.4);
    ctx.beginPath(); ctx.moveTo(...fp[0]); fp.forEach(q => ctx.lineTo(...q)); ctx.closePath(); ctx.fill(); ctx.restore();
  }
  ctx.strokeStyle = color; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (let k = 0; k < passes; k++) { ctx.lineWidth = k ? w * .55 : w; strokePts(jitter(base, seed * 31 + k * 101 + BOIL, amp), p); }
}
const rline = (x1, y1, x2, y2, o) => rpath([[x1, y1], [x2, y2]], o);
function rrect(x, y, w, h, o = {}) {
  const ov = 6; // slight overshoot at the closing corner like a pen stroke
  rpath([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y - ov]], { ...o, closed: false, fill: null });
  if (o.fill) rpath([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], { ...o, closed: true, passes: 0 });
}
function rcircle(cx, cy, r, o = {}) {
  const pts = []; const n = 40, rr = rng((o.seed || 1) * 13);
  for (let i = 0; i <= n + 3; i++) { const a = -Math.PI / 2 + i / n * Math.PI * 2; const k = 1 + (rr() - .5) * .04; pts.push([cx + Math.cos(a) * r * k, cy + Math.sin(a) * r * (o.squash || 1) * k]); }
  rpath(pts, { ...o, fill: null });
  if (o.fill) rpath(pts.slice(0, n), { ...o, closed: true, passes: 0 });
}
function rarrow(x1, y1, x2, y2, o = {}) {
  const p = o.p ?? 1; rline(x1, y1, x2, y2, { ...o, p: clamp(p / .8) });
  const hp = ap(p, .8, .2); if (hp <= 0) return;
  const a = Math.atan2(y2 - y1, x2 - x1), L = o.head || 34;
  rline(x2, y2, x2 - Math.cos(a - .45) * L, y2 - Math.sin(a - .45) * L, { ...o, p: hp, seed: (o.seed || 1) + 5 });
  rline(x2, y2, x2 - Math.cos(a + .45) * L, y2 - Math.sin(a + .45) * L, { ...o, p: hp, seed: (o.seed || 1) + 9 });
}
function cross(cx, cy, s, p, seed = 3) {
  rline(cx - s, cy - s, cx + s, cy + s, { p: clamp(p * 2), color: C.red, w: 11, seed });
  rline(cx + s, cy - s, cx - s, cy + s, { p: clamp(p * 2 - 1), color: C.red, w: 11, seed: seed + 1 });
}

// ---------- text ----------
function text(str, x, y, o = {}) {
  const { size = 64, color = C.ink, align = 'center', weight = 'bold', alpha = 1, scale = 1, rot = 0, base = 'middle' } = o;
  if (alpha <= 0 || scale <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(rot); ctx.scale(scale, scale);
  ctx.font = `${weight} ${size}px ${FONT}`; ctx.fillStyle = color; ctx.textAlign = align; ctx.textBaseline = base;
  ctx.fillText(str, 0, 0); ctx.restore();
}
const pop = (t, s, d = .45) => eBack(ap(t, s, d));
function typed(str, p) { return str.slice(0, Math.round(str.length * clamp(p))); }
function wrapText(str, maxW, size) {
  ctx.font = `bold ${size}px ${FONT}`; const out = []; let cur = '';
  for (const ch of str) { if (ctx.measureText(cur + ch).width > maxW && cur) { out.push(cur); cur = ch; } else cur += ch; }
  if (cur) out.push(cur); return out;
}

// ---------- icons ----------
function bulb(x, y, s, p, color = C.yellow, seed = 1) {
  rcircle(x, y - s * .15, s * .5, { p, fill: color, seed, w: 5 });
  rline(x - s * .22, y + s * .45, x + s * .22, y + s * .45, { p, seed: seed + 2, w: 5 });
  rline(x - s * .16, y + s * .6, x + s * .16, y + s * .6, { p, seed: seed + 3, w: 5 });
  if (p > .9) for (let i = 0; i < 5; i++) { const a = -Math.PI / 2 + (i - 2) * .55, r1 = s * .72, r2 = s * .92; rline(x + Math.cos(a) * r1, y - s * .15 + Math.sin(a) * r1, x + Math.cos(a) * r2, y - s * .15 + Math.sin(a) * r2, { seed: seed + 10 + i, w: 4, color: C.orange }); }
}
function broadcast(x, y, s, p, seed = 1) {
  rcircle(x, y, s * .12, { p, fill: C.blue, seed, w: 4 });
  for (let i = 1; i <= 3; i++) {
    const r = s * (.12 + i * .17), pts = [], pts2 = [];
    for (let k = 0; k <= 12; k++) { const a = -.7 + k / 12 * 1.4; pts.push([x + Math.cos(a) * r, y + Math.sin(a) * r]); pts2.push([x - Math.cos(a) * r, y + Math.sin(a) * r]); }
    rpath(pts, { p: ap(p, i * .2, .4), seed: seed + i, w: 5, color: C.blue }); rpath(pts2, { p: ap(p, i * .2, .4), seed: seed + i + 7, w: 5, color: C.blue });
  }
}
function coin(x, y, s, p, seed = 1) { rcircle(x, y, s * .45, { p, fill: C.yellow, seed, w: 5 }); text('¥', x, y + 4, { size: s * .55, alpha: clamp(p * 2 - 1) }); }
function lock(x, y, s, p, seed = 1) {
  rrect(x - s * .38, y - s * .05, s * .76, s * .55, { p, fill: C.btint, seed, w: 5 });
  const pts = []; for (let k = 0; k <= 14; k++) { const a = Math.PI + k / 14 * Math.PI; pts.push([x + Math.cos(a) * s * .24, y - s * .05 + Math.sin(a) * s * .32]); }
  rpath(pts, { p, seed: seed + 4, w: 6 });
}
function person(x, y, s, color, seed, p = 1) {
  rcircle(x, y - s * .55, s * .26, { p, fill: color, seed, w: 4, amp: 1.2 });
  const pts = []; for (let k = 0; k <= 12; k++) { const a = Math.PI + k / 12 * Math.PI; pts.push([x + Math.cos(a) * s * .45, y + s * .45 + Math.sin(a) * s * .5]); }
  rpath(pts, { p, seed: seed + 3, w: 4, amp: 1.2, color: C.ink, fill: color });
}
function face(x, y, s, mood, seed, p = 1) { // mood: 1 happy, 0 neutral, -1 doubtful
  rcircle(x, y, s, { p, fill: '#fff6e8', seed, w: 5 });
  if (p < .6) return;
  rcircle(x - s * .35, y - s * .15, s * .07, { fill: C.ink, seed: seed + 1, w: 3 }); rcircle(x + s * .35, y - s * .15, s * .07, { fill: C.ink, seed: seed + 2, w: 3 });
  const m = []; for (let k = 0; k <= 8; k++) { const u = k / 8 - .5; m.push([x + u * s * .8, y + s * .38 + mood * (0.25 - u * u) * s * .9 + (mood < 0 ? u * s * .25 : 0)]); }
  rpath(m, { seed: seed + 3, w: 5 });
}

// ---------- timeline helpers ----------
function scene(id) { return TL.scenes.find(s => s.id === id); }
function L(sc, i) { return sc.lines[i]; }
function at(sc, i, phrase) { // approximate time a phrase is spoken inside line i
  const l = sc.lines[i]; if (!phrase) return l.start;
  const idx = l.text.indexOf(phrase); return l.start + (l.end - l.start) * Math.max(0, idx) / l.text.length;
}
function title(t, sc, str, color = C.ink) {
  const p = pop(t, sc.start + .05, .5);
  text(str, W / 2, 230, { size: 72, scale: p, color });
  const w = Math.min(760, str.length * 74);
  rline(W / 2 - w / 2, 290, W / 2 + w / 2, 286, { p: ap(t, sc.start + .25, .5), color: C.orange, w: 9, seed: 77 });
}

const S = {};

// ---------- frame ----------
let paperTex = null;
function makePaper() {
  const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
  g.fillStyle = C.paper; g.fillRect(0, 0, W, H);
  const r = rng(99);
  for (let i = 0; i < 9000; i++) { g.fillStyle = `rgba(120,95,60,${r() * .06})`; g.fillRect(r() * W, r() * H, 1 + r() * 2.5, 1 + r() * 2.5); }
  const v = g.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, H * .75); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(90,60,30,.12)');
  g.fillStyle = v; g.fillRect(0, 0, W, H); return c;
}

function captionChunks(line) {
  const parts = line.text.split(/(?<=[，。：？！、])/).map(s => s.trim()).filter(Boolean);
  const out = [];
  for (const p of parts) { const s = p.replace(/[，。：、]$/, ''); if (s.length > 15) { const h = Math.ceil(s.length / 2); out.push(s.slice(0, h), s.slice(h)); } else out.push(s); }
  const total = out.reduce((a, s) => a + s.length, 0); let acc = 0;
  return out.map(s => { const st = line.start + (line.end - line.start) * acc / total; acc += s.length; return { s, start: st, end: line.start + (line.end - line.start) * acc / total }; });
}
const CAPS = TL.scenes.flatMap(s => s.lines.flatMap(captionChunks));

function drawCaption(t) {
  const c = CAPS.find(c => t >= c.start - .05 && t < c.end + .25); if (!c) return;
  ctx.font = `bold 54px ${FONT}`; const w = ctx.measureText(c.s).width + 70;
  const a = ap(t, c.start - .05, .12);
  ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = 'rgba(42,38,34,.88)';
  const x = W / 2 - w / 2, y = 1640, h = 96, r = 22;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.fill();
  text(c.s, W / 2, y + h / 2 + 2, { size: 54, color: '#fff8ec' });
  ctx.restore();
}

window.renderFrame = function (t) {
  BOIL = Math.floor(t * 6);
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
  ctx.drawImage(paperTex, 0, 0);
  for (const sc of TL.scenes) {
    if (t < sc.start - .01 || t >= sc.end) continue;
    const a = Math.min(ap(t, sc.start, .3), 1 - ap(t, sc.end - .28, .28));
    ctx.save(); ctx.globalAlpha = a;
    const z = 1 + (1 - eOut(ap(t, sc.start, .4))) * .03; ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2);
    S[sc.id](t, sc); ctx.restore();
  }
  // progress bar + handle
  const pr = t / TL.duration;
  ctx.fillStyle = 'rgba(42,38,34,.12)'; ctx.fillRect(80, 90, W - 160, 10);
  ctx.fillStyle = C.orange; ctx.fillRect(80, 90, (W - 160) * pr, 10);
  text((window.META && META.header) || '', W / 2, 140, { size: 34, color: C.soft, weight: 'normal' });
  drawCaption(t);
};

window.ready = (async () => {
  await Promise.all(['bold 60px "Hannotate SC"', '60px "Hannotate SC"', 'bold 60px "HanziPen SC"'].map(f => document.fonts.load(f, '测试中文')));
  paperTex = makePaper();
  return { duration: TL.duration, fonts: document.fonts.check('bold 60px "Hannotate SC"', '中') };
})();

// live preview when opened directly in a browser
if (!navigator.webdriver) window.ready.then(() => {
  const q = new URLSearchParams(location.search); let t0 = performance.now() - (+q.get('t') || 0) * 1000;
  const loop = () => { const t = (performance.now() - t0) / 1000 % TL.duration; renderFrame(t); requestAnimationFrame(loop); };
  if (q.has('still')) renderFrame(+q.get('t') || 0); else loop();
});
