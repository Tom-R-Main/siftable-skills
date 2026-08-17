# Rust async and concurrency

Use this reference for Tokio or other runtime code, task lifetimes, `Pin`,
channels, timeouts, cancellation, `select!`, streams, locks, blocking work,
cleanup, graceful shutdown, and async tests. Inspect the runtime and versions
already pinned by the project before using crate-specific APIs.

## Start with what the compiler builds

`async fn` and `async {}` compile to a state machine (a coroutine) that
implements `Future`. `expr.await` desugars to roughly
`match IntoFuture::into_future(expr) { mut f => loop { match poll(pin(&mut f), cx)
{ Ready(v) => break v, Pending => yield } } }`. Five consequences follow and
explain most async bugs:

1. **Futures are lazy.** Nothing runs until polled; `.await` yields to the
   executor and does not create a thread.
2. **Every `.await` — including ones hidden inside macros — is a suspension
   point, and therefore a point where the future may be dropped and never
   resumed.** That is cancellation (below).
3. **Every local live across an `.await` becomes a field of the state
   machine.** This determines the future's size, whether it is `Send`/`Sync`
   (a `!Send` guard alive across an await makes the whole future `!Send`, used
   or not), and makes the state self-referential — which is why polling
   requires `Pin`.
4. **`.await` accepts any `IntoFuture`**, not only `Future`; builders can
   return an `IntoFuture` so `client.get(url).await` works.
5. **A future that panicked is poisoned.** Polling it again panics
   ("resumed after panicking"); catching the panic does not make it resumable.

Choose async for many concurrent I/O-bound operations. Choose ordinary
synchronous code for simple blocking programs and CPU-bound kernels unless the
surrounding system requires async integration. Do not add a runtime merely
because a function may take time.

## `Pin` in practice

`Future::poll(self: Pin<&mut Self>, cx: &mut Context<'_>)`. `Pin` promises the
value will not move again until dropped, so self-references inside the state
machine stay valid. You meet it when you:

- pass a future **by reference** to `select!`/`join!` or reuse it across loop
  iterations (`let mut f = op(); loop { select! { r = &mut f => ..., ... } }`);
- poll manually, implement `Future` or `Stream`, or store `dyn Future`;
- see `error[E0277]: `dyn Future<Output = ()>` cannot be unpinned` /
  "the trait `Unpin` is not implemented".

Fixes, in order: `let f = std::pin::pin!(op());` (stack, no allocation);
`Box::pin(op())` when it must be `'static`, boxed, or `dyn`. Most hand-written
structs and `Box<F>` are `Unpin` and can be moved freely; async blocks are not.
Do not use `Pin::new_unchecked` in application code; the safe constructors
cover ordinary use.

## Own every task

Prefer structured concurrency: the scope that starts work should retain the
handles, define error policy, initiate cancellation, and wait for completion.

- Await `JoinHandle`/`JoinSet` results and handle both task failure (panic or
  abort) and inner operation failure.
- Do not detach tasks accidentally by dropping handles.
- Bound fan-out with a semaphore, worker pool, `JoinSet` with a cap, or
  `buffer_unordered(n)` on a stream.
- Decide whether one child failure cancels siblings, is collected, or is logged
  and isolated.
- Give background tasks an explicit shutdown owner.

Spawning requires owned data and often `Send + 'static`; that describes the
task's mobility and lifetime, not necessarily the application's desired
ownership. Borrowed concurrency within a scope (`join!`, `try_join!`, scoped
APIs) may avoid cloning large state.

## Backpressure and channel selection

Prefer bounded channels unless an unbounded queue has a proven memory bound.

| Need | Typical primitive |
|---|---|
| Many producers, one consumer, each item handled once | bounded `mpsc` |
| One response to one request | `oneshot` |
| Latest configuration/state, old values unimportant | `watch` |
| Every receiver observes later events and lag is explicit | `broadcast` |
| Shared read/write state | `RwLock`/`Mutex` after message passing is considered |
| Limit concurrent permits | `Semaphore` |

