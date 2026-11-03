# Provenance

Adapted from Lauren Tan / poteto pstack, MIT licensed, at immutable commit `5bf2b1544db739998121a306340631963c2ff3de`. This is a curated Codex adaptation, not the upstream Cursor plugin.

- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/interrogate/SKILL.md
- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/interrogate/references/rubric.md

Changes: native available tools and inherited model settings; task-scoped routing; existing local skill ownership; bounded verification and explicit limitations; no Cursor-only mode metadata, fixed model slugs, automatic PR posting, telemetry, or implicit authority to send messages, merge, deploy, or write memory. Sibling skill links are explicit installation dependencies; install their closure as well. Upstream updates require a reviewed rebase of these adaptations.

## Targeted refresh (2026-10-15)

Added discovery and a shared source list for applicable repository standards. Immutable source commits and adaptation limits are recorded in the [tometo refresh](../../tometo-mode/references/provenance.md#targeted-refresh-2026-10-15). Existing host mechanics and authorization boundaries remain intact.

## User-directed architecture policy (2026-11-01)

Added technology-choice and resource-performance review lenses for the library's system-efficiency priority. These are local policy additions, not new upstream findings: compare relevant language/framework choices against workload evidence, account for agent-assisted implementation and concrete ecosystem benefits, and retain correctness, safety, and task scope.

## Empirical verification refinement (2026-11-03)

Empirical review refinement (2026-11-03): prefer owner-rerun implementation reproducers, retain grounded static findings when execution is inappropriate, distinguish suspicions, and stop discretionary rounds without new evidence. Preserves compatibility intent and required review gates.

Source grounding: [pstack interrogate](https://github.com/cursor/plugins/blob/6ea74587e384e1a8035c09ae33a46fe3f881eb9b/pstack/skills/interrogate/SKILL.md), [PostHog validation criteria](https://github.com/PostHog/posthog/blob/227cbdda021e31226828a918b0768f0ac02ea6c4/products/review_hog/skills/review-hog-validation-criteria/SKILL.md), and [Sentry compatibility regression](https://github.com/getsentry/sentry/blob/05395fb78657c61e5ef49991d6e8a23f0eb1cfdb/tests/sentry/grouping/test_strategies.py#L101). Adaptation retains evidence-based static findings rather than importing pstack's strict run-only admission. The local pilot executed the actual Python CLI against disposable stores and representative defects. A two-client model with at most two attempts agreed between tla-ts 0.0.7 and TLC 1.7.4 on two healthy and three deliberately broken configurations. This is bounded model evidence, not an implementation refinement proof, production crash-durability check, or speed benchmark. No verifier became a package dependency.
