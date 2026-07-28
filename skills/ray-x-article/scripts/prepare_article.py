#!/usr/bin/env python3
"""Build a delivery package for the X Articles editor.

Everything counted here is counted the way the editor counts it, not the way the
Markdown source reads: the editor is Draft.js, so each list item is its own
block, and it offers exactly two heading levels — Heading (h1) and Subheading
(h2). Markdown `##` therefore becomes `<h1>` and anything deeper becomes `<h2>`.
"""

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

from PIL import Image


FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
WIKI_IMAGE = re.compile(r"!\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]")
INLINE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
WIKILINK = re.compile(r"\[\[([^\]|]+)\|?([^\]]*)\]\]")
BOLD = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}

# 译介支线：内容属于别人。授权和署名在写作阶段落定，这里是进后台前的最后一道门。
# 契约见 ray-writer/references/translation.md。
TRANSLATION_KINDS = {"translation", "repost"}
PERMISSION_CLEARED = {"granted", "open-license"}
SOURCE_FIELDS = ("source_title", "source_author", "source_url", "source_permission")


def split_frontmatter(text):
    match = FRONTMATTER.match(text)
    return (match.group(1), text[match.end():]) if match else ("", text)


def scalar(frontmatter, key):
    # 只吃行内空白：`\s*` 会跨过换行，让一个空字段吞掉下一行的值。
    match = re.search(rf"(?m)^{re.escape(key)}:[ \t]*(.+?)[ \t]*$", frontmatter)
    if not match:
        return ""
    return match.group(1).strip().strip('"').strip("'")


def check_translation(frontmatter, body):
    """Gate translated or reposted articles on permission and visible attribution."""
    if scalar(frontmatter, "kind") not in TRANSLATION_KINDS:
        return
    fields = {key: scalar(frontmatter, key) for key in SOURCE_FIELDS}
    problems = []
    missing = [key for key, value in fields.items() if not value]
    if missing:
        problems.append("缺少来源字段：" + "、".join(missing))
    permission = fields["source_permission"]
    if permission and permission not in PERMISSION_CLEARED:
        problems.append(f"source_permission 是 {permission}，未获授权的译稿不写平台草稿")
    visible = re.sub(r"\s+", "", body)
    for key, label in (("source_url", "原文链接"), ("source_author", "原作者")):
        value = fields[key]
        if value and re.sub(r"\s+", "", value) not in visible:
            problems.append(f"正文里找不到{label}")
    if problems:
        raise ValueError("译介稿未通过授权与署名检查：" + "；".join(problems))


def is_image_embed(target):
    return Path(target.split("#", 1)[0].strip()).suffix.lower() in IMAGE_SUFFIXES


def match_image_line(line):
    """Return (alt, target) when the whole line is a single image reference."""
    stripped = line.strip()
    standard = MD_IMAGE.fullmatch(stripped)
    if standard:
        return standard.group(1).strip(), standard.group(2).strip()
    wiki = WIKI_IMAGE.fullmatch(stripped)
    if wiki and is_image_embed(wiki.group(1)):
        return (wiki.group(2) or "").strip(), wiki.group(1).strip()
    return None


def vault_root(start):
    for candidate in [start, *start.parents]:
        if (candidate / ".obsidian").is_dir():
            return candidate
    return None


def resolve_asset(target, base):
    """Locate a local image the way Obsidian does: relative first, then vault-wide."""
    raw = target.split("#", 1)[0].strip()
    direct = (base / raw).expanduser()
    if direct.is_file():
        return direct.resolve()
    absolute = Path(raw).expanduser()
    if absolute.is_absolute() and absolute.is_file():
        return absolute.resolve()
    root = vault_root(base)
    if root:
        for found in root.rglob(Path(raw).name):
            if found.is_file():
                return found.resolve()
    raise ValueError(f"插图文件找不到：{target}")


def plain_body(markdown):
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


