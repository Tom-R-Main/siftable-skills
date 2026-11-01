---
name: pstack-architect
description: "Design or review interfaces, data ownership, language and framework choices, and module boundaries against actual callers. Use for substantial architecture changes, engineering plan reviews, or refactors requiring ordered verification and recovery."
license: MIT
metadata:
  upstream: cursor/plugins/pstack
  upstream-commit: 5bf2b1544db739998121a306340631963c2ff3de
  adaptation: tometo-codex
---

# Architect

Set the task mode first: review an existing plan, design only, or design then implement. Preserve an explicit review/approval boundary. When implementation is already authorized, a finished design is a phase, not a reason to stop.

## Ground and sketch

Trace current callers, data structures, ownership, failure paths, and constraints in the actual repository. Use existing vocabulary and relevant ADRs. Retrieve history when the design would discard a non-obvious boundary. Separate evidence from hypotheses.

Write the caller's intended usage first, then derive the smallest types, signatures, state transitions, and module boundaries that support it. Keep sketches in the plan or scratch space for design-only work. Do not introduce unimplemented stubs into the product merely to demonstrate planning.

When alternatives could materially change the design, compare structurally different options. Prototype empirical uncertainties in isolated task-owned space if authorized. Use independent design exploration only when its benefit justifies the cost and delegation is permitted. Do not require several models or alternatives for an obvious local change.

For a material language, framework, runtime, dependency, or execution-boundary choice, use [architecture selection](../architecture-selection/SKILL.md) before deriving interfaces. Carry its chosen execution design, resource goals, boundary contracts, and unresolved acceptance checks into this plan. Keep ordinary interface work in the established stack unless the task actually opens that choice.

Prefer structures that make invalid states difficult to represent, concentrate validation at real boundaries, and remove accidental shared state. Preserve legitimate compatibility, security checks, and migration safety; simplicity does not justify breaking callers or deleting a guard without proving its invariant.

## Make the plan executable

Record the recommended shape, real tradeoffs, and enough evidence for the decision. For multiple units, specify owned paths, dependency order, acceptance checks, migration/recovery steps, and which actions need separate authorization. Use the existing [plan](../plan/SKILL.md) when a visual dependency plan is requested; preserve explicit domain/supervision contracts.

When reviewing an existing plan, check its assumptions, interfaces, scope, failure modes, testability, rollout order, and recovery. Return actionable findings separately from optional alternatives. Do not replace the user's plan with a different product or silently implement the findings.

When implementing, check the resulting callers against the sketch. Repeated workarounds may invalidate the design; surface the failed assumption and revise the scoped plan. A different design is not automatically permission for a wider rewrite.

Deliver the chosen structure, why it fits the repository, the ordered work and verification, and unresolved decisions. A design review is not a review of a later implementation.

Source and adaptation details: [provenance](references/provenance.md). Read only when auditing or updating this skill.
