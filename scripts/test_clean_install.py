#!/usr/bin/env python3
"""Verify independent skills alone and workflows with their declared dependency closure."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from install_skills import copy_skill, select_skills
from validate_repo import skill_dependencies


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    skills = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    independent = 0
    for source in skills:
        closure = select_skills(ROOT / "skills", [source.name])
        if not skill_dependencies(source, ROOT / "skills"):
            if closure != [source.name]:
                raise RuntimeError(f"independent skill unexpectedly depends on others: {source.name}")
            independent += 1
        with tempfile.TemporaryDirectory(prefix=f"siftable-skill-{source.name}-") as temp:
            install_root = Path(temp)
            installed_skills = install_root / "skills"
            installed_skills.mkdir()
            for name in closure:
                copy_skill(ROOT / "skills" / name, installed_skills / name)
            scripts = install_root / "scripts"
            scripts.mkdir()
            shutil.copy2(ROOT / "scripts" / "validate_repo.py", scripts / "validate_repo.py")
            found = sorted(path.name for path in installed_skills.iterdir() if path.is_dir())
            if found != closure:
                raise RuntimeError(f"clean install selected unexpected skills: {found}")
            subprocess.run(
                [sys.executable, str(scripts / "validate_repo.py")],
                cwd=install_root,
                check=True,
                env=env,
            )
    print(f"clean-installed and validated {len(skills)} skill selections ({independent} independent, "
          f"{len(skills) - independent} with sibling dependencies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
