"""Transcribe every clip with local Whisper (mlx_whisper) and fail on clips that don't match the script.

usage: python3 qa_tts.py <project_dir>
Mismatched clips are renamed *.wav.bad so the next tts.py run re-synthesizes them.
"""
import difflib, hashlib, json, os, re, sys
import mlx_whisper

PROJ = os.path.abspath(sys.argv[1])
s = json.load(open(os.path.join(PROJ, "script.json")))
MODEL, VOICE = s.get("tts_model", "gemini-3.8-flash-tts"), s.get("voice", "Charon")
norm = lambda x: re.sub(r"[\s，。：？、！,.:?!；;“”\"'（）()]", "", x).lower()
bad = 0
for sc in s["scenes"]:
    for text in sc["lines"]:
        f = os.path.join(PROJ, "audio", hashlib.sha1(f"{MODEL}|{VOICE}|{text}".encode()).hexdigest()[:16] + ".wav")
        heard = mlx_whisper.transcribe(f, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="zh", initial_prompt=text)["text"]
        r = difflib.SequenceMatcher(None, norm(text), norm(heard)).ratio()
        ok = r > .8
        bad += not ok
        print(f"{'OK ' if ok else 'BAD'} {r:.2f} | {text[:22]} | {heard[:30]}")
        if not ok: os.rename(f, f + ".bad")
print("bad:", bad)
sys.exit(1 if bad else 0)
