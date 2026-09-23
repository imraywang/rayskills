from __future__ import annotations

import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/collect_last30.py"
SPEC = importlib.util.spec_from_file_location("collect_last30", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CollectLast30Tests(unittest.TestCase):
    def test_extract_report_ignores_progress_json(self) -> None:
        report = {
            "topic": "enterprise AI",
            "range": {"days": 30},
            "youtube": [{"title": "Example", "date": "2026-08-20"}],
        }
        text = 'progress {"step": 1}\n' + json.dumps(report) + "\nWEBSEARCH REQUIRED"
        self.assertEqual(MODULE.extract_report(text), report)

    def test_partition_enforces_window_and_preserves_unknowns(self) -> None:
        items = [
            {"title": "recent", "date": "2026-08-20"},
            {"title": "old", "date": "2025-08-20"},
            {"title": "unknown"},
        ]
        recent, old, undated = MODULE.partition_by_window(
            items, date(2026, 8, 1), date(2026, 8, 26)
        )
        self.assertEqual([item["title"] for item in recent], ["recent"])
        self.assertEqual([item["title"] for item in old], ["old"])
        self.assertEqual([item["title"] for item in undated], ["unknown"])

    def test_parse_compact_and_iso_dates(self) -> None:
        self.assertEqual(MODULE.parse_item_date({"upload_date": "20260818"}), date(2026, 8, 18))
        self.assertEqual(
            MODULE.parse_item_date({"published_at": "2026-08-18T12:30:00Z"}),
            date(2026, 8, 18),
        )


if __name__ == "__main__":
    unittest.main()
