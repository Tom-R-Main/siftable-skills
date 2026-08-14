---
name: typescript
description: Write, review, debug, migrate, or optimize TypeScript in any project. Use for .ts/.tsx files, tsconfig, type errors, generics/conditional/mapped/template-literal types, narrowing & discriminated unions, declaration (.d.ts) files, module-resolution problems, React/JSX typing, and strictness migrations — and to typecheck, build, test, and actually run the artifact. Prioritize local toolchain detection (tsc version, tsconfig, package manager), strict mode, parse-don't-validate, deriving types over duplicating them, and the project's existing patterns over memory.
---

# TypeScript

Domain + run skill for working on **any** TypeScript project: implementation,
review, type-system design, migration, and actually typechecking/building/running
the artifact. TypeScript's type system is structural and large — prefer the repo's
pinned compiler, nearby working code, and the official docs over memory.

Resolve `TYPESCRIPT_SKILL_DIR` to the directory containing this `SKILL.md`.
Run its scripts from the **target package root** (the directory with `package.json`
or `tsconfig.json`).

## First moves (detect the toolchain before editing)

```sh
node_modules/.bin/tsc --version 2>/dev/null || npx tsc --version   # the pinned compiler
ls package-lock.json pnpm-lock.yaml yarn.lock bun.lock* 2>/dev/null # package manager
find . -maxdepth 2 -name 'tsconfig*.json' -not -path '*/node_modules/*'
node -e "console.log(Object.keys(require('./package.json').scripts||{}).join(' '))"
```

Then read the nearest `tsconfig.json`: is `strict` on? `noUncheckedIndexedAccess`?
`moduleResolution` (`bundler` vs `nodenext` changes import rules)? Is it a monorepo
with `references` (needs `tsc -b`)? Match the codebase's patterns unless the task is
explicitly a migration. For current language/lib questions check the handbook
(`typescriptlang.org/docs/handbook`) and the tsconfig reference; report the version
assumption when it affects the answer.

**Native port (TS 7):** a repo may compile with `tsgo` (`@typescript/native-preview`,
the Go rewrite; the binary becomes `tsc` at the 7.0 RC). It's a drop-in CLI —
`--noEmit`, `-p`, `-b`, `-w` map 1:1 — and reuses the **same diagnostic codes, lib
types, and compiler options**, so everything in this skill still applies. It's
preview: keep the project's pinned `tsc` as the authoritative gate and treat `tsgo`
as a fast cross-check (one removed-options trap is in Gotchas).

## Run / drive a TS project (agent path) — do this first

`drive.sh` runs the gates, runs the `build` script, then launches any declared
`bin` to confirm the artifact starts — the floor for "I ran it," not just "tests
pass." Run from the package root:

```sh
"$TYPESCRIPT_SKILL_DIR/scripts/drive.sh"              # gates + build + probe bins (--help)
"$TYPESCRIPT_SKILL_DIR/scripts/drive.sh" --version    # probe with a different flag
```

`drive.sh` is the floor. To drive a real flow, extend per project type:

- **CLI:** run the built entry with representative args; assert exit code + output.
  `node dist/cli.js <args>`, or `<pm> run <script> -- <args>` (e.g. `tsx src/cli.ts`).
- **Server / API:** start it (`<pm> run start:dev`), then `curl` a health route and
  assert the response; tear it down. Don't claim "it works" off a clean typecheck.
- **Web app:** `<pm> run build` must pass; then run `vite preview` or the project's
  dev server and drive a representative flow with available browser automation.
- **Library / module:** no bin; the gates are the smoke. Add a tiny test or
  `node -e "require('./dist').thing()"` (or `tsx -e`) that imports and calls it.

## Validation gates

After touching TypeScript, run narrow→broad. `ts-gates.sh` auto-detects the package
manager, prefers your `package.json` scripts, and falls back to a direct `tsc`:

```sh
"$TYPESCRIPT_SKILL_DIR/scripts/ts-gates.sh"
```

…which is, in order, equivalent to (and you can run by hand):

```sh
tsc --noEmit          # or `tsc -b` for project references — THE type gate
<pm> run lint         # if defined
<pm> run test         # if defined
```

