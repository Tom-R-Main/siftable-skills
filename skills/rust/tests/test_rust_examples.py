#!/usr/bin/env python3
"""Compile and run the skill's stable examples, with a borrow-conflict control.

Uses the active installed rustc only; never invokes Cargo or installs a toolchain.
Run under each intended RUSTUP_TOOLCHAIN explicitly to check a version matrix.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = re.findall(
    r"```rust\n(.*?)\n```",
    (ROOT / "references/rust-places-projections.md").read_text(),
    re.DOTALL,
)


@unittest.skipUnless(shutil.which("rustc"), "installed rustc required; no auto-install")
class RustExamples(unittest.TestCase):
    def compile_example(self, source: str, edition: str, *, run: bool = True):
        # Keep generated binaries outside the installable skill package, within
        # the active project rather than a read-only reference checkout.
        with tempfile.TemporaryDirectory(prefix=".rust-example-", dir=ROOT.parents[1]) as tmp:
            path = Path(tmp)
            (path / "example.rs").write_text(source)
            env = dict(os.environ, RUSTUP_AUTO_INSTALL="0")
            result = subprocess.run(
                ["rustc", f"--edition={edition}", "--error-format=json", "-Dwarnings",
                 str(path / "example.rs"), "-o", str(path / "example")],
                capture_output=True, text=True, env=env, timeout=30,
            )
            if run:
                self.assertEqual(result.returncode, 0, result.stderr)
                executed = subprocess.run(
                    [str(path / "example")], capture_output=True, text=True,
                    env=env, timeout=10,
                )
                self.assertEqual(executed.returncode, 0, executed.stderr)
            return result

    def test_documented_stable_examples(self):
        self.assertEqual(len(EXAMPLES), 2, "include every stable example in the matrix")
        for edition in ("2021", "2024"):
            for i, source in enumerate(EXAMPLES):
                with self.subTest(edition=edition, example=i):
                    self.compile_example(source, edition)

    def assert_borrow_conflict(self, control: str):
        for edition in ("2021", "2024"):
            with self.subTest(edition=edition):
                result = self.compile_example(control, edition, run=False)
                self.assertNotEqual(result.returncode, 0)
                diagnostics = [json.loads(line) for line in result.stderr.splitlines()]
                self.assertTrue(any(
                    (item.get("code") or {}).get("code") in {"E0500", "E0502"}
                    for item in diagnostics
                ), result.stderr)

    def test_reference_to_guard_does_not_split_fields(self):
        original = EXAMPLES[0]
        control = original.replace("let state = &mut *guard;", "let state = &mut guard;")
        self.assertNotEqual(original, control)
        self.assert_borrow_conflict(control)

    def test_mutable_guard_alone_does_not_split_fields(self):
        original = EXAMPLES[0]
        control = original.replace("    let state = &mut *guard;\n", "")
        control = control.replace("state.cache", "guard.cache")
        control = control.replace("state.templates", "guard.templates")
        self.assertNotEqual(original, control)
        self.assert_borrow_conflict(control)

    def test_destructured_fields_work_in_earlier_editions(self):
        source = EXAMPLES[0].replace(
            "let state = &mut *guard;",
            "let State { templates, cache } = &mut *guard;",
        ).replace("state.cache", "cache").replace("state.templates", "templates")
        for edition in ("2015", "2018", "2021", "2024"):
            with self.subTest(edition=edition):
                self.compile_example(source, edition)

    def test_reference_cannot_escape_local_guard(self):
        result = self.compile_example(
            "use std::sync::Mutex;\n"
            "fn view(m: &Mutex<String>) -> &str { let guard = m.lock().unwrap(); "
            "guard.as_str() }\n"
            "fn main() { let m = Mutex::new(String::new()); let _ = view(&m); }",
            "2021", run=False,
        )
        self.assertNotEqual(result.returncode, 0)
        diagnostics = [json.loads(line) for line in result.stderr.splitlines()]
        self.assertTrue(any(
            (item.get("code") or {}).get("code") == "E0515" for item in diagnostics
        ), result.stderr)

    def test_zero_initialized_bool_is_valid_false(self):
        self.compile_example(
            "fn main() { let value: bool = unsafe { std::mem::zeroed() }; "
            "assert!(!value); }", "2021",
        )


if __name__ == "__main__":
    unittest.main()
