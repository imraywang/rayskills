#!/usr/bin/env python3
"""Render covers from compiled prompts, one independent image per platform.

usage: python3 gen_cover.py <cover_dir> [--platforms wechat,x,x-article,vertical,xhs,landscape,channels,card] [--jobs 3]
                            [--ref <photo>] [--backend api|codex] [--edit]

--backend api (default when OPENAI_API_KEY is set, env or ~/.zshenv): OpenAI Images API, model gpt-image-2.5-sunburst.
    With --ref it calls /v1/images/edits with the photo as the identity reference, otherwise /v1/images/generations.
    About 30–50 s and ~$0.07 per image (2026-10-15/16). Native sizes: xhs 1200×1600 is verified; if the API rejects a
    size for another platform the error says so — rerun that platform with --backend codex.
--backend codex: Codex CLI's image generation (Image 2) via `codex exec` (stdin closed, sandbox workspace-write inside
    <cover_dir>), 1–5 min per image. Needs `codex` logged in with the image_generation feature on.
--ref: a reference image (e.g. Ray's identity photo for video covers), copied into <cover_dir> as ref.<ext>. Only with
    Ray's consent (the photo is sent to OpenAI).
--edit (api only): change a finished cover locally instead of regenerating — composition and face stay. Takes
    raw-<platform>.png as the input image and prompts/<platform>-edit.md as the instruction ("只做一处修改：去掉胸前的领夹麦，
    其余一切保持不变…"). The previous raw / cover / thumb are kept as -v1, -v2 … before being replaced.

<cover_dir>/prompts/<platform>.md holds the complete prompt for that platform (written by the agent). The script writes
<cover_dir>/raw-<platform>.png, checks the aspect ratio, resizes to the target pixels (same ratio only; a wrong ratio is
reported, never cropped or stretched), writes <platform>-cover.png, a 420px thumbnail, and manifest.json.
"""
import base64, glob, json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

SIZES = {"wechat": (2100, 900), "x": (1600, 900), "x-article": (1600, 640),
         "vertical": (1080, 1920), "xhs": (1080, 1440),   # 9:16 抖音 / 视频号；3:4 小红书 / 视频号信息流
         "landscape": (1920, 1080),                       # 16:9 横屏视频：YouTube、视频号 / 抖音横屏
         "channels": (1080, 1260),                        # 6:7 视频号主页（横屏视频的竖版封面）
         "card": (1440, 1080)}                            # 4:3 横版：视频号「编辑分享卡片」（聊天、朋友圈）
PAD = {"channels": 1.0, "card": 1.5}   # Image 2 has no 6:7 / 4:3: generate 1:1 / 3:2, then extend the plain paper background
JPEG = {"landscape"}   # 另存一份 jpg：YouTube 缩略图上限 2 MB，1920×1080 的 png 常常超
RATIO_TOL = 0.02

REF = None   # file name of the reference image inside cover_dir, when --ref is given
BACKEND = "codex"
EDIT = False
API_MODEL = "gpt-image-2.5-sunburst"
# native request sizes for the API (padded platforms ask for the 1:1 / 3:2 they are padded from)
API_SIZE = {"xhs": "1200x1600", "vertical": "1080x1920", "landscape": "1920x1080", "wechat": "2100x900", "x": "1600x900",
            "x-article": "1600x640", "channels": "1200x1200", "card": "1536x1024"}


def api_key():
    k = os.environ.get("OPENAI_API_KEY")
    if not k and os.path.exists(os.path.expanduser("~/.zshenv")):
        m = re.search(r"^\s*export\s+OPENAI_API_KEY=[\"']?([^\"'\s]+)", open(os.path.expanduser("~/.zshenv")).read(), re.M)
        k = m.group(1) if m else None
    return k


