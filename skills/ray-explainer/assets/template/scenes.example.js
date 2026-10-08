// Example scenes from the first ray-explainer video (a16z on OpenAI, 2026-10-08).
// Copy patterns, not content. Each scene id must match an id in script.json.
window.META = { header: '一篇读懂 · a16z 谈 OpenAI' };
S.hook = (t, sc) => {
  const l2 = L(sc, 2).start, l3 = L(sc, 3).start;
  // leaderboard reshuffles weekly
  const boardA = 1 - ap(t, l2 - .2, .4);
  if (boardA > 0) {
    ctx.save(); ctx.globalAlpha *= boardA;
    const bx = 170, by = 380, bw = 740, bh = 640;
    rrect(bx, by, bw, bh, { p: ap(t, sc.start, .7), fill: '#fffaf1', seed: 11, w: 6 });
    text('模型排行榜', W / 2, by + 75, { size: 60, alpha: ap(t, sc.start + .3, .3) });
    const week = Math.floor(clamp(t - sc.start - .8, 0, 99) / 1.25);
    text(`第 ${week + 1} 周`, bx + bw - 30, by + 75, { size: 40, align: 'right', color: C.orange, alpha: ap(t, sc.start + .8, .3) });
    const names = ['GPT', 'Claude', 'Gemini', 'Grok'], cols = [C.green, C.orange, C.blue, C.purple];
    const orders = [[0, 1, 2, 3], [1, 0, 2, 3], [2, 1, 0, 3], [0, 2, 1, 3], [3, 0, 2, 1], [1, 3, 0, 2], [2, 0, 3, 1], [0, 1, 3, 2]];
    const ph = clamp(t - sc.start - .8, 0, 99) / 1.25, k = Math.floor(ph), f = eInOut(ap(ph - k, .55, .35));
    const cur = orders[k % orders.length], nxt = orders[(k + 1) % orders.length];
    names.forEach((n, i) => {
      const r0 = cur.indexOf(i), r1 = nxt.indexOf(i), r = lerp(r0, r1, f);
      const y = by + 175 + r * 112, a = ap(t, sc.start + .5 + i * .12, .3);
      ctx.save(); ctx.globalAlpha *= a;
      text(`${Math.round(r) + 1}`, bx + 70, y, { size: 54, color: C.soft });
      rrect(bx + 120, y - 40, (bw - 170) * (1 - r * .16), 80, { fill: cols[i] + '44', color: cols[i], seed: 20 + i, w: 4 });
      text(n, bx + 150, y + 2, { size: 50, align: 'left' });
      if (Math.round(r) === 0) text('👑', bx + bw - 70, y, { size: 50, rot: Math.sin(t * 6) * .12 });
      ctx.restore();
    });
    // one-line model swap
    const l1 = L(sc, 1).start, cp = ap(t, l1, .5);
    if (cp > 0) {
      const cy = 1100;
      rrect(150, cy, 780, 250, { p: cp, fill: '#2e2a26', color: C.ink, seed: 33, w: 5 });
      ctx.save(); ctx.globalAlpha *= clamp(cp * 2 - .5);
      text('client.chat(', 200, cy + 70, { size: 46, align: 'left', color: '#d8cfc2', weight: 'normal' });
      const sw = ap(t, at(sc, 1, '改一行'), .5);
      text('model: "gpt"', 250, cy + 140, { size: 50, align: 'left', color: '#9fd3a8', alpha: 1 - sw });
      text('model: "claude"', 250, cy + 140, { size: 50, align: 'left', color: '#f3b483', alpha: sw });
      text(')', 200, cy + 205, { size: 46, align: 'left', color: '#d8cfc2', weight: 'normal' });
      ctx.restore();
      text('← 改一行就行', 780, cy + 140, { size: 44, color: C.orange, scale: pop(t, at(sc, 1, '改一行')), rot: -.06 });
    }
    ctx.restore();
  }
  // the question
  const qa = ap(t, l2, .4) * (1 - ap(t, l3 - .1, .3) * .65);
  if (t > l2) {
    const qy = lerp(820, 520, eInOut(ap(t, l3 - .1, .6)));
    text('AI 公司', W / 2, qy - 110, { size: 90, scale: pop(t, l2), alpha: qa });
    text('到底靠什么赢？', W / 2, qy + 20, { size: 100, color: C.orange, scale: pop(t, l2 + .5), alpha: qa, rot: Math.sin(t * 3) * .015 });
  }
  if (t > l3) {
    text('David George · a16z', W / 2, 780, { size: 44, color: C.soft, alpha: ap(t, l3, .4) });
    const kp = at(sc, 3, '模型强不强');
    text('模型强不强', W / 2, 1020, { size: 120, scale: pop(t, kp) });
    cross(W / 2, 1020, 190, ap(t, at(sc, 3, '根本'), .5));
    text('根本不是重点', W / 2, 1230, { size: 76, color: C.red, scale: pop(t, at(sc, 3, '根本') + .3), rot: -.04 });
  }
};

