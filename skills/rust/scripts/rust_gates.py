#!/usr/bin/env python3
"""Non-mutating narrow→broad gates for a Cargo-native project.

Run from the package or workspace root:

    "$RUST_SKILL_DIR/scripts/rust-gates.sh"          # shim → this file
    "$RUST_SKILL_DIR/scripts/rust_gates.py" [--json]

Default sequence:
    detect build driver → toolchain preflight → fmt --check → clippy → tests
    → dependency policies (cargo deny / cargo vet) → CI-contract coverage
    → one-line summary

Exit codes:
    0    every gate that ran passed
    1    no Cargo.toml here, or a tool failed outside a gate
    2    usage error
    3    build driver detected (x.py, xtask, justfile, Makefile with Rust
         targets); its recipes are the contract. Detection walks up to the git
         top level; a parent-level driver counts only if it mentions the Rust
         toolchain. Set RUST_GATES_USE_DRIVER=1 to run its non-mutating
         recipes instead, or RUST_GATES_FORCE_CARGO=1 to run raw Cargo anyway.
    4    rustfmt.toml names nightly-only options that could not be promoted.
         Stable rustfmt drops such options from the file (with a warning) but
         honors them as `--config key=val`, so the gate parses the warning and
         re-runs with the options promoted; 4 means that was impossible.
    5    .config/nextest.toml exists (test groups, retries, timeouts are the
         test contract) but cargo-nextest is not installed.
    6    toolchain preflight: the selected toolchain is not installed (rustup
         auto-install is disabled for the run), lacks rustfmt/clippy, or its
         rustc is older than the workspace's declared rust-version.
    101  a Cargo gate failed (Cargo's own exit code is passed through)
    127  cargo not on PATH

Clippy denies warnings only when the repo has a Clippy policy (clippy.toml,
[lints.clippy], or clippy in CI workflows). Without one it runs as advisory:
warnings are aggregated by lint, the full output goes to a file, and the gate
does not fail — the repo never agreed to those lints. `--all-targets` builds
that fail only because a bench needs nightly (E0554) are retried without
benches.

Selection knobs:
    RUST_PACKAGE=name            check one package instead of --workspace
    RUST_FEATURES=a,b            enable selected features
    RUST_ALL_FEATURES=1          enable all features (composable feature sets only)
    RUST_NO_DEFAULT_FEATURES=1   disable default features
    RUST_UNLOCKED=1              omit --locked even when Cargo.lock exists

Gate knobs:
    RUST_GATES_FORCE_CARGO=1     run raw Cargo even though a build driver exists
    RUST_GATES_USE_DRIVER=1      run the driver's non-mutating recipes instead
    RUST_GATES_DRIVER_RECIPES=a,b  restrict delegation to these recipes
    RUST_GATES_AUTO_INSTALL=1    let rustup auto-install a missing toolchain
    RUST_GATES_SELECT_TOOLCHAIN=1  when rustc is below the MSRV and no file pins
                                 the toolchain, switch to an installed one that
                                 satisfies it (RUSTUP_TOOLCHAIN for this run)
    RUST_TEST_RUNNER=cargo       use cargo test even when .config/nextest.toml exists
    RUST_FMT_ALLOW_UNSTABLE_WARNINGS=1  legacy opt-in: report unpromotable fmt
                                      configuration as advisory, not CI coverage
    SKIP_RUST_FMT=1 / SKIP_RUST_CLIPPY=1 / SKIP_RUST_TEST=1
    SKIP_RUST_DENY=1 / SKIP_RUST_VET=1
    RUST_CHECK_ALWAYS=1          run cargo check even when Clippy also runs
    SKIP_RUST_CHECK=1            never run cargo check
    RUST_DENY_WARNINGS=1|0       force Clippy to deny (1) or advise (0)
    RUST_TEST_ALL_TARGETS=1      add --all-targets to the test run
    RUST_DOC_TESTS=1             run cargo test --doc (always on under nextest)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

PROG = "rust-gates.sh"
LOG = sys.stdout

# CI subcommands worth reporting coverage against, and the GitHub Actions
# that stand in for them.
CI_SUBS = (
    "fmt", "clippy", "test", "nextest", "hack", "miri", "deny", "vet",
    "audit", "semver-checks", "xtask", "udeps", "shear", "doc",
)
CI_ACTIONS = (
    (re.compile(r"cargo-deny-action"), "deny"),
    (re.compile(r"cargo-vet|tool:\s*cargo-vet"), "vet"),
    (re.compile(r"install-action@cargo-hack|tool:\s*cargo-hack"), "hack"),
    (re.compile(r"install-action@(cargo-)?nextest|tool:\s*(cargo-)?nextest"), "nextest"),
    (re.compile(r"cargo-semver-checks-action|tool:\s*cargo-semver-checks"), "semver-checks"),
    (re.compile(r"tool:\s*cargo-udeps"), "udeps"),
    (re.compile(r"tool:\s*cargo-shear"), "shear"),
)
CI_CARGO_RE = re.compile(
    r"(?:\bcargo|\$\{\{\s*env\.CARGO\s*\}\})\s+(\+[\w.-]+\s+)?(" + "|".join(re.escape(s) for s in CI_SUBS) + r")\b"
)
RUST_MENTION_RE = re.compile(r"(?<![A-Za-z0-9_])(cargo|rustfmt|clippy|rustup)(?![A-Za-z0-9_])")
RECIPE_RE = re.compile(r"^(fmt-check|fmt_check|check|clippy|lint|test)[A-Za-z0-9_%-]*(?:[ \t][^:\n]*)?:", re.M)
MAKE_DRIVER_RE = re.compile(r"^(fmt|lint|clippy|test|check)[a-z_%-]*:", re.M)
FMT_UNSTABLE_RE = re.compile(r"can't set `([A-Za-z0-9_]+) = ([^`]*)`")
NIGHTLY_WARNING = "unstable features are only available in nightly channel"
VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


class Exit(Exception):
    def __init__(self, code: int):
        super().__init__(code)
        self.code = code


def log(msg: str) -> None:
    print(f"[rust-gates] {msg}", file=LOG, flush=True)


def err(msg: str) -> None:
    print(f"[rust-gates] error: {msg}", file=sys.stderr, flush=True)


def knob(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def on(name: str) -> bool:
    return knob(name) == "1"


def version_tuple(text: str) -> tuple[int, int, int] | None:
    m = VERSION_RE.search(text)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def child_stdout():
    """Where an uncaptured child's stdout goes: stderr under --json, since
    stdout then carries only the JSON summary."""
    return sys.stderr if LOG is sys.stderr else None


def run_tee(argv: list[str], tee: str, cwd: Path | None = None) -> tuple[int, str]:
    """Run argv streaming one stream to the terminal while capturing it."""
    kwargs = {"stdout": subprocess.PIPE} if tee == "stdout" else {"stderr": subprocess.PIPE, "stdout": child_stdout()}
    try:
        proc = subprocess.Popen(argv, text=True, cwd=cwd, **kwargs)
    except FileNotFoundError:
        err(f"{argv[0]}: command not found")
        return 127, ""
    pipe = proc.stdout if tee == "stdout" else proc.stderr
    dest = (child_stdout() or sys.stdout) if tee == "stdout" else sys.stderr
    lines: list[str] = []
    assert pipe is not None
    for line in pipe:
        dest.write(line)
        dest.flush()
        lines.append(line)
    proc.wait()
    return proc.returncode, "".join(lines)


def run_quiet(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, text=True, capture_output=True, cwd=cwd)
    except FileNotFoundError:
        return subprocess.CompletedProcess(argv, 127, "", f"{argv[0]}: command not found\n")


@dataclass
class Driver:
    directory: Path
    name: str
    hint: str
    runner: str  # "just", "make", or ""
    recipes: list[str] = field(default_factory=list)


@dataclass
class State:
    cwd: Path
    repo_top: Path
    summary: dict[str, str] = field(default_factory=dict)
    drivers: list[Driver] = field(default_factory=list)
    covered: set[str] = field(default_factory=set)
    ci_contract: dict[str, str] = field(default_factory=dict)  # sub → detail
    common_args: list[str] = field(default_factory=list)
    clippy_log: Path | None = None
    json_mode: bool = False


# --- build-driver detection ---------------------------------------------------


def list_recipes(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    names = {m.group(0).split()[0].rstrip(":") for m in RECIPE_RE.finditer(text)}
    return sorted(names)


def mentions_rust(path: Path) -> bool:
    try:
        return bool(RUST_MENTION_RE.search(path.read_text(encoding="utf-8", errors="replace")))
    except OSError:
        return False


def detect_drivers(st: State) -> None:
    d = st.cwd
    while True:
        here = d == st.cwd
        for x in ("x.py", "x"):
            p = d / x
            if p.is_file() and (here or mentions_rust(p)):
                st.drivers.append(Driver(d, x, "use ./x fmt / ./x test", ""))
                break
        for jf in ("justfile", "Justfile", ".justfile"):
            p = d / jf
            if p.is_file() and (here or mentions_rust(p)):
                st.drivers.append(Driver(d, jf, "use just <recipe>", "just", list_recipes(p)))
                break
        mk = d / "Makefile"
        if mk.is_file():
            try:
                body = mk.read_text(encoding="utf-8", errors="replace")
            except OSError:
                body = ""
            if MAKE_DRIVER_RE.search(body) and (here or mentions_rust(mk)):
                st.drivers.append(Driver(d, "Makefile", "use make <target>", "make", list_recipes(mk)))
        if d == st.repo_top or d == d.parent:
            break
        d = d.parent


def driver_label(st: State, drv: Driver) -> str:
    if drv.directory == st.cwd:
        where = drv.name
    elif drv.directory == st.repo_top:
        where = f"{drv.name} at repo root ({st.repo_top})"
    else:
        where = f"{drv.name} in {drv.directory.relative_to(st.repo_top)}"
    return f"{where} ({drv.hint})"


def print_drivers(st: State, header: str) -> None:
    err(header)
    for drv in st.drivers:
        print(f"[rust-gates]   - {driver_label(st, drv)}", file=sys.stderr)
    hints = [f"{d.runner}: {' '.join(d.recipes)}  (from {d.name})" for d in st.drivers if d.runner and d.recipes]
    if hints:
        err("non-mutating recipes it exposes:")
        for h in hints:
            print(f"[rust-gates]   {h}", file=sys.stderr)


def detect_xtask(st: State) -> None:
    found = sorted(
        p for p in st.cwd.glob("**/xtask")
        if p.is_dir() and "target" not in p.relative_to(st.cwd).parts and len(p.relative_to(st.cwd).parts) <= 3
    )
    if found:
        rel = found[0].relative_to(st.cwd)
        st.drivers.append(Driver(st.cwd, f"xtask crate at {rel}", "use cargo xtask <task>", ""))
        return
    manifest = (st.cwd / "Cargo.toml").read_text(encoding="utf-8", errors="replace")
    cfg = ""
    for c in (".cargo/config.toml", ".cargo/config"):
        p = st.cwd / c
        if p.is_file():
            cfg += p.read_text(encoding="utf-8", errors="replace")
    if re.search(r'^\s*"([^"]*/)?xtask"\s*,?\s*$|^\s*members\s*=.*xtask', manifest, re.M) or re.search(r"^\s*xtask\s*=", cfg, re.M):
        st.drivers.append(Driver(st.cwd, "xtask crate", "use cargo xtask <task>", ""))


def delegate_to_driver(st: State) -> None:
    """Run the driver's recognized non-mutating recipes, in a fixed order."""
    order = ("fmt-check", "fmt_check", "check", "lint", "clippy", "test")
    wanted = {r for r in knob("RUST_GATES_DRIVER_RECIPES").split(",") if r}
    ran: list[str] = []
    for drv in st.drivers:
        if not drv.runner:
            continue
        recipes = [r for r in drv.recipes if "%" not in r]  # pattern rules are not runnable bare
        recipes.sort(key=lambda r: (order.index(r) if r in order else len(order), r))
        for recipe in recipes:
            if wanted and recipe not in wanted:
                continue
            if recipe not in order and not wanted:
                continue  # e.g. test-tui, check-wasm: only when asked for by name
            log(f"{drv.runner} {recipe}  (in {drv.directory})")
            code = subprocess.run([drv.runner, recipe], cwd=drv.directory, stdout=child_stdout()).returncode
            ran.append(f"{recipe}={'ok' if code == 0 else f'FAIL({code})'}")
            if code != 0:
                st.summary["driver"] = f"{drv.runner}({','.join(ran)})"
                raise Exit(code)
            for gate in ("fmt", "clippy", "test", "check"):
                if recipe.startswith(gate) or (gate == "clippy" and recipe == "lint"):
                    st.covered.add(gate)
    if not ran:
        err("RUST_GATES_USE_DRIVER=1 but no runnable non-mutating recipe was found")
        raise Exit(3)
    runner = next(d.runner for d in st.drivers if d.runner)
    st.summary["driver"] = f"{runner}({','.join(ran)})"


