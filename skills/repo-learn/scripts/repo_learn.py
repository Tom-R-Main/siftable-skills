#!/usr/bin/env python3
"""Local evidence and pattern library. Never executes code from a source repo."""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time

VERSION = "1.1.0"
MAX_FILE_BYTES = 1024 * 1024
MAX_LINES = 160
MAX_CHARS = 24000
MAX_FILES = 100000
EXCLUDED_DIRS = {".git", ".hg", ".svn", "node_modules", "build", "dist", "out",
                 "target", "__pycache__", ".venv", "venv", "data", ".next",
                 ".gitnexus", ".cache", "coverage"}
EXCLUDED_SUFFIXES = {".pem", ".p12", ".pfx", ".key", ".keystore", ".jks"}
TEXT_SUFFIXES = {".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
                 ".mts", ".cts", ".java", ".kt", ".kts", ".c", ".h", ".cc",
                 ".cpp", ".hpp", ".cs", ".go", ".rs", ".rb", ".php", ".swift",
                 ".scala", ".clj", ".ex", ".exs", ".erl", ".hs", ".lua", ".pl",
                 ".r", ".R", ".jl", ".dart", ".zig", ".m", ".mm", ".sh",
                 ".bash", ".zsh", ".fish", ".ps1", ".sql", ".proto", ".graphql",
                 ".gql", ".vue", ".svelte", ".html", ".css", ".scss", ".less",
                 ".md", ".mdx", ".rst", ".txt", ".toml", ".yaml", ".yml",
                 ".json", ".jsonc", ".xml", ".ini", ".cfg", ".gradle", ".cmake"}
MANIFESTS = {"package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml",
             "build.gradle", "build.gradle.kts", "CMakeLists.txt", "Makefile",
             "requirements.txt", "Gemfile", "composer.json", "AGENTS.md", "SKILL.md"}


class UserError(Exception):
    pass


class ProjectionError(UserError):
    def __init__(self, identity, cause):
        super().__init__(f"Pattern committed but JSON projection failed: {cause}")
        self.details = {"canonical_committed": True, "pattern_id": identity,
                        "projection_written": False,
                        "recovery": "Retry the identical card under the same ID."}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def bounded_int(value, low, high, label):
    if value < low or value > high:
        raise UserError(f"{label} must be between {low} and {high}")
    return value


def allowed_path(relative):
    p = Path(relative)
    if p.is_absolute() or not p.parts or any(x in {"..", "."} for x in p.parts):
        return False
    if any(x in EXCLUDED_DIRS for x in p.parts):
        return False
    if any(x.lower().startswith(".env") or x.lower() in
           {".ssh", ".aws", ".gnupg", "credentials", "secrets"} for x in p.parts):
        return False
    name = p.name.lower()
    if name.startswith(".env") or p.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if any(word in name for word in ("credential", "secret", "private_key", "private-key")):
        return False
    if name in {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", ".netrc", ".npmrc",
                ".pypirc", "auth.json", "token.json", "tokens.json"}:
        return False
    return (p.suffix in TEXT_SUFFIXES or p.suffix.lower() in TEXT_SUFFIXES or
            p.name in MANIFESTS or name.startswith(("readme", "license", "copying")) or
            name in {"dockerfile", "containerfile", "makefile", "gemfile", "go.mod"})


def root_path(value, store=None):
    candidate = Path(value).expanduser().absolute()
    if candidate.is_symlink():
        raise UserError("Source root cannot be a symlink")
    if not candidate.is_dir():
        raise UserError(f"Source directory unavailable: {candidate}")
    root = candidate.resolve()
    if store is not None and (store == root or root in store.parents):
        raise UserError("Store must be outside the source repository")
    return root


def open_source(root, relative):
    """Walk via directory descriptors, refusing symlinks in every component."""
    relative = str(relative)
    if not allowed_path(relative):
        raise UserError("Path excluded by source policy or not a supported text file")
    parts = Path(relative).parts
    descriptor = os.open(str(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                          dir_fd=descriptor)
            os.close(descriptor)
            descriptor = new
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=descriptor)
    finally:
        os.close(descriptor)
    return fd


