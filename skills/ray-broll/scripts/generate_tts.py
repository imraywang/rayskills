#!/usr/bin/env python3
"""Generate narration audio via Gemini TTS. Outputs 24kHz mono WAV.

Usage:
  .omni-venv/bin/python generate_tts.py --text "..." --output out.wav \
    [--voice Charon] [--style "平静克制的纪录片解说语气"]
"""

import argparse
import os
import struct
import sys

from google import genai
from google.genai import types


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--model", default="gemini-3.1-flash-tts-preview")
    ap.add_argument("--voice", default="Charon")
    ap.add_argument("--style", default="用平静、克制、干净利落的解说语气朗读")
    args = ap.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("GEMINI_API_KEY 未设置")

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=args.model,
        contents=f"{args.style}：{args.text}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=args.voice)
                )
            ),
        ),
    )

    part = resp.candidates[0].content.parts[0]
    pcm = part.inline_data.data
    rate = 24000
    mime = part.inline_data.mime_type or ""
    if "rate=" in mime:
        rate = int(mime.split("rate=")[1].split(";")[0])

    # 手写 WAV 头,避免依赖 ffmpeg 管道
    with open(args.output, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE")
        f.write(b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate,
                                      rate * 2, 2, 16))
        f.write(b"data" + struct.pack("<I", len(pcm)) + pcm)
    print(f"saved {args.output} ({len(pcm) / (rate * 2):.2f}s @ {rate}Hz)")


if __name__ == "__main__":
    main()