# --- toolchain preflight --------------------------------------------------------


def installed_toolchains() -> list[str]:
    res = run_quiet(["rustup", "toolchain", "list"])
    if res.returncode != 0:
        return []
    return [line.split()[0] for line in res.stdout.splitlines() if line.strip()]


def preflight(st: State) -> None:
    if not on("RUST_GATES_AUTO_INSTALL"):
        os.environ["RUSTUP_AUTO_INSTALL"] = "0"
    selected_once = False
    while True:
        res = run_quiet(["cargo", "--version"])
        if res.returncode != 0:
            sys.stderr.write(res.stderr)
            if "is not installed" in res.stderr:
                err("the toolchain this directory selects is not installed (rustup auto-install is")
                err("disabled for this run); install it with the command above, or set")
                err("RUST_GATES_AUTO_INSTALL=1 to let rustup download it.")
                raise Exit(6)
            err("cargo --version failed")
            raise Exit(1)
        log(res.stdout.strip())

        rustc_ver = None
        if shutil.which("rustc"):
            r = run_quiet(["rustc", "--version"])
            if r.returncode == 0 and r.stdout.strip():
                log(r.stdout.strip())
                rustc_ver = version_tuple(r.stdout)

        active = ""
        have_rustup = bool(shutil.which("rustup"))
        if have_rustup:
            r = run_quiet(["rustup", "show", "active-toolchain"])
            active = r.stdout.strip() if r.returncode == 0 else ""
            if active:
                log(f"active toolchain: {active}")
        elif (st.cwd / "rust-toolchain").is_file() or (st.cwd / "rust-toolchain.toml").is_file():
            log("toolchain file present at root (rustup honors the nearest one walking up from CWD)")

        # Declared MSRV: the highest rust-version across workspace members.
        # Cargo enforces it only at build time, so surface it before any gate.
        msrv_text, msrv = "", None
        meta = run_quiet(["cargo", "metadata", "--no-deps", "--format-version", "1"])
        if meta.returncode == 0 and meta.stdout.strip():
            try:
                pkgs = json.loads(meta.stdout).get("packages", [])
            except json.JSONDecodeError:
                pkgs = []
            for pkg in pkgs:
                rv = pkg.get("rust_version")
                vt = version_tuple(rv) if rv else None
                if vt and (msrv is None or vt > msrv):
                    msrv, msrv_text = vt, rv
        if msrv and rustc_ver and rustc_ver < msrv:
            rustc_text = ".".join(map(str, rustc_ver))
            pinned = "overridden by '" in active and ("rust-toolchain" in active)
            candidates = [
                t for t in installed_toolchains()
                if (vt := version_tuple(t)) and vt >= msrv and t.split("-")[0][0].isdigit()
            ]
            if candidates and on("RUST_GATES_SELECT_TOOLCHAIN") and not pinned and not selected_once:
                choice = sorted(candidates, key=version_tuple)[-1]
                log(f"rustc {rustc_text} is below declared rust-version {msrv_text}; selecting installed {choice}")
                os.environ["RUSTUP_TOOLCHAIN"] = choice
                selected_once = True
                continue
            err(f"workspace declares rust-version = {msrv_text} but the active rustc is {rustc_text};")
            err("cargo will refuse to build it. Select a toolchain that satisfies the MSRV")
            if candidates:
                err(f"— {', '.join(sorted(candidates))} installed and satisfies it: re-run with")
                err(f"RUSTUP_TOOLCHAIN={sorted(candidates, key=version_tuple)[-1]} (or RUST_GATES_SELECT_TOOLCHAIN=1) —")
            err(f"(e.g. rustup toolchain install {msrv_text}, or the repo's pinned channel) and re-run.")
            raise Exit(6)
        if msrv and rustc_ver:
            log(f"declared rust-version {msrv_text} satisfied by rustc {'.'.join(map(str, rustc_ver))}")

        if have_rustup:
            comps = run_quiet(["rustup", "component", "list", "--installed"]).stdout
            missing = []
            if not on("SKIP_RUST_FMT") and not re.search(r"^rustfmt(-|$)", comps, re.M):
                missing.append("rustfmt")
            if not on("SKIP_RUST_CLIPPY") and not re.search(r"^clippy(-|$)", comps, re.M):
                missing.append("clippy")
            if missing:
                name = active.split()[0] if active else ""
                err(f"the active toolchain lacks components this run needs: {' '.join(missing)}")
                err(f"install them: rustup component add{' --toolchain ' + name if name else ''} {' '.join(missing)}")
                err("(a rust-toolchain.toml can pin them under [toolchain] components = [...])")
                raise Exit(6)

        tc = active.split()[0] if active else (".".join(map(str, rustc_ver)) if rustc_ver else "?")
        st.summary["preflight"] = f"ok({tc}" + (f",msrv={msrv_text}" if msrv_text else "") + ")"
        return


