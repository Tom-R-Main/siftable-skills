"""Real executor on owned disposable-cache fixtures; liveness is simulated."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fs_lifecycle as fs


class CacheExecutorTests(unittest.TestCase):
    def test_homebrew_audit_apply_preserves_sibling_and_records_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            cache = root / 'downloads'; cache.mkdir()
            (cache / ('a' * 64 + '--fixture.tar.gz')).write_bytes(b'x' * 8192)
            sentinel = root / 'retained-source.txt'; sentinel.write_text('retain me')
            manifest = root / 'audit.json'
            rule = {'path': str(cache), 'owner': 'homebrew', 'processes': ('brew',), 'recovery': 'download again'}
            def invoke(*argv):
                args = fs.parser().parse_args(argv)
                return args.func(args)
            with patch.object(fs, 'KNOWN_CACHES', [rule]), patch.object(fs, 'process_snapshot', return_value=([], True, None)), patch.object(fs, 'open_codex_roots', return_value=[]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(invoke('audit', '--include-known-caches', '--kind', 'known_cache', '--volume', str(root), '--authorization-mode', 'goal_authorized', '--authorization-scope', 'owned fixture cache only', '--output', str(manifest)), 0)
                data = json.loads(manifest.read_text())
                self.assertEqual(len(data['candidates']), 1)
                item = data['candidates'][0]
                self.assertEqual(item['classification'], 'safe_now', item)
                self.assertEqual(invoke('apply', '--manifest', str(manifest), '--id', item['id'], '--authorization-source', 'goal_authorization', '--execute', '--ack', fs.ACK), 0)
            self.assertFalse(cache.exists())
            self.assertEqual(sentinel.read_text(), 'retain me')
            receipts = list(root.glob('*.execution-*.json'))
            self.assertEqual(len(receipts), 1)
            receipt = json.loads(receipts[0].read_text())
            self.assertEqual(receipt['state'], 'complete')
            self.assertEqual([(row['id'], row['status']) for row in receipt['results']], [(item['id'], 'removed')])
            self.assertGreater(receipt['results'][0]['removed_entries'], 0)


if __name__ == '__main__':
    unittest.main()
