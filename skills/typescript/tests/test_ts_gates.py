from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


class TypeScriptGatesTests(unittest.TestCase):
    def run_script(self, root, name, *args, **knobs):
        env = dict(os.environ, **knobs)
        env['npm_config_update_notifier'] = 'false'
        env['npm_config_audit'] = 'false'
        return subprocess.run(['/bin/bash', str(SCRIPTS / name), *args], cwd=root,
                              env=env, capture_output=True, text=True, timeout=30)

    def package(self, root, **fields):
        (root / 'package.json').write_text(json.dumps({'name': 'gate-fixture', **fields}))

    def require_node(self):
        if not shutil.which('node') or not shutil.which('npm'):
            self.skipTest('requires already installed node and npm')

    def test_help_without_toolchains(self):
        for name in ('ts-gates.sh', 'drive.sh'):
            result = self.run_script(Path.cwd(), name, '--help', PATH='')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Usage:', result.stdout)

    def test_gate_failures_stop_driver_before_later_steps(self):
        self.require_node()
        for gate in ('typecheck', 'lint', 'test', 'build'):
            with self.subTest(gate=gate), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                scripts = {g: 'node -e "process.exit(0)"' for g in ('typecheck','lint','test','build')}
                scripts[gate] = 'node -e "console.log(\'EXPECTED-FAIL\'); process.exit(19)"'
                self.package(root, scripts=scripts, bin='cli.js')
                (root/'cli.js').write_text('console.log("UNEXPECTED-LAUNCH");')
                result = self.run_script(root, 'drive.sh')
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('EXPECTED-FAIL', result.stdout)
                self.assertNotIn('UNEXPECTED-LAUNCH', result.stdout)
                self.assertNotIn('launched', result.stdout)

    def test_failed_cli_with_output_is_failure(self):
        self.require_node()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.package(root, bin='cli.js')
            (root/'cli.js').write_text('console.log("Expected error output"); process.exit(7);')
            result = self.run_script(root, 'drive.sh')
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('exit 7', result.stderr)
            self.assertNotIn('launched', result.stdout)

    def test_cli_success_and_explicit_help_probe(self):
        self.require_node()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.package(root, bin={'fixture':'cli.js'})
            (root/'cli.js').write_text('console.log("args=" + process.argv.slice(2).join(" "));')
            result=self.run_script(root,'drive.sh','--probe-argument','--help')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('args=--help',result.stdout)

    def test_large_cli_output_does_not_fail_from_broken_pipe(self):
        self.require_node()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.package(root,bin='cli.js')
            (root/'cli.js').write_text('console.log("usage"); console.log("long output".repeat(100000));')
            result=self.run_script(root,'drive.sh')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('launched',result.stdout)

    def test_missing_bin_fails(self):
        self.require_node()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.package(root,bin='missing.js')
            result=self.run_script(root,'drive.sh')
            self.assertNotEqual(result.returncode,0,result.stdout)
            self.assertIn('not built',result.stdout)

    def test_invalid_manifest_fails_instead_of_skipping_gates(self):
        self.require_node()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'package.json').write_text('{ malformed')
            result=self.run_script(root,'drive.sh')
            self.assertNotEqual(result.returncode,0,result.stdout)
            self.assertNotIn('no "bin" field',result.stdout)

    def test_workspace_compiler_found_without_using_global(self):
        self.require_node()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);subprocess.run(['git','init','-q'],cwd=root,check=True)
            package=root/'packages'/'sample';package.mkdir(parents=True)
            self.package(package);(package/'tsconfig.json').write_text('{}')
            compiler=root/'node_modules'/'.bin'/'tsc';compiler.parent.mkdir(parents=True)
            compiler.write_text('#!/bin/sh\nprintf "workspace-compiler %s\\n" "$*"\n');compiler.chmod(0o755)
            result=self.run_script(package,'ts-gates.sh')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('workspace-compiler --noEmit -p tsconfig.json',result.stdout)

    def test_compiler_absence_is_failure_even_if_global_available(self):
        self.require_node()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.package(root);(root/'tsconfig.json').write_text('{}')
            fake=root/'global-bin';fake.mkdir();compiler=fake/'tsc'
            compiler.write_text('#!/bin/sh\necho UNEXPECTED-GLOBAL\n');compiler.chmod(0o755)
            result=self.run_script(root,'ts-gates.sh',PATH=f'{fake}:{os.environ["PATH"]}')
            self.assertNotEqual(result.returncode,0,result.stdout)
            self.assertIn('no installed workspace',result.stderr)
            self.assertNotIn('UNEXPECTED-GLOBAL',result.stdout)

    def test_preview_compiler_runs_after_authoritative_gate(self):
        self.require_node()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.package(root,scripts={'typecheck':'node -e "console.log(\'AUTHORITATIVE\')"'})
            (root/'tsconfig.json').write_text('{}');compiler=root/'node_modules'/'.bin'/'tsgo'
            compiler.parent.mkdir(parents=True);compiler.write_text('#!/bin/sh\necho PREVIEW\n');compiler.chmod(0o755)
            result=self.run_script(root,'ts-gates.sh',TS_USE_TSGO='1')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertLess(result.stdout.index('AUTHORITATIVE'),result.stdout.index('PREVIEW'))


if __name__ == '__main__':
    unittest.main()
