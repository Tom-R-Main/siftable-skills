import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import fs_cache_recovery as recovery


class CacheRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def cache(self, name, owner):
        root = self.base / name
        root.mkdir()
        return root, {'path': str(root), 'owner': owner, 'recovery': 'owner reinstall'}

    def node(self):
        root, rule = self.cache('node-gyp', 'node-gyp')
        header = root / '22.1.0/include/node/node_version.h'
        header.parent.mkdir(parents=True)
        header.write_text('#define NODE_MAJOR_VERSION 22\n#define NODE_MINOR_VERSION 1\n#define NODE_PATCH_VERSION 0\n')
        (root / '22.1.0/installVersion').write_text('11\n')
        return root, rule

    def cypress(self):
        root, rule = self.cache('Cypress', 'cypress')
        app = root / '14.0.0/Cypress.app/Contents'
        (app / 'Resources/app').mkdir(parents=True)
        (app / 'Resources/app/package.json').write_text(json.dumps({'name': 'cypress', 'version': '14.0.0'}))
        (app / 'MacOS').mkdir()
        (app / 'MacOS/Cypress').write_bytes(b'fixture installer binary')
        (root / '14.0.0/binary_state.json').write_text('{"verified": true}')
        return root, rule

    def test_homebrew_downloads_qualify_without_network_or_owner_command(self):
        root, rule = self.cache('downloads', 'homebrew')
        (root / ('a' * 64 + '--node-22.1.0.tar.xz')).write_bytes(b'fixture archive')
        with patch('subprocess.run', side_effect=AssertionError('must not run owner')):
            result = recovery.cache_recovery(root, rule)
        self.assertTrue(result['verified'], result)
        self.assertTrue(result['download_required'])
        self.assertEqual(result, recovery.cache_recovery(root, rule))

    def test_mixed_homebrew_root_preserves_other_state_but_child_qualifies(self):
        root, rule = self.cache('Homebrew', 'homebrew')
        (root / 'downloads').mkdir()
        (root / 'downloads' / ('b' * 64 + '--foo.tar.gz')).write_bytes(b'archive')
        (root / 'unrecognized').mkdir()
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])
        child_rule = dict(rule, path=str(root / 'downloads'))
        self.assertTrue(recovery.cache_recovery(root / 'downloads', child_rule)['verified'])

    def test_homebrew_api_and_internal_alias(self):
        root, rule = self.cache('Homebrew', 'homebrew')
        (root / 'downloads').mkdir()
        filename = 'c' * 64 + '--foo.tar.gz'
        (root / 'downloads' / filename).write_bytes(b'archive')
        (root / 'foo.tar.gz').symlink_to('downloads/' + filename)
        (root / 'api').mkdir()
        (root / 'api/formula.jws.json').write_text('{}')
        self.assertTrue(recovery.cache_recovery(root, rule)['verified'])

    def test_incomplete_homebrew_download_is_not_qualified(self):
        root, rule = self.cache('downloads', 'homebrew')
        (root / ('d' * 64 + '--foo.tar.gz.incomplete')).write_bytes(b'partial')
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])

    def test_node_headers_qualify(self):
        root, rule = self.node()
        result = recovery.cache_recovery(root, rule)
        self.assertTrue(result['verified'], result)
        self.assertIn('node-gyp', result['adapter'])
        self.assertTrue(result['fingerprints']['owner_metadata_sha256'])

    def test_node_nested_openssl_uv_and_configuration_headers(self):
        root, rule = self.node()
        include = root / '22.1.0/include/node'
        for name in ('openssl/ssl.h', 'openssl/archs/darwin64-arm64-cc/asm/include/openssl/configuration.h', 'uv/darwin.h', 'v8.h', 'config.gypi', 'common.gypi'):
            path = include / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('/* fixture matching node-gyp extracted suffixes */')
        result = recovery.cache_recovery(root, rule)
        self.assertTrue(result['verified'], result)

    def test_node_version_mismatch_is_unknown(self):
        root, rule = self.node()
        (root / '22.1.0/include/node/node_version.h').write_text('#define NODE_MAJOR_VERSION 20\n')
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])

    def test_unexpected_header_payload_blocks_whole_tree(self):
        root, rule = self.node()
        (root / '22.1.0/include/node/unique.txt').write_text('authored notes')
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])

    def test_cypress_installer_qualifies(self):
        root, rule = self.cypress()
        result = recovery.cache_recovery(root, rule)
        self.assertTrue(result['verified'], result)

    def test_cypress_internal_framework_symlinks_remain_installer_data(self):
        root, rule = self.cypress()
        framework = root / '14.0.0/Cypress.app/Contents/Frameworks/Electron Framework.framework'
        (framework / 'Versions/A/Resources').mkdir(parents=True)
        (framework / 'Versions/A/Electron Framework').write_bytes(b'fixture framework')
        (framework / 'Versions/A/Resources/icudtl.dat').write_bytes(b'fixture runtime data')
        (framework / 'Versions/Current').symlink_to('A')
        (framework / 'Resources').symlink_to('Versions/Current/Resources')
        (framework / 'Electron Framework').symlink_to('Versions/Current/Electron Framework')
        result = recovery.cache_recovery(root, rule)
        self.assertTrue(result['verified'], result)

    def test_cypress_versions_discovered_without_authorizing_sessions(self):
        root, rule = self.cypress()
        (root / 'sessions').mkdir()
        (root / 'bundles').mkdir()
        (root / '15.0.0').symlink_to(root / '14.0.0', target_is_directory=True)
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])
        children = recovery.cache_children(root, rule)
        self.assertEqual([Path(r['path']).name for r in children], ['14.0.0'])
        self.assertTrue(recovery.cache_recovery(Path(children[0]['path']), children[0])['verified'])
        self.assertEqual(recovery.cache_children(Path(children[0]['path']), children[0]), [])

    def test_cypress_version_metadata_must_match(self):
        root, rule = self.cypress()
        (root / '14.0.0/Cypress.app/Contents/Resources/app/package.json').write_text('{"name":"cypress","version":"13.0.0"}')
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])

    def test_mutable_browser_state_is_not_installer_data(self):
        root, rule = self.cypress()
        (root / '14.0.0/Default').mkdir()
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])

    def test_public_cargo_archives_qualify_private_registry_does_not(self):
        root, rule = self.cache('cache', 'cargo')
        registry = root / 'index.crates.io-1949cf8c6b5b557f'
        registry.mkdir()
        (registry / 'serde-1.0.200.crate').write_bytes(b'archive')
        self.assertTrue(recovery.cache_recovery(root, rule)['verified'])
        (root / 'private.example-1234567890abcdef').mkdir()
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])

    def test_credential_name_rejected_without_reading_body(self):
        root, rule = self.node()
        (root / '.env').write_text('fixture secret not read')
        with patch.object(recovery, '_read_owner_file', side_effect=AssertionError('no owner files read after secret found')):
            self.assertFalse(recovery.cache_recovery(root, rule)['verified'])

    def test_fingerprints_detect_payload_drift(self):
        root, rule = self.node()
        before = recovery.cache_recovery(root, rule)
        (root / '22.1.0/include/node/new.h').write_text('/* downloadable header */')
        after = recovery.cache_recovery(root, rule)
        self.assertTrue(after['verified'])
        self.assertNotEqual(before['fingerprints'], after['fingerprints'])

    def test_aggregate_owner_read_bytes_budget(self):
        root, rule = self.node()
        header_bytes = (root / '22.1.0/include/node/node_version.h').stat().st_size
        # Each file individually fits; their aggregate does not.
        result = recovery.cache_recovery(root, rule, max_owner_bytes=header_bytes)
        self.assertFalse(result['verified'])
        self.assertIn('aggregate read budget', result['reason'])
        self.assertEqual(result['fingerprints'], {})

    def test_aggregate_owner_read_count_budget(self):
        root, rule = self.node()
        result = recovery.cache_recovery(root, rule, max_owner_reads=1)
        self.assertFalse(result['verified'])
        self.assertIn('read budget', result['reason'])

    def test_deadline_applies_after_inventory_before_owner_read(self):
        root, rule = self.node()
        clock = [0.0]
        original = recovery._read_owner_file
        def delayed_metadata(*args, **kwargs):
            clock[0] = 11.0
            return original(*args, **kwargs)
        with patch.object(recovery.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(recovery, '_read_owner_file', side_effect=delayed_metadata):
            result = recovery.cache_recovery(root, rule, timeout=10.0)
        self.assertFalse(result['verified'])
        self.assertIn('deadline exceeded', result['reason'])

    def test_outside_symlink_and_budget_hold_candidate(self):
        root, rule = self.node()
        (root / 'outside').symlink_to(self.base)
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])
        self.assertFalse(recovery.cache_recovery(root, rule, max_entries=1)['verified'])

    def test_exact_owner_path_required(self):
        root, rule = self.node()
        rule['path'] = str(self.base / 'different')
        self.assertFalse(recovery.cache_recovery(root, rule)['verified'])

    def test_vm_and_mcp_state_remain_actionable_unknown(self):
        for name, owner in (('vm_bundles', 'claude'), ('ms-playwright-mcp', 'playwright')):
            root, rule = self.cache(name, owner)
            result = recovery.cache_recovery(root, rule)
            self.assertFalse(result['verified'])
            self.assertTrue(result['reason'])


if __name__ == '__main__':
    unittest.main()
