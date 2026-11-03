#!/usr/bin/env python3
"""Offline contract and end-to-end tests; browser observations are test fixtures."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "persona_harness.py"
spec = importlib.util.spec_from_file_location("persona_harness", SCRIPT)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
EXAMPLE = SCRIPT.parent.parent / "assets" / "example-study.json"


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.study = h.read_json(EXAMPLE)
        self.run = self.root / "run"
        h.plan(self.study, self.run)
        self.sid = "first-time-editor--download-document"
        self.folder = self.run / "sessions" / self.sid

    def observation(self, step=1, source="browser", criteria=True):
        path = self.folder / f"step-{step}.txt"
        path.write_text(f"TEST FIXTURE ONLY: observed document result {step}")
        return {"step": step, "kind": "observation", "summary": "Fixture for artifact binding tests",
                "source": source, "artifacts": [str(path.relative_to(self.run))],
                "criteria": self.study["journeys"][0]["success_criteria"] if criteria else []}

    def outcome(self, status="completed", step=1):
        return {"step": step, "kind": "outcome", "summary": "Fixture verdict", "source": "model",
                "artifacts": [], "status": status}

    def test_example_valid_and_matrix_complete(self):
        h.validate_study(self.study)
        summary = h.summarize(self.run)
        self.assertEqual(summary["counts"], {"not_run": 2})
        packet = h.read_json(self.folder / "packet.json")
        self.assertEqual(packet["max_steps"], 8)
        self.assertEqual(packet["experience_mode"], "fresh")
        other = self.run / "sessions" / "keyboard-editor--download-document" / "packet.json"
        self.assertEqual(h.read_json(other)["experience_mode"], "returning")

    def test_no_overwrite(self):
        with self.assertRaises(FileExistsError):
            h.plan(self.study, self.run)

    def test_schema_rejects_unsafe_ids_and_ungrounded_personas(self):
        for field, value in (("id", "../escape"), ("assumptions", [])):
            study = deepcopy(self.study)
            study["personas"][0][field] = value
            with self.assertRaises(ValueError):
                h.validate_study(study)
        study = deepcopy(self.study)
        study["personas"][0]["constraints"]["max_steps"] = True
        with self.assertRaises(ValueError):
            h.validate_study(study)
        study = deepcopy(self.study)
        study["schema_version"] = True
        with self.assertRaises(ValueError):
            h.validate_study(study)

    def test_malformed_event_enum_values_rejected_cleanly(self):
        for key in ("kind", "source", "status"):
            event = self.outcome(status="blocked", step=0)
            event[key] = []
            with self.assertRaises(ValueError):
                h.record(self.run, self.sid, event)

    def test_global_budget_used_when_persona_budget_omitted(self):
        study = deepcopy(self.study)
        study["max_steps"] = 40
        study["personas"][0]["constraints"].pop("max_steps")
        packet = h.session_packet(study, self.sid, study["personas"][0], study["journeys"][0])
        self.assertEqual(packet["max_steps"], 40)

    def test_success_requires_observed_every_criterion(self):
        with self.assertRaisesRegex(ValueError, "every success criterion"):
            h.record(self.run, self.sid, self.outcome(step=0))
        h.record(self.run, self.sid, self.observation(criteria=False))
        with self.assertRaisesRegex(ValueError, "every success criterion"):
            h.record(self.run, self.sid, self.outcome())
        h.record(self.run, self.sid, self.observation(step=2))
        h.record(self.run, self.sid, self.outcome(step=2))
        self.assertEqual(h.summarize(self.run)["counts"], {"completed": 1, "not_run": 1})

    def test_fixture_cannot_establish_browser_success(self):
        h.record(self.run, self.sid, self.observation(source="fixture"))
        with self.assertRaisesRegex(ValueError, "every success criterion"):
            h.record(self.run, self.sid, self.outcome())
        self.assertEqual(h.summarize(self.run)["sessions"][0]["evidence_sources"], ["fixture"])

    def test_observations_need_artifacts_and_consecutive_steps(self):
        event = self.observation()
        event["artifacts"] = []
        with self.assertRaisesRegex(ValueError, "saved artifacts"):
            h.record(self.run, self.sid, event)
        with self.assertRaisesRegex(ValueError, "consecutive"):
            h.record(self.run, self.sid, self.observation(step=2))

    def test_terminal_session_cannot_resume(self):
        h.record(self.run, self.sid, self.outcome(status="blocked", step=0))
        with self.assertRaisesRegex(ValueError, "terminal"):
            h.record(self.run, self.sid, self.observation())

    def test_budget_enforced_and_missing_terminal_distinct(self):
        for step in range(1, 9):
            h.record(self.run, self.sid, self.observation(step, criteria=False))
        self.assertEqual(h.summarize(self.run)["sessions"][0]["status"], "budget_exhausted_unclosed")
        with self.assertRaisesRegex(ValueError, "budget"):
            h.record(self.run, self.sid, self.observation(9))
        h.record(self.run, self.sid, self.outcome("budget_exhausted", 8))

    def test_cross_session_and_symlink_artifacts_refused(self):
        event = self.observation()
        outside = self.root / "outside.txt"
        outside.write_text("outside")
        link = self.folder / "link.txt"
        link.symlink_to(outside)
        event["artifacts"] = [str(link.relative_to(self.run))]
        with self.assertRaises(ValueError):
            h.record(self.run, self.sid, event)
        other = self.run / "sessions" / "keyboard-editor--download-document" / "evidence.txt"
        other.write_text("other persona")
        event["artifacts"] = [str(other.relative_to(self.run))]
        with self.assertRaises(ValueError):
            h.record(self.run, self.sid, event)

    def test_report_detects_artifact_changes_and_event_tampering(self):
        event = self.observation()
        h.record(self.run, self.sid, event)
        artifact = self.run / event["artifacts"][0]
        original = artifact.read_text()
        artifact.write_text("changed")
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            h.summarize(self.run)
        artifact.write_text(original)
        events = self.folder / "events.jsonl"
        row = json.loads(events.read_text())
        row["session_id"] = "someone-else"
        events.write_text(json.dumps(row) + "\n")
        with self.assertRaisesRegex(ValueError, "identity"):
            h.summarize(self.run)

    def test_packet_changes_rejected(self):
        packet = h.read_json(self.folder / "packet.json")
        packet["max_steps"] = 100
        h.write_json(self.folder / "packet.json", packet)
        with self.assertRaisesRegex(ValueError, "packet differs"):
            h.summarize(self.run)

    def test_symlink_session_directory_cannot_write_outside_run(self):
        outside = self.root / "outside-session"
        self.folder.rename(outside)
        self.folder.symlink_to(outside, target_is_directory=True)
        original = (outside / "events.jsonl").read_bytes()
        with self.assertRaisesRegex(ValueError, "symlinks"):
            h.record(self.run, self.sid, self.outcome("blocked", 0))
        with self.assertRaisesRegex(ValueError, "symlinks"):
            h.summarize(self.run)
        self.assertEqual((outside / "events.jsonl").read_bytes(), original)
        self.assertFalse((outside / ".record-lock").exists())

    def test_symlink_sessions_ancestor_rejected(self):
        outside = self.root / "outside-sessions"
        sessions = self.run / "sessions"
        sessions.rename(outside)
        sessions.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            h.record(self.run, self.sid, self.outcome("blocked", 0))
        with self.assertRaisesRegex(ValueError, "symlinks"):
            h.compare(self.run, self.run)

    def test_symlink_metadata_and_writer_paths_rejected(self):
        for name in ("manifest.json", "packet.json", "packet.md", "events.jsonl", ".record-lock", ".events.tmp"):
            with self.subTest(name=name):
                path = self.run / name if name == "manifest.json" else self.folder / name
                outside = self.root / (name.replace(".", "-") + "-target")
                saved = path.read_bytes() if path.exists() else None
                if saved is not None:
                    path.rename(outside)
                elif name == ".record-lock":
                    outside.mkdir()
                else:
                    outside.write_text("untouched")
                path.symlink_to(outside, target_is_directory=outside.is_dir())
                try:
                    before = outside.read_bytes() if outside.is_file() else None
                    with self.assertRaisesRegex(ValueError, "symlinks"):
                        h.record(self.run, self.sid, self.outcome("blocked", 0))
                    with self.assertRaisesRegex(ValueError, "symlinks"):
                        h.summarize(self.run)
                    if before is not None:
                        self.assertEqual(outside.read_bytes(), before)
                finally:
                    path.unlink()
                    if saved is not None:
                        outside.rename(path)

    def test_canonical_parent_alias_is_allowed(self):
        alias = self.root / "parent-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertEqual(h.summarize(alias / "run")["counts"], {"not_run": 2})

    def test_compare_handles_missing_sessions_and_equivalent_preview_origin(self):
        study = deepcopy(self.study)
        study["target"]["revision"] = "new-version"
        study["journeys"][0]["start_url"] = "https://preview.example.test/"
        newer = self.root / "newer"
        h.plan(study, newer)
        result = h.compare(self.run, newer)
        self.assertFalse(result["sessions"][0]["comparable"])
        self.assertIsNone(result["sessions"][0]["step_delta"])

    def test_compare_rejects_changed_memory_and_start_path(self):
        for change in ("memory", "path"):
            study = deepcopy(self.study)
            if change == "memory":
                study["personas"][0]["prior_experience"] = ["Now knows the solution"]
            else:
                study["journeys"][0]["start_url"] += "direct-download"
            newer = self.root / change
            h.plan(study, newer)
            with self.assertRaisesRegex(ValueError, "incompatible"):
                h.compare(self.run, newer)

    def test_compare_candidate_regression_and_report(self):
        h.record(self.run, self.sid, self.observation())
        h.record(self.run, self.sid, self.outcome())
        baseline = self.run
        self.run = self.root / "newer"
        study = deepcopy(self.study)
        study["target"]["revision"] = "newer"
        h.plan(study, self.run)
        self.folder = self.run / "sessions" / self.sid
        h.record(self.run, self.sid, self.observation(criteria=False))
        h.record(self.run, self.sid, self.outcome("abandoned"))
        result = h.compare(baseline, self.run)
        self.assertTrue(result["sessions"][0]["candidate_regression"])
        destination = self.root / "report"
        h.report(self.run, destination)
        report = h.read_json(destination / "report.json")
        self.assertEqual(report["counts"], {"abandoned": 1, "not_run": 1})
        self.assertIn("not independently authenticated", (destination / "report.md").read_text())

    def test_cli_round_trip_and_invalid_json(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "validate", str(EXAMPLE)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["sessions"], 2)
        bad = self.root / "bad.json"
        bad.write_text("{")
        result = subprocess.run([sys.executable, str(SCRIPT), "validate", str(bad)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