S.drucker = (t, sc) => {
  title(t, sc, '德鲁克说');
  // doodle portrait
  const p = ap(t, sc.start + .2, .8);
  face(W / 2, 560, 150, 1, 41, p);
  rcircle(W / 2 - 55, 540, 42, { p: ap(t, sc.start + .8, .4), seed: 45, w: 5 }); rcircle(W / 2 + 55, 540, 42, { p: ap(t, sc.start + .9, .4), seed: 46, w: 5 });
  rline(W / 2 - 13, 540, W / 2 + 13, 540, { p: ap(t, sc.start + 1, .2), seed: 47, w: 5 });
  text('Peter Drucker', W / 2, 760, { size: 44, color: C.soft, alpha: ap(t, sc.start + .8, .4) });
  // the quote
  const l1 = L(sc, 1);
  if (t > l1.start - .3) {
    rrect(110, 870, 860, 470, { p: ap(t, l1.start - .3, .5), fill: C.tint, seed: 51, w: 6 });
    text('“', 170, 940, { size: 160, color: C.orange, alpha: ap(t, l1.start - .1, .3) });
    const tp = ap(t, l1.start, (l1.end - l1.start) * .9);
    text(typed('企业的目的，', tp * 2), W / 2, 1040, { size: 92 });
    text(typed('是创造顾客。', tp * 2 - 1), W / 2, 1190, { size: 104, color: C.orange });
    const up = ap(t, at(sc, 1, '创造顾客') + .4, .5);
    rline(380, 1260, 860, 1255, { p: up, color: C.orange, w: 10, seed: 59 });
  }
  text('—— 五十年前的一句话', W / 2, 1430, { size: 46, color: C.soft, alpha: ap(t, l1.end - .5, .5) });
};

// four levers grid, shared by "levers" and "cross"
const GRID = [
  { k: '新行为', sub: '创造新的用法', icon: bulb, x: 300, y: 650, col: C.tint },
  { k: '分发', sub: '触达更多人', icon: broadcast, x: 780, y: 650, col: C.btint },
  { k: '定价', sub: '把价值收回来', icon: coin, x: 300, y: 1130, col: '#fbf0cc' },
  { k: '切换成本', sub: '让用户走不了', icon: lock, x: 780, y: 1130, col: '#e8e1f6' },
];
function drawGrid(t, show, opts = {}) { // show[i] = appear time
  GRID.forEach((g, i) => {
    const p = ap(t, show[i], .6); if (p <= 0) return;
    const dim = opts.dim ? opts.dim[i] : 0;
    ctx.save(); ctx.globalAlpha *= 1 - dim * .6;
    rrect(g.x - 210, g.y - 210, 420, 420, { p, fill: g.col, seed: 60 + i, w: 6 });
    text(['①', '②', '③', '④'][i], g.x - 165, g.y - 165, { size: 46, color: C.soft, alpha: p });
    g.icon(g.x, g.y - 60, 150, ap(t, show[i] + .2, .6), 70 + i * 5);
    text(g.k, g.x, g.y + 95, { size: 66, scale: pop(t, show[i] + .3) });
    text(g.sub, g.x, g.y + 160, { size: 38, color: C.soft, alpha: ap(t, show[i] + .5, .4) });
    ctx.restore();
  });
}

