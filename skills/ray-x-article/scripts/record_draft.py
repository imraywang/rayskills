#!/usr/bin/env python3
import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


FIELDS = (
    "x_article_status",
    "x_article_draft_url",
    "x_article_saved_at",
    "x_article_cover",
    "x_article_content_sha256",
)


def quoted(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    parser = argparse.ArgumentParser(description="Record a verified X Article draft in Markdown frontmatter")
    parser.add_argument("--article", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--cover", required=True)
    parser.add_argument("--content-sha256", required=True)
    parser.add_argument("--status", choices=["draft", "draft-needs-cover"], default="draft")
    args = parser.parse_args()

    article = Path(args.article).expanduser().resolve()
    cover = Path(args.cover).expanduser().resolve()
    if not re.fullmatch(r"https://x\.com/compose/articles/edit/\d+", args.url):
        raise ValueError("draft URL must match https://x.com/compose/articles/edit/<id>")
    if not re.fullmatch(r"[0-9a-f]{64}", args.content_sha256):
        raise ValueError("content SHA-256 must be 64 lowercase hex characters")
    if not article.is_file() or not cover.is_file():
        raise FileNotFoundError("article or cover file does not exist")

    text = article.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        raise ValueError("article must have YAML frontmatter")
    frontmatter = match.group(1)
    for field in FIELDS:
        frontmatter = re.sub(rf"(?m)^{re.escape(field)}:.*\n?", "", frontmatter)
    saved_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    additions = [
        f"x_article_status: {args.status}",
        f"x_article_draft_url: {quoted(args.url)}",
        f"x_article_saved_at: {saved_at}",
        f"x_article_cover: {quoted(str(cover))}",
        f"x_article_content_sha256: {args.content_sha256}",
    ]
    updated = "---\n" + frontmatter.rstrip() + "\n" + "\n".join(additions) + "\n---\n" + text[match.end():]
    article.write_text(updated, encoding="utf-8")
    print(f"OK: recorded draft {args.url}")


if __name__ == "__main__":
    main()
