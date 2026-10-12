"""给数字人主持人做卡通形象（一次性）。照片属于个人生物特征数据：上传前必须在对话里得到本人明确同意。

步骤：
  python3 make_avatar.py candidates <照片> --name ray   # 生成 3 版扁平卡通形象（绿幕底），给用户挑
  python3 make_avatar.py build --name ray --pick 1      # 用挑中的那版做口型 / 眨眼图层
产物在 ~/.config/ray-explainer/avatars/<name>/（不放进任何仓库）：
  flat.png（交给 Kling 的原图）、base.png（抠掉绿幕的底图）、A E I O U M.png（口型补丁）、B.png（闭眼）、meta.json（补丁位置）
费用：candidates 出 3 张图，build 出 7 张图，都走 fal 的 nano-banana-pro/edit，按 fal 当前价计。
"""
import json, os, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

EDIT = "fal-ai/nano-banana-pro/edit"
STYLE = ("Redraw this person as a FLAT 2D mascot illustration for a Chinese explainer video channel: completely flat colors, NO shading, "
         "NO gradients, NO texture, NO highlights; clean uniform thick black outlines; minimal facial lines (simple dot-like eyes with a small "
         "white highlight, simple short eyebrows, tiny nose line, simple mouth), cute proportions with a larger head (about 1/3 of the visible "
         "body). Keep the person's identity: hairstyle, hair color, face shape, clothing. Clean face without stubble. Waist-up, centered, facing "
         "the viewer, friendly closed-mouth smile, both hands visible relaxed in front of the waist. Thick white sticker outline around the "
         "whole figure. Solid flat chroma-key green background (#00B140), nothing else, no text, empty margin above the head.")
KEEP = ("Keep the image pixel-identical: same flat cartoon character, same pose, same framing, same size, same position, same lines, same "
        "white sticker outline, same flat colors, same solid green background. Only change ")
MOUTHS = {"A": "the mouth: open wide as when saying 'ah', simple flat dark-red mouth shape with a small tongue, flat style.",
          "E": "the mouth: half open, wide, as when saying 'eh', simple flat shape showing a white strip of upper teeth.",
          "I": "the mouth: slightly open in a wide flat smile as when saying 'ee', a thin white strip of teeth.",
          "O": "the mouth: open in a small round 'oh' shape, flat dark-red oval.",
          "U": "the mouth: lips pushed into a small round pucker as when saying 'oo', tiny dark opening.",
          "M": "the mouth: lips pressed together in a short flat closed line as when saying 'mm'.",
          "B": "the eyes: both eyes closed in a blink, drawn as simple short downward-curved lines. Mouth unchanged."}

def zshrc_env(name):
    if os.environ.get(name): return os.environ[name]
    for line in open(os.path.expanduser("~/.zshrc")):
        line = line.strip()
        if line.startswith(f"export {name}="): return line.split("=", 1)[1].strip().strip('"\'')
    sys.exit(f"{name} not set")
def edit(prompt, img, out, n=1, ar=None):
    import fal_client
    args = {"prompt": prompt, "image_urls": [fal_client.upload_file(img)], "num_images": n, **({"aspect_ratio": ar} if ar else {})}
    r = fal_client.subscribe(EDIT, arguments=args)
    paths = []
    for i, im in enumerate(r["images"]):
        p = out.format(i=i); urllib.request.urlretrieve(im["url"], p); paths.append(p)
    return paths

args = sys.argv[1:]
name = args[args.index("--name") + 1] if "--name" in args else "ray"
D = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "ray-explainer", "avatars", name)
os.makedirs(os.path.join(D, "work"), exist_ok=True)
os.environ["FAL_KEY"] = zshrc_env("FAL_KEY")

