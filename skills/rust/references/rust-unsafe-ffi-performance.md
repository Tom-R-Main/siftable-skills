# Rust unsafe, FFI, and performance

Use this reference for unsafe blocks/traits, raw pointers, manual initialization,
`static mut`, C ABI boundaries, host-language native modules, synchronization
primitives, and performance work.

## Unsafe is a proof boundary

An `unsafe` block permits specific operations; it proves nothing. For each
operation, state the invariant that keeps it out of the Reference's list of
undefined behavior (`reference/behavior-considered-undefined.html`):

- **No data race.** Concurrent unsynchronized access where at least one side
  writes is UB, listed first in the Reference for a reason.
- **Every access is in bounds, aligned, and to live memory.** No dangling or
  misaligned place is loaded from or stored to; place projections (`.field`,
  `[i]`) stay within the allocation.
- **Aliasing rules hold for the whole reference lifetime.** `&mut T` is unique
  while live; `&T` (outside `UnsafeCell`) is immutable while live; a reference
  passed to a function is live for the whole call. The exact rules are *not yet
  finalized* — the Reference gives principles, and Miri checks a model of them
  (Stacked/Tree Borrows). That is why a clean Miri run is evidence, not proof.
- **Immutable bytes stay immutable.** Bytes reachable through a const-promoted
  expression, an immutable `static`, or a `'static`-extended borrow in a
  `static`/`const` initializer must not be written unless inside `UnsafeCell`.
- **Every value produced is valid for its type** — the *validity invariant*.
  "Producing" happens on any assignment, read, argument pass, or return, not
  only on dereference. Concretely: `bool` is `0` or `1`; `char` is not a
  surrogate and is `<= char::MAX`; an `enum` has a valid discriminant and valid
  fields; integers, floats, and raw pointers are initialized; a reference or
  `Box` is aligned, non-null, non-dangling, and points to a valid value;
  `NonNull`/`NonZero` are in range; a `!` never exists; wide-pointer metadata
  matches the unsized tail. `mem::zeroed::<bool>()`, transmuting an integer to
  an enum, and `MaybeUninit::assume_init` on partially written memory all
  violate this.
- **ABI and unwinding match.** Calling with the wrong ABI, or unwinding through
  a frame that does not allow it (`extern "C"` instead of `"C-unwind"`), is UB.
- **Layout and provenance are preserved.** Layout is not stable without
  `#[repr(C)]`/`#[repr(transparent)]`; integer-to-pointer and pointer arithmetic
  must keep valid provenance; the destructor runs exactly once.
- **Runtime assumptions hold.** For example, a Rust frame is not deallocated
  without running its destructors (`longjmp` across Rust frames violates this).

Keep the unsafe block around only the operations needing it:

```rust
/// # Safety
/// `ptr` must point to a live, aligned `Widget` for the returned lifetime.
unsafe fn widget_ref<'a>(ptr: *const Widget) -> &'a Widget {
    // SAFETY: the caller contract establishes validity, alignment, and lifetime.
    unsafe { &*ptr }
}
```

`unsafe_op_in_unsafe_fn` is allow-by-default through edition 2021 and
warn-by-default in edition 2024: an `unsafe fn` body is not implicitly proven,
so write inner `unsafe {}` blocks with their own `// SAFETY:` comments. Match
the repo's edition and lint policy. Some projects (rust-lang/rust among them)
require `// SAFETY:` comments and `# Safety` docs to be human-written; check
`CONTRIBUTING.md`/`AGENTS.md` before authoring them.

Build a small safe abstraction around raw operations. Put validation before the
unsafe boundary and prevent callers from constructing invalid states through
safe APIs.

## `static mut` and global state

Taking `&` or `&mut` to a `static mut` is `deny`-by-default in edition 2024
(`static_mut_refs`) because it creates aliased mutable references trivially.
Prefer, in order: an atomic; `Mutex`/`RwLock` in a `static`; `OnceLock`/
`LazyLock` for init-once data; `SyncUnsafeCell` with a documented external
synchronization invariant when a lock is genuinely unaffordable. If `static mut`
must remain, access it only through raw pointers (`&raw mut STATE`), never
references.

## Initialization, layout, and ownership

- Use `MaybeUninit<T>` only with a clear initialized-element count and cleanup
  path for partial failure.
- Do not create references to uninitialized, misaligned, dangling, or
  insufficiently valid memory.
- Do not assume Rust layout unless the type has an explicit representation such
  as `#[repr(C)]` and the field types also have compatible layout.
- Be careful with enum/niche layout; it is often an optimization detail, not a
  stable ABI.
- When reconstructing `Vec`, `Box`, or slices from raw parts, prove allocator,
  capacity, length, element initialization, and unique ownership match.
