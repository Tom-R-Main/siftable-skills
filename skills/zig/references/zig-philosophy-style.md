# Zig philosophy and style

Use this when reviewing whether code feels like Zig rather than C-with-syntax or Rust-without-borrow-checking. These are review heuristics, not language rules; `source-grounding.md` distinguishes official semantics, adopted conventions, community input, and original synthesis.

## The Zig contract

Good Zig code is:

- **Robust**: edge cases, allocation failure, invalid input, and impossible states are handled deliberately.
- **Optimal**: the programmer writes the intended machine behavior directly; abstractions must justify themselves.
- **Reusable**: code works across allocators, targets, operating systems, and runtimes because dependencies are explicit.
- **Maintainable**: intent is precise and low-overhead to read.

The recurring question is: **where are the bytes?** Know who owns each allocation, which lifetime a slice borrows from, and which unit space an integer belongs to.

## Naming: make unit bugs visible

Consider the [TigerBeetle-style](https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md#off-by-one-errors) suffix convention for low-level code when it makes unit conversions and off-by-one risks easier to see:

| Suffix | Meaning | Valid comparisons |
|---|---|---|
| `_count` | number of typed items | `index < count` |
| `_index` | index of one typed item | `index + n <= count` |
| `_size` | number of bytes | `offset < size` |
| `_offset` | byte offset | `offset + n <= size` |

Prefer:

```zig
const word_size = source.len;
const word_count = word_size / @sizeOf(Word);
var source_index: usize = 0;
var target_index: usize = 0;
```

Avoid new uses of ambiguous `length` in low-level code. External APIs may use `len`; adapt at boundaries but keep internal naming explicit.

Use suffix qualification rather than prefix soup:

```zig
source
source_words
source_index

target
target_words
target_index
```

Parallel names help diffs and loops line up:

```zig
source_index += marker.literal_word_count;
target_index += marker.literal_word_count;
```

## Parameter passing

Zig parameters are passed by value semantically: a function receives an independent value that cannot be modified externally through that parameter. The compiler may avoid or transform the copy under the as-if rule, especially after inlining, but do not rely on that for large structs in hot paths.

For large arrays, structs, and aggregate state that crosses non-inlined calls, prefer `*const T`, `*T`, slices, or small handles when copying is not the point. Confirm with benchmarks or generated code when the difference matters.

## Assertions as executable invariants

Use assertions where a violation means programmer error or corrupted internal state:

```zig
std.debug.assert(source_index <= source_count);
std.debug.assert(node_offset % node_size == 0);
```

For user input, return errors with useful diagnostics instead of asserting.

## Explicit dependencies

Pass dependencies as parameters:

```zig
fn parse(allocator: std.mem.Allocator, source: []const u8) !Ast { ... }
fn copyFile(io: std.Io, allocator: std.mem.Allocator, from: []const u8, to: []const u8) !void { ... }
```

Avoid hidden global allocators, hidden thread pools, hidden filesystem roots, or hidden output streams in library code.

## Allocation follows lifetime

Choose allocation strategy from ownership and lifetime rather than convenience:

- use caller-owned buffers when storage is bounded and ownership can stay with the caller;
- use `FixedBufferAllocator` when a bounded working set is known and exhausting it can be handled;
- use an arena when a cohort of allocations genuinely dies together, such as one parse, request, page, or frame;
- use explicit allocation and destruction for values that are replaced or released independently;
- use testing and failing allocators to exercise leak and out-of-memory paths.

An arena can retain excessive memory without technically leaking. Avoid one arena for unrelated lifetimes, and remember that a nested arena returns memory to its parent allocator rather than necessarily to the operating system.

## Data layout before instruction tuning

For parsers and hot kernels, first evaluate contiguous storage, stable indices, compact handles, separated hot and cold fields, and bulk lifetime management. These representations can improve cache behavior, ownership, serialization, and cleanup together.

Treat data-oriented layouts as candidates, not laws. Prefer the representation that makes invariants simplest, then measure it with representative inputs before tuning individual instructions.

## Error handling

Use Zig's error unions to keep failure part of the type. Prefer local error sets when they communicate meaning; avoid turning recoverable failures into panics.

```zig
const ReadError = error{
    FileTooLarge,
    BinaryData,
    InvalidUtf8,
};
```

Use `errdefer` for partial construction:

```zig
const buffer = try allocator.alloc(u8, byte_count);
errdefer allocator.free(buffer);

const table = try allocator.create(Table);
errdefer allocator.destroy(table);
```

Treat `try` as propagation, not proof that an error has been handled. Libraries should return precise failures; applications should choose recovery, diagnostics, degradation, or termination at a deliberate semantic boundary such as a command, request, document, page, or protocol operation.

Use `catch unreachable` only when failure would violate a proven invariant. Do not use it merely to suppress an inconvenient error path.

## Comptime style

Use comptime to remove runtime behavior or prove constraints, not to write impenetrable magic.

Good uses:

- generic data structures;
- format/parser specialization;
- field reflection with compile-time errors;
- ABI/layout assertions.

Prefer a plain runtime function when comptime does not simplify the result.

Keep capability-based `anytype` interfaces small and conventional. A `writer: anytype` parameter may be clear because the required surface is narrow; a large domain object accepted as `anytype` can hide its contract from readers and tools.

Static specialization can remove indirection but may increase compile time and code size. Runtime interfaces make substitution explicit and can limit specialization at the cost of indirection. Choose based on when substitution occurs, and measure generated behavior rather than assuming devirtualization or specialization benefits.

## Pre-1.0 containment

Pin the compiler and contain volatile standard-library surfaces behind small local adapters. Avoid exposing version-specific `std.Io`, build-system, or container details through otherwise stable library APIs when a narrower project-owned boundary will do.

Prefer the pinned version's documentation and nearby working code. Treat master examples as migration input, not as automatically applicable guidance.

## Safety modes

Debug and ReleaseSafe are allies. ReleaseFast is for measured hot paths where safety tradeoffs are intentional. Keep Debug/ReleaseSafe passing even when production artifacts use ReleaseFast for benchmarks.
