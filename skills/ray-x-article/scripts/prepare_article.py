#!/usr/bin/env python3
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

from PIL import Image


FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
INLINE_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
INLINE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
WIKILINK = re.compile(r"\[\[([^\]|]+)\|?([^\]]*)\]\]")
BOLD = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")


def split_frontmatter(text):
    match = FRONTMATTER.match(text)
    return (match.group(1), text[match.end():]) if match else ("", text)


def scalar(frontmatter, key):
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", frontmatter)
    if not match:
        return ""
    return match.group(1).strip().strip('"').strip("'")


def plain_body(markdown):
    if INLINE_IMAGE.search(markdown):
        raise ValueError("正文含行内图片；请先决定在 X 编辑器中的插入位置")
    body = markdown.replace("\r\n", "\n")
    body = re.sub(r"(?ms)^```[^\n]*\n(.*?)^```\s*$", r"\1", body)
    body = re.sub(r"(?m)^#{1,6}\s+", "", body)
    body = re.sub(r"(?m)^>\s?", "", body)
    body = INLINE_LINK.sub(lambda m: f"{m.group(1)}（{m.group(2)}）", body)
    body = WIKILINK.sub(lambda m: m.group(2) or m.group(1).split("/")[-1], body)
    body = re.sub(r"\*\*([^*]+)\*\*", r"\1", body)
    body = re.sub(r"__([^_]+)__", r"\1", body)
    body = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", body)
    body = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"\1", body)
    body = re.sub(r"`([^`]+)`", r"\1", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return body


def inline_html(text):
    value = html.escape(text.strip(), quote=True)
    value = INLINE_LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    return value


def rich_html(markdown):
    if INLINE_IMAGE.search(markdown):
        raise ValueError("正文含行内图片；请先决定在 X 编辑器中的插入位置")
    blocks = re.split(r"\n\s*\n", markdown.replace("\r\n", "\n").strip())
    rendered = []
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines()]
        if len(lines) == 1 and re.match(r"^#{1,3}\s+", lines[0]):
            match = re.match(r"^(#{1,3})\s+(.+)$", lines[0])
            level = 2 if len(match.group(1)) <= 2 else 3
            rendered.append(f"<h{level}>{inline_html(match.group(2))}</h{level}>")
        elif lines and all(re.match(r"^[-*+]\s+", line) for line in lines):
            items = "".join(f"<li>{inline_html(re.sub(r'^[-*+]\\s+', '', line))}</li>" for line in lines)
            rendered.append(f"<ul>{items}</ul>")
        elif lines and all(re.match(r"^\d+[.)]\s+", line) for line in lines):
            items = "".join(f"<li>{inline_html(re.sub(r'^\\d+[.)]\\s+', '', line))}</li>" for line in lines)
            rendered.append(f"<ol>{items}</ol>")
        else:
            paragraph = "<br>".join(inline_html(re.sub(r"^>\s?", "", line)) for line in lines)
            rendered.append(f"<p>{paragraph}</p>")
    return "".join(rendered)


def main():
    parser = argparse.ArgumentParser(description="Prepare a checked X Articles delivery package")
    parser.add_argument("--article", required=True)
    parser.add_argument("--cover", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="")
    args = parser.parse_args()

    article = Path(args.article).expanduser().resolve()
    cover = Path(args.cover).expanduser().resolve()
    output = Path(args.out).expanduser().resolve()
    if not article.is_file():
        raise FileNotFoundError(f"article not found: {article}")
    if not cover.is_file():
        raise FileNotFoundError(f"cover not found: {cover}")

    raw = article.read_text(encoding="utf-8")
    frontmatter, markdown = split_frontmatter(raw)
    title = (args.title or scalar(frontmatter, "title")).strip()
    body = plain_body(markdown)
    body_html = rich_html(markdown)
    source_blocks = [part.strip() for part in re.split(r"\n\s*\n", markdown) if part.strip()]
    h2_count = len(re.findall(r"(?m)^##\s+\S", markdown))
    bold_count = len(BOLD.findall(markdown))
    extra_blank_runs = len(re.findall(r"\n{3,}", markdown.replace("\r\n", "\n")))
    if not title:
        raise ValueError("missing article title")
    if len(title) > 120:
        raise ValueError("title is longer than 120 characters")
    if len(body) < 200:
        raise ValueError("article body is too short for an X Article")
    format_problems = []
    if extra_blank_runs:
        format_problems.append(f"{extra_blank_runs} extra blank-line runs")
    if len(body) >= 2000 and h2_count < 3:
        format_problems.append(f"at least 3 H2 headings required; got {h2_count}")
    if len(body) >= 2000 and bold_count < 3:
        format_problems.append(f"at least 3 bold key statements required; got {bold_count}")
    if format_problems:
        raise ValueError("article format is not ready for X: " + "; ".join(format_problems))

    with Image.open(cover) as image:
        width, height = image.size
    ratio = width / height
    if abs(ratio - 2.5) > 0.04:
        raise ValueError(f"cover must be close to 5:2; got {width}x{height} ({ratio:.3f}:1)")

    digest = hashlib.sha256((title + "\n" + body).encode("utf-8")).hexdigest()
    paragraphs = [part.strip() for part in body.split("\n\n") if part.strip()]
    package = {
        "schema_version": 2,
        "source_path": str(article),
        "title": title,
        "body": body,
        "body_html": body_html,
        "cover_path": str(cover),
        "cover_size": [width, height],
        "character_count": len(body),
        "paragraph_count": len(paragraphs),
        "heading_count": h2_count,
        "bold_count": bold_count,
        "extra_blank_runs": extra_blank_runs,
        "expected_editor": {
            "block_count": len(source_blocks),
            "blank_blocks": 0,
            "heading_count": h2_count,
            "bold_count": bold_count,
        },
        "content_sha256": digest,
        "start_anchor": body[:80],
        "end_anchor": body[-80:],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {title} | {len(body)} chars | {len(paragraphs)} paragraphs | {width}x{height}")


if __name__ == "__main__":
    main()
