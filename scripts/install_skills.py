#!/usr/bin/env python3
"""Preview or install complete skill packages offline, preserving local changes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from validate_repo import IGNORED, skill_dependencies, validate_skill

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = '.siftable-skills.json'
TRANSACTION = '.siftable-skills-transaction'
NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
PROFILES = {
    'all': None,
    'engineering': ('tometo-mode', 'pstack-architect', 'pstack-investigate', 'pstack-interrogate', 'pstack-verify',
                    'pstack-create-verification-skill', 'pstack-maintain-verification-skill', 'zig', 'typescript',
                    'rust', 'go', 'c-systems-programming', 'react-best-practices', 'css'),
    'languages': ('zig', 'typescript', 'rust', 'go', 'c-systems-programming', 'react-best-practices', 'css'),
}


def read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'Expected an ordinary JSON file: {path}')
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f'Expected a JSON object: {path}')
    return value


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + '.new')
    if temporary.exists() or temporary.is_symlink():
        raise ValueError(f'Refusing existing temporary file: {temporary}')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def check_path(path: Path) -> Path:
    """Reject symlink ancestors without following them or creating directories."""
    absolute = Path(os.path.abspath(path.expanduser()))
    for current in (absolute, *absolute.parents):
        if current.is_symlink():
            raise ValueError(f'Symlink destination component: {current}')
        if current.exists() and not current.is_dir():
            raise ValueError(f'Destination component is not a directory: {current}')
    return absolute


def inventory(root: Path) -> dict[str, Path]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f'Invalid skills source: {root}')
    found = {}
    for path in sorted(root.iterdir()):
        if path.name.startswith('.'):
            continue
        if path.is_symlink():
            raise ValueError(f'Symlink source: {path}')
        if path.is_dir():
            if not NAME.fullmatch(path.name) or len(path.name) > 64:
                raise ValueError(f'Invalid skill name: {path.name}')
            found[path.name] = path
    if not found:
        raise ValueError('No skills found')
    return found


def select_skills(root: Path, names: list[str] | None = None, profile: str = 'all') -> list[str]:
    found = inventory(root)
    requested = names or (list(PROFILES[profile]) if PROFILES[profile] is not None else list(found))
    pending, selected = list(requested), set()
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        if name not in found:
            raise ValueError(f'Missing selected skill or sibling dependency: {name}')
        errors = validate_skill(found[name])
        if errors:
            raise ValueError('\n'.join(errors))
        selected.add(name)
        pending.extend(skill_dependencies(found[name], root) - selected)
    return sorted(selected)


def tree_digest(root: Path) -> str:
    """Hash names, bytes, directory structure and executable bits; exclude caches."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f'Expected ordinary skill directory: {root}')
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Symlink in skill package: {path}')
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or path.suffix in {'.pyc', '.pyo'}:
            continue
        if not path.is_file() and not path.is_dir():
            raise ValueError(f'Special file in skill package: {path}')
        digest.update(('D' if path.is_dir() else 'F').encode())
        digest.update(str(relative).encode() + b'\0')
        if path.is_file():
            digest.update(str(path.stat().st_mode & 0o111).encode() + b'\0')
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def copy_skill(source: Path, destination: Path) -> None:
    tree_digest(source)  # Reject links and special files before copytree can follow them.
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*IGNORED, '*.pyc', '*.pyo'))
    if tree_digest(source) != tree_digest(destination):
        raise ValueError(f'Staged package differs from source: {source.name}')


def load_manifest(destination: Path) -> dict:
    path = destination / MANIFEST
    if not path.exists() and not path.is_symlink():
        return {'version': 1, 'installer': 'siftable-skills', 'skills': {}}
    result = read_json(path)
    if result.get('version') != 1 or result.get('installer') != 'siftable-skills' or not isinstance(result.get('skills'), dict):
        raise ValueError('Unrecognized installation manifest; refusing to adopt it')
    for name, value in result['skills'].items():
        if not NAME.fullmatch(name) or not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value):
            raise ValueError('Invalid installation manifest entry')
    return result


