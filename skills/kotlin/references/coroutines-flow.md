# Coroutine ownership, cancellation, and Flow

Start by naming the owner, lifetime, producer, consumers, and failure contract.
`suspend` does not itself select a dispatcher, make blocking code safe, or start
parallel work. Preserve a caller-owned suspend API unless the product requires
work with a different lifetime.

## Structured work and failure

Use `coroutineScope` for child work whose completion belongs to the operation;
use supervision when independent child failure is intended and handled. A
supervisor isolates failure propagation; it does not provide recovery. Inject or
use a lifecycle-owned scope only for work that really outlives the call, with a
visible shutdown/cancellation path. A fresh `Job` supplied to a builder can sever
its parent relationship. Avoid hidden per-call scopes and unowned GlobalScope.

Child failures normally cancel their parent even when produced by `async`.
Calling `await` is necessary for a result, but delaying or omitting it does not
turn a failing structured child into independent work. A
`CoroutineExceptionHandler` observes uncaught terminal failures; it is not a
replacement for catching an expected exception around the operation.

Cancellation is cooperative. Rethrow `CancellationException` when a broad catch
would translate it into an ordinary error; catch expected operational failures
more narrowly when possible. Kotlin stdlib `runCatching` catches `Throwable`,
including cancellation. Inspect `getOrElse`, retry, and fallback paths around
suspend calls before using it there. Do not catch fatal errors merely to return
`Result.failure`.

Inspect existing cancellation-aware result helpers and their enforced lint
rules before inventing another wrapper. Verify the implementation rather than
trusting its name; ordinary exceptions, cancellation, fatal errors, and a
pre-existing failed Result can take different paths.

CPU loops need cancellation checks such as `ensureActive()` where responsiveness
matters. Blocking calls need a suitable boundary and, where supported, an
interruptible adapter; putting them on `Dispatchers.IO` does not automatically
make the underlying operation cancellable. Reserve `runBlocking` for a genuine
blocking entry boundary or appropriate legacy test, not an ordinary suspend
implementation or UI/event-loop thread.

Use the project's injected dispatchers/executors and thread-affinity adapters.
A libGDX render thread is not interchangeable with Android `Dispatchers.Main`.
Check who closes custom dispatchers and whether work may outlive a screen or
keep the process alive. For native sessions and single-shot callback bridges,
read [production patterns](production-patterns.md).

Close resources in `finally`/`use`. Timeout and cancellation can race acquisition
and delivery. Keep ownership safe across that race; use `NonCancellable` only
for essential suspending cleanup with a bounded policy. Cancellation does not
roll back a database write or undo an external request.

## Model delivery before selecting a primitive

| Need | Candidate and questions |
| --- | --- |
| Latest renderable state | StateFlow; initial value, equality, conflation, immutable publication |
| Broadcast to subscribers | SharedFlow; replay, overflow, subscriber gaps, acceptable loss |
| Work handed to one receiver | Channel; capacity, close, cancellation, undelivered work |
| Operation owned by caller | Suspending return value; cancellation and typed failure |
| Must survive process death or need acknowledgement | Durable state/queue with IDs and acknowledgement, not an in-memory delivery guarantee |

StateFlow suppresses equal values and slow collectors can miss intermediate
states. Publish new snapshots rather than mutating an existing list/object in
place. For concurrent changes use atomic `update` when available; its function
may be retried, so keep it free of side effects. `_state.value =
_state.value.copy(...)` can lose a competing update.

For SharedFlow, extra buffer capacity accommodates slow active subscribers;
without subscribers only replay is retained. A replay-zero event can disappear
even when `tryEmit` succeeds. Adding replay can instead repeat navigation or
other side effects on re-collection. A buffered Channel can bridge a temporary
receiver gap within its owner's lifetime, but cancellation during delivery and
process death still prevent an exactly-once guarantee.

Specify whether one consumer or all consumers receive an event, whether loss or
duplicates are acceptable, and whether acknowledgement/retry is required.
Avoid a universal rule that all events must use either Channel or SharedFlow.

## Flow execution and observation

Cold builders rerun per collection. `stateIn`/`shareIn` introduce an owning scope
and a sharing policy: test start/stop, replay expiration, restart, and retained
resources. Sharing is not merely a performance annotation.

`flowOn` affects upstream context, not the collector's work. Use `channelFlow`
for appropriate concurrent producers and `callbackFlow` with `awaitClose` for
callback registration cleanup. Do not emit from an unrelated context inside a
regular `flow` builder. `catch` handles upstream failures; it does not catch
arbitrary downstream collector failures. Place retries at an intentional
upstream boundary and bound them according to the operation's idempotency.

`collectLatest`/latest operators cancel earlier work. `conflate`, buffer overflow,
and debounce deliberately skip values; each requires a behavioral reason.
Thread-safe primitives do not make compound invariants atomic: coordinate with
confinement, a mutex, atomics, or a transaction matching the real invariant.

Resolve extension overloads from the receiver's static type before judging
atomicity. JVM `ConcurrentMap.getOrPut` uses `putIfAbsent` to return the winning
stored value, although competing initializers may run; `MutableMap.getOrPut`
does not offer that concurrent guarantee. Repeated initialization and distinct
returned values are different claims; side effects in initialization still
need their own contract.

Use virtual-time lifecycle and delivery tests, plus real concurrency evidence
when races matter: see [testing](testing-performance.md).

## Sources

- [Coroutine exception propagation and supervision](https://kotlinlang.org/docs/exception-handling.html)
- [Cancellation and timeouts](https://kotlinlang.org/docs/cancellation-and-timeouts.html)
- [StateFlow API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/)
- [SharedFlow API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/)
- [callbackFlow registration and cleanup](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html)
- [flowOn context boundary](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow-on.html)
- [getOrPut overload guarantees](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.collections/get-or-put.html)
- [Upstream skills and direct runCatching source evidence](sources.md)