def gen_api(cover_dir, plat, prompt_file, image=None):
    """One image from the OpenAI Images API into raw-<plat>.png. image = input picture (identity ref or the cover to edit)."""
    key = api_key()
    if not key: return "OPENAI_API_KEY not set (env or ~/.zshenv): use --backend codex"
    url = "https://api.openai.com/v1/images/" + ("edits" if image else "generations")
    cmd = ["curl", "-sS", "--max-time", "600", url, "-H", f"Authorization: Bearer {key}"]
    if image:
        cmd += ["-F", f"model={API_MODEL}", "-F", f"size={API_SIZE[plat]}", "-F", "n=1",
                "-F", f"image=@{image}", "-F", f"prompt=<{prompt_file}"]
    else:
        body = {"model": API_MODEL, "size": API_SIZE[plat], "n": 1, "prompt": open(prompt_file).read()}
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body, ensure_ascii=False)]
    with open(os.path.join(cover_dir, f"api-{plat}.log"), "w") as log:
        p = subprocess.run(cmd, capture_output=True, text=True)
        try:
            d = json.loads(p.stdout)
        except ValueError:
            log.write(p.stdout + p.stderr); return f"API returned no JSON (see api-{plat}.log)"
        if "data" not in d:
            log.write(json.dumps(d, ensure_ascii=False, indent=1)); return f"API error: {json.dumps(d.get('error', d), ensure_ascii=False)[:300]}"
        log.write(json.dumps({k: v for k, v in d.items() if k != "data"}, ensure_ascii=False, indent=1))
    open(os.path.join(cover_dir, f"raw-{plat}.png"), "wb").write(base64.b64decode(d["data"][0]["b64_json"]))
    return None


def keep_old(cover_dir, plat):
    """raw / cover / thumb / jpg of this platform → -vN before an edit replaces them."""
    n = 1
    while glob.glob(os.path.join(cover_dir, f"raw-{plat}-v{n}.png")): n += 1
    for f in (f"raw-{plat}.png", f"{plat}-cover.png", f"{plat}-thumb.jpg", f"{plat}-cover.jpg"):
        src = os.path.join(cover_dir, f)
        if os.path.exists(src):
            b, e = os.path.splitext(f); shutil.copyfile(src, os.path.join(cover_dir, f"{b}-v{n}{e}"))
    return n


def run(cover_dir, plat):
    t0 = time.time()
    if EDIT:
        prompt = os.path.join("prompts", f"{plat}-edit.md"); raw_in = os.path.join(cover_dir, f"raw-{plat}.png")
        if not os.path.exists(os.path.join(cover_dir, prompt)) or not os.path.exists(raw_in):
            return plat, {"ok": False, "error": f"--edit needs {prompt} and raw-{plat}.png"}
        v = keep_old(cover_dir, plat)
        err = gen_api(cover_dir, plat, os.path.join(cover_dir, prompt), os.path.join(cover_dir, f"raw-{plat}-v{v}.png"))
        if err: return plat, {"ok": False, "error": err}
        return finish(cover_dir, plat, t0, {"edit_of": f"raw-{plat}-v{v}.png"})
    prompt = os.path.join("prompts", f"{plat}.md")
    if not os.path.exists(os.path.join(cover_dir, prompt)):
        return plat, {"ok": False, "error": f"missing {prompt}"}
    if BACKEND == "api":
        err = gen_api(cover_dir, plat, os.path.join(cover_dir, prompt), os.path.join(cover_dir, REF) if REF else None)
        if err: return plat, {"ok": False, "error": err}
        return finish(cover_dir, plat, t0)
    raw = f"raw-{plat}.png"
    ref = (f"把当前目录下的 {REF} 作为人物身份参考图一起交给图片生成工具（保留这个人的长相和身份，动作、表情、背景按提示词改）。" if REF else "")
    task = (f"读取 {prompt}，把其中的提示词原样交给你的图片生成工具，生成且只生成一张图（不要改写提示词、不要生成多张或拼图）。{ref}"
            f"生成后把这张图的文件复制为当前目录下的 {raw}。最后只回复 {raw} 的绝对路径。")
    with open(os.path.join(cover_dir, f"codex-{plat}.log"), "w") as log:
        p = subprocess.run(["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", cover_dir,
                            *(["-i", os.path.join(cover_dir, REF)] if REF else []), "--", task],   # -i takes many values: "--" keeps the task out of it
                           stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, timeout=1500)
    rp = os.path.join(cover_dir, raw)
    if p.returncode != 0 or not os.path.exists(rp):
        return plat, {"ok": False, "error": f"codex exit {p.returncode}, no {raw} (see codex-{plat}.log)"}
    return finish(cover_dir, plat, t0)


