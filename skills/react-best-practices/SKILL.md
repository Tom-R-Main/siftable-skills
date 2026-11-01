---
name: react-best-practices
description: Implement, review, and optimize React and Next.js applications with TypeScript. Use for hooks, data fetching, rendering, hydration, bundles, and measured performance.
---

# React Best Practices

## Overview

Use this skill to make React and Next.js code faster without weakening TypeScript guarantees. It adapts the Vercel React best-practices corpus into a Codex workflow and assumes performance changes must be validated with the project's own compiler, lint, tests, build, and, when relevant, browser/runtime evidence.

## Framework choice and compute boundaries

React and TypeScript can be the right choice for UI behavior, accessible components, framework integration, and a useful component ecosystem. For an authorized architecture decision, weigh those benefits against bundle, hydration, rendering, memory, and boundary costs. Use the available language skills to evaluate compute-heavy work in a native or WASM component when the workload warrants it; measure loading, marshaling, and consumer behavior before claiming a benefit. Familiarity or shorter manual implementation time alone should not decide the system architecture. An implementation request in an existing React app retains its selected stack and scope.

## Workflow

1. Detect the local stack before editing: package manager, scripts, framework, React/Next version, `tsconfig`, router model, bundler, lint rules, test setup, and nearby component idioms.
2. Use `$typescript` for TypeScript-specific work. For `.ts`/`.tsx`, run its first-move checks and resolve `TYPESCRIPT_SKILL_DIR` from the loaded TypeScript skill and run `"$TYPESCRIPT_SKILL_DIR/scripts/ts-gates.sh"` from the target package root after edits.
3. Classify the request by impact and read only the relevant reference:
   - Waterfalls, Suspense, client data fetching, event listeners, and browser storage: `references/async-and-data.md`.
   - Bundle size, dynamic imports, Next.js server work, Server Components, Server Actions, and cache boundaries: `references/bundle-and-server.md`.
   - Rerenders, hooks, memoization, transitions, hydration, JSX, and rendering behavior: `references/rendering-and-state.md`.
   - Hot JavaScript loops, DOM/CSS batching, maps/sets, storage caches, immutable arrays, idle work, and algorithmic cleanup: `references/browser-js-hot-paths.md`.
   - Upstream provenance and category mapping: `references/source-map.md`.
4. Optimize the highest-impact bottleneck first: waterfalls and bundle size usually outrank memoization; memoization usually outranks micro-optimizing loops only when profiling or code shape shows render churn.
5. Preserve correctness and type information. Avoid `any`; type external data as `unknown`; use `satisfies` over unsafe assertions; keep discriminated unions intact; use `import type` under `verbatimModuleSyntax`.
6. Do not add a runtime dependency such as SWR, `better-all`, or LRU cache unless it already exists or the user approves. Prefer native `Promise.all`, existing query libraries, or project-local helpers.
7. Validate narrowly then broadly. At minimum run typecheck/build or the TypeScript skill gates. For UI or perf-facing changes, drive the route with browser automation and only claim a performance win with before/after evidence.

## TypeScript Bias

- Keep component props explicit and derived from native element props where useful: `React.ComponentProps<"button"> & { loading?: boolean }`.
- Prefer typed route/data contracts over ad hoc object bags. Parse at boundaries and pass narrowed values into components.
- Preserve tuple inference in concurrent fetches. Use `as const` only when needed and prefer named promises when dependency structure matters.
- Check deep imports for `.d.ts` support before replacing barrel imports. If a deep import becomes implicit `any`, use framework-supported import optimization or keep the typed public import.
- Treat React hook dependency lists as type-and-runtime contracts: narrow to primitive dependencies when possible, avoid stale closures, and do not hide dependency errors with assertions.
- For client-only browser APIs, guard SSR (`typeof window !== "undefined"`) and type fallbacks against the active `lib` target.

## Review Checklist

- Are independent async operations accidentally sequential?
- Is expensive work pulled into the initial client bundle?
- Is server-only data serialized into client components unnecessarily?
- Are effects doing work that belongs in render, an event handler, or the server?
- Are dependencies stable and minimal without lying to the hook linter?
- Are memoization, transitions, or deferred values applied only where they remove real work or improve responsiveness?
- Are browser APIs guarded for SSR and invalidated when external state can change?
- Does the implementation still pass TypeScript gates and the relevant route/user-flow smoke?
