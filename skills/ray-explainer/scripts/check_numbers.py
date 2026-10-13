"""Verify how numbers were actually voiced (Whisper cannot: it writes digits whatever was said).

usage: python3 check_numbers.py <project_dir>      (after qa_tts.py; needs GEMINI_API_KEY)

For every line whose voiced text contains a number (Arabic digits or hanzi numerals next to 年/月/号/个/万/亿/%),
cut the first ~3 s around it and ask Gemini for a literal syllable transcription with numbers written as heard.
Prints voiced text vs heard reading so you can spot 两千零一十九 where 二零一九 was meant. Costs a few cents at most.
"""
import base64, json, os, re, subprocess, sys, tempfile, urllib.request

PROJ = os.path.abspath(sys.argv[1])
tl = json.load(open(os.path.join(PROJ, "timeline.json")))
key = os.environ.get("GEMINI_API_KEY")
if not key:
    for l in open(os.path.expanduser("~/.zshrc")):
        if l.strip().startswith("export GEMINI_API_KEY="): key = l.split("=", 1)[1].strip().strip("\"'")
if not key: sys.exit("GEMINI_API_KEY not set")
NUM = re.compile(r"\d|[零〇一二三四五六七八九十百千两]+(?=[年月号日个万亿%点])")
ASK = ("逐字写出这段中文语音实际念出的每个音节（汉字），数字必须按实际读法写成汉字："
       "念成“两千零一十九”就写“两千零一十九”，念成“二零一九”就写“二零一九”。只输出转写。")
for sc in tl["scenes"]:
    for ln in sc["lines"]:
        spoken = ln.get("spoken", ln["text"])
        m = NUM.search(spoken)
        if not m: continue
        t0 = ln["chars"][m.start()] if ln.get("chars") and m.start() < len(ln["chars"]) else ln["start"]
        with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(max(ln["start"], t0 - 0.3)), "-t", "3",
                            "-i", os.path.join(PROJ, "narration.wav"), f.name], check=True)
            body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(open(f.name, "rb").read()).decode()}}, {"text": ASK}]}]}
        req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
                                     data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        heard = json.load(urllib.request.urlopen(req, timeout=60))["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"{sc['id']:10} {spoken[max(0, m.start() - 4):m.start() + 12]:<20} → 听到：{heard}")
