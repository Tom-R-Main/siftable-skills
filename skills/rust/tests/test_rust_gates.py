#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "rust-gates.sh"

# `cargo metadata` is a preflight read, not a gate: it is answered from
# CARGO_FAKE_METADATA and deliberately not logged, so gate-order assertions
# stay about gates.
FAKE_CARGO = (
    "#!/bin/sh\n"
    'if [ "${1:-}" = metadata ]; then printf \'%s\\n\' "${CARGO_FAKE_METADATA:-}"; exit 0; fi\n'
    'printf \'%s\\n\' "$*" >> "$CARGO_FAKE_LOG"\n'
    'if [ "${1:-}" = --version ]; then printf \'cargo 1.0.0 (fake)\\n\'; fi\n'
)

# Behaves like a rustup proxy whose selected toolchain is not installed, and
# records whether the script disabled auto-install.
FAKE_CARGO_TOOLCHAIN_MISSING = (
    "#!/bin/sh\n"
    'printf \'auto=%s\\n\' "${RUSTUP_AUTO_INSTALL:-unset}" >> "$CARGO_FAKE_LOG"\n'
    "printf \"error: toolchain '1.98.0-fake' is not installed\\n\" >&2\n"
    "printf 'help: run `rustup toolchain install 1.98.0-fake` to install it\\n' >&2\n"
    "exit 1\n"
)

# Reports RUSTC_FAKE_VERSION, or the numeric prefix of RUSTUP_TOOLCHAIN when
# the script selected a toolchain for the run.
FAKE_RUSTC = (
    "#!/bin/sh\n"
    'v="${RUSTC_FAKE_VERSION:-1.95.0}"\n'
    'if [ -n "${RUSTUP_TOOLCHAIN:-}" ]; then v="${RUSTUP_TOOLCHAIN%%-*}"; fi\n'
    'printf \'rustc %s (fake)\\n\' "$v"\n'
)

# Logs each recipe it is asked to run; fails the recipe named by JUST_FAKE_FAIL.
FAKE_JUST = (
    "#!/bin/sh\n"
    'printf \'just %s\\n\' "$*" >> "$CARGO_FAKE_LOG"\n'
    'if [ "${1:-}" = "${JUST_FAKE_FAIL:-}" ]; then exit 7; fi\n'
)

FAKE_RUSTUP = (
    "#!/bin/sh\n"
    'case "${1:-} ${2:-}" in\n'
    '  "show active-toolchain") printf \'%s\\n\' "${RUSTUP_FAKE_ACTIVE:-fake-toolchain (default)}" ;;\n'
    '  "component list") printf \'%s\\n\' ${RUSTUP_FAKE_COMPONENTS:-rustfmt-fake clippy-fake} ;;\n'
    '  "toolchain list") printf \'%s\\n\' ${RUSTUP_FAKE_TOOLCHAINS:-} ;;\n'
    "esac\n"
)

# Fails --all-targets builds the way stable cargo does when a bench target
# uses `#![feature(test)]`, and succeeds once benches are excluded.
FAKE_CARGO_NIGHTLY_BENCH = FAKE_CARGO + (
    'case "$*" in\n'
    "  *--all-targets*)\n"
    "    printf 'error[E0554]: `#![feature]` may not be used on the stable release channel\\n' >&2\n"
    "    printf 'error: could not compile `globset` (bench \"bench\") due to 1 previous error\\n' >&2\n"
    "    exit 101 ;;\n"
    "esac\n"
)

# Prints realistic `cargo test` stdout so result parsing and --json stdout
# hygiene are exercised.
FAKE_CARGO_NOISY_TESTS = FAKE_CARGO + (
    'if [ "${1:-}" = test ]; then\n'
    "  printf '\\nrunning 3 tests\\ntest a ... ok\\ntest b ... ok\\ntest c ... ignored\\n\\n'\n"
    "  printf 'test result: ok. 2 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.00s\\n\\n'\n"
    "  printf 'test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s\\n'\n"
    "fi\n"
)

# Reports cargo-deny / cargo-vet as installed and accepts their check commands.
FAKE_CARGO_WITH_DENY_AND_VET = FAKE_CARGO + (
    'if [ "${1:-}" = deny ] && [ "${2:-}" = --version ]; then printf \'cargo-deny 0.18 (fake)\\n\'; fi\n'
    'if [ "${1:-}" = vet ] && [ "${2:-}" = --version ]; then printf \'cargo-vet 0.10 (fake)\\n\'; fi\n'
)