# --- CI contract ----------------------------------------------------------------


def scan_ci_contract(st: State) -> None:
    wf = st.repo_top / ".github" / "workflows"
    if not wf.is_dir():
        return
    for path in sorted(list(wf.glob("*.yml")) + list(wf.glob("*.yaml"))):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in CI_CARGO_RE.finditer(text):
            sub, tc = m.group(2), (m.group(1) or "").strip()
            detail = st.ci_contract.get(sub, "")
            if tc and tc not in detail:
                detail = (detail + " " + tc).strip()
            st.ci_contract[sub] = detail
        for rx, sub in CI_ACTIONS:
            if rx.search(text):
                st.ci_contract.setdefault(sub, "action")


def report_coverage(st: State) -> None:
    if not st.ci_contract:
        return
    covered_subs = set(st.covered)
    if "test" in covered_subs:
        covered_subs.add("nextest")
    if "nextest" in covered_subs:
        covered_subs.add("test")
    contract = " ".join(f"{s}({d})" if d else s for s, d in sorted(st.ci_contract.items()))
    log(f"CI contract (from .github/workflows): {contract}")
    hit = sorted(s for s in st.ci_contract if s in covered_subs)
    miss = sorted(s for s in st.ci_contract if s not in covered_subs)
    extra = sorted(s for s in st.covered if s not in st.ci_contract and s != "check")
    if hit:
        log(f"this run covered:  {' '.join(hit)}" + (f"  (also ran, not in CI contract: {' '.join(extra)})" if extra else ""))
    else:
        log(f"this run covered:  nothing in the CI contract" + (f" (ran: {' '.join(extra)})" if extra else ""))
    if miss:
        reasons = {
            "hack": "feature matrix; only RUST_FEATURES knobs here",
            "miri": "needs nightly; not run",
            "deny": "cargo-deny not installed or skipped",
            "vet": "cargo-vet not installed or skipped",
            "xtask": "repo-specific tasks; not run",
        }
        log("NOT covered:       " + "  ".join(f"{s}({reasons.get(s, 'not run')})" for s in miss))
    st.summary["ci"] = f"{len(hit)}/{len(st.ci_contract)}"