Channel closure is part of the protocol. Drop unused sender clones so receivers
can terminate. Handle receiver lag, sender closure, and failed replies
explicitly.

## Cancellation

**Definition.** Code is cancellation safe if it behaves correctly whether it
runs to completion or stops at *any* `.await` and never resumes.

**How cancellation happens** — four ways, with different guarantees:

| Mechanism | Cooperative? | Future is notified? |
|---|---|---|
| Dropping a future you own | no | only via destructors |
| `JoinHandle::abort` / `AbortHandle` | no | only via destructors |
| `CancellationToken` (or a `watch`/flag) | yes | yes — it must check |
| Implicitly, inside `select!`/`timeout` | no | only via destructors |

The consequences that cause real bugs:

- A future holding a cancellation token can still be cancelled by drop, abort,
  or `select!`, **and the token will not fire**. Cleanup that only runs on the
  token path is skipped on the others; put must-run cleanup in `Drop` or in a
  supervisor, not in the token branch.
- Non-cooperative cancellation gives no chance to await anything. There is no
  async `Drop` (see "Cleanup" below).
- The root cause of most cancellation-unsafety is **state split between the
  future and something outside it**: bytes read into a buffer *inside* a
  future, an item half-taken from a stream, a partially applied write. Drop
  the future and that state is lost or duplicated.

Before racing or aborting, answer for each operation:

- Is partial input buffered or lost if the future is dropped?
- Has external state changed?
- Can the operation be retried safely?
- Does a child task continue after the parent branch is cancelled?

