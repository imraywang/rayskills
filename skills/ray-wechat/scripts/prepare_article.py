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


# 译介支线：内容属于别人。授权和署名在写作阶段落定，这里是进后台前的最后一道门。
# 契约见 ray-writer/references/translation.md。
TRANSLATION_KINDS = {"translation", "repost"}
PERMISSION_CLEARED = {"granted", "open-license"}
SOURCE_FIELDS = ("source_title", "source_author", "source_url", "source_permission")


MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
WIKI_IMAGE = re.compile(r"!\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]")
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}
IMG_SRC = re.compile(r"<img\b[^>]*?\bsrc\s*=\s*\"([^\"]*)\"", re.I)


CODE_SPAN = re.compile(r"`([^`]+)`")
MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
# The underscore forms refuse intraword matches so identifiers such as
# in_progress stay intact; render_article.py tokenises by the same rules.
STRONG_STAR = re.compile(r"\*\*(.+?)\*\*")
STRONG_UNDER = re.compile(r"(?<![0-9A-Za-z_])__(?!\s)(.+?)(?<!\s)__(?![0-9A-Za-z_])")
EM_STAR = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
EM_UNDER = re.compile(r"(?<![0-9A-Za-z_])_(?!\s)([^_\n]+)(?<!\s)_(?![0-9A-Za-z_])")


def wikilink_label(inner: str) -> str:
    """Display text for [[note|label]], [[folder/note]] and [[note#anchor]]."""
    label = inner.split("|", 1)[1] if "|" in inner else inner.split("/")[-1]
    return label.split("#", 1)[0].strip()


def strip_inline_markup(text: str) -> str:
    """Reduce a Markdown line to the text the renderer will actually show."""
    held: list[str] = []

    def hold(match: re.Match) -> str:
        held.append(match.group(1))
        return f"\x00{len(held) - 1}\x00"

    clean = CODE_SPAN.sub(hold, text)
    clean = WIKI_IMAGE.sub("", clean)
    clean = MD_IMAGE.sub("", clean)
    clean = WIKILINK.sub(lambda m: wikilink_label(m.group(1)), clean)
    clean = MD_LINK.sub(r"\1", clean)
    clean = STRONG_STAR.sub(r"\1", clean)
    clean = STRONG_UNDER.sub(r"\1", clean)
    clean = EM_STAR.sub(r"\1", clean)
    clean = EM_UNDER.sub(r"\1", clean)
    return re.sub(r"\x00(\d+)\x00", lambda m: held[int(m.group(1))], clean)


def count_bold(text: str) -> int:
    masked = CODE_SPAN.sub("", text)
    return len(STRONG_STAR.findall(masked)) + len(STRONG_UNDER.findall(masked))


def is_image_embed(target: str) -> bool:
    return Path(target.split("#", 1)[0].strip()).suffix.lower() in IMAGE_SUFFIXES


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
        bold_count += count_bold(text)
        clean = strip_inline_markup(text)
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
        heading = HEADING.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            if level == 1:
                continue
            if level == 2:
                h2_count += 1
            bold_count += count_bold(heading.group(2))
            blocks.append(re.sub(r"\s+", "", strip_inline_markup(heading.group(2))))
            continue
        if re.fullmatch(r"(?:---+|\*\*\*+|___+)", line):
            flush()
            continue
        line = re.sub(r"^(?:>|[-*+] |\d+[.)] )\s*", "", line)
        if MD_IMAGE.fullmatch(line):
            continue
        wiki_embed = WIKI_IMAGE.fullmatch(line)
        if wiki_embed and is_image_embed(wiki_embed.group(1)):
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


def translation_findings(
    meta: dict[str, str], visible: str, fragment: str
) -> tuple[list[str], list[str]]:
    """Gate translated or reposted articles on permission and visible attribution.

    `visible` is the fragment's rendered text with whitespace already collapsed,
    so both sides of the attribution comparison get the same treatment. A source
    URL that only lives in an href counts as present but earns a warning: most
    accounts cannot make body links tappable, so the reader cannot reach it.
    """
    if meta.get("kind", "") not in TRANSLATION_KINDS:
        return [], []
    errors: list[str] = []
    warnings: list[str] = []
    fields = {key: meta.get(key, "").strip() for key in SOURCE_FIELDS}
    missing = [key for key, value in fields.items() if not value]
    if missing:
        errors.append(f"translation frontmatter missing: {', '.join(missing)}")
    permission = fields["source_permission"]
    if permission and permission not in PERMISSION_CLEARED:
        errors.append(f"source_permission is {permission}, not cleared for a platform draft")

    author = fields["source_author"]
    if author and re.sub(r"\s+", "", author) not in visible:
        errors.append("attribution block missing the original author")
    url = fields["source_url"]
    if url:
        if re.sub(r"\s+", "", url) in visible:
            pass
        elif url in fragment:
            warnings.append("source URL is only a link target; most accounts cannot open it")
        else:
            errors.append("attribution block missing the source URL")
    return errors, warnings


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

    # Local paths survive rendering on purpose; they must be swapped for hosted
    # URLs by wechat_images.py before the fragment may reach the draft API.
    unhosted = [
        src for src in IMG_SRC.findall(fragment) if not src.lower().startswith("https://")
    ]
    if unhosted:
        errors.append(f"images are not uploaded yet: {unhosted[:5]}")

    parsed = FragmentParser()
    try:
        parsed.feed(fragment)
    except Exception as exc:
        errors.append(f"HTML parse failed: {exc}")
    visible = re.sub(r"\s+", "", "".join(parsed.text))
    translation_errors, translation_warnings = translation_findings(meta, visible, fragment)
    errors.extend(translation_errors)
    warnings.extend(translation_warnings)

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
        "kind": meta.get("kind", ""),
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