S.levers = (t, sc) => {
  title(t, sc, '四根杠杆');
  const l1 = 1;
  drawGrid(t, [at(sc, l1, '创造新行为'), at(sc, l1, '扩大分发'), at(sc, l1, '定价赚钱'), at(sc, l1, '切换成本')]);
  text('想做成长久的生意，只有这四根', W / 2, 1480, { size: 46, color: C.soft, alpha: ap(t, sc.start + .6, .5) });
};

S.cross = (t, sc) => {
  title(t, sc, '四根里，两根是断的');
  const l0 = L(sc, 0).start, l1 = L(sc, 1).start, l2 = L(sc, 2).start;
  const dimP = ap(t, l2, .5);
  drawGrid(t, [-9, -9, -9, -9], { dim: [0, 0, dimP, dimP] });
  // ④ crossed: models swap freely
  cross(780, 1130, 150, ap(t, at(sc, 0, '基本没了'), .6), 81);
  if (t > at(sc, 0, '随时能换')) {
    const s = (t * 1.6) % 1, a = ap(t, at(sc, 0, '随时能换'), .3) * (1 - dimP);
    ctx.save(); ctx.globalAlpha *= a;
    rarrow(640, 1390, 920, 1390, { p: 1, color: C.red, w: 5, seed: 85, head: 22 });
    rarrow(920, 1430, 640, 1430, { p: 1, color: C.red, w: 5, seed: 86, head: 22 });
    text('随时能换', 780, 1490, { size: 40, color: C.red, scale: 1 + Math.sin(s * Math.PI * 2) * .03 });
    ctx.restore();
  }
  // ③ crossed: price is a result of scale
  cross(300, 1130, 150, ap(t, at(sc, 1, '它是结果'), .6), 91);
  if (t > at(sc, 1, '规模最大')) text('规模说了算', 300, 1420, { size: 44, color: C.red, scale: pop(t, at(sc, 1, '规模最大')), alpha: 1 - dimP, rot: .04 });
  // ① ② circled
  const cp = ap(t, at(sc, 2, '只剩两根'), .9);
  if (cp > 0) {
    const pts = []; for (let k = 0; k <= 50; k++) { const a = Math.PI + k / 46 * Math.PI * 2; pts.push([540 + Math.cos(a) * 520, 650 + Math.sin(a) * 270]); }
    rpath(pts, { p: cp, color: C.orange, w: 10, seed: 95 });
    text('真正能拉的', W / 2, 1450, { size: 80, color: C.orange, scale: pop(t, at(sc, 2, '只剩两根') + .6) });
  }
};

S.behavior = (t, sc) => {
  title(t, sc, '① 新行为：OpenAI 最会找');
  const l0 = L(sc, 0), l1 = L(sc, 1), l2 = L(sc, 2);
  const outA = 1 - ap(t, l2.start - .2, .4);
  if (outA > 0) {
    ctx.save(); ctx.globalAlpha *= outA;
    // a lone chat box
    const p = ap(t, l0.start + .2, .6);
    rrect(190, 400, 700, 330, { p, fill: '#fffaf1', seed: 101, w: 6 });
    text('ChatGPT', 240, 450, { size: 40, align: 'left', color: C.green, alpha: p });
    rrect(240, 510, 420, 80, { p: ap(t, l0.start + .6, .4), fill: C.btint, seed: 102, w: 4 });
    rrect(420, 615, 420, 80, { p: ap(t, l0.start + .9, .4), fill: C.gtint, seed: 103, w: 4 });
    // doubtful colleagues
    const dp = at(sc, 0, '一个聊天框');
    [[250, 900], [460, 930], [670, 900]].forEach(([x, y], i) => face(x, y, 80, -1, 110 + i * 4, ap(t, dp - .3 + i * .15, .4)));
    text('一个聊天框而已？', W / 2, 1060, { size: 64, color: C.soft, scale: pop(t, dp + .3), rot: -.03 });
    // Thiel's counsel
    if (t > l1.start - .1) {
      const tp = ap(t, l1.start, .5);
      rrect(140, 1150, 800, 300, { p: tp, fill: C.tint, seed: 121, w: 6 });
      text('Peter Thiel → Sam Altman', W / 2, 1210, { size: 40, color: C.soft, alpha: tp });
      text('你们创造了一种', W / 2, 1290, { size: 64, scale: pop(t, at(sc, 1, '你们创造')) });
      text('新顾客', W / 2, 1380, { size: 84, color: C.orange, scale: pop(t, at(sc, 1, '新顾客')) });
    }
    ctx.restore();
  }
  // the pattern: breakthroughs obvious in hindsight
  if (t > l2.start - .2) {
    const items = [['聊天', '后来的'], ['推理', '推理'], ['工具调用', '工具调用'], ['Computer Use', 'Computer']];
    items.forEach(([lab, ph], i) => {
      const s0 = i === 0 ? l2.start : at(sc, 2, ph), y = 470 + i * 230, p = ap(t, s0, .5);
      if (i > 0) rarrow(330, y - 150, 330, y - 70, { p, seed: 130 + i, w: 5, color: C.soft, head: 22 });
      bulb(250, y, 110, p, i === 0 ? C.green : C.yellow, 140 + i * 3);
      text(lab, 360, y, { size: 70, align: 'left', scale: pop(t, s0 + .1) });
    });
    const hp = at(sc, 2, '事后看');
    rrect(140, 1360, 800, 180, { p: ap(t, hp, .5), fill: C.gtint, seed: 150, w: 6 });
    text('事后看：理所当然', W / 2, 1420, { size: 62, scale: pop(t, hp + .2) });
    text('之前：没人做出来', W / 2, 1495, { size: 48, color: C.soft, alpha: ap(t, at(sc, 2, '之前就是'), .4) });
  }
};

