import importlib.metadata
import json
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tinytroupe_backend as backend


def study():
    return {"schema_version": 1, "id": "sample", "product": "Example",
            "target": {"revision": "v1"},
            "personas": [{"id": "new", "name": "Newcomer", "goals": ["Find a plan"],
                          "knowledge": ["Never used this app"],
                          "constraints": {"max_steps": 3}, "evidence": [],
                          "assumptions": ["Price-sensitive"], "prior_experience": []}],
            "journeys": [{"id": "plans", "goal": "Find a plan", "start_url": "https://example.test",
                          "success_criteria": ["Plan price is visible"], "initial_state": "Fresh visitor"}]}


class BackendTests(unittest.TestCase):
    def test_doctor_does_not_import_runtime(self):
        with patch.object(importlib.metadata, "distribution",
                          side_effect=importlib.metadata.PackageNotFoundError), \
                patch.dict(sys.modules, {"tinytroupe": None}):
            self.assertEqual(backend.doctor()["installed"], False)

    def test_doctor_checks_version_and_source_without_showing_url(self):
        dist = Mock(version="0.8.1")
        dist.read_text.return_value = json.dumps({"url": "PRIVATE", "vcs_info": {
            "commit_id": backend.UPSTREAM_COMMIT}})
        with patch.object(importlib.metadata, "distribution", return_value=dist):
            result = backend.doctor()
        self.assertTrue(result["commit_matches"])
        self.assertTrue(result["version_supported"])
        self.assertNotIn("PRIVATE", json.dumps(result))

    def test_export_is_native_spec_without_executable_state(self):
        persona = study()["personas"][0]
        persona.update({"mental_faculties": [{"type": "ExternalTool"}], "gender": "do not infer"})
        spec = json.loads(json.dumps(backend.export_spec(persona)))
        self.assertEqual(set(spec), {"type", "persona"})
        self.assertEqual(spec["type"], "TinyPerson")
        self.assertEqual(spec["persona"]["name"], "Newcomer")
        self.assertEqual(spec["persona"]["long_term_goals"], persona["goals"])
        self.assertNotIn("gender", spec["persona"])
        self.assertIn("Unvalidated assumption: Price-sensitive", spec["persona"]["other_facts"])

    def test_feedback_contract_and_early_done(self):
        person = Mock()
        person.act.side_effect = [[{"action": {"type": "TALK", "content": "Unclear"}}],
                                  [{"action": {"type": "DONE", "content": ""}}]]
        tiny = Mock()
        tiny.load_specification.return_value = person
        config = Mock()
        request = {"specification": backend.export_spec(study()["personas"][0]),
                   "model": "example-model", "max_turns": 4, "timeout_seconds": 10,
                   "stimulus": "A pricing page", "persona_id": "new", "study_sha256": "abc"}
        result = backend.perform_feedback(request, config, tiny)
        self.assertEqual(person.act.call_count, 2)
        self.assertFalse(result["browser_executed"])
        self.assertEqual(result["task_completion"], "not_evaluated")
        self.assertEqual(result["kind"], "synthetic_feedback")
        self.assertFalse(person.action_generator.enable_multi_action_output)
        tiny.load_specification.assert_called_once_with(request["specification"],
            suppress_mental_faculties=True, suppress_memory=True, suppress_mental_state=True)
        person.act.assert_called_with(until_done=False, n=1, return_actions=True,
                                      communication_display=False)
        self.assertFalse(config.update_multiple.call_args.args[0]["enable_memory_consolidation"])

    def test_live_call_requires_authorization_before_any_import_or_write(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(backend, "doctor") as doctor:
            output = Path(tmp) / "run"
            with self.assertRaisesRegex(ValueError, "allow-model-calls"):
                backend.simulate(study(), "new", "Page", output, "model", 1, 10)
            self.assertFalse(output.exists())
            doctor.assert_not_called()

    def test_timeout_records_failure_without_leaking_provider_output(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(backend, "doctor", return_value={"version_supported": True}), \
                patch.object(backend, "run_bounded", side_effect=subprocess.TimeoutExpired("backend", 1)) as run:
            output = Path(tmp) / "run"
            with self.assertRaisesRegex(ValueError, "timeout"):
                backend.simulate(study(), "new", "Page", output, "model", 1, 1, True)
            self.assertEqual(json.loads((output / "status.json").read_text())["status"], "timeout")
            self.assertFalse((output / "feedback.json").exists())
            self.assertEqual(run.call_args.kwargs["cwd"], output.resolve())
            self.assertEqual(run.call_count, 1)

    def test_export_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "persona.json"
            backend.write_new(output, {"first": True})
            with self.assertRaises(FileExistsError):
                backend.write_new(output, {"second": True})
            self.assertEqual(json.loads(output.read_text()), {"first": True})

    def test_offline_export_cli_uses_shared_study_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "study.json", Path(tmp) / "persona.json"
            source.write_text(json.dumps(study()))
            command = [sys.executable, str(Path(backend.__file__)), "export", str(source),
                       "--persona", "new", "--output", str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text()),
                             backend.export_spec(study()["personas"][0]))
            self.assertFalse(json.loads(result.stdout)["model_calls"])

    def test_simulate_cli_defaults_and_explicit_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, stimulus = Path(tmp) / "study.json", Path(tmp) / "screen.txt"
            source.write_text(json.dumps(study()))
            stimulus.write_text("A source connection screen")
            common = ["simulate", str(source), "--persona", "new", "--stimulus", str(stimulus),
                      "--output", str(Path(tmp) / "run"), "--allow-model-calls"]
            with patch.object(backend, "simulate", return_value={}) as simulate, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(backend.main(common), 0)
                self.assertEqual(simulate.call_args.args[4], "gpt-6.1-sol")
                self.assertEqual(simulate.call_args.args[-3:], ("codex", "high", None))
                self.assertEqual(backend.main(common + ["--model", "user-model", "--reasoning-effort", "medium",
                                                       "--provider", "openai", "--codex-bin", "/explicit/codex"]), 0)
                self.assertEqual(simulate.call_args.args[4], "user-model")
                self.assertEqual(simulate.call_args.args[-3:], ("openai", "medium", "/explicit/codex"))

    def test_invalid_budgets_refused_before_runtime(self):
        with patch.object(backend, "doctor") as doctor:
            for turns, timeout in [(0, 10), (11, 10), (1, 0), (1, 601)]:
                with self.assertRaises(ValueError):
                    backend.simulate(study(), "new", "Page", "/unused", "model", turns, timeout, True)
            doctor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
