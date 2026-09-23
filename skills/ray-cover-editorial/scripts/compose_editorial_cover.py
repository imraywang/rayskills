#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    print("ERROR: Pillow is required (python3 -m pip install Pillow)", file=sys.stderr)
    raise SystemExit(2)


SIZES = {
    "wechat": (2100, 900),
    "x": (1600, 900),
    "x_article": (1600, 640),
}
LATIN_FONTS = (
    "/System/Library/Fonts/Supplemental/Bodoni 72 Smallcaps Book.ttf",
    "/System/Library/Fonts/Supplemental/Didot.ttc",
    "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
)
CJK_FONTS = (
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/truetype/noto/NotoSerifCJK-Bold.ttc",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Optional manual compositor; the base-only skill does not call this automatically."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--platform", choices=SIZES, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mark")
    group.add_argument("--logo", type=Path)
    parser.add_argument("--font", type=Path)
    parser.add_argument("--mark-color", default="#F1E7D2")
    parser.add_argument("--stroke-color", default="#151515")
    parser.add_argument("--width-ratio", type=float, default=0.15)
    parser.add_argument("--overlay-color", default="#151515")
    parser.add_argument("--overlay-opacity", type=float, default=0.0)
    return parser.parse_args()


def contains_cjk(text):
    return any("\u3400" <= char <= "\u9fff" for char in text)


def choose_font(text, explicit):
    if explicit:
        if not explicit.is_file():
            raise FileNotFoundError(f"font not found: {explicit}")
        return explicit
    candidates = CJK_FONTS if contains_cjk(text) else LATIN_FONTS
    for candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return path
    raise FileNotFoundError("no suitable system font found; pass --font")


def fit_font(draw, text, font_path, max_width, max_height):
    size = max(18, int(max_height))
    while size >= 18:
        font = ImageFont.truetype(str(font_path), size=size)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=0)
        if box[2] - box[0] <= max_width and box[3] - box[1] <= max_height:
            return font
        size -= max(1, size // 24)
    raise ValueError("mark cannot fit the requested width")


def add_text_mark(image, text, font_path, color, stroke_color, width_ratio):
    draw = ImageDraw.Draw(image)
    width, height = image.size
    max_width = width * width_ratio
    max_height = height * 0.16
    font = fit_font(draw, text, font_path, max_width, max_height)
    stroke_width = max(1, round(height / 360))
    box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_width = box[2] - box[0]
    text_height = box[3] - box[1]
    x = (width - text_width) / 2 - box[0]
    y = (height - text_height) / 2 - box[1]
    draw.text(
        (x, y),
        text,
        font=font,
        fill=color,
        stroke_width=stroke_width,
        stroke_fill=stroke_color,
    )


def add_logo(image, logo_path, width_ratio):
    if not logo_path or not logo_path.is_file():
        raise FileNotFoundError(f"logo not found: {logo_path}")
    with Image.open(logo_path) as source:
        if source.format != "PNG" or logo_path.suffix.lower() != ".png":
            raise ValueError("logo must be a PNG file")
        logo = source.convert("RGBA")
    if logo.getchannel("A").getextrema()[0] == 255:
        raise ValueError("logo PNG must contain transparent pixels")
    width, height = image.size
    max_width = int(width * width_ratio)
    max_height = int(height * 0.18)
    scale = min(max_width / logo.width, max_height / logo.height)
    size = (max(1, int(logo.width * scale)), max(1, int(logo.height * scale)))
    logo = logo.resize(size, Image.Resampling.LANCZOS)
    position = ((width - size[0]) // 2, (height - size[1]) // 2)
    image.alpha_composite(logo, position)


def add_overlay(image, color, opacity):
    overlay = Image.new("RGBA", image.size, color)
    overlay.putalpha(round(255 * opacity))
    image.alpha_composite(overlay)


def main():
    args = parse_args()
    if not 0.08 <= args.width_ratio <= 0.22:
        print("ERROR: --width-ratio must be between 0.08 and 0.22", file=sys.stderr)
        return 2
    if not 0.0 <= args.overlay_opacity <= 0.30:
        print("ERROR: --overlay-opacity must be between 0.0 and 0.30", file=sys.stderr)
        return 2
    if not args.input.is_file():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 2

    target_size = SIZES[args.platform]
    image = Image.open(args.input).convert("RGBA")
    image = ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS)

    try:
        if args.overlay_opacity > 0:
            add_overlay(image, args.overlay_color, args.overlay_opacity)
        if args.logo:
            add_logo(image, args.logo, args.width_ratio)
        else:
            font_path = choose_font(args.mark, args.font)
            add_text_mark(
                image,
                args.mark.strip(),
                font_path,
                args.mark_color,
                args.stroke_color,
                args.width_ratio,
            )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(args.output, quality=95)
    print(f"OK: {args.output} {target_size[0]}x{target_size[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
