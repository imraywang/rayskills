// Mixed-mode renderer. Each scene is drawn either by ray-explainer's own kit (scenes.js) or by a
// huashu-art-motion explainer grammar clip (script.json scene has "grammar"); every frame gets the shared
// caption/progress overlay; headless Chrome seeks frame by frame and FFmpeg stitches frames + narration.
// usage:
//   node render.js <project> stills 3,12.5,40      -> <project>/stills/tNNN.N.jpg
//   node render.js <project> sheet [N]             -> N evenly spaced stills tiled into <project>/contact.jpg
//   node render.js <project> video [fps]           -> <project>/out.mp4
//   node render.js <project> gate [file.mp4]       -> film_gate on an existing render (video mode runs it automatically), writes gate.json
//   node render.js <project> serve                 -> live preview URL (kit scenes; grammar scenes show via stills)
// env RX_CLEAN=1: frames without captions / progress bar (publish.py uses it for the cover)
const path = require('path'), fs = require('fs'), http = require('http'), os = require('os');
const { spawn, execFileSync } = require('child_process');
// puppeteer-core lives outside the skill dir (installed by check_setup.sh) so the skill stays dependency-free
const DEPS = process.env.RAY_EXPLAINER_DEPS || path.join(os.homedir(), '.cache', 'ray-explainer');
let puppeteer;
try { puppeteer = require('puppeteer-core'); } catch { puppeteer = require(require.resolve('puppeteer-core', { paths: [DEPS] })); }

const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const HUASHU = path.resolve(__dirname, '..', 'assets', 'huashu');
const TEMPLATE = path.resolve(__dirname, '..', 'assets', 'template');
const [projArg, mode = 'sheet', arg] = process.argv.slice(2);
if (!projArg) { console.error('usage: node render.js <project> stills|sheet|video|gate|serve [arg]'); process.exit(2); }
const PROJ = path.resolve(projArg);
const SCRIPT = JSON.parse(fs.readFileSync(path.join(PROJ, 'script.json')));
const TL = JSON.parse(fs.readFileSync(path.join(PROJ, 'timeline.json')));
const W = 1080, H = 1920, SAFE = { top: 290, bottom: 380 };   // overlay: progress/header y 200–290, captions y 1560–1656; above 200 / below 1680 the phone UI covers the frame
// digital host (host.py wrote host/plan.json): captions move up to ~1470 and the corner presenter takes the bottom, so grammar clips keep clear of y>1440
if (fs.existsSync(path.join(PROJ, 'host', 'plan.json'))) SAFE.bottom = 480;

// ---------- theme: script.json "theme" → one palette for kit scenes and grammar clips ----------
// a huashu palette name (paper poster ink navy bauhaus snow wood chalk), "ray" (the kit's own colours), "ray-ip" (Ray's IP look:
// black / white / grey + ink green #054C4C, see references/ip-style.md), {name, <keys to override>}, or all 6 keys.
// Omitted → kit and every grammar keep their own default colours (old projects render unchanged).
// Besides the 6 palette keys a theme may carry: kit {green red yellow purple grain} (the kit's semantic colours / paper grain rgb),
// overlay {bar caption captionInk sigBar}, sig {6 keys + kit} (the palette of signature scenes: scenes with "sig" in script.json).
const RAY_PALETTE = { bg: '#f7f0e3', surface: '#fffaf1', ink: '#2a2622', sub: '#8a7f72', accent: '#e8743b', accent2: '#3d7fd9' };
const RAY_IP = { bg: '#f3f3f0', surface: '#ffffff', ink: '#111111', sub: '#6e6e6e', accent: '#054c4c', accent2: '#8c8c8c',
  kit: { green: '#054c4c', red: '#111111', yellow: '#d4d4d0', purple: '#8a8a8a', grain: '0,0,0' },
  overlay: { bar: '#111111', caption: 'rgba(17,17,17,.88)', captionInk: '#f3f3f0', sigBar: '#f3f3f0' },
  sig: { bg: '#054c4c', surface: '#0d5f5e', ink: '#f3f3f0', sub: '#9cc2bf', accent: '#ffffff', accent2: '#7fb0ac',
    kit: { green: '#9cc2bf', red: '#ffffff', yellow: '#d4d4d0', purple: '#7fb0ac', grain: '255,255,255' } } };
