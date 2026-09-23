#!/usr/bin/env python3
import json
import sys
from pathlib import Path

HOUSE_STYLE = "ray-editorial-engraving"
PALETTE = ["#151515", "#F1E7D2", "#183B66", "#D85C41"]
COMPOSITION_MODE = "split-scene-center-breathing-room"
SIZES = {
    "wechat": (2100, 900),
    "x": (1600, 900),
    "x_article": (1600, 640),
}
FORBIDDEN_MARKERS = (
    "a16z",
    "every",
    "elsewhere",
    "vox",
    "in the style of",
)
CENTER_FILL_MARKERS = (
    "主体可以占据中央",
    "占据或穿过画面中心",
    "不需要中央",
    "不设置中央安全区",
)


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
    for key in (
        "source",
        "title",
        "thesis",
        "subject",
        "composition",
        "base_prompt",
        "outputs",
    ):
        if data.get(key) in (None, "", [], {}):
            errors.append(f"missing or empty field: {key}")

    for forbidden_field in ("mark", "overlay"):
        if forbidden_field in data:
            errors.append(
                f"{forbidden_field} is not allowed in a base-only cover brief"
            )

    if data.get("house_style") != HOUSE_STYLE:
        errors.append(f"house_style must be {HOUSE_STYLE}")
    if data.get("palette") != PALETTE:
        errors.append("palette must match the fixed Ray editorial palette")

    prompt = str(data.get("base_prompt", ""))
    prompt_lower = prompt.lower()
    for marker in FORBIDDEN_MARKERS:
        if marker in prompt_lower:
            errors.append(f"base_prompt must describe the medium, not '{marker}'")
    for required in ("文字", "水印", "中央"):
        if required not in prompt:
            errors.append(f"base_prompt must explicitly mention: {required}")
    if not any(term in prompt for term in ("低细节", "安静", "呼吸区")):
        errors.append("base_prompt must describe a quiet, low-detail center")
    for marker in CENTER_FILL_MARKERS:
        if marker in prompt:
            errors.append(f"base_prompt must preserve center breathing room: {marker}")

    composition = data.get("composition")
    if not isinstance(composition, dict):
        errors.append("composition must be an object")
    else:
        if composition.get("mode") != COMPOSITION_MODE:
            errors.append(f"composition.mode must be {COMPOSITION_MODE}")
        left = composition.get("left_anchor")
        right = composition.get("right_anchor")
        if not isinstance(left, str) or not left.strip():
            errors.append("composition.left_anchor is required")
        if not isinstance(right, str) or not right.strip():
            errors.append("composition.right_anchor is required")
        if isinstance(left, str) and isinstance(right, str) and left.strip() == right.strip():
            errors.append("left_anchor and right_anchor must not be identical")
        ratio = composition.get("center_width_ratio")
        if not isinstance(ratio, (int, float)) or not 0.26 <= ratio <= 0.32:
            errors.append("composition.center_width_ratio must be between 0.26 and 0.32")

    negative = {str(item).lower() for item in data.get("negative_prompt", [])}
    for alternatives, label in (
        ({"文字", "text"}, "文字/text"),
        ({"logo", "标志"}, "Logo/标志"),
        ({"水印", "watermark"}, "水印/watermark"),
        ({"摄影", "photo", "photography"}, "摄影/photo"),
    ):
        if not (alternatives & negative):
            errors.append(f"negative_prompt must forbid {label}")

    outputs = data.get("outputs", {})
    if isinstance(outputs, dict):
        for platform, output in outputs.items():
            if platform not in SIZES:
                errors.append(f"unsupported output platform: {platform}")
                continue
            if not isinstance(output, dict):
                errors.append(f"outputs.{platform} must be an object")
                continue
            expected = SIZES[platform]
            if (output.get("width"), output.get("height")) != expected:
                errors.append(
                    f"outputs.{platform} must be {expected[0]}x{expected[1]}"
                )
    else:
        errors.append("outputs must be an object")

    if errors:
        return fail(errors)
    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
