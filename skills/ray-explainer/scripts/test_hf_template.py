"""Smoke test for assets/hf-template — run after editing make_beats.py / build.py / host_build.py.

usage: python3 test_hf_template.py          (offline, ~1 s; builds a throwaway project in a temp dir)

Each case is a template bug that first showed up in a real film (2026-10-15 《AI 游客》):
  - a decimal (2.5%) must stay in one caption               (make_beats.py split it at the ".")
  - ray-ip-dark must give a light top bar on a dark ground   (build.py kept the light-theme ink → invisible bar)
  - host_build.py must run with big segments                 (NameError: H used before it was computed)
  - two big segments 1 s apart must not shrink back between  (host flew to the corner and back in 1 s)
Exit 1 with the failing case named.
"""
import json, os, shutil, subprocess, sys, tempfile

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(SK, "assets", "hf-template")
fails = []


def check(ok, what):
    print(("ok    " if ok else "FAIL  ") + what)
    if not ok: fails.append(what)


def line(text, t0):
    chars = [round(t0 + 0.18 * i, 3) for i in range(len(text))]
    return {"text": text, "start": t0, "end": round(t0 + 0.18 * len(text), 3), "chars": chars}


with tempfile.TemporaryDirectory() as proj:
    hf = os.path.join(proj, "hf"); os.makedirs(os.path.join(hf, "compositions"))
    for f in ("make_beats.py", "build.py", "host_build.py"): shutil.copy(os.path.join(TPL, f), hf)
    shutil.copy(os.path.join(SK, "assets", "canvas.json"), hf)
    l1, l2 = "最后只有 2.5% 的人留了下来", "剩下的人都去找下一个热门产品了"
    a = line(l1, 0.6); b = line(l2, round(a["end"] + 0.32, 3))
    json.dump({"title": "t", "theme": "ray-ip-dark", "scenes": [{"id": "x", "lines": [l1, l2]}]}, open(os.path.join(proj, "script.json"), "w"), ensure_ascii=False)
    json.dump({"scenes": [{"id": "x", "start": 0, "end": b["end"], "lines": [a, b]}], "duration": b["end"]}, open(os.path.join(proj, "timeline.json"), "w"), ensure_ascii=False)
    os.makedirs(os.path.join(proj, "host", "avatar"))
    open(os.path.join(proj, "host", "avatar", "base.png"), "wb").write(b"")
    big = {"x": 300, "y": 700, "w": 600}
    json.dump({"avatar": {"size": [1000, 1300], "patches": {}}, "mouth": [], "blinks": [], "big": big,
               "segments": [{"start": 1.0, "end": 3.0, "dir": "host/frames/s1", "pad": [0.1, 0, 0.1, 0]},   # pad = H3 帧的绿边
                            {"start": 4.0, "end": 6.0, "dir": "host/frames/s2"}]},
              open(os.path.join(proj, "host", "plan.json"), "w"))
    os.makedirs(os.path.join(hf, "assets", "host"))
    for k in ("s1", "s2"): open(os.path.join(hf, "assets", "host", f"big_{k}.webm"), "wb").write(b"")   # skip the ffmpeg step

    def run(f):
        r = subprocess.run([sys.executable, os.path.join(hf, f)], capture_output=True, text=True, cwd=hf)
        check(r.returncode == 0, f"{f} runs" + ("" if r.returncode == 0 else f"\n{r.stderr.strip()[-600:]}"))
        return r

    r = run("make_beats.py")
    caps = [c["s"] for s in json.load(open(os.path.join(hf, "beats.json")))["scenes"] for c in s["caps"]] if r.returncode == 0 else []
    check(any("2.5%" in c for c in caps), f"decimal stays in one caption {caps}")
    check("WARN" not in r.stdout, "no split-number warning")
    run("host_build.py")
    host = open(os.path.join(hf, "compositions", "s-host.html")).read() if os.path.exists(os.path.join(hf, "compositions", "s-host.html")) else ""
    check(host.count("x: 0, y: 0, scale: 1, duration: 0.8") == 1, "adjacent big segments return to the corner once, not twice")
    run("build.py")
    idx = open(os.path.join(hf, "index.html")).read() if os.path.exists(os.path.join(hf, "index.html")) else ""
    check("--tb-ink: #F3F3F0" in idx and "background: #1C1D1D" in idx, "ray-ip-dark → light top bar on dark ground")

print("hf-template: " + ("OK" if not fails else f"{len(fails)} failed"))
sys.exit(1 if fails else 0)
