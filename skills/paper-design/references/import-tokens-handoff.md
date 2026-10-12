# Import, tokens, and handoff

Load this reference when moving designs or design-system information into or out of Paper.

## HTML into Paper

Paper translates HTML into editable layers rather than retaining a browser document verbatim.

- Use inline styles. Class names and selector-based CSS are dropped.
- Use flex, padding, and gap for primary layout.
- Do not use margin, CSS Grid, HTML tables, or `display: inline` in agent-authored Paper HTML unless the live guide says support changed.
- Paper applies `box-sizing: border-box`.
- `layer-name="…"` sets the layer label.
- `data-paper-locked` locks a layer; `hidden` preserves an invisible layer.
- `<x-paper-clone node-id="…">` clones an existing Paper node inline.
- Local image paths must be absolute and use `paper-asset:///absolute/path`.
- Remote image URLs must be publicly accessible for Paper to fetch them.
- Inputs become frames with text children.
- Rich text is limited: split mixed-style content into separate text layers rather than relying on nested inline formatting.
- Paper may strip redundant or inert styles. Inspect `ignoredStyles` from style operations when present.

For imports, paste one coherent region at a time. Very large documents are harder to inspect and repair.

## Paper Snapshot

Snapshot is the fastest and most predictable route from a live site to editable Paper layers. Prefer it over agent reconstruction when the running product surface exists because the browser has already resolved fonts, inherited CSS, actual dimensions, flex behavior, wrapping, variables, content, and layout.

For local development, the server must allow `https://app.paper.design` as a CORS origin. In Vite this is typically configured under `server.cors.origin`. Vite 6+ may still block `/@fs/` subresources; serve those assets from `public/` or apply a narrowly scoped development workaround.

Use this loop:

1. start the local product at the intended route and viewport;
2. capture the complete page or selected section with Snapshot;
3. paste into a dedicated Paper page/artboard;
4. inspect layer structure before restyling;
5. repair fonts, images, or overly deep wrappers;
6. create a derivative instead of overwriting the captured baseline;
7. retain multiple alternatives beside the labeled current state until one direction is approved.

Source: https://paper.design/docs/support

## Figma into Paper

Direct copy/paste can preserve editable layers, images, and SVGs. For MCP-assisted transfer, load `get_guide({ topic: "figma-import" })`.

Known limitations from Paper's documentation:

- SVG fills may arrive as images and component overrides may be lost.
- spacer layers can be ignored, altering layout gaps;
- inset borders may not translate to outlines;
- code-connected components are not reliably reconstructed;
- very large/deep designs should be transferred in smaller regions.

Treat the imported result as a baseline to normalize, not as perfect source parity.

## SVG and vectors

Pasted or HTML-authored SVG remains a real SVG subtree. Token references can be used in `fill` and `stroke`.

The Paper UI supports path selection and pen-tool editing. Current roadmap items include improved snapping, resizing/cropping, converting shapes to paths, and Boolean operations. Verify the live roadmap before describing any of those as shipped.

Use vectors for real icons and marks. Do not use emoji as a substitute.

Sources: https://paper.design/docs/svg and https://paper.design/roadmap

## Token round-trip

Treat code tokens as source of truth when a production system already exists. Otherwise derive a restrained semantic set from an approved Paper frame.

Supported namespaces in the 2026-08 docs:

- `--color-*`
- `--font-*`
- `--font-weight-*`
- `--text-*`
- `--leading-*`
- `--tracking-*`
- `--spacing-*`
- `--container-*`
- `--breakpoint-*`
- `--radius-*`

Prefer Tailwind v4-compatible names and units. Use pixels for font size, spacing, container, breakpoint, radius, and normally line height; use `em` for tracking.

### Code to Paper

1. Locate the actual theme/CSS variables in the codebase.
2. Map them to Paper's supported token types without renaming casually.
3. Use `get_tokens` first to avoid duplicates.
4. Create the smallest complete foundation, not hundreds of speculative tokens.
5. Bind styles with `var(--token-name)`.
6. Use `find_nodes` to confirm token adoption and locate remaining literals.
7. Update a token only after inspecting its current use; screenshot the affected artboards.

### Paper to code

1. Export tokens as Tailwind or CSS with `get_tokens`.
2. Compare names and semantics with the repository's existing theme.
3. Translate intentionally; do not fork a second design system merely to match Paper output.
4. Preserve aliases where useful.
5. Verify the compiled app at all represented breakpoints.

Tokens copied between Paper files are copies, not a synchronized library. Paper's docs and product may move at different speeds; verify the live guide and current build log before claiming whether direct UI creation, theme classes, multiple modes, or other token operations are available.

Source: https://paper.design/docs/tokens

## Responsive design

Represent materially different breakpoints with separate selected artboards. Give each artboard its real width and let content determine height when necessary.

- Desktop default: 1440×900.
- Tablet default: 768×1024.
- Mobile default: 390×844 and include the live-guide status bar unless the experience intentionally hides system chrome.

Responsive work should reuse the same semantic tokens and content but can change composition, ordering, visibility, density, and line breaks. The mobile version is not a scaled desktop screenshot.

## Paper to production code

Before implementation:

1. keep Paper structure code-friendly with flex layouts and named containers;
2. select the exact approved frame;
3. read JSX and exact styles rather than eyeballing a screenshot;
4. retrieve image fills or original asset URLs explicitly;
5. identify every represented breakpoint;
6. write or update an explicit component or screen spec for data, queries, states, interactions, invariants, responsive rules, and accessibility;
7. inspect the existing implementation and make a repository-native component plan.

After extraction:

- remove export-only IDs and incidental wrappers;
- preserve semantic HTML and accessibility;
- normalize font inheritance and token aliases;
- use the repository's components and translation system;
- implement states and interactions absent from the static canvas;
- run the real app and compare screenshots at matching viewports;
- repeat render → capture → compare → correct until the agreed visual tolerance is met;
- run behavior and accessibility checks separately from visual comparison;
- checkpoint source control before a large next iteration.

Read [Repo-aware implementation](repo-aware-implementation.md) for the complete spec, architecture-mapping, and verification loop.

For export artifacts, choose by intent:

- PNG is a reliable visual snapshot; use explicit scale for delivery density.
- Combined PDF is effective for review and presentation, but verify page rendering and document accessibility separately.
- Full-artboard SVG may contain a `foreignObject`, expanded browser styles, and embedded fonts. It is not automatically a compact, portable production asset.
- For a production vector, export or reconstruct the specific SVG node rather than an entire HTML-like artboard.

Paper's own MCP guide recommends building a small section first, then expanding. Larger frames increase translation errors.

## Manual tweak reconciliation

After a person changes the canvas manually:

1. re-read the relevant subtree and styles;
2. summarize only the detected differences;
3. check whether the changed values remain token-bound;
4. run a screenshot checkpoint;
5. update implementation specs or code only after the revised canvas is approved.

This closes the loop demonstrated in Paper's own real workflows: agent reskin, human adjustment, agent re-inspection, then production transfer.
