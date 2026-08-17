---
name: rust
description: Build, review, debug, migrate, test, or optimize Rust code. Use for .rs files, Cargo.toml/Cargo.lock, rust-toolchain files, workspaces and features, ownership/borrowing/lifetime errors, traits/generics/closures/macros and dyn compatibility, Result-based error design, async/Tokio concurrency (Pin, cancellation, select!, streams), unsafe code and C FFI, edition (2024) or MSRV migrations, Clippy/rustfmt failures, testing/fuzzing/benchmarking, and actually running Rust binaries, libraries, services, or native modules. Prioritize the repository's pinned toolchain, build driver, and existing patterns; explicit ownership and invariants; safe abstractions around unsafe code; bounded structured concurrency; and measured performance claims.
---

# Rust

Use this skill for Rust implementation, review, migration, and performance work.
Rust ships a stable release every six weeks; prefer the repository's pinned
toolchain, nearby working code, compiler diagnostics, and official documentation
over remembered APIs or blanket style rules. Neither this skill nor the model is
a source of truth: when a claim matters, read the pinned crate source, the
versioned std docs, or the Reference, and say what you found.

Paths below are relative to this skill directory, wherever your agent installed
it. Each reference opens with an anchor line naming the toolchain and date its
version-gated claims were reviewed against; anything newer is unverified.

Not covered here: `no_std` and embedded targets, proc-macro authoring
(`syn`/`quote`/`trybuild`), dependency auditing beyond honoring the
repository's existing policy, and WebAssembly or cross-compilation beyond
passing `--target`.

## First moves

Detect the actual project contract before editing:

```sh
find . -maxdepth 3 \( -name rust-toolchain -o -name rust-toolchain.toml \) -print
ls x.py x xtask justfile Justfile Makefile .cargo/config.toml 2>/dev/null
rg -n '^(edition|rust-version)[[:space:]]*=|^\[workspace\]|^resolver[[:space:]]*=' \
  -g 'Cargo.toml' .
rustc -Vv
cargo -V
rustup show active-toolchain 2>/dev/null || true
cargo metadata --no-deps --format-version 1
```

Read the results with these rules:

- **Toolchain files are per-directory, not per-repo.** rustup honors the nearest
  `rust-toolchain(.toml)` walking up from the *current directory*. A hit under
  `vendor/`, `examples/`, or a nested tool governs only that subtree. If the
  root has none, the toolchain is rustup's default — or the repo pins it
  somewhere non-standard (a bootstrap file, nix/bazel, CI). Find that before
  trusting `rustc -Vv`.
- **A build driver outranks Cargo.** If the repo has `x.py`, an `xtask` crate,
  a `justfile`, a `Makefile`, or scripts that wrap Cargo, its commands are the
  contract for build, test, fmt, and lint. Raw Cargo may use the wrong
  toolchain, features, profile, or rustfmt config and produce confident wrong
  output.
- **`edition = "2024"` implies `resolver = "3"`**, which makes `rust-version`
  affect dependency selection. Virtual workspaces must set `resolver`
  explicitly. See `references/rust-editions-migration.md`.

Then inspect the relevant `Cargo.toml`, `Cargo.lock` policy, `.cargo/config.toml`,
CI, `rustfmt.toml`, `clippy.toml`, `deny.toml`, and the driver. Determine:

- package versus workspace scope and `default-members`;
- edition, declared `rust-version` (MSRV), pinned channel, and required targets;
- default, optional, platform-specific, and mutually exclusive features;
- whether CI uses stable, nightly, `cargo nextest`, cross-compilation, Miri,
  sanitizers, coverage, or an MSRV matrix.

Match those choices unless the task explicitly changes them. Do not silently
update dependencies, `Cargo.lock`, the edition, MSRV, `resolver`, feature
defaults, or lint policy as a side effect.

For current language, standard-library, Cargo, or Clippy behavior, use the
versioned official docs for the detected toolchain. For Tokio or another crate,
inspect the pinned crate version and its official docs/source rather than
assuming the latest API.

## Working method

Distilled from the Rust project's own guidance for model-written code; it
generalizes to any repository:

- Treat generated code as a draft. Make the smallest change that fixes the
  problem; do not bundle refactors, renames, or cleanups.
- Read the relevant code, tests, docs, and git history before proposing a
  design, and verify understanding against them rather than memory.
- For a bug: add or find a failing test, run it, observe the failure, then
  implement, then watch it pass. Never combine the test edit and the fix.
- Prefer a linter to model review. When a rule can be mechanized — a
  disallowed method, a required wrapper, a naming pattern — configure Clippy
  (`disallowed-methods`, `disallowed-types`), rustfmt, or a small script and
  run it, so people not using a model get the same check.
