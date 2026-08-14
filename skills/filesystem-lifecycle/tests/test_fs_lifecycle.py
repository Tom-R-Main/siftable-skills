#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import argparse
import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fs_lifecycle.py"
SPEC = importlib.util.spec_from_file_location("fs_lifecycle", SCRIPT)
assert SPEC and SPEC.loader
FS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FS)


class FilesystemLifecycleTests(unittest.TestCase):
    def candidate(self, root: Path, path: Path) -> dict:
        return FS.candidate_base(
            path,
            root,
            "generated_artifact",
            "node-package-manager",
            {"level": "regenerable", "method": "package install"},
            {"driver": "filesystem", "operation": "delete_exact_tree"},
        )

    def test_process_cwd_and_open_handle_defer_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "node_modules"
            target.mkdir()
            candidate = self.candidate(root, target)
            processes = [{"pid": 10, "command": "node", "cwd": [str(target)], "paths": [str(target / "open.log")]}]
            FS.classify_path_candidate(candidate, processes, True, [])
            self.assertEqual(candidate["classification"], FS.CLASS_AFTER)
            self.assertEqual(candidate["references"]["cwd_pids"], [10])
            self.assertEqual(candidate["references"]["open_handle_pids"], [10])

    def test_open_handle_with_external_cwd_still_defers_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "node_modules"
            target.mkdir()
            candidate = self.candidate(root, target)
            processes = [{"pid": 11, "command": "node", "cwd": [str(root.parent)], "paths": [str(target / "open.log")]}]
            FS.classify_path_candidate(candidate, processes, True, [])
            self.assertEqual(candidate["classification"], FS.CLASS_AFTER)
            self.assertEqual(candidate["references"]["cwd_pids"], [])
            self.assertEqual(candidate["references"]["open_handle_pids"], [11])

    def test_incomplete_scan_never_becomes_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "unknown"
            candidate = FS.unknown_candidate(target, root, "generated_artifact", "unknown", "permission denied")
            FS.classify_path_candidate(candidate, [], True, [])
            self.assertEqual(candidate["classification"], FS.CLASS_UNKNOWN)

    def test_changed_inode_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "node_modules"
            target.mkdir()
            candidate = self.candidate(root, target)
            original = root / "original-node_modules"
            target.rename(original)
            target.mkdir()
            with self.assertRaisesRegex(RuntimeError, "identity changed"):
                FS.verify_identity(candidate)

    def test_symlink_target_is_never_traversed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            real = root / "real"
            real.mkdir()
            link = root / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                FS.safe_delete_tree(link)
            self.assertTrue(real.exists())

    def test_hardlink_accounting_records_shared_inode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first"
            second = root / "second"
            first.write_text("shared", encoding="utf-8")
            os.link(first, second)
            self.assertEqual(FS.path_identity(first)["link_count"], 2)
            self.assertEqual(first.stat().st_ino, second.stat().st_ino)

    def test_nested_artifact_is_covered_by_safe_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            worktree = root / "worktree"
            artifact = worktree / "node_modules"
            artifact.mkdir(parents=True)
            parent = FS.candidate_base(
                worktree,
                root,
                "git_worktree",
                "git",
                {"level": "exact", "method": "retained ref"},
                {"driver": "git", "operation": "worktree_remove_preserve_branch"},
            )
            parent["classification"] = FS.CLASS_SAFE
            child = self.candidate(worktree, artifact)
            child["classification"] = FS.CLASS_SAFE
            FS.add_overlap([parent, child])
            self.assertEqual(child["covered_by"], parent["id"])

    def test_stale_manifest_is_rejected_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = {
                "schema": FS.SCHEMA,
                "generated_at": (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)).isoformat(),
                "authorization": {"mode": "goal_authorized", "scope": ["test fixture"]},
                "candidates": [],
            }
            manifest["integrity"] = {"algorithm": "sha256", "digest": FS.manifest_digest(manifest)}
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            args = argparse.Namespace(
                execute=True,
                ack=FS.ACK,
                id=["missing"],
                manifest=str(manifest_path),
                max_age_minutes=30.0,
                authorization_source="goal_authorization",
                risk_ceiling_gib=None,
                target_gib=None,
                volume=str(root),
            )
            with self.assertRaisesRegex(SystemExit, "manifest is stale"):
                FS.apply_manifest(args)

    def test_dirty_and_unique_worktrees_are_retained(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            linked = root / "linked"
            repo.mkdir()
            self.assertEqual(FS.run(["git", "-C", str(repo), "init", "-b", "main"]).returncode, 0)
            self.assertEqual(FS.run(["git", "-C", str(repo), "config", "user.name", "Lifecycle Test"]).returncode, 0)
            self.assertEqual(FS.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"]).returncode, 0)
            (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
            self.assertEqual(FS.run(["git", "-C", str(repo), "add", "tracked.txt"]).returncode, 0)
            self.assertEqual(FS.run(["git", "-C", str(repo), "commit", "-m", "base"]).returncode, 0)
            self.assertEqual(FS.run(["git", "-C", str(repo), "worktree", "add", "-b", "candidate", str(linked)]).returncode, 0)

            (linked / "tracked.txt").write_text("dirty\n", encoding="utf-8")
            dirty = next(item for item in FS.audit_worktrees(repo, [], True, []) if item.get("canonical_path") == str(linked.resolve()))
            self.assertEqual(dirty["classification"], FS.CLASS_RETAIN)
            self.assertFalse(dirty["git"]["clean"])

            self.assertEqual(FS.run(["git", "-C", str(linked), "add", "tracked.txt"]).returncode, 0)
            self.assertEqual(FS.run(["git", "-C", str(linked), "commit", "-m", "unique"]).returncode, 0)
            unique = next(item for item in FS.audit_worktrees(repo, [], True, []) if item.get("canonical_path") == str(linked.resolve()))
            self.assertEqual(unique["classification"], FS.CLASS_RETAIN)
            self.assertEqual(unique["git"]["representation"], "unique")


if __name__ == "__main__":
    unittest.main()
