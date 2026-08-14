# Zig for terminal/TUI kernels and FFI

Use Zig when the hot path is small, deterministic, byte-oriented, and easy to measure. Keep orchestration in the host language when it depends on provider SDKs, auth, JSON streams, UI state, or rapid product iteration.

## Recommended split

Zig owns:

- filesystem traversal and byte scanning;
- native literal/regex-like search kernels;
- terminal cell buffers, diffing, ANSI segment coalescing, glyph transforms;
- image/audio/diagram kernels;
- parsers with bounded memory and deterministic diagnostics;
- C ABI libraries loaded by Bun/Node/Rust/Python/etc.

TypeScript/host owns:

- model/provider SDKs;
- auth and OAuth storage;
- HTTP streaming and retries;
- JSON schema/tool-call marshalling;
- TUI state machines and command routing;
- product-level feature iteration.

## C ABI boundary

Export small, stable functions. Prefer pointer + length pairs and explicit output buffers or allocator-owned result handles.

```zig
export fn zig_search_literal(
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

OpenTUI and Ghostty both validate the same architectural direction: a fast native core with a host-friendly API boundary, optimized render/parser loops, and careful terminal semantics. Copy the pattern, not necessarily the internals: define a narrow native kernel, keep it easy to test, and add benchmark gates before broadening the Zig surface.
