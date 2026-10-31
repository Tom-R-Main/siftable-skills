"""Owner-specific recoverability of disposable download caches.

No owner commands, network requests, credential reads, or mutations. The caller
must additionally prove exact authorization, mount boundaries, tracked-file
absence and current owner/session/handle inactivity before any deletion.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time
from typing import Any

SEMVER = re.compile(r'\d+\.\d+\.\d+')
HASHED_DOWNLOAD = re.compile(r'[0-9a-f]{64}--[^/]+')
PUBLIC_CRATE = re.compile(r'[A-Za-z0-9_-]+-\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.+-]+)?\.crate')
SECRET_SUFFIXES = ('.pem', '.p12', '.key', '.keychain', '.keychain-db')
STATE_NAMES = {'cookies', 'history', 'login data', 'local state', 'local storage', 'session storage', 'indexeddb', 'default', '.git', '.ssh', 'credentials', 'secrets', 'user-data', 'userdata', 'profiles'}
SOURCES = {
    'homebrew': 'https://docs.brew.sh/Manpage#cleanup-options-formulacask-',
    'node-gyp': 'https://github.com/nodejs/node-gyp/blob/main/lib/install.js',
    'cypress': 'https://docs.cypress.io/app/references/advanced-installation',
    'cargo': 'https://doc.rust-lang.org/cargo/guide/cargo-home.html',
    'playwright': 'https://playwright.dev/docs/browsers#managing-browser-binaries',
}


def _sensitive(name: str) -> bool:
    lower = name.lower()
    return (lower.startswith('.env') or lower.endswith(SECRET_SUFFIXES) or lower in STATE_NAMES
            or re.fullmatch(r'profile \d+', lower) is not None
            or lower.endswith(('.sqlite', '.sqlite3', '.db', '.db-wal')))


class _Budget:
    def __init__(self, seconds: float, max_owner_bytes: int, max_owner_reads: int):
        if not math.isfinite(seconds) or seconds <= 0 or type(max_owner_bytes) is not int or max_owner_bytes <= 0 or type(max_owner_reads) is not int or max_owner_reads <= 0:
            raise ValueError('observation budgets must be positive and finite')
        self.deadline = time.monotonic() + seconds
        self.remaining_bytes = max_owner_bytes
        self.remaining_reads = max_owner_reads

    def check(self) -> None:
        if time.monotonic() > self.deadline:
            raise ValueError('cache observation deadline exceeded')

    def reserve_read(self) -> None:
        self.check()
        if self.remaining_reads <= 0 or self.remaining_bytes <= 0:
            raise ValueError('aggregate owner metadata read budget exceeded')
        self.remaining_reads -= 1


def _inventory(root: Path, limit: int, budget: _Budget) -> tuple[dict[str, dict], dict[str, bytes]]:
    """Descriptor-based metadata inventory; selected owner files read separately."""
    records: dict[str, dict] = {}
    budget.check()
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    device = os.fstat(root_fd).st_dev
    def walk(fd: int, prefix: str, depth: int) -> None:
        if depth > 32:
            raise ValueError('cache layout exceeds depth budget')
        with os.scandir(fd) as entries:
            for entry in entries:
                budget.check()
                if len(records) >= limit:
                    raise ValueError('cache layout exceeds observation entry budget')
                if _sensitive(entry.name):
                    raise ValueError('credential-shaped or mutable runtime state requires separate owner review')
                st = entry.stat(follow_symlinks=False)
                if st.st_dev != device:
                    raise ValueError('cache crosses a filesystem boundary')
                relative = f'{prefix}/{entry.name}' if prefix else entry.name
                row = {'mode': st.st_mode, 'device': st.st_dev, 'inode': st.st_ino,
                       'size': st.st_size, 'mtime_ns': st.st_mtime_ns}
                records[relative] = row
                if stat.S_ISDIR(st.st_mode):
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                    try:
                        observed = os.fstat(child)
                        if (observed.st_dev, observed.st_ino) != (st.st_dev, st.st_ino):
                            raise ValueError('cache directory changed while observed')
                        walk(child, relative, depth + 1)
                    finally:
                        os.close(child)
                elif stat.S_ISLNK(st.st_mode):
                    target = os.readlink(entry.name, dir_fd=fd)
                    resolved = Path(os.path.normpath(str(root / prefix / target))) if not os.path.isabs(target) else Path(target)
                    if not resolved.is_relative_to(root):
                        raise ValueError('cache symlink points outside the qualified resource')
                    row['link'] = target
                elif not stat.S_ISREG(st.st_mode):
                    raise ValueError('cache contains a special file')
    try:
        walk(root_fd, '', 0)
    finally:
        os.close(root_fd)
    return records, {}


def _read_owner_file(root: Path, relative: str, maximum: int = 262144, *, budget: _Budget) -> bytes:
    budget.reserve_read()
    parts = PurePosixPath(relative).parts
    if not parts or any(_sensitive(p) or p in ('.', '..') for p in parts):
        raise ValueError('owner metadata path is not allowed')
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            budget.check()
            new_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(file_fd, 'rb') as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError('owner metadata is not a regular file')
            maximum = min(maximum, budget.remaining_bytes)
            if os.fstat(handle.fileno()).st_size > maximum:
                raise ValueError('owner metadata exceeds per-file or aggregate read budget')
            data = handle.read(maximum + 1)
            budget.remaining_bytes -= len(data)
            budget.check()
            if len(data) > maximum:
                raise ValueError('owner metadata exceeds per-file or aggregate read budget')
            return data
    finally:
        os.close(fd)


def _direct_index(records: dict, budget: _Budget) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for name, row in records.items():
        budget.check()
        prefix, _, basename = name.rpartition('/')
        index.setdefault(prefix, {})[basename] = row
    return index


def _directory(row: dict) -> bool:
    return stat.S_ISDIR(row['mode'])


def _regular(row: dict) -> bool:
    return stat.S_ISREG(row['mode'])


def _homebrew(root: Path, records: dict, metadata: dict, budget: _Budget, direct: dict) -> str:
    download_prefix = '' if root.name == 'downloads' else 'downloads'
    if download_prefix:
        top = direct.get('', {})
        if 'downloads' not in top or not _directory(top['downloads']):
            raise ValueError('Homebrew downloads layout missing; inspect exact downloads child')
        for name, row in top.items():
            budget.check()
            if name in ('downloads', 'api') and _directory(row):
                continue
            if stat.S_ISLNK(row['mode']) and 'downloads/' in row.get('link', ''):
                continue
            if name == '.DS_Store' and _regular(row):
                continue
            raise ValueError('Homebrew root contains other state; select its qualified downloads child instead')
        for name, row in records.items():
            budget.check()
            if name.startswith('api/'):
                if not _regular(row) or '/' in name[4:] or not name.endswith(('.json', '.jws.json')):
                    raise ValueError('unrecognized Homebrew API cache layout; select downloads child instead')
    downloads = direct.get(download_prefix, {})
    if not downloads:
        raise ValueError('no cached Homebrew downloads found')
    for name, row in downloads.items():
        budget.check()
        if not _regular(row) or not HASHED_DOWNLOAD.fullmatch(name) or name.endswith(('.incomplete', '.lock')):
            raise ValueError('unrecognized or incomplete Homebrew download; owner review required')
    return 'Homebrew hashed download assets and API cache; reinstall/download through the owning formula or cask'


def _node_gyp(root: Path, records: dict, metadata: dict, budget: _Budget, direct: dict) -> str:
    versions = direct.get('', {})
    if not versions:
        raise ValueError('no versioned Node headers found')
    for name, child in records.items():
        budget.check()
        version, separator, relative = name.partition('/')
        if not separator or relative == 'installVersion':
            continue
        if not relative.startswith('include') or not (_directory(child) or (_regular(child) and name.endswith(('.h', '.gypi', '.gyp')))):
            raise ValueError('node-gyp cache contains non-header state')
    for version, row in versions.items():
        budget.check()
        if not SEMVER.fullmatch(version) or not _directory(row):
            raise ValueError('node-gyp cache contains unrecognized top-level state')
        if set(direct.get(version, {})) != {'include', 'installVersion'}:
            raise ValueError('node-gyp version is not a supported Node header layout')
        install = _read_owner_file(root, f'{version}/installVersion', 64, budget=budget)
        if not re.fullmatch(rb'\d+\s*', install):
            raise ValueError('node-gyp installVersion is invalid')
        header_name = f'{version}/include/node/node_version.h'
        header = _read_owner_file(root, header_name, 65536, budget=budget)
        for part, expected in zip(('MAJOR', 'MINOR', 'PATCH'), version.split('.')):
            if not re.search(rb'#\s*define\s+NODE_' + part.encode() + rb'_VERSION\s+' + expected.encode() + rb'\b', header):
                raise ValueError('Node header version disagrees with cache directory')
        metadata[f'{version}/installVersion'] = install
        metadata[header_name] = header
    return 'Versioned Node development headers; node-gyp install <version> downloads replacement headers'


def _cypress(root: Path, records: dict, metadata: dict, budget: _Budget, direct: dict) -> str:
    child_root = SEMVER.fullmatch(root.name) is not None
    versions = {root.name: {'mode': stat.S_IFDIR}} if child_root else direct.get('', {})
    if not versions:
        raise ValueError('no versioned Cypress binary found')
    for version, row in versions.items():
        budget.check()
        if not SEMVER.fullmatch(version) or not _directory(row):
            raise ValueError('Cypress cache contains non-binary state; select qualified semver version children')
        prefix = '' if child_root else version + '/'
        top = direct.get('' if child_root else version, {})
        bundle = 'Cypress.app' if 'Cypress.app' in top else 'Cypress'
        if bundle not in top or not _directory(top[bundle]) or set(top) - {bundle, 'binary_state.json'}:
            raise ValueError('Cypress version contains non-binary state')
        package_name = prefix + bundle + '/' + ('Contents/Resources/app/package.json' if bundle.endswith('.app') else 'resources/app/package.json')
        package_bytes = _read_owner_file(root, package_name, budget=budget)
        package = json.loads(package_bytes)
        if not isinstance(package, dict) or package.get('version') != version or package.get('name') not in ('cypress', '@packages/server'):
            raise ValueError('Cypress binary package identity/version is not established')
        executable = prefix + bundle + '/' + ('Contents/MacOS/Cypress' if bundle.endswith('.app') else 'Cypress')
        if executable not in records or not _regular(records[executable]):
            raise ValueError('Cypress binary executable missing')
        if 'binary_state.json' in top and not _regular(top['binary_state.json']):
            raise ValueError('Cypress install state is not a regular file')
        metadata[package_name] = package_bytes
    return 'Versioned Cypress installer binaries; reinstall that Cypress version using its package CLI'


def cache_children(path: Path, rule: dict[str, Any]) -> list[dict[str, Any]]:
    """Discover only immediate Cypress version directories; never recurse profiles."""
    if rule.get('owner') != 'cypress' or rule.get('parent_path') or SEMVER.fullmatch(path.name):
        return []
    root = path.expanduser().absolute()
    expected = Path(rule['path']).expanduser().absolute()
    if root != expected or root.is_symlink() or root.resolve(strict=True) != root:
        raise ValueError('Cypress discovery requires its exact canonical owner root')
    children = []
    with os.scandir(root) as entries:
        for index, entry in enumerate(entries):
            if index >= 1000:
                raise ValueError('Cypress version discovery exceeds entry budget')
            if SEMVER.fullmatch(entry.name) and entry.is_dir(follow_symlinks=False):
                child = dict(rule, path=str(root / entry.name), parent_path=str(root))
                children.append(child)
    return sorted(children, key=lambda child: child['path'])


def _cargo_archives(root: Path, records: dict, metadata: dict, budget: _Budget, direct: dict) -> str:
    registries = direct.get('', {})
    if not registries:
        raise ValueError('no crates.io archive cache found')
    for registry, row in registries.items():
        budget.check()
        if not re.fullmatch(r'(?:index\.crates\.io|github\.com)-[0-9a-f]{16}', registry) or registry.startswith('github.com-') and registry != 'github.com-1ecc6299db9ec823' or not _directory(row):
            raise ValueError('private or unknown Cargo registry requires its own recovery evidence')
        for name, archive in direct.get(registry, {}).items():
            budget.check()
            if not _regular(archive) or not PUBLIC_CRATE.fullmatch(name):
                raise ValueError('Cargo archive cache contains unexpected state')
    return 'Published crates.io .crate downloads; Cargo fetch redownloads the dependency versions'


def cache_recovery(path: Path, rule: dict[str, Any], *, max_entries: int = 100000, timeout: float = 10.0, max_owner_bytes: int = 4 * 1024 * 1024, max_owner_reads: int = 512) -> dict[str, Any]:
    result = {'verified': False, 'level': 'none_or_unknown', 'method': rule.get('recovery', 'owner recovery unknown'),
              'reason': 'owner cache recovery is not established', 'fingerprints': {}}
    owner = rule.get('owner')
    if owner == 'claude':
        result['reason'] = 'VM bundles may include mutable runtime data; require an installed-app layout/restore contract before qualifying an exact bundle'
        return result
    if owner == 'playwright':
        result['reason'] = 'MCP caches can contain persistent login profiles; qualify browser-download revisions separately and retain all mcp-* profiles'
        return result
    handlers = {'homebrew': _homebrew, 'node-gyp': _node_gyp, 'cypress': _cypress}
    if owner == 'cargo' and path.name == 'cache':
        handlers['cargo'] = _cargo_archives
    if owner not in handlers:
        result['reason'] = 'This cache mixes source or execution state; inspect a disposable owner-specific subset instead of deleting the whole root'
        return result
    try:
        budget = _Budget(timeout, max_owner_bytes, max_owner_reads)
        root = path.expanduser().absolute()
        expected = Path(rule['path']).expanduser().absolute()
        if root != expected or root.is_symlink() or root.resolve(strict=True) != root or not root.is_dir():
            raise ValueError('cache must be the exact canonical nonsymlink owner path')
        if rule.get('parent_path') and (owner != 'cypress' or root.parent != Path(rule['parent_path']) or not SEMVER.fullmatch(root.name)):
            raise ValueError('invalid owner child boundary')
        records, metadata = _inventory(root, max_entries, budget)
        direct = _direct_index(records, budget)
        method = handlers[owner](root, records, metadata, budget, direct)
        budget.check()
        fingerprint = hashlib.sha256(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        owner_hashes = {}
        for name, data in sorted(metadata.items()):
            budget.check()
            owner_hashes[name] = hashlib.sha256(data).hexdigest()
        budget.check()
        result.update(verified=True, level='regenerable', method=method,
                      reason='Recognized disposable owner download layout; regeneration requires download, not guaranteed bit-identical restoration',
                      adapter=f'{owner}_download_cache_v1', download_required=True, rebuild_cost='owner reinstall/download',
                      download_bytes='unknown', source=SOURCES[owner],
                      fingerprints={'inventory_sha256': fingerprint, 'owner_metadata_sha256': owner_hashes})
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result['reason'] = str(exc) if isinstance(exc, ValueError) else 'owner cache metadata unavailable or invalid'
    return result
