# Candidate guidance

These are starting hypotheses, not rankings, exhaustive catalogs, or exclusive roles. Add an omitted language/framework when target requirements or existing assets justify it. Explicit user/platform constraints take precedence.

| Candidate | Reason to investigate | What could reverse the choice |
|---|---|---|
| Rust | New native systems with significant ownership, concurrency, or hostile-input risk; enforced ownership and data-race constraints | Required SDK/target gaps, costly representation or synchronization choices, difficult foreign ownership, or a stronger existing implementation |
| Zig | Whole engines or applications organized around explicit allocation, bounded lifetimes, layout, and C integration | Lifetime verification burden, missing libraries/platform support, toolchain/API change cost; pin and consult matching docs |
| C++ | Strong engines, numerical/media/graphics libraries, native frameworks, GPU/vendor tooling, or pervasive C++ object integration | A smaller safe-language design can meet the same contracts without an expensive interop boundary; manual lifetime risks lack adequate checks |
| C | Required source distribution, constrained/certified toolchains, established C implementation, small platform layers | Cross-language calling alone: a C ABI does not require a C implementation; system calls and bytes do not uniquely select C |
| Go | Services, controllers, concurrent coordination, or ports whose graph/lifetime structures fit its runtime | Measured allocation/GC CPU, retained heap, startup/artifact size, or tail latency under the actual cap erases the benefit |
| TypeScript/JavaScript | Browser or JS-hosted APIs, shared host objects, useful SDKs and substantial established behavior | CPU/memory cost or host limitations dominate a complete native alternative; type annotations do not validate external values |
| Python | Scientific/ML ecosystems and orchestration of effective native/GPU engines | Python execution/dispatch or deployment costs dominate; changing the controller does not inherently speed kernels |
| Swift/Kotlin and native platform frameworks | Platform APIs, lifecycle integration, accessibility, extension points, and native UI | Measured cross-platform reuse or another supported host provides a better complete result; shared core is a separate choice |
| SQL/query engine or GPU kernels | Push computation toward resident data or specialized execution | Transfers, synchronization, launch overhead, precision, or operational constraints outweigh saved work |
| Wasm | Required portability, browser reuse, or restricted guests | Host compatibility, imports, startup, conversions, or resource controls fail requirements; it is an execution target, not a UI framework |

For new native work with complex ownership, Rust is a useful first candidate because of its mechanically checked invariants. This is a defeasible policy, not comparative performance evidence. Zig and C++ need not remain small accelerators. Memory-safe choices still require tests for logical races, deadlocks, leaks, resource exhaustion, and semantics, plus scrutiny of unsafe/foreign dependencies.

## Memory shape before runtime labels

Identify live-set size, allocation rate, pointer density, sharing/cycles, batch lifetimes, and peak overlap at the expected concurrency. Compare managed heaps, arenas/regions, value ownership, and reusable buffers as applicable. Arenas suit shared lifetimes but can retain dead data until reset; reference counting has overhead and cycle concerns. Test managed-runtime headroom under a realistic whole-process cap. Native allocators can also fragment, retain memory, exhaust resources, and suffer nonlinear pressure effects. Do not bake in a universal GC multiplier or assume that no GC means real-time execution.

## Framework choice is its own decision

For content or sparse interaction, investigate generated/server-rendered HTML and limited interactive islands. For stateful applications, compare frameworks on required components, accessible behavior, rendering/update paths, ecosystem integration, and actual screens. React may earn its place through those assets; CRUD or dashboards alone neither require nor rule it out.

Measure transferred/executed client code, hydration, interaction latency, and main-thread work where relevant. Keep high-frequency engine state out of general UI reconciliation when it helps. A Worker can run JavaScript or Wasm; Wasm alone does not move work off the main thread. Browser/platform codecs or GPU facilities may outperform newly written native CPU loops despite a TypeScript controller.

For backend frameworks, compare middleware behavior, streaming/backpressure, cancellation, database access, instrumentation, deployment support, and failure recovery. HTTP hello-world rankings do not establish the best production framework. Choose database, persistence, and messaging technology from query/update shape, consistency/durability, data movement, and operational constraints rather than a language's default ecosystem.
