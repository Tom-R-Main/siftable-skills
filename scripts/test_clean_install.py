#!/usr/bin/env python3
"""Verify each skill as the only package in a fresh installation tree."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    skills = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for source in skills:
        with tempfile.TemporaryDirectory(prefix=f"siftable-skill-{source.name}-") as temp:
            install_root = Path(temp)
            installed_skills = install_root / "skills"
            installed_skills.mkdir()
            shutil.copytree(source, installed_skills / source.name)
            scripts = install_root / "scripts"
            scripts.mkdir()
            shutil.copy2(ROOT / "scripts" / "validate_repo.py", scripts / "validate_repo.py")
            found = [path.name for path in installed_skills.iterdir() if path.is_dir()]
            if found != [source.name]:
                raise RuntimeError(f"clean install selected unexpected skills: {found}")
            subprocess.run(
                [sys.executable, str(scripts / "validate_repo.py")],
                cwd=install_root,
                check=True,
                env=env,
            )
    print(f"clean-installed and validated {len(skills)} skills independently")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
