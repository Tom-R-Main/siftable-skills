# Animation performance

Read for observed jank, a concrete performance hypothesis, or a requested performance review. Do not turn a static craft edit into a benchmark project. Use the actual browser, library version, driver and representative load before claiming an improvement.

## Separate the mechanisms

Record which animation updates which properties, who schedules the updates, and the runtime conditions. Distinguish layout, paint/raster, compositing, JavaScript scheduling, and React rendering. A compositor-eligible property and an off-main-thread animation driver are related but different claims.

Transform and opacity are useful initial candidates because they often avoid layout and paint, but promotion and actual cost depend on the element, effects, browser and execution path. Filters, clip paths, backgrounds, masks, and Motion shorthand behavior are especially implementation/version-sensitive. A full transform string, CSS animation, or WAAPI call alone does not prove hardware acceleration.

## Investigate a bottleneck

1. Preserve the symptom and identify the artifact, browser/device, interaction, content size and competing load. Reproduce at normal speed with existing project tooling.
2. Inspect traces or browser performance/layer/paint tools that are actually available. Locate layout reads/writes, large paints/blur, excessive layers, long JavaScript, render churn, or mounting/data-fetching work that overlaps the interaction. Distinguish a measured cause from an inferred one.
3. Vary one plausible mechanism while preserving observable semantics. Prefer smaller scope, simpler effects, batching reads/writes, less unnecessary React work, or appropriately owned transient values over a blanket driver migration.
4. Compare before and after under comparable conditions; retain relevant run counts and variability. Recheck keyboard/focus, hit-testing, accessibility visibility, interruption, layout and text quality before calling the change an improvement.

## Common traps

- Replacing width/height with scale can change flow, text, children, and hit areas. Replacing display/visibility with opacity can leave invisible controls accessible or interactive. Preserve those semantics explicitly.
- `will-change` is a potentially costly hint, not a universal fix. Use evidence, scope its lifetime, and remove it when no longer useful.
- Inherited custom properties can affect style work, but not every variable update necessarily recomputes every descendant. Preserve tokens; place high-frequency gesture values at the narrowest appropriate owner and profile the actual invalidation.
- Keep frame-by-frame decorative values out of unnecessary component renders when an existing motion value, ref or driver can own them. Retain semantic application state and predictable lifecycle cleanup.
- Isolating competing loading/rendering work may be more valuable than changing the easing. Do not hide a broken loading state or drop required work to improve a trace.
- A throttled desktop or an isolated empty screen is a useful experiment, not proof of physical-device performance or behavior under production content.

If profiling or the actual runtime is unavailable, deliver source-based hypotheses and the exact missing check. Do not report an FPS/latency win from a screenshot, generic GPU claim, or a passing build.

[Shared verification](../SKILL.md#verify-the-interaction) remains the completion standard. The reviewed [Motion performance guide](https://motion.dev/docs/performance), [MDN reduced-motion reference](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion), and [upstream provenance](provenance.md) are sources to recheck for the relevant version and browser.
