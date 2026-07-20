#!/usr/bin/env python3
"""Deterministic cut-out headline card — 剪纸标题卡纸(字入画,零假字).

真·Vox 观感的画内大标题:每行一张卡纸条,粗字 + 微旋转 + 纸影,
Pillow 确定性渲染(沿用 ray-cover "AI 不写字"原则)。输出透明 PNG,
由 assemble.py overlay 进画面,或叠进静帧。

Usage:
  python render_headline.py --text "第一行\\n第二行" --output headline.png \
    [--fontsize 88] [--strip-hex F4EFE3] [--text-hex 1A1A1A] \
    [--accent-line 2 --accent-hex E8620A] [--max-width 900]
"""

import argparse

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_CANDIDATES = [
    ("/System/Library/Fonts/PingFang.ttc", 8),   # PingFang SC Semibold(常见)
    ("/System/Library/Fonts/PingFang.ttc", 2),
    ("/System/Library/Fonts/PingFang.ttc", 0),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 1),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
]

# 每行的确定性微旋转(度),循环使用——避免随机保证可复现
ROTATIONS = [-2.0, 1.5, -1.0, 2.0]


def load_font(size):
    for path, index in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size, index=index)
        except OSError:
            continue
    raise SystemExit("找不到可用的系统中文字体")


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def render_strip(text, font, strip_rgb, text_rgb, rotation):
    probe = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    bbox = probe.textbbox((0, 0), text, font=font)
    tw, th = int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])
    pad_x, pad_y = int(font.size * 0.42), int(font.size * 0.26)
    w, h = tw + pad_x * 2, th + pad_y * 2

    # 卡纸条 + 奶油白 keyline
    strip = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    d.rounded_rectangle([6, 6, w + 6, h + 6], radius=10,
                        fill=strip_rgb + (255,),
                        outline=(244, 239, 227, 255), width=5)
    d.text((6 + pad_x - bbox[0], 6 + pad_y - bbox[1]), text,
           font=font, fill=text_rgb + (255,))

    rotated = strip.rotate(rotation, expand=True, resample=Image.BICUBIC)
    # 柔和纸影
    shadow = Image.new("RGBA", rotated.size, (0, 0, 0, 0))
    alpha = rotated.getchannel("A").point(lambda a: min(a, 92))
    shadow.paste((20, 12, 0, 255), (0, 0), alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    out = Image.new("RGBA",
                    (rotated.width + 14, rotated.height + 16), (0, 0, 0, 0))
    out.alpha_composite(shadow, (10, 12))
    out.alpha_composite(rotated, (0, 0))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help=r"支持 \n 分行")
    ap.add_argument("--output", required=True)
    ap.add_argument("--fontsize", type=int, default=88)
    ap.add_argument("--strip-hex", default="F4EFE3")
    ap.add_argument("--text-hex", default="1A1A1A")
    ap.add_argument("--accent-line", type=int, default=0,
                    help="第 N 行(1 起)用点色卡纸,0=不用")
    ap.add_argument("--accent-hex", default="E8620A")
    ap.add_argument("--accent-text-hex", default="FFF6E8")
    ap.add_argument("--max-width", type=int, default=920,
                    help="超宽自动缩字号")
    args = ap.parse_args()

    lines = [l for l in args.text.replace("\\n", "\n").split("\n") if l.strip()]
    size = args.fontsize
    while size > 36:
        font = load_font(size)
        probe = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
        widest = max(probe.textbbox((0, 0), l, font=font)[2] for l in lines)
        if widest + int(size * 0.84) + 26 <= args.max_width:
            break
        size -= 4
    font = load_font(size)

    strips = []
    for i, line in enumerate(lines):
        accent = (args.accent_line == i + 1)
        strips.append(render_strip(
            line, font,
            hex_rgb(args.accent_hex if accent else args.strip_hex),
            hex_rgb(args.accent_text_hex if accent else args.text_hex),
            ROTATIONS[i % len(ROTATIONS)]))

    overlap = int(size * 0.18)
    W = max(s.width for s in strips)
    H = sum(s.height for s in strips) - overlap * (len(strips) - 1)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = 0
    for s in strips:
        canvas.alpha_composite(s, ((W - s.width) // 2, y))
        y += s.height - overlap
    canvas.save(args.output)
    print(f"saved {args.output} ({W}x{H}, fontsize={size})")


if __name__ == "__main__":
    main()
