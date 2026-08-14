---
name: zig
description: Build, review, debug, migrate, or optimize Zig code. Use for .zig, build.zig, build.zig.zon, Zig standard-library API questions, allocator and ownership bugs, comptime code, C ABI or host FFI modules for Bun/Node/TypeScript, terminal/TUI kernels, byte scanners, benchmarks, or Zig 0.15/0.16+ std.Io migration work. Prioritize local version detection, current official docs, explicit memory ownership, safety-mode choices, and measured performance claims.
---

# Zig

Use this skill for Zig implementation, review, migration, and performance work. Zig changes quickly; prefer the repository's pinned compiler, nearby working code, and official docs over memory.

## First Moves

1. Identify the actual Zig dialect before editing: inspect `.zig-version`, `build.zig.zon`, CI config, `README`, and existing `build.zig` patterns.
2. If shell access is available, run `zig version`; use `zig env` or `zig std` when API behavior is unclear.
3. Match the local codebase unless the request is explicitly a migration.
4. Report the version assumption when it affects the patch, review, or answer.
5. For current-language questions, check the official Zig docs at `https://ziglang.org/documentation/master/`; prefer versioned docs when the project is pinned.
6. Read `references/source-grounding.md` when a recommendation depends on a versioned API, an adopted external convention, or community experience rather than local evidence.

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
- Treat ReleaseFast and ReleaseSmall as safety-check-off modes; prove correctness in Debug or ReleaseSafe before benchmarking.

## Zig Versus Host Code

For agent, CLI, and TUI products, keep Zig narrow until measurement proves a broader native core is worth it.

- Put in Zig: filesystem traversal, byte scanning, parsers, native search kernels, terminal render buffers, ANSI/stringification kernels, compact deterministic algorithms, and host-loaded C ABI libraries.
- Keep in TypeScript or the host layer: model/provider SDKs, auth, HTTP streaming, JSON-heavy orchestration, UI state, command routing, and fast product iteration.
- Cross FFI with small C ABI functions, pointer-plus-length pairs, validated inputs, and explicit destroy/free exports for Zig-allocated results.

## Validation Gates

After touching Zig, run the narrowest meaningful gates first, then broaden:

```sh
zig fmt --check $(git ls-files '*.zig')
zig build test
zig build
```

Use `scripts/zig-gates.sh` from this skill as a conservative helper when a repo has a normal `build.zig`:

```sh
/path/to/zig/scripts/zig-gates.sh
```

Supported environment knobs:

- `SKIP_ZIG_BUILD=1` to skip `zig build`.
- `SKIP_ZIG_TEST=1` to skip `zig build test`.
- `ZIG_BUILD_ARGS="..."` for extra build args.
- `ZIG_TEST_ARGS="..."` for extra test args.

Only claim speedups with before/after numbers from ReleaseFast or the repo's benchmark lane, plus correctness evidence from Debug or ReleaseSafe.

## Open References As Needed

- `references/zig-current-apis.md`: modern build-system, writer/reader, allocator, and stale API traps.
- `references/zig-philosophy-style.md`: ownership, naming, invariants, error handling, and style.
- `references/zig-async-io-016.md`: `std.Io`, async/concurrent/cancel patterns for 0.16+ code.
- `references/zig-tui-ffi.md`: terminal kernels, host FFI boundaries, and benchmark shaping.
- `references/source-grounding.md`: official documentation, adopted conventions, community inputs, and the boundary between sourced facts and this skill's synthesis.

Keep these as checklists, not laws. If local compiler errors or nearby working code disagree, follow the pinned project and document the reason.
