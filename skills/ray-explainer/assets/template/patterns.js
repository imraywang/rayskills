// ray-explainer kit patterns: the hand-drawn scenes that keep coming back, driven by cues in script.json
// instead of per-film code. A kit scene with "pattern": "<name>" is drawn by P[name](t, sc, def);
// scenes.js S[sceneId] (if any) still runs afterwards, for one-off extras on top.
// def = { data, cues: [{ kind, t (absolute seconds), text, sub, data }] }. Cue "at" is a number (seconds into
// the scene) or { line, phrase, offset } — the same contract as grammar scenes. See references/patterns.md.
const P = {};
const SC_DEF = {};   // sceneId -> resolved def (cached)

function patternDef(sc) {
  if (SC_DEF[sc.id]) return SC_DEF[sc.id];
  const ss = window.SCRIPT && SCRIPT.scenes.find(x => x.id === sc.id);
  if (!ss || !ss.pattern) return null;
  const T = a => typeof a === 'number' ? sc.start + a : a ? at(sc, a.line || 0, a.phrase) + (a.offset || 0) : sc.start;
  const cues = (ss.cues || []).map(q => ({ ...q, t: T(q.at), data: q.data || {} })).sort((a, b) => a.t - b.t);
  return (SC_DEF[sc.id] = { name: ss.pattern, data: ss.data || {}, cues });
}
const cueOf = (def, kind) => def.cues.filter(q => q.kind === kind);
const first = (def, kind) => def.cues.find(q => q.kind === kind);
const tOf = (q, fb = 1e9) => q ? q.t : fb;
const ICON = { bulb: (x, y, s, p, sd) => bulb(x, y, s, p, C.yellow, sd), broadcast, coin, lock,
  person: (x, y, s, p, sd) => person(x, y + s * .1, s * .7, C.orange, sd, p), none: () => {} };
const TINTS = [C.tint, C.btint, '#fbf0cc', '#e8e1f6', C.gtint, '#f6dede'];

