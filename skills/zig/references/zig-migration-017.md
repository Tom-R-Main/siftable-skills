# Migrating Zig 0.16 to 0.17

Use for an explicitly requested migration or to explain a 0.17 compiler failure. New examples target **0.17.0**, not master. Preserve older pins for ordinary maintenance.

## Authoritative sources

- [0.17 release notes](https://ziglang.org/download/0.17.0/release-notes.html): breaking changes, upgrade examples, target support, known regressions.
- [0.17 language reference](https://ziglang.org/documentation/0.17.0/) and [standard library](https://ziglang.org/documentation/0.17.0/std/).
- Optional reference checkout: `ZIG_REFERENCE_DIR` points to a source checkout selected by the user. These notes were checked on 2026-10-09 against release tag `0.17.0`, commit `7647adab80`. Use `git show 0.17.0:<path>`; HEAD may already be 0.18 development code.

Third-party guides verified against master can mix release and development information. Resolve discrepancies against the selected release tag and official notes, especially C translation. Source inspection establishes signatures and intended semantics; compiling with 0.16 does not validate 0.17 examples.

## Migration sequence

1. Select and verify a 0.17 compiler before changing the pin. Inspect package and ZLS compatibility; a successful compiler upgrade does not establish dependency compatibility.
2. Audit the semantic traps below before mechanically repairing compile errors.
3. Update language/reflection, allocator/container, and build surfaces relevant to the project. Inspect each dependency's pin separately.
4. Run the selected compiler's formatter on changed files and review its rewrites; it migrates some builtins automatically. Do not mass-format unrelated source.
5. Test in debug or safe, including the affected behavior, then build required targets and benchmark only when performance is part of the request.

## Changes the compiler may not catch

- **`std.mem.containsAtLeastScalar(T, list, element, minimum)`** replaces the old `(T, list, minimum, element)`. Integer operands may type-check in either order. Audit every call and add a test with different element/minimum values. `containsAtLeastScalar2` is gone.
- **`@bitCast` uses logical bits independently of target endianness.** Array/vector elements concatenate in element order, each starting with its least-significant bit. Audit serialization, SIMD, packed data, and endian-sensitive casts; test against known bit patterns and relevant targets. Integer-to-integer and integer-to-bitpack casts retain their prior behavior. Extern structs/unions are no longer accepted: memory reinterpretation needs a valid pointer cast or extern union, with alignment, bounds, and lifetime checked. Enum destinations now check tag validity in safety modes.
- **`@hasDecl` only sees public declarations**, even inside the same file. Audit capability detection and comptime branches using private names; compilation may succeed while selecting a different branch.
- **Float equality is no longer short-circuited for identical slices** in `std.mem.eql` / `findDiff` when equality is non-reflexive. A float slice containing NaN is unequal to itself; inspect tests or callers relying on the old shortcut.
- **Configuration is cached.** `build.zig` need not execute on every invocation. File/directory observations that affect the graph must be tracked or poison the configure cache. A stale graph can survive an apparently successful build.

A focused semantic regression test for the argument-order change:

```zig
const std = @import("std");

test "minimum differs from the sought element" {
    const values = [_]u8{ 6, 6, 1, 6 };
    try std.testing.expect(std.mem.containsAtLeastScalar(u8, &values, 6, 3));
    try std.testing.expect(!std.mem.containsAtLeastScalar(u8, &values, 1, 2));
}
```

## Language and reflection

| Earlier pattern | Zig 0.17 guidance |
| --- | --- |
| `[1]u8{0} ** n` | `const bytes: [n]u8 = @splat(0);` for scalar repetition; repeated multi-element sequences need an explicit construction |
| `void{}` | `{}` |
| `errdefer \|err\| ...` | Keep ordinary `errdefer` for cleanup; catch errors at the intended diagnostic boundary |
| `@intFromEnum(value)` | `@backingInt(value)`; old builtin is deprecated |
| `@enumFromInt(integer)` | `@fromBackingInt(integer)`; argument must have the exact backing type, often requiring `@intCast` |
| `std.builtin` types | `std.lang`; the old namespace is deprecated |
| `std.lang.OptimizeMode`, `.Debug` / `.ReleaseSafe` / `.ReleaseFast` / `.ReleaseSmall` | `std.lang.Optimize`, `.debug` / `.safe` / `.fast` / `.small` |
| `builtin.mode` | `builtin.optimize`; old mode constant is deprecated |
| `builtin.cpu`, `.os`, `.abi`, `.object_format` | `builtin.target.cpu`, `.os`, `.abi`, `.ofmt` |
| `std.meta.Int`, `std.meta.Tuple` | `@Int`, `@Tuple` |
| `i0` | Evaluate whether `u0` preserves the intended model |
| Global linkage `.internal` / `.link_once` | Omit the export for internal symbols; evaluate `.weak` for link-once uses |

Deprecated mode declarations do not preserve enum-literal comparisons such as `optimize == .ReleaseFast`. Use `.fast`. Prefer `builtin.optimize.runtimeSafety()` for the caller module's safety mode. CLI spellings include `-O safe` and `-Doptimize=safe`; older spellings remain compatibility aliases.

`@backingInt` also accepts explicitly integer-backed packed structs/unions and tagged unions. `@fromBackingInt` constructs enums or explicitly backed bitpacks, not tagged unions. Check external integer inputs before constructing exhaustive enum values. `@divCeil` replaces catch-based `std.math.divCeil` usage; denominator and overflow preconditions remain the caller's responsibility.

Reflection now uses parallel arrays rather than field-record arrays:

```zig
const info = @typeInfo(T).@"struct";
inline for (info.field_names, info.field_types, info.field_attrs) |name, FieldType, attrs| {
    std.debug.print("{s}: {s}\n", .{ name, @typeName(FieldType) });
    _ = attrs.defaultValue(FieldType);
}
```

This is a contextual fragment, not a standalone program. Structs/unions expose `field_names`, `field_types`, `field_attrs`, and `decl_names`; enums expose `field_names`, `field_values`, `mode`, and `decl_names`. Functions expose `param_types`; error sets expose optional `error_names`; pointer qualifiers/alignment live in `attrs`. Inspect the matching `lib/std/lang.zig` type before reconstructing types or migrating serializers. Do not mechanically reuse old `.fields`, `.decls`, or `.params` layouts. Deprecated `std.meta.fields`/`fieldInfo`/`fieldNames`/`fieldTypes` helpers do not substitute for the new model.

When replacing captured errdefer, preserve which error is returned and when cleanup happens. A wrapper `inner(...) catch |err| { log(err); return err; }` covers all inner failures after its cleanup. Catching just one operation can miss later failures; a failing diagnostic write can replace the original error unless handled deliberately.

## Allocators, formatting, and containers

Use the concrete patterns in [zig-current-apis.md](zig-current-apis.md).

| Earlier API | Zig 0.17 |
| --- | --- |
| `std.heap.DebugAllocator(.{})` | `std.heap.SafeAllocator.init(backing_allocator, options)`; deinit returns a leak count, not `.ok` / `.leak` |
| `StackFallbackAllocator`, `std.heap.stackFallback` | `BufferFirstAllocator.init(buffer, fallback_allocator)`, then `.allocator()` |
| `std.fmt.allocPrint(allocator, fmt, args)` | `allocator.print(fmt, args)` |
| `std.fmt.bufPrint(buffer, fmt, args)` | `std.mem.print(buffer, fmt, args)` |
| `std.fmt.bufPrintZ`, `allocator.dupeZ` | `std.mem.printSentinel(buffer, fmt, args, 0)`, `allocator.dupeSentinel(T, source, 0)` |
| `list.getLastOrNull()` / `list.getLast()` | `list.last()` / `list.last().?`; `lastPtr()` returns an optional element pointer |
| Bit-set `initEmpty()` / `initFull()` | `.empty` / `.full` with an explicit type |
| `std.bit_set.StaticBitSet`, `DynamicBitSetUnmanaged` | `std.bit_set.Static`, `Dynamic`; other variants use `Integer` / `Array` |
| `DoublyLinkedList.pop()` | `popLast()` |
| `std.heap.MemoryPoolAligned` | `std.heap.memory_pool.Aligned` |
| `std.gpu` | `std.spirv` |
| `std.ascii.indexOfIgnoreCase*` | Corresponding `findIgnoreCase*` APIs |
| `std.mem.readPackedIntNative` / `writePackedIntNative` | `readPackedInt` / `writePackedInt` with `.native`; inspect foreign-endian callers explicitly |

Review `ArrayList` pointer lifetimes across growth and mutation. `lockPointers` / `unlockPointers` help diagnose illegal invalidation; they do not make pointers survive reallocations. `ArrayHashMap.setKey` drops its allocator argument. Bit-set managed variants are deprecated.

For ZON parsing, `fromSlice(T, .{ .gpa = scratch, .arena = arena, .source = sentinel_source, .diagnostics = &diag })` allocates results and diagnostics in the supplied arena. The source is `[:0]const u8`; `diag` is initialized by the parser. Keep the arena alive for both results and diagnostics, then deinitialize it as a cohort; remove obsolete per-result/per-diagnostic free calls. The old nonallocating `fromSlice` is now `fromSliceNoAlloc`; inspect `Options` because even that path needs diagnostic/scratch allocation. `updateFromSlice` supports layered configuration.

`Uri.getHost` moves to `std.Io.net.HostName.fromUri(uri, buffer)` with validation and a different error set; `getHostAlloc` is removed. Revisit error handling rather than renaming blindly.

## Build configuration and package management

The configurer produces a serialized graph; the maker executes it. Custom `Step.makeFn` callbacks and replacement build runners no longer fit that model. Express custom work as tools run through `b.addRunArtifact` / system-command steps, using `LazyPath` inputs and declared outputs. Tooling should use the Build Server Protocol or `zig build --print-configuration` rather than a forked build runner.

- Replace `if (b.args) |args| run.addArgs(args);` with `run.addPassthruArgs()`. Arguments after `--` are not observable during configuration.
- Use `b.findProgramLazy(.{ .names = &.{ "python3", "python" } })` when only a make step needs the executable. It returns a `LazyPath`; supply it as the command's first path argument to a Run step. Immediate `b.findProgram(.{ .names = ... })` returns `?[]const u8` and poisons the configuration cache.
- Track graph-affecting observations with `b.dependOnFileContents`, `dependOnFileMetadata`, `dependOnDirectoryContents`, or `dependOnDirectoryMetadata`. Otherwise use `b.graph.poisonCache()` deliberately. Make-time effects alone do not require poisoning; avoid `--cache-poison=ignored` as a correctness fix.
- `b.build_root` becomes `b.root`; `LazyPath.basename` is removed because the value may only be available at make time. Display paths through `{f}` rather than `getDisplayName`.
- Fmt options accept `LazyPath` lists: `b.pathList(&.{ "src", "build.zig" })`. Config-header `include_guard_override` becomes `include_guard`.
- Run path/artifact argument APIs have `*Arg2` variants with structured options; inspect the pinned signatures before migrating prefixes/decorations. Existing plain helpers may still exist as deprecated wrappers.
- Options distinguish `addOptionPath` (file), `addOptionPathDirectory`, and `addOptionPathUntracked`.
- `b.dependency` supports lazy dependencies. `try b.dependencyLazy(...)` can return `error.LazyDependencyNeeded`, which the build system handles by fetching and reconfiguring when propagated from the build function.
- `.path` dependencies cannot escape the parent package root. Global/local package caches and `--pkg-path` / `ZIG_LOCAL_PKG_DIR` are covered in [zig-current-apis.md](zig-current-apis.md).

## C translation

`@cImport`, `@cInclude`, `@cDefine`, and `@cUndef` are removed. **`b.addTranslateC` still exists but is deprecated**; prefer an explicit pinned dependency on the official [translate-c package](https://codeberg.org/ziglang/translate-c). Fetch only when dependency changes and network access are authorized:

```sh
zig fetch --save git+https://codeberg.org/ziglang/translate-c
```

The release-notes pattern is:

```zig
const Translator = @import("translate_c").Translator;
// Within build(), using the project's selected target, optimize, and exe:
const translate_c = b.dependency("translate_c", .{});
const translator: Translator = .init(translate_c, .{
    .c_source_file = b.path("src/c.h"),
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("c", translator.mod);
```

Use `@import("c")` in Zig source. Inspect the pinned translator's options for macro definitions, include paths, system libraries, and translation policy; move those settings deliberately. The translator has an independent release cadence, so pin its resolved hash and verify it with the selected Zig compiler.
