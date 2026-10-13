// Deterministic clip recorder for live web pages (interactive figures, WebGL demos, Anatomy works, dashboards).
// The page's clock (performance.now, Date.now, rAF, setTimeout/setInterval) is replaced by a virtual clock that
// only advances when we step it, so every frame is exactly 1/fps apart however slow the capture is: smooth,
// identical on every run, and WebGL included. Output: <jobs dir>/clips/<name>.mp4 (silent, H.264) plus
// <name>_first.png / <name>_last.png stills for placing the clip.
//
// usage: node record_clip.mjs jobs.json [name ...]        (no names = every job)
// job: { name, url (http(s) or local file), dur, fps=30, warm=1.5 (seconds run before recording starts),
//        width=1300, height=1200, dpr=2, crop: "auto" | "plate" | [x,y,w,h] (CSS px), pad=12, ow=1000 (output width),
//        setup: "js run once after load",
//        actions: [[t, action] ...] }   t = clip seconds (negative = during warm-up); action is one of
//          "mouse:fx,fy"  move the mouse to a fraction of the crop box   "click:fx,fy"  click there
//          "key:Enter"    press one key (puppeteer key names; single chars type themselves)
//          "char:x"       insert a character without key events       anything else: JS evaluated in the page
// crop "auto" finds the drawing (largest svg/canvas/custom element, inside .iso-plate when present, shadow DOM included).
// Pages that are themselves seekable (window.__seek(t)) don't need this: screenshot them per frame instead.
import { createRequire } from "node:module";
import { homedir } from "node:os";
import { mkdirSync, readFileSync, rmSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

// puppeteer-core lives outside the skill dir (installed by check_setup.sh), like render.js
const DEPS = process.env.RAY_EXPLAINER_DEPS || join(homedir(), ".cache", "ray-explainer");
const require = createRequire(join(DEPS, "/"));
const puppeteer = require("puppeteer-core");
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const [jobsFile, ...only] = process.argv.slice(2);
const jobs = JSON.parse(readFileSync(jobsFile, "utf8")).filter((j) => !only.length || only.includes(j.name));
const OUT = resolve(dirname(jobsFile), "clips");
mkdirSync(OUT, { recursive: true });

const CLOCK = `(() => {
  let now = 0; const t0 = 1.7e12; let seq = 0;
  const raf = []; const timers = new Map();
  const realRAF = window.requestAnimationFrame.bind(window);
  window.__realRAF = realRAF;
  performance.now = () => now;
  Date.now = () => t0 + now;
  window.requestAnimationFrame = (cb) => { const id = ++seq; raf.push([id, cb]); return id; };
  window.cancelAnimationFrame = (id) => { const i = raf.findIndex((r) => r[0] === id); if (i >= 0) raf.splice(i, 1); };
  window.setTimeout = (fn, d = 0, ...a) => { const id = ++seq; timers.set(id, { at: now + Math.max(0, d), fn, a }); return id; };
  window.clearTimeout = (id) => timers.delete(id);
  window.setInterval = (fn, d = 0, ...a) => { const id = ++seq; const tick = () => { timers.set(id, { at: now + Math.max(1, d), fn: () => { fn(...a); tick(); }, a: [] }); }; tick(); return id; };
  window.clearInterval = (id) => timers.delete(id);
  window.__step = (ms) => {
    const end = now + ms;
    for (;;) {
      let next = null;
      for (const [id, t] of timers) if (t.at <= end && (!next || t.at < next[1].at)) next = [id, t];
      if (!next) break;
      now = Math.max(now, next[1].at); timers.delete(next[0]);
      try { typeof next[1].fn === "function" && next[1].fn(...next[1].a); } catch (e) { console.error(e); }
    }
    now = end;
    const run = raf.splice(0);
    for (const [, cb] of run) { try { cb(now); } catch (e) { console.error(e); } }
  };
  window.__painted = () => new Promise((r) => realRAF(() => realRAF(r)));
})();`;

const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--use-angle=metal", "--hide-scrollbars"] });
for (const job of jobs) {
  const fps = job.fps ?? 30, dt = 1000 / fps, warm = job.warm ?? 1.5;
  const page = await browser.newPage();
  page.on("pageerror", (e) => console.log(job.name, "pageerror", e.message.slice(0, 160)));
  await page.setViewport({ width: job.width ?? 1300, height: job.height ?? 1200, deviceScaleFactor: job.dpr ?? 2 });
  await page.evaluateOnNewDocument(CLOCK);
  const url = /^https?:/.test(job.url) ? job.url : pathToFileURL(resolve(job.url)).href;
  await page.goto(url, { waitUntil: "networkidle2", timeout: 60000 });
  if (job.setup) await page.evaluate(job.setup);
  // find the drawing's box
  const box = await page.evaluate((crop, pad) => {
    if (Array.isArray(crop)) return { x: crop[0], y: crop[1], w: crop[2], h: crop[3] };
    const deep = (root, out = []) => { for (const e of root.querySelectorAll("*")) { out.push(e); if (e.shadowRoot) deep(e.shadowRoot, out); } return out; };
    let els;
    if (crop === "plate") els = [document.querySelector(".iso-plate")];
    else {
      const plate = document.querySelector(".iso-plate");
      const pool = plate ? deep(plate) : deep(document);
      els = pool.filter((e) => /^(svg|canvas)$/i.test(e.tagName) || e.tagName.startsWith("ANATOMY-"));
    }
    const rs = els.filter(Boolean).map((e) => e.getBoundingClientRect()).filter((r) => r.width > 200 && r.top < 1150);
    const x = Math.min(...rs.map((r) => r.left)), y = Math.min(...rs.map((r) => r.top));
    const r = Math.max(...rs.map((r) => r.right)), b = Math.max(...rs.map((r) => r.bottom));
    return { x: Math.max(0, x - pad), y: Math.max(0, y - pad), w: r - x + 2 * pad, h: b - y + 2 * pad };
  }, job.crop ?? "auto", job.pad ?? 12);
  const dir = join(OUT, job.name + "_frames");
  if (existsSync(dir)) rmSync(dir, { recursive: true });
  mkdirSync(dir, { recursive: true });
  const acts = [...(job.actions ?? [])].sort((a, b) => a[0] - b[0]);
  let ai = 0;
  const total = Math.round((warm + job.dur) * fps);
  for (let f = 0; f < total; f++) {
    const t = f / fps - warm;
    while (ai < acts.length && acts[ai][0] <= t + 1e-6) {
      const a = acts[ai][1]; ai++;
      const xy = (v) => { const [fx, fy] = v.split(",").map(Number); return [box.x + fx * box.w, box.y + fy * box.h]; };
      if (a.startsWith("mouse:")) await page.mouse.move(...xy(a.slice(6)), { steps: 4 });
      else if (a.startsWith("click:")) await page.mouse.click(...xy(a.slice(6)));
      else if (a.startsWith("key:")) await page.keyboard.press(a.slice(4));
      else if (a.startsWith("char:")) await page.keyboard.sendCharacter(a.slice(5));
      else await page.evaluate(a);
    }
    await page.evaluate((ms) => window.__step(ms), dt);
    await page.evaluate(() => window.__painted());
    if (t >= -1e-6) await page.screenshot({ path: join(dir, `f${String(f - Math.round(warm * fps)).padStart(4, "0")}.png`), clip: { x: box.x, y: box.y, width: box.w, height: box.h } });
  }
  const ow = job.ow ?? 1000;
  const mp4 = join(OUT, job.name + ".mp4");
  execFileSync("ffmpeg", ["-loglevel", "error", "-y", "-framerate", String(fps), "-i", join(dir, "f%04d.png"), "-vf", `scale=${ow}:-2:flags=lanczos,format=yuv420p`, "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-movflags", "+faststart", mp4]);
  execFileSync("cp", [join(dir, "f0000.png"), join(OUT, job.name + "_first.png")]);
  execFileSync("cp", [join(dir, `f${String(Math.round(job.dur * fps) - 1).padStart(4, "0")}.png`), join(OUT, job.name + "_last.png")]);
  rmSync(dir, { recursive: true });
  console.log(job.name, `${Math.round(box.w)}x${Math.round(box.h)}`, `${job.dur}s`, "→", mp4);
  await page.close();
}
await browser.close();
