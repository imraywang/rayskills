#!/usr/bin/env python3
"""Tighten Ray's raw talking-head recording: drop retakes, false starts and dead air, cutting only between words.
Approach from Peter Yang's video-short (MIT, https://github.com/petergyang/video-short): keep the last complete take of
a repeated line, start ~0.1 s before the first word and end ~0.1 s after the last, leave a short breath at pauses,
never speed the voice up. Run it before gate_breaths.py (which then silences the inhales left in the short gaps).

usage:
  python3 cut_retakes.py scan  <recording> [-o work]   # transcribe with word times, propose work/cuts.txt
  (read work/transcript_raw.md and edit work/cuts.txt: it is your edit decision, the script only proposes)
  python3 cut_retakes.py apply <recording> work/cuts.txt -o clean.mp4
                                                        # cut, 15 ms audio fades at every join; writes
                                                        # clean.map.json and work/transcript_clean.md to check

cuts.txt: one kept range per line, raw-recording seconds, `12.30-15.90  # what is said`; lines starting with # are
ignored. scan writes a suspected earlier take as a commented line marked [重说?], so it is dropped unless you restore it.
Pauses longer than --pause (0.6 s) become --keep (0.3 s): 0.1 s after the last word, the rest before the next word."""
import argparse, json, os, re, subprocess, sys, wave

import numpy as np

PUNCT = "，。！？、；：,.!?;: "


def transcribe(src, work):
    wav = os.path.join(work, "audio16k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", "16000", wav], check=True)
    subprocess.run(["mlx_whisper", wav, "--model", "mlx-community/whisper-large-v3-turbo", "--language", "zh",
                    "--word-timestamps", "True", "--output-format", "json", "--output-dir", work, "--output-name", "raw"],
                   check=True, capture_output=True)
    d = json.load(open(os.path.join(work, "raw.json")))
    words = []
    for seg in d["segments"]:
        for w in seg.get("words", []):
            t = w["word"].strip()
            if t:
                words.append({"text": t, "start": round(w["start"], 3), "end": round(w["end"], 3)})
    json.dump(words, open(os.path.join(work, "words_raw.json"), "w"), ensure_ascii=False, indent=0)
    return words


def energy(wav):
    """10 ms RMS in dB (3-frame smoothed) and the silence threshold max(noise floor + 8 dB, peak - 45 dB)."""
    with wave.open(wav) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        hop = w.getframerate() // 100
    n = len(x) // hop
    db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    db = np.convolve(db, np.ones(3) / 3, "same")
    return db, max(np.percentile(db, 10) + 8, db.max() - 45)


def snap(t, db, before=0.15, after=0.15):
    """Move a cut to the quietest 10 ms frame in [t - before, t + after]: Whisper word times drift, the gap between
    words doesn't. The end of a retake cut snaps mostly backward so it never eats the take that is kept."""
    a, b = max(0, int((t - before) * 100)), min(len(db), int((t + after) * 100) + 1)
    return (a + int(np.argmin(db[a:b]))) / 100 if b > a else t


def snap_quiet(t, db, thr, before, after, margin=6):
    """Nearest frame to t in [t - before, t + after] that is near-silent (≤ thr + margin dB), or None.
    A real restart nearly always has a short gap before it; with no gap, the cut would land inside speech."""
    a, b = max(0, int((t - before) * 100)), min(len(db), int((t + after) * 100) + 1)
    cand = [k for k in range(a, b) if db[k] <= thr + margin]
    return min(cand, key=lambda k: abs(k / 100 - t)) / 100 if cand else None


def silences(wav, min_len=0.3):
    """Silent spans from the audio itself (Whisper's word times stretch over pauses): frames below the threshold
    for at least min_len seconds."""
    db, thr = energy(wav)
    n = len(db)
    quiet = db < thr
    out, i = [], 0
    while i < n:
        if not quiet[i]:
            i += 1; continue
        j = i
        while j < n and quiet[j]:
            j += 1
        if (j - i) / 100 >= min_len:
            out.append((i / 100, j / 100))
        i = j
    return out, n / 100


def phrases(words, sil, dur):
    """Speech runs between silences, with the words whose start falls inside each."""
    edges = [0.0] + [t for s, e in sil for t in (s, e)] + [dur]
    runs = [(edges[k], edges[k + 1]) for k in range(0, len(edges) - 1, 2)]
    runs = [r for r in runs if r[1] - r[0] >= 0.15]
    out = []
    for k, (a, b) in enumerate(runs):
        lo = runs[k - 1][1] if k else -1.0     # Whisper starts drift into the pause before a word: split at the pause start
        hi = b if k + 1 < len(runs) else 1e9
        txt = "".join(w["text"] for w in words if lo <= w["start"] < hi)
        out.append({"start": a, "end": b, "text": txt})
    return [p for p in out if p["text"]]


