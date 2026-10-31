#!/usr/bin/env python3
"""Optional bounded Mole observation; no cleanup, installation or configuration."""
from __future__ import annotations
import argparse
import fnmatch
import datetime as dt
import json
import os
from pathlib import Path
import selectors
import re
import shutil
import subprocess
import time
from typing import Any
from fs_compare import exclusive_write

MAX_BYTES = 2 * 1024 * 1024
PROTECTED_COMPONENTS = {'.ssh', '.aws', '.azure', '.gnupg', '.kube', '.config', 'keychains', 'vault', 'vaults', 'credentials', 'secrets', 'cloudstorage', 'mobile documents', 'mail', 'messages', 'photos library.photoslibrary', 'documents', 'downloads', 'desktop', 'pictures', 'movies', 'music'}
PROTECTED_PATTERNS = ('.env*', '*.pem', '*.key', '*.p12', '*.keychain*', '*.photoslibrary')


def bounded_run(argv: list[str], timeout: float, max_bytes: int = MAX_BYTES) -> dict:
    """Drain both pipes under one memory/time budget. Never expose stderr content."""
    started = time.monotonic()
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd='/', stdin=subprocess.DEVNULL)
    buffers = {'stdout': bytearray(), 'stderr': bytearray()}
    status = 'complete'
    with selectors.DefaultSelector() as selector:
        for stream, name in ((process.stdout, 'stdout'), (process.stderr, 'stderr')):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        try:
            while selector.get_map():
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    status = 'timeout'
                    break
                for key, _ in selector.select(min(remaining, .1)):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    buffers[key.data].extend(chunk)
                    if sum(map(len, buffers.values())) > max_bytes:
                        status = 'output_limit'
                        break
                if status != 'complete':
                    break
            if status != 'complete':
                process.kill()
            process.wait(timeout=max(.1, timeout - (time.monotonic() - started)))
        except (BaseException,):
            if process.poll() is None:
                process.kill()
            process.wait()
            raise
        finally:
            process.stdout.close()
            process.stderr.close()
    return {'status': status, 'returncode': process.returncode,
            'stdout': bytes(buffers['stdout'][:max_bytes]), 'stderr_present': bool(buffers['stderr'])}


def finite_number(value: Any) -> bool:
    import math
    return type(value) in (int, float) and math.isfinite(value)


def filter_fields(value: Any, fields: tuple[str, ...]) -> dict:
    if not isinstance(value, dict):
        return {}
    return {key: value[key] for key in fields if key in value and type(value[key]) in (str, int, float, bool, type(None))}


def normalize(operation: str, data: Any) -> tuple[str, dict]:
    if not isinstance(data, dict):
        raise ValueError('Mole returned an unexpected document')
    if operation == 'analyze':
        status = data.get('scan_status')
        if status not in ('complete', 'partial', 'unavailable'):
            raise ValueError('Mole scan_status missing or unsupported')
        result = filter_fields(data, ('path', 'scan_status', 'total_size', 'total_files'))
        if status == 'unavailable':
            result['total_size'] = None
            result['total_files'] = None
        result['entries'] = []
        entries = data.get('entries', [])
        if not isinstance(entries, list):
            raise ValueError('invalid Mole entries')
        for item in entries:
            if not isinstance(item, dict) or item.get('scan_status') not in ('complete', 'partial', 'unavailable'):
                raise ValueError('missing entry coverage marker')
            row = filter_fields(item, ('name', 'path', 'scan_status', 'size', 'is_dir', 'insight', 'cleanable', 'last_access'))
            if row['scan_status'] == 'unavailable':
                row['size'] = None
            # Recognition by Mole does not grant lifecycle deletion eligibility.
            row['classification'] = 'unknown'
            row['supported_action'] = 'inventory_only'
            result['entries'].append(row)
        result['size_semantics'] = 'partial sizes are lower bounds; size is not physical reclaim'
        return status, result
    if operation == 'status':
        if not isinstance(data.get('memory'), dict) or not isinstance(data.get('disks'), list):
            raise ValueError('unsupported Mole status shape')
        result = {'memory': filter_fields(data['memory'], ('pressure', 'total', 'used', 'available', 'swap_used')),
                  'disks': [filter_fields(row, ('name', 'mount', 'path', 'total', 'used', 'free', 'available')) for row in data['disks']]}
        return 'complete', result
    if operation == 'history':
        if not isinstance(data.get('sessions'), list) or not isinstance(data.get('deletions'), list):
            raise ValueError('unsupported Mole history shape')
        return 'complete', {
            'sessions': [filter_fields(row, ('command', 'run_id', 'attribution', 'started_at', 'ended_at', 'items', 'size', 'failed_tasks')) for row in data['sessions']],
            'deletions': [filter_fields(row, ('timestamp', 'mode', 'status', 'size_kb', 'path')) for row in data['deletions']],
            'note': 'Bounded history is not proof that no other actions occurred; previews are not removals.'}
    raise ValueError('unsupported observation operation')