S.breadth = (t, sc) => {
  title(t, sc, '为什么总是它先找到？');
  const l0 = L(sc, 0), l1 = L(sc, 1), l2 = L(sc, 2);
  const cols = [C.orange, C.blue, C.green, C.purple, C.yellow, C.red, '#c78b5a', '#5ab3c7'];
  const r = rng(7); const N = 34;
  const ppl = Array.from({ length: N }, (_, i) => ({ x: 120 + r() * 840, y: 420 + r() * 520, c: cols[i % cols.length], s: 42 + r() * 22, d: r() }));
  const fStart = at(sc, 1, '足够杂') - .4, gen = at(sc, 1, '简单的答案');
  // funnel
  const fp = ap(t, at(sc, 1, '从一个具体'), .7);
  rpath([[200, 1000], [880, 1000], [610, 1230], [610, 1310], [470, 1310], [470, 1230], [200, 1000]], { p: fp, seed: 161, w: 6, fill: '#fffaf1' });
  ppl.forEach((q, i) => {
    const a = ap(t, l0.start + q.d * 1.6, .4);
    const m = eInOut(ap(t, fStart + q.d * 1.8, 1.1));
    const x = lerp(q.x, 540 + (q.x - 540) * .05, m), y = lerp(q.y + Math.sin(t * 2 + i) * 6, 1180, m);
    ctx.save(); ctx.globalAlpha *= a * (1 - ap(m, .85, .15)); person(x, y, q.s * (1 - m * .5), q.c, 170 + i, 1); ctx.restore();
  });
  if (t > l0.start) text('用户够杂', W / 2, 960, { size: 56, color: C.blue, alpha: ap(t, at(sc, 0, '够杂'), .4) * (1 - fp) });
  text('具体解法', 540, 1060, { size: 40, color: C.soft, alpha: fp });
  // the general solution pops out
  const gp = ap(t, gen, .6);
  if (gp > 0) {
    const y = 1420, s = 80 * pop(t, gen);
    rpath([[540, y - s], [540 + s, y], [540, y + s], [540 - s, y]], { closed: true, fill: C.yellow, seed: 181, w: 6 });
    text('通用解', 700, y, { size: 64, align: 'left', color: C.orange, scale: pop(t, gen + .2) });
  }
  // the takeaway equation
  if (t > l2.start - .1) {
    ctx.save(); ctx.globalAlpha *= ap(t, l2.start - .1, .4);
    ctx.fillStyle = C.paper + 'ee'; ctx.fillRect(0, 330, W, 1250); ctx.restore();
    const p = ap(t, l2.start, .5);
    rrect(150, 640, 780, 520, { p, fill: C.btint, seed: 191, w: 7 });
    text('通用能力', W / 2, 760, { size: 90, scale: pop(t, at(sc, 2, '通用能力')) });
    rarrow(W / 2, 1000, W / 2, 850, { p: ap(t, at(sc, 2, '取决于'), .5), color: C.orange, w: 9, seed: 195 });
    text('取决于', 700, 925, { size: 44, color: C.orange, alpha: ap(t, at(sc, 2, '取决于'), .4) });
    text('分发', W / 2, 1060, { size: 110, color: C.blue, scale: pop(t, at(sc, 2, '分发')) });
  }
};

