#!/usr/bin/env python3
"""Read-first filesystem lifecycle auditor and exact-manifest executor.

The default `audit` command only reads metadata. `apply` requires explicit IDs,
a recorded authorization source, an execution switch, an acknowledgement phrase,
fresh identity/liveness checks, and owner-specific revalidation.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable


SCHEMA = "filesystem-lifecycle/v2"
ACK = "DELETE EXACT SAFE-NOW PATHS"
CLASS_SAFE = "safe_now"
CLASS_AFTER = "safe_after_active_thread_closeout"
CLASS_RETAIN = "retain"
CLASS_UNKNOWN = "unknown"

ARTIFACT_RULES: dict[str, dict[str, Any]] = {
    ".zig-cache": {"owner": "zig", "markers": ("build.zig", "build.zig.zon"), "rebuild": "zig build"},
    "zig-cache": {"owner": "zig", "markers": ("build.zig", "build.zig.zon"), "rebuild": "zig build"},
    "target": {"owner": "cargo", "markers": ("Cargo.toml",), "rebuild": "cargo build"},
    "node_modules": {
        "owner": "node-package-manager",
        "markers": ("package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"),
        "rebuild": "use the repository lockfile and package manager install command",
    },
    ".venv": {
        "owner": "python-environment",
        "markers": ("pyproject.toml", "requirements.txt", "uv.lock", "Pipfile"),
        "rebuild": "recreate from pyproject, lockfile, or requirements",
    },
}

KNOWN_CACHES: tuple[dict[str, Any], ...] = (
    {"path": "~/.cache/huggingface", "owner": "huggingface", "processes": ("python",), "recovery": "redownload models and datasets"},
    {"path": "~/.npm/_cacache", "owner": "npm", "processes": ("node", "npm",), "recovery": "npm redownloads packages"},
    {"path": "~/.npm/_npx", "owner": "npx", "processes": ("node", "npm", "npx",), "recovery": "npx recreates executions"},
    {"path": "~/.cargo/registry/cache", "owner": "cargo", "processes": ("cargo", "rustc",), "recovery": "Cargo redownloads crates"},
    {"path": "~/.cargo/registry/src", "owner": "cargo", "processes": ("cargo", "rustc",), "recovery": "Cargo re-expands crates"},
    {"path": "~/.cargo/git/checkouts", "owner": "cargo", "processes": ("cargo", "rustc",), "recovery": "Cargo refetches Git dependencies"},
    {"path": "~/Library/Caches/Cypress", "owner": "cypress", "processes": ("cypress",), "recovery": "Cypress redownloads binaries"},
    {"path": "~/Library/Caches/ms-playwright-mcp", "owner": "playwright", "processes": ("playwright",), "recovery": "Playwright redownloads browser assets"},
    {"path": "~/Library/Caches/node-gyp", "owner": "node-gyp", "processes": ("node", "npm",), "recovery": "node-gyp redownloads headers"},
    {"path": "~/Library/Caches/Homebrew", "owner": "homebrew", "processes": ("brew",), "recovery": "Homebrew redownloads artifacts"},
    {"path": "~/Library/Application Support/Claude/vm_bundles", "owner": "claude", "processes": ("claude",), "recovery": "Claude recreates the VM bundle"},
)


def run(argv: list[str], *, check: bool = False, timeout: int = 120) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check, timeout=timeout)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode()).hexdigest()[:12]
    return f"{prefix}:{digest}"


def manifest_digest(manifest: dict[str, Any]) -> str:
    material = dict(manifest)
    material.pop("integrity", None)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def canonical(path: Path) -> Path:
    return path.expanduser().resolve(strict=True)


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def mount_root(path: Path) -> Path:
    current = path if path.is_dir() else path.parent
    device = current.stat().st_dev
    while current.parent != current:
        try:
            if current.parent.stat().st_dev != device:
                break
        except OSError:
            break
        current = current.parent
    return current


def path_identity(path: Path) -> dict[str, Any]:
    expanded = path.expanduser()
    st = expanded.lstat()
    real = expanded.resolve(strict=True)
    root = mount_root(real)
    return {
        "canonical_path": str(real),
        "device": int(st.st_dev),
        "inode": int(st.st_ino),
        "link_count": int(st.st_nlink),
        "mount_id": f"device:{int(real.stat().st_dev)}:{root}",
        "is_symlink": stat.S_ISLNK(st.st_mode),
    }


def allocated_bytes(path: Path) -> int:
    proc = run(["/usr/bin/du", "-skx", str(path)], timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode(errors="replace").strip() or "du failed")
    return int(proc.stdout.split(None, 1)[0]) * 1024


def logical_bytes(path: Path) -> int:
    argv = ["/usr/bin/du", "-skA", str(path)] if sys.platform == "darwin" else ["/usr/bin/du", "-sk", "--apparent-size", str(path)]
    proc = run(argv, timeout=600)
    if proc.returncode == 0:
        return int(proc.stdout.split(None, 1)[0]) * 1024
    total = 0
    seen: set[tuple[int, int]] = set()
    root_device = path.stat().st_dev
    for current, dirs, files in os.walk(path, followlinks=False):
        current_path = Path(current)
        dirs[:] = [name for name in dirs if not (current_path / name).is_symlink()]
        for name in files:
            child = current_path / name
            try:
                st = child.lstat()
            except OSError:
                continue
            if st.st_dev != root_device:
                continue
            key = (int(st.st_dev), int(st.st_ino))
            if key not in seen:
                seen.add(key)
                total += int(st.st_size)
    return total


def storage_evidence(path: Path) -> dict[str, Any]:
    return {
        "logical_bytes": logical_bytes(path),
        "allocated_bytes": allocated_bytes(path),
        "estimated_reclaimability": "unknown",
    }


def volume_free(path: Path) -> dict[str, Any]:
    anchor = path if path.exists() else path.parent
    usage = shutil.disk_usage(anchor)
    return {"anchor": str(anchor), "total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free}


def pid_tree(root_pid: int) -> list[int]:
    proc = run(["ps", "-axo", "pid=,ppid="], timeout=30)
    if proc.returncode != 0:
        return [root_pid]
    children: dict[int, list[int]] = {}
    for line in proc.stdout.decode(errors="replace").splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        pid, parent = int(fields[0]), int(fields[1])
        children.setdefault(parent, []).append(pid)
    result: set[int] = {root_pid}
    stack = [root_pid]
    while stack:
        current = stack.pop()
        for child in children.get(current, []):
            if child not in result:
                result.add(child)
                stack.append(child)
    return sorted(result)


def observer_context() -> dict[str, Any]:
    observer_pids = pid_tree(os.getpid())
    return {
        "pid": os.getpid(),
        "process_group": os.getpgrp(),
        "excluded_pids": observer_pids,
    }


def mounted_descendants(path: Path) -> list[str]:
    proc = run(["mount"], timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode(errors="replace").strip() or "mount inventory failed")
    result: list[str] = []
    real = path.resolve(strict=True)
    for line in proc.stdout.decode(errors="replace").splitlines():
        marker = " on "
        if marker not in line:
            continue
        right = line.split(marker, 1)[1]
        mount_text = (right.split(" (", 1)[0] if " (" in right else right.split(" type ", 1)[0]).replace("\\040", " ")
        mount_path = Path(mount_text).resolve(strict=False)
        if mount_path != real and is_within(mount_path, real):
            result.append(str(mount_path))
    return sorted(set(result))


def process_snapshot(exclude_pids: set[int] | None = None) -> tuple[list[dict[str, Any]], bool, str | None]:
    if shutil.which("lsof") is None:
        return [], False, "lsof unavailable"
    proc = run(["lsof", "-nP", "-F", "pcfn"], timeout=180)
    if proc.returncode not in (0, 1):
        return [], False, proc.stderr.decode(errors="replace").strip() or "lsof failed"
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    fd = ""
    for raw in proc.stdout.decode(errors="surrogateescape").splitlines():
        if not raw:
            continue
        tag, value = raw[0], raw[1:]
        if tag == "p":
            if current:
                records.append(current)
            current = {"pid": int(value), "command": "", "cwd": [], "paths": []}
            fd = ""
        elif current is not None and tag == "c":
            current["command"] = value
        elif current is not None and tag == "f":
            fd = value
        elif current is not None and tag == "n" and value.startswith("/"):
            if fd == "cwd":
                current["cwd"].append(value)
            else:
                current["paths"].append(value)
    if current:
        records.append(current)
    excluded = exclude_pids or set()
    return [record for record in records if record["pid"] not in excluded], True, None


def refs_for(path: Path, processes: list[dict[str, Any]]) -> dict[str, Any]:
    cwd_pids: set[int] = set()
    handle_pids: set[int] = set()
    for record in processes:
        for value in record["cwd"]:
            try:
                if is_within(Path(value).resolve(strict=False), path):
                    cwd_pids.add(record["pid"])
            except OSError:
                continue
        for value in record["paths"]:
            try:
                if is_within(Path(value).resolve(strict=False), path):
                    handle_pids.add(record["pid"])
            except OSError:
                continue
    return {"cwd_pids": sorted(cwd_pids), "open_handle_pids": sorted(handle_pids)}


def open_codex_roots(processes: list[dict[str, Any]]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for record in processes:
        for value in record["paths"]:
            if "/.codex/sessions/" not in value or not value.endswith(".jsonl") or value in seen:
                continue
            seen.add(value)
            try:
                with open(value, "r", encoding="utf-8", errors="replace") as handle:
                    for _ in range(8):
                        line = handle.readline(262_144)
                        if not line:
                            break
                        obj = json.loads(line)
                        payload = obj.get("payload", {})
                        root = payload.get("cwd") or payload.get("working_directory")
                        if obj.get("type") == "session_meta" and isinstance(root, str) and root.startswith("/"):
                            results.append({"session_file": value, "root": str(Path(root).resolve(strict=False))})
                            break
            except (OSError, ValueError, json.JSONDecodeError):
                continue
    return results


def codex_refs(path: Path, roots: list[dict[str, str]]) -> list[str]:
    matched: list[str] = []
    for item in roots:
        root = Path(item["root"])
        if is_within(path, root) or is_within(root, path):
            matched.append(item["root"])
    return sorted(set(matched))


def process_names(processes: list[dict[str, Any]]) -> set[str]:
    return {str(p["command"]).lower() for p in processes if p.get("command")}


def git_stdout(path: Path, args: list[str]) -> tuple[int, bytes, str]:
    proc = run(["git", "-C", str(path), *args])
    return proc.returncode, proc.stdout, proc.stderr.decode(errors="replace").strip()


def git_root(path: Path) -> Path | None:
    code, out, _ = git_stdout(path, ["rev-parse", "--show-toplevel"])
    if code != 0:
        return None
    try:
        return Path(out.decode().strip()).resolve(strict=True)
    except OSError:
        return None


def contains_tracked_files(path: Path) -> tuple[bool | None, str | None]:
    root = git_root(path.parent)
    if root is None:
        return False, None
    try:
        rel = path.relative_to(root)
    except ValueError:
        return None, "candidate is outside discovered Git root"
    code, out, err = git_stdout(root, ["ls-files", "-z", "--", str(rel)])
    if code != 0:
        return None, err or "git ls-files failed"
    return bool(out), None


def project_marker(path: Path, rule: dict[str, Any]) -> bool:
    parent = path.parent
    return any((parent / marker).exists() for marker in rule["markers"])


def scan_artifacts(roots: Iterable[Path], max_depth: int) -> tuple[list[tuple[Path, Path]], dict[str, Any]]:
    found: list[tuple[Path, Path]] = []
    errors: list[dict[str, str]] = []
    excluded_mounts: list[str] = []
    skip_names = {".git", ".svn", ".hg", "Library", "Documents", "Downloads", "Desktop", "Pictures", "Movies", "Music"}
    for raw_root in roots:
        root = canonical(raw_root)
        root_device = root.stat().st_dev
        stack: list[tuple[Path, int]] = [(root, 0)]
        while stack:
            current, depth = stack.pop()
            if depth >= max_depth:
                continue
            try:
                entries = list(os.scandir(current))
            except (OSError, PermissionError) as exc:
                errors.append({"path": str(current), "error": str(exc)})
                continue
            for entry in entries:
                if not entry.is_dir(follow_symlinks=False):
                    continue
                child = Path(entry.path)
                try:
                    if entry.stat(follow_symlinks=False).st_dev != root_device:
                        excluded_mounts.append(str(child))
                        continue
                except OSError as exc:
                    errors.append({"path": str(child), "error": str(exc)})
                    continue
                if entry.name in ARTIFACT_RULES:
                    found.append((child, root))
                    continue
                if entry.name in skip_names or entry.is_symlink():
                    continue
                stack.append((child, depth + 1))
    unique = sorted(set(found), key=lambda item: (str(item[0]), str(item[1])))
    return unique, {
        "scan_complete": not errors,
        "errors": errors,
        "excluded_mounts": sorted(set(excluded_mounts)),
        "stay_on_device": True,
    }


def parse_worktree_porcelain(data: bytes) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in data.split(b"\0"):
        if not raw:
            continue
        text = raw.decode(errors="surrogateescape")
        key, _, value = text.partition(" ")
        if key == "worktree":
            if current:
                entries.append(current)
            current = {"path": value}
        elif current is not None:
            current[key] = value if value else True
    if current:
        entries.append(current)
    return entries


def choose_base(repo: Path) -> str | None:
    for ref in ("refs/remotes/origin/main", "refs/remotes/origin/master", "refs/heads/main", "refs/heads/master"):
        code, _, _ = git_stdout(repo, ["show-ref", "--verify", "--quiet", ref])
        if code == 0:
            return ref
    return None


def representation(repo: Path, head: str, base: str) -> str:
    code, _, _ = git_stdout(repo, ["merge-base", "--is-ancestor", head, base])
    if code == 0:
        return "exact_ancestor"
    if code != 1:
        return "unknown"
    code, _, _ = git_stdout(repo, ["diff", "--quiet", base, head])
    if code == 0:
        return "tree_equivalent"
    if code != 1:
        return "unknown"
    code, out, _ = git_stdout(repo, ["cherry", base, head])
    if code != 0:
        return "unknown"
    lines = [line for line in out.decode(errors="replace").splitlines() if line.strip()]
    if lines and all(line.startswith("-") for line in lines):
        return "patch_equivalent"
    return "unique"


def candidate_base(path: Path, approved_root: Path, kind: str, owner: str, recovery: dict[str, str], action: dict[str, Any]) -> dict[str, Any]:
    real = canonical(path)
    root = canonical(approved_root)
    identity = path_identity(path)
    errors: list[str] = []
    unexpected_mounts: list[str] = []
    if real == root or not is_within(real, root):
        errors.append("candidate is not strictly beneath approved root")
    try:
        unexpected_mounts = mounted_descendants(real)
        if unexpected_mounts:
            errors.append("candidate contains a nested mount")
    except RuntimeError as exc:
        errors.append(str(exc))
    return {
        "id": stable_id(kind.split("_")[0], str(real)),
        "path": str(path.expanduser()),
        "canonical_path": str(real),
        "kind": kind,
        "owner": owner,
        "evidence": {"observed_at": now_utc(), "scan_complete": not errors, "errors": errors},
        "identity": identity,
        "boundary": {
            "approved_root": str(root),
            "approved_root_device": int(root.stat().st_dev),
            "stay_on_device": True,
            "unexpected_mounts": unexpected_mounts,
        },
        "storage": storage_evidence(real),
        "references": {"cwd_pids": [], "open_handle_pids": [], "codex_session_roots": []},
        "recovery": recovery,
        "classification": CLASS_UNKNOWN,
        "reasons": [],
        "action": action,
        "preconditions": ["strictly_beneath_approved_root", "canonical_identity_unchanged", "same_device", "no_nested_mount", "no_symlink_traversal", "no_live_reference", "fresh_manifest"],
    }


def unknown_candidate(path: Path, approved_root: Path, kind: str, owner: str, error: str) -> dict[str, Any]:
    expanded = path.expanduser()
    real = expanded.resolve(strict=False)
    root = approved_root.expanduser().resolve(strict=False)
    try:
        identity = path_identity(expanded)
    except OSError:
        identity = {
            "canonical_path": str(real),
            "device": None,
            "inode": None,
            "link_count": None,
            "mount_id": None,
            "is_symlink": None,
        }
    return {
        "id": stable_id(kind.split("_")[0], str(real)),
        "path": str(expanded),
        "canonical_path": str(real),
        "kind": kind,
        "owner": owner,
        "evidence": {"observed_at": now_utc(), "scan_complete": False, "errors": [error]},
        "identity": identity,
        "boundary": {
            "approved_root": str(root),
            "approved_root_device": None,
            "stay_on_device": True,
            "unexpected_mounts": [],
        },
        "storage": {"logical_bytes": None, "allocated_bytes": None, "estimated_reclaimability": "unknown"},
        "references": {"cwd_pids": [], "open_handle_pids": [], "codex_session_roots": []},
        "recovery": {"level": "none_or_unknown", "method": "unknown"},
        "classification": CLASS_UNKNOWN,
        "reasons": [error],
        "action": None,
        "preconditions": [],
    }


def classify_path_candidate(candidate: dict[str, Any], processes: list[dict[str, Any]], lsof_ok: bool, roots: list[dict[str, str]], *, tracked: bool | None = False, tracked_error: str | None = None, owner_active: bool = False) -> None:
    path = Path(candidate["canonical_path"])
    refs = refs_for(path, processes)
    refs["codex_session_roots"] = codex_refs(path, roots)
    candidate["references"] = refs
    if not candidate.get("evidence", {}).get("scan_complete", False):
        candidate["classification"] = CLASS_UNKNOWN
        candidate["reasons"].append("candidate evidence is incomplete")
    elif candidate.get("identity", {}).get("is_symlink"):
        candidate["classification"] = CLASS_UNKNOWN
        candidate["reasons"].append("candidate path is a symlink")
    elif not lsof_ok:
        candidate["classification"] = CLASS_UNKNOWN
        candidate["reasons"].append("open-handle inventory incomplete")
    elif tracked is None:
        candidate["classification"] = CLASS_UNKNOWN
        candidate["reasons"].append(tracked_error or "tracked-file check incomplete")
    elif tracked:
        candidate["classification"] = CLASS_RETAIN
        candidate["reasons"].append("contains Git-tracked files")
    elif refs["cwd_pids"] or refs["open_handle_pids"] or refs["codex_session_roots"] or owner_active:
        candidate["classification"] = CLASS_AFTER
        candidate["reasons"].append("currently referenced by a process, owner, or Codex task")
    else:
        candidate["classification"] = CLASS_SAFE
        candidate["reasons"].append("inactive and recoverable with no tracked files")


def audit_artifacts(discovered: list[tuple[Path, Path]], processes: list[dict[str, Any]], lsof_ok: bool, codex_roots: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path, approved_root in discovered:
        rule = ARTIFACT_RULES[path.name]
        try:
            candidate = candidate_base(
                path,
                approved_root,
                "generated_artifact",
                rule["owner"],
                {"level": "regenerable", "method": rule["rebuild"]},
                {"driver": "filesystem", "operation": "delete_exact_tree"},
            )
            candidate["preconditions"].extend(("recognized_artifact_marker", "contains_no_tracked_files"))
            if not project_marker(path, rule):
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append("recognized basename but project marker is missing")
            else:
                tracked, err = contains_tracked_files(path)
                classify_path_candidate(candidate, processes, lsof_ok, codex_roots, tracked=tracked, tracked_error=err)
            candidates.append(candidate)
        except (OSError, RuntimeError) as exc:
            candidates.append(unknown_candidate(path, approved_root, "generated_artifact", rule["owner"], str(exc)))
    return candidates


def audit_caches(processes: list[dict[str, Any]], lsof_ok: bool, codex_roots: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    names = process_names(processes)
    for rule in KNOWN_CACHES:
        path = Path(rule["path"]).expanduser()
        if not path.exists():
            continue
        try:
            if path.is_symlink():
                raise RuntimeError("cache path is a symlink")
            candidate = candidate_base(
                path,
                path.parent,
                "known_cache",
                rule["owner"],
                {"level": "recreated_by_owner", "method": rule["recovery"]},
                {"driver": "filesystem", "operation": "delete_exact_tree"},
            )
            candidate["preconditions"].append("known_cache_allowlist_match")
            active = any(any(token in name for name in names) for token in rule["processes"])
            classify_path_candidate(candidate, processes, lsof_ok, codex_roots, owner_active=active)
            candidates.append(candidate)
        except (OSError, RuntimeError) as exc:
            candidates.append(unknown_candidate(path, path.parent, "known_cache", rule["owner"], str(exc)))
    return candidates


def audit_worktrees(repo: Path, processes: list[dict[str, Any]], lsof_ok: bool, codex_roots: list[dict[str, str]]) -> list[dict[str, Any]]:
    repo = canonical(repo)
    code, out, err = git_stdout(repo, ["worktree", "list", "--porcelain", "-z"])
    if code != 0:
        return [unknown_candidate(repo, repo.parent, "git_repository", "git", err or "git worktree list failed")]
    entries = parse_worktree_porcelain(out)
    base = choose_base(repo)
    candidates: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        raw_path = Path(entry["path"])
        if not raw_path.exists():
            candidates.append({
                "id": stable_id("worktree", str(repo), str(raw_path)),
                "path": str(raw_path),
                "canonical_path": str(raw_path.resolve(strict=False)),
                "kind": "stale_worktree_registration",
                "owner": "git",
                "repository": str(repo),
                "evidence": {"observed_at": now_utc(), "scan_complete": False, "errors": ["worktree path is missing"]},
                "identity": {
                    "canonical_path": str(raw_path.resolve(strict=False)),
                    "device": None,
                    "inode": None,
                    "link_count": None,
                    "mount_id": None,
                    "is_symlink": None,
                },
                "boundary": {
                    "approved_root": str(raw_path.parent.resolve(strict=False)),
                    "approved_root_device": None,
                    "stay_on_device": True,
                    "unexpected_mounts": [],
                },
                "classification": CLASS_UNKNOWN,
                "reasons": ["registered worktree path is missing; inspect Git prune dry-run separately"],
                "recovery": {"level": "exact", "method": "Git refs remain unchanged"},
                "action": {"driver": "git", "operation": "worktree_prune_dry_run_then_prune"},
                "preconditions": ["path_still_missing", "registration_still_prunable", "not_locked"],
                "storage": {"logical_bytes": 0, "allocated_bytes": 0, "estimated_reclaimability": "unknown"},
                "references": {"cwd_pids": [], "open_handle_pids": [], "codex_session_roots": []},
            })
            continue
        try:
            candidate = candidate_base(
                raw_path,
                raw_path.parent,
                "git_worktree",
                "git",
                {"level": "exact", "method": "recreate checkout from retained Git ref or represented base"},
                {"driver": "git", "operation": "worktree_remove_preserve_branch"},
            )
            candidate.update({
                "repository": str(repo),
                "git": {
                    "head": str(entry.get("HEAD", entry.get("head", ""))),
                    "branch": entry.get("branch"),
                    "detached": bool(entry.get("detached")),
                    "locked": bool(entry.get("locked")),
                    "base_ref": base,
                    "clean": None,
                    "representation": None,
                },
            })
            candidate["preconditions"].extend(("registered_linked_worktree", "clean", "not_locked", "head_unchanged", "represented_in_base"))
            refs = refs_for(Path(candidate["canonical_path"]), processes)
            refs["codex_session_roots"] = codex_refs(Path(candidate["canonical_path"]), codex_roots)
            candidate["references"] = refs
            if index == 0:
                candidate["classification"] = CLASS_RETAIN
                candidate["reasons"].append("main worktree")
                candidates.append(candidate)
                continue
            if not candidate.get("evidence", {}).get("scan_complete", False) or candidate.get("identity", {}).get("is_symlink"):
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append("worktree boundary or identity evidence is incomplete")
                candidates.append(candidate)
                continue
            if entry.get("locked"):
                candidate["classification"] = CLASS_RETAIN
                candidate["reasons"].append("Git worktree is locked")
                candidates.append(candidate)
                continue
            status_code, status_out, status_err = git_stdout(Path(candidate["canonical_path"]), ["status", "--porcelain=v1", "-z", "--untracked-files=all"])
            if status_code != 0:
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append(status_err or "git status failed")
                candidates.append(candidate)
                continue
            clean = not bool(status_out)
            candidate["git"]["clean"] = clean
            if not clean:
                candidate["classification"] = CLASS_RETAIN
                candidate["reasons"].append("worktree contains tracked or untracked changes")
                candidates.append(candidate)
                continue
            head = candidate["git"]["head"]
            rep = representation(repo, head, base) if base and head else "unknown"
            candidate["git"]["representation"] = rep
            if not lsof_ok:
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append("open-handle inventory incomplete")
            elif refs["cwd_pids"] or refs["open_handle_pids"] or refs["codex_session_roots"]:
                candidate["classification"] = CLASS_AFTER
                candidate["reasons"].append("clean but currently referenced")
            elif base is None:
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append("no main/master base ref found")
            elif rep == "unknown":
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append("Git representation proof could not be completed")
            elif rep == "unique":
                candidate["classification"] = CLASS_RETAIN
                candidate["reasons"].append("clean checkout contains a unique patch relative to base")
            else:
                candidate["classification"] = CLASS_SAFE
                candidate["reasons"].append(f"clean inactive linked checkout represented by {rep}")
            candidates.append(candidate)
        except (OSError, RuntimeError) as exc:
            candidates.append(unknown_candidate(raw_path, raw_path.parent, "git_worktree", "git", str(exc)))
    return candidates


def add_overlap(candidates: list[dict[str, Any]]) -> None:
    safe_worktrees = [c for c in candidates if c.get("kind") == "git_worktree" and c.get("classification") == CLASS_SAFE and c.get("canonical_path")]
    for candidate in candidates:
        if candidate.get("kind") != "generated_artifact" or not candidate.get("canonical_path"):
            continue
        path = Path(candidate["canonical_path"])
        for worktree in safe_worktrees:
            if is_within(path, Path(worktree["canonical_path"])):
                candidate["covered_by"] = worktree["id"]
                candidate["reasons"].append("size overlaps removable worktree; do not sum or select both")
                break
    seen_inodes: dict[tuple[int, int], str] = {}
    for candidate in candidates:
        identity = candidate.get("identity", {})
        device, inode = identity.get("device"), identity.get("inode")
        if device is None or inode is None:
            continue
        key = (int(device), int(inode))
        if key in seen_inodes and not candidate.get("covered_by"):
            candidate["covered_by"] = seen_inodes[key]
            candidate["storage"]["estimated_reclaimability"] = "partial"
            candidate["reasons"].append("candidate shares an inode with another manifest record; do not count twice")
        else:
            seen_inodes[key] = candidate["id"]


def audit(args: argparse.Namespace) -> int:
    observer = observer_context()
    roots = [canonical(Path(value).expanduser()) for value in args.root]
    repos = [canonical(Path(value).expanduser()) for value in args.repo]
    if args.authorization_mode == "goal_authorized" and not args.authorization_scope:
        raise SystemExit("goal_authorized requires at least one --authorization-scope")
    discovered, discovery_evidence = scan_artifacts(roots, args.max_depth) if roots else ([], {"scan_complete": True, "errors": [], "excluded_mounts": [], "stay_on_device": True})
    processes, lsof_ok, lsof_error = process_snapshot(set(observer["excluded_pids"]))
    liveness_observed_at = now_utc()
    codex_roots = open_codex_roots(processes)
    candidates: list[dict[str, Any]] = []
    if discovered:
        candidates.extend(audit_artifacts(discovered, processes, lsof_ok, codex_roots))
    if args.include_known_caches:
        candidates.extend(audit_caches(processes, lsof_ok, codex_roots))
    for repo in repos:
        candidates.extend(audit_worktrees(repo, processes, lsof_ok, codex_roots))
    add_overlap(candidates)
    anchor = Path(args.volume).expanduser()
    manifest = {
        "schema": SCHEMA,
        "generated_at": now_utc(),
        "mode": "audit",
        "authorization": {"mode": args.authorization_mode, "scope": args.authorization_scope},
        "scope": {"roots": [str(p) for p in roots], "repositories": [str(p) for p in repos], "max_depth": args.max_depth, "stay_on_device": True},
        "evidence": {
            "observer": observer,
            "discovery": discovery_evidence,
            "liveness_observed_at": liveness_observed_at,
            "lsof_complete": lsof_ok,
            "lsof_error": lsof_error,
            "open_codex_session_roots": codex_roots,
            "volume_before": volume_free(anchor),
        },
        "candidates": candidates,
    }
    manifest["integrity"] = {"algorithm": "sha256", "digest": manifest_digest(manifest)}
    output = json.dumps(manifest, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"wrote {len(candidates)} candidates to {args.output}")
    else:
        print(output)
    return 0


def age_minutes(timestamp: str) -> float:
    created = dt.datetime.fromisoformat(timestamp)
    if created.tzinfo is None:
        created = created.replace(tzinfo=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - created).total_seconds() / 60.0


def safe_delete_tree(path: Path) -> None:
    if path.is_symlink():
        raise RuntimeError("refusing to traverse symlink target")
    root_device = path.stat().st_dev

    def preflight(current: Path) -> None:
        with os.scandir(current) as entries:
            for entry in entries:
                st = entry.stat(follow_symlinks=False)
                if st.st_dev != root_device:
                    raise RuntimeError(f"refusing cross-device traversal at {entry.path}")
                if stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode):
                    preflight(Path(entry.path))

    def remove(current: Path) -> None:
        with os.scandir(current) as entries:
            children = list(entries)
        for entry in children:
            st = entry.stat(follow_symlinks=False)
            if st.st_dev != root_device:
                raise RuntimeError(f"device changed during deletion at {entry.path}")
            child = Path(entry.path)
            if stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode):
                remove(child)
            else:
                child.unlink()
        current.rmdir()

    preflight(path)
    remove(path)


def verify_identity(candidate: dict[str, Any]) -> Path:
    path = Path(candidate["path"]).expanduser()
    real = canonical(path)
    if str(real) != candidate.get("canonical_path"):
        raise RuntimeError("canonical path changed")
    current_identity = path_identity(path)
    if current_identity != candidate.get("identity"):
        raise RuntimeError("path identity changed")
    if current_identity.get("is_symlink"):
        raise RuntimeError("target is a symlink")
    return real


def verify_boundary(candidate: dict[str, Any], path: Path) -> None:
    boundary = candidate.get("boundary", {})
    root = canonical(Path(boundary.get("approved_root", "")))
    if path == root or not is_within(path, root):
        raise RuntimeError("candidate is not strictly beneath approved root")
    root_device = int(root.stat().st_dev)
    if root_device != boundary.get("approved_root_device"):
        raise RuntimeError("approved-root device changed")
    if int(path.stat().st_dev) != root_device:
        raise RuntimeError("candidate crossed approved-root device")
    nested = mounted_descendants(path)
    if nested:
        raise RuntimeError(f"candidate contains nested mounts: {nested}")


def revalidate(candidate: dict[str, Any], processes: list[dict[str, Any]], lsof_ok: bool, codex_roots: list[dict[str, str]]) -> Path:
    if candidate.get("classification") != CLASS_SAFE:
        raise RuntimeError("candidate is not safe_now")
    if not lsof_ok:
        raise RuntimeError("open-handle inventory incomplete")
    path = verify_identity(candidate)
    verify_boundary(candidate, path)
    refs = refs_for(path, processes)
    if refs["cwd_pids"] or refs["open_handle_pids"] or codex_refs(path, codex_roots):
        raise RuntimeError("candidate acquired a live reference")
    kind = candidate.get("kind")
    if kind == "generated_artifact":
        rule = ARTIFACT_RULES.get(path.name)
        if rule is None or not project_marker(path, rule):
            raise RuntimeError("artifact ownership marker changed")
        tracked, err = contains_tracked_files(path)
        if tracked is None:
            raise RuntimeError(err or "tracked-file check failed")
        if tracked:
            raise RuntimeError("artifact now contains tracked files")
    elif kind == "known_cache":
        allowed = {str(Path(item["path"]).expanduser().resolve(strict=False)) for item in KNOWN_CACHES}
        if str(path) not in allowed:
            raise RuntimeError("path is not in known-cache allowlist")
    elif kind == "git_worktree":
        repo = Path(candidate["repository"])
        refreshed = audit_worktrees(repo, processes, lsof_ok, codex_roots)
        match = next((item for item in refreshed if item.get("canonical_path") == str(path)), None)
        if match is None or match.get("classification") != CLASS_SAFE:
            raise RuntimeError("worktree no longer classifies as safe_now")
        if match.get("git", {}).get("head") != candidate.get("git", {}).get("head"):
            raise RuntimeError("worktree HEAD changed")
    else:
        raise RuntimeError(f"executor does not support kind {kind!r}")
    return path


def apply_manifest(args: argparse.Namespace) -> int:
    if not args.execute or args.ack != ACK:
        print(f"refusing mutation: pass --execute --ack {ACK!r}", file=sys.stderr)
        return 2
    if not args.id:
        print("refusing mutation: pass at least one exact --id", file=sys.stderr)
        return 2
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA:
        raise SystemExit("unsupported or missing manifest schema")
    integrity = manifest.get("integrity", {})
    if integrity.get("algorithm") != "sha256" or integrity.get("digest") != manifest_digest(manifest):
        raise SystemExit("manifest integrity check failed; rerun audit")
    if age_minutes(manifest["generated_at"]) > args.max_age_minutes:
        raise SystemExit("manifest is stale; rerun audit")
    if args.authorization_source == "goal_authorization" and manifest.get("authorization", {}).get("mode") != "goal_authorized":
        raise SystemExit("manifest does not contain a goal_authorized scope")
    by_id = {item.get("id"): item for item in manifest.get("candidates", [])}
    if len(set(args.id)) != len(args.id) or any(item_id not in by_id for item_id in args.id):
        raise SystemExit("IDs must be unique and present in the manifest")
    selected = [by_id[item_id] for item_id in args.id]
    covered = {item.get("covered_by") for item in selected if item.get("covered_by")}
    selected_ids = {item["id"] for item in selected}
    if covered & selected_ids:
        raise SystemExit("do not select both a worktree and an overlapping artifact")
    selected_allocated = sum(int(item.get("storage", {}).get("allocated_bytes") or 0) for item in selected)
    if any(item.get("storage", {}).get("allocated_bytes") is None for item in selected):
        raise SystemExit("selected candidate has incomplete storage evidence")
    requested_ceiling = int(args.risk_ceiling_gib * 1024**3) if args.risk_ceiling_gib is not None else selected_allocated
    if requested_ceiling > selected_allocated:
        raise SystemExit("risk ceiling cannot exceed the frozen selected-candidate budget")
    risk_ceiling = requested_ceiling
    observer = observer_context()
    anchor = Path(args.volume).expanduser()
    before = volume_free(anchor)
    target = int(args.target_gib * 1024**3) if args.target_gib is not None else None
    results: list[dict[str, Any]] = []
    consumed_budget = 0
    stopped_reason = "approved_set_exhausted"
    for index, candidate in enumerate(selected):
        candidate_budget = int(candidate.get("storage", {}).get("allocated_bytes") or 0)
        if consumed_budget + candidate_budget > risk_ceiling:
            stopped_reason = "risk_ceiling_reached"
            for remaining in selected[index:]:
                results.append({"id": remaining.get("id"), "path": remaining.get("path"), "status": "not_attempted", "error": "frozen risk ceiling reached"})
            break
        processes, lsof_ok, _ = process_snapshot(set(observer["excluded_pids"]))
        codex_roots = open_codex_roots(processes)
        try:
            path = revalidate(candidate, processes, lsof_ok, codex_roots)
            if candidate["kind"] == "git_worktree":
                proc = run(["git", "-C", candidate["repository"], "worktree", "remove", "--", str(path)], timeout=600)
                if proc.returncode != 0:
                    raise RuntimeError(proc.stderr.decode(errors="replace").strip() or "git worktree remove failed")
            else:
                safe_delete_tree(path)
            if path.exists():
                raise RuntimeError("target still exists after operation")
            consumed_budget += candidate_budget
            current = volume_free(anchor)
            recovered = current["free_bytes"] - before["free_bytes"]
            results.append({"id": candidate["id"], "path": str(path), "status": "removed", "free_delta_bytes": recovered})
            if target is not None and recovered >= target:
                stopped_reason = "target_met"
                for remaining in selected[index + 1:]:
                    results.append({"id": remaining.get("id"), "path": remaining.get("path"), "status": "not_attempted", "error": "physical recovery target met"})
                break
        except Exception as exc:  # report and preserve remaining candidates
            results.append({"id": candidate.get("id"), "path": candidate.get("path"), "status": "skipped", "error": str(exc)})
    after = volume_free(anchor)
    physical_delta = after["free_bytes"] - before["free_bytes"]
    shortfall = max(0, target - max(0, physical_delta)) if target is not None else None
    report = {
        "schema": SCHEMA,
        "applied_at": now_utc(),
        "authorization_source": args.authorization_source,
        "observer": observer,
        "approved_budget": {
            "selected_ids": args.id,
            "selected_count": len(selected),
            "selected_allocated_bytes": selected_allocated,
            "risk_ceiling_bytes": risk_ceiling,
            "consumed_allocated_budget_bytes": consumed_budget,
            "target_free_delta_bytes": target,
        },
        "volume_before": before,
        "volume_after": after,
        "physical_free_delta_bytes": physical_delta,
        "shortfall_bytes": shortfall,
        "stopped_reason": stopped_reason,
        "results": results,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(item["status"] in ("removed", "not_attempted") for item in results) else 1


def self_test(_: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="filesystem-lifecycle-test-") as temp:
        root = Path(temp)
        project = root / "project"
        project.mkdir()
        (project / "package.json").write_text("{}\n", encoding="utf-8")
        generated = project / "node_modules"
        (generated / "pkg").mkdir(parents=True)
        (generated / "pkg" / "index.js").write_text("module.exports = 1;\n", encoding="utf-8")
        assert project_marker(generated, ARTIFACT_RULES["node_modules"])
        discovered, discovery_evidence = scan_artifacts([root], 4)
        assert discovery_evidence["scan_complete"]
        assert generated.resolve() in {item.resolve() for item, _ in discovered}
        ident = path_identity(generated)
        assert ident["inode"] > 0 and ident["link_count"] > 0 and not ident["is_symlink"]
        fixture_candidate = candidate_base(
            generated,
            root,
            "generated_artifact",
            "node-package-manager",
            {"level": "regenerable", "method": "package install"},
            {"driver": "filesystem", "operation": "delete_exact_tree"},
        )
        verify_boundary(fixture_candidate, generated.resolve())
        safe_delete_tree(generated)
        assert not generated.exists()
        hardlink_a = project / "hardlink-a"
        hardlink_b = project / "hardlink-b"
        hardlink_a.write_text("shared\n", encoding="utf-8")
        os.link(hardlink_a, hardlink_b)
        assert path_identity(hardlink_a)["link_count"] == 2

        generated_apply = project / "node_modules"
        (generated_apply / "pkg").mkdir(parents=True)
        (generated_apply / "pkg" / "index.js").write_text("module.exports = 2;\n", encoding="utf-8")
        apply_candidate = candidate_base(
            generated_apply,
            root,
            "generated_artifact",
            "node-package-manager",
            {"level": "regenerable", "method": "package install"},
            {"driver": "filesystem", "operation": "delete_exact_tree"},
        )
        apply_candidate["classification"] = CLASS_SAFE
        apply_manifest_data = {
            "schema": SCHEMA,
            "generated_at": now_utc(),
            "authorization": {"mode": "goal_authorized", "scope": ["temporary self-test fixture"]},
            "candidates": [apply_candidate],
        }
        apply_manifest_data["integrity"] = {"algorithm": "sha256", "digest": manifest_digest(apply_manifest_data)}
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(apply_manifest_data), encoding="utf-8")
        apply_args = argparse.Namespace(
            execute=True,
            ack=ACK,
            id=[apply_candidate["id"]],
            manifest=str(manifest_path),
            max_age_minutes=30.0,
            authorization_source="goal_authorization",
            risk_ceiling_gib=0.0,
            target_gib=None,
            volume=str(root),
        )
        with contextlib.redirect_stdout(io.StringIO()):
            assert apply_manifest(apply_args) == 0
        assert generated_apply.exists()
        apply_args.risk_ceiling_gib = None
        with contextlib.redirect_stdout(io.StringIO()):
            assert apply_manifest(apply_args) == 0
        assert not generated_apply.exists()
        sample = b"worktree /tmp/a\0HEAD abc\0branch refs/heads/main\0\0worktree /tmp/b\0HEAD def\0detached\0\0"
        parsed = parse_worktree_porcelain(sample)
        assert len(parsed) == 2 and parsed[1]["detached"] is True
        repo = root / "repo"
        linked = root / "linked"
        repo.mkdir()
        assert run(["git", "-C", str(repo), "init", "-b", "main"]).returncode == 0
        assert run(["git", "-C", str(repo), "config", "user.name", "Filesystem Lifecycle Test"]).returncode == 0
        assert run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"]).returncode == 0
        (repo / "tracked.txt").write_text("test\n", encoding="utf-8")
        assert run(["git", "-C", str(repo), "add", "tracked.txt"]).returncode == 0
        assert run(["git", "-C", str(repo), "commit", "-m", "fixture"]).returncode == 0
        assert run(["git", "-C", str(repo), "worktree", "add", "-b", "completed", str(linked)]).returncode == 0
        worktrees = audit_worktrees(repo, [], True, [])
        linked_record = next(item for item in worktrees if item.get("canonical_path") == str(linked.resolve()))
        assert linked_record["classification"] == CLASS_SAFE
        assert linked_record["git"]["representation"] == "exact_ancestor"
        assert run(["git", "-C", str(repo), "worktree", "remove", "--", str(linked)]).returncode == 0
    print("self-test passed")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    audit_parser = sub.add_parser("audit", help="read-only inventory and manifest")
    audit_parser.add_argument("--root", action="append", default=[], help="bounded root to scan for generated artifacts")
    audit_parser.add_argument("--repo", action="append", default=[], help="Git repository whose registered worktrees should be audited")
    audit_parser.add_argument("--include-known-caches", action="store_true", help="include exact allowlisted cache paths")
    audit_parser.add_argument("--max-depth", type=int, default=7)
    audit_parser.add_argument("--authorization-mode", choices=("audit_only", "goal_authorized"), default="audit_only")
    audit_parser.add_argument("--authorization-scope", action="append", default=[], help="bounded user-authorized mutation scope; required for goal_authorized")
    audit_parser.add_argument("--volume", default="/System/Volumes/Data" if sys.platform == "darwin" else "/")
    audit_parser.add_argument("--output")
    audit_parser.set_defaults(func=audit)

    apply_parser = sub.add_parser("apply", help="revalidate and remove exact approved manifest entries")
    apply_parser.add_argument("--manifest", required=True)
    apply_parser.add_argument("--id", action="append", default=[])
    apply_parser.add_argument("--authorization-source", choices=("manifest_approval", "goal_authorization"), required=True)
    apply_parser.add_argument("--execute", action="store_true")
    apply_parser.add_argument("--ack")
    apply_parser.add_argument("--max-age-minutes", type=float, default=30.0)
    apply_parser.add_argument("--target-gib", type=float)
    apply_parser.add_argument("--risk-ceiling-gib", type=float, help="optional ceiling no greater than selected allocated bytes")
    apply_parser.add_argument("--volume", default="/System/Volumes/Data" if sys.platform == "darwin" else "/")
    apply_parser.set_defaults(func=apply_manifest)

    test_parser = sub.add_parser("self-test", help="exercise parsing, discovery, identity, and deletion in a temporary fixture")
    test_parser.set_defaults(func=self_test)
    return result


def main() -> int:
    args = parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
