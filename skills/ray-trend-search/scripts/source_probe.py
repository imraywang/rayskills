#!/usr/bin/env python3
"""Probe local routes used by ray-trend-search without exposing credentials."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _first_existing(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        expanded = candidate.expanduser()
        if expanded.is_file():
            return expanded.resolve()
    return None


def _last30_script() -> Path | None:
    return _first_existing(
        [
            Path.home() / ".agents/skills/last30days/scripts/last30days.py",
            Path.home() / ".codex/skills/last30days/scripts/last30days.py",
        ]
    )


def _grok_wrapper() -> Path | None:
    skills_dir = Path(__file__).resolve().parents[2]
    return _first_existing(
        [
            skills_dir / "ray-multimodel/scripts/run_search.py",
            Path.home() / ".codex/skills/codex-grok-search/scripts/run_search.py",
            Path.home() / ".agents/skills/codex-grok-search/scripts/run_search.py",
        ]
    )


def _extract_json_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _last30_diagnose(script: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        completed = subprocess.run(
            [sys.executable, str(script), "--diagnose"],
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"diagnose_failed:{type(exc).__name__}"

    report = _extract_json_object(completed.stdout)
    if report is None:
        return None, f"diagnose_unreadable:exit_{completed.returncode}"
    return report, None


def build_report(run_diagnose: bool = True) -> dict[str, Any]:
    last30 = _last30_script()
    grok_wrapper = _grok_wrapper()
    grok_bin = _first_existing([Path.home() / ".grok/bin/grok"])
    yt_dlp = shutil.which("yt-dlp")

    diagnose: dict[str, Any] | None = None
    diagnose_error: str | None = None
    if run_diagnose and last30:
        diagnose, diagnose_error = _last30_diagnose(last30)

    def last30_ready(key: str) -> bool | None:
        if diagnose is None:
            return None
        value = diagnose.get(key)
        return value if isinstance(value, bool) else None

    grok_local_ready = bool(grok_wrapper and grok_bin)
    youtube_ready = bool(last30 and yt_dlp and last30_ready("youtube") is not False)

    return {
        "schema_version": 1,
        "routes": {
            "x": {
                "status": "ready" if grok_local_ready else "unavailable",
                "route": "grok",
                "note": "Live authentication is checked when a search runs.",
            },
            "reddit": {
                "status": "ready_with_permalink_fallback" if grok_local_ready else "unavailable",
                "route": "grok_then_public_web",
                "note": "Direct Reddit permalinks may require public-web recovery.",
            },
            "youtube": {
                "status": "ready" if youtube_ready else "unavailable",
                "route": "last30days_strict_filter",
            },
            "hackernews": {
                "status": "ready" if last30 and last30_ready("hackernews") is not False else "unavailable",
                "route": "last30days_strict_filter",
            },
            "polymarket": {
                "status": "ready" if last30 and last30_ready("polymarket") is not False else "unavailable",
                "route": "last30days",
            },
            "douyin": {"status": "browser_required", "route": "public_platform_search"},
            "video_accounts": {"status": "browser_required", "route": "public_platform_search"},
            "public_web": {"status": "agent_tool_required", "route": "public_web_search"},
        },
        "tools": {
            "last30days_script": str(last30) if last30 else None,
            "grok_wrapper": str(grok_wrapper) if grok_wrapper else None,
            "grok_binary": str(grok_bin) if grok_bin else None,
            "yt_dlp": yt_dlp,
        },
        "last30days_diagnose": diagnose,
        "diagnose_error": diagnose_error,
        "warnings": [
            "This probe checks route availability, not search-result quality.",
            "A restricted environment may block access to the local Grok session even when Grok is logged in.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe ray-trend-search source routes.")
    parser.add_argument(
        "--no-last30-diagnose",
        action="store_true",
        help="Skip running last30days --diagnose.",
    )
    args = parser.parse_args()
    print(json.dumps(build_report(not args.no_last30_diagnose), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