S.routes = (t, sc) => {
  title(t, sc, '② 分发：三条路');
  const l0 = L(sc, 0), l1 = L(sc, 1), l2 = L(sc, 2);
  const R = [
    { k: '自有产品', x: 220, ph: '自己做产品', note: '' },
    { k: '合作伙伴', x: 540, ph: '找合作伙伴', note: '最快' },
    { k: '平台', x: 860, ph: '做平台', note: '最慢' },
  ];
  rcircle(540, 470, 80, { p: ap(t, l0.start, .5), fill: C.tint, seed: 201, w: 6 });
  text('模型公司', 540, 472, { size: 38, scale: pop(t, l0.start + .2) });
  const focus = t > l2.start ? 2 : t > l1.start ? 1 : -1;
  R.forEach((r, i) => {
    const s0 = at(sc, 0, r.ph), p = ap(t, s0, .5);
    const dim = focus >= 0 && focus !== i ? .55 : 0;
    ctx.save(); ctx.globalAlpha *= 1 - dim;
    rarrow(540 + (i - 1) * 60, 560, r.x, 700, { p, seed: 210 + i, w: 5, color: C.soft, head: 24 });
    rrect(r.x - 140, 720, 280, 150, { p, fill: ['#fffaf1', C.btint, C.gtint][i], seed: 220 + i, w: 6 });
    text(r.k, r.x, 795, { size: i === 2 ? 64 : 52, scale: pop(t, s0 + .15) });
    ctx.restore();
  });
  // partnership: customers & data walk away to the partner
  if (t > l1.start && t < l2.start + .3) {
    const a = ap(t, l1.start, .4) * (1 - ap(t, l2.start - .1, .4));
    ctx.save(); ctx.globalAlpha *= a;
    text('最快', 540, 680, { size: 40, color: C.green, scale: pop(t, at(sc, 1, '最快')) });
    rrect(330, 1150, 420, 300, { p: ap(t, at(sc, 1, '但顾客'), .5), fill: '#efe7da', seed: 231, w: 6 });
    text('合作方手里', 540, 1400, { size: 46, color: C.red, alpha: ap(t, at(sc, 1, '对方手里'), .4) });
    const m = eInOut(ap(t, at(sc, 1, '顾客'), 1.2));
    person(lerp(480, 470, m), lerp(950, 1270, m), 70, C.orange, 241);
    const dm = eInOut(ap(t, at(sc, 1, '数据'), 1.2));
    rrect(lerp(570, 560, dm), lerp(910, 1230, dm), 90, 70, { fill: C.blue + '55', color: C.blue, seed: 245, w: 4 });
    text('数据', lerp(615, 605, dm), lerp(945, 1265, dm), { size: 30, color: C.blue });
    ctx.restore();
  }
  // platform: a spinning learning loop
  if (t > l2.start) {
    text('最慢', 860, 680, { size: 40, color: C.red, scale: pop(t, at(sc, 2, '最慢')) });
    const lp = ap(t, at(sc, 2, '别人在你上面'), .8), cx = 540, cy = 1210, rr = 220;
    const rot = t * 1.4;
    for (let k = 0; k < 2; k++) {
      const pts = []; for (let j = 0; j <= 20; j++) { const a = rot + k * Math.PI + j / 20 * Math.PI * .8; pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * .62]); }
      rpath(pts, { p: lp, color: C.green, w: 9, seed: 251 + k });
      if (lp > .95) { const a = rot + k * Math.PI + Math.PI * .8, x = cx + Math.cos(a) * rr, y = cy + Math.sin(a) * rr * .62; const ta = a + Math.PI / 2;
        rline(x, y, x - Math.cos(ta - .5) * 30, y - Math.sin(ta - .5) * 30 * .62, { color: C.green, w: 8, seed: 255 + k }); rline(x, y, x - Math.cos(ta + .5) * 30, y - Math.sin(ta + .5) * 30 * .62, { color: C.green, w: 8, seed: 257 + k }); }
    }
    text('用户怎么用', cx - 150, cy - 30, { size: 40, alpha: ap(t, at(sc, 2, '怎么用'), .4) });
    text('反过来教你', cx + 150, cy + 40, { size: 40, alpha: ap(t, at(sc, 2, '反过来'), .4) });
    text('学习回路 = 最难抄', W / 2, 1480, { size: 70, color: C.green, scale: pop(t, at(sc, 2, '这个学习回路')) });
  }
};