// ---------- leaderboard: rankings reshuffle → code card swap → big question → a claim gets crossed out ----------
P.leaderboard = (t, sc, d) => {
  const D = d.data, items = D.items || ['GPT', 'Claude', 'Gemini', 'Grok'], cols = [C.green, C.orange, C.blue, C.purple, C.red];
  const q = first(d, 'question'), st = first(d, 'strike'), cr = first(d, 'cross'), code = first(d, 'code'), sw = first(d, 'swap');
  const t0 = tOf(first(d, 'board'), sc.start), hide = tOf(first(d, 'hide'), tOf(q));
  const boardA = ap(t, t0, .3) * (1 - ap(t, hide - .2, .4));
  if (boardA > 0) {
    ctx.save(); ctx.globalAlpha *= boardA;
    const bx = 170, by = 380, bw = 740, period = D.period || 1.25;
    rrect(bx, by, bw, 175 + items.length * 112 - 15, { p: ap(t, t0, .7), fill: '#fffaf1', seed: 11, w: 6 });
    text(D.title || '排行榜', W / 2, by + 75, { size: 60, alpha: ap(t, t0 + .3, .3) });
    const ph = clamp(t - t0 - .8, 0, 999) / period, k = Math.floor(ph), f = eInOut(ap(ph - k, .55, .35));
    if (D.label !== '') text((D.label || '第 {n} 周').replace('{n}', k + 1), bx + bw - 30, by + 75, { size: 40, align: 'right', color: C.orange, alpha: ap(t, t0 + .8, .3) });
    const perm = s => { const r = rng(1000 + s), o = items.map((_, i) => i); for (let i = o.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [o[i], o[j]] = [o[j], o[i]]; } return o; };
    const cur = k === 0 ? items.map((_, i) => i) : perm(k), nxt = perm(k + 1);
    items.forEach((n, i) => {
      const r = lerp(cur.indexOf(i), nxt.indexOf(i), f), y = by + 175 + r * 112;
      ctx.save(); ctx.globalAlpha *= ap(t, t0 + .5 + i * .12, .3);
      text(`${Math.round(r) + 1}`, bx + 70, y, { size: 54, color: C.soft });
      rrect(bx + 120, y - 40, (bw - 170) * (1 - r * .16), 80, { fill: cols[i % cols.length] + '44', color: cols[i % cols.length], seed: 20 + i, w: 4 });
      text(n, bx + 150, y + 2, { size: 50, align: 'left' });
      if (Math.round(r) === 0) text('👑', bx + bw - 70, y, { size: 50, rot: Math.sin(t * 6) * .12 });
      ctx.restore();
    });
    if (code) {   // a code card where one line changes
      const cy = 380 + 175 + items.length * 112 + 30, cp = ap(t, code.t, .5), cd = code.data, swT = tOf(sw, code.t + 1);
      rrect(150, cy, 780, 250, { p: cp, fill: '#2e2a26', color: C.ink, seed: 33, w: 5 });
      ctx.save(); ctx.globalAlpha *= clamp(cp * 2 - .5);
      const s2 = ap(t, swT, .5);
      text(cd.head || 'client.chat(', 200, cy + 70, { size: 46, align: 'left', color: '#d8cfc2', weight: 'normal' });
      text(cd.from || 'model: "gpt"', 250, cy + 140, { size: 50, align: 'left', color: '#9fd3a8', alpha: 1 - s2 });
      text(cd.to || 'model: "claude"', 250, cy + 140, { size: 50, align: 'left', color: '#f3b483', alpha: s2 });
      text(cd.tail || ')', 200, cy + 205, { size: 46, align: 'left', color: '#d8cfc2', weight: 'normal' });
      ctx.restore();
      if (code.text) text(code.text, 780, cy + 140, { size: 44, color: C.orange, scale: pop(t, swT), rot: -.06 });
    }
    ctx.restore();
  }
  if (q && t > q.t) {   // the question: small line + big orange line; moves up once the claim arrives
    const up = eInOut(ap(t, tOf(st) - .1, .6)), qy = lerp(820, 520, up), qa = ap(t, q.t, .4) * (1 - up * .65);
    text(q.text || '', W / 2, qy - 110, { size: 90, scale: pop(t, q.t), alpha: qa });
    text(q.sub || '', W / 2, qy + 20, { size: 100, color: C.orange, scale: pop(t, q.t + .5), alpha: qa, rot: Math.sin(t * 3) * .015 });
  }
  if (st && t > st.t) {
    if (st.data.who) text(st.data.who, W / 2, 780, { size: 44, color: C.soft, alpha: ap(t, st.t, .4) });
    text(st.text || '', W / 2, 1020, { size: 120, scale: pop(t, st.t) });
    if (cr) { cross(W / 2, 1020, 190, ap(t, cr.t, .5)); if (cr.text) text(cr.text, W / 2, 1230, { size: 76, color: C.red, scale: pop(t, cr.t + .3), rot: -.04 }); }
  }
};

// ---------- quote: doodle portrait + quote card typed out + underline ----------
P.quote = (t, sc, d) => {
  const D = d.data; if (D.title) title(t, sc, D.title);
  const p = ap(t, sc.start + .2, .8);
  face(W / 2, 560, 150, 1, 41, p);
  if (D.glasses !== false) { rcircle(W / 2 - 55, 540, 42, { p: ap(t, sc.start + .8, .4), seed: 45, w: 5 }); rcircle(W / 2 + 55, 540, 42, { p: ap(t, sc.start + .9, .4), seed: 46, w: 5 }); rline(W / 2 - 13, 540, W / 2 + 13, 540, { p: ap(t, sc.start + 1, .2), seed: 47, w: 5 }); }
  if (D.who) text(D.who, W / 2, 760, { size: 44, color: C.soft, alpha: ap(t, sc.start + .8, .4) });
  const q = first(d, 'quote');
  if (q && t > q.t - .3) {
    const lines = D.lines || [q.text || ''], n = lines.length, accent = D.accent ?? n - 1, dur = q.data.dur || 2.4;
    rrect(110, 870, 860, 170 + n * 150, { p: ap(t, q.t - .3, .5), fill: C.tint, seed: 51, w: 6 });
    text('“', 170, 940, { size: 160, color: C.orange, alpha: ap(t, q.t - .1, .3) });
    const tp = ap(t, q.t, dur);
    lines.forEach((ln, i) => text(typed(ln, tp * n - i), W / 2, 1040 + i * 150, { size: i === accent ? 104 : 92, color: i === accent ? C.orange : C.ink }));
    const u = first(d, 'underline');
    if (u) rline(380, 1040 + accent * 150 + 70, 860, 1040 + accent * 150 + 65, { p: ap(t, u.t, .5), color: C.orange, w: 10, seed: 59 });
    const nt = first(d, 'note'); if (nt) text(nt.text, W / 2, 1100 + n * 150 + 80, { size: 46, color: C.soft, alpha: ap(t, nt.t, .5) });
  }
};

