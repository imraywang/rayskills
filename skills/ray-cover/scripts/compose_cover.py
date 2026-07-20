#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SIZES = {"wechat": (2100, 900), "x": (1600, 900), "x-article": (1600, 640)}
FONT_CANDIDATES = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]
SERIF_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc",
]


def font_path(explicit):
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"font not found: {path}")
        return str(path)
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError("no supported CJK font found; pass --font")


def serif_font_path(explicit):
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"serif font not found: {path}")
        return str(path)
    for candidate in SERIF_FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return font_path(None)


def fit_background(image, size, layout):
    centering = {"left": (0.62, 0.5), "right": (0.38, 0.5), "center": (0.5, 0.5)}[layout]
    return ImageOps.fit(image.convert("RGB"), size, method=Image.Resampling.LANCZOS, centering=centering)


def fit_font(draw, text, path, max_size, min_size, max_width, stroke=0, index=0):
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(path, size, index=index)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        if box[2] - box[0] <= max_width:
            return font
    return ImageFont.truetype(path, min_size, index=index)


def draw_top(draw, x, y, text, font, fill):
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((x - box[0], y - box[1]), text, font=font, fill=fill)
    return box[2] - box[0], box[3] - box[1]


def draw_tracked(draw, x, y, text, font, fill, tracking):
    cursor = x
    for char in text:
        draw_top(draw, cursor, y, char, font, fill)
        cursor += draw.textlength(char, font=font) + tracking
    return cursor - x - tracking if text else 0


