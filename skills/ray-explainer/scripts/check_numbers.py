"""Verify how numbers were actually voiced (Whisper cannot: it writes digits whatever was said).

usage: python3 check_numbers.py <project_dir>      (after qa_tts.py; needs GEMINI_API_KEY)

For every line whose voiced text contains a number (Arabic digits or hanzi numerals next to 年/月/号/个/万/亿/%),
cut the first ~3 s around it and ask Gemini for a literal syllable transcription with numbers written as heard.
Prints voiced text vs heard reading so you can spot 两千零一十九 where 二零一九 was meant. Costs a few cents at most.

Polyphones are NOT checked by Gemini: it transcribes by meaning (2026-10-16 it "heard" MiniMax's misread 几十万行人
xíng rén as háng rén, and on sub-second cuts it guessed at random). Instead every POLY that lint_readings.py lists
is cut (1.6 s around the character, 0.5 s silence between) into <project>/poly_listen.wav with the order printed —
hand it to Ray with the cut ("这几处多音字听一下"), a few seconds of listening.
"""
import base64, json, os, re, subprocess, sys, tempfile, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lint_readings

PROJ = os.path.abspath(sys.argv[1])
tl = json.load(open(os.path.join(PROJ, "timeline.json")))
WAV = os.path.join(PROJ, "narration.wav")
NUM = re.compile(r"\d|[零〇一二三四五六七八九十百千两]+(?=[年月号日个万亿%点])")
ASK = ("逐字写出这段中文语音实际念出的每个音节（汉字），数字必须按实际读法写成汉字："
       "念成“两千零一十九”就写“两千零一十九”，念成“二零一九”就写“二零一九”。只输出转写。")


def at(ln, i):
    return ln["chars"][i] if ln.get("chars") and i < len(ln["chars"]) else ln["start"]


def gemini_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        for l in open(os.path.expanduser("~/.zshrc")):
            if l.strip().startswith("export GEMINI_API_KEY="): key = l.split("=", 1)[1].strip().strip("\"'")
    if not key: sys.exit("GEMINI_API_KEY not set")
    return key


def listen(t_from, dur, key):
    with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t_from), "-t", str(dur), "-i", WAV, f.name], check=True)
        body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(open(f.name, "rb").read()).decode()}}, {"text": ASK}]}]}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))["candidates"][0]["content"]["parts"][0]["text"].strip()


nums = [(sc, ln, m) for sc in tl["scenes"] for ln in sc["lines"] for m in [NUM.search(ln.get("spoken", ln["text"]))] if m]
if nums:
    key = gemini_key()
    for sc, ln, m in nums:
        spoken = ln.get("spoken", ln["text"])
        heard = listen(max(ln["start"], at(ln, m.start()) - 0.3), 3, key)
        print(f"{sc['id']:10} {spoken[max(0, m.start() - 4):m.start() + 12]:<20} → 听到：{heard}")

polys = [(sc, ln, hit) for sc in tl["scenes"] for ln in sc["lines"] for hit in lint_readings.polyphones(ln.get("spoken", ln["text"]))]
out = os.path.join(PROJ, "poly_listen.wav")
if not polys:
    if os.path.exists(out): os.remove(out)
    print("多音字：无")
else:
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for k, (sc, ln, (i, c, ctx, guess, reason)) in enumerate(polys):
            t = max(ln["start"], at(ln, i) - 0.8)
            p = os.path.join(tmp, f"{k:02d}.wav")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-t", "1.6", "-i", WAV,
                            "-af", "afade=t=in:d=0.05,afade=t=out:st=1.5:d=0.1,apad=pad_dur=0.5", "-ar", "24000", "-ac", "1", p], check=True)
            parts.append(p)
        lst = os.path.join(tmp, "list.txt")
        open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, out], check=True)
    print(f"\n多音字 {len(polys)} 处 → {out}（按顺序每段 1.6 秒，请人听；读错就换同音字 + display 映射后重配那一句）")
    for k, (sc, ln, (i, c, ctx, guess, reason)) in enumerate(polys, 1):
        want = lint_readings.MEASURE[c][0] if reason == "measure" else guess
        print(f"  {k}. {sc['id']:10} {at(ln, i):7.2f}s  {c} …{ctx}…  应读 {want}")
