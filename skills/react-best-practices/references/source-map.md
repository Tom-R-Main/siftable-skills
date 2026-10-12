# Source Map

This skill adapts the Vercel Labs `agent-skills` React best-practices skill at:

`https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices`

The upstream corpus is a React and Next.js performance guide from Vercel Engineering, version 1.0.0, dated January 2026. It organizes rules into these areas:

- Eliminating waterfalls: cheap guards before awaits, defer awaits, dependency-based parallelization, API route promise scheduling, `Promise.all`, and Suspense boundaries.
- Bundle size: barrel imports, statically analyzable paths, dynamic imports, third-party deferral, conditional loading, and intent-based preload.
- Server-side performance: Server Action auth, per-request and cross-request caching, RSC prop serialization, static I/O hoisting, request-state isolation, parallel fetching, nested fetches, and non-blocking post-response work.
- Client data: SWR-style deduplication, global event listener deduplication, passive listeners, and localStorage schema minimization.
- Rerender optimization: deferred state reads, memoized components, stable default values, primitive dependencies, derived state, functional state updates, lazy initialization, split hooks, event-handler logic, transitions, deferred values, refs for transient data, and avoiding inline component declarations.
- Rendering performance: SVG wrapper animation, `content-visibility`, static JSX hoisting, SVG precision, hydration mismatch handling, Activity, explicit conditional rendering, resource hints, script loading, and transition-based loading states.
- JavaScript performance: DOM/CSS batching, maps and sets, property access, function result caches, storage caches, combined iterations, early exits, hoisted regexes, min/max loops, immutable array methods, `flatMap`, and idle callbacks.
- Advanced patterns: effect-event dependencies, stable event handler refs, one-time app initialization, and latest-callback access.

Local adaptations:

- The main `SKILL.md` is shorter than upstream and uses progressive disclosure.
- Guidance is TypeScript-first and expects `$typescript` to handle compiler/toolchain detection and validation.
- Dependency recommendations are conservative: do not add SWR, `better-all`, or LRU packages unless already present or approved.
- Deep import guidance includes a strict-TypeScript declaration check before replacing barrel imports.
- Performance claims require local before/after evidence rather than upstream impact numbers alone.