# --- gates ----------------------------------------------------------------------


def fmt_gate(st: State) -> None:
    if on("SKIP_RUST_FMT"):
        log("SKIP_RUST_FMT=1")
        st.summary["fmt"] = "skipped"
        return
    log("cargo fmt --all -- --check")
    code, errtext = run_tee(["cargo", "fmt", "--all", "--", "--check"], "stderr")
    promoted = ""
    if NIGHTLY_WARNING in errtext:
        opts = sorted({f"{k}={v}" for k, v in FMT_UNSTABLE_RE.findall(errtext)})
        if not opts:
            if on("RUST_FMT_ALLOW_UNSTABLE_WARNINGS"):
                log("warning: legacy override accepts dropped rustfmt options; fmt is advisory and does not count as CI coverage")
                st.summary["fmt"] = f"advisory(default-config,exit={code})"
                if code != 0:
                    raise Exit(code)
                return
            err("rustfmt.toml uses nightly-only options that this toolchain silently ignores,")
            err("and the warning names none of them, so they cannot be promoted to --config.")
            err("any diff printed above was measured with those options DROPPED (default config).")
            err("run the repo's own fmt command, or SKIP_RUST_FMT=1 to skip this gate.")
            st.summary["fmt"] = "FAIL(unpromotable)"
            raise Exit(4)
        promoted = ",".join(opts)
        log("rustfmt.toml has nightly-only options this toolchain drops from the file but honors on the CLI")
        log(f"cargo fmt --all -- --config {promoted} --check")
        code, errtext = run_tee(["cargo", "fmt", "--all", "--", "--config", promoted, "--check"], "stderr")
        # rustfmt keeps warning about the file entries even while honoring
        # the --config overrides; only a warning about something we did not
        # promote means the diff is unsound.
        still = ",".join(sorted({f"{k}={v}" for k, v in FMT_UNSTABLE_RE.findall(errtext)}))
        if still and still != promoted:
            err(f"rustfmt warned about nightly-only options beyond the promoted set ({still});")
            err("any diff printed above was measured against the DEFAULT configuration.")
            err("run the repo's own fmt command, or SKIP_RUST_FMT=1 to skip this gate.")
            st.summary["fmt"] = "FAIL(unpromotable)"
            raise Exit(4)
    tag = f"promoted={len(promoted.split(','))}" if promoted else ""
    if code != 0:
        st.summary["fmt"] = f"FAIL({code}{',' + tag if tag else ''})"
        raise Exit(code)
    st.summary["fmt"] = f"ok({tag})" if tag else "ok"
    st.covered.add("fmt")


