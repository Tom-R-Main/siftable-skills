# Provenance

Adapted from Lauren Tan / poteto pstack, MIT licensed, at immutable commit `5bf2b1544db739998121a306340631963c2ff3de`. This is a curated Codex adaptation, not the upstream Cursor plugin.

- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/architect/SKILL.md
- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md

Changes: native available tools and inherited model settings; task-scoped routing; existing local skill ownership; bounded verification and explicit limitations; no Cursor-only mode metadata, fixed model slugs, automatic PR posting, telemetry, or implicit authority to send messages, merge, deploy, or write memory. Sibling skill links are explicit installation dependencies; install their closure as well. Upstream updates require a reviewed rebase of these adaptations.

## User-directed architecture policy (2026-11-01)

Added [performance and technology selection](technology-selection.md) at the user's request: prioritize low-level resource efficiency and the best supported system outcome when selecting architectures, languages, frameworks, and runtimes; use capable agents and specialty skills rather than historical manual development convenience as the basis for feasibility. Concrete component and platform benefits remain valid reasons for higher abstractions. Whole-system measurements, ownership, correctness, migration scope, and explicit uncertainty constrain recommendations. This policy is a repository adaptation, not a claim about the pinned upstream or a measured language ranking.

## Architecture selection follow-up (2026-11-01)

The user-requested selection framework was authored in the local skill installation and then selectively ported into this library as [architecture-selection](../../architecture-selection/SKILL.md). It owns workload/placement comparisons, defect-class reasoning, boundary and migration costs, evidence limits, and a decision record. Tometo routes material stack choices through it before implementation skills; Architect consumes that choice when sketching interfaces. The previous technology-selection reference remains a forwarding route. Host-specific adapters and prior scope/authorization rules are preserved. This is original policy work, not a new upstream revision or a measured language ranking.
