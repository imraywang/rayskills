#!/usr/bin/env python3
"""Render a caption to a transparent PNG for ffmpeg overlay.

替代精简版 ffmpeg 缺失的 drawtext:用 Pillow + 系统中文字体渲染字幕条。

Usage:
  python render_caption.py --text "第一行\n第二行" --output cap.png [--fontsize 42]
"""

import argparse

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    ("/System/Library/Fonts/PingFang.ttc", 2),   # PingFang SC Medium(常见索引)
    ("/System/Library/Fonts/PingFang.ttc", 0),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
    ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
]


def load_font(size):
    for path, index in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size, index=index)
        except OSError:
            continue
    raise SystemExit("找不到可用的系统中文字体")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help=r"支持 \n 换行")
    ap.add_argument("--output", required=True)
    ap.add_argument("--fontsize", type=int, default=42)
    ap.add_argument("--line-spacing", type=int, default=14)
    args = ap.parse_args()

    text = args.text.replace("\\n", "\n")
    font = load_font(args.fontsize)

    probe = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    bbox = probe.multiline_textbbox((0, 0), text, font=font,
                                    spacing=args.line_spacing, align="center")
    tw, th = int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])

    pad_x, pad_y, radius = 26, 18, 14
    w, h = tw + pad_x * 2, th + pad_y * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius,
                           fill=(0, 0, 0, 96))
    draw.multiline_text((pad_x - bbox[0], pad_y - bbox[1]), text, font=font,
                        fill=(244, 239, 227, 255),
                        spacing=args.line_spacing, align="center")
    img.save(args.output)
    print(f"saved {args.output} ({w}x{h})")


if __name__ == "__main__":
    main()