def clippy_policy(st: State) -> str:
    if (st.cwd / "clippy.toml").is_file() or (st.cwd / ".clippy.toml").is_file():
        return "clippy.toml"
    manifest = (st.cwd / "Cargo.toml").read_text(encoding="utf-8", errors="replace")
    if re.search(r"^\[(workspace\.)?lints\.clippy\]", manifest, re.M):
        return "[lints.clippy] in Cargo.toml"
    if "clippy" in st.ci_contract:
        return "clippy in CI workflows"
    return ""


def run_all_targets(st: State, sub: str, tail: list[str], advisory: bool = False) -> tuple[int, str]:
    """cargo <sub> over --all-targets, retried without benches on E0554.

    Returns (code, stdout) — stdout is the JSON message stream in advisory
    mode and empty otherwise.
    """
    def attempt(targets: list[str]) -> tuple[int, str, str]:
        argv = ["cargo", sub, *st.common_args, *targets]
        if advisory:
            argv.append("--message-format=json")
        argv += tail
        if advisory:
            res = run_quiet(argv)
            sys.stderr.write(res.stderr)
            return res.returncode, res.stdout, res.stderr
        code, errtext = run_tee(argv, "stderr")
        return code, "", errtext

    code, out, errtext = attempt(["--all-targets"])
    if code != 0 and ("E0554" in errtext or '"code":"E0554"' in out.replace(" ", "")):
        log(f"a bench target needs nightly (E0554); retrying cargo {sub} without benches")
        log(f"cargo {sub} (lib, bins, tests, examples)")
        code, out, _ = attempt(["--lib", "--bins", "--tests", "--examples"])
        st.summary.setdefault("_benches", "benches-excluded")
    return code, out


