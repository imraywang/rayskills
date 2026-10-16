"""One still per caption, tiled into labelled contact sheets — HyperFrames mode's version of render.js sheet.

usage: python3 cap_sheet.py <project> [--scene <id>[,<id>…]] [--per 12]
       (after make_beats.py + build.py; writes <project>/hf/.capsheet/sheet-NN.jpg and prints their paths)

Every caption is one visual beat, so every caption gets a frame, taken at 75% of its span (the end state
of that beat). An evenly spaced sheet skips whole beats: in 2026-10-15 《AI 游客》 18 even frames missed both the
100 元 / 77 元 overlap and the near-empty opening of the 妙鸭 scene. Read each sheet and look for: an empty
or unchanged frame next to a new caption, overlapping elements, text under the caption bar or the host.
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

PROJ = os.path.abspath(sys.argv[1])
HF = os.path.join(PROJ, "hf")
args = sys.argv[2:]
only = set(args[args.index("--scene") + 1].split(",")) if "--scene" in args else None
PER = int(args[args.index("--per") + 1]) if "--per" in args else 12
B = json.load(open(os.path.join(HF, "beats.json")))

shots = []   # (global t, scene id, caption)
for s in B["scenes"]:
    if only and s["id"] not in only: continue
    for c in s["caps"]:
        shots.append((round(s["start"] + c["a"] + 0.75 * (c["b"] - c["a"]), 2), s["id"], c["s"]))
if not shots: sys.exit("no captions matched")

OUT = os.path.join(HF, ".capsheet"); RAW = os.path.join(OUT, "raw")
os.makedirs(RAW, exist_ok=True)
for f in os.listdir(OUT):
    if f.startswith("sheet-"): os.remove(os.path.join(OUT, f))
for i in range(0, len(shots), 40):   # a few dozen timestamps per snapshot call keeps each browser session short
    at = ",".join(f"{t:g}" for t, _, _ in shots[i:i + 40])
    subprocess.run(["npx", "hyperframes", "snapshot", HF, "--at", at, "--no-end", "--keep", "--describe", "false", "-o", RAW],
                   check=True, stdout=subprocess.DEVNULL)

try: font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 30)
except OSError: font = ImageFont.load_default()
TW, COLS = 360, 6
sheets = []
for k in range(0, len(shots), PER):
    chunk = shots[k:k + PER]
    tiles = []
    for t, sid, cap in chunk:
        im = Image.open(os.path.join(RAW, f"at-{t:g}s.png")).convert("RGB")
        im = im.resize((TW, round(im.height * TW / im.width)))
        tile = Image.new("RGB", (TW, im.height + 80), "white"); tile.paste(im, (0, 0))
        d = ImageDraw.Draw(tile)
        d.text((8, im.height + 6), f"{t:g}s · {sid}", fill="#555", font=font)
        d.text((8, im.height + 42), cap[:11], fill="black", font=font)
        tiles.append(tile)
    rows = -(-len(tiles) // COLS); th = tiles[0].height
    sheet = Image.new("RGB", (COLS * TW + (COLS - 1) * 6, rows * th + (rows - 1) * 6), "#888")
    for j, tile in enumerate(tiles): sheet.paste(tile, ((j % COLS) * (TW + 6), (j // COLS) * (th + 6)))
    p = os.path.join(OUT, f"sheet-{k // PER + 1:02d}.jpg"); sheet.save(p, quality=82); sheets.append(p)
print(f"{len(shots)} captions → {len(sheets)} sheets")
for p in sheets: print(p)
