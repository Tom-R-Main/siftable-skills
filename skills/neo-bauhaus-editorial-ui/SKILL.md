---
name: "neo-bauhaus-editorial-ui"
description: "Use for bold Neo-Bauhaus editorial redesigns of existing product UIs, especially when improving hierarchy, typography, empty states, and cross-view visual rhythm without backend changes."
---

# Neo-Bauhaus Editorial UI Skill

Use this skill when the goal is a strong, memorable visual direction with production-safe UI changes.

## Trigger guidance

Apply this visual direction when requested or consistent with the established design brief:
- The user asks for visual hierarchy improvements across existing screens.
- The UI feels flat/monochrome and needs layered surfaces and accent structure.
- Empty states are passive and need actionable guidance.
- Sidebar/list rhythms differ heavily across views and need unification.

Do not apply this skill when the request is backend-only, schema-only, or infrastructure-only.

## Audit rubric

Review the target screens for:
1. Surface ladder: clear levels as needed (`base`, `panel`, `card/elevated`).
2. Typography hierarchy: headings/body/meta clearly separated.
3. Empty states: actionable title + guidance + CTA.
4. Color intent: restrained palette with purposeful accents.
5. Interaction affordance: clickable/draggable controls visibly interactive.
6. Rhythm consistency: sidebar rows/badges/metadata follow shared patterns.

Priority order:
- P0: readability blockers, hidden affordances, broken navigation states.
- P1: hierarchy/spacing inconsistencies, weak empty states.
- P2: polish and motion refinements.

## Implementation workflow

1. Establish direction
- Confirm this visual concept fits the user’s brief and existing design system.
- Define one memorable signature pattern (accent rails + dense headings).

2. Token-first foundation
- Add semantic tokens for surface ladder, borders, text emphasis, and accents.
- Avoid one-off colors in feature files when token equivalents exist.

3. Build high-leverage primitives
- `SectionHeader`: kicker + icon + accent rail.
- `EmptyStatePanel`: title + explanation + optional CTA.
- `StatusBadge`: unified tone system.
- `SidebarListItem`: consistent row rhythm.

4. Screen-by-screen integration
- Start with the project’s highest-priority user journeys.
- Preserve behavior and API contracts while swapping visual structure.
- Replace dead text empty states with `EmptyStatePanel`.

5. Accessibility and interaction
- Keep keyboard semantics intact (no nested interactive controls).
- Add clear hover/focus states and minimum text contrast.

6. Validation
- Build frontend.
- Run targeted unit tests for touched areas.
- Run Playwright regression on desktop + mobile.

## Acceptance checklist

- Surface levels communicate hierarchy without unnecessary decoration.
- Section headers are scannable and no longer uniform gray labels.
- Empty states provide explicit next actions.
- Drag/click affordances are clear for the affected flows.
- Sidebar row rhythm is consistent across target screens.
- No console errors introduced by semantic/DOM issues.
- Playwright regression suite passes for primary flows.
