"""Passive, bounded filesystem diagnostics. Catalog entries never grant mutation."""
from __future__ import annotations
import argparse
import contextlib
import datetime as dt
import fnmatch
import json
import math
import os
from pathlib import Path
import plistlib
import selectors
import stat
import subprocess
import sys
import time
from typing import Any

SCHEMA = "filesystem-lifecycle/doctor-v1"
PROTECTED = {".git", ".ssh", ".gnupg", "Keychains", "Mail", "Messages", "Photos Library.photoslibrary", "Mobile Documents", "CloudStorage", "Documents", "Downloads", "Desktop", "Pictures", "Movies", "Music"}
SECRET_PATTERNS = (".env*", "*.pem", "*.p12", "*.key", "*.keychain*", "*.photoslibrary")
MAX_INPUT = 16 * 1024 * 1024


def protected(name: str) -> bool:
    return name in PROTECTED or any(fnmatch.fnmatchcase(name.lower(), p.lower()) for p in SECRET_PATTERNS)


def sensitive_component(name: str) -> bool:
    return name in {".ssh", ".gnupg", "Keychains", "Mail", "Messages", "Mobile Documents", "CloudStorage"} or any(fnmatch.fnmatchcase(name.lower(), p.lower()) for p in SECRET_PATTERNS)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def probe(argv: list[str], timeout: float, limit: int = 262144) -> dict[str, Any]:
    """Bound subprocess wall time and captured bytes, without temporary files."""
    start = time.monotonic()
    chunks = {"stdout": bytearray(), "stderr": bytearray()}
    reason = None
    try:
        process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
    except OSError as exc:
        return {"status": "unavailable", "reason": str(exc), "stdout": "", "stderr": ""}
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        try:
            while selector.get_map():
                remaining = timeout - (time.monotonic() - start)
                if remaining <= 0:
                    reason = "probe timeout"
                    break
                for key, _ in selector.select(min(remaining, .1)):
                    data = os.read(key.fileobj.fileno(), min(65536, limit + 1))
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    chunks[key.data].extend(data)
                    if sum(map(len, chunks.values())) > limit:
                        reason = "probe output limit"
                        break
                if reason:
                    break
        finally:
            if reason and process.poll() is None:
                process.kill()
            if process.poll() is None:
                try:
                    process.wait(timeout=max(.001, timeout - (time.monotonic() - start)))
                except subprocess.TimeoutExpired:
                    reason = reason or "probe timeout"
                    process.kill()
            process.wait()
            process.stdout.close()
            process.stderr.close()
    out = bytes(chunks["stdout"][:limit]).decode("utf-8", "replace")
    err = bytes(chunks["stderr"][:limit]).decode("utf-8", "replace")
    return {"status": "partial" if reason or err.strip() else "complete" if process.returncode == 0 else "unavailable", "reason": reason or ("probe warning" if err.strip() else None) or (f"exit {process.returncode}" if process.returncode else None), "stdout": out, "stderr": err, "returncode": process.returncode}


