import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import codex_transport as transport


SCHEMA = {"type": "object", "properties": {"answer": {"type": "string", "default": ""}},
          "$defs": {"nested": {"type": "object", "properties": {"value": {"type": "string"}}}}}


class Format:
    @staticmethod
    def model_json_schema():
        return SCHEMA

    @staticmethod
    def model_validate(value):
        if set(value) != {"answer"} or not isinstance(value["answer"], str):
            raise ValueError("invalid")
        return Mock(model_dump=lambda: value)


class TransportTests(unittest.TestCase):
    def client(self, directory):
        with patch.object(transport, "select_executable", return_value={
                "executable": "/test/codex", "cli_version": "codex-cli 0.166.0",
                "selection_reason": "explicit_flag", "candidates_checked": 1}):
            return transport.CodexClient("gpt-6.1-sol", directory, 60, 1, executable="codex")

    def test_schema_is_strict_and_does_not_mutate_input(self):
        result = transport.strict_schema(Format)
        self.assertEqual(result["required"], ["answer"])
        self.assertFalse(result["additionalProperties"])
        self.assertFalse(result["$defs"]["nested"]["additionalProperties"])
        self.assertNotIn("default", result["properties"]["answer"])
        self.assertEqual(SCHEMA["properties"]["answer"]["default"], "")

    def test_transport_preserves_roles_schema_usage_and_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = self.client(tmp)
            messages = [{"role": "system", "content": "Persona"},
                        {"role": "user", "content": {"stimulus": "Page"}},
                        {"role": "assistant", "content": "Prior response"}]
            def fake_run(command, **kwargs):
                if command[1:3] == ["mcp", "list"]:
                    disabled = any(arg.startswith("mcp_servers={") for arg in command)
                    return subprocess.CompletedProcess(command, 0, json.dumps([{"name": "server.with-dot", "enabled": not disabled,
                        "transport": {"type": "stdio", "env": {"key": "SECRET"}}}]), None)
                path = Path(kwargs["cwd"])
                (path / "response.json").write_text('{"answer":"Unclear"}')
                self.assertIn(json.dumps({"messages": messages}, ensure_ascii=False), kwargs["input"])
                self.assertIn("--ignore-user-config", command)
                self.assertIn("--ephemeral", command)
                self.assertIn("read-only", command)
                self.assertIn('model_reasoning_effort="high"', command)
                self.assertIn('mcp_servers={"server.with-dot"={enabled=false,command="false"}}', command)
                self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
                self.assertEqual(command[-1], "-")
                return subprocess.CompletedProcess(command, 0,
                    json.dumps({"type": "item.completed", "item": {"type": "error", "message": "unknown field ignored"}})
                    + "\n" + json.dumps({"type": "turn.completed",
                    "usage": {"input_tokens": 30, "output_tokens": 12, "sensitive_other": "no"}}), None)
            with patch.object(transport, "run_bounded", side_effect=fake_run):
                result = client.send_message(messages, response_format=Format)
                self.assertEqual(json.loads(result["content"]), {"answer": "Unclear"})
                with self.assertRaisesRegex(transport.TransportError, "budget"):
                    client.send_message(messages, response_format=Format)
            self.assertEqual(client.get_cost_stats()["total_tokens"], 42)
            self.assertNotIn("sensitive_other", client.calls[0]["usage"])
            self.assertEqual(client.calls[0]["warning_categories"], ["configuration"])
            self.assertEqual(client.calls[0]["disabled_mcp_server_count"], 1)
            self.assertEqual(client.calls[0]["reasoning_effort"], "high")
            self.assertEqual(client.calls[0]["executable"], "/test/codex")
            self.assertEqual(client.calls[0]["selection_reason"], "explicit_flag")
            self.assertNotIn("SECRET", json.dumps(client.calls))

    def test_failure_diagnostics_never_include_raw_error(self):
        self.assertEqual(transport.failure_category("Model gpt-example is not supported. SECRET"), "unsupported_model")
        self.assertEqual(transport.failure_category("401 unauthorized SECRET"), "authentication")
        self.assertEqual(transport.failure_category("invalid JSON schema SECRET"), "schema")
        self.assertEqual(transport.failure_category("unknown field SECRET"), "configuration")

    def test_unvalidated_schema_dict_cannot_start_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = self.client(tmp)
            with patch.object(transport, "run_bounded") as run:
                with self.assertRaisesRegex(transport.TransportError, "locally validating"):
                    client.send_message([{"role": "user", "content": "Page"}], response_format=SCHEMA)
                run.assert_not_called()
            self.assertEqual(client.calls, [])
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_nonzero_malformed_and_tool_output_rejected(self):
        cases = [(1, "", None), (0, "not-json", None),
                 (0, json.dumps({"type": "item.completed", "item": {"type": "command_execution"}}), None),
                 (0, json.dumps({"type": "turn.completed"}), '{"wrong":"shape"}'),
                 (0, json.dumps({"type": "turn.completed"}), '[1,2]')]
        for code, events, response in cases:
            with self.subTest(code=code, events=events), tempfile.TemporaryDirectory() as tmp:
                client = self.client(tmp)
                def fake_run(command, **kwargs):
                    if command[1:3] == ["mcp", "list"]:
                        return subprocess.CompletedProcess(command, 0, "[]", None)
                    if response:
                        (Path(kwargs["cwd"]) / "response.json").write_text(response)
                    return subprocess.CompletedProcess(command, code, events, "SECRET")
                with patch.object(transport, "run_bounded", side_effect=fake_run):
                    with self.assertRaises(transport.TransportError) as error:
                        client.send_message([{"role": "user", "content": "Page"}], response_format=Format)
                self.assertNotIn("SECRET", str(error.exception))
                self.assertEqual(client.calls[0]["status"], "failed")

    def test_inventory_failure_refuses_model_execution(self):
        for returncode, payload in [(1, ""), (0, "not-json"), (0, "{}"), (0, '[{"name":42}]'),
                                    (0, '[{"name":"server"}]'),
                                    (0, '[{"name":"server","transport":{"type":"unknown"}}]')]:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as tmp:
                client = self.client(tmp)
                with patch.object(transport, "run_bounded", return_value=subprocess.CompletedProcess(
                        [], returncode, payload, "PRIVATE")) as run:
                    with self.assertRaisesRegex(transport.TransportError, "inventory"):
                        client.send_message([{"role": "user", "content": "Page"}], response_format=Format)
                    self.assertEqual(run.call_count, 1)
                    self.assertEqual(run.call_args.args[0][1:3], ["mcp", "list"])

    @unittest.skipUnless(sys.version_info >= (3, 11), "stdlib TOML parser requires Python 3.11")
    def test_inventory_server_names_are_quoted_toml_keys(self):
        import tomllib
        names = ['server.with.dot', 'server"quoted', 'back\\slash']
        command = transport.codex_command("codex", "model", Path("/tmp/unused"),
                                          [{"name": name, "transport": "stdio"} for name in names])
        overrides = [command[index + 1] for index, arg in enumerate(command[:-1])
                     if arg == "--config" and command[index + 1].startswith("mcp_servers=")]
        self.assertEqual(len(overrides), 1)
        self.assertEqual(list(tomllib.loads(overrides[0])["mcp_servers"]), names)
        self.assertFalse(any(arg.startswith("mcp_servers.") for arg in command))

    def test_disabled_http_placeholder_has_no_stdio_command_or_credentials(self):
        command = transport.codex_command("codex", "model", Path("/tmp/unused"),
                                          [{"name": "http-server", "transport": "streamable_http"}])
        self.assertIn('mcp_servers={"http-server"={enabled=false,url="https://disabled.invalid/"}}', command)
        self.assertFalse(any("command=" in arg for arg in command))

    def test_effective_inventory_rejects_enabled_extra_or_renamed_servers(self):
        original = [{"name": "source", "transport": {"type": "stdio"}, "enabled": True}]
        cases = [original,
                 [{"name": '"source"', "transport": {"type": "stdio"}, "enabled": False}],
                 [{"name": "source", "transport": {"type": "stdio"}, "enabled": False},
                  {"name": "extra", "transport": {"type": "stdio"}, "enabled": False}], []]
        for verified in cases:
            with self.subTest(verified=verified), tempfile.TemporaryDirectory() as tmp:
                client = self.client(tmp)
                outputs = [subprocess.CompletedProcess([], 0, json.dumps(rows), None) for rows in (original, verified)]
                with patch.object(transport, "run_bounded", side_effect=outputs) as run:
                    with self.assertRaises(transport.TransportError):
                        client.send_message([{"role": "user", "content": "Page"}], response_format=Format)
                    self.assertEqual(run.call_count, 2)
                    self.assertNotIn("disabled_mcp_server_count", client.calls[0])

    def test_reasoning_override_reaches_inventory_and_execution(self):
        self.assertIn('model_reasoning_effort="medium"', transport.safety_options("medium"))
        command = transport.codex_command("codex", "user-model", Path("/tmp/unused"), reasoning_effort="medium")
        self.assertIn('model_reasoning_effort="medium"', command)
        self.assertNotIn('model_reasoning_effort="high"', command)
        self.assertEqual(command[command.index("--model") + 1], "user-model")

    def test_timeout_marks_receipt_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = self.client(tmp)
            with patch.object(transport, "run_bounded", side_effect=subprocess.TimeoutExpired("codex", 1)) as run:
                with self.assertRaisesRegex(transport.TransportError, "timed out"):
                    client.send_message([{"role": "user", "content": "Page"}], response_format=Format)
                self.assertEqual(run.call_count, 1)
            record = json.loads((Path(tmp) / "model-call-001/transport.json").read_text())
            self.assertEqual(record["status"], "timeout")

    def test_process_group_timeout_reaps_descendant(self):
        import time
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "descendant-survived"
            child_code = "import time,pathlib;time.sleep(0.7);pathlib.Path(" + repr(str(marker)) + ").touch()"
            parent_code = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child_code) + "]);time.sleep(10)"
            with self.assertRaises(subprocess.TimeoutExpired):
                transport.run_bounded([sys.executable, "-c", parent_code], cwd=tmp, timeout=0.2)
            time.sleep(0.7)
            self.assertFalse(marker.exists())


