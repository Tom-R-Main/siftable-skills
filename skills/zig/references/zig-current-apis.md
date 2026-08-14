# Zig current API guardrails

Zig evolves rapidly. Treat this reference as a checklist, not as a replacement for the local compiler and nearby working code. The official versioned sources behind these examples are mapped in `source-grounding.md`.

## Version detection

Before editing, check the actual project dialect:

```sh
zig version
zig env
find .. -maxdepth 3 \( -name .zig-version -o -name build.zig.zon -o -name build.zig \) -print
```

Prefer the project-pinned toolchain. If code and global `zig version` disagree, trust the repo's pin and CI.

## Migration and package workflow

When moving code across Zig versions, read the versioned release notes or upgrade guide before guessing from compiler errors. They often document the exact breaking change, rationale, and rewrite pattern.

For package updates, prefer `zig fetch --save` so `build.zig.zon` records the resolved package hash:

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

Resolve it from `build.zig` with `b.dependency("libmytools", .{ ... })`. Do not import another package's `build.zig` directly or manually compensate for its filesystem location.

## Build system pattern, Zig 0.15+

Prefer modules and `root_module`:

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

## Writer and reader pattern, Zig 0.15+

The modern writer/reader interfaces carry buffers explicitly.

```zig
const std = @import("std");

pub fn main(init: std.process.Init) !void {
    var stdout_buf: [4096]u8 = undefined;
    var stdout_file = std.Io.File.stdout().writer(init.io, &stdout_buf);
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
var file_reader = file.reader(&file_buf);
const reader = &file_reader.interface;

while (try reader.takeDelimiter('\n')) |line| {
    try handleLine(line);
}
```

Always flush buffered writers when output must be visible or persisted.

## Containers and allocators

Modern Zig code commonly uses `.empty` for empty unmanaged collections and `.init(...)` when a value has configuration or state.

```zig
var list: std.ArrayList(u8) = .empty;
defer list.deinit(allocator);
try list.appendSlice(allocator, "abc");

var gpa: std.heap.DebugAllocator(.{}) = .init;
defer std.debug.assert(gpa.deinit() == .ok);
const allocator = gpa.allocator();
```

Libraries should usually accept `allocator: std.mem.Allocator` instead of selecting a global allocator.

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
std.heap.GeneralPurposeAllocator(.{})              // prefer DebugAllocator in new code
async foo(); await frame;                          // old language keywords removed
```

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
