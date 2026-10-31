Relevance gate: Read this only when the user requests interaction variants, or a bounded behavioral prototype would resolve a material design uncertainty. Do not add a prototype stage to routine frontend implementation.

# Behavioral prototypes

Use the [shared workflow](../SKILL.md). [Paper](../../paper-design/SKILL.md) can establish visual truth; this reference complements it when timing, state transitions, input, or navigation need exploration. See [provenance](provenance.md) for the reviewed sources and corrections.

## Define the useful comparison

- State the unresolved behavior and the decision the prototype should support before making variants.
- Name distinct axes such as disclosure behavior, navigation model, information density, or motion choreography. Cosmetic renaming does not make two variants meaningfully different.
- Scale the number of variants to the user's request and the uncertainty. A focused comparison may need two; an exact approved direction may need one.
- Keep content and test conditions comparable so the behavioral difference can be judged.
- Reuse the project's components, tokens, data shape, and realistic edge states. Avoid inventing a parallel design system for the harness.
- Prefer an existing Storybook surface or a development-only route when it fits the project. Keep prototype entrypoints outside production navigation.
- Integrate a selected variant into production after selection, unless the user has already approved that exact direction and its implementation.

## Optional comparison harness

- Add a selector only when it makes the comparison easier; do not copy a rigid toolbar, theme, or page shell from an upstream example.
- Keep controls unobtrusive, responsive, keyboard accessible, and outside the content they would obscure. A full-page blocker overlay defeats interaction testing.
- Give variants stable, meaningful identifiers and an explicit ordered list of valid choices.
- If selection is encoded in the URL, validate it against that list. Missing, malformed, unknown, or out-of-range values resolve to the first valid variant.
- Keep the selector and URL consistent without triggering navigation loops or destroying unrelated URL state.
- Use `type="button"` for harness buttons so placing the harness near a form does not submit it.
- Preserve focus during swaps where the target still exists; when it disappears, move focus to a sensible surviving control instead of leaving it on the document body.
- Preserve input where the comparison permits it, or make reset behavior explicit. Do not erase typing on every selector update.
- Add shortcuts only when useful. Ignore editable targets, respect modifiers and existing browser/app shortcuts, and do not intercept ordinary typing unexpectedly.

## State and motion

- Swap variants immediately by default so the comparison remains direct. Optional motion replay is a separate control, not a reason to animate every swap.
- Respect reduced motion in both the prototype and its harness. A replay control must not override the user's preference silently.
- Keep loading, error, empty, long-content, and interrupted states available when they affect the decision; omit unrelated scenarios.
- Ensure animation completion is not the only path that commits state or restores interaction.
- Avoid a full JavaScript helper unless repeated use justifies maintaining it; a small local implementation is usually enough.

## Evaluation and handoff

- Exercise the behavior with relevant keyboard, pointer, and responsive conditions. Use [pstack-verify](../../pstack-verify/SKILL.md) when live behavior needs verification.
- Describe each variant's observable tradeoff and the evidence that would favor it. Do not declare a winner from a screenshot when the question concerns interaction.
- Report the prototype's location, available variants, and remaining decision. Keep preview access within the task's existing permissions.
- After selection, transfer the chosen behavior into the existing architecture and verify it there; prototype success alone does not establish production correctness.
- Remove only scaffold you own, within the user's cleanup authorization. Preserve requested comparison artifacts and any files still needed for review.
- Do not automatically delete a user-created worktree or requested prototype to make the workspace look tidy.
