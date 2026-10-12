---
name: paper-design
description: Create, inspect, edit, import, export, and hand off product or visual designs through Paper and its MCP server. Use when a request mentions Paper, Paper MCP, Paper Snapshot, a Paper file or selection, design tokens in Paper, HTML or SVG import, responsive Paper artboards, or translating between a Paper canvas and a codebase.
---

# Paper Design

Use Paper as a shared, inspectable web artifact: the person makes fast visual judgments on canvas while the agent handles structural repetition, token updates, inspection, and code translation.

Treat Paper as the visual oracle, not the architectural oracle. For an existing application, default to **running product → Snapshot → Paper → explicit spec → repository-aware implementation → browser or Storybook verification**. Do not default to exporting Paper JSX directly into production.

The Paper MCP server is the capability layer. This skill is the operating method and quality bar. Do not conflate them.

## Start every session from live context

Paper ships rapidly. Treat its live MCP guide and tool schemas as authoritative over this skill when they differ.

1. Confirm a compatible Paper instance and its MCP connection are actually available. The desktop app, MCP server, and account are not bundled; cloud tasks require an explicitly configured connection to a supported instance. If absent, report the capability gap and use another already available design route only when it satisfies the task. Do not install or register Paper automatically.
2. Call `get_guide({ topic: "paper-mcp-instructions" })` before any other Paper tool in a new or compacted MCP session.
3. Call `get_basic_info`; then call `get_selection` when the user's current focus matters.
4. Inspect existing tokens, fonts, artboards, and dimensions before proposing mutations.
5. For a new design, post the brief described below before creating an artboard or writing HTML.
6. Before the first typographic mutation, call `get_font_family_info` for every intended family and weight.
7. Prefer a new file, page, or clearly labeled lab artboard for experiments. Do not contaminate approved work.

If any normal tool reports an MCP quota error, stop further nonessential Paper calls, preserve the current design, call `finish_working_on_nodes`, and explain which validations remain unperformed. See [MCP operations](references/mcp-operations.md).

## Route the task

- **Create or explore**: brief → tokens → artboards → incremental groups → screenshots → targeted revisions.
- **Edit an existing design**: inspect selection/tree/styles → mutate exact nodes → screenshot → preserve unaffected work.
- **Existing product to Paper**: run the real application with representative data → capture the relevant region with Paper Snapshot → sync/reuse repository tokens → preserve the captured baseline → duplicate it for alternatives.
- **New code-informed design**: read the codebase's actual tokens, primitives, content, data constraints, and layout conventions → create/reuse Paper tokens → build a small representative surface → compare.
- **Paper to code**: approve an exact frame → capture nonvisual intent in a component or screen spec → inspect the existing implementation → map Paper elements to repository primitives → implement the smallest architectural delta → compare the rendered result with Paper.
- **Import a live page**: prefer Paper Snapshot over agent reconstruction when the running surface exists; use HTML paste when Snapshot is unavailable, then normalize the resulting layer structure before iterating.
- **Migrate a legacy Figma source**: use Paper's direct copy/paste path when the user supplies the source. Do not load or depend on Figma skills; treat the imported layers as ordinary Paper structure after transfer.
- **SVG work**: import or generate a real SVG subtree for structural use; reserve detailed path editing and pen-tool judgment for the Paper UI unless the live MCP exposes an appropriate operation.

Read [Import, tokens, and handoff](references/import-tokens-handoff.md) for the relevant route. Do not load unrelated references.

## Maintain three distinct truths

- **Paper holds visual truth**: composition, hierarchy, typography, color, spacing, and intended responsive arrangements.
- **The implementation spec holds behavioral and data truth**: component tree, inputs, queries, states, interactions, accessibility, invariants, and responsive rules that pixels cannot encode.
- **The repository holds architectural truth**: existing components, domain types, data access, state management, localization, tokens, and test conventions.

Before designing a data-backed region, name the query or source that backs it. Do not invent values, explanations, states, or behavior merely because they make the frame look complete.

