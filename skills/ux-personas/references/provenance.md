# Source decisions

Created 2026-11-03. This package contains original Python harness/adapter code and instructions. It does not vendor upstream implementations, persona datasets, or research text. The comparison below is based on inspected repository documentation; only TinyTroupe's adapter API is integrated. A project's README claims are not independently reproduced results.

## Why this architecture

The existing skill library uses portable Python helpers and host-provided tools. A standard-library evidence harness keeps planning, recording, and reporting usable without a model subscription, notebook server, browser installation, or service deployment. The host's existing agent supplies persona reasoning and browser operations. TinyTroupe is an optional process boundary for deeper persona feedback; its state and dependencies do not enter normal harness execution.

The main invariant is evidence separation: study assumptions, synthetic judgments, observed browser traces, and fixture output retain distinct labels. Completion requires browser-labeled artifact evidence covering declared success criteria. This validates recording structure and artifact integrity, not authorship or semantic truth. A supervisor must inspect the actual driver evidence.

## Repositories considered

| Project | Inspected mechanism and decision |
| --- | --- |
| [Microsoft TinyTroupe](https://github.com/microsoft/TinyTroupe) | Structured `TinyPerson` personas, persistent mental state, and bounded listening/acting are a useful optional feedback engine. Implement direct Python interoperability; do not vendor the dependency tree. |
| [UXAgent](https://github.com/neuhai/UXAgent/blob/master/README.md) | Persona-based browser sessions with explicit intents, step limits, and per-run traces. Adopt the session shape; reuse the host browser rather than importing the whole research runner. |
| [Gauntlet](https://github.com/jesposito/gauntlet/blob/main/README.md) | Persona/flow separation, browser artifacts, and verification-oriented reporting informed the evidence model. Its TypeScript/Bun/provider runner remains a separate possible integration, not a dependency or claimed tested backend. |
| [UXCascade](https://github.com/ogatakatsuya/UXCascade/blob/master/README.md) | This unofficial implementation separates simulation, issue analysis, and reevaluation. Adopt comparable runs and per-session drilldown; avoid requiring its React/FastAPI/PostgreSQL/MinIO application stack. |
| [UX researcher/designer skill](https://github.com/alirezarezvani/claude-skills/tree/main/product-team/skills/ux-researcher-designer) | Research grounding and journey mapping are useful preparation. Its generic sample-size/confidence thresholds are not imported as validity rules. |
| [User Simulation](https://github.com/PabloManzoni/user-simulation/blob/main/README.md) | Reusing the host browser and separating experience from heuristic inspection fits Tometo. Add executable validation and durable run artifacts rather than importing its Claude-specific orchestration. |
| [Persona generation workflow](https://github.com/joongishin/persona-generation-workflow/blob/main/README.md) | Human grouping and LLM summarization inform persona authoring. Preserve source-linked claims and explicit assumptions; do not automatically infer demographics or import its survey dataset. |

## TinyTroupe compatibility baseline

API inspection is pinned to [commit `7ce8be378a37ee73f9745d6781452712318afa04`](https://github.com/microsoft/TinyTroupe/tree/7ce8be378a37ee73f9745d6781452712318afa04). Its [package metadata](https://github.com/microsoft/TinyTroupe/blob/7ce8be378a37ee73f9745d6781452712318afa04/pyproject.toml) declares version 0.8.1 and Python 3.10+. The package includes ordinary Python modules; notebook examples do not require a notebook-driven integration. Its declared dependencies nevertheless include Jupyter, LlamaIndex, plotting, document, and model libraries.

The adapter targets [`TinyPerson.load_specification`, `listen`, and `act`](https://github.com/microsoft/TinyTroupe/blob/7ce8be378a37ee73f9745d6781452712318afa04/tinytroupe/agent/tiny_person.py). Its deterministic tests use fakes and offline CLI subprocesses. These tests alone do not certify provider compatibility, model output quality, or human behavioral validity. Two live feedback sessions were subsequently qualified through the Codex client, as described in [runtime validation](tinytroupe.md#validation-boundary). No upstream source is copied, so the separately installed runtime retains its own license notices.

## Codex client grounding

TinyTroupe's public client registry (`tinytroupe.clients.register_client` and `force_api_type`) provides the transport seam. The adapter uses it without modifying the upstream checkout. The Codex SDK at revision `079e17a422347e49d02501304f79fade7e569362`, particularly `sdk/typescript/src/thread.ts`, `events.ts`, and the `runStreamed.test.ts` regression test, supports distinct checks for item output, turn completion, usage, and failure. Its captured event contract has no backend-resolved model field; requested model identity is therefore not presented as resolved identity.

T3 Code's `apps/server/src/textGeneration/CodexTextGeneration.ts` and its tests at revision `cefb544af3c98224874419198c0359b652ca3c94` provide useful patterns for schema/output temporary files, independent decoding after process exit, cancellation cleanup, and explicit named MCP disabling. Their configured overrides do not establish our runtime's effective configuration. Codex's configuration loader and test show that `--ignore-user-config` removes the user layer, which alone does not remove every project or managed layer. These are source-supported design decisions, not claims that either reference repository's tests were executed or that their checked-out revision matches the installed CLI binary.

The same Codex source's model catalog declares minimum client version 0.153.0 for GPT-6.1 Sol; its model-list request carries the actual client version. Local PATH selected 0.147.0 even though 0.166.0 was already installed and its authenticated catalog listed the requested model. Real TinyPerson feedback subsequently completed with 0.166.0, `gpt-6.1-sol`, and high reasoning. The adapter now accepts explicit binary selection, records the resolved executable, and reports a stale client before attempting GPT-6.1 Sol on an older known binary. Old-client rejection is not evidence that this login lacks access.
