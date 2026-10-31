import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import fs_observe as observe


def response(data, stderr=False):
    return {'status': 'complete', 'returncode': 0, 'stdout': json.dumps(data).encode(), 'stderr_present': stderr}


VERSION = {'status': 'complete', 'returncode': 0, 'stdout': b'Mole 1.62.0\nmacOS: 15.0', 'stderr_present': False}


class ObserveTests(unittest.TestCase):
    def test_missing_tool_cleanly_unavailable(self):
        with patch('fs_observe.shutil.which', return_value=None):
            self.assertEqual(observe.observe('status', None)['status'], 'unavailable')

    def test_disallows_mutation_operations_before_tool_lookup(self):
        for operation in ('clean', 'purge', 'optimize', 'installer', 'uninstall', 'update'):
            with self.assertRaises(ValueError):
                observe.observe(operation, None)

    def test_analyze_refuses_root_before_tool_lookup(self):
        with patch('fs_observe.shutil.which') as lookup:
            with self.assertRaises(ValueError):
                observe.observe('analyze', '/')
            lookup.assert_not_called()

    def test_analyze_refuses_protected_and_cloud_roots(self):
        with tempfile.TemporaryDirectory() as temp, patch('fs_observe.shutil.which') as lookup:
            for name in ('.ssh', '.aws', '.env-secret', 'CloudStorage', 'Mobile Documents', 'vault'):
                root = Path(temp).resolve() / name
                root.mkdir()
                with self.assertRaises(ValueError):
                    observe.observe('analyze', str(root))
            lookup.assert_not_called()

    def test_analyze_refuses_ancestor_symlink(self):
        with tempfile.TemporaryDirectory() as temp, patch('fs_observe.shutil.which') as lookup:
            base = Path(temp).resolve()
            (base / 'real' / 'child').mkdir(parents=True)
            (base / 'alias').symlink_to(base / 'real', target_is_directory=True)
            with self.assertRaises(ValueError):
                observe.observe('analyze', str(base / 'alias' / 'child'))
            lookup.assert_not_called()

    def test_analyze_requires_explicit_scope(self):
        with self.assertRaises(ValueError):
            observe.observe('analyze', None)

    def test_partial_sizes_and_unknown_classification_preserved(self):
        data = {'scan_status': 'partial', 'total_size': 100, 'entries': [{'name': 'cache', 'path': '/cache', 'scan_status': 'unavailable', 'size': 0, 'cleanable': True}]}
        with tempfile.TemporaryDirectory() as root, patch('fs_observe.shutil.which', return_value='/fixture/mo'), patch('fs_observe.bounded_run', side_effect=[VERSION, response(data)]) as run:
            result = observe.observe('analyze', str(Path(root).resolve()))
        self.assertEqual(result['status'], 'partial')
        self.assertIsNone(result['data']['entries'][0]['size'])
        self.assertEqual(result['data']['entries'][0]['classification'], 'unknown')
        argv = run.call_args_list[1].args[0]
        self.assertEqual(argv[:3], ['/fixture/mo', 'analyze', '--json'])
        self.assertNotIn('--dry-run', argv)

    def test_diagnostics_do_not_expose_stderr(self):
        data = {'memory': {'pressure': 'normal', 'secret': 'omit'}, 'disks': []}
        with patch('fs_observe.shutil.which', return_value='/fixture/mo'), patch('fs_observe.bounded_run', side_effect=[VERSION, response(data, True)]):
            result = observe.observe('status', None)
        self.assertEqual(result['status'], 'partial')
        self.assertNotIn('secret', json.dumps(result))

    def test_version_is_reduced_to_edition_and_number(self):
        version = dict(VERSION, stdout=b'Mole 1.62.0\nmacOS: 15.0\nsecret fixture token')
        data = {'memory': {'pressure': 'normal'}, 'disks': []}
        with patch('fs_observe.shutil.which', return_value='/fixture/mo'), patch('fs_observe.bounded_run', side_effect=[version, response(data)]):
            result = observe.observe('status', None)
        self.assertEqual(result['version'], '1.62.0')
        self.assertNotIn('secret', json.dumps(result))

    def test_windows_edition_not_reused_as_macos(self):
        version = dict(VERSION, stdout=b'Mole 1.62.0\nWindows: 11')
        with patch('fs_observe.shutil.which', return_value='/fixture/mo'), patch('fs_observe.bounded_run', return_value=version) as run:
            result = observe.observe('status', None)
        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(run.call_count, 1)

    def test_malformed_schema_unavailable(self):
        with patch('fs_observe.shutil.which', return_value='/fixture/mo'), patch('fs_observe.bounded_run', side_effect=[VERSION, response({'other': 1})]):
            self.assertEqual(observe.observe('status', None)['status'], 'unavailable')

    def test_actual_subprocess_budget(self):
        result = observe.bounded_run([sys.executable, '-B', '-c', 'print("x" * 10000)'], 5, 100)
        self.assertEqual(result['status'], 'output_limit')
        self.assertLessEqual(len(result['stdout']), 100)

    def test_actual_subprocess_timeout(self):
        result = observe.bounded_run([sys.executable, '-B', '-c', 'import time; time.sleep(2)'], .05)
        self.assertEqual(result['status'], 'timeout')

    def test_cli_rejects_clean(self):
        run = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'fs_observe.py'), 'observe', '--adapter', 'mole', '--operation', 'clean'], capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('invalid choice', run.stderr)


if __name__ == '__main__':
    unittest.main()
