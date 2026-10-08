// Frame-by-frame renderer: headless Chrome seeks renderFrame(t), FFmpeg stitches frames + narration.
// usage:
//   node render.js <project> stills 3,12.5,40      -> <project>/stills/tNNN.N.jpg
//   node render.js <project> sheet [N]             -> N evenly spaced stills tiled into <project>/contact.jpg
//   node render.js <project> video [fps]           -> <project>/out.mp4
const path = require('path');
const os = require('os');
// puppeteer-core lives outside the skill dir (installed by check_setup.sh) so the skill stays dependency-free
const DEPS = process.env.RAY_EXPLAINER_DEPS || path.join(os.homedir(), '.cache', 'ray-explainer');
let puppeteer;
try { puppeteer = require('puppeteer-core'); } catch { puppeteer = require(require.resolve('puppeteer-core', { paths: [DEPS] })); }
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');

const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const [projArg, mode = 'sheet', arg] = process.argv.slice(2);
if (!projArg) { console.error('usage: node render.js <project> stills|sheet|video [arg]'); process.exit(2); }
const PROJ = path.resolve(projArg);

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--allow-file-access-from-files', '--force-device-scale-factor=1'] });
  const page = await browser.newPage();
  let pageErr = null;
  page.on('pageerror', e => { pageErr = e; console.error('PAGE ERROR', e.message); });
  await page.goto('file://' + path.join(PROJ, 'video.html'));
  const info = await page.evaluate(() => window.ready);
  const size = await page.evaluate(() => ({ w: document.getElementById('c').width, h: document.getElementById('c').height }));
  await page.setViewport({ width: size.w, height: size.h });
  if (!info.fonts) console.error('WARN: handwriting font not available — text will fall back');
  console.log('ready', info, size);
  const grab = (t, q) => page.evaluate((t, q) => { renderFrame(t); return document.getElementById('c').toDataURL('image/jpeg', q).split(',')[1]; }, t, q);

  const stills = async times => {
    const dir = path.join(PROJ, 'stills'); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir);
    for (const t of times) fs.writeFileSync(path.join(dir, `t${t.toFixed(1).padStart(5, '0')}.jpg`), Buffer.from(await grab(t, .85), 'base64'));
    return dir;
  };
  if (mode === 'stills') {
    console.log(await stills(String(arg).split(',').map(Number)));
  } else if (mode === 'sheet') {
    const n = +(arg || 18), cols = 6, rows = Math.ceil(n / cols);
    const times = Array.from({ length: n }, (_, i) => +(info.duration * (i + .5) / n).toFixed(1));
    const dir = await stills(times);
    execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-pattern_type', 'glob', '-i', path.join(dir, 't*.jpg'),
      '-vf', `scale=360:-1,tile=${cols}x${rows}:padding=6`, '-frames:v', '1', path.join(PROJ, 'contact.jpg')]);
    console.log('times', times.join(','));
    console.log(path.join(PROJ, 'contact.jpg'));
  } else {
    const fps = +(arg || 30), n = Math.ceil(info.duration * fps), out = path.join(PROJ, 'out.mp4');
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
  await browser.close();
  process.exit(pageErr ? 1 : 0);
})();
