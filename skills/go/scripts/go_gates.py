#!/usr/bin/env python3
"""Conservative, non-mutating validation gates for module-native Go projects."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


EXIT_OK = 0
EXIT_NOT_GO = 2
EXIT_DRIVER = 3
EXIT_TOOL_MISSING = 4
EXIT_GATE_FAILED = 5
EXIT_TOOLCHAIN = 6

# Keep discovery output useful without flooding an agent's context.
MAX_DRIVER_CANDIDATES = 30
MAX_CI_HINTS = 50
MAX_FORMAT_FINDINGS = 30
OUTPUT_PREVIEW_LINES = 18

# Bound command-line size while avoiding one process per Go file.
GOFMT_BATCH_SIZE = 200

# Go compilation and tests can be slow in a cold cache, but a stuck gate must
# eventually return control to the agent.
DEFAULT_COMMAND_TIMEOUT_SECONDS = 600

DRIVER_NAMES = (
    "Makefile",
    "Taskfile.yml",
    "Taskfile.yaml",
    "justfile",
    "Justfile",
    "magefile.go",
    "WORKSPACE",
    "WORKSPACE.bazel",
    "MODULE.bazel",
)

CI_PATTERN = re.compile(
    r"\b(go test|go vet|go generate|go mod tidy|go work sync|golangci-lint|"
    r"staticcheck|govulncheck|make (?:test|check|verify|lint)|-race\b|-fuzz\b|"
    r"benchstat)"
)


def command_text(argv: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(arg)) for arg in argv)


def run(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: int,
) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        return {
            "command": command_text(argv),
            "cwd": str(cwd),
            "exit": proc.returncode,
            "output": proc.stdout.rstrip(),
        }
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return {
            "command": command_text(argv),
            "cwd": str(cwd),
            "exit": 124,
            "output": f"timed out after {timeout}s\n{output}".rstrip(),
        }
    except OSError as exc:
        return {
            "command": command_text(argv),
            "cwd": str(cwd),
            "exit": 127,
            "output": str(exc),
        }


def git_root(cwd: Path, env: dict[str, str], timeout: int) -> Path:
    result = run(
        ["git", "rev-parse", "--show-toplevel"], cwd=cwd, env=env, timeout=timeout
    )
    if result["exit"] == 0 and result["output"]:
        return Path(result["output"].splitlines()[-1]).resolve()
    return cwd.resolve()


def walk_up(start: Path, stop: Path) -> Iterable[Path]:
    current = start.resolve()
    stop = stop.resolve()
    while True:
        yield current
        if current == stop or current.parent == current:
            break
        current = current.parent


def detect_drivers(cwd: Path, root: Path) -> list[Path]:
    found: list[Path] = []
    for directory in walk_up(cwd, root):
        for name in DRIVER_NAMES:
            candidate = directory / name
            if candidate.is_file():
                found.append(candidate)
    if (root / "src" / "make.bash").is_file() and (
        root / "src" / "run.bash"
    ).is_file():
        found.append(root / "src" / "make.bash")
        found.append(root / "src" / "run.bash")
    return sorted(set(found))


def candidate_make_targets(path: Path) -> list[str]:
    if path.name != "Makefile":
        return []
    candidates: list[str] = []
    pattern = re.compile(r"^([A-Za-z0-9_.%/-]+)\s*:(?!=)")
    try:
        for line in path.read_text(errors="replace").splitlines():
            match = pattern.match(line)
            if not match:
                continue
            target = match.group(1)
            if re.search(r"(?:test|check|verify|lint|vet|build|ci)", target):
                candidates.append(target)
    except OSError:
        return []
    return sorted(set(candidates))[:MAX_DRIVER_CANDIDATES]


def parse_directives(path: Path | None) -> dict[str, str]:
    data: dict[str, str] = {}
    if path is None or not path.is_file():
        return data
    try:
        for raw in path.read_text(errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0] in {"module", "go", "toolchain"}:
                data[parts[0]] = parts[1]
    except OSError:
        pass
    return data


def find_version_file(cwd: Path, root: Path) -> Path | None:
    for directory in walk_up(cwd, root):
        candidate = directory / ".go-version"
        if candidate.is_file():
            return candidate
    return None


def clean_go_env(allow_network: bool) -> dict[str, str]:
    env = os.environ.copy()
    env["GOTOOLCHAIN"] = "local"
    if not allow_network:
        env["GOPROXY"] = "off"
    return env


def go_env_value(
    go: str, key: str, *, cwd: Path, env: dict[str, str], timeout: int
) -> tuple[str, dict[str, Any]]:
    result = run([go, "env", key], cwd=cwd, env=env, timeout=timeout)
    lines = result["output"].splitlines()
    value = lines[-1].strip() if result["exit"] == 0 and lines else ""
    return value, result


def real_go_file(value: str) -> Path | None:
    if not value or value in {"/dev/null", "NUL"}:
        return None
    path = Path(value)
    return path.resolve() if path.is_file() else None


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def workspace_modules(
    go: str,
    work_file: Path,
    *,
    root: Path,
    env: dict[str, str],
    timeout: int,
) -> tuple[list[Path], list[Path], dict[str, Any]]:
    result = run([go, "work", "edit", "-json"], cwd=work_file.parent, env=env, timeout=timeout)
    inside: list[Path] = []
    outside: list[Path] = []
    if result["exit"] != 0:
        return inside, outside, result
    try:
        payload = json.loads(result["output"])
    except json.JSONDecodeError:
        result["exit"] = 1
        result["output"] = "go work edit -json returned invalid JSON"
        return inside, outside, result
    for entry in payload.get("Use", []):
        disk_path = entry.get("DiskPath")
        if not disk_path:
            continue
        path = Path(disk_path)
        if not path.is_absolute():
            path = work_file.parent / path
        path = path.resolve()
        if is_within(path, root):
            inside.append(path)
        else:
            outside.append(path)
    return sorted(set(inside)), sorted(set(outside)), result


def selected_modules(
    modules: list[Path], requested: list[str], root: Path
) -> list[Path]:
    if not requested:
        return modules
    wanted: set[Path] = set()
    for item in requested:
        candidate = Path(item)
        if not candidate.is_absolute():
            candidate = root / candidate
        wanted.add(candidate.resolve())
    return [module for module in modules if module.resolve() in wanted]


def tracked_go_files(root: Path, env: dict[str, str], timeout: int) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.go"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        proc = None
    if proc is not None and proc.returncode == 0:
        files = [part.decode(errors="replace") for part in proc.stdout.split(b"\0") if part]
    else:
        files = [str(path.relative_to(root)) for path in root.rglob("*.go")]
    return sorted(
        file
        for file in files
        if not file.startswith("vendor/")
        and "/vendor/" not in file
        and not file.startswith(".git/")
    )


def chunked(values: list[str], size: int = GOFMT_BATCH_SIZE) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def format_gate(
    gofmt: str,
    *,
    root: Path,
    env: dict[str, str],
    timeout: int,
) -> dict[str, Any]:
    files = tracked_go_files(root, env, timeout)
    unformatted: list[str] = []
    errors: list[str] = []
    for group in chunked(files):
        if not group:
            continue
        result = run([gofmt, "-l", *group], cwd=root, env=env, timeout=timeout)
        if result["output"]:
            lines = result["output"].splitlines()
            if result["exit"] == 0:
                unformatted.extend(lines)
            else:
                errors.extend(lines)
        if result["exit"] != 0 and not result["output"]:
            errors.append(f"gofmt exited {result['exit']}")
    return {
        "status": "ok" if not unformatted and not errors else "failed",
        "checked": len(files),
        "unformatted": unformatted,
        "errors": errors,
    }


def module_mode(module: Path, work_file: Path | None) -> str:
    if work_file is not None and (work_file.parent / "vendor").is_dir():
        return "vendor"
    if (module / "vendor").is_dir():
        return "vendor"
    return "readonly"


def go_gate_command(
    go: str,
    subcommand: str,
    *,
    mode: str,
    tags: str | None,
    fresh: bool,
    race: bool,
    packages: list[str],
) -> list[str]:
    argv = [go, subcommand, f"-mod={mode}"]
    if tags:
        argv.append(f"-tags={tags}")
    if subcommand == "test" and fresh:
        argv.append("-count=1")
    if subcommand == "test" and race:
        argv.append("-race")
    argv.extend(packages)
    return argv


def lint_config(root: Path) -> Path | None:
    for name in (".golangci.yml", ".golangci.yaml", ".golangci.toml", ".golangci.json"):
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def ci_hints(root: Path) -> list[str]:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.is_dir():
        return []
    hints: list[str] = []
    for path in sorted(workflow_dir.iterdir()):
        if path.suffix not in {".yml", ".yaml"} or not path.is_file():
            continue
        try:
            for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                if CI_PATTERN.search(line):
                    hints.append(f"{path.name}:{number}: {line.strip()}")
        except OSError:
            continue
    return hints[:MAX_CI_HINTS]


def short_output(output: str, limit: int = OUTPUT_PREVIEW_LINES) -> str:
    lines = output.splitlines()
    if len(lines) <= limit:
        return output
    return "\n".join([*lines[:limit], f"... {len(lines) - limit} more lines"])


def status_count(results: list[dict[str, Any]]) -> str:
    if not results:
        return "n/a"
    passed = sum(item.get("exit") == 0 for item in results)
    return f"{passed}/{len(results)}"


def print_text(report: dict[str, Any]) -> None:
    print(f"root: {report['root']}")
    if report.get("drivers"):
        print("drivers:")
        for driver in report["drivers"]:
            print(f"  {driver}")
        for makefile, targets in report.get("driver_candidates", {}).items():
            if targets:
                print(f"candidate targets in {makefile} (inspect recipes): {', '.join(targets)}")
    if report.get("message"):
        print(report["message"])
    authorities = report.get("authorities", {})
    if authorities:
        print(
            "versions: "
            f"local={authorities.get('local', 'unknown')} "
            f"go={authorities.get('required', 'n/a')} "
            f"toolchain={authorities.get('toolchain', 'n/a')} "
            f"version_file={authorities.get('version_file', 'n/a')}"
        )
    if report.get("workspace"):
        print(f"workspace: {report['workspace']}")
    if report.get("external_workspace_modules"):
        print("skipped external workspace modules:")
        for module in report["external_workspace_modules"]:
            print(f"  {module}")
    for key in ("preflight", "vet", "test", "race", "lint"):
        value = report.get(key)
        if isinstance(value, list):
            for item in value:
                if item.get("exit") != 0:
                    print(f"{key} failed: {item['cwd']}\n{short_output(item['output'])}")
        elif isinstance(value, dict) and value.get("exit") not in (None, 0):
            print(f"{key} failed:\n{short_output(value.get('output', ''))}")
    fmt = report.get("format")
    if isinstance(fmt, dict) and fmt.get("status") == "failed":
        if fmt.get("unformatted"):
            print("unformatted Go files:")
            for path in fmt["unformatted"][:MAX_FORMAT_FINDINGS]:
                print(f"  {path}")
        if fmt.get("errors"):
            print("gofmt errors:")
            for error in fmt["errors"][:MAX_FORMAT_FINDINGS]:
                print(f"  {error}")
    if report.get("ci_hints"):
        print("CI contract hints not automatically covered:")
        for hint in report["ci_hints"][:20]:
            print(f"  {hint}")
    print(report["summary"])


def finish(report: dict[str, Any], code: int, as_json: bool) -> int:
    report["exit"] = code
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run non-mutating Go format, vet, test, and configured-lint gates. "
            "Defaults to GOTOOLCHAIN=local and GOPROXY=off."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""exit codes:
  0  all requested gates passed
  2  no active Go module/workspace was found
  3  repository build driver detected; inspect and use it
  4  required local tool missing
  5  a requested validation gate failed
  6  local toolchain cannot load the module/workspace

This helper never runs formatter write mode, go generate, go fix, go mod tidy,
go work sync, vendoring, or tool installation.
""",
    )
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument(
        "--force-direct",
        action="store_true",
        help="run direct Go gates despite a detected build driver",
    )
    parser.add_argument(
        "--allow-network",
        action="store_true",
        help="allow module downloads through the existing GOPROXY setting; toolchain stays local",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        metavar="PATH",
        help="limit a workspace run to an in-repository module path; repeatable",
    )
    parser.add_argument(
        "--packages",
        action="append",
        default=[],
        metavar="PATTERN",
        help="package pattern relative to each module; repeatable, default ./...",
    )
    parser.add_argument("--tags", help="comma-separated build tags")
    parser.add_argument("--fresh", action="store_true", help="pass -count=1 to tests")
    parser.add_argument("--race", action="store_true", help="run an additional race test lane")
    parser.add_argument("--skip-format", action="store_true")
    parser.add_argument("--skip-vet", action="store_true")
    parser.add_argument("--skip-test", action="store_true")
    parser.add_argument("--skip-lint", action="store_true")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_COMMAND_TIMEOUT_SECONDS,
        help=(
            "per-command timeout in seconds "
            f"(default {DEFAULT_COMMAND_TIMEOUT_SECONDS})"
        ),
    )
    parser.add_argument(
        "directory", nargs="?", default=".", help="directory to inspect (default current directory)"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cwd = Path(args.directory).resolve()
    if not cwd.is_dir():
        print(f"not a directory: {cwd}", file=sys.stderr)
        return EXIT_NOT_GO

    base_env = os.environ.copy()
    root = git_root(cwd, base_env, args.timeout)
    report: dict[str, Any] = {
        "root": str(root),
        "network": "allowed" if args.allow_network else "off",
    }

    drivers = detect_drivers(cwd, root)
    report["drivers"] = [str(path) for path in drivers]
    report["driver_candidates"] = {
        str(path): candidate_make_targets(path) for path in drivers if path.name == "Makefile"
    }
    force_direct = args.force_direct or os.environ.get("GO_GATES_FORCE_DIRECT") == "1"
    if drivers and not force_direct:
        report["message"] = (
            "build driver detected; inspect its recipes and use the repository's narrow, "
            "non-mutating validation command. Pass --force-direct only after deciding raw Go "
            "commands are appropriate."
        )
        report["summary"] = (
            "summary: preflight=n/a format=n/a vet=n/a test=n/a race=n/a "
            "lint=n/a driver=refused exit=3"
        )
        return finish(report, EXIT_DRIVER, args.json)

    go = shutil.which("go")
    gofmt = shutil.which("gofmt")
    if not go or (not args.skip_format and not gofmt):
        missing = []
        if not go:
            missing.append("go")
        if not args.skip_format and not gofmt:
            missing.append("gofmt")
        report["message"] = f"missing required local tool(s): {', '.join(missing)}"
        report["summary"] = (
            "summary: preflight=missing-tool format=n/a vet=n/a test=n/a race=n/a "
            "lint=n/a driver=direct exit=4"
        )
        return finish(report, EXIT_TOOL_MISSING, args.json)

    assert go is not None
    env = clean_go_env(args.allow_network)
    version = run([go, "version"], cwd=cwd, env=env, timeout=args.timeout)
    local_version = "unknown"
    match = re.search(r"\bgo(\d+(?:\.\d+)+(?:[^\s]*)?)", version["output"])
    if match:
        local_version = match.group(1)

    gomod_value, gomod_result = go_env_value(
        go, "GOMOD", cwd=cwd, env=env, timeout=args.timeout
    )
    gowork_value, gowork_result = go_env_value(
        go, "GOWORK", cwd=cwd, env=env, timeout=args.timeout
    )
    gomod = real_go_file(gomod_value)
    gowork = real_go_file(gowork_value)
    report["workspace"] = str(gowork) if gowork else ""
    report["gomod"] = str(gomod) if gomod else ""

    directives = parse_directives(gowork or gomod)
    version_file = find_version_file(cwd, root)
    version_file_value = ""
    if version_file is not None:
        try:
            version_file_value = version_file.read_text(errors="replace").strip().splitlines()[0]
        except (OSError, IndexError):
            version_file_value = ""
    report["authorities"] = {
        "local": local_version,
        "required": directives.get("go", ""),
        "toolchain": directives.get("toolchain", ""),
        "version_file": version_file_value,
        "version_file_path": str(version_file) if version_file else "",
    }

    if version["exit"] != 0 or gomod_result["exit"] != 0 or gowork_result["exit"] != 0:
        report["preflight"] = [version, gomod_result, gowork_result]
        report["summary"] = (
            f"summary: preflight=failed({local_version}) format=n/a vet=n/a test=n/a "
            "race=n/a lint=n/a driver=direct exit=6"
        )
        return finish(report, EXIT_TOOLCHAIN, args.json)

    if gomod is None and gowork is None:
        report["message"] = "no active go.mod or go.work found"
        report["summary"] = (
            f"summary: preflight=not-go({local_version}) format=n/a vet=n/a test=n/a "
            "race=n/a lint=n/a driver=direct exit=2"
        )
        return finish(report, EXIT_NOT_GO, args.json)

    preflight = run([go, "list", "-m"], cwd=cwd, env=env, timeout=args.timeout)
    report["preflight"] = preflight
    if preflight["exit"] != 0:
        report["summary"] = (
            f"summary: preflight=failed({local_version}) format=n/a vet=n/a test=n/a "
            "race=n/a lint=n/a driver=direct exit=6"
        )
        return finish(report, EXIT_TOOLCHAIN, args.json)

    external_modules: list[Path] = []
    if gowork is not None:
        modules, external_modules, work_result = workspace_modules(
            go, gowork, root=root, env=env, timeout=args.timeout
        )
        report["workspace_read"] = work_result
        if work_result["exit"] != 0:
            report["summary"] = (
                f"summary: preflight=failed-workspace({local_version}) format=n/a vet=n/a "
                "test=n/a race=n/a lint=n/a driver=direct exit=6"
            )
            return finish(report, EXIT_TOOLCHAIN, args.json)
    else:
        assert gomod is not None
        modules = [gomod.parent]
    modules = selected_modules(modules, args.module, root)
    report["modules"] = [str(path) for path in modules]
    report["external_workspace_modules"] = [str(path) for path in external_modules]
    if not modules:
        report["message"] = "no in-scope workspace modules matched"
        report["summary"] = (
            f"summary: preflight=ok({local_version}) format=n/a vet=n/a test=n/a "
            "race=n/a lint=n/a driver=direct exit=2"
        )
        return finish(report, EXIT_NOT_GO, args.json)

    gate_failed = False
    if args.skip_format:
        report["format"] = {"status": "skipped", "checked": 0}
    else:
        assert gofmt is not None
        report["format"] = format_gate(
            gofmt, root=root, env=env, timeout=args.timeout
        )
        gate_failed |= report["format"]["status"] != "ok"

    packages = args.packages or ["./..."]
    vet_results: list[dict[str, Any]] = []
    test_results: list[dict[str, Any]] = []
    race_results: list[dict[str, Any]] = []
    for module in modules:
        mode = module_mode(module, gowork)
        if not args.skip_vet:
            vet = run(
                go_gate_command(
                    go,
                    "vet",
                    mode=mode,
                    tags=args.tags,
                    fresh=False,
                    race=False,
                    packages=packages,
                ),
                cwd=module,
                env=env,
                timeout=args.timeout,
            )
            vet_results.append(vet)
            gate_failed |= vet["exit"] != 0
        if not args.skip_test:
            test = run(
                go_gate_command(
                    go,
                    "test",
                    mode=mode,
                    tags=args.tags,
                    fresh=args.fresh,
                    race=False,
                    packages=packages,
                ),
                cwd=module,
                env=env,
                timeout=args.timeout,
            )
            test_results.append(test)
            gate_failed |= test["exit"] != 0
        if args.race:
            race_result = run(
                go_gate_command(
                    go,
                    "test",
                    mode=mode,
                    tags=args.tags,
                    fresh=args.fresh,
                    race=True,
                    packages=packages,
                ),
                cwd=module,
                env=env,
                timeout=args.timeout,
            )
            race_results.append(race_result)
            gate_failed |= race_result["exit"] != 0
    report["vet"] = vet_results
    report["test"] = test_results
    report["race"] = race_results

    config = lint_config(root)
    report["lint_config"] = str(config) if config else ""
    lint_result: dict[str, Any] | None = None
    lint_status = "n/a"
    if args.skip_lint:
        lint_status = "skipped"
    elif config is not None:
        golangci = shutil.which("golangci-lint")
        if not golangci:
            lint_result = {
                "command": "golangci-lint run",
                "cwd": str(root),
                "exit": 127,
                "output": "configured golangci-lint is not installed; no installation attempted",
            }
        else:
            lint_result = run(
                [golangci, "run"], cwd=root, env=env, timeout=args.timeout
            )
        lint_status = "ok" if lint_result["exit"] == 0 else "failed"
        gate_failed |= lint_result["exit"] != 0
    report["lint"] = lint_result or {"status": lint_status}
    report["ci_hints"] = ci_hints(root)

    format_status = report["format"]["status"]
    vet_status = "skipped" if args.skip_vet else status_count(vet_results)
    test_status = "skipped" if args.skip_test else status_count(test_results)
    race_status = status_count(race_results) if args.race else "n/a"
    code = EXIT_GATE_FAILED if gate_failed else EXIT_OK
    report["summary"] = (
        f"summary: preflight=ok({local_version},go={directives.get('go', 'n/a')},"
        f"toolchain={directives.get('toolchain', 'n/a')}) "
        f"modules={len(modules)} format={format_status} vet={vet_status} "
        f"test={test_status} race={race_status} lint={lint_status} "
        f"network={'allowed' if args.allow_network else 'off'} driver=direct exit={code}"
    )
    return finish(report, code, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