**`select!` specifics** (Tokio's; other runtimes are similar):

- It is usually the primary source of cancellation in a program: every branch
  that loses is dropped, silently.
- Branch patterns can fail to match (`Some(x) = s.next() => ...`); a
  non-matching branch is disabled but others keep polling. With no matching
  branch left and no `else`, **`select!` panics**.
- `if` guards are evaluated once when the macro starts, not on every poll.
- To keep a future alive across loop iterations (a timeout that spans the
  loop), create it outside and select on `&mut fut` — which requires `pin!`.
- The select-in-a-loop over a stream is the canonical data-loss shape: if the
  other branch wins mid-item, whether the item is lost or duplicated depends on
  the stream implementation. Prefer methods documented as cancellation safe
  (`mpsc::Receiver::recv`, `StreamExt::next`) and keep any partial-read buffer
  *outside* the raced future.

Use timeouts around semantic operations, not arbitrarily around every await.
Return a distinct timeout/cancelled outcome when callers need to choose
recovery. With biased or prioritized selection, document starvation behavior;
avoid loops whose always-ready branch prevents progress elsewhere.

## Blocking and CPU work

The rule is not "no CPU work in async"; it is **do not mix long-running and
latency-sensitive work on the same executor threads without special handling**.
Blocking I/O (everything in `std::io`, `std::fs`, `std::net`), `thread::sleep`,
and long computations stall every task on that worker.

- `spawn_blocking` runs **synchronous** code on the runtime's blocking pool.
  Its `JoinHandle` has `abort`, but the task **cannot be cancelled once
  started**; use it for work that finishes.
- Work that may block **indefinitely** (a listener loop, a subprocess wait)
  belongs on a dedicated `std::thread`, not the blocking pool, so it does not
  pin a pool thread forever.
- `tokio::fs` is `spawn_blocking` underneath; it is not truly asynchronous.
- Sustained CPU work goes to a compute pool (Rayon is the common choice) with a
  `oneshot` back to the async side, or to a separate runtime.
- `yield_now`/chunking only helps when the algorithm tolerates interleaving and
  latency actually improves; measure.

Blocking tasks need their own bound and their own shutdown owner.

## Locks across await

Do not hold a synchronous mutex guard across `.await`. Even an async-aware guard
should cover the smallest possible critical section:

```rust
let snapshot = {
    let state = shared.read().await;
    state.snapshot()
};

send_snapshot(snapshot).await?;
```

Prefer moving the owned snapshot or command out of the lock before awaiting.
Check lock ordering and poisoning policy in synchronous code (Tokio's mutex does
not poison; a panic while holding it can leave data inconsistent). For
read-heavy data, first consider immutable snapshots or an actor/task that owns
mutation.

## `Send`, `Sync`, and local tasks

A spawned future is often required to be `Send` because the executor may move
it between threads. A future becomes non-`Send` when a non-`Send` value is a
field of its state — that is, live across an `.await`, whether or not it is
used afterwards. Shorten its scope (`drop(guard)` or a block) or move the
awaited work outside that scope.

Use `LocalSet`/single-threaded executors only when non-`Send` state is an
intentional architecture choice. Do not weaken concurrency merely to silence a
diagnostic without checking throughput and integration constraints.

## Streams

There is no stable std trait for async iteration (`core::async_iter` is
unstable); use `futures::Stream`/`StreamExt` or `tokio_stream`. Consume with
`while let Some(item) = stream.next().await`; a `!Unpin` stream needs `pin!`
first. Prefer bounded concurrency combinators (`buffer_unordered(n)`,
`for_each_concurrent(Some(n), ..)`) over spawning per item. Remember that a
stream is a sequence of futures: dropping it mid-item has the same
cancellation semantics as dropping any future.

## Async traits and closures

- Native `async fn` in traits (1.75+) and `-> impl Future` methods are **not
  dyn compatible**. For `dyn Trait`, return `Pin<Box<dyn Future<Output = T> +
  Send + '_>>` or use the `async-trait` macro; each choice has allocation,
  `Send`-bound, and MSRV consequences.
- Async closures (`async |x| ..`, 1.85+) implement `AsyncFn`/`AsyncFnMut`/
  `AsyncFnOnce`; those traits are also not dyn compatible.
- Spell out `Send` bounds on returned futures at API boundaries when callers
  will spawn them.

Match the pinned MSRV; do not add a macro dependency automatically.

## Cleanup, panics, and the absence of async `Drop`

You cannot `.await` in a destructor, and non-cooperative cancellation runs
only destructors. Design cleanup accordingly:

- Prefer designs that need no async cleanup: idempotent operations,
  abort-and-restart, resources released synchronously in `Drop`.
- When an async goodbye is required (flush, unsubscribe, final message),
  separate cleanup from destruction: an explicit `async fn close(self)` plus a
  `Drop` that logs or `debug_assert!`s if `close` was skipped.
- Centralize cleanup in a supervisor task that owns the resources and outlives
  the workers, so a cancelled worker cannot skip it.
- Panics inside a task surface as `JoinError` on the handle; decide whether
  they crash the program, restart the task, or are logged. Never call async
  code while panicking.

## Graceful shutdown

A complete shutdown has three stages:

1. Detect a signal or internal failure.
2. Notify all owned tasks (cancellation token, channel closure, or protocol
   message).
3. Stop accepting work, drain or reject queued work according to policy, flush
   required state, and await task completion within a bounded deadline.

Aborting tasks is a last-stage policy, not a substitute for cooperative
shutdown, and it bypasses tokens. Test shutdown while work is active, not only
while idle.

## Observability and testing

- Instrument task creation and semantic operations with stable identifiers.
- Preserve causal error chains; avoid duplicate error logs at every layer.
- Record queue depth, saturation, timeouts, retries, cancellations, and task
  lifetime where operationally useful.
- Use runtime test time controls (paused/virtual time) instead of wall-clock
  sleeps.
- Test channel closure, slow consumers, timeout edges, cancellation at
  multiple await points, drop-during-await, and child-task failure.
- Use Loom or a similar model checker for small synchronization algorithms when
  interleavings are the correctness risk.

## Primary references

- [Asynchronous Programming in Rust](https://rust-lang.github.io/async-book/)
- [The Rust Programming Language, ch. 17: Async and Await](https://doc.rust-lang.org/book/ch17-00-async-await.html)
- [Tokio tutorial](https://tokio.rs/tokio/tutorial)
- [Tokio graceful shutdown](https://tokio.rs/tokio/topics/shutdown)
- [Tokio `select!` and cancellation](https://tokio.rs/tokio/tutorial/select)
