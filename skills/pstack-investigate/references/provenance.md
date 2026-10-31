# Provenance

Adapted from Lauren Tan / poteto pstack, MIT licensed, at immutable commit `5bf2b1544db739998121a306340631963c2ff3de`. This is a curated Codex adaptation, not the upstream Cursor plugin.

- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/playbooks/bug-fix.md
- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/how/SKILL.md
- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/why/SKILL.md

Changes: native available tools and inherited model settings; task-scoped routing; existing local skill ownership; bounded verification and explicit limitations; no Cursor-only mode metadata, fixed model slugs, automatic PR posting, telemetry, or implicit authority to send messages, merge, deploy, or write memory. Sibling skill links are explicit installation dependencies; install their closure as well. Upstream updates require a reviewed rebase of these adaptations.

## Targeted refresh (2026-10-15)

Added mutation readback, real-bug test boundaries, and a proposed cheap diagnostic signal. Immutable source commits and adaptation limits are recorded in the [tometo refresh](../../tometo-mode/references/provenance.md#targeted-refresh-2026-10-15). Existing host mechanics and authorization boundaries remain intact.
