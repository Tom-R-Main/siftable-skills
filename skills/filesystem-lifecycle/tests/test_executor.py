import argparse
import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fs_lifecycle as fs
import fs_safety as safety


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fs-executor-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / 'project'
        self.project.mkdir()
        (self.project / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n')
        self.target = self.project / 'target'
        self.target.mkdir()
        (self.target/'debug').mkdir()
        (self.target/'debug'/'a').write_text('generated')
        (self.target/'debug'/'b').write_text('generated')
        (self.target/'CACHEDIR.TAG').write_text('Signature: 8a477f597d28d172789f06886806bc55')
        (self.target/'.rustc_info.json').write_text('{"rustc_fingerprint": 123, "outputs": {}}')
        (self.project/'src').mkdir()
        (self.project/'src'/'main.rs').write_text('fn main() {}')
        for argv in (['init','-b','main'],['config','user.name','Fixture'],['config','user.email','fixture@example.invalid'],['add','Cargo.toml','src'],['commit','-m','fixture']):
            subprocess.run(['git','-C',str(self.project),*argv],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    def candidate(self):
        recovery = fs.artifact_recovery(self.target, fs.ARTIFACT_RULES['target'])
        item = fs.candidate_base(self.target, self.root, 'generated_artifact', 'cargo', recovery, {'driver':'filesystem'})
        item['classification'] = fs.CLASS_SAFE
        item['owner_root'] = str(self.project)
        return item

    def manifest(self, item=None):
        item = item or self.candidate()
        doc = {'schema':fs.SCHEMA, 'generated_at':fs.now_utc(), 'authorization':{'mode':'goal_authorized', 'envelope':{
            'roots':[str(self.root)], 'kinds':['generated_artifact'], 'exclusions':[],
            'volume':str(self.root), 'filesystem':safety.filesystem_identity(self.root),
            'target_free_delta_bytes':None, 'risk_ceiling_bytes':item['storage']['allocated_bytes']}}, 'candidates':[item]}
        doc['integrity'] = {'algorithm':'sha256','digest':fs.manifest_digest(doc)}
        path = self.root/'manifest.json'
        path.write_text(json.dumps(doc))
        return path, doc

    def args(self, path, doc):
        return argparse.Namespace(execute=True, ack=fs.ACK, manifest=str(path), id=[doc['candidates'][0]['id']], selection=None,
            authorization_source='goal_authorization', max_age_minutes=30, target_gib=None, risk_ceiling_gib=None,
            volume=str(self.root), report_output=None)

    def execute(self, args):
        with patch.object(fs, 'process_snapshot', return_value=([],True,None)), patch.object(fs, 'open_codex_roots', return_value=[]), contextlib.redirect_stdout(io.StringIO()):
            return fs.apply_manifest(args)

    def test_fd_delete_fixture(self):
        result = fs.safe_delete_tree(self.target, expected_identity=fs.path_identity(self.target))
        self.assertEqual(result['removed_entries'], 6)
        self.assertFalse(self.target.exists())

    def test_directory_swap_race_preserves_outside(self):
        victim = self.target/'nested'; victim.mkdir(); (victim/'own').write_text('own')
        outside = self.root/'outside'; outside.mkdir(); sentinel=outside/'sentinel'; sentinel.write_text('keep')
        original = os.open; swapped=False
        def race(name, flags, *args, **kwargs):
            nonlocal swapped
            if name == 'nested' and not swapped:
                swapped=True; victim.rename(self.target/'moved'); victim.symlink_to(outside, target_is_directory=True)
            return original(name, flags, *args, **kwargs)
        with patch.object(safety.os, 'open', side_effect=race), patch.object(safety.os, 'supports_dir_fd', os.supports_dir_fd | {safety.os.open}):
            with self.assertRaises(RuntimeError):
                safety.delete_tree(self.target)
        self.assertTrue(swapped)
        self.assertEqual(sentinel.read_text(),'keep')

    def test_ancestor_symlink_is_rejected(self):
        alias=self.root/'alias'; alias.symlink_to(self.project, target_is_directory=True)
        with self.assertRaises(RuntimeError): safety.delete_tree(alias/'target')
        self.assertTrue(self.target.exists())

    def test_partial_failure_receipt_budget_and_no_replay(self):
        path, doc=self.manifest(); args=self.args(path, doc)
        original=os.unlink
        def fail(name, *a, **kw):
            if name == 'b': raise PermissionError('fixture denied')
            return original(name,*a,**kw)
        with patch.object(safety.os,'unlink',side_effect=fail), patch.object(safety.os,'supports_dir_fd', os.supports_dir_fd | {safety.os.unlink}):
            self.assertEqual(self.execute(args),1)
        receipt=json.loads(fs.execution_report_path(path,doc).read_text())
        self.assertEqual(receipt['results'][0]['status'],'partially_removed')
        self.assertGreaterEqual(receipt['results'][0]['removed_entries'],1)
        self.assertEqual(receipt['approved_budget']['consumed_allocated_budget_bytes'],doc['candidates'][0]['storage']['allocated_bytes'])
        self.assertEqual(receipt['state'],'reconciliation_required')
        with self.assertRaises(ValueError): self.execute(args)
        self.assertTrue((self.target/'debug'/'b').exists())

    def test_intent_is_durable_before_dispatch(self):
        path,doc=self.manifest(); args=self.args(path,doc)
        def interrupted(*a,**kw):
            receipt=json.loads(fs.execution_report_path(path,doc).read_text())
            self.assertEqual(receipt['results'][0]['status'],'in_progress')
            raise KeyboardInterrupt()
        with patch.object(fs,'safe_delete_tree',side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt): self.execute(args)
        with self.assertRaises(ValueError): self.execute(args)
        self.assertTrue(self.target.exists())

    def test_unwritable_journal_does_not_dispatch(self):
        path,doc=self.manifest(); args=self.args(path,doc)
        with patch.object(fs,'atomic_json',side_effect=PermissionError('fixture')), patch.object(fs,'safe_delete_tree') as deletion:
            with self.assertRaises(PermissionError): self.execute(args)
            deletion.assert_not_called()
        self.assertTrue(self.target.exists())

    def test_success_and_readback(self):
        path,doc=self.manifest()
        self.assertEqual(self.execute(self.args(path,doc)),0)
        receipt=json.loads(fs.execution_report_path(path,doc).read_text())
        self.assertEqual(receipt['results'][0]['status'],'removed')
        self.assertEqual(receipt['source_manifest_digest'],doc['integrity']['digest'])
        self.assertFalse(self.target.exists())

    def test_partial_failure_cannot_be_success_from_space(self):
        self.assertEqual(fs.apply_exit_code({'results':[{'status':'partially_removed'}], 'approved_budget':{'target_free_delta_bytes':1},'shortfall_bytes':0}),1)

    def test_lsof_warning_is_incomplete(self):
        with patch.object(fs.shutil,'which',return_value='/fixture/lsof'), patch.object(fs,'run',return_value=subprocess.CompletedProcess([],0,b'p1\ncowner\n',b'WARNING: unavailable')):
            self.assertFalse(fs.process_snapshot()[1])

    def test_lsof_nonzero_and_empty_incomplete(self):
        for result in (subprocess.CompletedProcess([],1,b'',b''),subprocess.CompletedProcess([],0,b'',b'')):
            with patch.object(fs.shutil,'which',return_value='/fixture/lsof'),patch.object(fs,'run',return_value=result):
                self.assertFalse(fs.process_snapshot()[1])

    def test_lsof_malformed_and_timeout(self):
        with patch.object(fs.shutil,'which',return_value='/fixture/lsof'),patch.object(fs,'run',return_value=subprocess.CompletedProcess([],0,b'pabc\n',b'')):
            self.assertFalse(fs.process_snapshot()[1])
        with patch.object(fs.shutil,'which',return_value='/fixture/lsof'),patch.object(fs,'run',side_effect=subprocess.TimeoutExpired('lsof',1)):
            self.assertFalse(fs.process_snapshot()[1])

    def test_cache_owner_rechecked(self):
        item={'kind':'known_cache'}
        rule={'path':str(self.target),'processes':('owner',)}
        with patch.object(fs,'KNOWN_CACHES',(rule,)):
            with self.assertRaisesRegex(RuntimeError,'owner'):
                fs.revalidate_liveness(item,self.target,[{'pid':99,'command':'owner','cwd':[],'paths':[]}],True,[])

    def test_git_failure_not_untracked(self):
        with patch.object(fs,'git_stdout',return_value=(128,b'','permission denied')):
            self.assertIsNone(fs.contains_tracked_files(self.target)[0])

    def test_recovery_conservative(self):
        self.assertTrue(fs.artifact_recovery(self.target,fs.ARTIFACT_RULES['target'])['verified'])
        self.assertFalse(fs.artifact_recovery(self.target,fs.ARTIFACT_RULES['node_modules'])['verified'])
        (self.target/'authored.txt').write_text('unique')
        self.assertFalse(fs.artifact_recovery(self.target,fs.ARTIFACT_RULES['target'])['verified'])
        (self.target/'.env').write_text('not read')
        self.assertFalse(fs.artifact_recovery(self.target,fs.ARTIFACT_RULES['target'])['verified'])

    def test_recovery_drift(self):
        item=self.candidate(); (self.project/'Cargo.toml').write_text('changed')
        with self.assertRaisesRegex(RuntimeError,'recovery'): fs.revalidate_static(item)

    def test_same_device_different_filesystem_id_refused(self):
        path, doc = self.manifest()
        candidate = doc['candidates'][0]
        candidate['identity']['filesystem_id'] = 'other-filesystem'
        with self.assertRaisesRegex(ValueError, 'different target filesystem'):
            fs.validate_envelope(doc, [candidate], self.root)
        self.assertTrue(self.target.exists())

    def test_wrong_filesystem(self):
        path,doc=self.manifest(); doc['authorization']['envelope']['filesystem']['device']=-1
        with self.assertRaises(ValueError): fs.validate_envelope(doc,doc['candidates'],self.root)

    def test_exclusion_and_overlap(self):
        path,doc=self.manifest()
        with self.assertRaises(ValueError): fs.validate_envelope(doc,doc['candidates']*2,self.root)
        doc['authorization']['envelope']['exclusions']=[str(self.target/'a')]
        with self.assertRaises(ValueError): fs.validate_envelope(doc,doc['candidates'],self.root)

    def test_old_and_future_manifest_rejected(self):
        path,doc=self.manifest()
        for change in ({'schema':'filesystem-lifecycle/v2'},{'generated_at':(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=1)).isoformat()}):
            altered={**doc,**change}; altered['integrity']={'algorithm':'sha256','digest':fs.manifest_digest(altered)}; path.write_text(json.dumps(altered))
            with self.assertRaises(ValueError): fs.load_valid_manifest(str(path),30)

    def test_nonfinite_numbers_rejected(self):
        for value in (float('nan'),float('inf'),-1,True):
            with self.assertRaises(ValueError): safety.finite_number(value,'fixture')

    def test_logical_size_failure_has_no_silent_fallback(self):
        with patch.object(fs,'mounted_descendants',return_value=[]),patch.object(fs,'run',return_value=subprocess.CompletedProcess([],1,b'',b'permission denied')):
            with self.assertRaises(RuntimeError): fs.logical_bytes(self.target)

    def test_nested_mount_refused(self):
        with patch.object(fs,'mounted_descendants',return_value=[str(self.target/'nested')]):
            with self.assertRaises(RuntimeError): fs.safe_delete_tree(self.target)
            with self.assertRaises(RuntimeError): fs.logical_bytes(self.target)

    def test_audit_select_apply_fixture_flow(self):
        manifest_path=self.root/'flow.json'
        args=fs.parser().parse_args(['audit','--root',str(self.project),'--volume',str(self.root),'--kind','generated_artifact','--target-gib','0.000001','--authorization-mode','goal_authorized','--authorization-scope','fixture only','--output',str(manifest_path)])
        with patch.object(fs,'process_snapshot',return_value=([],True,None)), patch.object(fs,'open_codex_roots',return_value=[]),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(fs.audit(args),0)
        doc=fs.load_valid_manifest(str(manifest_path),30)
        self.assertEqual(doc['candidates'][0]['classification'],'safe_now')
        selection=self.root/'selection.json'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(fs.select_manifest(fs.parser().parse_args(['select','--manifest',str(manifest_path),'--output',str(selection)])),0)
        apply_args=fs.parser().parse_args(['apply','--manifest',str(manifest_path),'--selection',str(selection),'--authorization-source','goal_authorization','--execute','--ack',fs.ACK])
        self.execute(apply_args)
        self.assertFalse(self.target.exists())
        receipt=json.loads(fs.execution_report_path(manifest_path,doc).read_text())
        self.assertEqual(receipt['results'][0]['status'],'removed')

    def test_selection_cannot_increase_target(self):
        path,doc=self.manifest(); doc['authorization']['envelope']['target_free_delta_bytes']=1024
        doc['integrity']['digest']=fs.manifest_digest(doc); path.write_text(json.dumps(doc))
        args=fs.parser().parse_args(['select','--manifest',str(path),'--target-gib','1'])
        with self.assertRaises(ValueError): fs.select_manifest(args)

    def test_authority_kind_and_root_rejected(self):
        path,doc=self.manifest()
        doc['authorization']['envelope']['kinds']=[]
        with self.assertRaises(ValueError): fs.validate_envelope(doc,doc['candidates'],self.root)
        doc['authorization']['envelope']['kinds']=['generated_artifact']
        doc['authorization']['envelope']['roots']=[str(self.root/'other')]
        with self.assertRaises(ValueError): fs.validate_envelope(doc,doc['candidates'],self.root)

    def test_lsof_nul_preserves_newline_path(self):
        data=b'p123\0cowner\0\nfcwd\0n/fixture/line\nbreak\0\n'
        with patch.object(fs.shutil,'which',return_value='/fixture/lsof'),patch.object(fs,'run',return_value=subprocess.CompletedProcess([],0,data,b'')):
            records,complete,error=fs.process_snapshot()
        self.assertTrue(complete)
        self.assertEqual(records[0]['cwd'],['/fixture/line\nbreak'])

    def test_metadata_retains_ignored_worktree_state(self):
        # Both initial audit and revalidation must request ignored entries.
        repo=self.root/'repo'; repo.mkdir()
        for argv in (['init','-b','main'],['config','user.name','Fixture'],['config','user.email','fixture@example.invalid']):
            subprocess.run(['git','-C',str(repo),*argv],check=True,stdout=subprocess.DEVNULL)
        (repo/'tracked').write_text('source')
        (repo/'.gitignore').write_text('private\n')
        subprocess.run(['git','-C',str(repo),'add','tracked','.gitignore'],check=True)
        subprocess.run(['git','-C',str(repo),'commit','-m','fixture'],check=True,stdout=subprocess.DEVNULL)
        linked=self.root/'linked'
        subprocess.run(['git','-C',str(repo),'worktree','add','-b','done',str(linked)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        (linked/'private').write_text('state')
        candidates=fs.audit_worktrees(repo,[],True,[])
        self.assertEqual(next(x for x in candidates if x['canonical_path']==str(linked))['classification'],'retain')

if __name__ == '__main__': unittest.main()
