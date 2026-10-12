# Bundle And Server

Use this reference for bundle size, import shape, dynamic imports, third-party code, Server Components, Server Actions, RSC props, and cache boundaries.

## Bundle Priority

1. Keep heavy code out of the initial client bundle.
2. Avoid import forms that force whole libraries into development or server cold starts.
3. Split client-only features at interaction boundaries.
4. Defer analytics, telemetry, editors, charts, maps, and other non-critical libraries until they are needed.

## Imports

Avoid barrel imports only when the bundler/framework cannot optimize them. In Next.js 13.5+, prefer `optimizePackageImports` or the framework-supported public import path when available; it preserves TypeScript declarations and editor support.

Before changing to a deep import, verify the subpath has declarations. A faster import that becomes implicit `any` is not acceptable under strict TypeScript.

Common high-impact packages include icon sets, UI libraries, utility libraries, date libraries, and Rx-style packages. Match the local bundler's behavior before doing broad import rewrites.

## Dynamic And Conditional Imports

Use `next/dynamic` or dynamic `import()` for heavy UI that is not required for first interaction. Prefer feature-activation boundaries over arbitrary file splits.

```tsx
const ChartPanel = dynamic(() => import("./ChartPanel"), {
  loading: () => <ChartSkeleton />,
});
```

For browser-only modules, guard SSR:

```ts
if (enabled && typeof window !== "undefined") {
  const { loadEditor } = await import("./editor");
  await loadEditor();
}
```

Keep dynamic imports statically analyzable. Avoid computed paths that pull an entire directory into the bundle or server trace.

## Third-Party Work

Load non-critical analytics, logging, heatmaps, and support widgets after hydration or after user intent. Keep required compliance/security scripts in their required loading mode, and document that constraint.

For preloading, use hover/focus/viewport intent where it materially improves perceived speed. Do not preload everything; that recreates the initial-bundle problem.

## Server Components And Serialization

Minimize props crossing from Server Components into Client Components. Send IDs, labels, booleans, and small DTOs, not entire records or duplicated nested data. Derive client-specific DTO types from server schema or return types rather than hand-copying shapes.

Avoid passing the same large object through several client boundaries. Put a client island at the smallest interactive region and keep static rendering on the server.

## Server Actions And Auth

Authenticate and authorize Server Actions like API routes. Treat form input and action payloads as untrusted; parse to a precise type before performing mutations.

Do not rely on a client component hiding a button as authorization.

## Caching

Use `React.cache()` for per-request deduplication in Server Components. Use an LRU or external cache for cross-request reuse only when the data is safe to share across requests and the cache key includes tenant, locale, auth, and feature dimensions that affect the result.

Never store request-specific mutable state in module scope. Module state is shared across requests in SSR/RSC environments and can leak data between users.

Hoist static I/O to module scope only when it is truly static: fonts, build-time assets, metadata, and process-wide constants. Keep tenant/user/request-specific work inside the request path.

Use non-blocking post-response work (`after()` in supported Next.js versions) for analytics or cleanup that should not delay the response. Do not use it for work the user is waiting on.
