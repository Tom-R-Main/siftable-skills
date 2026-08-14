#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "forecast.py"


class ForecastTests(unittest.TestCase):
    def run_json(self, *args: str, payload: dict | None = None) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            if payload is not None:
                json.dump(payload, handle)
            path = handle.name
        command = [sys.executable, str(SCRIPT), *args]
        command = [path if item == "INPUT" else item for item in command]
        try:
            return subprocess.run(command, capture_output=True, text=True)
        finally:
            os.unlink(path)

    def test_preflight_refuses_probability_before_retrieval(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "preflight",
                "--requested",
                "quick",
                "--retrieval-capability",
                "yes",
                "--retrieval-completed",
                "no",
                "--isolated-contexts",
                "1",
                "--model-families",
                "1",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["forecast_ready"])

    def test_binary_score(self) -> None:
        result = self.run_json("score", "--input", "INPUT", payload={"type": "binary", "forecast": 0.8, "outcome": 1})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertAlmostEqual(json.loads(result.stdout)["score"]["brier_score"], 0.04)


if __name__ == "__main__":
    unittest.main()