// ---------- grid: N cards (icon + title + sub); cross / dim / circle for elimination arguments ----------
function gridLayout(n, colsWanted) {
  const cols = colsWanted || (n === 4 ? 2 : Math.min(n, 3)), rows = Math.ceil(n / cols);
  const gap = 60, cw = Math.min(420, (W - 120 - (cols - 1) * gap) / cols), ch = Math.min(cw, (1080 - (rows - 1) * gap) / rows);
  const top = 380 + (1120 - (rows * ch + (rows - 1) * gap)) / 2;
  return Array.from({ length: n }, (_, i) => { const r = Math.floor(i / cols), c = i % cols, inRow = Math.min(cols, n - r * cols);
    const x0 = (W - (inRow * cw + (inRow - 1) * gap)) / 2; return { x: x0 + c * (cw + gap) + cw / 2, y: top + r * (ch + gap) + ch / 2, w: cw, h: ch }; });
}
P.grid = (t, sc, d) => {
  const D = d.data, cards = D.cards || [], L0 = gridLayout(cards.length, D.cols), k = L0[0] ? L0[0].w / 420 : 1;
  if (D.title) title(t, sc, D.title);
  const shows = cueOf(d, 'show'), showT = i => { const q = shows.find(q => q.data.index == null || q.data.index === i || (Array.isArray(q.data.index) && q.data.index.includes(i))); return q ? q.t : -1e9; };
  const dimT = i => { const q = cueOf(d, 'dim').find(q => [].concat(q.data.index).includes(i)); return q ? q.t : 1e9; };
  cards.forEach((g, i) => {
    const o = L0[i], s0 = showT(i), p = ap(t, s0, .6); if (p <= 0) return;
    ctx.save(); ctx.globalAlpha *= 1 - ap(t, dimT(i), .5) * .6;
    rrect(o.x - o.w / 2, o.y - o.h / 2, o.w, o.h, { p, fill: g.color || TINTS[i % TINTS.length], seed: 60 + i, w: 6 });
    text('①②③④⑤⑥⑦⑧⑨'[i] || '', o.x - o.w / 2 + 45 * k, o.y - o.h / 2 + 45 * k, { size: 46 * k, color: C.soft, alpha: p });
    (ICON[g.icon] || ICON.none)(o.x, o.y - 60 * k, 150 * k, ap(t, s0 + .2, .6), 70 + i * 5);
    text(g.title || '', o.x, o.y + 95 * k, { size: 66 * k, scale: pop(t, s0 + .3) });
    if (g.sub) text(g.sub, o.x, o.y + 160 * k, { size: 38 * k, color: C.soft, alpha: ap(t, s0 + .5, .4) });
    ctx.restore();
  });
  const firstDim = Math.min(...cueOf(d, 'dim').map(q => q.t), 1e9);
  cueOf(d, 'cross').forEach((q, j) => { const o = L0[q.data.index]; if (!o) return;
    cross(o.x, o.y, o.w * .36, ap(t, q.t, .6), 81 + j * 10);
    if (q.text) { const na = ap(t, q.t + .3, .3) * (1 - ap(t, firstDim, .5));
      if (q.data.arrows) { ctx.save(); ctx.globalAlpha *= na; rarrow(o.x - 140, o.y + o.h / 2 + 50, o.x + 140, o.y + o.h / 2 + 50, { color: C.red, w: 5, seed: 85 + j, head: 22 }); rarrow(o.x + 140, o.y + o.h / 2 + 90, o.x - 140, o.y + o.h / 2 + 90, { color: C.red, w: 5, seed: 86 + j, head: 22 }); ctx.restore(); }
      text(q.text, o.x, o.y + o.h / 2 + (q.data.arrows ? 150 : 70), { size: 44, color: C.red, scale: pop(t, q.t + .3), alpha: 1 - ap(t, firstDim, .5), rot: .04 }); } });
  cueOf(d, 'circle').forEach((q, j) => { const idx = [].concat(q.data.index ?? [0]), os = idx.map(i => L0[i]).filter(Boolean); if (!os.length) return;
    const x0 = Math.min(...os.map(o => o.x - o.w / 2)), x1 = Math.max(...os.map(o => o.x + o.w / 2)), y0 = Math.min(...os.map(o => o.y - o.h / 2)), y1 = Math.max(...os.map(o => o.y + o.h / 2));
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, rx = (x1 - x0) / 2 * 1.08 + 30, ry = (y1 - y0) / 2 * 1.15 + 40, pts = [];
    for (let k2 = 0; k2 <= 50; k2++) { const a = Math.PI + k2 / 46 * Math.PI * 2; pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]); }
    rpath(pts, { p: ap(t, q.t, .9), color: C.orange, w: 10, seed: 95 + j });
    if (q.text) text(q.text, W / 2, 1450, { size: 80, color: C.orange, scale: pop(t, q.t + .6) }); });
  cueOf(d, 'note').forEach(q => text(q.text || '', W / 2, 1480, { size: 46, color: C.soft, alpha: ap(t, q.t, .5) }));
};

