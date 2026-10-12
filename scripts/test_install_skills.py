#!/usr/bin/env python3
"""Exercise installation authority, dependency closure and failure recovery offline."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import install_skills as installer


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        self.dest = self.root / 'installed'

    def skill(self, name, body=''):
        path = self.source / name
        path.mkdir(exist_ok=True)
        (path / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Use this portable test skill to validate the installation workflow.\n---\n{body}\n')
        return path

    def apply(self, names=None, **kwargs):
        return installer.install(self.source, self.dest, names, apply=True, **kwargs)

    def test_dry_run_does_not_create_destination(self):
        self.skill('alpha')
        self.assertEqual(installer.install(self.source, self.dest), [('alpha', 'install')])
        self.assertFalse(self.dest.exists())

    def test_transitive_cycle_and_resource_closure(self):
        self.skill('alpha', '[beta](../beta/SKILL.md)')
        self.skill('beta', 'Read `../gamma/SKILL.md`.')
        self.skill('gamma', '[alpha](../alpha/SKILL.md)')
        self.skill('independent')
        self.apply(['alpha'])
        self.assertEqual(sorted(p.name for p in self.dest.iterdir() if p.is_dir()), ['alpha', 'beta', 'gamma'])

    def test_missing_resource_rejected_before_mutation(self):
        self.skill('alpha', '[missing](../beta/SKILL.md)')
        with self.assertRaisesRegex(ValueError, 'unresolved resource'):
            self.apply()
        self.assertFalse(self.dest.exists())

    def test_unmanaged_even_identical_is_not_adopted(self):
        path = self.skill('alpha')
        self.dest.mkdir()
        installer.copy_skill(path, self.dest / 'alpha')
        with self.assertRaisesRegex(ValueError, 'Unmanaged'):
            self.apply(update=True)
        self.assertFalse((self.dest / installer.MANIFEST).exists())

    def test_idempotence_managed_update_and_local_edit_guard(self):
        source = self.skill('alpha')
        self.apply()
        manifest = (self.dest / installer.MANIFEST).read_bytes()
        self.assertEqual(self.apply(), [('alpha', 'unchanged')])
        self.assertEqual(manifest, (self.dest / installer.MANIFEST).read_bytes())
        (source / 'SKILL.md').write_text((source / 'SKILL.md').read_text() + '\nUpdated guidance\n')
        with self.assertRaisesRegex(ValueError, '--update'):
            self.apply()
        self.apply(update=True)
        self.assertEqual(installer.tree_digest(source), installer.tree_digest(self.dest / 'alpha'))
        (self.dest / 'alpha' / 'local.md').write_text('Local modification')
        with self.assertRaisesRegex(ValueError, 'Locally changed'):
            self.apply(update=True)
        self.assertTrue((self.dest / 'alpha' / 'local.md').exists())

    def test_symlink_source_and_destination_are_refused(self):
        source = self.skill('alpha')
        (source / 'link').symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            self.apply()
        (source / 'link').unlink()
        real_dest = self.root / 'real'
        real_dest.mkdir()
        self.dest.symlink_to(real_dest, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.apply()
        self.assertEqual(list(real_dest.iterdir()), [])

    def test_apply_failure_rolls_back_every_replaced_package(self):
        for name in ['alpha', 'beta']:
            self.skill(name)
        self.apply()
        old_manifest = (self.dest / installer.MANIFEST).read_bytes()
        old = {name: installer.tree_digest(self.dest / name) for name in ['alpha', 'beta']}
        for name in old:
            (self.source / name / 'new.md').write_text('New version')
        original = os.replace
        failed = False
        def fail_second_stage(source, target):
            nonlocal failed
            if not failed and Path(source).parent.name == 'stage' and Path(source).name == 'beta':
                failed = True
                raise OSError('simulated filesystem failure')
            return original(source, target)
        with patch.object(installer.os, 'replace', side_effect=fail_second_stage):
            with self.assertRaisesRegex(OSError, 'simulated'):
                self.apply(update=True)
        self.assertTrue(failed)
        self.assertEqual(old_manifest, (self.dest / installer.MANIFEST).read_bytes())
        for name, digest in old.items():
            self.assertEqual(installer.tree_digest(self.dest / name), digest)
        self.assertFalse((self.dest / installer.TRANSACTION).exists())

    def interrupted_update(self):
        source = self.skill('alpha')
        self.apply()
        old_manifest = installer.load_manifest(self.dest)
        old = installer.tree_digest(self.dest / 'alpha')
        (source / 'new.md').write_text('New version')
        new = installer.tree_digest(source)
        tx = self.dest / installer.TRANSACTION
        (tx / 'backup').mkdir(parents=True)
        (tx / 'stage').mkdir()
        installer.copy_skill(source, tx / 'stage' / 'alpha')
        journal = {'version': 1, 'state': 'staged', 'old_manifest': old_manifest,
                   'new_manifest': {**old_manifest, 'skills': {'alpha': new}},
                   'entries': [{'name': 'alpha', 'old': old, 'new': new}]}
        installer.write_json(tx / 'journal.json', journal)
        os.replace(self.dest / 'alpha', tx / 'backup' / 'alpha')
        os.replace(tx / 'stage' / 'alpha', self.dest / 'alpha')
        return old

    def test_interrupted_transaction_blocks_new_work_then_recovers(self):
        old = self.interrupted_update()
        with self.assertRaisesRegex(ValueError, 'Interrupted'):
            self.apply(update=True)
        installer.recover(self.dest)
        self.assertEqual(installer.tree_digest(self.dest / 'alpha'), old)
        self.assertFalse((self.dest / installer.TRANSACTION).exists())

    def test_recovery_refuses_post_interruption_changes(self):
        self.interrupted_update()
        (self.dest / 'alpha' / 'local.md').write_text('Preserve me')
        with self.assertRaisesRegex(ValueError, 'Changed skill'):
            installer.recover(self.dest)
        self.assertTrue((self.dest / 'alpha' / 'local.md').exists())
        self.assertTrue((self.dest / installer.TRANSACTION / 'backup' / 'alpha').exists())

    def test_recovery_refuses_missing_previous_backup(self):
        self.interrupted_update()
        shutil.rmtree(self.dest / installer.TRANSACTION / 'backup' / 'alpha')
        new = installer.tree_digest(self.dest / 'alpha')
        with self.assertRaisesRegex(ValueError, 'Missing previous package'):
            installer.recover(self.dest)
        self.assertEqual(installer.tree_digest(self.dest / 'alpha'), new)
        self.assertTrue((self.dest / installer.TRANSACTION).exists())

    def test_recovery_preserves_independent_manifest_edits(self):
        self.interrupted_update()
        manifest = installer.load_manifest(self.dest)
        manifest['skills']['independent'] = 'a' * 64
        installer.write_json(self.dest / installer.MANIFEST, manifest)
        with self.assertRaisesRegex(ValueError, 'Changed installation manifest'):
            installer.recover(self.dest)
        self.assertEqual(installer.load_manifest(self.dest), manifest)
        self.assertTrue((self.dest / installer.TRANSACTION).exists())

    def test_cache_files_are_not_installed_or_counted_as_edits(self):
        source = self.skill('alpha')
        (source / '__pycache__').mkdir()
        (source / '__pycache__' / 'ignored.pyc').write_bytes(b'cache')
        self.apply()
        self.assertFalse((self.dest / 'alpha' / '__pycache__').exists())
        (self.dest / 'alpha' / '__pycache__').mkdir()
        (self.dest / 'alpha' / '__pycache__' / 'ignored.pyc').write_bytes(b'cache')
        self.assertEqual(self.apply(), [('alpha', 'unchanged')])

    def test_executable_mode_change_counts_as_local_edit(self):
        self.skill('alpha')
        self.apply()
        path = self.dest / 'alpha' / 'SKILL.md'
        path.chmod(path.stat().st_mode | 0o100)
        with self.assertRaisesRegex(ValueError, 'Locally changed'):
            self.apply(update=True)


if __name__ == '__main__':
    unittest.main()