def observe(operation: str, root: str | None, timeout: float = 10, limit: int = 20) -> dict:
    if operation not in ('analyze', 'status', 'history'):
        raise ValueError('unsupported observation operation')
    if not finite_number(timeout) or not 0 < timeout <= 60 or type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError('invalid timeout or history limit')
    if operation == 'analyze' and not root:
        raise ValueError('analyze requires an explicit root')
    if operation != 'analyze' and root:
        raise ValueError('root is only supported for analyze')
    canonical_root = None
    if root:
        path = Path(root).expanduser()
        if not path.is_absolute() or path.is_symlink() or not path.is_dir():
            raise ValueError('root must be an absolute existing nonsymlink directory')
        canonical = path.resolve(strict=True)
        if path != canonical:
            raise ValueError('analyze root must use its canonical path without symlinked ancestors')
        if canonical == Path(canonical.anchor) or canonical == Path.home().resolve():
            raise ValueError('analyze requires a bounded directory below filesystem and home roots')
        if any(component.lower() in PROTECTED_COMPONENTS or any(fnmatch.fnmatchcase(component.lower(), pattern) for pattern in PROTECTED_PATTERNS) for component in canonical.parts):
            raise ValueError('protected or cloud root is excluded')
        canonical_root = str(canonical)
    result = {'schema': 'filesystem-lifecycle/observation-v1', 'adapter': 'mole', 'operation': operation,
              'observed_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'root': canonical_root,
              'status': 'unavailable', 'version': None, 'data': None,
              'capability': 'observation_only', 'coverage_gaps': []}
    executable = shutil.which('mo')
    if executable is None:
        result['coverage_gaps'].append('Mole is not installed; no installation attempted.')
        return result
    result['executable'] = str(Path(executable).resolve())
    try:
        version = bounded_run([executable, '--version'], timeout, 4096)
        if version['status'] != 'complete' or version['returncode'] != 0 or version['stderr_present']:
            raise ValueError('Mole version probe incomplete')
        version_text = version['stdout'].decode('utf-8').strip()
        # Keep version output bounded and reject controls other than normal line breaks.
        if not version_text or len(version_text) > 1024 or any(ord(c) < 32 and c not in '\n\t\r' for c in version_text):
            raise ValueError('Mole version invalid')
        version_match = re.search(r'\b(?:Mole\s+)?[vV]?(\d+\.\d+\.\d+)(?:[-+][A-Za-z0-9.]+)?', version_text)
        if not version_match or 'macos' not in version_text.lower():
            raise ValueError('Mole macOS edition/version was not established')
        result['version'] = version_match.group(1)
        result['edition'] = 'macOS'
        argv = [executable, operation, '--json']
        if operation == 'analyze':
            argv.append(canonical_root)
        elif operation == 'history':
            argv += ['--limit', str(limit)]
        probe = bounded_run(argv, timeout)
        if probe['status'] != 'complete' or probe['returncode'] != 0:
            result['coverage_gaps'].append('Mole probe failed, timed out, or exceeded its output budget.')
            return result
        data = json.loads(probe['stdout'], parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
        status, normalized = normalize(operation, data)
        if probe['stderr_present']:
            status = 'partial' if status != 'unavailable' else status
            result['coverage_gaps'].append('Mole emitted diagnostic output; coverage is uncertain. Raw diagnostics were omitted.')
        result['status'], result['data'] = status, normalized
        if status != 'complete':
            result['coverage_gaps'].append('Mole reported incomplete coverage; unavailable sizes remain unknown.')
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        result['coverage_gaps'].append('Mole observation could not be validated; no fallback action attempted.')
    return result


def observe_command(args: argparse.Namespace) -> int:
    try:
        document = observe(args.operation, args.root, args.timeout, args.limit)
        rendered = json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + '\n'
        if args.output:
            exclusive_write(args.output, rendered)
        else:
            print(rendered, end='')
        return 0 if document['status'] == 'complete' else 1
    except (ValueError, OSError):
        print('observation unavailable: invalid scope, arguments, or output destination')
        return 2


def register_commands(subparsers: Any) -> None:
    parser = subparsers.add_parser('observe', help='optional bounded observation through installed Mole')
    parser.add_argument('--adapter', choices=('mole',), required=True)
    parser.add_argument('--operation', choices=('analyze', 'status', 'history'), required=True)
    parser.add_argument('--root')
    parser.add_argument('--timeout', type=float, default=10)
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--output')
    parser.set_defaults(func=observe_command)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    register_commands(parser.add_subparsers(dest='command', required=True))
    args = parser.parse_args()
    raise SystemExit(args.func(args))
