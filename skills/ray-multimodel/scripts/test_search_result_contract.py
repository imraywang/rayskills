"""Regression coverage for complete Grok responses rejected by undisclosed rules."""

import copy
import json
import unittest
from datetime import datetime, timezone

import run_search as search


class ResultContractTests(unittest.TestCase):
    def setUp(self):
        self.since = datetime(2026, 7, 10, tzinfo=timezone.utc)
        self.until = datetime(2026, 9, 8, tzinfo=timezone.utc)
        self.payload = {
            "schema_version": 1,
            "session_id": "test-session",
            "summary": ["A user reports receiving SMS."],
            "findings": [{
                "id": "F1", "platform": "x", "source_kind": "social_post",
                "title_or_excerpt": "SMS experience", "author": "Example",
                "claimed_publication_time": "2026-09-07T00:00:00Z",
                "date_evidence": "platform_search",
                "direct_url": "https://x.com/example/status/123456789",
                "evidence_summary": "A personal report, not a carrier guarantee.",
                "visible_metrics": [],
            }],
            "cross_checks": [],
            "limitations": ["One public report only."],
        }

    def validate(self, payload=None):
        return search.validate_result_payload(
            self.payload if payload is None else payload,
            "test-session", "x", self.since, self.until,
        )

    def test_complete_cli_text_with_progress(self):
        envelope = json.dumps({"sessionId": "test-session", "text":
                               "Searching X. " + json.dumps(self.payload)})
        text = search._extract_json_report(envelope, "test-session")
        result, error = search.parse_result_text(
            text, "test-session", "x", self.since, self.until)
        self.assertEqual(result, self.payload)
        self.assertIsNone(error)

    def test_summary_overflow_is_still_rejected(self):
        self.payload["summary"] *= 11
        self.assertEqual(self.validate(), (False, "invalid_summary"))

    def test_unattached_background_is_still_rejected(self):
        self.payload["cross_checks"] = [{
            "finding_ids": [], "stance": "context",
            "source_url": "https://example.com/background",
            "summary": "Unrelated product background.",
        }]
        self.assertEqual(self.validate(), (False, "invalid_cross_check_finding_ids"))
        self.payload["cross_checks"][0]["finding_ids"] = ["F1"]
        self.assertEqual(self.validate(), (True, None))

    def test_invalid_references_do_not_crash_validator(self):
        for reference in ["F2", {}, [], None, 1]:
            with self.subTest(reference=reference):
                self.payload["cross_checks"] = [{
                    "finding_ids": [reference], "stance": "context",
                    "source_url": "https://example.com/background", "summary": "Context.",
                }]
                self.assertEqual(self.validate(), (False, "invalid_cross_check_finding_ids"))

    def test_scope_date_and_session_are_not_relaxed(self):
        for field, value, error in [
            ("platform", "web", "finding_platform_out_of_scope"),
            ("claimed_publication_time", "2026-02-23T00:03:00Z", "finding_outside_requested_window"),
            ("direct_url", "https://127.0.0.1/private", "invalid_direct_url"),
        ]:
            with self.subTest(field=field):
                payload = copy.deepcopy(self.payload)
                payload["findings"][0][field] = value
                self.assertEqual(self.validate(payload), (False, error))
        self.payload["session_id"] = "other-session"
        self.assertEqual(self.validate(), (False, "result_session_mismatch"))

    def test_truncated_json_is_not_success(self):
        result, error = search.parse_result_text(
            json.dumps(self.payload)[:-8], "test-session", "x", self.since, self.until)
        self.assertIsNone(result)
        self.assertIsNotNone(error)

    def test_honest_empty_results_are_valid(self):
        self.payload["findings"] = []
        self.payload["summary"] = ["No matching evidence was found."]
        self.assertEqual(self.validate(), (True, None))

    def test_deep_prompt_discloses_previously_hidden_rules(self):
        prompt = search.build_prompt("Research phones", "x", self.since, self.until, "deep")
        for required in ["1 to 10", "1 to 20", "NONEMPTY finding_ids", "platform=x",
                         "Never relabel", "at most 50", "no URLs", "including in deep mode"]:
            with self.subTest(required=required):
                self.assertIn(required, prompt)


if __name__ == "__main__":
    unittest.main()