When moving an approved design into code, read [Repo-aware implementation](references/repo-aware-implementation.md). Create or update the explicit spec before implementation whenever the frame contains meaningful data, interaction, state, or responsive behavior.

## Compose with specialist design skills

Paper is the editable canvas and handoff hub, not the entire design process. The following integrations are optional and may be absent from the installed catalog. Discover actual availability before invoking; do not install skills/providers or claim unavailable capabilities. Load only the specialists the task actually needs:

| Need | Use | Paper handoff |
| --- | --- | --- |
| Current product precedents and real screen/flow research | `refero-design` | Bring the synthesis and chosen patterns into Paper; do not copy a reference wholesale. |
| Source-grounded interface principles | `searching-design-corpus` with the UI collection | Turn the relevant findings into explicit layout, type, color, or interaction decisions before drawing. |
| A visual anchor when grounded references are genuinely absent | `generating-design-references` | Critique the generated image, then reconstruct the useful ideas as editable Paper layers. Never paste the raster as the finished interface. |
| Several image-based visual directions | `product-design:ideate` | Select a direction, then rebuild it in Paper when editable exploration or token work matters. |
| Product-flow, usability, or accessibility critique | `product-design:audit` | Audit the Paper result or the implemented product with screenshots and evidence; do not silently mutate during an audit-only request. |
| Distinctive production implementation from an approved Paper direction | `frontend-design` | Read exact Paper structure, styles, and tokens first; then implement in the repository's real component system. |
| Strict implementation of a selected screenshot or image | `product-design:image-to-code` | Use this instead of `frontend-design` when fidelity to a fixed image is the primary objective. |
| Clone a live URL | `product-design:url-to-code` | Use only for a true URL-cloning request, not ordinary redesign work. |
| Visual regression after implementation | `product-design:design-qa` | Compare the running product with the approved Paper or image reference and fix measurable drift. |

For code work, add stack-specific skills such as `css`, `typescript`, `react-best-practices`, or `shadcn` only when the repository and requested change call for them. Do not trigger every skill in this table for a normal Paper edit.

## Write the brief before a new design

Post this short brief as a user-visible message before any mutation:

- **Product truth**: what it is, who it serves, why it matters, and the primary action
- **Reference evidence**: 3–5 relevant references and the specific principle taken from each
- **Mood candidates**: 3–5 physical or visual registers
- **Mood chosen**: the committed direction and why it is not the first obvious choice
- **Palette**: 5–6 colors with roles and concrete scene references
- **Type**: verified families, weights, sizes, line heights, and tracking
- **Direction**: one sentence describing composition and intent
- **Refusals**: 3 predictable treatments this direction will deliberately avoid

If the user supplied a complete design system, state that it is the source of truth instead of inventing a new palette.

## Reject the first-pass agent look

Before approving a generated direction:

1. Use real content whenever available. Preserve the product truth and one clear primary action.
2. Generate 3–5 structurally distinct directions, not palette swaps; then select, combine, and edit. Never ship the first plausible generation.
3. Run a subtraction pass. Remove every card, badge, kicker, icon, label, container, or repeated device without a semantic or compositional job.
4. Use the smallest coherent type system that preserves the intended character. As a default pressure, keep each section near three hierarchy levels and do not use bold as the hierarchy mechanism everywhere.
5. Require every animation, hover treatment, shader, gradient, and decorative effect to clarify state, reinforce meaning, or express the specific brand. Remove effects whose only rationale is that they were easy to generate.
6. Enforce one visual grammar across tokens, radii, shadows, alignment lanes, asset treatment, interaction behavior, and voice. Justify exceptions.
7. Perform a human QA pass on desktop and mobile: readability, contrast, clipping, alignment, discoverability, perceived clickability, and loading, empty, error, and responsive states.
8. Apply the distinctness test: if removing the logo makes the result indistinguishable from generic AI software, revisit the direction.

Treat familiar AI tells as diagnostic signals, not universal bans. Read [Quality playbook](references/quality-playbook.md) when the result feels generic, overbuilt, or stylistically incoherent.

## Work in small structural operations

