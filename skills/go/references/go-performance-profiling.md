# Go performance, benchmarks, and profiling

Performance behavior depends on the exact compiler, target, build flags,
workload, runtime configuration, and machine.

## Contents

- Measurement contract and benchmark design
- Comparing results with `benchstat`
- CPU, memory, goroutine, block, mutex, and trace evidence
- Escape analysis, allocations, and GC
- Profile-guided optimization
- Review checklist

## Measurement contract

Before optimizing, define:

- the user-visible or system metric that matters;
- representative inputs, concurrency, data size, and warm/cold state;
- correctness invariants;
- environment and noise controls;
- acceptable tradeoffs in memory, latency tails, throughput, complexity, and
  compatibility.

Do not infer a bottleneck from code appearance. Use profiles, traces, production
metrics, or a focused benchmark that reproduces the relevant work.

## Benchmarks

Use `testing.B` with setup outside the timed region and cleanup after it.

On Go 1.24+, `B.Loop` manages the timer around the loop and keeps arguments and
results within the loop alive against dead-code elimination:

```go
func BenchmarkParse(b *testing.B) {
	data := loadRepresentativeInput(b)
	for b.Loop() {
		parse(data)
	}
}
```

Preserve `b.N` benchmarks when supporting older Go or avoiding unrelated
rewrites. For them, place setup before `ResetTimer`, use `StopTimer` around
per-iteration fixture work only when necessary, and prevent elimination without
distorting the operation.

Benchmark practices:

- Use sub-benchmarks for meaningful input dimensions.
- Report allocations with `-benchmem` or `ReportAllocs`.
- Use `SetBytes` or `ReportMetric` for domain throughput where useful.
- Do not mix correctness assertions into the hot loop when they dominate timing;
  validate setup/results outside or in separate tests.
- Avoid global sinks that introduce contention unless required; understand how
  the selected compiler treats `B.Loop` and result liveness.
- Benchmark concurrent code with realistic contention and `RunParallel` only
  when it models the production access pattern.

## Comparing results

Run multiple samples under comparable conditions and use `benchstat`:

```sh
go test -run '^$' -bench '^BenchmarkName$' -benchmem -count=10 ./path > before.txt
go test -run '^$' -bench '^BenchmarkName$' -benchmem -count=10 ./path > after.txt
benchstat before.txt after.txt
```

Use the same Go version, target, CPU settings, build tags, environment, and
background load. Interleave runs when drift matters. Report statistical
uncertainty and all relevant regressions, not only the favorable row.

Microbenchmark improvements are not automatically end-to-end improvements.
Validate the changed binary or service under a representative workload.

## Profiles and trace

Choose evidence by question:

- CPU profile: where sampled CPU time is spent.
- Heap `inuse_space`: retained live memory.
- Alloc profile: allocation volume/churn.
- Block profile: time blocked on synchronization operations it samples.
- Mutex profile: contended mutex delay.
- Goroutine profile: current stack/lifecycle state.
- Execution trace: scheduling, blocking, GC, syscalls, network, and task regions.

Profiles are sampled/aggregated views. A hot frame can be a caller, callee,
inlining artifact, or symptom of upstream work. Compare source and disassembly
only after confirming that instruction-level detail affects the metric.

Expose pprof endpoints only under the application's security and operational
policy. Profiles can contain paths, symbols, labels, request data, and resource
information.

## Escape analysis and allocations

Compiler messages from `-gcflags=-m` explain optimization and escape decisions,
but are not a performance score. Verify allocation counts and end-to-end effect.

Optimize in this order when evidence supports it:

1. unnecessary algorithmic work and I/O shape;
2. data representation and locality;
3. allocation count, lifetime, and retention;
4. contention and concurrency bounds;
5. serialization/copying;
6. instruction-level tuning.

Do not return pointers solely to "avoid copies"; that can force heap allocation
and increase GC retention. Do not pool cheap or long-lived objects reflexively.
`sync.Pool` is best for temporary reusable objects with high allocation churn
and clear reset/security semantics.

## GC and runtime tuning

Treat `GOGC`, memory limits, scheduler settings, and runtime experiments as
system policy. Measure heap, CPU, latency tails, and OOM behavior under realistic
load. Tuning around an avoidable retention bug makes the system more fragile.

Use `runtime/metrics` for stable documented metrics. Avoid building policy on
undocumented runtime internals.

## Profile-guided optimization

PGO uses a representative CPU pprof profile during build. Its benefit depends on
profile relevance and compiler version.

- Keep the profile representative of current production behavior.
- Understand how the repository stores, refreshes, and validates it.
- Compare PGO and non-PGO artifacts on correctness, size, startup, and workload
  metrics.
- Do not commit a profile containing sensitive data or unstable paths without
  review.
- A PGO gain does not replace source-level profiling or justify unrelated code
  complexity.

## Performance review checklist

- Is the target metric stated in user/system terms?
- Does the benchmark reproduce representative inputs and contention?
- Are before/after runs comparable and repeated?
- Does benchstat support the claimed difference?
- Were correctness, allocations, binary size, and latency tails checked?
- Do profiles identify the changed code as a material bottleneck?
- Are ownership/reuse contracts documented for any pooled or reused buffer?
- Was an adjacent timeout, retry, cache, or concurrency semantic changed without
  being required by the measured fix?
- Can the simpler implementation remain because the measured gain is negligible?
