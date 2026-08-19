---
name: semantic-density
description: >-
  Use for internal, personal, or model-facing prose such as prompts,
  instructions, planning notes, scratch notes, and temporary technical
  explanations. For publicly facing writing or durable user-visible strings,
  use human-writing instead.
---

# Semantic density

## Scope and routing

Use this skill when the text is for yourself, another internal reader, a model, or a temporary context. Optimize for information per sentence, explicit constraints, concrete references, and easy execution. Do not add personality, artificial messiness, or a simulated authorial voice.

For public-facing writing, product copy, documentation, or durable user-visible strings—including frontend labels, messages, errors, empty states, and onboarding text—use `human-writing` instead. That skill adds voice calibration, genre fit, authenticity, public-facing pattern review, source verification, and final text hygiene.

Do not rewrite code, schemas, commands, identifiers, quoted material, structured data, or required terminology unless the request explicitly includes them. Preserve their exact syntax and meaning.

## Workflow

1. **Identify the job.** State internally what the reader must know, decide, provide, or do.
2. **Protect constraints.** Preserve facts, assumptions, uncertainty, dependencies, names, numbers, dates, links, code, identifiers, and requested output shape.
3. **Compress.** Remove repetition, social wrappers, generic framing, filler, and claims that do not change the reader's understanding or next action.
4. **Specify.** Replace abstractions with the available actor, object, action, input, output, mechanism, result, or decision. If the source does not support specificity, state the uncertainty rather than guessing.
5. **Order.** Put the decision, request, or main conclusion first. Follow with only the context needed to interpret or execute it.
6. **Check.** Confirm that the result is complete, unambiguous, technically exact, and no stronger or more certain than the source.

## Density rules

- Prefer concrete nouns and strong verbs over nominalizations, weak verbs, and adverbs.
- Replace “in order to,” “due to the fact that,” “it is important to note,” and similar filler with the shortest form that preserves meaning.
- Remove chatbot residue such as “Of course,” “Great question,” “I hope this helps,” generic reassurance, offers to continue, and cutoff disclaimers unless the context genuinely requires them.
- Replace vague attribution such as “experts say” or “research suggests” with a source when one is available; otherwise narrow or remove the claim.
- Remove false contrasts, padded lists, synonym cycling, ornamental metaphors, and repeated headings when they add no logic.
- Keep one term for one concept. Do not vary terminology merely to avoid repetition.
- Use active voice when the actor matters; keep passive voice when the actor is unknown, irrelevant, obvious, or conventional.
- Split a sentence when its structure makes the reader backtrack. Keep a longer sentence when its clauses express one necessary relationship.
- Use headings, bullets, tables, and formatting only when they improve retrieval or execution.
- End with the last needed fact, decision, constraint, or next action. Do not append a generic summary.

## Final questions

Before delivery, ask:

1. Can the reader tell what this is about and what to do next?
2. Does every sentence add a fact, constraint, reason, decision, or useful transition?
3. Could any vague noun be replaced with an actor, object, action, mechanism, or result already supported by the source?
4. Did the rewrite add a fact, assumption, certainty, attribution, or requirement?
5. Did it preserve exact terminology, formatting, links, code, and output constraints?
6. Would a shorter version remain equally precise?

If the text is going to users, customers, readers, or a durable product surface, stop this pass and route it through `human-writing`.