// ---------- story: product sketch + doubtful faces + a quote bubble, then a lit-up timeline of steps ----------
P.story = (t, sc, d) => {
  const D = d.data; if (D.title) title(t, sc, D.title);
  const steps = cueOf(d, 'step'), sum = first(d, 'summary'), out = steps.length ? 1 - ap(t, steps[0].t - .2, .4) : 1;
  if (out > 0) {
    ctx.save(); ctx.globalAlpha *= out;
    const ch = first(d, 'chat');
    if (ch) { const p = ap(t, ch.t, .6);
      rrect(190, 400, 700, 330, { p, fill: '#fffaf1', seed: 101, w: 6 });
      text(ch.text || 'ChatGPT', 240, 450, { size: 40, align: 'left', color: C.green, alpha: p });
      rrect(240, 510, 420, 80, { p: ap(t, ch.t + .4, .4), fill: C.btint, seed: 102, w: 4 }); rrect(420, 615, 420, 80, { p: ap(t, ch.t + .7, .4), fill: C.gtint, seed: 103, w: 4 }); }
    const dq = first(d, 'doubt');
    if (dq) { [[250, 900], [460, 930], [670, 900]].forEach(([x, y], i) => face(x, y, 80, -1, 110 + i * 4, ap(t, dq.t - .3 + i * .15, .4)));
      text(dq.text || '', W / 2, 1060, { size: 64, color: C.soft, scale: pop(t, dq.t + .3), rot: -.03 }); }
    const b = first(d, 'bubble');
    if (b && t > b.t - .1) { const tp = ap(t, b.t, .5);
      rrect(140, 1150, 800, 300, { p: tp, fill: C.tint, seed: 121, w: 6 });
      if (b.data.who) text(b.data.who, W / 2, 1210, { size: 40, color: C.soft, alpha: tp });
      text(b.text || '', W / 2, 1290, { size: 64, scale: pop(t, b.t) });
      if (b.sub) text(b.sub, W / 2, 1380, { size: 84, color: C.orange, scale: pop(t, tOf(cueOf(d, 'bubble')[0]) + (b.data.subDelay ?? .8)) }); }
    ctx.restore();
  }
  const gap = Math.min(230, 860 / Math.max(1, steps.length));
  steps.forEach((q, i) => { const y = 470 + i * gap, p = ap(t, q.t, .5);
    if (i > 0) rarrow(330, y - gap + 80, 330, y - 70, { p, seed: 130 + i, w: 5, color: C.soft, head: 22 });
    bulb(250, y, 110, p, q.data.color ? C[q.data.color] || q.data.color : (i === 0 ? C.green : C.yellow), 140 + i * 3);
    text(q.text || '', 360, y, { size: 70, align: 'left', scale: pop(t, q.t + .1) }); });
  if (sum) { rrect(140, 1360, 800, 180, { p: ap(t, sum.t, .5), fill: C.gtint, seed: 150, w: 6 });
    text(sum.text || '', W / 2, 1420, { size: 62, scale: pop(t, sum.t + .2) });
    if (sum.sub) text(sum.sub, W / 2, 1495, { size: 48, color: C.soft, alpha: ap(t, sum.t + (sum.data.subDelay ?? 1.2), .4) }); }
};

