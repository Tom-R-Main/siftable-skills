# Repo-aware implementation

Load this reference when translating an approved Paper frame into a production codebase or when redesigning an existing product surface through Paper.

## Default workflow

For an existing application, use this sequence:

1. Run the real application at the target route and viewport with representative, non-sensitive data.
2. Capture the relevant page or region with Paper Snapshot. Do not ask an agent to reconstruct an available rendered surface from source code.
3. Read the repository's token sources and reuse or map them into Paper before serious redesign work.
4. Preserve the Snapshot as a labeled current-state baseline. Duplicate it for structurally distinct alternatives.
5. Work in small regions, approve one exact direction, and annotate localized intent with Paper comments when available.
6. Create or update a component or screen spec for meaning that the canvas cannot express.
7. Inspect the repository's existing components, types, queries, state, localization, accessibility patterns, and tests.
8. Map each approved Paper region to existing primitives and domain components. Prefer a new variant or composition over replacing a valid abstraction with exported markup.
9. Implement the smallest coherent architectural delta.
10. Render the implementation in the real app or Storybook at matching viewports. Capture, compare, correct, and repeat.
11. Run behavioral, interaction, responsive, and accessibility checks independently of visual comparison.
12. If Paper should remain the exploration surface, Snapshot the verified implementation back into a new labeled current-state frame.

For an entirely new interface, skip the initial Snapshot but retain the token, spec, architecture, and verification steps.

## Write the component or screen spec

Keep the spec close to the implementation or in the repository's established design-document location. Update an existing spec instead of creating a competing artifact.

Record only decisions needed to implement and verify the design:

```yaml
component: EntitySuggestion
purpose: Present a resolver-backed entity candidate and its evidence.

composition:
  - identity
  - confidence
  - evidence_summary
  - primary_action

data:
  entity_id: EntityId
  canonical_name: string
  document_frequency: integer
  confidence: float

queries:
  - entity suggestion query that supplies every displayed value

behavior:
  click: open_entity_detail
  hover: show_source_summary
  keyboard: focusable and activatable

states:
  - loading
  - default
  - selected
  - resolving
  - low_confidence
  - empty
  - error

responsive:
  - define reflow, visibility, density, and overflow rules at represented widths

invariants:
  - confidence comes from the resolver
  - explanation strings are never synthesized without supporting evidence
```

Include the component tree, appearance-critical values, required inputs, interactions, states, queries or data sources, invariants, responsive behavior, and accessibility semantics. Link exact repository symbols when known. Do not copy incidental Paper wrapper structure into the spec.

Before designing a data-backed cell, name the query or source that backs it. If the data contract is unknown, label it as unresolved rather than inventing realistic-looking content.

## Use comments for local intent

Use Paper comments for decisions attached to a specific visual region, such as:

- clicking pivots the current investigation rather than navigating away;
- the explanation must derive from evidence already present in the corpus;
- the control moves into the command drawer below a named breakpoint;
- an alternative is retained for comparison and must not be implemented.

Use the component or screen spec for cross-cutting behavior, data contracts, state matrices, and invariants. Resolve comments only after the implementation and verification satisfy them.

## Preserve architecture

Treat Paper MCP outputs—screenshots, JSX, computed styles, node structure, tokens, and fill images—as reconstruction evidence. They do not identify the correct production abstraction.

When an exported generic subtree visually corresponds to an existing repository component, keep the existing component. Adjust its variant, styling, tokens, or composition until the rendered result matches the approved design. Do not create a permanent Paper-node-to-component synchronization layer unless the user explicitly asks for one and the maintenance tradeoff is justified.

## Run mandatory visual QA

Use a closed loop rather than a one-shot implementation:

1. render the actual component or route;
2. capture it at the same viewport and state as the approved Paper frame;
3. compare typography, color, spacing, alignment, dimensions, content wrapping, imagery, and responsive behavior;
4. list concrete discrepancies;
5. correct the implementation through repository-native tokens and components;
6. repeat until no material discrepancy remains or the agreed tolerance is met.

Do not infer implementation correctness from a Paper screenshot alone. Verify exact values from Paper inspection tools and verify the result in the browser. Functional tests do not replace visual comparison, and visual parity does not replace behavior or accessibility tests.

## Capability boundary

Assume semantic round-tripping is incomplete unless the live Paper guide and tool schemas prove otherwise. Paper layers do not necessarily retain the identity, props, slots, data contract, or behavior of production components. Verify current capabilities before claiming native code-component, Tailwind, theme, token, or round-trip support.

Useful current sources to re-check when capability claims matter:

- https://paper.design/roadmap
- https://paper.design/build-log
- https://paper.design/docs/tokens
- https://paper.design/docs/support