class ExecutableSelectionTests(unittest.TestCase):
    def fake(self, root, folder, version, code=0):
        directory = root / folder
        directory.mkdir()
        executable = directory / "codex"
        executable.write_text("#!" + sys.executable + "\nimport sys\n"
                              "assert sys.argv[1:] == ['--version']\n"
                              "print(" + repr("codex-cli " + version) + ")\n"
                              "raise SystemExit(" + str(code) + ")\n")
        executable.chmod(0o700)
        return executable

    def environment(self, binaries, pin=None):
        values = {"PATH": transport.os.pathsep.join(str(path.parent) for path in binaries)}
        if pin is not None:
            values["CODEX_CLI_BIN"] = str(pin)
        return patch.dict(transport.os.environ, values, clear=True)

    def test_newer_stable_later_on_path_and_symlink_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = self.fake(root, "old", "0.147.0")
            new = self.fake(root, "new", "0.166.0")
            alias = root / "alias" / "codex"
            alias.parent.mkdir()
            alias.symlink_to(new)
            with self.environment([old, alias, new]):
                result = transport.select_executable()
            self.assertEqual(result["executable"], str(new.resolve()))
            self.assertEqual(result["cli_version"], "codex-cli 0.166.0")
            self.assertEqual(result["candidates_checked"], 2)
            self.assertEqual(result["selection_reason"], "newest_compatible_stable_on_path")

    def test_compatible_stable_preferred_to_newer_alpha(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alpha = self.fake(root, "alpha", "0.200.0-alpha.10")
            stable = self.fake(root, "stable", "0.166.0")
            with self.environment([alpha, stable]):
                self.assertEqual(transport.select_executable()["executable"], str(stable.resolve()))
            with self.environment([alpha]):
                self.assertEqual(transport.select_executable()["selection_reason"], "newest_compatible_prerelease_on_path")

    def test_explicit_and_environment_pins_never_silently_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = self.fake(root, "old", "0.147.0")
            stable = self.fake(root, "stable", "0.166.0")
            newer = self.fake(root, "newer", "0.180.0")
            with self.environment([old, stable, newer], pin=stable):
                result = transport.select_executable()
                self.assertEqual(result["executable"], str(stable.resolve()))
                self.assertEqual(result["selection_reason"], "environment_pin")
                result = transport.select_executable(str(newer))
                self.assertEqual(result["selection_reason"], "explicit_flag")
                with self.assertRaisesRegex(transport.TransportError, r"0.153.0.*--codex-bin"):
                    transport.select_executable(str(old))
            with self.environment([old, stable, newer], pin=old):
                with self.assertRaisesRegex(transport.TransportError, "0.153.0"):
                    transport.select_executable()

    def test_failed_and_unparseable_defaults_skipped_but_pins_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            failed = self.fake(root, "failed", "0.999.0", code=1)
            invalid = self.fake(root, "invalid", "unknown")
            stable = self.fake(root, "stable", "0.166.0")
            with self.environment([failed, invalid, stable]):
                self.assertEqual(transport.select_executable()["executable"], str(stable.resolve()))
                with self.assertRaisesRegex(transport.TransportError, "Pinned.*version check failed"):
                    transport.select_executable(str(failed))
            with self.environment([failed, invalid]):
                with self.assertRaisesRegex(transport.TransportError, "No working Codex CLI"):
                    transport.select_executable()

    def test_no_candidates_and_only_stale_have_actionable_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing" / "codex"
            with self.environment([missing]):
                with self.assertRaisesRegex(transport.TransportError, "CLI unavailable.*--codex-bin"):
                    transport.select_executable()
            old = self.fake(root, "old", "0.147.0")
            with self.environment([old]):
                with self.assertRaisesRegex(transport.TransportError, "No compatible.*0.153.0"):
                    transport.select_executable()


if __name__ == "__main__":
    unittest.main()
