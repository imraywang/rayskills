#!/usr/bin/env python3
"""Extract and verify absolute publication times for Reddit submission URLs."""

from __future__ import annotations

import re
import signal
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from contextlib import contextmanager
from html.parser import HTMLParser
from typing import Callable, Iterable
from urllib.parse import urlparse


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
MAX_REDDIT_FETCHES = 20
MAX_REDDIT_RESPONSE_BYTES = 2 * 1024 * 1024
REDDIT_REQUEST_TIMEOUT = 10.0
REDDIT_TOTAL_BUDGET = 45.0
REDDIT_URL_RE = re.compile(
    r"https?://(?:www\.|old\.)?reddit\.com/(?:r/[^/\s)\]>]+/)?comments/"
    r"[a-z0-9]+(?:/[^\s)\]>]*)?|https?://redd\.it/[a-z0-9]+",
    re.IGNORECASE,
)


class RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Reject every redirect before urllib opens the next destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(
            req.full_url, code, "reddit_redirect_rejected", headers, fp
        )


def _open_without_redirects(request: urllib.request.Request, timeout: float):
    return urllib.request.build_opener(RejectRedirects).open(request, timeout=timeout)


@contextmanager
def wall_clock_limit(seconds: float):
    """Enforce a POSIX wall-clock deadline for the blocking verifier call."""
    if seconds <= 0:
        raise TimeoutError("reddit_verification_deadline_exceeded")

    def alarm_handler(_signum, _frame):
        raise TimeoutError("reddit_verification_deadline_exceeded")

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def _parse_iso_datetime(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def extract_reddit_urls(text: str, limit: int | None = None) -> list[str]:
    """Return de-duplicated Reddit submission URLs in first-seen order."""
    seen: set[str] = set()
    urls: list[str] = []
    for match in REDDIT_URL_RE.finditer(text):
        url = match.group(0).rstrip(".,;:'\"")
        if url not in seen:
            seen.add(url)
            urls.append(url)
            if limit is not None and len(urls) >= limit:
                break
    return urls


def reddit_post_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    parts = [part for part in parsed.path.split("/") if part]
    if host.endswith("redd.it") and parts:
        return parts[0].lower()
    try:
        comments_index = parts.index("comments")
    except ValueError:
        return None
    if comments_index + 1 >= len(parts):
        return None
    return parts[comments_index + 1].lower()


def old_reddit_url(url: str) -> str | None:
    post_id = reddit_post_id(url)
    if not post_id:
        return None
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 4 and parts[0].lower() == "r" and parts[2] == "comments":
        subreddit = parts[1]
        slug = parts[4] if len(parts) > 4 else ""
        suffix = f"/{slug}" if slug else ""
        return f"https://old.reddit.com/r/{subreddit}/comments/{post_id}{suffix}/"
    return f"https://old.reddit.com/comments/{post_id}/"


class SubmissionTimeParser(HTMLParser):
    """Find the absolute time inside the submission node for a target post id."""

    def __init__(self, post_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.target_fullname = f"t3_{post_id.lower()}"
        self.div_depth = 0
        self.target_depth: int | None = None
        self.datetime_value: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value for key, value in attrs}
        if tag == "div":
            self.div_depth += 1
            if (
                self.target_depth is None
                and (attr_map.get("data-fullname") or "").lower() == self.target_fullname
            ):
                self.target_depth = self.div_depth
                timestamp = attr_map.get("data-timestamp")
                if timestamp and timestamp.isdigit():
                    value = datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.utc)
                    self.datetime_value = _iso_utc(value)
        elif (
            tag == "time"
            and self.target_depth is not None
            and self.div_depth == self.target_depth
            and not self.datetime_value
        ):
            candidate = attr_map.get("datetime")
            if candidate:
                self.datetime_value = _iso_utc(_parse_iso_datetime(candidate))

    def handle_endtag(self, tag: str) -> None:
        if tag != "div":
            return
        if self.target_depth == self.div_depth:
            self.target_depth = None
        self.div_depth = max(0, self.div_depth - 1)


def parse_submission_datetime(html: str, post_id: str) -> str | None:
    parser = SubmissionTimeParser(post_id)
    parser.feed(html)
    return parser.datetime_value