def source_bytes(root, relative):
    fd = open_source(root, relative)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise UserError("Only regular source files may be read")
        if info.st_size > MAX_FILE_BYTES:
            raise UserError("Source file exceeds 1 MiB limit")
        data = stream.read(MAX_FILE_BYTES + 1)
        after = os.fstat(stream.fileno())
    if len(data) > MAX_FILE_BYTES:
        raise UserError("Source file exceeds 1 MiB limit")
    if (info.st_size, info.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise UserError("Source changed during read; retry")
    if b"\x00" in data:
        raise UserError("Binary source files are excluded")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UserError("Source is not UTF-8 text") from exc
    return data


def git_result(root, arguments):
    if not shutil.which("git"):
        return None
    environment = os.environ.copy()
    environment.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    # Explicit roots must not be redirected by ambient repository selectors.
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        environment.pop(key, None)
    base = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
            "-c", "core.hooksPath=/dev/null", "-C", str(root)]
    try:
        overrides = []
        if arguments and arguments[0] == "status":
            # Status can hash dirty files through arbitrary configured clean or
            # process filters. Read ONLY driver key names, never their values,
            # and disable each driver before asking Git for dirty metadata.
            config = subprocess.run(base + ["config", "--name-only", "--get-regexp",
                                           r"^filter\..*\.(clean|process|required)$"],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    timeout=15, env=environment, check=False)
            if config.returncode not in (0, 1):
                return None
            prefixes = set()
            for key in config.stdout.decode("utf-8").splitlines():
                if not re.fullmatch(r"filter\.[^\x00-\x1f]+\.(clean|process|required)", key):
                    return None  # Unknown configuration shape: do not run it.
                prefixes.add(key.rsplit(".", 1)[0])
            for prefix in sorted(prefixes):
                overrides += ["-c", prefix + ".clean=", "-c", prefix + ".process=",
                              "-c", prefix + ".required=false"]
        result = subprocess.run(base + overrides + arguments,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=15, env=environment, check=False)
        return result.stdout if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError):
        return None


def repo_metadata(root, dirty=True):
    head = git_result(root, ["rev-parse", "--verify", "HEAD"])
    result = {"name": root.name, "repo_root": str(root),
              "head": head.decode().strip() if head else None,
              "git_metadata_available": head is not None}
    if dirty:
        status = git_result(root, ["status", "--porcelain=v1", "-z", "--untracked-files=normal",
                                   "--ignore-submodules=all"])
        result["dirty"] = bool(status) if status is not None else None
        result["dirty_status_available"] = status is not None
        result["dirty_scope"] = "Git status with hooks/fsmonitor/filters disabled; submodule contents ignored"
    return result


def inventory(root):
    """Metadata only. No claims of exhaustive text or semantic coverage."""
    files, skipped, errors = [], {}, []
    partial = False

    def skip(reason):
        skipped[reason] = skipped.get(reason, 0) + 1

    def walk_error(exc):
        errors.append(type(exc).__name__)

    for directory, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        retained = []
        for name in sorted(dirs):
            full = Path(directory) / name
            if name in EXCLUDED_DIRS:
                skip("excluded_directory")
            elif full.is_symlink():
                skip("symlink")
            else:
                retained.append(name)
        dirs[:] = retained
        for name in sorted(names):
            full = Path(directory) / name
            rel = full.relative_to(root).as_posix()
            try:
                info = full.lstat()
                if stat.S_ISLNK(info.st_mode):
                    skip("symlink")
                elif not stat.S_ISREG(info.st_mode):
                    skip("not_regular")
                elif not allowed_path(rel):
                    skip("excluded_or_unsupported_path")
                elif info.st_size > MAX_FILE_BYTES:
                    skip("oversized")
                else:
                    files.append({"path": rel, "bytes": info.st_size})
            except OSError:
                skip("unavailable")
                partial = True
            if len(files) >= MAX_FILES:
                partial = True
                break
        if len(files) >= MAX_FILES:
            break
    return files, {"eligible_files": len(files), "excluded_counts": skipped,
                   "partial": partial or bool(errors), "walk_errors": errors,
                   "inventory_limit": MAX_FILES,
                   "policy": "allowlisted text paths; symlinks, sensitive names, generated dirs and >1MiB excluded",
                   "coverage": "filesystem path metadata; not semantic coverage; gitignore not applied; text validated on read",
                   "secret_detection": "filename exclusions only, not comprehensive content secret detection"}


