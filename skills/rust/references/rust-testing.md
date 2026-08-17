# Rust testing

Use this reference when adding regressions, designing a test strategy, debugging
flaky tests, validating async or unsafe code, or measuring coverage.

## Choose the test from the risk

| Risk | Best starting test |
|---|---|
| Pure function or local invariant | unit test beside the module |
| Public crate behavior | integration test under `tests/` |
| Public usage example | rustdoc test |
| Parser/serializer algebra | property test or fuzz target |
| Large generated/rendered output | reviewed snapshot with semantic assertions |
| Concurrency interleaving | deterministic synchronization test or Loom model |
| Unsafe/aliasing/initialization | unit tests plus Miri/sanitizer checks |
| Performance regression | benchmark with controlled inputs and baseline |

For bug fixes, reproduce the failure before changing implementation: add or
find the test, run it, and watch it fail for the expected reason *before* any
implementation edit; do not combine the test edit and the fix; run it again
after and watch it pass. Assert the externally meaningful behavior, then keep
the regression focused enough to explain the bug. If a first viable test would
require restructuring production code (new seams, exposed internals, a new
harness), stop and design that boundary deliberately — it is test-suite
design, not a regression test.

Model-written changes without tests are not done. Tests are the evidence the
reviewer can run; the conversation is not.

## Unit, integration, and doc tests

- Put private implementation tests in `#[cfg(test)] mod tests`.
- Put consumer-visible behavior in `tests/*.rs`; those tests use only the public
  API and expose accidental visibility assumptions.
- Use doc tests for short, stable public examples. Mark examples `no_run` only
  when execution genuinely requires unavailable resources.
- Let test functions return `Result` when `?` improves failure context.
- Name tests for scenario and outcome. Avoid a mandatory `test_` prefix when the
  surrounding project has a clearer convention.
- Multiple assertions are fine when they describe one behavior. “One assertion
  per test” is a heuristic, not a law.

Prefer equality/matches that produce useful diffs:

```rust
assert_eq!(actual, expected);
assert!(matches!(error, ParseError::UnexpectedToken { .. }));
```

Test exact strings only when wording is part of the contract. Otherwise assert
the typed variant and relevant fields.

## Dependencies and seams

Prefer real values, in-memory implementations, temporary directories, and small
trait seams over broad mocking. Mocking is useful for failure injection or
expensive external boundaries, but interaction-heavy mocks couple tests to
implementation order.

Do not add `rstest`, `proptest`, `mockall`, `insta`, `tempfile`, or another test
crate automatically. First check existing dev-dependencies and whether the same
test can remain clear with the standard library.

Keep test helpers explicit. A helper that hides most setup can make failures
harder to interpret; builders with sensible defaults are often a good balance.

## Property testing and fuzzing

Use property tests when many examples share an invariant:

- encode/decode round trips;
- normalization idempotence;
- sort ordering and element preservation;
- parser never panics on arbitrary input;
- valid constructors always produce values accepted downstream.

Keep generators valid enough to reach deep behavior, and include shrinking so
failures become small. Store important minimized regressions as ordinary tests.

Use `cargo fuzz`/libFuzzer or the project's fuzz harness for untrusted parsers,
decoders, protocol handlers, and unsafe boundaries. Seed with representative
corpus data and convert crashes into permanent regressions.

## Async and concurrency tests

- Use the pinned runtime's test macro and virtual-time controls.
- Do not rely on short sleeps to “let a task run.”
- Coordinate with channels, barriers, notifications, or paused time.
- Test cancellation, channel closure, backpressure, timeout boundaries, and
  shutdown with in-flight work.
- Avoid globally shared mutable state; if unavoidable, make serialization and
  cleanup explicit.
- Treat a flaky test as a correctness problem. Capture seeds, schedules, ports,
  environment, and timing evidence rather than adding retries blindly.

## Snapshots

Snapshots fit structured diagnostics, generated schemas, render trees, and
large text output. Keep a few semantic assertions beside the snapshot so a
visually plausible but wrong result cannot pass unnoticed. Review diffs rather
than accepting updates mechanically: run the focused test *without* the
update/bless flag first and confirm the mismatch is the one you expected, then
regenerate, then read the generated diff. If the tool produced text you did
not expect, stop and report it rather than editing the snapshot by hand.

Avoid snapshots for unstable maps, timestamps, paths, random IDs, or error
debug output unless those fields are normalized intentionally.

## Coverage

Coverage finds unexercised code; it does not prove behavior or test quality.
Follow the repository's existing threshold. Do not invent a universal 80% or
100% target.

Prioritize:

- safety and authorization boundaries;
- parsers and protocol state transitions;
- error/retry/cancellation paths;
- public API behavior;
- bug regressions.

Exclude generated bindings only through an explicit project policy.

## Commands

Start focused, then broaden:

```sh
cargo test -p package_name test_name
cargo test -p package_name --test integration_name
cargo test -p package_name --doc
cargo test --workspace
```

Use the project's established runner when present:

```sh
cargo nextest run --workspace     # only if configured/installed
cargo llvm-cov --workspace        # only if configured/installed
cargo test -- --ignored           # explicitly opted-in suites
```

Run feature, target, and MSRV matrices when those are contractual. Avoid
`--all-features` if features are intentionally mutually exclusive.

## Benchmarks are tests of claims

Use Criterion, iai-callgrind, built-in benches, or the repo's harness as already
configured. Include warmup/sample policy, input distribution, release profile,
target CPU, and variance. Validate results for equivalence outside the benchmark
and guard against dead-code elimination with the harness's black-box mechanism.

Never call a debug-profile timing a production speedup.

## Primary references

- [Rust Book: Writing Automated Tests](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [Cargo test command](https://doc.rust-lang.org/cargo/commands/cargo-test.html)
- [Rustdoc tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html)
- [Rust Fuzz Book](https://rust-fuzz.github.io/book/)
