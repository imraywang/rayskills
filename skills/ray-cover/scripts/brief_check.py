#!/usr/bin/env python3
import json
import sys
from pathlib import Path

STYLES = {
    "editorial-metaphor-collage",
    "minimal-metaphor",
    "midcentury-editorial",
    "quiet-ink",
    "tool-bridge",
}
REQUIRED = [
    "source", "title", "short_title", "thesis", "emotion", "conflict",
    "metaphor", "style_id", "composition", "palette", "image_prompt",
    "negative_prompt", "outputs",
]
FORBIDDEN_PROMPT_MARKERS = ["vox style", "adrianpunk style", "in the style of"]


def fail(messages):
    for message in messages:
        print(f"ERROR: {message}", file=sys.stderr)
    return 1


def main():
    if len(sys.argv) != 2:
        return fail(["usage: brief_check.py <cover-brief.json>"])
    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return fail([f"cannot read valid JSON: {exc}"])

    errors = []
    for key in REQUIRED:
        if key not in data or data[key] in (None, "", [], {}):
            errors.append(f"missing or empty field: {key}")

    short_title = str(data.get("short_title", "")).replace("|", "")
    if len(short_title) > 24:
        errors.append("short_title must be 24 characters or fewer")
    if data.get("style_id") not in STYLES:
        errors.append(f"style_id must be one of: {', '.join(sorted(STYLES))}")

    prompt = str(data.get("image_prompt", "")).lower()
    for marker in FORBIDDEN_PROMPT_MARKERS:
        if marker in prompt:
            errors.append(f"image_prompt must describe visual principles, not '{marker}'")

    negative = {str(item).lower() for item in data.get("negative_prompt", [])}
    if not ({"文字", "text"} & negative):
        errors.append("negative_prompt must explicitly forbid text/文字")
    if not ({"水印", "watermark"} & negative):
        errors.append("negative_prompt must explicitly forbid watermark/水印")

    outputs = data.get("outputs", {})
    expected = {"wechat": (2100, 900), "x": (1600, 900)}
    for platform, size in expected.items():
        item = outputs.get(platform)
        if not isinstance(item, dict):
            errors.append(f"outputs.{platform} is required")
            continue
        if (item.get("width"), item.get("height")) != size:
            errors.append(f"outputs.{platform} must default to {size[0]}x{size[1]}")
        if item.get("layout") not in {"left", "right", "center"}:
            errors.append(f"outputs.{platform}.layout must be left, right, or center")

    if errors:
        return fail(errors)
    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
