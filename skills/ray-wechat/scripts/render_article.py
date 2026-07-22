#!/usr/bin/env python3
"""Render a Markdown article into one clean, inline-styled WeChat fragment."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


SKILL_ROOT = Path(__file__).resolve().parent.parent
THEMES_PATH = SKILL_ROOT / "references" / "ray-themes.json"


def load_themes() -> dict[str, dict]:
    return json.loads(THEMES_PATH.read_text(encoding="utf-8"))


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


def article_title(meta: dict[str, str], body: str) -> str:
    if meta.get("title"):
        return meta["title"]
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "公众号排版预览"


def safe_href(value: str) -> str:
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme.lower() not in {"http", "https", "mailto"}:
        return "#"
    return html.escape(value, quote=True)


def inline_markup(text: str, styles: dict[str, str]) -> str:
    token_re = re.compile(
        r"(`[^`]+`|\*\*.+?\*\*|__.+?__|\[[^\]]+\]\([^)]+\)|(?<!\*)\*[^*]+\*(?!\*)|(?<!_)_[^_]+_(?!_))"
    )
    parts: list[str] = []
    cursor = 0
    for match in token_re.finditer(text):
        parts.append(html.escape(text[cursor : match.start()]))
        token = match.group(0)
        if token.startswith("`"):
            parts.append(f'<code style="{styles["code"]}">{html.escape(token[1:-1])}</code>')
        elif token.startswith(("**", "__")):
            parts.append(
                f'<strong style="{styles["strong"]}">{html.escape(token[2:-2])}</strong>'
            )
        elif token.startswith("["):
            link = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", token)
            if link:
                label, href = link.groups()
                parts.append(
                    f'<a href="{safe_href(href)}" style="{styles["a"]}">{html.escape(label)}</a>'
                )
            else:
                parts.append(html.escape(token))
        else:
            parts.append(f'<em style="{styles["em"]}">{html.escape(token[1:-1])}</em>')
        cursor = match.end()
    parts.append(html.escape(text[cursor:]))
    return "".join(parts)


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_table(lines: list[str], styles: dict[str, str]) -> str:
    header = table_cells(lines[0])
    rows = [table_cells(line) for line in lines[2:]]
    head = "".join(
        f'<th style="{styles["th"]}">{inline_markup(cell, styles)}</th>' for cell in header
    )
    body_rows = []
    for row in rows:
        cells = "".join(
            f'<td style="{styles["td"]}">{inline_markup(cell, styles)}</td>' for cell in row
        )
        body_rows.append(f"<tr>{cells}</tr>")
    return f'<table style="{styles["table"]}"><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table>'


def render_markdown(body: str, styles: dict[str, str]) -> str:
    lines = body.splitlines()
    rendered: list[str] = []
    paragraph: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph).strip()
            if text:
                rendered.append(f'<p style="{styles["p"]}">{inline_markup(text, styles)}</p>')
            paragraph.clear()

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            rendered.append(f'<pre style="{styles["pre"]}">{html.escape(chr(10).join(code_lines))}</pre>')
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            rendered.append(f'<h3 style="{styles["h2"]}">{inline_markup(stripped[3:], styles)}</h3>')
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            rendered.append(f'<h4 style="{styles["h3"]}">{inline_markup(stripped[4:], styles)}</h4>')
            index += 1
            continue
        if re.fullmatch(r"(?:---+|\*\*\*+|___+)", stripped):
            flush_paragraph()
            rendered.append(f'<hr style="{styles["hr"]}">')
            index += 1
            continue

        image = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if image:
            flush_paragraph()
            alt, src = image.groups()
            rendered.append(
                f'<img src="{safe_href(src)}" alt="{html.escape(alt, quote=True)}" style="{styles["img"]}">'
            )
            index += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(re.sub(r"^>\s?", "", lines[index].strip()))
                index += 1
            quote = " ".join(quote_lines).strip()
            rendered.append(f'<blockquote style="{styles["blockquote"]}">{inline_markup(quote, styles)}</blockquote>')
            continue

        list_match = re.match(r"^(?:([-*+])|(\d+)[.)])\s+(.+)$", stripped)
        if list_match:
            flush_paragraph()
            ordered = bool(list_match.group(2))
            tag = "ol" if ordered else "ul"
            items: list[str] = []
            while index < len(lines):
                item = re.match(r"^(?:([-*+])|(\d+)[.)])\s+(.+)$", lines[index].strip())
                if not item or bool(item.group(2)) != ordered:
                    break
                items.append(item.group(3))
                index += 1
            item_html = "".join(
                f'<li style="{styles["li"]}">{inline_markup(item, styles)}</li>' for item in items
            )
            rendered.append(f'<{tag} style="{styles[tag]}">{item_html}</{tag}>')
            continue

        if (
            "|" in stripped
            and index + 1 < len(lines)
            and is_table_separator(lines[index + 1])
        ):
            flush_paragraph()
            table_lines = [raw, lines[index + 1]]
            index += 2
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                table_lines.append(lines[index])
                index += 1
            rendered.append(render_table(table_lines, styles))
            continue

        paragraph.append(raw)
        index += 1

    flush_paragraph()
    return "\n".join(rendered)


def preview_document(fragment: str, title: str, theme: dict) -> str:
    page_title = html.escape(title or "公众号排版预览")
    theme_name = html.escape(theme["name"])
    background = theme["preview_background"]
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title} · {theme_name}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:{background};font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}.bar{{position:sticky;top:0;z-index:2;display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:#151515;color:#fff;font-size:13px}}button{{border:1px solid #fff;background:#fff;color:#111;padding:7px 13px;border-radius:3px;font:inherit;cursor:pointer}}main{{width:min(100%,420px);margin:18px auto 40px;box-shadow:0 8px 28px rgba(0,0,0,.08)}}@media(max-width:460px){{main{{margin:0 auto;box-shadow:none}}}}
</style>
</head>
<body>
<div class="bar"><span>{theme_name} · 420px 手机预览</span><button id="copy-button" type="button" onclick="copyArticle()">复制到公众号</button></div>
<main id="copy-root">{fragment}</main>
<script>
function copyArticle(){{const root=document.getElementById('copy-root');const button=document.getElementById('copy-button');const range=document.createRange();range.selectNodeContents(root);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);const copied=document.execCommand('copy');selection.removeAllRanges();button.textContent=copied?'已复制':'请手动复制';setTimeout(()=>{{button.textContent='复制到公众号'}},1600);}}
</script>
</body>
</html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Ray WeChat article theme")
    parser.add_argument("--article", type=Path)
    parser.add_argument("--theme")
    parser.add_argument("--html", type=Path)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--list-themes", action="store_true")
    args = parser.parse_args()

    themes = load_themes()
    if args.list_themes:
        for key, theme in themes.items():
            print(f'{key}\t{theme["name"]}\t{theme["description"]}')
        return 0
    if not args.article or not args.theme or not args.html:
        parser.error("--article, --theme and --html are required unless --list-themes is used")
    if args.theme not in themes:
        print(f"unknown theme: {args.theme}", file=sys.stderr)
        return 2

    raw = args.article.read_text(encoding="utf-8")
    meta, body = split_frontmatter(raw)
    if meta.get("kind") in {"content-pack", "idea", "research"}:
        print(f'source is {meta["kind"]}, not a final article', file=sys.stderr)
        return 2
    theme = themes[args.theme]
    content = render_markdown(body, theme["styles"])
    fragment = f'<section style="{theme["styles"]["container"]}">\n{content}\n</section>\n'
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(fragment, encoding="utf-8")
    title = article_title(meta, body)
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        args.preview.write_text(
            preview_document(fragment, title, theme), encoding="utf-8"
        )
    print(
        json.dumps(
            {
                "article": str(args.article.resolve()),
                "theme": args.theme,
                "theme_name": theme["name"],
                "title": title,
                "html": str(args.html.resolve()),
                "preview": str(args.preview.resolve()) if args.preview else "",
                "status": "rendered",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
