# Tailwind Compiler Model

## Contents

- Mental model
- Entrypoint layers
- AST and directives
- Utility generation path
- Theme variables
- Implementation guidance

## Mental model

For Tailwind v4 source matching the project pin, Tailwind is best understood as a CSS compiler, not as CSS itself. It parses CSS, handles Tailwind-specific at-rules, scans source files for class candidates, compiles candidates into AST rules, sorts those rules, and emits CSS.

Optional version-matched checkout (set `TAILWIND_REFERENCE_DIR` first):

```sh
cd "$TAILWIND_REFERENCE_DIR"
```

Do not apply these v4 directives to v3 projects. Package layouts and source line
numbers can drift; search symbols first. If a source checkout is absent, inspect
the installed package and use version-matched official documentation.

## Entrypoint layers

Tailwind's package entry CSS declares the layer contract directly:

```css
@layer theme, base, components, utilities;
```

Source:

```sh
nl -ba "$TAILWIND_REFERENCE_DIR/packages/tailwindcss/index.css" | sed -n '1,20p'
```

This matters because browser cascade layers decide which declarations win. Normal utilities should beat normal component/base/theme declarations by layer order, while normal unlayered author CSS can still beat layered Tailwind CSS.

## AST and directives

Tailwind parses CSS into an AST with node kinds for:

- style rules
- at-rules
- declarations
- comments
- context wrappers
- at-root hoisting

Source:

```sh
nl -ba "$TAILWIND_REFERENCE_DIR/packages/tailwindcss/src/ast.ts" | sed -n '1,90p'
```

The main compiler path tracks feature flags for Tailwind-specific constructs such as `@apply`, `@import`, `theme(...)`, `@tailwind utilities`, `@variant`, and `@theme`.

Source:

```sh
nl -ba "$TAILWIND_REFERENCE_DIR/packages/tailwindcss/src/index.ts" | sed -n '117,210p'
```

High-value directives and concepts to inspect:

- `@tailwind utilities`: placeholder replaced with generated utility class CSS.
- `@theme`: records custom properties and can emit CSS variables.
- `@utility`: registers custom utilities and must be top-level in current source.
- `@variant`: applies or registers variant behavior.
- `@apply`: expands utility behavior into authored CSS, with special prefix/reference traps.
- `source(...)`: controls scanner roots for class candidate discovery.
- `@reference`: can make theme/reference behavior differ from emitted CSS behavior.

## Utility generation path

The common utility flow is:

1. Integrations create or reuse a compiler.
2. A scanner finds class candidates in source files.
3. The compiler parses candidates and variants.
4. Candidates compile into AST rules.
5. Rules are sorted by variant order and property order.
6. Generated rules replace the `@tailwind utilities` placeholder.

Sources:

```sh
nl -ba "$TAILWIND_REFERENCE_DIR/packages/@tailwindcss-postcss/src/index.ts" | sed -n '211,235p'
nl -ba "$TAILWIND_REFERENCE_DIR/packages/tailwindcss/src/compile.ts" | sed -n '11,85p'
nl -ba "$TAILWIND_REFERENCE_DIR/packages/tailwindcss/src/index.ts" | sed -n '677,705p'
```

When a utility class is missing, ask:

- Did the source scanner see the class as a static candidate?
- Is `@tailwind utilities` present and not inside a context that removes it?
- Is the candidate invalid for the active design system?
- Is a prefix required?
- Is the variant known and applicable?
- Is generated CSS present but losing in the browser cascade?

## Theme variables

Tailwind theme resolution leans on CSS custom properties. In the version-matched source, theme variable resolution returns `var(...)`, with a fallback for reference-mode values.

Source:

```sh
nl -ba "$TAILWIND_REFERENCE_DIR/packages/tailwindcss/src/theme.ts" | sed -n '193,225p'
```

Practical implications:

- Debug theme values as CSS variables in computed styles, not just as config values.
- `@theme` and `@reference` can affect whether variables are emitted or only referenced.
- Inline theme options can change whether a value resolves to a raw value or a `var(...)`.

## Implementation guidance

- For app styling, prefer authored Tailwind classes and existing tokens before custom CSS.
- For repeated semantic patterns, use project-local components or existing component layer conventions.
- For compiler/source work in Tailwind itself, use `$typescript` and the Tailwind repo's `pnpm` scripts.
- Do not invent dynamic class strings that the scanner cannot see. Prefer static complete class names, variant maps, or safelist/config mechanisms already used by the project.
- For cascade bugs, inspect generated CSS plus browser computed styles. Tailwind class order in markup is not the cascade order; generated CSS order and layers matter.
