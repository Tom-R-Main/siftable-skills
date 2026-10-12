# Go concurrency, context, and the memory model

Concurrency APIs and runtime behavior are versioned. Verify version-sensitive
claims against the selected toolchain's `sync`, `context`, `testing/synctest`,
memory-model, and race-detector documentation.

## Contents

- Lifecycle proof and context
- Goroutine groups, channels, and cancellation
- Locks, atomics, and shared state
- Happens-before reasoning
- Deterministic tests, race tests, and leak tests
- Review checklist

## Start with the lifecycle proof

Before adding or reviewing a goroutine, answer:

1. Who owns starting it?
2. What inputs or state does it retain?
3. How does it exit on success, error, cancellation, and partial startup?
4. Who can request shutdown?
5. Who waits for completion?
6. Where does its error go?
7. What bounds the number of goroutines and queued work?
8. Which happens-before edges make shared memory safe?

If these answers are unclear, concurrency is not yet designed. A goroutine's
cheap startup cost does not make its lifetime free.

## Context

Use `context.Context` for request-scoped cancellation, deadlines, and metadata
that must cross API boundaries.

- Put context first and do not accept nil; use `context.Background()` or
  `TODO()` at a real root.
- Always call a returned cancel function unless ownership is explicitly
  transferred. This releases timers and descendants even if the deadline never
  fires.
- Propagate context through blocking I/O and downstream calls. A goroutine only
  stops if its code observes cancellation or another exit condition.
- Avoid storing context in structs. A rare API that must do so should document
  replacement, lifetime, and concurrency semantics.
- Context values are for request-scoped cross-boundary data, not optional
  parameters, dependencies, or mutable state. Use unexported key types.
- `context.WithCancelCause`/`Cause` can preserve why work stopped, but do not
  turn cancellation into an unbounded error-reporting channel.
- `context.AfterFunc` runs a function in its own goroutine after cancellation;
  design the race between the function and `stop` explicitly.

## Goroutine groups

Use the simplest construct that represents the contract:

- `sync.WaitGroup`: completion only; no built-in errors or cancellation.
- `WaitGroup.Go` (Go 1.25+): start and track tasks; the function must not panic.
- `golang.org/x/sync/errgroup`: first-error propagation, optional sibling
  cancellation, and optional concurrency limits. Use only when already allowed
  by dependency policy.
- A repository-specific group or supervisor: process-lifetime tasks, restart
  policy, health, or multi-error semantics not represented above.

Do not call `Add` concurrently with an initial `Wait` in a way that permits
`Wait` to observe zero before work is registered. Version-gate `WaitGroup.Go`;
do not modernize a module below Go 1.25 merely because the host toolchain has it.

When using `errgroup.WithContext`, remember that the derived context is canceled
when the first task returns an error *or when `Wait` returns*. Do not return data
that still depends on that context after `Wait`.

## Channels

Treat a channel as a protocol, not a queue-shaped variable.

Specify:

- the message meaning and ownership;
- who sends and who receives;
- who closes and after which senders have stopped;
- behavior on cancellation or early receiver exit;
- whether buffering is required for a semantic reason; and
- whether zero values or closed-channel receives are valid messages.

Rules with concrete failure modes:

- Only code that knows no future sends can occur may close the channel.
- A receiver does not close merely because it is no longer interested; it must
  signal cancellation or drain according to the protocol.
- A send on a closed channel and a second close panic.
- Receives from a closed channel yield remaining buffered values and then the
  zero value with `ok == false`.
- A nil channel blocks forever in send/receive and disables a `select` case.
- Buffer size is part of backpressure and memory behavior. Do not increase it to
  conceal a blocked lifecycle without understanding the producer/consumer rate.

Sending a pointer is not inherently wrong. Decide whether it transfers exclusive
ownership, shares immutable data, or creates synchronized shared mutation. Make
that contract explicit.

## Select and cancellation

