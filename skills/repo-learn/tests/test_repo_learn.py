#!/usr/bin/env python3
"""Exercise the installed evidence-library CLI against disposable source files."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / 'scripts' / 'repo_learn.py'


class EvidenceLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.store = self.root / 'library'
        (self.source / 'worker.py').write_text('def run():\n    commit_effect()\n    save_checkpoint()\n')

    def command(self, *args, success=True, store=None):
        result = subprocess.run([sys.executable, str(CLI), '--store', str(store or self.store), *map(str, args)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return json.loads(result.stdout if success else result.stderr)

    def read(self):
        return self.command('read', self.source, 'worker.py', '--start', '1', '--end', '3',
                            '--question', 'When is progress persisted?')['evidence']

    def test_capture_retrieve_freshness_and_replay(self):
        evidence = self.read()
        self.assertEqual(self.read()['id'], evidence['id'])
        card = dict(id='effect-checkpoint-v1', title='Commit effect before checkpoint',
                    problem='An interrupted worker can lose unfinished work.',
                    mechanism='Persist progress only after the corresponding effect.',
                    when_to_use='Resumable work', when_not_to_use='Advisory progress only',
                    tradeoffs='A shared transaction may be needed.',
                    counterexample='The checkpoint commits while the effect fails.',
                    transfer=dict(target='Fixture worker', application='Candidate for review',
                                  compatibility_checks='Inspect transaction ownership.'),
                    validation=dict(level='source', result='Source inspected; runtime untested.'),
                    evidence_ids=[evidence['id']], tags=['retry', 'recovery'])
        payload = self.root / 'card.json'
        payload.write_text(json.dumps(card))
        first = self.command('add-pattern', payload)
        replay = self.command('add-pattern', payload)
        self.assertFalse(first['repeated'])
        self.assertTrue(replay['repeated'])
        found = self.command('query', 'recovery checkpoint')['results']
        self.assertEqual([item['pattern']['id'] for item in found], [card['id']])
        self.assertEqual(found[0]['evidence_freshness'][0]['status'], 'fresh')
        (self.source / 'worker.py').write_text('def run():\n    save_checkpoint()\n    commit_effect()\n')
        self.assertEqual(self.command('verify')['evidence'][0]['status'], 'stale')
        exported = self.command('export')
        self.assertIn('stale', Path(exported['path']).read_text())
        card['mechanism'] = 'Contradictory replacement'
        payload.write_text(json.dumps(card))
        self.command('add-pattern', payload, success=False)
        self.assertEqual(self.command('status')['counts']['patterns'], 1)

    def test_sensitive_paths_symlinks_and_inside_source_store_are_rejected(self):
        (self.source / '.env').write_text('PLACEHOLDER=not-a-credential\n')
        (self.source / 'linked.py').symlink_to(self.source / 'worker.py')
        for path in ['.env', 'linked.py']:
            self.command('read', self.source, path, '--start', '1', '--end', '1',
                         '--question', 'Excluded input', success=False)
        nested = self.source / 'new-library'
        self.command('catalog', self.source, store=nested, success=False)
        self.assertFalse(nested.exists())

    def test_search_continuation_rejects_changed_source_membership(self):
        (self.source / 'second.py').write_text('def run():\n    return 1\n')
        page = self.command('find', self.source, 'def', '--max-files', '1')
        self.assertTrue(page['partial'])
        token = page['next']['cursor']
        self.command('find', self.source, 'def', '--max-files', '1', '--cursor', token)
        (self.source / 'third.py').write_text('def run():\n    return 2\n')
        self.command('find', self.source, 'def', '--max-files', '1', '--cursor', token, success=False)


if __name__ == '__main__':
    unittest.main()