Knobs: `SKIP_TS_TYPECHECK=1`, `SKIP_TS_LINT=1`, `SKIP_TS_TEST=1`,
`TS_TSCONFIG=path/to/tsconfig.json`, `TS_USE_TSGO=1` (cross-check with the native
TS 7 compiler if `node_modules/.bin/tsgo` is present). **`tsc --noEmit` is the gate that matters** —
a green test run with type errors is not green. Only claim a perf win with
before/after numbers; the type system has zero runtime cost (it's all erased), so
"optimization" usually means runtime JS, not types.

## Implementation bias

Make illegal states unrepresentable, and let the compiler prove the rest.

- **Strict mode on.** `strict` + `noUncheckedIndexedAccess`. Treat `tsc --noEmit`
  as a hard gate, not advice.
- **Parse, don't validate.** Narrow `unknown` at the boundary into a precise type
  once; downstream code receives the narrow type, not re-checks. Type external
  input (`JSON.parse`, network, `catch`) as `unknown`, never `any`.
- **Derive, don't duplicate.** `typeof`, `keyof`, indexed access, `ReturnType`, and
  the utility types let one source of truth generate the rest. Don't hand-copy shapes.
- **Discriminated unions + exhaustive switches** over optional-everything bags;
  close them with `assertNever` so a new variant is a compile error.
- **`type` by default, `unknown` over `any`, `satisfies` over `as`.** Above all,
  match the surrounding file's idiom.

## References (open as needed — checklists, not laws)

- `references/ts-type-system.md` — type vs interface, unions/intersections/tuples,
  generics, conditional/mapped/template-literal types, deriving types, utility types.
- `references/ts-narrowing.md` — control flow analysis, all narrowing forms, type
  predicates, assertion functions, discriminated unions, never/exhaustiveness.
- `references/ts-conventions.md` — opinionated project conventions for co-location,
  constant naming, parameter destructuring, filter inference, arktype, and enums.
- `references/ts-config-modules.md` — tsconfig strictness, module resolution/output,
  classes, decorators (stage-3 vs legacy), `.d.ts` authoring.
- `references/ts-react-jsx.md` — typed React: props, hooks, events, generic
  components, discriminated props.
- `assets/tsconfig.strict.json` — copyable strict baseline.

If local compiler errors or nearby working code disagree with a reference, follow
the project and note why.

## Gotchas (high-value TS traps)

- **`as` is not a cast — it's a compile-time *assertion* that can lie.** It does no
  runtime conversion and silently permits unsafe narrowing. Want checking-without-
  widening? Use **`satisfies`** (TS 4.9+): `const c = {…} satisfies Config` checks the
  shape *and* keeps the narrow literal types — whereas both `as Config` and a `: Config`
  annotation widen (`c.a` becomes the declared type, not its literal). Reserve `as` for
  genuinely unknowable cases (prefer `as unknown as T` to flag the danger).
- **Excess-property checks only fire on *fresh* object literals.** Assigning through
  an intermediate variable bypasses the check — so an unexpected "object literal may
  only specify known properties" error usually means a typo or wrong shape, and
  "bypassing" it by extracting a variable hides a real bug.
- **`noUncheckedIndexedAccess` is OFF even under `strict`.** Without it `arr[i]` and
  `record[key]` are typed `T` (not `T | undefined`) and walk straight off the end at
  runtime. Turn it on; it surfaces the most common silent crash.
- **`any` poisons transitively** — its members are `any`, so one `any` disables
  checking far downstream. Use `unknown` and narrow.
- **`typeof null === "object"` and `typeof [] === "object"`.** `typeof` won't
  separate null/array from objects — use `=== null` / `Array.isArray` (see narrowing).
- **Types are erased** — no runtime reflection. You can't `instanceof` an
  `interface`/`type`; branch on a discriminant value, not a type.
- **Floating promises.** An un-`await`ed async call swallows errors and races. Await
  it or explicitly `void` it; enable `@typescript-eslint/no-floating-promises`.
- **Type-only imports under `verbatimModuleSyntax`/`isolatedModules`** must use
  `import type` or you get runtime/emit errors. `const enum` is banned there too.
- **Decorators come in two incompatible flavors** — NestJS/TypeORM/Angular need
  legacy `experimentalDecorators` (+ `emitDecoratorMetadata`); TS 5 defaults to
  stage-3. Check before adding any. (The native `tsgo`/TS 7 compiler implements legacy
  decorators but not stage-3 decorator *metadata* yet.)
- **On `tsgo`/TS 7, some legacy tsconfig options are *removed*, not just deprecated**
  — `baseUrl`, `outFile`, `target: ES5`, `module: amd|system|umd`, `moduleResolution:
  classic`, and the `*: false` interop toggles become hard errors (`TS5102`/`TS5108`).
  `baseUrl` bites most — replace it with `paths` using explicit relative roots.

## Troubleshooting (error → fix; codes are stable across `tsc` and `tsgo`)

- **TS2532 / TS18048** `Object is possibly 'undefined'` / `'X' is possibly 'null'` →
  narrow first (`if (x != null)`), or you just enabled `noUncheckedIndexedAccess` on
  an `arr[i]`. A *flood* of these after turning on strict flags is the point — narrow
  the now-visible `undefined`s, migrating file-by-file with `tsc --noEmit` per package.
- **TS2339** `Property 'x' does not exist on type 'A | B'` → narrow the union
  (discriminant / `in` / guard) before access — see `references/ts-narrowing.md`.
- **TS2322 / TS2345** `Type 'X' is not assignable…` / `Argument of type 'X'…` → read
  the *innermost* "not assignable" line; it pinpoints the mismatch. Check optional vs
  `| undefined` (**TS2375**, `exactOptionalPropertyTypes`); **TS2741** = a required
  property is missing.
- **TS2353** `Object literal may only specify known properties` → freshness check; fix
  the typo/shape, don't extract a variable to silence it.
- **TS2307** `Cannot find module 'x' or its type declarations` → install `@types/x`,
  add a `.d.ts` shim, or fix `moduleResolution`/`paths` (**TS2792** suggests
  `nodenext`; **TS1192** = module has no default export).
- **TS1484** `'X' is a type and must be imported using import type` (under
  `verbatimModuleSyntax`) → use `import type`.
- **TS7006 / TS7016** implicit `any` (parameter / missing declaration file) →
  annotate, or install the package's types.
- **TS2554** `Expected N arguments, but got M` → arity mismatch (often a changed signature).
- **TS2742** `inferred type of 'x' cannot be named` → add an explicit return type, or
  import the referenced type so it's nameable in the emitted `.d.ts`.
- **TS1206** `Decorators are not valid here` / metadata missing → set
  `experimentalDecorators` + `emitDecoratorMetadata` (legacy frameworks).
- **TS5102 / TS5108** `Option 'X' has been removed` → you're on `tsgo`/TS 7 and a
  legacy option is gone (see Gotchas) — most often `baseUrl` or `outFile`.
