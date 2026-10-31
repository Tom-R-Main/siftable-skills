"""Public CLI journeys; fixture metadata only, no live cleanup."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / 'scripts' / 'fs_lifecycle.py'

class PublicCliTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(CLI), *map(str, args)], capture_output=True, text=True, timeout=30)

    def test_public_help_lists_passive_commands(self):
        result = self.cli('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ('doctor', 'report', 'compare', 'observe', 'audit', 'select', 'apply'):
            self.assertIn(name, result.stdout)

    def test_doctor_report_preserve_fixture_and_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = base / 'project'; project.mkdir()
            (project / 'sample').write_bytes(b'x' * 8192)
            report = base / 'doctor.json'
            result = self.cli('doctor', '--root', project, '--volume', project, '--output', report)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((project / 'sample').read_bytes(), b'x' * 8192)
            data = json.loads(report.read_text())
            self.assertIn('resources', data)
            self.assertEqual(os.stat(report).st_mode & 0o777, 0o600)
            rendered = self.cli('report', '--input', report, '--format', 'markdown')
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertIn('Allocated size', rendered.stdout)
            self.assertIn('sample', rendered.stdout)
            refused = self.cli('doctor', '--root', project, '--volume', project, '--output', report)
            self.assertNotEqual(refused.returncode, 0)
            self.assertEqual(json.loads(report.read_text()), data)

    def test_report_rejects_secret_symlink_and_fifo_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / 'record.json'; source.write_text('{"resources": []}')
            secret = base / '.env'; secret.write_text('{"resources": []}')
            link = base / 'link.json'; link.symlink_to(source)
            fifo = base / 'pipe.json'; os.mkfifo(fifo)
            for path in (secret, link, fifo):
                result = self.cli('report', '--input', path)
                self.assertNotEqual(result.returncode, 0, str(path))

    def test_mutating_mole_commands_are_unavailable(self):
        result = self.cli('observe', '--adapter', 'mole', '--operation', 'clean')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('invalid choice', result.stderr)

if __name__ == '__main__':
    unittest.main()