const PAL_KEYS = ['bg', 'surface', 'ink', 'sub', 'accent', 'accent2'];
const hsv = h => { const [r, g, b] = [1, 3, 5].map(i => parseInt(h.substr(i, 2), 16) / 255), mx = Math.max(r, g, b), d = mx - Math.min(r, g, b);
  const hue = d === 0 ? 0 : mx === r ? 60 * (((g - b) / d) % 6) : mx === g ? 60 * ((b - r) / d + 2) : 60 * ((r - g) / d + 4); return [(hue + 360) % 360, mx ? d / mx : 0]; };
function six(o, where, avail) {
  const bad = PAL_KEYS.filter(k => !/^#[0-9a-f]{6}$/i.test(String(o[k] || '')));
  if (bad.length) throw new Error(`script.json ${where} 缺或写错 ${bad.join(' ')}（每个键写 #rrggbb；或写 name 用一套色板补齐）。可用：${avail}`);
  for (const k of ['bg', 'surface', 'accent']) { const [h, sat] = hsv(o[k]); if (h >= 225 && h <= 300 && sat >= .3) console.warn(`WARN ${where}.${k}=${o[k]} 落在蓝紫区（色相 225°–300°），film_gate 会量出蓝紫底`); }
  return Object.fromEntries(PAL_KEYS.map(k => [k, o[k].toLowerCase()]));
}
function resolveTheme(th) {
  if (th == null) return null;
  const sb = { window: {} }; require('vm').runInNewContext(fs.readFileSync(path.join(HUASHU, 'lib', 'palettes.js'), 'utf8'), sb);
  const named = { ray: RAY_PALETTE, 'ray-ip': RAY_IP, ...sb.window.PALETTES }, avail = Object.keys(named).join(' / ');
  const name = typeof th === 'string' ? th : th.name;
  if (name != null && !named[name]) throw new Error(`script.json theme「${name}」不是色板名。可用：${avail}`);
  const base = name != null ? named[name] : {}, over = typeof th === 'object' ? th : {};
  const out = { ...base, ...over, kit: { ...(base.kit || {}), ...(over.kit || {}) }, overlay: { ...(base.overlay || {}), ...(over.overlay || {}) } };
  const sig = over.sig || base.sig ? { ...(base.sig || {}), ...(over.sig || {}) } : null;
  return { pal: six(out, 'theme', avail), kit: out.kit, overlay: out.overlay, sig: sig ? { pal: six(sig, 'theme.sig', avail), kit: sig.kit || {} } : null };
}
{ const st = [...new Set(SCRIPT.scenes.map(s => s.grammar || 'kit'))];   // one film, one style (Ray, 2026-10-13)
  if (st.length > 1 && !SCRIPT.mix) console.warn(`WARN 一期只用一种画法：这条片子混了 ${st.length} 种（${st.join(' / ')}），见 grammars.md「一期一种画法」；确实要混，script.json 写 "mix": true`); }
const THEME_ALL = resolveTheme(SCRIPT.theme), THEME = THEME_ALL && THEME_ALL.pal;
// signature scenes (script.json scene "sig": true): the opening / closing moments, drawn in the theme's sig palette (ray-ip: ink green).
// Ray's avatar is not part of the sig scene: it is the corner presenter (host with "big": [], free), present through the whole film.
const SIG = SCRIPT.scenes.filter(s => s.sig).map(s => {
  const tsc = TL.scenes.find(x => x.id === s.id); if (!tsc) throw new Error(`scene ${s.id}: sig scene missing from timeline.json`);
  return { id: s.id, start: tsc.start, end: tsc.end };
});
if (SIG.length && !(THEME_ALL && THEME_ALL.sig)) console.warn('WARN script.json 有 sig 场景，但 theme 没有 sig 色板（用 "ray-ip"）——sig 不起作用');
const PAGE_INIT = (THEME_ALL ? `window.THEME=${JSON.stringify({ ...THEME_ALL.pal, kit: THEME_ALL.kit, overlay: THEME_ALL.overlay, sig: THEME_ALL.sig })};` : '') +
  (SIG.length ? `window.SIG=${JSON.stringify(SIG)};` : '');

// ---------- static server: project at /, vendored huashu engine at /huashu/, overlay.js always from the skill ----------
// overlay.js (captions, progress bar, header, digital host) is pipeline infrastructure, not per-film content: it must match
// this render.js (RXO.prep / ready / draw), so it is served from the skill even when an old project still has its own copy
const MIME = { '.webp': 'image/webp', '.js': 'text/javascript', '.html': 'text/html', '.woff': 'font/woff', '.woff2': 'font/woff2', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.wav': 'audio/wav' };
function serve() {
  const srv = http.createServer((req, res) => {
    let u = decodeURIComponent(req.url.split('?')[0]); let base = PROJ;
    if (u.startsWith('/huashu/')) { base = HUASHU; u = u.slice(7); }
    else if (u === '/overlay.js') { base = TEMPLATE; }
    const f = path.join(base, path.normalize(u));
    if (!f.startsWith(base) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
  });
  return new Promise(r => srv.listen(+process.env.PORT || 0, '127.0.0.1', () => r(srv)));
}

// ---------- film gate (scripts/film_gate.py, from huashu-art-motion): report only, never blocks the render ----------
// measures how much of the film moves inside the shot, mid-film blank frames and blue/purple share; writes <project>/gate.json
function gate(mp4) {
  const L = { red: '红', yellow: '黄', green: '绿', pass: '绿' };
  let d;
  try {
    const raw = execFileSync('uv', ['run', '-q', path.join(__dirname, 'film_gate.py'), mp4, '--no-template', '--sub-band', '0.2', '--json'],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], maxBuffer: 64 << 20 });
    d = JSON.parse(raw);
  } catch (e) {
    if (e.code === 'ENOENT') return console.log('gate: 没装 uv，跳过 film_gate');
    const out = String(e.stdout || ''); try { d = JSON.parse(out); } catch { return console.log('gate: film_gate 没跑成 —', String(e.stderr || e.message).trim().split('\n').pop()); }
  }
  fs.writeFileSync(path.join(PROJ, 'gate.json'), JSON.stringify(d, null, 1));
  const lt = k => L[d.lights[k]] || '—';
  console.log(`gate: [${L[d.verdict] || d.verdict}] 快动帧占比 ${d.fast_ratio}（${lt('fast_ratio')}，花叔的红线 0.035、认可片最低 0.068）· ` +
    `中段空画面 ${d.blank_run_s}s（${lt('blank_run_s')}）· 蓝紫占比 ${d.blue_purple_share}（${lt('blue_purple_share')}）· 推近 ${d.push_in_per_min} 次/分钟`);
  console.log(`gate: 最差 30 秒 ${d.worst_window_start_s}–${d.worst_window_start_s + d.worst_window_len_s}s（快动帧占比 ${d.fast_ratio_worst_window}）· 最长无事件 ${d.max_event_gap_s}s` +
    ((d.blank_runs_s || []).length ? ` · 空画面在 ${d.blank_runs_s.map(r => Array.isArray(r) ? r.join('–') : r).join(', ')}s` : ''));
  if (d.verdict === 'red') console.log('gate: 红灯只是提醒：用正常速度看一遍最差那 30 秒，再决定要不要补镜头内运动（见 SKILL.md 第 6 步）');
}

// ---------- cue timing: number (seconds into the scene) or {line, phrase, offset} on Whisper per-char timing ----------
function cueTime(at, tsc, where) {
  if (typeof at === 'number') return at;
  const l = tsc.lines[at.line]; if (!l) throw new Error(`${where}: line ${at.line} does not exist`);
  let t = l.start;
  if (at.phrase) {
    const i = l.text.indexOf(at.phrase);
    if (i < 0) throw new Error(`${where}: phrase "${at.phrase}" not found in line ${at.line}: ${l.text}`);
    t = l.chars && l.chars.length === l.text.length ? l.chars[i] : l.start + (l.end - l.start) * i / l.text.length;
  }
  return Math.max(0, +(t - tsc.start + (at.offset || 0)).toFixed(3));
}
function specFor(ssc, tsc, fps) {
  const cues = (ssc.cues || []).map((q, k) => ({ ...q, at: cueTime(q.at ?? 0, tsc, `scene ${ssc.id} cue ${k}`) }));
  for (const q of cues) if (q.video) {   // 视频＝项目里的帧目录（scripts/video_frames.sh 生成 0001.jpg…），帧数在这里数好写进 spec
    const dir = path.join(PROJ, q.video.dir.replace(/^\//, ''));
    if (!fs.existsSync(dir)) throw new Error(`scene ${ssc.id}: video dir not found: ${q.video.dir}`);
    q.video = { ...q.video, count: fs.readdirSync(dir).filter(f => /^\d{4}\.jpg$/.test(f)).length };
  }
  return { grammar: ssc.grammar, duration: +(tsc.end - tsc.start).toFixed(3), fps, width: W, height: H,
    safe: { ...SAFE, ...(ssc.safe || {}) }, ...(ssc.data ? { data: ssc.data } : {}), ...(ssc.theme ? { theme: ssc.theme } : ssc.sig && THEME_ALL && THEME_ALL.sig ? { theme: THEME_ALL.sig.pal } : THEME ? { theme: THEME } : {}), cues };
}

(async () => {
  if (mode === 'gate') return gate(path.join(PROJ, arg || 'out.mp4'));
  for (const s of SCRIPT.scenes) if (s.grammar && !fs.existsSync(path.join(HUASHU, 'clips', s.grammar + '.js'))) throw new Error(`scene ${s.id}: unknown grammar ${s.grammar}`);
  const srv = await serve(), port = srv.address().port, base = `http://127.0.0.1:${port}`;
  if (mode === 'serve') { console.log(`preview: ${base}/video.html   (kit scenes; ?t=<sec>&still for one frame)`); return; }
  const fps = mode === 'video' ? +(arg || 30) : 30;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--force-device-scale-factor=1'] });
  let pageErr = 0; const seen = new Set();
  const open = async (url, init) => {
    const p = await browser.newPage(); await p.setViewport({ width: W, height: H });
    p.on('console', m => { const ty = m.type(), tx = m.text(); if ((ty === 'error' || ty === 'warning') && !/404/.test(tx) && !seen.has(tx)) { seen.add(tx); console.log(`[${ty}]`, tx); if (ty === 'error') pageErr++; } });
    p.on('pageerror', e => { console.log('[pageerror]', e.message); pageErr++; });
    if (init) await p.evaluateOnNewDocument(init);
    await p.goto(url); return p;
  };
  const CLEAN = process.env.RX_CLEAN ? 'window.RX_CLEAN=true;' : '';
  const kit = await open(`${base}/video.html`, (CLEAN + PAGE_INIT) || undefined);
  const info = await kit.evaluate(() => window.ready);
  const META = { header: SCRIPT.header || '', ...(await kit.evaluate(() => window.META || {})) };
  if (!info.fonts) console.warn('WARN: handwriting font not available — kit text falls back');
  console.log('ready', { duration: TL.duration, scenes: TL.scenes.map(s => `${s.id}:${s.grammar || 'kit'}`).join(' ') });

  const clips = {};   // sceneId -> page with that scene's grammar clip + overlay
  const clipPage = async sid => {
    if (clips[sid]) return clips[sid];
    const ssc = SCRIPT.scenes.find(s => s.id === sid), tsc = TL.scenes.find(s => s.id === sid), spec = specFor(ssc, tsc, fps);
    fs.mkdirSync(path.join(PROJ, 'specs'), { recursive: true }); fs.writeFileSync(path.join(PROJ, 'specs', sid + '.json'), JSON.stringify(spec, null, 1));
    const p = await open(`${base}/huashu/clip.html?render=1`, `${CLEAN}${PAGE_INIT}window.CLIP_SPEC=${JSON.stringify(spec)};window.TIMELINE=${JSON.stringify(TL)};window.META=${JSON.stringify(META)};`);
    await p.waitForFunction('window.__ready === true || !!window.__bootFailed', { timeout: 120000 });
    const bf = await p.evaluate('window.__bootFailed || null'); if (bf) throw new Error(`scene ${sid} (${ssc.grammar}) failed to boot:\n${bf}`);
    await p.addScriptTag({ url: `${base}/overlay.js` }); await p.evaluate(() => window.RXO.ready);
    return (clips[sid] = { p, sc: tsc });
  };
  const sceneAt = t => TL.scenes.find(s => t >= s.start && t < s.end) || (t < TL.scenes[0].start ? TL.scenes[0] : TL.scenes[TL.scenes.length - 1]);
  const grab = async (t, q) => {
    const sc = sceneAt(t);
    if (sc.grammar) {
      const { p } = await clipPage(sc.id), lt = Math.min(Math.max(0, t - sc.start), sc.end - sc.start - 1 / fps);
      await p.evaluate(t => RXO.prep(t), t);
      return p.evaluate((lt, t, q) => { renderFrame(lt); RXO.draw(window.__canvas.getContext('2d'), t); return window.__canvas.toDataURL('image/jpeg', q).split(',')[1]; }, lt, t, q);
    }
    await kit.evaluate(t => window.RXO && RXO.prep && RXO.prep(t), t);
    return kit.evaluate((t, q) => { renderFrame(t); return document.getElementById('c').toDataURL('image/jpeg', q).split(',')[1]; }, t, q);
  };

  const stills = async times => {
    const dir = path.join(PROJ, 'stills'); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir);
    for (const t of times) fs.writeFileSync(path.join(dir, `t${t.toFixed(1).padStart(5, '0')}.jpg`), Buffer.from(await grab(t, .85), 'base64'));
    return dir;
  };
  if (mode === 'stills') {
    console.log(await stills(String(arg).split(',').map(Number)));
  } else if (mode === 'sheet') {
    const n = +(arg || 18), cols = 6, rows = Math.ceil(n / cols);
    const times = Array.from({ length: n }, (_, i) => +(TL.duration * (i + .5) / n).toFixed(1));
    const dir = await stills(times);
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-pattern_type', 'glob', '-i', path.join(dir, 't*.jpg'),
      '-vf', `scale=360:-1,tile=${cols}x${rows}:padding=6`, '-frames:v', '1', path.join(PROJ, 'contact.jpg')]);
    console.log('times', times.join(','));
    console.log(path.join(PROJ, 'contact.jpg'));
  } else {
    const n = Math.ceil(TL.duration * fps), out = path.join(PROJ, 'out.mp4');
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(fps), '-i', '-',
      '-i', path.join(PROJ, 'narration.wav'), '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
      '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      const buf = Buffer.from(await grab(i / fps, .93), 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 600 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    console.log('wrote', out);
    gate(out);
  }
  await browser.close(); srv.close();
  process.exit(pageErr ? 1 : 0);
})().catch(e => { console.error(e.message || e); process.exit(1); });
