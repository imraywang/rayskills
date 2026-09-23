#!/usr/bin/env python3
"""Collect supported last30days sources and enforce a strict recent window."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


REPORT_MARKERS = {"topic", "range", "youtube", "hackernews", "polymarket"}


def locate_last30days() -> Path | None:
    candidates = [
        Path.home() / ".agents/skills/last30days/scripts/last30days.py",
        Path.home() / ".codex/skills/last30days/scripts/last30days.py",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def extract_report(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    candidates: list[dict[str, Any]] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            candidates.append(value)

    for value in candidates:
        if len(REPORT_MARKERS.intersection(value.keys())) >= 2:
            return value
    raise ValueError("No last30days JSON report found in command output")


def parse_item_date(item: dict[str, Any]) -> date | None:
    keys = (
        "date",
        "upload_date",
        "published_at",
        "publishedAt",
        "created_at",
        "timestamp",
    )
    for key in keys:
        raw = item.get(key)
        if raw in (None, ""):
            continue
        if isinstance(raw, (int, float)):
            try:
                return datetime.fromtimestamp(raw, tz=timezone.utc).date()
            except (OverflowError, OSError, ValueError):
                continue
        value = str(raw).strip()
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(value.replace("Z", "+0000"), fmt).date()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            continue
    return None


def partition_by_window(
    items: Iterable[dict[str, Any]], start: date, end: date
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    recent: list[dict[str, Any]] = []
    old: list[dict[str, Any]] = []
    undated: list[dict[str, Any]] = []
    for item in items:
        item_date = parse_item_date(item)
        if item_date is None:
            undated.append(item)
        elif start <= item_date <= end:
            recent.append(item)
        else:
            old.append(item)
    return recent, old, undated


def _list_field(report: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = report.get(key, [])
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for child_key in ("items", "results", "videos", "posts", "markets"):
            child = value.get(child_key)
            if isinstance(child, list):
                return [item for item in child if isinstance(item, dict)]
    return []


def collect(
    topic: str,
    video_query: str,
    days: int,
    mode: str,
    timeout: int,
    last30_script: Path,
) -> dict[str, Any]:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)

    with tempfile.TemporaryDirectory(prefix="ray-trend-search-") as temp_dir:
        command = [
            sys.executable,
            str(last30_script),
            video_query,
            "--emit=json",
            "--search=youtube,hn,polymarket",
            f"--days={days}",
            "--no-native-web",
            f"--save-dir={temp_dir}",
        ]
        if mode == "quick":
            command.append("--quick")
        elif mode == "deep":
            command.append("--deep")

        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "schema_version": 1,
                "topic": topic,
                "source_query": video_query,
                "window": {"from": start.isoformat(), "to": end.isoformat(), "days": days},
                "source_status": {"last30days": "unavailable"},
                "recent": {"youtube": [], "hackernews": [], "polymarket": []},
                "background": {"youtube": [], "hackernews": [], "undated": []},
                "warnings": [f"last30days timed out after {exc.timeout} seconds"],
            }

    warnings: list[str] = []
    try:
        report = extract_report(completed.stdout)
    except ValueError as exc:
        stderr_tail = completed.stderr.strip()[-500:]
        warnings.append(str(exc))
        if stderr_tail:
            warnings.append(f"stderr_tail: {stderr_tail}")
        return {
            "schema_version": 1,
            "topic": topic,
            "source_query": video_query,
            "window": {"from": start.isoformat(), "to": end.isoformat(), "days": days},
            "source_status": {
                "last30days": "unavailable" if completed.returncode else "degraded"
            },
            "recent": {"youtube": [], "hackernews": [], "polymarket": []},
            "background": {"youtube": [], "hackernews": [], "undated": []},
            "warnings": warnings,
        }

    youtube = _list_field(report, "youtube")
    hackernews = _list_field(report, "hackernews") or _list_field(report, "hn")
    polymarket = _list_field(report, "polymarket")

    yt_recent, yt_old, yt_undated = partition_by_window(youtube, start, end)
    hn_recent, hn_old, hn_undated = partition_by_window(hackernews, start, end)

    if yt_old or yt_undated:
        warnings.append(
            "Older or undated YouTube results were moved to background and are not counted as recent."
        )
    if hn_old or hn_undated:
        warnings.append(
            "Older or undated Hacker News results were moved to background and are not counted as recent."
        )
    if completed.returncode:
        warnings.append(f"last30days exited with status {completed.returncode}; inspect source coverage.")

    return {
        "schema_version": 1,
        "topic": topic,
        "source_query": video_query,
        "window": {"from": start.isoformat(), "to": end.isoformat(), "days": days},
        "source_status": {
            "last30days": "ok" if completed.returncode == 0 else "degraded",
            "youtube": "ok" if youtube or completed.returncode == 0 else "degraded",
            "hackernews": "ok" if hackernews or completed.returncode == 0 else "degraded",
            "polymarket": "ok" if polymarket or completed.returncode == 0 else "degraded",
            "x": "not_requested",
            "reddit": "not_requested",
        },
        "recent": {
            "youtube": yt_recent,
            "hackernews": hn_recent,
            "polymarket": polymarket,
        },
        "background": {
            "youtube": yt_old,
            "hackernews": hn_old,
            "undated": yt_undated + hn_undated,
        },
        "counts": {
            "youtube_recent": len(yt_recent),
            "youtube_background": len(yt_old) + len(yt_undated),
            "hackernews_recent": len(hn_recent),
            "hackernews_background": len(hn_old) + len(hn_undated),
            "polymarket_active": len(polymarket),
        },
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect YouTube/HN/Polymarket via last30days with a strict date window."
    )
    parser.add_argument("--topic", required=True, help="Human-readable research topic.")
    parser.add_argument(
        "--video-query",
        required=True,
        help="Short YouTube-oriented query, normally 3-6 words in one language.",
    )
    parser.add_argument("--days", type=int, default=30, choices=range(1, 31), metavar="1-30")
    parser.add_argument("--mode", choices=("quick", "balanced", "deep"), default="quick")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--last30-script", type=Path, help="Override the last30days script path.")
    args = parser.parse_args()

    script = args.last30_script.expanduser().resolve() if args.last30_script else locate_last30days()
    if not script or not script.is_file():
        print("last30days script not found", file=sys.stderr)
        return 2

    result = collect(
        topic=args.topic,
        video_query=args.video_query,
        days=args.days,
        mode=args.mode,
        timeout=args.timeout,
        last30_script=script,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "source_status": result["source_status"],
                "counts": result.get("counts", {}),
                "warnings": result.get("warnings", []),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["source_status"]["last30days"] != "unavailable" else 1


if __name__ == "__main__":
    raise SystemExit(main())
