#!/usr/bin/env python3
"""Verify independent skills alone and workflows with their declared dependency closure."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from install_skills import copy_skill, select_skills
from validate_repo import skill_dependencies


ROOT = Path(__file__).resolve().parents[1]


def check_tometo_cli(env: dict[str, str]) -> None:
    """Exercise the documented entry point without a pre-existing skill catalog."""
    required = {
        "tometo-mode", "architecture-selection", "footwork-tools", "pstack-investigate", "pstack-architect",
        "pstack-interrogate", "pstack-verify", "pstack-create-verification-skill",
        "pstack-maintain-verification-skill", "typescript", "react-best-practices",
        "css", "rust", "go", "zig", "kotlin", "swift", "cpp", "linux", "c-systems-programming", "wasm",
    }
    with tempfile.TemporaryDirectory(prefix=".tometo-install-", dir=ROOT) as temp:
        destination = Path(temp).resolve() / "skills"
        command = [sys.executable, str(ROOT / "scripts/install_skills.py"),
                   "--destination", str(destination), "--skill", "tometo-mode"]

        def run(arguments: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
            result = subprocess.run(arguments, cwd=cwd, env=env, text=True, capture_output=True)
            if result.returncode:
                raise RuntimeError(f"{' '.join(arguments)} failed:\n{result.stdout}{result.stderr}")
            return result

        run(command)
        if destination.exists():
            raise RuntimeError("Tometo preview mutated the destination")
        run([*command, "--apply"])
        installed = {path.name for path in destination.iterdir() if path.is_dir()}
        if missing := required - installed:
            raise RuntimeError(f"Tometo starter omitted required workflow/language skills: {sorted(missing)}")
        manifest_path = destination / ".siftable-skills.json"
        manifest = manifest_path.read_bytes()
        if set(json.loads(manifest)["skills"]) != installed:
            raise RuntimeError("Tometo installation manifest disagrees with installed packages")
        run([sys.executable, "scripts/check-routes.py"], cwd=destination / "tometo-mode")
        checker = [sys.executable, str(destination / "tometo-mode/scripts/check-routes.py"),
                   "--skills-root", str(destination)]
        for name in sorted(installed):
            checker.extend(["--skill", name])
        run(checker)
        run([sys.executable, str(ROOT / "scripts/validate_repo.py"),
             "--skills-root", str(destination)])
        run([*command, "--apply"])
        if manifest_path.read_bytes() != manifest:
            raise RuntimeError("Repeating the documented Tometo install changed its manifest")
        (destination / "wasm/SKILL.md").unlink()
        broken = subprocess.run(checker, cwd=ROOT, env=env, text=True, capture_output=True)
        if broken.returncode == 0 or "wasm/SKILL.md" not in broken.stderr:
            raise RuntimeError("Installed route checks failed to detect a missing WASM entrypoint")
    print("Tometo CLI preview, clean installation, installed routes and repeat installation passed")


def main() -> int:
    skills = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    check_tometo_cli(env)
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
