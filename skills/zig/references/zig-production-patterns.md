# Production Zig patterns: Ghostty and TigerBeetle

Use when choosing architecture, allocation strategy, platform boundaries, or tests for substantial Zig work. These are source-backed examples and conditional design choices, not universal style rules.

## Source versions and scope

Source provenance recorded on 2026-10-09 (optional checkouts; not bundled):

| Checkout | Commit | Compiler contract |
| --- | --- | --- |
| `ghostty` | `246f702876b924a1cb7cade1e99274d1470302fc` | `build.zig.zon` requests 0.16.0; `src/build/zig.zig:requireZig` requires matching major/minor and at least the required patch |
| `tigerbeetle` | `c95d7a53a3d044741409b03b2f334a8ed033fa3c` | `build.zig` checks exact 0.16.0 major/minor/patch |

Both therefore reject 0.17 under their current contracts. Borrow engineering patterns; translate APIs against the selected compiler. TigerBeetle's C header test still uses `@cImport`, old reflection helpers, and its build uses `b.args`; these are migration inputs, not 0.17 recipes. Repository guidance applies when working in that repository, not globally to unrelated projects.

The map below covers representative implementation and test seams across major domains. It is not a claim to have audited every feature or run either test suite. A workflow definition establishes available/configured gates, not a current passing run.

## Domain map

Paths below are relative to the checkout named in the column. Read the implementations and nearby tests before adapting a pattern.

| Domain | Ghostty source | TigerBeetle source | Decision it informs |
| --- | --- | --- | --- |
| Core and platform boundary | `src/apprt.zig`, `src/apprt/runtime.zig` | `src/io.zig`, `src/storage.zig` | Keep domain logic reusable; isolate lifecycle and OS effects |
| Compile-time interfaces | `src/renderer/generic.zig` with Metal/OpenGL implementations | `src/vsr/replica.zig:ReplicaType`, `src/testing/cluster.zig:ClusterType` | Specialize at real backend seams, with a discoverable contract |
| Ownership and allocation | `src/terminal/Page.zig`, `src/datastruct/limited_allocator.zig` | `src/static_allocator.zig`, replica init/deinit | Choose by lifetime, latency, and capacity; distinguish request limits from total budgets |
| Parsing and streaming | `src/terminal/Parser.zig`, `stream.zig`, `kitty/graphics_command.zig` | `src/vsr/message_header.zig`, `src/repl/parser.zig` | Separate validation from internal invariants; retain partial-input state explicitly |
| Domain behavior | `src/terminal/Screen.zig` and stream regression tests | `src/state_machine_tests.zig`, `state_machine_fuzz.zig` | Verify feature semantics beyond byte-level memory safety |
| Fonts, Unicode, caches | `src/font/SharedGrid.zig`, `shaper/Cache.zig`, `glyf_rasterize_png_test.zig` | `src/lsm/cache_map.zig`, `set_associative_cache.zig` | Cache keys must cover dependencies; shared state needs an invalidation/replacement lifetime |
| Rendering and scheduling | `src/renderer/State.zig`, `Thread.zig`, `src/termio/Thread.zig` | `src/stdx/time.zig`, `src/vsr/replica.zig` | Treat bounded work, fairness, and time as part of correctness |
| Data layout | `src/terminal/Page.zig`, `size.zig`, `bitmap_allocator.zig` | `src/vsr/message_header.zig`, `src/stdx/stdx.zig` | Use compact indices/offsets where useful; verify alignment, padding, and representation |
| Persistence and restoration | `src/terminal/snapshot/`, `compress/` | `src/vsr/journal.zig`, `superblock.zig`, `src/testing/storage.zig` | Test truncation, corruption, ordering, recovery, and format compatibility |
| FFI and clients | `src/terminal/c/`, `include/ghostty/vt/`, `src/lib_vt.zig` | `src/clients/c/tb_client_header_test.zig`, language-client tests | Trace headers, exports, lifetime rules, and actual host callers together |
| Configuration and tooling | `src/config/Config.zig`, `src/build/`, module-specific build steps | `src/config.zig`, `src/unit_tests.zig`, `src/scripts/` | Control import breadth and test discovery; generated artifacts need consistency checks |
| SIMD and portability | `src/simd/main.zig`, `.github/workflows/test.yml:test-simd` | `src/io/{linux,darwin,windows}.zig`, `src/io/test.zig` | Exercise alternate implementations and real OS behavior separately |
| Memory diagnostics | `build.zig:test-valgrind`, `src/global.zig`, allocator-failure tests | static-allocation lifecycle checks and safe-mode assertions | Match tools to visible allocations and failure modes; see `zig-valgrind.md` |
| Fuzzing and replay | `test/fuzz-libghostty/`, checked-in regression inputs | `src/fuzz_tests.zig`, `vopr.zig`, `testing/packet_simulator.zig` | Retain seeds/bytes and verify the harness reaches the intended code |
| Integration and upgrades | `test/esctest/`, `test/windows/`, packaging checks in CI | `src/vortex.zig`, `src/build_multiversion.zig`, versioned state-machine tests | Simulation, conformance, native clients, and shipped artifacts prove different things |
| Benchmarks | `src/benchmark/AGENTS.md`, `src/terminal/compress/AGENTS.md` | benchmark files, fixed workload in `src/vopr.zig` | Use identical representative inputs; distinguish throughput, latency, ratio, and footprint |

