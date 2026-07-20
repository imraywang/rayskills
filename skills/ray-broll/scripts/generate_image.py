#!/usr/bin/env python3
"""Generate a still frame via Gemini image models (nano banana).

Claude Code replacement for the Codex-only `image_gen` step in
gbro-collage-broll Gate 2. Uses the same GEMINI_API_KEY and the shared
venv at ~/hyperframes-projects/.omni-venv/.

Usage:
  .omni-venv/bin/python generate_image.py \
    --prompt-file prompt.txt --output still.png --aspect-ratio 9:16
"""

import argparse
import os
import sys

from google import genai
from google.genai import types


def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--prompt")
    group.add_argument("--prompt-file")
    ap.add_argument("--output", required=True)
    ap.add_argument("--model", default="gemini-3-pro-image",
                    help="便宜备选: gemini-3.1-flash-image")
    ap.add_argument("--aspect-ratio", default="9:16")
    ap.add_argument("--style-ref", default=None,
                    help="风格锚参考图(批量时传第一张过审静帧,锁定设计语言)")
    args = ap.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("GEMINI_API_KEY 未设置")

    client = genai.Client(api_key=api_key)

    try:
        config = types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=args.aspect_ratio),
        )
    except (TypeError, AttributeError):
        # 旧版 SDK 无 image_config：把比例写进 prompt 兜底
        config = types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
        prompt += f"\nAspect ratio: {args.aspect_ratio} vertical."

    contents = prompt
    if args.style_ref:
        with open(args.style_ref, "rb") as f:
            ref = f.read()
        mime = ("image/jpeg" if args.style_ref.lower().endswith((".jpg", ".jpeg"))
                else "image/png")
        contents = [
            types.Part.from_bytes(data=ref, mime_type=mime),
            "The attached image is a STYLE REFERENCE from the same batch. "
            "Match its exact design language: halftone treatment, cutout "
            "edge style, keyline weight, shadow softness, paper grain and "
            "accent-color family. Do NOT copy its subject or composition.\n\n"
            + prompt,
        ]

    resp = client.models.generate_content(
        model=args.model, contents=contents, config=config)

    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "wb") as f:
                f.write(part.inline_data.data)
            print(f"saved {args.output}")
            return

    sys.exit(f"模型未返回图片：{resp.candidates[0].finish_reason}")


if __name__ == "__main__":
    main()