1. Create the artboard at a conventional device size unless the user specified one.
2. Use flex containers, padding, and gap as the default Paper layout vocabulary.
3. Make each `write_html` call roughly one visible group: a header, row, action group, paragraph, or shell.
4. Reuse proven structure with `duplicate_nodes` or `<x-paper-clone>`; then apply `set_text_content`, `rename_nodes`, and `update_styles` in batches.
5. Use `move_nodes` to reorder or reparent existing layers. Do not delete and recreate merely to change hierarchy.
6. Use `write_html` in `replace` mode only when replacing the targeted subtree is genuinely simpler.
7. Keep icon and trailing-action lanes fixed-width with `flex-shrink: 0` across repeated rows.
8. Use named layers for meaningful groups. Rename important clones immediately.
9. Use design tokens through CSS variables whenever the file has them.
10. Call `finish_working_on_nodes` when Paper work ends, including partial work after a quota or tool failure.

HTML import accepts inline styles, not stylesheet classes. Do not use margin, CSS Grid, HTML tables, emoji icons, or mixed-style rich text in agent-written Paper HTML unless the current live guide says support changed. Use SVGs for icons.

## Review every meaningful section

After a section or a few mutations, call `get_screenshot` and give a one-line verdict covering:

- spacing and visual rhythm;
- typographic hierarchy and small-text legibility;
- contrast;
- shared alignment lanes;
- artboard fit and clipping;
- excessive repetition or card-grid sameness.

Fix specific problems in place. If content clips, set the artboard to `height: "fit-content"`; do not guess a taller fixed height. Do not flatten the design or restart wholesale to correct a local issue.

Screenshots are for visual QA only. Never infer exact dimensions, colors, copy, or assets from a screenshot when `get_jsx`, `get_computed_styles`, `get_node_info`, `get_tokens`, or `get_fill_image` can supply the exact value.

## Use the human–agent loop

The productive loop is:

1. import the running product with Snapshot, or build new real structure when no implementation exists;
2. reuse repository tokens and preserve the captured current state;
3. let the agent make broad, repetitive, system-level changes;
4. let the person make fast visual tweaks directly on canvas;
5. have the agent re-read the changed nodes and summarize what changed;
6. run a screenshot checkpoint and approve one exact direction;
7. record nonvisual intent in a component or screen spec;
8. implement through the repository's existing architecture;
9. render in Storybook or the real app, capture, compare with Paper, correct, and repeat;
10. run behavioral and accessibility checks; optionally Snapshot the implementation back into Paper as a new current-state baseline.

This is where Paper differs most from a static mockup handoff: the canvas and code can be inspected through the same web primitives.

## Hand off honestly

Report:

- the file and page by human-readable name or URL;
- artboards created or changed;
- tokens created, updated, or reused;
- visual checkpoints and remaining issues;
- what was tested live versus supported only by documentation;
- any quota, export, font, import, or code-generation caveat.

Do not expose raw node IDs in user-facing text.

Paper's JSX/Tailwind export is evidence and a structural starting point, not production-ready code. If Paper exports a generic subtree but the repository already has a domain component or primitive, preserve the repository abstraction and adapt its styling, variants, or composition. Normalize inheritance, typography, semantics, responsiveness, accessibility, state, and repository-specific tokens.

Do not stop at functional correctness. Render at matching viewports, capture the actual implementation, compare it with the approved Paper target, identify concrete discrepancies, correct them, and repeat until the agreed tolerance is met. Then verify behavior and accessibility separately.

## References

- [MCP operations](references/mcp-operations.md): live-first tool workflow, tested capability matrix, quota behavior, and operation recipes.
- [Import, tokens, and handoff](references/import-tokens-handoff.md): Snapshot, HTML/Figma/SVG translation, token round-trips, responsive frames, and code transfer.
- [Repo-aware implementation](references/repo-aware-implementation.md): explicit component/screen specs, architecture mapping, and visual/behavior verification.
- [Quality playbook](references/quality-playbook.md): visual direction, canvas review, and collaboration checkpoints.
