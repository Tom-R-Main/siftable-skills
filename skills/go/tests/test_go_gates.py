from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


GATE = Path(__file__).resolve().parents[1] / "scripts" / "go-gates.sh"


class GoGatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        missing = [name for name in ("git", "go", "gofmt", "python3") if shutil.which(name) is None]
        if missing:
            raise unittest.SkipTest(f"missing required tools: {', '.join(missing)}")

    def run_gate(self, root: Path, *args: str, timeout: int = 45) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [str(GATE), *args],
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )

    def init_git(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)

    def write_module(self, root: Path, source: str | None = None) -> None:
        (root / "go.mod").write_text("module example.com/gates\n\ngo 1.20\n")
        (root / "gates.go").write_text(source or "package gates\n\nfunc Add(a, b int) int { return a + b }\n")
        (root / "gates_test.go").write_text(
            "package gates\n\n"
            'import "testing"\n\n'
            "func TestAdd(t *testing.T) {\n"
            "\tif got := Add(2, 3); got != 5 {\n"
            '\t\tt.Fatalf("Add(2, 3) = %d, want 5", got)\n'
            "\t}\n"
            "}\n"
        )

    def test_help_without_go_toolchain(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            # Supply only the running interpreter, independently of system
            # Python shims, toolchains, or package-manager install prefixes.
            (Path(temp) / "python3").symlink_to(sys.executable)
            result = subprocess.run(["/bin/sh", str(GATE), "--help"], env={"PATH": temp},
                                    capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)

    def test_non_go_directory_is_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_git(root)
            result = self.run_gate(root)

        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("no active go.mod or go.work", result.stdout)

    def test_repository_driver_requires_explicit_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_module(root)
            (root / "Makefile").write_text("test:\n\tgo test ./...\n")
            self.init_git(root)
            result = self.run_gate(root)

        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("build driver detected", result.stdout)
        self.assertIn("--force-direct", result.stdout)

    def test_minimal_module_passes_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_module(root)
            self.init_git(root)
            # The first standard-library build can have a cold compiler cache.
            result = self.run_gate(root, "--fresh", timeout=180)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("format=ok", result.stdout)
        self.assertIn("vet=1/1", result.stdout)
        self.assertIn("test=1/1", result.stdout)

    def test_unformatted_source_fails_format_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_module(root, "package gates\nfunc Add(a,b int)int{return a+b}\n")
            self.init_git(root)
            result = self.run_gate(root, "--skip-vet", "--skip-test", "--skip-lint")

        self.assertEqual(result.returncode, 5, result.stdout)
        self.assertIn("format=failed", result.stdout)
        self.assertIn("unformatted", result.stdout)

    def test_unavailable_required_toolchain_fails_before_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_module(root)
            (root / "go.mod").write_text("module example.com/gates\n\ngo 999.0\n")
            self.init_git(root)
            result = self.run_gate(
                root,
                "--skip-format",
                "--skip-vet",
                "--skip-test",
                "--skip-lint",
            )

        self.assertEqual(result.returncode, 6, result.stdout)
        self.assertIn("preflight failed", result.stdout)
        self.assertIn("GOTOOLCHAIN=local", result.stdout)

    def test_workspace_skips_modules_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as repo_temp, tempfile.TemporaryDirectory() as external_temp:
            root = Path(repo_temp)
            module = root / "inside"
            module.mkdir()
            self.write_module(module)

            external = Path(external_temp)
            (external / "go.mod").write_text("module example.com/external\n\ngo 1.20\n")
            (external / "external.go").write_text("package external\n")

            (root / "go.work").write_text(
                "go 1.20\n\n"
                "use (\n"
                "\t./inside\n"
                f"\t{external}\n"
                ")\n"
            )
            self.init_git(root)
            result = self.run_gate(
                root,
                "--json",
                "--skip-format",
                "--skip-vet",
                "--skip-test",
                "--skip-lint",
            )

        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["modules"]), 1)
        self.assertEqual(Path(payload["modules"][0]), module.resolve())
        self.assertEqual(
            [Path(item) for item in payload["external_workspace_modules"]],
            [external.resolve()],
        )


if __name__ == "__main__":
    unittest.main()
