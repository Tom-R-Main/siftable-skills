# Zig 0.17 API guardrails

Examples target Zig 0.17.0. Check the project pin before applying them; for breaking changes read [zig-migration-017.md](zig-migration-017.md). The source of truth is the selected compiler and its standard library.

## Version detection

Before editing, check the actual project dialect:

```sh
zig version
zig env
rg --files --hidden -g '.zig-version' -g 'build.zig.zon' -g 'build.zig' -g '!zig-out' -g '!.zig-cache' -g '!.git'
```

Prefer the project-pinned toolchain. If code and global `zig version` disagree, trust the repo's pin and CI. `zig env` identifies the local library; read its source when signatures are unclear.

If a matching source checkout is available, set `ZIG_REFERENCE_DIR` to its absolute path. Select a matching release tag rather than assuming HEAD matches the installed compiler:

```sh
git -C "$ZIG_REFERENCE_DIR" show 0.17.0:lib/std/Io/File.zig
```

Verify the tag locally. This reads source without checking out a branch or fetching; a reference checkout is not a compiler installation.

For worked examples, an optional `zig-guide` source checkout contains:

- `snippets/01-getting-started/zig-0-17.zig`: migration shapes and observable output.
- `snippets/03-standard-library/allocators.zig` and `arraylist.zig`: allocation and pointer-lifetime examples.
- `snippets/03-standard-library/cancellation.zig`: cancellation and simultaneous-progress requirements.

Its CI tracks **master**, so inspect its tested version and compare examples against the selected release. Its older prose and C translation examples can lag the release notes; CI configuration is not evidence of a fresh successful run.

## Migration and package workflow

When moving code across Zig versions, read the versioned release notes or upgrade guide before guessing from compiler errors. They often document the exact breaking change, rationale, and rewrite pattern.

When a package update is authorized, prefer `zig fetch --save` so `build.zig.zon` records the resolved package hash:

```sh
zig fetch --save git+https://example.com/owner/package.git
zig fetch --save https://example.com/owner/package/archive/refs/heads/main.tar.gz
```

Use `--save-exact` only when the project deliberately wants to store the URL verbatim instead of Zig's resolved package identity.

For a local project dependency, prefer a relative `.path` entry in `build.zig.zon`:

```zig
.dependencies = .{
    .libmytools = .{ .path = "extern/libmytools" },
},
```

In 0.17, path dependencies must stay within the parent package root. Plain `zig fetch` populates the global cache; `--save` variants also fetch locally, and `zig build` fetches locally as well. `--pkg-path` / `ZIG_LOCAL_PKG_DIR` control the local package path.

Resolve it from `build.zig` with `b.dependency("libmytools", .{ ... })`. Do not import another package's `build.zig` directly or manually compensate for its filesystem location.

## Build system pattern, Zig 0.17

Prefer modules and `root_module`; `b.standardOptimizeOption` now returns `std.lang.Optimize`:

```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const mod = b.createModule(.{
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    });

    const exe = b.addExecutable(.{
        .name = "app",
        .root_module = mod,
    });

    b.installArtifact(exe);

    const tests = b.addTest(.{
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });

    const run_tests = b.addRunArtifact(tests);
    const test_step = b.step("test", "Run unit tests");
    test_step.dependOn(&run_tests.step);
}
```

Use `exe.root_module.addImport("name", module)` for imports. Prefer `exe.root_module.addCSourceFile`, `exe.root_module.linkLibrary`, `exe.root_module.linkSystemLibrary`, and `exe.root_module.link_libc = true` style APIs when the local compiler supports them.

## Writer and reader pattern, Zig 0.17

The modern writer/reader interfaces carry buffers explicitly.

```zig
const std = @import("std");

pub fn main(init: std.process.Init) !void {
    var stdout_buf: [4096]u8 = undefined;
    var stdout_file = std.Io.File.stdout().writerStreaming(init.io, &stdout_buf);
    const stdout = &stdout_file.interface;

    try stdout.print("hello {s}\n", .{"zig"});
    try stdout.flush();
}
```

For in-memory output:

```zig
var buf: [256]u8 = undefined;
var w: std.Io.Writer = .fixed(&buf);
try w.print("{s}:{d}", .{ "row", 12 });
const rendered = w.buffered();
```

For input:

```zig
var file_buf: [4096]u8 = undefined;
var file_reader = file.reader(io, &file_buf);
const reader = &file_reader.interface;

while (try reader.takeDelimiter('\n')) |line| {
    try handleLine(line);
}
```

Pass `io: std.Io` explicitly. Use `readerStreaming` / `writerStreaming` for streams such as stdin, stdout, and pipes; `reader` / `writer` default to positional I/O and fall back to streaming. Reader-returned slices borrow its buffer and may be invalidated by the next read; copy them if retained. Flush buffered writers before completion or when output must become visible; durability may additionally require a file sync.

## Containers and allocators

Modern Zig code commonly uses `.empty` for empty unmanaged collections and `.init(...)` when a value has configuration or state.

```zig
var safe: std.heap.SafeAllocator = .init(std.heap.page_allocator, .{});
defer {
    const leaks = safe.deinit();
    std.debug.assert(leaks == 0);
}
const allocator = safe.allocator();

var list: std.ArrayList(u8) = .empty;
defer list.deinit(allocator);
try list.appendSlice(allocator, "abc");
```

Libraries should usually accept `allocator: std.mem.Allocator` instead of selecting a global allocator. `SafeAllocator.deinit()` returns a leak count and frees backing memory; all users must finish before deinit. Its backing allocator must be thread-safe for the wrapper to be thread-safe. Keep deinit outside expressions that might not execute in unsafe modes.

Use `try allocator.print(fmt, args)` for allocated strings and `try std.mem.print(&buffer, fmt, args)` for caller-owned output. Sentinel variants are `allocator.printSentinel(fmt, args, 0)`, `std.mem.printSentinel(&buffer, fmt, args, 0)`, and `allocator.dupeSentinel(u8, text, 0)`. Free allocated results through the allocator that produced them, preserving sentinel slice types when freeing so the allocation size remains correct.

For stack-first allocation, provide a buffer to `std.heap.BufferFirstAllocator.init(&buffer, fallback_allocator)` and use `.allocator()`. Keep both the buffer and allocator instance alive for their allocations.

Use an allocator when the callee must create storage whose size or lifetime is not covered by caller-provided memory. Use a buffer when the caller can bound and own the storage. For C APIs that require null-terminated strings, prefer accepting `[:0]const u8` when callers can provide it; otherwise allocate a temporary sentinel copy only for the call's required lifetime.

Do not deinitialize values you did not create or receive ownership of. For example, `std.process.Init.environ_map` is prepared and cleaned up by process startup; a map created with `std.process.Environ.createMap(...)` is caller-owned and must be deinitialized by the caller.

Benchmark allocation strategies in safe modes when objects are large or hot. `std.heap.MemoryPool` can do useful poisoning/undefined writes on create/destroy; that safety behavior may dominate costs for large item types.

## Format methods

In recent Zig, custom formatting uses `format(self, writer)` and callers often need `{f}` when formatting a formatter object.

```zig
pub fn format(self: Id, writer: *std.Io.Writer) std.Io.Writer.Error!void {
    try writer.print("id={d}", .{self.value});
}
```

## Removed or commonly stale patterns

Avoid unless the project is pinned to an older compiler that requires them:

```zig
pub usingnamespace @import("other.zig");          // removed; explicitly re-export names
const stdout = std.io.getStdOut().writer();       // old writer API
.root_source_file = b.path("src/main.zig"),       // old compile-step field
var list: std.ArrayList(u8) = .{};                // ambiguous/stale container init
std.ArrayListUnmanaged(u8)                         // old naming in many codebases
std.heap.GeneralPurposeAllocator(.{})              // use SafeAllocator in 0.17
async foo(); await frame;                          // old language keywords removed
```

For 0.17-specific removals and deprecations, including reflection and C translation, use [zig-migration-017.md](zig-migration-017.md).

## Testing

Use ordinary Zig tests for local invariants and doctests for examples that should stay compiled.

```zig
const std = @import("std");

test "read window stays in bounds" {
    const source_count: usize = 10;
    const source_index: usize = 3;
    const read_count: usize = 4;
    try std.testing.expect(source_index + read_count <= source_count);
}
```

When debugging failures, prefer compiler errors and test traces over guessing. Zig deliberately makes many mistakes loud at compile time.