`select` chooses pseudo-randomly among ready cases. A cancellation case does not
automatically win over another ready send or receive.

For operations that must not proceed after cancellation, recheck the context or
encode state so the undesired operation cannot be ready. Do not add
`ctx.Done()` mechanically to every select: some loops have process lifetime,
another shutdown signal, or a non-cancelable atomic operation. The exit contract
decides.

Timers and tickers require lifecycle care:

- Stop tickers when no longer needed.
- Reused timers need version-appropriate stop/drain/reset handling; consult the
  selected `time.Timer` docs because semantics changed in Go 1.23.
- `time.After` is fine for simple one-shot waits. In hot or long-lived loops,
  a reusable timer may reduce churn, but measure before complicating code.

## Locks, atomics, and shared state

Prefer confinement when it simplifies the invariant. When state is shared:

- Put the mutex adjacent to the fields it protects and comment the protected
  region when it is not obvious.
- Keep critical sections narrow, but do not split one atomic state transition
  merely to reduce lock duration.
- Do not call unknown callbacks under a lock unless reentrancy and blocking are
  explicitly supported.
- Define lock ordering when multiple locks can be held.
- Never copy a used mutex, RWMutex, Once, atomic value, or containing struct.
- Use `RWMutex` only when profiles or contention behavior justify the extra
  complexity; readers still exclude writers and may starve or add overhead.
- Use typed atomics for simple independently meaningful state. Multi-field
  invariants usually need a lock or immutable snapshot, not several atomics.
- `sync.Map` is specialized; read its docs and prefer a typed map plus mutex for
  ordinary shared state.
- `sync.Pool` is an opportunistic cache whose contents may disappear at any GC.
  Pooled objects must be reset, must not escape while pooled, and must not carry
  secrets across users.

## Happens-before reasoning

Race freedom requires synchronization, not "it usually runs first."

Useful synchronizing operations include mutex unlock/lock pairs, channel
send/receive and close/receive relationships, atomics, WaitGroup completion,
Once, and other operations documented by the standard library. Exact guarantees
belong to the Go memory model and package docs.

Do not use sleeps to establish ordering. A sleep changes probability, not the
memory model. Use a channel, condition, wait group, atomic, lock, or test seam
that represents the actual event.

## Deterministic tests with synctest

`testing/synctest` is available in Go 1.25+. It runs code in an isolated bubble
with a fake clock and can wait until other bubble goroutines are durably blocked.

Use it for timers, deadlines, context cancellation, and goroutine coordination
that otherwise depend on wall time. Constraints matter:

- network I/O and external processes are not durably blocking;
- channels/timers associated with a bubble cannot be operated from outside;
- leaked goroutines and outside dependencies break isolation;
- mutex blocking is not classified as durable blocking.

Prefer a fake clock or explicit seam if the module supports older Go or the code
interacts with external I/O.

## Race and leak testing

`go test -race` dynamically instruments supported targets and only finds races
on executed paths. Run focused representative workloads, not only tiny unit
tests. Race builds are slower, use more memory, and usually require CGO.

For leaks:

- make shutdown and join observable through the API when possible;
- use test cleanup to cancel and wait;
- inspect timeout goroutine dumps and pprof stacks;
- use a repository-approved leak detector if already present;
- avoid asserting only `runtime.NumGoroutine`, which is noisy process-global
  state.

## Concurrency review checklist

- Is synchronous code simpler and sufficient?
- Does every goroutine have an owner, exit, join, and error path?
- Is concurrency bounded under adversarial input?
- Are channel close and send ownership unambiguous?
- Can an early return leave a blocked producer or receiver?
- Are callbacks or I/O performed under locks?
- Is lock ordering documented and consistent?
- Are buffer reuse and shared pointers safe for caller retention?
- Does each claimed ordering have a real happens-before edge?
- Are cancellation races and partial startup/shutdown tested?
