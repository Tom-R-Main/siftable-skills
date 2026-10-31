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
import re
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable
from fs_cache_recovery import cache_recovery, cache_children
from fs_safety import atomic_json, delete_tree, DeletionFailure, filesystem_identity, finite_number


SCHEMA = "filesystem-lifecycle/v3"
SELECTION_SCHEMA = "filesystem-lifecycle/selection-v3"
ACK = "DELETE EXACT SAFE-NOW PATHS"
CLASS_SAFE = "safe_now"
CLASS_AFTER = "safe_after_active_thread_closeout"
CLASS_RETAIN = "retain"
CLASS_UNKNOWN = "unknown"
SAFE_REPRESENTATIONS = {"exact_ancestor", "tree_equivalent", "patch_equivalent"}

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
    {"path": "~/Library/Caches/ms-playwright-mcp", "owner": "playwright", "processes": ("playwright",), "recovery": "persistent MCP browser profiles may contain unique state; inspect owner export/recovery"},
    {"path": "~/Library/Caches/node-gyp", "owner": "node-gyp", "processes": ("node", "npm",), "recovery": "node-gyp redownloads headers"},
    {"path": "~/Library/Caches/Homebrew/downloads", "owner": "homebrew", "processes": ("brew",), "recovery": "Homebrew redownloads installer archives"},
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
        "filesystem_id": filesystem_identity(real)["filesystem_id"],
        "inode": int(st.st_ino),
        "link_count": int(st.st_nlink),
        "mount_id": f"device:{int(real.stat().st_dev)}:{root}",
        "is_symlink": stat.S_ISLNK(st.st_mode),
    }


def allocated_bytes(path: Path) -> int:
    if mounted_descendants(path):
        raise RuntimeError("sizing refuses nested mounts")
    proc = run(["/usr/bin/du", "-skx", str(path)], timeout=600)
    if proc.returncode != 0 or proc.stderr.strip():
        raise RuntimeError("allocated sizing incomplete")
    return int(proc.stdout.split(None, 1)[0]) * 1024


def logical_bytes(path: Path) -> int:
    if mounted_descendants(path):
        raise RuntimeError("sizing refuses nested mounts")
    argv = ["/usr/bin/du", "-skAx", str(path)] if sys.platform == "darwin" else ["/usr/bin/du", "-skx", "--apparent-size", str(path)]
    proc = run(argv, timeout=600)
    if proc.returncode or proc.stderr.strip():
        raise RuntimeError("logical sizing incomplete")
    return int(proc.stdout.split(None, 1)[0]) * 1024


def storage_evidence(path: Path, *, allocated_only: bool = False) -> dict[str, Any]:
    return {
        "logical_bytes": None if allocated_only else logical_bytes(path),
        "allocated_bytes": allocated_bytes(path),
        "estimated_reclaimability": "unknown",
    }


def volume_free(path: Path) -> dict[str, Any]:
    anchor = canonical(path)
    usage = shutil.disk_usage(anchor)
    return {"anchor": str(anchor), "total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free, "filesystem": filesystem_identity(anchor)}


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
    real = path.resolve(strict=True)
    paths = []
    def unescape(value):
        return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)
    if sys.platform.startswith("linux"):
        for line in Path("/proc/self/mountinfo").read_text().splitlines():
            fields = line.split()
            if len(fields) < 10 or "-" not in fields:
                raise RuntimeError("incomplete mount inventory")
            paths.append(unescape(fields[4]))
    else:
        proc = run(["mount"], timeout=30)
        if proc.returncode or proc.stderr.strip() or not proc.stdout.strip():
            raise RuntimeError("mount inventory incomplete")
        for line in proc.stdout.decode(errors="strict").splitlines():
            if " on " not in line or " (" not in line:
                raise RuntimeError("unrecognized mount inventory record")
            paths.append(unescape(line.split(" on ", 1)[1].rsplit(" (", 1)[0]))
    result = []
    for value in paths:
        mount = Path(value).resolve(strict=False)
        if mount != real and is_within(mount, real):
            result.append(str(mount))
    return sorted(set(result))


