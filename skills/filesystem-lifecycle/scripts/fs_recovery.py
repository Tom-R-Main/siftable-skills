"""Practical owner-specific recovery evidence for generated project artifacts.

Evidence establishes a retained rebuild specification and owner-created output.
It does not promise bit-identical restoration or future registry availability.
No installs, network requests, or source mutations occur here.
"""
from __future__ import annotations
import hashlib
import base64
import csv
from email.parser import Parser
import io
import json
import os
from pathlib import Path, PurePosixPath
import fnmatch
import re
import shlex
import stat
import time
from contextlib import contextmanager
import tomllib


class Unqualified(ValueError):
    pass


@contextmanager
def regular_fd(path):
    path=Path(os.path.abspath(path)); fds=[]
    try:
        parent=os.open(path.anchor,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);fds.append(parent)
        for component in path.parts[1:-1]:
            parent=os.open(component,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent);fds.append(parent)
        fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent);fds.append(fd)
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):raise Unqualified('owner-listed file is not a regular file')
        yield fd,info
    finally:
        for fd in reversed(fds):os.close(fd)


class Evidence:
    def __init__(self, artifact):
        self.artifact = artifact.resolve(strict=True)
        self.hashes = {}
        self.read_bytes = 0

    def read(self, path):
        path = Path(os.path.abspath(path))
        if path.name.startswith('.env') or path.suffix in ('.pem', '.key', '.p12'):
            raise Unqualified('credential-shaped metadata is excluded; retain it without opening')
        with regular_fd(path) as (fd, info):
            limit=min(16*1024*1024, 64*1024*1024-self.read_bytes)
            if info.st_size > limit: raise Unqualified('metadata budget exceeded; inspect owner separately')
            chunks=[]; total=0
            while total <= limit:
                chunk=os.read(fd,min(1024*1024,limit+1-total))
                if not chunk: break
                chunks.append(chunk);total+=len(chunk)
            if total > limit: raise Unqualified('metadata grew beyond read budget')
            data=b''.join(chunks)
            after=os.fstat(fd)
            if (info.st_size,info.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                raise Unqualified('owner metadata changed during inspection')
            self.read_bytes+=total
            self.hashes[str(path)]=hashlib.sha256(data).hexdigest()
            return data.decode('utf-8')

    def json(self, path):
        value = json.loads(self.read(path))
        if not isinstance(value, dict):
            raise Unqualified(f'owner metadata must be an object: {Path(path).name}')
        return value

    def retained(self, path):
        path = Path(path).resolve(strict=True)
        if path == self.artifact or self.artifact in path.parents:
            raise Unqualified('local/editable source is inside the deletion candidate; retain or relocate source first')
        st = path.stat()
        self.hashes['local-source:' + str(path)] = f'{st.st_dev}:{st.st_ino}:{st.st_mtime_ns}'
        return path


def local_reference(value, parent, evidence):
    if not isinstance(value, str):
        return
    if value.startswith(('file:', 'link:')):
        value = value.split(':', 1)[1]
        return evidence.retained(parent / value)


def screen_tree(path, *, max_entries=1000000):
    """Metadata only; never follow package symlinks or inspect arbitrary bodies."""
    device = path.stat().st_dev
    count = 0
    stack = [path]
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            for item in entries:
                count += 1
                if count > max_entries:
                    raise Unqualified('metadata traversal budget exceeded; narrow the candidate')
                st = item.stat(follow_symlinks=False)
                if st.st_dev != device:
                    raise Unqualified('nested filesystem encountered; classify it separately')
                # Embedded repositories and actual environment files are concrete unique-state signals.
                if item.name in ('.git', '.hg', '.svn', '.ssh', '.aws', '.gnupg', 'Keychains') or item.name.lower().startswith('.env') or item.name.lower().endswith(('.pem', '.p12', '.key', '.sqlite', '.sqlite3', '.db', '.db-wal')):
                    raise Unqualified('embedded repository, credential-shaped or database state found; retain pending owner-specific evidence')
                if stat.S_ISDIR(st.st_mode):
                    stack.append(Path(item.path))


def npm_installation(path):
    """Find the retained project lock and its installed npm lock, without symlinks."""
    for ancestor in (path, *path.parents):
        if ancestor.name == 'node_modules' and (ancestor/'.package-lock.json').is_file() and (ancestor.parent/'package-lock.json').is_file():
            return ancestor
        if (ancestor/'package-lock.json').is_file() and (ancestor/'node_modules/.package-lock.json').is_file():
            return ancestor/'node_modules'
    raise Unqualified('npm installation lock missing; need the project and installed package-lock files')


def npm_records(installation, ev):
    parent = installation.parent
    spec = ev.json(parent/'package.json')
    lock = ev.json(parent/'package-lock.json')
    installed = ev.json(installation/'.package-lock.json')
    if lock.get('lockfileVersion') not in (2, 3) or installed.get('lockfileVersion') not in (2, 3):
        raise Unqualified('npm adapter supports package-lock v2/v3; inspect this lock format separately')
    packages = lock.get('packages'); actual = installed.get('packages')
    if not isinstance(packages, dict) or not isinstance(packages.get(''),dict) or not isinstance(actual, dict) or not actual:
        raise Unqualified('npm package records missing; regenerate or inspect installation metadata')
    def local(value, directory):
        source = local_reference(value, directory, ev)
        if source is not None and source.is_relative_to(installation):
            raise Unqualified('npm local source is inside the dependency installation')
    def specification(metadata, frozen, directory):
        for section in ('dependencies', 'devDependencies', 'optionalDependencies'):
            declared = metadata.get(section, {})
            if not isinstance(declared, dict) or declared != frozen.get(section, {}):
                raise Unqualified('package specification and lock disagree; reconcile them before reclaim')
            for value in declared.values(): local(value, directory)
    specification(spec, packages.get('', {}), parent)
    workspaces = spec.get('workspaces', [])
    if isinstance(workspaces, dict): workspaces = workspaces.get('packages', [])
    if not isinstance(workspaces, list) or any(not isinstance(p,str) for p in workspaces):
        raise Unqualified('malformed npm workspace declarations')
    if spec.get('workspaces', []) != packages.get('', {}).get('workspaces', []):
        raise Unqualified('workspace specification and lock disagree')
    workspace_paths = set()
    local_sources = {record.get('resolved') for record in packages.values()
                     if isinstance(record,dict) and record.get('link') and isinstance(record.get('resolved'),str)}
    for key, record in packages.items():
        parts = PurePosixPath(key).parts if isinstance(key,str) else ()
        if not isinstance(record, dict) or not isinstance(key,str) or key.startswith('/') or ('..' in parts and key not in local_sources) or '\\' in key:
            raise Unqualified('malformed npm lock entry')
        if record.get('link'):
            resolved = record.get('resolved')
            if not isinstance(resolved, str) or Path(resolved).is_absolute() or '://' in resolved or '\\' in resolved:
                raise Unqualified('npm local link has no retained source path')
            source = ev.retained(parent/resolved)
            if source.is_relative_to(installation):
                raise Unqualified('npm local source is inside the dependency installation')
            if resolved in packages and any(fnmatch.fnmatchcase(resolved,p) for p in workspaces):
                workspace_paths.add(resolved)
        local(record.get('resolved'), parent)
    for workspace in workspace_paths:
        ev.retained(parent/workspace)
        metadata = ev.json(parent/workspace/'package.json')
        specification(metadata, packages[workspace], parent/workspace)
        if metadata.get('version') != packages[workspace].get('version'):
            raise Unqualified('workspace package version differs from retained lock')
    for key, record in actual.items():
        if not isinstance(key,str) or not isinstance(record,dict) or key.startswith('/') or ('..' in PurePosixPath(key).parts and key not in local_sources) or '\\' in key or not (key.startswith('node_modules/') or key in workspace_paths or key in local_sources or any(key.startswith(w+'/node_modules/') for w in workspace_paths)):
            raise Unqualified('unsupported npm installation record path')
    return parent, packages, actual


def npm(path, ev):
    installation = npm_installation(path)
    ev.npm_installation_root = str(installation)
    parent, packages, actual = npm_records(installation, ev)
    owned = set(actual) | {key for key, record in packages.items() if record.get('link')}
    # Inspect only this candidate's installed packages. Workspace source remains
    # outside a root node_modules candidate, and is never traversed for deletion.
    for key in owned:
        package = parent/key
        if not package.is_relative_to(path): continue
        declared = packages.get(key)
        record = actual.get(key, declared)
        if not isinstance(declared, dict) or any(record.get(field) != declared.get(field) for field in ('version', 'resolved', 'integrity', 'link') if field in record):
            raise Unqualified('installed npm owner metadata for this candidate differs from retained lock; reconcile installation')
        if not record.get('link') and (not isinstance(record.get('version'),str) or not record['version']):
            raise Unqualified('installed npm package owner record lacks a version')
        if record.get('link') and not package.is_symlink():
            raise Unqualified('npm source link was replaced by a directory; preserve possible local source')
        if package.is_symlink():
            source = ev.retained(package)
            expected = packages[key].get('resolved')
            if not packages[key].get('link') or not isinstance(expected,str) or source != (parent/expected).resolve(strict=True):
                raise Unqualified('npm symlink differs from retained local source')
        else:
            metadata = ev.json(package/'package.json')
            if record.get('version') and metadata.get('version') != record['version']:
                raise Unqualified('installed npm package version differs from its owner record')
    # Only owner-listed package trees and npm's generated bin/lock entry belong here.
    if path.name == 'node_modules':
        prefix = path.relative_to(parent).as_posix()+'/'
        allowed = {key[len(prefix):].split('/')[0] for key in owned if key.startswith(prefix)} | {'.bin','.package-lock.json'}
        if any(item.name not in allowed for item in path.iterdir()):
            raise Unqualified('unowned top-level content in node_modules; inspect that entry before reclaim')
    elif path.name.startswith('@'):
        if any(p.relative_to(parent).as_posix() not in owned or p.is_symlink() for p in path.iterdir()):
            raise Unqualified('unowned package or source link in npm scope')
    elif path.relative_to(parent).as_posix() not in actual:
        raise Unqualified('package unit has no installed npm owner record')
    for current, dirs, files in os.walk(path, followlinks=False):
        folder = Path(current)
        if folder.name != 'node_modules': continue
        for package in folder.iterdir():
            if package.name in ('.bin', '.package-lock.json'): continue
            entries = list(package.iterdir()) if package.name.startswith('@') and package.is_dir() and not package.is_symlink() else [package]
            for entry in entries:
                key = entry.relative_to(parent).as_posix()
                if key not in owned:
                    raise Unqualified('installed package directory has no npm owner record; inspect unowned package')
    return 'npm ci', 'npm_package_lock_v2_v3', 'retained npm specification/workspaces/lock and matching installation records'


def cargo(path, ev):
    parent = path.parent
    manifest = tomllib.loads(ev.read(parent/'Cargo.toml'))
    if not isinstance(manifest.get('package') or manifest.get('workspace'), dict):
        raise Unqualified('Cargo manifest has no package or workspace')
    if (parent/'Cargo.lock').exists(): ev.read(parent/'Cargo.lock')
    owner = ev.json(path/'.rustc_info.json')
    if not isinstance(owner.get('rustc_fingerprint'), int) or not isinstance(owner.get('outputs'), dict):
        raise Unqualified('Cargo compiler owner record is malformed')
    if not ev.read(path/'CACHEDIR.TAG').startswith('Signature: 8a477f597d28d172789f06886806bc55'):
        raise Unqualified('Cargo cache ownership tag is missing or invalid')
    def paths(value, base):
        if isinstance(value, dict):
            if isinstance(value.get('path'), str): ev.retained(base/value['path'])
            for child in value.values(): paths(child, base)
        elif isinstance(value, list):
            for child in value: paths(child, base)
    paths(manifest, parent)
    if isinstance(manifest.get('package'), dict):
        if (parent/'src').exists(): ev.retained(parent/'src')
        elif not manifest.get('lib') and not manifest.get('bin'):
            raise Unqualified('Cargo source is missing; restore source before deleting outputs')
        build = manifest['package'].get('build')
        if isinstance(build, str): ev.retained(parent/build)
        elif (parent/'build.rs').exists(): ev.retained(parent/'build.rs')
    workspace = manifest.get('workspace', {})
    for pattern in workspace.get('members', []):
        members = list(parent.glob(pattern))
        if not members: raise Unqualified('Cargo workspace member source missing')
        for member in members:
            ev.retained(member)
            member_spec = tomllib.loads(ev.read(member/'Cargo.toml'))
            paths(member_spec, member)
            if isinstance(member_spec.get('package'),dict):
                if (member/'src').exists(): ev.retained(member/'src')
                elif not member_spec.get('lib') and not member_spec.get('bin'):
                    raise Unqualified('Cargo workspace member source missing; restore it before reclaim')
                build=member_spec['package'].get('build')
                if isinstance(build,str):ev.retained(member/build)
                elif (member/'build.rs').exists():ev.retained(member/'build.rs')
    allowed = {'debug', 'release', 'doc', 'tmp', 'package', 'CACHEDIR.TAG', '.rustc_info.json', '.rustdoc_fingerprint.json'} | set(manifest.get('profile', {}))
    if any(item.name not in allowed and not (item.is_dir() and re.fullmatch(r'[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+){2,}', item.name)) for item in path.iterdir()):
        raise Unqualified('unowned top-level content in Cargo target; inspect that entry')
    return 'cargo build', 'cargo_build_output', 'retained Cargo manifests/source and compiler-owned build cache; dependencies may redownload'


def zig(path, ev):
    parent = path.parent
    ev.read(parent/'build.zig')
    if (parent/'build.zig.zon').exists():
        zon = ev.read(parent/'build.zig.zon')
        for value in re.findall(r'\.path\s*=\s*"([^"\n]+)"', zon): ev.retained(parent/value)
    if not (path/'h').is_dir() or not (path/'o').is_dir() or not any((path/'h').glob('*.txt')):
        raise Unqualified('Zig cache manifest/object layout missing; inspect cache ownership')
    for marker in sorted((path/'h').glob('*.txt'))[:32]: ev.read(marker)
    if any(item.name not in ('h','o','z','tmp','v') for item in path.iterdir()):
        raise Unqualified('unowned top-level content in Zig cache; inspect that entry')
    return 'zig build', 'zig_build_cache', 'retained build specification and Zig manifest/object cache layout'


def python_env(path, ev):
    parent = path.parent
    cfg = ev.read(path/'pyvenv.cfg')
    if not any(line.strip().lower().startswith('home') and '=' in line for line in cfg.splitlines()):
        raise Unqualified('pyvenv.cfg lacks environment owner information')
    installed_pins = []
    requirement_sources={'no_index':False,'links':False}
    def requirements(file, visited):
        file = ev.retained(file)
        if file in visited: return
        if file.suffix not in ('.txt','.in'):
            raise Unqualified('unsupported requirements include format')
        visited.add(file)
        for line in ev.read(file).splitlines():
            line = line.strip()
            if not line or line.startswith('#'): continue
            tokens=shlex.split(line)
            if not tokens: continue
            flag=tokens[0].split('=',1)[0]
            if flag in ('-r','--requirement','-c','--constraint','-f','--find-links'):
                value=tokens[0].split('=',1)[1] if '=' in tokens[0] else (tokens[1] if len(tokens)==2 else None)
                if not value:raise Unqualified('requirements option has unsupported/missing value')
                if flag in ('-r','--requirement','-c','--constraint'):
                    if '://' in value:raise Unqualified('remote requirements includes need separate inspection')
                    requirements(file.parent/value,visited)
                else:
                    requirement_sources['links']=True
                    if '://' not in value:ev.retained(file.parent/value)
                    elif value.startswith('file:'):
                        from urllib.parse import urlparse,unquote
                        ev.retained(Path(unquote(urlparse(value).path)))
                continue
            if line == '--no-index':
                requirement_sources['no_index']=True;continue
            if line.startswith(('-r','-c','-f')) and not line.startswith('--'):
                raise Unqualified('use separated requirement/constraint/find-links option values for inspection')
            if line.startswith(('-e ', '--editable ')):
                target = line.split(None,1)[1]
                if '://' not in target and not target.startswith('git+'):
                    ev.retained(file.parent/target)
                continue
            if line.startswith(('./','../','/')): ev.retained(file.parent/line); continue
            if ' @ file:' in line: ev.retained(file.parent/line.split(' @ file:',1)[1])
            if line.startswith('--'):
                if flag in ('--index-url','--extra-index-url','--trusted-host','--pre','--prefer-binary','--only-binary','--no-binary','--require-hashes','--hash'):
                    continue
                raise Unqualified('unsupported requirements option; inspect its rebuild source semantics')
            if line.endswith(('.whl','.tar.gz','.zip')) and '://' not in line:
                ev.retained(file.parent/line)
    if (parent/'requirements.txt').is_file():
        requirements(parent/'requirements.txt', set())
        if requirement_sources['no_index'] and not requirement_sources['links']:
            raise Unqualified('no-index specification lacks retained find-links rebuild source')
        method = 'recreate venv and install retained requirements.txt'
    elif (parent/'pyproject.toml').is_file() and (parent/'uv.lock').is_file():
        tomllib.loads(ev.read(parent/'pyproject.toml'))
        lock = tomllib.loads(ev.read(parent/'uv.lock'))
        if not isinstance(lock.get('package'),list): raise Unqualified('uv lock package records missing')
        for package in lock['package']:
            source=package.get('source',{})
            for key in ('editable','directory','path'):
                if key in source: ev.retained(parent/source[key])
        method='uv sync from retained pyproject.toml and uv.lock'
    else:
        raise Unqualified('retain a requirements.txt or pyproject.toml + uv.lock to rebuild this environment')
    sites = list((path/'lib').glob('python*/site-packages')) + ([path/'Lib/site-packages'] if (path/'Lib/site-packages').is_dir() else [])
    distributions = [item for site in sites if not site.is_symlink() for item in site.glob('*.dist-info')]
    if not distributions: raise Unqualified('installed dist-info owner records missing')
    for distribution in distributions:
        if distribution.is_symlink(): raise Unqualified('symlinked distribution metadata needs owner inspection')
        metadata = Parser().parsestr(ev.read(distribution/'METADATA'))
        name, version = metadata.get('Name'), metadata.get('Version')
        if not name or not version: raise Unqualified('distribution lacks name/version recovery metadata')
        installed_pins.append(name + '==' + version)
        ev.read(distribution/'RECORD')
        if (distribution/'direct_url.json').exists():
            direct=ev.json(distribution/'direct_url.json')
            url=direct.get('url','')
            if url.startswith('file:'):
                from urllib.parse import urlparse, unquote
                ev.retained(Path(unquote(urlparse(url).path)))
        # .pth may identify editable local source. Read only this owner metadata format.
    for site in sites:
        for item in site.glob('*.egg-link'):
            ev.retained(Path(ev.read(item).splitlines()[0]))
    # Verify only files explicitly owned by installed distributions; never follow an
    # owner record outside this venv or open credential-shaped files to hash them.
    owned = set()
    hashed_bytes = 0
    hash_started = time.monotonic()
    for distribution in distributions:
        site = distribution.parent
        for row in csv.reader(io.StringIO(ev.read(distribution/'RECORD'))):
            if len(row) != 3: raise Unqualified('malformed distribution RECORD')
            relative, digest, size = row
            file = site / relative
            real = file.resolve(strict=True)
            if path.resolve() not in real.parents:
                raise Unqualified('distribution RECORD points outside environment; inspect owner metadata')
            if file.name.startswith('.env') or file.suffix in ('.pem','.key','.p12'):
                raise Unqualified('credential-shaped installed file retained without opening')
            if file.is_symlink(): raise Unqualified('symlinked distribution file needs owner inspection')
            owned.add(real)
            if file.suffix == '.pyc': continue
            if not digest:
                if file == distribution/'RECORD': continue
                raise Unqualified('unhashed installed file needs ownership/integrity verification')
            algorithm, expected = digest.split('=',1)
            if algorithm not in ('sha256','sha384','sha512'):
                raise Unqualified('unsupported installed RECORD digest')
            hasher=hashlib.new(algorithm)
            with regular_fd(file) as (fd, info):
                limit=min(256*1024*1024, 2*1024*1024*1024-hashed_bytes)
                if info.st_size > limit: raise Unqualified('installed-file integrity budget exceeded; inspect this environment separately')
                if size and info.st_size != int(size): raise Unqualified('installed file size differs from RECORD; preserve local edits')
                count=0
                while count <= limit:
                    if time.monotonic()-hash_started > 30:
                        raise Unqualified('installed-file integrity time budget exceeded; inspect environment separately')
                    chunk=os.read(fd,min(1024*1024,limit+1-count))
                    if not chunk: break
                    count+=len(chunk);hasher.update(chunk)
                if count > limit: raise Unqualified('installed file grew beyond integrity read budget')
                after=os.fstat(fd)
                if (info.st_size,info.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                    raise Unqualified('installed file changed during verification')
                hashed_bytes+=count
            if base64.urlsafe_b64encode(hasher.digest()).decode().rstrip('=') != expected:
                raise Unqualified('installed file differs from RECORD; preserve local edits')
    for site in sites:
        for current, dirs, files in os.walk(site,followlinks=False):
            for name in files:
                file=Path(current)/name
                if file.suffix == '.pyc': continue
                if file.resolve() not in owned:
                    raise Unqualified('unowned site-packages file found; preserve custom state')
            for name in dirs:
                file=Path(current)/name
                if file.is_symlink():
                    ev.retained(file)
    allowed={'bin','lib','lib64','include','etc','share','Lib','Scripts','Include','pyvenv.cfg','.gitignore','CACHEDIR.TAG'}
    if any(item.name not in allowed for item in path.iterdir()):
        raise Unqualified('unowned top-level venv content; preserve custom state')
    ev.hashes['installed-version-pins'] = hashlib.sha256(json.dumps(sorted(installed_pins)).encode()).hexdigest()
    ev.installed_pins = sorted(installed_pins)
    return method, 'python_venv_specification', 'retained environment specification and installed distribution ownership records'


def artifact_recovery(path, rule):
    result={'verified':False,'level':'none_or_unknown','method':rule['rebuild']}
    try:
        path=Path(path)
        if path.is_symlink(): raise Unqualified('candidate is a symlink')
        screen_tree(path)
        ev=Evidence(path)
        adapter={'node-package-manager':npm, 'cargo':cargo, 'zig':zig, 'python-environment':python_env}.get(rule['owner'])
        if adapter is None: raise Unqualified('no owner recovery adapter for this resource')
        method,name,reason=adapter(path,ev)
        result.update(verified=True,level='regenerable',method=method,adapter=name,reason=reason,
                      evidence_fingerprints=ev.hashes, rebuild_cost='build time and possible dependency downloads')
        if hasattr(ev, 'installed_pins'): result['installed_version_pins'] = ev.installed_pins
        if hasattr(ev, 'npm_installation_root'): result['npm_installation_root'] = ev.npm_installation_root
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        result['reason']=str(exc) if isinstance(exc,Unqualified) else (f'required owner metadata missing: {Path(exc.filename).name}' if isinstance(exc,FileNotFoundError) and exc.filename else 'owner/specification metadata unavailable or malformed; inspect the named project metadata')
    return result