class Store:
    def __init__(self, value):
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise UserError("Store must be an absolute path")
        if path.is_symlink():
            raise UserError("Store directory must not be a symlink")
        path.mkdir(parents=True, exist_ok=True)
        self.path = path.resolve()
        for name in ("library.sqlite3", "library.sqlite3-journal", "library.sqlite3-wal",
                     "library.sqlite3-shm", "catalogs", "evidence", "patterns", "patterns.md"):
            if (self.path / name).is_symlink():
                raise UserError(f"Managed store path must not be a symlink: {name}")
        self.db = sqlite3.connect(self.path / "library.sqlite3", timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS patterns(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS catalogs(root TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS journal(id INTEGER PRIMARY KEY, at TEXT NOT NULL,
          action TEXT NOT NULL, body TEXT NOT NULL);
        CREATE VIRTUAL TABLE IF NOT EXISTS pattern_fts USING fts5(id UNINDEXED, text);
        """)
        with self.db:
            if self.db.execute("PRAGMA user_version").fetchone()[0] < 2:
                self.db.execute("DELETE FROM pattern_fts")
                for row in self.db.execute("SELECT id,body FROM patterns").fetchall():
                    self.db.execute("INSERT INTO pattern_fts(id,text) VALUES(?,?)",
                                    (row["id"], card_search_text(json.loads(row["body"]))))
                self.db.execute("PRAGMA user_version=2")

    def close(self):
        self.db.close()

    def log(self, action, body):
        self.db.execute("INSERT INTO journal(at, action, body) VALUES(?,?,?)",
                        (now(), action, json_text(body)))

    def atomic_json(self, folder, name, value):
        destination = self.path / folder
        if destination.is_symlink():
            raise UserError("Managed store directories must not be symlinks")
        destination.mkdir(parents=True, exist_ok=True)
        atomic_text(destination / (name + ".json"), json_text(value) + "\n")


def atomic_text(path, content):
    if path.is_symlink() or path.parent.is_symlink():
        raise UserError("Managed store paths must not be symlinks")
    fd, temp = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def freshness(item):
    root = Path(item["repo_root"])
    result = {"id": item["id"], "repo_root": str(root), "path": item["path"],
              "captured_head": item["head"], "captured_file_sha256": item["file_sha256"]}
    if not root.is_dir():
        return {**result, "status": "unavailable", "reason": "repository unavailable or offline"}
    if root.is_symlink():
        return {**result, "status": "unavailable", "reason": "repository root became a symlink"}
    try:
        data = source_bytes(root, item["path"])
    except FileNotFoundError:
        return {**result, "status": "missing", "reason": "source file missing"}
    except (OSError, UserError) as exc:
        return {**result, "status": "unavailable", "reason": str(exc)}
    sha = digest(data)
    current = repo_metadata(root, dirty=False)["head"]
    state = ("stale" if sha != item["file_sha256"] else
             "revision-advanced" if current is not None and current != item["head"] else "fresh")
    return {**result, "status": state, "current_head": current, "current_file_sha256": sha,
            "revision_check_available": current is not None,
            "reason": "content changed" if state == "stale" else "content hash unchanged"}


def evidence_by_id(store, identity):
    row = store.db.execute("SELECT body FROM evidence WHERE id=?", (identity,)).fetchone()
    if row is None:
        raise UserError(f"Unknown evidence id: {identity}")
    return json.loads(row["body"])


def nonempty(value):
    return ((isinstance(value, str) and bool(value.strip())) or
            (isinstance(value, list) and bool(value) and
             all(isinstance(x, str) and bool(x.strip()) for x in value)))


def validate_pattern(store, card):
    if not isinstance(card, dict):
        raise UserError("Pattern must be a JSON object")
    for key in ("id", "title", "problem", "mechanism", "when_to_use", "when_not_to_use",
                "tradeoffs", "counterexample"):
        if not nonempty(card.get(key)):
            raise UserError(f"Pattern requires nonempty {key}")
    for key in ("id", "title", "problem", "mechanism", "counterexample"):
        if not isinstance(card[key], str):
            raise UserError(f"{key} must be a string")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,95}", card["id"]):
        raise UserError("Pattern id must be 1-96 lowercase letters, digits, hyphens or underscores")
    transfer = card.get("transfer")
    if not isinstance(transfer, dict) or any(not nonempty(transfer.get(k)) for k in
                                            ("target", "application", "compatibility_checks")):
        raise UserError("transfer requires target, application and compatibility_checks")
    validation = card.get("validation")
    if (not isinstance(validation, dict) or validation.get("level") not in
            {"source", "model", "integration"} or not nonempty(validation.get("result"))):
        raise UserError("validation requires level source|model|integration and nonempty result")
    ids = card.get("evidence_ids")
    if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids):
        raise UserError("evidence_ids must be a nonempty list of existing evidence IDs")
    if len(set(ids)) != len(ids):
        raise UserError("evidence_ids must not contain duplicates")
    for identity in ids:
        evidence_by_id(store, identity)
    if not isinstance(card.get("tags"), list) or any(not nonempty(x) or not isinstance(x, str)
                                                    for x in card["tags"]):
        raise UserError("tags must be a list of nonempty strings")
    return card


def card_search_text(card):
    """Index human statements, never JSON keys, timestamps, or evidence IDs."""
    def values(value):
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [part for item in value for part in values(item)]
        if isinstance(value, dict):
            return [part for item in value.values() for part in values(item)]
        return []
    fields = ("id", "title", "problem", "mechanism", "when_to_use", "when_not_to_use",
              "tradeoffs", "transfer", "counterexample", "validation", "tags")
    return "\n".join(part for field in fields for part in values(card.get(field)))


def command_doctor(store, args):
    return {"version": VERSION, "python": sys.version.split()[0],
            "sqlite": sqlite3.sqlite_version, "fts5": True, "store": str(store.path),
            "tools": {name: {"available": shutil.which(name) is not None,
                              "path": shutil.which(name)}
                      for name in ("git", "rg", "ast-grep", "octocode", "gitnexus", "repomix")},
            "note": "Tool presence only; adapters not executed, installed, downloaded or qualified."}


def command_catalog(store, args):
    repositories = []
    for value in args.repos:
        root = root_path(value, store.path)
        files, scope = inventory(root)
        tops = {}
        for file in files:
            top = file["path"].split("/")[0] if "/" in file["path"] else "(root)"
            tops[top] = tops.get(top, 0) + 1
        item = {**repo_metadata(root), "captured_at": now(), "scope": scope,
                "file_count": len(files), "files": files,
                "manifests": [f["path"] for f in files if Path(f["path"]).name in MANIFESTS],
                "top_directories": dict(sorted(tops.items(), key=lambda pair: (-pair[1], pair[0])))}
        with store.db:
            store.db.execute("INSERT OR REPLACE INTO catalogs VALUES(?,?)", (str(root), json_text(item)))
            store.log("catalog", {"repo_root": str(root), "file_count": len(files), "scope": scope})
        identity = digest(str(root).encode())[:20]
        store.atomic_json("catalogs", identity, item)
        summary = {k: v for k, v in item.items() if k != "files"}
        summary["manifests"] = item["manifests"][:20]
        summary["manifests_total"] = len(item["manifests"])
        summary["manifests_omitted"] = max(0, len(item["manifests"]) - 20)
        summary["top_directories"] = dict(list(item["top_directories"].items())[:20])
        summary["top_directories_total"] = len(item["top_directories"])
        summary["top_directories_omitted"] = max(0, len(item["top_directories"]) - 20)
        summary["eligible_bytes"] = sum(file["bytes"] for file in files)
        summary["inventory_path"] = str(store.path / "catalogs" / (identity + ".json"))
        repositories.append(summary)
    return {"repositories": repositories}


def command_find(store, args):
    root = root_path(args.repo, store.path)
    limit = bounded_int(args.limit, 1, 100, "limit")
    max_files = bounded_int(args.max_files, 1, MAX_FILES, "max-files")
    offset = bounded_int(args.offset, 0, MAX_FILES, "offset")
    if not args.query or len(args.query) > 1000 or "\n" in args.query:
        raise UserError("Query must be 1-1000 characters on one line")
    files, scope = inventory(root)
    candidates = [f for f in files if not args.glob or fnmatch.fnmatchcase(f["path"], args.glob)]
    candidates.sort(key=lambda item: item["path"])
    binding = {"version": 1, "root": str(root), "query": args.query,
               "glob": args.glob, "max_files": max_files, "limit": limit,
               "inventory": digest(json_text([f["path"] for f in candidates]).encode())}
    if args.cursor:
        try:
            if len(args.cursor) > 16000:
                raise ValueError()
            token = json.loads(base64.b64decode(args.cursor, altchars=b"-_", validate=True))
            if not isinstance(token, dict) or token.get("binding") != binding:
                raise ValueError()
            position = token["offset"]
            if type(position) is not int or not 0 < position <= len(candidates):
                raise ValueError()
            if offset not in (0, position):
                raise ValueError()
            offset = position
        except (ValueError, KeyError, TypeError):
            raise UserError("Continuation no longer matches query or inventory; restart without --cursor/--offset")
    elif offset:
        raise UserError("Nonzero --offset requires the matching --cursor; restart the scan")
    if scope["partial"] and (args.cursor or len(candidates) > max_files):
        raise UserError("Incomplete inventory cannot support continuation; narrow the source root")
    window = candidates[offset:offset + max_files]
    remaining = max(0, len(candidates) - offset - len(window))
    matches, failures = [], {}
    total, read_count = 0, 0
    for file in window:
        try:
            data = source_bytes(root, file["path"]).decode("utf-8")
            read_count += 1
        except (OSError, UserError) as exc:
            reason = type(exc).__name__
            failures[reason] = failures.get(reason, 0) + 1
            continue
        for number, line in enumerate(data.splitlines(), 1):
            if args.query in line:
                total += 1
                if len(matches) < limit:
                    matches.append({"path": file["path"], "line": number,
                                    "text": line[:500], "text_truncated": len(line) > 500})
    after_files, after_scope = inventory(root)
    after_paths = sorted(f["path"] for f in after_files
                         if not args.glob or fnmatch.fnmatchcase(f["path"], args.glob))
    if after_scope["partial"] != scope["partial"] or digest(json_text(after_paths).encode()) != binding["inventory"]:
        raise UserError("Inventory changed during search; restart the scan")
    continuation = base64.urlsafe_b64encode(json_text(
        {"binding": binding, "offset": offset + len(window)}).encode()).decode() if remaining else None
    scope.update(content_consistency="live reads; membership-bound continuation, not a content snapshot",
                 candidate_files=len(candidates), searched_files=read_count,
                 read_failures=failures, glob=args.glob,
                 file_offset=offset, file_budget=max_files, selected_files=len(window),
                 unsearched_files=len(candidates) - len(window), remaining_files=remaining,
                 match_kind="case-sensitive literal matching lines; not semantic identity")
    result = {**repo_metadata(root, dirty=False), "query": args.query,
              "matches": matches, "matched_lines": total, "returned": len(matches),
              "omitted": total - len(matches), "truncated": total > len(matches),
              "partial": scope["partial"] or bool(failures) or total > len(matches) or
                         len(window) != len(candidates),
              "scope": scope,
              "next": {"cursor": continuation, "offset": offset + len(window), "max_files": max_files,
                       "glob": args.glob} if remaining else None,
              "hint": "Narrow --glob on large repositories; matched_lines counts only this file window. Use read for evidence."}
    with store.db:
        store.log("find", {k: v for k, v in result.items() if k != "matches"})
    return result


def command_read(store, args):
    root = root_path(args.repo, store.path)
    if not args.question.strip():
        raise UserError("question must be nonempty")
    if args.start < 1 or args.end < args.start or args.end - args.start + 1 > MAX_LINES:
        raise UserError("Read range must be 1-based, ordered, and at most 160 lines")
    raw = source_bytes(root, args.path)
    lines = raw.decode("utf-8").splitlines(keepends=True)
    if args.end > len(lines):
        raise UserError(f"Read end exceeds file length ({len(lines)} lines)")
    snippet = "".join(lines[args.start - 1:args.end])
    if len(snippet) > MAX_CHARS:
        raise UserError("Read exceeds 24000 characters; request a smaller range")
    relative = Path(args.path).as_posix()
    metadata = repo_metadata(root)
    identity_data = json_text([str(root), relative, digest(raw), args.start, args.end]).encode()
    identity = "ev-" + digest(identity_data)[:24]
    item = {"id": identity, "repo_root": str(root), "path": relative,
            "head": metadata["head"], "dirty": metadata["dirty"],
            "dirty_status_available": metadata["dirty_status_available"],
            "dirty_scope": metadata["dirty_scope"], "file_sha256": digest(raw),
            "slice_sha256": digest(snippet.encode("utf-8")), "start_line": args.start,
            "end_line": args.end, "snippet": snippet, "question": args.question,
            "captured_at": now(), "tool_version": VERSION, "evidence_kind": "source",
            "claim_limit": "Source observation; does not prove runtime behavior or transfer."}
    with store.db:
        store.db.execute("BEGIN IMMEDIATE")
        existing = store.db.execute("SELECT body FROM evidence WHERE id=?", (identity,)).fetchone()
        repeated = existing is not None
        if existing:
            item = json.loads(existing["body"])
        store.db.execute("INSERT OR IGNORE INTO evidence VALUES(?,?)", (identity, json_text(item)))
        store.log("read", {"evidence_id": identity, "question": args.question, "repeated": repeated})
    store.atomic_json("evidence", identity, item)
    return {"evidence": item, "repeated": repeated,
            "freshness": freshness(item), "requested_question": args.question}


def command_add_pattern(store, args):
    path = Path(args.file).expanduser()
    if path.stat().st_size > MAX_FILE_BYTES:
        raise UserError("Pattern JSON exceeds 1 MiB")
    card = validate_pattern(store, json.loads(path.read_text(encoding="utf-8")))
    # Serialize lookup and creation so simultaneous identical retries converge.
    with store.db:
        store.db.execute("BEGIN IMMEDIATE")
        existing = store.db.execute("SELECT body FROM patterns WHERE id=?", (card["id"],)).fetchone()
        repeated = existing is not None
        if existing:
            stored = json.loads(existing["body"])
            payload = {k: v for k, v in stored.items() if k not in ("created_at", "schema_version")}
            incoming = {k: v for k, v in card.items() if k not in ("created_at", "schema_version")}
            if payload != incoming:
                raise UserError("Pattern id already exists with different content; use a new versioned id")
        else:
            stored = {**card, "created_at": now(), "schema_version": 1}
            store.db.execute("INSERT INTO patterns VALUES(?,?)", (card["id"], json_text(stored)))
            store.db.execute("INSERT INTO pattern_fts(id,text) VALUES(?,?)",
                             (card["id"], card_search_text(stored)))
        store.log("add-pattern", {"pattern_id": card["id"], "evidence_ids": card["evidence_ids"],
                                  "repeated": repeated})
    try:
        store.atomic_json("patterns", card["id"], stored)
    except (OSError, UserError) as exc:
        raise ProjectionError(card["id"], exc) from exc
    return {"pattern": stored, "repeated": repeated, "canonical_committed": True,
            "projection_written": True,
            "evidence_freshness": [freshness(evidence_by_id(store, x)) for x in card["evidence_ids"]],
            "note": "Schema and provenance checked; validation statements remain author assertions."}


def command_query(store, args):
    limit = bounded_int(args.limit, 1, 100, "limit")
    words = re.findall(r"\w+", args.query, flags=re.UNICODE)
    if not words or len(words) > 50:
        raise UserError("Query requires 1-50 searchable words")
    expression = " OR ".join('"' + word.replace('"', '""') + '"' for word in words)
    rows = store.db.execute("SELECT p.body, bm25(pattern_fts) AS score FROM pattern_fts "
                            "JOIN patterns p ON p.id=pattern_fts.id WHERE pattern_fts MATCH ? "
                            "ORDER BY score, p.id LIMIT ?", (expression, limit)).fetchall()
    results = []
    for row in rows:
        pattern = json.loads(row["body"])
        results.append({"pattern": pattern, "score": row["score"],
                        "evidence_freshness": [freshness(evidence_by_id(store, x))
                                               for x in pattern["evidence_ids"]]})
    with store.db:
        store.log("query", {"query": args.query, "returned": len(results)})
    return {"query": args.query, "results": results,
            "ranking": "FTS5 BM25 over pattern cards; lower score ranks first; relevance is not proof"}


def command_verify(store, args):
    results = [freshness(json.loads(row["body"])) for row in
               store.db.execute("SELECT body FROM evidence ORDER BY id")]
    summary = {}
    for item in results:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    with store.db:
        store.log("verify", {"summary": summary})
    return {"evidence": results, "summary": summary,
            "note": "Original evidence retained unchanged. Fresh content is not proof the interpretation is correct."}


def command_export(store, args):
    cards = [json.loads(row["body"]) for row in store.db.execute("SELECT body FROM patterns ORDER BY id")]
    lines = ["# Repository pattern library", "", f"Exported {now()}", "",
             "Validation levels are author assertions. Inspect evidence and test transfer before reuse.", ""]
    for card in cards:
        lines += [f"## {card['title']}", "", f"ID: `{card['id']}`", ""]
        for key in ("problem", "mechanism", "when_to_use", "when_not_to_use", "tradeoffs",
                    "transfer", "counterexample", "validation", "tags"):
            value = card[key]
            if isinstance(value, dict):
                value = "; ".join(f"{k}: {v}" for k, v in value.items())
            elif isinstance(value, list):
                value = "; ".join(value)
            lines += [f"**{key.replace('_', ' ').capitalize()}:** {value}", ""]
        lines += ["Evidence:", ""]
        for identity in card["evidence_ids"]:
            item = evidence_by_id(store, identity)
            state = freshness(item)
            lines += [f"- `{identity}`: `{item['repo_root']}/{item['path']}` "
                      f"lines {item['start_line']}–{item['end_line']}; {state['status']}; "
                      f"HEAD `{item['head']}`; SHA-256 `{item['file_sha256']}`."]
        lines += [""]
    path = store.path / "patterns.md"
    atomic_text(path, "\n".join(lines))
    with store.db:
        store.log("export", {"path": str(path), "patterns": len(cards)})
    return {"path": str(path), "patterns": len(cards)}


def command_status(store, args):
    counts = {table: store.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
              for table in ("evidence", "patterns", "catalogs", "journal")}
    return {"store": str(store.path), "version": VERSION, "counts": counts}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--store", help="Explicit directory outside source repositories")
    sub = p.add_subparsers(dest="command", required=True)
    commands = {}
    for name in ("doctor", "catalog", "find", "read", "add-pattern", "query", "verify", "export", "status"):
        commands[name] = sub.add_parser(name)
        commands[name].add_argument("--store", default=argparse.SUPPRESS)
    commands["catalog"].add_argument("repos", nargs="+")
    commands["find"].add_argument("repo")
    commands["find"].add_argument("query")
    commands["find"].add_argument("--glob")
    commands["find"].add_argument("--limit", type=int, default=20)
    commands["find"].add_argument("--max-files", type=int, default=2000)
    commands["find"].add_argument("--cursor", help="Opaque continuation returned by the previous find page")
    commands["find"].add_argument("--offset", type=int, default=0)
    commands["read"].add_argument("repo")
    commands["read"].add_argument("path")
    commands["read"].add_argument("--start", type=int, required=True)
    commands["read"].add_argument("--end", type=int, required=True)
    commands["read"].add_argument("--question", required=True)
    commands["add-pattern"].add_argument("file")
    commands["query"].add_argument("query")
    commands["query"].add_argument("--limit", type=int, default=10)
    return p


def main(argv=None):
    store = None
    started = time.monotonic()
    try:
        args = parser().parse_args(argv)
        if not args.store:
            raise UserError("--store is required; no implicit global writes")
        # Validate source/store overlap BEFORE creating even the store directory.
        destination = Path(args.store).expanduser()
        if not destination.is_absolute():
            raise UserError("Store must be an absolute path")
        sources = getattr(args, "repos", []) or ([args.repo] if hasattr(args, "repo") else [])
        for source in sources:
            root_path(source, destination.resolve())
        store = Store(destination)
        handler = globals()["command_" + args.command.replace("-", "_")]
        result = handler(store, args)
        print(json_text({"ok": True, "command": args.command,
                         "elapsed_seconds": round(time.monotonic() - started, 4), **result}))
        return 0
    except (UserError, OSError, ValueError, sqlite3.Error) as exc:
        print(json_text({"ok": False, "error": str(exc), **getattr(exc, "details", {})}), file=sys.stderr)
        return 2
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    raise SystemExit(main())
