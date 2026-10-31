#!/usr/bin/env python3
r"""Read-only checks for explicitly selected installed skill directories.

By default, inspect this script's tometo-mode installation and its two pstack
verification-authoring siblings. Repeat --skills-root to check host adapters,
--skill to replace the default selection, and --shared-file to compare explicitly
shared assets. Dependency links are checked for existence, never crawled.

From an installed tometo-mode directory:
  python3 scripts/check-routes.py
  python3 scripts/check-routes.py --skills-root /path/to/first/skills \
    --skills-root /path/to/second/skills \
    --shared-file tometo-mode/references/catch-up.md
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


DEFAULT_SKILLS = (
    "tometo-mode",
    "pstack-create-verification-skill",
    "pstack-maintain-verification-skill",
)
SKIP_DIRS = {".git", "node_modules", "build", "dist", "__pycache__", ".venv", "data"}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
INLINE_LINK = re.compile(r"\[[^\]\n]*\]\(\s*(<[^>\n]*>|(?:\\.|[^()\s]|\([^()\n]*\))+)\s*(?:[\"'][^\n]*[\"']\s*)?\)")
REFERENCE_LINK = re.compile(r"^ {0,3}\[[^\]\n]+\]:\s*(<[^>\n]*>|\S+)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def inside(path: Path, directory: Path) -> bool:
    return path == directory or directory in path.parents


def sensitive(path: Path) -> bool:
    return path.name.startswith(".env") or path.suffix.lower() in {".pem", ".p12", ".key"}


def local_links(source: str):
    """Yield (line, relative destination), excluding fences and inline code."""
    fence_char, fence_length = "", 0
    for number, line in enumerate(source.splitlines(), 1):
        match = FENCE.match(line)
        if fence_char:
            if match and match[1][0] == fence_char and len(match[1]) >= fence_length and not match[2].strip():
                fence_char, fence_length = "", 0
            continue
        if match:
            fence_char, fence_length = match[1][0], len(match[1])
            continue
        line = re.sub(r"(`+).*?\1", "", line)
        destinations = [match[1] for match in INLINE_LINK.finditer(line)]
        reference = REFERENCE_LINK.match(line)
        if reference:
            destinations.append(reference[1])
        for destination in destinations:
            destination = re.sub(r"\\(.)", r"\1", destination.strip("<>"))
            if not destination or destination.startswith(("#", "/", "//")) or SCHEME.match(destination):
                continue
            # A query or fragment changes the view, not the file being linked.
            path = unquote(urlsplit(destination).path)
            if path:
                yield number, path


def frontmatter_name(source: str) -> str | None:
    lines = source.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None
    names = []
    for line in lines[1:end]:
        match = re.match(r"^name\s*:\s*(.*?)\s*$", line)
        if not match:
            continue
        value = match[1]
        if value.startswith('"'):
            try:
                value, _ = json.JSONDecoder().raw_decode(value)
            except (ValueError, TypeError):
                return None
        elif value.startswith("'"):
            match = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", value)
            if not match:
                return None
            value = match[1].replace("''", "'")
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        names.append(value)
    return names[0] if len(names) == 1 and isinstance(names[0], str) else None


class Check:
    def __init__(self):
        self.errors: set[str] = set()
        self.skills = self.documents = self.links = self.shared = 0

    def error(self, path: Path, message: str):
        self.errors.add(f"{path}: {message}")

    def resolve(self, path: Path) -> Path | None:
        try:
            return path.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            self.error(path, f"missing target or dangling/cyclic symlink ({type(error).__name__})")
            return None

    def skill(self, folder: Path):
        resolved = self.resolve(folder)
        if resolved is None:
            return
        if not resolved.is_dir():
            self.error(folder, "selected skill is not a directory")
            return
        self.skills += 1
        documents = []
        edges: dict[Path, set[Path]] = {}
        directory_links = []
        pending = [folder]
        while pending:
            directory = pending.pop()
            real_directory = directory.resolve()
            try:
                entries = sorted(directory.iterdir())
            except OSError as error:
                self.error(directory, f"cannot inspect directory ({type(error).__name__})")
                continue
            for entry in entries:
                if entry.is_symlink():
                    target = self.resolve(entry)
                    if target is None:
                        continue
                    if target.is_dir():
                        # Check the link itself, but do not follow a linked directory.
                        directory_links.append((entry, real_directory, target))
                        if inside(target, resolved):
                            edges.setdefault(real_directory, set()).add(target)
                    elif target.is_file() and entry.suffix.lower() == ".md" and not sensitive(entry):
                        if sensitive(target):
                            self.error(entry, "refusing to read a secret-like Markdown target")
                        else:
                            documents.append(entry)
                elif entry.is_dir() and entry.name not in SKIP_DIRS and not sensitive(entry):
                    edges.setdefault(real_directory, set()).add(entry.resolve())
                    pending.append(entry)
                elif entry.is_file() and entry.suffix.lower() == ".md" and not sensitive(entry):
                    documents.append(entry)
        for link, origin, target in directory_links:
            reached, pending_targets = set(), [target]
            while pending_targets:
                node = pending_targets.pop()
                if node in reached:
                    continue
                reached.add(node)
                pending_targets.extend(edges.get(node, ()))
            if inside(origin, target) or origin in reached:
                self.error(link, "cyclic directory symlink")
        skill_file = folder / "SKILL.md"
        if skill_file not in documents:
            self.error(skill_file, "missing root SKILL.md")
        for document in sorted(documents):
            try:
                source = document.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                self.error(document, f"cannot read Markdown ({type(error).__name__})")
                continue
            self.documents += 1
            if document == skill_file:
                name = frontmatter_name(source)
                if name != folder.name:
                    self.error(document, f"frontmatter name must equal {folder.name!r}; found {name!r}")
            for line, destination in local_links(source):
                self.links += 1
                self.resolve(document.parent / destination)

    def compare(self, roots: list[Path], relative: Path):
        if sensitive(relative):
            self.error(relative, "refusing to read a secret-like shared file")
            return
        contents = []
        for root in roots:
            path = root / relative
            resolved = self.resolve(path)
            if resolved is None:
                continue
            if sensitive(resolved):
                self.error(path, "refusing to read a secret-like shared target")
                continue
            if not resolved.is_file():
                self.error(path, "shared asset is not a file")
                continue
            try:
                contents.append((path, path.read_bytes()))
            except OSError as error:
                self.error(path, f"cannot read shared asset ({type(error).__name__})")
        if len(contents) == len(roots) and len(roots) > 1:
            self.shared += 1
            if any(content != contents[0][1] for _, content in contents[1:]):
                self.error(relative, "shared asset differs across selected skills roots")


def relative_argument(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise argparse.ArgumentTypeError("must be a relative path without '..'")
    return path


def skill_argument(value: str) -> str:
    path = relative_argument(value)
    if len(path.parts) != 1 or value in {".", ".."}:
        raise argparse.ArgumentTypeError("must be one skill directory name")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skills-root", action="append", type=Path, help="installed skills root; repeat for multiple hosts")
    parser.add_argument("--skill", action="append", type=skill_argument, help="skill directory to inspect; replaces default selection")
    parser.add_argument("--shared-file", action="append", type=relative_argument, default=[], help="relative asset to compare byte-for-byte across roots")
    arguments = parser.parse_args(argv)
    default_root = Path(os.path.abspath(__file__)).parents[2]
    roots = sorted(set(path.expanduser().absolute() for path in (arguments.skills_root or [default_root])))
    skills = sorted(set(arguments.skill or DEFAULT_SKILLS))
    check = Check()
    for root in roots:
        for skill in skills:
            check.skill(root / skill)
    for relative in sorted(set(arguments.shared_file)):
        check.compare(roots, relative)
    if check.errors:
        for error in sorted(check.errors):
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL: {len(check.errors)} error(s)", file=sys.stderr)
        return 1
    print(f"OK: {check.skills} skills, {check.documents} Markdown files, {check.links} local links; {check.shared} shared files compared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
