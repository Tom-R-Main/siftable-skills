#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "postprocess_output.py"
SPEC = importlib.util.spec_from_file_location("postprocess_output", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PostprocessOutputTests(unittest.TestCase):
    def test_removes_invisible_carriers_and_normalizes_spaces(self) -> None:
        cleaned, stats = MODULE.clean_text("one\u200btwo\u00a0three")
        self.assertEqual(cleaned, "onetwo three")
        self.assertEqual(stats["removed_count"], 1)
        self.assertEqual(stats["replaced_count"], 1)

    def test_cli_stdin_stdout(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-", "--stats"],
            input="hello\u00ad world",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "hello world")
        self.assertIn('"removed_count": 1', result.stderr)


if __name__ == "__main__":
    unittest.main()
