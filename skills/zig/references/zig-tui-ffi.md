# Zig for terminal/TUI kernels and FFI

Evaluate Zig for resource-sensitive kernels or a broader native implementation when its ownership, layout, and execution model fit the workload. Host-language orchestration can earn its place through concrete SDK, UI/component, platform, or interoperability benefits. Choose the boundary from end-to-end performance and correctness evidence; manual iteration speed alone should not decide it, and Zig need not be limited to small plugins.

## Candidate responsibilities

Potential Zig responsibilities include:

- filesystem traversal and byte scanning;
- native literal/regex-like search kernels;
- terminal cell buffers, diffing, ANSI segment coalescing, glyph transforms;
- image/audio/diagram kernels;
- parsers with bounded memory and deterministic diagnostics;
- C ABI libraries loaded by Bun/Node/Rust/Python/etc.

Potential host-language responsibilities, where existing integration benefits justify them, include:

- model/provider SDKs;
- auth and OAuth storage;
- HTTP streaming and retries;
- JSON schema/tool-call marshalling;
- TUI state machines and command routing.

Compare a native core, a host implementation, and a split only when those alternatives could change the result. Account for calls, copying, allocations, marshaling, startup, and error/lifecycle ownership across the boundary. Available agents and language skills make native options candidates for evaluation; they do not prove a performance advantage or remove maintenance and safety obligations.

## C ABI boundary

For Zig 0.17, `@cImport` is removed. Translate headers through the official `translate-c` package; see [zig-migration-017.md](zig-migration-017.md). `b.addTranslateC` still exists but is deprecated. Review casts involving extern layouts because `@bitCast` no longer accepts extern structs/unions.

Export small, stable functions. Prefer pointer + length pairs and explicit output buffers or allocator-owned result handles.

```zig
export fn sift_search_literal(
    haystack_ptr: [*]const u8,
    haystack_len: usize,
    needle_ptr: [*]const u8,
    needle_len: usize,
) c_int {
    const haystack = haystack_ptr[0..haystack_len];
    const needle = needle_ptr[0..needle_len];
    return if (std.mem.indexOf(u8, haystack, needle) != null) 1 else 0;
}
```

Avoid returning raw pointers without an accompanying destroy/free function. For host-loaded dynamic libraries, include an explicit `destroy_*` export for every allocation returned across the boundary.

## Result handles

For richer APIs, return an opaque handle:

```zig
const SearchResult = struct {
    matches: []Match,
    bytes_scanned: usize,
};

export fn search_result_destroy(ptr: ?*SearchResult) void {
    if (ptr) |result| {
        // free owned fields, then result
    }
}
```

Host code should not infer Zig layout for non-extern structs.

## Terminal performance

Measure these separately:

- parse time;
- layout time;
- render/cell-fill time;
- ANSI serialization time;
- host FFI conversion time;
- host TUI repaint time.

Keep benchmarks synthetic and real-repo/real-terminal. Synthetic benches catch regressions; real benches catch cache, filesystem, terminal, and FFI costs.

## Output shaping for speed

For search and read APIs, expose policy knobs that prevent unnecessary work:

- include/exclude hidden files;
- skip vendor/build-output directories by default;
- honor `.gitignore` when appropriate;
- cap file bytes, file count, match count, and recursion depth;
- choose detail level: `paths`, `locations`, `snippets`, `full`.

The fastest byte scanner still loses if it scans too much or returns too much.

## Inspiration patterns

Use OpenTUI and Ghostty as source candidates when researching native terminal designs; inspect the relevant mechanisms in their actual sources. Keep the boundary testable and use representative end-to-end measurements to decide whether a narrow kernel, a broader Zig surface, or a host implementation fits best.

## Policy adaptation (2026-11-01)

The responsibility split is a candidate design rather than a fixed language assignment. This user-directed change replaces manual iteration speed as the deciding factor with system performance, correctness, and concrete integration benefits; it adds no runtime benchmark result or migration authority.