## Architecture: portable core with deliberate effect boundaries

Ghostty selects application runtimes at compile time and shares terminal/font/rendering logic across native hosts. Its generic renderer gives Metal and OpenGL a documented graphics interface. TigerBeetle parameterizes replicas over state machine, storage, message bus, and AOF; its test cluster supplies controllable implementations to the same code.

Use this pattern when multiple platforms or deterministic tests genuinely need the same behavior. Document the required interface next to the implementation and instantiate meaningful variants in tests. Avoid making every object generic or putting domain logic into mocks. Choose runtime interfaces when substitution happens after compilation.

Respect an established I/O runtime. Ghostty combines `std.Io`, libxev event loops, and a deliberately limited `TinyIo`; TigerBeetle has OS-specific callback I/O. Replacing these with a default `std.Io.Threaded` instance can alter footprint, cancellation, concurrency, and ordering. Inspect the contract before attempting a migration.

## Allocation: enforce the policy where it matters

TigerBeetle's replica allocates during initialization, then transitions `StaticAllocator` to a state that rejects further allocation/resize/remap/free until teardown. This makes a startup-only allocation policy executable, instead of relying on review. It suits a bounded, latency-sensitive replica; test infrastructure and tooling still use ordinary dynamic allocators.

Ghostty dynamically manages terminal pages, caches, fonts, and surfaces. Its `LimitedAllocator` limits each individual request, not aggregate memory use. A small per-request bound does not bound a large number of allocations. Resource limits also need to cover retained bytes, decoded sizes, queue depth, and fan-out when those affect the workload.

For each subsystem, decide who owns its memory, which operations can allocate, what happens at capacity, and how failure leaves state valid. Use pools/arenas/indices only where their lifetime and invalidation rules help the workload. Keep safety checks and allocation diagnostics in the appropriate build modes.

## Failure and invariants: state rollback is observable behavior

Ghostty's `Screen` hyperlink test injects allocation failure and checks that a wrapped ID counter returns to its original value. A leak-free cleanup can still leave counters, pins, collections, or published state inconsistent.

For fallible mutations, test failure after meaningful partial progress. Check both resource release and the public state contract: unchanged state, documented partial state, or explicit invalidation. Cover zero, exact capacity, capacity+1, rollover, malformed input, and the next successful operation after failure where relevant.

Use assertions for programmer invariants and compile-time layout/constant relationships. External malformed data and ordinary OS failures need deliberate error handling. Borrow TigerStyle's attention to bounds and paired invariants without imposing its assertion count, function length, no-recursion policy, or fixed-width-only rule on every project.

## Streaming, snapshots, and codecs: compare independent paths

Ghostty compares scalar versus bulk parsing, continuation replay, chunk-independent state, and idempotent continuation encoding. Chunk boundaries may fall inside UTF-8, escape sequences, or payloads; final screen state alone can miss duplicated side effects or lost pending state.

For stream changes, compare whole-input and split-input execution, including pending state and effects. When restoring snapshots, verify what is published before completion and the handling of truncated or invalid records. Do not infer cross-process durability from an in-memory round trip.

