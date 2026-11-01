# Concurrency, progress and asynchronous lifetimes

First identify the scheduler: ordinary threads, a repository pool, Qt/event loop,
GPU/backend work, coroutines, or a third-party runtime. Their cancellation,
ownership and exception policies differ. Serialization, CPU-thread affinity,
event-loop affinity and completion are different properties.

## Locks and publication

State which accesses each lock protects and what synchronization publishes data.
Use scoped lock ownership and predicate-based condition-variable waits. Check the
predicate under the same protocol that changes it; notifications alone do not
store state. Include shutdown in the predicate and wake all waiters whose progress
depends on it. Establish lock ordering; inspect callbacks, destructors and joins
that may reenter or acquire other locks. Avoid unknown callbacks under locks when
the contract can instead publish owned state then invoke after unlocking.

An atomic protects its own accesses, not an arbitrary neighboring object graph.
Use the simplest synchronization that establishes the required happens-before
edges. Relaxed counters may allocate distinct work indices without publishing
payloads; they do not replace a completion barrier. Do not change memory orders
or implement a lock-free reclamation scheme without a local correctness argument
and appropriate stress/model evidence. ABA, lifetime and reclamation survive an
otherwise correct compare-exchange loop.

## Parallel batches

A useful phase split is: freeze membership and input → assign independent slots
→ perform one-writer work → synchronize completion → reduce/publish.
Binaryen's parallel analysis provides a concrete trace. Verify the container's
concurrent-element guarantees and stable storage, not merely unique keys. Avoid
inserting lookup during parallel work; packed proxy elements such as `vector<bool>`
can share storage. Reads of shared mutable input still require synchronization.

Join before reducing or destroying borrowed callback state. Check nested dispatch
and callback exception policy; a pool's successful path is not evidence it can
recover from throwing jobs. A pointer-keyed map's iteration order is not stable
logical input order. Use deliberate reduction order if output or floating-point
reproducibility is promised, and compare sequential/parallel results accordingly.

## Stop, wake, complete, destroy

For each worker/callback, identify its owner, admission point, bounded retained
work, every blocking wait, cancellation observation, completion signal and final
cleanup. A stop flag cannot wake a producer blocked on a full semaphore/queue.
Use the existing close/stop-aware wait protocol or an explicit wakeup that lets
the worker observe stop without corrupting accounting.

qBittorrent's sender requests interruption and drains a pipe to release capacity.
This permits progress; it does not synchronously join the worker, prevent every
last write, or bound all process memory. Shared state must remain valid through
actual worker completion, and Qt deletion still needs the owning event loop.

`std::thread` destruction while joinable terminates. `jthread`, where supported,
requests stop and joins on destruction, but cooperative stop cannot forcibly
interrupt arbitrary blocking work; destruction can block. Ensure referenced
members outlive the join and avoid joining while holding a needed lock. Detached
work needs an explicit lifetime and shutdown owner. `std::async` and futures have
policy-dependent scheduling and waiting behavior; do not assume fire-and-forget.

## Callbacks and coroutines

Capturing `this`, a view, reference or native handle does not extend its lifetime.
Define what prevents execution after teardown; disconnection is not automatically
quiescence for callbacks already running. Guard stale results separately from
transport ordering when newer state can supersede an earlier computation.

For one-shot APIs that require completion, give each admitted operation one
completion owner. Trace success, failure, cancellation and synchronous early exits
for exactly-once delivery under that API's contract. Framework error macros may
return from the enclosing function; a synchronous helper can omit the completion
required by an asynchronous entry point. Inspect the actual helper/control flow.

Completion can synchronously destroy the operation, context or owning object.
Where the contract permits that, publish status/output and finish cleanup that
borrows them before invoking completion. Treat the invocation as a terminal
ownership boundary: later member access, local destructors and scope guards also
need a lifetime proof. Merely placing `return` after the callback does not make a
guard that still borrows the destroyed context safe.

A coroutine is not inherently a background thread or a cancellable task. Read the
actual task/promise/executor type: initial/final suspension, frame ownership,
exception storage, resumption, cancellation and destruction. Parameters and lambda
captures can remain borrowed across suspension, and a closure may die before its
coroutine finishes. Destroying a suspended frame is not a general safe substitute
for a coordinated stop; prove no resumer still owns access. Do not hold ordinary
locks across suspension unless the runtime and protocol explicitly support it.

Use gates/latches/barriers for deterministic lifetime and shutdown tests. Exercise
blocked producers, stop-before-admission, late callbacks, exception publication,
required completion on every terminal path, destruction and repeated shutdown.
TSan covers exercised races, not deadlock
freedom, logical freshness or all schedules; add a progress assertion and bounded
test timeout whose failure is visible.