if args and args[0] == "candidates":
    photo = args[1]
    for p in edit(STYLE, photo, os.path.join(D, "work", "cand-{i}.png"), n=3, ar="9:16"): print(p)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *sum([["-i", os.path.join(D, "work", f"cand-{i}.png")] for i in range(3)], []),
                    "-filter_complex", "[0]scale=-2:800[a];[1]scale=-2:800[b];[2]scale=-2:800[c];[a][b][c]hstack=3", os.path.join(D, "work", "candidates.jpg")])
    print(os.path.join(D, "work", "candidates.jpg"), "← 给用户看，挑一版（0/1/2）；要改风格就改 STYLE 重跑")

elif args and args[0] == "build":
    from PIL import Image, ImageFilter
    import numpy as np, shutil
    pick = args[args.index("--pick") + 1]
    flat = os.path.join(D, "flat.png"); shutil.copy(os.path.join(D, "work", f"cand-{pick}.png"), flat)
    with ThreadPoolExecutor(7) as ex:
        list(ex.map(lambda k: edit(KEEP + MOUTHS[k], flat, os.path.join(D, "work", f"v_{k}.png")), MOUTHS))
    base = Image.open(flat).convert("RGB"); W, H = base.size; b = np.asarray(base).astype(int)
    gd = b[:, :, 1] - np.maximum(b[:, :, 0], b[:, :, 2])
    A = Image.fromarray((np.clip(1 - (gd - 15) / 40, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    rgb = b.copy(); sp = gd > 0; rgb[sp, 1] = np.maximum(rgb[sp, 0], rgb[sp, 2])            # 去绿边
    im = Image.fromarray(rgb.astype(np.uint8)); im.putalpha(A); im.save(os.path.join(D, "base.png"))
    Af = np.asarray(A).astype(float) / 255; meta = {}
    for k in MOUTHS:
        a = np.asarray(Image.open(os.path.join(D, "work", f"v_{k}.png")).convert("RGB")).astype(int)
        if a.shape != b.shape: sys.exit(f"{k}：编辑后尺寸变了 {a.shape}，重跑 build")
        d = np.abs(a - b).sum(2) > 40
        rows = np.nonzero(d.sum(1) > 4)[0]
        if not len(rows): sys.exit(f"{k}：没改动，重跑 build")
        # 只保留脸部那一块的改动：口型取下半张脸，眨眼取眼睛那一带
        y0, y1 = (int(H * .26), int(H * .36)) if k == "B" else (int(H * .34), int(H * .50))
        m = np.zeros_like(d); m[y0:y1] = d[y0:y1]
        m = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(4))
        m = np.asarray(m).astype(float) / 255 * Af
        ys, xs = np.nonzero(m > .01); x0, x1, yy0, yy1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        Image.fromarray(np.dstack([a, m * 255]).astype(np.uint8)[yy0:yy1, x0:x1], "RGBA").save(os.path.join(D, f"{k}.png"))
        meta[k] = [int(x0), int(yy0), int(x1 - x0), int(yy1 - yy0)]
    json.dump({"size": [W, H], "patches": meta}, open(os.path.join(D, "meta.json"), "w"))
    # 检查图：底图 + 每个补丁，深色底
    tiles = []
    for k in ["X", *MOUTHS]:
        c = Image.new("RGBA", (W, H), (15, 16, 19, 255)); c.alpha_composite(Image.open(os.path.join(D, "base.png")))
        if k != "X": x, y, w, h = meta[k]; c.alpha_composite(Image.open(os.path.join(D, f"{k}.png")), (x, y))
        tiles.append(c.crop((int(W * .25), int(H * .2), int(W * .75), int(H * .52))).convert("RGB"))
    tw, th = tiles[0].size; sheet = Image.new("RGB", (tw * len(tiles), th))
    for i, t in enumerate(tiles): sheet.paste(t, (i * tw, 0))
    sheet.save(os.path.join(D, "work", "layers.jpg")); print(os.path.join(D, "work", "layers.jpg"), "← 检查每个口型和眨眼有没有接缝、错位")
else:
    sys.exit(__doc__)
