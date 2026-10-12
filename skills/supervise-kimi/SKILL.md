---
name: supervise-kimi
description: Compatibility entrypoint for trusted Kimi K3 frontend and reference-design implementation with Claude Opus 5 xhigh review, isolated worktrees, design evidence, staged verification, Codex Sol remediation, and final judgment. Use when the user invokes $supervise-kimi or asks Kimi K3 to implement a bounded design-heavy repository task under external supervision.
---

# Supervise Kimi

Read and follow [the canonical supervision workflow](../supervise-workflow/SKILL.md)
completely. Set the writer backend to `kimi` and `review_backend` to `claude`.
Default to `fresh-context-review`: one strong Kimi writer followed by a fresh Opus 5 xhigh
review. Use `two-candidate-tournament` only when the user wants two materially
different directions, and encode both directions explicitly. Keep design-corpus
and vault access on the trusted monitor side. For large UI work that benefits
from explicit planning, use `planned-fresh-context-review` for fresh Opus 5 xhigh
plan and review nodes; Codex
Sol takes over any remediation. If the UI has no visual
precedent after corpus search, let the trusted monitor generate, view, and critique
one design scaffold before launch and pass it as
`design.generated_reference_images`; Kimi must not run the generator itself.
