#!/usr/bin/env python3
"""Validate the portable Siftable Skills repository without third-party packages."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REQUIRED_FRONTMATTER = {"name", "description"}
OPTIONAL_FRONTMATTER = {"metadata", "license", "compatibility", "allowed-tools"}
PORTABILITY_PATTERNS = {
    "personal macOS home": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "personal Linux home": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "personal Windows home": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\", re.IGNORECASE),
    "named external volume": re.compile(r"(?<![A-Za-z0-9_/])/Volumes/[^/\n]+/"),
    "installed Codex skill path": re.compile(r"~?/\.codex/skills/|~/\.codex/skills/"),
    "installed Claude skill path": re.compile(r"~?/\.claude/skills/|~/\.claude/skills/"),
    "private project name": re.compile(r"execufunction", re.IGNORECASE),
    "excluded personal workflow": re.compile(
        r"\b(?:flirt|dating-decisions|dating-profile|dating-wingman|relationship-conversations|conversation-coach)\b",
        re.IGNORECASE,
    ),
}
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
RELATIVE_RESOURCE = re.compile(r"(?<![A-Za-z0-9_./-])((?:scripts|references|assets|tests)/[A-Za-z0-9_.@/+:-]+)")
SIBLING_RESOURCE = re.compile(r"(?<![A-Za-z0-9_./-])(\.\./[A-Za-z0-9_.@/+:-]+)")
MARKDOWN_LINK = re.compile(r"!?\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)")
FENCED_BLOCK = re.compile(r"(?ms)^[ \t]*(`{3,}|~{3,})[^\n]*\n.*?^[ \t]*\1[ \t]*$")
ICON_RESOURCE = re.compile(r"(?m)^\s*icon_(?:small|large)\s*:\s*[\"']?([^\s\"'#]+)")
HELP_CONTRACTS = {
    "filesystem-lifecycle/scripts/fs_lifecycle.py", "human-writing/scripts/postprocess_output.py",
    "pgvector-postgres/scripts/compare_recall.py", "pgvector-postgres/scripts/inspect_plan.py",
    "predict-future/scripts/forecast.py", "rust/scripts/rust-gates.sh",
    "search-local-corpus/scripts/query_local_corpus.py", "strategic-decision-mapping/scripts/analyze_game.py",
    "typescript/scripts/drive.sh", "typescript/scripts/ts-gates.sh", "zig/scripts/zig-gates.sh",
    "screenshot/scripts/take_screenshot.py",
}
IGNORED = {"__pycache__", ".DS_Store", ".pytest_cache"}


def label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resource_references(path: Path, skill: Path) -> list[tuple[str, Path]]:
    """Markdown links are document-relative; bundled code paths use the skill root.

    Explicit sibling paths are document-relative in both prose and code. URLs,
    fragment-only links, absolute examples and interpolated templates are omitted.
    """
    text = path.read_text(encoding="utf-8")
    resources: dict[str, Path] = {}
    if path.suffix in {".yaml", ".yml"}:
        for match in ICON_RESOURCE.finditer(text):
            raw = match.group(1)
            if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", raw):
                resources[raw] = skill / raw
    prose = FENCED_BLOCK.sub("", text)
    links = list(MARKDOWN_LINK.finditer(prose))
    for match in links:
        raw = match.group(1).strip("<>")
        if raw.startswith(("#", "/", "~", "$")) or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", raw):
            continue
        raw = unquote(raw.split("#", 1)[0].split("?", 1)[0])
        if raw and not any(char in raw for char in "${}*<>"):
            resources[raw] = path.parent / raw
    # Do not reinterpret a link's nested path as a root-relative code reference.
    code_text = MARKDOWN_LINK.sub("", text)
    for pattern, base in ((RELATIVE_RESOURCE, skill), (SIBLING_RESOURCE, path.parent)):
        for match in pattern.finditer(code_text):
            raw = match.group(1).rstrip(".,;:)")
            if raw.startswith("tests/"):
                # Test layouts and Terraform examples normally belong to the target
                # project. Explicit links and prose code references to test files
                # declare bundled resources; fenced project examples do not.
                if not Path(raw).suffix or f"`{raw}`" not in prose:
                    continue
            if pattern is SIBLING_RESOURCE and not (Path(raw).suffix or raw.endswith("SKILL.md")):
                continue  # Project import examples such as ../../components/X.
            resources[raw] = base / raw
    return list(resources.items())


def skill_dependencies(skill: Path, skills_root: Path) -> set[str]:
    dependencies: set[str] = set()
    for path in sorted(skill.rglob("*")):
        if path.suffix not in {".md", ".yaml", ".yml"} or not path.is_file() or path.is_symlink():
            continue
        for raw, target in resource_references(path, skill):
            try:
                relative = target.resolve().relative_to(skills_root.resolve())
            except ValueError:
                raise ValueError(f"{label(path)}: resource escapes skills tree: {raw}")
            if relative.parts and relative.parts[0] != skill.name:
                dependencies.add(relative.parts[0])
    return dependencies


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
        if key in data:
            raise ValueError(f"duplicate top-level frontmatter field: {key}")
        if key in {"name", "description", "license", "compatibility"} and raw not in {">", ">-", "|", "|-"}:
            if not raw.startswith(('"', "'")) and re.search(r":(?:\s|$)", raw):
                raise ValueError(f"{key}: quote a scalar containing a colon followed by whitespace")
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


def validate_skill(skill: Path, *, run_help: bool = False) -> list[str]:
    errors: list[str] = []
    skill_file = skill / "SKILL.md"
    if not skill_file.is_file():
        return [f"{label(skill)}: missing SKILL.md"]
    try:
        frontmatter = parse_frontmatter(skill_file)
    except ValueError as exc:
        return [f"{label(skill_file)}: {exc}"]
    missing = REQUIRED_FRONTMATTER - frontmatter.keys()
    if missing:
        errors.append(f"{label(skill_file)}: missing frontmatter fields {sorted(missing)}")
    if frontmatter.get("name") != skill.name:
        errors.append(f"{label(skill_file)}: name must match directory basename")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill.name) or len(skill.name) > 64:
        errors.append(f"{label(skill_file)}: name must be 1-64 lowercase letters, digits and single hyphens")
    description = frontmatter.get("description", "")
    if len(description) < 40:
        errors.append(f"{label(skill_file)}: description must substantively explain the skill capability")
    extra = set(frontmatter) - REQUIRED_FRONTMATTER - OPTIONAL_FRONTMATTER
    if extra:
        errors.append(f"{label(skill_file)}: unsupported frontmatter fields {sorted(extra)}")

    for path in sorted(skill.rglob("*")):
        if path.is_symlink():
            errors.append(f"{label(path)}: symlinks are not allowed")
            continue
        if not path.is_file() or any(part in IGNORED for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern_label, pattern in PORTABILITY_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label(path)}: contains {pattern_label}")
        for pattern_label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label(path)}: contains possible {pattern_label}")
        if path.suffix in {".md", ".yaml", ".yml"}:
            for raw, target in resource_references(path, skill):
                try:
                    target.resolve().relative_to(skill.parent.resolve())
                except ValueError:
                    errors.append(f"{label(path)}: resource escapes skills tree: {raw}")
                if not target.exists():
                    errors.append(f"{label(path)}: unresolved resource {raw}")

    scripts = skill / "scripts"
    if run_help and scripts.is_dir():
        for path in sorted(scripts.iterdir()):
            if not path.is_file() or path.suffix not in {".py", ".sh"}:
                continue
            if f"{skill.name}/scripts/{path.name}" not in HELP_CONTRACTS:
                continue
            try:
                result = subprocess.run(script_command(path), cwd=skill, capture_output=True, text=True, timeout=15)
            except (OSError, subprocess.TimeoutExpired) as exc:
                errors.append(f"{label(path)}: --help failed: {exc}")
                continue
            if result.returncode != 0 or "usage" not in (result.stdout + result.stderr).lower():
                errors.append(f"{label(path)}: must support --help with exit code 0")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, default=SKILLS, help="validate a source or installed skills tree")
    parser.add_argument("--script-help", action="store_true", help="exercise only the existing allowlisted --help contracts")
    args = parser.parse_args()
    if not args.skills_root.is_dir():
        print("skills directory is missing", file=sys.stderr)
        return 1
    errors: list[str] = []
    skill_dirs = sorted(path for path in args.skills_root.iterdir() if path.is_dir() and not path.name.startswith("."))
    if not skill_dirs:
        errors.append("no skills found")
    for skill in skill_dirs:
        if skill.is_symlink():
            errors.append(f"{label(skill)}: symlinks are not allowed")
        else:
            errors.extend(validate_skill(skill, run_help=args.script_help))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"validated {len(skill_dirs)} skills and their declared resources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
