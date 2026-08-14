# TypeScript type system

Checklist for designing types. TypeScript is **structural** (duck-typed): a value
fits a type if it has the right shape, regardless of declared name. Think of types
like variables — name them, compose them, derive them; don't repeat shapes inline.

## `type` vs `interface`

Both describe object shapes; they diverge at the edges.

| | `type` (alias) | `interface` |
|---|---|---|
| Unions / intersections / tuples / primitives | ✅ `type Id = string \| number` | ❌ object shapes only |
| `extends` / `implements` hierarchies | via `&` | ✅ first-class |
| Declaration merging (reopen + add fields) | ❌ | ✅ (footgun for app code, feature for ambient/global aug) |
| Mapped / conditional / template-literal | ✅ | ❌ |

Default to **`type`** for application code (composes with the whole type system, no
surprise merging). Reach for `interface` for public, extends-heavy API surfaces and
for declaration merging / module augmentation. **Above all, match the file you're
in.** See `ts-conventions.md`.

## Object literal type syntax

```ts
type JSONResponse = {
  version: number;            // field
  /** in bytes */ payloadSize: number;  // JSDoc shows in editors
  outOfStock?: boolean;       // optional
  update: (retryTimes: number) => void; // arrow-fn field
  update(retryTimes: number): void;     // method form
  (): JSONResponse;           // callable
  new (s: string): JSONResponse;        // newable
  [key: string]: number;      // index signature (any key)
  readonly body: string;      // can't reassign
};
```

## Composing types

- **Union** `A | B` — one of several. Narrow before use (see `ts-narrowing.md`).
- **Intersection** `A & B` — has all members of both. Great for merging shapes.
- **Tuple** `[string, number]` — fixed-length array with known per-index types.
- **Literal** `"small" | "medium" | "large"` — a finite set of exact values.

```ts
type Size = "small" | "medium" | "large";   // union of literals
type Point = { x: number } & { y: number };  // intersection
type Pair  = [name: string, age: number];    // labeled tuple
```

## Deriving types from other types (don't hand-duplicate)

```ts
const config = { host: "localhost", port: 5432 };
type Config = typeof config;            // type from a value
type Port   = (typeof config)["port"];  // indexed access -> number
type Keys   = keyof Config;             // "host" | "port"

const make = () => ({ id: "x", n: 1 });
type Made   = ReturnType<typeof make>;  // type from a function's return

type Data   = import("./data").Data;    // type from a module
```

- `keyof T` — union of T's keys.
- `T[K]` — the type at key K (use `T[keyof T]` for "any value type").
- `typeof x` (type position) — the type TS inferred for runtime value `x`.
- Prefer `as const` on source data, then derive everything from it (see naming
  conventions). `as const` freezes a value to its narrowest literal types.

## Generics

A generic parameter ties inputs to outputs. **Every type parameter must be used in
a way that relates two positions** — if it appears once, it's not doing anything
(use the concrete type or `unknown`/`any` instead).

```ts
function first<T>(xs: readonly T[]): T | undefined { return xs[0]; }

// constraint: only accept types that have a .length
function longest<T extends { length: number }>(a: T, b: T): T {
  return a.length >= b.length ? a : b;
}

// default parameter
type Box<T = string> = { value: T };
```

Let TS infer type args from call sites; annotate only when inference is wrong or
you need to widen. Use `NoInfer<T>` (TS 5.4+) to block inference at a specific
position. `const` type parameters (`<const T>`, TS 5.0+) infer literal types from args.

## Conditional types — `if` for the type system

```ts
type IsArray<T> = T extends unknown[] ? true : false;
type Element<T> = T extends (infer U)[] ? U : T;   // `infer` captures a sub-type
```

**Distributive over unions — but *only when the check type is a bare type
parameter*.** `T extends U ? X : Y` with a naked union `T` distributes over each
member. Wrapping it (`[T] extends [U]`) makes it a one-tuple — no longer bare — so
distribution stops:

```ts
type NonNull<T> = T extends null | undefined ? never : T;
type R = NonNull<string | null>;  // string   (distributes, null -> never -> dropped)

type IsNever<T> = [T] extends [never] ? true : false;  // the classic opt-out idiom
```

## Mapped types — `map` for the type system

```ts
type Optional<T> = { [K in keyof T]?: T[K] };
type Mutable<T>  = { -readonly [K in keyof T]: T[K] };   // strip readonly
type Required<T> = { [K in keyof T]-?: T[K] };           // strip optional

// key remapping with `as` + template literal
type Getters<T> = { [K in keyof T & string as `get${Capitalize<K>}`]: () => T[K] };
```

Modifiers: `?`/`-?` (optional), `readonly`/`-readonly`. Remap or drop keys with
`as` (`as never` removes a key).

## Template literal types

```ts
type Lang   = "en" | "pt" | "zh";
type Slot   = "header" | "footer";
type LocaleId = `${Lang}_${Slot}_id`;   // "en_header_id" | "en_footer_id" | ...
```

Built-in intrinsics: `Uppercase` `Lowercase` `Capitalize` `Uncapitalize`.

## Utility types (built-in — reach for these before hand-rolling)

| Utility | Result |
|---|---|
| `Partial<T>` / `Required<T>` | all props optional / required |
| `Readonly<T>` | all props `readonly` |
| `Record<K, V>` | object with keys `K`, values `V` |
| `Pick<T, K>` / `Omit<T, K>` | keep / drop a subset of keys |
| `Exclude<U, M>` / `Extract<U, M>` | remove / keep union members |
| `NonNullable<T>` | drop `null \| undefined` |
| `ReturnType<F>` / `Parameters<F>` | a function's return / args tuple |
| `ConstructorParameters<C>` / `InstanceType<C>` | a class's ctor args / instance |
| `Awaited<T>` | unwrap (recursively) a `Promise<T>` |
| `NoInfer<T>` | block inference at this position (TS 5.4+) |

Two sharp edges worth knowing: `Omit<T, K>`'s `K` is `keyof any`, so — unlike
`Pick` — it does **not** error on keys absent from `T` (a typo'd key is silently
ignored). And `NonNullable<T>` is defined as `T & {}` (since TS 4.8).

## `any` vs `unknown` vs `never`

- **`any`** — disables checking, transitively. It poisons everything it touches.
  Only acceptable mid-migration. In a real TS project it's an `@ts-ignore` per use.
- **`unknown`** — the safe top type: accepts anything, but you must **narrow**
  before using it. Use it for "I'll pass this through" or untyped boundaries
  (`JSON.parse`, `catch (e: unknown)`).
- **`never`** — the bottom type: no value. Signals unreachable code and powers
  exhaustiveness checks (see `ts-narrowing.md`).
