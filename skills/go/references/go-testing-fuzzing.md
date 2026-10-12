# Go testing and fuzzing

Testing APIs are versioned. Check the module's `go` directive and selected
toolchain before adopting newer helpers.

## Contents

- Regression-first fixes and package choice
- Table tests, subtests, and parallel tests
- Time, context, goroutines, and integration tests
- Fuzzing
- Coverage, examples, and golden files
- Caching, flakes, repetition, and review checklist

## Regression-first fixes

For a behavioral bug:

1. Identify the narrowest observable contract.
2. Add or find a test that fails for the reported reason.
3. Run it against the broken state and retain the failure evidence.
4. Implement the smallest correction.
5. Run the focused test, adjacent package tests, then repository gates.
6. State which production/environment conditions were not reproduced.

A test that passes before the fix does not establish the regression. Avoid
overfitting to internal statements when public behavior can express the bug.

## Package choice

- Same-package tests can inspect unexported details. Use them when internal
  invariants genuinely need direct testing.
- External `package_test` tests exercise the exported contract as a consumer.
  Use them for public APIs and examples when practical.
- A package can intentionally use both. Do not reorganize existing tests merely
  to impose one style.

Test-file organization follows local code. Co-locate `_test.go` files with the
package, but do not impose one test file per source file or one universal naming
scheme beyond Go's required `TestX`, `BenchmarkX`, `FuzzX`, and `ExampleX` forms.

## Table tests and subtests

Table-driven tests work well when cases share setup and assertions. They are not
mandatory when cases have materially different behavior or clearer standalone
names.

- Give cases stable diagnostic names.
- Report inputs, got, and want in failures.
- Avoid assertion loops that continue after a prerequisite failure.
- Pass the subtest's `*testing.T` to helpers and assertion objects; do not retain
  the parent `T` accidentally.
- Call `t.Helper()` in reusable test helpers so failures point to the caller.
- Use `t.Cleanup` for resources whose lifetime belongs to the test.

## Parallel tests

Parallelism is an opt-in semantic claim: tests must not share mutable process
state, ports, fixed files, environment variables, current working directory,
global loggers, or order-dependent fixtures.

- `t.Parallel` pauses a subtest until its sequential parent returns or becomes
  parallel. Understand this barrier before sharing setup.
- Language versions before Go 1.22 have the old range-variable capture behavior.
  Match the module's language version; do not assume the host compiler changes
  source semantics for an older module.
- Do not enable parallelism solely to reduce CI time without measuring contention
  and flake behavior.
- `T.Setenv` and `T.Chdir` affect process-global state and cannot be used in
  parallel tests or parallel ancestors.

Use the race detector on representative concurrent tests. A passing race run is
not proof for unexecuted paths.

## Time, context, and goroutines

Avoid wall-clock sleeps as coordination. Prefer injected clocks, explicit
events, or `testing/synctest` on Go 1.25+.

- `T.Context` (Go 1.24+) is canceled before cleanup functions run, allowing
  cleanup to wait for context-driven shutdown.
- Register cancellation and joins with cleanup so a failure does not leak work.
- Give blocking tests bounded time and make timeout failures print useful state.
- For external systems, wait on a specific readiness condition rather than a
  guessed duration.

See `go-concurrency-context-memory.md` for synctest constraints and lifecycle
proofs.

## Integration and end-to-end tests

Use the repository's separation mechanism: dedicated packages/directories,
build tags, flags, scripts, containers, or test harness. Build tags are one
option, not a universal requirement.

Integration tests should make dependencies explicit:

- required services, kernel features, privileges, credentials, and ports;
- setup/cleanup ownership;
- isolation between tests and retries;
- deterministic seed and fixture version;
- skip reason when an environment is intentionally unavailable.

Do not silently convert an integration test into a unit test with mocks if the
real boundary is the contract under test.

## Fuzzing

Native fuzz targets execute their seed corpus during ordinary `go test`. A fuzz
campaign requires `-fuzz` and normally a bounded `-fuzztime` in agent work.

Good fuzz targets:

- accept supported primitive parameter types;
- add representative valid and invalid seeds;
- reject invalid domains cheaply with `t.Skip` when appropriate;
- assert invariants, round trips, parser safety, or equivalence;
- avoid nondeterministic external systems and process-global mutation;
- do not retain or mutate fuzz-provided byte slices after the call;
- turn discovered crashes into committed regression seeds after review.

Run one matching target at a time:

```sh
go test ./path/to/pkg -run '^$' -fuzz '^FuzzName$' -fuzztime=30s
```

Fuzzing writes cache/corpus artifacts. Know where they go and inspect any
candidate before committing it, especially if inputs may contain sensitive data.

## Coverage, examples, and golden files

Coverage is a navigation signal, not a quality target. Inspect uncovered
branches that carry meaningful behavior; do not add assertions-free tests to
raise a number.

Examples with `// Output:` are executable documentation. Prefer them for public
call sequences and stable output. Avoid network or nondeterministic examples.

Golden files are useful for large stable output when review of the complete
artifact matters. Updates must be explicit, diffed, and separated from ordinary
test execution. Never make a failing test rewrite its own expected output by
default.

## Caching, flakes, and repetition

Successful `go test` results may be cached. Use `-count=1` when a fresh run is
part of the claim, not reflexively for every local test.

For flakes:

```sh
go test -count=50 -run '^TestName$' ./path/to/pkg
go test -shuffle=on -count=20 ./path/to/pkg
go test -race -count=10 -run '^TestName$' ./path/to/pkg
```

Adapt counts to cost. Capture the seed printed by `-shuffle` and the exact Go
version, target, tags, and environment. Fix the missing synchronization or state
isolation; do not increase sleeps/timeouts without evidence that the threshold
is the contract.

## Test review checklist

- Did the regression test fail before the fix for the intended reason?
- Does the test assert observable behavior and important error paths?
- Is state isolated from order, parallelism, and the developer machine?
- Are cleanup and goroutine joins guaranteed on failure?
- Are fake time and cancellation used instead of sleeps where appropriate?
- Does integration coverage exercise the real boundary?
- Are fuzz inputs deterministic, non-sensitive, and bounded?
- Do failures explain got, want, and the case that failed?
- Were cached, race, platform, or privileged limitations reported honestly?