def recover(destination: Path) -> None:
    """Rollback an interrupted transaction, refusing edits made after interruption."""
    destination = check_path(destination)
    transaction = destination / TRANSACTION
    if transaction.is_symlink() or not transaction.is_dir():
        raise ValueError('No ordinary transaction directory is available for recovery')
    journal = read_json(transaction / 'journal.json')
    if journal.get('version') != 1 or journal.get('state') not in {'staged', 'committed'}:
        raise ValueError('Unrecognized recovery journal')
    entries = journal.get('entries', [])
    if not isinstance(entries, list) or not entries:
        raise ValueError('Invalid recovery journal entries')
    for entry in entries:
        if not isinstance(entry, dict) or not NAME.fullmatch(entry.get('name', '')):
            raise ValueError('Invalid recovery skill name')
        if not re.fullmatch(r'[0-9a-f]{64}', entry.get('new', '')):
            raise ValueError('Invalid recovery hash')
        if entry.get('old') is not None and not re.fullmatch(r'[0-9a-f]{64}', entry['old']):
            raise ValueError('Invalid previous hash')
    manifest_path = destination / MANIFEST
    current_manifest = load_manifest(destination) if manifest_path.exists() or manifest_path.is_symlink() else None
    if current_manifest not in (journal.get('old_manifest'), journal.get('new_manifest')):
        raise ValueError('Changed installation manifest prevents automatic recovery')
    if journal['state'] == 'committed':
        for entry in entries:
            if tree_digest(destination / entry['name']) != entry['new']:
                raise ValueError('Committed skills changed; preserve the transaction for manual review')
        current = load_manifest(destination)
        if current != journal.get('new_manifest'):
            raise ValueError('Committed manifest changed; preserve the transaction for manual review')
        shutil.rmtree(transaction)
        return
    # Preflight every current and saved package before making recovery mutations.
    for entry in entries:
        target = destination / entry['name']
        backup = transaction / 'backup' / entry['name']
        stage = transaction / 'stage' / entry['name']
        if entry['old'] is not None and not backup.exists():
            if not target.exists() or tree_digest(target) != entry['old']:
                raise ValueError(f'Missing previous package or backup prevents recovery: {entry["name"]}')
        if entry['old'] is None and stage.exists() and (target.exists() or target.is_symlink()):
            raise ValueError(f'Unowned conflict prevents recovery: {target}')
        if backup.exists() or backup.is_symlink():
            if entry['old'] is None or tree_digest(backup) != entry['old']:
                raise ValueError(f'Changed recovery backup: {backup}')
        if target.exists() or target.is_symlink():
            actual = tree_digest(target)
            allowed = {entry['new']} if backup.exists() else {entry['old'], entry['new']}
            if actual not in allowed:
                raise ValueError(f'Changed skill prevents automatic recovery: {target}')
    for entry in reversed(entries):
        target = destination / entry['name']
        backup = transaction / 'backup' / entry['name']
        if backup.exists():
            if target.exists():
                shutil.rmtree(target)
            os.replace(backup, target)
        elif entry['old'] is None and target.exists():
            shutil.rmtree(target)
    old_manifest = journal.get('old_manifest')
    if old_manifest is None:
        manifest = destination / MANIFEST
        if manifest.is_symlink():
            raise ValueError('Symlink manifest prevents recovery')
        if manifest.exists():
            manifest.unlink()
    else:
        write_json(destination / MANIFEST, old_manifest)
    shutil.rmtree(transaction)


