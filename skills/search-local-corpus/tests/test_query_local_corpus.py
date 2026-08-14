#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
WRAPPER = SKILL / "scripts" / "query_local_corpus.py"
BACKEND = SKILL / "tests" / "synthetic_backend.py"


class QueryLocalCorpusTests(unittest.TestCase):
    def run_wrapper(self, *args: str, command: str | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.pop("LOCAL_CORPUS_COMMAND", None)
        if command is not None:
            env["LOCAL_CORPUS_COMMAND"] = command
        return subprocess.run([sys.executable, str(WRAPPER), *args], capture_output=True, text=True, env=env)

    def test_missing_backend_fails_cleanly(self) -> None:
        result = self.run_wrapper("--query", "classification")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not configured", json.loads(result.stderr)["error"])

    def test_synthetic_backend_and_collection(self) -> None:
        result = self.run_wrapper(
            "--query",
            "safe candidate evidence",
            "--collection",
            "engineering-notes",
            "--limit",
            "1",
            command=f"{sys.executable} {BACKEND}",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["source"], "filesystem-notes.md")
        self.assertTrue(payload["results"][0]["locator"])

    def test_malformed_backend_is_rejected(self) -> None:
        result = self.run_wrapper(
            "--query",
            "anything",
            command=f"{sys.executable} -c 'print(\"not-json\")'",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", json.loads(result.stderr)["error"])


if __name__ == "__main__":
    unittest.main()
