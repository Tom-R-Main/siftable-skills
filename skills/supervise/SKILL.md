---
name: supervise
description: Compatibility entrypoint for trusted supervised coding with isolated workers, structured evidence, independent verification, remediation, and final judgment. Use when the user invokes $supervise or asks a Codex Sol worker to implement bounded repository work under external supervision.
---

# Supervise

Read and follow [the canonical supervision workflow](../supervise-workflow/SKILL.md)
completely. Default the writer backend to `codex`. Use `single-worker` only for
low-risk bounded work; use `fresh-context-review` when independent scrutiny is
part of the request. For large, ambiguous, or high-blast-radius work, use
`planned-fresh-context-review` with pinned Claude Opus 5 xhigh planning and
review. Use the portable
Codex adapter for full harness evidence; native app subagents are a manual path
until the harness gains an ingestion adapter. Preserve all canonical scope,
verification, remediation, and
judgment requirements.
