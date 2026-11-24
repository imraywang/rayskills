#!/usr/bin/env python3
"""Rubber-stamp PNGs (worn ink, block font) for the 小Lin-style piece. python3 make_stamps.py -> assets/img/stamp-<id>.png
Rendered once here instead of CSS filters: deterministic and cheap for the capture engine."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "fontdl/NotoSansSC-Black.otf"
RED, GREEN = (236, 44, 40), (52, 190, 110)
STAMPS = [  # id, text, color, font px (output is half this scale)
    ("st1", "好几年不能卖", RED, 150), ("st2", "不能说不要", RED, 150),
    ("f-st", "允许捐股票", GREEN, 130), ("f-ok", "批准", GREEN, 120),
    ("t-free", "捐出 = 不算卖出", GREEN, 116), ("k-s1", "不能拒收", RED, 150), ("k-s2", "不能换", RED, 150),
    ("m-st", "选举前换成现金", RED, 140), ("b1", "税省了", RED, 140), ("b2", "股锁了", RED, 140),
    ("b3", "+7,200 万个家庭", RED, 124),
]

def noise(h, w, rng, scale):
    """Smooth value noise: random grid upsampled bicubically."""
    g = rng.random((h // scale + 2, w // scale + 2))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w + scale, h + scale), Image.BICUBIC))[:h, :w] / 255.0

def stamp(text, color, px, seed):
    rng = np.random.default_rng(seed)
    font = ImageFont.truetype(FONT, px)
    l, t, r, b = font.getbbox(text)
    tw, th = r - l, b - t
    pad, bw = int(px * 0.26), int(px * 0.13)
    W, H = tw + pad * 2 + bw * 2, th + pad * 2 + bw * 2
    m = Image.new("L", (W + 40, H + 40), 0)
    d = ImageDraw.Draw(m)
    o = 20
    d.rounded_rectangle([o, o, o + W, o + H], radius=int(px * 0.12), outline=255, width=bw)
    d.text((o + bw + pad - l, o + bw + pad - t), text, font=font, fill=255)
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(1.2))) / 255.0
    h, w = a.shape
    # worn ink: big blotches of light coverage + fine speckle holes + rough edges
    blot = noise(h, w, rng, 60)
    speck = noise(h, w, rng, 6)
    grain = rng.random((h, w))
    cover = np.clip(0.8 + 0.7 * (blot - 0.4), 0.55, 1.0)
    holes = (speck > 0.8) | (grain > 0.985)
    alpha = a * cover
    alpha[holes] *= 0.15
    alpha = np.where(alpha > 0.18, alpha, 0) * 0.92
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = color
    rgba[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    # soft dark halo under the ink so it reads on bright footage
    halo = np.asarray(m.filter(ImageFilter.GaussianBlur(18))) / 255.0 * 0.55
    out = np.zeros((h, w, 4), np.float32)
    ia = rgba[..., 3] / 255.0
    oa = ia + halo * (1 - ia)
    out[..., :3] = (np.array(color) * ia[..., None]) / np.maximum(oa, 1e-6)[..., None]
    out[..., 3] = oa * 255
    im = Image.fromarray(out.astype(np.uint8))
    return im.resize((int(w * 0.6), int(h * 0.6)), Image.LANCZOS)

if __name__ == "__main__":
    for i, (sid, text, color, px) in enumerate(STAMPS):
        im = stamp(text, color, px, 7 + i)
        im.save(f"assets/img/stamp-{sid}.png")
        print(sid, im.size)