def summarize_clippy_json(st: State, out: str) -> str:
    counts: dict[str, int] = {}
    rendered: list[str] = []
    for line in out.splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("reason") != "compiler-message":
            continue
        m = msg.get("message", {})
        if m.get("level") != "warning":
            continue
        code = (m.get("code") or {}).get("code") or "(uncoded)"
        counts[code] = counts.get(code, 0) + 1
        if m.get("rendered"):
            rendered.append(m["rendered"])
    total = sum(counts.values())
    if not total:
        log("clippy (advisory): no warnings")
        return "0w"
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    log(f"clippy (advisory): {total} warnings across {len(counts)} lints; top:")
    for code, n in top:
        log(f"  {n:>5}  {code}")
    path = Path(tempfile.gettempdir()) / f"rust-gates-clippy-{os.getpid()}.txt"
    path.write_text("".join(rendered), encoding="utf-8")
    st.clippy_log = path
    log(f"full clippy output: {path}")
    return f"{total}w"


def check_and_clippy_gates(st: State) -> None:
    run_check = not on("SKIP_RUST_CHECK") and (on("SKIP_RUST_CLIPPY") or on("RUST_CHECK_ALWAYS"))
    if run_check:
        log("cargo check (selected scope/features, all targets)")
        code, _ = run_all_targets(st, "check", [])
        if code != 0:
            st.summary["check"] = f"FAIL({code})"
            raise Exit(code)
        st.summary["check"] = "ok"
        st.covered.add("check")
    else:
        log("cargo check skipped (Clippy covers it; set RUST_CHECK_ALWAYS=1 to force)")

    if on("SKIP_RUST_CLIPPY"):
        log("SKIP_RUST_CLIPPY=1")
        st.summary["clippy"] = "skipped"
        return
    policy = clippy_policy(st)
    forced = knob("RUST_DENY_WARNINGS")
    deny = forced == "1" if forced in ("0", "1") else bool(policy)
    if deny:
        log(f"cargo clippy (selected scope/features, all targets, deny warnings{'; policy: ' + policy if policy else ''})")
        code, _ = run_all_targets(st, "clippy", ["--", "-D", "warnings"])
        extra = st.summary.pop("_benches", "")
        if code != 0:
            st.summary["clippy"] = f"FAIL({code})"
            raise Exit(code)
        st.summary["clippy"] = "deny(ok" + (f",{extra}" if extra else "") + ")"
    else:
        if not policy and forced == "":
            log("no Clippy policy found (no clippy.toml, no [lints.clippy], no clippy in CI);")
            log("running Clippy as advisory: warnings are reported but not fatal (RUST_DENY_WARNINGS=1 to enforce)")
        log("cargo clippy (selected scope/features, all targets, advisory)")
        code, out = run_all_targets(st, "clippy", [], advisory=True)
        extra = st.summary.pop("_benches", "")
        if code != 0:
            st.summary["clippy"] = f"FAIL({code})"
            raise Exit(code)
        tag = summarize_clippy_json(st, out)
        st.summary["clippy"] = f"advisory({tag}" + (f",{extra}" if extra else "") + ")"
    st.covered.add("clippy")


