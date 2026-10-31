---
name: supervise-opus
description: Trusted Claude Opus 5 xhigh planning and independent review workflow with Codex GPT-6.1 Sol as the default implementation worker, optional Kimi K3 for reference-driven UI, isolated worktrees, monitor-run verification, bounded remediation, and final human judgment. Use when the user invokes $supervise-opus or asks for a high-confidence implementation workflow or fresh review of an existing committed diff.
---

# Supervise Opus

Read and follow [the canonical supervision workflow](../supervise-workflow/SKILL.md)
completely. Treat the immutable task contract as the only authority.

Default large or ambiguous work to `planned-fresh-context-review`:

1. a fresh read-only `claude-opus-5` planner at `xhigh` effort;
2. Codex GPT-6.1 Sol implementing in one isolated worktree;
3. monitor-run scope, deterministic, and visual verification;
4. a separate fresh read-only `claude-opus-5` reviewer at `xhigh` effort,
   consuming the sanitized evidence packet;
5. bounded remediation by the writer, followed by a new review.

For a review-only request, use `review-existing` with an explicit `base_ref`.
Require a clean source checkout, omit the implementation `backend`, and inspect
the compiled plan to confirm it contains exactly one read-only
`claude-opus-5` reviewer at `xhigh`.

Collapse small, fully deterministic, low-blast-radius work to `single-worker`.
For medium work, use `fresh-context-review` with no separate planner and set
`review_backend` to `claude`. Inspect the compiled plan and confirm every Claude
node records the exact model and effort before launch.

For screenshot, Figma, or strong reference-driven UI work, `backend: kimi` is an
explicit writer alternative only when the spec includes design evidence,
viewports, and a visual verification command. Do not add Kimi as a fourth role.
On remediation, Codex Sol takes over the existing Kimi worktree.

For blank-page UI planning, search `searching-design-corpus` first. If it provides
no useful visual precedent, use the canonical workflow's sibling
`generating-design-references` skill on the trusted side, view and critique its
PNG, and declare it as `design.generated_reference_images`. Require the Opus
plan to state what it will use and reject from every generated scaffold. Never
confuse one with a user-supplied fidelity target.

Use the portable `codex exec` adapter when the harness's worktree, report, timeout,
digest, and policy guarantees are required. The Codex app can delegate to native
Sol subagents, but the current executable harness cannot ingest those sessions;
native delegation is therefore a manual, weaker-evidence path rather than an
equivalent adapter. Each Opus plan or review node remains a fresh Claude CLI
session. Use [supervise-fable](../supervise-fable/SKILL.md) when Fable should be
the named planner or reviewer; do not silently turn an Opus invocation into a
Fable workflow.
