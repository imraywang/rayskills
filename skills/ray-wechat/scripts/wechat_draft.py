#!/usr/bin/env python3
"""Create, update, or verify a WeChat official-account draft safely."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from prepare_article import (
    FragmentParser,
    SIGNATURE_MARKERS,
    has_mojibake,
    mojibake_candidate,
    source_blocks,
    split_frontmatter,
)


DEFAULT_API_BASE = "https://api.weixin.qq.com/cgi-bin"
SCRIPT_DIR = Path(__file__).resolve().parent


class DraftError(RuntimeError):
    pass


def read_wechat_config(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    in_wechat = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^wechat:\s*(?:#.*)?$", raw):
            in_wechat = True
            continue
        if in_wechat and raw and not raw[0].isspace():
            break
        if not in_wechat:
            continue
        match = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*?)\s*$", raw)
        if not match:
            continue
        value = match.group(2)
        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[match.group(1)] = value
    return values


def credentials(config: Path) -> tuple[str, str, str]:
    cfg = read_wechat_config(config)
    appid = os.environ.get("WECHAT_APPID") or cfg.get("appid", "")
    secret = os.environ.get("WECHAT_SECRET") or cfg.get("secret", "")
    author = os.environ.get("WECHAT_AUTHOR") or cfg.get("author", "")
    if not appid or not secret:
        raise DraftError("WeChat credentials are missing")
    return appid, secret, author


def request_json(
    url: str,
    *,
    label: str,
    params: dict[str, str] | None = None,
    payload: dict | None = None,
    body: bytes | None = None,
    content_type: str = "application/json; charset=utf-8",
) -> dict:
    if params:
        url = f"{url}?{urlencode(params)}"
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": content_type} if body is not None else {}
    request = Request(url, data=body, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read()
    except (HTTPError, URLError, TimeoutError, OSError):
        raise DraftError(f"{label} network request failed") from None
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DraftError(f"{label} returned invalid UTF-8 JSON") from None
    if data.get("errcode", 0) not in (0, None):
        raise DraftError(f"{label} failed: {data.get('errcode')} {data.get('errmsg', '')}")
    return data


def access_token(api_base: str, appid: str, secret: str) -> str:
    data = request_json(
        f"{api_base}/token",
        label="token",
        params={"grant_type": "client_credential", "appid": appid, "secret": secret},
    )
    token = data.get("access_token")
    if not token:
        raise DraftError("token response is missing access_token")
    return token


def draft_get(api_base: str, token: str, media_id: str) -> dict:
    data = request_json(
        f"{api_base}/draft/get",
        label="draft/get",
        params={"access_token": token},
        payload={"media_id": media_id},
    )
    items = data.get("news_item") or []
    if len(items) != 1:
        raise DraftError(f"expected one article in draft, got {len(items)}")
    return items[0]


def upload_cover(api_base: str, token: str, cover: Path) -> str:
    if not cover.exists():
        raise DraftError(f"cover not found: {cover}")
    boundary = f"----raywechat{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(cover.name)[0] or "application/octet-stream"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="media"; filename="{cover.name}"\r\n'.encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            cover.read_bytes(),
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
    data = request_json(
        f"{api_base}/material/add_material",
        label="cover upload",
        params={"access_token": token, "type": "image"},
        body=body,
        content_type=f"multipart/form-data; boundary={boundary}",
    )
    media_id = data.get("media_id")
    if not media_id:
        raise DraftError("cover upload response is missing media_id")
    return media_id


def repair_mojibake(value: str) -> str:
    current = value
    for _ in range(2):
        candidate = mojibake_candidate(current)
        if candidate is None:
            break
        current = candidate
    return current


def run_prepare(article: Path, html: Path, signature: str) -> dict:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "prepare_article.py"),
            "--article",
            str(article),
            "--html",
            str(html),
            "--signature",
            signature,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        manifest = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise DraftError("local article validation did not return JSON") from None
    if result.returncode != 0 or manifest.get("errors"):
        raise DraftError(f"local article validation failed: {manifest.get('errors', [])}")
    return manifest


def article_payload(
    *,
    title: str,
    author: str,
    digest: str,
    content: str,
    thumb_media_id: str,
    previous: dict | None,
) -> dict:
    if not title:
        raise DraftError("article title is missing")
    if not thumb_media_id:
        raise DraftError("cover media_id is missing")
    if len(digest.encode("utf-8")) > 120:
        raise DraftError("digest exceeds 120 UTF-8 bytes")
    previous = previous or {}
    return {
        "title": title,
        "author": author,
        "digest": digest,
        "content": content,
        "content_source_url": previous.get("content_source_url", ""),
        "thumb_media_id": thumb_media_id,
        "need_open_comment": previous.get("need_open_comment", 0),
        "only_fans_can_comment": previous.get("only_fans_can_comment", 0),
    }


def verify_remote(
    *,
    stored: dict,
    article: Path,
    manifest: dict,
    expected_title: str,
    expected_digest: str,
    expected_author: str,
    expected_cover: str,
    signature: str,
) -> dict:
    md = article.read_text(encoding="utf-8")
    _, body = split_frontmatter(md)
    blocks, _, _, source_has_signature = source_blocks(body)
    content = stored.get("content", "")
    parsed = FragmentParser()
    parsed.feed(content)
    visible = re.sub(r"\s+", "", "".join(parsed.text))

    cursor = 0
    missing: list[str] = []
    for block in blocks:
        found = visible.find(block, cursor)
        if found < 0:
            missing.append(block[:48])
        else:
            cursor = found + len(block)

    has_signature = bool(re.search(r"我是.{1,40}[，,]", visible)) or any(
        marker in visible for marker in SIGNATURE_MARKERS
    )
    signature_ok = (
        (signature == "absent" and not has_signature)
        or (signature == "present" and has_signature)
        or (signature == "inherit" and has_signature == source_has_signature)
    )
    combined = "\n".join(
        [stored.get("title", ""), stored.get("digest", ""), visible]
    )
    checks = {
        "title_correct": stored.get("title", "") == expected_title,
        "digest_correct": stored.get("digest", "") == expected_digest,
        "author_correct": stored.get("author", "") == expected_author,
        "cover_correct": stored.get("thumb_media_id", "") == expected_cover,
        "all_source_blocks_present": not missing,
        "empty_paragraphs": parsed.empty_paragraphs,
        "chapter_count": parsed.h3_count,
        "strong_count": parsed.strong_count,
        "signature_correct": signature_ok,
        "encoding_correct": not has_mojibake(combined),
    }
    ok = all(
        [
            checks["title_correct"],
            checks["digest_correct"],
            checks["author_correct"],
            checks["cover_correct"],
            checks["all_source_blocks_present"],
            checks["empty_paragraphs"] == 0,
            checks["chapter_count"] == manifest["chapter_count"],
            checks["strong_count"] == manifest["html_strong_count"],
            checks["signature_correct"],
            checks["encoding_correct"],
        ]
    )
    if not ok:
        raise DraftError(f"remote verification failed: {checks}; missing={missing[:5]}")
    return checks


def yaml_value(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def record_frontmatter(
    article: Path,
    *,
    media_id: str,
    theme: str,
    cover: Path | None,
    created: bool,
) -> None:
    text = article.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise DraftError("cannot record draft state: article has no frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise DraftError("cannot record draft state: frontmatter is not closed")
    head = text[4:end]
    tail = text[end + 5 :]
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    updates = {
        "wechat_draft_status": "draft",
        "wechat_draft_media_id": media_id,
        "wechat_draft_theme": theme,
        "wechat_draft_updated_at": now,
    }
    if created or "wechat_draft_saved_at:" not in head:
        updates["wechat_draft_saved_at"] = now
    if cover:
        updates["wechat_draft_cover"] = str(cover.resolve())

    for key, value in updates.items():
        rendered = value if key.endswith(("_at", "_status", "_theme")) else yaml_value(value)
        pattern = re.compile(rf"^{re.escape(key)}:.*$", re.M)
        line = f"{key}: {rendered}"
        if pattern.search(head):
            head = pattern.sub(line, head)
        else:
            head = f"{head.rstrip()}\n{line}"

    new_text = f"---\n{head}\n---\n{tail}"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=article.parent, prefix=f".{article.name}.", delete=False
    ) as handle:
        handle.write(new_text)
        temp_path = Path(handle.name)
    os.replace(temp_path, article)


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--article", required=True, type=Path)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=Path("~/.wewrite/config.yaml").expanduser())
    parser.add_argument("--media-id")
    parser.add_argument("--title")
    parser.add_argument("--author")
    parser.add_argument("--digest")
    parser.add_argument("--cover", type=Path)
    parser.add_argument("--cover-media-id")
    parser.add_argument("--theme", default="ray-editorial")
    parser.add_argument("--signature", choices=("absent", "present", "inherit"), default="inherit")
    parser.add_argument("--record", action="store_true")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage a WeChat official-account draft")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("create", "update", "verify"):
        child = sub.add_parser(name)
        add_common(child)
        if name != "verify":
            child.add_argument("--confirm", action="store_true")
    args = parser.parse_args()

    manifest = run_prepare(args.article, args.html, args.signature)
    md = args.article.read_text(encoding="utf-8")
    meta, _ = split_frontmatter(md)
    media_id = args.media_id or meta.get("wechat_draft_media_id", "")

    if args.command in ("update", "verify") and not media_id:
        raise DraftError("existing wechat_draft_media_id is required")
    if args.command in ("create", "update") and not args.confirm:
        raise DraftError("external draft write requires --confirm")
    if args.command == "create" and media_id:
        raise DraftError("article already has a draft media_id; use update")

    appid, secret, config_author = credentials(args.config.expanduser())
    api_base = os.environ.get("RAY_WECHAT_API_BASE", DEFAULT_API_BASE).rstrip("/")
    token = access_token(api_base, appid, secret)
    content = args.html.read_text(encoding="utf-8").strip()
    existing = draft_get(api_base, token, media_id) if media_id else None

    title = args.title or meta.get("title", "") or (existing or {}).get("title", "")
    author = args.author if args.author is not None else (existing or {}).get("author", config_author)
    old_digest = repair_mojibake((existing or {}).get("digest", ""))
    digest = args.digest if args.digest is not None else old_digest
    cover_media_id = args.cover_media_id or (existing or {}).get("thumb_media_id", "")
    if args.cover:
        cover_media_id = upload_cover(api_base, token, args.cover)
    if args.command == "create" and not digest:
        raise DraftError("create requires an explicit digest")

    if args.command == "verify":
        stored = existing or {}
        expected_title = args.title or meta.get("title", "") or stored.get("title", "")
        expected_digest = args.digest if args.digest is not None else repair_mojibake(stored.get("digest", ""))
        expected_author = args.author if args.author is not None else stored.get("author", "")
        expected_cover = args.cover_media_id or stored.get("thumb_media_id", "")
        checks = verify_remote(
            stored=stored,
            article=args.article,
            manifest=manifest,
            expected_title=expected_title,
            expected_digest=expected_digest,
            expected_author=expected_author,
            expected_cover=expected_cover,
            signature=args.signature,
        )
        print(json.dumps({"status": "verified", "media_id": media_id, "checks": checks}, ensure_ascii=False, indent=2))
        return 0

    payload = article_payload(
        title=title,
        author=author,
        digest=digest,
        content=content,
        thumb_media_id=cover_media_id,
        previous=existing,
    )
    if args.command == "update":
        request_json(
            f"{api_base}/draft/update",
            label="draft/update",
            params={"access_token": token},
            payload={"media_id": media_id, "index": 0, "articles": payload},
        )
    else:
        created = request_json(
            f"{api_base}/draft/add",
            label="draft/add",
            params={"access_token": token},
            payload={"articles": [payload]},
        )
        media_id = created.get("media_id", "")
        if not media_id:
            raise DraftError("draft/add response is missing media_id")

    stored = draft_get(api_base, token, media_id)
    checks = verify_remote(
        stored=stored,
        article=args.article,
        manifest=manifest,
        expected_title=title,
        expected_digest=digest,
        expected_author=author,
        expected_cover=cover_media_id,
        signature=args.signature,
    )
    if args.record:
        record_frontmatter(
            args.article,
            media_id=media_id,
            theme=args.theme,
            cover=args.cover,
            created=args.command == "create",
        )
    print(
        json.dumps(
            {
                "status": "draft",
                "operation": args.command,
                "media_id": media_id,
                "title": title,
                "checks": checks,
                "recorded": args.record,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DraftError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