- Mass renames and mechanical rewrites go through a syntax-aware tool
  (`ast-grep`, `cargo fix`, rustfmt, the project's own tool). Generate the
  rule; do not perform the rewrite by hand.
- Some projects require humans to write `// SAFETY:` comments, public doc
  comments, diagnostic wording, or soundness-critical code. Check
  `CONTRIBUTING.md`/`AGENTS.md` first; when a rule applies, review and
  explain, do not draft.
- Before handing off, be able to state in plain words: what the bug was and
  when it happens; why this fix and what alternatives were rejected; which
  edge cases exist and which are tested; which invariants existed and were
  preserved; what behavior is unchanged and which test proves it; what is
  still uncertain. When stakes warrant, have a *different* model review the
  diff — models prefer their own output.

## Implementation bias

Make ownership, invalid states, fallibility, and concurrency visible in the
types and at call sites.

- Borrow when the callee only observes data; take ownership when it stores,
  consumes, transfers, or transforms it. Prefer `&str`, `&[T]`, and `&Path` over
  borrowed owned containers in parameters. Return owned data when the function
  creates it.
- Treat `.clone()` as an ownership decision, not a borrow-checker escape hatch.
  Cheap reference-count increments can still extend lifetimes or retain large
  object graphs; measure clones in hot paths.
- Parse untrusted or weakly typed input once into domain types. Use newtypes,
  enums, exhaustive matches, and validated constructors to make illegal states
  hard to express.
- Use `Result<T, E>` for recoverable failure and reserve panic for bugs,
  violated internal invariants, or explicitly unrecoverable process policy.
  Treat reachable production `unwrap`/`expect` as a review point, not a
  mechanically forbidden token.
- Preserve actionable error context without erasing library contracts. Prefer
  typed errors at reusable boundaries and contextual reports at application
  boundaries. Add `thiserror`, `anyhow`, or other crates only when they fit the
  existing dependency policy.
- Prefer clear concrete types and small traits. Use generics for compile-time
  substitution and `dyn Trait` for runtime heterogeneity; account for dyn
  compatibility, monomorphization, compile time, and public API stability.
- Bound closure parameters by the weakest trait the body needs (`FnOnce`,
  then `FnMut`, then `Fn`); `move` changes capture, not the trait.
- Keep public surface area narrow (`pub(crate)` or private by default). Re-export
  an intentional API rather than exposing module layout accidentally.
- Keep `unsafe` blocks small and wrap them in safe abstractions whose invariants
  are documented and tested. Every unsafe operation needs a local proof; an
  `unsafe fn` contract does not replace it.
- Prefer ordinary code over intricate lifetime parameters, macros, typestate, or
  interior mutability when a simpler ownership boundary expresses the same
  invariant. Use advanced patterns when they remove invalid states or essential
  duplication, not for novelty.
- Optimize data layout, allocation count, I/O shape, and algorithmic work before
  instruction-level tweaks. Benchmark release artifacts with representative
  inputs and preserve a correctness gate in the normal test profile.

## Validation gates

Run the repository's own commands when they exist; the Cargo baseline is a
fallback, not the default:

```sh
# Repos with a build driver: use it and stop here.
./x fmt --check && ./x test <target>      # x.py bootstrap (rust-lang/rust)
cargo xtask ci                            # xtask pattern
just check && just test                   # justfile pattern

# Cargo-native repos:
scripts/rust-gates.sh
```

The helper refuses (exit 3) when it detects a build driver, and fails (exit 4)
instead of printing diffs when `rustfmt.toml` uses nightly-only options on the
current toolchain — stable rustfmt silently drops them, so those diffs measure
the wrong configuration. Otherwise it runs non-mutating gates: rustfmt check,
Clippy (`cargo check` only as an opt-in fast-fail, since Clippy repeats it),
and tests. It respects `Cargo.lock`, supports workspace/package and feature
selection, and documents its knobs in the script header and under `--help`.

The direct baseline is:

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
```

Adapt that baseline to the repo:

- Omit `--locked` when no lockfile is intentionally committed.
- Use `-p <package>` for a focused package before checking the whole workspace.
- Use `--all-features` only when the feature set is designed to compose; some
  crates intentionally have mutually exclusive backends.
- Match the repo's warning policy. Clippy's `pedantic` group is opt-in and can
  have false positives; do not impose it wholesale.
- Run target-specific builds when `cfg` or FFI changes (`--target <triple>`).
- Run MSRV CI when public compatibility is part of the contract.

Do not stop at compilation when the task changes behavior:

- **CLI:** run the real binary with representative arguments and assert output,
  exit status, and failure behavior.
- **Service:** start it with the project command, probe a health and changed
  route, then shut it down cleanly.
- **Library:** run unit, integration, and doc tests; add a consumer-style test
  for public API changes.
- **FFI/native module:** exercise the host-language boundary, allocation/free
  path, invalid inputs, and panic/error translation.
- **Performance:** compare before/after release-profile measurements. Report
  inputs, profile, target, variance, and correctness evidence.

## Open references as needed

- `references/rust-design-ownership-errors.md` — ownership decisions, borrow
  errors (NLL, two-phase borrows, moves), closures, data modeling, errors,
  traits and dyn compatibility, naming/idiom, std I/O contracts, anti-patterns.
- `references/rust-async-concurrency.md` — what the compiler builds, `Pin`,
  task ownership, channels, cancellation and `select!`, blocking, locks,
  streams, async traits/closures, cleanup without async Drop, shutdown, tests.
- `references/rust-testing.md` — regression-first fixes, unit/integration/doc
  tests, properties, fuzzing, snapshots, concurrency tests, and coverage.
- `references/rust-unsafe-ffi-performance.md` — the UB list and validity
  invariant, `static mut`, `unsafe extern` and FFI contracts,
  Miri/sanitizers/Loom, profiling, and benchmark discipline.
- `references/rust-editions-migration.md` — toolchain/MSRV/resolver facts,
  the migration procedure, and the Rust 2024 change checklist.

Treat these as decision guides, not laws. If the compiler, pinned crate source,
nearby code, or project policy disagrees, follow the project and record why.

## High-value diagnostics

- **E0382, use of moved value:** decide whether the later use needs a borrow,
  ownership transfer, scoped move, or a deliberate clone. Do not clone first and
  reason later.
- **E0499/E0502, conflicting borrows:** borrows end at last use (NLL), so
  reorder or extract a value first. Shorten borrow scope, split fields or
  collections, or use an entry API. `v.push(v.len())` compiles because implicit
  `&mut self` autorefs are two-phase; an explicit `let r = &mut v;` is not.
  Interior mutability is a semantic choice, not a generic escape.
- **E0507/E0508/E0509, cannot move out of a borrow / an array / a `Drop`
  type:** you cannot move from behind `&`/`&mut`, from an array or slice
  index, or from a field of a type with `Drop`. Use `Option::take`,
  `mem::take`/`replace`, clone, `ref` destructuring, or restructure ownership.
- **E0515/E0597, value does not live long enough:** the returned/reference value
  outlives its owner. Return ownership, move the owner outward, or tie the
  lifetime to a real input; never reach for `'static` reflexively.
- **E0277, trait bound not satisfied:** read the complete obligation chain.
  Check `Send`/`Sync`, iterator item/reference types, feature gates, target cfg,
  and whether the bound belongs on the function, impl, or associated type.
  "`dyn Future<..>` cannot be unpinned" means `pin!(fut)`/`Box::pin(fut)`
  before polling or passing `&mut fut` to `select!`.
- **E0038, "`X` is not dyn compatible":** the trait has a generic method, uses
  `Self` outside the receiver, has an associated const, or is `Sized`. Add
  `where Self: Sized` to non-dispatchable methods, box returns, or use generics.
- **E0282/E0283, type annotations needed:** add the smallest annotation at the
  ambiguous collection, parse, conversion, or error boundary.
- **future is not `Send`:** find the non-`Send` value alive across `.await`
  (often a guard, `Rc`, or reference); it is a field of the state machine even
  if unused after the await. Drop/scope it before awaiting, or use the
  runtime's local-task model only when that is intentional.

## Gotchas

- Rustfmt without `--check` mutates files. Use check mode for review-only work.
  Stable rustfmt ignores nightly-only options in `rustfmt.toml` with only a
  warning; check with the toolchain the repo formats with.
- `cargo check` is not a runtime test, and test/debug profiles can differ from
  release in overflow checks, optimization, timing, and layout.
- Futures are lazy. Creating a future does nothing until it is polled; dropping
  one cancels it at its current `.await`, which may leave externally visible
  partial work. `select!` and timeouts cancel by dropping and do not fire
  cancellation tokens.
- Do not hold a synchronous mutex guard across `.await`; minimize critical
  sections even with async-aware locks.
- `Rc<T>`/`RefCell<T>` and `Arc<T>`/locks solve different single-threaded versus
  shared-threaded problems. The compiler traits `Send` and `Sync` are part of
  the design, not lint noise.
- Edition 2024: `unsafe extern` blocks, `#[unsafe(no_mangle)]`,
  `static_mut_refs` denied, `unsafe_op_in_unsafe_fn` warns, `-> impl Trait`
  captures all lifetimes, tail-expression temporaries drop earlier.
- `BufWriter` ignores flush errors in `Drop`; call `flush()`/`into_inner()` and
  check them. `Write::write` may be partial — use `write_all` when you mean
  all. `Read::read` returning `Ok(0)` means EOF.
- Cargo features should normally be additive, but real projects sometimes use
  exclusive backends. Inspect compile errors and CI before assuming
  `--all-features` is authoritative.
- Build scripts and proc macros execute code during builds. Treat new build-time
  dependencies and generated artifacts as supply-chain and reproducibility
  decisions.
- Cargo may download missing dependencies even for check/test commands. Honor
  the environment's network-approval rules; use `--offline` only when the
  required index and crates are already cached.
- An `unsafe` block permits specific operations; it does not prove aliasing,
  initialization, validity, provenance, thread safety, ABI, or lifetime
  correctness.
