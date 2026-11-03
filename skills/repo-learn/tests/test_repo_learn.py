#!/usr/bin/env python3
"""Exercise the installed evidence-library CLI against disposable source files."""
import json
import sqlite3
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

    def card_payload(self):
        evidence = self.read()
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
        return payload, card

    def test_capture_retrieve_freshness_and_replay(self):
        evidence = self.read()
        self.assertEqual(self.read()['id'], evidence['id'])
        payload, card = self.card_payload()
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

    def stored_pattern(self, identity):
        # Read canonical storage directly, independently of CLI success claims.
        with sqlite3.connect(self.store / 'library.sqlite3') as db:
            bodies = db.execute('SELECT body FROM patterns WHERE id=?', (identity,)).fetchall()
            self.assertEqual(len(bodies), 1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM pattern_fts WHERE id=?',
                                        (identity,)).fetchone()[0], 1)
        return json.loads(bodies[0][0])

    def test_projection_failure_then_identical_retry_repairs_committed_record(self):
        payload, card = self.card_payload()
        projection = self.store / 'patterns' / (card['id'] + '.json')
        projection.mkdir(parents=True)
        result = subprocess.run([sys.executable, str(CLI), '--store', str(self.store),
                                 'add-pattern', str(payload)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        partial = json.loads(result.stderr)
        self.assertFalse(partial['ok'])
        self.assertTrue(partial['canonical_committed'])
        self.assertFalse(partial['projection_written'])
        self.assertEqual(partial['pattern_id'], card['id'])
        original = self.stored_pattern(card['id'])
        self.assertEqual(original['mechanism'], card['mechanism'])
        self.assertTrue(original['created_at'])
        projection.rmdir()  # Remove only this test's empty obstruction.
        repaired = self.command('add-pattern', payload)
        self.assertTrue(repaired['repeated'])
        self.assertTrue(repaired['canonical_committed'])
        self.assertTrue(repaired['projection_written'])
        self.assertEqual(self.stored_pattern(card['id']), original)
        self.assertTrue(projection.is_file(), 'Identical retry must repair the JSON projection')
        self.assertEqual(json.loads(projection.read_text()), original)

    def test_conflicting_retry_preserves_canonical_record_and_projection(self):
        payload, card = self.card_payload()
        self.command('add-pattern', payload)
        original = self.stored_pattern(card['id'])
        projection = self.store / 'patterns' / (card['id'] + '.json')
        original_projection = projection.read_bytes()
        card['mechanism'] = 'A conflicting replacement must never become canonical.'
        payload.write_text(json.dumps(card))
        rejected = self.command('add-pattern', payload, success=False)
        self.assertIn('different content', rejected['error'])
        self.assertEqual(self.stored_pattern(card['id']), original)
        self.assertEqual(projection.read_bytes(), original_projection)

    def test_concurrent_identical_submissions_converge(self):
        payload, card = self.card_payload()
        argv = [sys.executable, str(CLI), '--store', str(self.store),
                'add-pattern', str(payload)]
        children = [subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True) for _ in range(2)]
        results = []
        try:
            for child in children:
                stdout, stderr = child.communicate(timeout=30)
                self.assertEqual(child.returncode, 0, stdout + stderr)
                results.append(json.loads(stdout))
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.communicate()
        self.assertEqual(sorted(result['repeated'] for result in results), [False, True])
        original = self.stored_pattern(card['id'])
        self.assertEqual([result['pattern'] for result in results], [original, original])
        projection = self.store / 'patterns' / (card['id'] + '.json')
        self.assertEqual(json.loads(projection.read_text()), original)

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
