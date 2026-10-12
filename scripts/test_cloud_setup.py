#!/usr/bin/env python3
"""Execute the documented setup and maintenance block against an offline Git fixture."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CloudSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.origin = self.root / 'origin'
        self.origin.mkdir()
        (self.origin / 'scripts').mkdir()
        for name in ('install_skills.py', 'validate_repo.py'):
            shutil.copy2(ROOT / 'scripts' / name, self.origin / 'scripts' / name)
        skill = self.origin / 'skills' / 'fixture'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('---\nname: fixture\ndescription: Use this portable skill to verify cloud installation and restoration.\n---\n')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        commit = self.git('rev-parse', 'HEAD').stdout.strip()
        docs = (ROOT / 'docs' / 'cloud-setup.md').read_text()
        self.block = re.search(r'```bash\n(.*?)\n```', docs, re.S).group(1)
        # Replace only the documented fixed origin with a local fixture: no fetch
        # or install touches the network, current HOME, or user skill directories.
        self.block = self.block.replace('https://github.com/Tom-R-Main/siftable-skills.git', str(self.origin))
        self.env = os.environ.copy()
        self.env.update(SIFTABLE_SKILLS_COMMIT=commit,
                        SIFTABLE_SKILLS_CACHE_ROOT=str(self.root / 'cache'),
                        SIFTABLE_SKILLS_DESTINATION=str(self.root / 'installed'),
                        PYTHONDONTWRITEBYTECODE='1',
                        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        self.checkout = self.root / 'cache' / commit
        self.destination = self.root / 'installed'

    def git(self, *args, cwd=None):
        return subprocess.run(['git', *args], cwd=cwd or self.origin, check=True,
                              capture_output=True, text=True)

    def execute(self, expected=0):
        result = subprocess.run(['bash', '-c', self.block], env=self.env,
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_cold_install_warm_maintenance_and_missing_cache_restore(self):
        self.execute()
        installed = self.destination / 'fixture' / 'SKILL.md'
        self.assertTrue(installed.exists())
        self.assertEqual(self.git('rev-parse', 'HEAD', cwd=self.checkout).stdout.strip(), self.env['SIFTABLE_SKILLS_COMMIT'])
        before = installed.read_bytes()
        self.assertIn('unchanged: fixture', self.execute().stdout)
        self.assertEqual(installed.read_bytes(), before)
        shutil.rmtree(self.root / 'cache')  # Only the fixture cache is retired.
        self.assertIn('unchanged: fixture', self.execute().stdout)
        self.assertEqual(installed.read_bytes(), before)

    def test_dirty_cached_checkout_refused(self):
        self.execute()
        (self.checkout / 'skills' / 'fixture' / 'SKILL.md').write_text('Local modification')
        self.execute(expected=1)
        self.assertIn('description:', (self.destination / 'fixture' / 'SKILL.md').read_text())

    def test_unexpected_remote_refused(self):
        self.execute()
        self.git('remote', 'set-url', 'origin', str(self.root / 'wrong-origin'), cwd=self.checkout)
        self.execute(expected=1)

    def test_mutable_ref_refused_before_checkout(self):
        self.env['SIFTABLE_SKILLS_COMMIT'] = 'main'
        self.execute(expected=1)
        self.assertFalse((self.root / 'cache').exists())

    def test_managed_local_changes_refused_on_maintenance(self):
        self.execute()
        installed = self.destination / 'fixture' / 'SKILL.md'
        installed.write_text(installed.read_text() + '\nPreserve local instructions\n')
        result = self.execute(expected=1)
        self.assertIn('Locally changed', result.stderr)
        self.assertIn('Preserve local instructions', installed.read_text())


if __name__ == '__main__':
    unittest.main()
