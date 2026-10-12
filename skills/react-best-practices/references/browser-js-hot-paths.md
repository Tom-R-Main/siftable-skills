# Browser JS Hot Paths

Use this reference for JavaScript hot paths inside React apps: loops, lookups, DOM writes, storage, regular expressions, immutable arrays, and idle work.

## When To Use

Apply these rules after larger React and data-flow issues are handled, or when profiling/code shape points to a specific hot path. Do not trade readability for micro-optimizations on cold paths.

## Lookups And Iteration

Use `Set` or `Map` for repeated membership and lookup checks. Building the map has a cost, so do it once per stable input, not inside every item render.

Combine repeated array passes when each pass walks the same large array and the code remains readable. Use a single loop for multiple buckets, min/max, or validation with early exits.

Use `flatMap` for map-and-filter flows when it improves clarity and removes an intermediate array. Be aware that `filter(Boolean)` can narrow incorrectly; prefer typed predicates when preserving non-null types matters.

## Immutability

Do not mutate props or state arrays. Prefer `toSorted`, `toReversed`, `toSpliced`, and `with` when the target runtime supports them. Use spread-and-sort fallback for older runtimes.

Check the project's `target`, `lib`, browserslist, and polyfill strategy before using newer array methods.

## Storage And Cookies

`localStorage`, `sessionStorage`, and `document.cookie` are synchronous. Cache repeated reads in memory and keep the cache in sync on writes.

Invalidate storage caches on the `storage` event when other tabs can modify the value. Clear or refresh cookie caches when returning to a visible tab if the server can update cookies.

Parse stored JSON through `unknown` and narrow. Never cast storage data directly to an application type.

## DOM And CSS

Batch DOM reads and writes to avoid layout thrashing. Prefer class changes or `cssText` updates over many scattered style writes when updating several properties together.

Use passive listeners for scroll/touch/wheel handlers that do not call `preventDefault`.

## Regular Expressions And Properties

Hoist static `RegExp` objects to module scope. For dynamic regexes, memoize by the dynamic input and escape user-provided text.

Avoid global regex reuse with `.test()` unless you understand and reset `lastIndex`.

Cache repeated object property access in very hot loops only when profiling or algorithmic structure justifies it. Prefer clear code elsewhere.

## Idle Work

Use `requestIdleCallback` for non-critical analytics, prefetch, persistence, and chunked background processing. Provide a fallback when the target browsers do not support it, and use a timeout for work that must eventually run.

Do not schedule user-visible updates, required validation, or security-sensitive work as idle tasks.
