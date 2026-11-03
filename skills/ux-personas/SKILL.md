---
name: ux-personas
description: "Build persistent, evidence-grounded UX personas and run bounded persona-by-journey evaluations with traceable findings and version comparisons. Use for synthetic user testing or persona-driven product feedback."
license: MIT
---

# UX personas

Use the executable harness to maintain a study, produce separate persona sessions, record evidence, and compare product revisions. The host agent supplies reasoning and an available browser driver; optional TinyTroupe supplies headless persona feedback. Neither synthetic feedback nor a passing fixture establishes real-user satisfaction or conversion.

The optional model-backed feedback command defaults to the logged-in Codex CLI with `gpt-6.1-sol` and high reasoning. It discovers installed CLI versions on PATH and selects the newest compatible stable client. Explicit `--codex-bin` and `CODEX_CLI_BIN` settings remain authoritative. Keep unavailable-model errors explicit; do not substitute another model without the user's instruction.

For feedback, use `python3 "$UX_PERSONAS_DIR/scripts/run_feedback.py"` with the backend arguments. The launcher uses `UX_PERSONAS_PYTHON`, the skill root's optional `.ux-personas-runtime.json` interpreter, or the current Python in that order, so a configured installation does not require manual environment activation. The main study harness remains standard-library-only.

## Choose the evaluation

- **Product concept, copy, or screen description:** run persona feedback through the current agent, or use the optional [TinyTroupe backend](references/tinytroupe.md). Record its responses as synthetic judgments.
- **Working interface:** prepare a persona-by-journey study and drive the actual interface with available tools. Use [Footwork tools](../footwork-tools/SKILL.md) to establish the driver. Browser control is supplied by the host, not by the Python harness.
- **Regression comparison:** preserve the cohort, tasks, starting application state, and prior experience; change the product revision. Compare recorded runs, then inspect their evidence. A remembered journey and a first-time journey are different conditions.

## Ground and prepare

Start from the user's audience and product goal. Group available research by goals, knowledge, context, and behavioral constraints. Keep source references next to supported claims; label invented traits as assumptions. Avoid manufacturing quotes or inferring ability from age, gender, or other demographic categories. If research is absent, create an explicitly assumption-based exploratory cohort and proceed within scope.

Use the [example study](assets/example-study.json) and [data contract](references/data-contract.md). Give each persona stable IDs, goals, knowledge, constraints, evidence, assumptions, and explicit prior experience. Prefer a few meaningfully different profiles over a large Cartesian product of decorative traits. Set actionable constraints such as keyboard-only input, mobile viewport, limited product knowledge, or a short action budget. Preserve curated personas between versions; add experience only when intentionally testing returning users.

Set `UX_PERSONAS_DIR` to this skill's directory and use an approved project output location. These commands require only Python 3.10+ and make no network requests:

```bash
python3 "$UX_PERSONAS_DIR/scripts/persona_harness.py" validate study.json
python3 "$UX_PERSONAS_DIR/scripts/persona_harness.py" plan study.json --output ux-run-v1
```

Inspect the session count and packets before execution. The matrix is work to perform, not completed testing. Each persona must start from the declared application state in an isolated browser context or an explicitly reset session. If the available driver cannot provide isolation, record that limitation and avoid independent-cohort claims.

## Execute and record

For each packet, give the evaluator only its persona, task, starting state, and observations. Do not leak other personas' findings, hidden implementation details, or a solution route. Use separate agent contexts when available and authorized; otherwise disclose that one host agent ran the sessions sequentially.

Drive one visible action at a time, respecting persona constraints and the packet's budget. Capture what appeared and what changed. Separate observed events from simulated interpretations such as frustration. An asserted disability is not an accessibility audit: keyboard-only testing requires keyboard input, and screen-reader claims require an actual compatible driver.

Save relevant screenshots, traces, or readable driver outputs inside the run. Record events using the [event contract](references/data-contract.md). Stop on task completion, abandonment, a blocker, or the action budget. Missing runtime access is blocked or untested, never a successful simulated journey. Existing task authorization governs purchases, sends, account changes, and other effects; a persona is not additional authority.

```bash
python3 "$UX_PERSONAS_DIR/scripts/persona_harness.py" record ux-run-v1 \
  --session first-time-editor--download-document --event observation.json
python3 "$UX_PERSONAS_DIR/scripts/persona_harness.py" report ux-run-v1 --output ux-report-v1
python3 "$UX_PERSONAS_DIR/scripts/persona_harness.py" compare ux-run-v1 ux-run-v2
```

The recorder checks identities, ordering, budgets, artifact integrity, and completion evidence. It cannot authenticate an author's `browser` label or determine whether an artifact semantically proves the criterion; the supervising agent must inspect it. Never relabel fixture output or TinyTroupe narration as live-browser evidence.

## Return to Tometo

Report concrete friction with affected personas, task, observed trace, synthetic interpretation, and a proposed check. Include missing sessions and blockers in the denominator. Keep counts descriptive of the simulated cohort. Fixes continue only within the user's existing implementation scope, using the project's verification route, then rerun comparable sessions. Do not replace human research with population claims from these results.

Read [source decisions](references/provenance.md) when considering a different engine or extending the backend. Runtime installation and paid model execution are separate from the dependency-free harness.
