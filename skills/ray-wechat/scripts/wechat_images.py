#!/usr/bin/env python3
"""Upload the local body images of a rendered fragment and rewrite them in place.

render_article.py deliberately leaves local absolute paths in `src`; this script
turns each of them into a hosted mmbiz URL. prepare_article.py then refuses any
fragment that still points at a local file, so an article can never reach the
draft API with an image WeChat cannot serve.

Uploads go to media/uploadimg, which returns a permanent URL for use inside
article bodies and does not consume the material library quota.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from prepare_article import IMG_SRC
from wechat_draft import (
    DEFAULT_API_BASE,
    DraftError,
    access_token,
    credentials,
    multipart,
    request_json,
    tls_context,
)
from wechat_egress import EgressError, fixed_egress


DEFAULT_CACHE = Path("~/.wewrite/image-cache.json").expanduser()
MAX_BYTES = 1024 * 1024
ACCEPTED = {".jpg", ".jpeg", ".png"}


def load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_cache(path: Path, cache: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        json.dump(cache, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp = Path(handle.name)
    os.replace(temp, path)


def fit_for_wechat(source: Path) -> tuple[str, bytes]:
    """Return (filename, bytes) small enough and in a format WeChat accepts."""
    payload = source.read_bytes()
    if source.suffix.lower() in ACCEPTED and len(payload) <= MAX_BYTES:
        return source.name, payload
    try:
        from PIL import Image
    except ImportError:
        raise DraftError(
            f"{source.name} is {len(payload) // 1024}KB or an unsupported format; "
            "install Pillow so it can be re-encoded, or shrink it by hand"
        ) from None
    with Image.open(source) as image:
        image = image.convert("RGB")
        image.thumbnail((1600, 1600))
        for quality in (88, 78, 68, 58):
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            if buffer.tell() <= MAX_BYTES:
                return f"{source.stem}.jpg", buffer.getvalue()
    raise DraftError(f"cannot shrink {source.name} under 1MB; provide a smaller image")


def upload_image(api_base: str, token: str, source: Path) -> str:
    filename, payload = fit_for_wechat(source)
    body, content_type = multipart(filename, payload)
    data = request_json(
        f"{api_base}/media/uploadimg",
        label=f"body image upload ({source.name})",
        params={"access_token": token},
        body=body,
        content_type=content_type,
    )
    url = data.get("url")
    if not url:
        raise DraftError(f"uploadimg response for {source.name} is missing url")
    return normalize_hosted_url(url)


def normalize_hosted_url(url: str) -> str:
    """Upgrade WeChat's legacy mmbiz image URLs to HTTPS."""
    parsed = urlparse(url)
    if parsed.scheme == "http" and (parsed.hostname or "").endswith(".qpic.cn"):
        return parsed._replace(scheme="https").geturl()
    return url


def local_sources(fragment: str) -> list[str]:
    seen: list[str] = []
    for src in IMG_SRC.findall(fragment):
        if urlparse(src).scheme.lower() in {"http", "https"}:
            continue
        if src not in seen:
            seen.append(src)
    return seen


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload WeChat body images and rewrite the fragment")
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=Path("~/.wewrite/config.yaml").expanduser())
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    fragment = args.html.read_text(encoding="utf-8")
    pending = local_sources(fragment)
    if not pending:
        print(json.dumps({"status": "no-local-images", "uploaded": 0}, ensure_ascii=False))
        return 0

    missing = [src for src in pending if not Path(src).is_file()]
    if missing:
        raise DraftError(f"images referenced but not on disk: {missing}")

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "local_images": pending}, ensure_ascii=False, indent=2))
        return 0

    cache = load_cache(args.cache)
    appid, secret, _ = credentials(args.config.expanduser())
    api_base = os.environ.get("RAY_WECHAT_API_BASE", DEFAULT_API_BASE).rstrip("/")
    try:
        with fixed_egress(tls_context()):
            token = access_token(api_base, appid, secret)

            mapping: dict[str, str] = {}
            reused = 0
            for src in pending:
                source = Path(src)
                key = hashlib.sha256(source.read_bytes()).hexdigest()
                url = normalize_hosted_url(cache.get(key, ""))
                if url:
                    reused += 1
                    cache[key] = url
                else:
                    url = upload_image(api_base, token, source)
                    cache[key] = url
                mapping[src] = url
    except EgressError as exc:
        raise DraftError(str(exc)) from None

    def swap(match: re.Match) -> str:
        src = match.group(1)
        return match.group(0).replace(f'"{src}"', f'"{mapping[src]}"') if src in mapping else match.group(0)

    updated = IMG_SRC.sub(swap, fragment)
    if local_sources(updated):
        raise DraftError("rewrite left local image paths behind")
    args.html.write_text(updated, encoding="utf-8")
    save_cache(args.cache, cache)

    print(
        json.dumps(
            {
                "status": "uploaded",
                "html": str(args.html.resolve()),
                "images": len(mapping),
                "reused_from_cache": reused,
                "cache": str(args.cache),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DraftError as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1) from None