S.flip = (t, sc) => {
  title(t, sc, '最反直觉的一点');
  const l0 = L(sc, 0), l1 = L(sc, 1);
  const flipT = at(sc, 0, '因果是反的'), f = eInOut(ap(t, flipT, .9));
  text(f < .5 ? '你以为' : '其实是', W / 2, 520, { size: 56, color: f < .5 ? C.soft : C.orange, scale: 1 - Math.sin(f * Math.PI) * .3 });
  // two boxes swap places
  const yA = lerp(700, 1150, f), yB = lerp(1150, 700, f), xs = Math.sin(f * Math.PI) * 220;
  const box = (x, y, label, col, seed) => { rrect(x - 260, y - 95, 520, 190, { fill: col, seed, w: 7 }); text(label, x, y, { size: 80 }); };
  const p0 = ap(t, l0.start, .5);
  ctx.save(); ctx.globalAlpha *= p0;
  box(540 - xs, yA, '最好的模型', C.btint, 301);
  box(540 + xs, yB, '最好的分发', C.tint, 302);
  rarrow(540, 820, 540, 1030, { p: 1 - Math.sin(f * Math.PI), color: f < .5 ? C.soft : C.orange, w: 9, seed: 305 });
  ctx.restore();
  if (f < .5) text('才能赢', 760, 925, { size: 44, color: C.soft, alpha: p0 * (1 - f * 2) });
  if (f >= 1) text('才会有', 760, 925, { size: 44, color: C.orange, alpha: ap(t, flipT + .9, .3) });
  if (t > l1.start) {
    text('分发 → 模型', W / 2, 1420, { size: 104, color: C.orange, scale: pop(t, at(sc, 1, '是因为')) });
  }
};

S.takeaway = (t, sc) => {
  title(t, sc, '下次换三个问题看');
  const l1 = L(sc, 1), l2 = L(sc, 2);
  const Q = [['它创造了什么', '新行为？', '它创造'], ['它能触达', '多杂的人？', '它能触达'], ['它能从这些人身上', '学到什么？', '它能从']];
  const shrink = eInOut(ap(t, l2.start + .2, .6));
  Q.forEach(([a, b, ph], i) => {
    const s0 = i === 0 ? at(sc, 0, '三个问题') : at(sc, 1, ph);   // first box as soon as「三个问题」is said
    const y = lerp(520 + i * 300, 450 + i * 210, shrink), p = ap(t, s0 - .2, .5);
    rrect(140, y - 110 + shrink * 30, 800, 230 - shrink * 60, { p, fill: '#fffaf1', seed: 401 + i, w: 6 });
    rrect(185, y - 40, 80, 80, { p, seed: 411 + i, w: 6 });
    const ck = ap(t, s0 + .9, .4);
    rpath([[200, y], [225, y + 28], [275, y - 50]], { p: ck, color: C.green, w: 11, seed: 421 + i });
    text(a, 310, y - 30, { size: 44, align: 'left', color: C.soft, alpha: p * (1 - shrink) });
    text(b, 310, lerp(y + 40, y + 5, shrink), { size: 66, align: 'left', scale: pop(t, s0 + .3) });
  });
  if (t > l2.start) {
    const yp = at(sc, 2, '包括你自己');
    text('看任何一家公司都好用', W / 2, 1150, { size: 60, alpha: ap(t, l2.start + .5, .5) });
    text('包括你自己', W / 2, 1320, { size: 120, color: C.orange, scale: pop(t, yp, .6), rot: -.03 });
    rarrow(W / 2 + 280, 1420, W / 2 + 150, 1480, { p: ap(t, yp + .5, .5), color: C.orange, w: 8, seed: 431 });
  }
};
