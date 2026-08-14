# tsconfig, modules, classes & declaration files

## What the compiler emits

One `.ts` file generates **`.js`** (the runtime code, types erased) and **`.d.ts`**
(the types only). The `.d.ts` is *implied by* the `.js` — it's the contract
consumers typecheck against. Types have **no runtime presence**: you cannot branch
on them at runtime (`if (x is Foo)` doesn't exist), only on values.

## Strictness flags (turn them on; they catch real bugs)

`"strict": true` turns on the whole **strict family** — keep it on:
`noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`,
`strictPropertyInitialization`, `strictBuiltinIteratorReturn` (TS 5.6+),
`noImplicitThis`, `useUnknownInCatchVariables`. The two that earn their keep most:

| Flag (inside `strict`) | Effect |
|---|---|
| `strictNullChecks` | `null`/`undefined` become distinct types you must handle. Without it they're silently assignable everywhere. **The single most valuable flag.** |
| `noImplicitAny` | error on params/vars TS can't infer, instead of a silent `any`. |

**OFF even with `strict: true` — add these deliberately** (they are *not* in the
strict family):

| Flag | Effect |
|---|---|
| `noUncheckedIndexedAccess` | `arr[i]` / `record[key]` typed `T \| undefined`. Catches the #1 silent crash. |
| `exactOptionalPropertyTypes` | `{ x?: number }` ≠ `{ x: number \| undefined }` — no explicit `undefined` into an optional. |
| `noImplicitOverride` | require `override` when overriding a base method. |
| `noUnusedLocals` / `noUnusedParameters` | flag dead bindings. |
| `noFallthroughCasesInSwitch` | flag missing `break`/`return`. |

## Key non-strict knobs

- **`target`** — JS version emitted (`ES2022`+ for modern Node/browsers).
- **`module` / `moduleResolution`** — for apps + bundlers use `"bundler"`; for
  Node ESM/CJS dual use `"nodenext"`. `moduleResolution: bundler` allows
  extensionless imports; `nodenext` requires `.js` extensions in import specifiers.
  (TS 6.0+ *computes* the default from `module`: `nodenext`/`node16`/`node18` mirror
  the module setting, else `bundler` — so set it explicitly rather than relying on it.)
- **`lib`** — ambient APIs available (`["ES2022","DOM"]` for web; drop `DOM` for
  pure Node).
- **`esModuleInterop`** — fixes `import x from "cjs"` default-import interop. Default
  `true` since TS 6.0 (still set it on for older toolchains).
- **`isolatedModules`** — each file must compile alone (required by esbuild/swc/Vite/Babel).
  Bans `const enum` and ambiguous re-exports.
- **`verbatimModuleSyntax`** — `import`/`export` are emitted verbatim; **type-only
  imports must use `import type`** or they'll be elided/kept incorrectly.
- **`skipLibCheck`** — skip checking `.d.ts` in `node_modules` (faster builds; common).
- **`paths`** (+ `baseUrl`) — path aliases (`"@/*": ["src/*"]`). The bundler/test
  runner needs the matching alias too (Vite `resolve.alias`, Jest `moduleNameMapper`).
  Note `baseUrl` is deprecated in TS 6.0 / removed in 7.0 — prefer `paths` with
  explicit relative roots.
- **`composite` / `references`** — project references for monorepos; build with
  `tsc -b`.

Type-check without emitting: **`tsc --noEmit`** (or `tsc -b` for referenced
projects). This is the gate; the bundler does the actual JS emit.

## Deprecated in TS 6.0 (hard error in TS 7.0)

`tsc` 6.0 warns "deprecated, will stop functioning in TypeScript 7.0" (silence with
`"ignoreDeprecations": "6.0"`, but prefer migrating). Under the native compiler
(`tsgo`/TS 7) these are already removed and become `TS5102`/`TS5108` errors:

- **Targets**: `target: ES5` (and `ES3`).
- **Modules**: `module` ∈ `none | amd | umd | system`; `moduleResolution` ∈
  `node10` (`node`) `| classic`.
- **Paths/output**: `baseUrl`, `outFile`, `downlevelIteration`.
- **Interop off-toggles**: `esModuleInterop: false`, `allowSyntheticDefaultImports:
  false`, `alwaysStrict: false` (these are forced on).
- **Import assertions removed** — `assert { type: "json" }` errors; use *attributes*:
  `import data from "./x.json" with { type: "json" }`.

## Type-only imports

Under `isolatedModules`/`verbatimModuleSyntax`, separate types from values:

```ts
import type { User } from "./user";          // erased at compile time
import { createUser, type UserId } from "./user";  // mixed: value + inline type
```

## Classes (TS extensions over ES classes)

```ts
class User extends Account implements Updatable {
  id: string;                 // field
  displayName?: string;       // optional field
  readonly createdAt = new Date();  // readonly + default
  private secret = "x";       // TS-only private (compile-time; visible at runtime)
  #token = "y";               // JS-native private (enforced at runtime)
  static count = 0;           // static member
  constructor(public name: string) { super(); }  // parameter property: declares+assigns this.name
  get id2() { return this.id; }            // getter
  set id2(v: string) { this.id = v; }      // setter
}

abstract class Shape { abstract area(): number; }  // can't instantiate; subclass must implement
```

- `private` (TS) is erased and only enforced at type-check time; `#field` is truly
  private at runtime. Prefer `#` when runtime privacy matters.
- `implements` only checks conformance — it does **not** inherit. A class can be a
  type and a value; don't `class C implements SomeClass {}` expecting fields.
- Parameter properties (`constructor(public x: number)`) declare and assign in one
  line.

## Decorators — two incompatible systems

- **Stage-3 / TC39 decorators** (TS 5.0+, default, no flag): the modern standard.
- **Legacy decorators** (`"experimentalDecorators": true`): required by **NestJS,
  TypeORM, Angular**, and anything using `reflect-metadata` + `emitDecoratorMetadata`.

They are not interchangeable. Check which a framework needs before adding decorators.

## Declaration files (`.d.ts`)

Author types for untyped JS or to describe a global/ambient API.

```ts
// module augmentation — add to an existing module's types
declare module "express" {
  interface Request { userId?: string; }
}

// ambient global (no import needed)
declare global {
  interface Window { __APP_CONFIG__: AppConfig; }
}

// typing an untyped npm package: declarations/foo.d.ts
declare module "untyped-pkg" {
  export function doThing(x: string): number;
}
```

First look for `@types/<pkg>` (DefinitelyTyped) before hand-writing. "Cannot find
module or its type declarations" → install `@types/...` or add a `.d.ts` shim.