// ---------- funnel: a diverse crowd pours into a funnel and comes out as one answer; optional formula card ----------
P.funnel = (t, sc, d) => {
  const D = d.data; if (D.title) title(t, sc, D.title);
  const cols = [C.orange, C.blue, C.green, C.purple, C.yellow, C.red, '#c78b5a', '#5ab3c7'], r = rng(7), N = D.crowd || 34;
  const ppl = Array.from({ length: N }, (_, i) => ({ x: 120 + r() * 840, y: 420 + r() * 520, c: cols[i % cols.length], s: 42 + r() * 22, d: r() }));
  const cr = tOf(first(d, 'crowd'), sc.start), fn = first(d, 'funnel'), po = first(d, 'pour'), re = first(d, 'result'), fo = first(d, 'formula');
  const fp = ap(t, tOf(fn), .7);
  rpath([[200, 1000], [880, 1000], [610, 1230], [610, 1310], [470, 1310], [470, 1230], [200, 1000]], { p: fp, seed: 161, w: 6, fill: '#fffaf1' });
  ppl.forEach((q, i) => { const a = ap(t, cr + q.d * 1.6, .4), m = eInOut(ap(t, tOf(po) + q.d * 1.8, 1.1));
    const x = lerp(q.x, 540 + (q.x - 540) * .05, m), y = lerp(q.y + Math.sin(t * 2 + i) * 6, 1180, m);
    ctx.save(); ctx.globalAlpha *= a * (1 - ap(m, .85, .15)); person(x, y, q.s * (1 - m * .5), q.c, 170 + i, 1); ctx.restore(); });
  const lab = first(d, 'crowd'); if (lab && lab.text) text(lab.text, W / 2, 960, { size: 56, color: C.blue, alpha: ap(t, lab.t + .3, .4) * (1 - fp) });
  if (fn && fn.text) text(fn.text, 540, 1060, { size: 40, color: C.soft, alpha: fp });
  if (re) { const gp = ap(t, re.t, .6); if (gp > 0) { const y = 1420, s = 80 * pop(t, re.t);
    rpath([[540, y - s], [540 + s, y], [540, y + s], [540 - s, y]], { closed: true, fill: C.yellow, seed: 181, w: 6 });
    text(re.text || '', 700, y, { size: 64, align: 'left', color: C.orange, scale: pop(t, re.t + .2) }); } }
  if (fo && t > fo.t - .1) {
    ctx.save(); ctx.globalAlpha *= ap(t, fo.t - .1, .4); ctx.fillStyle = C.paper + 'ee'; ctx.fillRect(0, 330, W, 1250); ctx.restore();
    const vt = fo.t + (fo.data.verbDelay ?? .8), bt = fo.t + (fo.data.bottomDelay ?? 1.4);
    rrect(150, 640, 780, 520, { p: ap(t, fo.t, .5), fill: C.btint, seed: 191, w: 7 });
    text(fo.text || '', W / 2, 760, { size: 90, scale: pop(t, fo.t + .1) });
    rarrow(W / 2, 1000, W / 2, 850, { p: ap(t, vt, .5), color: C.orange, w: 9, seed: 195 });
    if (fo.data.verb) text(fo.data.verb, 700, 925, { size: 44, color: C.orange, alpha: ap(t, vt, .4) });
    text(fo.sub || '', W / 2, 1060, { size: 110, color: C.blue, scale: pop(t, bt) });
  }
};