# Reports cargo-deny / cargo-vet as missing.
FAKE_CARGO_WITHOUT_DENY_AND_VET = FAKE_CARGO + (
    'if [ "${1:-}" = deny ] || [ "${1:-}" = vet ]; then printf \'error: no such command\\n\' >&2; exit 101; fi\n'
)

# Emits rustfmt's generic nightly warning with no option name, which the
# script cannot promote to --config.
FAKE_CARGO_UNPARSEABLE_FMT_WARNING = FAKE_CARGO + (
    'if [ "${1:-}" = fmt ]; then\n'
    "  printf 'Warning: unstable features are only available in nightly channel.\\n' >&2\n"
    "fi\n"
)

# Emits the real stable-rustfmt warning for two file-level options. Real
# rustfmt (verified on 1.95.0) keeps emitting these on EVERY run while the
# entries stay in rustfmt.toml, including the run where --config overrides
# them and they are honored, so this fake warns unconditionally.
FAKE_CARGO_NAMED_FMT_WARNINGS = FAKE_CARGO + (
    'if [ "${1:-}" = fmt ]; then\n'
    "  printf \"Warning: can't set \\`imports_granularity = Item\\`, unstable features are only available in nightly channel.\\n\" >&2\n"
    "  printf \"Warning: can't set \\`group_imports = StdExternalCrate\\`, unstable features are only available in nightly channel.\\n\" >&2\n"
    "fi\n"
)

# Warns about one option on the plain run and a DIFFERENT one on the --config
# run, so the promoted set does not cover what rustfmt still rejects.
FAKE_CARGO_SHIFTING_FMT_WARNINGS = FAKE_CARGO + (
    'if [ "${1:-}" = fmt ]; then\n'
    '  case "$*" in\n'
    "    *--config*) printf \"Warning: can't set \\`wrap_comments = true\\`, unstable features are only available in nightly channel.\\n\" >&2 ;;\n"
    "    *) printf \"Warning: can't set \\`imports_granularity = Item\\`, unstable features are only available in nightly channel.\\n\" >&2 ;;\n"
    "  esac\n"
    "fi\n"
)

# Reports cargo-nextest as installed.
FAKE_CARGO_WITH_NEXTEST = FAKE_CARGO + (
    'if [ "${1:-}" = nextest ] && [ "${2:-}" = --version ]; then printf \'cargo-nextest 0.9 (fake)\\n\'; fi\n'
)

# Reports cargo-nextest as missing.
FAKE_CARGO_WITHOUT_NEXTEST = FAKE_CARGO + (
    'if [ "${1:-}" = nextest ]; then printf \'error: no such command\\n\' >&2; exit 101; fi\n'
)


def write_fake_cargo(root: Path, body: str) -> Path:
    """Install fake cargo plus fake rustc and rustup so preflight is deterministic."""
    fake_bin = root / "bin"
    fake_bin.mkdir(exist_ok=True)
    for name, text in (("cargo", body), ("rustc", FAKE_RUSTC), ("rustup", FAKE_RUSTUP), ("just", FAKE_JUST)):
        tool = fake_bin / name
        tool.write_text(text, encoding="utf-8")
        tool.chmod(0o755)
    return fake_bin


def git_init(root: Path) -> None:
    subprocess.run(
        ["git", "init", "-q", str(root)],
        check=True,
        capture_output=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull},
    )


def run_gates(
    root: Path,
    fake_bin: Path | None = None,
    cwd: Path | None = None,
    **knobs: str,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    env = os.environ.copy()
    log = root / "cargo.log"
    env["CARGO_FAKE_LOG"] = str(log)
    if fake_bin is not None:
        env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env.update(knobs)
    result = subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        cwd=cwd or root,
        capture_output=True,
        text=True,
        env=env,
    )
    return result, log


def log_lines(log: Path) -> list[str]:
    return log.read_text(encoding="utf-8").splitlines()


