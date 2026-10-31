"""Small, standard-library safety primitives. No work occurs on import."""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import stat
import tempfile


def finite_number(value, name, *, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and at least {minimum}")
    return value


def filesystem_identity(path: Path):
    real = path.expanduser().resolve(strict=True)
    st = real.stat()
    vfs = os.statvfs(real)
    return {"device": st.st_dev, "filesystem_id": getattr(vfs, "f_fsid", None)}


def atomic_json(path: Path, value, *, replace=True):
    """Persist in the same directory; a failed replace retains the prior receipt."""
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if replace:
            os.replace(name, path)
        else:
            os.link(name, path)
        parent_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class DeletionFailure(RuntimeError):
    def __init__(self, message, removed_entries):
        super().__init__(message)
        self.removed_entries = removed_entries


def delete_tree(path: Path, *, expected_identity=None, progress=None, heartbeat_seconds=5.0):
    """No-follow descriptor traversal; refuses unsupported platforms."""
    import time
    required = (os.open, os.stat, os.unlink, os.rmdir)
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY") or any(fn not in os.supports_dir_fd for fn in required):
        raise RuntimeError("descriptor-relative deletion is unavailable")
    path = Path(os.path.abspath(path))
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    count = 0
    started = last = time.monotonic()
    fds = []
    def note():
        nonlocal last
        now = time.monotonic()
        if progress and now - last >= heartbeat_seconds:
            progress({"phase": "removed", "preflight_entries": 0, "removed_entries": count, "elapsed_seconds": now-started})
            last = now
    def identity(st):
        return st.st_dev, st.st_ino
    def visit(parent, name, device):
        nonlocal count
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if before.st_dev != device:
            raise RuntimeError("device changed during deletion")
        if stat.S_ISDIR(before.st_mode):
            fd = os.open(name, flags, dir_fd=parent)
            try:
                if identity(os.fstat(fd)) != identity(before):
                    raise RuntimeError("directory identity changed during open")
                for child in sorted(os.listdir(fd)):
                    visit(fd, child, device)
                if identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != identity(before):
                    raise RuntimeError("directory replaced during deletion")
                os.rmdir(name, dir_fd=parent)
                count += 1
                note()
            finally:
                os.close(fd)
        else:
            os.unlink(name, dir_fd=parent)
            count += 1
            note()
    try:
        current = os.open(path.anchor, flags)
        fds.append(current)
        for component in path.parts[1:-1]:
            current = os.open(component, flags, dir_fd=current)
            fds.append(current)
        root = os.stat(path.name, dir_fd=current, follow_symlinks=False)
        if not stat.S_ISDIR(root.st_mode):
            raise RuntimeError("candidate is not a real directory")
        if expected_identity and (root.st_dev != expected_identity["device"] or root.st_ino != expected_identity["inode"]):
            raise RuntimeError("candidate identity changed before descriptor open")
        visit(current, path.name, root.st_dev)
        return {"removed_entries": count}
    except Exception as exc:
        raise DeletionFailure(str(exc), count) from exc
    finally:
        for fd in reversed(fds):
            os.close(fd)
