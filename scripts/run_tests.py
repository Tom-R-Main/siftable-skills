#!/usr/bin/env python3
"""Run every deterministic skill test and required smoke test."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(argv: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(argv))
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(argv, cwd=cwd or ROOT, check=True, env=env)


def main() -> int:
    run([sys.executable, "scripts/validate_repo.py", "--script-help"])
    root_tests = sorted((ROOT / "scripts").glob("test_*.py"))
    for test in root_tests:
        run([sys.executable, str(test)])
    tests = sorted((ROOT / "skills").glob("*/tests/test_*.py"))
    for test in tests:
        run([sys.executable, str(test)])
    run([sys.executable, "scripts/fs_lifecycle.py", "self-test"], ROOT / "skills/filesystem-lifecycle")
    run(["bash", "-n", "scripts/ts-gates.sh", "scripts/drive.sh"], ROOT / "skills/typescript")
    print(f"passed {len(root_tests) + len(tests)} test files, static resource validation, "
          "existing script help contracts and 2 smoke-test groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
