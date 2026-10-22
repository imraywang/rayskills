#!/usr/bin/env python3
"""Board / desk backgrounds as PNG (radial vignettes pre-rendered: CSS radial-gradient on many elements makes
HyperFrames capture black frames). python3 make_bg.py -> assets/img/board.png, desk.png"""
import numpy as np
from PIL import Image

W, H = 1920, 1080
y, x = np.mgrid[0:H, 0:W]

def rad(c0, c1, c2, name, cx=0.5, cy=0.4):
    d = np.clip(np.sqrt(((x - cx * W) / (W * 0.75)) ** 2 + ((y - cy * H) / (H * 0.85)) ** 2), 0, 1)[..., None]
    c0, c1, c2 = (np.array(c, float) for c in (c0, c1, c2))
    img = np.where(d < 0.55, c0 + (c1 - c0) * (d / 0.55), c1 + (c2 - c1) * ((d - 0.55) / 0.45))
    img += np.random.default_rng(1).normal(0, 1.2, img.shape)  # dither against banding
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(f"assets/img/{name}.png")

rad((29, 38, 56), (18, 24, 37), (11, 14, 20), "board")
rad((58, 42, 30), (34, 23, 15), (18, 12, 8), "desk")
