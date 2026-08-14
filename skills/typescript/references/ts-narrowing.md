# Narrowing & control flow analysis (CFA)

CFA is how TypeScript reduces a union to a smaller type *inside a scope* based on
the logic you wrote. Most narrowing comes for free from ordinary JS control flow —
learn the operators that trigger it, and lean on them instead of casting with `as`.

## The narrowing operators

```ts
const input = getUserInput();   // string | number | string[]

if (typeof input === "string") { input; }     // string  (typeof — primitives)
if (Array.isArray(input))      { input; }     // string[] (built-in guard fn)
if (input instanceof Date)     { input; }     // Date    (instanceof — classes)
if ("error" in obj)            { obj; }        // the branch with `error`  (in — objects)
```

Narrowing also happens inline in boolean expressions, not just in `if` blocks:

```ts
const len = (typeof input === "string" && input.length) || 0;  // input: string before .length
```

### typeof guards (primitives)

`"string" | "number" | "bigint" | "boolean" | "symbol" | "undefined" | "object" |
"function"`. **Traps:** `typeof null === "object"` and `typeof [] === "object"` —
`typeof` alone won't separate null/array from objects.

### Truthiness narrowing

`if (value)` removes `null`, `undefined`, `0`, `""`, `NaN`, `false`. Useful to drop
nullish — but **`0` and `""` are falsy**, so `if (count)` wrongly skips a real `0`.
Guard nullish explicitly when zero/empty are valid: `if (value != null)`.

### Equality narrowing

`===`/`!==`/`==`/`!=` and `switch` narrow both sides. `x != null` (loose) removes
**both** `null` and `undefined` in one check.

### `in` operator

`"prop" in obj` splits a union by whether members have that property — the classic
discriminator for object unions that lack a literal tag.

### Assignment narrowing

Assigning narrows to the assigned value's type; the variable's *declared* type
still bounds future assignments.

```ts
let x: string | number = "hi";  // x: string
x = 42;                          // x: number  (declared type still string | number)
```

## Type predicates — user-defined guards (`x is T`)

When a check is too complex for built-in narrowing, write a function whose return
type **describes the narrowing**:

```ts
function isErrorResponse(r: Response): r is APIErrorResponse {
  return r instanceof APIErrorResponse;
}
if (isErrorResponse(res)) { res; /* APIErrorResponse */ }
```

The `r is APIErrorResponse` return position is the assertion. **TS 5.5+ infers
predicates for *comparison/guard* `.filter()` callbacks automatically — don't
hand-write them** (see `ts-conventions.md`):

```ts
const defined = items.filter((x) => x !== undefined);  // inferred T[], not (T|undefined)[]
```

Only comparison/guard callbacks infer (`x => x !== undefined`, `x => x != null`,
`x => typeof x === "string"`). A bare **truthiness** callback (`x => !!x`, `x => x`)
does **not** — `xs.filter((x) => !!x)` stays `(T | null)[]`, not `T[]`.

## Assertion functions (`asserts x is T`)

Like a guard, but it **throws** instead of returning false, so it narrows the rest
of the current scope:

```ts
function assertResponse(o: unknown): asserts o is SuccessResponse {
  if (!(o instanceof SuccessResponse)) throw new Error("not a success");
}
assertResponse(res);
res;  // SuccessResponse for the rest of the scope
```

`asserts x` (no `is T`) just asserts truthiness (e.g. a typed `assert(cond)`).

## Discriminated (tagged) unions

The most robust pattern for modeling "one of N shapes." Give every member a common
**literal** field; CFA discriminates on it. Prefer this over optional-everything
"bag" objects.

```ts
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "square"; side: number };

function area(s: Shape): number {
  switch (s.kind) {
    case "circle": return Math.PI * s.radius ** 2;  // s: circle
    case "square": return s.side ** 2;              // s: square
  }
}
```

## `never` + exhaustiveness checking

In the `default`/`else`, a fully-narrowed union is `never`. Assigning it to a
`never` parameter makes **adding a new variant a compile error** — your switch
tells you exactly what you forgot (mirror of Zig's exhaustive switch).

```ts
function assertNever(x: never): never {
  throw new Error(`unhandled: ${JSON.stringify(x)}`);
}

function area(s: Shape): number {
  switch (s.kind) {
    case "circle": return Math.PI * s.radius ** 2;
    case "square": return s.side ** 2;
    default: return assertNever(s);  // add a 3rd Shape -> compile error here
  }
}
```

Don't silence the resulting error with a cast or a catch-all `default` that ignores
the type — walk the new case in, like Zig's tagged-union switch.
