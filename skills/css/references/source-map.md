# CSS source map

Use the target project's installed versions and styling entrypoints first.
Reference corpora and source checkouts are optional; none are bundled here.

## Browser CSS

- [MDN CSS reference](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference)
  documents properties, selectors, at-rules, and browser support.
- If the user provides a generated MDN-derived reference, set
  `CSS_REFERENCE_FILE` to its absolute path. Search symbols rather than saved
  line numbers, and check its generation date before browser-support claims.

```sh
rg -n 'Style rule syntax|Selectors|@layer|Custom properties' "$CSS_REFERENCE_FILE"
```

Do not assume a generator exists or fetch a corpus without authorization.

## Tailwind

Detect the installed version from the lockfile and package metadata. Inspect
`node_modules/tailwindcss` or the framework integration's resolved package.
The compiler checklist describes v4; v3 configuration differs.
[Official documentation](https://tailwindcss.com/docs) must match the selected version.

For source investigation, optionally set `TAILWIND_REFERENCE_DIR` to a checkout
matching the installed package version. Verify its tag/commit before borrowing
APIs; current upstream HEAD may have different behavior.

Relevant v4 paths under that checkout:

- `packages/tailwindcss/index.css`: layer order and imports.
- `packages/tailwindcss/src/ast.ts`: AST nodes.
- `packages/tailwindcss/src/index.ts`: parse/compile and at-rule handling.
- `packages/tailwindcss/src/compile.ts`: candidate compilation.
- `packages/tailwindcss/src/theme.ts`: variable resolution.
- `packages/@tailwindcss-postcss/src/index.ts`: scanner/integration.

```sh
rg -n '@theme|@utility|@variant|@apply|@tailwind utilities' "$TAILWIND_REFERENCE_DIR/packages/tailwindcss/src"
rg -n 'parseCandidate|compileCandidates|compileAstNodes|getVariantOrder' "$TAILWIND_REFERENCE_DIR/packages/tailwindcss/src"
```

## Validation

Inspect and run the target project's declared CSS, lint, test, and build gates.
For Tailwind source work, inspect that checkout's own contributor guidance and
scripts. For visual changes, drive the relevant route in an available browser,
inspect computed styles, and check responsive and interaction states. Static
inspection or a passing build alone does not qualify a visual fix.
