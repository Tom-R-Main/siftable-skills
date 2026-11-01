# Testing, diagnostics and performance

Use the owner's test runner and configuration. Frameworks such as GoogleTest,
Catch2, doctest, Boost.Test and custom harnesses have different filters and test
registration. CTest can be only an outer dispatcher. Discover the intended test,
check target membership, run it and inspect actual result counts and skips.

For a bug, observe a focused failure and then success after the correction.
Check that a deliberately broken control fails for the intended assertion rather
than for compilation, missing dependencies or a timeout in unrelated setup.
Keep test oracles active in optimized builds; `assert` may disappear under
`NDEBUG`, except where the repository deliberately preserves assertions.

Choose evidence from the changed boundary:

- Ownership: constructor failure, move/copy, self-alias assignment, expired weak
  promotion, exact release counts, callbacks after close, and finalization error.
- Fallible state: inject at a specific operation, catch while the object is alive,
  inspect invariants and pending work, then destroy/reset and try fresh work.
- Parallel work: gates for overlapping access, wait/stop, late completion and
  teardown; compare one-worker/multi-worker results with the promised ordering.
- Required one-shot completion: success/error/cancellation and early-return paths,
  exactly-once delivery, and local cleanup after a callback can destroy its context.
- Parsers/codecs: boundary and split-input cases, malformed lengths, bounded
  allocation and recovery; independent byte goldens, noncanonical encodings and
  intended byte consumption. Round trips alone can miss an overly permissive
  decoder or paired codec drift. Fuzz the real entry point with a useful oracle.
- API/ABI: a consumer compiled/linked with supported flags and a real host call.
- Platform/backend: actual supported backend or a clearly scoped compile-only lane.

## Diagnostics under the real flags

Use the pinned formatter's check/dry-run mode, configured clang-tidy checks and
compilation database, and compiler warnings matching CI. Do not impose an unrelated
`-Werror`, enable every tidy category, or mass-apply fixes for a narrow defect.
Static analyzer findings need a reachable ownership/control-flow explanation.
Dependency or tool installation is a separate scoped action.

Where supported by the selected compiler and target:

- ASan detects exercised invalid memory accesses and certain lifetime failures;
  UBSan detects configured classes of undefined behavior. Instrument and link
  relevant components through the compiler driver. A recovered diagnostic can
  leave exit status zero; inspect reports or use the project's fail-on-error mode.
- TSan is a separate configuration for exercised data races. Do not combine it
  with ASan; account for uninstrumented libraries and supported platforms.
- MemorySanitizer needs suitable instrumented dependencies to make uninitialized
  data reports useful. Leak detection and Valgrind have platform/runtime limits;
  a lane unavailable on this host remains unqualified.

None proves all bounds, lifetimes, logical races, data-format validity or resource
budgets. Retain explicit invariant and progress tests. Review suppressions and
custom allocator visibility rather than turning a report off to make it pass.

Fuzz runs need an explicit target, seed/corpus, time/resource limit and failure
handling. Preserve minimized regressions in the normal test lane. Distinguish
test definitions read, corpus replay and new fuzz exploration. Consensus/format
code can need differential or independent implementation checks in addition to
generic memory instrumentation; preserve the project's existing harnesses.

## Measurements

Start with algorithmic work, layout, allocation, copying, I/O shape, contention
and dispatch overhead. Collect evidence before changing representation or adding
SIMD, custom allocators or lock-free structures. A view or move can reduce one
copy while retaining a larger allocation or disabling elision elsewhere.

Benchmark comparable optimized artifacts: same compiler/library/flags, target,
backend, workload, warmup, sample count and machine conditions. Preserve observable
results so dead-code elimination does not erase the work. Report variance and
latency/throughput/memory tradeoffs, plus correctness evidence from an appropriate
diagnostic build. Sanitizer timings and debug timings do not establish release
performance; one tiny microbenchmark does not establish end-to-end benefit.

Report exact commands/configuration, what actually ran, and unavailable lanes.
A standalone source-component test can be valuable, but does not replace full
repository build, application integration, or supported compiler/platform CI.
