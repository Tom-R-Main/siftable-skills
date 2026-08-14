# Zig std.Io async I/O, 0.16+

This reference tracks the versioned `std.Io` surface summarized in `source-grounding.md`. Treat its code as 0.16-oriented migration guidance and compile it against the pinned project toolchain.

Use only when the project is pinned to a Zig version that has the new `std.Io` primitives or when explicitly migrating toward them. For older Zig, the language-level `async` / `await` keywords are removed and should not be reintroduced.

## Mental model

- `async` means work may be decoupled from the caller and awaited later.
- `concurrent` means work must make progress simultaneously; use it only when simultaneous execution is required.
- The I/O implementation decides how asynchrony is executed: blocking, thread pool, event loop, io_uring/kqueue/iocp, or another strategy.

Pass `std.Io` like an allocator: explicit, testable, and not global.

```zig
const std = @import("std");
const Allocator = std.mem.Allocator;
const Io = std.Io;

fn mainImpl(gpa: Allocator, io: Io) !void {
    try runWork(gpa, io);
}

pub fn main() !void {
    var debug_allocator: std.heap.DebugAllocator(.{}) = .init;
    defer std.debug.assert(debug_allocator.deinit() == .ok);
    const gpa = debug_allocator.allocator();

    var threaded: std.Io.Threaded = .init(gpa, .{});
    defer threaded.deinit();
    const io = threaded.io();

    try mainImpl(gpa, io);
}
```

## Spawn and await

```zig
var future = io.async(doWork, .{io, "task"});
try future.await(io);
```

If work can fail, be careful not to `try` the first await and skip cleanup for later futures.

## Cancellation pattern

For spawned work, add cancellation immediately after spawning. `cancel` has await-like semantics plus a cancellation request, and repeated await/cancel operations are intended to be idempotent.

```zig
var a = io.async(loadChunk, .{ allocator, io, path_a });
defer if (a.cancel(io)) |bytes| allocator.free(bytes) else |_| {};

var b = io.async(loadChunk, .{ allocator, io, path_b });
defer if (b.cancel(io)) |bytes| allocator.free(bytes) else |_| {};

const a_bytes = try a.await(io);
const b_bytes = try b.await(io);
useBytes(a_bytes, b_bytes);
```

This pattern keeps ordinary `try` / `return` flow and prevents leaks when one task fails before another completes.

## Async vs concurrent

Use `io.async` when tasks can be scheduled opportunistically and sequential awaiting is valid.

Use `try io.concurrent` when a deadlock is possible unless producer and consumer make progress at the same time.

```zig
var queue: Io.Queue([]const u8) = .init(&.{});

var producer_task = try io.concurrent(producer, .{ io, &queue });
defer producer_task.cancel(io) catch {};

var consumer_task = try io.concurrent(consumer, .{ io, &queue });
defer _ = consumer_task.cancel(io) catch {};

const item = try consumer_task.await(io);
```

Handle `error.ConcurrencyUnavailable`, especially in single-threaded builds or constrained runtimes.

## zio compatibility note

If a repo uses [`lalinsky/zio`](https://github.com/lalinsky/zio), treat it as a project-level async runtime choice. Inspect the pinned zio version and branch before editing. Do not mix raw `std.Io` assumptions into a zio codebase unless the repo already bridges them.

Recent Zio design notes emphasize features beyond direct `std.Io` expression, such as generalized timeout/cancellation helpers (`AutoCancel`) and backend-specific behavior. Do not assume a std-only rewrite preserves Zio semantics.

Backend caveats matter:

- Linux `io_uring`: async DNS and `-fsingle-threaded` can be appropriate in Zio versions that support them.
- Windows IOCP: single-threaded can be viable when file operations and DNS are async.
- Other systems: prefer the thread-pool backend unless the pinned Zio docs or local tests show otherwise.

Useful review questions:

1. Does every spawned future have a cleanup/cancel path?
2. Did we ask for concurrency only where simultaneous progress is semantically required?
3. Are queues, tasks, and buffers owned by a lifetime that outlives all futures?
4. Does single-threaded mode fail clearly rather than deadlocking silently?
