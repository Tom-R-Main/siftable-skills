#!/usr/bin/env python3
"""Passive comparison of explicitly supplied lifecycle records; no live discovery."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMAS = {'filesystem-lifecycle/v2', 'filesystem-lifecycle/v3', 'filesystem-lifecycle/doctor-v1'}
MAX_INPUT_BYTES = 16 * 1024 * 1024


def timestamp(value: Any) -> dt.datetime:
    if not isinstance(value, str):
        raise ValueError('missing timestamp')
    result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timestamp must include timezone')
    if result > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
        raise ValueError('timestamp is in the future')
    return result


def digest(document: dict) -> str:
    body = dict(document)
    body.pop('integrity', None)
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def safe_path(path: str) -> Path:
    target = Path(path).expanduser()
    for component in target.parts:
        lowered = component.lower()
        if (lowered.startswith('.env') or lowered.endswith(('.pem', '.p12', '.key'))
                or lowered in ('.ssh', '.gnupg', 'credentials', 'credentials.json', 'secrets.json')):
            raise ValueError('credential-shaped input/output is excluded')
    return target


def exclusive_write(path: str, content: str) -> None:
    target = safe_path(path)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def load_record(path: str) -> dict:
    fd = os.open(safe_path(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError('input must be a regular file')
        raw = handle.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError('record exceeds input limit')
    document = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON number')))
    if not isinstance(document, dict) or document.get('schema') not in SCHEMAS:
        raise ValueError('unsupported lifecycle record schema')
    integrity = document.get('integrity')
    if integrity is not None and (not isinstance(integrity, dict) or integrity.get('algorithm') != 'sha256' or integrity.get('digest') != digest(document)):
        raise ValueError('record checksum mismatch')
    return document


def path_value(row: dict) -> str:
    value = row.get('canonical_path') or row.get('path')
    if not isinstance(value, str) or not value.startswith('/') or '..' in PurePosixPath(value).parts or '\x00' in value:
        raise ValueError('resource requires an absolute canonical path')
    return str(PurePosixPath(value))


def identity(row: dict) -> tuple:
    value = row.get('identity') or {}
    if not isinstance(value, dict):
        raise ValueError('invalid resource identity')
    for key in ('device', 'inode'):
        if value.get(key) is not None and (type(value[key]) is not int or value[key] < 0):
            raise ValueError('invalid numeric resource identity')
    if value.get('mount_id') is not None and not isinstance(value['mount_id'], str):
        raise ValueError('invalid mount identity')
    return value.get('device'), value.get('mount_id'), value.get('inode')


def resources(document: dict) -> dict[str, dict]:
    rows = document.get('resources') if document.get('schema') == 'filesystem-lifecycle/doctor-v1' else document.get('candidates')
    if not isinstance(rows, list):
        raise ValueError('comparison requires audit manifests or doctor inventories')
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('invalid candidate')
        path = path_value(row)
        if path in result:
            raise ValueError('duplicate resource path')
        identity(row)
        if not isinstance(row.get('storage', {}), dict) or not isinstance(row.get('recovery', {}), dict):
            raise ValueError('invalid resource evidence')
        result[path] = row
    return result


def integer(value: Any) -> int | None:
    return value if type(value) is int else None


def same_filesystem(left: dict, right: dict) -> bool:
    a, b = identity(left), identity(right)
    left_fsid = (left.get('identity') or {}).get('filesystem_id')
    right_fsid = (right.get('identity') or {}).get('filesystem_id')
    if left_fsid is not None and right_fsid is not None:
        return a[0] is not None and a[0] == b[0] and left_fsid == right_fsid
    return a[0] is not None and a[1] is not None and a[:2] == b[:2]


def complete_scope(before: dict, after: dict) -> bool:
    if before.get('schema') != after.get('schema'):
        return False
    if after.get('schema') == 'filesystem-lifecycle/doctor-v1':
        return (before.get('scope') == after.get('scope') and before.get('limits_per_root') == after.get('limits_per_root')
                and after.get('status') == 'complete' and not after.get('coverage_gaps')
                and isinstance(after.get('scans'), list) and all(scan.get('status') == 'complete' for scan in after['scans']))
    evidence = after.get('evidence') or {}
    discovery = evidence.get('discovery') or {}
    assessment = evidence.get('candidate_assessment') or {}
    planning = after.get('planning') or {}
    return (before.get('scope') == after.get('scope') and discovery.get('scan_complete') is True
            and assessment.get('deferred_unassessed_candidate_count', 0) == 0
            and planning.get('mode') != 'target_limited')


def source_digest(receipt: dict) -> Any:
    value = receipt.get('source_manifest_digest') or receipt.get('manifest_digest')
    source = receipt.get('manifest') or receipt.get('source_manifest') or {}
    return value or (source.get('digest') if isinstance(source, dict) else None)


def filesystem(document: dict) -> Any:
    value = document.get('filesystem') or (document.get('authorization') or {}).get('envelope', {}).get('filesystem')
    if not isinstance(value, dict) or type(value.get('device')) is not int or type(value.get('filesystem_id')) not in (str, int):
        return None
    return {'device': value['device'], 'filesystem_id': str(value['filesystem_id'])}


def compare_records(before: dict, after: dict, receipts: list[dict]) -> dict:
    start, end = timestamp(before.get('generated_at')), timestamp(after.get('generated_at'))
    if end < start:
        raise ValueError('after manifest predates before manifest')
    old, new = resources(before), resources(after)
    prior_digest = before.get('integrity', {}).get('digest')
    events: dict[str, tuple[dt.datetime, dict]] = {}
    gaps = []
    old_fs, new_fs = filesystem(before), filesystem(after)
    filesystem_compatible = old_fs == new_fs and (old_fs is not None or before.get('schema') == after.get('schema') == 'filesystem-lifecycle/v2')
    if not filesystem_compatible:
        gaps.append('Manifest filesystem identities are missing or incompatible.')
    for receipt in receipts:
        when = timestamp(receipt.get('applied_at'))
        if not start <= when <= end:
            gaps.append('Receipt outside comparison interval was excluded.')
            continue
        results = receipt.get('results')
        if not isinstance(results, list):
            raise ValueError('receipt requires results')
        bound = (prior_digest is not None and source_digest(receipt) == prior_digest
                 and old_fs is not None and filesystem(receipt) == old_fs)
        if not bound:
            gaps.append('Unbound legacy or unrelated receipt cannot prove recreation.')
            continue
        for row in results:
            if not isinstance(row, dict):
                raise ValueError('invalid receipt result')
            if row.get('status') != 'removed':
                continue
            path = path_value(row)
            previous = old.get(path)
            # The manifest digest and exact ID bind a completed action to its frozen resource.
            if previous is None or row.get('id') != previous.get('id'):
                continue
            if row.get('identity') and identity(row) != identity(previous):
                gaps.append('Receipt resource identity disagrees with its source manifest.')
                continue
            completed = timestamp(row.get('completed_at') or receipt.get('completed_at') or receipt.get('applied_at'))
            if not when <= completed <= end:
                gaps.append('Receipt completion outside comparison interval was excluded.')
                continue
            if path not in events or completed > events[path][0]:
                events[path] = (completed, row)
    rows = []
    for path in sorted(old.keys() | new.keys()):
        previous, current = old.get(path), new.get(path)
        removal = events.get(path)
        seconds = None
        interval_delta = None
        if current is None:
            state = 'not_observed' if complete_scope(before, after) else 'not_assessed'
        elif previous is None:
            state = 'newly_observed'
        elif not filesystem_compatible or not same_filesystem(previous, current):
            state = 'identity_uncertain'
        elif removal:
            state = 'recreated'
            seconds = (end - removal[0]).total_seconds()
            interval_delta = integer(removal[1].get('interval_physical_free_delta_bytes'))
        elif identity(previous)[2] != identity(current)[2]:
            state = 'replaced_or_recreated'
        else:
            state = 'still_observed'
        resource = current or previous
        recovery = resource.get('recovery') or {}
        allocated = integer((current.get('storage') or {}).get('allocated_bytes')) if current else None
        old_allocated = integer((previous.get('storage') or {}).get('allocated_bytes')) if previous else None
        if allocated is not None and allocated < 0:
            raise ValueError('negative allocated footprint')
        recommendation = 'No prevention change justified by this comparison.'
        if state == 'recreated':
            if resource.get('kind') == 'generated_artifact':
                recommendation = 'Review dependency hydration and owner-supported shared-cache reuse for this project.'
            else:
                recommendation = 'Review the owning application\'s documented cache or retention settings before another purge.'
        rows.append({'path': path, 'id': resource.get('id'), 'owner': resource.get('owner'), 'state': state,
                     'current_allocated_bytes': allocated,
                     'allocated_change_bytes': allocated - old_allocated if allocated is not None and old_allocated is not None and previous and current and same_filesystem(previous, current) else None,
                     'seconds_since_removal': seconds, 'prior_interval_free_delta_bytes': interval_delta,
                     'recovery_method': recovery.get('method', 'unknown'),
                     'rebuild_cost': recovery.get('rebuild_cost', 'unknown'),
                     'download_bytes': recovery.get('download_bytes', 'unknown'),
                     'prevention': recommendation})
    return {'schema': 'filesystem-lifecycle/comparison-v1', 'before_at': start.isoformat(), 'after_at': end.isoformat(),
            'resources': rows, 'coverage_gaps': sorted(set(gaps)),
            'notes': ['Free-space deltas are volume-wide observations, not exclusive attribution.',
                      'Not observed does not prove deletion; checksums do not authenticate human approval.',
                      'No live paths, settings, history stores, or schedules were changed.']}


def cell(value: Any) -> str:
    return str('unknown' if value is None else value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def render(document: dict, format: str) -> str:
    if format == 'json':
        return json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + '\n'
    lines = ['| Resource | State | Current allocated bytes | Seconds since removal | Prior volume free delta | Prevention |',
             '|---|---|---:|---:|---:|---|']
    for row in document['resources']:
        lines.append('| ' + ' | '.join(cell(row.get(key)) for key in ('path', 'state', 'current_allocated_bytes', 'seconds_since_removal', 'prior_interval_free_delta_bytes', 'prevention')) + ' |')
    lines += ['', *document['notes'], '', *document['coverage_gaps']]
    return '\n'.join(lines) + '\n'


def compare_command(args: argparse.Namespace) -> int:
    try:
        result = compare_records(load_record(args.before), load_record(args.after), [load_record(p) for p in args.receipt])
        output = render(result, args.format)
        if args.output:
            exclusive_write(args.output, output)
        else:
            print(output, end='')
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(f'comparison unavailable: {type(exc).__name__}; validate input schemas, timestamps, and provenance')
        return 2


def register_commands(subparsers: Any) -> None:
    parser = subparsers.add_parser('compare', help='compare explicit manifests or doctor inventories and receipts without live scans')
    parser.add_argument('--before', required=True)
    parser.add_argument('--after', required=True)
    parser.add_argument('--receipt', action='append', default=[])
    parser.add_argument('--format', choices=('json', 'markdown'), default='markdown')
    parser.add_argument('--output')
    parser.set_defaults(func=compare_command)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    register_commands(parser.add_subparsers(dest='command', required=True))
    args = parser.parse_args()
    raise SystemExit(args.func(args))
