# Concurrency and cancellation

## Determine isolation before choosing a fix

Record language mode, strict checking, default actor isolation and upcoming
features per affected module. In Swift 6.2-capable toolchains,
`NonisolatedNonsendingByDefault` changes nonisolated async execution to inherit
the caller's actor; `@concurrent` provides an explicit switch away. Availability
alone does not mean the feature is enabled. Default `MainActor` inference is a
separate setting. Do not promise background execution from `async`, `await`,
`nonisolated`, or `Task {}` in isolation.

Sources: [SE-0461](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0461-async-function-isolation.md),
[SE-0466](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md),
[migration diagnostics](https://docs.swift.org/latest/documentation/diagnostics/nonisolated-nonsending-by-default/).

`Sendable` describes values that may cross concurrency domains safely under their
contract. An actor can own mutable state, but every suspension can permit other
work to change it. Capture a request identity/version, perform the asynchronous
work, then verify it is still current before publishing. For transactions,
reserve/commit/rollback or revalidate explicitly; holding actor isolation before
an `await` does not reserve the state after it.

Actors serialize isolated work without promising a stable OS thread. A legacy
framework requiring a particular queue or thread needs that execution contract;
an ordinary actor only solves exclusion. Keep synchronous locks within short,
non-suspending scopes and invoke reentrant callbacks outside locks.

## Give tasks a lifecycle

Use `async let` or task groups for child work whose completion belongs to a
lexical scope. Groups await their children before leaving; cancellation is
cooperative. A timeout implemented as two group children can remain blocked on
a cancellation-ignoring loser. Establish whether a deadline means stop waiting,
request cancellation, or prove the underlying effect stopped.

`Task {}` is unstructured: it can inherit actor context and task-local context,
but its lifetime/cancellation are not managed like a group child.
`Task.detached` also drops inherited actor context. Store handles when an owner
needs to cancel/join them, observe errors, and define replacement and shutdown.
Do not use detached tasks merely to quiet isolation diagnostics. Do not block
the cooperative executor with semaphores, synchronous waiting on async work, or
long blocking calls; adapt through the actual subsystem's execution boundary.

Cancellation flags are not preemption. Check cancellation at useful boundaries,
propagate it through broad catches, and connect it to cancellable underlying
operations. Some APIs report domain-specific cancellation errors rather than
`CancellationError`; inspect their contract. A cancelled network task may already
have committed a server effect. Retry only according to that effect's identity
and idempotency contract.

For large dynamic workloads, a task group supplies lifetime structure but does
not impose an admission limit. Keep at most the chosen number of children in
flight, adding work as results arrive; account for retained bytes separately.
Task-group results arrive by completion order, so retain input identity if the
consumer needs original order. A child throwing does not by itself mean all
siblings have already been cancelled: inspect result consumption and whether
the error propagates out of the group body. Catching child errors as `Result`
changes fail-fast behavior; preserve cancellation and the required partial-result
policy deliberately.

## Bridge callbacks with a state machine

For each continuation adapter, identify registration, completion, cancellation
and teardown owners. Test these orderings:

1. Already cancelled before registration, including synchronous callback APIs.
2. Cancellation while admission/handle installation is in progress.
3. Success/error racing cancellation, duplicate callbacks and late callbacks.
4. Resource or delegate shutdown before any callback.

Consume/remove the completion token before resuming it so reentrancy cannot
complete it twice. Synchronize cancellation and registration together or provide
an explicit cancelled-before-registration state. Cancellation handlers can run
concurrently and cannot simply mutate actor state synchronously. A hop into an
actor can make cleanup eventual; prove the ordering at admission too.

When multiple waiters share one platform operation, one caller's cancellation
must not abandon other callers. Distinguish cancelling a waiter from stopping
the platform request. [OpenClaw receipts](production-patterns.md#waiters-and-timeout-races)
show both coalesced waiters and a timeout adapter; transfer the invariant, not its
entire implementation or newer toolchain requirements.

For `AsyncStream`/`AsyncThrowingStream`, choose buffering and loss policy explicitly,
finish once, unregister the producer on termination, and check what cancellation
does to the underlying work. A bounded buffer with dropped yields is not producer
backpressure. A single stream is not automatically a replaying broadcast bus.
For Combine bridges, preserve scheduler, demand, completion and subscription
lifetimes rather than assuming async iteration has identical semantics.

Use `@unchecked Sendable`, `nonisolated(unsafe)`, `@preconcurrency` or isolation
assertions only after documenting the specific external invariant and every
access path it covers. They cannot repair a race or missing executor hop.

## Diagnose the boundary, not only the annotation

| Symptom | First investigation |
| --- | --- |
| Main-actor member used from a nonisolated context | Identify the real owner and caller executor. Isolate or hop only for work that belongs there. |
| Sending a value risks a data race | Trace aliases that survive the transfer. Prefer an owned value/snapshot or verified isolation; do not assert sendability reflexively. |
| Isolated witness cannot satisfy a protocol | Inspect requirement and consumer isolation; consider supported isolated conformance, rather than making stateful code `nonisolated`. |
| Synchronous waiting is unavailable in async code | Await completion through the supported API; do not add a semaphore that blocks the executor. |
| New warnings after an SDK/compiler change | Compare imported annotations and target settings before adding `@preconcurrency` or changing public isolation. |

Use the selected compiler's exact diagnostic and supported syntax. A linter's
request to remove `async` is not decisive when a protocol, override or deliberate
executor boundary requires it; do not insert a meaningless `await` to silence it.
