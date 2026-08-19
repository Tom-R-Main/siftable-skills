# Human writing skill

`human-writing` is a source-preserving writing and editing skill. It combines voice calibration, intent-first drafting, generic-pattern diagnosis, factual auditing, and a final read-aloud revision.

The skill does not use blanket bans on dashes, adverbs, passive voice, questions, fragments, or three-item lists. It treats those as contextual signals and lets the author's sample, genre, and source material decide. Its pattern catalog is English-first; the source-preservation and voice workflow can be adapted to other languages with language-specific diagnostics.

## Files

- `SKILL.md` contains the executable instructions.
- `references/pattern-catalog.md` expands the diagnostic catalog.
- `references/evaluation-rubric.md` defines the scoring system.
- `references/voice-profile-schema.md` provides a reusable voice-analysis format.
- `tests/test-cases.md` provides acceptance cases and edge conditions.

## Suggested invocation

Use the skill when drafting from notes, rewriting a source, matching an author's own sample, reviewing prose for generic model patterns, or producing copy inside another workflow.

For best results, provide the intended reader, the communication goal, immutable facts, and one or more author-owned samples from a similar context. The skill can infer missing details when the surrounding material makes them clear.

## Default output

The default is finished prose only. Ask for an audit when you want a diagnosis or scorecard alongside the revision.
