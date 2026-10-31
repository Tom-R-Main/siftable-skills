---
name: colophon
description: Discover user-configured local Colophon voice profiles, export verified writing guidance, and check Markdown candidates while keeping profiles and source passages private.
license: MIT
---

# Colophon local profiles

Use a separately configured Colophon runtime and the user's explicit local profile registry. This package ships the adapter, documentation, and synthetic tests; it contains no author profiles, source texts, prompt excerpts, credentials, or writing-provider client.

Resolve bundled paths from this skill directory. The [runtime contract](references/runtime-contract.md) explains registry setup, supported commands, privacy boundaries, and receipt interpretation.

## Discover and export

1. Establish the document, intended reader, requested editing scope, and selected local profile. Do not silently select an author or substitute another profile. Local availability does not establish that a profile fits the genre or override the host's author-style policies.
2. Run `python3 scripts/colophon_adapter.py doctor`, then `python3 scripts/colophon_adapter.py profiles`. Discovery delegates to Colophon's native registry; it does not scan source collections, fetch a corpus, or install a runtime. Missing configuration is a setup result, not an empty author library to recreate.
3. Export guidance to an authorized private path with `python3 scripts/colophon_adapter.py prompt PROFILE --output PRIVATE_PROMPT --mode numeric --task rewrite`. Use a configured alias in place of `PROFILE`. Modes and source-passage implications are documented in the runtime contract. The adapter validates profile identity and the prompt's saved bytes before reporting success.
4. Use the saved guidance with the document's facts and the already authorized writing tool. Exporting a prompt never calls a writing model. Provider access, disclosure, and spend remain governed by the user's task; do not introduce a new approval stage when they are already authorized.

The adapter accepts `--runtime` and `--registry` before the command. Otherwise runtime lookup uses `COLOPHON_BIN` then `PATH`, and registry lookup follows Colophon's native configuration. Use the CLI's `--help` for exact syntax. Legacy single-document `.analysis.json` profiles are a different contract; do not pass them through this route.

## Edit a README or other Markdown

Follow [human-writing](../human-writing/SKILL.md) for the factual claim ledger, prose review, and text hygiene. Draft a separate candidate and preserve commands, fenced and indented code, inline identifiers, link destinations, and other immutable source material. Do not put private guidance, profile files, or source excerpts into a public documentation change.

Run `python3 scripts/colophon_adapter.py check-candidate SOURCE CANDIDATE` before applying a rewrite. This is a read-only structural check. It does not prove factual preservation, correct citations, naturalness, copying safety, accessibility, or voice fidelity; inspect the full diff and perform the relevant project checks too. Never call an unrun or failed check a pass.

Keep the original intact until the candidate passes the requested review. A mechanical guard failure is a reason to repair the candidate, not weaken the source contract. Apply or publish only within the user's authorized task.

## Report the actual result

Distinguish registry discovery, validated profile identity, exported prompt, generated candidate, structural checks, and human review. Report unavailable runtime capabilities and uncertain outputs explicitly. Preserve an uncertain artifact for inspection and reconcile it before retrying. A receipt verifies an artifact at check time, not literary quality or continued freshness.