def install(source: Path, destination: Path, names: list[str] | None = None, *, profile: str = 'all',
            apply: bool = False, update: bool = False) -> list[tuple[str, str]]:
    destination = check_path(destination)
    if (destination / TRANSACTION).exists() or (destination / TRANSACTION).is_symlink():
        raise ValueError('Interrupted transaction exists; inspect it and run --recover before installing')
    selected = select_skills(source, names, profile)
    manifest = load_manifest(destination)
    actions, entries = [], []
    for name in selected:
        target = destination / name
        desired = tree_digest(source / name)
        previous = manifest['skills'].get(name)
        if target.exists() or target.is_symlink():
            actual = tree_digest(target)
            if previous is None:
                raise ValueError(f'Unmanaged skill exists; refusing adoption or replacement: {name}')
            if actual != previous:
                raise ValueError(f'Locally changed managed skill; preserve or relocate it before updating: {name}')
            if desired == actual:
                actions.append((name, 'unchanged'))
                continue
            if not update:
                raise ValueError(f'Managed skill differs; pass --update to replace: {name}')
            action, old = 'update', actual
        else:
            if previous is not None:
                raise ValueError(f'Managed skill is missing; manifest requires review: {name}')
            action, old = 'install', None
        actions.append((name, action))
        entries.append({'name': name, 'old': old, 'new': desired})
    if not apply or not entries:
        return actions
    destination.mkdir(parents=True, exist_ok=True)
    transaction = destination / TRANSACTION
    transaction.mkdir()  # Exclusive mkdir also rejects another active installer.
    journal_written = False
    try:
        (transaction / 'stage').mkdir()
        (transaction / 'backup').mkdir()
        for entry in entries:
            copy_skill(source / entry['name'], transaction / 'stage' / entry['name'])
            if tree_digest(transaction / 'stage' / entry['name']) != entry['new']:
                raise ValueError('Source changed while staging; retry from an immutable checkout')
        updated = {'version': 1, 'installer': 'siftable-skills', 'skills': dict(manifest['skills'])}
        updated['skills'].update({entry['name']: entry['new'] for entry in entries})
        journal = {'version': 1, 'state': 'staged', 'entries': entries,
                   'old_manifest': manifest if (destination / MANIFEST).exists() else None, 'new_manifest': updated}
        write_json(transaction / 'journal.json', journal)
        journal_written = True
        # Revalidate the complete plan immediately before any replacement.
        if load_manifest(destination) != manifest:
            raise ValueError('Manifest changed during staging')
        for entry in entries:
            target = destination / entry['name']
            if entry['old'] is None:
                if target.exists() or target.is_symlink():
                    raise ValueError(f'Conflict appeared during staging: {target}')
            elif tree_digest(target) != entry['old']:
                raise ValueError(f'Skill changed during staging: {target}')
        for entry in entries:
            name = entry['name']
            if entry['old'] is not None:
                os.replace(destination / name, transaction / 'backup' / name)
            os.replace(transaction / 'stage' / name, destination / name)
        for entry in entries:
            if tree_digest(destination / entry['name']) != entry['new']:
                raise ValueError('Installed package readback failed')
        write_json(destination / MANIFEST, updated)
        if load_manifest(destination) != updated:
            raise ValueError('Manifest readback failed')
        journal['state'] = 'committed'
        write_json(transaction / 'journal.json', journal)
    except BaseException:
        if journal_written:
            recover(destination)
        else:
            shutil.rmtree(transaction)
        raise
    # Keep failures of final housekeeping recoverable, after the committed marker.
    shutil.rmtree(transaction)
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'skills', help='offline source tree (default: repository skills/)')
    parser.add_argument('--destination', type=Path, required=True, help='explicit installation directory')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--skill', action='append', help='select a skill; repeat for multiple; includes sibling dependencies')
    selection.add_argument('--profile', choices=PROFILES, default='all')
    parser.add_argument('--apply', action='store_true', help='apply the plan; omitted means read-only dry run')
    parser.add_argument('--update', action='store_true', help='replace only unchanged skills managed by this installer')
    parser.add_argument('--recover', action='store_true', help='with --apply, rollback or finish an interrupted transaction')
    args = parser.parse_args()
    try:
        if args.recover:
            if not args.apply:
                raise ValueError('Recovery mutates installation state and requires --apply')
            recover(check_path(args.destination))
            print('Recovered installation transaction')
            return 0
        actions = install(args.source, args.destination, args.skill, profile=args.profile, apply=args.apply, update=args.update)
        for name, action in actions:
            print(f'{action}: {name}')
        print('Installation verified' if args.apply else 'Dry run; no files changed. Pass --apply to install.')
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
