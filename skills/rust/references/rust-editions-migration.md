# Rust editions, toolchains, and migration

Use this reference for edition upgrades (especially 2015/2018/2021 → 2024),
toolchain pins, MSRV policy, resolver behavior, and rustfmt style editions.

Anchor: reviewed 2026-08-17 against Rust 1.95.0. Every compiler-observable item
in the Rust 2024 checklist below was verified on that toolchain by compiling the
same snippet under editions 2021 and 2024. Rust releases every six weeks —
confirm version-gated claims against the toolchain your project pins.

## Toolchain and MSRV facts that change what tools do

- **`rust-toolchain(.toml)` is per-directory.** rustup uses the nearest one
  walking *up from the current directory*. A file under `vendor/`, `examples/`,
  or a nested tool crate governs only that subtree; the repo root may pin
  nothing and rely on rustup's default, CI, or a bootstrap file. Always confirm
  which toolchain actually built the code you are changing.
- **`package.rust-version` (MSRV)** is a promise to callers and, under
  resolver 3, an input to dependency resolution. Changing it is an API change.
- **`edition = "2024"` implies `resolver = "3"`** in a package. Resolver 3 is
  Rust-version aware: it prefers dependency versions compatible with your
  `rust-version` (`resolver.incompatible-rust-versions = "fallback"`). The
  setting is honored only for the top-level workspace and ignored inside
  dependencies. **Virtual workspaces must set `resolver = "3"` explicitly** —
  the edition of member crates does not imply it.
- **Stable rustfmt silently ignores nightly-only options** (`imports_granularity`,
  `group_imports`, `ignore`, ...) with a warning. If a repo's `rustfmt.toml`
  uses them, only the toolchain the repo formats with produces meaningful diffs.
- **`style_edition`** is separate from `edition`. rustfmt defaults the style
  edition to the crate's edition; set `style_edition = "2024"` in `rustfmt.toml`
  so editors and CI agree. Moving to the 2024 style produces a large diff
  (version-sorting, raw-identifier sorting, formatting fixes) — commit it
  separately.

## Migration procedure (from the Edition Guide)

1. Update dependencies to versions that support the target edition (`cargo
   update` if the project's lockfile policy allows).
2. `cargo fix --edition` on the current edition. It applies compatibility
   lints automatically and prints what it cannot fix.
3. Set `edition = "2024"` (and `resolver` for a virtual workspace) in
   `Cargo.toml`.
4. Build and run the full test suite; resolve leftover warnings by hand.
5. `cargo fmt` — as a separate commit.
6. Optionally `cargo fix --edition-idioms` for the new edition's idioms.

Do it one workspace at a time; per-crate editions in one workspace are legal
and useful for staging. Do not combine the migration with refactors.

## Rust 2024 change checklist

Verify each against the crate you are migrating; the Edition Guide has one
page per item under `rust-2024/`.

**Unsafe**
- `unsafe extern { .. }` is required; items inside can be `safe fn`/`unsafe fn`.
- `#[no_mangle]`, `#[export_name]`, `#[link_section]` become `#[unsafe(...)]`.
- `unsafe_op_in_unsafe_fn` becomes warn-by-default: write inner `unsafe {}`
  blocks with `// SAFETY:` comments inside `unsafe fn`.
- `static_mut_refs` becomes deny-by-default: no `&`/`&mut` to `static mut`.
- `std::env::set_var`, `remove_var`, and `CommandExt::before_exec` are `unsafe`.

**Lifetimes and temporaries**
- `-> impl Trait` captures *all* in-scope generic parameters, including
  lifetimes. Replace `Captures`/outlives tricks with `use<..>` bounds or delete
  them; add `use<..>` when you need to *exclude* a lifetime.
- Tail-expression temporaries in a block/function body may drop before local
  variables. Code that relied on a guard living to the end of the block through
  a tail expression may fail to compile or change drop order.
- `if let` scrutinee temporaries drop before the `else` branch runs.

**Type system and patterns**
- Never-type fallback is `!` instead of `()`;
  `never_type_fallback_flowing_into_unsafe` is deny-by-default.
- Match ergonomics are stricter: `mut`, `ref`, `ref mut`, and `&`/`&mut`
  patterns are only allowed where the pattern prefix is fully explicit.
- `boxed_slice.into_iter()` now yields by value (`Box<[T]>: IntoIterator`).
- `if let` / `while let` chains (`if let A = a && let B = b`) are available
  (1.88+, edition 2024 only).

**Std and prelude**
- `Future` and `IntoFuture` are in the prelude; method-name ambiguities may
  appear.

**Cargo**
- Resolver 3 (see above).
- Removed duplicate spellings: `[project]` → `[package]`, `default_features` →
  `default-features`, `crate_type` → `crate-type`, `proc_macro` → `proc-macro`.
- `default-features = false` is rejected on an inherited workspace dependency
  whose workspace entry has default features on.

**Macros and syntax**
- `gen` is reserved.
- `missing_fragment_specifier` is a hard error.
- The `expr` fragment also matches `const { .. }` and `_`; `expr_2021` keeps
  the old behavior.

**rustfmt**
- Style edition 2024: sorting and formatting changes; `style_edition` key.

## When the target is *not* the latest edition

The Edition Guide covers 2018 and 2021 with the same shape (`rust-2018/`,
`rust-2021/`): disjoint closure captures, `IntoIterator` for arrays, panic
macro consistency, and reserved prefixes are the usual 2021 items. Follow the
same procedure; `cargo fix --edition` targets the next edition from the current
one, so multi-step upgrades run once per edition.

## Primary references

- [Edition Guide](https://doc.rust-lang.org/edition-guide/) — see
  *Transitioning an existing project to a new edition* and *Rust 2024*
- [Cargo: rust-version](https://doc.rust-lang.org/cargo/reference/rust-version.html)
- [Cargo: resolver versions](https://doc.rust-lang.org/cargo/reference/resolver.html#resolver-versions)
- [rustup: overrides](https://rust-lang.github.io/rustup/overrides.html)