def mount_inventory(timeout: float) -> dict[str, Any]:
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/self/mountinfo", "rb") as handle:
                raw = handle.read(1048577)
            if len(raw) > 1048576:
                raise ValueError("mount inventory exceeds limit")
            paths = []
            for line in raw.decode().splitlines():
                columns = line.split()
                if len(columns) < 10 or " - " not in line:
                    raise ValueError("malformed mount record")
                value = columns[4]
                for old, new in (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"), ("\\134", "\\")):
                    value = value.replace(old, new)
                paths.append(value)
            return {"status": "complete", "paths": paths}
        except (OSError, ValueError) as exc:
            return {"status": "unavailable", "paths": [], "reason": str(exc)}
    if sys.platform == "darwin":
        result = probe(["/sbin/mount"], timeout)
        paths = []
        for line in result["stdout"].splitlines():
            if " on " not in line or " (" not in line:
                result["status"] = "partial"
                result["reason"] = "unparsed mount record"
                continue
            paths.append(line.split(" on ", 1)[1].rsplit(" (", 1)[0])
        return {k: v for k, v in result.items() if k not in ("stdout", "stderr")} | {"paths": paths}
    return {"status": "unavailable", "paths": [], "reason": "unsupported mount inventory platform"}


def load_catalog() -> list[dict[str, Any]]:
    document = json.loads(Path(__file__).with_name("resource_catalog.json").read_text())
    if document.get("schema") != "filesystem-lifecycle/catalog-v1" or not isinstance(document.get("entries"), list):
        raise ValueError("invalid diagnostic catalog schema")
    entries = document["entries"]
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise ValueError("invalid catalog entry")
        if "command" in entry or "argv" in entry or "script" in entry:
            raise ValueError("catalog cannot contain executable commands")
        if entry.get("owner_resolver") not in {"project-marker", "bundle-metadata"}:
            raise ValueError("unknown catalog owner resolver")
        if entry.get("supported_actions", ["inventory"]) != ["inventory"]:
            raise ValueError("diagnostic catalog may only authorize inventory")
        for marker in entry.get("markers", []):
            if Path(marker).name != marker or protected(marker):
                raise ValueError("unsafe catalog marker")
    return entries


def owner_for(path: Path, catalog: list[dict[str, Any]], parent_fd: int | None = None) -> dict[str, Any]:
    for item in catalog:
        if sys.platform not in item.get("platforms", []):
            continue
        match = path.name == item.get("basename") or bool(item.get("suffix") and path.name.endswith(item["suffix"]))
        if not match:
            continue
        if item["owner_resolver"] == "project-marker":
            found = False
            for name in item.get("markers", []):
                try:
                    marker_stat = os.stat(name if parent_fd is not None else path.parent / name, dir_fd=parent_fd, follow_symlinks=False)
                    found = found or stat.S_ISREG(marker_stat.st_mode)
                except OSError:
                    pass
            return {"owner": item["owner"] if found else "unknown", "purpose": item["purpose"], "catalog_id": item["id"], "recovery": {"level": "none_or_unknown", "method": item["recovery_method"]}, "owner_evidence": "project marker exists" if found else "project marker missing"}
        # Do not open arbitrary plists. Only the conventional bundle identity file,
        # with no-follow handling and a strict size bound; expose allowlisted fields.
        try:
            with contextlib.ExitStack() as cleanup:
                flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                bundle_fd = os.open(path.name if parent_fd is not None else path, flags, dir_fd=parent_fd)
                cleanup.callback(os.close, bundle_fd)
                contents_fd = os.open("Contents", flags, dir_fd=bundle_fd)
                cleanup.callback(os.close, contents_fd)
                fd = os.open("Info.plist", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=contents_fd)
                with os.fdopen(fd, "rb") as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise ValueError("bundle metadata is not regular")
                    raw = stream.read(262145)
            if len(raw) > 262144:
                raise ValueError("bundle metadata too large")
            data = plistlib.loads(raw)
            bundle = data.get("CFBundleIdentifier")
            return {"owner": bundle if isinstance(bundle, str) else "unknown", "purpose": item["purpose"], "catalog_id": item["id"], "classification": "retain", "owner_evidence": "bundle identifier only; service registration unassessed"}
        except (OSError, ValueError, plistlib.InvalidFileException):
            return {"owner": "unknown", "purpose": item["purpose"], "classification": "retain", "owner_evidence": "bundle metadata unavailable"}
    return {"owner": "unknown", "purpose": "Unclassified filesystem resource"}


def scan_root(root: Path, *, mounts: dict[str, Any], max_depth: int, max_entries: int, timeout: float, catalog: list[dict[str, Any]]) -> dict[str, Any]:
    start = time.monotonic()
    gaps: list[dict[str, str]] = []
    rows: dict[str, dict[str, Any]] = {}
    seen: set[tuple[int, int]] = set()
    entries = 0
    def gap(path: Path, reason: str) -> None:
        if len(gaps) < 1000:
            gaps.append({"path": str(path), "reason": reason})
    def result(status: str) -> dict[str, Any]:
        return {"root": str(root), "status": status, "entries_examined": entries, "elapsed_seconds": round(time.monotonic() - start, 6), "coverage_gaps": gaps, "resources": list(rows.values())}
    if mounts.get("status") != "complete":
        gap(root, "mount inventory incomplete; traversal refused")
        return result("unavailable")
    if root.is_symlink() or protected(root.name) or any(sensitive_component(part) for part in root.parts):
        gap(root, "protected or symlinked root")
        return result("unavailable")
    root = root.absolute()
    if root == Path(root.anchor):
        gap(root, "filesystem root traversal is not supported; name bounded directories")
        return result("unavailable")
    try:
        root = root.resolve(strict=True)
        initial = root.stat()
        root_filesystem_id = getattr(os.statvfs(root), "f_fsid", None)
        if not stat.S_ISDIR(initial.st_mode):
            raise ValueError("root is not a directory")
    except (OSError, ValueError) as exc:
        gap(root, str(exc))
        return result("unavailable")
    mount_paths = {str(Path(p).resolve(strict=False)) for p in mounts["paths"]}
    stopped = False
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    def walk(directory_fd: int, current: Path, depth: int, buckets: tuple[str, ...]) -> None:
        nonlocal entries, stopped
        if stopped:
            return
        if depth >= max_depth:
            gap(current, "depth limit")
            return
        try:
            with os.scandir(directory_fd) as children:
                for child in children:
                    if entries >= max_entries or time.monotonic() - start >= timeout:
                        gap(current, "scan time or entry budget exhausted")
                        stopped = True
                        return
                    entries += 1
                    path = current / child.name
                    if protected(child.name):
                        gap(path, "protected name excluded")
                        continue
                    try:
                        st = child.stat(follow_symlinks=False)
                    except OSError as exc:
                        gap(path, f"metadata unavailable: {exc}")
                        continue
                    if stat.S_ISLNK(st.st_mode):
                        gap(path, "symlink excluded")
                        continue
                    if st.st_dev != initial.st_dev or os.path.normpath(str(path)) in mount_paths:
                        gap(path, "mount boundary excluded")
                        continue
                    owner = owner_for(path, catalog, parent_fd=directory_fd) if not buckets or any(path.name == rule.get("basename") or bool(rule.get("suffix") and path.name.endswith(rule["suffix"])) for rule in catalog) else {}
                    keys = buckets
                    if not keys or owner.get("catalog_id"):
                        key = str(path)
                        rows[key] = {"path": key, "canonical_path": key, "kind": "inventory", "classification": "unknown", "identity": {"device": st.st_dev, "filesystem_id": root_filesystem_id, "inode": st.st_ino, "mount_id": f"device:{st.st_dev}:" + max((m for m in mount_paths if Path(m) == root or Path(m) in root.parents), key=len, default=str(root))}, "storage": {"allocated_bytes": 0, "logical_bytes": 0, "estimated_reclaimability": "unknown"}, "file_count": 0, "recovery": {"level": "none_or_unknown"}, "action": None, "reasons": ["inventory only; deletion eligibility unassessed"], **owner}
                        if buckets:
                            rows[key]["covered_by"] = buckets[-1]
                            rows[key]["reasons"].append("footprint overlaps parent inventory row; do not sum")
                        keys = buckets + (key,)
                    ident = (st.st_dev, st.st_ino)
                    if ident not in seen:
                        seen.add(ident)
                        for key in keys:
                            rows[key]["storage"]["allocated_bytes"] += st.st_blocks * 512
                            rows[key]["storage"]["logical_bytes"] += st.st_size
                    for key in keys:
                        if stat.S_ISREG(st.st_mode): rows[key]["file_count"] += 1
                    if stat.S_ISDIR(st.st_mode):
                        try:
                            fd = os.open(child.name, flags, dir_fd=directory_fd)
                            try:
                                opened = os.fstat(fd)
                                if (opened.st_dev, opened.st_ino) != (st.st_dev, st.st_ino):
                                    gap(path, "directory identity changed")
                                else:
                                    walk(fd, path, depth + 1, keys)
                            finally:
                                os.close(fd)
                        except OSError as exc:
                            gap(path, f"directory open failed: {exc}")
        except OSError as exc:
            gap(current, f"directory unavailable: {exc}")
    try:
        root_fd = os.open(root, flags)
        try:
            opened = os.fstat(root_fd)
            if (opened.st_dev, opened.st_ino) != (initial.st_dev, initial.st_ino):
                gap(root, "root identity changed")
            else:
                walk(root_fd, root, 0, ())
        finally:
            os.close(root_fd)
    except OSError as exc:
        gap(root, f"root open failed: {exc}")
    for row in rows.values():
        row["scan_status"] = "partial" if gaps else "complete"
        row["storage"]["measurement_kind"] = "observed_allocated_lower_bound" if gaps else "allocated_footprint_not_exclusive_recovery"
    return result("partial" if gaps else "complete")


def capacity(volume: Path) -> dict[str, Any]:
    try:
        st = volume.stat()
        v = os.statvfs(volume)
        return {"status": "complete", "path": str(volume.resolve()), "device": st.st_dev, "filesystem_id": getattr(v, "f_fsid", None), "total_bytes": v.f_blocks * v.f_frsize, "available_bytes": v.f_bavail * v.f_frsize, "free_bytes": v.f_bfree * v.f_frsize, "inodes_total": v.f_files if v.f_files > 0 else None, "inodes_available": v.f_favail if v.f_files > 0 else None}
    except OSError as exc:
        return {"status": "unavailable", "path": str(volume), "reason": str(exc)}


def filesystem_mount(path: Path, timeout: float) -> dict[str, Any]:
    """Bind a path to a mount by device and filesystem ID before path ancestry.

    Darwin firmlinks make /Users a Data-volume path even though the Data mount
    is not its textual ancestor. Snapshot roots may even share st_dev while
    statvfs reports a different filesystem ID. Prefix alone selects / wrongly.
    """
    inventory = mount_inventory(timeout)
    if inventory.get("status") != "complete":
        return {"status": "unavailable", "reason": "mount inventory incomplete"}
    try:
        target = path.resolve(strict=True)
        device = target.stat().st_dev
        fsid = getattr(os.statvfs(target), "f_fsid", None)
    except OSError as exc:
        return {"status": "unavailable", "reason": f"target filesystem unavailable: {exc}"}
    matching = []
    failures = []
    for raw in inventory.get("paths", []):
        mount = Path(raw)
        try:
            mount_device = mount.stat().st_dev
            mount_fsid = getattr(os.statvfs(mount), "f_fsid", None)
            if mount_device == device and (fsid is None or mount_fsid == fsid):
                matching.append(mount)
        except OSError:
            failures.append(raw)
    ancestors = [mount for mount in matching if target == mount or mount in target.parents]
    if ancestors:
        chosen = max(ancestors, key=lambda m: len(m.parts))
    elif len(matching) == 1 and not failures:
        chosen = matching[0]
    else:
        return {"status": "unavailable", "reason": "target device has no unambiguous observed mount", "device": device}
    return {"status": "complete", "path": str(chosen), "device": device}


def deleted_open(root: Path, timeout: float) -> dict[str, Any]:
    # Target mount only. Return names only if beneath the authorized root.
    binding = filesystem_mount(root, timeout)
    if binding["status"] != "complete":
        return {**binding, "resources": []}
    mount = binding["path"]
    result = probe(["lsof", "-nP", "+L1", "-a", "-F", "pcfns", "+f", "--", mount], timeout)
    records = []
    pid = command = fd = size = None
    for line in result["stdout"].splitlines():
        if not line:
            continue
        tag, value = line[0], line[1:]
        if tag == "p": pid, command, fd, size = value, None, None, None
        elif tag == "c": command = value
        elif tag == "f": fd, size = value, None
        elif tag == "s": size = int(value) if value.isdigit() else None
        elif tag == "n" and value.startswith(str(root).rstrip("/") + "/"):
            records.append({"pid": pid, "owner": command, "fd": fd, "path": value, "logical_bytes": size})
    if result.get("returncode") == 1 and not result["stdout"] and not result["stderr"]:
        result["status"] = "complete"
        result["reason"] = "no matches in caller-visible scope"
    return {k: v for k, v in result.items() if k not in ("stdout", "stderr")} | {"mount": binding, "resources": records, "visibility": "current user; absence is not proof of system-wide absence"}


def apfs_observation(volume: Path, timeout: float) -> dict[str, Any]:
    if sys.platform != "darwin":
        return {"status": "unavailable", "reason": "APFS probe is macOS-only"}
    binding = filesystem_mount(volume, timeout)
    if binding["status"] != "complete":
        return binding
    mount = binding["path"]
    result = probe(["diskutil", "info", "-plist", mount], timeout)
    try:
        data = plistlib.loads(result["stdout"].encode())
        allowed = ("FilesystemType", "APFSContainerReference", "APFSContainerFree", "VolumeTotalSpace", "VolumeFreeSpace", "DeviceIdentifier", "MountPoint")
        fields = {k: data[k] for k in allowed if k in data}
    except (ValueError, plistlib.InvalidFileException):
        fields = {}
        result["status"] = "unavailable"
        result["reason"] = "diskutil plist unavailable"
    snapshots = probe(["diskutil", "apfs", "listSnapshots", "-plist", mount], timeout)
    try:
        snap_data = plistlib.loads(snapshots["stdout"].encode())
        count = len(snap_data["Snapshots"]) if isinstance(snap_data.get("Snapshots"), list) else None
    except (ValueError, plistlib.InvalidFileException):
        count = None
    if count is None or snapshots["status"] != "complete":
        result["status"] = "partial" if fields else "unavailable"
        result["reason"] = "snapshot probe incomplete"
    return {"status": result["status"], "reason": result.get("reason"), "mount": binding, "fields": fields, "snapshots": {"status": snapshots["status"] if count is not None else "unavailable", "count": count}, "accounting": "Container capacity is shared. Snapshot and clone sharing prevent attribution of allocated footprints to exclusive recovery."}


def launchd_observation(owners: set[str], timeout: float) -> dict[str, Any]:
    """Read only launchctl's label/PID table; never dump service environments."""
    if sys.platform != "darwin":
        return {"status": "unavailable", "reason": "launchd is macOS-only", "matches": []}
    result = probe(["launchctl", "list"], timeout)
    matches = []
    for line in result["stdout"].splitlines():
        columns = line.split(None, 2)
        if len(columns) != 3 or columns[0] == "PID":
            continue
        pid, exit_status, label = columns
        if label in owners:
            matches.append({"label": label, "pid": int(pid) if pid.isdigit() else None, "registered": True})
    return {"status": result["status"], "reason": result.get("reason"), "matches": matches, "visibility": "current launchctl domain; absence is not proof of orphaned application data"}


def render_report(document: dict[str, Any], format: str = "markdown") -> str:
    if format == "json":
        return json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    def cell(value: Any) -> str:
        return str(value if value is not None else "unknown").replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    lines = []
    if "physical_free_delta_bytes" in document:
        lines.append(f"Measured volume free-space change: {cell(document['physical_free_delta_bytes'])} bytes (volume-wide interval, not exclusive causality).")
    if "shortfall_bytes" in document:
        lines.append(f"Target shortfall: {cell(document['shortfall_bytes'])} bytes.")
    capacity_data = document.get("probes", {}).get("capacity", {})
    if capacity_data:
        lines.append(f"Capacity ({cell(capacity_data.get('status'))}): {cell(capacity_data.get('path'))}; available {cell(capacity_data.get('available_bytes'))} bytes; available inodes {cell(capacity_data.get('inodes_available'))} / {cell(capacity_data.get('inodes_total'))}.")
    lines.append(f"Observation status: {cell(document.get('status', document.get('stopped_reason', 'not supplied')))}.")
    for name, observation in document.get("probes", {}).items():
        if name in {"capacity", "mounts"}: continue
        lines.append(f"Probe {cell(name)}: {cell(observation.get('status'))}; {cell(observation.get('reason', 'no diagnostic warning recorded'))}.")
        if name == "apfs":
            lines.append(f"APFS snapshot count: {cell(observation.get('snapshots', {}).get('count'))}; fields: {cell(json.dumps(observation.get('fields', {}), sort_keys=True))}.")
        if name == "deleted_open":
            for child in observation.get("observations", []):
                lines.append(f"Deleted-open visibility: {cell(child.get('status'))}; {cell(child.get('reason'))}; {len(child.get('resources', []))} observed resources.")
    lines += ["", "| Resource | Owner/purpose | Classification | Allocated size | Recovery confidence | Blocker | Proposed action |", "|---|---|---|---|---|---|---|"]
    rows = document.get("resources", document.get("candidates", document.get("results", [])))
    for item in rows:
        item = {**(item.get("candidate") or {}), **item}
        storage = item.get("storage") or {}
        size = storage.get("allocated_bytes")
        size_text = f"{size:,} bytes" if isinstance(size, int) else "unknown"
        if item.get("scan_status") == "partial": size_text += " (lower bound)"
        recovery = item.get("recovery") or {}
        action = item.get("action")
        action_text = action.get("operation", "unknown") if isinstance(action, dict) else action or "inventory only"
        values = [item.get("path", item.get("id", "unknown")), f"{item.get('owner', 'unknown')} / {item.get('purpose', 'unspecified')}", item.get("classification", item.get("status", "unknown")), size_text, recovery.get("level", "unknown"), "; ".join(item.get("reasons", [])) or item.get("error", "none recorded"), action_text]
        lines.append("| " + " | ".join(map(cell, values)) + " |")
    if not rows: lines.append("| No assessed resources | — | unknown | unknown | unknown | See coverage | inventory only |")
    lines.extend(["", "Allocated footprints are not promised recovery; shared blocks and sparse files affect accounting. Root and catalog rows can overlap; do not sum them."])
    if document.get("high_file_count"):
        lines.extend(["", "Highest observed file counts (parent/catalog rows may overlap):"])
        lines.extend(f"- {cell(row['path'])}: {cell(row['file_count'])} files ({cell(row.get('scan_status'))})" for row in document["high_file_count"][:10])
    for diagnosis in document.get("diagnoses", []):
        lines.append(f"Diagnosis {cell(diagnosis.get('condition'))}: {cell(diagnosis.get('evidence'))}.")
    gaps = document.get("coverage_gaps", [])
    if gaps:
        lines.extend(["", "Coverage gaps:"])
        lines.extend(f"- {cell(g.get('path', g.get('probe', 'probe')))}: {cell(g.get('reason'))}" for g in gaps)
    return "\n".join(lines) + "\n"


def emit(document: dict[str, Any], args: argparse.Namespace) -> int:
    rendered = render_report(document, args.format)
    if args.output:
        fd = os.open(Path(args.output).expanduser(), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as handle: handle.write(rendered)
    else:
        print(rendered, end="")
    return 0 if document.get("status", "complete") == "complete" else 1


def doctor(args: argparse.Namespace) -> int:
    if not 1 <= args.max_depth <= 128 or args.max_entries < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
        raise ValueError("scan limits must be positive and finite; max-depth must be 1..128")
    volume = Path(args.volume).expanduser().absolute()
    roots = list(dict.fromkeys(Path(p).expanduser().absolute() for p in args.root))
    catalog = load_catalog()
    mounts = mount_inventory(args.timeout) if roots else {"status": "complete", "paths": []}
    scans = [scan_root(root, mounts=mounts, max_depth=args.max_depth, max_entries=args.max_entries, timeout=args.timeout, catalog=catalog) for root in roots]
    probes = {"capacity": capacity(volume), "mounts": mounts}
    if args.deleted_open:
        probes["deleted_open"] = {"status": "complete", "observations": [deleted_open(root, args.timeout) for root in roots]}
        if any(p["status"] != "complete" for p in probes["deleted_open"]["observations"]): probes["deleted_open"]["status"] = "partial"
    if args.apfs: probes["apfs"] = apfs_observation(volume, args.timeout)
    gaps = [gap for scan in scans for gap in scan["coverage_gaps"]]
    gaps.extend({"probe": key, "reason": p.get("reason", "probe incomplete")} for key, p in probes.items() if p["status"] != "complete")
    resources = [row for scan in scans for row in scan["resources"]]
    resources.sort(key=lambda r: r["storage"]["allocated_bytes"], reverse=True)
    if args.launchd:
        probes["launchd"] = launchd_observation({r["owner"] for r in resources if r.get("owner") not in {None, "unknown"}}, args.timeout)
        if probes["launchd"]["status"] != "complete":
            gaps.append({"probe": "launchd", "reason": probes["launchd"].get("reason", "incomplete")})
    diagnoses = []
    cap = probes["capacity"]
    if cap.get("status") == "complete":
        if cap["available_bytes"] == 0:
            diagnoses.append({"condition": "blocks_exhausted", "evidence": "zero caller-available bytes on target filesystem"})
        if cap.get("inodes_total") and cap.get("inodes_available") == 0:
            diagnoses.append({"condition": "inodes_exhausted", "evidence": "zero available inodes; inspect high_file_count"})
    if gaps:
        diagnoses.append({"condition": "incomplete_coverage", "evidence": "see coverage_gaps; unobserved sizes are unknown"})
    high_file_count = [{"path": r["path"], "file_count": r["file_count"], "scan_status": r["scan_status"]} for r in sorted(resources, key=lambda row: row["file_count"], reverse=True)[:20]]
    document = {"diagnoses": diagnoses, "high_file_count": high_file_count, "schema": SCHEMA, "generated_at": now(), "mode": "doctor", "status": "partial" if gaps else "complete", "filesystem": {k: probes["capacity"][k] for k in ("device", "filesystem_id") if k in probes["capacity"]}, "scope": {"roots": [scan["root"] for scan in scans], "volume": str(volume), "max_depth": args.max_depth}, "limits_per_root": {"max_depth": args.max_depth, "max_entries": args.max_entries, "timeout_seconds": args.timeout}, "resources": resources, "scans": scans, "probes": probes, "coverage_gaps": gaps, "mutation_authorized": False}
    return emit(document, args)


def report(args: argparse.Namespace) -> int:
    path = Path(args.input).expanduser()
    if any(sensitive_component(part) for part in path.parts):
        raise ValueError("protected report input excluded")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("report input must be a regular file")
        raw = handle.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT: raise ValueError("report input exceeds 16 MiB")
    document = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    if not isinstance(document, dict): raise ValueError("report requires a JSON object")
    return emit(document, args)


def register_commands(subparsers: Any) -> None:
    p = subparsers.add_parser("doctor", help="passive bounded capacity and consumer diagnosis")
    p.add_argument("--root", action="append", default=[], help="explicit bounded traversal root; omit for capacity only")
    p.add_argument("--volume", default="/System/Volumes/Data" if sys.platform == "darwin" else "/")
    p.add_argument("--max-depth", type=int, default=5)
    p.add_argument("--max-entries", type=int, default=100000)
    p.add_argument("--timeout", type=float, default=15)
    p.add_argument("--deleted-open", action="store_true", help="opt in to scoped lsof probe")
    p.add_argument("--apfs", action="store_true", help="opt in to read-only APFS capacity/snapshot probes")
    p.add_argument("--launchd", action="store_true", help="opt in to current-domain launchd label matching for observed owners")
    p.add_argument("--format", choices=("json", "markdown"), default="json")
    p.add_argument("--output", help="write a new output file exclusively; never overwrite")
    p.set_defaults(func=doctor)
    p = subparsers.add_parser("report", help="render an existing manifest or receipt without scanning")
    p.add_argument("--input", required=True)
    p.add_argument("--format", choices=("json", "markdown"), default="markdown")
    p.add_argument("--output")
    p.set_defaults(func=report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    register_commands(parser.add_subparsers(required=True))
    try:
        arguments = parser.parse_args()
        raise SystemExit(arguments.func(arguments))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
