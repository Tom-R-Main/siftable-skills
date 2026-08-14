#!/usr/bin/env python3
"""Validate the portable Siftable Skills repository without third-party packages."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REQUIRED_FRONTMATTER = {"name", "description"}
PORTABILITY_PATTERNS = {
    "personal macOS home": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "personal Linux home": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "installed Codex skill path": re.compile(r"~?/\.codex/skills/|~/\.codex/skills/"),
    "installed Claude skill path": re.compile(r"~?/\.claude/skills/|~/\.claude/skills/"),
    "private project name": re.compile(r"execufunction", re.IGNORECASE),
}
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
RELATIVE_RESOURCE = re.compile(r"(?<![A-Za-z0-9_./-])((?:scripts|references|assets|tests)/[A-Za-z0-9_.@/+:-]+)")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening YAML frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("missing closing YAML frontmatter delimiter") from exc
    data: dict[str, str] = {}
    index = 1
    while index < end:
        line = lines[index]
        if not line or line[0].isspace() or ":" not in line:
            index += 1
            continue
        key, raw = line.split(":", 1)
        key, raw = key.strip(), raw.strip()
        if raw in {">", ">-", "|", "|-"}:
            chunks: list[str] = []
            index += 1
            while index < end and (not lines[index] or lines[index][0].isspace()):
                chunks.append(lines[index].strip())
                index += 1
            data[key] = " ".join(chunk for chunk in chunks if chunk)
            continue
        data[key] = raw.strip('"\'')
        index += 1
    return data


def script_command(path: Path) -> list[str]:
    if path.suffix == ".py":
        return [sys.executable, str(path), "--help"]
    if path.suffix == ".sh":
        return ["bash", str(path), "--help"]
    return [str(path), "--help"]


def validate_skill(skill: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill / "SKILL.md"
    if not skill_file.is_file():
        return [f"{skill.relative_to(ROOT)}: missing SKILL.md"]
    try:
        frontmatter = parse_frontmatter(skill_file)
    except ValueError as exc:
        return [f"{skill_file.relative_to(ROOT)}: {exc}"]
    missing = REQUIRED_FRONTMATTER - frontmatter.keys()
    if missing:
        errors.append(f"{skill_file.relative_to(ROOT)}: missing frontmatter fields {sorted(missing)}")
    if frontmatter.get("name") != skill.name:
        errors.append(f"{skill_file.relative_to(ROOT)}: name must match directory basename")
    description = frontmatter.get("description", "")
    if len(description) < 40 or "use" not in description.lower():
        errors.append(f"{skill_file.relative_to(ROOT)}: description must explain capability and when to use it")
    extra = set(frontmatter) - REQUIRED_FRONTMATTER
    if extra:
        errors.append(f"{skill_file.relative_to(ROOT)}: unsupported frontmatter fields {sorted(extra)}")

    for path in sorted(skill.rglob("*")):
        if path.is_symlink():
            errors.append(f"{path.relative_to(ROOT)}: symlinks are not allowed")
            continue
        if not path.is_file() or path.name == ".DS_Store":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PORTABILITY_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path.relative_to(ROOT)}: contains {label}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{path.relative_to(ROOT)}: contains possible {label}")
        if path.suffix in {".md", ".yaml", ".yml"}:
            for match in RELATIVE_RESOURCE.finditer(text):
                target = skill / match.group(1).rstrip(".,;:)")
                if not target.exists():
                    errors.append(f"{path.relative_to(ROOT)}: unresolved resource {match.group(1)}")

    scripts = skill / "scripts"
    if scripts.is_dir():
        for path in sorted(scripts.iterdir()):
            if not path.is_file() or path.suffix not in {".py", ".sh"}:
                continue
            try:
                result = subprocess.run(script_command(path), cwd=skill, capture_output=True, text=True, timeout=15)
            except (OSError, subprocess.TimeoutExpired) as exc:
                errors.append(f"{path.relative_to(ROOT)}: --help failed: {exc}")
                continue
            if result.returncode != 0 or "usage" not in (result.stdout + result.stderr).lower():
                errors.append(f"{path.relative_to(ROOT)}: must support --help with exit code 0")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    if not SKILLS.is_dir():
        print("skills directory is missing", file=sys.stderr)
        return 1
    errors: list[str] = []
    skill_dirs = sorted(path for path in SKILLS.iterdir() if path.is_dir() and not path.name.startswith("."))
    if not skill_dirs:
        errors.append("no skills found")
    for skill in skill_dirs:
        errors.extend(validate_skill(skill))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"validated {len(skill_dirs)} self-contained skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
