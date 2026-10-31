import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import fs_compare as compare


def manifest(at, candidates=None, partial=False):
    doc = {'schema': 'filesystem-lifecycle/v3', 'generated_at': at,
           'authorization': {'envelope': {'filesystem': {'device': 1, 'filesystem_id': 1}}},
           'scope': {'roots': ['/projects']}, 'planning': {'mode': 'full'},
           'evidence': {'discovery': {'scan_complete': not partial}},
           'candidates': candidates if candidates is not None else [candidate()]}
    doc['integrity'] = {'algorithm': 'sha256', 'digest': compare.digest(doc)}
    return doc


def candidate(inode=1):
    return {'id': 'artifact:a', 'canonical_path': '/projects/app/node_modules', 'kind': 'generated_artifact',
            'owner': 'npm', 'identity': {'device': 1, 'mount_id': 'device:1:/', 'inode': inode},
            'storage': {'allocated_bytes': 123}, 'recovery': {'method': 'install from lockfile'}}


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.before = manifest('2025-01-01T00:00:00+00:00')
        self.after = manifest('2025-01-03T00:00:00+00:00', [candidate(2)])
        self.receipt = {'schema': 'filesystem-lifecycle/v3', 'applied_at': '2025-01-02T00:00:00+00:00',
                        'filesystem': {'device': 1, 'filesystem_id': 1},
                        'source_manifest_digest': self.before['integrity']['digest'],
                        'results': [{'id': 'artifact:a', 'path': '/projects/app/node_modules', 'status': 'removed',
                                     'identity': candidate()['identity'], 'interval_physical_free_delta_bytes': 100}]}

    def test_recreation_requires_successful_bound_receipt(self):
        result = compare.compare_records(self.before, self.after, [self.receipt])['resources'][0]
        self.assertEqual(result['state'], 'recreated')
        self.assertEqual(result['seconds_since_removal'], 86400)
        self.assertEqual(result['prior_interval_free_delta_bytes'], 100)
        self.assertEqual(result['rebuild_cost'], 'unknown')

    def test_completion_after_observation_excluded(self):
        self.receipt['results'][0]['completed_at'] = '2025-01-04T00:00:00+00:00'
        result = compare.compare_records(self.before, self.after, [self.receipt])
        self.assertNotEqual(result['resources'][0]['state'], 'recreated')
        self.assertTrue(result['coverage_gaps'])

    def test_changed_inode_without_receipt_not_proven_recreated(self):
        self.assertEqual(compare.compare_records(self.before, self.after, [])['resources'][0]['state'], 'replaced_or_recreated')

    def test_partial_receipt_cannot_prove_recreation(self):
        self.receipt['results'][0]['status'] = 'partially_removed'
        self.assertNotEqual(compare.compare_records(self.before, self.after, [self.receipt])['resources'][0]['state'], 'recreated')

    def test_receipt_identity_mismatch_not_accepted(self):
        self.receipt['results'][0]['identity']['inode'] = 999
        self.assertNotEqual(compare.compare_records(self.before, self.after, [self.receipt])['resources'][0]['state'], 'recreated')

    def test_filesystem_id_over_mount_path_presentation(self):
        old = self.before['candidates'][0]['identity']
        new = self.after['candidates'][0]['identity']
        old['filesystem_id'] = new['filesystem_id'] = 12
        new['mount_id'] = 'alternate-presentation'
        self.assertEqual(compare.compare_records(self.before, self.after, [self.receipt])['resources'][0]['state'], 'recreated')
        new['filesystem_id'] = 13
        self.assertEqual(compare.compare_records(self.before, self.after, [self.receipt])['resources'][0]['state'], 'identity_uncertain')

    def test_other_filesystem_is_not_recreated(self):
        self.after['candidates'][0]['identity']['device'] = 2
        self.assertEqual(compare.compare_records(self.before, self.after, [self.receipt])['resources'][0]['state'], 'identity_uncertain')

    def test_unbound_legacy_receipt_is_advisory(self):
        self.receipt['schema'] = 'filesystem-lifecycle/v2'
        self.receipt.pop('source_manifest_digest')
        result = compare.compare_records(self.before, self.after, [self.receipt])
        self.assertNotEqual(result['resources'][0]['state'], 'recreated')
        self.assertTrue(result['coverage_gaps'])

    def test_doctor_inventory_comparison(self):
        before = {'schema': 'filesystem-lifecycle/doctor-v1', 'generated_at': '2025-01-01T00:00:00+00:00', 'filesystem': {'device': 1, 'filesystem_id': 1}, 'status': 'complete', 'scope': {'roots': ['/projects']}, 'limits_per_root': {'max_depth': 3}, 'resources': [candidate()], 'scans': [{'status': 'complete'}], 'coverage_gaps': []}
        after = dict(before, generated_at='2025-01-03T00:00:00+00:00')
        self.assertEqual(compare.compare_records(before, after, [])['resources'][0]['state'], 'still_observed')
        after = dict(after, resources=[], status='partial', coverage_gaps=['time budget'])
        self.assertEqual(compare.compare_records(before, after, [])['resources'][0]['state'], 'not_assessed')
        after = dict(after, status='complete', coverage_gaps=[])
        self.assertEqual(compare.compare_records(before, after, [])['resources'][0]['state'], 'not_observed')

    def test_partial_absence_is_not_assessed(self):
        after = manifest('2025-01-03T00:00:00+00:00', [], partial=True)
        self.assertEqual(compare.compare_records(self.before, after, [])['resources'][0]['state'], 'not_assessed')

    def test_full_absence_does_not_claim_deleted(self):
        after = manifest('2025-01-03T00:00:00+00:00', [])
        self.assertEqual(compare.compare_records(self.before, after, [])['resources'][0]['state'], 'not_observed')

    def test_chronology_rejected(self):
        with self.assertRaises(ValueError):
            compare.compare_records(self.after, self.before, [])

    def test_actual_cli_reads_only_explicit_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before, after, receipt = [root / name for name in ('before.json', 'after.json', 'receipt.json')]
            for path, data in ((before, self.before), (after, self.after), (receipt, self.receipt)):
                path.write_text(json.dumps(data))
            snapshots = {p.name: p.read_bytes() for p in root.iterdir()}
            run = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'fs_compare.py'), 'compare', '--before', str(before), '--after', str(after), '--receipt', str(receipt), '--format', 'json'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['resources'][0]['state'], 'recreated')
            self.assertEqual({p.name: p.read_bytes() for p in root.iterdir()}, snapshots)

    def test_actual_doctor_inventory_can_be_compared(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            root = base / 'fixture'
            root.mkdir()
            (root / 'sample.txt').write_text('fixture')
            records = []
            for name in ('before.json', 'after.json'):
                run = subprocess.run([sys.executable, '-B', str(SCRIPTS / 'fs_diagnostics.py'), 'doctor', '--root', str(root), '--volume', str(root), '--format', 'json'], capture_output=True, text=True)
                self.assertIn(run.returncode, (0, 1), run.stderr)
                path = base / name
                path.write_text(run.stdout)
                records.append(compare.load_record(str(path)))
            result = compare.compare_records(*records, [])
            self.assertEqual(result['resources'][0]['state'], 'still_observed')

    def test_secret_input_rejected_before_open(self):
        with self.assertRaises(ValueError):
            compare.load_record('/fixture/.env.json')

    def test_output_does_not_overwrite_or_follow_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'out.json'
            compare.exclusive_write(str(path), 'original')
            with self.assertRaises(FileExistsError):
                compare.exclusive_write(str(path), 'replacement')
            link = Path(temp) / 'link.json'
            link.symlink_to(path)
            with self.assertRaises(FileExistsError):
                compare.exclusive_write(str(link), 'replacement')
            self.assertEqual(path.read_text(), 'original')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_receipt_filesystem_mismatch_not_accepted(self):
        self.receipt['filesystem']['filesystem_id'] = 2
        result = compare.compare_records(self.before, self.after, [self.receipt])
        self.assertNotEqual(result['resources'][0]['state'], 'recreated')

    def test_corrupt_checksum_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'record.json'
            self.before['candidates'][0]['storage']['allocated_bytes'] += 1
            path.write_text(json.dumps(self.before))
            with self.assertRaises(ValueError):
                compare.load_record(str(path))


if __name__ == '__main__':
    unittest.main()
