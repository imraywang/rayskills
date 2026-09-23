#!/usr/bin/env python3
import argparse
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    print("ERROR: Pillow is required (python3 -m pip install Pillow)", file=sys.stderr)
    raise SystemExit(2)


def main():
    parser = argparse.ArgumentParser(description="Build a thumbnail contact sheet.")
    parser.add_argument("output", type=Path)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--columns", type=int, default=3)
    args = parser.parse_args()

    missing = [str(path) for path in args.images if not path.is_file()]
    if missing:
        print(f"ERROR: missing images: {', '.join(missing)}", file=sys.stderr)
        return 2
    if args.columns < 1:
        print("ERROR: --columns must be positive", file=sys.stderr)
        return 2

    thumb = (480, 270)
    gap = 24
    label_height = 34
    rows = math.ceil(len(args.images) / args.columns)
    width = gap + args.columns * (thumb[0] + gap)
    height = gap + rows * (thumb[1] + label_height + gap)
    sheet = Image.new("RGB", (width, height), "#111111")
    draw = ImageDraw.Draw(sheet)

    for index, path in enumerate(args.images):
        col = index % args.columns
        row = index // args.columns
        x = gap + col * (thumb[0] + gap)
        y = gap + row * (thumb[1] + label_height + gap)
        image = Image.open(path).convert("RGB")
        image = ImageOps.fit(image, thumb, method=Image.Resampling.LANCZOS)
        sheet.paste(image, (x, y))
        draw.text((x, y + thumb[1] + 8), path.stem[:60], fill="#F1E7D2")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=94)
    print(f"OK: {args.output} {width}x{height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