// ---------- paths: one root branching into N options; focus one; "loss" (things walk away) or "loop" (learning loop) ----------
P.paths = (t, sc, d) => {
  const D = d.data, ps = D.paths || [], n = ps.length, sp = Math.min(320, (W - 160) / Math.max(1, n)), bw = Math.min(280, sp - 40);
  if (D.title) title(t, sc, D.title);
  const xs = ps.map((_, i) => W / 2 + (i - (n - 1) / 2) * sp), rt = tOf(first(d, 'root'), sc.start);
  rcircle(540, 470, 80, { p: ap(t, rt, .5), fill: C.tint, seed: 201, w: 6 });
  text(D.root || '', 540, 472, { size: 38, scale: pop(t, rt + .2) });
  const foc = cueOf(d, 'focus').filter(q => q.t <= t).pop(), focus = foc ? foc.data.index : -1, ends = [...cueOf(d, 'focus').map(q => q.t), sc.end];
  ps.forEach((g, i) => { const pq = cueOf(d, 'path').find(q => q.data.index === i), s0 = tOf(pq, rt + .4 + i * .4), p = ap(t, s0, .5);
    ctx.save(); ctx.globalAlpha *= 1 - (focus >= 0 && focus !== i ? .55 : 0);
    rarrow(540 + (i - (n - 1) / 2) * 60, 560, xs[i], 700, { p, seed: 210 + i, w: 5, color: C.soft, head: 24 });
    rrect(xs[i] - bw / 2, 720, bw, 150, { p, fill: g.color || ['#fffaf1', C.btint, C.gtint, C.tint][i % 4], seed: 220 + i, w: 6 });
    text(g.title || '', xs[i], 795, { size: (g.title || '').length > 3 ? 52 : 64, scale: pop(t, s0 + .15) }); ctx.restore(); });
  cueOf(d, 'note').forEach(q => { const i = q.data.index ?? 0; text(q.text || '', xs[i], 680, { size: 40, color: q.data.color ? C[q.data.color] || q.data.color : C.orange, scale: pop(t, q.t) }); });
  const lo = first(d, 'loss');
  if (lo && t > lo.t) { const end = ends.find(e => e > lo.t + .1) || sc.end, a = ap(t, lo.t, .4) * (1 - ap(t, end - .1, .4)), i = lo.data.index ?? Math.max(0, focus), x = xs[i] ?? 540;
    ctx.save(); ctx.globalAlpha *= a;
    rrect(x - 210, 1150, 420, 300, { p: ap(t, lo.t + .3, .5), fill: '#efe7da', seed: 231, w: 6 });
    if (lo.text) text(lo.text, x, 1400, { size: 46, color: C.red, alpha: ap(t, lo.t + 1.2, .4) });
    const m = eInOut(ap(t, lo.t + .2, 1.2)), dm = eInOut(ap(t, lo.t + .6, 1.2));
    person(lerp(x - 60, x - 70, m), lerp(950, 1270, m), 70, C.orange, 241);
    rrect(lerp(x + 30, x + 20, dm), lerp(910, 1230, dm), 90, 70, { fill: C.blue + '55', color: C.blue, seed: 245, w: 4 });
    text(lo.sub || '数据', lerp(x + 75, x + 65, dm), lerp(945, 1265, dm), { size: 30, color: C.blue });
    ctx.restore(); }
  const lp0 = first(d, 'loop');
  if (lp0 && t > lp0.t) { const lp = ap(t, lp0.t, .8), cx = 540, cy = 1210, rr = 220, rot = t * 1.4;
    for (let k = 0; k < 2; k++) { const pts = []; for (let j = 0; j <= 20; j++) { const a = rot + k * Math.PI + j / 20 * Math.PI * .8; pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * .62]); }
      rpath(pts, { p: lp, color: C.green, w: 9, seed: 251 + k });
      if (lp > .95) { const a = rot + k * Math.PI + Math.PI * .8, x = cx + Math.cos(a) * rr, y = cy + Math.sin(a) * rr * .62, ta = a + Math.PI / 2;
        rline(x, y, x - Math.cos(ta - .5) * 30, y - Math.sin(ta - .5) * 30 * .62, { color: C.green, w: 8, seed: 255 + k }); rline(x, y, x - Math.cos(ta + .5) * 30, y - Math.sin(ta + .5) * 30 * .62, { color: C.green, w: 8, seed: 257 + k }); } }
    if (lp0.text) text(lp0.text, cx - 150, cy - 30, { size: 40, alpha: ap(t, lp0.t + .5, .4) });
    if (lp0.sub) text(lp0.sub, cx + 150, cy + 40, { size: 40, alpha: ap(t, lp0.t + 1.2, .4) }); }
  cueOf(d, 'punch').forEach(q => text(q.text || '', W / 2, 1480, { size: 70, color: C.green, scale: pop(t, q.t) }));
};

