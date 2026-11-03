#!/usr/bin/env python3
"""Run the feedback backend using this installation's optional Python runtime."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    skill = Path(__file__).resolve().parents[1]
    selected = os.environ.get("UX_PERSONAS_PYTHON")
    configuration = skill.parent / ".ux-personas-runtime.json"
    try:
        if selected is None and configuration.exists():
            value = json.loads(configuration.read_text(encoding="utf-8"))
            selected = value["python"]
        selected = selected if selected is not None else sys.executable
        if not isinstance(selected, str) or not selected.strip():
            raise ValueError("runtime interpreter must be a nonempty path")
        result = subprocess.run([selected, str(skill / "scripts/tinytroupe_backend.py"),
                                 *sys.argv[1:]], check=False)
        return result.returncode
    except (OSError, ValueError, TypeError, KeyError):
        print("Feedback runtime unavailable; configure UX_PERSONAS_PYTHON or the skill root's .ux-personas-runtime.json python path.",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
