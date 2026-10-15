"""Cut the real source-audio clips listed in script.json, and find where words are said in a recording.

usage:
  python3 cut_clips.py <project> [clip id …]                          cut every clip that has a "cut" spec (or just these)
  python3 cut_clips.py --words <audio> [--from 2:41:00] [--to 2:43:30] [--lang en]
                                                                     word-level Whisper timestamps (mlx_whisper) to pick segs

script.json "clips"[] entries gain a "cut" block next to the fields splice_clips.py reads:
  "cut": {"file": "/…/art002_2026-04-07_oe1.m4a",   # source recording (absolute, or relative to the project)
          "base": "0:41:00",                          # optional offset into the file (h:m:s, m:s or seconds)
          "segs": [[2.1, 9.4], [12.0, 15.2]],          # seconds after base; several segments are joined
          "gap": 0.45}                                # silence between joined segments (default 0.45 s)
→ writes the clip's "src" (default clips/<id>.wav): every segment faded in/out, joined, loudnorm -17 LUFS,
  24 kHz mono s16 — the format splice_clips.py expects. Re-run after changing segs, then splice_clips.py.
`--words` prints each Whisper segment as word@seconds (relative to --from), so segs can be read off directly.
"""
import json, os, subprocess, sys, tempfile, wave

RATE = 24000


def secs(t):
    if isinstance(t, (int, float)): return float(t)
    p = [float(x) for x in str(t).split(":")]
    return sum(v * 60 ** (len(p) - 1 - i) for i, v in enumerate(p))


def words(audio, t0=None, t1=None, lang="en"):
    import mlx_whisper
    src = audio
    if t0 is not None or t1 is not None:
        src = tempfile.mktemp(suffix=".wav")
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-ss", str(secs(t0 or 0))]
        if t1 is not None: cmd += ["-t", str(secs(t1) - secs(t0 or 0))]
        subprocess.run(cmd + ["-i", audio, "-ac", "1", "-ar", "16000", src], check=True)
    r = mlx_whisper.transcribe(src, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True, language=lang)
    for s in r["segments"]:
        print(" ".join(f'{w["word"].strip()}@{w["start"]:.2f}' for w in s.get("words", [])))
    if src != audio: os.unlink(src)


def cut(proj, c):
    spec = c["cut"]; src = spec["file"] if os.path.isabs(spec["file"]) else os.path.join(proj, spec["file"])
    base, gap = secs(spec.get("base", 0)), float(spec.get("gap", 0.45))
    parts = []
    for a, z in spec["segs"]:
        f = tempfile.mktemp(suffix=".wav"); d = z - a
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{base + a:.3f}", "-t", f"{d:.3f}", "-i", src,
                        "-af", f"afade=t=in:d=0.04,afade=t=out:st={d - 0.08:.3f}:d=0.08", "-ac", "1", "-ar", str(RATE), "-sample_fmt", "s16", f], check=True)
        with wave.open(f) as w: parts.append(w.readframes(w.getnframes()))
        os.unlink(f)
    raw = (b"\0\0" * int(gap * RATE)).join(parts)
    tmp = tempfile.mktemp(suffix=".wav")
    with wave.open(tmp, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(raw)
    out = os.path.join(proj, c.get("src") or f"clips/{c['id']}.wav"); os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-17:TP=-1.5:LRA=11",
                    "-ac", "1", "-ar", str(RATE), "-sample_fmt", "s16", out], check=True)
    os.unlink(tmp)
    print(f"  {c['id']:4} {len(raw) / 2 / RATE:6.2f}s  {len(spec['segs'])} seg  → {os.path.relpath(out, proj)}")
    return os.path.relpath(out, proj)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--words":
        opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
        words(a[1], opt("--from"), opt("--to"), opt("--lang", "en")); sys.exit(0)
    if not a: sys.exit(__doc__)
    proj = os.path.abspath(a[0]); want = set(a[1:])
    sf = os.path.join(proj, "script.json"); script = json.load(open(sf))
    todo = [c for c in script.get("clips", []) if c.get("cut") and (not want or c["id"] in want)]
    if not todo: sys.exit("no clips with a \"cut\" spec in script.json")
    changed = False
    for c in todo:
        rel = cut(proj, c)
        if c.get("src") != rel: c["src"] = rel; changed = True
    if changed: json.dump(script, open(sf, "w"), ensure_ascii=False, indent=1)
    print("next: splice_clips.py <project>")
