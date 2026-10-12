---
name: zig
description: Build, review, debug, migrate, and optimize Zig code. Use for build scripts, allocator lifetimes, std.Io, C FFI, and measured performance with the project toolchain.
---

# Zig

Use this skill for Zig implementation, review, migration, and performance work. The guidance targets **Zig 0.17.0** for new, unpinned work. Preserve an existing project's compiler pin unless migration is requested; 0.16 and 0.18-dev are different dialects.

## First Moves

1. Identify the actual Zig dialect before editing: inspect `.zig-version`, `build.zig.zon`, CI config, `README`, and existing `build.zig` patterns.
2. Run the project-selected `zig version` and inspect `zig env` for its standard-library directory. A global compiler or reference checkout may be a different version; do not treat either as the project toolchain.
3. Match the local codebase unless the request is explicitly a migration.
4. Report the version assumption when it affects the patch, review, or answer.
5. For 0.17 work, use the [versioned language reference](https://ziglang.org/documentation/0.17.0/), [standard-library docs](https://ziglang.org/documentation/0.17.0/std/), and [release notes](https://ziglang.org/download/0.17.0/release-notes.html). Use master only for an explicitly selected development compiler.
6. For a 0.16 → 0.17 migration, read `references/zig-migration-017.md` before editing. Audit semantic changes as well as compilation failures, especially `containsAtLeastScalar`, `@bitCast`, and `@hasDecl`.

## Implementation Bias

Write Zig as explicit systems code whose invariants are visible at call sites.

- Pass `std.mem.Allocator`, I/O handles, buffers, configuration, and host handles explicitly.
- Make ownership and lifetimes obvious: caller-owned memory, borrowed slices, arena lifetimes, and destroy/free paths.
- Choose allocation by lifetime: caller buffers for bounded storage, arenas for cohorts that die together, and explicit ownership for independently replaced values. Avoid one arena for unrelated lifetimes.
- Use `errdefer` for partial initialization and `defer` in reverse ownership order.
- Treat `try` as propagation, not handling. Return precise errors from libraries and choose recovery, diagnostics, degradation, or termination at a deliberate semantic boundary.
- Prefer `const`; use `var` only when mutated.
- Name low-level integers by unit: `*_count`, `*_index`, `*_size`, and `*_offset`.
- Avoid passing large structs by value in hot or non-inlined paths unless copying is intentional and measured; prefer pointers, slices, or small handles.
- Keep `anytype` and comptime interfaces narrow and discoverable; use concrete types or runtime interfaces when substitution happens at runtime, and measure specialization, compile-time, and code-size costs.
- Optimize representation before instructions: consider contiguous storage, stable indices, compact handles, and bulk lifetime management before tuning individual loops.
- Contain volatile pre-1.0 standard-library APIs behind small local adapters instead of leaking version-specific `std.Io`, build, or container details through otherwise stable library boundaries.
- For parsers, queues, caches, and decoded payloads, choose explicit resource bounds and capacity behavior where input or retained work can grow. Distinguish a per-allocation limit from a total memory budget.
- Keep programmer invariants separate from external-input validation. Test fallible mutations for both resource cleanup and state rollback; leak-free failure can still leave corrupt counters or published state.
- In 0.17, use `.debug`, `.safe`, `.fast`, and `.small` (`std.lang.Optimize`). The last two disable runtime safety checks; prove correctness in debug or safe before benchmarking.

## Zig Versus Host Code

For agent, CLI, and TUI products, keep Zig narrow until measurement proves a broader native core is worth it.

- Put in Zig: filesystem traversal, byte scanning, parsers, native search kernels, terminal render buffers, ANSI/stringification kernels, compact deterministic algorithms, and host-loaded C ABI libraries.
- Keep in TypeScript or the host layer: model/provider SDKs, auth, HTTP streaming, JSON-heavy orchestration, UI state, command routing, and fast product iteration.
- Cross FFI with small C ABI functions, pointer-plus-length pairs, validated inputs, and explicit destroy/free exports for Zig-allocated results.

## Validation Gates

After touching Zig, run the narrowest meaningful gates first, then broaden:

```sh
zig fmt --check build.zig src
zig build test
zig build
```

Adapt paths and test steps to the project. Use its selected compiler; do not run these examples with an unrelated global Zig. If a required compiler is unavailable, report that limit rather than claiming compilation or installing it without authorization.

Select additional gates from the changed contract: split-input/property and fuzz tests for parsers/codecs; real host/layout tests for FFI; native backend tests for platform changes; deterministic fault/recovery checks for stateful systems. Verify that the step imports/instantiates the changed module and distinguish executed tests from compile-only, skipped, suppressed, or report-only checks. See `references/zig-production-patterns.md`.

For C/FFI memory corruption or leaks, read `references/zig-valgrind.md` to choose a Memcheck lane with visible allocation boundaries and reviewed suppressions. Keep ordinary safe-mode and allocator-failure coverage.

Use `scripts/zig-gates.sh` from this skill as a conservative helper when a repo has a normal `build.zig`:

```sh
/path/to/zig/scripts/zig-gates.sh
```

Supported environment knobs:

- `SKIP_ZIG_BUILD=1` to skip `zig build`.
- `SKIP_ZIG_TEST=1` to skip `zig build test`.
- `ZIG_BUILD_ARGS="..."` for extra build args.
- `ZIG_TEST_ARGS="..."` for extra test args.

Only claim speedups with before/after numbers from `-O fast` / `-Doptimize=fast` or the repo's benchmark lane, plus correctness evidence from debug or safe. Older compiler pins use their own mode spellings.

## Open References As Needed

- `references/source-grounding.md`: primary source provenance and adopted conventions.
- `references/zig-current-apis.md`: 0.17 build-system, writer/reader, allocator, and formatting patterns.
- `references/zig-migration-017.md`: 0.16 → 0.17 language, reflection, container, build, and C translation changes; silent behavior traps.
- `references/zig-philosophy-style.md`: ownership, naming, invariants, error handling, and style.
- `references/zig-async-io-016.md`: `std.Io`, async/concurrent/cancel patterns checked against 0.17; retains its existing filename for compatibility.
- `references/zig-production-patterns.md`: source-backed Ghostty/TigerBeetle architecture, domain map, allocation, FFI, simulation, testing, and measurement choices; both source checkouts currently target 0.16.
- `references/zig-valgrind.md`: Ghostty Memcheck integration, allocator visibility, definedness, suppressions, supported platforms, and evidence limits.
- `references/zig-tui-ffi.md`: terminal kernels, host FFI boundaries, and benchmark shaping.

Keep these as checklists, not laws. If local compiler errors or nearby working code disagree, follow the pinned project and document the reason.
