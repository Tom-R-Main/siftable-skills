#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "compare_recall.py"
FIXTURES = SKILL / "tests" / "fixtures"


class CompareRecallTests(unittest.TestCase):
    def test_reports_recall_and_shortfall(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--exact",
                str(FIXTURES / "exact-results.json"),
                "--approx",
                str(FIXTURES / "approximate-results.json"),
                "--k",
                "4",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["query_count"], 2)
        self.assertEqual(payload["mean_recall_at_k"], 0.625)
        self.assertEqual(payload["queries"][1]["result_shortfall"], 1)

    def test_rejects_mismatched_query_sets(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json") as approximate:
            json.dump({"queries": [{"query_id": "other", "ids": ["a"]}]}, approximate)
            approximate.flush()
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--exact",
                    str(FIXTURES / "exact-results.json"),
                    "--approx",
                    approximate.name,
                    "--k",
                    "4",
                ],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("query sets differ", json.loads(result.stderr)["error"])


if __name__ == "__main__":
    unittest.main()
