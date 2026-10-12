---
name: css
description: Implement, debug, and review CSS and Tailwind styling. Use for selectors, cascade, layers, custom properties, responsive layouts, computed styles, and compiler behavior.
---

# CSS

## Overview

Use this skill for styling work where browser CSS semantics matter, including Tailwind. Treat CSS as the browser rule language first, then Tailwind as a compiler and authoring layer that emits CSS.

## Workflow

1. Detect the local styling stack before editing: framework, bundler, Tailwind version/config, CSS entry files, PostCSS/Vite plugins, design tokens, global styles, and nearby component conventions.
2. Classify the problem and read only the relevant reference:
   - Browser CSS semantics, selectors, cascade, layers, inheritance, custom properties, and value grammar: `references/css-browser-model.md`.
   - Tailwind source behavior, generated utilities, `@theme`, `@utility`, `@variant`, `@apply`, `@tailwind utilities`, scanning, and candidate compilation: `references/tailwind-compiler.md`.
   - Local docs/source paths and useful grep commands: `references/source-map.md`.
3. Use `$typescript` or `$react-best-practices` alongside this skill when styling changes touch `.ts`, `.tsx`, React props, component state, hydration, or route-level behavior.
4. Prefer the project's existing styling system. Do not introduce Tailwind, Sass, CSS Modules, CSS-in-JS, or a new design-token scheme unless the repo already uses it or the user asks.
5. For Tailwind specifics, inspect the installed package or an optional version-matched checkout before relying on memory. Configure `TAILWIND_REFERENCE_DIR` only when such a checkout exists; v4 compiler behavior differs from v3 configuration.
6. Validate visually and mechanically. Run the project's CSS/build/type/test gates where available, then use browser/computed-style inspection for user-facing layout, cascade, responsive, animation, or interaction changes.

## CSS Bias

- Start from the DOM and cascade, not from class strings alone. Identify the element, matching selectors/utilities, layer/order, specificity, inheritance, and computed value.
- Prefer small CSS changes that preserve semantics: native layout primitives, logical properties, accessible focus states, and tokenized colors/spacing when the project has tokens.
- Treat `@layer` order as a cascade contract. In Tailwind v4-style entry CSS, `theme`, `base`, `components`, and `utilities` are explicitly layered.
- Treat custom properties as cascading data. A `var(--x)` result depends on where `--x` is declared, inherited, overridden, and possibly emitted by Tailwind `@theme`.
- Avoid `!important` until layer/order/specificity and source placement are understood. If it is needed, explain the cascade reason.
- Use feature queries, media/container queries, and progressive enhancement when support or viewport behavior matters. Check MDN for exact syntax and browser notes.

## Debugging Checklist

- Is the rule generated and loaded in the page?
- Does the selector or utility actually match the element?
- Which declaration wins by origin, importance, layer, specificity, scope, and source order?
- Is the expected value invalid for that property, causing the declaration to be dropped?
- Is an inherited/custom property value different at this element than at `:root`?
- Does a variant, media query, container query, pseudo-class, or data/aria selector need a missing state?
- In Tailwind, did the scanner see the class candidate as a static string, and is `@tailwind utilities` present where generated CSS should be inserted?
