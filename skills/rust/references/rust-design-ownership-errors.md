# Rust design, ownership, and errors

Use this reference when designing or reviewing ordinary safe Rust: API
boundaries, borrow-checker fixes, closures, state modeling, error types,
traits and `dyn`, naming, std I/O contracts, and crate structure.

Anchor: reviewed 2026-08-17 against Rust 1.95.0; the borrow and dyn-compatibility
behavior below was compiler-checked on that toolchain. Rust releases every six
weeks — confirm version-gated claims against the toolchain your project pins.

## Ownership decision table

| Callee needs to | Prefer | Why |
|---|---|---|
| Read text/bytes/items | `&str`, `&[u8]`, `&[T]` | Accepts owned and borrowed callers |
| Mutate caller-owned data | `&mut T`, `&mut [T]` | Makes exclusive mutation explicit |
| Store or transfer a value | `T`, `String`, `Vec<T>` | Ownership outlives the call |
| Accept several path-like inputs | `impl AsRef<Path>` at a leaf boundary | Convenience without generic bounds in domain APIs |
| Return newly created data | owned `T` | No hidden lifetime coupling |
| Return a view into input | `&T` with input-tied lifetime | Makes provenance explicit |
| Sometimes allocate | `Cow<'a, T>` after profiling/API need | Avoids allocation while preserving ownership option |

Do not use `&String` when `&str` expresses the contract, or `&Vec<T>` when
`&[T]` does. Do not add generic `AsRef`/`Into` bounds everywhere: they can make
diagnostics, inference, and public APIs harder.

Moves are usually cheap transfers of ownership. A move of `String` or `Vec<T>`
copies a small handle, not its backing allocation. A clone duplicates according
to the type's `Clone` implementation and can be expensive or semantically
significant. For `Rc`/`Arc`, cloning increments a reference count and may extend
the lifetime of everything reachable from the allocation.

## Read borrow errors as design feedback

Two facts about the checker shape most fixes:

- **Borrows end at their last use, not at scope end** (non-lexical lifetimes).
  Reordering statements, or extracting a value out of a borrow before the
  conflicting use, often resolves E0499/E0502 with no new structure.
- **Implicit `&mut self` autorefs are two-phase**: `v.push(v.len())` compiles
  because the receiver borrow is only *reserved* until the arguments are
  evaluated. Explicit borrows are not: `let r = &mut v; r.push(v.len())` is
  an error. When a nested call fails, compute the argument first.

When two operations conflict over a borrow, ask:

1. Which operation owns the value?
2. Which references must coexist, and for how long?
3. Can computation be separated from mutation?
4. Can a borrow end earlier through a smaller scope or an extracted value?
5. Does a collection API (`entry`, `split_at_mut`, iterator adapters) express
   disjoint access safely?
6. Is shared mutation actually part of the domain? Only then consider
   `Cell`/`RefCell`, `Mutex`, `RwLock`, or atomics.

Moving out of a place is refused when the place is behind `&`/`&mut` (E0507),
is an index of an array or slice (E0508), or is a field of a type that
implements `Drop` (E0509). Choose deliberately: `Option::take`, `mem::take`/
`mem::replace`, `clone`, destructuring with `ref`, `into_iter`/`drain`, or
restructure so the caller owns the value.

Prefer returning ownership or an index/handle over self-referential structures.
Use arenas or pinning only when stable addresses are a real requirement and the
project already has an ownership model for them.

Lifetimes describe relationships between references; they do not extend the
lifetime of data. Add explicit lifetime parameters when they clarify which input
a returned reference borrows from, not to appease the compiler mechanically.

## Closures: `Fn`, `FnMut`, `FnOnce`

Bound a parameter by the *weakest* trait the body needs; every closure that
satisfies a stronger one also satisfies it:

- called at most once, or the body moves a captured value out → `FnOnce`;
- called repeatedly and mutates captured state → `FnMut` (take `mut f: impl FnMut`);
- called repeatedly through a shared reference, possibly concurrently → `Fn`.

`move` controls *how* values are captured (by value), not which trait the
closure implements; a `move` closure that only reads is still `Fn`. Closures
capture disjoint fields (2021+), so `|| self.a.len()` does not borrow all of
`self`. Spawn-style APIs need `Send + 'static`, hence `move` of owned data.
Return closures as `impl Fn(..) -> ..`; store heterogeneous ones as
`Box<dyn Fn>`/`Box<dyn FnMut>`/`Box<dyn FnOnce>`.

## Model the domain in types

- Use newtypes for identifiers, units, validated text, and capabilities that
  must not be mixed.
- Use enums instead of booleans or bags of optional fields when states have
  distinct valid data.
- Match business-critical enums exhaustively so adding a variant forces a
  decision. Use `_` when forward compatibility or intentionally irrelevant
  cases are part of the contract.
- Parse input into validated types at system boundaries. Keep raw strings,
  integers, and maps out of the core when they permit invalid values.
- Use constructors for invariants. If fields must stay coherent, keep them
  private.
- Apply typestate only when compile-time sequencing prevents meaningful misuse
  and the extra types do not make ordinary control flow harder.

For public libraries, remember that adding enum variants or fields can be
breaking unless the API was explicitly designed for extension (for example with
`#[non_exhaustive]`). Check the project's SemVer policy before reshaping public
types.

## Error strategy by boundary

Classify failure before choosing syntax:

- **Caller can recover or branch:** return a typed `Result<T, E>`.
- **Value may legitimately be absent:** return `Option<T>`.
- **Internal invariant is violated:** an assertion or panic can be appropriate.
- **Application is reporting and exiting:** attach operational context near the
  top-level boundary.

Good library errors expose stable, meaningful categories without leaking every
dependency error as public API. Wrap lower-level sources when callers benefit
from them, and preserve `source()` chains. Avoid stringly typed branching.

`thiserror` is useful for structured library/module errors; `anyhow`-style
reports are useful in binaries and orchestration. Neither is mandatory. Reuse
the project's error stack and avoid adding a dependency for a one-variant error.

Use `?` for propagation when no local recovery or translation is needed.
Add context where the lower-level error cannot answer “what operation failed?”
Do not log and return the same error at every layer; that creates duplicate
noise. Choose one boundary that owns reporting.

`unwrap` and `expect` are reasonable in tests, examples, and prototypes. In
production paths, prefer explicit errors, or an `expect` whose message states
the invariant that makes failure impossible ("hardcoded IP should parse")
rather than restating the failure — so a future reader knows what assumption
to re-check when the input source changes.

## Traits, generics, and dispatch

- Define traits around required behavior, not around every struct.
- Keep traits small enough to implement and test independently.
- Prefer associated types when an implementation has one natural related type;
  use generic parameters when callers choose the type per use.
- Use `impl Trait`/generics for static dispatch and `dyn Trait` for runtime
  heterogeneity. Measure hot paths before treating dynamic dispatch as a
  bottleneck.
- Check **dyn compatibility** (the term rustc uses; formerly "object safety")
  before promising `dyn Trait` in a public API. A trait is dyn compatible only
  if: no supertrait is `Sized`; it has no associated consts and no generic
  associated types; every method either is dispatchable (no type parameters,
  `Self` only as the receiver, receiver `&self`/`&mut self`/`Box`/`Rc`/`Arc`/
  `Pin<..>` of those) or opts out with `where Self: Sized`. `async fn` in
  traits and `AsyncFn*` are not dyn compatible. E0038 reports "`X` is not dyn
  compatible" with the violated rule.
- Avoid speculative abstraction. Two similar implementations are not
  necessarily the same concept.
- Use sealed traits when external implementations would prevent future
  evolution and the project accepts that closed extension model.

Macros are appropriate for syntax generation or repetition that functions and
traits cannot express. Keep expansions inspectable, preserve spans/diagnostics,
test edge cases, and avoid hiding control flow or unsafe operations.

## API and module shape

- Organize by domain/capability, not mechanically by type category.
- Keep implementation modules private and re-export a deliberate public API.
- Use `pub(crate)` for cross-module internals.
- Document public fallibility, panics, safety requirements, and important
  complexity.
- Put executable examples in rustdoc where they remain useful as doc tests.
- Use `#[must_use]` when silently discarding a value is probably a bug, but do
  not annotate everything.

## Naming and idiom (Rust Style Guide)

- Types, traits, and enum variants: `UpperCamelCase`. Functions, methods,
  fields, locals, modules, macros: `snake_case`. `const`s and immutable
  `static`s: `SCREAMING_SNAKE_CASE`.
- A reserved word as a name: raw identifier (`r#crate`) or trailing underscore
  (`crate_`) — do not misspell it (`krate`).
- Prefer expression orientation: `let x = if c { 1 } else { 0 };` over
  declare-then-assign in branches.
- Avoid `#[path]` module annotations.
- Formatting exists for readability *without* tooling — diffs, grep, compiler
  output. Let rustfmt own layout; spend review attention on names and shape.

## Standard I/O contracts worth remembering

- `Read::read` may return fewer bytes than requested; `Ok(0)` means EOF (or an
  empty buffer). Use `read_exact`, `read_to_end`, `read_to_string` when you mean
  "all".
- `Write::write` may write partially; use `write_all` when you mean all.
  `Vec<u8>` as a writer always writes everything; `&[u8]` as a reader is
  allocation-free — both are ideal test doubles.
- `BufWriter` flushes in `Drop` **but ignores the error**. Call `flush()` or
  `into_inner()` and check the result before dropping anything that matters.
- Wrap many small reads/writes in `BufReader`/`BufWriter`; each unbuffered call
  is typically a syscall.
- `io::Error::from(ErrorKind)` and `ErrorKind` matching are allocation-free;
  `io::Error::new`/`other` box a payload. Match on `kind()` rather than message
  text.

## Anti-pattern review

Flag these with context, not mechanical search-and-replace:

- clones added solely to satisfy the borrow checker;
- `'static` added solely to satisfy a lifetime error;
- `Box<dyn Error>` erasing a reusable library contract;
- `Arc<Mutex<_>>` introduced before deciding whether state must be shared;
- `Box<dyn Fn>` where `impl Fn` or a generic parameter would do;
- wildcard matches hiding domain variants;
- public fields that bypass invariants;
- iterator chains that obscure control flow, or loops that allocate needless
  intermediate collections;
- `unsafe` used to bypass an ownership design problem.

## Primary references

- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [Rust Reference](https://doc.rust-lang.org/reference/) — see *Dyn compatibility*
- [Rust Style Guide](https://doc.rust-lang.org/style-guide/)
- [Apollo Rust Best Practices handbook](https://github.com/apollographql/rust-best-practices)
