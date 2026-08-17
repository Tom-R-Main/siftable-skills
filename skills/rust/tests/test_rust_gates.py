#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "rust-gates.sh"

FAKE_CARGO = (
    "#!/bin/sh\n"
    'printf \'%s\\n\' "$*" >> "$CARGO_FAKE_LOG"\n'
    'if [ "${1:-}" = --version ]; then printf \'cargo 1.0.0 (fake)\\n\'; fi\n'
)

FAKE_CARGO_NIGHTLY_FMT = (
    "#!/bin/sh\n"
    'printf \'%s\\n\' "$*" >> "$CARGO_FAKE_LOG"\n'
    'if [ "${1:-}" = --version ]; then printf \'cargo 1.0.0 (fake)\\n\'; fi\n'
    'if [ "${1:-}" = fmt ]; then\n'
    "  printf 'Warning: unstable features are only available in nightly channel.\\n' >&2\n"
    "fi\n"
)


def write_fake_cargo(root: Path, body: str) -> Path:
    fake_bin = root / "bin"
    fake_bin.mkdir(exist_ok=True)
    fake_cargo = fake_bin / "cargo"
    fake_cargo.write_text(body, encoding="utf-8")
    fake_cargo.chmod(0o755)
    return fake_bin


def run_gates(root: Path, fake_bin: Path | None = None, **knobs: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    env = os.environ.copy()
    log = root / "cargo.log"
    env["CARGO_FAKE_LOG"] = str(log)
    if fake_bin is not None:
        env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env.update(knobs)
    result = subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )
    return result, log


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

    def test_gate_order_skips_check_and_respects_lockfile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "Cargo.lock").write_text("version = 3\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                log.read_text(encoding="utf-8").splitlines(),
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
                log.read_text(encoding="utf-8").splitlines(),
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

    def test_nightly_only_rustfmt_options_fail_instead_of_reporting_diffs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Cargo.toml").write_text("[package]\nname = \"demo\"\n", encoding="utf-8")
            (root / "rustfmt.toml").write_text("imports_granularity = \"Crate\"\n", encoding="utf-8")
            fake_bin = write_fake_cargo(root, FAKE_CARGO_NIGHTLY_FMT)
            result, log = run_gates(root, fake_bin)
            self.assertEqual(result.returncode, 4)
            self.assertIn("WRONG configuration", result.stderr)
            self.assertEqual(
                log.read_text(encoding="utf-8").splitlines(),
                ["--version", "fmt --all -- --check"],
            )

            allowed, allowed_log = run_gates(
                root,
                fake_bin,
                RUST_FMT_ALLOW_UNSTABLE_WARNINGS="1",
            )
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            self.assertIn("clippy --workspace --all-targets -- -D warnings", allowed_log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