TEST_RESULT_RE = re.compile(r"^test result: \w+\. (\d+) passed; (\d+) failed; (\d+) ignored", re.M)
NEXTEST_SUMMARY_RE = re.compile(r"Summary \[.*?\]\s+(\d+) tests? run: (\d+) passed(?:.*?(\d+) failed)?(?:.*?(\d+) skipped)?")


def test_gate(st: State) -> None:
    if on("SKIP_RUST_TEST"):
        log("SKIP_RUST_TEST=1")
        st.summary["test"] = "skipped"
        return
    targets = ["--all-targets"] if on("RUST_TEST_ALL_TARGETS") else []
    runner = "cargo"
    if (st.cwd / ".config" / "nextest.toml").is_file() and knob("RUST_TEST_RUNNER") != "cargo":
        if run_quiet(["cargo", "nextest", "--version"]).returncode == 0:
            runner = "nextest"
        else:
            err(".config/nextest.toml is present, so nextest's test groups, retries, and")
            err("timeouts are this repo's test contract, but cargo-nextest is not installed.")
            err("install it (cargo install --locked cargo-nextest) or set RUST_TEST_RUNNER=cargo")
            err("to run cargo test and knowingly ignore that configuration.")
            st.summary["test"] = "FAIL(nextest-missing)"
            raise Exit(5)

    def doc_tests() -> tuple[int, str]:
        log("cargo test --doc (selected scope/features)")
        return run_tee(["cargo", "test", *st.common_args, "--doc"], "stdout")

    if runner == "nextest":
        log("cargo nextest run (selected scope/features; .config/nextest.toml governs)")
        code, errtext = run_tee(["cargo", "nextest", "run", *st.common_args, *targets], "stderr")
        if code != 0:
            st.summary["test"] = f"FAIL({code})"
            raise Exit(code)
        m = NEXTEST_SUMMARY_RE.search(errtext)
        counts = f"{m.group(2)}/{m.group(3) or 0}/{m.group(4) or 0}" if m else "?"
        log("cargo test --doc (nextest does not run doctests)")
        code, out = run_tee(["cargo", "test", *st.common_args, "--doc"], "stdout")
        if code != 0:
            st.summary["test"] = f"FAIL(doc,{code})"
            raise Exit(code)
        st.summary["test"] = f"nextest({counts})"
    else:
        log(f"cargo test (selected scope/features{', all targets' if targets else ''})")
        code, out = run_tee(["cargo", "test", *st.common_args, *targets], "stdout")
        if code != 0:
            st.summary["test"] = f"FAIL({code})"
            raise Exit(code)
        p = f = i = 0
        for m in TEST_RESULT_RE.finditer(out):
            p, f, i = p + int(m.group(1)), f + int(m.group(2)), i + int(m.group(3))
        if on("RUST_DOC_TESTS"):
            code, dout = doc_tests()
            if code != 0:
                st.summary["test"] = f"FAIL(doc,{code})"
                raise Exit(code)
            for m in TEST_RESULT_RE.finditer(dout):
                p, f, i = p + int(m.group(1)), f + int(m.group(2)), i + int(m.group(3))
        st.summary["test"] = f"cargo({p}/{f}/{i})"
    st.covered.add("test")
    if runner == "nextest":
        st.covered.add("nextest")


