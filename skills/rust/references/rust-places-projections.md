# Places, guards, and pointer projection

Use this when field splitting stops compiling after a smart-pointer/guard
refactor, or when projecting raw, foreign, uninitialized, or pinned storage.
The two stable examples below are compiler/run checked on Rust 1.95 and 1.98,
editions 2021 and 2024. Design-status review: 2026-11-05.

## Expose disjoint fields through a guard

Rust can track separate fields of an ordinary struct place. Through a library
pointer, field access may instead borrow the whole wrapper for `Deref` or
`DerefMut`; separate fields alone do not ensure separate wrapper borrows.
Reborrow the pointee once and keep its guard alive:

```rust
use std::collections::HashMap;
use std::sync::Mutex;

#[derive(Default)]
struct State {
    templates: HashMap<String, String>,
    cache: HashMap<String, String>,
}

fn main() {
    let shared = Mutex::new(State::default());
    let mut guard = shared.lock().unwrap();
    guard.templates.insert("home".into(), "Hello, {name}".into());
    let state = &mut *guard;
    let rendered = state.cache.entry("home".into()).or_insert_with(|| {
        state.templates["home"].replace("{name}", "Rust")
    });
    assert_eq!(rendered, "Hello, Rust");
}
```

This is a safe reborrow, not a new allocation or another lock. `mut guard`
permits `DerefMut`; that alone does not resolve the field conflict. The reference
and any view returned through it remain bounded by the guard's lifetime; do not
return a reference from a function that acquired a local guard. Return owned
data or an appropriate guard API instead. `RefMut` has a similar issue, though
its access is enforced by runtime borrow checking rather than a mutex.

The example's closure requires edition 2021+ disjoint capture. For earlier
editions, use `let State { templates, cache } = &mut *guard;`, then
`cache.entry(..).or_insert_with(|| templates[..].replace(..))`. Capturing these
separate field references works across editions without cloning the template.
For projected views that must retain dynamic borrow ownership, consider
`Ref::map`, `RefMut::map`, or `RefMut::map_split` as their contracts allow.

Disjoint closure capture (edition 2021+) helps with ordinary struct fields; it
does not grant arbitrary `Deref` types the compiler's built-in reference/`Box`
semantics. See [Reference capture precision](https://doc.rust-lang.org/reference/types/closure.html#capture-precision).

## Project without inventing a reference

For raw-pointer or foreign wrappers, do not turn an ergonomic problem into a
stronger aliasing promise. A C/C++ alias need not satisfy `&mut T` exclusivity;
`NonNull<T>` need not point to live, aligned, initialized storage. Use the
wrapper's documented projection API, or keep a narrow raw-pointer operation
whose invariant you can establish. For initialization, for example:

```rust
use std::mem::MaybeUninit;

struct Pair { first: u32, second: u32 }

fn main() {
    let mut slot = MaybeUninit::<Pair>::uninit();
    let ptr = slot.as_mut_ptr();
    // SAFETY: ptr is aligned writable storage for Pair; both fields are
    // initialized in bounds before producing a Pair, with no intermediate &Pair.
    let value = unsafe {
        (&raw mut (*ptr).first).write(10);
        (&raw mut (*ptr).second).write(20);
        slot.assume_init()
    };
    assert_eq!((value.first, value.second), (10, 20));
}
```

For partially initialized values with destructors, also track which fields must
be dropped if initialization fails. For packed fields, use the appropriate
unaligned read/write operation rather than constructing a reference. Raw
projection still has bounds, validity, and provenance obligations; see
[unsafe and FFI](rust-unsafe-ffi-performance.md).

For `Pin<&mut T>`, choose whether each field is structurally pinned. Use the
project's existing projection abstraction (for example `pin-project`) if
needed; never use an ordinary mutable field borrow to bypass pinning of a
`!Unpin` field. Check drop and replacement behavior as well as projection.

## Beyond the Ampersand is design work

The talk's handles make *places* an extension point for library pointers:
projection, dereference, reads/writes, and borrowing are separate capabilities.
That explains why stable `Deref` ergonomics fall short; it is not a stable API
recipe. `BorrowPlace`, `ProjectPlace`, `DerefPlace`, `WritePlace`, `handle!`,
`borrow!`, an `@` borrow operator, and place wrappers in that design must not be
emitted as working std Rust. In-place initialization proposals likewise require
separate status verification; do not infer support from the talk or a mockup.

The [Beyond Refs design repository](https://github.com/rust-lang/beyond-refs)
and [field projection design index](https://rust-lang.github.io/beyond-refs/field-projections.html)
are the sources for experiments. Names and syntax may change. In the inspected
Rust checkout, `DerefPure` is unstable and its precise semantics are undecided;
`deref_patterns` is also unstable. Neither means all handle capabilities exist
on stable. Distinguish an accepted goal, design, prototype, nightly feature, and
stabilized implementation. Before a requested experiment, identify the exact
branch/compiler and check which operations it actually supports.

For production code, use stable reborrows, scoped guards, existing projection
APIs and explicit raw operations. Introduce a macro or pointer abstraction only
when repeated, demonstrated needs justify its maintenance and safety burden.