// ---------- swap: two boxes with an arrow; they trade places ("you think A→B; actually B→A") ----------
P.swap = (t, sc, d) => {
  const D = d.data; if (D.title) title(t, sc, D.title);
  const sh = tOf(first(d, 'show'), sc.start), fl = first(d, 'flip'), f = eInOut(ap(t, tOf(fl), .9));
  text(f < .5 ? (D.before || '你以为') : (D.after || '其实是'), W / 2, 520, { size: 56, color: f < .5 ? C.soft : C.orange, scale: 1 - Math.sin(f * Math.PI) * .3, alpha: ap(t, sh, .4) });
  const yA = lerp(700, 1150, f), yB = lerp(1150, 700, f), xs = Math.sin(f * Math.PI) * 220;
  const box = (x, y, label, col, seed) => { rrect(x - 260, y - 95, 520, 190, { fill: col, seed, w: 7 }); text(label, x, y, { size: label.length > 6 ? 64 : 80 }); };
  const p0 = ap(t, sh, .5);
  ctx.save(); ctx.globalAlpha *= p0;
  box(540 - xs, yA, D.a || 'A', C.btint, 301); box(540 + xs, yB, D.b || 'B', C.tint, 302);
  rarrow(540, 820, 540, 1030, { p: 1 - Math.sin(f * Math.PI), color: f < .5 ? C.soft : C.orange, w: 9, seed: 305 });
  ctx.restore();
  if (f < .5 && D.arrowBefore) text(D.arrowBefore, 760, 925, { size: 44, color: C.soft, alpha: p0 * (1 - f * 2) });
  if (f >= 1 && D.arrowAfter) text(D.arrowAfter, 760, 925, { size: 44, color: C.orange, alpha: ap(t, tOf(fl) + .9, .3) });
  cueOf(d, 'punch').forEach(q => text(q.text || '', W / 2, 1420, { size: 104, color: C.orange, scale: pop(t, q.t) }));
};

// ---------- checklist: question boxes tick one by one, then shrink up for a closing line ----------
P.checklist = (t, sc, d) => {
  const D = d.data; if (D.title) title(t, sc, D.title);
  const items = cueOf(d, 'item'), fin = first(d, 'final'), n = items.length, shrink = eInOut(ap(t, tOf(fin) + .2, .6));
  const g0 = Math.min(300, 1000 / Math.max(1, n)), g1 = Math.min(210, 700 / Math.max(1, n));
  items.forEach((q, i) => { const s0 = q.t, y = lerp(520 + i * g0, 450 + i * g1, shrink), p = ap(t, s0 - .2, .5);
    rrect(140, y - 110 + shrink * 30, 800, 230 - shrink * 60, { p, fill: '#fffaf1', seed: 401 + i, w: 6 });
    rrect(185, y - 40, 80, 80, { p, seed: 411 + i, w: 6 });
    rpath([[200, y], [225, y + 28], [275, y - 50]], { p: ap(t, s0 + (q.data.checkDelay ?? .9), .4), color: C.green, w: 11, seed: 421 + i });
    if (q.sub) text(q.sub, 310, y - 30, { size: 44, align: 'left', color: C.soft, alpha: p * (1 - shrink) });
    text(q.text || '', 310, q.sub ? lerp(y + 40, y + 5, shrink) : y, { size: 66, align: 'left', scale: pop(t, s0 + .3) }); });
  if (fin && t > fin.t) {
    const big = fin.t + (fin.data.bigDelay ?? 2.5);
    if (fin.sub) text(fin.sub, W / 2, 1150, { size: 60, alpha: ap(t, fin.t + .5, .5) });
    text(fin.text || '', W / 2, 1320, { size: 120, color: C.orange, scale: pop(t, big, .6), rot: -.03 });
    rarrow(W / 2 + 280, 1420, W / 2 + 150, 1480, { p: ap(t, big + .5, .5), color: C.orange, w: 8, seed: 431 });
  }
};