def process_snapshot(exclude_pids: set[int] | None = None, *, include_test_runtimes: bool = False) -> tuple[list[dict[str, Any]], bool, str | None]:
    if shutil.which("lsof") is None:
        return [], False, "lsof unavailable"
    try:
        proc = run(["lsof", "-nP", "-F0pcfn"], timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return [], False, "lsof unavailable or timed out"
    if proc.returncode != 0 or proc.stderr.strip() or not proc.stdout.strip():
        return [], False, proc.stderr.decode(errors="replace").strip() or "lsof failed"
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    fd = ""
    if b"\0" not in proc.stdout:
        return [], False, "lsof field delimiters unavailable"
    for raw in proc.stdout.decode(errors="surrogateescape").split("\0"):
        raw = raw.lstrip("\n")
        if not raw:
            continue
        tag, value = raw[0], raw[1:]
        if tag == "p":
            if not value.isdigit():
                return [], False, "malformed lsof process record"
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
    if include_test_runtimes:
        # Python closes source files after importing them. Retain its environment
        # from launch arguments as well as mapped files/CWDs; never log raw args.
        ps=run(['ps','-Aww','-o','pid=,args='],timeout=30)
        if ps.returncode or ps.stderr.strip() or not ps.stdout.strip():
            return [],False,'test-runtime process argument observation incomplete'
        by_pid={r['pid']:r for r in records}
        for line in ps.stdout.decode(errors='strict').splitlines():
            fields=line.strip().split(None,1)
            if not fields or not fields[0].isdigit():return [],False,'malformed test-runtime process observation'
            pid=int(fields[0])
            if pid in excluded or len(fields)<2:continue
            paths=re.findall(r'(/[^\s]+/output/[^/\s]+/(?:venv|empty-cache))(?=/|\s|$)',fields[1])
            if paths:
                record=by_pid.setdefault(pid,{'pid':pid,'command':'test-runtime-reference','cwd':[],'paths':[]})
                record['paths'].extend(paths)
        records=list(by_pid.values())
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
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("active Codex session metadata unavailable") from exc
    return results


def codex_refs(path: Path, roots: list[dict[str, str]], *, owner_root: Path | None = None) -> list[str]:
    matched: list[str] = []
    for item in roots:
        root = Path(item["root"])
        if owner_root is not None:
            referenced = is_within(root, owner_root)
        else:
            referenced = is_within(path, root) or is_within(root, path)
        if referenced:
            matched.append(item["root"])
    return sorted(set(matched))


def process_names(processes: list[dict[str, Any]]) -> set[str]:
    return {str(p["command"]).lower() for p in processes if p.get("command")}


def git_stdout(path: Path, args: list[str]) -> tuple[int, bytes, str]:
    proc = run(["git", "-C", str(path), *args])
    return proc.returncode, proc.stdout, proc.stderr.decode(errors="replace").strip()


def git_root(path: Path) -> Path | None:
    code, out, err = git_stdout(path, ["rev-parse", "--show-toplevel"])
    if code != 0:
        if "not a git repository" in err.lower() and not any((ancestor / ".git").exists() for ancestor in (path, *path.parents)):
            return None
        raise RuntimeError("Git repository discovery incomplete")
    try:
        return Path(out.decode().strip()).resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("Git root unavailable") from exc


def contains_tracked_files(path: Path) -> tuple[bool | None, str | None]:
    try:
        root = git_root(path.parent)
    except RuntimeError as exc:
        return None, str(exc)
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
    if rule['owner'] == 'node-package-manager':
        from fs_recovery import npm_installation, Unqualified
        try:
            npm_installation(path)
            return True
        except (OSError, Unqualified):
            return False
    parent = path.parent
    return any((parent / marker).exists() for marker in rule["markers"])


def artifact_rule(path: Path) -> dict[str, Any] | None:
    if not path.name.startswith('.') and (path.parent.name == 'node_modules' or (path.parent.name.startswith('@') and path.parent.parent.name == 'node_modules')):
        return ARTIFACT_RULES['node_modules']
    return ARTIFACT_RULES.get(path.name)


def npm_live(candidate, processes, owner_root):
    install = candidate.get('recovery', {}).get('npm_installation_root')
    if not install:
        return False
    refs = refs_for(Path(install), processes)
    # A consumer of any package can import another package later. A package-unit
    # cleanup therefore protects the entire installation, plus owner CWDs.
    cwd_refs = refs_for(owner_root, processes)['cwd_pids']
    return bool(refs['cwd_pids'] or refs['open_handle_pids'] or cwd_refs)


def artifact_recovery(path: Path, rule: dict[str, Any]) -> dict[str, Any]:
    from fs_recovery import artifact_recovery as inspect_recovery
    if mounted_descendants(path):
        return {"verified": False, "level": "none_or_unknown", "method": rule["rebuild"], "reason": "candidate contains a nested mount"}
    return inspect_recovery(path, rule)


def validate_envelope(manifest, selected, volume, target=None):
    envelope = manifest["authorization"]["envelope"]
    actual = filesystem_identity(volume)
    if actual != envelope.get("filesystem"):
        raise ValueError("target filesystem does not match frozen authorization")
    allowed = envelope.get("kinds", [])
    roots = [Path(value) for value in envelope.get("roots", [])]
    exclusions = [Path(value) for value in envelope.get("exclusions", [])]
    if target is not None and envelope.get("target_free_delta_bytes") is not None and target > envelope["target_free_delta_bytes"]:
        raise ValueError("target exceeds frozen authorization")
    for candidate in selected:
        path = Path(candidate["canonical_path"])
        if candidate["kind"] not in allowed or not any(path != root and is_within(path, root) for root in roots):
            raise ValueError("candidate outside authorization roots or kinds")
        if any(is_within(path, item) or is_within(item, path) for item in exclusions):
            raise ValueError("candidate overlaps authorization exclusion")
        if (candidate.get("identity", {}).get("device") != actual["device"]
                or candidate.get("identity", {}).get("filesystem_id") != actual["filesystem_id"]):
            raise ValueError("candidate is on a different target filesystem")
        finite_number(candidate.get("storage", {}).get("allocated_bytes"), "allocated bytes")
    for i, candidate in enumerate(selected):
        for other in selected[i + 1:]:
            if candidates_overlap(candidate, other):
                raise ValueError("selected candidates overlap")
    return envelope


def scan_artifacts(roots: Iterable[Path], max_depth: int, npm_package_units: bool = False, npm_package_names: set[str] | None = None) -> tuple[list[tuple[Path, Path]], dict[str, Any]]:
    found: list[tuple[Path, Path]] = []
    errors: list[dict[str, str]] = []
    excluded_mounts: list[str] = []
    skip_names = {".git", ".svn", ".hg", "Library", "Documents", "Downloads", "Desktop", "Pictures", "Movies", "Music"}
    for raw_root in roots:
        root = canonical(raw_root)
        root_device = root.stat().st_dev
        nested_mounts = {Path(item) for item in mounted_descendants(root)}
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
                if child in nested_mounts:
                    excluded_mounts.append(str(child))
                    continue
                try:
                    if entry.stat(follow_symlinks=False).st_dev != root_device:
                        excluded_mounts.append(str(child))
                        continue
                except OSError as exc:
                    errors.append({"path": str(child), "error": str(exc)})
                    continue
                if entry.name in ARTIFACT_RULES:
                    found.append((child, root))
                    if npm_package_units and entry.name == 'node_modules':
                        # Inventory exact top-level package/scope directories;
                        # each still needs lock ownership, content screening,
                        # recovery and whole-installation liveness qualification.
                        try:
                            with os.scandir(child) as packages:
                                for package in packages:
                                    if Path(package.path) in nested_mounts:
                                        excluded_mounts.append(package.path)
                                        continue
                                    if not package.name.startswith('.') and (not npm_package_names or package.name in npm_package_names) and package.is_dir(follow_symlinks=False) and package.stat(follow_symlinks=False).st_dev == root_device:
                                        found.append((Path(package.path), root))
                                        if package.name.startswith('@'):
                                            with os.scandir(package.path) as scoped:
                                                for member in scoped:
                                                    if Path(member.path) in nested_mounts:
                                                        excluded_mounts.append(member.path)
                                                        continue
                                                    if not member.name.startswith('.') and member.is_dir(follow_symlinks=False) and member.stat(follow_symlinks=False).st_dev == root_device:
                                                        found.append((Path(member.path), root))
                        except OSError as exc:
                            errors.append({'path': str(child), 'error': str(exc)})
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


def candidate_base(
    path: Path,
    approved_root: Path,
    kind: str,
    owner: str,
    recovery: dict[str, str],
    action: dict[str, Any],
    *,
    measure_storage: bool = True,
) -> dict[str, Any]:
    real = canonical(path)
    root = canonical(approved_root)
    identity = path_identity(path)
    errors: list[str] = []
    unexpected_mounts: list[str] = []
    if real == root or not is_within(real, root):
        errors.append("candidate is not strictly beneath approved root")
    try:
        unexpected_mounts = mounted_descendants(real)
        unexpected_mounts = sorted(set(unexpected_mounts + [mount for mount in mounted_descendants(root) if is_within(real, Path(mount))]))
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
        "storage": storage_evidence(real) if measure_storage else {
            "logical_bytes": None,
            "allocated_bytes": None,
            "estimated_reclaimability": "unknown",
        },
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


def classify_path_candidate(
    candidate: dict[str, Any],
    processes: list[dict[str, Any]],
    lsof_ok: bool,
    roots: list[dict[str, str]],
    *,
    tracked: bool | None = False,
    tracked_error: str | None = None,
    owner_active: bool = False,
    owner_root: Path | None = None,
) -> None:
    path = Path(candidate["canonical_path"])
    refs = refs_for(path, processes)
    refs["codex_session_roots"] = codex_refs(path, roots, owner_root=owner_root)
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
    elif candidate.get("recovery", {}).get("verified") is not True:
        candidate["classification"] = CLASS_UNKNOWN
        candidate["reasons"].append(candidate.get("recovery", {}).get("reason", "adapter recovery evidence is incomplete"))
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
        rule = artifact_rule(path)
        try:
            candidate = candidate_base(
                path,
                approved_root,
                "generated_artifact",
                rule["owner"],
                artifact_recovery(path, rule),
                {"driver": "filesystem", "operation": "delete_exact_tree"},
                measure_storage=False,
            )
            candidate["preconditions"].extend(("recognized_artifact_marker", "contains_no_tracked_files"))
            install = candidate['recovery'].get('npm_installation_root')
            owner_parent = Path(install).parent if install else path.parent
            owner_root = git_root(owner_parent) or owner_parent.resolve(strict=True)
            candidate["owner_root"] = str(owner_root)
            if not project_marker(path, rule):
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append("recognized basename but project marker is missing")
            else:
                tracked, err = contains_tracked_files(path)
                classify_path_candidate(candidate, processes, lsof_ok, codex_roots, tracked=tracked, tracked_error=err, owner_root=owner_root, owner_active=npm_live(candidate, processes, owner_root))
            candidates.append(candidate)
        except (OSError, RuntimeError) as exc:
            candidates.append(unknown_candidate(path, approved_root, "generated_artifact", rule["owner"], str(exc)))
    return candidates


def audit_target_artifacts(
    discovered: list[tuple[Path, Path]],
    processes: list[dict[str, Any]],
    lsof_ok: bool,
    codex_roots: list[dict[str, str]],
    required_allocated_bytes: int,
    max_candidates: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Assess shallow generated artifacts until a safe allocated-byte budget exists."""
    ordered = sorted(
        discovered,
        key=lambda item: (
            len(item[0].relative_to(item[1]).parts),
            str(item[0]),
        ),
    )
    candidates: list[dict[str, Any]] = []
    measured_bytes = 0
    measured_paths = []
    for path, approved_root in ordered:
        if max_candidates is not None and len(candidates) >= max_candidates:
            break
        if any(is_within(path, parent) for parent in measured_paths):
            continue
        candidate = audit_artifacts([(path, approved_root)], processes, lsof_ok, codex_roots)[0]
        candidates.append(candidate)
        if candidate.get("classification") != CLASS_SAFE:
            continue
        print(f"[audit:assess {len(candidates)}] sizing {candidate.get('path')}", file=sys.stderr, flush=True)
        try:
            candidate["storage"] = storage_evidence(Path(candidate["canonical_path"]), allocated_only=True)
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            candidate["classification"] = CLASS_UNKNOWN
            candidate["evidence"]["scan_complete"] = False
            candidate["evidence"]["errors"].append(str(exc))
            candidate["reasons"].append("storage measurement failed")
            continue
        measured_bytes += int(candidate["storage"]["allocated_bytes"] or 0)
        measured_paths.append(path)
        if measured_bytes >= required_allocated_bytes:
            break
    return candidates, {
        "classification_mode": "target_limited",
        "discovered_candidate_count": len(ordered),
        "assessed_candidate_count": len(candidates),
        "deferred_unassessed_candidate_count": len(ordered) - len(candidates),
    }


def iter_cache_rules():
    for rule in KNOWN_CACHES:
        path = Path(rule["path"]).expanduser()
        children = []
        try:
            if path.is_dir() and not path.is_symlink():
                children = list(cache_children(path, rule))
        except (OSError, ValueError, RuntimeError):
            yield {**rule, "discovery_error": "cache child inventory incomplete; inspect this owner root"}
            continue
        yield rule
        yield from children


def audit_caches(processes: list[dict[str, Any]], lsof_ok: bool, codex_roots: list[dict[str, str]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    names = process_names(processes)
    for rule in iter_cache_rules():
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
                ({"verified": False, "level": "none_or_unknown", "method": rule["recovery"], "reason": rule["discovery_error"]} if rule.get("discovery_error") else cache_recovery(path, rule)),
                {"driver": "filesystem", "operation": "delete_exact_tree"},
                measure_storage=False,
            )
            candidate["preconditions"].append("known_cache_allowlist_match")
            active = any(any(token in name for name in names) for token in rule["processes"])
            tracked, tracked_error = contains_tracked_files(path)
            classify_path_candidate(candidate, processes, lsof_ok, codex_roots, owner_active=active, tracked=tracked, tracked_error=tracked_error)
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
                measure_storage=False,
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
            refs["codex_session_roots"] = codex_refs(
                Path(candidate["canonical_path"]),
                codex_roots,
                owner_root=Path(candidate["canonical_path"]),
            )
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
            status_code, status_out, status_err = git_stdout(Path(candidate["canonical_path"]), ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"])
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
            if base is None:
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append("no main/master base ref found")
            elif rep == "unknown":
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append("Git representation proof could not be completed")
            elif rep == "unique":
                candidate["classification"] = CLASS_RETAIN
                candidate["reasons"].append("clean checkout contains a unique patch relative to base")
            elif not entry.get("branch") and rep != "exact_ancestor":
                candidate["classification"] = CLASS_RETAIN
                candidate["reasons"].append("detached commit history is not retained by protected base")
            elif not lsof_ok:
                candidate["classification"] = CLASS_UNKNOWN
                candidate["reasons"].append("open-handle inventory incomplete")
            elif refs["cwd_pids"] or refs["open_handle_pids"] or refs["codex_session_roots"]:
                candidate["classification"] = CLASS_AFTER
                candidate["reasons"].append("represented checkout is currently referenced")
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


DEFAULT_KIND_ORDER = ("known_cache", "generated_artifact", "git_worktree")


def candidate_depth(candidate: dict[str, Any]) -> int:
    try:
        path = Path(candidate["canonical_path"])
        root = Path(candidate["boundary"]["approved_root"])
        return len(path.relative_to(root).parts)
    except (KeyError, TypeError, ValueError):
        return 1_000_000


def ordered_candidates(candidates: Iterable[dict[str, Any]], preferred_kinds: list[str] | None = None) -> list[dict[str, Any]]:
    preferred = list(dict.fromkeys(preferred_kinds or []))
    kind_order = preferred + [kind for kind in DEFAULT_KIND_ORDER if kind not in preferred]
    rank = {kind: index for index, kind in enumerate(kind_order)}
    return sorted(
        candidates,
        key=lambda item: (
            rank.get(str(item.get("kind")), len(rank)),
            candidate_depth(item),
            str(item.get("canonical_path") or item.get("path") or ""),
        ),
    )


def candidates_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get("covered_by") == right.get("id") or right.get("covered_by") == left.get("id"):
        return True
    left_path = left.get("canonical_path")
    right_path = right.get("canonical_path")
    if not isinstance(left_path, str) or not isinstance(right_path, str):
        return False
    a, b = Path(left_path), Path(right_path)
    return is_within(a, b) or is_within(b, a)


def target_budget_bytes(target_bytes: int, headroom_percent: float) -> int:
    if target_bytes < 0:
        raise ValueError("target must be non-negative")
    if headroom_percent < 0:
        raise ValueError("headroom percent must be non-negative")
    return int(target_bytes * (1.0 + headroom_percent / 100.0))


def size_candidates(
    candidates: list[dict[str, Any]],
    *,
    target_bytes: int | None,
    headroom_percent: float,
    preferred_kinds: list[str] | None,
    included_kinds: set[str] | None,
) -> dict[str, Any]:
    """Measure eligible candidates, stopping once a target-plus-headroom budget exists."""
    target_budget = target_budget_bytes(target_bytes, headroom_percent) if target_bytes is not None else None
    eligible_classes = {CLASS_SAFE} if target_budget is not None else {CLASS_SAFE, CLASS_AFTER, CLASS_UNKNOWN, CLASS_RETAIN}
    eligible = [
        item for item in candidates
        if item.get("classification") in eligible_classes
        and (not included_kinds or item.get("kind") in included_kinds)
    ]
    chosen: list[dict[str, Any]] = []
    measured_bytes = 0
    started = time.monotonic()
    for candidate in ordered_candidates(eligible, preferred_kinds):
        if target_budget is not None and any(candidates_overlap(candidate, prior) for prior in chosen):
            candidate["storage_deferred"] = "overlaps a higher-priority target candidate"
            continue
        ordinal = len(chosen) + 1
        if candidate.get("storage", {}).get("allocated_bytes") is None:
            print(f"[audit:size {ordinal}] {candidate.get('path')}", file=sys.stderr, flush=True)
            try:
                candidate["storage"] = storage_evidence(
                    Path(candidate["canonical_path"]),
                    allocated_only=target_budget is not None,
                )
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                candidate["classification"] = CLASS_UNKNOWN
                candidate["evidence"]["scan_complete"] = False
                candidate["evidence"]["errors"].append(str(exc))
                candidate["reasons"].append("storage measurement failed")
                continue
        chosen.append(candidate)
        measured_bytes += int(candidate["storage"]["allocated_bytes"] or 0)
        if target_budget is not None and measured_bytes >= target_budget:
            break
    measured_ids = {item["id"] for item in chosen}
    if target_budget is not None:
        for candidate in eligible:
            if candidate["id"] not in measured_ids and "storage_deferred" not in candidate:
                candidate["storage_deferred"] = "target-plus-headroom budget already satisfied"
    return {
        "mode": "target_limited" if target_budget is not None else "full",
        "target_free_delta_bytes": target_bytes,
        "headroom_percent": headroom_percent if target_budget is not None else None,
        "preferred_kinds": list(preferred_kinds or []),
        "included_kinds": sorted(included_kinds) if included_kinds else [],
        "required_allocated_budget_bytes": target_budget,
        "measured_allocated_bytes": measured_bytes,
        "measured_candidate_ids": [item["id"] for item in chosen],
        "budget_status": (
            "not_applicable" if target_budget is None
            else "budget_met" if measured_bytes >= target_budget
            else "insufficient_safe_budget"
        ),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def select_candidates(
    candidates: list[dict[str, Any]],
    *,
    target_bytes: int,
    headroom_percent: float,
    preferred_kinds: list[str] | None,
    included_kinds: set[str] | None,
) -> tuple[list[dict[str, Any]], int, int]:
    required = target_budget_bytes(target_bytes, headroom_percent)
    eligible = [
        item for item in candidates
        if item.get("classification") == CLASS_SAFE
        and item.get("storage", {}).get("allocated_bytes") is not None
        and (not included_kinds or item.get("kind") in included_kinds)
    ]
    selected: list[dict[str, Any]] = []
    allocated = 0
    for candidate in ordered_candidates(eligible, preferred_kinds):
        if any(candidates_overlap(candidate, prior) for prior in selected):
            continue
        selected.append(candidate)
        allocated += int(candidate["storage"]["allocated_bytes"] or 0)
        if allocated >= required:
            break
    return selected, allocated, required


def audit(args: argparse.Namespace) -> int:
    started = time.monotonic()
    if args.target_gib is not None:
        finite_number(args.target_gib, "target", minimum=0.000001)
    finite_number(args.headroom_percent, "headroom")
    if args.target_gib is not None and args.target_gib <= 0:
        raise SystemExit("--target-gib must be positive")
    if args.headroom_percent < 0:
        raise SystemExit("--headroom-percent must be non-negative")
    observer = observer_context()
    roots = [canonical(Path(value).expanduser()) for value in args.root]
    protected = [Path("/"), Path.home(), Path.home()/".ssh", Path.home()/".aws", Path.home()/".gnupg", Path.home()/"Library/Keychains",
                 Path.home()/"Documents", Path.home()/"Downloads", Path.home()/"Desktop", Path.home()/"Pictures", Path.home()/"Music", Path.home()/"Movies", Path.home()/"Library/Mail", Path.home()/"Library/Messages"]
    if any(root == item or (item.name in (".ssh", ".aws", ".gnupg", "Keychains", "Mail", "Messages") and is_within(root, item)) for root in roots for item in protected):
        raise ValueError("discovery requires bounded project roots; protected roots are excluded")
    repos = [canonical(Path(value).expanduser()) for value in args.repo]
    included_kinds = set(args.kind) if args.kind else None
    if args.authorization_mode == "goal_authorized" and not args.authorization_scope:
        raise SystemExit("goal_authorized requires at least one --authorization-scope")
    target = int(args.target_gib * 1024**3) if args.target_gib is not None else None
    assessment_limit = getattr(args, 'max_artifact_candidates', None)
    if assessment_limit is not None and (assessment_limit < 1 or target is None or included_kinds != {'generated_artifact'}):
        raise ValueError('--max-artifact-candidates requires a positive limit, --target-gib and --kind generated_artifact only')
    required_target_budget = target_budget_bytes(target, args.headroom_percent) if target is not None else None
    scan_generated = included_kinds is None or "generated_artifact" in included_kinds
    package_names = set(getattr(args,'npm_package_name',[]) or [])
    if package_names and not getattr(args,'npm_package_units',False):
        raise ValueError('--npm-package-name requires --npm-package-units')
    if any(not name or name.startswith('.') or '/' in name or '\\' in name for name in package_names):
        raise ValueError('npm package names must be exact top-level package or scope directory names')
    discovered, discovery_evidence = scan_artifacts(roots, args.max_depth, getattr(args,'npm_package_units',False), package_names) if roots and scan_generated else ([], {"scan_complete": True, "errors": [], "excluded_mounts": [], "stay_on_device": True})
    anchor = Path(args.volume).expanduser()
    filesystem = filesystem_identity(anchor)
    exclusions = [Path(value).expanduser().resolve(strict=False) for value in getattr(args, "exclude", [])]
    discovered = [(path, root) for path, root in discovered if path.stat().st_dev == filesystem["device"] and not any(is_within(path, value) or is_within(value, path) for value in exclusions)]
    processes, lsof_ok, lsof_error = process_snapshot(set(observer["excluded_pids"]))
    liveness_observed_at = now_utc()
    codex_roots = open_codex_roots(processes)
    candidates: list[dict[str, Any]] = []
    discovery_planning = {
        "classification_mode": "full",
        "discovered_candidate_count": len(discovered),
        "assessed_candidate_count": len(discovered),
        "deferred_unassessed_candidate_count": 0,
    }
    generated_only_fast_path = target is not None and included_kinds == {"generated_artifact"}
    if discovered and generated_only_fast_path:
        candidates, discovery_planning = audit_target_artifacts(
            discovered,
            processes,
            lsof_ok,
            codex_roots,
            int(required_target_budget or 0),
            max_candidates=assessment_limit,
        )
    elif discovered:
        candidates.extend(audit_artifacts(discovered, processes, lsof_ok, codex_roots))
    if args.include_known_caches and (included_kinds is None or "known_cache" in included_kinds):
        candidates.extend(audit_caches(processes, lsof_ok, codex_roots))
    if included_kinds is None or "git_worktree" in included_kinds:
        for repo in repos:
            candidates.extend(audit_worktrees(repo, processes, lsof_ok, codex_roots))
    add_overlap(candidates)
    anchor = Path(args.volume).expanduser()
    exclusions = [str(Path(value).expanduser().resolve(strict=False)) for value in getattr(args, "exclude", [])]
    authorized_roots = {str(root) for root in roots}
    authorized_roots.update(item["boundary"]["approved_root"] for item in candidates if item["kind"] == "git_worktree" and item.get("repository") in {str(repo) for repo in repos})
    if args.include_known_caches:
        authorized_roots.update(str(Path(rule["path"]).expanduser().parent.resolve(strict=False)) for rule in KNOWN_CACHES)
    filesystem = filesystem_identity(anchor)
    for candidate in candidates:
        path = Path(candidate["canonical_path"])
        if candidate.get("identity", {}).get("device") != filesystem["device"] or candidate.get("identity", {}).get("filesystem_id") != filesystem["filesystem_id"] or any(is_within(path, Path(value)) or is_within(Path(value), path) for value in exclusions):
            candidate["classification"] = CLASS_UNKNOWN
            candidate["reasons"].append("outside target filesystem or overlaps exclusion")
    planning = size_candidates(
        candidates,
        target_bytes=target,
        headroom_percent=args.headroom_percent,
        preferred_kinds=args.prefer_kind,
        included_kinds=included_kinds,
    )
    envelope = {"roots": sorted(authorized_roots), "kinds": sorted(included_kinds or DEFAULT_KIND_ORDER), "exclusions": exclusions,
                "filesystem": filesystem, "volume": str(canonical(anchor)), "target_free_delta_bytes": target,
                "risk_ceiling_bytes": sum(int(item.get("storage", {}).get("allocated_bytes") or 0) for item in candidates if item["classification"] == CLASS_SAFE)}
    manifest = {
        "schema": SCHEMA,
        "generated_at": now_utc(),
        "mode": "audit",
        "authorization": {"mode": args.authorization_mode, "scope": args.authorization_scope, "envelope": envelope},
        "scope": {
            "roots": [str(p) for p in roots],
            "repositories": [str(p) for p in repos],
            "max_depth": args.max_depth,
            "stay_on_device": True,
            "included_kinds": sorted(included_kinds) if included_kinds else list(DEFAULT_KIND_ORDER),
        },
        "planning": planning,
        "evidence": {
            "observer": observer,
            "discovery": discovery_evidence,
            "candidate_assessment": discovery_planning,
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
        atomic_json(Path(args.output), manifest)
        print(
            f"wrote {len(candidates)} candidates to {args.output} in {time.monotonic() - started:.2f}s "
            f"({planning['budget_status']}, {planning['measured_allocated_bytes'] / 1024**3:.2f} GiB measured)"
        )
    else:
        print(output)
    return 0


def age_minutes(timestamp: str) -> float:
    created = dt.datetime.fromisoformat(timestamp)
    if created.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    age = (dt.datetime.now(dt.timezone.utc) - created).total_seconds() / 60.0
    if age < 0:
        raise ValueError("future timestamp")
    return age


def load_valid_manifest(path: str, max_age_minutes: float) -> dict[str, Any]:
    finite_number(max_age_minutes, "max age", minimum=0.001)
    manifest = json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ValueError("unsupported manifest; regenerate a v3 audit before mutation")
    integrity = manifest.get("integrity", {})
    if integrity.get("algorithm") != "sha256" or integrity.get("digest") != manifest_digest(manifest):
        raise ValueError("manifest checksum mismatch; rerun audit")
    if age_minutes(manifest["generated_at"]) > max_age_minutes:
        raise ValueError("manifest is stale; rerun audit")
    if not isinstance(manifest.get("candidates"), list) or not isinstance(manifest.get("authorization", {}).get("envelope"), dict):
        raise ValueError("missing structured scope")
    ids = [item["id"] for item in manifest["candidates"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate candidate IDs")
    return manifest


def select_manifest(args: argparse.Namespace) -> int:
    manifest = load_valid_manifest(args.manifest, args.max_age_minutes)
    planning = manifest.get("planning", {})
    if args.target_gib is not None:
        target = int(finite_number(args.target_gib, "target", minimum=0.000001) * 1024**3)
    else:
        target = planning.get("target_free_delta_bytes")
    if not isinstance(target, int) or target <= 0:
        raise SystemExit("selection requires --target-gib or a positive audit target")
    bound_target = manifest["authorization"]["envelope"].get("target_free_delta_bytes")
    if bound_target is not None and target > bound_target:
        raise ValueError("selection cannot increase authorized target")
    headroom = args.headroom_percent
    if headroom is not None:
        finite_number(headroom, "headroom")
    if headroom is None:
        recorded_headroom = planning.get("headroom_percent")
        headroom = float(recorded_headroom) if recorded_headroom is not None else 25.0
    preferred_kinds = args.prefer_kind or list(planning.get("preferred_kinds") or [])
    recorded_kinds = set(planning.get("included_kinds") or [])
    included_kinds = set(args.kind) if args.kind else (recorded_kinds or None)
    selected, allocated, required = select_candidates(
        manifest.get("candidates", []),
        target_bytes=target,
        headroom_percent=headroom,
        preferred_kinds=preferred_kinds,
        included_kinds=included_kinds,
    )
    validate_envelope(manifest, selected, Path(manifest["authorization"]["envelope"]["volume"]), target)
    selection = {
        "schema": SELECTION_SCHEMA,
        "filesystem": manifest["authorization"]["envelope"]["filesystem"],
        "generated_at": now_utc(),
        "manifest": {
            "path": str(Path(args.manifest).expanduser().resolve(strict=True)),
            "digest": manifest["integrity"]["digest"],
        },
        "target_free_delta_bytes": target,
        "headroom_percent": headroom,
        "required_allocated_budget_bytes": required,
        "selected_allocated_bytes": allocated,
        "selected_ids": [item["id"] for item in selected],
        "selected": [
            {
                "id": item["id"],
                "path": item["path"],
                "kind": item["kind"],
                "allocated_bytes": item["storage"]["allocated_bytes"],
                "recovery": item.get("recovery"),
            }
            for item in selected
        ],
        "status": "budget_met" if allocated >= required else "insufficient_safe_budget",
    }
    selection["integrity"] = {"algorithm": "sha256", "digest": manifest_digest(selection)}
    output = json.dumps(selection, indent=2, sort_keys=True)
    if args.output:
        atomic_json(Path(args.output), selection)
        print(
            f"wrote {len(selected)} exact non-overlapping IDs to {args.output} "
            f"({allocated / 1024**3:.2f}/{required / 1024**3:.2f} GiB allocated budget)"
        )
    else:
        print(output)
    return 0 if allocated >= required else 1


def safe_delete_tree(path: Path, *, progress: Any | None = None, heartbeat_seconds: float = 5.0, expected_identity=None):
    if mounted_descendants(path):
        raise RuntimeError("deletion refuses nested mounts")
    return delete_tree(path, expected_identity=expected_identity, progress=progress, heartbeat_seconds=heartbeat_seconds)


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
    if any(is_within(path, Path(mount)) for mount in mounted_descendants(root)):
        raise RuntimeError('candidate is at or beneath a nested mount in its approved root')
    nested = mounted_descendants(path)
    if nested:
        raise RuntimeError(f"candidate contains nested mounts: {nested}")


def revalidate_worktree(candidate: dict[str, Any], path: Path) -> None:
    repo = canonical(Path(candidate["repository"]))
    code, out, err = git_stdout(repo, ["worktree", "list", "--porcelain", "-z"])
    if code != 0:
        raise RuntimeError(err or "git worktree list failed")
    entries = parse_worktree_porcelain(out)
    match: tuple[int, dict[str, Any]] | None = None
    for index, entry in enumerate(entries):
        entry_path = Path(entry["path"]).resolve(strict=False)
        if entry_path == path:
            match = (index, entry)
            break
    if match is None:
        raise RuntimeError("worktree is no longer registered")
    index, entry = match
    if index == 0 or path == repo:
        raise RuntimeError("refusing to remove the main worktree")
    if entry.get("locked"):
        raise RuntimeError("worktree is now locked")
    expected_git = candidate.get("git", {})
    head = str(entry.get("HEAD", entry.get("head", "")))
    if not head or head != expected_git.get("head"):
        raise RuntimeError("worktree HEAD changed")
    if entry.get("branch") != expected_git.get("branch"):
        raise RuntimeError("worktree branch or detached state changed")
    status_code, status_out, status_err = git_stdout(path, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored"])
    if status_code != 0:
        raise RuntimeError(status_err or "git status failed")
    if status_out:
        raise RuntimeError("worktree now contains tracked or untracked changes")
    base = expected_git.get("base_ref")
    if not isinstance(base, str) or not base:
        raise RuntimeError("worktree has no frozen protected base")
    rep = representation(repo, head, base)
    if rep not in SAFE_REPRESENTATIONS or (not entry.get("branch") and rep != "exact_ancestor"):
        raise RuntimeError(f"worktree history is no longer retained: {rep}")


def revalidate_static(candidate: dict[str, Any]) -> Path:
    if candidate.get("classification") != CLASS_SAFE:
        raise RuntimeError("candidate is not safe_now")
    path = verify_identity(candidate)
    verify_boundary(candidate, path)
    kind = candidate.get("kind")
    if kind == "generated_artifact":
        rule = artifact_rule(path)
        if rule is None or not project_marker(path, rule):
            raise RuntimeError("artifact ownership marker changed")
        recovery = artifact_recovery(path, rule)
        if not recovery.get("verified") or recovery != candidate.get("recovery"):
            raise RuntimeError("artifact recovery evidence missing or changed")
        tracked, err = contains_tracked_files(path)
        if tracked is None:
            raise RuntimeError(err or "tracked-file check failed")
        if tracked:
            raise RuntimeError("artifact now contains tracked files")
    elif kind == "known_cache":
        rule = next((item for item in iter_cache_rules() if Path(item["path"]).expanduser().resolve(strict=False) == path), None)
        if rule is None:
            raise RuntimeError("cache owner rule missing")
        recovery = cache_recovery(path, rule)
        if not recovery.get("verified") or recovery != candidate.get("recovery"):
            raise RuntimeError("cache recovery evidence missing or changed")
        tracked, error = contains_tracked_files(path)
        if tracked is not False:
            raise RuntimeError(error or "cache now contains Git-tracked state")
    elif kind == "git_worktree":
        revalidate_worktree(candidate, path)
    else:
        raise RuntimeError(f"executor does not support kind {kind!r}")
    return path


def revalidate_liveness(candidate: dict[str, Any], path: Path, processes: list[dict[str, Any]], lsof_ok: bool, codex_roots: list[dict[str, str]]) -> None:
    if not lsof_ok:
        raise RuntimeError("open-handle inventory incomplete")
    refs = refs_for(path, processes)
    owner_root: Path | None = None
    if candidate.get("kind") == "known_cache":
        rule = next((item for item in iter_cache_rules() if Path(item["path"]).expanduser().resolve(strict=False) == path), None)
        if rule is None or any(token in name for name in process_names(processes) for token in rule["processes"]):
            raise RuntimeError("cache owner is active or unknown")
    if candidate.get("kind") == "git_worktree":
        owner_root = path
    elif candidate.get("kind") == "generated_artifact" and candidate.get("owner_root"):
        owner_root = Path(candidate["owner_root"])
        if not is_within(path, owner_root):
            raise RuntimeError("generated-artifact owner root changed")
        if npm_live(candidate, processes, owner_root):
            raise RuntimeError('dependency environment has a live consumer')
    if refs["cwd_pids"] or refs["open_handle_pids"] or codex_refs(path, codex_roots, owner_root=owner_root):
        raise RuntimeError("candidate acquired a live reference")


def load_selection(path: str, manifest_path: str, manifest: dict[str, Any], max_age_minutes: float) -> dict[str, Any]:
    selection = json.loads(Path(path).read_text(encoding="utf-8"))
    if selection.get("schema") != SELECTION_SCHEMA:
        raise SystemExit("unsupported or missing selection schema")
    integrity = selection.get("integrity", {})
    if integrity.get("algorithm") != "sha256" or integrity.get("digest") != manifest_digest(selection):
        raise SystemExit("selection integrity check failed; rerun select")
    if age_minutes(selection["generated_at"]) > max_age_minutes:
        raise SystemExit("selection is stale; rerun select")
    frozen_manifest = selection.get("manifest", {})
    if frozen_manifest.get("digest") != manifest.get("integrity", {}).get("digest"):
        raise SystemExit("selection was created from a different manifest")
    if Path(frozen_manifest.get("path", "")).resolve(strict=False) != Path(manifest_path).expanduser().resolve(strict=True):
        raise SystemExit("selection manifest path does not match --manifest")
    ids = selection.get("selected_ids")
    if not isinstance(ids, list) or not ids or not all(isinstance(item, str) for item in ids):
        raise SystemExit("selection contains no exact candidate IDs")
    if selection.get("status") != "budget_met":
        raise ValueError("selection has insufficient safe budget")
    if selection.get("filesystem") != manifest["authorization"]["envelope"]["filesystem"]:
        raise ValueError("selection filesystem mismatch")
    return selection


def default_report_path(manifest_path: str) -> Path:
    source = Path(manifest_path).expanduser()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return source.with_name(f"{source.stem}.apply-{stamp}.json")


def execution_report_path(source: Path, manifest: dict[str, Any]) -> Path:
    return source.with_name(f"{source.name}.execution-{manifest['integrity']['digest'][:20]}.json")


def apply_exit_code(report: dict[str, Any], *, report_written: bool = True) -> int:
    if not report_written or any(item.get("status") in ("partially_removed", "failed_unknown_effect", "in_progress") for item in report.get("results", [])):
        return 1
    target = report.get("approved_budget", {}).get("target_free_delta_bytes")
    if target is not None:
        return 0 if report.get("shortfall_bytes") == 0 else 1
    return 0 if all(item.get("status") in ("removed", "not_attempted") for item in report.get("results", [])) else 1


def apply_manifest(args: argparse.Namespace) -> int:
    if not args.execute or args.ack != ACK:
        raise ValueError("mutation requires explicit execute and acknowledgement")
    manifest = load_valid_manifest(args.manifest, args.max_age_minutes)
    if not args.id and not args.selection:
        raise ValueError("exact candidate IDs or frozen selection required")
    if args.authorization_source == "goal_authorization" and manifest["authorization"].get("mode") != "goal_authorized":
        raise ValueError("manifest has no goal authorization")
    selection = None
    selected_ids = list(args.id or [])
    if args.selection:
        if args.authorization_source != "goal_authorization":
            raise ValueError("selection requires goal authorization")
        selection = load_selection(args.selection, args.manifest, manifest, args.max_age_minutes)
        selected_ids = selection["selected_ids"]
    by_id = {item["id"]: item for item in manifest["candidates"]}
    if len(set(selected_ids)) != len(selected_ids) or any(item not in by_id for item in selected_ids):
        raise ValueError("unknown or duplicate selected IDs")
    selected = [by_id[item] for item in selected_ids]
    target = None
    if args.target_gib is not None:
        target = int(finite_number(args.target_gib, "target", minimum=0.000001) * 1024**3)
    if selection:
        selected_target = finite_number(selection["target_free_delta_bytes"], "selection target", minimum=1)
        if target is not None and target != selected_target:
            raise ValueError("target differs from frozen selection")
        target = selected_target
    elif args.authorization_source == "goal_authorization" and target is None:
        target = manifest["authorization"]["envelope"].get("target_free_delta_bytes")
    anchor = Path(args.volume or manifest["authorization"]["envelope"]["volume"]).expanduser()
    envelope = validate_envelope(manifest, selected, anchor, target)
    selected_allocated = sum(item["storage"]["allocated_bytes"] for item in selected)
    ceiling = min(selected_allocated, finite_number(envelope["risk_ceiling_bytes"], "frozen ceiling"))
    if args.risk_ceiling_gib is not None:
        requested = int(finite_number(args.risk_ceiling_gib, "risk ceiling") * 1024**3)
        if requested > ceiling:
            raise ValueError("risk ceiling exceeds frozen scope")
        ceiling = requested
    before = volume_free(anchor)
    observer = observer_context()
    source = Path(args.manifest).expanduser().resolve(strict=True)
    journal = execution_report_path(source, manifest)
    evidence_paths = [source, journal]
    if args.report_output:
        output = Path(args.report_output).expanduser().resolve(strict=False)
        if output == source:
            raise ValueError("report cannot overwrite its source manifest")
        if os.path.lexists(output):
            raise ValueError("report-output already exists; choose a new path")
        evidence_paths.append(output)
    if any(is_within(evidence, Path(item["canonical_path"])) for evidence in evidence_paths for item in selected):
        raise ValueError("operation evidence must be stored outside deletion candidates")
    report = {
        "schema": SCHEMA, "mode": "apply", "state": "started", "applied_at": now_utc(),
        "source_manifest_digest": manifest["integrity"]["digest"], "source_manifest": str(source),
        "authorization_source": args.authorization_source, "filesystem": envelope["filesystem"],
        "observer": observer, "volume_before": before, "results": [],
        "approved_budget": {"selected_ids": selected_ids, "selected_count": len(selected),
            "selected_allocated_bytes": selected_allocated, "risk_ceiling_bytes": ceiling,
            "consumed_allocated_budget_bytes": 0, "target_free_delta_bytes": target},
        "report_path": str(journal), "stopped_reason": "approved_set_exhausted",
    }
    # Exclusive durable claim prevents concurrent execution and blind retries, even after a crash.
    try:
        fd = os.open(journal, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except FileExistsError as exc:
        raise ValueError("execution receipt already exists: inspect and reconcile it, then create a fresh audit; never replay this manifest") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(report, handle, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    atomic_json(journal, report)
    previous_free = before["free_bytes"]
    for index, candidate in enumerate(selected):
        cost = candidate["storage"]["allocated_bytes"]
        if report["approved_budget"]["consumed_allocated_budget_bytes"] + cost > ceiling:
            report["stopped_reason"] = "risk_ceiling_reached"
            break
        item = {"id": candidate["id"], "path": candidate["path"], "canonical_path": candidate["canonical_path"],
                "kind": candidate["kind"], "identity": candidate["identity"], "candidate": candidate,
                "status": "skipped_before_mutation", "started_at": now_utc(), "removed_entries": 0}
        report["results"].append(item)
        dispatched = False
        try:
            # Age, filesystem, boundaries, recovery and owner state are checked for every candidate.
            if age_minutes(manifest["generated_at"]) > args.max_age_minutes:
                raise RuntimeError("manifest expired before candidate dispatch")
            validate_envelope(manifest, [candidate], anchor, target)
            path = revalidate_static(candidate)
            processes, complete, error = process_snapshot(set(observer["excluded_pids"]))
            revalidate_liveness(candidate, path, processes, complete, open_codex_roots(processes))
            item["status"] = "in_progress"
            report["approved_budget"]["consumed_allocated_budget_bytes"] += cost
            atomic_json(journal, report)
            dispatched = True
            if candidate["kind"] == "git_worktree":
                proc = run(["git", "-C", candidate["repository"], "worktree", "remove", "--", str(path)], timeout=600)
                if proc.returncode:
                    raise RuntimeError("Git worktree removal failed; reconcile owner state")
                retained_ref = candidate["git"].get("branch")
                if retained_ref:
                    code, out, _ = git_stdout(Path(candidate["repository"]), ["rev-parse", retained_ref])
                    if code or out.decode().strip() != candidate["git"]["head"]:
                        raise RuntimeError("retained branch verification failed")
            else:
                def progress(state):
                    item["removed_entries"] = state["removed_entries"]
                    print(f"deleting {candidate['id']}: {state['removed_entries']} entries removed", file=sys.stderr, flush=True)
                effect = safe_delete_tree(path, expected_identity=candidate["identity"], progress=progress)
                item["removed_entries"] = effect["removed_entries"]
            if os.path.lexists(path):
                raise RuntimeError("target still present after removal")
            item["status"] = "removed"
        except Exception as exc:
            if isinstance(exc, DeletionFailure):
                item["removed_entries"] = exc.removed_entries
            item["status"] = ("partially_removed" if item["removed_entries"] else "failed_unknown_effect") if dispatched else "skipped_before_mutation"
            item["error"] = str(exc)
            if dispatched:
                report["stopped_reason"] = "reconciliation_required"
        item["completed_at"] = now_utc()
        try:
            current = volume_free(anchor)
            item["interval_physical_free_delta_bytes"] = current["free_bytes"] - previous_free
            previous_free = current["free_bytes"]
            report["volume_after"] = current
            report["physical_free_delta_bytes"] = current["free_bytes"] - before["free_bytes"]
        except Exception as exc:
            report["measurement_error"] = str(exc)
            report["stopped_reason"] = "reconciliation_required"
        atomic_json(journal, report)
        if report["stopped_reason"] == "reconciliation_required":
            break
        if target is not None and report.get("physical_free_delta_bytes", 0) >= target:
            report["stopped_reason"] = "target_met"
            break
    attempted = {item["id"] for item in report["results"]}
    for candidate in selected:
        if candidate["id"] not in attempted:
            report["results"].append({"id": candidate["id"], "path": candidate["path"], "status": "not_attempted"})
    report["completed_at"] = now_utc()
    report["state"] = "reconciliation_required" if report["stopped_reason"] == "reconciliation_required" else "complete"
    report["shortfall_bytes"] = max(0, target - max(0, report.get("physical_free_delta_bytes", 0))) if target is not None else None
    atomic_json(journal, report)
    if args.report_output and Path(args.report_output).resolve(strict=False) != journal:
        atomic_json(Path(args.report_output), report, replace=False)
    print(json.dumps(report, indent=2, sort_keys=True))
    return apply_exit_code(report) if report["state"] == "complete" else 1


def self_test(_: argparse.Namespace) -> int:
    import unittest
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent.parent / "tests"), pattern="test_*.py")
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="command", required=True)
    audit_parser = sub.add_parser("audit", help="read-only inventory and manifest")
    audit_parser.add_argument("--root", action="append", default=[], help="bounded root to scan for generated artifacts")
    audit_parser.add_argument("--repo", action="append", default=[], help="Git repository whose registered worktrees should be audited")
    audit_parser.add_argument("--include-known-caches", action="store_true", help="include exact allowlisted cache paths")
    audit_parser.add_argument("--max-depth", type=int, default=7)
    audit_parser.add_argument('--npm-package-units', action='store_true', help='also qualify exact npm package/scope directories when a whole installation must be retained')
    audit_parser.add_argument('--npm-package-name', action='append', default=[], help='narrow package-unit discovery to this exact top-level package or scope name; repeatable')
    audit_parser.add_argument('--max-artifact-candidates', type=int, help='bound target-limited generated-artifact qualification; report remaining candidates as deliberately unassessed')
    audit_parser.add_argument("--authorization-mode", choices=("audit_only", "goal_authorized"), default="audit_only")
    audit_parser.add_argument("--authorization-scope", action="append", default=[], help="bounded user-authorized mutation scope; required for goal_authorized")
    audit_parser.add_argument("--target-gib", type=float, help="stop expensive sizing after safe candidates cover this target plus headroom")
    audit_parser.add_argument("--headroom-percent", type=float, default=25.0, help="allocated-size margin above a target (default: 25)")
    audit_parser.add_argument("--prefer-kind", action="append", choices=DEFAULT_KIND_ORDER, default=[], help="candidate kind to rank first; repeat to set order")
    audit_parser.add_argument("--kind", action="append", choices=DEFAULT_KIND_ORDER, default=[], help="restrict audit and target sizing to this candidate kind; repeat as needed")
    audit_parser.add_argument("--volume", default="/System/Volumes/Data" if sys.platform == "darwin" else "/")
    audit_parser.add_argument("--exclude", action="append", default=[], help="exclude exact paths and overlapping candidates")
    audit_parser.add_argument("--output")
    audit_parser.set_defaults(func=audit)

    select_parser = sub.add_parser("select", help="build a frozen non-overlapping exact-ID plan from a fresh manifest")
    select_parser.add_argument("--manifest", required=True)
    select_parser.add_argument("--target-gib", type=float, help="override the target recorded by audit")
    select_parser.add_argument("--headroom-percent", type=float, help="override the audit headroom")
    select_parser.add_argument("--prefer-kind", action="append", choices=DEFAULT_KIND_ORDER, default=[], help="candidate kind to rank first; repeat to set order")
    select_parser.add_argument("--kind", action="append", choices=DEFAULT_KIND_ORDER, default=[], help="restrict selection to this candidate kind; repeat as needed")
    select_parser.add_argument("--max-age-minutes", type=float, default=30.0)
    select_parser.add_argument("--output")
    select_parser.set_defaults(func=select_manifest)

    apply_parser = sub.add_parser("apply", help="revalidate and remove exact approved manifest entries")
    apply_parser.add_argument("--manifest", required=True)
    apply_scope = apply_parser.add_mutually_exclusive_group()
    apply_scope.add_argument("--id", action="append", default=[])
    apply_scope.add_argument("--selection", help="frozen select output; allowed only with goal_authorization")
    apply_parser.add_argument("--authorization-source", choices=("manifest_approval", "goal_authorization"), required=True)
    apply_parser.add_argument("--execute", action="store_true")
    apply_parser.add_argument("--ack")
    apply_parser.add_argument("--max-age-minutes", type=float, default=30.0)
    apply_parser.add_argument("--target-gib", type=float)
    apply_parser.add_argument("--risk-ceiling-gib", type=float, help="optional ceiling no greater than selected allocated bytes")
    apply_parser.add_argument("--volume", help="must match frozen target filesystem; defaults to manifest volume")
    apply_parser.add_argument("--report-output", help="new optional receipt copy; durable digest-bound execution receipt is always kept beside the manifest")
    apply_parser.set_defaults(func=apply_manifest)

    from fs_diagnostics import register_commands as register_diagnostics
    from fs_compare import register_commands as register_comparison
    from fs_observe import register_commands as register_observation
    register_diagnostics(sub)
    register_comparison(sub)
    register_observation(sub)

    test_parser = sub.add_parser("self-test", help="exercise parsing, discovery, identity, and deletion in a temporary fixture")
    test_parser.set_defaults(func=self_test)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return int(args.func(args))
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"refused or incomplete: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
