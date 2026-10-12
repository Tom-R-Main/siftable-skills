# Provenance

Adapted from Lauren Tan / poteto pstack, MIT licensed, at immutable commit `5bf2b1544db739998121a306340631963c2ff3de`. This is a curated Codex adaptation, not the upstream Cursor plugin.

- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/maintain-verification-skill/SKILL.md

Changes: native available tools and inherited model settings; task-scoped routing; existing local skill ownership; bounded verification and explicit limitations; no Cursor-only mode metadata, fixed model slugs, automatic PR posting, telemetry, or implicit authority to send messages, merge, deploy, or write memory. Sibling skill links are explicit installation dependencies; install their closure as well. Upstream updates require a reviewed rebase of these adaptations.

Verification refresh, 2026-10-02: this route now uses the shared `pstack-verify` execution workflow. Its [grounding](../../pstack-verify/references/grounding.md) records transcript timestamps, upstream commit `7022c81efb48d8b5eb15498ce6043a3bd74b694c`, and the inspected Footwork source. Other upstream adaptations remain based on the original commit above.
