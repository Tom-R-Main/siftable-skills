"""Git owner contract against real disposable repositories."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import fs_lifecycle as fs

class GitOwnerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name).resolve()
        self.repo=self.root/'repo'; self.repo.mkdir()
        self.git('init','-b','main')
        self.git('config','user.name','Fixture')
        self.git('config','user.email','fixture@example.invalid')
        (self.repo/'source.txt').write_text('source\n')
        self.git('add','source.txt'); self.git('commit','-m','fixture')
        self.linked=self.root/'linked'
        self.git('worktree','add','-b','completed',str(self.linked))
    def tearDown(self): self.temp.cleanup()
    def git(self,*args,repo=None):
        p=subprocess.run(['git','-C',str(repo or self.repo),*args],capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        return p.stdout
    def row(self):
        return next(r for r in fs.audit_worktrees(self.repo,[],True,[]) if r['canonical_path']==str(self.linked))
    def test_clean_retirement_preserves_branch_and_main(self):
        record=self.row(); self.assertEqual(record['classification'],fs.CLASS_SAFE)
        fs.revalidate_worktree(record,self.linked)
        refs=self.git('show-ref')
        self.git('worktree','remove','--',str(self.linked))
        self.assertEqual(self.git('show-ref'),refs)
        self.assertTrue((self.repo/'source.txt').exists())
    def test_dirty_or_unique_is_retained(self):
        (self.linked/'unique.txt').write_text('unique\n')
        self.assertEqual(self.row()['classification'],fs.CLASS_RETAIN)
        self.git('add','unique.txt',repo=self.linked)
        self.git('commit','-m','unique',repo=self.linked)
        self.assertEqual(self.row()['classification'],fs.CLASS_RETAIN)
    def test_locked_worktree_cannot_be_revalidated(self):
        record=self.row()
        self.git('worktree','lock','--reason','fixture',str(self.linked))
        with self.assertRaises(RuntimeError): fs.revalidate_worktree(record,self.linked)
    def test_main_and_task_scope(self):
        records=fs.audit_worktrees(self.repo,[],True,[])
        main=next(r for r in records if r['canonical_path']==str(self.repo))
        self.assertEqual(main['classification'],fs.CLASS_RETAIN)
        self.assertEqual(fs.codex_refs(self.linked,[{'root':str(self.root)}],owner_root=self.linked),[])
        self.assertTrue(fs.codex_refs(self.linked,[{'root':str(self.linked)}],owner_root=self.linked))

if __name__=='__main__': unittest.main()