def norm(t):
    return re.sub(f"[{re.escape(PUNCT)}]", "", t)


def retakes(ph, window=12.0, k=4):
    """Indices of phrases that look like an abandoned take: a later phrase within `window` s starts with the same
    first k characters (a restart), or repeats this phrase almost entirely."""
    bad = set()
    for i, p in enumerate(ph):
        a = norm(p["text"])
        if len(a) < 2:
            continue
        for j in range(i + 1, len(ph)):
            if ph[j]["start"] - p["end"] > window:
                break
            b = norm(ph[j]["text"])
            if (len(a) >= k and b.startswith(a[:k])) or (len(a) >= 2 and a in b):
                bad.add(i)
                break
    return bad


def repeats(words, min_len=3, max_gap=2):
    """Restarts inside the word stream: a run of >= min_len characters said again within max_gap characters
    ("现在我做事现在我做事…", "我跟他说这个是我跟他说这个风格"). Returns (cut_start, cut_end, text) in raw seconds,
    cutting from the first take's first word to the retake's first word, so cuts stay on word boundaries."""
    text, owner = "", []
    for k, w in enumerate(words):
        t = norm(w["text"])
        text += t
        owner += [k] * len(t)
    found, i = [], 0
    while i < len(text):
        hit = None
        for L in range(min(14, (len(text) - i) // 2), min_len - 1, -1):
            a = text[i:i + L]
            j = text.find(a, i + L, i + L + max_gap + L)
            if j >= 0:
                hit = (L, j); break
        if not hit:
            i += 1; continue
        L, j = hit
        wi, wj = owner[i], owner[j]
        if wj > wi and (i == 0 or owner[i - 1] != wi) and (owner[j - 1] != wj):   # both takes start on a word
            found.append((words[wi]["start"], words[wj]["start"], text[i:j]))
        i = j
    return found


def scan(a):
    work = a.out
    os.makedirs(work, exist_ok=True)
    words = transcribe(a.recording, work)
    sil, dur = silences(os.path.join(work, "audio16k.wav"))
    ph = phrases(words, sil, dur)
    bad = retakes(ph)
    md = ["# 原始逐字稿（带时间、停顿和疑似重说）", "",
          "⚠ 标出的是疑似重说：前一条没说完、后面又从头说了一遍。默认去掉前一条，留最后完整的那一遍。", ""]
    for i, p in enumerate(ph):
        gap = p["start"] - ph[i - 1]["end"] if i else p["start"]
        if gap > a.pause:
            md.append(f"　　‖ 停顿 {gap:.1f}s ‖")
        md.append(f"{'⚠ ' if i in bad else ''}[{p['start']:.2f}–{p['end']:.2f}] {p['text']}")
    reps_all = repeats(words)
    if reps_all:
        md += ["", "## 句内重说（剪掉前一遍，从第二遍的第一个字接上）", ""] + [f"- {cs:.2f}–{ce:.2f}「{t}」" for cs, ce, t in reps_all]
    open(os.path.join(work, "transcript_raw.md"), "w").write("\n".join(md) + "\n")
    # keep ranges: phrases with lead/tail, long pauses shrunk to --keep; then subtract retakes
    db, thr = energy(os.path.join(work, "audio16k.wav"))
    lead, tail = 0.1, 0.12
    keeps = []
    for p in ph:
        st, en = max(0.0, p["start"] - lead), p["end"] + tail
        if keeps and st - keeps[-1][1] <= a.pause - lead - tail:
            keeps[-1][1] = en
        elif keeps:
            keeps.append([max(keeps[-1][1], p["start"] - (a.keep - tail)), en])
        else:
            keeps.append([st, en])
    drops = [(max(0.0, ph[i]["start"] - 0.1), ph[i]["end"] + 0.1, ph[i]["text"], "整句重说?") for i in sorted(bad)]
    unsure = []
    for cs, ce, t in repeats(words):
        if ce - cs >= 8:
            continue
        qs, qe = snap_quiet(cs, db, thr, 0.3, 0.15), snap_quiet(ce, db, thr, 0.4, 0.05)
        if qs is not None and qe is not None and qe - qs > 0.15:
            drops.append((qs, qe, t, "句内重说"))
        else:
            unsure.append((cs, ce, t, "句内重说·没找到停顿，未剪，请听一下"))
    for ds, de, _, _ in drops:
        nxt = []
        for ks, ke in keeps:
            if de <= ks or ds >= ke:
                nxt.append([ks, ke]); continue
            if ds - ks >= 0.15: nxt.append([ks, ds])
            if ke - de >= 0.15: nxt.append([de, ke])
        keeps = nxt
    said = lambda x, y: "".join(w["text"] for w in words if x - 0.05 <= w["start"] < y - 0.05)
    lines = [("k", ks, ke, said(ks, ke)) for ks, ke in keeps] + [("d", ds, de, f"[{kind}] {t}") for ds, de, t, kind in drops + unsure]
    lines.sort(key=lambda x: x[1])
    out = ["# 保留的片段（原始录音的秒数）。改这个文件就是改剪辑决定；# 开头的行不用，[..] 是被剪掉的重说。", ""]
    for kind, x0, x1, txt in lines:
        out.append(f"{x0:.2f}-{x1:.2f}  # {txt[:40]}" if kind == "k" else f"# {x0:.2f}-{x1:.2f}  {txt[:40]}")
    open(os.path.join(work, "cuts.txt"), "w").write("\n".join(out) + "\n")
    kept = sum(ke - ks for ks, ke in keeps)
    print(f"{len(ph)} 句，整句重说 {len(bad)} 处，句内重说 {sum(1 for d in drops if d[3] == '句内重说')} 处已剪、{len(unsure)} 处待确认；建议保留 {kept:.1f}s / 原长 {dur:.1f}s")
    print(f"看 {work}/transcript_raw.md，改 {work}/cuts.txt，再跑 apply")


def apply(a):
    keep = []
    for ln in open(a.cuts):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"([\d.]+)\s*-\s*([\d.]+)", ln)
        if not m:
            sys.exit(f"看不懂这一行：{ln}")
        keep.append((float(m.group(1)), float(m.group(2))))
    keep.sort()
    for (s0, e0), (s1, e1) in zip(keep, keep[1:]):
        if s1 < e0:
            sys.exit(f"片段重叠：{s0}-{e0} 和 {s1}-{e1}")
    f, parts = [], []
    for i, (s, e) in enumerate(keep):
        d = e - s
        fd = min(0.015, d / 4)
        f.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}]")
        f.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d={fd},afade=t=out:st={d - fd}:d={fd}[a{i}]")
        parts.append(f"[v{i}][a{i}]")
    f.append("".join(parts) + f"concat=n={len(keep)}:v=1:a=1[v][a]")
    script = os.path.splitext(os.path.abspath(a.out))[0] + ".filter.txt"
    open(script, "w").write(";\n".join(f))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.recording, "-/filter_complex", script, "-map", "[v]",
                    "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", a.out], check=True)
    os.unlink(script)
    # map raw word times onto the clean timeline
    segs, t = [], 0.0
    for s, e in keep:
        segs.append({"raw_start": s, "raw_end": e, "clean_start": round(t, 3)}); t += e - s
    json.dump(segs, open(os.path.splitext(a.out)[0] + ".map.json", "w"), indent=1)
    work = os.path.dirname(os.path.abspath(a.cuts))
    wf = os.path.join(work, "words_raw.json")
    if os.path.isfile(wf):
        words = json.load(open(wf))
        clean = []
        for w in words:
            for sg in segs:
                if sg["raw_start"] <= w["start"] and w["end"] <= sg["raw_end"] + 0.02:
                    off = sg["clean_start"] - sg["raw_start"]
                    clean.append({**w, "start": round(w["start"] + off, 3), "end": round(w["end"] + off, 3)})
                    break
        clipped = []
        wav = os.path.join(work, "audio16k.wav")
        if os.path.isfile(wav):
            db, thr = energy(wav)
            for ks, ke in keep:
                for tc in (ks, ke):
                    k = int(tc * 100)
                    if 0 <= k < len(db) and db[k] > thr + 12:
                        clipped.append({"text": f"{tc:.2f}s 处 {db[k]:.0f} dB", "start": tc, "end": tc})
        json.dump(clean, open(os.path.join(work, "words_clean.json"), "w"), ensure_ascii=False, indent=0)
        md = ["# 剪后逐字稿", "", "".join(w["text"] for w in clean), ""]
        if clipped:
            md += ["## ⚠ 切点处声音还很响，可能切进了字里（在 cuts.txt 里把这个切点挪到字与字之间）", ""] + [
                f"- {w['text']}" for w in clipped]
        open(os.path.join(work, "transcript_clean.md"), "w").write("\n".join(md) + "\n")
        print(f"剪后逐字稿：{work}/transcript_clean.md" + (f"；有 {len(clipped)} 个切点可能切进了字里" if clipped else ""))
    print(f"{len(keep)} 段，剪后 {t:.1f}s → {a.out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan"); s.add_argument("recording"); s.add_argument("-o", "--out", default="work")
    s.add_argument("--pause", type=float, default=0.6); s.add_argument("--keep", type=float, default=0.3)
    p = sub.add_parser("apply"); p.add_argument("recording"); p.add_argument("cuts"); p.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    scan(a) if a.cmd == "scan" else apply(a)
