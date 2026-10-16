"""Smoke test for the re-voice path of assets/hf-template/build.py — run after editing build.py / make_beats.py.

usage: python3 test_hf_anchors.py          (offline, ~2 s; builds a throwaway project in a temp dir)

Both cases first bit in a real film (2026-10-15 《Roadster 真能飞》, a scene was cut and the voice redone):
  - <video data-start> was hard-coded scene seconds → every clip had to be re-timed by hand.
    Now data-start="{{line:1}}" / {{phrase:0:词+0.2}} / {{clip:c1}} / {{clip:c1:end}} / {{cap:N}} resolve on every build,
    and still follow the voice on the second build (the tag keeps data-anchor-start).
  - narration.m4a was not re-encoded after narration.wav changed → picture and voice drifted apart.
Exit 1 with the failing case named.
"""
import json, os, re, shutil, subprocess, sys, tempfile, time, wave

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(SK, "assets", "hf-template")
fails = []


def check(ok, what):
    print(("ok    " if ok else "FAIL  ") + what)
    if not ok: fails.append(what)


def line(text, t0):
    chars = [round(t0 + 0.2 * i, 3) for i in range(len(text))]
    return {"text": text, "start": t0, "end": round(t0 + 0.2 * len(text), 3), "chars": chars}


def voice(proj, shift):
    """Write timeline.json as if the voice was (re-)recorded: everything moves by `shift` seconds."""
    a = line("这辆车真的飞起来了", 0.6 + shift)
    b = line("然后它稳稳落地", round(a["end"] + 2.5, 3))   # a 2 s source clip sits between the lines
    c1 = {"id": "c1", "start": round(a["end"] + 0.2, 3), "end": round(a["end"] + 2.2, 3), "speaker": "Elon Musk", "utc": "2026-10-15",
          "segs": [[round(a["end"] + 0.2, 3), "So yes, it can fly", "所以它真能飞"]]}
    json.dump({"scenes": [{"id": "x", "start": 0, "end": b["end"], "lines": [a, b]}], "clips": [c1], "duration": b["end"]},
              open(os.path.join(proj, "timeline.json"), "w"), ensure_ascii=False)
    return a, b, c1


with tempfile.TemporaryDirectory() as proj:
    hf = os.path.join(proj, "hf"); os.makedirs(os.path.join(hf, "compositions"))
    for f in ("make_beats.py", "build.py"): shutil.copy(os.path.join(TPL, f), hf)
    shutil.copy(os.path.join(SK, "assets", "canvas.json"), hf)
    json.dump({"title": "t", "scenes": [{"id": "x", "lines": ["这辆车真的飞起来了", "然后它稳稳落地"]}]},
              open(os.path.join(proj, "script.json"), "w"), ensure_ascii=False)
    scene = os.path.join(hf, "compositions", "s-x.html")
    open(scene, "w").write("""<template><div id="s-x" data-composition-id="s-x">
  <video id="x-v1" src="assets/video/a.mp4" muted data-start="0" data-duration="2"></video>
  <video id="x-v2" src="assets/video/a.mp4" muted data-start="{{phrase:0:飞起来+0.2}}" data-duration="2"></video>
  <video id="x-v3" src="assets/video/a.mp4" muted data-start="{{clip:c1}}" data-duration="2"></video>
  <video id="x-v4" src="assets/video/a.mp4" muted data-start="{{clip:c1:end}}" data-duration="2"></video>
  <video id="x-v5" src="assets/video/a.mp4" muted data-start="{{line:1}}" data-duration="2"></video>
  <video id="x-v6" src="assets/video/a.mp4" muted data-start="{{cap:1-0.1}}" data-duration="2"></video>
  <video id="x-v7" src="assets/video/a.mp4" muted data-start="4.2" data-playback-rate="0.1" data-duration="2"></video>
</div></template>""")

    def build():
        out = ""
        for f in ("make_beats.py", "build.py"):
            r = subprocess.run([sys.executable, os.path.join(hf, f)], capture_output=True, text=True, cwd=hf)
            check(r.returncode == 0, f"{f} runs" + ("" if r.returncode == 0 else f"\n{r.stderr.strip()[-600:]}"))
            out += r.stdout
        return out

    def starts():
        return {m[0]: (m[1], float(m[2])) for m in re.findall(r'id="(x-v\d)"[^>]*?(?:data-anchor-start="([^"]*)" )?data-start="([\d.]+)"', open(scene).read())}

    def expect(a, b, c1, when):
        st = starts()
        caps = json.load(open(os.path.join(hf, "beats.json")))["scenes"][0]["caps"]
        want = {"x-v2": a["chars"][a["text"].index("飞起来")] + 0.2, "x-v3": c1["start"], "x-v4": c1["end"],
                "x-v5": b["chars"][0], "x-v6": caps[1]["a"] - 0.1}
        for k, v in want.items():
            check(k in st and abs(st[k][1] - v) < 0.002, f"{when}: {k} data-start = {v:.3f} (got {st.get(k)})")
        check(st.get("x-v1") == ("", 0.0), f"{when}: plain data-start=\"0\" left alone")

    a, b, c1 = voice(proj, 0); out = build(); expect(a, b, c1, "first build")
    check("{{" not in open(scene).read(), "no {{…}} left in the scene file after build")
    check("x-v7" in out and "写死" in out, "hard-coded video data-start is flagged")
    check("x-v7 0.1" in out, "playback-rate below 0.35 is flagged")
    a, b, c1 = voice(proj, 1.3); build(); expect(a, b, c1, "after re-voice (+1.3 s)")

    if shutil.which("ffmpeg"):
        wav, m4a = os.path.join(proj, "narration.wav"), os.path.join(hf, "assets", "audio", "narration.m4a")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(b"\0\0" * 16000)
        out = build()
        check(os.path.exists(m4a) and "重新编码" in out, "narration.m4a is encoded from narration.wav")
        out = build()
        check("重新编码" not in out, "narration.m4a up to date → not re-encoded")
        t = time.time() + 5; os.utime(wav, (t, t))   # re-voice: wav newer than m4a
        out = build()
        check("重新编码" in out and os.path.getmtime(m4a) >= os.path.getmtime(wav) - 5, "newer narration.wav → m4a re-encoded")
    else:
        print("skip  narration.m4a re-encode (no ffmpeg)")

print("hf-anchors: " + ("OK" if not fails else f"{len(fails)} failed"))
sys.exit(1 if fails else 0)
