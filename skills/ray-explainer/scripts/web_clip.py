#!/usr/bin/env python3
"""Record a few seconds of a YouTube / Bilibili video that is open in Ray's Chrome, as a real moving clip for a film
(hyperframes.md「取材」: real footage first). Same idea as ref_frames.py: yt-dlp gets 403 from YouTube and reading
Chrome's cookie store is off limits, so the page records its own <video> (captureStream + MediaRecorder, picture and
sound, in real time) and POSTs the webm to this receiver on 127.0.0.1, which turns it into an mp4.

usage:
  python3 web_clip.py <out_dir>                         # start the receiver (run in the background); clips land in <out_dir>
  python3 web_clip.py --js <name> <start> <seconds>     # print the JS to run on the video page (Claude in Chrome javascript tool);
      it returns at once and works in the background: poll JSON.stringify(window.__clip) until state is done / error
      <start> is seconds or m:ss / h:mm:ss into the video. Recording is real time: a 10 s clip takes ~10 s plus buffering.
  → <out_dir>/<name>.mp4 (H.264 + AAC, 30 fps), <name>.json (page url, title, start, duration, recorded span)

Notes:
- The page plays the segment while recording; the snippet sets volume to 0 on Chrome's output only where it can —
  check that the mp4 has sound (ffprobe) and tell Ray the tab will make noise if it doesn't.
- YouTube: wait out / skip the ad first (the snippet clicks "Skip" when it can) and ask the player for 1080p.
- The JSON keeps the source link: put it in credits.json and on screen as「来源 · 日期」.
Stop the receiver when done.
"""
import datetime, http.server, json, os, re, subprocess, sys, urllib.parse

PORT = 8766

JS = r"""const S=x=>window.__clip.state=x;const R=async(name,start,dur)=>{const sl=m=>new Promise(r=>setTimeout(r,m)),V=()=>document.querySelector('video');
for(let i=0;i<40&&!(V()&&V().duration>0);i++)await sl(500);
S('ad');for(let i=0;i<240&&document.querySelector('.ad-showing');i++){const s=document.querySelector('.ytp-skip-ad-button,.ytp-ad-skip-button-modern');if(s)s.click();await sl(1000)}
const p=document.querySelector('#movie_player');try{p.setPlaybackQualityRange('hd1080','hd1080')}catch(e){}
const v=V();v.pause();v.playbackRate=1;
S('buffer');await new Promise(r=>{v.addEventListener('seeked',r,{once:true});v.currentTime=start});
for(let i=0;i<40;i++){const b=v.buffered;let ok=false;for(let k=0;k<b.length;k++)if(b.start(k)<=start+.1&&b.end(k)>=Math.min(v.duration,start+dur))ok=true;if(ok)break;
 v.play();await sl(400);v.pause();await new Promise(r=>{v.addEventListener('seeked',r,{once:true});v.currentTime=start})}
const st=v.captureStream();const mt=['video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm'].find(t=>MediaRecorder.isTypeSupported(t));
const rec=new MediaRecorder(st,{mimeType:mt,videoBitsPerSecond:12e6,audioBitsPerSecond:192e3});const ch=[];rec.ondataavailable=e=>e.data.size&&ch.push(e.data);
S('record');const done=new Promise(r=>rec.onstop=r);const t0=v.currentTime;rec.start(250);await v.play();
while(v.currentTime<start+dur&&!v.ended)await sl(30);
rec.stop();v.pause();await done;const t1=v.currentTime;
const meta={url:location.href,title:document.title,start,duration:dur,recorded_from:t0,recorded_to:t1,size:[v.videoWidth,v.videoHeight],mime:mt};
const q='http://127.0.0.1:%d/save?name='+encodeURIComponent(name)+'&meta='+encodeURIComponent(JSON.stringify(meta));
S('upload');return await fetch(q,{method:'POST',body:new Blob(ch,{type:mt})}).then(r=>r.text()).catch(e=>'ERR '+e.message)};
window.__clip={state:'wait'};R('%s',%s,%s).then(r=>{window.__clip.state='done';window.__clip.result=r}).catch(e=>{window.__clip.state='error';window.__clip.result=String(e)});'started — poll: JSON.stringify(window.__clip)'"""


def secs(x):
    parts = [float(p) for p in x.split(":")]
    return sum(p * 60 ** i for i, p in enumerate(reversed(parts)))


if len(sys.argv) > 1 and sys.argv[1] == "--js":
    name, start, dur = re.sub(r"[^\w-]", "_", sys.argv[2]), secs(sys.argv[3]), float(sys.argv[4])
    print(JS % (PORT, name, start, dur))
    sys.exit(0)
if len(sys.argv) < 2: sys.exit(__doc__)
OUT = os.path.abspath(sys.argv[1]); os.makedirs(OUT, exist_ok=True)


class H(http.server.BaseHTTPRequestHandler):
    def cors(self):
        for k, v in (("Access-Control-Allow-Origin", "*"), ("Access-Control-Allow-Methods", "POST, OPTIONS"),
                     ("Access-Control-Allow-Headers", "*"), ("Access-Control-Allow-Private-Network", "true")): self.send_header(k, v)

    def do_OPTIONS(self): self.send_response(204); self.cors(); self.end_headers()

    def do_POST(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        name = re.sub(r"[^\w-]", "_", q.get("name", ["clip"])[0]); meta = json.loads(q.get("meta", ["{}"])[0])
        tag = datetime.datetime.now().strftime("%H%M%S%f")   # each upload gets its own temp files: a stale run can't clobber a fresh one
        webm = os.path.join(OUT, f".{name}.{tag}.webm"); tmp = os.path.join(OUT, f".{name}.{tag}.mp4"); mp4 = os.path.join(OUT, name + ".mp4")
        open(webm, "wb").write(self.rfile.read(int(self.headers["Content-Length"])))
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", webm, "-r", "30", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], capture_output=True, text=True)
        meta["captured"] = datetime.datetime.now().isoformat(timespec="seconds")
        json.dump(meta, open(os.path.join(OUT, name + ".json"), "w"), ensure_ascii=False, indent=1)
        msg = f"ok {name}.mp4 {meta.get('recorded_from', 0):.2f}→{meta.get('recorded_to', 0):.2f}s" if r.returncode == 0 else "ffmpeg failed: " + r.stderr[-300:]
        if r.returncode == 0: os.replace(tmp, mp4); os.remove(webm)
        print(msg, flush=True)
        self.send_response(200); self.cors(); self.end_headers(); self.wfile.write(msg.encode())

    def log_message(self, *a): pass


print(f"receiving clips into {OUT} on 127.0.0.1:{PORT}", flush=True)
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