def policy_gates(st: State) -> None:
    for name, policy_file, tool, argv in (
        ("deny", st.cwd / "deny.toml", "cargo-deny", ["cargo", "deny", "check"]),
        ("vet", st.cwd / "supply-chain" / "config.toml", "cargo-vet", ["cargo", "vet"]),
    ):
        if not policy_file.is_file():
            st.summary[name] = "n/a"
            continue
        label = "deny.toml" if name == "deny" else "supply-chain/"
        if on(f"SKIP_RUST_{name.upper()}"):
            log(f"SKIP_RUST_{name.upper()}=1 ({label} present)")
            st.summary[name] = "skipped"
            continue
        if run_quiet(["cargo", name, "--version"]).returncode != 0:
            log(f"note: {label} present but {tool} is not installed; that policy was NOT checked")
            log(f"      (cargo install --locked {tool}, or SKIP_RUST_{name.upper()}=1 to silence)")
            st.summary[name] = "NOT_RUN"
            continue
        log(f"{' '.join(argv)} ({label} governs)")
        code = subprocess.run(argv, stdout=child_stdout()).returncode
        if code != 0:
            st.summary[name] = f"FAIL({code})"
            raise Exit(code)
        st.summary[name] = "ok"
        st.covered.add(name)


# --- main -----------------------------------------------------------------------


def print_summary(st: State, code: int) -> None:
    order = ("driver", "preflight", "fmt", "check", "clippy", "test", "deny", "vet", "ci")
    parts = [f"{k}={st.summary[k]}" for k in order if k in st.summary]
    parts.append(f"exit={code}")
    if st.json_mode:
        payload = {**{k: st.summary[k] for k in order if k in st.summary}, "exit": code,
                   "covered": sorted(st.covered), "ci_contract": st.ci_contract}
        if st.clippy_log:
            payload["clippy_log"] = str(st.clippy_log)
        print(json.dumps(payload), flush=True)
    else:
        log("summary: " + " ".join(parts))


def main(argv: list[str]) -> int:
    global LOG
    if argv and argv[0] in ("--help", "-h"):
        print(__doc__.replace("rust_gates.py", PROG, 1).replace("Non-mutating", f"Usage: {PROG} [--json]\n\nNon-mutating", 1))
        return 0
    json_mode = "--json" in argv
    rest = [a for a in argv if a != "--json"]
    if rest:
        err(f"unsupported argument: {rest[0]}")
        return 2
    if json_mode:
        LOG = sys.stderr

    cwd = Path.cwd().resolve()
    top = run_quiet(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    repo_top = Path(top.stdout.strip()).resolve() if top.returncode == 0 and top.stdout.strip() else cwd
    st = State(cwd=cwd, repo_top=repo_top, json_mode=json_mode)

    code = 0
    try:
        code = run_pipeline(st)
    except Exit as e:
        code = e.code
    print_summary(st, code)
    return code


def run_pipeline(st: State) -> int:
    cwd = st.cwd
    if True:
        detect_drivers(st)
        if not (cwd / "Cargo.toml").is_file():
            err("no Cargo.toml; run from a Cargo package/workspace root")
            if st.drivers:
                print_drivers(st, "this directory has a build driver; its recipes are the contract:")
            raise Exit(1)
        detect_xtask(st)
        scan_ci_contract(st)

        if st.drivers and on("RUST_GATES_USE_DRIVER"):
            delegate_to_driver(st)
            report_coverage(st)
            return 0
        if st.drivers and not on("RUST_GATES_FORCE_CARGO"):
            print_drivers(st, "build driver detected; raw Cargo gates are not this repo's contract:")
            err("run the driver's fmt/lint/test commands, RUST_GATES_USE_DRIVER=1 to run its")
            err("non-mutating recipes from here, or RUST_GATES_FORCE_CARGO=1 for raw Cargo")
            raise Exit(3)

        if not shutil.which("cargo"):
            err("cargo not found on PATH")
            raise Exit(127)
        preflight(st)

        if on("RUST_ALL_FEATURES") and knob("RUST_FEATURES"):
            err("choose RUST_ALL_FEATURES or RUST_FEATURES, not both")
            raise Exit(2)
        pkg = knob("RUST_PACKAGE")
        st.common_args = ["-p", pkg] if pkg else ["--workspace"]
        if (cwd / "Cargo.lock").is_file() and not on("RUST_UNLOCKED"):
            st.common_args.append("--locked")
        if on("RUST_ALL_FEATURES"):
            st.common_args.append("--all-features")
        elif knob("RUST_FEATURES"):
            st.common_args += ["--features", knob("RUST_FEATURES")]
        if on("RUST_NO_DEFAULT_FEATURES"):
            st.common_args.append("--no-default-features")

        fmt_gate(st)
        check_and_clippy_gates(st)
        test_gate(st)
        policy_gates(st)
        report_coverage(st)
        log("ok")
        return 0


if __name__ == "__main__":
    _st_code = 0
    try:
        _st_code = main(sys.argv[1:])
    finally:
        pass
    sys.exit(_st_code)
