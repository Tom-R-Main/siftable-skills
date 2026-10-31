---
name: emil-design-eng
description: "Build or review polished frontend interactions and component motion using Emil Kowalski's design-engineering principles. Use for UI craft, animation decisions, interaction continuity, or motion-performance work alongside the project's CSS, React, and TypeScript practices."
license: MIT
metadata:
  upstream: emilkowalski/skills
  upstream-commit: 2d228630ba1446365f614a108cb8252f1feda202
  adaptation: tometo-portable
---

# Frontend design engineering

Make interactions clear, responsive, coherent, and usable with real content and input methods. Apply the relevant guidance within the current task: review stays review-only; implementation already authorized continues through verification. Do not replace the task with a readiness statement, extra approval stage, new dependency, or unrelated redesign.

## Work in the actual product

1. Inspect the component's purpose, callers, rendered states, frequency of use, framework and library versions, tokens, and existing accessible primitives. Reuse its design system before inventing curves, dimensions, or abstractions.
2. Preserve semantic behavior first: content, keyboard activation, focus, cancellation, loading/error states, accessible names, and reduced-motion behavior. Visual polish must not delay an action, conceal content, or turn a gesture into the only way to complete it.
3. Decide whether motion has a useful job: feedback, orientation, a state transition, continuity, or requested expression. For repeated keyboard-first workflows, prefer immediate response and omit decorative delay. Removing unnecessary motion is a valid improvement.
4. Use the simplest suitable mechanism already available. CSS is often enough for a small state change; existing animation tooling can own springs, layout, exit, and gestures. Do not add or migrate a library merely to fit a recipe.
5. Implement or recommend the smallest coherent change, then inspect it at normal speed and through relevant repeated/reversed interactions. Separate a demonstrated defect from an aesthetic preference. Report evidence and limits rather than a universal craft score.

Use [css](../css/SKILL.md) for cascade, layout, styling, and browser semantics; [react-best-practices](../react-best-practices/SKILL.md) for React/Next behavior and measured performance; [typescript](../typescript/SKILL.md) for contracts and toolchain checks. Load only those matching the repository. For consequential new visual directions, use available design tools or reviewable mockups; [Paper](../paper-design/SKILL.md) is one optional route. This skill adds interaction detail to the existing design process.

## Load only the relevant reference

| Task | Reference |
|---|---|
| Create or tune requested web motion; describe its behavior precisely | [Motion construction and patterns](references/motion.md) |
| Diagnose dropped frames or main-thread/rendering cost | [Animation performance](references/performance.md) |
| Review existing motion, find useful opportunities, or plan a wider improvement | [Review and discovery](references/review-and-discovery.md) |
| Mobile web/PWA inputs, viewport, keyboard, safe areas, or touch gestures | [Mobile web](references/mobile-web.md) |
| Compare genuinely distinct live variants alongside an approved/design exploration | [Prototypes](references/prototypes.md) |
| Choose an interaction library or change a Sonner toast integration | [Libraries and Sonner](references/libraries.md) |
| Implement or review the affected Expo/React Native or Swift code | [Native specialists](references/native-specialists.md) |

These are conditional references, not a sequence to run on every frontend task. Do not route web/PWA work to Expo or Swift. Existing domain and supervision workflows keep their ownership.

## Verify the interaction

Establish an actual driver with [footwork-tools](../footwork-tools/SKILL.md) and use [pstack-verify](../pstack-verify/SKILL.md) before claiming changed behavior works. Check relevant entry/exit states, rapid reversal, repeated triggering, keyboard/focus, pointer cancellation, reduced motion, and representative content/container sizes. Select cases from the actual change; do not impose an unrelated full matrix.

Use [break-ui](../break-ui/SKILL.md) when data, layout resilience, localization, or edge-state coverage is part of the promise. It tests the real data boundary; animation polish does not replace that proof.

A screenshot establishes a captured appearance, not interruption, input semantics, performance, or persistence. Slow/frame-by-frame inspection can explain a timing problem; repeat at normal speed. Bind evidence to source/build and record browser/device and any unavailable checks. Desktop emulation does not establish physical-device behavior.

Sources, corrections, and specialist coverage: [provenance](references/provenance.md). Read it when maintaining this adaptation or validating a source-specific claim.
