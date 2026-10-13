// Mixed-mode renderer. Each scene is drawn either by ray-explainer's own kit (scenes.js) or by a
// huashu-art-motion explainer grammar clip (script.json scene has "grammar"); every frame gets the shared
// caption/progress overlay; headless Chrome seeks frame by frame and FFmpeg stitches frames + narration.
// usage:
//   node render.js <project> stills 3,12.5,40      -> <project>/stills/tNNN.N.jpg
//   node render.js <project> sheet [N]             -> N evenly spaced stills tiled into <project>/contact.jpg
//   node render.js <project> video [fps]           -> <project>/out.mp4
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
if (!projArg) { console.error('usage: node render.js <project> stills|sheet|video|serve [arg]'); process.exit(2); }
const PROJ = path.resolve(projArg);
const SCRIPT = JSON.parse(fs.readFileSync(path.join(PROJ, 'script.json')));
const TL = JSON.parse(fs.readFileSync(path.join(PROJ, 'timeline.json')));
const W = 1080, H = 1920, SAFE = { top: 290, bottom: 380 };   // overlay: progress/header y 200–290, captions y 1560–1656; above 200 / below 1680 the phone UI covers the frame
// digital host (host.py wrote host/plan.json): captions move up to ~1470 and the corner presenter takes the bottom, so grammar clips keep clear of y>1440
if (fs.existsSync(path.join(PROJ, 'host', 'plan.json'))) SAFE.bottom = 480;

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
    safe: { ...SAFE, ...(ssc.safe || {}) }, ...(ssc.data ? { data: ssc.data } : {}), cues };
}

(async () => {
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
  const kit = await open(`${base}/video.html`, CLEAN || undefined);
  const info = await kit.evaluate(() => window.ready);
  const META = { header: SCRIPT.header || '', ...(await kit.evaluate(() => window.META || {})) };
  if (!info.fonts) console.warn('WARN: handwriting font not available — kit text falls back');
  console.log('ready', { duration: TL.duration, scenes: TL.scenes.map(s => `${s.id}:${s.grammar || 'kit'}`).join(' ') });

  const clips = {};   // sceneId -> page with that scene's grammar clip + overlay
  const clipPage = async sid => {
    if (clips[sid]) return clips[sid];
    const ssc = SCRIPT.scenes.find(s => s.id === sid), tsc = TL.scenes.find(s => s.id === sid), spec = specFor(ssc, tsc, fps);
    fs.mkdirSync(path.join(PROJ, 'specs'), { recursive: true }); fs.writeFileSync(path.join(PROJ, 'specs', sid + '.json'), JSON.stringify(spec, null, 1));
    const p = await open(`${base}/huashu/clip.html?render=1`, `${CLEAN}window.CLIP_SPEC=${JSON.stringify(spec)};window.TIMELINE=${JSON.stringify(TL)};window.META=${JSON.stringify(META)};`);
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
  }
  await browser.close(); srv.close();
  process.exit(pageErr ? 1 : 0);
})().catch(e => { console.error(e.message || e); process.exit(1); });
