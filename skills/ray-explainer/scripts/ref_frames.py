#!/usr/bin/env python3
"""Grab reference frames from a YouTube / Bilibili video that is open in Ray's Chrome, for the style reference library
(references/style-refs.md). Frames go into Ray's vault (60-素材/50-调研媒体/解说视频风格参考/<id>/, with --vault) or, without
a vault, ~/.config/ray-explainer/style-refs/<id>/ — never into a repo: they are other people's work, kept only as private reference.

Why this way: yt-dlp gets 403 from YouTube for video segments, and reading Chrome's cookie store is off limits. So the
page itself draws the paused <video> into a canvas and POSTs the JPEG to this receiver on 127.0.0.1.

usage:
  python3 ref_frames.py <id> [--vault <vault root>]   # start the receiver (run in the background)
  then, with Claude in Chrome on the video page, run the JS printed by:  python3 ref_frames.py --js <id> [n=12]
  (YouTube: wait out / skip the ad first — the snippet clicks "Skip" when it can. Bilibili works the same way.)
Stop the receiver when done.
"""
import http.server, os, re, sys, urllib.parse

ROOT = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "ray-explainer", "style-refs")
PORT = 8765

JS = """const G=async(p,fr,st=1800)=>{const sl=m=>new Promise(r=>setTimeout(r,m)),V=()=>document.querySelector('video');
for(let i=0;i<40&&!(V()&&V().duration>0);i++)await sl(500);
for(let i=0;i<60&&document.querySelector('.ad-showing');i++){const s=document.querySelector('.ytp-skip-ad-button,.ytp-ad-skip-button-modern');if(s)s.click();await sl(1000)}
const v=V();v.muted=true;const o=[];for(const[k,f]of fr.entries()){const t=v.duration*f;v.pause();
await new Promise(r=>{v.addEventListener('seeked',r,{once:true});v.currentTime=t});await sl(st);
const c=document.createElement('canvas');c.width=960;c.height=Math.round(960*v.videoHeight/v.videoWidth);c.getContext('2d').drawImage(v,0,0,c.width,c.height);
const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.85));
o.push(t.toFixed(0)+'s '+v.videoWidth+'x'+v.videoHeight+' '+await fetch('http://127.0.0.1:%d/save?name='+p+'-'+String(k).padStart(2,'0')+'.jpg',{method:'POST',body:b}).then(r=>r.text()).catch(e=>'ERR '+e.message))}return o};
await G('%s',%s);"""

if len(sys.argv) > 1 and sys.argv[1] == "--js":
    rid, n = sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 12
    print(JS % (PORT, rid, [round(0.04 + 0.9 * i / max(1, n - 1), 3) for i in range(n)]))
    sys.exit(0)
if len(sys.argv) < 2: sys.exit(__doc__)
VAULT = sys.argv[sys.argv.index("--vault") + 1] if "--vault" in sys.argv else os.environ.get("RAY_VAULT")
if VAULT: ROOT = os.path.join(VAULT, "60-素材", "50-调研媒体", "解说视频风格参考")
OUT = os.path.join(ROOT, re.sub(r"[^\w-]", "_", sys.argv[1])); os.makedirs(OUT, exist_ok=True)

class H(http.server.BaseHTTPRequestHandler):
    def cors(self):
        for k, v in (("Access-Control-Allow-Origin", "*"), ("Access-Control-Allow-Methods", "POST, OPTIONS"),
                     ("Access-Control-Allow-Headers", "*"), ("Access-Control-Allow-Private-Network", "true")): self.send_header(k, v)
    def do_OPTIONS(self): self.send_response(204); self.cors(); self.end_headers()
    def do_POST(self):
        name = re.sub(r"[^\w.-]", "_", urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("name", ["x.jpg"])[0])
        open(os.path.join(OUT, name), "wb").write(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(200); self.cors(); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self, *a): pass

print(f"receiving frames into {OUT} on 127.0.0.1:{PORT}", flush=True)
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
