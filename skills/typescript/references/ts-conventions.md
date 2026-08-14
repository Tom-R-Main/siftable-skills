# TypeScript conventions & style

Opinionated rules (sourced from the `mastering-typescript-skill` guidelines and the
handbook's Do's & Don'ts). The **meta-rule overrides all of these: write code that
reads like the surrounding code** — match the file's existing idiom before applying
a preference.

## Prefer `type` over `interface`

Default to `type` aliases. They compose with the whole type system (unions,
intersections, mapped/conditional types) and don't silently declaration-merge.
Reach for `interface` only for public extends-heavy API surfaces or when you
*want* module augmentation / declaration merging. See `ts-type-system.md`.

## Don't add manual type predicates to `.filter()` (TS 5.5+)

TypeScript infers the narrowed type from a comparison/guard filter callback. The
manual predicate is noise.

```ts
const filtered = items.filter((x) => x !== undefined);                  // ✅ inferred NonNullable
const filtered = items.filter((x): x is NonNullable<typeof x> => x);    // ❌ unnecessary
```

(Caveat: only comparison/guard callbacks infer — a bare truthiness callback like
`x => !!x` does **not**, and still returns the wide type. See `ts-narrowing.md`.)

## Object method shorthand in factory returns

When a function exists only to be returned from a factory/creator, define it inline
with method shorthand instead of a separate `const`.

```ts
function makeThing() {              // ✅
  return {
    helper() { /* ... */ },
  };
}

function makeThing() {             // ❌ extra ceremony
  const helper = () => { /* ... */ };
  return { helper };
}
```

## Parameter destructuring for factory/options functions

Destructure the options object **in the signature**, with defaults at the API
boundary — not in the body.

```ts
function createKeyRecorder({ onRegister, onClear, max = 4 }: {  // ✅
  onRegister: (combo: string[]) => void;
  onClear: () => void;
  max?: number;
}) { /* ... */ }

function create(opts: { foo: string; bar?: number }) {  // ❌ body destructuring
  const { foo, bar = 10 } = opts;
}
```

Works with `const` generics: `function select<const T extends readonly string[]>({ options, nullable = false }: { options: T; nullable?: boolean }) {…}`.
**Valid exceptions** for body destructuring: distinguishing "missing" vs
"undefined" (`'key' in opts`), complex normalization, or passing the whole `opts`
object onward.

## Type co-location — never use generic type buckets

Don't create `$lib/types/models.ts` (or `src/types/index.ts`) dumping grounds —
they create unclear dependencies and resist refactoring/deletion.

- **Service-specific types** → `[service-folder]/types.ts`
- **Component-specific types** → in the component file itself
- **Shared domain types** → the domain folder's `types.ts`
- **Cross-domain types** (truly shared across multiple domains) → only then
  `src/types/[specific-name].ts` (a *specific* name, never `models`/`common`)

Benefits: clear ownership, easier deletion, lower coupling.

## Absolute imports when relocating

When moving a file, convert relative imports that now climb directories to the
project's path alias (e.g. `../../components/X` → `$lib/components/X` or `@/components/X`).

## Constant array naming conventions

| Pattern | Suffix | Example |
|---|---|---|
| Simple values (source of truth) | plural noun + unit | `BITRATES_KBPS`, `SAMPLE_RATES` |
| Rich array (source of truth) | plural noun | `PROVIDERS`, `RECORDING_MODE_OPTIONS` |
| IDs for validation (derived) | `_IDS` | `PROVIDER_IDS` |
| UI `{value,label}` (derived) | `_OPTIONS` | `BITRATE_OPTIONS` |
| Label map `Record<Id,string>` | `_TO_LABEL` (singular) | `LANGUAGES_TO_LABEL` |

Always `SCREAMING_SNAKE_CASE`; never camelCase for constant arrays/objects.
Co-locate derived `_OPTIONS`/`_IDS` in the **same file** as the source array.

```ts
// Pattern 1 — label computed from value
export const BITRATES_KBPS = ["16", "32", "64", "128"] as const;
export const BITRATE_OPTIONS = BITRATES_KBPS.map((b) => ({ value: b, label: `${b} kbps` }));

// Pattern 3 — rich array is the source of truth; derive IDs from it
export const RECORDING_MODE_OPTIONS = [
  { label: "Manual", value: "manual", icon: "mic" },
  { label: "Voice Activated", value: "vad", icon: "mic-voice" },
] as const satisfies { label: string; value: string; icon: string }[];
export const RECORDING_MODE_IDS = RECORDING_MODE_OPTIONS.map((o) => o.value);
```

Choose by how the label relates to the value: formatted value → derived; needs
separate data → values + metadata object; extra UI fields (icon/disabled) → rich
array. Keep options inline in a component only when content is platform- or
runtime-conditional.

## Prefer `as const` object + union over `enum`

Enums emit runtime code and have nominal/structural quirks. A frozen object plus a
derived union is leaner and plays nicely with the type system:

```ts
const LogLevel = { Debug: "debug", Info: "info", Error: "error" } as const;
type LogLevel = (typeof LogLevel)[keyof typeof LogLevel];  // "debug" | "info" | "error"
```

(If a codebase already standardizes on `enum`, match it — but `const enum` is
banned under `isolatedModules`/`verbatimModuleSyntax`.)

## `unknown`, not `any`

Type untyped boundaries (`JSON.parse`, network, `catch`) as `unknown` and narrow.
`any` silently disables checking transitively. In `catch (e)`, type `e: unknown`
and narrow (`e instanceof Error`).

## Callback return types: `void`, not `any`

For callbacks whose return is ignored, type the return as `void` — it prevents
accidentally consuming a return value, and (unlike a specific type) lets callers
pass functions that *do* return something.

```ts
function each(fn: (x: T) => void) { /* ... */ }   // ✅
```

## arktype: optional props use `'key?'`, never `| undefined`

In arktype schemas, `| undefined` produces invalid JSON Schema (`anyOf: [{type},{}]`),
breaking OpenAPI/MCP tool-schema generation. Use the optional-key syntax so the
prop is omitted from `required`.

```ts
const schema = type({ "window_id?": "string", "url?": "string" });   // ✅
const schema = type({ window_id: "string | undefined" });            // ❌ breaks JSON Schema
```

## Boxed primitive types are banned

Never `String`, `Number`, `Boolean`, `Symbol`, `Object` (capital) — use lowercase
`string`, `number`, `boolean`, `symbol`, and `object`/a precise shape. The boxed
types refer to wrapper objects and are almost never what you want.
