import argparse
import base64
import hashlib
import subprocess
import os
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import fs_lifecycle as fs
import fs_recovery as recovery


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='fs-recovery-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.project=self.root/'project'; self.project.mkdir()

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value) if isinstance(value,dict) else value)

    def npm(self):
        target=self.project/'node_modules'; target.mkdir()
        self.write(self.project/'package.json',{'name':'fixture','dependencies':{'pkg':'^1.0.0'}})
        records={'':{'dependencies':{'pkg':'^1.0.0'}},'node_modules/pkg':{'version':'1.0.1','resolved':'https://private.example/pkg.tgz','integrity':'sha512-fixture'}}
        self.write(self.project/'package-lock.json',{'lockfileVersion':3,'packages':records})
        self.write(target/'.package-lock.json',{'lockfileVersion':3,'packages':{'node_modules/pkg':records['node_modules/pkg']}})
        self.write(target/'pkg/package.json',{'name':'pkg','version':'1.0.1'})
        self.write(target/'pkg/index.js','module.exports = 1')
        return target

    def cargo(self):
        target=self.project/'target'; target.mkdir()
        self.write(self.project/'Cargo.toml','[package]\nname="fixture"\nversion="0.1.0"\nbuild="build.rs"\n[dependencies]\nserde="1"\n[workspace]\nmembers=["member"]\n')
        self.write(self.project/'build.rs','fn main() {}')
        self.write(self.project/'src/main.rs','fn main() {} // dirty retained source')
        self.write(self.project/'member/Cargo.toml','[package]\nname="member"\nversion="0.1.0"\n')
        self.write(self.project/'member/src/lib.rs','// retained')
        self.write(target/'CACHEDIR.TAG','Signature: 8a477f597d28d172789f06886806bc55')
        self.write(target/'.rustc_info.json',{'rustc_fingerprint':1,'outputs':{}})
        self.write(target/'debug/binary','build output')
        return target

    def zig(self):
        target=self.project/'.zig-cache'; target.mkdir()
        self.write(self.project/'build.zig','pub fn build(b: *Build) void {}')
        self.write(self.project/'build.zig.zon','. { .dependencies = .{ .dep = .{ .url = "https://private.example/dep.tar.gz" } } }')
        self.write(target/'h/abcdef.txt','owner cache manifest')
        self.write(target/'o/abcdef/build.o','compiled object')
        return target

    def venv(self):
        target=self.project/'.venv'; target.mkdir()
        self.write(target/'pyvenv.cfg','home = /fixture/python\nversion = 3.12\n')
        self.write(self.project/'requirements.txt','pkg==1.0\n')
        self.write(target/'lib/python3.12/site-packages/pkg-1.0.dist-info/METADATA','Name: pkg\nVersion: 1.0\n')
        self.write(target/'lib/python3.12/site-packages/pkg/__init__.py','# installed')
        self.venv_record(target)
        return target

    def venv_record(self,target):
        site=target/'lib/python3.12/site-packages'
        rows=[]
        for file in sorted(site.rglob('*')):
            if file.is_file() and file.name != 'RECORD':
                data=file.read_bytes();digest=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
                rows.append(f'{file.relative_to(site)},sha256={digest},{len(data)}')
        rows.append('pkg-1.0.dist-info/RECORD,,')
        self.write(site/'pkg-1.0.dist-info/RECORD','\n'.join(rows)+'\n')

    def audit(self,target,processes=None):
        with patch.object(fs,'open_codex_roots',return_value=[]):
            return fs.audit_artifacts([(target,self.root)],processes or [],True,[])[0]

    def apply(self,item):
        item['storage']=fs.storage_evidence(Path(item['canonical_path']))
        envelope={'roots':[str(self.root)],'kinds':['generated_artifact'],'exclusions':[],
            'filesystem':fs.filesystem_identity(self.root),'volume':str(self.root),'target_free_delta_bytes':None,
            'risk_ceiling_bytes':item['storage']['allocated_bytes']}
        doc={'schema':fs.SCHEMA,'generated_at':fs.now_utc(),'authorization':{'mode':'goal_authorized','envelope':envelope},'candidates':[item]}
        doc['integrity']={'algorithm':'sha256','digest':fs.manifest_digest(doc)}
        path=self.root/'manifest.json'; path.write_text(json.dumps(doc))
        args=fs.parser().parse_args(['apply','--manifest',str(path),'--id',item['id'],'--authorization-source','goal_authorization','--execute','--ack',fs.ACK])
        with patch.object(fs,'process_snapshot',return_value=([],True,None)),patch.object(fs,'open_codex_roots',return_value=[]),contextlib.redirect_stdout(io.StringIO()):
            return fs.apply_manifest(args)

    def test_npm_private_registry_success_and_real_fixture_apply(self):
        target=self.npm(); item=self.audit(target)
        self.assertEqual(item['classification'],'safe_now',item['recovery'])
        self.assertEqual(self.apply(item),0)
        self.assertFalse(target.exists()); self.assertTrue((self.project/'package-lock.json').exists())

    def test_cargo_dependencies_workspace_dirty_source_success_apply(self):
        target=self.cargo(); item=self.audit(target)
        self.assertEqual(item['classification'],'safe_now',item['recovery'])
        self.assertEqual(self.apply(item),0)
        self.assertFalse(target.exists()); self.assertTrue((self.project/'src/main.rs').exists()); self.assertTrue((self.project/'build.rs').exists())

    def test_zig_success_apply(self):
        target=self.zig(); item=self.audit(target)
        self.assertEqual(item['classification'],'safe_now',item['recovery'])
        self.assertEqual(self.apply(item),0)
        self.assertFalse(target.exists()); self.assertTrue((self.project/'build.zig').exists())

    def test_venv_success_apply(self):
        target=self.venv(); item=self.audit(target)
        self.assertEqual(item['classification'],'safe_now',item['recovery'])
        self.assertEqual(self.apply(item),0)
        self.assertFalse(target.exists()); self.assertTrue((self.project/'requirements.txt').exists())

    def test_npm_active_handle_veto(self):
        target=self.npm()
        item=self.audit(target,[{'pid':9,'command':'node','cwd':[],'paths':[str(target/'pkg/index.js')]}])
        self.assertEqual(item['classification'],'safe_after_active_thread_closeout')

    def workspace(self):
        target=self.npm()
        spec=json.loads((self.project/'package.json').read_text());spec['workspaces']=['apps/*'];self.write(self.project/'package.json',spec)
        lock=json.loads((self.project/'package-lock.json').read_text()); records=lock['packages']
        records['']['workspaces']=['apps/*']
        records['apps/mobile']={'name':'mobile','version':'1.0.0','dependencies':{'inner':'1.0.0'}}
        records['apps/mobile/node_modules/inner']={'version':'1.0.0','resolved':'https://registry.npmjs.org/inner/-/inner-1.0.0.tgz','integrity':'sha512-fixture'}
        records['node_modules/mobile']={'resolved':'apps/mobile','link':True}
        self.write(self.project/'package-lock.json',lock)
        self.write(target/'.package-lock.json',{'lockfileVersion':3,'packages':{k:v for k,v in records.items() if k}})
        self.write(self.project/'apps/mobile/package.json',{'name':'mobile','version':'1.0.0','dependencies':{'inner':'1.0.0'}})
        self.write(self.project/'apps/mobile/node_modules/inner/package.json',{'name':'inner','version':'1.0.0'})
        (target/'mobile').symlink_to('../apps/mobile',target_is_directory=True)
        return target

    def test_workspace_root_apply_preserves_workspace_source_and_nested_install(self):
        target=self.workspace(); source=self.project/'apps/mobile/package.json';before=source.read_bytes()
        item=self.audit(target);self.assertEqual(item['classification'],'safe_now',item['recovery'])
        self.assertEqual(self.apply(item),0);self.assertFalse(target.exists())
        self.assertEqual(source.read_bytes(),before)
        self.assertTrue((self.project/'apps/mobile/node_modules/inner/package.json').exists())

    def test_workspace_nested_install_and_root_package_unit_supported(self):
        target=self.workspace()
        for path in [self.project/'apps/mobile/node_modules',target/'pkg']:
            item=self.audit(path);self.assertEqual(item['classification'],'safe_now',item['recovery'])

    def test_workspace_spec_drift_refused(self):
        target=self.workspace()
        self.write(self.project/'apps/mobile/package.json',{'name':'mobile','version':'2','dependencies':{'inner':'1.0.0'}})
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_workspace_install_escape_and_undeclared_workspace_refused(self):
        target=self.workspace();p=target/'.package-lock.json';d=json.loads(p.read_text())
        d['packages']['../outside']={'version':'1'};self.write(p,d)
        self.assertEqual(self.audit(target)['classification'],'unknown')
        del d['packages']['../outside'];d['packages']['unlisted/workspace']={'version':'1'};self.write(p,d)
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_package_unit_apply_retains_sensitive_sibling_without_reading_it(self):
        target=self.npm();self.write(target/'pkg2/.env','fixture sentinel')
        # The unowned/sensitive sibling prevents whole-tree deletion but does
        # not confer ownership or deletion authority on that sibling.
        self.assertEqual(self.audit(target)['classification'],'unknown')
        item=self.audit(target/'pkg');self.assertEqual(item['classification'],'safe_now',item['recovery'])
        self.assertEqual(self.apply(item),0)
        self.assertTrue((target/'pkg2/.env').exists());self.assertTrue((target/'.package-lock.json').exists())

    def test_package_unit_unknown_and_sensitive_content_refused(self):
        target=self.npm();self.write(target/'custom/package.json',{'version':'1'})
        self.assertEqual(self.audit(target/'custom')['classification'],'unknown')
        self.write(target/'pkg/.env','fixture sentinel')
        self.assertEqual(self.audit(target/'pkg')['classification'],'unknown')

    def test_package_unit_consumer_of_sibling_and_owner_cwd_protect_install(self):
        target=self.npm()
        for process in [
            {'pid':9,'command':'node','cwd':[],'paths':[str(target/'other/index.js')]},
            {'pid':9,'command':'node','cwd':[str(self.project)],'paths':[]},
        ]:
            self.assertEqual(self.audit(target/'pkg',[process])['classification'],'safe_after_active_thread_closeout')

    def test_package_unit_owner_appears_after_audit_vetoes_apply(self):
        target=self.npm();item=self.audit(target/'pkg')
        with self.assertRaisesRegex(RuntimeError,'live consumer'):
            fs.revalidate_liveness(item,target/'pkg',[{'pid':9,'command':'node','cwd':[str(self.project)],'paths':[]}],True,[])
        self.assertTrue((target/'pkg').exists())

    def test_package_unit_discovery_requires_explicit_flag(self):
        target=self.npm()
        ordinary,_=fs.scan_artifacts([self.project],7)
        expanded,_=fs.scan_artifacts([self.project],7,npm_package_units=True)
        self.assertNotIn((target/'pkg',self.project),ordinary)
        self.assertIn((target/'pkg',self.project),expanded)
        narrowed,_=fs.scan_artifacts([self.project],7,npm_package_units=True,npm_package_names={'other'})
        self.assertNotIn((target/'pkg',self.project),narrowed)

    def test_package_unit_mount_point_excluded_and_apply_boundary_refuses_it(self):
        target=self.npm();item=self.audit(target/'pkg')
        with patch.object(fs,'mounted_descendants',side_effect=lambda path:[str(target/'pkg')] if path in (self.project,self.root) else []):
            discovered,evidence=fs.scan_artifacts([self.project],7,npm_package_units=True)
            self.assertNotIn((target/'pkg',self.project),discovered)
            self.assertIn(str(target/'pkg'),evidence['excluded_mounts'])
            self.assertEqual(self.audit(target/'pkg')['classification'],'unknown')
            with self.assertRaisesRegex(RuntimeError,'nested mount'):fs.verify_boundary(item,target/'pkg')

    def test_scoped_package_unit_apply_and_unowned_child_refusal(self):
        target=self.npm()
        for file in [self.project/'package-lock.json',target/'.package-lock.json']:
            data=json.loads(file.read_text());data['packages']['node_modules/@scope/tool']={'version':'1.0.0'};self.write(file,data)
        self.write(target/'@scope/tool/package.json',{'name':'@scope/tool','version':'1.0.0'})
        item=self.audit(target/'@scope');self.assertEqual(item['classification'],'safe_now',item['recovery'])
        self.write(target/'@scope/custom/package.json',{'name':'custom','version':'1'})
        self.assertEqual(self.audit(target/'@scope')['classification'],'unknown')
        leaf=self.audit(target/'@scope/tool');self.assertEqual(leaf['classification'],'safe_now',leaf['recovery'])
        discovered,_=fs.scan_artifacts([self.project],7,npm_package_units=True,npm_package_names={'@scope'})
        self.assertIn((target/'@scope/tool',self.project),discovered)
        (target/'@scope/custom/package.json').unlink();(target/'@scope/custom').rmdir()
        item=self.audit(target/'@scope');self.assertEqual(self.apply(item),0)
        self.assertTrue((target/'pkg/package.json').exists())

    def test_target_limited_qualification_never_counts_parent_and_child_twice(self):
        target=self.npm()
        items,planning=fs.audit_target_artifacts([(target,self.root),(target/'pkg',self.root)],[],True,[],10**12)
        self.assertEqual(len(items),1)
        self.assertEqual(planning['deferred_unassessed_candidate_count'],1)

    def test_assessment_limit_leaves_remaining_candidates_explicitly_unassessed(self):
        target=self.npm()
        other=self.root/'z-project/node_modules';other.mkdir(parents=True)
        items,planning=fs.audit_target_artifacts([(target,self.root),(other,self.root)],[],True,[],10**12,max_candidates=1)
        self.assertEqual(len(items),1)
        self.assertEqual(planning['assessed_candidate_count'],1)
        self.assertEqual(planning['deferred_unassessed_candidate_count'],1)

    def test_unit_local_source_inside_another_package_refused(self):
        target=self.npm()
        spec=json.loads((self.project/'package.json').read_text());spec['dependencies']['local']='file:node_modules/pkg2'
        self.write(self.project/'package.json',spec)
        lock=json.loads((self.project/'package-lock.json').read_text());lock['packages']['']['dependencies']=spec['dependencies'];self.write(self.project/'package-lock.json',lock)
        self.write(target/'pkg2/package.json',{'version':'1'})
        item=self.audit(target/'pkg');self.assertEqual(item['classification'],'unknown')
        self.assertIn('local source',item['recovery']['reason'])

    def test_unit_lock_drift_after_audit_refuses_removal(self):
        target=self.npm();item=self.audit(target/'pkg')
        lock=json.loads((self.project/'package-lock.json').read_text());lock['packages']['node_modules/pkg']['version']='2';self.write(self.project/'package-lock.json',lock)
        with self.assertRaisesRegex(RuntimeError,'recovery'): fs.revalidate_static(item)
        self.assertTrue((target/'pkg').exists())

    def test_stale_sibling_does_not_disqualify_independent_package_unit(self):
        target=self.npm()
        lock=json.loads((self.project/'package-lock.json').read_text());lock['packages']['node_modules/stale']={'version':'2'};self.write(self.project/'package-lock.json',lock)
        installed=json.loads((target/'.package-lock.json').read_text());installed['packages']['node_modules/stale']={'version':'1'};self.write(target/'.package-lock.json',installed)
        self.write(target/'stale/package.json',{'name':'stale','version':'1'})
        self.assertEqual(self.audit(target)['classification'],'unknown')
        self.assertEqual(self.audit(target/'stale')['classification'],'unknown')
        good=self.audit(target/'pkg');self.assertEqual(good['classification'],'safe_now',good['recovery'])
        self.assertEqual(self.apply(good),0);self.assertTrue((target/'stale/package.json').exists())

    def test_incomplete_package_owner_record_cannot_authorize_deletion(self):
        target=self.npm();data=json.loads((target/'.package-lock.json').read_text());data['packages']['node_modules/pkg']={};self.write(target/'.package-lock.json',data)
        self.assertEqual(self.audit(target/'pkg')['classification'],'unknown')

    def test_retained_sibling_local_source_link_supported_without_deleting_source(self):
        target=self.npm();self.write(self.root/'local/package.json',{'name':'local','version':'1'})
        lock=json.loads((self.project/'package-lock.json').read_text())
        lock['packages']['../local']={'version':'1'}
        lock['packages']['node_modules/local']={'resolved':'../local','link':True}
        self.write(self.project/'package-lock.json',lock)
        installed=json.loads((target/'.package-lock.json').read_text())
        installed['packages']['../local']={'version':'1'}
        installed['packages']['node_modules/local']={'resolved':'../local','link':True}
        self.write(target/'.package-lock.json',installed)
        (target/'local').symlink_to('../../local',target_is_directory=True)
        item=self.audit(target);self.assertEqual(item['classification'],'safe_now',item['recovery'])
        self.assertEqual(self.apply(item),0);self.assertTrue((self.root/'local/package.json').exists())

    def test_source_link_replaced_by_real_directory_is_not_disposable(self):
        target=self.workspace();(target/'mobile').unlink()
        self.write(target/'mobile/package.json',{'name':'mobile','version':'1.0.0'})
        self.assertEqual(self.audit(target/'mobile')['classification'],'unknown')
        self.assertTrue((target/'mobile/package.json').exists())

    def test_npm_mutated_owner_metadata_rejected(self):
        target=self.npm(); item=self.audit(target)
        self.write(target/'pkg/package.json',{'name':'pkg','version':'2'})
        with self.assertRaisesRegex(RuntimeError,'recovery'): fs.revalidate_static(item)

    def test_npm_unsupported_lock_reason(self):
        target=self.npm(); self.write(self.project/'package-lock.json',{'lockfileVersion':1})
        item=self.audit(target)
        self.assertEqual(item['classification'],'unknown')
        self.assertIn('v2/v3',item['recovery']['reason'])

    def test_npm_missing_local_dependency_retained(self):
        target=self.npm(); spec=json.loads((self.project/'package.json').read_text());spec['dependencies']['pkg']='file:../missing'
        self.write(self.project/'package.json',spec)
        lock=json.loads((self.project/'package-lock.json').read_text());lock['packages']['']['dependencies']=spec['dependencies'];self.write(self.project/'package-lock.json',lock)
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_cargo_missing_path_dependency_retained(self):
        target=self.cargo()
        with (self.project/'Cargo.toml').open('a') as f: f.write('\n[dependencies.local]\npath="../missing"\n')
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_python_missing_editable_source_retained(self):
        target=self.venv()
        self.write(target/'lib/python3.12/site-packages/pkg-1.0.dist-info/direct_url.json',{'url':'file:///missing-fixture-source','dir_info':{'editable':True}})
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_custom_top_level_state_retained(self):
        target=self.npm(); self.write(target/'my-notes.txt','unique')
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_sensitive_state_inside_owned_package_is_retained_without_read(self):
        target=self.npm(); self.write(target/'pkg/private.key','fixture sensitive state')
        with patch.object(recovery.Evidence, 'read', side_effect=AssertionError('screen metadata before reading bodies')):
            item=self.audit(target)
        self.assertEqual(item['classification'],'unknown')
        self.assertIn('credential-shaped',item['recovery']['reason'])

    def test_unknown_candidates_are_sized_in_full_audit_only(self):
        target=self.npm();self.write(self.project/'package-lock.json',{'lockfileVersion':1})
        item=self.audit(target)
        fs.size_candidates([item],target_bytes=None,headroom_percent=25,preferred_kinds=[],included_kinds=None)
        self.assertGreater(item['storage']['allocated_bytes'],0)
        chosen,_,_=fs.select_candidates([item],target_bytes=1,headroom_percent=0,preferred_kinds=[],included_kinds=None)
        self.assertEqual(chosen,[])

    def test_npm_unlisted_scoped_package_preserved(self):
        target=self.npm()
        self.write(target/'@scope/custom/package.json',{'name':'@scope/custom','version':'1'})
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_python_modified_owned_file_preserved(self):
        target=self.venv()
        self.write(target/'lib/python3.12/site-packages/pkg/__init__.py','user edit')
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_python_unowned_file_preserved(self):
        target=self.venv()
        self.write(target/'lib/python3.12/site-packages/custom.py','unique')
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_public_cli_npm_audit_select_apply_preserves_source(self):
        target=self.npm(); before=(self.project/'package.json').read_bytes()
        binary=self.root/'bin'; binary.mkdir(); fake=binary/'lsof'
        fake.write_text('#!/usr/bin/env python3\nimport sys\nsys.stdout.buffer.write(b"p999999\\0cfixture\\0\\n")\n')
        fake.chmod(0o700)
        env={**os.environ,'PATH':str(binary)+os.pathsep+os.environ.get('PATH',''),'PYTHONDONTWRITEBYTECODE':'1'}
        script=Path(fs.__file__)
        manifest=self.root/'cli.json'; selection=self.root/'selected.json'
        def run(*args):
            result=subprocess.run([sys.executable,'-B',str(script),*args],env=env,cwd=self.root,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        run('audit','--root',str(self.project),'--volume',str(self.root),'--kind','generated_artifact','--authorization-mode','goal_authorized','--authorization-scope','temporary fixture only','--output',str(manifest))
        run('select','--manifest',str(manifest),'--target-gib','0.000001','--output',str(selection))
        selected=json.loads(selection.read_text())['selected_ids'][0]
        run('apply','--manifest',str(manifest),'--id',selected,'--authorization-source','manifest_approval','--execute','--ack',fs.ACK)
        self.assertFalse(target.exists())
        self.assertEqual((self.project/'package.json').read_bytes(),before)

    def test_python_missing_local_wheel_source_retained(self):
        target=self.venv()
        self.write(self.project/'requirements.txt','--no-index\n--find-links ../missing-wheels\npkg==1.0\n')
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_python_missing_constraint_include_retained(self):
        target=self.venv()
        self.write(self.project/'requirements.txt','-c constraints.txt\npkg==1.0\n')
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_cargo_workspace_member_missing_source_retained(self):
        target=self.cargo()
        (self.project/'member/src/lib.rs').unlink();(self.project/'member/src').rmdir()
        self.assertEqual(self.audit(target)['classification'],'unknown')

    def test_metadata_symlink_ancestor_refused(self):
        target=self.npm(); outside=self.root/'outside';outside.mkdir()
        self.write(outside/'package.json',{'name':'pkg','version':'1.0.1'})
        (target/'pkg/index.js').unlink();(target/'pkg/package.json').unlink();(target/'pkg').rmdir()
        (target/'pkg').symlink_to(outside,target_is_directory=True)
        # Local package symlink may be retained, but opening owner metadata through it is forbidden.
        with self.assertRaises(OSError):recovery.Evidence(target).read(target/'pkg/package.json')

if __name__=='__main__':unittest.main()
