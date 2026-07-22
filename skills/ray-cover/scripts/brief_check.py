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
GENERATION_STRATEGIES = {"direct-first", "deterministic"}


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

    prompt_raw = str(data.get("image_prompt", ""))
    prompt = prompt_raw.lower()
    fallback_prompt = str(data.get("fallback_image_prompt", "")).lower()
    for field, value in (("image_prompt", prompt), ("fallback_image_prompt", fallback_prompt)):
        for marker in FORBIDDEN_PROMPT_MARKERS:
            if marker in value:
                errors.append(f"{field} must describe visual principles, not '{marker}'")

    explicit_strategy = data.get("generation_strategy")
    strategy = explicit_strategy or "deterministic"
    if strategy not in GENERATION_STRATEGIES:
        errors.append(
            "generation_strategy must be one of: "
            + ", ".join(sorted(GENERATION_STRATEGIES))
        )

    negative = {str(item).lower() for item in data.get("negative_prompt", [])}
    if not ({"水印", "watermark"} & negative):
        errors.append("negative_prompt must explicitly forbid watermark/水印")

    if strategy == "direct-first":
        cover_text = data.get("cover_text")
        if not isinstance(cover_text, dict):
            errors.append("cover_text is required for direct-first generation")
        else:
            title_lines = cover_text.get("title_lines")
            if not isinstance(title_lines, list) or not title_lines or not all(
                isinstance(line, str) and line.strip() for line in title_lines
            ):
                errors.append("cover_text.title_lines must be a non-empty list of text lines")
            exact_texts = []
            for key in ("eyebrow", "subtitle"):
                value = cover_text.get(key)
                if isinstance(value, str) and value.strip():
                    exact_texts.append(value.strip())
            if isinstance(title_lines, list):
                exact_texts.extend(
                    line.strip() for line in title_lines
                    if isinstance(line, str) and line.strip()
                )
            for exact_text in exact_texts:
                if exact_text not in prompt_raw:
                    errors.append(
                        f"image_prompt must contain cover text verbatim: {exact_text}"
                    )
        if not fallback_prompt:
            errors.append("fallback_image_prompt is required for direct-first generation")
        if not ({"额外文字", "extra text"} & negative):
            errors.append("direct-first negative_prompt must forbid extra text/额外文字")
        fallback_negative = {
            str(item).lower() for item in data.get("fallback_negative_prompt", [])
        }
        if not ({"文字", "text"} & fallback_negative):
            errors.append(
                "fallback_negative_prompt must explicitly forbid text/文字"
            )
        if not ({"水印", "watermark"} & fallback_negative):
            errors.append(
                "fallback_negative_prompt must explicitly forbid watermark/水印"
            )
    elif not ({"文字", "text"} & negative):
        errors.append(
            "deterministic negative_prompt must explicitly forbid text/文字"
        )

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

    x_article = outputs.get("x_article")
    if x_article is not None:
        if not isinstance(x_article, dict):
            errors.append("outputs.x_article must be an object")
        else:
            if (x_article.get("width"), x_article.get("height")) != (1600, 640):
                errors.append("outputs.x_article must default to 1600x640")
            if x_article.get("layout") not in {"left", "right", "center"}:
                errors.append("outputs.x_article.layout must be left, right, or center")

    if errors:
        return fail(errors)
    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