For codecs, use an independent walker/decoder or oracle plus round-trip identity, malformed/truncated inputs, exact output bounds, and representative data. A matching encoder and decoder can share a bug. Ghostty's compression guidance prioritizes real page-shaped data and decompression latency over a generic text benchmark; those priorities follow its scrollback workload, not every codec workload.

## Deterministic simulation: faults plus independent checks

TigerBeetle controls simulated time, storage latency/corruption, packet loss/replay/partitions, and replica lifecycle. It retains reproducible seeds and uses separate state, storage, grid, manifest, and journal checkers. VOPR separates correctness/crash failure from inability to converge and transitions to a liveness phase.

For a stateful service, make time, randomness, event ordering, and I/O injectable at a small seam. Record the seed, configuration, compiler, and revision. Verify both safe behavior during faults and recovery/progress after the declared fault conditions cease. Constrain injected faults to a stated model so expected impossibility is not mislabeled a product bug.

Keep real integration coverage: TigerBeetle also has OS I/O tests and a Linux-only Vortex driver exercising actual processes and client workloads. A deterministic simulator does not prove syscall behavior, dynamic-library loading, host callback lifetimes, or deployment compatibility.

## FFI: the contract extends beyond Zig structs

Ghostty's C API uses opaque long-lived handles, explicit sized structs where suitable, C-compatible tagged unions, and coordinated Zig declarations/exports/headers. Its allocation helpers define zero-length/null behavior and require the original allocator when freeing. TigerBeetle compares exported Zig types and enum values against translated C headers, including sizes and alignments.

Verify the whole boundary: symbol names, calling convention, layout, enum width, lengths, null/empty handling, ownership, sentinel handling, callback lifetime/thread, and teardown. Prefer a tiny C/host caller test when the changed behavior crosses FFI. For 0.17, migrate header translation through the selected `translate-c` dependency rather than copying TigerBeetle's 0.16 `@cImport` test verbatim.

## Testing and evidence: a green lane has a defined scope

Zig's lazy analysis makes import/instantiation coverage important. TigerBeetle's root unit-test import list has a self-checking generation mechanism; Ghostty separates application, VT, C API, schema, and platform gates. Confirm that the module and variants changed are actually included by the selected step/filter.

Choose gates from the changed contract:

| Changed surface | Useful evidence |
| --- | --- |
| Collection/ownership | Unit invariants, allocator failure, teardown, sanitizer/Memcheck when applicable |
| Parser/decoder | Split-input properties, malformed inputs, targeted fuzz regression/corpus |
| ABI or library packaging | Header/layout checks, actual host caller, static/shared linking and symbols |
| Stateful recovery | Deterministic fault replay plus independent safety/liveness checks |
| OS/GPU/input behavior | Native backend tests and an actual relevant UI/device flow |
| Optimization | Baseline and optimized correctness, fallback behavior, controlled benchmarks |

Test the harness itself. TigerBeetle has a canary fuzzer that deliberately exits with failure for selected seeds. Ghostty documents that sending corpus minimization inputs through the wrong AFL channel can measure just the C harness, not the Zig parser. Record which inputs/variants ran, skips, exit status, and what failures are allowed.

Ghostty's esctest lane reports conformance failures without failing CI, and its fuzz CI job builds the harness rather than conducting a sustained campaign. These are useful signals with different acceptance authority. Do not promote either to proof of passing conformance or fresh fuzz coverage.

## Measurement: isolate cost and preserve semantics

Generate benchmark data before timing; reuse exact files/seeds, flags, dimensions, compiler mode, and target across revisions. Avoid concurrent benchmarks on the same machine. Measure latency distribution and retained memory as well as throughput when they affect the user.

Ghostty tests SIMD on/off and benchmarks different pipeline stages. A fallback keeps semantics portable; it does not establish equal performance. SharedGrid documents replacing shared font state when configuration changes rather than mutating it underneath unrelated surfaces. Cache invalidation and fairness under sustained output can matter more than one fast kernel.

Keep tiny adapters for proven toolchain/backend exceptions and document their removal conditions. Ghostty's `src/lib/compat/README.md` explicitly treats compatibility code as temporary or subject to relocation. Neither an upstream workaround nor a historic benchmark justifies permanent global rules or an unmeasured speed claim.
