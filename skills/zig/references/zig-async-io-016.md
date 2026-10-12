# Zig std.Io async I/O, Zig 0.17

This file retains its earlier filename, but examples target Zig 0.17.0. Match older project pins explicitly. `io.async` and `future.await(io)` are library methods; the removed language-level `async` / `await` syntax must not be reintroduced.

## Mental model

- `async` means work may be decoupled from the caller and awaited later.
- `concurrent` means work must make progress simultaneously; use it only when simultaneous execution is required.
- The I/O implementation decides how asynchrony is executed: blocking, thread pool, event loop, io_uring/kqueue/iocp, or another strategy.

Pass `std.Io` like an allocator: explicit, testable, and not global. Ordinary executables can use `std.process.Init`; embedded runtimes that own an `Io.Threaded` instance must join/cancel tasks before deinitializing it.

```zig
const std = @import("std");
const Allocator = std.mem.Allocator;
const Io = std.Io;

fn mainImpl(gpa: Allocator, io: Io) !void {
    try runWork(gpa, io);
}

pub fn main(init: std.process.Init) !void {
    try mainImpl(init.gpa, init.io);
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

Here the cancel defers are the sole owners of successful result buffers; `useBytes` borrows them. Do not also free or transfer those slices without changing the cleanup path: await/cancel cache the same result and repeated calls do not create fresh ownership. Future await/cancel are idempotent but not thread-safe. Propagate `error.Canceled` rather than silently swallowing it inside task bodies.

This pattern keeps ordinary `try` / `return` flow and prevents leaks when one task fails before another completes.

## Async vs concurrent

Use `io.async` when tasks can be scheduled opportunistically and sequential awaiting is valid. The function may execute inline **before `io.async` returns**. Do not start a blocking producer, an indefinite sleeper, or a worker awaiting a signal from the caller this way; later cancellation cannot help if the spawn call never returns.

Use `try io.concurrent` when a deadlock is possible unless producer and consumer make progress at the same time.

```zig
var queue: Io.Queue([]const u8) = .init(&.{});

var producer_task = try io.concurrent(producer, .{ io, &queue });
defer producer_task.cancel(io) catch {};

var consumer_task = try io.concurrent(consumer, .{ io, &queue });
defer _ = consumer_task.cancel(io) catch {};

const item = try consumer_task.await(io);
```

Handle `error.ConcurrencyUnavailable`, especially in single-threaded builds or constrained runtimes. For an `Io.Group`, install `defer group.cancel(io)` before spawning members so partial spawn failures still join/cancel existing tasks. Pure computation has no automatic cancellation points: add `try io.checkCancel()` in long-running loops when prompt cancellation is part of the contract. Keep shared state alive until every task has joined.

## zio compatibility note

If a repo uses `github.com/lalinsky/zio`, treat it as a project-level async runtime choice. Inspect the pinned zio version and branch before editing. Do not mix raw `std.Io` assumptions into a zio codebase unless the repo already bridges them.

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