def inline_text(text):
    """The visible text of a block after the HTML paste — links keep only their label."""
    value = text.strip()
    value = INLINE_LINK.sub(lambda m: m.group(1), value)
    value = WIKILINK.sub(lambda m: m.group(2) or m.group(1).split("/")[-1], value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"__([^_]+)__", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    return value


def strip_leading_title(markdown):
    lines = markdown.replace("\r\n", "\n").splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        # The X editor has a dedicated title field. A leading H1 therefore
        # belongs there even when its wording differs slightly from --title.
        if re.match(r"^#\s+\S", line):
            return "\n".join(lines[:index] + lines[index + 1 :]).lstrip()
        break
    return markdown


def render_block(lines):
    """Render one source block.

    Returns (html, block_texts). block_texts has one entry per editor block, so a
    four-item list contributes four entries even though it is a single <ul>.
    """
    heading = HEADING.match(lines[0]) if len(lines) == 1 else None
    if heading:
        # Heading = h1, Subheading = h2. The editor has no third level, so
        # anything deeper than ### collapses into Subheading rather than
        # silently losing its heading status on paste.
        level = 1 if len(heading.group(1)) <= 2 else 2
        return (
            f"<h{level}>{inline_html(heading.group(2))}</h{level}>",
            [inline_text(heading.group(2))],
        )
    if all(re.match(r"^[-*+]\s+", line) for line in lines):
        texts = [re.sub(r"^[-*+]\s+", "", line) for line in lines]
        items = "".join(f"<li>{inline_html(text)}</li>" for text in texts)
        return f"<ul>{items}</ul>", [inline_text(text) for text in texts]
    if all(re.match(r"^\d+[.)]\s+", line) for line in lines):
        texts = [re.sub(r"^\d+[.)]\s+", "", line) for line in lines]
        items = "".join(f"<li>{inline_html(text)}</li>" for text in texts)
        return f"<ol>{items}</ol>", [inline_text(text) for text in texts]
    texts = [re.sub(r"^>\s?", "", line) for line in lines]
    paragraph = "<br>".join(inline_html(text) for text in texts)
    return f"<p>{paragraph}</p>", ["\n".join(inline_text(text) for text in texts)]


def build_editor_content(markdown, base):
    """Render the body and pull illustrations out into a positioned manifest.

    X has no API for inserting an image at a given offset, so the images are
    delivered as a list the operator places by hand. Each entry says how many
    editor blocks precede it and quotes the block it follows.
    """
    parts = []
    block_texts = []
    images = []
    for source in re.split(r"\n\s*\n", markdown.replace("\r\n", "\n").strip()):
        lines = [line.rstrip() for line in source.splitlines() if line.strip()]
        if not lines:
            continue
        image_lines = [match_image_line(line) for line in lines]
        if all(image_lines):
            for alt, target in image_lines:
                images.append(
                    {
                        "order": len(images) + 1,
                        "alt": alt,
                        "path": str(resolve_asset(target, base)),
                        "after_block": len(block_texts),
                        "after_text": block_texts[-1][-60:] if block_texts else "",
                    }
                )
            continue
        if any(image_lines) or any(
            MD_IMAGE.search(line) or WIKI_IMAGE.search(line) for line in lines
        ):
            raise ValueError(f"插图必须独占一段，不能和正文混在同一段：{lines[0][:60]}")
        rendered, texts = render_block(lines)
        parts.append(rendered)
        block_texts.extend(texts)
    if not block_texts:
        raise ValueError("正文没有可写入编辑器的内容块")
    return "".join(parts), block_texts, images


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
    if not title:
        raise ValueError("missing article title")
    editor_markdown = strip_leading_title(markdown)
    body_html, block_texts, images = build_editor_content(editor_markdown, article.parent)
    body = plain_body(re.sub(r"(?m)^\s*(!\[[^\]]*\]\([^)]+\)|!\[\[[^\]]+\]\])\s*$", "", editor_markdown))
    check_translation(frontmatter, body)
    chapter_count = len(re.findall(r"(?m)^##\s+\S", editor_markdown))
    h1_count = body_html.count("<h1>")
    h2_count = body_html.count("<h2>")
    bold_count = len(BOLD.findall(editor_markdown))
    extra_blank_runs = len(re.findall(r"\n{3,}", editor_markdown.replace("\r\n", "\n")))
    if len(title) > 120:
        raise ValueError("title is longer than 120 characters")
    if len(body) < 200:
        raise ValueError("article body is too short for an X Article")
    format_problems = []
    if extra_blank_runs:
        format_problems.append(f"{extra_blank_runs} extra blank-line runs")
    if len(body) >= 2000 and chapter_count < 3:
        format_problems.append(f"at least 3 chapter headings required; got {chapter_count}")
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
        "schema_version": 3,
        "source_path": str(article),
        "kind": scalar(frontmatter, "kind"),
        "title": title,
        "body": body,
        "body_html": body_html,
        "cover_path": str(cover),
        "cover_size": [width, height],
        "character_count": len(body),
        "paragraph_count": len(paragraphs),
        "chapter_count": chapter_count,
        "bold_count": bold_count,
        "extra_blank_runs": extra_blank_runs,
        "images": images,
        "expected_editor": {
            "block_count": len(block_texts),
            "blank_blocks": 0,
            "h1_count": h1_count,
            "h2_count": h2_count,
            "bold_count": bold_count,
        },
        "content_sha256": digest,
        "start_anchor": block_texts[0][:80],
        "end_anchor": block_texts[-1][-80:],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK: {title} | {len(body)} chars | {len(block_texts)} editor blocks "
        f"| h1 {h1_count} / h2 {h2_count} | {len(images)} images | {width}x{height}"
    )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
