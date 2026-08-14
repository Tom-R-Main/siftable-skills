#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "zig-gates.sh"


class ZigGatesTests(unittest.TestCase):
    def test_help_does_not_require_zig(self) -> None:
        result = subprocess.run(["/bin/bash", str(SCRIPT), "--help"], capture_output=True, text=True, env={"PATH": ""})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage: zig-gates.sh", result.stdout)

    def test_missing_zig_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(["/bin/bash", str(SCRIPT)], capture_output=True, text=True, env={"PATH": temp})
            self.assertEqual(result.returncode, 127)
            self.assertIn("zig not found", result.stderr)

    def test_gate_order_and_selected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            log = root / "zig.log"
            fake_zig = fake_bin / "zig"
            fake_zig.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$*\" >> \"$ZIG_FAKE_LOG\"\n"
                "if [ \"${1:-}\" = version ]; then printf '0.16.0\\n'; fi\n"
                "if [ \"${1:-}\" = build ] && [ \"${2:-}\" = --help ]; then printf '  test  Run tests\\n'; fi\n",
                encoding="utf-8",
            )
            fake_zig.chmod(0o755)
            (root / "build.zig").write_text("pub fn build() void {}\n", encoding="utf-8")
            (root / "main.zig").write_text("pub fn main() void {}\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "build.zig", "main.zig"], cwd=root, check=True)
            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env['PATH']}"
            env["ZIG_FAKE_LOG"] = str(log)
            result = subprocess.run(["/bin/bash", str(SCRIPT)], cwd=root, capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                log.read_text(encoding="utf-8").splitlines(),
                ["version", "fmt --check build.zig main.zig", "build --help", "build test", "build"],
            )


if __name__ == "__main__":
    unittest.main()
