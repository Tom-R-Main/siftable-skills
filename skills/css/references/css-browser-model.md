# CSS Browser Model

Optional local search examples below require `CSS_REFERENCE_FILE` to point to
an existing, user-configured MDN-derived reference file. Without it, use the
[official MDN CSS reference](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference).

## Contents

- Rule shape
- Selectors
- Cascade and layers
- Custom properties
- Validation and browser debugging

## Rule shape

CSS turns document structure into visual formatting. The basic browser-level shape is:

```css
selector {
  property: value;
}
```

The local generated MDN CSS reference says a style rule is a selector list plus a property list, and each property has its own valid value grammar. For exact syntax, search:

```sh
rg -n "Style rule syntax|properties-list|selectors-list" "$CSS_REFERENCE_FILE"
```

## Selectors

Selectors decide which DOM elements a rule applies to. Check type selectors, class selectors, ID selectors, attributes, combinators, and pseudo selectors before assuming a declaration is wrong.

Useful MDN search:

```sh
rg -n "^## Selectors|Basic selectors|Combinators|Pseudo" "$CSS_REFERENCE_FILE"
```

Practical debugging order:

1. Confirm the target element exists in the DOM.
2. Confirm the selector or Tailwind variant selector matches that element.
3. Inspect computed styles and matched rules in the browser.
4. Check whether a rule is present but crossed out by the cascade.

## Cascade and layers

Resolve conflicts through the cascade before changing CSS. The high-value order is:

1. Origin and importance.
2. Cascade layer order.
3. Specificity.
4. Scoping proximity and source order.
5. Inheritance, initial values, and user-agent defaults.

For `@layer`, MDN notes that normal unlayered author styles override normal layered styles, and that later-declared layers beat earlier-declared layers for normal declarations. Important declarations reverse the layer order. Search:

```sh
rg -n '^# `@layer` CSS at-rule|Styles that are not defined in a layer|first declared layer' "$CSS_REFERENCE_FILE"
```

Tailwind makes this especially important because its package entry CSS declares:

```css
@layer theme, base, components, utilities;
```

That gives `utilities` higher normal layer priority than `components`, `base`, and `theme`.

## Custom properties

Custom properties are CSS variables. MDN describes `--foo` properties as reusable with `var()`, scoped to elements, and participating in the cascade.

Search:

```sh
rg -n "^# Custom properties|participate in the cascade|var\\(\\)" "$CSS_REFERENCE_FILE"
```

Practical implications:

- `:root` is only a common declaration site, not a magic global override.
- The winning custom property value is computed per element.
- Invalid fallback or invalid final values can make the consuming declaration fail.
- Tailwind `@theme` emits variables that later resolve through `var(--...)` unless configured inline.

## Validation and browser debugging

For user-facing styling, validate in a browser. Prefer computed-style checks over eyeballing generated CSS:

```js
getComputedStyle(document.querySelector(".target")).getPropertyValue("color")
```

When debugging layout, inspect the actual box model: containing block, display mode, grid/flex formatting context, min/max constraints, overflow, stacking context, transform, and position.

When a declaration appears ignored:

- Check whether the property name is valid.
- Check whether the value grammar matches that property.
- Check whether a later or more specific declaration wins.
- Check whether a media/container query or pseudo-class is inactive.
- Check whether a Tailwind class was generated at all.
