#!/usr/bin/env python3
"""Discover private Colophon voices, export verified local prompts, and guard Markdown.

The configured Colophon executable owns registry discovery and VoiceProfile
validation. This adapter never calls a writing provider or reads source corpora.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time


MAX_FILE = 16 * 1024 * 1024
MAX_RESPONSE = 256 * 1024
PACKAGE = Path(__file__).resolve().parents[1]
ALIAS = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
QUALITY = ("voice", "naturalness", "factuality", "preservation", "copying", "human_or_literary_validation")
GUARD_SCOPE = "fenced/indented code, inline code, link/image destinations and reference definitions; conservative Markdown subset, no factual or voice validation"


class AdapterError(Exception):
    def __init__(self, code, *, status="error", recovery_path=None):
        self.code, self.status, self.recovery_path = code, status, recovery_path
        super().__init__(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def secret_path(path):
    return any(part.lower().startswith(".env") or part.lower() in {".ssh", ".aws", ".gnupg"}
               for part in path.parts) or path.suffix.lower() in {".pem", ".p12", ".pfx", ".key", ".keystore"} or any(
                   value in path.name.lower() for value in ("credential", "private_key", "private-key"))


def regular_bytes(path, maximum=MAX_FILE):
    path = Path(path).expanduser()
    if secret_path(path):
        raise AdapterError("secret_path_refused")
    if path.is_symlink():
        raise AdapterError("symlink_refused")
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                raise AdapterError("unsupported_file")
            data = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        if len(data) > maximum or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise AdapterError("file_changed_or_oversized")
        return data
    except AdapterError:
        raise
    except OSError:
        raise AdapterError("file_unavailable") from None


def decode_json(data, code="invalid_runtime_response"):
    try:
        result = json.loads(data, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise AdapterError(code) from None


def git_env():
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_CONFIG_NOSYSTEM="1", GIT_OPTIONAL_LOCKS="0", LC_ALL="C")
    return env


def git_call(directory, *arguments):
    try:
        return subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(directory), *arguments],
                              env=git_env(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        raise AdapterError("git_privacy_check_unavailable") from None


def git_root(path):
    directory = path if path.is_dir() else path.parent
    while not directory.exists() and directory != directory.parent:
        directory = directory.parent
    result = git_call(directory, "rev-parse", "--show-toplevel")
    if result.returncode == 128:
        # A broken worktree, ownership denial or unreadable registration is
        # unknown Git state, not evidence that an artifact is outside Git.
        for ancestor in (directory, *directory.parents):
            if os.path.lexists(ancestor / ".git") or ((ancestor / "HEAD").is_file() and (ancestor / "objects").is_dir()):
                raise AdapterError("git_privacy_check_failed")
        if b"not a git repository" not in result.stderr:
            raise AdapterError("git_privacy_check_failed")
        return None
    if result.returncode != 0:
        raise AdapterError("git_privacy_check_failed")
    try:
        return Path(result.stdout.decode().strip()).resolve(strict=True)
    except (ValueError, OSError, UnicodeError):
        raise AdapterError("git_privacy_check_failed") from None


def private_path(path):
    """Local artifacts can be outside Git or untracked and ignored in Git."""
    path = Path(path).expanduser()
    if secret_path(path):
        raise AdapterError("secret_path_refused")
    if path.is_symlink():
        raise AdapterError("symlink_refused")
    real = path.resolve(strict=False)
    if any(part.casefold() == ".git" for part in path.parts):
        raise AdapterError("private_artifact_in_git_metadata")
    if real == PACKAGE.parent or PACKAGE.parent in real.parents:
        raise AdapterError("private_artifact_in_skill_tree")
    roots = {root for root in (git_root(path), git_root(Path.cwd())) if root is not None}
    # An inner repository's ignore rules do not hide an artifact from an
    # enclosing checkout. This also qualifies final prompt destinations.
    for location in (path.absolute(), real):
        for ancestor in location.parents:
            try:
                (ancestor / ".git").lstat()
            except FileNotFoundError:
                continue
            except OSError:
                raise AdapterError("git_privacy_check_failed") from None
            root = git_root(ancestor)
            if root is None:
                raise AdapterError("git_privacy_check_failed")
            roots.add(root)
    for root in roots:
        if real == root or root in real.parents:
            relative = str(real.relative_to(root))
            tracked = git_call(root, "ls-files", "--error-unmatch", "--", relative)
            if tracked.returncode == 0:
                raise AdapterError("private_artifact_tracked")
            if tracked.returncode != 1:
                raise AdapterError("git_privacy_check_failed")
            if git_call(root, "check-ignore", "--quiet", "--", relative).returncode != 0:
                raise AdapterError("private_artifact_not_ignored")
    return real


def runtime_path(value):
    selected = value or os.environ.get("COLOPHON_BIN") or "colophon"
    found = shutil.which(selected)
    if not found:
        raise AdapterError("runtime_unavailable", status="unavailable")
    path = Path(found).resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise AdapterError("runtime_unavailable", status="unavailable")
    return str(path)


def native(runtime, arguments, timeout):
    """Bound captured responses; never return arbitrary stderr or failure text."""
    with tempfile.TemporaryDirectory(prefix="colophon-adapter-call-") as temporary:
        root = Path(temporary)
        with (root / "stdout").open("w+b") as out, (root / "stderr").open("w+b") as err:
            try:
                process = subprocess.Popen([runtime, *arguments], stdin=subprocess.DEVNULL,
                                           stdout=out, stderr=err, cwd=root,
                                           start_new_session=os.name == "posix")
                deadline = time.monotonic() + timeout
                while process.poll() is None:
                    oversized = os.fstat(out.fileno()).st_size > MAX_RESPONSE or os.fstat(err.fileno()).st_size > MAX_RESPONSE
                    if oversized or time.monotonic() >= deadline:
                        try:
                            if os.name == "posix":
                                os.killpg(process.pid, signal.SIGKILL)
                            else:
                                process.kill()
                        except ProcessLookupError:
                            pass
                        process.wait()
                        raise AdapterError("runtime_response_oversized" if oversized else "runtime_timeout", status="unknown")
                    time.sleep(.02)
                if os.name == "posix":
                    # A completed export has no need for owned background
                    # helpers; stop descendants left in its dedicated group.
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            except OSError:
                raise AdapterError("runtime_unavailable", status="unavailable") from None
            if out.tell() > MAX_RESPONSE or err.tell() > MAX_RESPONSE:
                raise AdapterError("runtime_response_oversized")
            out.seek(0)
            data = out.read(MAX_RESPONSE + 1)
            if process.returncode:
                try:
                    response = decode_json(data)
                except AdapterError:
                    raise AdapterError("runtime_failed") from None
                error = response.get("error")
                code = error.get("code", "runtime_failed") if isinstance(error, dict) else "runtime_failed"
                if not isinstance(code, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", code):
                    code = "runtime_failed"
                raise AdapterError("native_" + code,
                                   status="unknown" if response.get("status") in {"unknown", "unverified"} else "error")
            return data


def registry_arguments(registry):
    if registry is None:
        return []
    path = Path(registry).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    private_path(path)
    # Keep lexical symlink hops for native every-location privacy validation.
    # The native registry owns content checks; do not read or canonicalize it.
    return ["--registry", str(path)]


def list_profiles(runtime, registry, timeout):
    value = decode_json(native(runtime, ["voice", "profiles", "list", *registry], timeout))
    if type(value.get("schema_version")) is not int or value.get("schema_version") != 1 or value.get("status") not in {"configured", "not_configured"} or not isinstance(value.get("profiles"), list):
        raise AdapterError("invalid_registry_response")
    profiles = []
    for item in value["profiles"]:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not ALIAS.fullmatch(item["name"]):
            raise AdapterError("invalid_registry_response")
        if item.get("kind") != "VoiceProfile":
            raise AdapterError("unsupported_profile_kind")
        profiles.append({"name": item["name"], "kind": "VoiceProfile"})
    if len({item["name"] for item in profiles}) != len(profiles):
        raise AdapterError("duplicate_profile_alias")
    return {"status": value["status"], "profiles": profiles}


def resolve_profile(runtime, registry, name, timeout):
    value = decode_json(native(runtime, ["voice", "profiles", "resolve", name, *registry], timeout))
    if type(value.get("schema_version")) is not int or value.get("schema_version") != 1 or value.get("status") != "resolved" or value.get("name") != name or value.get("kind") != "VoiceProfile":
        raise AdapterError("invalid_resolution_response")
    raw_path = value.get("profile_path")
    if not isinstance(raw_path, str) or not Path(raw_path).is_absolute():
        raise AdapterError("invalid_resolution_response")
    path = private_path(Path(raw_path))
    data = regular_bytes(path)
    profile = decode_json(data, "invalid_voice_profile")
    if profile.get("schema_version") != "1" or not isinstance(profile.get("profile_id"), str):
        raise AdapterError("invalid_voice_profile")
    if profile["profile_id"] != value.get("profile_id") or sha(data) != value.get("profile_sha256"):
        raise AdapterError("resolved_profile_changed")
    return path, data, profile["profile_id"]


def publish(path, data):
    if os.path.lexists(path):
        raise AdapterError("output_exists")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        raise AdapterError("output_exists") from None
    except OSError:
        raise AdapterError("publish_unknown", status="unknown", recovery_path=str(path)) from None
    try:
        observed = regular_bytes(path)
    except AdapterError:
        raise AdapterError("publish_readback_unknown", status="unknown", recovery_path=str(path)) from None
    if observed != data:
        raise AdapterError("publish_readback_mismatch", status="unknown", recovery_path=str(path))


def physical_output(path):
    """Do not erase symlink hops before qualifying a private destination."""
    path = Path(path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current = current / component
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            raise AdapterError("output_path_unavailable") from None
        if stat.S_ISLNK(info.st_mode):
            raise AdapterError("output_symlink_component")
    return private_path(path)


def prompt(args, runtime, registry):
    output = physical_output(args.output)
    if os.path.lexists(output):
        raise AdapterError("output_exists")
    if not output.parent.is_dir():
        raise AdapterError("output_parent_missing")
    path, source, identity = resolve_profile(runtime, registry, args.name, args.timeout)
    run = Path(tempfile.mkdtemp(prefix="colophon-prompt-"))
    scratch = run / "guidance.txt"
    try:
        response = decode_json(native(runtime, ["voice", "prompt", str(path), "--mode", args.mode,
                                               "--task", args.task, "-o", str(scratch), "--receipt"], args.timeout))
        if response.get("schema_version") != "1" or response.get("status") != "written":
            raise AdapterError("prompt_not_verified", status="unknown")
        observed = regular_bytes(scratch)
        observed.decode("utf-8")
        if not observed.strip():
            raise AdapterError("empty_prompt")
        if regular_bytes(path) != source:
            raise AdapterError("source_profile_changed", status="unknown")
        expected_source = response.get("source_profile", {})
        expected_artifact = response.get("artifact", {})
        if not isinstance(expected_source, dict) or expected_source.get("id") != identity or expected_source.get("sha256") != sha(source) or expected_source.get("path") != str(path):
            raise AdapterError("receipt_source_mismatch", status="unknown")
        if not isinstance(expected_artifact, dict) or type(expected_artifact.get("bytes")) is not int or expected_artifact.get("bytes") != len(observed) or expected_artifact.get("sha256") != sha(observed):
            raise AdapterError("receipt_artifact_mismatch", status="unknown")
        if response.get("mode") != args.mode or response.get("task") != args.task or response.get("target_path") != str(scratch):
            raise AdapterError("receipt_request_mismatch", status="unknown")
        if private_path(path) != path or physical_output(args.output) != output:
            raise AdapterError("private_location_changed", status="unknown")
        publish(output, observed)
        return {"status": "written", "output": str(output), "source_profile": {"id": identity, "sha256": sha(source)},
                "artifact": {"bytes": len(observed), "sha256": sha(observed)}, "mode": args.mode, "task": args.task,
                "verification_scope": "prompt artifact only", "generation": "not_performed",
                "quality_dimensions": dict.fromkeys(QUALITY, "unverified")}
    except (AdapterError, UnicodeError) as error:
        if scratch.exists():
            if isinstance(error, AdapterError):
                error.status = "unknown"
                error.recovery_path = error.recovery_path or str(run)
            else:
                raise AdapterError("invalid_prompt_encoding", status="unknown", recovery_path=str(run)) from None
        else:
            shutil.rmtree(run)
        raise
    finally:
        # Successful publication has an independently read-back final artifact.
        if output.exists() and scratch.exists():
            try:
                if regular_bytes(output) == regular_bytes(scratch):
                    shutil.rmtree(run)
            except AdapterError:
                pass


def protected_spans(text):
    """A bounded Markdown guard, not a full Markdown or HTML parser."""
    spans = []
    lines = text.splitlines(keepends=True)
    offset, opened = 0, None
    for line in lines:
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*?)(?:\r?\n)?$", line)
        if opened:
            start, char, length = opened
            if match and match[1][0] == char and len(match[1]) >= length and not match[2].strip():
                spans.append((start, offset + len(line), "fenced_code")); opened = None
        elif match:
            opened = (offset, match[1][0], len(match[1]))
        offset += len(line)
    if opened:
        spans.append((opened[0], len(text), "fenced_code"))

    def available(start, end):
        return not any(start < right and end > left for left, right, _ in spans)

    for match in re.finditer(r"(?m)^(?: {4}|\t)[^\n]*(?:\n(?:(?: {4}|\t)[^\n]*|[ \t]*))*", text):
        if available(*match.span()):
            spans.append((*match.span(), "indented_code"))
    for match in re.finditer(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)", text, re.DOTALL):
        if available(*match.span()):
            spans.append((*match.span(), "inline_code"))
    for match in re.finditer(r"(?m)^ {0,3}\[[^\]\n]+\]:[^\n]*(?:\n[ \t]+[^\n]*)*", text):
        if available(*match.span()):
            spans.append((*match.span(), "reference_definition"))
    for match in re.finditer(r"(?<!\\)\]\(", text):
        if not available(*match.span()):
            continue
        start, cursor, depth, angle = match.end() - 1, match.end(), 1, False
        while cursor < len(text) and depth:
            if text[cursor] == "\\":
                cursor += 2; continue
            if text[cursor] == "<": angle = True
            elif text[cursor] == ">": angle = False
            elif text[cursor] == "(" and not angle: depth += 1
            elif text[cursor] == ")" and not angle: depth -= 1
            cursor += 1
        if not depth and available(start, cursor):
            spans.append((start, cursor, "link_destination"))
    for pattern, kind in ((r"!?\[[^\]\n]*\](\[[^\]\n]*\])", "reference_link"),
                          (r"<(?:https?://|mailto:)[^>\n]+>", "autolink"),
                          (r"(?i)\b(?:href|src)\s*=\s*([\"'])(.*?)\1", "html_destination")):
        for match in re.finditer(pattern, text):
            region = (match.span(1) if match[1] != "[]" else match.span()) if kind == "reference_link" else match.span()
            if available(*region):
                spans.append((*region, kind))
    labels = {re.sub(r"\s+", " ", match[1]).strip().casefold()
              for match in re.finditer(r"(?m)^ {0,3}\[([^\]\n]+)\]:", text)}
    for match in re.finditer(r"!?\[([^\]\n]+)\](?![\[(])", text):
        if re.sub(r"\s+", " ", match[1]).strip().casefold() in labels and available(*match.span()):
            spans.append((*match.span(), "shortcut_reference"))
    return [(kind, text[left:right]) for left, right, kind in sorted(spans)]


def check_candidate(source_path, candidate_path):
    source, candidate = Path(source_path), Path(candidate_path)
    try:
        if source.samefile(candidate):
            raise AdapterError("candidate_aliases_source")
    except OSError:
        pass
    original, proposed = regular_bytes(source), regular_bytes(candidate)
    try:
        before, after = protected_spans(original.decode("utf-8")), protected_spans(proposed.decode("utf-8"))
    except UnicodeError:
        raise AdapterError("invalid_markdown_encoding") from None
    preserved = before == after
    return {"status": "preserved" if preserved else "rejected", "protected_spans": len(before),
            "candidate_spans": len(after), "source_sha256": sha(original), "candidate_sha256": sha(proposed),
            "verification_scope": GUARD_SCOPE, "factuality": "unverified", "voice": "unverified"}


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--runtime", help="Trusted Colophon executable; otherwise COLOPHON_BIN or PATH")
    result.add_argument("--registry", help="Private native Colophon registry override")
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("profiles", help="Read native registry aliases without source passages")
    sub.add_parser("doctor", help="Check native command compatibility without model calls")
    render = sub.add_parser("prompt", help="Export and verify private writing guidance; never generate writing")
    render.add_argument("name")
    render.add_argument("--output", required=True)
    render.add_argument("--mode", choices=("numeric", "qualitative", "exemplars", "hybrid"), default="numeric")
    render.add_argument("--task", choices=("rewrite", "generate"), default="rewrite")
    render.add_argument("--timeout", type=float, default=30)
    guard = sub.add_parser("check-candidate", help="Read-only protected Markdown comparison")
    guard.add_argument("source")
    guard.add_argument("candidate")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "check-candidate":
            result = check_candidate(args.source, args.candidate)
            code = 0 if result["status"] == "preserved" else 1
        else:
            runtime = runtime_path(args.runtime)
            registry = registry_arguments(args.registry)
            if args.command == "profiles":
                result, code = list_profiles(runtime, registry, 10), 0
            elif args.command == "doctor":
                for arguments, flags in ((["voice", "profiles", "list", "--help"], ("--registry",)),
                                         (["voice", "profiles", "resolve", "--help"], ("--registry",)),
                                         (["voice", "prompt", "--help"], ("--receipt", "--mode", "--task", "--output"))):
                    try:
                        help_text = native(runtime, arguments, 10).decode("utf-8")
                    except (AdapterError, UnicodeError):
                        raise AdapterError("runtime_contract_unavailable", status="unavailable") from None
                    if any(flag not in help_text for flag in flags):
                        raise AdapterError("runtime_contract_unavailable", status="unavailable")
                listing = list_profiles(runtime, registry, 10)
                result, code = {"status": "ready", "registry_status": listing["status"],
                                "profiles": len(listing["profiles"]), "generation": "not_performed"}, 0
            else:
                if not ALIAS.fullmatch(args.name):
                    raise AdapterError("invalid_profile_alias")
                if not 0 < args.timeout <= 300:
                    raise AdapterError("invalid_timeout")
                result, code = prompt(args, runtime, registry), 0
    except AdapterError as error:
        result, code = {"status": error.status, "error_code": error.code,
                        "error": "Operation did not produce a verified result; inspect the named capability or local artifact before retrying."}, 1
        if error.recovery_path:
            result["recovery_path"] = error.recovery_path
    except (OSError, ValueError, UnicodeError):
        result, code = {"status": "error", "error_code": "invalid_local_input",
                        "error": "Local input could not be validated; no raw runtime or profile content was reported."}, 1
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