class RustGatesTests(unittest.TestCase):
    def test_help_does_not_require_cargo(self) -> None:
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            env={"PATH": ""},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage: rust-gates.sh", result.stdout)

    def test_unsupported_argument_is_rejected(self) -> None:
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT), "--workspace"],
            capture_output=True,
            text=True,
            env={"PATH": ""},
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("unsupported argument", result.stderr)

    def test_missing_manifest_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result, _ = run_gates(Path(temp))
            self.assertEqual(result.returncode, 1)
            self.assertIn("no Cargo.toml", result.stderr)

    def test_missing_manifest_still_names_a_local_driver(self) -> None:
        # Running from a repo root that holds the justfile but not the
        # workspace should point at the driver, not just "no Cargo.toml".
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "justfile").write_text(
                'set working-directory := "rs"\n\nfmt-check:\n\tcargo fmt --check\n\ntest *args:\n\tcargo test {{args}}\n',
                encoding="utf-8",
            )
            result, _ = run_gates(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("no Cargo.toml", result.stderr)
            self.assertIn("build driver", result.stderr)
            self.assertIn("just: fmt-check test", result.stderr)

    # --- build-driver detection ------------------------------------------

    def test_build_driver_refuses_raw_cargo(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "justfile").write_text("test:\n\tcargo test\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 3)
            self.assertIn("build driver detected", result.stderr)
            self.assertFalse(log.exists(), "no cargo gate may run when a driver is detected")

            forced, forced_log = run_gates(root, fake_bin, RUST_GATES_FORCE_CARGO="1")
            self.assertEqual(forced.returncode, 0, forced.stderr)
            self.assertTrue(forced_log.exists())

    def test_refusal_lists_non_mutating_recipes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "justfile").write_text(
                "fmt:\n\tcargo fmt\n\nfmt-check:\n\tcargo fmt --check\n\nfix *args:\n\tcargo clippy --fix\n\n"
                "clippy *args:\n\tcargo clippy {{args}}\n\ntest *args:\n\tcargo nextest run {{args}}\n\n"
                "test-tui:\n\tcargo test -p tui\n",
                encoding="utf-8",
            )
            result, _ = run_gates(root, write_fake_cargo(root, FAKE_CARGO))
            self.assertEqual(result.returncode, 3)
            self.assertIn("just: clippy fmt-check test test-tui", result.stderr)
            self.assertNotRegex(result.stderr, r"just: .*\bfix\b")
            self.assertNotRegex(result.stderr, r"just: .*\bfmt\b ")

    def test_makefile_pattern_targets_are_listed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "Makefile").write_text(
                "check-%:\n\tcargo check\n\ntest-%:\n\tcargo test\n\nclippy-%:\n\tcargo clippy -- -D warnings\n\ndoc:\n\tcargo doc\n",
                encoding="utf-8",
            )
            result, _ = run_gates(root, write_fake_cargo(root, FAKE_CARGO))
            self.assertEqual(result.returncode, 3)
            self.assertIn("make: check-% clippy-% test-%", result.stderr)

    def test_root_driver_governs_nested_workspace(self) -> None:
        # Layout: <git root>/justfile + <git root>/rs/Cargo.toml, run from rs/.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            git_init(root)
            (root / "justfile").write_text(
                'set working-directory := "rs"\n\nclippy *args:\n\tcargo clippy --tests {{args}}\n\ntest *args:\n\tcargo nextest run {{args}}\n',
                encoding="utf-8",
            )
            ws = root / "rs"
            ws.mkdir()
            (ws / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin, cwd=ws)
            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertIn("justfile at repo root", result.stderr)
            self.assertIn("just: clippy test", result.stderr)
            self.assertFalse(log.exists())

    def test_parent_driver_without_rust_mentions_is_ignored(self) -> None:
        # A polyglot monorepo's top-level justfile that never touches cargo
        # is not this workspace's contract.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            git_init(root)
            (root / "justfile").write_text("deploy:\n\tkubectl apply -f k8s/\n", encoding="utf-8")
            ws = root / "svc"
            ws.mkdir()
            (ws / "Cargo.toml").write_text("[package]\nname = \"svc\"\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin, cwd=ws)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(log.exists())

    def test_driver_search_stops_at_git_top_level(self) -> None:
        # A justfile above the git root (e.g. in $HOME) must not count.
        with tempfile.TemporaryDirectory() as temp:
            outer = Path(temp).resolve()
            (outer / "justfile").write_text("test:\n\tcargo test\n", encoding="utf-8")
            root = outer / "repo"
            root.mkdir()
            git_init(root)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            fake_bin = write_fake_cargo(outer, FAKE_CARGO)
            result, log = run_gates(outer, fake_bin, cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(log.exists())

    def test_nested_xtask_directory_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[workspace]\nmembers = [\"tools/xtask\"]\n", encoding="utf-8")
            (root / "tools" / "xtask").mkdir(parents=True)
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 3)
            self.assertIn("tools/xtask", result.stderr)
            self.assertFalse(log.exists())

    def test_xtask_workspace_member_without_root_directory_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text(
                "[workspace]\nmembers = [\n  \"app\",\n  \"tools/xtask\",\n]\n",
                encoding="utf-8",
            )
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 3)
            self.assertIn("xtask crate", result.stderr)
            self.assertFalse(log.exists())

    def test_cargo_alias_xtask_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / ".cargo").mkdir()
            (root / ".cargo" / "config.toml").write_text(
                "[alias]\nxtask = \"run --package xtask --\"\n",
                encoding="utf-8",
            )
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 3)
            self.assertIn("xtask crate", result.stderr)
            self.assertFalse(log.exists())

    def test_similar_crate_name_does_not_trip_detection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text(
                "[workspace]\nmembers = [\n  \"myxtask\",\n]\n",
                encoding="utf-8",
            )
            (root / "myxtask").mkdir()
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(log.exists())

    def test_missing_cargo_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            empty_bin = root / "empty-bin"
            empty_bin.mkdir()
            result = subprocess.run(
                ["/bin/bash", str(SCRIPT)],
                cwd=root,
                capture_output=True,
                text=True,
                env={"PATH": str(empty_bin)},
            )
            self.assertEqual(result.returncode, 127)
            self.assertIn("cargo not found", result.stderr)

    # --- gate order and selection ----------------------------------------

    def test_gate_order_skips_check_and_respects_lockfile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "Cargo.lock").write_text("version = 3\n", encoding="utf-8")
            (root / "clippy.toml").write_text("", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                log_lines(log),
                [
                    "--version",
                    "fmt --all -- --check",
                    "clippy --workspace --locked --all-targets -- -D warnings",
                    "test --workspace --locked",
                ],
            )

    def test_package_and_feature_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(
                root,
                fake_bin,
                RUST_PACKAGE="demo",
                RUST_FEATURES="a,b",
                RUST_NO_DEFAULT_FEATURES="1",
                SKIP_RUST_FMT="1",
                SKIP_RUST_CLIPPY="1",
                RUST_TEST_ALL_TARGETS="1",
                RUST_DOC_TESTS="1",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                log_lines(log),
                [
                    "--version",
                    "check -p demo --features a,b --no-default-features --all-targets",
                    "test -p demo --features a,b --no-default-features --all-targets",
                    "test -p demo --features a,b --no-default-features --doc",
                ],
            )

    def test_conflicting_feature_knobs_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, _ = run_gates(root, fake_bin, RUST_ALL_FEATURES="1", RUST_FEATURES="a")
            self.assertEqual(result.returncode, 2)
            self.assertIn("not both", result.stderr)

    # --- rustfmt nightly-only options ------------------------------------

    def test_named_nightly_options_are_promoted_to_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "rustfmt.toml").write_text(
                'imports_granularity = "Item"\ngroup_imports = "StdExternalCrate"\n',
                encoding="utf-8",
            )
            fake_bin = write_fake_cargo(root, FAKE_CARGO_NAMED_FMT_WARNINGS)
            result, log = run_gates(root, fake_bin, SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1", SKIP_RUST_TEST="1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                log_lines(log),
                [
                    "--version",
                    "fmt --all -- --check",
                    "fmt --all -- --config group_imports=StdExternalCrate,imports_granularity=Item --check",
                ],
            )
            self.assertNotIn("WRONG", result.stderr)
            self.assertNotIn("DEFAULT configuration", result.stderr)

    def test_warnings_beyond_promoted_set_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "rustfmt.toml").write_text('imports_granularity = "Item"\n', encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_SHIFTING_FMT_WARNINGS)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 4)
            self.assertIn("beyond the promoted set (wrap_comments=true)", result.stderr)
            self.assertEqual(
                log_lines(log),
                ["--version", "fmt --all -- --check", "fmt --all -- --config imports_granularity=Item --check"],
            )

    def test_unparseable_nightly_warning_fails_instead_of_reporting_diffs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "rustfmt.toml").write_text("imports_granularity = \"Crate\"\n", encoding="utf-8")
            (root / "clippy.toml").write_text("", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_UNPARSEABLE_FMT_WARNING)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 4)
            self.assertIn("DROPPED", result.stderr)
            self.assertEqual(log_lines(log), ["--version", "fmt --all -- --check"])

            skipped, skipped_log = run_gates(root, fake_bin, SKIP_RUST_FMT="1")
            self.assertEqual(skipped.returncode, 0, skipped.stderr)
            self.assertIn("clippy --workspace --all-targets -- -D warnings", skipped_log.read_text(encoding="utf-8"))

    # --- clippy policy -----------------------------------------------------

    def _clippy_line(self, root: Path, **knobs: str) -> tuple[subprocess.CompletedProcess[str], str]:
        fake_bin = write_fake_cargo(root, FAKE_CARGO)
        (root / "cargo.log").unlink(missing_ok=True)  # each run appends; isolate this one
        result, log = run_gates(root, fake_bin, SKIP_RUST_FMT="1", SKIP_RUST_TEST="1", **knobs)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [l for l in log_lines(log) if l.startswith("clippy")]
        self.assertEqual(len(lines), 1, lines)
        return result, lines[0]

    def test_clippy_is_advisory_without_a_repo_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            result, line = self._clippy_line(root)
            self.assertEqual(line, "clippy --workspace --all-targets --message-format=json")
            self.assertIn("no Clippy policy found", result.stdout)

            _, forced = self._clippy_line(root, RUST_DENY_WARNINGS="1")
            self.assertEqual(forced, "clippy --workspace --all-targets -- -D warnings")

    def test_clippy_denies_when_repo_declares_a_policy(self) -> None:
        cases = {
            "clippy.toml": lambda r: (r / ".clippy.toml").write_text("", encoding="utf-8"),
            "[lints.clippy]": lambda r: (r / "Cargo.toml").write_text(
                "[package]\nname = \"demo\"\n\n[lints.clippy]\nunwrap_used = \"deny\"\n", encoding="utf-8"
            ),
            "workspace lints": lambda r: (r / "Cargo.toml").write_text(
                "[workspace]\n\n[workspace.lints.clippy]\nunwrap_used = \"deny\"\n", encoding="utf-8"
            ),
            "clippy in CI": lambda r: (
                (r / ".github" / "workflows").mkdir(parents=True),
                (r / ".github" / "workflows" / "ci.yml").write_text("run: cargo clippy -- -D warnings\n", encoding="utf-8"),
            ),
        }
        for name, setup in cases.items():
            with self.subTest(policy=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                git_init(root)
                (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
                setup(root)
                result, line = self._clippy_line(root)
                self.assertEqual(line, "clippy --workspace --all-targets -- -D warnings")
                self.assertIn("policy:", result.stdout)

                _, relaxed = self._clippy_line(root, RUST_DENY_WARNINGS="0")
                self.assertEqual(relaxed, "clippy --workspace --all-targets --message-format=json")

    def test_nightly_only_bench_targets_are_excluded_on_e0554(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "clippy.toml").write_text("", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_NIGHTLY_BENCH)
            result, log = run_gates(root, fake_bin, SKIP_RUST_FMT="1", SKIP_RUST_TEST="1", RUST_CHECK_ALWAYS="1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("retrying cargo check without benches", result.stdout)
            self.assertIn("retrying cargo clippy without benches", result.stdout)
            self.assertEqual(
                log_lines(log),
                [
                    "--version",
                    "check --workspace --all-targets",
                    "check --workspace --lib --bins --tests --examples",
                    "clippy --workspace --all-targets -- -D warnings",
                    "clippy --workspace --lib --bins --tests --examples -- -D warnings",
                ],
            )

    # --- toolchain preflight ---------------------------------------------

    def test_missing_pinned_toolchain_is_reported_not_installed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_TOOLCHAIN_MISSING)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 6)
            self.assertIn("is not installed", result.stderr)
            self.assertIn("RUST_GATES_AUTO_INSTALL=1", result.stderr)
            self.assertEqual(log_lines(log), ["auto=0"], "rustup auto-install must be disabled by default")

            log.unlink()
            allowed, allowed_log = run_gates(root, fake_bin, RUST_GATES_AUTO_INSTALL="1")
            self.assertEqual(log_lines(allowed_log), ["auto=unset"])

    def test_missing_components_are_reported_with_install_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(
                root, fake_bin, RUSTUP_FAKE_COMPONENTS="cargo-fake rustc-fake", RUSTUP_FAKE_ACTIVE="1.98.0-fake (overridden by rust-toolchain.toml)"
            )
            self.assertEqual(result.returncode, 6)
            self.assertIn("lacks components this run needs: rustfmt clippy", result.stderr)
            self.assertIn("rustup component add --toolchain 1.98.0-fake rustfmt clippy", result.stderr)
            self.assertEqual(log_lines(log), ["--version"], "no gate may run before preflight passes")

            log.unlink()
            fmt_only, _ = run_gates(root, fake_bin, RUSTUP_FAKE_COMPONENTS="rustfmt-fake", SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1")
            self.assertEqual(fmt_only.returncode, 0, fmt_only.stderr)

    def test_declared_msrv_above_rustc_fails_before_any_gate(self) -> None:
        metadata = '{"packages":[{"name":"a","rust_version":"1.80"},{"name":"b","rust_version":"1.96"}]}'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin, CARGO_FAKE_METADATA=metadata, RUSTC_FAKE_VERSION="1.95.0")
            self.assertEqual(result.returncode, 6)
            self.assertIn("rust-version = 1.96", result.stderr)
            self.assertIn("rustc is 1.95.0", result.stderr)
            self.assertEqual(log_lines(log), ["--version"])

            log.unlink()
            ok, ok_log = run_gates(root, fake_bin, CARGO_FAKE_METADATA=metadata, RUSTC_FAKE_VERSION="1.96.1")
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertIn("declared rust-version 1.96 satisfied by rustc 1.96.1", ok.stdout)
            self.assertIn("fmt --all -- --check", log_lines(ok_log))

    # --- dependency policy gates -----------------------------------------

    def test_deny_and_vet_run_when_policy_files_and_tools_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            (root / "deny.toml").write_text("[advisories]\n", encoding="utf-8")
            (root / "supply-chain").mkdir()
            (root / "supply-chain" / "config.toml").write_text("[policy]\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_WITH_DENY_AND_VET)
            result, log = run_gates(root, fake_bin, SKIP_RUST_FMT="1", SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1", SKIP_RUST_TEST="1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(log_lines(log), ["--version", "deny --version", "deny check", "vet --version", "vet"])

            log.unlink()
            skipped, skipped_log = run_gates(
                root, fake_bin, SKIP_RUST_FMT="1", SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1", SKIP_RUST_TEST="1",
                SKIP_RUST_DENY="1", SKIP_RUST_VET="1",
            )
            self.assertEqual(skipped.returncode, 0, skipped.stderr)
            self.assertEqual(log_lines(skipped_log), ["--version"])

    def test_missing_policy_tools_are_named_not_silently_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            (root / "deny.toml").write_text("[advisories]\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_WITHOUT_DENY_AND_VET)
            result, log = run_gates(root, fake_bin, SKIP_RUST_FMT="1", SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1", SKIP_RUST_TEST="1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("deny.toml present but cargo-deny is not installed; that policy was NOT checked", result.stdout)
            self.assertNotIn("deny check", log.read_text(encoding="utf-8"))

    # --- summary, coverage, delegation, toolchain selection ---------------

    def test_summary_line_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, _ = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 0, result.stderr)
            last = result.stdout.strip().splitlines()[-1]
            self.assertTrue(last.startswith("[rust-gates] summary: "), last)
            for token in ("preflight=ok(fake-toolchain)", "fmt=ok", "clippy=advisory(0w)", "test=cargo(0/0/0)", "deny=n/a", "vet=n/a", "exit=0"):
                self.assertIn(token, last)

            as_json = subprocess.run(
                ["/bin/bash", str(SCRIPT), "--json"], cwd=root, capture_output=True, text=True,
                env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}", "CARGO_FAKE_LOG": str(root / "cargo.log")},
            )
            self.assertEqual(as_json.returncode, 0, as_json.stderr)
            payload = json.loads(as_json.stdout.strip().splitlines()[-1])
            self.assertEqual(payload["exit"], 0)
            self.assertEqual(payload["clippy"], "advisory(0w)")
            self.assertIn("fmt", payload["covered"])
            self.assertIn("[rust-gates] cargo fmt --all -- --check", as_json.stderr, "logs move to stderr under --json")
            self.assertNotIn("[rust-gates]", as_json.stdout, "stdout carries only the JSON summary")

    def test_json_stdout_stays_clean_and_test_counts_are_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_NOISY_TESTS)
            plain, _ = run_gates(root, fake_bin, SKIP_RUST_FMT="1", SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1")
            self.assertEqual(plain.returncode, 0, plain.stderr)
            self.assertIn("test=cargo(6/0/1)", plain.stdout)
            self.assertIn("running 3 tests", plain.stdout, "test output streams to stdout normally")

            as_json = subprocess.run(
                ["/bin/bash", str(SCRIPT), "--json"], cwd=root, capture_output=True, text=True,
                env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}", "CARGO_FAKE_LOG": str(root / "cargo.log"),
                     "SKIP_RUST_FMT": "1", "SKIP_RUST_CLIPPY": "1", "SKIP_RUST_CHECK": "1"},
            )
            self.assertEqual(as_json.returncode, 0, as_json.stderr)
            payload = json.loads(as_json.stdout)  # the WHOLE stdout must be the JSON document
            self.assertEqual(payload["test"], "cargo(6/0/1)")
            self.assertIn("running 3 tests", as_json.stderr, "child stdout is rerouted to stderr under --json")

    def test_failure_summary_names_the_failed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "rustfmt.toml").write_text('imports_granularity = "Crate"\n', encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_UNPARSEABLE_FMT_WARNING)
            result, _ = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 4)
            self.assertIn("fmt=FAIL(unpromotable)", result.stdout)
            self.assertIn("exit=4", result.stdout)

    def test_ci_contract_coverage_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            wf = root / ".github" / "workflows"
            wf.mkdir(parents=True)
            (wf / "ci.yml").write_text(
                "jobs:\n  a:\n    steps:\n"
                "      - run: cargo fmt --all --check\n"
                "      - run: cargo +nightly clippy --all-targets -- -D warnings\n"
                "      - run: cargo hack check --feature-powerset\n"
                "      - run: cargo nextest run --workspace\n"
                "      - run: ${{ env.CARGO }} test --verbose\n"
                "      - uses: EmbarkStudios/cargo-deny-action@v2\n",
                encoding="utf-8",
            )
            fake_bin = write_fake_cargo(root, FAKE_CARGO_WITHOUT_DENY_AND_VET)
            result, _ = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CI contract (from .github/workflows): clippy(+nightly) deny(action) fmt hack nextest test", result.stdout)
            self.assertIn("this run covered:  clippy fmt nextest test", result.stdout)
            self.assertIn("NOT covered:       deny(", result.stdout)
            self.assertIn("hack(feature matrix", result.stdout)
            self.assertIn("ci=4/6", result.stdout)
            # clippy in CI counts as a Clippy policy → deny warnings
            self.assertIn("policy: clippy in CI workflows", result.stdout)

    def test_driver_delegation_runs_non_mutating_recipes_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "justfile").write_text(
                "fmt:\n\tcargo fmt\n\ntest *args:\n\tcargo test\n\nfmt-check:\n\tcargo fmt --check\n\n"
                "clippy:\n\tcargo clippy\n\ntest-tui:\n\tcargo test -p tui\n",
                encoding="utf-8",
            )
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin, RUST_GATES_USE_DRIVER="1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(log_lines(log), ["just fmt-check", "just clippy", "just test"], "fmt/test-tui must not run unasked")
            self.assertIn("driver=just(fmt-check=ok,clippy=ok,test=ok)", result.stdout)

            log.unlink()
            picked, picked_log = run_gates(root, fake_bin, RUST_GATES_USE_DRIVER="1", RUST_GATES_DRIVER_RECIPES="test-tui,fmt-check")
            self.assertEqual(picked.returncode, 0, picked.stderr)
            self.assertEqual(log_lines(picked_log), ["just fmt-check", "just test-tui"])

            log.unlink()
            failed, failed_log = run_gates(root, fake_bin, RUST_GATES_USE_DRIVER="1", JUST_FAKE_FAIL="clippy")
            self.assertEqual(failed.returncode, 7)
            self.assertEqual(log_lines(failed_log), ["just fmt-check", "just clippy"], "fail fast")
            self.assertIn("driver=just(fmt-check=ok,clippy=FAIL(7))", failed.stdout)

    def test_select_installed_toolchain_that_satisfies_msrv(self) -> None:
        metadata = '{"packages":[{"name":"b","rust_version":"1.96"}]}'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            common = dict(CARGO_FAKE_METADATA=metadata, RUSTC_FAKE_VERSION="1.95.0", RUSTUP_FAKE_TOOLCHAINS="1.95.0-fake 1.98.0-fake stable-fake")
            suggest, _ = run_gates(root, fake_bin, **common)
            self.assertEqual(suggest.returncode, 6)
            self.assertIn("RUSTUP_TOOLCHAIN=1.98.0-fake", suggest.stderr)

            (root / "cargo.log").unlink()
            chosen, _ = run_gates(root, fake_bin, RUST_GATES_SELECT_TOOLCHAIN="1", **common)
            self.assertEqual(chosen.returncode, 0, chosen.stderr)
            self.assertIn("selecting installed 1.98.0-fake", chosen.stdout)
            self.assertIn("declared rust-version 1.96 satisfied by rustc 1.98.0", chosen.stdout)

            pinned, _ = run_gates(
                root, fake_bin, RUST_GATES_SELECT_TOOLCHAIN="1",
                RUSTUP_FAKE_ACTIVE="1.95.0-fake (overridden by '/repo/rust-toolchain.toml')", **common,
            )
            self.assertEqual(pinned.returncode, 6, "a file pin is the repo's choice; never override it")

    @unittest.skipUnless(shutil.which("cargo") and shutil.which("rustfmt"), "needs a real cargo + rustfmt")
    def test_real_rustfmt_honors_promoted_options(self) -> None:
        # The one behavior fakes cannot model: stable rustfmt drops file-level
        # nightly options but honors them via --config, and keeps warning
        # about the file entries either way.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text('[package]\nname = "smoke"\nversion = "0.1.0"\nedition = "2021"\n', encoding="utf-8")
            (root / "rustfmt.toml").write_text('imports_granularity = "Item"\n', encoding="utf-8")
            (root / "src").mkdir()
            src = root / "src" / "lib.rs"
            src.write_text("use std::{collections::HashMap, fmt::Debug};\n\npub fn f(_m: HashMap<String, String>, _d: &dyn Debug) {}\n", encoding="utf-8")
            knobs = dict(SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1", SKIP_RUST_TEST="1")
            result, _ = run_gates(root, None, **knobs)
            self.assertEqual(result.returncode, 1, "grouped import must be reported as a diff under Item granularity")
            self.assertIn("--config imports_granularity=Item --check", result.stdout)
            self.assertIn("fmt=FAIL(1,promoted=1)", result.stdout)

            src.write_text("use std::collections::HashMap;\nuse std::fmt::Debug;\n\npub fn f(_m: HashMap<String, String>, _d: &dyn Debug) {}\n", encoding="utf-8")
            ok, _ = run_gates(root, None, **knobs)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertIn("fmt=ok(promoted=1)", ok.stdout)

    # --- nextest -----------------------------------------------------------

    def test_nextest_config_selects_nextest_and_keeps_doctests(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            (root / ".config").mkdir()
            (root / ".config" / "nextest.toml").write_text("[profile.default]\nretries = 1\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_WITH_NEXTEST)
            result, log = run_gates(root, fake_bin, SKIP_RUST_FMT="1", SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                log_lines(log),
                [
                    "--version",
                    "nextest --version",
                    "nextest run --workspace",
                    "test --workspace --doc",
                ],
            )

    def test_nextest_config_without_tool_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[workspace]\n", encoding="utf-8")
            (root / ".config").mkdir()
            (root / ".config" / "nextest.toml").write_text("[profile.default]\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_WITHOUT_NEXTEST)
            result, log = run_gates(root, fake_bin, SKIP_RUST_FMT="1", SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1")
            self.assertEqual(result.returncode, 5)
            self.assertIn("cargo-nextest is not installed", result.stderr)
            self.assertNotIn("test --workspace", log.read_text(encoding="utf-8"))

            log.unlink()  # each run appends; isolate the forced run's calls
            forced, forced_log = run_gates(
                root, fake_bin, SKIP_RUST_FMT="1", SKIP_RUST_CLIPPY="1", SKIP_RUST_CHECK="1", RUST_TEST_RUNNER="cargo"
            )
            self.assertEqual(forced.returncode, 0, forced.stderr)
            self.assertEqual(log_lines(forced_log), ["--version", "test --workspace"])


if __name__ == "__main__":
    unittest.main()
