#!/usr/bin/env python3
"""Validate a WeChat HTML fragment against its source Markdown."""

from __future__ import annotations

import argparse
import hashlib
import html as html_module
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


FORBIDDEN = {
    "document wrapper": re.compile(r"</?(?:html|head|body)\b", re.I),
    "script or style tag": re.compile(r"<(?:script|style)\b", re.I),
    "div tag": re.compile(r"</?div\b", re.I),
    "class or id attribute": re.compile(r"\s(?:class|id)\s*=", re.I),
    "unsupported position": re.compile(r"position\s*:\s*(?:fixed|absolute|sticky)", re.I),
    "grid layout": re.compile(r"display\s*:\s*grid", re.I),
}
SIGNATURE_MARKERS = (
    "{{作者名}}",
    "{{简介}}",
    "点赞、在看、转发",
    "点赞在看转发",
)
MOJIBAKE_MARKERS = ("Ã", "Â", "â", "å", "æ", "ç", "ã")


def mojibake_candidate(value: str) -> str | None:
    try:
        candidate = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return None
    before_markers = sum(value.count(marker) for marker in MOJIBAKE_MARKERS)
    after_markers = sum(candidate.count(marker) for marker in MOJIBAKE_MARKERS)
    before_cjk = len(re.findall(r"[\u3400-\u9fff]", value))
    after_cjk = len(re.findall(r"[\u3400-\u9fff]", candidate))
    if after_markers < before_markers or after_cjk > before_cjk:
        return candidate
    return None


def has_mojibake(value: str) -> bool:
    return any(marker in value for marker in MOJIBAKE_MARKERS) or mojibake_candidate(value) is not None


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    meta: dict[str, str] = {}
    for raw in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw)
        if not match:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[match.group(1)] = value
    return meta, text[end + 5 :]


def source_blocks(markdown_body: str) -> tuple[list[str], int, int, bool]:
    blocks: list[str] = []
    h2_count = 0
    bold_count = 0
    signature_present = False
    buffer: list[str] = []

    def flush() -> None:
        nonlocal bold_count, signature_present
        if not buffer:
            return
        text = " ".join(buffer).strip()
        bold_count += len(re.findall(r"\*\*(.+?)\*\*", text))
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        clean = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", clean)
        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
        clean = re.sub(r"`([^`]+)`", r"\1", clean)
        if re.search(r"我是.{1,40}[，,]", clean) or any(x in clean for x in SIGNATURE_MARKERS):
            signature_present = True
        blocks.append(re.sub(r"\s+", "", clean))
        buffer.clear()

    in_fence = False
    for raw in markdown_body.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            buffer.append(raw.rstrip())
            continue
        if not line:
            flush()
            continue
        if line.startswith("# "):
            flush()
            continue
        if line.startswith("## "):
            flush()
            h2_count += 1
            blocks.append(re.sub(r"\s+", "", line[3:]))
            continue
        if line.startswith("### "):
            flush()
            blocks.append(re.sub(r"\s+", "", line[4:]))
            continue
        line = re.sub(r"^(?:>|[-*+] |\d+[.)] )\s*", "", line)
        if re.fullmatch(r"!\[[^\]]*\]\([^)]+\)", line):
            continue
        buffer.append(line)
    flush()
    return blocks, h2_count, bold_count, signature_present


class FragmentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.p_stack: list[list[str]] = []
        self.empty_paragraphs = 0
        self.h3_count = 0
        self.strong_count = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "p":
            self.p_stack.append([])
        elif tag == "h3":
            self.h3_count += 1
        elif tag == "strong":
            self.strong_count += 1

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self.p_stack:
            self.p_stack[-1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self.p_stack:
            current = self.p_stack.pop()
            if not "".join(current).strip():
                self.empty_paragraphs += 1


def ascii_emphasis_splits(fragment: str) -> list[str]:
    after = re.compile(
        r'<span[^>]*border-bottom:[^>]*><span[^>]*>([^<]*)</span></span><span[^>]*>([^<]*)</span>',
        re.I,
    )
    before = re.compile(
        r'<span[^>]*>([^<]*)</span><span[^>]*border-bottom:[^>]*><span[^>]*>([^<]*)</span></span>',
        re.I,
    )
    found: list[str] = []
    for left, right in [*after.findall(fragment), *before.findall(fragment)]:
        left = html_module.unescape(left)
        right = html_module.unescape(right)
        if not left or not right:
            continue
        if left[-1].isascii() and left[-1].isalnum() and right[0].isascii() and right[0].isalnum():
            found.append(f"{left[-12:]}|{right[:12]}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WeChat article HTML")
    parser.add_argument("--article", required=True, type=Path)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--signature", choices=("absent", "present", "inherit"), default="inherit")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    md = args.article.read_text(encoding="utf-8")
    meta, body = split_frontmatter(md)
    fragment = args.html.read_text(encoding="utf-8").strip()
    blocks, source_h2, source_bold, source_has_signature = source_blocks(body)

    errors: list[str] = []
    warnings: list[str] = []
    if meta.get("kind") in {"content-pack", "idea", "research"}:
        errors.append(f"source is {meta['kind']}, not a final article")
    if not fragment.startswith("<section") or not fragment.endswith("</section>"):
        errors.append("HTML must be one clean section fragment")
    for label, pattern in FORBIDDEN.items():
        if pattern.search(fragment):
            errors.append(f"forbidden {label}")

    parsed = FragmentParser()
    try:
        parsed.feed(fragment)
    except Exception as exc:
        errors.append(f"HTML parse failed: {exc}")
    visible = re.sub(r"\s+", "", "".join(parsed.text))

    cursor = 0
    missing: list[str] = []
    for block in blocks:
        index = visible.find(block, cursor)
        if index < 0:
            missing.append(block[:48])
        else:
            cursor = index + len(block)
    if missing:
        errors.append(f"source blocks missing or reordered: {missing[:5]}")
    if parsed.empty_paragraphs:
        errors.append(f"empty paragraphs: {parsed.empty_paragraphs}")
    if parsed.h3_count != source_h2:
        errors.append(f"chapter mismatch: source={source_h2}, html={parsed.h3_count}")

    html_has_signature = bool(re.search(r"我是.{1,40}[，,]", visible)) or any(
        marker in visible for marker in SIGNATURE_MARKERS
    )
    if args.signature == "absent" and html_has_signature:
        errors.append("signature or interaction footer must be absent")
    elif args.signature == "present" and not html_has_signature:
        errors.append("signature footer expected but not found")
    elif args.signature == "inherit" and html_has_signature != source_has_signature:
        errors.append("HTML signature policy differs from source article")

    if has_mojibake(visible):
        errors.append("possible mojibake in visible text")
    splits = ascii_emphasis_splits(fragment)
    if splits:
        errors.append(f"emphasis splits ASCII words: {splits[:5]}")

    body_chars = len(re.sub(r"\s+", "", body))
    if body_chars >= 2000 and source_h2 < 4:
        warnings.append("long article has fewer than four chapters")
    if body_chars >= 2000 and source_bold < 6:
        warnings.append("source long-form article has fewer than six bold judgments")

    manifest = {
        "article": str(args.article.resolve()),
        "html": str(args.html.resolve()),
        "title": meta.get("title", ""),
        "source_blocks": len(blocks),
        "chapter_count": source_h2,
        "source_bold_count": source_bold,
        "html_strong_count": parsed.strong_count,
        "empty_paragraphs": parsed.empty_paragraphs,
        "signature_policy": args.signature,
        "signature_present": html_has_signature,
        "content_sha256": hashlib.sha256(fragment.encode("utf-8")).hexdigest(),
        "errors": errors,
        "warnings": warnings,
        "status": "ready" if not errors else "blocked",
    }
    output = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