def finish(cover_dir, plat, t0, extra_info=None):
    raw = f"raw-{plat}.png"; rp = os.path.join(cover_dir, raw)
    im = Image.open(rp); tw, th = SIZES[plat]; r, tr = im.width / im.height, tw / th
    info = {"raw": raw, "raw_size": list(Image.open(rp).size), "seconds": round(time.time() - t0), "backend": "api" if (BACKEND == "api" or EDIT) else "codex", **(extra_info or {})}
    if plat in PAD and abs(r - PAD[plat]) / PAD[plat] <= RATIO_TOL:
        # extend with plain paper (colour + grain sampled from an edge band that holds only background) — never crop,
        # stretch or mirror. A plain edge gets padding; an edge the subject runs off (e.g. a body at the bottom) gets none.
        import numpy as np
        src = im.convert("RGB"); a = np.asarray(src).astype(float); w = im.width; h = round(w / tr); extra = h - im.height
        def plain(rows):
            m = np.median(rows.reshape(-1, 3), 0); return (np.abs(rows - m).sum(2) > 40).mean() < 0.01, m, rows.std(0).mean()
        pt, mt, st = plain(a[:12]); pb, mb, sb = plain(a[-12:])
        top = extra // 2 if pt and pb else (extra if pt else 0)
        if not (pt or pb): info = {**info, "ok": False, "error": "no plain edge to pad: regenerate with plain margins"}; return plat, info
        band = lambda n, m, sd: Image.fromarray(np.clip(m + np.random.default_rng(n).normal(0, min(sd, 4), (n, w, 1)), 0, 255).astype("uint8"))
        canvas = Image.new("RGB", (w, h)); canvas.paste(src, (0, top))
        if top: canvas.paste(band(top, mt, st), (0, 0))
        if extra - top: canvas.paste(band(extra - top, mb, sb), (0, top + im.height))
        im = canvas; r = w / h; info_pad = f"padded {top}px top, {extra - top}px bottom of paper"
    else: info_pad = None
    if abs(r - tr) / tr > RATIO_TOL:
        info.update(ok=False, error=f"ratio {r:.3f} ≠ target {tr:.3f}: regenerate this platform, do not crop")
        return plat, info
    if info_pad: info["pad"] = info_pad
    out = f"{plat}-cover.png"; big = im.convert("RGB").resize((tw, th), Image.LANCZOS); big.save(os.path.join(cover_dir, out))
    if plat in JPEG: big.save(os.path.join(cover_dir, f"{plat}-cover.jpg"), quality=90); info["jpg"] = f"{plat}-cover.jpg"
    thumb = im.convert("RGB"); thumb.thumbnail((420, 420)); thumb.save(os.path.join(cover_dir, f"{plat}-thumb.jpg"), quality=88)
    info.update(ok=True, file=out, size=[tw, th], thumb=f"{plat}-thumb.jpg")
    return plat, info

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if "-h" in a or "--help" in a: print(__doc__); sys.exit(0)
    cover_dir = os.path.abspath(a[0])
    plats = (a[a.index("--platforms") + 1] if "--platforms" in a else "wechat,x,x-article").split(",")
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 3
    global REF, BACKEND, EDIT
    BACKEND = a[a.index("--backend") + 1] if "--backend" in a else ("api" if api_key() else "codex")
    EDIT = "--edit" in a
    if BACKEND not in ("api", "codex"): sys.exit("--backend api|codex")
    if EDIT and not api_key(): sys.exit("--edit needs the API (OPENAI_API_KEY)")
    if "--ref" in a:
        src = a[a.index("--ref") + 1]; REF = "ref" + os.path.splitext(src)[1].lower()
        shutil.copyfile(src, os.path.join(cover_dir, REF))
    bad = [p for p in plats if p not in SIZES]
    if bad: sys.exit(f"unknown platform {bad}; use {list(SIZES)}")
    with ThreadPoolExecutor(jobs) as ex: res = dict(ex.map(lambda p: run(cover_dir, p), plats))
    mp = os.path.join(cover_dir, "manifest.json"); man = json.load(open(mp)) if os.path.exists(mp) else {}
    man.setdefault("outputs", {}).update(res); man["generator"] = f"OpenAI Images API · {API_MODEL}" if (BACKEND == "api" or EDIT) else "codex exec · image_generation (Image 2)"
    json.dump(man, open(mp, "w"), ensure_ascii=False, indent=2)
    for p, r in res.items(): print(f"{p:10} {'OK  ' + r['file'] if r['ok'] else 'FAIL ' + r['error']}")
    sys.exit(0 if all(r["ok"] for r in res.values()) else 1)

if __name__ == "__main__":
    main()
