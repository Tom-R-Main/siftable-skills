# Paper quality playbook

Use this reference for new visual directions, generic-looking agent output, style drift, and detailed canvas QA.

## Choose a point of view

Start from a physical or cultural register rather than an abstract color trend: editorial, gallery, mineral, maritime, industrial, bookish, chapel, signage, terminal, instrument panel, botanical, nocturnal, or another concrete scene.

Name the objects behind the colors. One intense accent is usually stronger than five unrelated accents. Pure white is a normal ground for high-chroma product/editorial work; off-white is a specific aesthetic choice, not a universal mark of taste.

Avoid reflexive combinations that make generated work look interchangeable:

- warm cream with orange/terracotta;
- dark navy with electric purple, lime, or teal;
- generic gradients and heavy shadows;
- every piece of information boxed into a card;
- three “directions” that differ only in color.

For multiple directions, vary the underlying point of view: hierarchy, density, composition, imagery, type personality, and interaction emphasis.

## Diagnose the agent look

Treat these as prompts to investigate, not automatic prohibitions:

- **Typography proliferation**: too many sizes, weights, labels, and tiny all-caps kickers create a noisy hierarchy. Consolidate roles; use spacing, position, scale, and contrast instead of bold everywhere.
- **Container reflex**: every idea becomes a card, pill, badge, or bordered box. Delete wrappers that do not group, separate, afford, or prioritize anything.
- **Ornamental metadata**: arbitrary numbers, icons, corner marks, and status labels fill space without helping comprehension. Remove them unless they carry real information.
- **Effects without a job**: gradients, shaders, glows, shadows, cursor-following elements, scroll hijacking, and timed fade-ins attract attention without explaining the product. Keep an effect only when it clarifies state, reinforces meaning, or expresses the specific brand.
- **Interaction head fakes**: clickable things fade away, non-actions look clickable, critical controls appear only on hover, or automatic motion changes the interface while the user reads. Make affordances stable, discoverable, and valid on touch devices.
- **Fragmented visual grammar**: neighboring sections use unrelated radii, shadows, type rules, colors, illustration styles, or interaction behavior. Normalize them through tokens and explicit exceptions.
- **Template messaging**: vague claims, invented jargon, generic social proof, or multiple competing calls to action obscure what the product is, who it serves, and why it matters. Rewrite around the user's language and one primary action.
- **Unrequested completeness**: gratuitous dark mode, dashboards, settings, or extra states appear because generation made them cheap. Keep only scope that advances the actual product goal.
- **Unreviewed output**: clipping, weak contrast, inconsistent asset treatment, broken transitions, and responsive failures reveal that the first generation was accepted without human editing.

Run the distinctness test after cleanup: hide the logo and ask whether the composition, content, type, imagery, and interaction still express this product rather than a generic software category. If not, revisit the point of view instead of adding more decoration.

## Product versus expressive work

- For product flows, optimize legibility, task hierarchy, state, and novice comprehension.
- For marketing, brand, and portfolio work, allow more asymmetry, scale contrast, and one or two playful devices.
- Do not let visual novelty conceal a dead-end product flow.
- Use real or realistic content. Placeholder copy often hides wrapping, density, and information-priority failures.

## Typography

- Verify families and available weights before styling.
- Use strong contrast between display and labels.
- Tighten large display tracking slightly; keep tiny labels open enough to read.
- Avoid body text at 12px or below unless density truly requires it.
- Use explicit pixel line heights to keep Paper-to-code translation stable.
- Screenshot at 2× only when small type or fine details need inspection.

## Layout

- Group related information with tighter spacing; use larger gaps between conceptual regions.
- Prefer a small number of strong surfaces over a uniform card grid.
- Use fixed-width lanes for icons, status markers, and actions in repeated rows.
- Use asymmetric scale or negative space deliberately, not as accidental leftovers.
- For overflow, use `height: fit-content`; do not guess a new artboard height.
- Keep decorative absolute layers from covering the entire artboard and blocking canvas selection.

## Review checkpoint

After each meaningful section, inspect the screenshot as a senior designer and state a one-line verdict:

1. **Spacing** — rhythm, groupings, cramped or accidental voids.
2. **Typography** — hierarchy, line height, wrapping, small text.
3. **Contrast** — readable at a glance, including muted text.
4. **Alignment** — shared lanes and consistent repeated-row geometry.
5. **Artboard fit** — no clipping or accidental overflow.
6. **Repetition** — sufficient variation in scale, weight, or spacing.

Then make targeted corrections. Preserve good work instead of deleting the whole artboard.

## Collaboration loop

Use comments as work items when available:

- list open threads;
- read the full relevant thread;
- change only the pinned or clearly related area;
- verify visually;
- resolve the thread only when its feedback is fully addressed.

For live human edits, re-inspect rather than assuming the agent's previous state still matches the canvas.

## Final canvas QA

- Exact copy is present and not truncated.
- Tokens are used where system semantics exist.
- Repeated rows align at desktop and mobile widths.
- SVGs remain vectors and images have retrievable sources.
- Responsive artboards represent composition changes, not scaling.
- Meaningful groups have useful layer names.
- No agent working indicators remain.
- The handoff distinguishes live-tested operations from docs-only claims.
