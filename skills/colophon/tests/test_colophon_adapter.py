"""Public CLI checks use synthetic profiles and an offline fake native runtime."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "colophon_adapter.py"
FAKE = r'''#!/usr/bin/env python3
import hashlib,json,os,pathlib,sys,time
args=sys.argv[1:]
mode=os.environ.get('COLOPHON_FAKE_MODE','')
if os.environ.get('FAKE_CALL_LOG'):
 with open(os.environ['FAKE_CALL_LOG'],'a') as out:out.write(json.dumps(args)+'\n')
if '--help' in args:
 if mode=='missing_resolve' and args[:3]==['voice','profiles','resolve']:sys.exit(2)
 print('--registry --receipt --mode --task --output');sys.exit(0)
def digest(data):return hashlib.sha256(data).hexdigest()
def fail(code):
 print(json.dumps({'status':'error','error':{'code':code,'message':'PRIVATE CONTENT SHOULD NOT LEAK'}}));sys.exit(1)
if args[:2]==['voice','profiles']:
 registry=args[args.index('--registry')+1] if '--registry' in args else os.environ.get('COLOPHON_PROFILES_FILE')
 if not registry or not pathlib.Path(registry).exists():
  print(json.dumps({'schema_version':1,'status':'not_configured','profiles':[]}));sys.exit(0)
 try:
  data=json.loads(pathlib.Path(registry).read_text())
  if data.get('schema_version')!=1 or not isinstance(data.get('profiles'),dict):raise ValueError()
 except Exception:fail('invalid_registry')
 if args[2]=='list':
  print(json.dumps({'schema_version':1,'status':'configured','profiles':[{'name':name,'kind':'VoiceProfile'} for name in data['profiles']]}));sys.exit(0)
 name=args[3]
 if name not in data['profiles']:fail('profile_not_found')
 path=pathlib.Path(data['profiles'][name]['path'])
 try:raw=path.read_bytes();profile=json.loads(raw)
 except Exception:fail('invalid_voice_profile')
 print(json.dumps({'schema_version':1,'status':'resolved','name':name,'kind':'VoiceProfile','profile_path':os.environ.get('FAKE_PROFILE_PATH',str(path)),'profile_id':profile.get('profile_id'),'profile_sha256':digest(raw),'language':'en','documents':0}));sys.exit(0)
if args[:2]!=['voice','prompt']:fail('unknown_command')
if mode=='timeout':time.sleep(15)
if mode=='large_output':print('X'*300000);sys.exit(0)
profile_path=pathlib.Path(args[2]);source=profile_path.read_bytes();profile=json.loads(source)
target=pathlib.Path(args[args.index('-o')+1]);content=b'Synthetic local writing guidance.\n'
target.write_bytes(content)
if mode=='source_drift':profile_path.write_bytes(source+b' ')
record={'schema_version':'1','status':'written','target_path':str(target),'artifact':{'bytes':len(content),'sha256':digest(content)},'source_profile':{'id':profile.get('profile_id'),'path':str(profile_path),'sha256':digest(source)},'mode':args[args.index('--mode')+1],'task':args[args.index('--task')+1]}
if mode=='wrong_hash':record['artifact']['sha256']='0'*64
if mode=='wrong_source':record['source_profile']['sha256']='0'*64
if mode=='wrong_mode':record['mode']='exemplars'
if mode in ('unknown','native_unknown'):
 record['status']='unknown'
 if mode=='native_unknown':record['error']='PRIVATE CONTENT SHOULD NOT LEAK'
if mode=='no_json':print('PRIVATE CONTENT SHOULD NOT LEAK');sys.exit(1)
print(json.dumps(record))
if mode in ('unknown','native_unknown'):sys.exit(1)
'''


def profile():
    return {"schema_version": "1", "extractor_version": "1", "profile_id": "synthetic-v1",
            "author": "Synthetic fixture", "language": "en", "corpus_hash": "a" * 64,
            "config_hash": "b" * 64, "documents": [], "numerical": {}, "traits": [],
            "exemplars": [], "corrections": [], "warnings": [], "limitations": []}


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="colophon-adapter-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.project = self.root / "project"; self.project.mkdir()
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        self.private = self.root / "private"; self.private.mkdir()
        self.voice = self.private / "synthetic.voice.json"
        self.voice.write_text(json.dumps(profile()))
        self.registry = self.private / "profiles.json"
        self.registry.write_text(json.dumps({"schema_version": 1, "profiles": {"my-docs": {"path": str(self.voice)}}}))
        self.runtime = self.root / "fake-colophon"
        self.runtime.write_text(FAKE.replace("#!/usr/bin/env python3", "#!" + sys.executable, 1))
        self.runtime.chmod(0o755)
        self.log = self.root / "calls.jsonl"
        self.output = self.private / "prompt.txt"
        self.env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "FAKE_CALL_LOG": str(self.log)}
        self.env.pop("COLOPHON_BIN", None)
        self.env.pop("COLOPHON_PROFILES_FILE", None)
        self.env.pop("COLOPHON_FAKE_MODE", None)
        self.env.pop("FAKE_PROFILE_PATH", None)

    def cli(self, *arguments, mode=None, registry=True, runtime=True, extra_env=None, cwd=None):
        command = [sys.executable, "-B", str(SCRIPT)]
        if runtime:command += ["--runtime", str(self.runtime)]
        if registry:command += ["--registry", str(self.registry)]
        env = dict(self.env)
        if mode:env["COLOPHON_FAKE_MODE"] = mode
        if extra_env:env.update(extra_env)
        result = subprocess.run([*command, *map(str, arguments)], cwd=cwd or self.project, env=env,
                                capture_output=True, text=True, timeout=20)
        self.assertNotIn("PRIVATE CONTENT", result.stdout + result.stderr)
        return result.returncode, json.loads(result.stdout)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def prompt(self, *extra, **kwargs):
        return self.cli("prompt", "my-docs", "--output", self.output, *extra, **kwargs)

    def test_discovery_and_doctor_delegate_native_registry(self):
        code, listing = self.cli("profiles")
        self.assertEqual(code, 0)
        self.assertEqual(listing, {"status": "configured", "profiles": [{"name": "my-docs", "kind": "VoiceProfile"}]})
        code, result = self.cli("doctor")
        self.assertEqual((code, result["status"], result["profiles"]), (0, "ready", 1))
        self.assertTrue(all(call[:2] == ["voice", "profiles"] or "--help" in call for call in self.calls()))
        self.assertEqual(self.voice.read_text(), json.dumps(profile()))

    def test_native_default_registry_and_missing_registry(self):
        code, result = self.cli("profiles", registry=False)
        self.assertEqual((code, result["status"]), (0, "not_configured"))
        code, result = self.cli("profiles", registry=False, extra_env={"COLOPHON_PROFILES_FILE": str(self.registry)})
        self.assertEqual((code, result["status"]), (0, "configured"))

    def test_registry_path_hops_reach_native_validator_unchanged(self):
        intermediate = self.project / "registry-link"
        intermediate.symlink_to(self.private, target_is_directory=True)
        subprocess.run(["git", "-C", str(self.project), "add", "registry-link"], check=True)
        external = self.root / "external-registry-link"
        external.symlink_to(intermediate, target_is_directory=True)
        self.registry = external / "profiles.json"
        # This fake checks dispatch only; real native tests establish refusal
        # of the tracked intermediate hop before any registry content read.
        self.cli("profiles")
        call = self.calls()[-1]
        self.assertEqual(call[call.index("--registry") + 1], str(self.registry))

    def test_prompt_output_does_not_hide_a_tracked_intermediate_symlink(self):
        intermediate = self.project / "private-output-link"
        intermediate.symlink_to(self.private, target_is_directory=True)
        subprocess.run(["git", "-C", str(self.project), "add", "private-output-link"], check=True)
        external = self.root / "external-output-link"
        external.symlink_to(intermediate, target_is_directory=True)
        self.output = external / "new.prompt.txt"
        original = self.voice.read_bytes()
        code, result = self.prompt()
        self.assertEqual((code, result["error_code"]), (1, "output_symlink_component"))
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.private / "new.prompt.txt").exists())
        self.assertEqual(self.voice.read_bytes(), original)

    def test_missing_runtime_and_invalid_registry_are_honest(self):
        code, result = self.cli("doctor", runtime=False, extra_env={"PATH": str(self.root / "missing")})
        self.assertEqual((code, result["status"], result["error_code"]), (1, "unavailable", "runtime_unavailable"))
        self.registry.write_text('{"profiles": []}')
        code, result = self.cli("profiles")
        self.assertEqual((code, result["error_code"]), (1, "native_invalid_registry"))

    def test_doctor_requires_resolve_command(self):
        code, result = self.cli("doctor", mode="missing_resolve")
        self.assertEqual((code, result["status"], result["error_code"]),
                         (1, "unavailable", "runtime_contract_unavailable"))

    def test_prompt_receipt_binds_source_and_artifact(self):
        before = self.voice.read_bytes()
        code, result = self.prompt()
        self.assertEqual((code, result["status"]), (0, "written"))
        self.assertEqual(result["generation"], "not_performed")
        self.assertEqual(result["mode"], "numeric")
        self.assertEqual(result["source_profile"]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(result["artifact"]["sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.voice.read_bytes(), before)
        self.assertEqual(set(result["quality_dimensions"].values()), {"unverified"})
        self.assertEqual(self.calls()[-1][:2], ["voice", "prompt"])

    def test_receipt_mismatch_unknown_and_source_drift_do_not_publish(self):
        for mode in ("wrong_hash", "wrong_source", "wrong_mode", "unknown", "native_unknown", "source_drift"):
            with self.subTest(mode=mode):
                code, result = self.prompt(mode=mode)
                self.assertEqual(code, 1)
                self.assertEqual(result["status"], "unknown")
                self.assertFalse(self.output.exists())
                self.assertIn("recovery_path", result)
                shutil.rmtree(result["recovery_path"])
                self.voice.write_text(json.dumps(profile()))

    def test_output_exists_before_any_runtime_call(self):
        self.output.write_text("retain")
        code, result = self.prompt()
        self.assertEqual((code, result["error_code"]), (1, "output_exists"))
        self.assertEqual(self.output.read_text(), "retain")
        self.assertEqual(self.calls(), [])

    def test_failure_and_timeout_do_not_publish_or_retry(self):
        for mode in ("no_json", "timeout", "large_output"):
            with self.subTest(mode=mode):
                prior = len(self.calls())
                code, result = self.prompt("--timeout", ".1" if mode == "timeout" else "5", mode=mode)
                self.assertEqual(code, 1)
                self.assertFalse(self.output.exists())
                self.assertEqual(len(self.calls()) - prior, 2)
                if "recovery_path" in result:shutil.rmtree(result["recovery_path"])

    def test_registry_and_profiles_must_be_private_regular_files(self):
        self.registry = self.project / "profiles.json"
        self.registry.write_text(json.dumps({"schema_version": 1, "profiles": {}}))
        code, result = self.cli("profiles")
        self.assertEqual((code, result["error_code"]), (1, "private_artifact_not_ignored"))
        (self.project / ".gitignore").write_text("profiles.json\nlocal/\n")
        code, result = self.cli("profiles")
        self.assertEqual(code, 0)
        subprocess.run(["git", "-C", str(self.project), "add", "-f", "profiles.json"], check=True)
        code, result = self.cli("profiles")
        self.assertEqual((code, result["error_code"]), (1, "private_artifact_tracked"))

    def test_ignored_local_profiles_and_prompt_are_allowed(self):
        local = self.project / "local"; local.mkdir()
        (self.project / ".gitignore").write_text("local/\n")
        self.voice.rename(local / "synthetic.voice.json")
        self.voice = local / "synthetic.voice.json"
        self.registry.write_text(json.dumps({"schema_version": 1, "profiles": {"my-docs": {"path": str(self.voice)}}}))
        self.output = local / "prompt.txt"
        code, result = self.prompt()
        self.assertEqual((code, result["status"]), (0, "written"))

    def test_broken_active_git_state_is_not_treated_as_private(self):
        shutil.rmtree(self.project / ".git")
        (self.project / ".git").write_text("gitdir: missing-registration\n")
        code, result = self.cli("profiles")
        self.assertEqual((code, result["error_code"]), (1, "git_privacy_check_failed"))
        self.assertEqual(self.calls(), [])

    def test_profile_inside_any_installed_skill_is_refused(self):
        public_file = SCRIPT.parents[2] / "human-writing" / "SKILL.md"
        code, result = self.prompt(extra_env={"FAKE_PROFILE_PATH": str(public_file)})
        self.assertEqual((code, result["error_code"]), (1, "private_artifact_in_skill_tree"))
        self.assertFalse(self.output.exists())

    def test_nested_ignore_does_not_hide_tracking_in_outer_git_checkout(self):
        inner = self.project / "inner"; inner.mkdir()
        local = inner / "local"; local.mkdir()
        self.registry = local / "profiles.json"
        self.registry.write_text(json.dumps({"schema_version": 1, "profiles": {}}))
        subprocess.run(["git", "-C", str(self.project), "add", "inner/local/profiles.json"], check=True)
        subprocess.run(["git", "init", "-q", str(inner)], check=True)
        (inner / ".gitignore").write_text("local/\n")
        code, result = self.cli("profiles", cwd=self.private)
        self.assertEqual((code, result["error_code"]), (1, "private_artifact_tracked"))
        self.assertEqual(self.calls(), [])

    def test_symlink_secret_and_nonignored_profile_are_refused(self):
        original = self.voice
        for name, symlink in (("alias.voice.json", True), (".env.voice.json", False), ("public.voice.json", False)):
            with self.subTest(name=name):
                path = self.private / name if name != "public.voice.json" else self.project / name
                if symlink:path.symlink_to(original)
                else:path.write_text(original.read_text())
                self.registry.write_text(json.dumps({"schema_version": 1, "profiles": {"my-docs": {"path": str(path)}}}))
                code, result = self.prompt()
                self.assertEqual(code, 1)
                self.assertIn(result["error_code"], {"symlink_refused", "secret_path_refused", "private_artifact_not_ignored"})
                self.assertFalse(self.output.exists())

    def test_markdown_guard_allows_prose_changes_and_rejects_technical_edits(self):
        source = self.project / "README.md"
        candidate = self.project / "candidate.md"
        text = '# Guide\n\nOriginal prose with `name()` and [label](https://example.invalid/a_(b)).\n\n```sh\nrun --flag\n```\n\n![image](asset.png)\n[ref]: docs/guide.md "title"\nUse [label][ref], [ref], and [ref][].\n[![badge](badge.png)](badge-target)\n'
        source.write_text(text)
        candidate.write_text(text.replace("Original prose", "Clearer prose").replace("[label]", "[helpful label]", 1))
        code, result = self.cli("check-candidate", source, candidate, runtime=False, registry=False)
        self.assertEqual((code, result["status"]), (0, "preserved"))
        for old, new in (("name()", "other()"), ("run --flag", "run --other"), ("asset.png", "other.png"),
                         ("a_(b)", "c"), ('docs/guide.md', 'docs/other.md'), ("[label][ref]", "[label][wrong]"),
                         ("and [ref][]", "and [wrong][]"), (", [ref],", ", [wrong],"), ("badge-target", "wrong-target"),
                         ("Original prose", "Original prose `new()`")):
            candidate.write_text(text.replace(old, new))
            code, result = self.cli("check-candidate", source, candidate, runtime=False, registry=False)
            self.assertEqual((code, result["status"]), (1, "rejected"), (old, result))
            self.assertEqual(source.read_text(), text)

    def test_indented_commands_are_guarded_conservatively(self):
        source = self.project / "README.md"
        candidate = self.project / "candidate.md"
        for indent in ("    ", "\t"):
            with self.subTest(indent=repr(indent)):
                text = f"Paragraph.\n\n{indent}run --dry-run\n\n{indent}next --check\n\nFinal prose.\n"
                source.write_text(text)
                candidate.write_text(text.replace("--dry-run", "--live"))
                code, result = self.cli("check-candidate", source, candidate, runtime=False, registry=False)
                self.assertEqual((code, result["status"]), (1, "rejected"))
                candidate.write_text(text.replace("Final prose", "Revised final prose"))
                code, result = self.cli("check-candidate", source, candidate, runtime=False, registry=False)
                self.assertEqual((code, result["status"]), (0, "preserved"))

    @unittest.skipUnless(os.environ.get("COLOPHON_TEST_BIN"), "set COLOPHON_TEST_BIN for an explicitly selected native runtime")
    def test_real_native_runtime_with_synthetic_profile(self):
        self.runtime = Path(os.environ["COLOPHON_TEST_BIN"])
        code, readiness = self.cli("doctor")
        self.assertEqual((code, readiness["status"], readiness["profiles"]), (0, "ready", 1), readiness)
        code, result = self.prompt()
        self.assertEqual((code, result["status"]), (0, "written"), result)
        self.assertEqual(result["source_profile"]["id"], "synthetic-v1")
        self.assertEqual(result["generation"], "not_performed")


if __name__ == "__main__":
    unittest.main()
