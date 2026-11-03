# Optional TinyTroupe backend

TinyTroupe is a Python library with notebook examples. This adapter uses its Python API directly, so the operator does not need to run a notebook. Upstream still declares Jupyter and a substantial collection of model, retrieval, plotting, and document dependencies. Keep it in a separate project environment when needed; the main harness remains standard-library-only.

## Offline operations

Use the installed skill directory as `UX_PERSONAS_DIR`:

```bash
python3 "$UX_PERSONAS_DIR/scripts/run_feedback.py" doctor
python3 "$UX_PERSONAS_DIR/scripts/run_feedback.py" export study.json \
  --persona first-time-editor --output editor-tinyperson.json
```

`doctor` reads distribution metadata without importing TinyTroupe or initializing its clients. It reports version compatibility and whether an installation's VCS metadata matches the inspected commit. This is availability evidence, not a provider health check. `export` converts the selected validated persona into a native `TinyPerson` specification without model calls. It excludes executable faculties and runtime memory.

## Headless feedback

Use an approved environment containing TinyTroupe 0.8.1 and either a logged-in Codex CLI or an already configured OpenAI provider. See the [compatibility baseline](provenance.md#tinytroupe-compatibility-baseline) for the inspected commit and upstream installation documentation. The skill does not install packages, acquire credentials, or authorize spend. Configure credentials through the environment's normal opaque credential route; never copy their values into study or stimulus files.

After model execution is authorized, supply a reviewed text description of the concept or screen:

```bash
python3 "$UX_PERSONAS_DIR/scripts/run_feedback.py" simulate study.json \
  --persona first-time-editor --stimulus screen-description.txt --output ux-feedback-v1 \
  --provider codex --max-turns 1 --timeout-seconds 120 \
  --allow-model-calls
```

The command requires a fresh output directory and starts a separate process there. It loads the persona with saved faculties, memory, and mental state suppressed, delivers the stimulus, and requests bounded action turns. The process has a wall-clock deadline; automatic adapter retry is disabled. Turn and deadline limits are not an exact token, request-count, or billing guarantee. Version 0.8.1 compatibility does not establish source-commit identity; inspect `doctor` if reproducibility requires the exact pin.

The isolated process does not load a parent project's `config.ini`. The OpenAI path uses package defaults, the explicit model and bounds, and inherited opaque credential environment. Custom endpoints or provider choices held only in a project configuration file are not carried over. The Codex path uses a registered custom client instead of TinyTroupe's OpenAI client; embedding-based faculties and memory remain disabled in this feedback profile.

The default model is `gpt-6.1-sol` with `high` reasoning, as explicitly requested. Override with `--model` and `--reasoning-effort` when desired. Unavailable models fail explicitly; the adapter does not substitute another model.

To use the existing Codex login instead of an OpenAI API key, add `--provider codex` as above. The selected model must be available to that login. TinyTroupe remains the persona engine: the custom client sends its complete message history to a fresh headless `codex exec` invocation and returns the structured response to TinyTroupe's action parser. The OpenAI path remains available with `--provider openai` and a provider-compatible model selection.

The Codex transport uses an ephemeral, read-only invocation with user configuration disabled, structured final output, and a deadline. Authentication stays with Codex; the adapter does not read or copy login files. Separate invocations receive only the explicit TinyTroupe message history. User/project or managed settings can still affect an installed CLI; a fresh process is not proof of an otherwise instruction-free model. Tool-event rejection detects an unexpected operation after it is reported and is not a universal prevention guarantee. Transport receipts record the CLI/model and invocation outcomes for review. See [Codex noninteractive commands](https://learn.chatgpt.com/docs/developer-commands#codex-exec) for the CLI interface.

Before model execution, the transport lists configured MCP servers and adds explicit named disabling overrides. An inventory error stops execution. Only the count is recorded; configuration values and server names are not copied into feedback. This is a static preflight, not a proof against every managed or dynamically changing tool surface.

`request.json` records the supplied inputs; `status.json` records completion, timeout, or backend failure. A successful run writes `feedback.json`, explicitly marked `synthetic_feedback`, `browser_executed: false`, and `task_completion: not_evaluated`. Provider output is suppressed to avoid leaking client configuration or exception bodies. Retain only inputs you are authorized to send and store.

Use the transcript to identify hypotheses and interview questions. To add a relevant reaction to a browser run, record a `model` judgment with a copied transcript artifact inside that session. Never convert TinyTroupe's narrative into a browser observation or task-completion event. It does not browse the product or independently establish accessibility, user frustration, or conversion.

## Validation boundary

The bundled tests check the native specification mapping, adapter calls with fakes, explicit execution gate, timeout/process cleanup, offline operation, and Codex response handling. A passing mock test does not mean the provider-backed runtime was exercised.

On November 3, 2026, two actual TinyTroupe 0.8.1 `TinyPerson` sessions completed through ChatGPT-authenticated Codex CLI 0.166.0 with `gpt-6.1-sol` and high reasoning. Each produced one `TALK` action via one CLI invocation. Both passed the effective MCP inventory check. The test used a supplied screen description, not browser navigation, and does not establish persona realism or human usability. CLI JSON did not report a separate backend-resolved model field; configured model identity remains labeled as such.

An earlier PATH-selected CLI 0.147.0 rejected the model, while the already installed compatible 0.166.0 listed it and ran it successfully under the same login. The earlier rejection was a client-version problem; it did not establish missing account access.

## Selecting the CLI binary

Without a binary override, the transport inspects Codex executables on PATH, deduplicates their resolved paths, and selects the newest compatible stable version. A compatible prerelease is considered only when no compatible stable client exists. Use `--codex-bin /path/to/codex` or `CODEX_CLI_BIN` to pin an executable; explicit CLI selection takes precedence over the environment, and either pin is honored even when incompatible, producing a clear error rather than silently selecting another binary. Model and reasoning choices remain separate. The adapter records the chosen executable and version. It does not change the global PATH or install/upgrade Codex automatically.

The inspected model catalog requires Codex 0.153.0 or later for GPT-6.1 Sol. An older binary can show a different live model catalog under the same login. Check visible CLI executables and their versions before concluding the account lacks model access. An explicit incompatible binary fails with a stale-client error; model selection does not silently fall back.

## Installation runtime

The standard-library launcher reads an optional `.ux-personas-runtime.json` in the skill discovery root, beside the `ux-personas` directory, containing `{"python": "/path/to/approved/venv/bin/python"}`. This file is local setup, not a public-package credential or bundled runtime. `UX_PERSONAS_PYTHON` overrides it. With neither configured, the launcher uses its current interpreter. Keep the runtime available for subsequent tasks; if it moves, update the local pointer. The launcher forwards the backend's status and does not install dependencies.