def fetch_old_reddit(
    url: str,
    timeout: float = REDDIT_REQUEST_TIMEOUT,
    deadline: float | None = None,
) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with _open_without_redirects(request, timeout) as response:
        final_url = response.geturl()
        try:
            final = urlparse(final_url)
            final_port = final.port
        except ValueError as exc:
            raise ValueError("unsafe_reddit_redirect") from exc
        if (
            final.scheme != "https"
            or (final.hostname or "").lower().rstrip(".") != "old.reddit.com"
            or final_port not in (None, 443)
            or final.username is not None
            or final.password is not None
            or final.fragment
            or reddit_post_id(final_url) != reddit_post_id(url)
        ):
            raise ValueError("unsafe_reddit_redirect")
        payload = bytearray()
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError("reddit_verification_deadline_exceeded")
            chunk = response.read(min(64 * 1024, MAX_REDDIT_RESPONSE_BYTES + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
            if len(payload) > MAX_REDDIT_RESPONSE_BYTES:
                raise ValueError("reddit_response_too_large")
        return bytes(payload).decode("utf-8", errors="replace")


def verify_reddit_url(
    url: str,
    since: datetime | None = None,
    until: datetime | None = None,
    fetcher: Callable[[str], str] = fetch_old_reddit,
    timeout: float = REDDIT_REQUEST_TIMEOUT,
) -> dict[str, object]:
    post_id = reddit_post_id(url)
    verification_url = old_reddit_url(url)
    base: dict[str, object] = {
        "url": url,
        "attempted": True,
        "post_id": post_id,
        "status": "unverified",
        "published_at_utc": None,
        "within_window": None,
        "date_source": None,
        "verification_url": verification_url,
    }
    if not post_id or not verification_url:
        base["error"] = "unsupported_reddit_url"
        return base

    try:
        html = (
            fetch_old_reddit(
                verification_url,
                timeout=timeout,
                deadline=time.monotonic() + timeout,
            )
            if fetcher is fetch_old_reddit
            else fetcher(verification_url)
        )
        published = parse_submission_datetime(html, post_id)
    except (OSError, OverflowError, TimeoutError, ValueError, urllib.error.URLError) as exc:
        base["error"] = f"fetch_failed: {exc}"
        return base

    if not published:
        base["error"] = "absolute_date_not_found"
        return base

    published_dt = _parse_iso_datetime(published)
    within_window: bool | None = None
    if since is not None or until is not None:
        within_window = True
        if since is not None and published_dt < since:
            within_window = False
        if until is not None and published_dt > until:
            within_window = False

    base.update(
        {
            "status": "verified",
            "published_at_utc": _iso_utc(published_dt),
            "within_window": within_window,
            "date_source": "old_reddit_submission_datetime",
        }
    )
    return base


def verify_reddit_urls(
    urls: Iterable[str],
    since: datetime | None = None,
    until: datetime | None = None,
    fetcher: Callable[[str], str] = fetch_old_reddit,
    total_budget: float = REDDIT_TOTAL_BUDGET,
) -> list[dict[str, object]]:
    started = time.monotonic()
    results: list[dict[str, object]] = []
    ordered_urls = list(dict.fromkeys(urls))
    for index, url in enumerate(ordered_urls):
        base_unverified = {
            "url": url,
            "attempted": False,
            "post_id": reddit_post_id(url),
            "status": "unverified",
            "published_at_utc": None,
            "within_window": None,
            "date_source": None,
            "verification_url": old_reddit_url(url),
        }
        if index >= MAX_REDDIT_FETCHES:
            results.append({**base_unverified, "error": "verification_limit_exceeded"})
            continue
        remaining = total_budget - (time.monotonic() - started)
        if remaining <= 0:
            results.append({**base_unverified, "error": "verification_budget_exhausted"})
            continue
        try:
            with wall_clock_limit(remaining):
                item = verify_reddit_url(
                    url,
                    since,
                    until,
                    fetcher,
                    timeout=min(REDDIT_REQUEST_TIMEOUT, remaining),
                )
        except TimeoutError:
            item = {
                **base_unverified,
                "attempted": True,
                "error": "verification_budget_exhausted",
            }
        if time.monotonic() - started > total_budget:
            item.update(
                {
                    "status": "unverified",
                    "published_at_utc": None,
                    "within_window": None,
                    "date_source": None,
                    "error": "verification_budget_exhausted",
                }
            )
        results.append(item)
    return results
