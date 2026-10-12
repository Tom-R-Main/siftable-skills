from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts'/'glcheck.sh'


class GLCheckTests(unittest.TestCase):
    def test_help_does_not_require_compiler(self):
        result=subprocess.run(['/bin/bash',str(SCRIPT),'--help'],env={'PATH':''},capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('Usage:',result.stdout)

    def run_mock_compiler(self,root,fail=False):
        compiler=root/'cc';compiler.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$GL_FAKE_LOG"\nexit '+('1' if fail else '0')+'\n');compiler.chmod(0o755)
        env=dict(os.environ,CC=str(compiler),GLFLAGS='-Ialready-installed-headers',GL_FAKE_LOG=str(root/'cc.log'))
        return subprocess.run(['/bin/bash',str(SCRIPT),'fixture.c'],env=env,cwd=root,capture_output=True,text=True)

    def test_warning_and_sanitizer_flags_and_compile_only_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);result=self.run_mock_compiler(root)
            self.assertEqual(result.returncode,0,result.stderr)
            calls=(root/'cc.log').read_text().splitlines()
            self.assertEqual(len(calls),2)
            self.assertTrue(all('-Werror' in call for call in calls))
            self.assertIn('-fsanitize=address,undefined',calls[1])
            self.assertIn('temporary binary will be removed',result.stdout)
            self.assertNotIn('ASAN_OPTIONS=detect_leaks=1',result.stdout)

    def test_compiler_failure_propagates(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=self.run_mock_compiler(Path(tmp),True)
            self.assertNotEqual(result.returncode,0,result.stdout)
            self.assertIn('PROBLEMS FOUND',result.stdout)


if __name__ == '__main__':
    unittest.main()
