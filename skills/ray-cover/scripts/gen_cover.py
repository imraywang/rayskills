#!/usr/bin/env python3
"""Render covers from compiled prompts with Codex CLI's image generation (Image 2), one independent image per platform.

usage: python3 gen_cover.py <cover_dir> [--platforms wechat,x,x-article,vertical,xhs,landscape,channels,card] [--jobs 3] [--ref <photo>]

--ref: a reference image (e.g. Ray's identity photo for video covers). It is copied into <cover_dir> as ref.<ext> and passed
to codex exec with -i; the prompt tells the image tool to use it as the identity reference. Only with Ray's consent.

<cover_dir>/prompts/<platform>.md holds the complete prompt for that platform (written by the agent from the Punk blueprint).
For each platform this runs `codex exec` (stdin closed, sandbox workspace-write inside <cover_dir>) and asks it to generate
exactly one image from that prompt and copy it to <cover_dir>/raw-<platform>.png. The script then checks the aspect ratio,
resizes to the target pixels (same ratio only; a wrong ratio is reported, never cropped or stretched), writes
<platform>-cover.png, a 420px thumbnail, and manifest.json.
"""
import json, os, subprocess, sys, time
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

def run(cover_dir, plat):
    prompt = os.path.join("prompts", f"{plat}.md")
    if not os.path.exists(os.path.join(cover_dir, prompt)):
        return plat, {"ok": False, "error": f"missing {prompt}"}
    raw = f"raw-{plat}.png"
    ref = (f"把当前目录下的 {REF} 作为人物身份参考图一起交给图片生成工具（保留这个人的长相和身份，动作、表情、背景按提示词改）。" if REF else "")
    task = (f"读取 {prompt}，把其中的提示词原样交给你的图片生成工具，生成且只生成一张图（不要改写提示词、不要生成多张或拼图）。{ref}"
            f"生成后把这张图的文件复制为当前目录下的 {raw}。最后只回复 {raw} 的绝对路径。")
    t0 = time.time()
    with open(os.path.join(cover_dir, f"codex-{plat}.log"), "w") as log:
        p = subprocess.run(["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", cover_dir,
                            *(["-i", os.path.join(cover_dir, REF)] if REF else []), "--", task],   # -i takes many values: "--" keeps the task out of it
                           stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, timeout=1500)
    rp = os.path.join(cover_dir, raw)
    if p.returncode != 0 or not os.path.exists(rp):
        return plat, {"ok": False, "error": f"codex exit {p.returncode}, no {raw} (see codex-{plat}.log)"}
    im = Image.open(rp); tw, th = SIZES[plat]; r, tr = im.width / im.height, tw / th
    info = {"raw": raw, "raw_size": list(Image.open(rp).size), "seconds": round(time.time() - t0)}
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
    global REF
    if "--ref" in a:
        import shutil
        src = a[a.index("--ref") + 1]; REF = "ref" + os.path.splitext(src)[1].lower()
        shutil.copyfile(src, os.path.join(cover_dir, REF))
    bad = [p for p in plats if p not in SIZES]
    if bad: sys.exit(f"unknown platform {bad}; use {list(SIZES)}")
    with ThreadPoolExecutor(jobs) as ex: res = dict(ex.map(lambda p: run(cover_dir, p), plats))
    mp = os.path.join(cover_dir, "manifest.json"); man = json.load(open(mp)) if os.path.exists(mp) else {}
    man.setdefault("outputs", {}).update(res); man["generator"] = "codex exec · image_generation (Image 2)"
    json.dump(man, open(mp, "w"), ensure_ascii=False, indent=2)
    for p, r in res.items(): print(f"{p:10} {'OK  ' + r['file'] if r['ok'] else 'FAIL ' + r['error']}")
    sys.exit(0 if all(r["ok"] for r in res.values()) else 1)

if __name__ == "__main__":
    main()
