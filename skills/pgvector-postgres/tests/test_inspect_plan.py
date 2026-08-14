#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "inspect_plan.py"
PLAN = SKILL / "tests" / "fixtures" / "plan.json"


class InspectPlanTests(unittest.TestCase):
    def test_summarizes_index_and_filter_evidence(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(PLAN)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["top_node_type"], "Limit")
        self.assertEqual(payload["node_count"], 2)
        self.assertEqual(payload["index_names"], ["items_embedding_hnsw_idx"])
        self.assertTrue(payload["flags"]["uses_index"])
        self.assertTrue(payload["flags"]["has_filter"])
        self.assertFalse(payload["flags"]["uses_sequential_scan"])

    def test_rejects_non_plan_json(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json") as handle:
            json.dump({"not_plan": True}, handle)
            handle.flush()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", handle.name],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("top-level Plan", json.loads(result.stderr)["error"])


if __name__ == "__main__":
    unittest.main()
