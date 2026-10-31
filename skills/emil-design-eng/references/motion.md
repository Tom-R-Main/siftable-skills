# Motion construction and patterns

Read for requested web animation or a specific interaction-polish task. Reuse existing tokens, primitives, and library versions; timing and curves below are starting points, not required design-system replacements.

## Decide and choose

Name the purpose, expected frequency, input methods, state transitions, and interruptions before choosing effects. High-frequency work should respond immediately; do not make focus, content access, or actions wait for an entrance. Decoration needs a product reason. Existing keyboard feedback or orientation can still be useful.

Prefer explicit transition properties to `transition: all`. Choose a transition when an existing property should smoothly retarget; use keyframes or WAAPI for a defined sequence; use an existing spring/gesture driver when velocity continuity matters. Any driver needs correct cancellation and final state. CSS, keyframes, WAAPI, and a Motion prop do not by themselves guarantee a particular thread or compositing path.

For a new motion without tokens, useful initial ranges are press feedback around 100–160ms, small popovers 125–200ms, menus 150–250ms, and larger drawers roughly 200–500ms. Tune for distance and frequency, allow faster exits when they improve response, and preserve consistent product pacing. These are examples, not a universal 300ms cap or mandatory asymmetric timing.

Entrances often benefit from prompt initial movement; an ease-out curve is a useful starting point. Movement between settled positions may use ease-in-out; continuous progress may use linear timing. Use the project's curves before a custom one. A drawer, progress indicator, and celebratory illustration need not share one easing law.

## Patterns to consider, not apply automatically

- **Press feedback:** a subtle transform or existing state treatment can acknowledge input. Keep focus visible, disabled semantics correct, and precise controls stable; scaling every button is not a requirement.
- **Anchored popovers:** when scaling is appropriate, use the actual trigger-aware origin exposed by the installed primitive. Centered dialogs follow their own composition. Check collision/flipped positions rather than hardcoding the default side.
- **Entry/exit:** preserve mounted lifetime and hidden/open semantics until the transition completes. A slight scale plus opacity can work without an appearance from scale zero. Do not leave invisible controls focusable or interactive.
- **Tooltips:** a grouped tooltip primitive can delay the first hover and make adjacent tooltips immediate. Retain keyboard access and usable disclosure on touch; do not implement essential information as hover-only.
- **Tabs or clipped reveals:** animate a decorative highlight/copy while retaining one functional accessible tablist. Decorative copies must be hidden from assistive technology, unfocusable, free of duplicate IDs, and unable to intercept input.
- **Lists:** use stagger only when it helps comprehension or requested expression. Never hold content or interaction behind decorative sequencing. Layout/height transitions may be justified; they are not interchangeable with scaling text or children.
- **Blur and shadows:** optional effects, with costs dependent on area, browser, device and DPR. Do not obscure useful text or assume a small radius is free.
- **Hold or swipe actions:** a visual progress overlay does not implement the action. Define activation, cancellation, accessible alternatives, and undo/confirmation semantics before wiring any consequential effect. Use the mobile-web reference for gesture mechanics.

## Accessibility and continuity

Handle reduced motion alongside the implementation, not after it. Remove or substantially reduce nonessential translation, scale, parallax, bounce and sequencing; preserve the correct final visible/hidden state. Minimal opacity feedback is an option when appropriate, not an obligation to animate. Ensure the override actually neutralizes the original movement and exit behavior.

Gate hover-only decoration by input capabilities without removing keyboard focus feedback or touch access. Retarget from the current visual state when reversing; clean up animations/listeners on unmount and avoid stale completion callbacks after a newer state wins.

Check installed browser targets before using `@starting-style`, intrinsic-size transitions, view transitions, or primitive-specific CSS variables/data attributes. Prefer progressive enhancement; do not introduce effect-driven mount state or new runtime libraries without a demonstrated need.

## Vocabulary when it helps the brief

Use a term only to make a concrete outcome clearer: **easing** is pacing, **spring** describes a physical response, **overshoot** passes the target, **stagger** offsets multiple starts, **morph** changes shape, **shared layout** preserves identity between positions, **scrub** maps progress to another input, and **momentum** carries motion after release. These names do not select an implementation by themselves.

Validate the affected interaction through the [shared workflow](../SKILL.md#verify-the-interaction). For jank or acceleration questions, load [performance](performance.md).
