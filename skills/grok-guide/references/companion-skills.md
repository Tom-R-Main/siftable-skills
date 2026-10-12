# Companion Skills and Pattern Lineage

Use companions only when they strengthen a bounded part of the lifecycle. They remain subordinate to the human/Grok/Codex authority contract.

## User-created local skills

- `$strategic-decision-mapping`: use before the Grok lifecycle when the human objective itself is a consequential strategic fork. Once the objective is fixed, do not let this skill create a competing implementation plan.
- `$thinking-scientific-method`: use during fact gathering when repository evidence requires explicit hypotheses, falsification, or uncertainty tracking. Feed only resulting facts and unknowns to Grok.
- `$typescript`: use inside a Grok task for TypeScript toolchain detection, typing, and narrow-to-broad verification. It may choose execution mechanics but may not expand `allowedPaths`.
- `$react-best-practices`: use inside an approved React/Next task. Its performance priorities remain bounded by Grok's acceptance criteria and non-goals.
- `$strategic-decision-mapping` and domain skills may help the human clarify inputs; none may silently revise a valid Grok plan.

This follows the local custom-skill convention: keep the trigger and workflow lean, load focused references progressively, preserve literal `$skill-name` invocations in metadata, and validate the installed artifact rather than assuming a copy succeeded.

## gstack patterns adopted

- From `autoplan`: treat the workflow as executable sequencing with explicit gates and a final decision boundary.
- From `freeze`: treat path scope as a hard boundary. If `$freeze` is available and the user wants stronger host-level protection, set it to the union of active task paths. Its hook is an adjunct, not the Grok Guide security boundary.
- From `careful`: add destructive-operation confirmation for production, shared, irreversible, or data-loss-capable work.
- From `qa` and `review`: collect observable verification and adversarial findings as worker evidence. Neither replaces Grok's completion audit.
- From `context-save`: preserve a compact lifecycle record during long runs: objective, plan version, replan count, packet hash, active tasks, blockers, and audit state. Do not save evidence excerpts or credentials.
- From gstack's confusion protocol: STOP on high-stakes ambiguity and return the decision to its owner. Do not ask routine questions that evidence can settle.

## Interoperability rules

1. Do not run `autoplan` after Grok has issued the controlling plan; two planners would create ambiguous authority.
2. Do not let `review`, `qa`, or a domain skill mark the overall task complete. Their output becomes worker evidence for `audit`.
3. Do not let `freeze` broaden paths. The effective scope is the intersection of its boundary, repository instructions, human constraints, and Grok `allowedPaths`.
4. Do not let a companion answer `needs_human` questions. Only the human can resolve them.
5. If a companion discovers a conflict with a governing decision or non-goal, create a contradiction packet and replan.