def parse_color(value):
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError("colors must be six-digit hex values")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def main():
    parser = argparse.ArgumentParser(description="Compose exact CJK text over a no-text cover background")
    parser.add_argument("--background", required=True)
    parser.add_argument("--title", required=True, help="Use | for an intentional line break")
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--eyebrow", default="")
    parser.add_argument("--platform", choices=SIZES, required=True)
    parser.add_argument("--layout", choices=["left", "right", "center"], default="left")
    parser.add_argument("--title-mode", choices=["keyword", "hero", "balanced"], default="hero")
    parser.add_argument("--keyword", default="", help="Focal Han character or short word for keyword mode")
    parser.add_argument("--text-color", default="#171717")
    parser.add_argument("--accent-color", default="#C75B32")
    parser.add_argument("--font")
    parser.add_argument("--serif-font")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    width, height = SIZES[args.platform]
    source = Image.open(args.background)
    canvas = fit_background(source, (width, height), args.layout).convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    if args.layout == "left":
        for x in range(int(width * 0.58)):
            alpha = int(225 * (1 - x / (width * 0.58)) ** 1.7)
            odraw.line((x, 0, x, height), fill=(246, 239, 222, alpha))
    elif args.layout == "right":
        start = int(width * 0.42)
        for x in range(start, width):
            alpha = int(225 * ((x - start) / (width - start)) ** 1.7)
            odraw.line((x, 0, x, height), fill=(246, 239, 222, alpha))
    else:
        odraw.rectangle((int(width * 0.16), int(height * 0.16), int(width * 0.84), int(height * 0.84)), fill=(246, 239, 222, 210))

    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)
    cjk_font = font_path(args.font)
    serif_font = serif_font_path(args.serif_font)
    text_color = parse_color(args.text_color)
    accent = parse_color(args.accent_color)
    margin_x = int(width * 0.07)
    if args.layout == "right":
        block_left, block_right = int(width * 0.48), width - margin_x
        anchor = "ra"
        x = block_right
    elif args.layout == "center":
        block_left, block_right = int(width * 0.14), int(width * 0.86)
        anchor = "ma"
        x = width // 2
    else:
        block_left, block_right = margin_x, int(width * 0.52)
        anchor = "la"
        x = block_left
    max_text_width = block_right - block_left

    y = int(height * (0.13 if args.title_mode == "keyword" else 0.16 if args.title_mode == "hero" else 0.21))
    if args.eyebrow:
        eyebrow_font = ImageFont.truetype(cjk_font, max(24, int(height * 0.035)))
        bar_width = int(width * 0.045)
        if args.layout == "right":
            bar_left = block_right - bar_width
        elif args.layout == "center":
            bar_left = x - bar_width // 2
        else:
            bar_left = block_left
        draw.rectangle((bar_left, y - 9, bar_left + bar_width, y - 2), fill=accent)
        draw.text((x, y + 14), args.eyebrow, font=eyebrow_font, fill=accent, anchor=anchor, spacing=6)
        y += int(height * (0.075 if args.title_mode == "keyword" else 0.08 if args.title_mode == "hero" else 0.10))

    lines = [line.strip() for line in args.title.split("|") if line.strip()]
    if not lines:
        raise ValueError("title cannot be empty")
    if args.title_mode == "keyword":
        if args.layout != "left":
            raise ValueError("keyword mode currently requires --layout left")
        full_title = "".join(lines)
        keyword = args.keyword.strip()
        if not keyword or keyword not in full_title:
            raise ValueError("keyword mode requires --keyword contained in --title")
        prefix, suffix = full_title.split(keyword, 1)
        prefix_font = fit_font(draw, prefix, cjk_font, int(height * 0.062), int(height * 0.045), max_text_width)
        draw_tracked(draw, x, y, prefix, prefix_font, text_color, int(height * 0.008))

        keyword_top = y + int(height * 0.09)
        keyword_font = fit_font(
            draw,
            keyword,
            serif_font,
            int(height * 0.47),
            int(height * 0.30),
            int(max_text_width * 0.52),
            index=0,
        )
        keyword_width, keyword_height = draw_top(draw, x, keyword_top, keyword, keyword_font, text_color)

        punctuation = suffix[-1] if suffix and suffix[-1] in "？！!?" else ""
        suffix_text = suffix[:-1] if punctuation else suffix
        suffix_x = x + keyword_width + int(width * 0.025)
        suffix_width = max(1, block_right - suffix_x)
        suffix_font = fit_font(draw, suffix_text, cjk_font, int(height * 0.115), int(height * 0.065), suffix_width)
        suffix_y = keyword_top + int(keyword_height * 0.46)
        body_width, body_height = draw_top(draw, suffix_x, suffix_y, suffix_text, suffix_font, text_color)
        if punctuation:
            punctuation_size = max(int(suffix_font.size * 0.72), int(height * 0.05))
            punctuation_font = ImageFont.truetype(cjk_font, punctuation_size)
            draw_top(
                draw,
                suffix_x + body_width - int(punctuation_size * 0.04),
                suffix_y + int(body_height * 0.18),
                punctuation,
                punctuation_font,
                accent,
            )
        y = keyword_top + keyword_height + int(height * 0.045)
    elif args.title_mode == "hero":
        title_ratio = 0.25 if len(lines) == 1 else 0.28 if len(lines) == 2 else 0.18
        minimum_ratio = 0.09
        line_gap_ratio = 0.012
    else:
        title_ratio = 0.135 if len(lines) <= 2 else 0.11
        minimum_ratio = 0.065
        line_gap_ratio = 0.035
    if args.title_mode != "keyword":
        title_size = int(height * title_ratio)
        fonts = [fit_font(draw, line, cjk_font, title_size, int(height * minimum_ratio), max_text_width) for line in lines]
        line_gap = int(height * line_gap_ratio)
        for line, title_font in zip(lines, fonts):
            draw.text((x, y), line, font=title_font, fill=text_color, anchor=anchor)
            box = draw.textbbox((x, y), line, font=title_font, anchor=anchor)
            y += (box[3] - box[1]) + line_gap

    if args.subtitle:
        y += int(height * 0.02)
        subtitle_width = min(max_text_width, int(width * 0.34)) if args.title_mode == "keyword" else max_text_width
        subtitle_font = fit_font(draw, args.subtitle, cjk_font, int(height * 0.045), int(height * 0.03), subtitle_width)
        draw.text((x, y), args.subtitle, font=subtitle_font, fill=text_color, anchor=anchor)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out, quality=95)
    manifest = {
        "output": str(out.resolve()),
        "background": str(Path(args.background).resolve()),
        "platform": args.platform,
        "size": [width, height],
        "layout": args.layout,
        "title_mode": args.title_mode,
        "keyword": args.keyword,
        "title": args.title.replace("|", "\n"),
        "subtitle": args.subtitle,
        "eyebrow": args.eyebrow,
        "font": cjk_font,
        "serif_font": serif_font,
    }
    out.with_suffix(".json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {out} ({width}x{height})")


if __name__ == "__main__":
    main()
