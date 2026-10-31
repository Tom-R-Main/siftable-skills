# Tests, execution evidence, and performance

Derive checks from the changed contract, its configured consumers, and CI. Keep
existing JUnit/kotlin.test/Kotest/MockK/Turbine conventions; do not introduce a
test framework simply because the skill mentions it.

## Select the smallest useful lane

| Change | Evidence to seek |
| --- | --- |
| Pure logic or parser | Focused regression, boundary input, relevant property cases |
| Coroutine/Flow | Cancellation, failure, collection/restart and required delivery semantics |
| JVM library API | API/ABI task and representative Kotlin/Java consumers |
| Serialization | Exact wire fixtures including absence, null, defaults, and evolution |
| Shared source set | Tests/compilation in affected configured target consumers |
| Android UI/platform | Host tests plus relevant device, lifecycle or UI behavior |
| Backend route/transaction | Real framework wiring and the relevant persistence boundary |
| Compiler/stdlib | Area-specific runner, fixture/diagnostic/box expectations and regeneration rules |
| Native handle or callback adapter | Real boundary lane for shutdown/races, plus repeat completion/cancellation and resource-release checks |
| Offline sync or schema change | Checkpoint/retry behavior and data-preserving migration of supported old stores |
| Derived search index or relationship refresh | Repeat population, content edits/removals, true row identity, and removed memberships using the real storage semantics |

Check reports for selected cases and actual test counts. `BUILD SUCCESSFUL` can
include zero selected tests, `NO-SOURCE`, cache reuse, host-disabled targets, or
tasks that compile but never run the affected path. Use the documented mechanism
to force a fresh run when freshness is the assertion being tested; do not wipe
caches as a default.

For artifact behavior, run the built CLI with a representative input, call a
service route, exercise a library from a consumer, or drive the changed UI flow.
Choose a bounded test that can run in the authorized environment. Describe
compile-only, framework-test, and deployed/live evidence distinctly.

Include repository-specific Detekt rules, architecture/import tests, and
screenshot verification when the changed contract triggers them. Screenshot
recording replaces expectations; it is not a verification fix. Follow the
repository's baseline ownership and CI procedure instead of regenerating images
to make a failed comparison pass.

Reuse the smallest existing harness that exercises the boundary: presenter fakes
and Turbine for state transitions, a database migration harness for old stores,
or a game engine's headless/render-thread runner for engine calls. Preserve
required working directories, assets, seeds, and JVM agents. Pure logic should
not acquire an emulator or render loop just because another test uses one.

In JVM weak-listener tests, keep the receiver observably reachable through the
last delivery assertion; lexical local-variable scope alone does not establish
GC liveness. Use a retained test owner or an appropriate
`Reference.reachabilityFence(owner)` after the assertion where supported. Keep
explicit unregistration tests separate from nondeterministic GC cleanup tests.

## Coroutine tests

Use the project's compatible `kotlinx-coroutines-test`. With `runTest`, share
one `TestCoroutineScheduler` across injected dispatchers. Delays on a real
Default/IO dispatcher are not skipped by virtual time.

`StandardTestDispatcher` queues newly launched work. Establish collectors before
emitting when subscription matters, using `runCurrent()` or a deliberate eager
test dispatcher. Control virtual time around the actual boundary; in supported
versions `advanceTimeBy` does not run work scheduled exactly at the new endpoint
until `runCurrent()`. Avoid arbitrary wall-clock sleeps.

Infinite collectors need cancellation or `backgroundScope`; waiting for their
normal completion makes a test hang. Reset a replaced Main dispatcher and close
owned executors. Return `runTest`'s result directly in common/JS tests where the
test host requires it. Check versioned APIs for opt-ins and scheduler semantics.

Assert the contract, not an impossible emission history. A StateFlow test should
not require every intermediate write unless the design provides that guarantee.
For `WhileSubscribed`, run a collector when testing producer start/stop. Include
subscriber gaps, multiple consumers, cancellation, retries, and cleanup only as
relevant to the changed behavior.

Virtual-time tests exercise scheduling deterministically; a single-threaded test
does not demonstrate freedom from data races. Add a bounded real multithreaded
or repository stress lane when changing shared-state synchronization.

## Performance

First identify whether the cost is runtime, allocation/GC, startup, UI frames,
build configuration, incremental compilation, or generated code size. Capture a
representative baseline with the same inputs, artifact mode, toolchain, target,
and environment before changing the implementation.

Use the repository's harness. For JVM microbenchmarks, an existing JMH setup
provides warmup, forks, and dead-code-elimination controls. For Android, use the
appropriate Microbenchmark/Macrobenchmark and profileable/release configuration;
debug timings and emulator rankings do not justify device performance claims.
For Native or JS/Wasm use the target's actual optimizer/runtime. Do not benchmark
real-time latency with a virtual-time coroutine scheduler.

Measure before replacing loops with Sequences/Flow, adding `inline`, caching,
parallelizing collection operators, or introducing value classes. Allocation,
boxing, retained state, contention, and added work can outweigh syntactic gains.
Report sample counts, variance, workload, warm/cold state, and correctness gates;
keep conclusions no broader than the measured environment.

## Sources

- [kotlinx-coroutines-test scheduler and runTest API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/)
- [advanceTimeBy endpoint behavior](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/advance-time-by.html)
- [Ktor application tests](https://ktor.io/docs/server-testing.html)
- [JVM reachability and reachabilityFence](https://docs.oracle.com/en/java/javase/11/docs/api/java.base/java/lang/ref/Reference.html#reachabilityFence(java.lang.Object))
- [Community KMP test coverage and local compiler test guidance](sources.md)
