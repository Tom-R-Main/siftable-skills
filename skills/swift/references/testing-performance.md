# Testing and performance

## Use the real test owner

Discover the repository's runner, target membership, scheme, test plan and
destination first. Use existing CI commands. Only when SwiftPM owns the affected
tests and execution/dependencies are authorized, examples include:

```sh
swift test --filter 'AccountTests'
swift test
swift build -c release
```

Check the selected tool's help for test-filter syntax and actual discovered
names; Swift Testing and XCTest names need not have identical shape. Confirm
the intended test count in the result. Test discovery/listing is not execution.
Do not use `--skip-build` against artifacts from before the change.

For Xcode, use the wrapper when one exists. A manual example, only after
selecting an existing workspace, shared scheme and available simulator ID, is:

```sh
xcodebuild test -workspace App.xcworkspace -scheme App \
  -destination 'id=<available-simulator-uuid>' \
  -only-testing:AppTests/AccountTests \
  -resultBundlePath <new-result-path>.xcresult
```

These placeholders describe target-project inputs, not bundled resources.
`build`, `build-for-testing` and `test-without-building` have different meanings;
the last must use the correct rebuilt artifacts and test-run configuration.
Preserve `.xcresult` summaries including failures and skips. A runner that exits
successfully after selecting zero tests is not a passing regression check.

Use the configured formatter/linter in check mode and with its pinned version.
`swift-format`, `swift format`, SwiftFormat and SwiftLint are distinct tools with
different configurations; do not substitute one or reformat a whole repository.
Missing tools, caches, SDKs, simulator access or signing are environment gaps;
do not install dependencies or weaken gates without authority.

## Choose tests that can distinguish the failure

Keep XCTest or Swift Testing according to target support and local practice;
both can coexist. UI automation/performance tooling may still require XCTest.
With Swift Testing, use `#expect` for checks that may continue and `#require` when
the rest of the test requires a value/condition. Avoid broad test-framework
migration as part of a feature fix.

Swift Testing tests normally run concurrently. Per-test fixtures and injected
clocks/services are preferable to shared process state. `.serialized` orders
tests within its scope; unrelated suites can still overlap. A main-actor test
can interleave at suspension too. Sources:
[suite organization](https://docs.swift.org/latest/documentation/testing/organizingtests/),
[serialization scope](https://developer.apple.com/videos/play/wwdc2024/10195/).

For asynchronous defects, control registration and completion with explicit
signals or an injected clock. Cover cancellation before/after registration,
duplicate/late completion, out-of-order results, owner destruction and shutdown.
Arbitrary sleeps and repeated `Task.yield()` do not prove an ordering. A watchdog
is a hang bound, not the test's synchronization mechanism. Include a control
that would fail if the cancellation/identity guard were absent.

Swift Testing's `confirmation` checks events within its body; it does not wait
for a callback after the body returns. Await the tested operation or its owned
task inside that scope, or bridge a callback with a correctly bounded lifecycle.
A zero-event confirmation proves only the observed interval. Do not use it as
proof that a late callback can never occur. Check the selected toolchain's time
limit API rather than inventing a subsecond trait; use an injected clock/gate
for deadline behavior. See [XCTest migration semantics](https://docs.swift.org/latest/documentation/testing/migratingfromxctest/).

For persistence, check legacy fixtures and migration rollback/failure behavior.
For encoders, assert the consumer-visible bytes/fields, not only a round trip
through the same potentially wrong implementation. For public SDK changes,
exercise an external consumer and the supported language/platform tuple.

For framed input, test complete, fragmented and coalesced records, including a
size limit crossed by the chunk containing the delimiter. A check on only the
unfinished buffer can miss an oversized complete record. Cover exact-limit
acceptance and recovery after rejection. For echoed UI state, repeat an older
value with unrelated state changed while newer local input remains pending;
ordered transport alone does not make each repeated value a fresh acknowledgement.

## Verify the actual artifact and measure what changed

- CLI: run the built product with representative success/failure arguments;
  assert output, exit status and cancellation/shutdown.
- Service: use the project's server driver, exercise the changed route and
  failure path, then stop owned processes. A health route proves less than the
  changed request. For event-loop frameworks, follow that framework's blocking
  and shutdown contract rather than generic actor advice.
- UI: exercise the packaged app's entry path, resources, navigation and changed
  interaction on the relevant simulator/device or macOS host.
- Native bridge: run through the real consumer, checking lifetime, ABI, error
  translation and callback executor. Use ASan/TSan or Instruments only on the
  supported platform/configuration and state which boundary they observe.

Measure release/optimized artifacts with comparable toolchain, inputs, hardware
and settings; keep a correctness gate. Profile before changing allocations,
copy-on-write behavior, existentials, specialization, task fan-out or ARC traffic.
Account for warmup, caches, variance, peak retained memory and cancellation cost.
A redraw count, source simplification, sanitizer pass or compiler success alone
does not establish a speed improvement or absence of races.
