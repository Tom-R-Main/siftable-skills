# UI / interface design corpus (`--collection ui`)

Suggested reference sources; this package does not include the books or indexed chunks. Three of the four are **page-image embedded** — the figures
ARE the content, so a suitable backend can return an `image_path` to open; the text snippet is
just a caption. Tidwell is text-embedded.

## Sources

- **Refactoring UI** (Wathan & Schoger) — *page-image* — opinionated, example-driven
  tactics; sparse text, heavy before/after visuals
- **Practical UI, 2e** (Adham Dannaway) — *page-image* — chaptered guidelines,
  extremely image-heavy (~30 figures/page)
- **How to Design Better UI Components 3.0** (Kuleszo) — *page-image* — component
  patterns and tips
- **Designing Interfaces, 3e** (Tidwell, Brewer & Valencia) — *text* — interaction
  design pattern language

Themes (reference themes to investigate; Practical UI's page headers literally name its
chapters):

- **Visual hierarchy & emphasis** — de-emphasize secondary/tertiary info; size,
  weight, color, and contrast to guide the eye; separate visual from document hierarchy
- **Spacing, sizing & layout** — non-linear spacing/sizing scales, white space
  ("be generous"), grids ("grids are overrated"), baseline alignment
- **Typography** — type scales, regular/bold weights only, single-typeface
  discipline, pairing, tone (caps formal / italics informal)
- **Color** — HSL/HSB over hex, contrast ratios & accessibility, dominant + accent,
  predefined palettes
- **Depth, light & shadow** — emulate a light source from above, layered/two-part
  shadows
- **Components & patterns** — buttons, forms (required/optional fields, validation),
  modals, dropdowns/nested, accordions, cards, pricing tables, badges, nav bars
- **Interaction & navigation** — menus / context menus / toolbars, Back/Next/Up
  models, streams & feeds, task panes, spatial memory
- **Data visualization** — brushing & linked views
- **Copywriting / microcopy** — clear, recoverable error messages
- **Process & craft** — don't over-design, grayscale-first, simplicity ("less is
  more"), finishing touches
- **Accessibility & human-centered / ethical design**

## Example questions to validate against your configured backend

- `"how to establish visual hierarchy with size weight and color"` → Refactoring UI,
  Practical UI, Designing Interfaces
- `"using whitespace and spacing to reduce visual clutter"` → Practical UI,
  Refactoring UI
- `"accessible color contrast ratios"` → Practical UI (Colour chapter)
- `"button placement and order on mobile"` → How to Design Better UI Components,
  Practical UI