- Document every `unsafe impl Send`/`Sync` with the synchronization or
  immutability invariant that makes cross-thread access sound.

## C and host FFI

Keep the ABI narrow and explicit:

- Declare foreign items in `unsafe extern "C" { ... }` (required in edition
  2024, allowed since 1.82). Mark each item: `pub safe fn sqrt(x: f64) -> f64;`
  when any argument is sound, `pub unsafe fn strlen(p: *const c_char) -> usize;`
  when the caller must uphold a contract; unmarked items are `unsafe`. Use
  `extern "C-unwind"` on either side when unwinding may cross the boundary.
- Exported symbols use `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "...")]`,
  `#[unsafe(link_section = "...")]` in edition 2024; the `unsafe(...)` wrapper
  records that a symbol collision or wrong section is the author's problem.
- Use `#[repr(C)]` data; pass buffers as pointer-plus-length/capacity with
  exact units.
- Define nullability, alignment, encoding, and lifetime for every pointer.
- Avoid exposing Rust `String`, `Vec`, trait objects, references, panics, or
  compiler-specific enum layout directly across the ABI.
- Identify which side allocates and export the matching destroy/free function.
- Make double-free, use-after-free, and use-after-callback impossible or
  detectable through opaque handles and ownership transfer.
- Translate errors to stable result codes plus an owned diagnostic mechanism.
- Contain panics before they cross a non-unwinding foreign boundary
  (`catch_unwind` at the exported function, or `"C-unwind"` deliberately).
- Define callback thread, reentrancy, lifetime, and cancellation rules.
- Note edition-2024 newly-`unsafe` std functions at the process boundary:
  `std::env::set_var`/`remove_var` and `CommandExt::before_exec`.

For Node/Bun/Python/Swift/other hosts, test the real host boundary—not only the
Rust function behind it. Exercise empty buffers, invalid UTF-8, large lengths,
nulls where permitted, repeated create/destroy, callback teardown, and
concurrent calls.

## Verification tools

Use the tools already supported by the project and pinned toolchain:

- **Miri:** undefined behavior in many unsafe operations and aliasing cases,
  under a specific aliasing model;
- **sanitizers:** address, thread, leak, or memory errors on supported targets;
- **Loom:** modeled interleavings for small synchronization code;
- **fuzzing:** malformed inputs and state transitions;
- **Valgrind/platform tools:** allocator and syscall evidence where relevant.

Each tool has coverage limits, and the aliasing rules themselves are still
being finalized. A clean Miri or sanitizer run is evidence, not a soundness
proof. Review the invariants manually.

## Performance workflow

1. Define the user-visible metric and representative workload.
2. Record a stable before measurement in the intended release profile.
3. Profile to locate time, allocation, contention, cache, I/O, or code-size
   costs.
4. Change the highest-impact representation or operation.
5. Re-run correctness and safety gates.
6. Compare distributions, not one timing.

Start with:

- algorithmic complexity and repeated work;
- data layout, cache locality, enum/struct size, and indirection;
- allocation count, buffer reuse, and avoidable formatting;
- cloning/retention in hot loops;
- I/O batching and syscall count (buffered readers/writers; `io::copy`
  specializes to `copy_file_range`/`sendfile`/`splice` on Linux when both ends
  are file descriptors);
- lock contention, queueing, and task fan-out;
- future size: every local live across an `.await` becomes a field of the
  state machine, so a large buffer held across an await bloats every task that
  holds it — scope it or box it;
- code size/monomorphization when compile time or instruction cache matters.

Iterator versus loop, generic versus dynamic dispatch, stack versus heap, and
clone versus borrow are context-dependent. Inspect optimized output or benchmark
when the choice matters; do not encode folklore as fact.

Use `cargo build --release`, the repo's custom profiles, Criterion, perf,
Instruments, flamegraph, heap profilers, or build timings as applicable. Record
the exact profile and target. Debug builds are for correctness feedback, not
speed claims.

For microbenchmarks:

- prevent constant folding/dead-code elimination through the harness;
- separate setup from the measured operation;
- choose inputs that resemble production distributions;
- watch allocator and CPU frequency noise;
- confirm the optimized behavior still produces the same result.

## Primary references

- [Rust Reference: behavior considered undefined](https://doc.rust-lang.org/reference/behavior-considered-undefined.html)
- [Rustonomicon](https://doc.rust-lang.org/nomicon/)
- [Unsafe Code Guidelines reference](https://rust-lang.github.io/unsafe-code-guidelines/)
- [Edition Guide: Rust 2024 unsafe changes](https://doc.rust-lang.org/edition-guide/rust-2024/)
- [Rust Performance Book](https://nnethercote.github.io/perf-book/)
