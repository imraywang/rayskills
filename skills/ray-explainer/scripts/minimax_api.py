"""Direct MiniMax API (no fal): text-to-speech, file upload, voice cloning. Standard library only.

Auth: MINIMAX_API_KEY (shell env, else an `export MINIMAX_API_KEY=...` line in ~/.zshrc).
Host: MINIMAX_API_HOST (env or ~/.zshrc), default https://api.minimax.io (international). Keys from the
mainland-China platform (platform.minimax.cn) only work on https://api.minimax.cn — same paths and fields.
Cloning on the China platform requires personal or company verification on the account first.
"""
import json, os, sys, urllib.request, uuid


def _env(name, default=None):
    if os.environ.get(name): return os.environ[name]
    try:
        for line in open(os.path.expanduser("~/.zshrc")):
            line = line.strip()
            if line.startswith(f"export {name}="): return line.split("=", 1)[1].strip().strip('"\'')
    except OSError: pass
    if default is not None: return default
    sys.exit(f"{name} not set (env or ~/.zshrc)")


HOST = _env("MINIMAX_API_HOST", "https://api.minimax.io").rstrip("/")


def _call(path, body=None, data=None, ctype="application/json", timeout=180):
    req = urllib.request.Request(HOST + path, data if data is not None else json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + _env("MINIMAX_API_KEY"), "Content-Type": ctype})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    br = r.get("base_resp") or {}
    if br.get("status_code", 0) != 0:
        raise RuntimeError(f"MiniMax {path}: {br.get('status_code')} {br.get('status_msg')}")
    return r


def tts(text, voice_id, model="speech-2.8-hd", speed=1.0, emotion=None):
    """→ (mp3 bytes, extra_info). extra_info carries usage_characters and audio_length (ms)."""
    vs = {"voice_id": voice_id, "speed": speed, "vol": 1, "pitch": 0}
    if emotion: vs["emotion"] = emotion
    r = _call("/v1/t2a_v2", {"model": model, "text": text, "stream": False, "voice_setting": vs, "language_boost": "Chinese",
                             "audio_setting": {"format": "mp3", "sample_rate": 32000, "bitrate": 128000, "channel": 1},
                             "output_format": "hex"})
    return bytes.fromhex(r["data"]["audio"]), r.get("extra_info") or {}


def upload(path, purpose="voice_clone"):
    """multipart upload → file_id. purpose: voice_clone (10 s–5 min, ≤20 MB) or prompt_audio (<8 s)."""
    b = uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\n{purpose}\r\n'
            f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(path)}"\r\n'
            f'Content-Type: application/octet-stream\r\n\r\n').encode() + open(path, "rb").read() + f"\r\n--{b}--\r\n".encode()
    return _call("/v1/files/upload", data=body, ctype=f"multipart/form-data; boundary={b}")["file"]["file_id"]


def clone(file_id, voice_id, preview_text=None, model="speech-2.8-hd"):
    """Register file_id as voice_id (8–256 chars, starts with a letter, [A-Za-z0-9_-], unique). → demo_audio URL or None.
    MiniMax deletes a cloned voice that is not used for TTS within 7 days."""
    body = {"file_id": file_id, "voice_id": voice_id, "need_noise_reduction": True, "need_volume_normalization": True}
    if preview_text: body.update(text=preview_text, model=model)
    return _call("/v1/voice_clone", body).get("demo_audio") or None
