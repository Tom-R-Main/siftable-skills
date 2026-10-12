---
name: supervise-fable
description: Trusted Claude Fable 5 supervision for bounded coding work, routing Fable to fresh planning, independent review, or both while Codex Sol or gated Kimi implements in an isolated worktree. Use when the user invokes $supervise-fable or specifically wants Fable to supervise an implementation or review an existing committed diff.
---

# Supervise Fable

Read and follow [the canonical supervision workflow](../supervise-workflow/SKILL.md)
completely. Treat the immutable task contract as the only authority.

This is a Fable-first supervisor, not an alias for another model. Every launched
workflow must contain at least one fresh read-only `claude-fable-5` node at `max`
effort unless the user requested compile-only inspection. Never silently replace
Fable with Opus. If Fable is unavailable or the provider reports a fallback,
stop or finish safe local inspection, report that Fable did not fulfill the role,
and ask whether to proceed with a named alternative.

Keep Fable on the supervisory side of the trust boundary. In the current native
harness, Fable may plan, review, or do both; it is not an implementation backend.
Use Codex GPT-5.6 Sol for general implementation and remediation, or gated Kimi
K3 for reference-driven UI under the canonical design requirements. The invoking
host remains the trusted monitor and final judge.

Require every writer to follow the externally validated runtime's `supervised-worker` contract (see the [readable reference](../supervise-workflow/assets/prompts/supervised-worker.md)): no
delegation, minimal in-scope edits, focused tests early, one early checkpoint,
and a protected closure budget for scope inspection, final verification, visual
evidence, and the required JSON report. Fable reviews sanitized monitor evidence,
not the writer's unverified claim that its work passed.

## Choose Fable's role

Use the smallest workflow that spends Fable where its judgment matters:

- For an existing committed diff, use `review-existing` with a clean checkout,
  explicit `base_ref`, `review_backend: "claude"`,
  `review_model: "claude-fable-5"`, and `review_effort: "max"`.
- For medium implementation work, use `fresh-context-review` with Sol writing
  and Fable independently reviewing the monitor-generated evidence packet.
- For large, ambiguous, long-horizon, or high-blast-radius work, use
  `planned-fresh-context-review` with separate fresh Fable planner and reviewer
  sessions around one isolated writer.
- When planning is the hard part but cross-model review is more valuable, use a
  Fable planner and an Opus reviewer. When only one Fable call is justified,
  prefer Fable for final review because it can inspect the actual diff and
  monitor verification evidence.
- For a candidate tournament, use Fable as each viable candidate's fresh
  reviewer. Do not add a planning node the pattern does not support or spend
  remediation on an unselected direction.

Do not collapse an explicitly requested Fable run to `single-worker`, because
that pattern contains no Fable role. If the task is too small to justify a fresh
review, explain the cost/latency tradeoff and offer the ordinary canonical
workflow; do not pretend a Fable workflow ran.

For a Fable planner, set:

```json
{
  "planner_backend": "claude",
  "planner_model": "claude-fable-5",
  "planner_effort": "max"
}
```

For a Fable reviewer, set:

```json
{
  "review_backend": "claude",
  "review_model": "claude-fable-5",
  "review_effort": "max"
}
```

Use the exact model identifier, not the moving `fable` alias. Before the first
paid Fable run or after a Claude CLI/model change, run the canonical Claude
doctor and a tiny structured-output probe pinned to `claude-fable-5` at `max`.
Compile and validate before launch, then inspect every Fable node's backend,
model, effort, mode, dependencies, timeout, and task-contract hash.

On remediation, resample the writer under the canonical rules and run a new
fresh Fable review against new monitor evidence. Fable findings are advisory;
scope, deterministic and visual verification, policy gates, and final acceptance
remain monitor-owned. Report Fable's actual role, exact model and effort,
provider fallback or availability issues, rounds, findings, and disposition.
