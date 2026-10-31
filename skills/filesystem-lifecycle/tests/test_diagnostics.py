import contextlib
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
import fs_diagnostics as d


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='fs-doctor-fixture-')
        self.root = Path(self.tmp.name).resolve()
        self.mounts = {'status':'complete','paths':['/']}
    def tearDown(self): self.tmp.cleanup()
    def scan(self, **kwargs):
        return d.scan_root(self.root, mounts=kwargs.pop('mounts', self.mounts), max_depth=kwargs.pop('max_depth', 5), max_entries=kwargs.pop('max_entries', 100), timeout=kwargs.pop('timeout', 5), catalog=d.load_catalog(), **kwargs)
    def test_metadata_and_unknown_owner(self):
        (self.root/'large').write_bytes(b'x'*8192)
        result=self.scan()
        self.assertEqual(result['status'],'complete')
        self.assertEqual(result['resources'][0]['classification'],'unknown')
        self.assertGreaterEqual(result['resources'][0]['storage']['allocated_bytes'],8192)
        self.assertIsNone(result['resources'][0]['action'])
    def test_protected_names_and_symlinks_are_not_read(self):
        secret=self.root/'.env'; secret.write_text('private')
        folder=self.root/'Mail'; folder.mkdir(); (folder/'message').write_text('private')
        (self.root/'alias').symlink_to(folder, target_is_directory=True)
        result=self.scan()
        self.assertEqual(result['resources'],[])
        self.assertEqual(result['status'],'partial')
        self.assertEqual(secret.read_text(),'private')
    def test_bind_mount_same_device_excluded(self):
        folder=self.root/'mounted';folder.mkdir();(folder/'payload').write_text('data')
        result=self.scan(mounts={'status':'complete','paths':[str(folder)]})
        self.assertFalse(result['resources'])
        self.assertIn('mount boundary',result['coverage_gaps'][0]['reason'])
    def test_incomplete_mount_probe_refuses_scan(self):
        result=self.scan(mounts={'status':'partial','paths':[]})
        self.assertEqual(result['status'],'unavailable'); self.assertEqual(result['entries_examined'],0)
    def test_entry_and_depth_limits_are_partial(self):
        for n in range(5): (self.root/str(n)).write_text('x')
        self.assertEqual(self.scan(max_entries=2)['entries_examined'],2)
        folder=self.root/'deep';folder.mkdir();(folder/'file').write_text('x')
        result=self.scan(max_depth=1)
        self.assertEqual(result['status'],'partial')
        self.assertTrue(any(g['reason']=='depth limit' for g in result['coverage_gaps']))
    def test_catalog_is_inventory_only(self):
        (self.root/'package.json').write_text('{}')
        folder=self.root/'node_modules';folder.mkdir()
        info=d.owner_for(folder,d.load_catalog())
        self.assertEqual(info['owner'],'node-package-manager')
        self.assertEqual(info['recovery']['level'],'none_or_unknown')
    def test_report_unknown_size_and_pipe_escaping(self):
        result=d.render_report({'candidates':[{'path':'x|y','classification':'unknown'}]})
        self.assertIn('x\\|y',result);self.assertIn('unknown',result);self.assertNotIn('0 bytes',result)
    def test_report_cli_preserves_input_and_refuses_overwrite(self):
        source=self.root/'manifest.json';source.write_text(json.dumps({'candidates':[{'path':'fixture','storage':{'allocated_bytes':12}}]}))
        before=source.read_bytes()
        cmd=[sys.executable,'-B',str(Path(d.__file__)),'report','--input',str(source)]
        proc=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr);self.assertIn('12 bytes',proc.stdout)
        proc=subprocess.run(cmd+['--output',str(source)],capture_output=True,text=True)
        self.assertEqual(proc.returncode,2);self.assertEqual(source.read_bytes(),before)
    def test_doctor_cli_fixture(self):
        (self.root/'payload').write_text('data')
        before=set(self.root.iterdir())
        proc=subprocess.run([sys.executable,'-B',str(Path(d.__file__)),'doctor','--root',str(self.root),'--volume',str(self.root)],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        data=json.loads(proc.stdout);self.assertEqual(data['mode'],'doctor')
        self.assertFalse(data['mutation_authorized']);self.assertEqual(set(self.root.iterdir()),before)
    def test_probe_output_limit_and_timeout(self):
        result=d.probe([sys.executable,'-c','print("x"*100000)'],2,limit=1024)
        self.assertEqual(result['status'],'partial');self.assertLessEqual(len(result['stdout']),1024)
        result=d.probe([sys.executable,'-c','import time;time.sleep(1)'],.01)
        self.assertEqual(result['status'],'partial');self.assertEqual(result['reason'],'probe timeout')
    def test_warning_visibility_is_not_complete(self):
        result=d.probe([sys.executable,'-c','import sys;sys.stderr.write("warning")'],2)
        self.assertEqual(result['status'],'partial')
    def test_no_roots_means_no_traversal(self):
        parser=d.argparse.ArgumentParser();d.register_commands(parser.add_subparsers(required=True))
        args=parser.parse_args(['doctor','--volume',str(self.root)])
        with patch.object(d,'scan_root',side_effect=AssertionError('must not traverse')), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(d.doctor(args),0)
        self.assertEqual(json.loads(out.getvalue())['resources'],[])

    def test_markdown_capacity_partial_and_apply_receipt(self):
        doc={'status':'partial','probes':{'capacity':{'status':'complete','path':'fixture','available_bytes':2048,'inodes_available':3,'inodes_total':7},'deleted_open':{'status':'partial','observations':[{'status':'unavailable','reason':'permission denied','resources':[]}]}},'coverage_gaps':[{'probe':'deleted_open','reason':'permission denied'}]}
        output=d.render_report(doc)
        self.assertIn('available 2048 bytes',output)
        self.assertIn('available inodes 3 / 7',output)
        self.assertIn('permission denied',output)
        output=d.render_report({'physical_free_delta_bytes':99,'results':[{'status':'partially_removed','candidate':{'path':'fixture','storage':{'allocated_bytes':42},'recovery':{'level':'regenerable'}}}]})
        self.assertTrue(output.startswith('Measured volume free-space change: 99'))
        self.assertIn('42 bytes',output);self.assertIn('partially_removed',output)
    def test_nested_catalog_discovery_records_overlap(self):
        project=self.root/'project';project.mkdir();(project/'package.json').write_text('{}')
        modules=project/'node_modules';modules.mkdir();(modules/'file').write_text('data')
        rows=self.scan()['resources'];module=next(r for r in rows if r['path']==str(modules))
        self.assertEqual(module['owner'],'node-package-manager');self.assertEqual(module['covered_by'],str(project))
    def test_directory_swap_to_symlink_is_not_traversed(self):
        folder=self.root/'swap';folder.mkdir();outside=self.root/'outside';outside.mkdir();(outside/'sentinel').write_text('secret')
        original=os.open
        def swapping(path, flags, *args, **kwargs):
            if path=='swap' and kwargs.get('dir_fd') is not None:
                folder.rename(self.root/'old-swap');folder.symlink_to(outside,target_is_directory=True)
            return original(path,flags,*args,**kwargs)
        with patch.object(d.os,'open',side_effect=swapping): result=self.scan()
        self.assertEqual(result['status'],'partial')
        self.assertTrue(any('directory open failed' in g['reason'] for g in result['coverage_gaps']))
        self.assertEqual((outside/'sentinel').read_text(),'secret')
    def test_apfs_snapshot_failure_propagates(self):
        info=d.plistlib.dumps({'FilesystemType':'apfs'}).decode()
        with patch.object(d.sys,'platform','darwin'), patch.object(d,'filesystem_mount',return_value={'status':'complete','path':'/System/Volumes/Data','device':2}), patch.object(d,'probe',side_effect=[{'status':'complete','stdout':info},{'status':'unavailable','stdout':''}]):
            result=d.apfs_observation(self.root,1)
        self.assertEqual(result['status'],'partial')
    def test_launchd_matches_only_scoped_owner_labels(self):
        output='PID Status Label\n12 0 com.example.fixture\n99 0 unrelated\n'
        with patch.object(d.sys,'platform','darwin'),patch.object(d,'probe',return_value={'status':'complete','stdout':output}):
            result=d.launchd_observation({'com.example.fixture'},1)
        self.assertEqual(result['matches'],[{'label':'com.example.fixture','pid':12,'registered':True}])

    def test_firmlink_mount_uses_device_before_prefix(self):
        from types import SimpleNamespace
        target=Path('/fixture/project')
        devices={'/':1,'/System/Volumes/Data':2,str(target):2}
        def fake_stat(path, *args, **kwargs): return SimpleNamespace(st_dev=devices[str(path)])
        with patch.object(d,'mount_inventory',return_value={'status':'complete','paths':['/','/System/Volumes/Data']}), patch.object(Path,'resolve',lambda p, **kw:p), patch.object(Path,'stat',fake_stat), patch.object(d.os,'statvfs',return_value=SimpleNamespace(f_fsid=2)):
            binding=d.filesystem_mount(target,1)
        self.assertEqual(binding,{'status':'complete','path':'/System/Volumes/Data','device':2})
    def test_device_bind_mount_uses_longest_matching_ancestor(self):
        from types import SimpleNamespace
        with patch.object(d,'mount_inventory',return_value={'status':'complete','paths':['/','/mnt/bind']}), patch.object(Path,'resolve',lambda p, **kw:p), patch.object(Path,'stat',return_value=SimpleNamespace(st_dev=2)), patch.object(d.os,'statvfs',return_value=SimpleNamespace(f_fsid=2)):
            self.assertEqual(d.filesystem_mount(Path('/mnt/bind/project'),1)['path'],'/mnt/bind')
    def test_apfs_and_lsof_use_bound_mount(self):
        info=d.plistlib.dumps({'FilesystemType':'apfs'}).decode()
        snaps=d.plistlib.dumps({'Snapshots':[]}).decode()
        binding={'status':'complete','path':'/System/Volumes/Data','device':2}
        with patch.object(d.sys,'platform','darwin'),patch.object(d,'filesystem_mount',return_value=binding),patch.object(d,'probe',side_effect=[{'status':'complete','stdout':info},{'status':'complete','stdout':snaps}]) as probe:
            self.assertEqual(d.apfs_observation(Path('/fixture'),1)['status'],'complete')
            self.assertTrue(all(call.args[0][-1]=='/System/Volumes/Data' for call in probe.call_args_list))
        with patch.object(d,'filesystem_mount',return_value=binding),patch.object(d,'probe',return_value={'status':'complete','stdout':'','stderr':'','returncode':0}) as probe:
            d.deleted_open(Path('/fixture'),1)
            self.assertEqual(probe.call_args.args[0][-1],'/System/Volumes/Data')
    def test_capacity_filesystem_identity_is_numeric(self):
        self.assertIsInstance(d.capacity(self.root)['filesystem_id'],int)

    def test_apfs_snapshot_same_device_distinct_filesystem_id(self):
        from types import SimpleNamespace
        def fsid(path): return SimpleNamespace(f_fsid=1 if str(path)=='/' else 2)
        with patch.object(d,'mount_inventory',return_value={'status':'complete','paths':['/','/System/Volumes/Data']}),patch.object(Path,'resolve',lambda p, **kw:p),patch.object(Path,'stat',return_value=SimpleNamespace(st_dev=2)),patch.object(d.os,'statvfs',side_effect=fsid):
            self.assertEqual(d.filesystem_mount(Path('/fixture'),1)['path'],'/System/Volumes/Data')

if __name__=='__main__': unittest.main()
